# MCP agent protocol

Server: `python3 -B scripts/mcp_stdio_server.py` (stdio, newline-delimited JSON-RPC 2.0, standard MCP
handshake: `initialize`, `notifications/initialized`, `ping`, `tools/list`, `tools/call`).
Options: `--mode human_vs_agent|agent_vs_agent|random_assignment`, `--seed N` (tests only),
`--turn-seconds 12`, `--memory-dir DIR` (or env `PK_MEMORY_DIR`; off by default, see `agent_memory_paths.md`).

## Tools

| Tool | Purpose |
|---|---|
| `get_public_state` | positions, hp, wind, round, `phase` (human / agent / over), seconds left, shield state, remaining ultimates, `remembered_enemy_paths` |
| `get_history` | last N throws: round, team, unit, `wind_at_throw`, `landing_x/y`, `hit_type`, `throw_id`, flight `path` points (every 6th step) |
| `submit_action` | `unit` + `action`: throw `{angle 25-80, power 0-115}`, move `{direction}`, defend `{path1, path2}` |
| `end_turn` | ends the current phase; pass `phase: "agent"` when you are the agent |
| `set_notes` / `get_notes` | per-match scratchpad (max 2000 chars) for lessons; the UI shows it |

## Rules the server enforces

- One action per unit per turn. A second submit is rejected; a defending unit cannot throw.
- Move: the engine rolls the die (1-6) and moves 36 px per pip; the agent never picks the number. Moving does not use the turn: one move per unit, then one attack; a move after the attack is rejected.
- Defend: knight only; two different `throw_id`s from `remembered_enemy_paths` (last 4 enemy throws).
- Ultimates in a room: `submit_action` with `type: "ultimate"` works for the skeleton, wizard, bat, bride, hunchback and hag; the knight's ultimate (hidden points) and the necromancer's ultimate (its flames start on a clock-driven orbit) are refused in a room with an error and change nothing (the page's own button refuses them too). Offline they work.
- A room judged by the page does not end your turn on the 12 s timer measured offline: the page decides when a turn ends (measured: still open after 5 s with a 3 s timer, and after 75 s); poll `get_public_state` about once a second while it is the other side's turn.
- Phases: human units act first, then agent units. Agent phase times out after 12 s; units that did not act idle.
- Failed calls return `isError: true` and do not use up the unit's action.

## Fairness

Public data only. No tool returns the RNG seed, the dice, future wind, or another side's unsubmitted
action. Human angle and power are not published, only landings and paths. There is no simulator tool:
the agent must infer the effect of power and wind from `get_history`.

## Playing as the opponent from Kiro

1. Enable the `pumpkin-killer` server (`.kiro/settings/mcp.json`).
2. Loop: `get_public_state` until `phase` is `agent`; `get_history` (limit 50); write your lessons with `set_notes`.
3. For each living unit you control: `submit_action` with `unit`, `action`, and `round` (guards against stale replies).
4. Call `end_turn` with `phase: "agent"`. Never act or end turns in the human phase.

## Remote Streamable HTTP MCP (`/mcp`)

For hosted or local-network play without installing the repo on the agent's machine, run `scripts/pk_mcp_http.py` (behind `/mcp` in `deploy/nginx.conf`, or locally via `python3 -B scripts/dev_server.py 8080 --with-relay --with-mcp`).

One-line client setup:
```sh
claude mcp add --transport http pumpkin-killer https://<host>/mcp
```
(Or generate JSON with `python3 -B scripts/make_agent_join_config.py --http https://<host>/mcp`.)

Additional room-lifecycle tools exposed on `/mcp` (and on stdio with `--room-tools` / `--relay <url>`):

| Tool | Purpose |
|---|---|
| `join_room` | Join a room by 6-character code or full invite URL (`?room=CODE&seat=...&team=...`). Auto-readies and reconnects automatically via `seat_token` + `resume` if the socket drops. |
| `wait_for_turn` | Short long-poll (up to 25 s) that wakes immediately when it is your turn, when the match ends, or on error; returns `status: "waiting"` cleanly before client HTTP timeouts. |
| `leave_room` | Leave the current room cleanly so the same MCP session can join another room without restarting. |

Hosted limits (MCP-RISK-A and MCP-RISK-B):
- One client may hold `PK_MCP_MAX_SESSIONS_PER_IP` (default 8) sessions on `/mcp`; the next `initialize` answers HTTP 429 with `Retry-After`. The whole server holds at most `PK_MCP_MAX_SESSIONS` (default 64), then 503. The client is `CF-Connecting-IP` when `PK_RELAY_TRUST_PROXY=1`, otherwise the `X-Real-IP` that nginx sets.
- The relay counts hosted seats per remote client (`PK_RELAY_MAX_PER_ADDR` applies to each client, not to all of `/mcp` together). The gateway proves itself with `PK_RELAY_GATEWAY_TOKEN`, which `deploy/entrypoint.sh` generates at start. Without the token the relay behaves as before. Page-judge mode (`PK_MCP_PAGE_JUDGE`, off by default when hosted) opens its sockets from a separate node process and is not covered.
