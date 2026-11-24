# Kiro task 07 — standard MCP server and "sub-agents learn to counter" (adversarial) interface

Context: `scripts/mcp_game_server.py` has the game rule engine plus a hand-rolled JSON-RPC loop that is NOT the standard MCP handshake.
Shared numbers are in `shared/constants.json` (already on this branch). Rules: `docs/game_mode.md` (read it).
Design intent (owner): the opponent units are LLM sub-agents that LEARN during the match: they only see public information
(positions, wind, hp, shield state, and the history of past throws: where they landed and the flight path points), NOT a ballistic simulator,
NOT hidden state. Between rounds they adjust aim from that history (in-context learning, no model training). The remembered
paths are also what the Pumpkin Guard's floating shield uses (it remembers the last 4 enemy paths).

## Do exactly this
1. Create `scripts/mcp_stdio_server.py` (stdlib only, no pip): a STANDARD MCP server over stdio (newline-delimited JSON-RPC 2.0):
   `initialize` (reply with `protocolVersion`, `capabilities: {tools: {}}`, `serverInfo`), accept `notifications/initialized`, `ping`,
   `tools/list` (JSON-Schema `inputSchema` for every tool), `tools/call` (result `content: [{type:"text", text: <json string>}]`, `isError` on failure).
   Wrap the existing engine class from `scripts/mcp_game_server.py` (import it; do NOT change its physics).
2. Tools: `get_public_state` (positions, wind, round, hp, shield state, remaining ultimates, whose phase it is),
   `get_history` (last N throws: team, unit, landing_x, landing_y, hit_type, wind_at_throw, round, and the sampled flight path points),
   `submit_action` (unit, action = throw{angle, power} | move{direction: forward|backward} | defend{path1, path2}); one action per unit per turn;
   a second submit for the same unit is rejected; a defending unit cannot throw; moves use a die (1-6, 16 px per pip) chosen by the engine, not the agent;
   `end_turn`, `set_notes` / `get_notes` (a per-match scratchpad the agent writes its lessons into, e.g. "player aims about x=640"; the UI will show it).
   Agent phase has a 12 s timeout per turn: on timeout the unit idles. No tool may return the RNG seed or any hidden value.
3. Create `scripts/test_mcp_stdio.py` (stdlib `unittest`, spawns the server as a subprocess and speaks JSON-RPC): handshake works, `tools/list`
   returns all tools with schemas, `get_public_state` has no hidden fields, double submit rejected, defend+throw rejected, bad args give `isError`,
   timeout logic unit-tested with an injected clock.
4. Create `scripts/eval_agent_learning.py`: a scripted baseline agent that uses ONLY `get_history` (e.g. nearest-neighbour correction of angle/power
   from past landing errors) plays N seeded rounds against a fixed target and prints hit rate per round; assert the average error in rounds 6-10 is
   lower than in rounds 1-5 (a measurable "it learns" curve). Seed everything.
5. Add `.kiro/settings/mcp.json` registering the server for Kiro (command `python3`, args `["-B", "scripts/mcp_stdio_server.py"]`) and a short
   `docs/mcp_agent_protocol.md` (<= 40 lines) describing the tools, the fairness rules and how a Kiro agent can play as the opponent.
6. Spec in `.kiro/specs/mcp-standard/` (`requirements.md` EARS, `design.md`, `tasks.md`).
7. Do NOT edit `index.html`, `scripts/mcp_game_server.py` physics, or `assets/`. No git commands. Existing `python3 -B scripts/test_mcp_game.py` must keep passing.
8. Finish with a 6-line summary: files, tools, any protocol detail you were unsure about, what you could not run (you cannot run Python/Node; the reviewer will).

## AMENDMENT (supersedes anything above that conflicts)
- You may NOT edit any EXISTING file (edits are refused in this environment). Create NEW files only.
- Do not change `scripts/mcp_game_server.py`. To get flight-path samples and `wind_at_throw`, WRAP or SUBCLASS the engine inside the new `scripts/mcp_stdio_server.py`
  (for example record the (x, y) positions yourself by re-integrating each throw with the same constants from `shared/constants.json`, every 6th step), or leave the paths out and say so.
- `docs/game_mode.md` and `(not published)` now exist in this directory: read them.
- You cannot run Python; the reviewer will run every test. Say which parts are untested.
