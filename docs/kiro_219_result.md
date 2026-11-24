# Kiro task 219 result

## What changed

- `index.html`, `HERO_PROFILES.bride.hp`: `hp: 70` → `hp: 80`. This required value was already present in the worktree when this task began; it was retained and verified.
- `js/class_stats.js`, `CLASSES.bride.hp`: `hp: 70` → `hp: 80`. This required value was already present in the worktree when this task began; it was retained and verified.
- `shared/heroes.json`, `bride.hp`: `"hp": 70` → `"hp": 80`. This required value was already present in the worktree when this task began; it was retained and verified. The Python MCP engine reads this shared table, so it has no separate Bride HP constant.
- `scripts/test_decisions_frozen.js`, agreed hero table: `bride: [70, 28]` → `bride: [80, 28]`. This required test update was already present in the worktree when this task began; it was retained and verified.
- `scripts/test_class_stats.js`, `zero defense preserves the existing hits-to-kill matrix`: Bride-target cells for Bat and Ghost Nun changed from `3` to `4`, reflecting 80 HP.
- `scripts/test_properties.js`, `checkBalance`: lower balance guard `0.08` → `0.15`; error text `8 to 80 percent` → `15 to 80 percent`. The comment now records the eight-seed measurement.
- `docs/character_plan_20261116.json`: regenerated with `scripts/make_roster_json.py`, as required. Its Bride row changed `"hp": 75.0` → `"hp": 80.0`, and stale documented damage `25.0` → the already-pinned page value `28.0`; the actual combat damage was not changed. The generator also refreshed stale non-Bride roster facts from `index.html`.

No Bride HP appeared in `shared/constants.json`, `scripts/make_roster_json.py`, `scripts/mcp_game_server.py`, either `assets/i18n` dictionary, or `scripts/mcp_referee_baseline_145.json`. The referee baseline was not regenerated because it contains no Bride and the task expressly prohibits regenerating it otherwise.

## Eight-seed balance measurement

The command used the required seeds `179, 1..7`, normal AI, and 56 matches per unordered pairing for each seed. “Before” clones `ClassStats.CLASSES` and changes only `bride.hp` to 70; it does not modify project files.

| Hero | Before, Bride 70 HP | After, Bride 80 HP |
|---|---:|---:|
| Skeleton | 60.8% | 59.3% |
| Wizard | 39.8% | 39.8% |
| Bat | 36.7% | 34.0% |
| Knight | 68.6% | 68.6% |
| Bride | 10.6% | 18.6% |
| Hunchback | 64.6% | 64.5% |
| Reaper | 55.1% | 52.6% |
| Ghost Nun | 63.8% | 62.5% |

The Bride’s 18.6% eight-seed average exceeds 15%, so the property-test lower bound was raised from 8% to 15%.

## Commands run

```text
node -e "const { runPairings } = require('./scripts/sim_balance.js'); const seeds = [179,1,2,3,4,5,6,7]; const totals = {}; for (const seed of seeds) { const result = runPairings({ seed, matchesPerPairing: 56, agentLevel: 'normal' }); for (const [hero, rate] of Object.entries(result.classAverage)) totals[hero] = (totals[hero] || 0) + rate; } console.log(JSON.stringify({ seeds, matchesPerPairing: 56, classAverage: Object.fromEntries(Object.entries(totals).map(([hero, total]) => [hero, total / seeds.length])) }, null, 2));"
# "bride": 0.18622448979591835

node scripts/test_properties.js
# ok   - all balance pairings finish without numerical dominance (2016 matches)
# test_properties: all 6 properties passed

python3 -B scripts/make_roster_json.py
# wrote docs/character_plan_20261116.json heroes 8 missing []

python3 -B scripts/test_heroes_sync.py
# OK: shared/heroes.json matches index.html HERO_PROFILES for 8 heroes.

node -e "const { runPairings } = require('./scripts/sim_balance.js'); const CS = require('./js/class_stats.js'); const seeds = [179,1,2,3,4,5,6,7]; function average(table) { const totals = {}; for (const seed of seeds) { const result = runPairings({ seed, matchesPerPairing: 56, agentLevel: 'normal', table }); for (const [hero, rate] of Object.entries(result.classAverage)) totals[hero] = (totals[hero] || 0) + rate; } return Object.fromEntries(Object.entries(totals).map(([hero, total]) => [hero, total / seeds.length])); } const before = JSON.parse(JSON.stringify(CS.CLASSES)); before.bride.hp = 70; console.log(JSON.stringify({ seeds, matchesPerPairing: 56, beforeHp70: average(before), afterHp80: average(CS.CLASSES) }, null, 2));"
# "bride": 0.10586734693877552
# "bride": 0.18622448979591835

node scripts/test_class_stats.js
# ok   - comparison and calculations are deterministic without ambient entropy or time
# test_class_stats: all 14 tests passed

for test in scripts/test_*.js; do node "$test" || exit $?; done
# test_wind_reach: all passed
# exit 0

for test in scripts/test_*.py; do case "$test" in scripts/test_ai_gateway.py|scripts/test_clean_checkout.py|scripts/test_e2e_local.py|scripts/test_mcp_connect.py|scripts/test_mcp_connect_weather.py|scripts/test_pk_relay.py|scripts/test_relay_reconnect.py|scripts/test_smoke_deployed.py|scripts/test_smoke_url.py) continue ;; esac; python3 -B "$test" || exit $?; done
# FAILED (failures=1)
# test_mcp_seats.py failed at test_referee_matches_the_pre_seat_baseline

result_code=0; for test in scripts/test_mcp_skills_ultimates.py scripts/test_mcp_stdio.py scripts/test_mcp_turns.py scripts/test_mcp_units.py scripts/test_mutation_smoke.py scripts/test_no_secrets_in_tree.py scripts/test_pk_headless_match.py scripts/test_pk_mcp_health.py scripts/test_postprocess_audio.py scripts/test_preload_links.py scripts/test_privacy_gate.py scripts/test_pwa_files.py scripts/test_qr_decode.py scripts/test_room_codes.py scripts/test_round_hash.py scripts/test_score_ghost_tests.py scripts/test_shield_wall.py scripts/test_weather_golden.py; do python3 -B "$test" || result_code=1; done; exit "$result_code"
# test_weather_golden.py: 800 cases passed
# exit 1: scripts/test_pwa_files.py failed because `sw.js` is stale: `STALE sw precache: would write 69 files; 20 preload assets; pk-e435eb771d`
```

Socket-requiring Python tests were deliberately excluded from the socket-free run: `test_ai_gateway.py`, `test_clean_checkout.py`, `test_e2e_local.py`, `test_mcp_connect.py`, `test_mcp_connect_weather.py`, `test_pk_relay.py`, `test_relay_reconnect.py`, `test_smoke_deployed.py`, and `test_smoke_url.py`.

## Could not verify

- The complete socket-free Python suite did not pass. `scripts/test_mcp_seats.py` reports a mismatch against `scripts/mcp_referee_baseline_145.json`. That fixture has no Bride occurrence, so I did not regenerate it, as the brief requires. The mismatch must be handled by the owner of the unrelated baseline drift.
- `scripts/test_pwa_files.py` reports that `sw.js` is stale. No Chinese text was added by this task, and `sw.js` is outside the task’s allowed file list, so I did not run the write-mode precache generator or modify it.
- `scripts/test_qr_decode.py` skipped its required UTF-8 ECI decode portion because `cv2.QRCodeDetector` cannot decode it and `pyzbar` is unavailable. It did not fail.
- I did not do a browser playthrough, socket/relay test, commit, push, deployment, remote change, or secret access.
