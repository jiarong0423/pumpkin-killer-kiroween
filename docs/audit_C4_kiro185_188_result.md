# Crew C4 result — independent re-run of Kiro 185 / 188 / RELEASE_READINESS (2026-11-16 06:10-06:16)

Nothing was fixed. Python run with `python3 -B`. Raw output: scratchpad `$TMPDIR/c4/`.
Snapshot rule: first pass ran at about 06:11. At 06:13-06:16 another task was still editing
`scripts/mcp_game_server.py` and `scripts/mcp_stdio_server.py`, so a later sweep of the same MCP
tests failed with a half-changed signature (`ValueError: red hero must be a list of exactly 4 ids`).
That later result is UNSTABLE, re-run later; it is not counted against Kiro.

## Commands (last lines)

| Command | Result | Last line |
|---|---|---|
| test_mcp_skills_ultimates.py | pass (06:11), unstable after | Ran 6 tests, OK |
| test_mcp_game.py | pass (06:11), unstable after | Eight hero table / status / 1v1 Passed |
| test_mcp_stdio.py | pass (06:11) | Ran 29 tests, OK |
| test_mcp_seats.py, test_mcp_turns.py | pass (06:11), unstable after | Ran 6 / 5 tests, OK |
| test_constants_sync.py, test_heroes_sync.py | pass | 13 constants / 8 heroes match index.html |
| test_determinism_golden.py + test_determinism.js | pass | 1040 golden, 10000 seed cases |
| 8 node ultimate/particle tests named in 185 | pass | 67/67; 24; 13; 6; 6; 13; 7; 6 |
| git diff --check | pass | no output, exit 0 |
| test_smoke_deployed.py | needs-owner-terminal | all 3 tests die in setUp: socket bind PermissionError |
| smoke_deployed.py --check-config deploy/nginx.conf | pass | NGINX_CONFIG PASS |
| sh -n deploy/entrypoint.sh | pass | syntax ok |
| test_check_deploy_files.py | pass | Ran 3 tests, OK |
| test_export_tree.py, test_make_download_package.py | pass | Ran 8 / 5, OK |
| test_privacy_gate.py (unit test) | pass | OK |
| export_tree.py --help / --dry-run | pass | selected=1185, wrote nothing |
| test_pwa_files.py | FAIL | manifest display 'fullscreen' != 'standalone' |
| privacy_gate.py with PK_TERMS | not run | needs owner file `$HOME/pk_privacy_terms.txt` |
| Docker build, curl, deployed smoke, relay tests (test_pk_relay, test_relay_reconnect, test_smoke_url, test_mcp_connect*) | needs-owner-terminal | bind / socket PermissionError |
| Other JS: test_opening.js, test_wind_reach.js | fail, unstable | both edited today by other tasks (06:12, 05:48); out of 185/188 scope |
| Other JS (37 of 39 files) | pass | |

## Failures and whether Kiro's claim is wrong

1. `scripts/test_pwa_files.py:45`: manifest `display` is now `fullscreen` (file changed 06:02, test last
   edited 03:36). Cause: a later task (landscape fill) changed the manifest without updating the test.
   188 and RELEASE_READINESS list this test as run; it passed then, so the claim was true then and is now stale.
2. `scripts/test_smoke_deployed.py`: sandbox cannot bind a port; `setUp` binds for every test, even the two that
   need no socket. Not a defect, but the "Deploy files PASS" and "Smoke script PASS" rows rest on a test only
   the owner terminal can run. I ran the two non-socket halves (nginx check, `sh -n`): both pass.
3. Export count: 188 says 1158/1159 files; today's dry run selects 1185. Files were added since; the
   readiness number is stale (size not re-checked).

## Claims checked against code

- Eight ultimates implemented: yes. `shared/heroes.json` has an `ultimate` block for all 8; `_resolve_throw`
  has a branch for skeleton, bat, reaper, hag, wizard, hunchback, bride; knight is `set_knight_wall` in
  `mcp_stdio_server._do_ultimate`. Probe (scratchpad `probe_c4.py`): same aim, ultimate damage vs normal:
  skeleton 33 vs 22, bat 36 vs 24, hag 27.6 vs 24, hunchback 52.5 vs 21, reaper 42.9 vs 22 (+burn), bride 28 or
  64.4 (swarm fires), wizard blast works. Numbers match heroes.json multipliers.
- Heal 35 HP, double 1.04x power with 0.26 s, heavy 1.5x, one use per side: matches code (`mcp_stdio_server.py` ~735-765).
- Naming: Kiro's text says "necromancer" and "nun"; the code and heroes.json call them `reaper` and `hag`. Wording only.
- Dockerfile.coolify / entrypoint / nginx match the result: relay on 127.0.0.1:8765, nginx on 80, `/relay`
  maps to `/ws` on Upgrade and `/health` otherwise, `deploy/relay/requirements.txt` exists (websockets 15.0.1),
  `pk_relay.py` honours HOST, PORT, PK_RELAY_ORIGINS, serves `/health` and `/ws`.

## Defects to fix (highest risk first)

1. DEPLOY WIRING GAP (P0). `index.html` never reads `window.PK_RELAY`; the relay address comes only from
   `?relay=` (index.html:669). `relaySocketUrl` then appends `/ws` unless the value already ends with `/ws`,
   so `wss://host/relay` becomes `wss://host/relay/ws`, which nginx 404s (only `location = /relay` exists).
   Adding the `relay-config.js` tag, as 188 says, does not make the deployed page use the relay. The smoke
   script connects to `/relay` directly, so it would pass while the real page still cannot join a room.
   Fix: make the page default to `window.PK_RELAY`, and make nginx accept either path or stop appending `/ws`.
2. Shield Wall (P1, disclosed by Kiro): no 3-enemy-attack expiry; it also blocks any crossing within 70 px at any
   height, before the hunchback shield bypass. Page-parity gap, not a crash.
3. Weak tests (P1): `test_every_projectile_ultimate_resolves_with_nonnegative_damage` only asserts damage >= 0, so
   it passes with a no-op ultimate. The reaper skip test only checks that white_1 is absent from results.
4. `test_pwa_files.py` stale vs manifest `fullscreen` (P1, see above) breaks the release gate list.
5. Readiness doc stale (P2): file count 1159 vs 1185; `relay-config.js` not in the sw.js precache list.
6. `deploy/.dockerignore` is not read when the context is the repo root (Docker reads root `.dockerignore`
   or `Dockerfile.coolify.dockerignore`); the COPY lines already act as the allowlist, so low risk (P2).
7. `entrypoint.sh` (P2): under `set -e`, a non-zero `wait` exits before `status=$?`; a relay crash is not
   restarted (only the healthcheck turns unhealthy). README lists the smoke command twice (harmless).
8. Re-run later (unstable): all `test_mcp_*`, `test_pk_headless_match`, `test_pk_mcp_health`, `test_mcp_allowlist`
   once the engine edit settles; their failures at 06:13+ come from the in-progress signature change.
