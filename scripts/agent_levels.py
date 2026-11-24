#!/usr/bin/env python3
"""Seeded, public-information difficulty wrappers for the history learner."""
import random
from typing import Any, Dict, List, Sequence, Tuple

import eval_agent_learning as learner

# The sole difficulty controls.  Perception values are maximum absolute errors in
# public target x (pixels) and wind (HUD units); power_error is likewise absolute.
LEVELS = {
    "easy": {
        "perception_target_px": 180.0,  # mistaken reading of public target position
        "perception_wind": 1.8,         # mistaken reading of public HUD wind
        "aim_power_error": 13.0,        # uniform random power error after learning
        "memory": 3,                    # own public throws retained for the learner
        "fit_wind": False,              # hides wind variation from the learner fit
    },
    "normal": {
        "perception_target_px": 80.0,   # moderately inaccurate public target reading
        "perception_wind": 0.8,         # moderately inaccurate public wind reading
        "aim_power_error": 6.0,         # moderate post-choice power error
        "memory": 12,                   # recent own public throws retained
        "fit_wind": True,               # fit the public wind term from history
    },
    "hard": {
        "perception_target_px": 20.0,   # near-accurate public target reading
        "perception_wind": 0.2,         # near-accurate public wind reading
        "aim_power_error": 3.0,         # small post-choice power error
        "memory": 50,                   # all server-available own public throws
        "fit_wind": True,               # fit the public wind term from history
    },
}

LEVEL_NAMES = tuple(LEVELS)
PUBLIC_TOOLS = frozenset((
    "get_public_state", "get_history", "submit_action", "end_turn", "set_notes", "get_notes",
))


def level_config(level: str) -> Dict[str, Any]:
    """Return a copy of the named knob row so callers cannot change LEVELS."""
    if level not in LEVELS:
        raise ValueError("unknown level: %s" % level)
    return dict(LEVELS[level])


class PublicToolClient(learner.ToolClient):
    """Baseline JSON-RPC client constrained to the six published MCP tools."""

    def __init__(self, server: Any) -> None:
        super().__init__(server)
        self.calls: List[str] = []

    def call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name not in PUBLIC_TOOLS:
            raise AssertionError("agent attempted non-public tool: %s" % name)
        self.calls.append(name)
        return super().call(name, arguments)


class LevelAgent:
    """Apply the three level knobs around eval_agent_learning.HistoryLearner."""

    def __init__(self, level: str, seed: int, unit: str = learner.UNIT) -> None:
        self.level = level
        self.config = level_config(level)
        self.unit = unit
        self.rng = random.Random(seed)
        self.learner = None

    def choose_power(self, state: Dict[str, Any], throws: Sequence[Dict[str, Any]]) -> float:
        """Choose from a deliberately noisy reading of public state and public history."""
        unit_state = state["units"][self.unit]
        target_id, target = self._nearest_target(state, unit_state)
        del target_id  # Target identity is public; only its x is needed by the baseline learner.
        target_x = float(target["x"]) + self._noise("perception_target_px")
        wind = float(state["wind"]) + self._noise("perception_wind")
        direction = 1 if target_x > float(unit_state["x"]) else -1
        if self.learner is None:
            self.learner = learner.HistoryLearner(direction)

        mine = [dict(row) for row in throws if row.get("unit") == self.unit]
        mine = mine[-int(self.config["memory"]):]
        if not self.config["fit_wind"]:
            # The imported learner receives no wind variation, so its c term remains zero.
            wind = 0.0
            for row in mine:
                row["wind_at_throw"] = 0.0
        power = self.learner.choose(target_x, wind, mine)
        power += self._noise("aim_power_error")
        return max(learner.POWER_LOW, min(learner.POWER_HIGH, power))

    def _nearest_target(self, state: Dict[str, Any], unit_state: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        opponents = [
            (uid, row) for uid, row in state["units"].items()
            if row["alive"] and row["team"] != unit_state["team"]
        ]
        if not opponents:
            raise RuntimeError("no public living target")
        return min(opponents, key=lambda item: abs(float(item[1]["x"]) - float(unit_state["x"])))

    def _noise(self, key: str) -> float:
        return self.rng.uniform(-float(self.config[key]), float(self.config[key]))


def choose_action(agent: LevelAgent, client: PublicToolClient) -> Dict[str, float]:
    """Make one throw decision using only state and the server's history tool."""
    state = client.call("get_public_state", {})
    history = client.call("get_history", {
        "limit": min(50, int(agent.config["memory"])), "unit": agent.unit, "include_path": False,
    })
    return {"angle": learner.ANGLE, "power": round(agent.choose_power(state, history["throws"]), 1)}
