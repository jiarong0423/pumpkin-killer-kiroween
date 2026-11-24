# Tasks: standard MCP server

Team-size constraint: the engine accepts 1, 2, or 3 units per side. It formerly accepted 4 units per side.

- [x] 1. `scripts/mcp_stdio_server.py`: JSON-RPC loop, MCP handshake, `tools/list`, `tools/call`.
- [x] 2. `TrackedGameState` subclass: agent AI off, per-throw log with wind and sampled path.
- [x] 3. Tools: `get_public_state`, `get_history`, `submit_action` (throw, move, defend), `end_turn`, `set_notes`, `get_notes`.
- [x] 4. Phases, one action per unit per turn, defend/throw exclusion, die for moves, 12 s agent timeout (injected clock).
- [x] 5. Optional staging folder from `(not published)` (public data only).
- [x] 6. `scripts/test_mcp_stdio.py`: subprocess protocol tests and in-process session tests.
- [x] 7. `scripts/eval_agent_learning.py`: history-only baseline agent, learning-curve check.
- [x] 8. `.kiro/settings/mcp.json` and `docs/mcp_agent_protocol.md`.
- [ ] 9. Reviewer runs `python3 -B scripts/test_mcp_stdio.py`, `python3 -B scripts/eval_agent_learning.py`, `python3 -B scripts/test_mcp_game.py` (not run by the author).
- [x] 10a. Owner decided 2026-11-09: move 36 px per pip; moving does not use the turn; only path1 is enforced by the shield (path2 recorded only, until the 3v3 round flow is fixed).
- [ ] 10b. Add `(not published)` to `.gitignore` (main line).
