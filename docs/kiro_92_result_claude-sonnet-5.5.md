# Kiro task 92 result (claude-sonnet-5.5)

## What changed
Only `(not published)` was rewritten (105 lines, under 120). This file is the only other file written.
1. Picture: `(not published)` right after the first paragraphs, relative link, with an alt text that says it is a preview GIF and not a play recording. I chose it over `svg_scene_gameplay_showcase.gif` because I opened that one: it is a 4 vs 4 mockup (395 HP, team panels), which the 1 vs 1 game does not show, so it would overclaim. Both gifs are INCLUDE in `scripts/release/export_manifest.json`.
2. First screen: what the game is, the MCP-seat idea, category, `HOSTED_URL` (literal). Two caveats before the picture (1 vs 1, Traditional Chinese text).
3. All limits moved to the last section "Known limits". Added two more true ones: the picture's labels show broken characters and the bat holds a dagger (rules say darts); the browser game and MCP engine are separate rule code with a different wind formula.
4. "Bring your own agent": keeps "The browser game does not call the MCP server". Added "Try it" with `python3 -B scripts/eval_agent_learning.py`.
5. "How it was built": 8-topic table with one path and a status each. Statuses come from `docs/kiro_verified.json` (MCP verified task 80; constants test verified; the rest "not checked"). The Hooks row says there is no IDE hook run log yet. The powers row says present, not installed or verified.
6. Removed the old long "What runs today" and "Tests" caveat text; no names, emails, local paths, credits or Co-Authored-By (grep found none).

## Run
- `python3 -B scripts/eval_agent_learning.py` ran, exit 0, last lines: `mean error rounds 1-5: 346.7 px | rounds 6-10: 153.6 px` and `OK: error fell by 56%`. The README quotes the first lines and the last two, with the middle rounds left out (marked `...`).

## Paths checked with `ls` (all exist)
`(not published)`, `docs/game_mode.md`, `docs/kiro_75_mcp_plan_claude-sonnet-5.5.md`, `docs/kiro_76_4v4_plan_claude-sonnet-5.5.md`, `docs/mcp_agent_protocol.md`, `docs/kiro_verified.json`, `docs/kiro_evidence/raw/hook_runs.log`, `scripts/mcp_stdio_server.py`, `scripts/mcp_game_server.py`, `scripts/eval_agent_learning.py`, `scripts/kiro_route.py`, `(not published)` for particles, audio, mcp_game, mcp_stdio, constants_sync, i18n, fonts, ingest_sheets, ingest_wind_sheets, postprocess_audio, `js/i18n.js`, `index.html`, `.kiro/steering/` and `tech.md`, `.kiro/settings/mcp.json`, `.kiro/agents/`, `(not published)`, `.kiro/specs/`, `.kiro/powers/pumpkin-killer-seat/`, `LICENSE`.
- `JUDGES.md` and `CREDITS.md` exist in `(not published)`; the README links them as root files, as the export does.

## Not run or not verified
- I did not re-run any test except `eval_agent_learning.py`. "`test_i18n.js` fails" and the optional-package list come from the old draft and `docs/kiro_verified.json` (2026-11-11), not from a new run.
- The hook log shows a manual dry run and "kiro result saved" entries with no recorded trigger. I read only its first part (the file is large); I did not prove where those runs came from.
- Seven agent files exist; I did not open them. Powers folder contents were only listed.
- The `HOSTED_URL` and `<REPOSITORY_URL>` placeholders are untouched.
- The earlier path-check loops were denied by the shell; a single `ls -d` over the paths was used instead. One `ls` with stderr counting gave a bogus 33 and was re-done in plain form, which listed every path.
