# Kiro task 75 — MCP planning (Sonnet = systems; main line verifies everything)

**READ FIRST: docs/owner_decisions_20261110_agents_headless.md (decided by the owner today: every player brings their own sub-agent, the game is headless in principle, everything modular and maintainable). Your plan must be built on these; where an earlier instruction in this brief conflicts, the decisions file wins.**


Owner 2026-11-10: Kiro owns the MCP PLAN (and the art prompts, which are task 73). Read first: docs/ROLES.md, (not published), (not published), .kiro/settings/mcp.json, .kiro/specs/ (every spec that mentions MCP), scripts/mcp_game_server.py and its tests (read only), (not published) rows that mention MCP, the AI-opponent code in index.html (read only). Owner rules in the log are decided: do not reopen them.

Deliver ONE file: docs/kiro_75_mcp_plan_claude-sonnet-5.5.md (max 200 lines), no code or config edits:
1. Current state: what the MCP game server already offers (tool list, data it exposes, what is hidden from the agent to keep it fair), what .kiro/settings/mcp.json registers, which tests exist. Mark each statement READ (from a file, give the path:line) or ASSUMED.
2. The goal: an MCP opponent mode where a sub-agent plays against the human with only public information (the same view the human has), plus whatever else MCP should do for the project and for the Kiroween judges to see (for example: a read-only status tool, a match-replay tool, an asset-inventory tool for docs/asset_inventory.json, a run-measure tool for the AI hit rate). For each candidate: purpose, tools and arguments, data hidden, who calls it, cost, risk, and whether it is worth building before the deadline (2026-12-04, freeze 2026-11-27 provisional).
3. Fairness and safety rules: what the agent may never see (exact wind noise, the AI's own aiming state, hidden shield points A-B-C), rate limits, no network beyond localhost, no file writes outside a scratch folder, no secrets; list the checks the main line can run to prove it.
4. A schedule: ordered steps, size, dependencies, what needs the owner, and a verification command per step.
5. Open owner decisions, each as one short question with your recommendation first.
Do not claim anything was run. Plain English.
