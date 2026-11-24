#!/usr/bin/env python3
"""Run a deterministic, public-tool-only Pumpkin Killer practice match."""
import argparse
import json
import os
import sys
from typing import Any, Dict, Optional, Sequence

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import mcp_stdio_server as srv  # noqa: E402


class ScriptedStandIn:
    """A deliberately small opponent that reads state and history through MCP only."""

    def __init__(self, session: srv.Session, seat: Dict[str, Any], transcript: Any) -> None:
        self.seat = seat
        self.client = srv.InProcessToolClient(srv.McpServer(session, seat=seat, transcript=transcript))
        self.last_view: Optional[Dict[str, Any]] = None

    def drive(self, _session: srv.Session) -> None:
        state = self.client.call("get_public_state", {})
        self.last_view = state
        if state["phase"] not in ("human", "agent"):
            return
        controller = "human" if state["phase"] == "human" else "subagent"
        units = [uid for uid in self.seat["units"]
                 if state["units"][uid]["alive"] and state["units"][uid]["controller"] == controller]
        if not units:
            return
        unit_id = units[0]
        unit = state["units"][unit_id]
        targets = [row for row in state["units"].values()
                   if row["alive"] and row["team"] != unit["team"]]
        target = min(targets, key=lambda row: abs(row["x"] - unit["x"]))
        history = self.client.call("get_history", {"limit": 1, "unit": unit_id,
                                                    "include_path": False})["throws"]
        if history:
            previous = history[-1]
            direction = 1.0 if target["x"] > unit["x"] else -1.0
            power = previous["power"] + direction * (target["x"] - previous["landing_x"]) / 20.0
        else:
            power = 70.0
        action = {"type": "throw", "angle": 62.0, "power": round(max(20.0, min(100.0, power)), 1)}
        self.client.call("submit_action", {"unit": unit_id, "round": state["round"], "action": action})
        self.client.call("end_turn", {"round": state["round"], "phase": state["phase"]})
        self.last_view = self.client.call("get_public_state", {})


def make_actor(spec: str, session: srv.Session, seat: Dict[str, Any], transcript: Any) -> Any:
    if spec == "scripted":
        return ScriptedStandIn(session, seat, transcript)
    if spec.startswith("builtin:"):
        return srv.BuiltinPracticeSeat(session, seat, spec.split(":", 1)[1], transcript)
    raise ValueError("actor must be scripted or builtin:<easy|normal|hard|adaptive>")


def set_duel_fixture(session: srv.Session) -> None:
    """Keep the runner short while agents still receive only their normal public views."""
    for uid, unit in session.engine.units.items():
        if uid not in ("red_3", "white_1"):
            unit["alive"] = False
            unit["hp"] = 0
    session.engine.units["red_3"].update({"alive": True, "hp": 26, "max_hp": 26, "x": 600.0})
    session.engine.units["white_1"].update({"alive": True, "hp": 26, "max_hp": 26, "x": 1320.0})


def run_match(seed: int, red: str, white: str, out: str, max_rounds: int = 80) -> Dict[str, Any]:
    transcript = srv.TranscriptWriter(out)
    try:
        session = srv.Session(mode="human_vs_agent", seed=seed, clock=lambda: 0.0,
                              human_turn_seconds=0, turn_seconds=0)
        set_duel_fixture(session)
        red_actor = make_actor(red, session, session.seats["red"], transcript)
        white_actor = make_actor(white, session, session.seats["white"], transcript)
        actors = (red_actor, white_actor)
        while session.winner is None and session.engine.round_num <= max_rounds:
            before = session.engine.round_num
            for actor in actors:
                actor.drive(session)
                if session.winner is not None:
                    break
            if session.engine.round_num == before and session.winner is None:
                raise RuntimeError("no actor could advance round %d" % before)
        if session.winner is None:
            raise RuntimeError("practice match did not finish within %d rounds" % max_rounds)
        return {"winner": session.winner, "rounds": session.engine.round_num - 1}
    finally:
        transcript.close()


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--red", default="scripted")
    parser.add_argument("--white", default="builtin:normal")
    parser.add_argument("--out", required=True, help="public JSONL transcript")
    parser.add_argument("--max-rounds", type=int, default=80)
    args = parser.parse_args(argv)
    try:
        result = run_match(args.seed, args.red, args.white, args.out, args.max_rounds)
    except (ValueError, RuntimeError) as error:
        parser.error(str(error))
    print("winner=%s rounds=%d" % (result["winner"], result["rounds"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
