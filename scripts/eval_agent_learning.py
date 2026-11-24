#!/usr/bin/env python3
"""Learning-curve evaluation for the MCP sub-agent interface (stdlib only).

A scripted baseline agent plays N seeded rounds against a FIXED target through the MCP tools.
It learns ONLY from `get_history` (its own past power, the wind at throw time, where each throw
landed). It has no ballistic simulator; the public wind and the unit positions come from
`get_public_state`, as for any agent.

Learner: a local linear model landing_x ~ x_anchor + b * (power - p_anchor) + c * (wind - w_anchor)
  - b (px per power point) and c (px per wind unit) are fitted from all pairs of past throws with a
    ridge prior (b = 20 px/power, c = 0: "wind is ignored until the history shows otherwise");
  - the anchor is the nearest past throw (similar wind and power), which is the nearest-neighbour
    correction of the remaining nonlinearity.

Run:  python3 -B scripts/eval_agent_learning.py [--rounds 10] [--seeds 101 202 303 404 505]
Exit code 1 if the mean error in the second half of the rounds is not lower than in the first half.
"""
import argparse
import json
import os
import sys
import tempfile
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import mcp_stdio_server as srv  # noqa: E402

UNIT = "white_1"        # the agent's thrower (pumpkin wizard, x=1360)
TARGET = "red_3"        # the fixed target, the last red unit in the supported N = 3 team
ANGLE = 62.0            # fixed high arc, clears the fence
FIRST_POWER = 70.0
PRIOR_SLOPE = 20.0      # px of landing per power point, rough rule of thumb
PRIOR_WIND = 0.0        # px per wind unit: unknown at the start
LAMBDA_B = 200.0        # ridge weights of the priors
LAMBDA_C = 20.0
WIND_WEIGHT = 4.0       # one wind unit counts like 4 power points when picking the nearest throw
MAX_STEP = 25.0         # largest power change from the anchor throw
POWER_LOW, POWER_HIGH = 20.0, 100.0
DEFAULT_SEEDS = (101, 202, 303, 404, 505)


class FixedTargetEngine(srv.TrackedGameState):
    """Test fixture: only red_3 is alive, unkillable, and every unit returns to its spawn point.

    The base engine moves all units randomly after each round; the evaluation needs a target that
    stays put. Physics is not touched.
    """

    def __init__(self, mode: str = "human_vs_agent", seed: Optional[int] = None, **engine_options: Any) -> None:
        super().__init__(mode=mode, seed=seed, **engine_options)   # units, hero_red, hero_white (Kiro 193) are forwarded
        for uid in ("red_1", "red_2"):
            self.units[uid]["alive"] = False
            self.units[uid]["hp"] = 0
        for uid in ("white_2", "white_3"):   # one shooter: the server lets exactly one unit per team act and rotates it, so the fixture keeps only UNIT alive on its side
            if uid in self.units:
                self.units[uid]["alive"] = False
                self.units[uid]["hp"] = 0
        self.units[TARGET]["hp"] = self.units[TARGET]["max_hp"] = 10 ** 6
        self._spawn = {uid: (u["x"], u["y"]) for uid, u in self.units.items()}

    def resolve_round(self) -> Dict[str, Any]:
        result = super().resolve_round()
        for uid, unit in self.units.items():
            unit["x"], unit["y"] = self._spawn[uid]
        self.central_wall_hp = 100
        return result


class ToolClient:
    """Calls tools through the real JSON-RPC handler (same code path as the stdio loop)."""

    def __init__(self, server: srv.McpServer) -> None:
        self.server = server
        self.next_id = 1

    def call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        msg = {"jsonrpc": "2.0", "id": self.next_id, "method": "tools/call",
               "params": {"name": name, "arguments": arguments}}
        self.next_id += 1
        resp = self.server.handle_message(msg)
        result = resp["result"]
        payload = json.loads(result["content"][0]["text"])
        if result["isError"]:
            raise RuntimeError("%s failed: %s" % (name, payload))
        return payload


class HistoryLearner:
    """Chooses power from get_history samples only."""

    def __init__(self, direction: int) -> None:
        self.direction = direction  # +1: target is to the right of the thrower, -1: to the left
        self.b = direction * PRIOR_SLOPE
        self.c = PRIOR_WIND

    def fit(self, samples: List[Tuple[float, float, float]]) -> None:
        """Ridge fit of dx = b*dp + c*dw over all pairs of past throws."""
        b0 = self.direction * PRIOR_SLOPE
        a11, a12, a22 = LAMBDA_B, 0.0, LAMBDA_C
        r1, r2 = LAMBDA_B * b0, LAMBDA_C * PRIOR_WIND
        for i in range(len(samples)):
            for j in range(i + 1, len(samples)):
                dp = samples[i][0] - samples[j][0]
                dw = samples[i][1] - samples[j][1]
                dx = samples[i][2] - samples[j][2]
                a11 += dp * dp
                a12 += dp * dw
                a22 += dw * dw
                r1 += dx * dp
                r2 += dx * dw
        det = a11 * a22 - a12 * a12
        b = (r1 * a22 - r2 * a12) / det
        c = (a11 * r2 - a12 * r1) / det
        if b * self.direction < 5.0:   # more power must move the landing toward the target side
            b = self.direction * 5.0
        self.b = max(-60.0, min(60.0, b))
        self.c = c

    def _solve(self, anchor: Tuple[float, float, float], target_x: float, wind: float) -> float:
        power = anchor[0] + (target_x - anchor[2] - self.c * (wind - anchor[1])) / self.b
        power = max(anchor[0] - MAX_STEP, min(anchor[0] + MAX_STEP, power))
        return max(POWER_LOW, min(POWER_HIGH, power))

    def choose(self, target_x: float, wind: float, throws: List[Dict[str, Any]]) -> float:
        mine = [t for t in throws if t["unit"] == UNIT and abs(t.get("angle", -1.0) - ANGLE) < 1e-9]
        samples = [(t["power"], t["wind_at_throw"], t["landing_x"])
                   for t in mine if t["hit_type"] != "central_wall"]
        if not samples:
            # first throw, or every earlier throw hit the fence (too short): add power
            return min(POWER_HIGH, mine[-1]["power"] + 10.0) if mine else FIRST_POWER
        self.fit(samples)
        anchor = min(reversed(samples), key=lambda s: abs(s[1] - wind))
        first_guess = self._solve(anchor, target_x, wind)
        anchor = min(reversed(samples),
                     key=lambda s: WIND_WEIGHT * abs(s[1] - wind) + abs(s[0] - first_guess))
        return self._solve(anchor, target_x, wind)

    def lesson(self, round_no: int, target_x: float, signed_error: float) -> str:
        return ("round %d: +1 power moves the landing %+.0f px; +1 wind moves it %+.0f px; "
                "last throw landed %+.0f px from the target at x=%.0f"
                % (round_no, self.b, self.c, signed_error, target_x))


def play_seed(seed: int, rounds: int, memory_dir: str) -> List[Tuple[float, bool]]:
    """Return (abs error px, hit) for each round."""
    session = srv.Session(mode="human_vs_agent", seed=seed, clock=lambda: 0.0, turn_seconds=12,
                          memory_dir=memory_dir, engine_cls=FixedTargetEngine)
    client = ToolClient(srv.McpServer(session))
    learner: Optional[HistoryLearner] = None
    rows: List[Tuple[float, bool]] = []
    for round_no in range(1, rounds + 1):
        state = client.call("get_public_state", {})
        wind = state["wind"]
        target_x = state["units"][TARGET]["x"]
        if learner is None:
            learner = HistoryLearner(1 if target_x > state["units"][UNIT]["x"] else -1)
        history = client.call("get_history", {"limit": 50, "unit": UNIT, "include_path": False})
        power = round(learner.choose(target_x, wind, history["throws"]), 1)
        client.call("end_turn", {"phase": "human", "round": state["round"]})   # the scripted "humans" do nothing
        client.call("submit_action", {"unit": UNIT, "round": state["round"],
                                      "action": {"type": "throw", "angle": ANGLE, "power": power}})
        summary = client.call("end_turn", {"phase": "agent", "round": state["round"]})
        throw = next(t for t in summary["throws"] if t["unit"] == UNIT)
        signed = throw["landing_x"] - target_x
        rows.append((abs(signed), throw["hit_type"] == "hero"))
        client.call("set_notes", {"text": learner.lesson(round_no, target_x, signed)})
    return rows


def check_staging(memory_dir: str, rounds: int) -> None:
    """The run must have left a public-only history.jsonl with one line per throw."""
    found = []
    for root, _dirs, names in os.walk(memory_dir):
        if "history.jsonl" in names:
            with open(os.path.join(root, "history.jsonl"), "r", encoding="utf-8") as fh:
                text = fh.read()
            found.append(text)
    if len(found) != 1:
        raise AssertionError("expected one history.jsonl under %s, found %d" % (memory_dir, len(found)))
    if len(found[0].splitlines()) != rounds:
        raise AssertionError("history.jsonl should have %d lines" % rounds)
    if '"seed"' in found[0]:
        raise AssertionError("history.jsonl must not contain the seed")


def mean(values: List[float]) -> float:
    return sum(values) / len(values)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--rounds", type=int, default=10)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    args = parser.parse_args(argv)
    if args.rounds < 2:
        parser.error("--rounds must be at least 2")

    per_seed: Dict[int, List[Tuple[float, bool]]] = {}
    with tempfile.TemporaryDirectory() as tmp:
        for seed in args.seeds:
            seed_dir = os.path.join(tmp, "seed_%d" % seed)
            per_seed[seed] = play_seed(seed, args.rounds, seed_dir)
            check_staging(seed_dir, args.rounds)

    n = len(args.seeds)
    print("Baseline agent, history-only learning. %d seeds, target %s at fixed x, angle %.0f" % (n, TARGET, ANGLE))
    print("round | hit rate | mean |error| px")
    err_by_round: List[float] = []
    for r in range(args.rounds):
        errs = [per_seed[s][r][0] for s in args.seeds]
        hits = [per_seed[s][r][1] for s in args.seeds]
        err_by_round.append(mean(errs))
        print("%5d | %7.0f%% | %8.1f" % (r + 1, 100.0 * sum(hits) / n, err_by_round[-1]))
    half = args.rounds // 2
    early, late = mean(err_by_round[:half]), mean(err_by_round[-half:])
    print("mean error rounds 1-%d: %.1f px | rounds %d-%d: %.1f px"
          % (half, early, args.rounds - half + 1, args.rounds, late))
    for s in args.seeds:
        e = [row[0] for row in per_seed[s]]
        print("  seed %d: %.1f -> %.1f" % (s, mean(e[:half]), mean(e[-half:])))
    if not late < early:
        print("FAIL: the agent did not improve (late %.1f >= early %.1f)" % (late, early))
        return 1
    print("OK: error fell by %.0f%%" % (100.0 * (early - late) / early))
    return 0


if __name__ == "__main__":
    sys.exit(main())
