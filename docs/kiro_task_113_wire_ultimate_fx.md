# Kiro task 113 — spec task 3: wire the ultimate effects module into the page (the only `index.html` task now)

You are the only writer of `index.html` during this task; the main line will not touch it. Back it up first: copy `index.html` to `(not published)` (the folder is git-ignored).

Read: `.kiro/specs/ultimates-v2/requirements.md` (requirements 1 to 9), `design.md`, `tasks.md` (task 3), `js/ultimate_fx.js`, `scripts/test_ultimate_fx.js`, `docs/kiro_99_result_gpt-5.6-terra.md`, `docs/kiro_evidence/visual/BASELINE_ULT_20261115.md`, and in `index.html` the ultimate branches in `executeThrow` (grep `ultThrow`, `ultBlast`, `ultGroup`, `proj_spear`, `cannonball`, `proj_shuriken`) and how the page loads other `js/*.js` files (script tags near the end of `<head>` or `<body>`).

Do:
1. Add `<script src="js/ultimate_fx.js"></script>` where the other modules load. Do not add a build step.
2. In `executeThrow`, for the bat, skeleton and wizard ultimates, call the timelines from `UltimateFx` to schedule the extra visual effects (use the page's existing particle and floating-text helpers); keep EVERY damage number, the energy and `ultUsed` bookkeeping and the `ULT_BUILT` list exactly as today. If `UltimateFx` is not defined, the page must behave exactly as before (guard with `typeof UltimateFx !== "undefined"`).
3. Keep the effect layer from covering the top bar, the timer, the wind readout, the health bars and the bottom dock (use the existing avoid areas if the page has them).
4. Verify with commands only: `node scripts/test_ultimate_fx.js`, `node scripts/test_ultimate.js`, `node scripts/test_particles.js`, `python3 -B scripts/test_constants_sync.py`, `python3 -B scripts/test_preload_links.py`, `python3 -B scripts/test_mcp_game.py`; paste the last lines. Do not claim the effects look right: the main line looks at them in the browser.

Touch only `index.html`, `.kiro/specs/ultimates-v2/tasks.md` (tick task 3 only if the commands above pass) and the result file exactly `(not published)` (max 20 lines: what you changed by function name, commands with last output lines, what you did not run). No network, no git.
