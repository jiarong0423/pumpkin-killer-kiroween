# What Kiro did and what it changed (inventory by the main line, 2026-11-10)

Method: `git log` (199 commits; 69 mention Kiro in the message, 35 percent; this counts MENTIONS, the author field is the same account for everything), file sizes (`wc -l`), which scripts index.html really loads (`grep "<script src"`), the ledger (docs/KIRO_LEDGER.md, 68 task briefs) and the main line's own re-checks (docs/kiro_verified.json). Impact = what a player or the project can see. A row says LOADED only if index.html loads it.

## 1. Code Kiro wrote that the game page loads (visible to a player)
| area | files (lines) | origin | impact on the game | check |
|---|---|---|---|---|
| Particle effects | js/particles.js 980, js/particles_draw.js 191 | Kiro CLI task 06, commit c8f18c1 ("12 presets and seeded property tests") | every hit, spray, heal rain, ghost-fire, status effect in the game | LOADED; `node scripts/test_particles.js` passes (300 seeded cases per property) |
| Sound module | js/audio.js 1,878, js/ambient_sfx.js 418 | Kiro CLI task 20, commit c409781 (1,145 lines first version), later extended | all music, effects, ambience and the synthesised fallbacks (59 mentions of synth) | LOADED; `node scripts/test_audio.js`, `test_ambient_sfx.js` pass |
| Wind visuals | js/wind_fx.js 374 | Kiro wind design, commit 7dcfc9c | scene wind effects (leaves, dust, fog); the wind strength factor 72 | LOADED; `node scripts/test_wind_fx.js` 19 tests pass |
| Bottom dock and style sheets | css/dock.css, dock_art.css, fonts.css (about 1,000 lines) | Kiro dock design, commit d009bea | the bottom bar the player uses; OFL fonts built by Kiro tasks 48/49 | LOADED (CSS) |
Subtotal: about 3,840 JavaScript lines plus about 1,000 CSS lines loaded from Kiro work, against about 3,000 lines in index.html (the main line's page, many later edits).

## 2. Code Kiro wrote that is in the project but NOT loaded by the page
| area | files (lines) | status |
|---|---|---|
| Class stat table | js/class_stats.js 570 | numbers mirrored inside index.html and tested (`node scripts/test_class_stats.js`); not loaded as a script |
| Ultimate ledger | js/ultimate.js 281 | tested, not loaded (the page has its own ultimate code) |
| Scene layers | js/scene_layers.js 552 | tested (`test_scene_layers.js`), not loaded |
| i18n | js/i18n.js 158 | its test fails (`test_i18n.js`: missing assets/i18n/zh-TW.json), not loaded |
| Start screen and name | (not published) (48 tests) | only in ../pumpkin-killer_kiro59, not merged |
| Pose animation | (not published) 356 | only in ../pumpkin-killer_kiro67, not merged |

## 3. Tools and servers Kiro wrote (not part of the page, part of the project)
| area | files (lines) | impact | check |
|---|---|---|---|
| Standard MCP server for an opponent agent | scripts/mcp_stdio_server.py 813, mcp_game_server.py 528 | the agent-opponent mode and the base for the multiplayer design; aligned with the page by Kiro 80 today | `python3 -B scripts/test_mcp_stdio.py` (23 tests), `test_mcp_game.py`, `test_constants_sync.py` pass (re-run today) |
| Balance simulator | scripts/sim_balance.js 821 (+ tests) | measured hits-to-kill per class and set the HP and damage numbers (commit bf95661); updated today for the wall | `node scripts/test_sim_balance.js` 27 tests pass |
| Shared constants | shared/constants.json (Kiro task 01) | one source of numbers for the page and the engine | `test_constants_sync.py` passes |
| Image and wind-picture ingest | scripts/ingest_sheets.py, check_continuity.py, make_strip_gif.py, ingest_wind_sheets.py (about 1,300 lines with tests, tasks 64 and 71) | turns generated pictures into game assets with checks | tests pass (re-run today) |
| Router and tools | scripts/kiro_route.py and tests (task routing with retries), daily_log.py (task 78), score_ghost_tests.py (task 82) | model routing evidence, daily log, model test scorer | tests pass (re-run today) |

## 4. Design work by Kiro that changed game rules
- **Ultimate rules (Kiro task 44 addenda, about 20 commits on 2026-11-09):** skeleton triple javelin with +5 percent per hit and a crit on three, wizard explosion plus molotov, bat swarm, hunchback boomerang axe, knight hidden shield points A-B-C, bride wave and bat swarm numbers, cat-bat slow, stun timer, head-crit stun. Each rule is a log row with the Kiro addendum number.
- **Airdrop design (task 31):** landing zones, 3-round expiry, first crate to the human, AI only when hurt (commit 0d2ed21).
- **Class stats v2 and the strength reviews (tasks 38 to 40, 55, 56):** per-class HP 100/85/90/120 and the hits-to-kill band 4 to 6.
- **Review of the running game (task 58):** P0/P1 bugs found and fixed by the main line (menu fall-through, Space guard, heal checks, mouse button check).
- **Today:** art-gap prompts and the style-for-Colab diagnosis (tasks 73, 79), flow and system spec (74), MCP plan (75), 4v4 plan with overlap, splash and particle budget (76), architecture and task split (77), evidence and ledger (83). The main line corrected several of them against the owner's decisions the same day.

## 5. Kiro-native structure (what the rules ask judges to see)
| item | count | evidence status |
|---|---|---|
| /.kiro specs | 21 folders (61 spec files) | real files; tracked in git (73 files under .kiro) |
| steering files | 4 (+ kiro_assignment.md new, untracked) | real |
| custom agents | 4 (researcher used by every route run; tester; rules-reviewer; asset-inventory) | only researcher has run evidence; daily-logger was never created |
| hooks | 3 | no run logs; one is a no-op (points at files that do not exist) |
| MCP | .kiro/settings/mcp.json + the server above | tests exist; no recorded Kiro-side transcript |
| property-based tests | **js particles: seeded property tests, 300 cases per property (scripts/test_particles.js)**; rules and engine: none yet | corrects an earlier note of mine that said none existed |
| powers | none found | not used |

## 6. What this means
- Kiro's share of the SHIPPED front-end by lines is large (about 4,800 of roughly 7,800 lines loaded by the page), mostly effects, sound, wind and the dock; the core game loop, HUD drawing, AI and today's status effects, wind ghost, preload are the main line's in index.html. Say it that way in the write-up.
- Biggest gaps against the rules' "variety of Kiro tools": hooks and agents with no run evidence, no property tests for the rules, no powers. Queue A2 and A3 close the first two.
- Unmerged Kiro code (start screen, pose animation, the 58/60 patches) is the cheapest way to raise Kiro's visible share: queue A1 and C1 to C2.
