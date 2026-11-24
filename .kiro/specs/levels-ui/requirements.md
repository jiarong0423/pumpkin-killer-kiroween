# Requirements: levels and start screen (levels-ui)
Written 2026-11-15 by Kiro from the owner's brief in chat. I did not read `scripts/agent_levels.py`, `scripts/adaptive_level.py`, `js/adaptive_level.js`, `scripts/adaptive_level_vectors.json`, `docs/ai_levels_sweep_20261115.md` or `index.html` for this spec. Task 1 reads them and corrects this file where they differ. Nothing here was run.

## Facts given by the owner
- `scripts/agent_levels.py` has three computer levels: `easy`, `normal`, `hard`. Measured hit rates (`docs/ai_levels_sweep_20261115.md`): easy 11.2 percent, normal 29.2 percent, hard 52.2 percent.
- `scripts/adaptive_level.py` and `js/adaptive_level.js` share the test vectors in `scripts/adaptive_level_vectors.json`.
- Adaptive level rules: it changes the level for one match only; it starts at `normal`; it looks at the human seat's last 3 throws; it goes up when the hit rate is above 40 percent and down when below 15 percent; at most 2 changes per match; a 2-throw cooldown after a change.
- The current level and the reason of the last change are public and must show in the page HUD.
- Strength and learning are valid for a single match only. Nothing is saved between matches.
- Start screen, owner choice (option 1): remove the grey "in production" cards for the ghost bride, the hunchback and the necromancer, and the two "in production" battlefields. Only playable heroes and the finished battlefield stay. The removed content is mentioned as planned in the README only.

## Requirements
Computer levels
1. When the player starts a match against the computer and picks a level (`easy`, `normal` or `hard`), the system shall play the computer seats at that level for the whole match. (test: "fixed level is used all match")
2. The page shall use the same level parameters as `scripts/agent_levels.py`. A change to one without the other shall fail a check. (check: "level table matches agent_levels.py")
3. If no level is picked, then the system shall use `normal`. (test: "default level is normal")

Adaptive level
4. When the player picks adaptive, the system shall start the match at `normal`. (test: "adaptive starts at normal")
5. While an adaptive match runs, the system shall compute the human seat's hit rate over its last 3 throws and, when fewer than 3 throws exist, shall not change the level. (test: "no change before 3 throws")
6. When the hit rate is above 40 percent, the system shall move the level up one step. When it is below 15 percent, the system shall move the level down one step. At `hard` it shall not go up and at `easy` it shall not go down. (test: "thresholds and bounds")
7. The system shall make at most 2 level changes per match. (test: "at most 2 changes")
8. After a level change, the system shall not change the level again until 2 more throws by the human seat have been made. (test: "2-throw cooldown")
9. `js/adaptive_level.js` shall give the same results as `scripts/adaptive_level.py` on every case in `scripts/adaptive_level_vectors.json`. (test: `node scripts/test_adaptive_level.js` and the Python test, both on the shared vectors; exact file names confirmed in task 1)
10. Only the human seat's throws shall count. The computer seats' throws shall not enter the hit rate. (test: "only human throws count")
11. In a match with more than one human seat, the system shall apply the rule to the seat the owner names in decision 1 below. (check: owner answer, provisional)

HUD
12. While a match against the computer runs, the HUD shall show the current level (`easy`, `normal` or `hard`). (check: recorded browser run)
13. When the adaptive level changes, the HUD shall show the reason of the last change (for example "hit rate above 40 percent over last 3 throws") until the next change or the end of the match. (test: "reason text is set on change"; check: recorded browser run)
14. The level and the reason shall be part of the public state. No hidden value (individual throw history beyond what the reason says) shall be added to it. (test: "public view contains level and reason only")

Single match only
15. When a match ends or a new match starts, the system shall reset the level, the throw history, the change count and the cooldown. (test: "state resets between matches")
16. The system shall not write level, hit-rate or learning data to `localStorage`, cookies, files or any server. (check: grep of the new code and a browser run with storage cleared before and inspected after)

Start screen
17. The start screen shall not show a card for the ghost bride, the hunchback or the necromancer. (check: recorded browser run; test: "start screen lists only playable heroes" if the list is data)
18. The start screen shall not show the two battlefields marked "in production". Only the finished battlefield shall show. (check: recorded browser run)
19. The system shall show every playable hero (those in the page's built list) and nothing else on the hero row, in the existing order. (check: recorded browser run)
20. The removed heroes and battlefields shall be mentioned as planned in `README.md` only, not on the start screen. (check: `README.md` has the lines; the page has no such text)
21. The removal shall not change any playable hero, the finished battlefield or an existing save/load path. (check: the existing test scripts still pass, rerun by the main line)

Records
22. Each task shall end with its test output pasted into its result file, rerun by the main line, and recorded in `docs/kiro_verified.json`. Kiro's own report never counts as verification.

## Out of scope
New heroes or battlefields; changing the measured hit rates or retuning the levels; saving any strength or learning between matches; replacing the ultimates spec (`ultimates-v2`); English labels (W6).

## Open decisions for the owner
1. Multiplayer: which human seat does the adaptive level watch? Options: each human seat separately, the average of all human seats, or only seat 1. Recommended: the average of the human seats, because one level applies to all computer seats. Requirement 11 waits for this.
2. Where the level picker sits on the start screen (new control or existing difficulty control). Recommended: reuse the existing control if there is one; task 1 reports.
