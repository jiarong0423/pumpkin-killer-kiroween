---
name: play
description: Play a Pumpkin Killer seat through the MCP tools: read your public view, choose angle and power, submit one action per unit turn, end the turn. Use when the user says join a room, take a seat, play Pumpkin Killer.
---
# Playing a seat fairly
1. Call `get_public_state` first. It shows only what a human at that seat sees: wind as the HUD shows it, unit positions on the 36 px grid, health bars, statuses, landing points of past throws. Do NOT try to read hidden state (other seats' pending actions, shields, aiming, seeds): the server refuses and the attempt is logged.
2. Use `get_history` (past landings and wind at the throw) and `get_notes` / `set_notes` (2000 characters) to learn from earlier throws.
3. Take ONE decision per unit turn: `submit_action` with `throw {angle 25-80, power 0-100}`, `move {direction}` (the die decides the steps) or `defend` (knight only), then `end_turn`. A turn lasts 12 seconds (7 if stunned); a timeout forfeits that unit's turn only.
4. The rules are the same as for a human: you cannot act out of turn, for another seat's unit, or with an illegal value. Never try to bypass them.
5. First side is decided by a coin toss: when asked, call heads or tails once.
6. Room tools (`join_room`, `leave_room`, `wait_for_turn`) connect to a live multiplayer room (`1 v 1`, `2 v 2`, or `3 v 3`) over stdio (`scripts/mcp_stdio_server.py`) or Streamable HTTP (`/mcp`, `scripts/pk_mcp_http.py`), supporting both full-team seats and partial-unit `claim=1..units`.
