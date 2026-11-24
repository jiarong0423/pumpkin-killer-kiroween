# Wave 3: front-end match matrix (page code), 2026-11-17

New files only: `scripts/page_match_driver.js`, `scripts/run_page_matrix_vm.js`, `scripts/run_page_matrix_cdp.mjs`, `scripts/test_page_match_driver.js`, this report, and the output `(not published)`. `index.html` untouched; no network, no commit.

## What runs
- Driver `runPageMatch({hero,size,seed})`: one self-contained function (string `source` + CommonJS export, no Node call inside) that plays a whole match in a loaded page: both seats `ai` with the spec tiers, left hero for all units, right hero `(seed*7+3)%8`, positions/wind/weather/coin from the match seed, the page's own `updatePhysics(1/60)` and AI turns, FAKE clock (page `setTimeout`, `performance.now`, `Date.now` replaced, restored afterwards), seeded `Math.random`. Counters by wrapping page functions (`executeThrow`, `pushHitReport`, `cbBegin`, `cbNearMiss`); `direct_hits` = throws with a direct hit (a bounce or pierce counts once), `pity_triggers` = projectiles that used a charge > 0, `comeback_hits` = projectiles whose capped underdog x pity multiplier > 1, `near_misses` = near misses that took hp (0 at size 1). Result record exactly as the spec.
- Vm runner: 240 matches, 142 s, 0 errors, 0 without winner, 1 cap end (2v2 bride). Test `scripts/test_page_match_driver.js`: 16 ok (duel, 2v2, 3v3 end with a winner, counters sane, tiers/right hero follow the spec rule, same seed twice identical record, page restored, 3 negatives). `test_page_team_exec` 88, `test_page_wave2a` 14, `test_team_rules` 10 still green.

## vm table (rounds mean / left win share)
size 1: 9.1 / 26 %   size 2: 12.7 / 35 %   size 3: 17.0 / 40 %   (all: left wins 33.8 %). Per hero (1v1, 2v2, 3v3): skeleton 10.0/13.5/17.2 (40,40,60 %), wizard 7.2/9.5/13.6, bat 10.4/10.8/15.7, knight 10.6/15.7/19.4, bride 9.0/12.2/17.0, hunchback 9.1/14.5/18.0, reaper 8.1/11.7/16.9, hag 8.6/13.5/17.9 (hag duel 10 % left). Full table: `node scripts/run_page_matrix_vm.js` prints it. Team matches: comeback hits 6.9 to 18.1 and pity 2.9 to 6.0 per match, near misses 5.0 per match.
## plainOnly (new default, like the engine bot) - old vs new table
`runPageMatch` option `plainOnly` (default true; `--rich` in both runners restores the full page AI): `queueAiThrow` forced to `useUltimate = false`, heavy/double/heal charges 0, `tryAiDefend` returns false, `scheduleAirdrop` no-op (no items). Kept and counted: the right AI's own dice move (25 % of its turns, measured 0.25; the engine bot moves 35 %; the left AI never moves) in `record.options.moves_right/moves_left`. `options` is in each record and in the file header; a plainOnly record with an ultimate or an item gets an error (none occurred).
Rounds mean / left win share, 240 matches each (rich = old page AI, re-run on the current page: identical to the first run):
| size | rich (old) | plainOnly (new) | engine (from coordinator) |
|---|---|---|---|
| 1v1 | 9.1 / 26 % | 9.2 / 44 % | left win 42 % |
| 2v2 | 12.7 / 35 % | 12.3 / 45 % | 61 % |
| 3v3 | 17.0 / 40 % | 17.5 / 44 % | 58 % |
plainOnly: ultimates 0 on both sides in all 240, 0 errors, 0 caps, 0 without winner, run 113 s (`(not published)`; rich in `(not published)`). Per hero (left win share 1v1/2v2/3v3): skeleton 60/60/70, wizard 50/50/80, bat 60/50/60, knight 70/60/40, bride 20/30/30, hunchback 20/10/10, reaper 40/60/50, hag 30/40/10; rounds per hero are in the vm runner table. Remaining asymmetry: the right AI moves, the left AI does not.
Main-line fix `beginOpeningTurn` normalisation: `node scripts/test_page_match_driver.js` 17 ok, `test_page_team_exec` 88, `test_page_wave2a` 14, `test_team_rules` 10: nothing broke (the driver's own 0/1 mapping gives the same side).

## Findings that shape the numbers (page behaviour, not fixed by me)
1. The left AI seat (`triggerLeftAiTurn`) never uses ultimates, moves, skills or the knight shield (ultimates_left = 0 in all 240; right AI 1.29 per match): the left side is structurally weaker, so left win share is low whatever the tier (right tier hard beats left 85 %, easy 47 %). The back end must model the same asymmetry to compare, or the page needs a left AI with the same turn code.
2. (fixed on the page by the main line since) `showCoinToss(firstSide)` passed the NUMBER 0/1 to `beginOpeningTurn(side)`, which tests `side === "right"` and `seats[side]`: right-first never happens and `firstOpener` is always "player" in the shipped flow (index.html lines about 1172 to 1185, 1195 to 1203). The driver maps 0 to "left" and 1 to "right" itself (intended behaviour). Fix on the page: pass `"left"`/`"right"`.
3. Duel start positions come from `randomizePositions` (seeded) like a reset game, not the fixed 340/1560 default.

## Commands for the owner (terminal on the Mac, repository root; plain throws is the default, add `--rich` for the full page AI)
- Desktop Chrome: `node scripts/run_page_matrix_cdp.mjs --desktop` -> `(not published)` (needs Chrome or `CHROME_PATH`; starts its own dev server).
- Phone (dev server on 8080 and `adb reverse tcp:8080 tcp:8080` already set): `adb -s <phone-ip>:5555 forward tcp:9333 localabstract:chrome_devtools_remote` then `node scripts/run_page_matrix_cdp.mjs --phone` (default port 9333, option `--port`; reuses the tab on `http://localhost:8080/`, else `/json/new`) -> `(not published)`. Keep the phone screen on. Slow phone: `--per-cell 3` first, `--resume` continues after a drop, `--hero knight --size 3` for one cell.
- In-app browser pane without sockets: open `http://localhost:8080/index.html?team=2` in the pane, then `node scripts/run_page_matrix_cdp.mjs --print-snippet --size 2 --hero wizard --seeds 2` and paste the printed text into the pane's javascript tool (returns a JSON array of records; one size per page load, validated here by running it in the vm).
## Not done
The three CDP paths were NOT run (sockets blocked here): `node --check` passes and the connection-failure path exits 1 cleanly, but the Chrome launch, the phone tab handling and per-match navigation are untested. Real-Chrome speed and any differences from the vm (real DOM, real fx systems) are unmeasured. No engine comparison made (back end is the other engineer's).
