# Tasks: balance simulator

Kiro task 42 (all done):
- [x] 1. Read `docs/class_stats_judgement.md`, `docs/playtest_fixes.md`, the projectile loop, `executeThrow`, `aiAttackNow`, `resolveRound` and the move code in `index.html` (read only).
- [x] 2. Write this spec: requirements (22, each checkable), design.
- [x] 3. `scripts/sim_balance.js`: physics, the six class rules, the cat's volley through the real ledger, the bot, `simulateMatch`, `runPairings`, report, command line. (Req 1 to 12, 17 to 21)
- [x] 4. `scripts/test_sim_balance.js`: 27 tests; constants read from `index.html`; rules played with hand-placed projectiles; determinism, no NaN, the match ends; symmetric totals; the command line. (Req 1 to 21)
- [x] 5. Run the simulator for the provisional and the recommended values (200 matches per pairing, seed 7) and keep the real matrices in `docs/implementation_report.md`. Extra runs: aim error 5 and 14, knight rule A, wave rule centre.
- [x] 6. Run `node scripts/test_sim_balance.js` and record the last line in `docs/implementation_report.md`.
- [x] 7. Write the wiring note and the findings for the main line in `docs/implementation_report.md`.

Handed to the main line (not part of task 42):
- Decide the numbers after reading the findings (bride, hunchback, skeleton, knight rule).
- Add the sky shield and a human-like bot (unknown wind) if the owner wants a closer check.
- Run the simulator in the test hook after any number in `HERO_PROFILES` changes.
