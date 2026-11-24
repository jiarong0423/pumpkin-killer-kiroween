#!/usr/bin/env python3
"""Tests for scripts/mcp_stdio_server.py (stdlib unittest).

Run:  python3 -B scripts/test_mcp_stdio.py

Part 1 spawns the server as a subprocess and speaks newline-delimited JSON-RPC.
Part 2 tests the session logic in-process with an injected clock.
"""
import json
import os
import queue
import subprocess
import sys
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SERVER = os.path.join(HERE, "mcp_stdio_server.py")

import mcp_stdio_server as srv  # noqa: E402

EXPECTED_TOOLS = {"get_public_state", "get_roster", "get_history", "submit_action", "end_turn", "set_notes", "get_notes"}
FORBIDDEN_KEYS = {"seed", "rng", "dice", "pending_throw", "pending_action", "last_throw"}


class RpcClient:
    """Minimal MCP stdio client around a server subprocess."""

    def __init__(self, *extra):
        self.proc = subprocess.Popen(
            [sys.executable, "-B", SERVER] + list(extra),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding="utf-8", bufsize=1)
        self.lines = queue.Queue()
        self.next_id = 1
        threading.Thread(target=self._pump, daemon=True).start()

    def _pump(self):
        for line in self.proc.stdout:
            self.lines.put(line)
        self.lines.put(None)

    def send_raw(self, text):
        self.proc.stdin.write(text + "\n")
        self.proc.stdin.flush()

    def read(self, timeout=10):
        line = self.lines.get(timeout=timeout)
        if line is None:
            raise AssertionError("server closed stdout")
        return json.loads(line)

    def request(self, method, params=None):
        rid = self.next_id
        self.next_id += 1
        msg = {"jsonrpc": "2.0", "id": rid, "method": method}
        if params is not None:
            msg["params"] = params
        self.send_raw(json.dumps(msg))
        resp = self.read()
        assert resp.get("id") == rid, "response id %r does not match request %r" % (resp.get("id"), rid)
        return resp

    def notify(self, method, params=None):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        self.send_raw(json.dumps(msg))

    def call(self, name, args=None):
        """Return (is_error, parsed_payload) for a tools/call."""
        resp = self.request("tools/call", {"name": name, "arguments": args if args is not None else {}})
        result = resp["result"]
        content = result["content"]
        assert content and content[0]["type"] == "text"
        return result["isError"], json.loads(content[0]["text"])

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()
            self.proc.wait()
        self.proc.stdout.close()


def walk_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            for sub in walk_keys(v):
                yield sub
    elif isinstance(obj, list):
        for item in obj:
            for sub in walk_keys(item):
                yield sub


class StdioProtocolTest(unittest.TestCase):
    SEED = 7351829

    def setUp(self):
        self.c = RpcClient("--seed", str(self.SEED), "--turn-seconds", "600")
        self.addCleanup(self.c.close)

    def init(self):
        resp = self.c.request("initialize", {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "test", "version": "0"}})
        self.c.notify("notifications/initialized")
        return resp

    # ---- handshake
    def test_handshake(self):
        resp = self.init()
        result = resp["result"]
        self.assertEqual(resp["jsonrpc"], "2.0")
        self.assertEqual(result["protocolVersion"], "2025-06-18")
        self.assertIn("tools", result["capabilities"])
        self.assertTrue(result["serverInfo"]["name"])
        # The initialized notification must not produce a reply: the next response is the ping's.
        ping = self.c.request("ping")
        self.assertEqual(ping["result"], {})

    def test_unsupported_protocol_version_falls_back(self):
        resp = self.c.request("initialize", {"protocolVersion": "1999-01-01", "capabilities": {}})
        self.assertIn(resp["result"]["protocolVersion"], srv.SUPPORTED_PROTOCOLS)

    def test_unknown_method_and_parse_error(self):
        self.init()
        resp = self.c.request("does/not/exist")
        self.assertEqual(resp["error"]["code"], -32601)
        self.c.send_raw("{this is not json")
        err = self.c.read()
        self.assertEqual(err["error"]["code"], -32700)
        self.assertIsNone(err["id"])
        self.assertEqual(self.c.request("ping")["result"], {})  # server survived

    def test_unknown_tool_is_protocol_error(self):
        self.init()
        resp = self.c.request("tools/call", {"name": "nope", "arguments": {}})
        self.assertEqual(resp["error"]["code"], -32602)

    # ---- tools/list
    def test_tools_list_has_all_tools_with_schemas(self):
        self.init()
        tools = self.c.request("tools/list")["result"]["tools"]
        self.assertEqual({t["name"] for t in tools}, EXPECTED_TOOLS)
        for tool in tools:
            self.assertTrue(tool["description"], tool["name"])
            schema = tool["inputSchema"]
            self.assertEqual(schema["type"], "object", tool["name"])
            self.assertIn("properties", schema, tool["name"])
        submit = next(t for t in tools if t["name"] == "submit_action")
        self.assertEqual(set(submit["inputSchema"]["required"]), {"unit", "action"})

    # ---- public state
    def test_public_state_has_no_hidden_fields(self):
        self.init()
        is_error, state = self.c.call("get_public_state")
        self.assertFalse(is_error)
        for key in ("round", "wind", "phase", "units", "shields", "ultimates_remaining"):
            self.assertIn(key, state)
        self.assertEqual(len(state["units"]), 6)
        self.assertEqual(state["phase"], "human")
        self.assertEqual(state["weather"], {"id": "clear", "label": "Clear", "round": 1,
                                            "active": False})
        self.assertFalse(set(walk_keys(state)) & FORBIDDEN_KEYS)
        self.assertNotIn(str(self.SEED), json.dumps(state))

    # ---- action rules
    def test_double_submit_rejected(self):
        self.init()
        first_error, _ = self.c.call("submit_action", {"unit": "red_1", "action": {"type": "throw", "angle": 54, "power": 60}})
        self.assertFalse(first_error)
        is_error, payload = self.c.call("submit_action", {"unit": "red_1", "action": {"type": "throw", "angle": 50, "power": 70}})
        self.assertTrue(is_error)
        self.assertIn("already", payload["error"])
        is_error, _ = self.c.call("submit_action", {"unit": "red_1", "action": {"type": "move", "direction": "forward"}})
        self.assertTrue(is_error)

    def test_defend_after_throw_and_non_knight_defend_rejected(self):
        knight = RpcClient("--seed", str(self.SEED), "--turn-seconds", "600", "--units", "1",
                           "--hero-red", "knight", "--hero-white", "wizard")
        self.addCleanup(knight.close)
        knight.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}})
        first_error, _ = knight.call("submit_action", {"unit": "red_1", "action": {"type": "throw", "angle": 54, "power": 60}})
        self.assertFalse(first_error)
        is_error, payload = knight.call("submit_action", {"unit": "red_1", "action": {"type": "defend", "path1": 1, "path2": 2}})
        self.assertTrue(is_error)
        self.assertIn("already", payload["error"])
        is_error, payload = self.c.call("submit_action", {"unit": "red_1", "action": {"type": "defend", "path1": 1, "path2": 2}})
        self.assertTrue(is_error)
        self.assertIn("knight", payload["error"])

    def test_bad_arguments_give_is_error_and_do_not_consume_the_action(self):
        self.init()
        throw = {"type": "throw", "angle": 54, "power": 60}
        bad_calls = [
            ("submit_action", {}),
            ("submit_action", {"unit": "red_1"}),
            ("submit_action", {"unit": "red_1", "action": "throw"}),
            ("submit_action", {"unit": "red_1", "action": {"type": "teleport"}}),
            ("submit_action", {"unit": "red_9", "action": throw}),
            ("submit_action", {"unit": "red_1", "action": dict(throw, angle=10)}),
            ("submit_action", {"unit": "red_1", "action": dict(throw, angle=90)}),
            ("submit_action", {"unit": "red_1", "action": dict(throw, power=-1)}),
            ("submit_action", {"unit": "red_1", "action": dict(throw, power="60")}),
            ("submit_action", {"unit": "red_1", "action": dict(throw, angle=True)}),
            ("submit_action", {"unit": "red_1", "action": dict(throw, spin=1)}),
            ("submit_action", {"unit": "red_1", "action": {"type": "move", "direction": "sideways"}}),
            ("submit_action", {"unit": "red_1", "action": throw, "round": 5}),
            ("submit_action", {"unit": "red_1", "action": throw, "extra": 1}),
            ("get_history", {"limit": 0}),
            ("get_history", {"team": "blue"}),
            ("end_turn", {"phase": "agent"}),
            ("set_notes", {}),
            ("set_notes", {"text": "x" * (srv.MAX_NOTES_CHARS + 1)}),
            ("get_public_state", {"verbose": True}),
        ]
        for name, args in bad_calls:
            is_error, payload = self.c.call(name, args)
            self.assertTrue(is_error, "%s %r should be rejected" % (name, args))
            self.assertIn("error", payload)
        # NaN is accepted by Python's json parser, so the server must reject it itself.
        self.c.send_raw('{"jsonrpc":"2.0","id":900,"method":"tools/call","params":{"name":"submit_action",'
                        '"arguments":{"unit":"red_1","action":{"type":"throw","angle":NaN,"power":50}}}}')
        resp = self.c.read()
        self.assertEqual(resp["id"], 900)
        self.assertTrue(resp["result"]["isError"])
        is_error, _ = self.c.call("submit_action", {"unit": "red_1", "action": throw})
        self.assertFalse(is_error, "failed calls must not use up the unit's action")

    def test_phase_rules(self):
        self.init()
        agent_throw = {"unit": "white_1", "action": {"type": "throw", "angle": 54, "power": 60}}
        is_error, payload = self.c.call("submit_action", agent_throw)
        self.assertTrue(is_error)
        self.assertIn("phase", payload["error"])
        is_error, _ = self.c.call("end_turn", {"phase": "agent"})
        self.assertTrue(is_error)
        is_error, payload = self.c.call("end_turn", {"phase": "human"})
        self.assertFalse(is_error)
        self.assertEqual(payload["phase"], "agent")
        is_error, state = self.c.call("get_public_state")
        self.assertEqual(state["phase"], "agent")
        self.assertGreater(state["turn_seconds_left"], 0)
        is_error, _ = self.c.call("submit_action", {"unit": "red_1", "action": {"type": "throw", "angle": 54, "power": 60}})
        self.assertTrue(is_error)
        is_error, _ = self.c.call("submit_action", agent_throw)
        self.assertFalse(is_error)

    def test_move_uses_engine_die(self):
        self.init()
        is_error, before = self.c.call("get_public_state")
        is_error, moved = self.c.call("submit_action", {"unit": "red_1", "action": {"type": "move", "direction": "forward"}})
        self.assertFalse(is_error)
        self.assertIn(moved["die"], range(1, 7))
        self.assertEqual(moved["pixels"], moved["die"] * srv.MOVE_PX_PER_PIP)
        _, after = self.c.call("get_public_state")
        # The page clamps a move to its zone (red 160..760), so a long forward move can stop at the edge.
        expected = min(before["units"]["red_1"]["x"] + moved["pixels"], srv.TEAM_X_LIMITS["red"][1])
        # Team matches (3 units here): the page's step-back rule keeps the unit 120 px from every living teammate,
        # so it may stop between where it stood and the zone-clamped target (then blocked_by_teammate is true).
        got = after["units"]["red_1"]["x"]
        if moved.get("blocked_by_teammate"):
            self.assertTrue(before["units"]["red_1"]["x"] <= got < expected, (got, expected))
        else:
            self.assertEqual(got, expected)
        mates = [u["x"] for uid, u in after["units"].items() if uid.startswith("red_") and uid != "red_1" and u["alive"]]
        self.assertTrue(all(abs(got - x) >= 120 - 1e-6 for x in mates), (got, mates))
        is_error, _ = self.c.call("submit_action", {"unit": "red_1", "action": {"type": "move", "direction": "forward", "die": 6}})
        self.assertTrue(is_error)  # the agent cannot choose the die

    def test_move_does_not_use_the_turn(self):
        self.init()
        is_error, _ = self.c.call("submit_action", {"unit": "red_1", "action": {"type": "move", "direction": "forward"}})
        self.assertFalse(is_error)
        is_error, again = self.c.call("submit_action", {"unit": "red_1", "action": {"type": "move", "direction": "backward"}})
        self.assertTrue(is_error)
        self.assertIn("already moved", again["error"])
        is_error, _ = self.c.call("submit_action", {"unit": "red_1", "action": {"type": "throw", "angle": 50, "power": 70}})
        self.assertFalse(is_error)  # the throw is still allowed after the move
        _, state = self.c.call("get_public_state")
        self.assertTrue(state["units"]["red_1"]["moved"])
        self.assertTrue(state["units"]["red_1"]["acted"])

    def test_full_round_history_and_notes(self):
        self.init()
        _, state = self.c.call("get_public_state")
        wind = state["wind"]
        self.c.call("submit_action", {"unit": "red_1", "action": {"type": "throw", "angle": 54, "power": 60}})
        self.c.call("end_turn", {"phase": "human"})
        self.c.call("submit_action", {"unit": "white_1", "action": {"type": "throw", "angle": 62, "power": 70}})
        is_error, summary = self.c.call("end_turn", {"phase": "agent"})
        self.assertFalse(is_error)
        self.assertEqual(summary["round_resolved"], 1)
        self.assertEqual(len(summary["throws"]), 2)
        _, state2 = self.c.call("get_public_state")
        self.assertEqual(state2["round"], 2)
        self.assertEqual(state2["phase"], "human")
        _, hist = self.c.call("get_history", {"limit": 10})
        throws = hist["throws"]
        self.assertEqual(len(throws), 2)
        for t in throws:
            self.assertEqual(t["round"], 1)
            self.assertEqual(t["wind_at_throw"], wind)
            self.assertIn("landing_x", t)
            self.assertIn("landing_y", t)
            self.assertIn("hit_type", t)
            self.assertGreaterEqual(len(t["path"]), 3)
            self.assertEqual(t["path"][-1], [t["landing_x"], t["landing_y"]])
        by_unit = {t["unit"]: t for t in throws}
        self.assertNotIn("angle", by_unit["red_1"])    # human aim stays private
        self.assertNotIn("power", by_unit["red_1"])
        self.assertEqual(by_unit["white_1"]["angle"], 62)
        self.assertEqual(by_unit["white_1"]["power"], 70)
        _, own = self.c.call("get_history", {"unit": "white_1", "include_path": False})
        self.assertEqual(len(own["throws"]), 1)
        self.assertNotIn("path", own["throws"][0])
        self.assertFalse(set(walk_keys(hist)) & FORBIDDEN_KEYS)
        is_error, _ = self.c.call("set_notes", {"text": "player aims about x=640"})
        self.assertFalse(is_error)
        self.c.call("set_notes", {"text": "wind +1 adds ~80 px", "mode": "append"})
        _, notes = self.c.call("get_notes")
        self.assertEqual(notes["notes"], "player aims about x=640\nwind +1 adds ~80 px")


class FakeClock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


def make_session(mode="human_vs_agent", seed=5, clock=None, **kwargs):
    clock = clock or FakeClock()
    return srv.Session(mode=mode, seed=seed, clock=clock, turn_seconds=12, **kwargs), clock


THROW = {"type": "throw", "angle": 54, "power": 60}
SYNTHETIC_PATH = [[1300.0, 500.0], [900.0, 420.0], [700.0, 450.0], [500.0, 600.0]]


def g_wind_at_start(seed):
    """Wind of round 1 for a seed, read from a fresh engine (round 1 wind is public anyway)."""
    return srv.TrackedGameState(mode="human_vs_agent", seed=seed).wind


def fake_enemy_throw(session, path):
    """Append a white throw to the log so the red knight has something to remember (test only)."""
    log = session.engine.throw_log
    tid = session.engine.next_throw_id
    session.engine.next_throw_id += 1
    log.append({"throw_id": tid, "round": 1, "team": "white", "unit": "white_1", "controller": "subagent",
                "angle": 55.0, "power": 60.0, "wind_at_throw": 0.0, "landing_x": path[-1][0],
                "landing_y": path[-1][1], "hit_type": "ground", "hit_target": None,
                "damage_dealt": 0, "path": path})
    return tid


class SessionTest(unittest.TestCase):
    def test_timeout_idles_units_with_injected_clock(self):
        s, clock = make_session()
        s.call("end_turn", {"phase": "human"})
        s.call("submit_action", {"unit": "white_1", "action": THROW})
        clock.advance(11.9)
        state = s.call("get_public_state", {})
        self.assertEqual(state["phase"], "agent")
        self.assertEqual(state["round"], 1)
        self.assertAlmostEqual(state["turn_seconds_left"], 0.1, places=1)
        clock.advance(0.2)
        state = s.call("get_public_state", {})
        self.assertEqual(state["round"], 2)
        self.assertEqual(state["phase"], "human")
        self.assertIsNone(state["turn_seconds_left"])
        self.assertEqual(state["last_timeout"], {"round": 1, "idle_units": []})
        throws = s.call("get_history", {})["throws"]
        self.assertEqual([t["unit"] for t in throws], ["white_1"])  # idle units never threw

    def test_human_timeout_ends_the_phase_at_its_deadline(self):
        s, clock = make_session()
        clock.advance(11.99)
        self.assertEqual(s.call("get_public_state", {})["phase"], "human")
        clock.advance(0.02)
        state = s.call("get_public_state", {})
        self.assertEqual(state["phase"], "agent")
        self.assertEqual(state["round"], 1)
        self.assertEqual(state["last_timeout"],
                         {"round": 1, "idle_units": ["red_1"]})
        self.assertAlmostEqual(state["turn_seconds_left"], 12.0, places=1)

    def test_agent_vs_agent_timeout_with_no_actions(self):
        s, clock = make_session(mode="agent_vs_agent")
        self.assertEqual(s.phase, "agent")
        clock.advance(12.0)
        state = s.call("get_public_state", {})
        self.assertEqual(state["round"], 2)
        self.assertEqual(state["phase"], "agent")
        self.assertEqual(state["last_timeout"]["idle_units"], sorted(s.engine.units))
        self.assertEqual(state["turn_seconds_left"], 12.0)  # fresh timer for the new round

    def test_stale_submit_after_timeout_is_rejected(self):
        s, clock = make_session(mode="agent_vs_agent")
        clock.advance(13)
        with self.assertRaises(srv.ToolError):
            s.call("submit_action", {"unit": "white_1", "action": THROW, "round": 1})

    def test_no_hidden_values_in_state(self):
        s, _ = make_session(seed=987654321)
        text = json.dumps(s.public_state())
        self.assertNotIn("987654321", text)
        self.assertFalse(set(walk_keys(s.public_state())) & FORBIDDEN_KEYS)

    def test_defend_flow(self):
        s, _ = make_session()
        s.active_unit_index["red"] = 2  # red_3 is the knight's scheduled team turn
        first = fake_enemy_throw(s, SYNTHETIC_PATH)
        second = fake_enemy_throw(s, SYNTHETIC_PATH)
        far = fake_enemy_throw(s, [[1300.0, 500.0], [1100.0, 600.0]])
        self.assertEqual(s.public_state()["remembered_enemy_paths"]["red"], [first, second, far])
        defend = {"type": "defend", "path1": first, "path2": second}
        with self.assertRaises(srv.ToolError):
            s.call("submit_action", {"unit": "red_3", "action": {"type": "defend", "path1": first, "path2": first}})
        with self.assertRaises(srv.ToolError):
            s.call("submit_action", {"unit": "red_3", "action": {"type": "defend", "path1": first, "path2": 999}})
        with self.assertRaises(srv.ToolError):
            s.call("submit_action", {"unit": "red_3", "action": {"type": "defend", "path1": first, "path2": far}})
        result = s.call("submit_action", {"unit": "red_3", "action": defend})
        self.assertTrue(result["ok"])
        shield = s.public_state()["shields"]["red"]
        self.assertTrue(shield["active"])
        self.assertEqual(shield["path_ids"], [first, second])
        self.assertEqual((shield["x"], shield["y"]), (result["shield_x"], result["shield_y"]))
        with self.assertRaises(srv.ToolError) as ctx:
            s.call("submit_action", {"unit": "red_3", "action": THROW})
        self.assertIn("cannot throw", str(ctx.exception))

    def test_unit_that_did_not_move_keeps_x_across_rounds(self):
        s, _ = make_session()
        start = {uid: u["x"] for uid, u in s.engine.units.items()}
        for _ in range(3):
            s.call("end_turn", {"phase": "human"})
            s.call("end_turn", {"phase": "agent"})  # resolves the round; nobody moved
        self.assertEqual(s.engine.round_num, 4)
        self.assertEqual({uid: u["x"] for uid, u in s.engine.units.items()}, start)

    def test_start_x_ranges_match_the_page(self):
        for units in range(1, 4):
            for seed in range(1, 40):
                s, _ = make_session(seed=seed, units=units)
                for team, bounds in (("red", (240, 680)), ("white", (1240, 1680))):
                    xs = [unit["x"] for unit in s.engine.units.values() if unit["team"] == team]
                    self.assertTrue(all(bounds[0] <= x <= bounds[1] for x in xs),
                                    "seed %d %s x=%s outside %s" % (seed, team, xs, bounds))
                    if units > 1:
                        self.assertTrue(all(right - left >= 120 for left, right in zip(sorted(xs), sorted(xs)[1:])),
                                        "seed %d %s spacing %s" % (seed, team, xs))

    def test_only_the_move_action_changes_x(self):
        s, _ = make_session()
        before = s.engine.units["red_1"]["x"]
        result = s.call("submit_action", {"unit": "red_1", "action": {"type": "move", "direction": "forward"}})
        self.assertEqual(result["x_before"], before)
        s.call("end_turn", {"phase": "human"})
        s.call("end_turn", {"phase": "agent"})
        self.assertEqual(s.engine.units["red_1"]["x"], result["x_after"])  # the round did not move it again

    def test_move_zones_match_the_page(self):
        self.assertEqual(srv.TEAM_X_LIMITS["red"], (110.0, 640.0))   # the retreat limit is 110 since 2026-11-17 (was 240); the forward limit 640 since 2026-11-18 (was 680, the fence collision grew)
        self.assertEqual(srv.TEAM_X_LIMITS["white"], (1280.0, 1810.0))   # 1810 since 2026-11-17 (was 1680); the forward limit 1280 since 2026-11-18 (was 1240)
        s, _ = make_session(units=1)   # one unit per team: the 120 px teammate rule has nobody to apply to
        s.engine.units["red_1"]["x"] = 675.0
        result = s.call("submit_action", {"unit": "red_1", "action": {"type": "move", "direction": "forward"}})
        self.assertEqual(result["x_after"], 640.0)
        self.assertTrue(result["blocked_by_edge"])
        s.engine.units["white_1"]["x"] = 1245.0
        s.call("end_turn", {"phase": "human"})
        result = s.call("submit_action", {"unit": "white_1", "action": {"type": "move", "direction": "forward"}})
        self.assertEqual(result["x_after"], 1280.0)  # white forward is -x
        self.assertTrue(result["blocked_by_edge"])

    def test_move_stays_inside_team_limits(self):
        s, _ = make_session()
        result = s.call("submit_action", {"unit": "red_1", "action": {"type": "move", "direction": "backward"}})
        lo, hi = srv.TEAM_X_LIMITS["red"]
        self.assertGreaterEqual(result["x_after"], lo)
        self.assertLessEqual(result["x_after"], hi)
        self.assertIn(result["die"], range(1, 7))

    def test_sample_path_matches_engine_landing(self):
        g = srv.TrackedGameState(mode="human_vs_agent", seed=456, units=3)
        g.units["red_3"]["x"] = 560.0  # start x is random now; pin it for a known release point
        g.submit_throw("red_3", angle=58.0, power=82.0)
        g.resolve_round()
        rec = g.throw_log[0]
        path = rec["path"]
        self.assertEqual(path[-1], [rec["landing_x"], rec["landing_y"]])
        self.assertEqual(path[0], [560 + 51, 860 - 73])  # knight shield launch follows shared/heroes.json
        self.assertGreater(len(path), 10)
        xs = [p[0] for p in path]
        self.assertEqual(xs, sorted(xs))
        self.assertLessEqual(max(p[1] for p in path), srv.GROUND_Y)
        self.assertEqual(rec["wind_at_throw"], 0.0 + g_wind_at_start(456))

    def test_engine_ai_is_disabled(self):
        s, _ = make_session(mode="agent_vs_agent")
        result = s.call("end_turn", {"phase": "agent"})
        self.assertEqual(result["throws"], [])  # nobody acted, nobody threw

    def test_match_end_writes_staging_files_without_seed_or_human_aim(self):
        with tempfile.TemporaryDirectory() as tmp:
            s, _ = make_session(seed=424242, memory_dir=tmp)
            s.call("set_notes", {"text": "lesson one"})
            s.call("submit_action", {"unit": "red_1", "action": THROW})
            s.call("end_turn", {"phase": "human"})
            s.call("submit_action", {"unit": "white_1", "action": THROW})
            s.call("end_turn", {"phase": "agent"})
            for unit in s.engine.units.values():
                if unit["team"] == "white":
                    unit["alive"] = False
                    unit["hp"] = 0
            s.call("end_turn", {"phase": "human"})  # no agent unit alive: the round resolves at once
            self.assertEqual(s.winner, "red")
            self.assertEqual(s.phase, "over")
            with self.assertRaises(srv.ToolError):
                s.call("end_turn", {})
            files = {}
            for root, _dirs, names in os.walk(tmp):
                for name in names:
                    with open(os.path.join(root, name), "r", encoding="utf-8") as fh:
                        files[name] = fh.read()
            for name in ("meta.json", "history.jsonl", "notes.json", "result.json", "index.jsonl", "schema_version.json"):
                self.assertIn(name, files)
            self.assertNotIn("424242", "".join(files.values()))
            self.assertNotIn("seed", files["meta.json"])
            lines = [json.loads(x) for x in files["history.jsonl"].splitlines()]
            self.assertEqual(len(lines), 2)
            human = next(x for x in lines if x["controller"] == "human")
            self.assertNotIn("angle", human)
            self.assertEqual(json.loads(files["result.json"])["winner"], "red")
            self.assertEqual(json.loads(files["index.jsonl"].splitlines()[0])["winner"], "red")


class StatusTurnTest(unittest.TestCase):
    def test_slow_blocks_only_the_target_next_move_and_status_words_are_public(self):
        session, _ = make_session()
        target = session.engine.units["red_2"]
        target["statuses"] = {"slow": 1}
        # The effect was received after red's turn in round 1, so it binds at red's round-2 start.
        session.call("end_turn", {"phase": "human"})
        session.call("end_turn", {"phase": "agent"})
        self.assertEqual(session.public_state()["units"]["red_2"]["statuses"], ["slow:1"])
        with self.assertRaisesRegex(srv.ToolError, "slowed"):
            session.call("submit_action", {"unit": "red_2", "action": {"type": "move", "direction": "forward"}})
        session.call("end_turn", {"phase": "human"})
        self.assertEqual(target["statuses"], {})

    def test_head_crit_shortens_the_affected_phase_timer(self):
        session, clock = make_session()
        target = session.engine.units["white_1"]
        target["statuses"] = {"stun": True}
        session.call("end_turn", {"phase": "human"})
        self.assertEqual(session.phase, "agent")
        self.assertEqual(session.deadline, clock() + 7.0)
        self.assertEqual(target["statuses"], {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
