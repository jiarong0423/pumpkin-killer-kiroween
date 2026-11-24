# Kiro task 194 result

## What changed

- Updated owner-approved move zones to left `240..680` and right `1240..1680` in `index.html`, `js/knockback.js`, `scripts/sim_balance.js`, `scripts/mcp_game_server.py`, and their pinned tests. Start positions and existing golden vectors were not changed.
- Updated `scripts/test_wind_reach.js`: winds `-5..5` must all be hittable. It reports the six documented `±6` exceptions rather than hiding them: `L240→R1640`, `L240→R1680`, `L280→R1680`, and their right-to-left mirrors.
- Added deployment wiring: root `relay-config.js`, `relay-config.js` page loading, query/config/localhost relay selection, exact `/relay` preservation in `RelayClient.relaySocketUrl`, `--with-relay` in `scripts/dev_server.py`, network-first `relay-config.js` service-worker handling, corrected fullscreen PWA assertions, safer entrypoint `wait`, and smoke-config parsing.
- Added `Determinism.sideDraw()` in JavaScript and Python, with 52 golden vectors independent from the coin-toss domain. The start-screen side-choice UI and relay `start` side field are not yet integrated.
- Added the pure `js/team_battle.js` helper and `scripts/test_team_battle.js`; task 2 is checked in the team spec. It covers living-unit lists, stable ID rotation, win conditions, and N=1..4 formation slots.
- Added room-code normalization and per-socket wrong-code rate limiting in `scripts/pk_relay.py`, corresponding relay-client tests, `scripts/test_room_codes.py`, and the short multiplayer explanation. `docs/relay_protocol_20261115.md` no longer says that a player downloads the game.
- Refreshed `docs/RELEASE_READINESS_20261116.md` from a dry run: `selected=1212`.

## Sub-agent mechanism

This session provided no Kiro sub-agent dispatch tool. I performed the isolated S1-style pure-module work directly. No separate S2/S3/S4 agent result is claimed.

## Stable team-spec stages

Only task 2 (pure helpers) is stable and checked. Steps 1 and 3b through 8 were not integrated. The existing page remains 1v1, so N=1 byte-identical behavior was retained rather than attempting an unsafe partial team-state rewrite.

## Commands run

```text
node scripts/test_knockback.js && node scripts/test_sim_balance.js && node scripts/test_wind_reach.js && python3 -B scripts/test_mcp_game.py && python3 -B scripts/test_mcp_stdio.py
...
test_knockback: all 3 tests passed
test_sim_balance: all 29 tests passed
test_wind_reach: all passed
🎉 ALL MCP GAME ENGINE TESTS PASSED!
Ran 29 tests in 1.087s
OK

python3 -B scripts/make_sw_precache.py --apply && node scripts/test_team_battle.js && node scripts/test_determinism.js && node scripts/test_relay_client.js && node scripts/test_page_parses.js && python3 -B scripts/test_determinism_golden.py && python3 -B scripts/test_room_codes.py && python3 -B scripts/test_pwa_files.py && python3 -B scripts/test_smoke_deployed.py
...
test_team_battle: rotation, alive lists, winners, and N=1..4 slots passed
test_determinism.js: 1092 golden vectors passed
test_determinism_golden.py: 1092 golden vectors passed
Ran 4 tests in 1.545s
OK
Ran 3 tests in 0.039s
OK
OVERALL PASS

node scripts/test_ui_settings.js && node scripts/test_phone_layout.js && node scripts/test_i18n.js && node scripts/test_layout_property.mjs && node scripts/measure_phone_layout.mjs && python3 -B scripts/test_constants_sync.py
...
test_ui_settings: 7/7 checks passed
test_phone_layout: 7/7 checks passed
26 passed, 0 failed (254 keys per language)
test_layout_property: 200 seeded landscape viewports passed
measure_phone_layout: 5/5 viewports passed
OK: shared/constants.json matches index.html for all 13 constants and adaptive-level tables.
```

## Not verified / main-line follow-up

- I did not complete the requested S2 screenshot review or create `(not published)`; no visual changes were made.
- I did not implement the start-screen left/right/computer-decides choice, team battle steps 1 and 3b–8, per-unit HUD/items, or multiplayer page-state integration. The page therefore does not yet meet the full 1–4 unit task.
- I did not run every `scripts/test_*.js` and socket-free Python test after all changes.
- I did not run a real relay session with two phones. The owner/main line must start `python3 -B scripts/dev_server.py --with-relay`, open the static page on two devices, create a room, scan or open the QR link, enter a deliberately bad code six times to verify rate limiting, then create/join, ready, and compare the two round hashes.
