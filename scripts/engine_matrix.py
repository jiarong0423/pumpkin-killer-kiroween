#!/usr/bin/env python3
"""Back-end half of the front-versus-back match matrix (docs/MATRIX_SPEC_20261117.md).

Plays 8 heroes x 3 sizes x 10 plays = 240 matches on the Python engine (mcp_stdio_server.Session over mcp_game_server),
both sides computer-controlled by the bot of scripts/sim_team_headless.py (perfect-aim bisection plus a power error, a
random move 35 percent of the turns), team rules as built (hp scale, ramp, round cap, comeback pack), 60-round guard for
duels. Strength is hidden and random: a mulberry32 PRNG over `seed ^ 0x5eed` draws the left tier and then the right
tier from [hard, normal, easy]; tier -> power error sd 4.9 / 9.1 / 23.4 (2026-11-18 x 0.65 of 7.5 / 14 / 36; owner 2026-11-17: the computer was too strong; calibrated to about 0.45 / 0.30 / 0.15 direct hits per throw, the same targets as the page AI). The tiers are written to the record only.

Run:   python3 -B scripts/engine_matrix.py [--out logs_local/matrix_engine.json] [--plays 10] [--sizes 1 2 3]
                                           [--heroes skeleton ...] [--move-rate 0.35] [--quiet]
Exit:  0 when the file was written and no match raised an error, 1 when any match recorded an error, 2 on a usage or load failure.
Log:   logs_local/matrix_engine.log (this run only; the sim's own log is not touched).
"""
import argparse
import json
import logging
import os
import random
import sys
import time
import traceback
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOG_DIR = os.path.join(ROOT, "logs_local")
DEFAULT_OUT = os.path.join(LOG_DIR, "matrix_engine.json")
sys.path.insert(0, HERE)

HEROES = ["skeleton", "wizard", "bat", "knight", "bride", "hunchback", "reaper", "hag"]
TIERS = ["hard", "normal", "easy"]
TIER_NOISE = {"hard": 4.9, "normal": 9.1, "easy": 23.4}   # 2026-11-18 owner: the computer is too weak (1v1 hits per throw 0.205, 19.4 percent of duels hit the round cap): every tier x 0.65 (was 7.5 / 14 / 36, before that 1.6 / 5 / 9); isolated sweep (scripts/ai_calib.py, scratch) gives 0.458 / 0.305 / 0.154 hits per throw for 4.9 / 9.1 / 23.4, the owner targets 0.45 / 0.30 / 0.15
DUEL_GUARD = 60
TEAM_GUARD = 150
LOG = logging.getLogger("engine_matrix")


def mulberry32(seed):
    """The same generator as js/weather_fx.js mulberry32 (32-bit integer semantics)."""
    mask = 0xFFFFFFFF
    state = [seed & mask]

    def imul(x, y):
        return (x * y) & mask

    def next_value():
        state[0] = (state[0] + 0x6D2B79F5) & mask
        a = state[0]
        t = imul(a ^ (a >> 15), 1 | a)
        t = ((t + imul(t ^ (t >> 7), 61 | t)) & mask) ^ t
        return ((t ^ (t >> 14)) & mask) / 4294967296.0
    return next_value


def cell_seed(hero_index, size, play):
    """Plays 0 to 9 keep the 240-match spec seeds; from play 10 on a cell gets its own range (no seed shared by two cells in a 20,000-match run), see docs/MATRIX_SPEC_20261117.md."""
    if play < 10:
        return 7000 + 100 * hero_index + 10 * size + play
    return 100000 + (hero_index * 3 + size - 1) * 100000 + play


def right_hero(seed):
    return HEROES[(seed * 7 + 3) % 8]


def draw_tiers(seed):
    """Left tier first, then right tier, each uniform over [hard, normal, easy]."""
    rand = mulberry32(seed ^ 0x5eed)
    left = TIERS[int(rand() * 3)]
    right = TIERS[int(rand() * 3)]
    return left, right


def _load_engine():
    # the sim configures logging at import time: point its log at this run's own file so logs_local/sim_team_headless.log stays
    os.makedirs(LOG_DIR, exist_ok=True)
    os.environ.setdefault("PK_SIM_LOG", os.path.join(LOG_DIR, "matrix_engine_sim_import.log"))
    import sim_team_headless as sim  # noqa: E402
    import mcp_stdio_server as server  # noqa: E402
    return sim, server


def team_from(first, size):
    start = HEROES.index(first)
    return [HEROES[(start + i) % len(HEROES)] for i in range(size)]


def team_share(eng, team):
    units = [u for u in eng.units.values() if u["team"] == team]
    return sum(u["hp"] for u in units if u["hp"] > 0) / sum(u["max_hp"] for u in units)


def rich_turn(session, server, sim, eng, rng, move_rng, active, rnd, team, noise, seat, count):
    """One unit's attack turn with every player-facing action in play (owner 2026-11-17: 'full skills and events'): heal when hurt, defend now and then,
    the ultimate whenever the three pips are there, heavy and double shots, plain throws otherwise. A refusal by the engine is counted, never hidden."""
    unit = eng.units[active]
    other = "white" if team == "red" else "red"

    def act(action, key):
        try:
            session.call("submit_action", {"unit": active, "round": rnd, "action": action}, seat)
            count(key)
            return True
        except server.ToolError:
            count("refused_" + key)
            return False
    left = session.skills_remaining[team]   # a team has one of each skill: only ask for one that is left, so a refusal means something is really wrong
    hurt = unit["hp"] < 0.45 * unit["max_hp"]
    if hurt and left["heal"] > 0 and move_rng.random() < 0.8:
        act({"type": "skill", "skill": "heal"}, "skill_heal")
    if unit["hero"] == "knight" and move_rng.random() < 0.25:   # the shield wants two remembered enemy paths
        paths = session.remembered_paths(team)
        if len(paths) >= 2 and act({"type": "defend", "path1": paths[-1], "path2": paths[-2]}, "defend"):
            return
    angle, power, _ = sim.aim(rng, eng, unit, noise)
    if session.energy[team] >= 3 and session.ultimates_used[team] < server.MAX_ULTIMATES_PER_MATCH and move_rng.random() < 0.7:
        if unit["hero"] == "knight":
            foes = [u for u in eng.units.values() if u["team"] == other and u["alive"]]
            if foes:
                step = 1 if foes[0]["x"] > unit["x"] else -1
                pts = [{"x": unit["x"] + step * d, "y": 700.0} for d in (250.0, 500.0, 750.0)]
                if act({"type": "ultimate", "points": pts}, "ultimate_knight"):
                    pass
        elif act({"type": "ultimate", "angle": angle, "power": power}, "ultimate_" + unit["hero"]):
            return
    roll = move_rng.random()
    if roll < 0.2 and left["heavy"] > 0 and act({"type": "skill", "skill": "heavy", "angle": angle, "power": power}, "skill_heavy"):
        return
    if 0.2 <= roll < 0.4 and left["double"] > 0 and act({"type": "skill", "skill": "double", "angle": angle, "power": power}, "skill_double"):
        return
    session.call("submit_action", {"unit": active, "round": rnd, "action": {"type": "throw", "angle": angle, "power": power}}, seat)
    count("throw_plain")


def play_match(sim, server, hero, size, seed, move_rate=0.35, rich=False):
    """One match; returns the spec's result record. Never raises: a failure goes into `errors`."""
    tier_left, tier_right = draw_tiers(seed)
    hero_right = right_hero(seed)
    record = {"end": "engine", "hero": hero, "hero_right": hero_right, "heroes_left": [hero] if size == 1 else team_from(hero, size), "heroes_right": [hero_right] if size == 1 else team_from(hero_right, size), "size": size, "seed": seed,
              "tier_left": tier_left, "tier_right": tier_right, "winner": "none", "rounds": 0,
              "hp_share_left": None, "hp_share_right": None, "units_left_alive": None, "units_right_alive": None,
              "throws": 0, "direct_hits": 0, "near_misses": 0, "pity_triggers": 0, "comeback_hits": 0,
              "ultimates_left": 0, "ultimates_right": 0, "errors": []}
    events = {}   # rich mode: how often each player-facing event fired (skills, ultimates, defend, moves) and how often the engine refused it

    def count(key):
        events[key] = events.get(key, 0) + 1
    if rich:
        record["events"] = events
    try:
        noise = {"red": TIER_NOISE[tier_left], "white": TIER_NOISE[tier_right]}
        rng = random.Random(seed * 7919 + size)
        move_rng = random.Random(seed * 104729 + size)
        red = hero if size == 1 else team_from(hero, size)       # mixed teams: the hero, then the next heroes in the fixed order, none twice
        white = hero_right if size == 1 else team_from(hero_right, size)
        session = server.Session(seed=seed, units=size, hero_red=red, hero_white=white, clock=lambda: 0.0,
                                 human_turn_seconds=0, turn_seconds=100)
        eng = session.engine
        guard = DUEL_GUARD if size == 1 else TEAM_GUARD
        original_resolve = eng._resolve_throw

        def resolve_throw(unit, throw):
            team = unit["team"]
            other = "white" if team == "red" else "red"
            pity_before = eng.pity[team] if size > 1 else 0
            behind = size > 1 and team_share(eng, team) < team_share(eng, other)
            result = original_resolve(unit, throw)
            record["throws"] += 1
            direct = result.get("hit_type") == "hero"
            record["direct_hits"] += 1 if direct else 0
            if "near_miss" in result:
                record["near_misses"] += 1
            if direct and pity_before > 0:
                record["pity_triggers"] += 1
            if direct and (pity_before > 0 or behind):
                record["comeback_hits"] += 1
            if result.get("ultimate"):
                record["ultimates_left" if team == "red" else "ultimates_right"] += 1
            return result
        eng._resolve_throw = resolve_throw
        seat_of = {"red": session.seats["red"], "white": session.seats["white"]}
        phase_of = {"red": "human", "white": "agent"}
        while session.winner is None and eng.round_num <= guard:
            rnd = eng.round_num
            for team in ("red", "white"):
                if session.phase == "over":
                    break
                active = session._active_unit(team)
                if active is not None and active not in session.skipped_units:
                    if move_rng.random() < move_rate:
                        try:
                            session.call("submit_action", {"unit": active, "round": rnd, "action": {
                                "type": "move", "direction": move_rng.choice(("forward", "backward"))}}, seat_of[team])
                        except server.ToolError:
                            pass   # a slowed unit may not move
                    if rich:
                        rich_turn(session, server, sim, eng, rng, move_rng, active, rnd, team, noise[team], seat_of[team], count)
                    else:
                        angle, power, _ = sim.aim(rng, eng, eng.units[active], noise[team])
                        session.call("submit_action", {"unit": active, "round": rnd,
                                                       "action": {"type": "throw", "angle": angle, "power": power}},
                                     seat_of[team])
                session.call("end_turn", {"round": rnd, "phase": phase_of[team]}, seat_of[team])
        record["rounds"] = eng.round_num - 1
        reason = session.winner_reason
        if session.winner == "red":
            record["winner"] = "cap_left" if reason == "round_cap" else "left"
        elif session.winner == "white":
            record["winner"] = "cap_right" if reason == "round_cap" else "right"
        else:
            record["winner"] = "none"   # a draw, or the duel guard
            if session.winner is None:
                record["errors"].append("guard: no winner after %d rounds" % guard) if size > 1 else None
        record["hp_share_left"] = round(team_share(eng, "red"), 4)
        record["hp_share_right"] = round(team_share(eng, "white"), 4)
        record["units_left_alive"] = sum(1 for u in eng.units.values() if u["team"] == "red" and u["alive"])
        record["units_right_alive"] = sum(1 for u in eng.units.values() if u["team"] == "white" and u["alive"])
    except Exception as error:   # noqa: BLE001 - a failing match must be recorded, not stop the matrix
        record["errors"].append("%s: %s" % (type(error).__name__, error))
        LOG.error("match hero=%s size=%d seed=%d failed\n%s", hero, size, seed, traceback.format_exc())
    return record


def run_matrix(heroes, sizes, plays, move_rate=0.35, progress=None, rich=False):
    sim, server = _load_engine()
    matches = []
    for hero in heroes:
        hero_index = HEROES.index(hero)
        for size in sizes:
            for play in range(plays):
                seed = cell_seed(hero_index, size, play)
                matches.append(play_match(sim, server, hero, size, seed, move_rate, rich))
                if progress:
                    progress(len(matches))
    return matches


def summarize(matches):
    """{(hero, size): row} with rounds mean, left win share, hits per throw, near misses, pity triggers, errors."""
    cells = {}
    for match in matches:
        cells.setdefault((match["hero"], match["size"]), []).append(match)
    rows = {}
    for key, group in cells.items():
        n = len(group)
        throws = sum(m["throws"] or 0 for m in group)
        rows[key] = {
            "n": n, "rounds": sum(m["rounds"] for m in group) / n,
            "left_win": sum(1 for m in group if m["winner"] in ("left", "cap_left")) / n,
            "hits_per_throw": (sum(m["direct_hits"] or 0 for m in group) / throws) if throws else 0.0,
            "near_misses": sum(m["near_misses"] or 0 for m in group),
            "pity_triggers": sum(m["pity_triggers"] or 0 for m in group),
            "errors": sum(len(m["errors"]) for m in group)}
    return rows


def print_table(matches):
    rows = summarize(matches)
    print("%-10s %-5s %-3s %-8s %-9s %-10s %-11s %-12s %s" % (
        "hero", "size", "n", "rounds", "left win", "hits/throw", "near miss", "pity trig.", "errors"))
    for hero in HEROES:
        for size in (1, 2, 3):
            row = rows.get((hero, size))
            if row:
                print("%-10s %-5s %-3d %-8.1f %-9s %-10.3f %-11d %-12d %d" % (
                    hero, "%dv%d" % (size, size), row["n"], row["rounds"], "%.0f%%" % (100 * row["left_win"]),
                    row["hits_per_throw"], row["near_misses"], row["pity_triggers"], row["errors"]))
    print("")
    for size in (1, 2, 3):
        group = [m for m in matches if m["size"] == size]
        if not group:
            continue
        throws = sum(m["throws"] for m in group) or 1
        print("%dv%d overall: %d matches, rounds mean %.1f, left wins %.0f%%, caps %d, none %d, hits/throw %.3f, near misses %d, pity triggers %d, errors %d" % (
            size, size, len(group), sum(m["rounds"] for m in group) / len(group),
            100.0 * sum(1 for m in group if m["winner"] in ("left", "cap_left")) / len(group),
            sum(1 for m in group if m["winner"] in ("cap_left", "cap_right")), sum(1 for m in group if m["winner"] == "none"),
            sum(m["direct_hits"] for m in group) / throws, sum(m["near_misses"] for m in group),
            sum(m["pity_triggers"] for m in group), sum(len(m["errors"]) for m in group)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--plays", type=int, default=10)
    parser.add_argument("--sizes", type=int, nargs="+", default=[1, 2, 3], choices=[1, 2, 3])
    parser.add_argument("--heroes", nargs="+", default=HEROES, choices=HEROES)
    parser.add_argument("--move-rate", type=float, default=0.35)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--rich", action="store_true", help="the bot also uses heal, defend, heavy, double and the ultimates; the record gets an `events` counter")
    args = parser.parse_args(argv)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    logging.basicConfig(filename=os.path.join(LOG_DIR, "matrix_engine.log"), filemode="w", level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    clock = time.time()
    total = len(args.heroes) * len(args.sizes) * args.plays

    def progress(done):
        if not args.quiet and done % 24 == 0:
            print("  %d / %d matches, %.0fs" % (done, total, time.time() - clock), flush=True)
    try:
        matches = run_matrix(args.heroes, args.sizes, args.plays, args.move_rate, progress, args.rich)
    except Exception:   # noqa: BLE001 - load failure
        LOG.error("fatal\n%s", traceback.format_exc())
        print("ERROR cannot run the engine matrix, see logs_local/matrix_engine.log")
        return 2
    payload = {"end": "engine", "started": started, "params": {"move_rate": args.move_rate, "plays": args.plays, "rich": args.rich,
               "tier_noise": TIER_NOISE, "duel_guard": DUEL_GUARD}, "matches": matches}
    tmp = args.out + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1)
        handle.write("\n")
    os.replace(tmp, args.out)
    print_table(matches)
    errors = sum(len(m["errors"]) for m in matches)
    print("\n%d matches in %.0fs, %d errors, written to %s" % (len(matches), time.time() - clock, errors, args.out))
    for match in matches:
        for error in match["errors"]:
            print("ERROR seed=%d hero=%s size=%d: %s" % (match["seed"], match["hero"], match["size"], error))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
