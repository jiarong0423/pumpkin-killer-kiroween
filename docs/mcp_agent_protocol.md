# MCP agent protocol

Server: `python3 -B scripts/mcp_stdio_server.py` (stdio, newline-delimited JSON-RPC 2.0, standard MCP
handshake: `initialize`, `notifications/initialized`, `ping`, `tools/list`, `tools/call`).
Options: `--mode human_vs_agent|agent_vs_agent|random_assignment`, `--seed N` (tests only),
`--turn-seconds 12`, `--memory-dir DIR` (or env `PK_MEMORY_DIR`; off by default, see `agent_memory_paths.md`).

## Tools

| Tool | Purpose |
|---|---|
| `get_public_state` | positions, hp, wind, round, `phase` (human / agent / over), seconds left, shield state, remaining ultimates, `remembered_enemy_paths` |
| `get_roster` | active hero roster, stats, and unit ownership (`owners`) for all units |
| `get_history` | last N throws: round, team, unit, `wind_at_throw`, `landing_x/y`, `hit_type`, `throw_id`, flight `path` points (every 6th step) |
| `submit_action` | `unit` + `action`: throw `{angle 25-80, power 0-115}`, `ultimate` (throwable heroes), and offline `skill` / `move` / `defend` |
| `end_turn` | ends the current phase; pass `round` and `phase` (in `PageJudgeRelay` rooms, follow `end_turn_args` returned by `submit_action`) |
| `set_notes` / `get_notes` | per-match scratchpad (max 2000 chars) for lessons; the UI shows it |

## Rules the server enforces

- One action per unit per turn (`1` unit acts per team turn across seats in team rooms). A second submit is rejected.
- `PageJudgeRelay` room mode (default `PK_MCP_PAGE_JUDGE=auto`, `scripts/page_judge_seat.js` on Node.js 22): accepts `throw` and throwable `ultimate`; `move`, `defend`, `skill`, Knight's ultimate, and Necromancer's ultimate are refused in rooms (`scripts/mcp_stdio_server.py`).
- Offline Python-engine mode: `move` rolls the die (1–6) and moves 36 px per pip before an attack; `defend` (Knight) takes two `throw_id`s from `remembered_enemy_paths`; phases time out after 12 s.
- A room judged by the page ends turns when the page finishes resolution rather than on the offline 12 s timer. Use `wait_for_turn` in room mode or poll `get_public_state` offline.
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

Additional room-lifecycle tools (4 room tools; **11 MCP tools total**) exposed on `/mcp` and on stdio with `--room-tools` / `--relay <url>`:

| Tool | Purpose |
|---|---|
| `join_room` | Join a room by 6-character code or invite URL (`?room=CODE&team=...&lobby=1&invite=...`). Supports `invite` (one-use ticket), `claim`, `heroes`, `name`, and auto-reconnects via `seat_token` + `resume` on socket drop. |
| `lock_hero` | Lock a chosen hero in lobby rooms (no duplicate hero on the same team); required for invited agents and after `lobby_reset` rematches. |
| `wait_for_turn` | Short long-poll (up to 25 s) that wakes on `your_turn` (gated on `page_my_turn` in `PageJudgeRelay`), `pick_again` (after refusal or `lobby_reset`), `game_over`, or error; returns `status: "waiting"` before HTTP timeouts. |
| `leave_room` | Leave the current room cleanly so the same MCP session can join another room without restarting. |

Hosted limits (MCP-RISK-A, MCP-RISK-B, and `LIVE-3V3-4`):
- One client may hold `PK_MCP_MAX_SESSIONS_PER_IP` (default 8) sessions on `/mcp`; the next `initialize` answers HTTP 429 with `Retry-After`. The whole server holds at most `PK_MCP_MAX_SESSIONS` (default 64), then 503. The client is `CF-Connecting-IP` when `PK_RELAY_TRUST_PROXY=1`, otherwise the `X-Real-IP` that nginx sets.
- The relay counts hosted seats per remote client (`PK_RELAY_MAX_PER_ADDR`, set to 16 in Coolify). The gateway proves itself with `PK_RELAY_GATEWAY_TOKEN`, which `deploy/entrypoint.sh` generates at start.
- **Page-judge mode is enabled by default in the container (`PK_MCP_PAGE_JUDGE=auto`, `PK_MCP_MAX_PAGE_JUDGES=10`, `nodejs` 22 in `deploy/Dockerfile.coolify`)**: invited MCP agents spawn a `--max-old-space-size=96` `scripts/page_judge_seat.js` child (~65 MB RSS per active process) judged on the real `index.html` VM and cleaned up on room exit or cap.
