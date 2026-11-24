# Tasks: remaining heroes
Written 2026-11-15. None is done. A task is done only when the main line has rerun its test or check and recorded it in `docs/kiro_verified.json`.

Rules:
- `index.html` changes happen one task at a time. A task that edits `index.html` starts only after the previous `index.html` task (in this spec, `ultimates-v2` or `levels-ui`) is applied and recorded.
- The main line applies every `index.html` change and verifies it in the browser, then records the run. Kiro does not mark such a task done.
- Pure modules with tests (tasks 2 and 3) can be written by Kiro CLI in parallel, before and during the page tasks. They do not touch `index.html`.
- One hero at a time: hunchback (H), then necromancer (R), then bride (B). The card and `ULT_BUILT` come last for each hero.

Before the tasks: the owner answers open questions 1 and 2 in `requirements.md` (the eighth hero; which stats table). Questions 3 to 7 have recommended answers; tasks may proceed on them and the main line records any change.

## Shared
- [ ] 1. Read-only check. Read `index.html` from line 620 to the end (throw, hit, draw, status, `DOCK_PORTRAIT`, `DOCK_GLYPH`, `switchHero`, `applyClassStats`), `scripts/sim_balance.js`, `docs/audio_event_map.json`, `docs/pose_spec.md`, `docs/converge_characters.md`, `docs/ultimate_rules.md`, and list `assets/poses`, `assets/portraits`, `assets/weapons` and `assets/fx/sprites`. Write the findings in `(not published)`: which pose, weapon and effect files exist for each hero, whether `proj_axe` is wired, how bleed and statuses work, what `sim_balance.js` reads, which sound event names exist. Correct `requirements.md` and `design.md` where they differ. Also list the corrections `docs/ultimate_mapping.md` rows 5 to 7 need. (Req 1 to 5, 12, 24)
- [ ] 2. `(not published)` and `(not published)` (Kiro CLI): bleed, burn, knockback, first-unit hit, ultimate targets and strikes, with the test names in `design.md` and a 300-seed determinism check. Test command: `node (not published)`. (Req 5, 8, 9, 10, 16, 17, 21, 22, 26)
- [ ] 3. `js/class_stats.js` and its test (Kiro CLI): one table per hero after open question 2; rename or remove the duplicate reaper/necromancer row after open questions 1 and 7; hunchback weapon `proj_axe`; replace `reaper_combo`. Test command: `node scripts/test_class_stats.js` (it reads `index.html`; the main line reruns it after the page tasks). (Req 1, 13)
- [ ] 4. `index.html`: `READY_HEROES` list and the computer-opponent pick (`startMatch`, initial `aiClass`) read from it; pose table and `poseFor` lookup with fallbacks; `THROW_SOUND` extension point. No new hero is visible after this task. Main line applies and verifies: the four existing heroes still start, play and show their cards, on a recorded run. (Req 2, 3, 4)

## Hero 1: hunchback
- [ ] H1. `index.html`: `HERO_PROFILES.hunchback`, `DOCK_PORTRAIT`, `DOCK_GLYPH`, `HERO_BLURB`, `proj_axe` and `fx_axe_thrown` in `imgList` (only for files that exist). The hero stays out of `READY_HEROES`. Check: page loads, start button opens, the four old heroes play. (Req 6)
- [ ] H2. `index.html`: the eight pose states for the hunchback. Check: `python3 -B scripts/check_pose_set.py --strict` shows hunchback 8/8, and a recorded run shows every state (hunchback chosen through a temporary developer switch, removed afterwards). (Req 7)
- [ ] H3. `index.html`: the heavy axe, bleed, knockback, using `(not published)`; `THROW_SOUND` entry. Check: recorded run with a hit, a miss, a knockback at the fence, bleed ticking at two round starts. (Req 8, 9, 12)
- [ ] H4. `index.html`: the hunchback ultimate (tower toll), timeline in `js/ultimate_fx.js`. Check: recorded run of one full ultimate, damage numbers match `ultimateStrikes`. (Req 10, 25, 26)
- [ ] H5. Balance: `node scripts/sim_balance.js` with the hunchback; paste output; retune in the stats table only. (Req 13)
- [ ] H6. `index.html`: add the hunchback to `READY_HEROES` and `ULT_BUILT`, remove his card from `COMING_HEROES`, final blurb. Check: recorded run from the start screen through a full match against each opponent class. (Req 2, 11, 25)

## Hero 2: necromancer (id `reaper`)
- [ ] R1 to R6: the same steps as H1 to H6 for `reaper`: profile with `proj_soulflame` and the purple art (R1); poses including the legacy `necro_*` files (R2, check `check_pose_set.py` reaper 8/8); purple-flame push and burn (R3, requirement 16); three-fire ultimate (R4, requirement 17); balance (R5); card, `READY_HEROES`, `ULT_BUILT`, removal from `COMING_HEROES` (R6). (Req 14 to 18, 25, 26)

## Hero 3: ghost bride
- [ ] B1 to B6: the same steps for `bride`: profile with `sound_wave` (B1); poses (B2); the ring that hits one unit, visual rings, new blurb text replacing "everything on the flight path is hurt" (B3, requirements 21 and 23); piercing ultimate (B4, requirement 22); balance (B5); card, `READY_HEROES`, `ULT_BUILT` (B6). (Req 19 to 24, 25, 26)

## Closing
- [ ] 5. Main-line rerun of `node (not published)`, `node scripts/test_class_stats.js`, `node scripts/test_ultimate_fx.js`, `python3 -B scripts/check_pose_set.py --strict` and `node scripts/sim_balance.js`; record in `docs/kiro_verified.json`. Update `docs/ultimate_mapping.md` rows 5 to 7 and the README's planned list. (Req 27)

Order: 1 first. 2 and 3 in parallel with 4 (they do not touch `index.html`). Then H1 to H6, R1 to R6, B1 to B6, each `index.html` task only after the previous one is recorded. Then 5. The `index.html` tasks also queue behind `ultimates-v2` tasks 3 and 5 and `levels-ui` tasks 3 to 5 while those are open.

Art needed from the owner: none for the tasks above if the files named in `requirements.md` exist (task 1 checks). A missing weapon picture (`proj_axe`, `fx_axe_thrown`, a flame sprite) blocks the page task that needs it; the code falls back to a drawn shape or glyph and says so in the result file.
