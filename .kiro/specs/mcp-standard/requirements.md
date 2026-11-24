# Requirements: standard MCP server and learning sub-agents

Notation: EARS. "The server" is `scripts/mcp_stdio_server.py`.

Team-size constraint: the engine accepts 1, 2, or 3 units per side. It formerly accepted 4 units per side.

## Protocol

1. When the server receives `initialize`, the server shall reply with `protocolVersion`, `capabilities: {tools: {}}` and `serverInfo`, echoing the client's version if supported and otherwise its latest supported version.
2. When the server receives a notification (no `id`), including `notifications/initialized`, the server shall not reply.
3. When the server receives `ping`, the server shall reply with an empty result.
4. When the server receives `tools/list`, the server shall return every tool with a JSON-Schema `inputSchema`.
5. When the server receives `tools/call` for a known tool, the server shall return `content: [{type: "text", text: <JSON string>}]` and set `isError` to true if the call fails.
6. If the tool name is unknown, the server shall return JSON-RPC error -32602. If a method is unknown, -32601. If a line is not valid JSON, -32700 with `id` null.
7. The server shall write only protocol messages to stdout, one JSON object per line.

## Tools and rules

8. The server shall provide `get_public_state`, `get_history`, `submit_action`, `end_turn`, `set_notes`, `get_notes`.
9. The server shall reuse the engine class in `scripts/mcp_game_server.py` without changing its physics.
10. When `get_history` is called, the server shall return the last N throws with round, team, unit, `wind_at_throw`, landing point, `hit_type` and sampled flight path points.
11. If a unit has already submitted an action this turn, then the server shall reject a second `submit_action` for it, and the rejection shall not alter state.
12. If a unit is defending, then the server shall reject a throw by that unit.
13. When a unit moves, the server shall roll a die from 1 to 6 and move the unit 36 px per pip; the agent shall not choose the number.
14. If a unit other than the knight submits `defend`, or `path1`/`path2` are not two different remembered enemy throws, then the server shall reject the action.
15. While the phase is `human`, the server shall accept actions only for human-controlled units; while `agent`, only for agent-controlled units.
16. If an argument is missing, mistyped, out of range, non-finite or unknown, then the server shall return `isError: true` and leave the unit's action unused.
17. When the agent phase has lasted 12 s (injected clock), the server shall idle units that have not acted and resolve the round.
18. The server shall limit notes to 2000 characters.

## Fairness

19. The server shall not return the RNG seed, the dice stream, pending actions, or future wind in any tool result or staged file.
20. The server shall not publish a human unit's angle or power, only its landing point and path.
21. The server shall not provide a trajectory simulator or trial-throw tool.

## Evaluation

22. When the baseline agent, using only `get_history`, plays seeded rounds against a fixed target, the mean error in the second half of the rounds shall be lower than in the first half.
