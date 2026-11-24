# Kiro task 220 result

## What changed

- `js/smart_candidates.js`: added the deterministic, DOM-free `SmartCandidates.build` candidate builder. It takes the noisy public opponent view plus AI-owned availability state and a supplied landing function. It returns three to six contract-only candidates, numbers them after distance ordering, creates normal, ±3-power, heavy, ultimate, Knight defend, and position-improving move choices as applicable, and does not use `Math.random`.
- `scripts/test_smart_candidates.js`: added checks for deterministic generation, three-to-six candidates, contract-only/public candidate fields, distance ordering and IDs, Knight defend after two recent player hits, and charged-only ultimate choices.
- `index.html`: loads the candidate module. Smart seats now request `/ai` with `prompt_kind: "pick"` and the public candidate list, validate a returned candidate ID, and route the resulting action through the built-in AI throw/defend/move paths. The six-second request timeout, host-only relay rule, relay throw broadcast, round-hash throw values, fallback notice, and two-unavailable downgrade remain in place. The built-in AI's Normal path still uses its existing aim, skill, and physics code.
- `index.html`: factored the existing AI Knight shield behavior into `tryAiDefend`, so both Normal's occasional shield decision and Smart's candidate action use the same action path.
- `assets/i18n/en.json` and `assets/i18n/zh-TW.json`: added the literal `level.smartHelp` key and changed `level.smart`. The label and visible help say that an online model chooses an action while the game calculates shot numbers locally.
- `scripts/test_smart_opponent.js`: replaced aim-template tests with fake-gateway `pick` tests. It checks a valid ID, rejection of invalid IDs, six-second abort, fallback wiring and notice, one-time Normal downgrade after two unavailable responses, host-only relay behavior, round hashes, and absence of private slot data or key-shaped strings in the request.
- `scripts/sim_smart.js`: added a deterministic 2,000-match-per-policy measurement using the candidate builder and the existing simulator’s fixed-step landing function. It reports Smart `always_1`, lowest-distance, seeded-random, and Normal win/hit rates.
- Ran the required font build and service-worker precache generator after adding Traditional Chinese text. The generators updated their generated font artifacts and `sw.js`.

## Commands run

```text
node scripts/test_smart_candidates.js
# test_smart_candidates: determinism, public fields, sorting, defend, and ultimate rules passed

node scripts/test_smart_opponent.js
# test_smart_opponent: fake pick gateway, timeout, fallback, host, and secret checks passed

node scripts/test_i18n.js
# 26 passed, 0 failed (270 keys per language)

node scripts/test_page_parses.js
# test_page_parses: 2 inline scripts and every js/*.js parse

node scripts/test_phone_layout.js
# test_phone_layout: 7/7 checks passed

node scripts/test_layout_property.mjs
# measure_phone_layout: 200/200 viewports passed (seed 19120261116)
# test_layout_property: 200 seeded landscape viewports passed

node scripts/test_ui_settings.js
# test_ui_settings: 7/7 checks passed

python3 -B scripts/build_fonts.py
# built assets/fonts/pk-display-cjk-900.woff2  406.7 KB
# total font bytes: 1133096 (1.08 MB)

python3 -B scripts/test_fonts.py
# Ran 36 tests in 0.325s
# OK

python3 -B scripts/make_sw_precache.py --apply
# STALE sw precache: would write 70 files; 20 preload assets; pk-bed322c73e
# OK wrote sw precache and cache name

python3 -B scripts/test_pwa_files.py
# Ran 3 tests in 0.056s
# OK

node scripts/test_*.js (each matching script run in a loop)
# test_wind_reach: all passed
# exit 0

python3 -B scripts/test_*.py (each matching script run in a loop)
# test_weather_golden.py: 800 cases passed
# exit 1

node scripts/sim_smart.js
# always_1: win 84.25% hit 52.11%
# lowest_predicted_distance: win 84.25% hit 52.11%
# seeded_random: win 56.00% hit 30.00%
# normal: win 67.95% hit 36.92%
# always_1 vs Normal delta: 16.30 points
# exit 1

git diff --check
# exit 0; no output
```

## Could not verify

- No real model call was made. It needs the owner's Bedrock model ID, enabled model access, and server credentials.
- I did not run a browser playthrough or a relay-room session.
- The complete Python test loop exited 1 because unrelated existing tests failed: `scripts/test_e2e_local.py` reported `stale_or_out_of_turn`, and `scripts/test_mcp_seats.py` differed from its pre-seat referee baseline. I did not modify their files because they are outside this task’s allowed paths.
- The required candidate ordering and fallback requirement conflict in the current Normal AI: candidates are sorted by actual fixed-step predicted distance, but the Normal heuristic can be less accurate than its deliberate ±3-power variants. In the required simulator, ID 1 therefore differs from the Normal action by 16.30 win-rate points, not the required maximum of 2. I left the simulator failing rather than misreporting the `always_1` policy as Normal. Resolving this needs an owner decision on whether to preserve strict distance ordering or reserve candidate ID 1 for the Normal aim.
- No commit, push, deployment, remote change, or secret access occurred.
