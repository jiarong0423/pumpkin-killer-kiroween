#!/usr/bin/env python3
"""Portable deterministic match values, kept equivalent to js/determinism.js."""

UINT32_MAX = 0xffffffff
START_STEP = 36
LEFT_START = 252
RIGHT_START = 1296
START_CHOICES = 11
DOMAIN = {
    "wind": 0x51F15E1D,
    "startX": 0x5A17A7E1,
    "moveDie": 0x6D0D0001,
    "supplyDrop": 0x51A0D00D,
    "bounceCount": 0xB00CE001,
    "nunStunPick": 0x57A70001,
    "sideDraw": 0x51DE0001,
    "bigHit": 0xB16D0001,
}


def _uint32(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > UINT32_MAX:
        raise ValueError("%s must be a uint32 integer" % name)
    return value


def _side(value):
    result = _uint32(value, "side")
    if result not in (0, 1):
        raise ValueError("side must be 0 or 1")
    return result


def _positive(value, name):
    result = _uint32(value, name)
    if result < 1:
        raise ValueError("%s must be at least 1" % name)
    return result


def _mix32(value):
    value = ((value ^ (value >> 16)) * 0x85EBCA6B) & UINT32_MAX
    value = ((value ^ (value >> 13)) * 0xC2B2AE35) & UINT32_MAX
    return (value ^ (value >> 16)) & UINT32_MAX


def _hash(seed, domain, first, second):
    value = _mix32((_uint32(seed, "seed") + 0x9E3779B9) & UINT32_MAX)
    value = _mix32((value ^ domain) & UINT32_MAX)
    value = _mix32((value ^ _uint32(first, "hash input")) & UINT32_MAX)
    return _mix32((value ^ _uint32(second, "hash input")) & UINT32_MAX)


def wind(seed, round_number):
    seed_value = _uint32(seed, "seed")
    round_value = _positive(round_number, "round")
    tenths = (seed_value % 81) - 40 if round_value == 1 else (_hash(seed_value, DOMAIN["wind"], round_value, 0) % 81) - 40
    return tenths / 10


def start_x(seed, side, slot):
    side_value = _side(side)
    slot_value = _uint32(slot, "slot")
    start = LEFT_START if side_value == 0 else RIGHT_START
    return start + (_hash(seed, DOMAIN["startX"], side_value, slot_value) % START_CHOICES) * START_STEP


def move_die(seed, round_number, side):
    return 1 + (_hash(seed, DOMAIN["moveDie"], _positive(round_number, "round"), _side(side)) % 6)


def supply_drop(seed, round_number):
    value = _hash(seed, DOMAIN["supplyDrop"], _positive(round_number, "round"), 0)
    return {"side": value & 1, "item": (value >> 1) & 1, "offset": -120 + ((value >> 2) % 241)}


def bounce_count(seed, round_number, throw_id):
    return 1 + (_hash(seed, DOMAIN["bounceCount"], _positive(round_number, "round"), _uint32(throw_id, "throwId")) % 6)


def nun_stun_pick(seed, round_number, throw_id, n):
    return _hash(seed, DOMAIN["nunStunPick"], _positive(round_number, "round"), _uint32(throw_id, "throwId")) % _positive(n, "n")


BIG_HIT_ONE_IN = 10   # twin of js/determinism.js: one throw in ten may take more than half of a unit's health bar


def big_hit_pass(seed, round_number, throw_id):
    return _hash(seed, DOMAIN["bigHit"], _positive(round_number, "round"), _uint32(throw_id, "throwId")) % BIG_HIT_ONE_IN == 0


def side_draw(seed):
    """Return 0 for human left or 1 for human right, independent of coin_toss."""
    return _hash(seed, DOMAIN["sideDraw"], 0, 0) & 1


def coin_toss(seed):
    """Return the opening side: 0 for left, 1 for right."""
    return _hash(seed, 7001, 0, 0) & 1
