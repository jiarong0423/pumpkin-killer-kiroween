---
name: play
description: Play a Pumpkin Killer seat through the MCP tools: read your public view, choose angle and power, submit one action per unit turn, end the turn. Use when the user says join a room, take a seat, play Pumpkin Killer.
---
# Playing a seat fairly
1. Call `get_public_state` and `get_roster` first. They show only what a human at that seat sees: wind as the HUD shows it, unit positions on the 36 px grid, health bars, statuses, landing points of past throws. Do NOT try to read hidden state (other seats' pending actions, hidden Shield Wall points, aiming, seeds): the server refuses and the attempt is logged.
2. Use `get_history` (past landings and wind at the throw) and `get_notes` / `set_notes` (2000 characters) to learn from earlier throws.
3. Take ONE decision per unit turn: `submit_action` with `throw {angle 25-80, power 0-115}` (or throwable `ultimate`), then call `end_turn` as instructed by the tool response. (Offline Python-engine mode also supports `move {direction}` and `defend` with a 12 s timer; in live `PageJudgeRelay` rooms, turns allow throws/throwable ultimates only and end when the page completes resolution.)
4. The rules are the same as for a human: you cannot act out of turn, for another seat's unit, or with an illegal value. Never try to bypass them.
5. First side is decided by a coin toss in local mode.
6. Four room tools (`join_room`, `lock_hero`, `wait_for_turn`, `leave_room`) connect to live multiplayer lobby rooms (`1 v 1`, `2 v 2`, or `3 v 3`) over stdio (`scripts/mcp_stdio_server.py --room-tools`) or Streamable HTTP `/mcp` (`scripts/pk_mcp_http.py`), supporting one-use `invite=` tickets (call `lock_hero` to pick a unique hero on your team), full-team seats, or partial-unit `claim=1..units`.
