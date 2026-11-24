# Bring your own agent to a room (host how-to)

You open a room, your own AI agent plays the other seat. The agent runs **on your machine with your own model account**: the game server only relays small structured messages (throws, hits, hashes) and never calls a model, so the game costs the owner nothing and you control what your agent costs.

## What you need on the agent's machine
This repository (the bridge runs the real game page in the background to judge shots, so `index.html` and `js/` must be there), **Node.js 18 or newer** and Python 3.9 or newer. Nothing else is installed on the server side.

## 1. Open the room
In the game choose the team size (1 to 3 units), pick **Agent** for the other seat, press Start. The screen shows a **6-character room code** and a QR code.

## 2. Make the agent's configuration
On the machine that runs your agent, from this repository:

```bash
python3 -B scripts/make_agent_join_config.py --relay wss://<relay host>/relay --code <ROOM CODE>
```

It prints an MCP server entry. Paste it into your agent's MCP settings (Kiro, Claude Desktop, ...). For Claude Code use the one-line form instead:

```bash
python3 -B scripts/make_agent_join_config.py --relay wss://<relay host>/relay --code <ROOM CODE> --claude-command
```

`--seat red|white` picks the seat (default white, the right side). The agent joins the room, sends ready, and the match starts when you are ready too.

## 3. Tell the agent how to play
A short instruction is enough:

> You play the white seat of a turn-based artillery game through the MCP tools. Each turn call `get_public_state`, read `get_history` for where earlier shots landed, then `submit_action` for the active unit (angle, power; a move before the throw is allowed) and `end_turn`. Use `set_notes` to remember what worked. You only see what a human sees: positions, hp, wind and weather as shown. Aim from your own earlier shots.

Tools: `get_public_state`, `get_history`, `get_roster`, `get_notes`, `set_notes`, `submit_action`, `end_turn`.

## 4. What the agent can and cannot see
It sees the public state only (the same numbers a player sees). It is not given the game's flight formula or any hidden value, and it plays through the same turn rules and limits as a human seat.

## Limits and messages
- The relay caps rooms (200), connections per address (8), spectators per room (12) and message rate (10 per second per connection). Messages you may see: `server_busy` (the server is full, try later), `rate_limited` (slow down), `room_full`, `unknown_code`.
- Idle rooms are closed after 30 minutes without messages.
- Your agent's model usage is on your own account; a short turn (read state, one action) is a few small calls. Use a cheap model.

## What the agent can do today
Throws and thrown ultimates in a room (items, shield, and movement remain local-only; `join_room` supports `claim=1..units` so an agent can take a full team or share a team with humans or other agents). The bridge uses the real page as its judge, so hits, hp and the round hash agree with the other seats (verified across 1v1, 2v2, and 3v3 mixed-seat matches, `scripts/test_mcp_claim.py`, `docs/HYBRID_RUN_20261117.md`).
