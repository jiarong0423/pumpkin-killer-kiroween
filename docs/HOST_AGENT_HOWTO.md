# Bring your own agent to a room (host how-to)

You open a room, your own AI agent plays the other seat. The agent runs **on your machine with your own model account**: the game server only relays small structured messages (throws, hits, hashes) and never calls a model, so the game costs the owner nothing and you control what your agent costs.

## What you need
- **Hosted / Streamable HTTP (`/mcp`)**: zero local repo or runtime install on the agent machine — connect directly to `https://<host>/mcp` (`join_room` supports both 6-char room codes and one-use `invite` tickets from the lobby).
- **Local stdio bridge (`scripts/mcp_stdio_server.py`)**: this repository (since `PageJudgeRelay` loads `index.html` and `js/` to judge turns identically to the browser), **Node.js 22 or newer** (required for global `WebSocket` in `scripts/page_judge_seat.js`), and Python 3.9+ (`websockets`).

## 1. Open the room and invite your agent
1. On the start screen pick **1 v 1**, **2 v 2**, or **3 v 3** and click **Play with friends** (enter a one-time display name).
2. In the full-screen **Lobby**, tick **Allow agents** (host only).
3. Any seated player can click **Invite an agent** to generate a one-use ticket, or share the **6-character room code** and `/mcp` URL.

## 2. Make the agent's configuration
For remote Streamable HTTP `/mcp` (recommended):

```bash
python3 -B scripts/make_agent_join_config.py --http https://<host>/mcp
```

For Claude Code directly over `/mcp`:

```bash
claude mcp add --transport http pumpkin-killer https://<host>/mcp
```

Or for local stdio connecting from this repository (`--room-tools` / `--relay`):

```bash
python3 -B scripts/make_agent_join_config.py --relay wss://<relay host>/relay --code <ROOM CODE>
```

Each agent calls `join_room(room=<code or invite URL>, invite=<ticket>, name=<agent name>)` followed by `lock_hero(hero=<id>)` (no duplicate heroes on a team), or claims whole/partial slots via `claim=1..units`.

## 3. Tell the agent how to play
A short instruction is enough:

> Join the room with `join_room` and pick a hero with `lock_hero`. Loop `wait_for_turn`, read `get_public_state`, `get_roster`, and `get_history`, submit one action as `{"unit": "<active_unit>", "action": {"type": "throw", "angle": 50, "power": 75}}` (angle 25–80, power 0–115; or `"type": "ultimate"` for a throwable ultimate), and call `end_turn` as instructed by the tool reply. Use `set_notes` to remember what worked. You only see what a human sees: positions, hp, wind and weather as shown.

11 MCP tools: 7 game tools (`get_public_state`, `get_roster`, `get_history`, `submit_action`, `end_turn`, `set_notes`, `get_notes`) and 4 room tools (`join_room`, `lock_hero`, `wait_for_turn`, `leave_room`).

## 4. What the agent can and cannot see
It sees the public state only (the same numbers a player sees). It is not given the game's flight formula or any hidden value, and it plays through the same turn rules and limits as a human seat.

## Limits and messages
- The relay caps rooms (200), connections per address (configurable via `PK_RELAY_MAX_PER_ADDR`), spectators per room (12) and message rate (10 per second per connection). Messages you may see: `server_busy`, `rate_limited`, `room_full`, `unknown_code`, `team_full`.
- Idle rooms are closed after 30 minutes without messages.
- Your agent's model usage is on your own account; a short turn is a few small tool calls.

## What the agent can do today
Throws and throwable ultimates in a room (items, shield, movement, `skill`, and the Knight/Necromancer ultimates remain offline/local-only; `join_room` supports `invite=` or `claim=1..units` so an agent can take a full team or share a team with humans or computer seats). Room play is always judged by **`PageJudgeRelay`** (`scripts/page_judge_seat.js`, which needs Node.js 22 or newer; since 2026-11-27 the server refuses to start with `auto` or `off`), keeping HP, hits, and `round_hash` bit-exact with browser seats across `1v1`, `2v2`, and `3v3`.
