# Kiro task 111 result (claude-sonnet-5.5): docs refresh, blocks B12, B13, B14
## What changed (only `(not published)`)
- JUDGES.md: the 8-topic table rewritten with the new 2026-11-15 evidence and done/partly/not done words. Steering row now uses `.kiro/steering/tech.md` and `.kiro/steering/rules.md`. Old `pk-checks.json` and `.kiro.hook` paths removed. Property row cites the counts below.
- README.md (119 lines): new section "Computer levels (scripts only)" with the sweep numbers copied from `docs/ai_levels_sweep_20261115.md`. The "How it was built" table updated the same way as JUDGES. Its `rules.md` mention now has the full path.
- CREDITS.md: new "Tools used" section (Kiro, models in the ledger, Claude Code, Qwen 2509 and 2511 as recorded). Local model: "not recorded".
## Verify
- `wc -l (not published)` (119). `grep -c AdaptiveLevel index.html` (0 found with the grep tool, so the page does not use the levels; README says so).
- `node scripts/test_particles.js`, `node scripts/test_ultimate.js`, `node scripts/test_ultimate_fx.js`, `node scripts/test_knight_ult.js`.
## Runs (my own, 2026-11-15)
- test_particles: last line `48/48 properties passed`, exit 0. test_ultimate: `all 24 tests passed`, exit 0. test_ultimate_fx: `all 6 tests passed`, exit 0.
- test_knight_ult: last line `test_knight_ult: 9 of 10 tests FAILED`, exit 1. Only the determinism test passed. I did not look for the cause. JUDGES and README say it fails.
## Not verified
- Path check: my script was refused by the shell. I listed the new paths with `ls` instead (sweep doc, framework plan, work queue, levels scripts, powers files, mcp.json, LICENSE, dock.css, gifs, plan docs) and with the file tools (six hook files, seven agents, seven steering files, spec folders, evidence files). All exist. The old unchanged paths were not rechecked.
- Brief says the IDE was used for "spec edits". No file I read records one, so JUDGES says "No file records an IDE spec edit". The 12-15 15:41 IDE session failed (WORK_QUEUE B01).
- README mentions `JUDGES.md`, `CREDITS.md`, `LICENSE`: they sit at the release root after export, so they do not resolve inside `(not published)`. Left as is.
- Hook evidence is from the older `.kiro.hook` file. No run of the six JSON files in the IDE is recorded.
- I did not run the level scripts or their tests. No test counts are claimed for them.
