# Tasks: levels and start screen (levels-ui)
Written 2026-11-15. None is done. A task is done only when the main line has rerun its test or check and recorded it in `docs/kiro_verified.json`.

Rules for every task that touches `index.html`:
- `index.html` changes happen one task at a time. A wiring task starts only after the previous `index.html` task (in this spec or in `ultimates-v2`) is finished and recorded.
- The main line applies each `index.html` change and verifies it in the browser, then records the run. Kiro does not mark such a task done.

Before any task: the owner answers open decision 1 in `requirements.md` (multiplayer seat for the adaptive level). Task 3 can go ahead with the single-human limit in `design.md` if the answer is late.

- [ ] 1. Read-only check. Read `scripts/agent_levels.py`, `scripts/adaptive_level.py`, `js/adaptive_level.js`, `scripts/adaptive_level_vectors.json`, `docs/ai_levels_sweep_20261115.md`, and the start-screen, difficulty, match-start and match-end code in `index.html`. Write findings in `(not published)`: how the levels are stored, whether the page can use them, how the hero and battlefield cards are built, where match state is created and reset. Correct `requirements.md` and `design.md` where they differ. (Req 1 to 3, 11, 17 to 19)
- [ ] 2. Level table and shared-vector tests. Settle option A or B in `design.md`; add the page-readable level table and a check that it matches `agent_levels.py`. Run the existing tests for the adaptive module on `scripts/adaptive_level_vectors.json` (Python and Node) and add cases for the bounds, the cooldown and the 2-change limit if the vectors lack them. Test commands are confirmed in task 1. (Req 2, 4 to 10)
- [ ] 3. `index.html` wiring of the levels and the adaptive state: level picker, one adaptive state per match, human throws fed to the module, level applied to the computer seats, reset at match start and end, no storage calls. Main line applies it and verifies it in the browser: a fixed-level match for each of the three levels, and an adaptive match that changes level at least once up and once down (use a scripted or seeded run if a real one is too slow). Record the runs. (Req 1, 3, 4, 15, 16)
- [ ] 4. `index.html` HUD: the level line, the adaptive reason line, and `ai_level` and `ai_reason` in the public state. Main line verifies in the browser that the level shows in every computer match and that the reason shows after a change and clears at the next match. (Req 12 to 14)
- [ ] 5. `index.html` start-screen cleanup: remove the three grey hero cards and the two "in production" battlefield cards (markup or data, not CSS hiding). Main line verifies in the browser that only the built heroes and the finished battlefield show, that each built hero still starts a match, and reruns the existing test scripts. In the same step the main line or the owner adds the "planned" paragraph to `README.md` listing ghost bride, hunchback, necromancer and the two battlefields (Kiro does not edit `README.md` under this spec). (Req 17 to 21)
- [ ] 6. Main-line rerun of the adaptive tests (Python and Node, same vectors), the level-table check, and the grep that finds no `localStorage` or cookie use in the new code; record in `docs/kiro_verified.json`. (Req 2, 9, 16, 22)

Order: 1, then 2, then 3, 4, 5 one at a time (each only after the previous `index.html` task is recorded), then 6. Tasks 3 to 5 also queue behind `ultimates-v2` tasks 3 and 5 when those are open.

Art needed from the owner: none.
