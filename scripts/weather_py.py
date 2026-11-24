#!/usr/bin/env python3
"""Deterministic public round weather, kept equivalent to js/weather.js."""
import math
import re

ROUNDS_PER_WEATHER = 2
WEATHER = {
    "clear": {"attackMult": 1.0, "moveMult": 1.0, "windBonus": 0.0, "label": "Clear"},
    "rain": {"attackMult": 0.9, "moveMult": 1.0, "windBonus": 0.0, "label": "Rain"},
    "snow": {"attackMult": 1.0, "moveMult": 0.5, "windBonus": 0.0, "label": "Snow"},
    "storm": {"attackMult": 0.9, "moveMult": 1.0, "windBonus": 1.5, "label": "Storm"},
    "fog": {"attackMult": 1.0, "moveMult": 1.0, "windBonus": 0.0, "label": "Fog"},
}
WEIGHTS = {
    "graveyard": {"clear": 42, "rain": 20, "snow": 8, "storm": 5, "fog": 25},
    "church": {"clear": 24, "rain": 32, "snow": 6, "storm": 18, "fog": 20},
    "school": {"clear": 37, "rain": 27, "snow": 7, "storm": 4, "fog": 25},
    "bell_tower": {"clear": 34, "rain": 8, "snow": 24, "storm": 27, "fog": 7},
    "pumpkin_field": {"clear": 50, "rain": 8, "snow": 17, "storm": 4, "fog": 21},
    "default": {"clear": 40, "rain": 20, "snow": 12, "storm": 8, "fog": 20},
}
IDS = ("clear", "rain", "snow", "storm", "fog")


def is_num(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def to_int(value, fallback):
    return math.floor(value) if is_num(value) else fallback


def safe_seed(value):
    # JavaScript's bitwise OR converts the integer to signed int32.
    result = to_int(value, 0) & 0xffffffff
    return result - 0x100000000 if result >= 0x80000000 else result


def safe_round(value):
    return max(1, to_int(value, 1))


def scene_key(value):
    if not isinstance(value, str):
        return "default"
    key = re.sub(r"[\s-]+", "_", value.lower())
    return key if key in WEIGHTS else "default"


def sample(seed, block):
    point = (safe_seed(seed) * 97 + block * 37) % 100
    return point / 100


def id_for(seed, block, weights):
    point = math.floor(sample(seed, block) * 100 + 1e-8)
    total = 0
    for weather_id in IDS:
        total += weights[weather_id]
        if point < total:
            return weather_id
    return "clear"


def copy_weather(weather_id, starts_round, ends_round):
    effect = WEATHER.get(weather_id, WEATHER["clear"])
    return {
        "id": weather_id,
        "startsRound": starts_round,
        "endsRound": ends_round,
        "attackMult": effect["attackMult"],
        "moveMult": effect["moveMult"],
        "windBonus": effect["windBonus"],
        "label": effect["label"],
    }


def for_round(seed, round_number, scene_id):
    round_value = safe_round(round_number)
    block = math.floor((round_value - 1) / ROUNDS_PER_WEATHER)
    starts = block * ROUNDS_PER_WEATHER + 1
    return copy_weather(id_for(seed, block, WEIGHTS[scene_key(scene_id)]), starts,
                        starts + ROUNDS_PER_WEATHER - 1)


def apply_attack(weather, damage):
    value = float(damage) if is_num(damage) else 0.0
    if value <= 0:
        return 0
    multiplier = weather.get("attackMult") if isinstance(weather, dict) and is_num(weather.get("attackMult")) else 1
    return max(1, math.floor(value * multiplier * 10 + 0.5) / 10)


def apply_move(weather, pixels):
    distance = float(pixels) if is_num(pixels) else 0.0
    multiplier = weather.get("moveMult") if isinstance(weather, dict) and is_num(weather.get("moveMult")) else 1
    return math.floor(distance * multiplier * 10 + 0.5) / 10


def public_state(weather):
    value = weather if isinstance(weather, dict) else for_round(0, 1, "default")
    weather_id = value.get("id") if value.get("id") in WEATHER else "clear"
    return {
        "id": weather_id,
        "endsRound": safe_round(value.get("endsRound")),
        "attackMult": value.get("attackMult") if is_num(value.get("attackMult")) else 1,
        "moveMult": value.get("moveMult") if is_num(value.get("moveMult")) else 1,
    }


def hash_text(weather):
    value = weather if isinstance(weather, dict) else for_round(0, 1, "default")
    public = public_state(value)
    bonus = value.get("windBonus") if is_num(value.get("windBonus")) else 0
    return "%s,%d,%.1f,%.1f,%.1f" % (public["id"], public["endsRound"],
                                      public["attackMult"], public["moveMult"], bonus)
