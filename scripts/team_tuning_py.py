"""Python twin of js/team_tuning.js (team HP scale, late ramp, round cap). One unit per team returns the neutral value.
Constants are read from shared/team_tuning.json; shared/team_tuning_vectors.json pins JS and Python to the same numbers."""
import json
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(_ROOT, "shared", "team_tuning.json"), encoding="utf-8") as _fh:
    _C = json.load(_fh)
HP_SCALE = {int(k): float(v) for k, v in _C["hp_scale"].items()}
HP_FLOOR_HITS = float(_C["hp_floor_hits"])
RAMP_START = int(_C["ramp"]["start_round"])
RAMP_PER_ROUND = float(_C["ramp"]["per_round"])
ROUND_CAP = {int(k): int(v) for k, v in _C["round_cap"].items()}


def _round_half_up(x):
    return int(x + 0.5) if x >= 0 else -int(-x + 0.5)


def team_max_hp(hp, dmg, n):
    if n not in HP_SCALE:
        return hp
    return _round_half_up(max(hp * HP_SCALE[n], HP_FLOOR_HITS * dmg))


def ramp_multiplier(round_number, n):
    if n not in HP_SCALE or round_number < RAMP_START:
        return 1.0
    return round((1 + RAMP_PER_ROUND * (round_number - (RAMP_START - 1))) * 1e6) / 1e6


def round_cap(n):
    return ROUND_CAP.get(n, float("inf"))


def cap_winner(teams):
    """teams = {'left': [{'hp':..,'maxHp':..}], 'right': [...]} -> 'left' or 'right'."""
    def share(units):
        hp = mx = alive = 0
        for u in units:
            mx += u["maxHp"]
            if u["hp"] > 0:
                hp += u["hp"]
                alive += 1
        return (hp / mx if mx > 0 else 0.0), alive
    ls, la = share(teams["left"])
    rs, ra = share(teams["right"])
    if ls != rs:
        return "left" if ls > rs else "right"
    if la != ra:
        return "left" if la > ra else "right"
    return "right"
