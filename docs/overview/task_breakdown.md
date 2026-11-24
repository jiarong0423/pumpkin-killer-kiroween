# Task breakdown (Kiro task 77, 2026-11-10)

Documentation only. Nothing here was run, rendered or tested. Module = node id in `architecture.mmd` / `pumpkin_killer_architecture.svg`.
Built on `docs/owner_decisions_20261110_agents_headless.md` (own sub-agent per player, headless rules, modular, seats = agent / human / builtin-ai, public view only).

## How to read it

- Owner role: SONNET-flow, TERRA-art, COLAB, IMAGE2, MAIN-integrate, OWNER-decides. SONNET-flow code work happens in a `kiro/<name>` branch and MAIN re-runs it (ROLES.md).
- **[T73] [T74] [T75] [T76]** in "depends on" = needs the output of that Kiro task, which is **not finished yet**. This table only references those outputs, it does not guess their contents. The `(not published)` result files were not present when this was written.
- `*` = edits `index.html` (or the renderer after R04). Rule: at most one `*` task per wave (ROLES.md lock: one writer per file).
- Size: S under half a day, M about a day, L several days.
- "Done-when" is a check MAIN can run. Commands that already exist are named. "New test" means the test file does not exist yet and is created by the task.
- Names of new modules are placeholders until task 76 fixes them.

## Table

| id | task | module | owner role | depends on | size | done-when |
|---|---|---|---|---|---|---|
| R01 | Read the results of tasks 73 to 76, reconcile with this table, fix wrong rows | all | MAIN-integrate | **[T73] [T74] [T75] [T76]** | S | The four result files exist under `docs/` and every row below that cites a task section has been checked against it |
| R02 | Owner answers the open decisions: ghost carries the airdrop crate (B1), start ultimates (B2), wind drift engine vs page (`tech.md`), terrain and others that T74 to T76 list | G_OWNER | OWNER-decides | R01 | S | Answers appended to `(not published)` |
| R03 | Extract the rules into a module with no DOM (state, turn order, damage, wind step), boundaries as in task 76 | S_RULES | MAIN-integrate | R01, **[T76]** | L | New test runs the module under `node` with no browser and reproduces one fixed-seed match twice with identical output |
| R04 | Make `index.html` call the rules module and keep only input and drawing (no behaviour change) * | S_RULES, B_CORE | MAIN-integrate | R03 | L | `python3 -B scripts/test_constants_sync.py`, `node scripts/test_class_stats.js`, `node scripts/test_ultimate.js` still pass; same-seed replay gives the same final HP as before the change |
| R05 | 4v4 step 1: `units` array with aliases `player = units.red[0]`, `ai = units.white[0]` * | S_UNITS | MAIN-integrate | R04, **[T76]** | M | Game plays 1v1 exactly as before: rules-module replay test equal, plus one manual match |
| R06 | 4v4 step 2: active-unit pointer, team-order turn flow, dice for first team, 12 s timer per unit | S_ACTIVE | MAIN-integrate | R05, **[T76]** | L | New test: 4v4 turn sequence matches the order given in the T76 plan; forfeited turn on timeout |
| R07 | 4v4 step 3: loop over all units for projectile collision, statuses, draw order and depth sorting * | S_UNITS, B_CORE | MAIN-integrate | R06, **[T76]** | L | Rules test with 8 units: every projectile resolves; no unit left out of the status tick; browser check of draw order |
| R08 | Minimum spacing, push-apart and movement limits next to the fence | S_UNITS | MAIN-integrate | R07, **[T76]** | M | New test: random moves never leave two units closer than the T76 minimum; moves still stay in the allowed zones |
| R09 | Overlap damage: hitbox per unit, order of hits for one projectile, crit, shield, status and chain bonus per unit, friendly fire off | S_COLL | MAIN-integrate | R07, **[T76 section 9]** | M | New test reproduces the T76 worked example (3 units in a line) number for number |
| R10 | Splash range: radius per area attack, falloff, wall effect, ring size equal to the radius | S_COLL | MAIN-integrate | R09, **[T76 section 10]** | M | New test reproduces the T76 example (4 enemies at 60, 140, 220, 300 px); drawn ring radius equals the rule radius |
| R11 | Particle budget for 8 units: presets reused or added, per-frame cap, shrink rules * | S_BUDGET, B_PART | MAIN-integrate | R07, **[T76 section 11]** | M | `node scripts/test_particles.js` passes; frame-time measurement with 8 units stays under the limit T76 states |
| R12 | 4-unit HUD and dock: active unit highlight, small HP bars, no health numbers, click to select * | S_HUD4, B_HUD | MAIN-integrate | R07, **[T76 section 4]** | L | Overlap check of canvas and DOM rectangles shows no overlap at two window widths (new test); manual click-to-select pass |
| R13 | Built-in AI for several units: which unit acts, public-view aiming | S_AI4, B_AI | MAIN-integrate | R07, R15, **[T76 section 5]** | M | Extended `node scripts/sim_ai_nosim.js` finishes N matches and reports the hit rate; no hidden field is read |
| R14 | Controller per unit: agent, human, builtin-ai (hot-seat out of scope) | S_SEATS | MAIN-integrate | R06, **[T76 section 2]** | M | New test: an action from the wrong seat is refused; each controller type completes a turn |
| R15 | Per-seat public view builder | S_PUBVIEW | MAIN-integrate | R14, **[T75]** | M | New test: the output of the builder never contains exact wind noise, hidden shield points A-B-C or the AI aiming state |
| R16 | MCP server serves the seat-scoped public view and seat-checked actions | T_MCPSTD, T_MCPENG | SONNET-flow | R15, **[T75]** | L | `python3 -B scripts/test_mcp_stdio.py` passes plus new cases for seat scoping |
| R17 | MCP opponent mode end to end: a sub-agent plays a match against a human seat | G_MCPOPP | MAIN-integrate | R14, R16, **[T75]** | L | Scripted match through the MCP tools reaches a result; `python3 scripts/eval_agent_learning.py` runs against it |
| R18 | Fairness and safety checks for MCP: hidden fields, rate limit, localhost only, writes only to a scratch folder, no secrets | T_MCPSTD, X_NEW | SONNET-flow | R16, **[T75 section 3]** | M | New tests for each rule in T75 section 3 pass; `grep` of the server for network binds shows localhost only |
| R19 | Extra MCP tools that T75 marks as worth building before the deadline (status, replay, inventory, hit-rate run) | T_MCPSTD, D_AINV | SONNET-flow | R16, R02, **[T75 section 2]** | M | Each chosen tool listed by `tools/list` and covered by a test in `test_mcp_stdio.py` |
| R20 | Wind ghost 8-frame blowing loop: five Colab frames, review, then 8-cell sheet if needed | A_GHOST, A_COLAB | COLAB | none (running) | M | Frames present in the Colab output folder; `python3 scripts/ingest_wind_sheets.py` and `python3 scripts/check_continuity.py` accept them; MAIN looks at the result |
| R21 | Feet-chain picture for the slow status (`colab/jobs_chain_20261110.json`) | A_CHAIN, A_COLAB | COLAB | R20 (same GPU queue) | S | Keyed PNG exists with no edge contact; MAIN looks at the result |
| R22 | Wire the new ghost loop (replace the 4 named frames) and show the chain on slowed units * | B_WGHOST, B_STAT | MAIN-integrate | R20, R21 | M | `node scripts/test_wind_fx.js` passes; screenshot reviewed by MAIN |
| R23 | Blue twin of the purple coffin; remove the hue-rotate stopgap | A_COFFIN | COLAB | **[T73]** | S | PNG installed; same size and viewpoint as `assets/env/platform_coffin_purple.png`; MAIN looks at the result |
| R24 | Fence damaged and broken art that reads differently from intact at game size | A_FENCE | IMAGE2 | **[T73]** | M | Three fence states are visibly different in a screenshot at game size; no black slab |
| R25 | Front portraits (the list of missing ones differs between `asset_inventory.json` and task 73: check the folder first) | A_PORT | IMAGE2 | **[T73]** | M | `ls assets/portraits` shows every class; face matches the class idle picture |
| R26 | Redo pose pictures (39 listed, face lock) | A_POSE39 | IMAGE2 | **[T73]** | L | `python3 scripts/check_pose_set.py` and `python3 scripts/check_continuity.py` pass per class |
| R27 | New battlefields: bell tower and pumpkin field backgrounds | A_BG | COLAB | **[T73]**, Colab 16:9 check | M | `assets/env/bg_belltower.png` and `bg_pumpkin_field.png` exist; 16:9; ground line matches `GROUND_Y` |
| R28 | `unit_knight_unarmed.png` and the missing pose frames T73 lists | A_KEY, A_ASSETS | COLAB | **[T73]** | S | File exists at the same size as `unit_knight.png`; thrown shield leaves an empty hand in the page |
| R29 | Install all arrived art, update the inventory * | A_ASSETS, D_AINV | MAIN-integrate | R23 to R28 (whatever has arrived) | M | `python3 scripts/make_asset_inventory.py` regenerates `docs/asset_inventory.json` with the six open_art items updated |
| R30 | Make the bride playable (checklist and stat table from T74) * | B_CNEW, D_CSTAT | MAIN-integrate | R25, R26, R29, **[T74]** | L | `node scripts/test_class_stats.js` passes; bride selectable and finishes a match; her pose set passes `check_pose_set.py` |
| R31 | Make the hunchback playable * | B_CNEW | MAIN-integrate | R26, R29, **[T74]** | M | Same checks as R30 for the hunchback |
| R32 | Make the necromancer (reaper) playable * | B_CNEW | MAIN-integrate | R26, R29, **[T74]** | M | Same checks as R30 for the necromancer |
| R33 | Knight ultimate: defend mode with hidden points A-B-C * | B_ULT, B_SHLD | MAIN-integrate | R02, R07, **[T74]** | L | `node scripts/test_ultimate.js` extended and passing; the points never appear in the public view (R15 test) |
| R34 | Ultimates for bride, hunchback, necromancer * | B_ULT | MAIN-integrate | R30, R31, R32, R33, **[T74]** | L | `node scripts/test_ultimate.js` passes for all seven classes; numbers marked provisional |
| R35 | Status effects verified per unit in 4v4 (stacking, clears, shield and ultimate interaction from T74) | B_STAT | MAIN-integrate | R07, **[T74 section 3]** | M | New test table: one case per row of the T74 status table |
| R36 | Sound gaps: `move_step`, `item_pickup`, `ultimate_ready_chime`, status and ultimate sounds, synthesised or CC0 as T74 decides | B_AUD, D_AMAP | MAIN-integrate | **[T74 section 5]** | M | `node scripts/test_audio.js` and `node scripts/test_ambient_sfx.js` pass; `assets/audio/CREDITS.md` lists any new file |
| R37 | Owner listens to a match and reports volume balance (D3) | B_AUD | OWNER-decides | R36 | S | Owner's reply logged in `(not published)` |
| R38 | Balance pass: 200 automatic matches after 4v4 and the new classes, no across-the-board nerfs | D_CSTAT, X_BAL | MAIN-integrate | R13, R30, R31, R32, R34 | M | `node scripts/sim_balance.js` report inside the bands in `js/class_stats.js`; `node scripts/test_sim_balance.js` passes |
| R39 | Re-measure the AI hit rate on the real page after the wind rule (target 25 to 30 percent) | B_AI | MAIN-integrate | R13 | M | 300 AI throws logged; rate reported with the count |
| R40 | Browser smoke test and frame-time check (no browser test exists today) | X_NEW | MAIN-integrate | R03, R11, R12 | M | New script loads the page, plays a scripted match, fails on any console error, reports frame time for 8 units |

## Waves (at most 3 tasks at the same time; 16 GB machine, 6 terminal tabs)

Within a wave the tasks can run in parallel. A wave starts when the previous one has passed its done-when checks. At most one `*` task per wave. COLAB runs one GPU job at a time.

| wave | tasks | notes |
|---|---|---|
| W1 | R01, R20 | R01 starts when the four result files exist. R20 can start now. |
| W2 | R02, R03, R21 | |
| W3 | R04 *, R23, R24 | R24 needs the owner to paste into image2. |
| W4 | R05 *, R25, R27 | R25 needs the owner. |
| W5 | R06, R26, R28 | R26 needs the owner and is the longest art task. |
| W6 | R07 *, R14 | |
| W7 | R08, R09, R15 | |
| W8 | R10, R12 *, R16 | |
| W9 | R11 *, R13, R17 | |
| W10 | R18, R19, R29 * | R29 installs whatever art has arrived. Late art goes into a repeat of R29. |
| W11 | R22 *, R35, R40 | |
| W12 | R30 *, R36 | |
| W13 | R31 *, R37, R39 | |
| W14 | R32 * | |
| W15 | R33 * | |
| W16 | R34 * | |
| W17 | R38 | |

## Rows that wait on unfinished tasks 73 to 76

- [T73] (Terra art pack): R23, R24, R25, R26, R27, R28.
- [T74] (Sonnet flow and systems): R30, R31, R32, R33, R34, R35, R36.
- [T75] (Sonnet MCP plan): R15, R16, R17, R18, R19.
- [T76] (Sonnet 4v4 plan): R03, R05 to R15.
- R01 waits on all four. Rows with no tag (R02, R20, R21, R22, R29, R37, R38, R39, R40) can start from what is already in the repo, apart from their listed row dependencies.

## Points to check when the results arrive

- The portrait list differs: `docs/asset_inventory.json` names bride, hunchback and necromancer; task 73 names bat and necromancer. `assets/portraits/` currently holds bride, hunchback, knight, reaper, skeleton and wizard front pictures (READ from the directory listing), so a bat portrait is missing. Resolve in R25.
- `ROLES.md` says Kiro implements code modules, while the 2026-11-10 briefs make the main line build 4v4. This table follows the briefs: MAIN-integrate for 4v4, SONNET-flow for MCP server code.
- The wind difference between page and engine (`tech.md`, "Known drift") is not fixed here. It is listed in R02 for the owner, and it matters for a shared headless rules module (R03).
