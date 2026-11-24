#!/usr/bin/env python3
"""Read-only diagnosis of gap N10: the 3v3 ultimate room test sometimes ends with `round N hash differs` between red-1 and white-1.

It repeats the scenario of `scripts/test_page_judge_relay.py::test_3v3_ultimate_over_page_judge_relay` one run at a time (no parallel runs), but starts the two
page seats through diagnostic copies (`scripts/diag_page_judge_seat.js`, `scripts/diag_headless_seat.js`) that record every input given to the round hash.
When a run ends with differing hashes it writes `redteam/evidence/n10_desync_<label>_run<NN>.json` with: the round, the unit fields that differ between the two seats'
hash inputs (x, y, hp, alive, statuses, wall hp), how often each seat hashed that round, and the relay's ordered message log around the round. Nothing in the page,
the bridge or the relay is changed; the test file is only imported.

Needs localhost sockets and Node 22+ (run in a normal terminal, not the Claude sandbox):
    python3 -B scripts/diag_judge_relay_desync.py --max-runs 40 --stop-after 3
Per run line goes to logs_local/diag_n10/<label>/runs.jsonl. Exit code: 0 = no failure in the runs, 1 = at least one failure captured, 2 = setup problem.
"""
import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import mcp_stdio_server as srv  # noqa: E402
import test_page_judge_relay as T  # noqa: E402

EVIDENCE = ROOT / "redteam" / "evidence"
LOG_BASE = ROOT / "logs_local" / "diag_n10"


class DiagPageJudgeRelay(srv.PageJudgeRelay):
    """Same bridge, but its page seat is the diagnostic copy that records the hash inputs."""

    def start(self):
        session = self.session
        session.weather_enabled = True
        session.sync = {"status": "pending", "round": session.engine.round_num}
        own = session.engine.hero_red if self.seat == "red" else session.engine.hero_white
        heroes = list(own) if isinstance(own, (list, tuple)) else [own]
        command = [self.node, str(HERE / "diag_page_judge_seat.js"), "--relay", self.url.rsplit("/ws", 1)[0], "--code", self.code, "--team", self.seat,
                   "--heroes", ",".join(heroes), "--rng", str(self.rng), "--speed", str(self.speed)]
        self.proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1, cwd=str(ROOT))
        import threading
        self.thread = threading.Thread(target=self._read, name="pk-page-judge", daemon=True)
        self.thread.start()


class DiagRoomTest(T.PageJudgeRoomTest):
    captured = {}

    def start_pair(self):
        url = "ws://127.0.0.1:%d" % self.port
        red = ["bride", "hunchback", "reaper"]
        white = ["hag", "skeleton", "wizard"]
        self.procs.append(subprocess.Popen(["node", str(HERE / "diag_headless_seat.js"), "--relay", url, "--code", self.code, "--team", "white", "--heroes", ",".join(white),
                                            "--level", "normal", "--rng", "5", "--speed", "8", "--max-s", "120"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=str(ROOT)))
        session = srv.Session(seed=1, units=3, seat="red", hero_red=red, hero_white=white, turn_seconds=3600, human_turn_seconds=3600)
        self.bridge = DiagPageJudgeRelay(session, url + "/ws", self.code, "red", speed=8.0, rng=7)
        self.server = srv.McpServer(session)
        self.server.relay = self.bridge
        self.session = session
        self.bridge.start()
        T.wait_for(lambda: self.bridge.started, "the bridge's page did not see the room start")
        time.sleep(0.5)

    def tearDown(self):
        try:
            room = self.host.relay.rooms[self.code]
            time.sleep(0.4)   # one more probe write
            DiagRoomTest.captured = {"log": [dict(m) for m in room.log], "round_hashes": {str(k): dict(v) for k, v in room.round_hashes.items()}}
        except Exception as exc:  # diagnostics only
            DiagRoomTest.captured = {"error": str(exc)}
        super().tearDown()


def load_probe(dump_dir):
    seats = {}
    for name in ("red-bridge-page", "white-headless"):
        path = dump_dir / (name + ".json")
        try:
            seats[name] = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            seats[name] = None
    return seats


def unit_rows(state):
    rows = {}
    for u in state.get("units", []):
        rows[u["id"]] = {"x": u.get("x"), "y": u.get("y"), "hp": u.get("hp"), "alive": u.get("alive"), "statuses": sorted(u.get("statuses") or [])}
    return rows


def diff_round(seats, number):
    result = {"round": number, "calls": {}, "differences": [], "note": ""}
    picked = {}
    for name, data in seats.items():
        if not data:
            result["note"] += "%s: no probe file; " % name
            continue
        entries = [e for e in data["inputs"] if e.get("state", {}).get("round") == number]
        result["calls"][name] = [e["hash"] for e in entries]
        if entries:
            picked[name] = entries[-1]["state"]
    if len(picked) < 2:
        result["note"] += "inputs for the round missing on one seat"
        return result
    a, b = picked["red-bridge-page"], picked["white-headless"]
    if a.get("wallHp") != b.get("wallHp"):
        result["differences"].append({"field": "wallHp", "red-bridge-page": a.get("wallHp"), "white-headless": b.get("wallHp")})
    ra, rb = unit_rows(a), unit_rows(b)
    for uid in sorted(set(ra) | set(rb)):
        for field in ("x", "y", "hp", "alive", "statuses"):
            va = ra.get(uid, {}).get(field, "<absent>")
            vb = rb.get(uid, {}).get(field, "<absent>")
            if va != vb:
                result["differences"].append({"unit": uid, "field": field, "red-bridge-page": va, "white-headless": vb})
    for key in ("phase", "seed", "teamSize"):
        if a.get(key) != b.get(key):
            result["differences"].append({"field": key, "red-bridge-page": a.get(key), "white-headless": b.get(key)})
    return result


def compact_log(log, number):
    rows = []
    for m in log:
        r = m.get("round")
        if r in (number - 1, number) or m.get("type") in ("out_of_sync",):
            rows.append({k: m[k] for k in ("seq", "type", "seat_id", "unit", "round", "phase", "next_phase", "kind", "hit", "hp_after", "ref", "angle", "power", "ultimate") if k in m})
    return rows


def one_run(index, label_dir, label):
    dump_dir = label_dir / ("run_%02d" % index)
    if dump_dir.exists():
        shutil.rmtree(dump_dir)
    dump_dir.mkdir(parents=True)
    os.environ["PK_DIAG_DIR"] = str(dump_dir)
    DiagRoomTest.captured = {}
    suite = unittest.TestSuite([DiagRoomTest("test_3v3_ultimate_over_page_judge_relay")])
    stream = io.StringIO()
    started = time.time()
    result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
    elapsed = round(time.time() - started, 1)
    text = stream.getvalue()
    (dump_dir / "unittest.txt").write_text(text, encoding="utf-8")
    row = {"run": index, "ok": result.wasSuccessful(), "seconds": elapsed, "load1": round(os.getloadavg()[0], 2), "rounds_hashed": sorted(int(k) for k in DiagRoomTest.captured.get("round_hashes", {}))}
    if result.wasSuccessful():
        return row, None
    differing = sorted(int(k) for k, v in DiagRoomTest.captured.get("round_hashes", {}).items() if len(set(v.values())) > 1)
    row["failure"] = "hash_differs" if differing else "other"
    row["differing_rounds"] = differing
    row["tail"] = [ln for ln in text.splitlines() if ln.strip()][-3:]
    if not differing:
        return row, None
    seats = load_probe(dump_dir)
    detail = {"label": label, "run": index, "head": subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip(),
              "relay_round_hashes": DiagRoomTest.captured.get("round_hashes"), "rounds": []}
    for number in differing:
        d = diff_round(seats, number)
        d["relay_log_rounds_n_minus_1_and_n"] = compact_log(DiagRoomTest.captured.get("log", []), number)
        detail["rounds"].append(d)
    detail["full_relay_log"] = DiagRoomTest.captured.get("log", [])
    detail["probe_status"] = {k: (v or {}).get("status") for k, v in seats.items()}
    out = EVIDENCE / ("n10_desync_%s_run%02d.json" % (label, index))
    out.write_text(json.dumps(detail, indent=1, ensure_ascii=False), encoding="utf-8")
    row["evidence"] = str(out.relative_to(ROOT))
    row["differences"] = [d["differences"] for d in detail["rounds"]]
    return row, detail


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--max-runs", type=int, default=40)
    ap.add_argument("--stop-after", type=int, default=3, help="stop after this many failed runs")
    ap.add_argument("--label", default="a")
    args = ap.parse_args()
    if args.max_runs < 1 or args.stop_after < 1:
        print("ERROR bad arguments", file=sys.stderr)
        return 2
    if shutil.which("node") is None:
        print("ERROR node not found", file=sys.stderr)
        return 2
    label_dir = LOG_BASE / args.label
    label_dir.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    jsonl = label_dir / "runs.jsonl"
    failures = 0
    setup_errors = 0
    for i in range(1, args.max_runs + 1):
        try:
            row, _ = one_run(i, label_dir, args.label)
        except Exception as exc:
            print("ERROR run %d setup: %s" % (i, exc), flush=True)
            setup_errors += 1
            if setup_errors >= 2:
                return 2
            continue
        with jsonl.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(time.strftime("%H:%M:%S"), "run %02d/%d %s %.1fs load1 %.2f%s" % (i, args.max_runs, "OK" if row["ok"] else "FAIL " + row.get("failure", "?"), row["seconds"], row["load1"],
              "" if row["ok"] else " rounds %s -> %s" % (row.get("differing_rounds"), row.get("evidence", "no evidence")) ), flush=True)
        if not row["ok"]:
            failures += 1
            for diffs in row.get("differences", []):
                for d in diffs:
                    print("   DIFF", json.dumps(d, ensure_ascii=False), flush=True)
            if failures >= args.stop_after:
                break
    print("RESULT failures %d in runs done; RESOURCE_RELEASED" % failures, flush=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
