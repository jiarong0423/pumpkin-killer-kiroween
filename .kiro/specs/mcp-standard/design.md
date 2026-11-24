# Design: standard MCP server

Team-size constraint: the engine accepts 1, 2, or 3 units per side. It formerly accepted 4 units per side.

## Layers

```
stdin/stdout  ->  serve()            read a line, parse JSON, write one line
              ->  McpServer          JSON-RPC and MCP methods, tools/list, tools/call
              ->  Session            match phases, action bookkeeping, timer, notes, staging
              ->  TrackedGameState   subclass of GameState (scripts/mcp_game_server.py)
```

`McpServer.handle_message` returns a dict or None, so tests and the evaluation call it without a subprocess.

## Engine wrapper

`TrackedGameState` changes no physics. It overrides two things:

- `compute_subagent_throw` returns `{}`, so the engine's built-in AI never throws for an agent. Units that do not act idle.
- `resolve_round` snapshots each pending throw's launch data (position, facing, angle, power, wind) before calling the base method. Afterwards it logs one record per throw with `round`, `wind_at_throw`, and a sampled path.

Path sampling (`sample_path`) re-integrates the throw with the engine's formula and constants (1/60 s steps, wind adds `wind * 45` px/s, release at `x + 25*facing`, `y - 65`) and stops at the step whose rounded position equals the recorded landing. It keeps every 6th point plus the release and landing points. It does not model collisions itself; the stop step comes from the engine's own landing record.

## Phases

```
human --end_turn(human)--> agent --end_turn(agent) or 12 s--> resolve --> next round
```

- A round starts in `human` if a human unit is alive, else in `agent`. If no agent unit is alive, ending the human phase resolves the round.
- The agent deadline is `clock() + 12`. It is checked at the start of every `tools/call` (lazy, no threads). The clock is injected for tests.
- `acted` maps unit to action type for the current round and is cleared when a round begins.

## Tool arguments

`submit_action` takes `unit`, `action`, optional `round`. Checks run in this order: arguments shape, stale round, match over, unit exists and alive, phase and controller, already acted, action type, action fields. Only success marks the unit as acted.

Defend: `path1` and `path2` are `throw_id`s among the last 4 throws of the other team. The engine has one shield box, so it is placed at the middle in-airspace point of path1; path2 is validated and recorded in the public shield state (`path_ids`), not enforced by physics. This is a known gap.

## Fairness

- `get_public_state` is built from `GameState.get_public_state()` minus `landing_history` (history comes from `get_history`), plus phase, timer, `class`, `acted`, remembered path ids.
- `public_throw` hides angle and power for human throws.
- The dice use a separate `random.Random` derived from the seed. Nothing returns it.
- The staging folder (`--memory-dir`) holds public data only. `meta.json` has no seed and the folder id uses the engine `match_id`, which departs from `agent_memory_paths.md` (it lists the seed).

## Evaluation

`scripts/eval_agent_learning.py` subclasses the engine to keep one unkillable target at a fixed x. The agent fits `landing_x ~ b*power + c*wind` by ridge regression on all pairs of past throws and corrects from the nearest past throw. It uses the tools through `McpServer.handle_message`.

## Open points

- Move size is 36 px per pip (`docs/game_mode.md`); the task text said 16. One constant: `MOVE_PX_PER_PIP`.
- Moving does not use the turn (owner decision 2026-11-09, follows `game_mode.md`): one move, then one attack per unit; move after an attack is rejected.
- Ultimates are not selectable; `ultimates_remaining` is always 2.
