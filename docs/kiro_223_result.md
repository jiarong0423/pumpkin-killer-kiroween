# Kiro task 223 result

## What changed

- `js/perspective.js`: added pure `Perspective.create(ownSeat)` local/world mapping. It mirrors only a right-seat device and provides coordinate, wind, side, unit-ID, direction, angle, and dice-direction helpers. Local forward remains `+x`.
- `js/relay_client.js`: added optional perspective-aware translation at the action/judge wire boundary. `sendAction` and `sendJudge` convert local coordinates, unit IDs, sides, directions, and wind to world values. Inbound action/judge messages are converted back before listeners receive them. The protocol shape is unchanged. `setPerspective` allows the page to select the guest mapping after relay seat assignment.
- `index.html`: loads the pure mapper without changing rendering or the frozen orientation table. Joining as relay `white` selects the right-seat mapping before play. Seeded positions and wind are localized immediately at their world boundary. Human throw and move actions include their local start/result position and are converted by the relay client. The round-hash state converts unit IDs, positions, and wind back to world values; non-relay N=1 throw labels retain their existing values so the baseline fixture remains byte-identical.
- `scripts/test_perspective.js`: added 1,000 coordinate-inverse cases, wind/zone/start-range checks, relay in/out conversion checks, a three-round two-device page-like simulation, transcript verification, and assertions that character rendering and `ART_FACES_RIGHT` have no `Perspective` dependency.
- `docs/transcripts/two_seats_mirror.json` and `docs/transcripts/two_seats_mirror.sha256`: added the recorded simulated left/right world-state and hash agreement fixture.
- `sw.js`: regenerated through `python3 -B scripts/make_sw_precache.py --apply` to precache `js/perspective.js`.

The asymmetric deterministic starts are intentionally checked by legal zone, not equality: world left `252..612` mirrors to local opponent `1308..1668`, inside `1240..1680`; world right `1296..1656` mirrors to local-me `624..264`, inside `240..680`.

## Transcript SHA-256

- `docs/transcripts/n1_baseline.json`: `40be5ea22bd157b8da6ed5e0d8c297fc12f31cef2f10daf7354b934ae9911646`
- `docs/transcripts/two_seats_mirror.json`: `df2bfc3c4db1eb950d1583794c044d76cd1a01fc6837e1e09a827289350f6eb4`

## Verification commands and last lines

```text
node scripts/test_perspective.js
... 
test_perspective: two-seat simulated rounds agree in world state and round hash
test_perspective transcript sha256: df2bfc3c4db1eb950d1583794c044d76cd1a01fc6837e1e09a827289350f6eb4
test_perspective: rendering and orientation tables remain perspective-free

node scripts/test_relay_client.js
relay client paths: ok
relay client ordering: ok
relay client reconnect and hash checks: ok

node scripts/test_page_parses.js && node scripts/test_orientation_frozen.js && node scripts/record_match_transcript.mjs
test_orientation_frozen: 5/5 checks passed
record_match_transcript: baseline matches (40be5ea22bd157b8da6ed5e0d8c297fc12f31cef2f10daf7354b934ae9911646)
record_match_transcript: two recordings are byte-identical

for test in scripts/test_*.js; do node "$test" || exit $?; done
... 
test_wind_reach: all passed
(exit 0)

python3 -B scripts/test_mcp_game.py && python3 -B scripts/test_mcp_stdio.py && python3 -B scripts/test_constants_sync.py
Ran 29 tests in 2.872s
OK
OK: shared/constants.json matches index.html for all 16 constants and adaptive-level tables.

python3 -B scripts/make_sw_precache.py --apply && python3 -B scripts/test_pwa_files.py
OK wrote sw precache and cache name
Ran 3 tests in 0.059s
OK

node scripts/test_ui_settings.js && node scripts/test_phone_layout.js && node scripts/test_i18n.js
test_ui_settings: 7/7 checks passed
test_phone_layout: 7/7 checks passed
26 passed, 0 failed (266 keys per language)

shasum -a 256 docs/transcripts/n1_baseline.json docs/transcripts/two_seats_mirror.json
40be5ea22bd157b8da6ed5e0d8c297fc12f31cef2f10daf7354b934ae9911646  docs/transcripts/n1_baseline.json
df2bfc3c4db1eb950d1583794c044d76cd1a01fc6837e1e09a827289350f6eb4  docs/transcripts/two_seats_mirror.json
```

No visible string changed, so I did not run the font builder. No dictionary key was needed.

## What I could not verify

- I did not run a real two-device relay session. The owner must run `python3 -B scripts/dev_server.py --with-relay`, open the host page on the left seat, join from a second device as the right-seat guest, have both devices throw once, verify each screen presents its own unit on the local left, and verify the round hashes agree.
- `node scripts/measure_phone_layout.mjs` did not produce successful layout metrics. It failed at `873x392` with the pre-existing opponent name plate intersection with the sound, reset, language, settings, and help buttons. `node scripts/test_layout_property.mjs` likewise failed at the pre-existing seeded `882x381` case with the same intersections. This task made no visual/CSS change, so I cannot claim measured numbers were produced or identical; the structural `test_phone_layout.js` gate passed.
- The complete Python loop did not finish green because pre-existing relay/MCP tests failed outside this task's lock: `test_e2e_local.py` reported `red action was not acknowledged and judged` with `bridge=stale_or_out_of_turn`; `test_mcp_seats.py` reported the pre-seat referee baseline mismatch; and a later repeat of `test_mcp_connect.py` had `round_hashes[1]` contain two values. The task-specific client checks and the core engine/stdio/constants commands above passed.
- No commit, push, deploy, remote change, secret access, or image generation was performed.
