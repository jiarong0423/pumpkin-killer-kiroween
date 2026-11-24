"""Python twin of js/comeback.js (near-miss damage, underdog bonus, pity charge) for team matches. Constants come from shared/comeback.json;
shared/comeback_vectors.json pins JS and Python to the same numbers."""
import json
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(_ROOT, "shared", "comeback.json"), encoding="utf-8") as _fh:
    _C = json.load(_fh)
NEAR_ENABLED = bool(_C["near_miss"].get("enabled", True))
NEAR_REACH = float(_C["near_miss"]["reach_px"])
NEAR_SCALE = float(_C["near_miss"]["scale"])
UNDERDOG_MAX = float(_C["underdog"]["max_bonus"])
UNDERDOG_FULL = float(_C["underdog"]["full_at_deficit"])
PITY_PER_MISS = float(_C["pity"]["per_miss"])
PITY_CAP = float(_C["pity"]["cap"])
MAX_TOTAL = float(_C["max_total_multiplier"])


def round1(x):
    """Round half up to 0.1, the same as Math.round(x * 10) / 10 for the values used here."""
    return int(x * 10 + 0.5) / 10.0 if x >= 0 else -int(-x * 10 + 0.5) / 10.0


def hp_share(units):
    hp = mx = 0.0
    for u in units:
        mx += u["maxHp"]
        if u["hp"] > 0:
            hp += u["hp"]
    return hp / mx if mx > 0 else 0.0


def near_miss_damage(base_dmg, e):
    if not (e > 0) or e > NEAR_REACH:
        return 0.0
    return round1(base_dmg * NEAR_SCALE * (1 - e / NEAR_REACH))


def underdog_multiplier(own_share, enemy_share):
    deficit = max(0.0, enemy_share - own_share)
    return 1 + min(UNDERDOG_MAX, deficit / UNDERDOG_FULL)


def pity_bonus(miss_count):
    return min(PITY_CAP, PITY_PER_MISS * max(0, miss_count))


def final_damage(weather_and_ramp_base, own_share, enemy_share, miss_count):
    return round1(weather_and_ramp_base * min(MAX_TOTAL, underdog_multiplier(own_share, enemy_share) * (1 + pity_bonus(miss_count))))
