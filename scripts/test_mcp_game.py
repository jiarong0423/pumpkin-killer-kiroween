#!/usr/bin/env python3
"""Automated Test Suite for Pumpkin Killer MCP Game Server.

Tests:
1. Human vs Sub-agent mode
2. Random Controller Assignment mode
3. Agent vs Agent (Auto Battle) mode
4. Ballistic physics & central wall obstruction
"""
import sys
import json
from mcp_game_server import GameState, handle_mcp_request, WALL_HIT_DMG


def test_modes():
    print("--- 1. Testing Random Assignment Mode ---")
    g_rand = GameState(mode="random_assignment", seed=42)
    state = g_rand.get_public_state()
    controllers = [u["controller"] for u in state["units"].values()]
    print(f"Randomly assigned controllers: {controllers}")
    assert "human" in controllers and "subagent" in controllers, "Both controllers should exist"
    print("✅ Random Assignment Passed!")

    print("\n--- 2. Testing Central Wall Collision ---")
    # A mid-power low angle throw from red_3 (x=560) directed right into the wall (x=890)
    g_pve = GameState(mode="human_vs_agent", seed=123, units=3)
    g_pve.units["red_3"]["x"] = 560.0  # start x is random now; pin it for a known shot
    g_pve.wind = 0.0  # no wind: the test is about the wall, and the wind (x1.5 on 2026-11-15) would change the landing
    res = g_pve.submit_throw("red_3", angle=15.0, power=65.0)
    round_res = g_pve.resolve_round()
    hit_types = [r["hit_type"] for r in round_res["results"] if r["unit_id"] == "red_3"]
    print(f"Red 3 low angle throw hit: {hit_types[0]}")
    assert hit_types[0] == "central_wall", "Low angle must hit central wall"
    print("✅ Central Wall Block Passed!")

    print("\n--- 3. Testing High Arc Clearance & Hit ---")
    # High power arc should clear wall and land on enemy territory
    g_pve2 = GameState(mode="human_vs_agent", seed=456, units=3)
    g_pve2.units["red_3"]["x"] = 560.0
    g_pve2.submit_throw("red_3", angle=58.0, power=82.0)
    r2 = g_pve2.resolve_round()
    red3_res = next(r for r in r2["results"] if r["unit_id"] == "red_3")
    print(f"Red 3 high arc landing X: {red3_res['landing_x']} (Wall ends at 1030)")
    assert red3_res["landing_x"] > 1030, "High arc must clear the wall!"
    print("✅ High Arc Wall Clearance Passed!")

    print("\n--- 4. Testing JSON-RPC MCP Interface ---")
    req = {
        "jsonrpc": "2.0",
        "id": 101,
        "method": "get_public_state",
        "params": {}
    }
    resp = handle_mcp_request(req)
    assert resp["result"]["round"] >= 1, "Public state should return round number"
    assert "shields" in resp["result"], "Public state must include tactical shields"
    print("✅ MCP JSON-RPC Protocol Passed!")

    print("\n--- 5. Testing Airborne Floating Shield Prediction & 2-Round Persistence ---")
    g_def = GameState(mode="human_vs_agent", seed=789, units=3)
    for unit in g_def.units.values():
        if unit["team"] == "white":
            unit["controller"] = "human"  # isolate red shield interception from the AI's own attack
    g_def.units["red_3"]["x"] = 560.0  # pinned: units no longer reset to a fixed spot between rounds
    # The wizard's 70/118 muzzle offset reaches this point at x=1330.
    def_res = g_def.submit_defend("white_2", shield_x=1330.0, shield_y=310.0)
    assert def_res["success"], "Defend action should succeed"
    assert def_res["remaining_charges"] == 4
    assert def_res["duration_rounds"] == 2
    assert g_def.shields["white"]["active"] is True

    # Round 1: Red throws high-arc artillery aimed toward x=1330
    g_def.submit_throw("red_3", angle=58.0, power=82.0)
    r_def = g_def.resolve_round()

    red_shot = next(r for r in r_def["results"] if r.get("unit_id") == "red_3")
    print(f"Round 1: Red 3 shot hit type: {red_shot['hit_type']}, target: {red_shot['hit_target']}, damage: {red_shot['damage_dealt']}")
    assert red_shot["hit_type"] == "shield_blocked", "Expected airborne shield to intercept incoming shot"
    assert red_shot["damage_dealt"] == 0, "Blocked shot deals 0 damage"
    assert g_def.shields["white"]["charges"] == 3, "White shield charge should decrement to 3"
    # Defense persists for 2 rounds: after round 1, duration is 1 and still active!
    assert g_def.shields["white"]["duration_rounds"] == 1, "Shield duration should be 1 round remaining"
    assert g_def.shields["white"]["active"] is True, "Shield should still be active for 2nd round"

    # Round 2: Shield remains active without White re-deploying!
    print("Round 2: Testing 2nd round shield persistence without re-casting...")
    # Position White shield at x=1330 again just to ensure it stays in airspace
    g_def.shields["white"]["x"] = 1330.0
    g_def.shields["white"]["y"] = 310.0
    assert g_def.units["red_3"]["x"] == 560.0, "a unit that did not move keeps its x"
    g_def.submit_throw("red_3", angle=58.0, power=82.0)
    r_def2 = g_def.resolve_round()

    red_shot2 = next(r for r in r_def2["results"] if r.get("unit_id") == "red_3")
    print(f"Round 2: Red 3 shot hit type: {red_shot2['hit_type']}")
    assert red_shot2["hit_type"] == "shield_blocked", "Shield should intercept in round 2"
    # After round 2, duration expires!
    assert g_def.shields["white"]["duration_rounds"] == 0
    assert g_def.shields["white"]["active"] is False, "Shield should expire after 2 rounds"
    print("✅ Airborne Floating Shield & 2-Round Defense Persistence Passed!")

    print("\n==========================================")
    print("🎉 ALL MCP GAME ENGINE TESTS PASSED!")
    print("==========================================")


def test_wall_loses_8_per_hit():
    print("\n--- 6. Testing wall damage = WALL_HIT_DMG (8) per hit ---")
    assert WALL_HIT_DMG == 8, "WALL_HIT_DMG must follow index.html (8)"
    g = GameState(mode="human_vs_agent", seed=123, units=3)
    g.units["red_3"]["x"] = 560.0
    g.submit_throw("red_3", angle=15.0, power=65.0)  # same low shot as test 2: hits the wall
    res = g.resolve_round()
    wall_hits = sum(1 for r in res["results"] if r.get("hit_type") == "central_wall")
    assert wall_hits >= 1, "the low shot must hit the wall"
    assert g.central_wall_hp == 100 - 8 * wall_hits, (
        f"wall hp {g.central_wall_hp} after {wall_hits} hit(s); expected {100 - 8 * wall_hits}")
    print(f"✅ Wall lost 8 per hit ({wall_hits} hit(s), hp {g.central_wall_hp}) Passed!")


def test_unmoved_units_keep_x_across_rounds():
    print("\n--- 7. Testing units are not re-placed between rounds ---")
    g = GameState(mode="agent_vs_agent", seed=5)
    before = {uid: u["x"] for uid, u in g.units.items()}
    for _ in range(4):
        g.resolve_round()  # engine AI throws for every unit; nobody uses the move action
    after = {uid: u["x"] for uid, u in g.units.items()}
    assert before == after, f"x changed without a move action: {before} -> {after}"
    print("✅ Unmoved units keep their x Passed!")


def test_start_x_ranges_and_determinism():
    print("\n--- 8. Testing seeded start positions and 120 px team spacing ---")
    seen_red, seen_white = set(), set()
    for units in range(1, 4):
        for seed in range(1, 201):
            g = GameState(mode="human_vs_agent", seed=seed, units=units)
            for team, bounds in (("red", (240, 680)), ("white", (1240, 1680))):
                xs = [unit["x"] for unit in g.units.values() if unit["team"] == team]
                assert len(xs) == units
                assert all(bounds[0] <= x <= bounds[1] for x in xs), (
                    f"seed {seed}: {team} positions {xs} outside {bounds}")
                if units > 1:
                    assert all(right - left >= 120 for left, right in zip(sorted(xs), sorted(xs)[1:])), (
                        f"seed {seed}: {team} positions overlap: {xs}")
                (seen_red if team == "red" else seen_white).update(xs)
    assert len(seen_red) > 10 and len(seen_white) > 10, "seeded starts should vary"
    for units in range(1, 4):
        a = GameState(mode="human_vs_agent", seed=77, units=units)
        b = GameState(mode="human_vs_agent", seed=77, units=units)
        assert {k: u["x"] for k, u in a.units.items()} == {k: u["x"] for k, u in b.units.items()}, \
            "same seed must give the same start positions"
        assert a.wind == b.wind
    print("✅ Seeded start positions and spacing Passed!")


if __name__ == "__main__":
    test_modes()
    test_wall_loses_8_per_hit()
    test_unmoved_units_keep_x_across_rounds()
    test_start_x_ranges_and_determinism()
    print("\n🎉 ALL NEW POSITION / WALL TESTS PASSED!")


# Task 175 engine-table coverage.
def test_eight_heroes_launches_statuses_and_one_unit_mode():
    print("\n--- 9. Testing shared eight-hero table, launch offsets, statuses, and 1v1 ---")
    expected = {"skeleton", "wizard", "bat", "knight", "reaper", "bride", "hunchback", "hag"}
    assert set(GameState(seed=1).get_public_state()["units"]["red_1"].keys()) >= {"hero", "statuses"}
    assert set(__import__("mcp_game_server").HERO_TEMPLATES) == expected
    duel = GameState(seed=2, units=1, hero_red="skeleton", hero_white="reaper")
    assert list(duel.units) == ["red_1", "white_1"]
    assert duel.units["red_1"]["launch"] == {"fwd": 58, "up": 110}
    assert duel.units["white_1"]["hit_box"] == {"halfWidth": 57, "height": 165}

    target = duel.units["white_1"]
    attacker = duel.units["red_1"]
    target["x"] = 1300.0
    result = duel._apply_hit(attacker, target, 1300.0, 800.0)
    assert result["statuses"] == ["bleed:2", "weak:2"]
    before = target["hp"]
    duel.begin_team_turn("white")
    assert target["hp"] == before - 2
    assert target["statuses"]["bleed"] == 1

    burn_target = GameState(seed=3, units=1, hero_red="reaper", hero_white="hag")
    burn_target.units["white_1"]["hp"] = 30
    burn = burn_target._apply_hit(burn_target.units["red_1"], burn_target.units["white_1"], 1400.0, 800.0)
    assert burn["statuses"] == ["burn:3"]
    burn_target.units["white_1"]["hp"] = 2
    burn_target.begin_team_turn("white")
    assert burn_target.units["white_1"]["hp"] == 1

    axe = GameState(seed=4, units=1, hero_red="hunchback", hero_white="hag")
    axe.units["red_1"]["x"] = 600
    axe.units["white_1"]["x"] = 1400
    axe_result = axe._apply_hit(axe.units["red_1"], axe.units["white_1"], 1400, 800)
    assert axe_result["knockback"] == 50
    assert axe.units["white_1"]["x"] == 1450

    weather = GameState(seed=5, units=1, hero_red="wizard", hero_white="hag")
    weather.weather = {"attackMult": 0.9}
    weather_result = weather._apply_hit(weather.units["red_1"], weather.units["white_1"], 1400, 800)
    assert abs(weather_result["damage"] - 32.4) < 1e-9   # wizard 36 x 0.9 since 2026-11-18 (glass cannon +10 percent; 33 x 0.9 = 29.7 on 2026-11-17, 30 x 0.9 = 27 before)
    print("✅ Eight hero table / status / 1v1 mode Passed!")


if __name__ == "__main__":
    test_eight_heroes_launches_statuses_and_one_unit_mode()
