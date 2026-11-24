#!/usr/bin/env python3
"""Measure the seeded public-information agent levels through MCP tools."""
import argparse
import math
import os
import sys
import tempfile
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import agent_levels
import eval_agent_learning as learner

DEFAULT_SEEDS = (101, 202, 303, 404, 505, 606, 707, 808)
MODES = ("human_vs_agent", "agent_vs_agent")
REPORT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "docs", "ai_levels_sweep_20261115.md")


def mean(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def wilson_interval(hits: int, throws: int) -> Tuple[float, float]:
    """Return the two-sided 95% Wilson interval without external statistics packages."""
    if not throws:
        return 0.0, 0.0
    z = 1.959963984540054
    rate = hits / throws
    denom = 1.0 + z * z / throws
    centre = (rate + z * z / (2.0 * throws)) / denom
    radius = z * math.sqrt(rate * (1.0 - rate) / throws + z * z / (4.0 * throws * throws)) / denom
    return centre - radius, centre + radius


def play_match(level: str, seed: int, mode: str, throws: int) -> List[Tuple[float, bool]]:
    """Run one fixed-target match, submitting each action only through the MCP server."""
    if mode not in MODES:
        raise ValueError("unsupported mode: %s" % mode)
    session = learner.srv.Session(mode=mode, seed=seed, clock=lambda: 0.0, turn_seconds=12,
                                 engine_cls=learner.FixedTargetEngine)
    client = agent_levels.PublicToolClient(learner.srv.McpServer(session))
    agent = agent_levels.LevelAgent(level, seed * 31 + MODES.index(mode), unit=learner.UNIT)
    rows: List[Tuple[float, bool]] = []
    for _round in range(throws):
        if mode == "human_vs_agent":
            client.call("end_turn", {"phase": "human"})
        action = agent_levels.choose_action(agent, client)
        client.call("submit_action", {
            "unit": learner.UNIT,
            "action": {"type": "throw", "angle": action["angle"], "power": action["power"]},
        })
        summary = client.call("end_turn", {"phase": "agent"})
        throw = next(row for row in summary["throws"] if row["unit"] == learner.UNIT)
        target_x = session.engine.units[learner.TARGET]["x"]
        rows.append((abs(float(throw["landing_x"]) - float(target_x)), throw["hit_type"] == "hero"))
    if set(client.calls) - agent_levels.PUBLIC_TOOLS:
        raise AssertionError("agent used a tool outside the published six")
    return rows


def allocations(total_throws: int, seeds: Sequence[int]) -> List[Tuple[int, str, int]]:
    """Divide throws over every seed and each required MCP match mode."""
    slots = [(seed, mode) for seed in seeds for mode in MODES]
    if total_throws < len(slots):
        raise ValueError("throws must be at least %d to cover every seed and mode" % len(slots))
    base, remainder = divmod(total_throws, len(slots))
    return [(seed, mode, base + (1 if index < remainder else 0))
            for index, (seed, mode) in enumerate(slots)]


def measure_level(level: str, total_throws: int, seeds: Sequence[int]) -> Dict[str, float]:
    """Aggregate hit and learning-curve measurements across seeded MCP matches."""
    rows: List[Tuple[float, bool]] = []
    first_halves: List[float] = []
    second_halves: List[float] = []
    for seed, mode, count in allocations(total_throws, seeds):
        match = play_match(level, seed, mode, count)
        rows.extend(match)
        half = count // 2
        first_halves.append(mean(error for error, _hit in match[:half]))
        second_halves.append(mean(error for error, _hit in match[-half:]))
    hits = sum(1 for _error, hit in rows if hit)
    low, high = wilson_interval(hits, len(rows))
    return {
        "level": level,
        "throws": len(rows),
        "hits": hits,
        "hit_rate": hits / len(rows),
        "first_half_error": mean(first_halves),
        "second_half_error": mean(second_halves),
        "ci_low": low,
        "ci_high": high,
    }


def run_sweep(total_throws: int = 400, seeds: Sequence[int] = DEFAULT_SEEDS) -> List[Dict[str, float]]:
    if len(seeds) < 5:
        raise ValueError("at least five seeds are required")
    return [measure_level(level, total_throws, seeds) for level in agent_levels.LEVEL_NAMES]


def render_table(rows: Sequence[Dict[str, float]]) -> List[str]:
    lines = [
        "| level | throws | hits | hit rate | mean landing error, first half | mean landing error, second half | 95% hit-rate interval |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append("| %(level)s | %(throws)d | %(hits)d | %(rate).1f%% | %(first).1f px | %(second).1f px | %(low).1f%%–%(high).1f%% |" % {
            "level": row["level"], "throws": int(row["throws"]), "hits": int(row["hits"]),
            "rate": 100.0 * row["hit_rate"], "first": row["first_half_error"],
            "second": row["second_half_error"], "low": 100.0 * row["ci_low"], "high": 100.0 * row["ci_high"],
        })
    return lines


def write_report(rows: Sequence[Dict[str, float]], total_throws: int, seeds: Sequence[int]) -> None:
    command = "python3 -B scripts/sweep_agent_levels.py --throws %d --seeds %s" % (
        total_throws, " ".join(str(seed) for seed in seeds))
    lines = [
        "# AI level sweep — 2026-11-15",
        "",
        "Command: `%s`" % command,
        "",
        "Each level has %d total throws split over the human-vs-agent and agent-vs-agent MCP modes and seeds %s. "
        "Each action uses only the six published MCP tools. Landing error is absolute horizontal error; "
        "the two error columns average the first and second halves of each seeded match." %
        (total_throws, ", ".join(str(seed) for seed in seeds)),
        "",
        *render_table(rows),
        "",
        "The 95% interval is the Wilson interval for the observed hit rate.",
    ]
    with open(REPORT_PATH, "w", encoding="utf-8") as report:
        report.write("\n".join(lines) + "\n")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--throws", type=int, default=400, help="total throws per level (default: 400)")
    parser.add_argument("--seeds", type=int, nargs="+", default=list(DEFAULT_SEEDS))
    args = parser.parse_args(argv)
    try:
        rows = run_sweep(args.throws, args.seeds)
    except ValueError as error:
        parser.error(str(error))
    write_report(rows, args.throws, args.seeds)
    for line in render_table(rows):
        print(line)
    rates = [row["hit_rate"] for row in rows]
    if not rates[0] < rates[1] < rates[2]:
        print("FAIL: hit-rate order is not easy < normal < hard")
        return 1
    print("PASS: hit-rate order easy < normal < hard")
    return 0


if __name__ == "__main__":
    sys.exit(main())
