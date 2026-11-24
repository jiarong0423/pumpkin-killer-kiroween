# Tasks: class stats

Kiro task 42 (all done):
- [x] 1. Read `docs/class_stats_judgement.md`, `docs/playtest_fixes.md` (knight, ground skip), `docs/converge_characters.md` (invented numbers), `HERO_PROFILES` in `index.html` (read only).
- [x] 2. Write this spec: requirements (16, each checkable), design.
- [x] 3. `js/class_stats.js`: `CLASSES`, `PROVISIONAL`, `hitsToKill`, `expectedDamage`, `expectedDamageDetail`, `power`, `powerTable`, `matrix`, `matrixStats`, `validate`, `compareTables`, `ultimatePerUnit`, `ultimateOneTarget`, `oneShotRisks`, `formatMatrix`. (Req 1 to 15)
- [x] 4. `scripts/test_class_stats.js`: 17 tests; the provisional fixture is read from `index.html`, the recommended matrix is compared with the document cell for cell, and the difference between the two tables is printed. (Req 1 to 16)
- [x] 5. Run `node scripts/test_class_stats.js` and record the last line in `docs/implementation_report.md`.
- [x] 6. Write the wiring note for the main line in `docs/implementation_report.md`.

Handed to the main line (not part of task 42; `index.html` was not touched):
- Decide the knight's `dTyp` after the robot run (the simulator measures about 17, the hand estimate is 20).
- Decide the bride (see the report: the simulator finds her far weaker than the hand model).
- When `(not published)` exists, read the numbers from there and keep this file as a test fixture.
