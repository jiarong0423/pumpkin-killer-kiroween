# Dispatch board 2026-11-15 (written 17:30 Taiwan time; freeze 12-02 06:00, deadline 12-05 06:00)
Statuses come from `docs/kiro_verified.json` and commands the dispatcher re-ran (`check_asset_refs.py` missing=7, `test_knight_ult.js` 13 pass, `test_ultimate_fx.js` 10 pass). Kiro result files alone are not proof. Running now: 116, 117, 118. Result files exist but are not yet in `kiro_verified.json`: 111, 114, 115.

## 1. Dispatch order, next 6 hours (a slot is about 60 minutes; start the next when the main line has re-run the last)
| Slot | Lane 1 (CLI, scripts) | Lane 2 (CLI, scripts) | Lane 3 (CLI, the `index.html` lane) | IDE lane | Colab lane |
|---|---|---|---|---|---|
| T0 now | 117 hero fx timelines (running) | 118 balance of eight (running) | 116 hero plan (running, reads `index.html` only) | owner: read the IDE MCP log, restart the IDE (task 124 adds the evidence) | hold |
| T1 | 119 `kiro_task_119_page_ai_level_table.md`: page level table. Needs nothing; unblocks 123, the owner's level request | 122 `kiro_task_122_audio_drop_missing_refs.md`: small, no owner input, takes missing 7 to 4 | 120 `kiro_task_120_wire_knight_ultimate.md`: the only unfinished ultimate of the four playable heroes; needs 116 finished | owner: power check; no `index.html` save while lane 3 writes | hold; main line checks 115's JSON and reference paths |
| T2 | 124 `kiro_task_124_mcp_health_check.md`: proves or kills the "relative path" cause of the empty IDE panel | 121 `kiro_task_121_i18n_inventory.md`: runs on a snapshot of `index.html` taken after 120 is verified | 123 `kiro_task_123_wire_levels_into_page.md`: needs 119 and 120 verified | IDE: spec task `judging-fit` 5 (add one hook) as real IDE evidence | hold |
| T3 | 125+ hero module test follow-ups (briefs written after 116 lands) | 125+ English wording review (docs, Sonnet) | 125+ hero 1 in the page (the hero 116 ranks first; art already in `assets/poses`) | free | hold |
| T4 | MCP allowlist test (plan F2) | spec tick audit | hero 2 in the page | free | hold |
Colab: no new run until the owner says. Gap found in `docs/colab_run_20261115.md` step 14: only `fx_feet_chain` has an ingest mapping, so write a reviewed-mapping brief (126, Kiro CLI, scripts only) BEFORE the run, or the pictures cannot be installed. When released, order: `unit_knight_unarmed`, `fx_feet_chain`, two backgrounds, ghoststar, coins (`colab/jobs_missing_20261115.json`, steps in `docs/colab_run_20261115.md`).

## 2. Open work blocks
| id | status | proof | blocker | next owner | size | writes |
|---|---|---|---|---|---|---|
| B01 IDE evidence | partly | `docs/kiro_evidence/raw/ide_hook_run_20261115.txt` (hook ran), `ide_mcp_attempt_20261115.txt` (MCP call failed) | IDE MCP panel empty | owner, then main line | S | `docs/kiro_evidence/raw/*` |
| B02 Web and Crew | not started | none | needs the new repo (B11) and the GitHub app | owner | S | none local |
| B03 public URL | partly | verified 93: `deploy/`, `smoke_url.py`; docker build not run | owner hold on any URL; owner runs the tunnel | owner | M | `deploy/*` |
| B04 ultimates | partly | verified 99 (bat, skeleton, wizard wired); 100, 108 (knight module, not wired) | knight wiring open; 117 running | Kiro CLI (120) | L | `index.html`, `js/ultimate_fx.js`, `js/knight_ult.js` |
| B05 AI levels | partly | verified 104, 105; `grep -c AdaptiveLevel index.html` = 0 | page AI unchanged | Kiro CLI (119, 123) | L | `js/ai_levels_page.js`, `index.html` |
| B06 opening flow | blocked | `(not published)` is empty | owner concept images; cut-list item | owner | L | `index.html`, new `js/` |
| B07 missing pictures | blocked | `check_asset_refs.py`: 4 pictures; 115 made the job file (its JSON check was refused, not seen) | owner Colab hold | owner, main line verifies 115 | M | `colab/jobs_missing_20261115.json`, `assets/*` |
| B08 missing sounds | not started | 3 `.ogg` listed MISSING | none (recommendation: drop the references) | Kiro CLI (122) | S | `js/audio.js`, `docs/audio_event_map.json` |
| B09 English UI | not started | 151 lines with Chinese in `index.html`; `test_i18n.js` fails | order behind index tasks | Kiro CLI (121, then a wiring task) | L | `assets/i18n/*`, then `index.html` |
| B10 export and gate | partly | verified 85a, 86; 114 code reported OK (not yet re-run by main line); `(not published)` shows 68 BLOCK, all P13 in spec and skill text, though the manifest already transforms those paths | export is probably stale | main line (re-export, gate) | M | `(not published)`, `scripts/release/*` |
| B11 history and private push | not started | `UPLOAD_APPROVAL.md` and `OWNER_ANSWERS.md` do not exist | B10; owner permission to commit | main line, owner | M | git state, `(not published)` |
| B12 write-up | partly | `(not published)` 51 lines (111; its "9 of 10 knight tests fail" is stale) | B01, B10 | Kiro CLI (Sonnet), later | M | `(not published)` |
| B13 README, Devpost text | partly | README draft 119 lines; Devpost text none | URL (B03) | Kiro CLI draft, owner pastes | M | `(not published)` |
| B14 disclosure list | partly | `CREDITS.md` 101 lines (111); pre-10-30 items not checked | none | main line review | S | `(not published)` |
| B15 test gaps | partly | verified 110; `test_i18n.js` still fails | B09 | main line | S | `scripts/release/clean_checkout.sh` |
| B16 video | not started | none | freeze, URL | owner | L | none |
| B17 blog, social post | not started | none | B13 | owner | M | none |
| B18 credits, final form | not started | none | all | owner | S | none |
| B19 4 vs 4 | frozen | none | owner rule | none | L | none |
| B20 local LLM agent | not started | none | B05 | Kiro CLI, later (needs localhost only) | M | `scripts/*` |
| B21 eight heroes | partly | `assets/poses` has bride 8, hunchback 8, necro 5, reaper 4; 116, 117, 118 running; page has 4 heroes | 116 result; one `index.html` writer | Kiro CLI after 116 | L | `index.html`, `js/class_stats.js`, `js/ultimate_fx.js` |
Specs (`.kiro/specs/*/tasks.md`, unticked count): `ultimates-v2` 6 (tasks 2 and 4 are done in code, tick by main line; 5 is B04; 6 is B08), `levels-ui` 6 (B05), `release-package` 32 (ticks stale, B10), `i18n` 3 plus ticks 1 to 7 that the main tree does not match (`assets/i18n` absent), `judging-fit` 8, `audio-generation` 9 (owner steps), `mcp-standard` 2, `physics-pbt` 3 (ticked files absent), `asset-candidates` 3, `shared-constants` 1. Old plans with no work scheduled, cut candidates: `delivery-plan` 65, `gameplay-experience` 29, `dock-design` 21, `wind-design` 13, `fonts` 10, `scene-layers` 10, `sound-design` 6, `particles` 5.

## 3. Conflicts (never run together) and critical path
- `index.html`: 120, 123, every hero task, the English wiring, B06; also any IDE save of that file (it fires the engine-test hook and can overwrite from a stale buffer). One writer at a time. Readers use a snapshot (121) or run read-only (116, 119).
- `js/ultimate_fx.js` and its test: 117 only. `js/class_stats.js`, `scripts/sim_balance.js`: 118 only; hero tasks that change numbers wait for 118 verified.
- `js/audio.js`, `docs/audio_event_map.json`: 122 only. `assets/i18n/*`: 121 only. `shared/constants.json`: one task at a time.
- `docs/kiro_verified.json`, `docs/KIRO_LEDGER.md`: main line only. `(not published)` and the gate logs: main line only; no Kiro task while an export runs.
- Critical path 1 (the long pole): 120, 123, hero 1, 2, 3, 4, English wiring, polish. 6 heroes by 11-27, 8 by 12-01, freeze 12-02 06:00. Lane 3 must never idle: write the next brief before the last one finishes.
- Critical path 2: owner terms file (present) and R0 answers and commit permission, re-export, gate 0, clean checkout, single commit, private push, Public before 12-01, URL smoke, video 12-04, Devpost 12-04 18:00.
- Drift: `(not published)` still says four heroes and a public URL by 11-18; the owner now says no URL tonight and eight heroes.

## 4. Open questions for the owner (recommendation first)
1. Reaper and necromancer both ship (8 heroes)? Yes if the seventh is playable by 11-30; the reaper is cut first.
2. One private smoke deploy of the page by 11-20, even if the link stays unshared? Yes; the rules need a working URL and the first deploy is where surprises are.
3. English as the default page language with a Chinese switch? Yes; start the string layer now (task 121).
4. Drop the three missing sound references, including `item_pickup`? Yes, synth stays; restore after you listen to a licensed file.
5. Skip the opening-flow concept images and keep the current start screen (cut list)? Yes; spend the time on heroes.
6. Write the R0 answers and allow the working-tree commit this week? Yes; it unblocks B10 and B11.
7. May the MCP server get one opt-in transcript flag and a player agent that auto-approves its own tools (plan F3, F5)? Yes; no shell, in-memory state only.
8. Which hero first in the page? Take what 116 ranks first (most art exists: hunchback or necromancer).
