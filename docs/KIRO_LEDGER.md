# Kiro ledger (generated 2026-11-16 04:27 by scripts/make_kiro_ledger.py)

One row per task brief in docs/. 'main' = the result file is inside this project; 'worktree only' = it exists only in a ../pumpkin-killer_kiroNN folder and is NOT merged.
The last column comes from docs/kiro_verified.json, which only the main line edits after re-running a check itself. Route status comes from the kiro_route logs (they may be missing for old tasks).

| id | task | model | route status | results | unmerged | main-line verification |
|---|---|---|---|---|---|---|
| 1 | shared game constants (small, to measure credit cost) | - | no log | - | - | not checked by the main line |
| 3 | object detail inventory (read the mockup, read the game mode, write the inventory) | - | no log | - | - | not checked by the main line |
| 6 | particle effects module (pure, testable) | - | no log | - | - | not checked by the main line |
| 7 | standard MCP server and "sub-agents learn to counter" (adversarial) interface | - | no log | - | - | not checked by the main line |
| 8 | bilingual (zh-TW / en) mapping for the whole game UI | - | no log | - | - | not checked by the main line |
| 12 | playtest review (look at the frames, give opinions, record them) | - | no log | - | - | not checked by the main line |
| 13 | make the game deeper (design proposal, documents only) | - | no log | - | - | not checked by the main line |
| 15 | asset candidate sheet (read and write files only, no images, no downloads) | - | no log | - | - | not checked by the main line |
| 17 | gameplay experience + particle effects design (read and write files only) | - | no log | - | - | not checked by the main line |
| 18 | fix the judging gaps (files and docs only) | - | no log | - | - | not checked by the main line |
| 19 | design the bottom dock (items / skills / hero bar) - design files only | - | no log | - | - | not checked by the main line |
| 20 | sound design: music and effect sounds (design + one JS module + its tests) | - | no log | - | - | not checked by the main line |
| 22 | verify CC0 sound sources on the web (web allowed, files only, NO downloads) | - | no log | - | - | not checked by the main line |
| 23 | can Colab generate the sounds? options, licenses, prompts, a Colab job (web allowed, files | - | no log | - | - | not checked by the main line |
| 24 | find copyright-free Halloween / magical music (web allowed, files only, NO downloads) | - | no log | - | - | not checked by the main line |
| 25 | design the wind: how strong, and how the scene reacts (design + one JS module + tests) | - | no log | - | - | not checked by the main line |
| 26 | write the object prompts for the Colab art (files only) | - | no log | - | - | not checked by the main line |
| 30 | sound mapping table: which sound goes to which game event (design only) | - | no log | - | - | not checked by the main line |
| 31 | design the ghost airdrop (supply drop) system: rules, items, balance (design only) | - | no log | - | - | not checked by the main line |
| 32 | full UI re-skin plan: every object, the fonts, the wind indicator (design only) | - | no log | - | - | not checked by the main line |
| 33 | roster of at least 6 classes, 4 vs 4 on the field, clearly different attacks (design only) | - | no log | - | - | not checked by the main line |
| 34 | make the game richer: a content-richness plan (design only) | - | no log | - | - | not checked by the main line |
| 35 | ultimates, area attacks and showpiece effects (design only) | - | no log | - | - | not checked by the main line |
| 36 | REVIEW and reconcile the converged character / scene / design documents (review only) | - | no log | - | - | not checked by the main line |
| 37 | review the playtest data and give concrete FIXES and weapon-effect improvements (review +  | - | no log | - | - | not checked by the main line |
| 38 | multi-party ARBITRATION of the current game balance (spawn sub-agents) | - | no log | - | - | not checked by the main line |
| 39 | design WHEN an ultimate may be used, and the ultimate MAPPING table ("link-up" table) | - | no log | - | - | not checked by the main line |
| 40 | (A) judge the per-class HP and strength, (B) write the Colab art prompts, weapon and ultim | - | no log | - | - | not checked by the main line |
| 41 | redraw the ARCHITECTURE diagram and the WORKFLOW diagram from the real repo (diagrams as t | - | no log | - | - | not checked by the main line |
| 42 | IMPLEMENT four modules from the specs and plans (spec-driven; the main line wires and veri | - | no log | - | - | not checked by the main line |
| 44 | recompute the class stats table (7 classes) with the hunchback's GIANT AXE (knockback allo | - | no log | - | - | not checked by the main line |
| 45 | build a headless 4 v 4 ARENA (engine + command-line interface) so sub-agents can play real | - | no log | - | - | not checked by the main line |
| 46 | connect the MCP / public-information opponent to the game, and an optimisation design (imp | - | no log | - | - | not checked by the main line |
| 47 | TERRAIN: a floor with pits (凹洞) or slopes (斜坡), set by the owner (design + a pure module + | - | no log | - | - | not checked by the main line |
| 48 | FONTS: you are responsible for the font integration (scripts, CSS, tests, license files);  | - | no log | - | - | verified: build_fonts.py rebuilt 2026-11-11 (added U+30FB, U+8F09); test_fonts 36 OK; backup (not published) |
| 49 | raise the VISUAL QUALITY of the screen and SPLIT the assets into layers (design + a small  | - | no log | - | - | not checked by the main line |
| 50 | RESEARCH the bell-tower scene: Gothic cathedral + bell tower, medieval style (references a | - | no log | - | - | not checked by the main line |
| 51 | analyse the human-vs-AI matches and recommend AI / balance adjustments | - | no log | main: kiro_51_recommendations.md | - | not checked by the main line |
| 52 | sky target that heals the hitter's whole side | - | no log | main: kiro_52_recommendations.md | - | not checked by the main line |
| 53 | the reaper as the fire thrower | - | no log | main: kiro_53_recommendations.md | - | partly: copied into main; recommendations not applied |
| 54 | the knight's ultimate is the defend-mode A-B-C shield | - | no log | - | worktree only: kiro_54_recommendations.md | not checked by the main line |
| 55 | retune the strength of every class (owner: opponents die in two or three hits) | - | no log | - | worktree only: kiro_55_recommendations.md | not checked by the main line |
| 56 | re-check the strength retune against the NEW measured data | claude-sonnet-5.5 | ok | - | worktree only: kiro_56_recommendations.md | not checked by the main line |
| 57 | layered wind: strength and altitude | claude-sonnet-5.5 | ok | - | worktree only: kiro_57_recommendations.md | not checked by the main line |
| 58 | review the current game's details and controls (a player's view) | claude-sonnet-5.5 | ok | main: kiro_58_recommendations.md | - | partly: P0/P1 fixes re-run with synthetic events and merged; other patches (C3 exit, touch 44 px, HUD fonts, power meter, help text, reset confirm) NOT merged |
| 59 | the start screen: big character pictures, very short text (implement as an isolated module | claude-sonnet-5.5 | ok | - | - | not checked by the main line |
| 60 | the remaining controls fixes from task 58 (write the patch spec, implement what is isolate | claude-sonnet-5.5 | ok | - | worktree only: kiro_60_patches.md | not checked by the main line |
| 62 | write the image-edit prompts for the art redo (you are one of TWO independent authors) | claude-sonnet-5.5 | no result line | - | - | not checked by the main line |
| 63 | write prompts for OpenAI's image model (image2) that the owner will paste by hand | gpt-5.6-terra | ok | - | worktree only: kiro_63_image2_prompts.md | not checked by the main line |
| 64 | the scripts that take the owner's image2 sprite sheets and turn them into game-ready, chec | gpt-5.6-terra | ok | - | - | verified: scripts copied into main; python3 -B scripts/test_ingest_sheets.py OK (re-run 2026-11-10) |
| 65 | can you read pictures? (a test with known answers) | gpt-5.6-terra | failed | - | worktree only: kiro_65_image_read_gpt-5.6-terra.json | not checked by the main line |
| 67 | the continuity module: smooth, connected character animation (write it as an isolated, tes | gpt-5.6-terra | ok | - | - | partly: (not published) test passes in ../pumpkin-killer_kiro67; NOT merged or wired |
| 68 | the whole game's style: what would YOU change? | gpt-5.6-terra | ok | - | worktree only: kiro_68_opinion.md | not checked by the main line |
| 69 | art-design optimisation: close the gap between the concept and the game | gpt-5.6-terra | ok | main: kiro_69_art_optimization.md | - | not checked by the main line |
| 70 | one-time review of the placed concept pieces (read-only, Terra) | gpt-5.6-terra | ok | main: kiro_70_review_gpt-5.6-terra.md | - | read_only: screenshot review read; its fixes partly applied (HP number removed later by the owner) |
| 71 | wind pictures ingest script (Terra writes it; main line re-runs every test itself) | gpt-5.6-terra | ok | main: kiro_71_result_gpt-5.6-terra.md | - | verified: test_ingest_wind_sheets OK (rerun by main line 2026-11-11) |
| 72 | one overview diagram as SVG (documentation, NOT game art) | claude-sonnet-5.5 | no result line | - | - | not checked by the main line |
| 73 | art gap design pack (Terra = art design; main line verifies everything) | gpt-5.6-terra | ok | main: kiro_73_art_pack_gpt-5.6-terra.md | - | read_only: art pack read; reduced list applied by the main line; no prompt run yet |
| 74 | game flow and system planning (Sonnet = flow and systems; main line verifies everything) | claude-sonnet-5.5 | ok | main: kiro_74_flow_plan_claude-sonnet-5.5.md | - | verified: 6 spot checks re-run in code, all true; owner corrections applied in the text |
| 75 | MCP planning (Sonnet = systems; main line verifies everything) | claude-sonnet-5.5 | ok | main: kiro_75_mcp_plan_claude-sonnet-5.5.md | - | verified: 9 spot checks re-run, all true; plan not applied |
| 76 | 4v4 implementation plan (Sonnet = systems; the MAIN LINE implements it, so the plan must b | claude-sonnet-5.5 | ok | main: kiro_76_4v4_plan_claude-sonnet-5.5.md | - | partly: sections 1,2,3,9,10,12 read; cites spot-checked; OWNER CORRECTIONS and KIRO 76 ANSWERS blocks added; nothing built |
| 77 | architecture diagram first, then the task split (Sonnet = systems; main line assigns from  | claude-sonnet-5.5 | ok | - | - | partly: table read; corrected by docs/overview/task_breakdown_update_20261110.md; diagram not redrawn |
| 78 | automatic daily log and progress table, written by sub-agents (Sonnet = flow/systems) | claude-sonnet-5.5 | ok | main: kiro_78_result_claude-sonnet-5.5.md | - | partly: test_daily_log OK; daily-logger.json now exists; docs/daily + PROGRESS_TABLE exist (Kiro 83 claim 'missing' is stale) |
| 79 | make the Colab (Qwen-Image-Edit) model understand the game's art style (Terra = art design | gpt-5.6-terra | ok | main: kiro_79_style_for_colab_gpt-5.6-terra.md | - | read_only: diagnosis matches the main line finding; calibration batch not run |
| 80 | align the Python MCP engine with the page on wall damage and unit positions (Sonnet, MCP o | claude-sonnet-5.5 | ok | main: kiro_80_result_claude-sonnet-5.5.md | - | verified: test_mcp_game, test_mcp_stdio, test_constants_sync all pass (rerun 2026-11-11) |
| 81 | Kiro task 81 (queue step K1) — wire the start screen and name module into the page (Terra  | - | no log | - | - | not checked by the main line |
| 82 | three open-source image/video models, one fair test (Terra writes the Colab cells and the  | gpt-5.6-terra | ok | - | - | partly: test_score_ghost_tests OK; Colab cells B/C never run |
| 83 | wrap-up and EVIDENCE of Kiro's work (Sonnet; the main line re-checks every item itself) | claude-sonnet-5.5 | failed | - | - | partly: evidence file read; counts rerun: logs 14 (not 13), briefs 71 (not 68), kiro_queue/docs/daily/daily-logger now exist (stale), (not published), assets/i18n, task72 outputs still missing; worktrees 67, kiro/* branches 66, origin/main ea39931 confirmed; class_stats wired only 3 refs, scene_layers/i18n not wired |
| 84 | design draft for the FRESH public GitHub repository (Sonnet; plan only, the main line veri | claude-sonnet-5.5 | ok | main: kiro_84_release_plan_claude-sonnet-5.5.md | - | not checked by the main line |
| 85 | build the final-commit step and the Kiro attribution (Terra writes the script and the comm | - | no log | main: kiro_85_R1_result_gpt-5.6-terra.md, kiro_85_R2_result_gpt-5.6-terra.md, kiro_85_R4_result_claude-sonnet-5.5.md, kiro_85_R5_result_gpt-5.6-terra.md | - | not checked by the main line |
