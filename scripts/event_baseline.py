#!/usr/bin/env python3
"""Event baseline: what events appear and what events never appear (owner 2026-11-23: "take the fixed build as the standard front-end and back-end simulation data; an event that does not show up is recorded as a gap").

Modes
  --build    read the full-scale front-end audit (redteam/evidence/audit_page_events_*_merged.json, 20,000 page matches) and write the baseline
             docs/event_baseline_20261123.json (per event: fired count and per-match rate; the never-fired list) plus the gap list docs/event_gaps_20261123.md.
  --compare  NEW.json   compare another merged audit (same format) with the baseline per match: an event that fired in the baseline and now never fires is a FAIL (exit 1);
             a rate that moved by more than --tolerance (default 0.25) for an event with at least --min-count (default 1000) baseline firings is a WARN; an event that never fired
             in the baseline and fires now is a NOTE (the gap closed). Exit 0 when there is no FAIL, 1 on FAIL, 2 on a usage or input error.
  --selftest prove the comparison catches a vanished event, a shifted rate and a closed gap on a mutated copy of the baseline (no files written).
Log: logs_local/event_baseline.log (appended). A failure prints a line that starts with ERROR.
Back end: the engine side has no per-event tally yet (scripts/sim_team_headless.py records checks, not events); that is written down as gap EB-BACK in the gap list, not guessed.
"""
import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SOURCE = os.path.join(ROOT, "redteam", "evidence", "audit_page_events_20261122_full_after_fix_merged.json")
BASELINE = os.path.join(ROOT, "docs", "event_baseline_20261123.json")
GAPS_MD = os.path.join(ROOT, "docs", "event_gaps_20261123.md")
GRAPH = os.path.join(ROOT, "docs", "role_event_graph_20261123.json")
LOG = os.path.join(ROOT, "logs_local", "event_baseline.log")

# Why an event never fires in computer-versus-computer matches. Source: the closing inventory gap N8 (docs/GAP_QUEUE_OPEN_20261122.md) and index.html call sites.
UI_PATH = {
    "ui_click": "human UI path (button press)",
    "ui_hover": "human UI path (pointer over a control)",
    "charge": "human charge swell while the pointer is held",
    "coin_flip": "human coin toss on the start of a match",
    "shield_place": "human placing of the shield",
    "ultimate_ready": "human HUD, raised when the energy marks reach three for the human seat",
    "low_hp_heartbeat": "human HUD, low hit points of the human unit",
    "round_end": "human UI round banner",
    "flight_spear": "flight loop started from the human throw path",
    "flight_shuriken": "flight loop started from the human throw path",
    "flight_cannon": "flight loop started from the human throw path",
    "flight_shield": "flight loop started from the human throw path",
}


def say(text):
    line = "%s %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), text)
    print(line)
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError as error:
        print("ERROR cannot write the log: %s" % error)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_audit(path):
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    totals = data["totals"]
    matches = int(totals["matches"])
    if matches <= 0:
        raise ValueError("no matches in %s" % path)
    events = {}
    for entry in data["events"]:
        events[entry["event"]] = {"fired": int(entry["fired"]), "referenced": bool(entry.get("referenced", True))}
    return {"matches": matches, "errors": int(totals.get("errors", 0)), "events": events}


def git_head():
    try:
        return subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return "unknown"


def build():
    audit = load_audit(SOURCE)
    if audit["errors"] != 0:
        say("ERROR the source audit has %d errors; a baseline must come from a clean run" % audit["errors"])
        return 1
    per_match = {}
    never = []
    for name, entry in sorted(audit["events"].items()):
        per_match[name] = {"fired": entry["fired"], "per_match": round(entry["fired"] / float(audit["matches"]), 6)}
        if entry["fired"] == 0:
            never.append(name)
    baseline = {
        "built": datetime.date.today().isoformat(),
        "tree_head_when_built": git_head(),
        "source": os.path.relpath(SOURCE, ROOT),
        "source_sha256": sha256(SOURCE),
        "note": "front end only: 20,000 computer-versus-computer page matches on the build after the hp-residue and skill-leak fixes (gap N7); the back end has no per-event tally yet (gap EB-BACK)",
        "matches": audit["matches"],
        "events": per_match,
        "never_fired": never,
    }
    with open(BASELINE, "w", encoding="utf-8") as handle:
        json.dump(baseline, handle, indent=1, sort_keys=True)
        handle.write("\n")
    gaps = []
    for name in never:
        gaps.append((name, UI_PATH.get(name, "UNCLASSIFIED: never fired and not on the known human-UI list; needs a look")))
    unclassified = [g for g in gaps if g[1].startswith("UNCLASSIFIED")]
    if os.path.exists(GRAPH):
        with open(GRAPH, encoding="utf-8") as handle:
            graph = json.load(handle)
        scenario_missing = [e for e in graph.get("eventsNotFiredInTheScenarios", []) if audit["events"].get(e, {}).get("fired", 0) > 0]
        graph_note = scenario_missing
        status_gaps = graph.get("gaps", [])
    else:
        scenario_missing, status_gaps = [], []
    lines = [
        "# Event gaps from the baseline (2026-11-23)",
        "",
        "Baseline: `docs/event_baseline_20261123.json`, built by `python3 -B scripts/event_baseline.py --build` from `%s` (%d page matches, source sha256 `%s`)." % (baseline["source"], audit["matches"], baseline["source_sha256"][:16]),
        "Rule (owner 2026-11-23): an event that does not show up is a gap. Compare a later run with `python3 -B scripts/event_baseline.py --compare <merged audit json>`.",
        "",
        "## A. Events that never fired in 20,000 matches (%d of %d)" % (len(never), len(audit["events"])),
        "| # | Event | Why it does not fire in computer-versus-computer matches | Gap |",
        "|---|---|---|---|",
    ]
    for index, (name, why) in enumerate(gaps, 1):
        lines.append("| EB-%02d | `%s` | %s | wired in the page, not exercised by a scripted run (N8) |" % (index, name, why) if not why.startswith("UNCLASSIFIED") else "| EB-%02d | `%s` | %s | NEW |" % (index, name, why))
    lines += [
        "",
        "## B. Events that fire in the 20,000 matches but not in the role graph scenarios (%d)" % len(scenario_missing),
        "These are not event gaps; the role graph (`docs/role_event_graph_20261123.html`) did not drive them. List: %s." % ", ".join("`%s`" % e for e in scenario_missing),
        "",
        "## C. Status and sound gaps measured in the role graph (gap N9)",
    ]
    for gap in status_gaps:
        lines.append("- %s: %s (%s)" % (gap.get("kind"), gap.get("detail"), gap.get("role")))
    lines += [
        "",
        "## D. Back end",
        "- EB-BACK: the engine simulation (`scripts/sim_team_headless.py`) counts rule checks, not events, so there is no engine-side event baseline. Needed: a tally of engine events (throw outcomes: hit, ground, wall, shield block, ultimate kinds, each status applied and expired, KO, round end) per hero and team size, from a fresh run (heavy: needs the resource assessment table and the owner's word first). Until then the back-end comparison is the golden hashes and the 20,001-match checks only.",
        "",
        "Unclassified events: %d." % len(unclassified),
    ]
    with open(GAPS_MD, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    say("built %s: %d events, %d never fired, %d unclassified; gaps in %s" % (os.path.relpath(BASELINE, ROOT), len(audit["events"]), len(never), len(unclassified), os.path.relpath(GAPS_MD, ROOT)))
    return 0


def compare_data(base, new, tolerance, min_count):
    fails, warns, notes = [], [], []
    base_matches = float(base["matches"])
    new_matches = float(new["matches"])
    for name, entry in sorted(base["events"].items()):
        now = new["events"].get(name)
        if now is None:
            fails.append("%s: present in the baseline, missing from the new audit" % name)
            continue
        base_rate = entry["fired"] / base_matches
        new_rate = now["fired"] / new_matches
        if entry["fired"] > 0 and now["fired"] == 0:
            fails.append("%s: fired %d times in the baseline, never fires now" % (name, entry["fired"]))
        elif entry["fired"] == 0 and now["fired"] > 0:
            notes.append("%s: never fired in the baseline, fires now (%d): the gap closed" % (name, now["fired"]))
        elif entry["fired"] >= min_count and base_rate > 0 and abs(new_rate - base_rate) / base_rate > tolerance:
            warns.append("%s: per-match rate %.4f -> %.4f (%.0f percent)" % (name, base_rate, new_rate, 100.0 * (new_rate - base_rate) / base_rate))
    for name in sorted(set(new["events"]) - set(base["events"])):
        notes.append("%s: not in the baseline (new event)" % name)
    return fails, warns, notes


def compare(path, tolerance, min_count):
    try:
        with open(BASELINE, encoding="utf-8") as handle:
            base = json.load(handle)
        new = load_audit(path)
    except (OSError, ValueError, KeyError) as error:
        say("ERROR cannot compare: %s" % error)
        return 2
    new_view = {"matches": new["matches"], "events": new["events"]}
    fails, warns, notes = compare_data(base, new_view, tolerance, min_count)
    for line in fails:
        say("ERROR FAIL " + line)
    for line in warns:
        say("WARN " + line)
    for line in notes:
        say("NOTE " + line)
    say("compare %s with the baseline: %d FAIL, %d WARN, %d NOTE" % (os.path.basename(path), len(fails), len(warns), len(notes)))
    return 1 if fails else 0


def selftest():
    with open(BASELINE, encoding="utf-8") as handle:
        base = json.load(handle)
    fired = [n for n, e in base["events"].items() if e["fired"] >= 1000]
    never = base["never_fired"]
    if len(fired) < 2 or not never:
        print("ERROR selftest needs at least two common events and one never-fired event in the baseline")
        return 1
    mutated = json.loads(json.dumps(base))
    mutated["events"][fired[0]]["fired"] = 0
    mutated["events"][fired[1]]["fired"] = int(mutated["events"][fired[1]]["fired"] * 2)
    mutated["events"][never[0]]["fired"] = 5
    fails, warns, notes = compare_data(base, mutated, 0.25, 1000)
    ok = (len(fails) == 1 and fired[0] in fails[0]) and (len(warns) == 1 and fired[1] in warns[0]) and any(never[0] in n for n in notes)
    identical = compare_data(base, json.loads(json.dumps(base)), 0.25, 1000)
    ok = ok and not identical[0] and not identical[1] and not identical[2]
    print("selftest %s: vanished event -> %d FAIL, doubled rate -> %d WARN, closed gap -> %d NOTE, identical copy -> clean" % ("OK" if ok else "FAILED", len(fails), len(warns), len(notes)))
    return 0 if ok else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--compare", metavar="NEW_JSON")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--tolerance", type=float, default=0.25)
    parser.add_argument("--min-count", type=int, default=1000)
    args = parser.parse_args()
    chosen = sum(1 for flag in (args.build, bool(args.compare), args.selftest) if flag)
    if chosen != 1:
        parser.print_usage(sys.stderr)
        return 2
    try:
        if args.build:
            return build()
        if args.compare:
            return compare(args.compare, args.tolerance, args.min_count)
        return selftest()
    except Exception as error:
        say("ERROR unexpected: %s: %s" % (type(error).__name__, error))
        return 2


if __name__ == "__main__":
    sys.exit(main())
