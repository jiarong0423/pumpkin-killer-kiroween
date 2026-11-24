#!/usr/bin/env python3
"""Stress and CPU-load diagnosis for gap N10 (room round hash differs under CPU load).

Runs `scripts/test_page_judge_relay.py` many times in a row (default 30 rounds), one subprocess per round, optionally while N busy-loop
processes keep the CPUs saturated. It changes no production code and writes no formal data: it only writes its own log folder and a summary.

Per round it records: exit code, seconds, load average before and after, the test's last lines, and (on failure) every `round N hash differs`
line with the two hashes, so a failure can be classed as a real desync (the two pages disagree on state) or a harness race (timeout, relay
did not start, node seat died). Resumable: rounds already in rounds.jsonl are skipped with --resume.

Needs localhost sockets and Node 22+, so run it in a normal terminal, not in the Claude sandbox:
    python3 -B scripts/stress_judge_relay.py --rounds 30 --load-workers 0      # idle baseline
    python3 -B scripts/stress_judge_relay.py --rounds 30 --load-workers 3      # moderate CPU contention (owner 2026-11-23: no high concurrency)

Rounds always run one at a time. Load workers are capped at MAX_LOAD_WORKERS (3); more needs --allow-heavy.

Output: logs_local/stress_judge_relay/<label>/run_NN.log, rounds.jsonl, summary.json; the summary is also copied to
redteam/evidence/stress_judge_relay_<label>_summary.json (the copy is the evidence file).
Exit code: 0 = every round passed, 1 = at least one round failed, 2 = bad arguments or the test script is missing, 130 = interrupted.
"""
import argparse
import atexit
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TEST = HERE / "test_page_judge_relay.py"
MAX_LOAD_WORKERS = 3
LOG_BASE = ROOT / "logs_local" / "stress_judge_relay"
EVIDENCE = ROOT / "redteam" / "evidence"

# only the real result line of a failed assertion ("AssertionError: 2 != 1 : round 12 hash differs: {...}"); the traceback also prints the test's own source line
# `"round %s hash differs: %s" % ...`, which an unanchored pattern counted too (red team R1-8: the first summaries say 6 and 4, the real counts were 3 and 2)
SCENARIO_RE = re.compile(r"^SCENARIO_RECORD (\{.*\})\s*$", re.MULTILINE)   # one line per scenario the test really played (main window rule 2026-11-23: a pass counts only if the scenario happened)
HASH_RE = re.compile(r"^AssertionError:.*?round (\d+) hash differs: (\{.*\})\s*$", re.MULTILINE)
MARKERS = {
    "hash_differs": "hash differs",
    "relay_not_started": "relay did not start",
    "timeout": "timed out",
    "address_in_use": "Address already in use",
    "node_missing": "Node is not installed",
    "eperm": "EPERM",
}

_burners = []
_interrupted = False


def free_memory_percent():
    """System-wide free memory in percent from `memory_pressure` (macOS); None when the tool is not available."""
    try:
        out = subprocess.run(["memory_pressure"], capture_output=True, text=True, timeout=10).stdout
        for line in out.splitlines():
            if "free percentage" in line:
                return float(line.rsplit(":", 1)[1].strip().rstrip("%"))
    except Exception:
        return None
    return None


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def burner_main():
    x = 0
    while True:
        x = (x * 1103515245 + 12345) & 0x7FFFFFFF


def start_burners(count):
    for _ in range(count):
        p = subprocess.Popen([sys.executable, "-B", str(Path(__file__).resolve()), "--burner"],
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _burners.append(p)


def stop_burners():
    for p in _burners:
        try:
            p.terminate()
        except Exception:
            pass
    deadline = time.time() + 5
    for p in _burners:
        try:
            p.wait(max(0.1, deadline - time.time()))
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
    _burners.clear()


def on_signal(signum, _frame):
    global _interrupted
    _interrupted = True
    log("signal %s: finishing the current round, then stopping" % signum)


def classify(text, code):
    found = [k for k, v in MARKERS.items() if v in text]
    if code == 0:
        return []
    return found or ["other"]


def run_round(index, label_dir, timeout, tests):
    load_before = os.getloadavg()[0]
    started = time.time()
    log_path = label_dir / ("run_%02d.log" % index)
    try:
        proc = subprocess.run([sys.executable, "-B", str(TEST)] + tests, cwd=str(HERE), capture_output=True, text=True, timeout=timeout)
        code, out = proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired as exc:
        code = 124
        out = ((exc.stdout or b"").decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")) + \
              ((exc.stderr or b"").decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")) + "\nERROR round timed out after %ss\n" % timeout
    elapsed = time.time() - started
    log_path.write_text(out, encoding="utf-8")
    hashes = [{"round": m.group(1), "seats": m.group(2)[:300]} for m in HASH_RE.finditer(out)]
    scenario = []
    for match in SCENARIO_RE.finditer(out):
        try:
            scenario.append(json.loads(match.group(1)))
        except ValueError:
            pass
    tail = [ln for ln in out.splitlines() if ln.strip()][-3:]
    return {
        "round": index, "exit": code, "seconds": round(elapsed, 2),
        "load1_before": round(load_before, 2), "load1_after": round(os.getloadavg()[0], 2),
        "classes": classify(out, code), "hash_differs": hashes, "tail": tail, "log": str(log_path.relative_to(ROOT)),
        "skipped_tests": len(re.findall(r"skipped", out)),
        "scenario": scenario,
    }


def read_done(path):
    done = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    row = json.loads(line)
                    done[row["round"]] = row
                except Exception:
                    continue
    return done


def scenario_summary(rows):
    """How often the scenario really happened. Rounds without a SCENARIO_RECORD line are written as not recorded, never guessed."""
    recorded = [r for r in rows if r.get("scenario")]
    records = [rec for r in recorded for rec in r["scenario"]]
    fired = [rec for rec in records if rec.get("ultimate_fired")]
    hist = {"0": 0, "1": 0, "2+": 0}
    for rec in fired:
        victims = rec.get("victims")
        if victims is None:
            continue
        hist["0" if victims == 0 else "1" if victims == 1 else "2+"] += 1
    return {"rounds": len(rows), "rounds_with_record": len(recorded), "rounds_not_recorded": len(rows) - len(recorded), "records": len(records),
            "ultimate_fired": len(fired), "ultimate_not_fired": len(records) - len(fired), "victims_histogram": hist, "pierce_two_or_more": hist["2+"],
            "note": "victims = enemy units that lost hit points to the ultimate; rounds without a record are NOT counted as fired"}


def summarize(rows, args, label, load_workers, finished):
    passed = [r for r in rows if r["exit"] == 0]
    failed = [r for r in rows if r["exit"] != 0]
    classes = {}
    for r in failed:
        for c in r["classes"]:
            classes[c] = classes.get(c, 0) + 1
    secs = sorted(r["seconds"] for r in rows) or [0]
    return {
        "label": label, "rounds_requested": args.rounds, "rounds_done": len(rows), "passed": len(passed), "failed": len(failed),
        "failed_rounds": [r["round"] for r in failed], "failure_classes": classes,
        "hash_differs_total": sum(len(r["hash_differs"]) for r in rows),
        "load_workers": load_workers, "cpu_count": os.cpu_count(),
        "load1_before_avg": round(sum(r["load1_before"] for r in rows) / max(1, len(rows)), 2),
        "load1_after_avg": round(sum(r["load1_after"] for r in rows) / max(1, len(rows)), 2),
        "seconds_min": secs[0], "seconds_median": secs[len(secs) // 2], "seconds_max": secs[-1],
        "scenario_counts": scenario_summary(rows),
        "finished": finished, "tests": args.tests or "(whole file)", "hash_differs_note": "counts only real AssertionError result lines (fixed 2026-11-23, R1-8); summaries written before that counted traceback source lines as well, so idle 6 and load3 4 in the first N10 summaries were really 3 and 2", "result": "PASS" if finished and not failed and len(rows) >= args.rounds else "FAIL",
        "finished_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def main():
    if "--burner" in sys.argv:
        burner_main()
        return 0
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--rounds", type=int, default=30)
    ap.add_argument("--load-workers", type=int, default=0, help="busy-loop processes kept running during the rounds (0 = idle baseline)")
    ap.add_argument("--allow-heavy", action="store_true", help="allow more than %d load workers (owner approval needed)" % MAX_LOAD_WORKERS)
    ap.add_argument("--tests", default="", help="comma-separated unittest names to run in each round, e.g. PageJudgeRoomTest.test_3v3_ultimate_over_page_judge_relay,PageJudgeRoomTest.test_hag_ultimate_over_page_judge_relay (default: the whole file)")
    ap.add_argument("--label", default="", help="folder name; default idle or load<N>")
    ap.add_argument("--timeout", type=int, default=240, help="seconds per round")
    ap.add_argument("--resume", action="store_true", help="skip rounds already in rounds.jsonl of this label")
    ap.add_argument("--min-free-percent", type=float, default=0.0, help="stop before a round when the system's free memory is below this percent (0 = no check); exit 3")
    ap.add_argument("--stop-after-failures", type=int, default=0, help="stop early after this many failed rounds (0 = never)")
    args = ap.parse_args()
    if args.rounds < 1 or args.load_workers < 0 or args.timeout < 10:
        print("ERROR bad arguments", file=sys.stderr)
        return 2
    if args.load_workers > MAX_LOAD_WORKERS and not args.allow_heavy:
        print("ERROR --load-workers %d is above the cap %d (use --allow-heavy only with the owner's word)" % (args.load_workers, MAX_LOAD_WORKERS), file=sys.stderr)
        return 2
    if not TEST.exists():
        print("ERROR missing %s" % TEST, file=sys.stderr)
        return 2
    if shutil.which("node") is None:
        print("ERROR node not found on PATH (the test needs Node 22+)", file=sys.stderr)
        return 2
    tests = [t.strip() for t in args.tests.split(",") if t.strip()]
    label = args.label or ("idle" if args.load_workers == 0 else "load%d" % args.load_workers)
    label_dir = LOG_BASE / label
    label_dir.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    jsonl = label_dir / "rounds.jsonl"
    done = read_done(jsonl) if args.resume else {}
    if not args.resume and jsonl.exists():
        jsonl.rename(label_dir / ("rounds.%d.jsonl.old" % int(time.time())))
    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)
    atexit.register(stop_burners)
    log("stress %s: %d rounds, %d load workers on %s cpus, load1 now %.2f" % (label, args.rounds, args.load_workers, os.cpu_count(), os.getloadavg()[0]))
    if args.load_workers:
        start_burners(args.load_workers)
        time.sleep(2)
    rows = [done[k] for k in sorted(done)]
    failures = sum(1 for r in rows if r["exit"] != 0)
    finished = True
    memory_stop = []
    try:
        for i in range(1, args.rounds + 1):
            if i in done:
                continue
            if _interrupted:
                finished = False
                break
            if args.min_free_percent:
                free = free_memory_percent()
                if free is not None and free < args.min_free_percent:
                    log("ERROR free memory %.0f%% is below the limit %.0f%%: stopping before round %d" % (free, args.min_free_percent, i))
                    finished = False
                    memory_stop.append(free)
                    break
            row = run_round(i, label_dir, args.timeout, tests)
            rows.append(row)
            with jsonl.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            status = "OK" if row["exit"] == 0 else "FAIL " + ",".join(row["classes"])
            log("round %02d/%d %s %.1fs load1 %.2f->%.2f" % (i, args.rounds, status, row["seconds"], row["load1_before"], row["load1_after"]))
            if row["exit"] != 0:
                failures += 1
                for ln in row["tail"][-2:]:
                    log("   ERROR " + ln[:200])
                if args.stop_after_failures and failures >= args.stop_after_failures:
                    log("stopping early: %d failed rounds" % failures)
                    finished = False
                    break
    finally:
        stop_burners()
    rows.sort(key=lambda r: r["round"])
    summary = summarize(rows, args, label, args.load_workers, finished)
    (label_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    (EVIDENCE / ("stress_judge_relay_%s_summary.json" % label)).write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    log("RESULT %s passed %d/%d failed %d classes %s (summary: redteam/evidence/stress_judge_relay_%s_summary.json)" % (
        summary["result"], summary["passed"], summary["rounds_done"], summary["failed"], summary["failure_classes"] or "-", label))
    log("RESOURCE_RELEASED burners=%d" % len(_burners))
    if memory_stop:
        return 3
    if _interrupted:
        return 130
    return 0 if summary["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
