# Z8 design: every move, declared versus actually wired (2026-11-23, design only, nothing run)

Owner: "all moves are the full set, and there is the wiring mismatch problem". Merged with Z1 / Z5 (8-hero room matrix) and EB-BACK (event tally) so there is ONE move catalog and ONE set of runners, not three.

## 0. Sources of truth that exist today (read, not remembered)
| Layer | Where | What it declares |
|---|---|---|
| Spec data | `shared/heroes.json` | per hero: hp, dmg, weapon (`proj_*`), launch point, hit box, `statusOnHit` (bleed, weak, poison, slow, burn, knockback), `ultimate.kind` (triple_javelin, pumpkin_blast, shuriken_rain, shield_wall, ghostfire_trio, bat_swarm, boomerang, cross_dart), knight `bounce` |
| Page | `index.html` `HERO_PROFILES`, `ULT_BUILT`, weapon draw code, `snd(...)` calls, `HIT_SOUND`, fx emits | what the player sees and hears |
| Engine | `scripts/mcp_game_server.py` `HERO_TEMPLATES`, `_resolve_throw`, status code | what the back end simulates |
| MCP | `scripts/mcp_stdio_server.py` tools and `submit_action` types (throw, move, defend, skill heal/double/heavy, ultimate) | what an agent can do |
| Audio and fx | `assets/audio/` map (52 events), `docs/role_event_graph_20261123.json` | event to file, role to cue |
| Room rules | `toggleUltimate` guard (index.html about line 2126), `PageJudgeRelay.submit` guard (mcp_stdio_server.py about line 1989), `en.json relay.noItems`, `docs/mcp_agent_protocol.md` | which moves a room refuses |

## 1. The move catalog (one script, shared)
`scripts/move_catalog.py` (new, read-only): builds `(not published)` from the sources above. One row per move: id, hero, kind (plain, skill heal / double / heavy, ultimate, shield, knight wall, movement dice, supply / airdrop, status source), and for each layer what it declares (weapon, image key, damage, status, sound events, fx names, room allowed yes / no). A cell that a layer does not declare is `absent`, so a missing declaration is visible before any run. Statuses (bleed, poison, burn, slow, stun, shock, weak, frost) get rows too, with the move(s) that cause them.
EB-BACK's event tally and the 8-hero room matrix import this catalog for their expected sets (no second list).

## 2. Mismatch classes, each a re-runnable gate (all start as read-only scripts with a failing exit code)
- M1 move wired to the wrong weapon or effect: page vs engine vs spec for each row (weapon, damage after ramp / comeback / weather, status, bounce, ultimate kind). Fixed seeds, page in the node vm (`page_harness`), engine through `Session`.
- M2 wrong sound or picture: for each row, the sound events and fx the page actually emits (event log of `(not published)`'s machinery) against the catalog and the role graph.
- M3 selection leftovers: extend `scripts/test_skill_state_no_leak.js` over every move and all three seats (human, left computer, right computer).
- M4 declared but never wired: every audio event, every `HERO_PROFILES` / heroes.json field, every i18n key used by a move: find "defined with no call site" (static scan, allowlist for intentional ones, like `test_sim_clock_reads`).
- M5 page = engine = MCP action: one move through all three, same seed, compare hit_type, damage, statuses, positions (the existing `rerun_hit_coverage.py` covers plain flights; this adds skills, ultimates, statuses).
- M6 room mode differs from single player: the refusal list (knight, reaper, and the hag if it is made room-refused) must agree across UI guard, bridge guard, `relay.noItems` text and the protocol doc; run the UI guard in the node vm (`toggleUltimate` with the room state set) and the bridge guard through the matrix.

## 3. Runs (heavy, so resource table and the owner's word first)
8-hero room matrix = Z1 + Z5 widened (cell H of `scripts/mcp_acceptance_matrix.py`): for each hero, each team size 1 / 2 / 3, until at least 30 ultimate attempts (fired, or refused for knight and reaper) and at least 30 plain throws by that hero; the agent aims with the engine's own flight (fixed seed per run), the focal hero is the first unit of the red team, the computer opponent uses heroes without a room-refused ultimate. Per run row: who threw, what (plain or ultimate), the page's result (`get_history`), statuses seen, and whether both seats' round hash agreed for that round. Output: an 8 x scenario matrix (heroes x {plain, ultimate} x {1v1, 2v2, 3v3}) with runs, throws and desync count per cell; any desync stops the run for diagnosis.
Role x event coverage in rooms comes from the same rows (events seen per hero); empty cells become EB gaps.
Weather and wind groups: the matrix seeds cover the graveyard scene; the weather / wind sweep stays in the existing `rear_rear_weather_wind.py` and `audit_page_events` runs and is re-run on the fixed tree at the end.

## 4. Order
1. `move_catalog.py` plus M4 and M6 (static, minutes, no run). 2. M1, M2, M5, M3 on small samples to measure time and memory. 3. Resource table. 4. Heavy runs one at a time: EB-BACK (running now), Z1 room stress, 8-hero matrix, M-gates at full scale. Every mismatch: ledger row first, backup, fix the wiring table at its root, re-run until 0 mismatches. The corrected catalog and matrix are then saved as the baseline for `event_baseline.py --compare`.
