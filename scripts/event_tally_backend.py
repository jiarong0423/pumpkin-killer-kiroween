#!/usr/bin/env python3
"""Back-end event tally (gap EB-BACK): which game events the rules engine produces, how often, per hero and per team size, and which never appear.

The engine (scripts/mcp_game_server.py through scripts/mcp_stdio_server.py Session) is driven without sockets by a bot that mixes plain throws, heavy and double
skills, heal, moves, the knight's shield and wall and every hero's ultimate (scripts/sim_team_headless.py supplies the aiming). It changes no engine behaviour:
every tool call goes through a wrapper that takes a snapshot of the match before and after and turns the difference into events (a status appeared, a status expired,
a unit died, the round counter moved, the wall broke, a throw landed as hero / ground / wall / shield ...). The result has the same shape as the front-end baseline
(docs/event_baseline_20261123.json): per event `fired` and `per_match`, a `never_fired` list, plus `by_hero` and `by_size` breakdowns.

Modes
  --run         play the matches (default 1000 per team size 1, 2, 3), in chunks of --chunk matches that are saved and can be resumed (--resume), merge them and write
                the result (--out, default redteam/evidence/event_tally_backend_<label>.json)
  --compare NEW.json [--baseline FILE]   compare a result with a baseline (default docs/event_baseline_backend_20261123.json): an event that fired in the baseline and
                now never fires is FAIL (exit 1); a per-match rate that moved by more than --tolerance (0.25) for an event with at least --min-count (1000) baseline
                firings is WARN; an event that never fired in the baseline and fires now is NOTE
  --selftest    prove the comparison catches a vanished event, a shifted rate and a closed gap on a mutated copy (no files written)
Log: logs_local/event_tally_backend.log (appended). A failure prints a line that starts with ERROR. Exit 0 = done / no FAIL, 1 = engine exception or FAIL, 2 = usage.
Heavy runs (thousands of matches) need the resource assessment first (resource-run-gate); a small run (--matches-per-size 20) takes seconds.
"""
import argparse
import datetime
import json
import os
import random
import subprocess
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
os.environ.setdefault("PK_SIM_LOG", os.path.join(ROOT, "logs_local", "event_tally_backend_sim.log"))
LOG = os.path.join(ROOT, "logs_local", "event_tally_backend.log")
CHUNK_DIR = os.path.join(ROOT, "logs_local", "event_tally_backend")
BASELINE = os.path.join(ROOT, "docs", "event_baseline_backend_20261123.json")
SEED_BASE = 20262000
MAX_ROUNDS = 150
STATUS_NAMES = ("bleed", "poison", "burn", "weak", "slow", "stun")
TICK_STATUSES = ("bleed", "poison", "burn")


def say(text):
    line = "%s %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), text)
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError as error:
        print("ERROR cannot write the log: %s" % error)


def git_head():
    try:
        return subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return "unknown"


class Tally:
    """Counts: events[name] total, by_hero[name][hero], by_size[name][size]; plus rejected tool calls."""

    def __init__(self):
        self.events = {}
        self.by_hero = {}
        self.by_size = {}
        self.rejected = {}
        self.matches = {}
        self.exceptions = []
        self.pending_kind = {}   # unit id -> heavy / double / plain of its submitted throw until the round resolves

    def add(self, name, hero=None, size=None, n=1):
        self.events[name] = self.events.get(name, 0) + n
        if hero is not None:
            row = self.by_hero.setdefault(name, {})
            row[hero] = row.get(hero, 0) + n
        if size is not None:
            row = self.by_size.setdefault(name, {})
            row[str(size)] = row.get(str(size), 0) + n

    def to_dict(self):
        return {"events": self.events, "by_hero": self.by_hero, "by_size": self.by_size, "rejected": self.rejected, "matches": self.matches, "exceptions": self.exceptions}

    def merge(self, other):
        for name, count in other["events"].items():
            self.events[name] = self.events.get(name, 0) + count
        for name, row in other["by_hero"].items():
            target = self.by_hero.setdefault(name, {})
            for key, count in row.items():
                target[key] = target.get(key, 0) + count
        for name, row in other["by_size"].items():
            target = self.by_size.setdefault(name, {})
            for key, count in row.items():
                target[key] = target.get(key, 0) + count
        for name, count in other["rejected"].items():
            self.rejected[name] = self.rejected.get(name, 0) + count
        for key, count in other["matches"].items():
            self.matches[key] = self.matches.get(key, 0) + count
        self.exceptions.extend(other["exceptions"])


def snapshot(session):
    eng = session.engine
    return {
        "round": eng.round_num,
        "winner": session.winner,
        "reason": session.winner_reason,
        "units": {uid: {"hero": u["hero"], "team": u["team"], "alive": bool(u["alive"]), "hp": float(u["hp"]),
                        "statuses": {k: v for k, v in u.get("statuses", {}).items() if v}} for uid, u in eng.units.items()},
        "wall": float(eng.central_wall_hp),
        "shield": {team: bool(eng.shields[team]["active"]) for team in ("red", "white")},
        "energy": dict(session.energy),
        "knight_wall": {team: bool(eng.knight_walls[team]) for team in ("red", "white")},
        "log": len(eng.throw_log),
        "skipped": sorted(session.skipped_units),
        "heals": dict(session.skills_remaining.get("red", {})),
    }


def diff_events(tally, session, before, after, size, call_name, args):
    eng = session.engine
    # throws that landed during this call (they resolve when the round resolves, so usually in the end_turn of the second team)
    for record in eng.throw_log[before["log"]:after["log"]]:
        unit_id = record.get("unit")
        unit = eng.units.get(unit_id)
        hero = unit["hero"] if unit else None
        kind = tally.pending_kind.pop(unit_id, "plain")
        hit_type = str(record.get("hit_type"))
        tally.add("throw.total", hero, size)
        tally.add("throw.result." + hit_type, hero, size)
        if record.get("ultimate"):
            tally.add("throw.kind.ultimate", hero, size)
            tally.add("ultimate.used", hero, size)
        else:
            tally.add("throw.kind." + (kind if kind in ("heavy", "double") else "plain"), hero, size)
        if record.get("critical"):
            tally.add("throw.critical", hero, size)
        if record.get("near_miss"):
            tally.add("throw.near_miss", hero, size)   # team matches only: a ground landing near an enemy still hurts it
        if record.get("knockback"):
            tally.add("throw.knockback", hero, size)
        if record.get("damage_dealt", 0) > 0:
            tally.add("throw.damage", hero, size)
        for word in record.get("statuses") or []:
            tally.add("throw.status_carried." + str(word).split(":")[0], hero, size)
        if hit_type == "central_wall":
            tally.add("wall.hit", hero, size)
    # state differences
    for uid, now in after["units"].items():
        old = before["units"].get(uid)
        if old is None:
            continue
        hero = now["hero"]
        if old["alive"] and not now["alive"]:
            tally.add("unit.ko", hero, size)
        for name in STATUS_NAMES:
            had, has = bool(old["statuses"].get(name)), bool(now["statuses"].get(name))
            if has and not had:
                tally.add("status.applied." + name, hero, size)
            if had and not has:
                tally.add("status.expired." + name, hero, size)
        # damage that no throw of this call explains: a damage-over-time tick at a phase boundary
        if now["hp"] < old["hp"] - 1e-9 and after["log"] == before["log"]:
            for name in TICK_STATUSES:
                if old["statuses"].get(name):
                    tally.add("status.tick_damage." + name, hero, size)
        if now["hp"] > old["hp"] + 1e-9 and call_name == "submit_action" and isinstance(args, dict) and args.get("action", {}).get("skill") == "heal":
            tally.add("skill.heal", hero, size)
    if after["wall"] <= 0 < before["wall"]:
        tally.add("wall.broken", None, size)
    for team in ("red", "white"):
        if after["shield"][team] and not before["shield"][team]:
            tally.add("shield.placed", None, size)
        if before["shield"][team] and not after["shield"][team]:
            tally.add("shield.expired", None, size)
        if after["knight_wall"][team] and not before["knight_wall"][team]:
            tally.add("knight_wall.set", None, size)
        if before["knight_wall"][team] and not after["knight_wall"][team]:
            tally.add("knight_wall.used_up", None, size)
        if after["energy"][team] >= 3 > before["energy"][team]:
            tally.add("energy.ultimate_ready", None, size)
        if after["energy"][team] > before["energy"][team]:
            tally.add("energy.gained", None, size)
    if after["round"] > before["round"]:
        tally.add("round.end", None, size)
    if before["winner"] is None and after["winner"] is not None:
        tally.add("match.end." + str(after["reason"] or "ko"), None, size)
        tally.add("match.winner." + str(after["winner"]), None, size)
    for uid in after["skipped"]:
        if uid not in before["skipped"]:
            tally.add("turn.skipped", after["units"][uid]["hero"] if uid in after["units"] else None, size)
    if call_name == "submit_action" and isinstance(args, dict):
        atype = args.get("action", {}).get("type")
        if atype == "move":
            unit = after["units"].get(args.get("unit"))
            tally.add("action.move", unit["hero"] if unit else None, size)
        elif atype == "defend":
            tally.add("action.defend", "knight", size)
        elif atype == "ultimate" and after["knight_wall"] != before["knight_wall"]:
            tally.add("ultimate.used", "knight", size)


def play_match(sim, server, tally, size, seed):
    rng = random.Random(seed * 7919 + size)
    act = random.Random(seed * 104729 + size)
    heroes_red = [rng.choice(sim.HERO_IDS) for _ in range(size)]
    heroes_white = [rng.choice(sim.HERO_IDS) for _ in range(size)]
    session = server.Session(seed=seed, units=size, hero_red=heroes_red, hero_white=heroes_white, clock=lambda: 0.0, human_turn_seconds=0, turn_seconds=100)
    eng = session.engine
    rosters = {team: sorted(uid for uid in eng.units if eng.units[uid]["team"] == team) for team in ("red", "white")}
    seat_of = {"red": "red", "white": "white"}
    phase_of = {"red": "human", "white": "agent"}
    cap = sim.tuning.round_cap(size)
    wild = act.random() < 0.08
    tally.matches[str(size)] = tally.matches.get(str(size), 0) + 1

    def call(name, args, team):
        before = snapshot(session)
        try:
            result = session.call(name, args, session.seats[seat_of[team]])
        except server.ToolError as error:
            key = "%s:%s" % (name, (args.get("action") or {}).get("type") if isinstance(args, dict) and isinstance(args.get("action"), dict) else "-")
            tally.rejected[key] = tally.rejected.get(key, 0) + 1
            raise
        if name == "submit_action" and isinstance(args, dict) and isinstance(args.get("action"), dict):
            action = args["action"]
            if action.get("type") == "skill" and action.get("skill") in ("heavy", "double"):
                tally.pending_kind[args.get("unit")] = action["skill"]
            elif action.get("type") in ("throw", "ultimate"):
                tally.pending_kind[args.get("unit")] = "plain"
        diff_events(tally, session, before, snapshot(session), size, name, args)
        return result

    guard = 0
    while session.winner is None:
        guard += 1
        if guard > MAX_ROUNDS or eng.round_num > MAX_ROUNDS:
            tally.exceptions.append("size=%d seed=%d: guard hit at round %d" % (size, seed, eng.round_num))
            return
        rnd = eng.round_num
        for team in ("red", "white"):
            if session.phase == "over":
                break
            active = session._active_unit(team)
            if active is None:
                continue
            unit = eng.units[active]
            skipped = active in session.skipped_units
            if not skipped:
                hero = unit["hero"]
                # optional pre-actions that do not end the turn: knight wall, move, heal
                if hero == "knight" and session.energy[team] >= 3 and session.ultimates_used[team] < 2 and act.random() < 0.8:
                    points = [{"x": round(act.uniform(500, 1500), 1), "y": round(act.uniform(200, 800), 1)} for _ in range(3)]
                    try:
                        call("submit_action", {"unit": active, "round": rnd, "action": {"type": "ultimate", "points": points}}, team)
                    except server.ToolError:
                        pass
                if act.random() < 0.30:
                    try:
                        call("submit_action", {"unit": active, "round": rnd, "action": {"type": "move", "direction": act.choice(("forward", "backward"))}}, team)
                    except server.ToolError:
                        pass
                if session.skills_remaining[team].get("heal", 0) > 0 and unit["hp"] < unit["max_hp"] * 0.6 and act.random() < 0.5:
                    try:
                        call("submit_action", {"unit": active, "round": rnd, "action": {"type": "skill", "skill": "heal"}}, team)
                    except server.ToolError:
                        pass
                angle, power, _target = sim.aim(rng, eng, unit, 60.0 if wild else act.choice((None, None, 5.0, 9.0)))   # sloppy aim now and then; about 8 percent of matches are wild (power error 60) so that some reach the round cap
                done = False
                roll = act.random()
                if hero == "knight" and roll < 0.30:
                    paths = list(session.remembered_paths(team))
                    if len(paths) >= 2:
                        try:
                            call("submit_action", {"unit": active, "round": rnd, "action": {"type": "defend", "path1": paths[0], "path2": paths[1]}}, team)
                            done = True
                        except server.ToolError:
                            pass
                if not done and session.energy[team] >= 3 and session.ultimates_used[team] < 2 and hero != "knight" and act.random() < 0.85:
                    try:
                        call("submit_action", {"unit": active, "round": rnd, "action": {"type": "ultimate", "angle": angle, "power": power}}, team)
                        done = True
                    except server.ToolError:
                        pass
                if not done and roll < 0.55:
                    skill = act.choice(("heavy", "double"))
                    if session.skills_remaining[team].get(skill, 0) > 0:
                        try:
                            call("submit_action", {"unit": active, "round": rnd, "action": {"type": "skill", "skill": skill, "angle": angle, "power": power}}, team)
                            done = True
                        except server.ToolError:
                            pass
                if not done:
                    try:
                        call("submit_action", {"unit": active, "round": rnd, "action": {"type": "throw", "angle": angle, "power": power}}, team)
                    except server.ToolError:
                        pass
            call("end_turn", {"round": rnd, "phase": phase_of[team]}, team)
    tally.add("match.rounds", None, size, n=eng.round_num - 1)


# Everything this tally can produce, so that a never-seen event is a visible gap and not an unknown. Hero-specific rows are checked in by_hero.
EXPECTED_EVENTS = (
    ["throw.total", "throw.damage", "throw.critical", "throw.knockback", "throw.kind.plain", "throw.kind.heavy", "throw.kind.double", "throw.kind.ultimate",
     "throw.result.hero", "throw.result.ground", "throw.result.central_wall", "throw.result.shield_blocked", "throw.result.ultimate_blocked",
     "ultimate.used", "skill.heal", "action.move", "action.defend", "shield.placed", "shield.expired", "knight_wall.set", "knight_wall.used_up",
     "wall.hit", "wall.broken", "unit.ko", "round.end", "energy.gained", "energy.ultimate_ready", "turn.skipped",
     "match.end.ko", "match.end.round_cap", "match.winner.red", "match.winner.white"]
    + ["status.applied." + n for n in STATUS_NAMES] + ["status.expired." + n for n in STATUS_NAMES] + ["status.tick_damage." + n for n in TICK_STATUSES]
)
HERO_EVENTS = ("throw.total", "ultimate.used", "unit.ko")
# Events the engine can produce but that are switched off on purpose; they are listed, not counted as gaps.
DISABLED_BY_DESIGN = {"throw.near_miss": "owner decision: near-miss compensation is completely off (shared/comeback.json near_miss.enabled false); the field exists but never fires"}


def chunk_path(label, size, index):
    return os.path.join(CHUNK_DIR, label, "chunk_%d_%04d.json" % (size, index))


def run(args):
    import importlib
    sim = importlib.import_module("sim_team_headless")
    server = sim.server
    os.makedirs(os.path.join(CHUNK_DIR, args.label), exist_ok=True)
    started = time.time()
    total = Tally()
    sizes = [int(s) for s in args.sizes.split(",")]
    say("event_tally_backend: label %s, %d matches per size, sizes %s, chunk %d, resume %s, head %s" % (args.label, args.matches_per_size, sizes, args.chunk, args.resume, git_head()))
    for size in sizes:
        chunks = (args.matches_per_size + args.chunk - 1) // args.chunk
        for index in range(chunks):
            path = chunk_path(args.label, size, index)
            if args.resume and os.path.exists(path):
                with open(path, encoding="utf-8") as handle:
                    total.merge(json.load(handle))
                continue
            part = Tally()
            first = index * args.chunk
            last = min(args.matches_per_size, first + args.chunk)
            t0 = time.time()
            for match in range(first, last):
                seed = SEED_BASE + size * 100000 + match
                try:
                    play_match(sim, server, part, size, seed)
                except Exception:
                    part.exceptions.append("size=%d seed=%d\n%s" % (size, seed, traceback.format_exc(limit=4)))
            with open(path + ".tmp", "w", encoding="utf-8") as handle:
                json.dump(part.to_dict(), handle)
            os.replace(path + ".tmp", path)
            total.merge(part.to_dict())
            say("size %d chunk %d/%d done: %d matches in %.1fs, exceptions so far %d" % (size, index + 1, chunks, last - first, time.time() - t0, len(total.exceptions)))
    matches = sum(total.matches.values())
    result = build_result(total, matches, args)
    out = args.out or os.path.join(ROOT, "redteam", "evidence", "event_tally_backend_%s.json" % args.label)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=1, sort_keys=True)
    say("wrote %s: %d matches, %d events fired, never fired %d, exceptions %d, rejected tool calls %d, %.0fs" % (
        os.path.relpath(out, ROOT), matches, sum(1 for e in result["events"].values() if e["fired"]), len(result["never_fired"]), len(total.exceptions), sum(total.rejected.values()), time.time() - started))
    for line in total.exceptions[:5]:
        say("ERROR engine exception: " + line.replace("\n", " | ")[:300])
    say("RESOURCE_RELEASED")
    return 1 if total.exceptions else 0


def build_result(total, matches, args):
    events = {}
    names = set(EXPECTED_EVENTS) | set(total.events)
    for name in sorted(names):
        fired = total.events.get(name, 0)
        events[name] = {"fired": fired, "per_match": round(fired / matches, 4) if matches else 0.0}
    never = [name for name in sorted(EXPECTED_EVENTS) if not total.events.get(name)]
    heroes = sorted(set(h for row in total.by_hero.values() for h in row))
    hero_gaps = []
    all_heroes = sorted(("bat", "bride", "hag", "hunchback", "knight", "reaper", "skeleton", "wizard"))
    for name in HERO_EVENTS:
        for hero in all_heroes:
            if not total.by_hero.get(name, {}).get(hero):
                if name == "ultimate.used" or name == "throw.total" or name == "unit.ko":
                    hero_gaps.append("%s / %s" % (name, hero))
    return {"built": datetime.date.today().isoformat(), "kind": "back end event tally", "tree_head": git_head(), "label": args.label, "matches": matches,
            "matches_by_size": total.matches, "events": events, "never_fired": never, "never_fired_by_hero": hero_gaps, "disabled_by_design": DISABLED_BY_DESIGN, "by_hero": total.by_hero, "by_size": total.by_size,
            "rejected_tool_calls": total.rejected, "exceptions": len(total.exceptions), "heroes_seen": heroes,
            "note": "Back end only: the rules engine driven by a bot (plain, heavy, double, heal, move, knight shield and wall, every ultimate). Events come from before/after snapshots of the match; nothing in the engine was changed."}


def compare(new_path, base_path, tolerance, min_count):
    with open(base_path, encoding="utf-8") as handle:
        base = json.load(handle)
    with open(new_path, encoding="utf-8") as handle:
        new = json.load(handle)
    return compare_data(base, new, tolerance, min_count)


def compare_data(base, new, tolerance, min_count):
    fails, warns, notes = [], [], []
    for name, row in sorted(base["events"].items()):
        now = new["events"].get(name, {"fired": 0, "per_match": 0.0})
        if row["fired"] > 0 and now["fired"] == 0:
            fails.append("FAIL %s fired %d times in the baseline and never now" % (name, row["fired"]))
        elif row["fired"] >= min_count and row["per_match"] > 0:
            change = abs(now["per_match"] - row["per_match"]) / row["per_match"]
            if change > tolerance:
                warns.append("WARN %s per match %.4f -> %.4f (%.0f%%)" % (name, row["per_match"], now["per_match"], 100 * change))
        elif row["fired"] == 0 and now["fired"] > 0:
            notes.append("NOTE %s never fired in the baseline and fires now (%d): a gap closed" % (name, now["fired"]))
    for pair in base.get("never_fired_by_hero", []):
        if pair not in new.get("never_fired_by_hero", []):
            notes.append("NOTE hero gap closed: " + pair)
    return fails, warns, notes


def selftest():
    base = {"events": {"a": {"fired": 5000, "per_match": 5.0}, "b": {"fired": 10, "per_match": 0.01}, "c": {"fired": 0, "per_match": 0.0}}, "never_fired_by_hero": ["x / bat"]}
    gone = {"events": {"a": {"fired": 5000, "per_match": 5.0}, "b": {"fired": 0, "per_match": 0.0}, "c": {"fired": 0, "per_match": 0.0}}, "never_fired_by_hero": ["x / bat"]}
    fails, _, _ = compare_data(base, gone, 0.25, 1000)
    assert len(fails) == 1 and "b " in fails[0], fails
    shifted = {"events": {"a": {"fired": 9000, "per_match": 9.0}, "b": {"fired": 10, "per_match": 0.01}, "c": {"fired": 0, "per_match": 0.0}}, "never_fired_by_hero": ["x / bat"]}
    fails, warns, _ = compare_data(base, shifted, 0.25, 1000)
    assert not fails and len(warns) == 1 and "a " in warns[0], (fails, warns)
    closed = {"events": {"a": {"fired": 5000, "per_match": 5.0}, "b": {"fired": 10, "per_match": 0.01}, "c": {"fired": 3, "per_match": 0.003}}, "never_fired_by_hero": []}
    fails, warns, notes = compare_data(base, closed, 0.25, 1000)
    assert not fails and not warns and len(notes) == 2, (fails, warns, notes)
    same_fails, same_warns, same_notes = compare_data(base, base, 0.25, 1000)
    assert not (same_fails or same_warns or same_notes)
    print("selftest OK: a vanished event is FAIL, a shifted rate is WARN, a closed gap is NOTE, identical data is silent")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--matches-per-size", type=int, default=1000)
    ap.add_argument("--sizes", default="1,2,3")
    ap.add_argument("--chunk", type=int, default=100)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--label", default="run")
    ap.add_argument("--out", default="")
    ap.add_argument("--compare", metavar="NEW.json", default="")
    ap.add_argument("--baseline", default=BASELINE)
    ap.add_argument("--tolerance", type=float, default=0.25)
    ap.add_argument("--min-count", type=int, default=1000)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if args.compare:
        try:
            fails, warns, notes = compare(args.compare, args.baseline, args.tolerance, args.min_count)
        except (OSError, ValueError, KeyError) as error:
            say("ERROR cannot compare: %s" % error)
            return 2
        for line in fails + warns + notes:
            say(line)
        say("compare: %d FAIL, %d WARN, %d NOTE" % (len(fails), len(warns), len(notes)))
        return 1 if fails else 0
    if args.run or True:
        if args.matches_per_size < 1 or args.chunk < 1:
            say("ERROR bad arguments")
            return 2
        return run(args)


if __name__ == "__main__":
    sys.exit(main())
