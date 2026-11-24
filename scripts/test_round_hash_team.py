#!/usr/bin/env python3
"""Team-battle round hash (2026-11-17): every unit of both teams, ordered by id; same vectors as the JS test."""
import copy
import json
import os

from round_hash_py import canonical_text, engine_unit_id, hash_state, unit_ids, world_unit_id

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(_ROOT, "shared", "round_hash_golden.json"), encoding="utf-8") as _input:
    GOLDEN = json.load(_input)


def raises(function, exception, text=""):
    try:
        function()
    except exception as error:
        assert text in str(error), "%s not in %s" % (text, error)
        return
    raise AssertionError("expected %s" % exception.__name__)


assert GOLDEN["cases"][0]["name"] == "state-00" and GOLDEN["cases"][0]["hash"] == "696f9f69"
assert GOLDEN["cases"][1]["hash"] == "2df7b83c"
assert len(GOLDEN["cases"]) >= 33
team_cases = [entry for entry in GOLDEN["cases"] if entry["name"].startswith("team-")]
for size in (1, 2, 3):
    assert any(entry["state"]["teamSize"] == size for entry in team_cases), size
for entry in team_cases:
    state, size = entry["state"], entry["state"]["teamSize"]
    assert len(state["units"]) == 2 * size, entry["name"]
    assert canonical_text(state) == entry["canonical"] and hash_state(state) == entry["hash"], entry["name"]
    rows = entry["canonical"].split("\n")
    ids = [row.split(",")[0] for row in rows[:2 * size]]
    assert len(rows) == 2 * size + 4 and ids == sorted(ids), entry["name"]
    if size > 1:
        assert ids == unit_ids(size)
    reversed_state = copy.deepcopy(state)
    reversed_state["units"].reverse()
    assert hash_state(reversed_state) == entry["hash"], entry["name"] + " reversed"
    keyed = copy.deepcopy(state)
    keyed["units"] = {unit["id"]: {k: v for k, v in unit.items() if k != "id"} for unit in state["units"]}
    assert hash_state(keyed) == entry["hash"], entry["name"] + " keyed"
    for index in range(2 * size):
        for edit in (lambda u: u.update(x=u["x"] + 1), lambda u: u.update(y=u["y"] + 1),
                     lambda u: u.update(hp=u["hp"] + 0.1), lambda u: u.update(alive=not u["alive"]),
                     lambda u: u.update(statuses=list(u.get("statuses") or []) + ["stun"])):
            changed = copy.deepcopy(state)
            edit(changed["units"][index])
            assert hash_state(changed) != entry["hash"], (entry["name"], index)
assert any(not unit["alive"] and ",false," in entry["canonical"] for entry in team_cases for unit in entry["state"]["units"])

two = next(entry["state"] for entry in team_cases if entry["state"]["teamSize"] == 2)
missing = copy.deepcopy(two); missing["units"].pop()
raises(lambda: canonical_text(missing), TypeError, "every unit of both teams")
wrong = copy.deepcopy(two); wrong["units"][0]["id"] = "left_5"
raises(lambda: canonical_text(wrong), TypeError, "team units must be")
duplicate = copy.deepcopy(two); duplicate["units"][1]["id"] = duplicate["units"][0]["id"]
raises(lambda: canonical_text(duplicate), TypeError, "duplicate unit id")
bad_size = copy.deepcopy(two); bad_size["teamSize"] = 4
raises(lambda: canonical_text(bad_size), ValueError, "teamSize must be 1..3")
bad_id = copy.deepcopy(two); bad_id["units"][0]["id"] = "left_0,1"
raises(lambda: canonical_text(bad_id), TypeError, "unit id is invalid")
no_size = copy.deepcopy(two); del no_size["teamSize"]; no_size["units"].pop()
canonical_text(no_size)
legacy = next(entry["state"] for entry in team_cases if entry["state"]["teamSize"] == 1)
without_size = copy.deepcopy(legacy); del without_size["teamSize"]
assert hash_state(without_size) == hash_state(legacy)

table = {"red_1": "left_0", "red_2": "left_1", "red_3": "left_2", "white_1": "right_0", "white_2": "right_1",
         "white_3": "right_2", "left_1": "left_1", "right_2": "right_2", "left": "left", "right": "right"}
for key, value in table.items():
    assert world_unit_id(key) == value, key
for bad in ("red_0", "red_4", "blue_1", "", "left_10", "x", None):
    raises(lambda bad=bad: world_unit_id(bad), TypeError)
for world, engine_id in (("left_0", "red_1"), ("left_2", "red_3"), ("right_0", "white_1"), ("right_1", "white_2"), ("red_2", "red_2"), ("white_3", "white_3")):
    assert engine_unit_id(world) == engine_id, world
for bad in ("left", "right", "left_3", "red_0", "x", "", None):
    raises(lambda bad=bad: engine_unit_id(bad), TypeError)
for engine_id in ("red_1", "red_2", "red_3", "white_1", "white_2", "white_3"):
    assert engine_unit_id(world_unit_id(engine_id)) == engine_id, engine_id
mcp_named = copy.deepcopy(two)
renamed = {"left_0": "red_1", "left_1": "red_2", "right_0": "white_1", "right_1": "white_2"}
for unit in mcp_named["units"]:
    unit["id"] = world_unit_id(renamed[unit["id"]])
assert hash_state(mcp_named) == hash_state(two)
print("PASS: team round hash (%d vectors for N=1..3; order, field, roster and id-mapping checks)" % len(team_cases))
