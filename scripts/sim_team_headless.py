#!/usr/bin/env python3
"""Headless seeded 2v2 and 3v3 team-battle simulation for the Python match engine.

Run:  python3 -B scripts/sim_team_headless.py
Log:  logs_local/sim_team_headless.log   (overwritten on every run)
Exit: 0 when every check passes, 1 when any check fails, 2 when the engine cannot be loaded.

The engine is driven without sockets, the way scripts/test_mcp_units.py does it: a
mcp_stdio_server.Session (red = human phase, white = agent phase, one active unit per team)
over the mcp_game_server rules engine. Only throws are played. The independent reference
below re-traces every projectile from the pre-throw state (own step loop, own hit boxes from
the page rules: 70 x 190, reaper 57 x 165, widened by sqrt(len*thick)/2-20) and compares it
with what the engine did.

Checks (per match unless noted):
  rotation       the active unit of a team is the next living unit after the previous active
                 unit in fixed id order (cyclic); a dead unit is never active
  no_repeat      no unit is the active unit twice in a row while a teammate lives
  frozen         a living non-active teammate cannot submit an action
  throw_log      no dead unit appears in the throw log after the round it died in
  first_hit      a throw hits exactly the first living enemy unit its path touches (the
                 reference set at the first touching step contains the target) and damages
                 nobody else; a throw with no touch damages nobody
  winner         winner is set only when a whole team has no living unit, and always then
  guard          the match ends before MAX_ROUNDS
  crossing       (constructed, per N) a shot whose path crosses two or three enemy boxes
                 damages only the first living one, also when the nearest one is dead
  tie_nearest    two boxes touched in the same step: the engine hits the unit nearest to the
                 PROJECTILE (docs/TEAM_RULES_20261117.md rule 4), not the one nearest the shooter
  hp_scale       every unit starts with max hp = team_max_hp(hero hp, hero dmg, N) and never exceeds it
  ramp           every contact hit equals round_tenth(base x ramp_multiplier(round, N)) (checked
                 against an independent formula for non-bouncing weapons)
  wave           a bride wave damages the touched unit and every living enemy within 105 px of the
                 wave centre, each with the stepped 100/75/50 percent of its own distance
  cap            a match that is still undecided when the round counter passes round_cap(N) ends in
                 that round, winner from the hp share rule, reason 'round_cap'; a kill win has none
  cap_len        no match is longer than the cap (resolved rounds <= cap, counter <= cap + 1)
  gap            no two living teammates are closer than 120 px: at the start, after every MOVE
                 and after every round (knockbacks)
  near_miss      a ground landing within 450 px of the nearest living enemy box edge hits exactly that unit for
                 round1(dmg x 0.9 x (1 - e/450)), never on a direct hit, never when e <= 0 or e > 450
  pity           per-team miss counter: +1 per throw without a direct hit (near miss included), reset on a direct
                 hit, engine counter equals the independent counter, bonus capped at +1.6
  underdog       the damage formula is base x ramp x min(2.3, underdog x (1 + pity)) with the HP shares at the
                 moment of the hit; the factor is never below 1 nor above 2.3; state.comeback_multiplier equals it
  one_unit       (N = 1, PK_SIM_ONE matches) no pity / underdog_bonus keys, no near_miss, hp = table, no ramp, no cap
Skill gap: PK_SIM_MODE=gap runs expert (1.6) vs sloppy (9) and decent (5) vs sloppy, sides swapped on the same
seeds (PK_SIM_MATCHES seeds x 2 sides per size) and prints the weaker team's win share and the match length.
Moves: PK_SIM_MOVE_RATE (default 0.35) is the chance that the active unit moves before it throws.
Aim noise: PK_SIM_NOISE (default 1.6) is the sd of the power error of the bot (about 5 = decent, 9 = sloppy).
"""
import json
import logging
import math
import os
import random
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LOG_PATH = os.environ.get("PK_SIM_LOG") or os.path.join(ROOT, "logs_local", "sim_team_headless.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logging.basicConfig(filename=LOG_PATH, filemode="w", level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
LOG = logging.getLogger("sim_team_headless")


def say(text=""):
    print(text)
    LOG.info(text)


sys.path.insert(0, HERE)
try:
    import mcp_game_server as engine  # noqa: E402
    import mcp_stdio_server as server  # noqa: E402
    import team_tuning_py as tuning  # noqa: E402
except Exception:  # pragma: no cover - load failure is a hard error
    LOG.error("cannot import the engine\n%s", traceback.format_exc())
    print("ERROR cannot import the engine, see %s" % LOG_PATH)
    sys.exit(2)

CRIT_MULT_CHECK = 1.1   # the crit multiplier the engine uses (scripts/mcp_game_server.py CRIT_MULTIPLIER, index.html CRIT_MULT)
MATCHES_PER_N = int(os.environ.get("PK_SIM_MATCHES", "50"))   # PK_SIM_MATCHES=1250 runs 1250 matches per team size
MOVE_RATE = float(os.environ.get("PK_SIM_MOVE_RATE", "0.35"))
AIM_NOISE = float(os.environ.get("PK_SIM_NOISE", "1.6"))
POWER_CAP = 115.0   # MAX_POWER of index.html and POWER_MAX of mcp_stdio_server since owner H15 2026-11-19 (it was 100)
MIN_GAP = 120.0
WAVE_STEPS = ((35.0, 1.0), (70.0, 0.75), (105.0, 0.5))   # independent copy of js/sound_wave.js (cells of 35 px since 2026-11-18)
SEED_BASE = 20261117
MAX_ROUNDS = 150
CROSSING_CASES = 80
SIZES = (2, 3)
# Informational length target (never a failed check): expected rounds per team match for the 2026-11-17 tuning (7 minute owner
# target); the band is 0.5 x to 1.5 x of it. Update with shared/team_tuning.json (hp_scale, ramp, cap) when that is retuned.
EXPECTED_ROUNDS = {2: 12.5, 3: 17.0}


def length_band(units):
    return 0.5 * EXPECTED_ROUNDS[units], 1.5 * EXPECTED_ROUNDS[units]
ONE_MATCHES = int(os.environ.get("PK_SIM_ONE", "20"))
MODE = os.environ.get("PK_SIM_MODE", "rules")   # "rules" (default) or "gap"

with open(os.path.join(ROOT, "shared", "constants.json"), encoding="utf-8") as _fh:
    K = json.load(_fh)
with open(os.path.join(ROOT, "shared", "heroes.json"), encoding="utf-8") as _fh:
    HEROES = json.load(_fh)
with open(os.path.join(ROOT, "shared", "team_tuning.json"), encoding="utf-8") as _fh:
    TT = json.load(_fh)
with open(os.path.join(ROOT, "shared", "comeback.json"), encoding="utf-8") as _fh:
    CB = json.load(_fh)   # independent reading: the sim does not import comeback_py
GROUND_Y = float(K["GROUND_Y"])
GRAVITY = float(K["GRAVITY"])
V0 = float(K["V0_PER_POWER"])
WALL_X0 = K["FENCE_X"] - K["FENCE_W"] / 2.0
WALL_X1 = K["FENCE_X"] + K["FENCE_W"] / 2.0
WALL_TOP = GROUND_Y - K["FENCE_H"]
PUSH_TAIL = K["WIND_TAIL"] * 0.9375
PUSH_HEAD = K["WIND_HEAD"] * 0.9375
HERO_IDS = sorted(HEROES)
# Page hit boxes (requirements R3 / index.html touches()): half width, height
BOX = {hero: ((57.0, 165.0) if hero == "reaper" else (70.0, 190.0)) for hero in HERO_IDS}
WAVE_BOX = (105.0, 40.0)
THROW_ANGLES = (50, 55, 60, 65, 70, 75)


# ------------------------------------------------------------------ check bookkeeping
class Checks:
    def __init__(self):
        self.passed = {}
        self.failed = {}
        self.messages = []

    def ok(self, name, condition, detail=""):
        if condition:
            self.passed[name] = self.passed.get(name, 0) + 1
            return True
        self.failed[name] = self.failed.get(name, 0) + 1
        if len(self.messages) < 200:
            self.messages.append("FAIL %s: %s" % (name, detail))
        LOG.error("FAIL %s: %s", name, detail)
        return False

    def total_failed(self):
        return sum(self.failed.values())


CHECKS = Checks()


# ------------------------------------------------------------------ reference physics
def flight(origin_x, origin_y, facing, launch, angle, power, wind, wall_hp, sweep=False, wall_sweep=True, wave=False):
    """Return (points, end). end is 'wall' (wall point not in points) or 'ground'. sweep: every step is also cut into sub-points about 3 px apart (the swept contact of the page and the engine, 2026-11-18)."""
    rad = math.radians(angle)
    speed = power * V0
    vx = speed * math.cos(rad) * facing
    vy = -speed * math.sin(rad)
    x = float(origin_x + launch["fwd"] * facing)
    y = float(origin_y - launch["up"])
    accel = wind * (engine._WIND_TAIL if wind * facing > 0 else engine._WIND_HEAD)   # the page's step: wind is a constant acceleration on vx (2026-11-17, was a constant drift)
    points = []
    for _ in range(300):
        vx += accel / 60.0
        vy += GRAVITY / 60.0
        prev_gx, prev_gy = x, y
        x += vx / 60.0
        y += vy / 60.0
        if wave and prev_gy < GROUND_Y < y:   # the bride's wave counts where it REALLY lands (page tCross, engine twin 2026-11-19): the frame that crosses the ground is cut back to the crossing point
            t_cross = (GROUND_Y - prev_gy) / (y - prev_gy)
            x = prev_gx + (x - prev_gx) * t_cross
            y = float(GROUND_Y)
        if wall_sweep and wall_hp > 0:   # swept wall (2026-11-18), for every weapon: a step that clips the fence corner between two end points still hits it, as in the page and the engine
            wpx, wpy = (points[-1] if points else (origin_x + launch["fwd"] * facing, origin_y - launch["up"]))
            n_w = max(1, math.ceil(math.hypot(x - wpx, y - wpy) / 1.5))
            for k in range(1, n_w):
                qx, qy = wpx + (x - wpx) * k / n_w, wpy + (y - wpy) * k / n_w
                if WALL_X0 <= qx <= WALL_X1 and qy >= WALL_TOP:
                    return points, "wall"
        if wall_hp > 0 and WALL_X0 <= x <= WALL_X1 and y >= WALL_TOP:
            return points, "wall"
        if sweep:
            px, py = (points[-1] if points else (origin_x + launch["fwd"] * facing, origin_y - launch["up"]))
            n_sub = max(1, math.ceil(math.hypot(x - px, y - py) / 3.0))
            for k in range(1, n_sub):
                points.append((px + (x - px) * k / n_sub, py + (y - py) * k / n_sub))
        points.append((x, y))
        if y >= GROUND_Y:
            return points, "ground"
    return points, "ground"


def reach_of(weapon):
    size = engine.PROJECTILE_SIZE.get(weapon)
    if size is None or weapon == "proj_soundwave":
        return 0.0
    return max(0.0, math.sqrt(size[0] * size[1]) / 2.0 - 20.0)


def touches(weapon, target_hero, target_x, px, py, armed=True):
    if weapon == "proj_soundwave":
        half, height = WAVE_BOX
        return abs(px - target_x) <= half and GROUND_Y - height <= py <= GROUND_Y
    half, height = BOX[target_hero]
    reach = reach_of(weapon)
    if not (abs(px - target_x) <= half + reach and GROUND_Y - height - reach <= py <= GROUND_Y + reach):
        return False
    # the decided box AND the figure (binary masks, shared/hit_masks.json; the left team stands left of x = 960 and faces right)
    masks = engine._hit_masks()
    return masks is None or not masks.has(target_hero) or masks.touches(target_hero, px - target_x, py - GROUND_Y, reach, target_x < 960.0, armed)


def first_touches(points, weapon, enemies, armed=None):
    """enemies: list of (id, hero, x). Returns {id: first step index} for every touched enemy."""
    found = {}
    for index, (px, py) in enumerate(points):
        for uid, hero, ex in enemies:
            if uid not in found and touches(weapon, hero, ex, px, py, True if armed is None else armed.get(uid, True)):
                found[uid] = index
    return found


def landing_x(origin, angle, power, wind, wall_hp):
    points, end = flight(origin["x"], origin["y"], origin["facing"], origin["launch"], angle, power, wind, wall_hp, sweep=True)
    return None if end == "wall" else points[-1][0]


def aim(rng, eng, unit, noise=None):
    """Pick a living enemy, an arc angle, bisect the power for its x, add noise."""
    enemies = [u for u in eng.units.values() if u["team"] != unit["team"] and u["alive"]]
    nearest = min(enemies, key=lambda u: abs(u["x"] - unit["x"]))
    target = nearest if rng.random() < 0.5 else rng.choice(enemies)
    angle = rng.choice(THROW_ANGLES)
    origin = {"x": unit["x"], "y": unit["y"], "facing": unit["facing"], "launch": unit["launch"]}
    lo, hi = 10.0, POWER_CAP
    for _ in range(14):
        mid = (lo + hi) / 2.0
        land = landing_x(origin, angle, mid, eng.wind, eng.central_wall_hp)
        short = land is None or (land < target["x"] if unit["facing"] > 0 else land > target["x"])
        if short:
            lo = mid
        else:
            hi = mid
    power = max(0.0, min(POWER_CAP, (lo + hi) / 2.0 + rng.gauss(0.0, AIM_NOISE if noise is None else noise)))
    return float(angle), round(power, 2), target["id"]


# ------------------------------------------------------------------ engine instrumentation
class Observer:
    """Wraps one engine instance so every projectile and every damage application is recorded."""

    def __init__(self, eng):
        self.eng = eng
        self.events = []
        self._current = None
        original_resolve = type(eng)._resolve_throw
        original_apply = type(eng)._apply_hit

        def resolve_throw(unit, throw):
            enemies = [(u["id"], u["hero"], float(u["x"])) for u in eng.units.values()
                       if u["team"] != unit["team"] and u["alive"]]
            armed = {u["id"]: True for u in eng.units.values()}   # the armed mask always (red-team R3A-1): same as the page and mcp_game_server.projectile_hits
            self._current = {
                "unit": unit["id"], "team": unit["team"], "weapon": unit["weapon"], "enemies": enemies, "armed": armed,
                "origin": {"x": float(unit["x"]), "y": float(unit["y"]), "facing": unit["facing"],
                           "launch": dict(unit["launch"])},
                "angle": throw["angle"], "power": throw["power"], "special": throw.get("special"),
                "wind": eng.wind, "wall_hp": eng.central_wall_hp, "damaged": [],
                "shield_up": eng.shields["red" if unit["team"] == "white" else "white"]["active"],
                "round": eng.round_num,
                "weak": bool(unit["statuses"].get("weak", 0)), "unit_dmg": unit["dmg"],
                "pity": dict(getattr(eng, "pity", {})),
            }
            record = original_resolve(eng, unit, throw)
            self._current["record"] = record
            self.events.append(self._current)
            self._current = None
            return record

        def apply_hit(attacker, target, *args, **kwargs):
            weak = bool(args[2]) if len(args) > 2 else bool(kwargs.get("weak_active"))
            shares = ((share_of(eng, attacker["team"]), share_of(eng, target["team"])) if eng.units_per_side > 1 else (1.0, 1.0))
            pity_count = eng.pity[attacker["team"]] if eng.units_per_side > 1 else 0
            result = original_apply(eng, attacker, target, *args, **kwargs)
            if self._current is not None:
                self._current["damaged"].append(target["id"])
                scale = args[3] if len(args) > 3 else kwargs.get("damage_scale", 1.0)
                self._current.setdefault("applies", []).append({
                    "target": target["id"], "scale": scale, "damage": result["damage"], "critical": result["critical"],
                    "base": attacker["dmg"], "weak": weak,
                    "bounce": bool(attacker.get("bounce")), "round": eng.round_num,
                    "own_share": shares[0], "enemy_share": shares[1], "pity": pity_count})
            return result

        eng._resolve_throw = resolve_throw
        eng._apply_hit = apply_hit

    def drain(self):
        events, self.events = self.events, []
        return events


def round_tenth(value):
    return math.floor(value * 10 + 0.5) / 10


def expected_ramp(round_number, units):
    """Independent copy of the late-ramp rule, read from shared/team_tuning.json (not from team_tuning_py)."""
    if units < 2 or round_number < TT["ramp"]["start_round"]:
        return 1.0
    return 1 + TT["ramp"]["per_round"] * (round_number - (TT["ramp"]["start_round"] - 1))


def wave_factor(distance):
    for limit, factor in WAVE_STEPS:
        if distance <= limit:
            return factor
    return 0.0


def round1(value):
    return round_tenth(value)


def share_of(eng, team):
    units = [u for u in eng.units.values() if u["team"] == team]
    hp = mx = 0.0   # a plain left-to-right loop like comeback_py.hp_share and js/comeback.js hpShare: Python 3.12 sum() uses compensated addition, which differs in the last bit and flipped a 3rd-decimal rounding tie (full-scale run 2026-11-22: seed 20264953, round 4, 0.482 against 0.483)
    for u in units:
        mx += u["max_hp"]
        if u["hp"] > 0: hp += u["hp"]
    return hp / mx


def underdog_ref(own, enemy):
    return 1 + min(CB["underdog"]["max_bonus"], max(0.0, enemy - own) / CB["underdog"]["full_at_deficit"])


def pity_ref(count):
    return min(CB["pity"]["cap"], CB["pity"]["per_miss"] * max(0, count))


def near_miss_ref(base, edge):
    reach = CB["near_miss"]["reach_px"]
    if not edge > 0 or edge > reach:
        return 0.0
    return round1(base * CB["near_miss"]["scale"] * (1 - edge / reach))


def wave_factors_allowed(distance):
    """The wave centre is logged rounded to 0.1 px, so a unit within 0.06 px of a step edge may land on either side."""
    return {wave_factor(distance - 0.06), wave_factor(distance + 0.06), wave_factor(distance)}


def cap_reference(eng):
    """Independent copy of round_cap_rule: larger hp share, then more living units, then the right side (white)."""
    def share(team):
        units = [u for u in eng.units.values() if u["team"] == team]
        total = sum(u["max_hp"] for u in units)
        return sum(u["hp"] for u in units if u["hp"] > 0) / total, sum(1 for u in units if u["hp"] > 0)
    (rs, ra), (ws, wa) = share("red"), share("white")
    if rs != ws:
        return "red" if rs > ws else "white"
    if ra != wa:
        return "red" if ra > wa else "white"
    return "white"


def min_teammate_gap(eng):
    """Smallest distance between two living teammates (None when no team has two living units)."""
    best = None
    for team in ("red", "white"):
        xs = sorted(u["x"] for u in eng.units.values() if u["team"] == team and u["alive"])
        for left, right in zip(xs, xs[1:]):
            best = right - left if best is None else min(best, right - left)
    return best


def verify_event(event, stats, where, units, ref_pity):
    """Compare one engine throw with the reference trace. Returns nothing; records checks."""
    record = event["record"]
    # ramp: every contact hit equals round_tenth(base x weak x scale [x crit] x ramp) (bouncing shields excluded)
    applies = event.get("applies", [])
    first = applies[0] if applies else None   # the page fixes the shares and the pity charge at the FIRST damage of a projectile; every later hit of it (blast, wave splash, swarm) uses them (index.html cbBegin; red-team R11B-2)
    for hit in applies:
        if first is not None:
            hit = dict(hit, own_share=first["own_share"], enemy_share=first["enemy_share"], pity=first["pity"])
        if hit["bounce"]:
            continue
        value = hit["base"] * (0.85 if hit["weak"] else 1.0) * hit["scale"]
        if hit["critical"]:
            value = round_tenth(value * CRIT_MULT_CHECK)
        ramp = expected_ramp(hit["round"], units)
        if units > 1:
            bare = round_tenth(value * ramp)
            underdog = underdog_ref(hit["own_share"], hit["enemy_share"])
            value = round_tenth(value * ramp * min(CB["max_total_multiplier"], underdog * (1 + pity_ref(hit["pity"]))))
            stats["capped_stack_hits"] += 1 if underdog * (1 + pity_ref(hit["pity"])) > CB["max_total_multiplier"] else 0
            CHECKS.ok("underdog", underdog >= 1.0 and hit["damage"] >= bare - 0.051,
                      "%s %s round %s: underdog %s, damage %s below the bare %s" % (
                          where, event["unit"], hit["round"], underdog, hit["damage"], bare))
            stats["underdog_hits"] += 1 if underdog > 1.0 else 0
            stats["pity_hits"] += 1 if hit["pity"] > 0 else 0
            stats["pity_cap_hits"] += 1 if hit["pity"] * CB["pity"]["per_miss"] >= CB["pity"]["cap"] else 0
        CHECKS.ok("ramp", abs(hit["damage"] - value) < 0.051,
                  "%s %s round %s: damage %s expected %s (ramp %s, scale %s, own %.3f enemy %.3f pity %s)" % (
                      where, event["unit"], hit["round"], hit["damage"], round(value, 3), ramp, hit["scale"],
                      hit["own_share"], hit["enemy_share"], hit["pity"]))
        stats["ramped_hits" if ramp != 1.0 else "plain_hits"] += 1
    # comeback pack: independent pity counter and near-miss reference (team matches only)
    if units > 1:
        team = event["team"]
        direct = record["hit_type"] == "hero"
        CHECKS.ok("pity", event["pity"][team] == ref_pity[team],
                  "%s %s round %s: engine pity %s vs reference %s before the throw" % (
                      where, event["unit"], event["round"], event["pity"][team], ref_pity[team]))
        ref_pity[team] = 0 if direct else ref_pity[team] + 1
        enemies = event["enemies"]
        if direct:
            CHECKS.ok("near_miss", "near_miss" not in record, "%s round %s: near miss on a direct hit" % (where, event["round"]))
        elif record["hit_type"] == "ground":
            reach = CB["near_miss"]["reach_px"]
            edges = [(max(0.0, abs(ex - record["landing_x"]) - BOX[hero][0]), uid) for uid, hero, ex in enemies]
            edge, nearest = min(edges) if edges else (None, None)
            got = record.get("near_miss")
            if not CB["near_miss"].get("enabled", True):   # the switch is off: a ground landing never hurts anybody
                CHECKS.ok("near_miss", got is None, "%s round %s: near miss %s although the compensation is off" % (where, event["round"], got))
                stats["plain_misses"] += 1
            elif edge is None or abs(edge) < 0.06 or abs(edge - reach) < 0.06:
                pass   # a landing logged to 0.1 px cannot tell which side of the 0 / 450 px limit it was on
            elif edge <= 0 or edge > reach:
                CHECKS.ok("near_miss", got is None, "%s round %s: near miss %s with edge %s" % (where, event["round"], got, edge))
                stats["plain_misses"] += 1
            else:
                want = near_miss_ref(event["unit_dmg"] * (0.85 if event["weak"] else 1.0), edge)
                CHECKS.ok("near_miss", (got is None and want == 0.0) or
                          (got is not None and got["target"] == nearest and abs(got["damage"] - want) < 0.11),
                          "%s round %s: near miss %s expected target %s damage %s (edge %.2f)" % (
                              where, event["round"], got, nearest, want, edge))
                if got is not None:
                    stats["near_misses"] += 1
                    stats["near_miss_edges"].append(edge)
        else:
            CHECKS.ok("near_miss", "near_miss" not in record, "%s round %s: near miss on %s" % (where, event["round"], record["hit_type"]))
    else:
        CHECKS.ok("one_unit", "near_miss" not in record, "%s: near miss in a 1v1 match" % where)
    points, end = flight(event["origin"]["x"], event["origin"]["y"], event["origin"]["facing"],
                         event["origin"]["launch"], event["angle"], event["power"], event["wind"],
                         event["wall_hp"], wave=event["weapon"] == "proj_soundwave", sweep=event["weapon"] != "proj_soundwave")
    touched = first_touches(points, event["weapon"], event["enemies"], event.get("armed"))
    if len(touched) >= 2:
        stats["cross_two"] += 1
    stats["throws"] += 1
    damaged = event["damaged"]
    if event["special"] is not None or event["shield_up"]:
        return  # the sim plays plain throws, no shields
    wave = event["weapon"] == "proj_soundwave"
    # engine stops at the first step that touches an enemy, or at the wall / ground
    first_step = None
    candidates = []
    if touched:
        first_step = min(touched.values())
        candidates = sorted(uid for uid, step in touched.items() if step == first_step)
    if end == "wall" and first_step is not None:
        # the wall point is not part of `points`; a touch earlier on the same path still wins
        pass
    expected_type = "hero" if candidates else ("central_wall" if end == "wall" else "ground")
    CHECKS.ok("first_hit", record["hit_type"] == expected_type,
              "%s %s %s: engine hit_type=%s reference=%s throw=%s/%s" % (
                  where, event["unit"], event["round"], record["hit_type"], expected_type,
                  event["angle"], event["power"]))
    if expected_type == "hero":
        stats["hero_hits"] += 1
        CHECKS.ok("first_hit", record["hit_target"] in candidates,
                  "%s %s round %s: engine target %s not in first-touch set %s (touched=%s)" % (
                      where, event["unit"], event["round"], record["hit_target"], candidates, touched))
        if wave:
            # area effect: the touched unit plus every living enemy within 105 px of the wave centre (record landing_x)
            centre = record["landing_x"]
            must = {record["hit_target"]} | {uid for uid, _h, ex in event["enemies"] if abs(ex - centre) <= WAVE_BOX[0] - 0.06}
            may = {uid for uid, _h, ex in event["enemies"] if abs(ex - centre) <= WAVE_BOX[0] + 0.06}
            expected_damaged = sorted(must)
            CHECKS.ok("wave", must <= set(damaged) <= (must | may),
                      "%s %s round %s: wave centre %.1f damaged %s expected %s" % (
                          where, event["unit"], event["round"], centre, sorted(damaged), expected_damaged))
            for hit in event.get("applies", []):
                ex = next(e[2] for e in event["enemies"] if e[0] == hit["target"])
                CHECKS.ok("wave", hit["scale"] in wave_factors_allowed(abs(ex - centre)),
                          "%s round %s: %s took scale %s at %.1f px, expected %s" % (
                              where, event["round"], hit["target"], hit["scale"], abs(ex - centre),
                              wave_factor(abs(ex - centre))))
                stats["wave_hits"] += 1
        else:
            CHECKS.ok("first_hit", damaged == [record["hit_target"]],
                      "%s %s round %s: damaged %s but target %s" % (
                          where, event["unit"], event["round"], damaged, record["hit_target"]))
        if len(candidates) > 1:
            stats["ties"] += 1
            # the tie rule is the PROJECTILE: the candidate whose x is nearest to the point where the path first touches
            px = points[first_step][0]
            nearest = min(candidates, key=lambda uid: abs(next(e[2] for e in event["enemies"] if e[0] == uid) - px))
            shooter_nearest = min(candidates, key=lambda uid: abs(next(e[2] for e in event["enemies"] if e[0] == uid)
                                                                 - event["origin"]["x"]))
            if shooter_nearest != nearest:
                stats["ties_shooter_metric_differs"] += 1   # the old (wrong) metric would have flagged these
            ok = record["hit_target"] == nearest
            CHECKS.ok("tie_nearest", ok, "%s round %s: touched %s, engine picked %s, projectile-nearest is %s" % (
                where, event["round"], candidates, record["hit_target"], nearest))
            if not ok:
                stats["ties_farther"] += 1
        if len(touched) >= 2 and not wave:
            others = [uid for uid in touched if uid != record["hit_target"]]
            CHECKS.ok("first_hit", not any(uid in damaged for uid in others),
                      "%s round %s: path crossed %s, damaged %s" % (where, event["round"], touched, damaged))
    else:
        CHECKS.ok("first_hit", not damaged,
                  "%s round %s: no touch (%s) but damaged %s" % (where, event["round"], expected_type, damaged))
        if expected_type == "central_wall":
            stats["wall"] += 1
        else:
            stats["ground"] += 1


# ------------------------------------------------------------------ one seeded match
def next_alive(roster, alive, previous):
    start = roster.index(previous) + 1 if previous else 0
    for step in range(len(roster)):
        uid = roster[(start + step) % len(roster)]
        if uid in alive:
            return uid
    return None


def play_match(units, seed, stats, noise_by_team=None):
    rng = random.Random(seed * 7919 + units)
    heroes_red = [rng.choice(HERO_IDS) for _ in range(units)]
    heroes_white = [rng.choice(HERO_IDS) for _ in range(units)]
    where = "units=%d seed=%d" % (units, seed)
    session = server.Session(seed=seed, units=units, hero_red=heroes_red, hero_white=heroes_white,
                             clock=lambda: 0.0, human_turn_seconds=0, turn_seconds=100)
    eng = session.engine
    observer = Observer(eng)
    rosters = {team: sorted(uid for uid in eng.units if eng.units[uid]["team"] == team)
               for team in ("red", "white")}
    move_rng = random.Random(seed * 104729 + units)   # separate stream: the move decisions never change the aim stream
    cap = tuning.round_cap(units)
    ref_pity = {"red": 0, "white": 0}
    noise_by_team = noise_by_team or {}
    # hp scale: start and max hp of every unit follow shared/team_tuning.json (independent formula)
    for uid, unit in eng.units.items():
        template = HEROES[unit["hero"]]
        want = (template["hp"] if units == 1 else
                int(math.floor(max(template["hp"] * TT["hp_scale"][str(units)], TT["hp_floor_hits"] * template["dmg"]) + 0.5)))
        CHECKS.ok("hp_scale", unit["max_hp"] == want and unit["hp"] == float(want),
                  "%s %s (%s): max_hp %s hp %s expected %s" % (where, uid, unit["hero"], unit["max_hp"], unit["hp"], want))
    gap = min_teammate_gap(eng)
    CHECKS.ok("gap", gap is None or gap >= MIN_GAP - 1e-6, "%s: spawn gap %s" % (where, gap))
    previous = {"red": None, "white": None}
    death_round = {}
    turns = {"red": [], "white": []}
    seat_of = {"red": "red", "white": "white"}
    phase_of = {"red": "human", "white": "agent"}
    rounds = 0

    while session.winner is None:
        if eng.round_num > MAX_ROUNDS:
            CHECKS.ok("guard", False, "%s still running at round %d (guard %d)" % (where, eng.round_num, MAX_ROUNDS))
            stats["guard_hits"] += 1
            return
        rnd = eng.round_num
        for team in ("red", "white"):
            if session.phase == "over":
                break
            CHECKS.ok("phase", session.phase == phase_of[team],
                      "%s round %d: expected phase %s for %s, got %s" % (where, rnd, phase_of[team], team, session.phase))
            alive = {uid for uid in rosters[team] if eng.units[uid]["alive"]}
            active = session._active_unit(team)
            expected = next_alive(rosters[team], alive, previous[team])
            CHECKS.ok("rotation", active == expected,
                      "%s round %d %s: active=%s expected=%s previous=%s alive=%s" % (
                          where, rnd, team, active, expected, previous[team], sorted(alive)))
            if active != expected:
                kind = "prev_alive" if previous[team] in alive else "prev_dead"
                stats["rot_" + kind] += 1
            CHECKS.ok("rotation", active is not None and eng.units[active]["alive"],
                      "%s round %d %s: active %s is not alive" % (where, rnd, team, active))
            stats["turns"] += 1
            if len(alive) > 1:
                if active == previous[team]:
                    stats["repeat"] += 1
                CHECKS.ok("no_repeat", active != previous[team],
                          "%s round %d %s: %s acts twice in a row with living teammates %s" % (
                              where, rnd, team, active, sorted(alive - {active})))
            turns[team].append((rnd, active))
            previous[team] = active
            seat = session.seats[seat_of[team]]
            # a frozen teammate must be refused
            for other in sorted(alive - {active}):
                if other in session.skipped_units:
                    continue
                refused = False
                try:
                    session.call("submit_action", {"unit": other, "round": rnd,
                                                   "action": {"type": "throw", "angle": 55, "power": 60}}, seat)
                except server.ToolError as error:
                    refused = "frozen" in str(error)
                CHECKS.ok("frozen", refused, "%s round %d: teammate %s was not refused as frozen" % (where, rnd, other))
                break
            if active not in session.skipped_units and move_rng.random() < MOVE_RATE:
                direction = move_rng.choice(("forward", "backward"))
                try:
                    moved = session.call("submit_action", {"unit": active, "round": rnd,
                                                           "action": {"type": "move", "direction": direction}}, seat)
                except server.ToolError:
                    moved = None   # slowed unit: a refused move is legal
                if moved is not None:
                    stats["moves"] += 1
                    if moved.get("blocked_by_teammate"):
                        stats["moves_stepped_back"] += 1
                    gap = min_teammate_gap(eng)
                    CHECKS.ok("gap", gap is None or gap >= MIN_GAP - 1e-6,
                              "%s round %d: gap %.2f px after %s moved %s (x %.1f -> %.1f)" % (
                                  where, rnd, gap if gap is not None else -1.0, active, direction,
                                  moved["x_before"], moved["x_after"]))
            if active not in session.skipped_units:
                angle, power, _target = aim(rng, eng, eng.units[active], noise_by_team.get(team))
                session.call("submit_action", {"unit": active, "round": rnd,
                                               "action": {"type": "throw", "angle": angle, "power": power}}, seat)
            else:
                stats["skipped_turns"] += 1
            summary = session.call("end_turn", {"round": rnd, "phase": phase_of[team]}, seat)
            if team == "white" or session.phase == "over":
                for event in observer.drain():
                    verify_event(event, stats, where, units, ref_pity)
                for unit in eng.units.values():
                    CHECKS.ok("hp_scale", unit["hp"] <= unit["max_hp"] + 1e-9 and unit["hp"] >= 0,
                              "%s round %d: %s hp %s max %s" % (where, rnd, unit["id"], unit["hp"], unit["max_hp"]))
                for record in eng.throw_log[-4:]:
                    if record["round"] == rnd and record.get("knockback"):
                        stats["knockbacks"] += 1
                state = session.public_state()
                if units > 1:
                    CHECKS.ok("pity", dict(eng.pity) == ref_pity and all(
                        state["pity"][t]["misses"] == ref_pity[t] and state["pity"][t]["bonus"] == pity_ref(ref_pity[t])
                        for t in ("red", "white")),
                        "%s round %d: engine pity %s state %s reference %s" % (where, rnd, eng.pity, state.get("pity"), ref_pity))
                    for t, o in (("red", "white"), ("white", "red")):
                        stack = min(CB["max_total_multiplier"], underdog_ref(share_of(eng, t), share_of(eng, o)) * (1 + pity_ref(ref_pity[t])))
                        CHECKS.ok("underdog", abs(state["comeback_multiplier"][t] - stack) < 0.0006 and 1.0 <= state["comeback_multiplier"][t] <= CB["max_total_multiplier"],
                                  "%s round %d: comeback_multiplier %s expected %s" % (where, rnd, state["comeback_multiplier"][t], stack))
                        want = round(underdog_ref(share_of(eng, t), share_of(eng, o)) - 1.0, 3)
                        CHECKS.ok("underdog", state["underdog_bonus"][t] == want and want >= 0.0,
                                  "%s round %d: underdog_bonus %s expected %s" % (where, rnd, state["underdog_bonus"][t], want))
                else:
                    CHECKS.ok("one_unit", "pity" not in state and "underdog_bonus" not in state and "winner_reason" not in state,
                              "%s round %d: team-only keys in a 1v1 state" % (where, rnd))
                gap = min_teammate_gap(eng)
                CHECKS.ok("gap", gap is None or gap >= MIN_GAP - 1e-6,
                          "%s round %d: teammate gap %.2f px after the round (knockback)" % (
                              where, rnd, gap if gap is not None else -1.0))
                stats["min_gap"] = gap if gap is not None and gap < stats["min_gap"] else stats["min_gap"]
                # winner bookkeeping after the round resolved
                red_alive = any(u["alive"] for u in eng.units.values() if u["team"] == "red")
                white_alive = any(u["alive"] for u in eng.units.values() if u["team"] == "white")
                expected_winner = ("draw" if not red_alive and not white_alive else
                                   "white" if not red_alive else "red" if not white_alive else None)
                expected_reason = None
                if expected_winner is None and eng.round_num > cap:
                    expected_winner, expected_reason = cap_reference(eng), "round_cap"
                CHECKS.ok("cap", session.winner_reason == expected_reason and summary.get("winner_reason") == expected_reason,
                          "%s round %d: winner_reason session=%r summary=%r expected=%r (counter %d, cap %s)" % (
                              where, rnd, session.winner_reason, summary.get("winner_reason"), expected_reason,
                              eng.round_num, cap))
                if expected_reason == "round_cap":
                    stats["capped"] += 1
                CHECKS.ok("winner", session.winner == expected_winner and summary.get("winner") == expected_winner,
                          "%s round %d: session.winner=%r summary=%r expected=%r red_alive=%s white_alive=%s" % (
                              where, rnd, session.winner, summary.get("winner"), expected_winner, red_alive, white_alive))
                CHECKS.ok("winner", (session.phase == "over") == (expected_winner is not None),
                          "%s round %d: phase=%s winner=%r" % (where, rnd, session.phase, expected_winner))
                for uid, unit in eng.units.items():
                    if not unit["alive"] and uid not in death_round:
                        death_round[uid] = rnd
                break
        rounds += 1

    # after the match
    CHECKS.ok("cap_len", session.engine.round_num - 1 <= cap and session.engine.round_num <= cap + 1,
              "%s: %d rounds resolved, cap %s" % (where, session.engine.round_num - 1, cap))
    CHECKS.ok("winner", session.winner in ("red", "white", "draw"), "%s: no winner at exit" % where)
    capped = session.winner_reason == "round_cap"
    losers = {"red": "white", "white": "red", "draw": None}.get(session.winner)
    if losers and not capped:
        CHECKS.ok("winner", all(not u["alive"] for u in eng.units.values() if u["team"] == losers),
                  "%s: winner %s but a %s unit lives" % (where, session.winner, losers))
    if losers:
        stats["last_winner_alive"].append(sum(1 for u in eng.units.values() if u["team"] == session.winner and u["alive"]))
    refused = False
    try:
        session.call("submit_action", {"unit": rosters["red"][0],
                                       "action": {"type": "throw", "angle": 55, "power": 60}}, session.seats["red"])
    except server.ToolError as error:
        refused = "over" in str(error) or "dead" in str(error)
    CHECKS.ok("winner", refused, "%s: an action was accepted after the match ended" % where)
    # throw log: no unit throws in a round after its death round, no dead unit active
    for record in eng.throw_log:
        died = death_round.get(record["unit"])
        CHECKS.ok("throw_log", died is None or record["round"] <= died,
                  "%s: %s threw in round %s after dying in round %s" % (where, record["unit"], record["round"], died))
    for team in ("red", "white"):
        for rnd, uid in turns[team]:
            died = death_round.get(uid)
            CHECKS.ok("throw_log", died is None or rnd <= died,
                      "%s: dead unit %s was active in round %s (died round %s)" % (where, uid, rnd, died))
    stats["rounds"].append(session.engine.round_num - 1)
    stats["wins"][session.winner] = stats["wins"].get(session.winner, 0) + 1
    stats["winners"].append(session.winner)
    LOG.info("match %s heroes red=%s white=%s rounds=%d winner=%s", where, heroes_red, heroes_white,
             session.engine.round_num - 1, session.winner)


# ------------------------------------------------------------------ constructed crossing shots
def build_game(units, thrower_team, seed, spacing, base, wind, heroes_thrower, heroes_target):
    heroes = {"red": None, "white": None}
    target_team = "white" if thrower_team == "red" else "red"
    heroes[thrower_team] = heroes_thrower
    heroes[target_team] = heroes_target
    # TrackedGameState (what Session plays) leaves units without a queued throw idle; the plain
    # GameState would auto-throw for every "subagent" unit and pollute the one-shot measurement.
    eng = server.TrackedGameState(mode="human_vs_agent", seed=seed, units=units,
                                  hero_red=heroes["red"], hero_white=heroes["white"])
    eng.wind = wind
    thrower_x = 480.0 if thrower_team == "red" else 1440.0
    for index in range(1, units + 1):
        eng.units["%s_%d" % (thrower_team, index)]["x"] = thrower_x
        # enemies ordered by id from the thrower outward, i.e. id 1 is the nearest to the thrower
        offset = (index - 1) * spacing
        eng.units["%s_%d" % (target_team, index)]["x"] = float(base + offset if thrower_team == "red" else base - offset)
    return eng, target_team


def run_crossing(units, stats):
    rng = random.Random(SEED_BASE + 31 * units)
    for thrower_team in ("red", "white"):
        valid = 0
        for case in range(CROSSING_CASES):
            spacing = rng.choice((120, 150, 200))
            if thrower_team == "red":
                base = rng.uniform(1150.0, 1680.0 - (units - 1) * spacing)
            else:
                base = rng.uniform(240.0 + (units - 1) * spacing, 700.0)
                base = min(base, 700.0)
            wind = round(rng.uniform(-4.0, 4.0), 1)
            seed = 9000 + case
            heroes_thrower = [rng.choice(HERO_IDS)] * units
            heroes_target = [rng.choice(HERO_IDS) for _ in range(units)]
            eng, target_team = build_game(units, thrower_team, seed, spacing, base, wind,
                                          heroes_thrower, heroes_target)
            shooter = eng.units["%s_1" % thrower_team]
            origin = {"x": shooter["x"], "y": shooter["y"], "facing": shooter["facing"], "launch": shooter["launch"]}
            enemies = [(u["id"], u["hero"], u["x"]) for u in eng.units.values() if u["team"] == target_team]
            shots = []
            for angle in range(26, 80, 2):
                for power in range(20, 101):
                    points, end = flight(origin["x"], origin["y"], origin["facing"], origin["launch"],
                                         angle, power, wind, eng.central_wall_hp, wave=shooter["weapon"] == "proj_soundwave", sweep=shooter["weapon"] != "proj_soundwave")
                    touched = first_touches(points, shooter["weapon"], enemies)
                    steps = sorted(touched.values())
                    if len(touched) >= 2 and len(set(steps)) == len(steps):
                        shots.append((angle, power, touched))
            if not shots:
                continue
            angle, power, touched = rng.choice(shots)
            order = sorted(touched, key=lambda uid: touched[uid])
            # variant A: everybody alive, first touched takes the hit
            # variant B: the first touched is already dead, the next touched takes it
            for variant, expected in (("A", order[0]), ("B", order[1] if len(order) > 1 else None)):
                eng2, _ = build_game(units, thrower_team, seed, spacing, base, wind, heroes_thrower, heroes_target)
                if variant == "B":
                    dead = eng2.units[order[0]]
                    dead.update({"alive": False, "hp": 0.0})
                    living = [(uid, hero, x) for uid, hero, x in enemies if uid != order[0]]
                    steps_b = first_touches(flight(origin["x"], origin["y"], origin["facing"], origin["launch"],
                                                   angle, power, wind, eng2.central_wall_hp, wave=shooter["weapon"] == "proj_soundwave", sweep=shooter["weapon"] != "proj_soundwave")[0],
                                            shooter["weapon"], living)
                    if not steps_b:
                        continue
                    expected = min(steps_b, key=lambda uid: steps_b[uid])
                hp_before = {uid: u["hp"] for uid, u in eng2.units.items()}
                eng2.submit_throw("%s_1" % thrower_team, float(angle), float(power))
                result = eng2.resolve_round()
                record = next(r for r in result["results"] if r.get("unit_id") == "%s_1" % thrower_team and "hit_type" in r)
                lost = sorted(uid for uid, u in eng2.units.items() if u["hp"] < hp_before[uid])
                if shooter["weapon"] == "proj_soundwave":
                    # area effect: the touched unit plus every living enemy within 105 px of the wave centre
                    centre = record["landing_x"]
                    living = [uid for uid, u in eng2.units.items() if u["team"] == target_team and hp_before[uid] > 0]
                    near = {uid for uid in living if abs(eng2.units[uid]["x"] - centre) <= WAVE_BOX[0] - 0.06}
                    edge = {uid for uid in living if abs(eng2.units[uid]["x"] - centre) <= WAVE_BOX[0] + 0.06}
                    expected_lost = sorted({expected} | near)
                    if {expected} | near <= set(lost) <= {expected} | edge:
                        expected_lost = lost   # a unit within 0.06 px of the 105 px edge: either side is within logging precision
                else:
                    expected_lost = [expected]
                where = "crossing units=%d %s case=%d variant=%s shot=%d/%d spacing=%d wind=%.1f" % (
                    units, thrower_team, case, variant, angle, power, spacing, wind)
                CHECKS.ok("crossing", record["hit_type"] == "hero" and record["hit_target"] == expected,
                          "%s: expected first living touched %s, engine hit_type=%s target=%s touched=%s" % (
                              where, expected, record["hit_type"], record["hit_target"], touched))
                CHECKS.ok("crossing", lost == expected_lost,
                          "%s: expected %s to lose hp, lost=%s" % (where, expected_lost, lost))
                stats["crossing_checked"] += 1
            valid += 1
        stats["crossing_valid_" + thrower_team] = valid
        CHECKS.ok("crossing", valid >= 20, "units=%d %s: only %d of %d constructed shots crossed two enemy boxes (need 20)"
                  % (units, thrower_team, valid, CROSSING_CASES))


# ------------------------------------------------------------------ main
def new_stats():
    return {"rounds": [], "wins": {}, "throws": 0, "hero_hits": 0, "wall": 0, "ground": 0, "cross_two": 0,
            "ties": 0, "ties_farther": 0, "rot_prev_alive": 0, "rot_prev_dead": 0, "repeat": 0, "turns": 0, "guard_hits": 0, "skipped_turns": 0, "last_winner_alive": [],
            "crossing_checked": 0, "ramped_hits": 0, "plain_hits": 0, "wave_hits": 0, "ties_shooter_metric_differs": 0,
            "moves": 0, "moves_stepped_back": 0, "knockbacks": 0, "capped": 0, "min_gap": float("inf"),
            "capped_stack_hits": 0, "underdog_hits": 0, "pity_hits": 0, "pity_cap_hits": 0, "near_misses": 0, "near_miss_edges": [], "plain_misses": 0,
            "winners": []}


def skill_gap():
    """Expert / decent against sloppy on the same seeds with the sides swapped; the weaker team's win share and the match length."""
    say("skill gap: %d seeds x 2 sides per size, sides swapped on identical heroes and seeds, move rate %.2f" % (MATCHES_PER_N, MOVE_RATE))
    pairs = (("expert 1.6 vs sloppy 9", 1.6, 9.0), ("decent 5 vs sloppy 9", 5.0, 9.0), ("expert 1.6 vs decent 5", 1.6, 5.0))
    table = []
    for units in SIZES:
        for label, strong, weak in pairs:
            weak_wins = strong_wins = draws = capped_n = 0
            rounds = []
            for index in range(MATCHES_PER_N):
                seed = SEED_BASE + units * 1000 + index
                for strong_team in ("red", "white"):
                    stats = new_stats()
                    weak_team = "white" if strong_team == "red" else "red"
                    try:
                        play_match(units, seed, stats, {strong_team: strong, weak_team: weak})
                    except Exception:
                        CHECKS.ok("exception", False, "gap units=%d seed=%d\n%s" % (units, seed, traceback.format_exc()))
                        continue
                    winner = stats["winners"][-1]
                    weak_wins += winner == weak_team
                    strong_wins += winner == strong_team
                    draws += winner == "draw"
                    capped_n += stats["capped"]
                    rounds.extend(stats["rounds"])
            n = len(rounds) or 1
            rounds.sort()
            lo, hi = length_band(units)
            inside = sum(1 for r in rounds if lo <= r <= hi)
            table.append((units, label, n, 100.0 * weak_wins / n, 100.0 * strong_wins / n, sum(rounds) / n,
                          rounds[int(0.1 * (n - 1))] if rounds else 0, rounds[int(0.9 * (n - 1))] if rounds else 0,
                          100.0 * inside / n, capped_n, draws))
    say("")
    say("%-5s %-26s %-6s %-12s %-12s %-24s %-10s %-6s %s" % ("size", "pair", "n", "weaker wins", "stronger", "rounds mean/p10/p90", "in band", "caps", "draws"))
    for units, label, n, ww, sw, mean, p10, p90, inside, caps, draws in table:
        say("%-5s %-26s %-6d %-12s %-12s %-24s %-10s %-6d %d" % ("%dv%d" % (units, units), label, n, "%.1f%%" % ww, "%.1f%%" % sw,
                                                              "%.1f/%d/%d" % (mean, p10, p90), "%.0f%%" % inside, caps, draws))


def finish(started):
    for name in sorted(set(CHECKS.passed) | set(CHECKS.failed)):
        say("check %-10s pass %-6d fail %d" % (name, CHECKS.passed.get(name, 0), CHECKS.failed.get(name, 0)))
    failed = CHECKS.total_failed()
    for message in CHECKS.messages[:12]:
        say(message.splitlines()[0][:300])
    if failed > 12:
        say("... %d more failures, see %s" % (failed - 12, LOG_PATH))
    say("elapsed %.1fs  failures %d  log %s" % (time.time() - started, failed, LOG_PATH))
    say("RESULT %s" % ("PASS" if failed == 0 else "FAIL"))
    return 0 if failed == 0 else 1




def main():
    started = time.time()
    say("sim_team_headless: %d matches per size, sizes %s, guard %d rounds, seeds from %d" % (
        MATCHES_PER_N, list(SIZES), MAX_ROUNDS, SEED_BASE))
    # preconditions: the page hit boxes the reference uses must equal the shared data the engine reads
    for hero in HERO_IDS:
        box = HEROES[hero]["hitBox"]
        CHECKS.ok("data", (float(box["halfWidth"]), float(box["height"])) == BOX[hero],
                  "heroes.json hitBox of %s is %s, page rule is %s" % (hero, box, BOX[hero]))
    CHECKS.ok("data", (engine._WIND_TAIL, engine._WIND_HEAD) == (K["WIND_TAIL"], K["WIND_HEAD"]) == (56.0, 84.0), "wind acceleration constants %s %s" % (engine._WIND_TAIL, engine._WIND_HEAD))
    if MODE == "gap":
        skill_gap()
        return finish(started)
    all_stats = {}
    one = new_stats()
    for index in range(ONE_MATCHES):   # N = 1: the comeback pack, ramp, cap and hp scale must stay out of it
        seed = SEED_BASE + 1000 * 9 + index
        try:
            play_match(1, seed, one)
        except Exception:
            CHECKS.ok("exception", False, "units=1 seed=%d\n%s" % (seed, traceback.format_exc()))
    for units in SIZES:
        stats = new_stats()
        all_stats[units] = stats
        for index in range(MATCHES_PER_N):
            seed = SEED_BASE + units * 1000 + index
            try:
                play_match(units, seed, stats)
            except Exception:
                CHECKS.ok("exception", False, "units=%d seed=%d\n%s" % (units, seed, traceback.format_exc()))
        try:
            run_crossing(units, stats)
        except Exception:
            CHECKS.ok("exception", False, "crossing units=%d\n%s" % (units, traceback.format_exc()))

    say("")
    r1 = sorted(one["rounds"]) or [0]
    say("1v1 (%d matches, nothing of the team rules may show): rounds mean %.1f max %d, ramped hits %d, near misses %d, caps %d" % (
        len(one["rounds"]), sum(r1) / len(r1), r1[-1], one["ramped_hits"], one["near_misses"], one["capped"]))
    say("%-6s %-8s %-22s %-8s %-10s %-9s %-9s %-10s %s" % (
        "size", "matches", "rounds min/mean/max", "throws", "hits/thr", "wall/thr", "cross2", "ties(far)", "wins red/white/draw"))
    for units in SIZES:
        s = all_stats[units]
        n = len(s["rounds"])
        rounds = s["rounds"] or [0]
        wins = s["wins"]
        say("%-6s %-8d %-22s %-8d %-10.3f %-9.3f %-9d %-10s %d/%d/%d" % (
            "%dv%d" % (units, units), n,
            "%d/%.1f/%d" % (min(rounds), sum(rounds) / max(1, n), max(rounds)),
            s["throws"], s["hero_hits"] / max(1, s["throws"]), s["wall"] / max(1, s["throws"]),
            s["cross_two"], "%d(%d)" % (s["ties"], s["ties_farther"]),
            wins.get("red", 0), wins.get("white", 0), wins.get("draw", 0)))
        say("       skipped turns %d, guard hits %d, crossing checks %d (valid shots red %d, white %d), "
            "survivors of winner mean %.2f" % (
                s["skipped_turns"], s["guard_hits"], s["crossing_checked"],
                s.get("crossing_valid_red", 0), s.get("crossing_valid_white", 0),
                sum(s["last_winner_alive"]) / max(1, len(s["last_winner_alive"]))))
    for units in SIZES:
        s = all_stats[units]
        rounds = sorted(s["rounds"]) or [0]
        n = len(rounds)
        lo, hi = length_band(units)
        inside = sum(1 for r in rounds if lo <= r <= hi)
        say("%dv%d rounds per match: mean %.1f  p10 %d  p50 %d  p90 %d  max %d  inside %.1f-%.1f (0.5-1.5 x expected %.1f): %.0f%%  ended by the cap (%d): %d  [noise %.1f, move rate %.2f]" % (
            units, units, sum(rounds) / n, rounds[int(0.1 * (n - 1))], rounds[int(0.5 * (n - 1))],
            rounds[int(0.9 * (n - 1))], rounds[-1], lo, hi, EXPECTED_ROUNDS[units], 100.0 * inside / n,
            tuning.round_cap(units), s["capped"], AIM_NOISE, MOVE_RATE))
        edges = sorted(s["near_miss_edges"])
        say("%dv%d comeback: near misses %d (edge p50 %s px, max %s px), plain misses %d, underdog-boosted hits %d, hits with a pity charge %d (at the pity cap %d), stacks cut by the 2.3 cap %d" % (
            units, units, s["near_misses"], "%.0f" % edges[len(edges) // 2] if edges else "-",
            "%.0f" % edges[-1] if edges else "-", s["plain_misses"], s["underdog_hits"], s["pity_hits"], s["pity_cap_hits"], s["capped_stack_hits"]))
        say("%dv%d rules: ramped hits %d (plain %d), wave hits %d, ties %d (engine off the projectile-nearest rule: %d; the old shooter metric would have flagged %d), "
            "moves %d (stepped back %d), knockbacks %d, smallest teammate gap seen %s px" % (
                units, units, s["ramped_hits"], s["plain_hits"], s["wave_hits"], s["ties"], s["ties_farther"],
                s["ties_shooter_metric_differs"], s["moves"], s["moves_stepped_back"], s["knockbacks"],
                "n/a" if s["min_gap"] == float("inf") else "%.1f" % s["min_gap"]))
    for units in SIZES:
        s = all_stats[units]
        say("%dv%d rotation: %d turns, %d off-order (previous alive %d, previous dead %d), %d repeats with a living teammate" % (
            units, units, s["turns"], s["rot_prev_alive"] + s["rot_prev_dead"], s["rot_prev_alive"],
            s["rot_prev_dead"], s["repeat"]))
    say("")
    return finish(started)
if __name__ == "__main__":
    try:
        code = main()
    except Exception:
        LOG.error("fatal\n%s", traceback.format_exc())
        print("ERROR fatal, see %s" % LOG_PATH)
        code = 1
    logging.shutdown()
    sys.exit(code)
