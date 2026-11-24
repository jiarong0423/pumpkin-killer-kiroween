#!/usr/bin/env python3
import copy
import json
import os

from round_hash_py import canonical_text, hash_state

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(_ROOT, "shared", "round_hash_golden.json"), encoding="utf-8") as _input:
    GOLDEN = json.load(_input)

for entry in GOLDEN["cases"]:
    assert canonical_text(entry["state"]) == entry["canonical"], entry["name"] + " canonical text"
    assert hash_state(entry["state"]) == entry["hash"], entry["name"] + " hash"

base = GOLDEN["cases"][0]["state"]
small_difference = copy.deepcopy(base)
small_difference["units"][0]["x"] += 0.0004
one_pixel_difference = copy.deepcopy(base)
one_pixel_difference["units"][0]["x"] += 1
assert hash_state(small_difference) == hash_state(base), "0.0004 px must not change the hash"
assert hash_state(one_pixel_difference) != hash_state(base), "1 px must change the hash"
print("PASS: %d round-hash goldens; sub-pixel stable and one-pixel sensitive" % len(GOLDEN["cases"]))
