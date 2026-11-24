# Kiro task 189 result

## What changed

- `scripts/install_coins.py` keys the owner-approved magenta coin sources, crops their opaque bounds, and writes `assets/ui/coin_pumpkin_head.png` and `assets/ui/coin_pumpkin_tail.png` as 512 × 512 RGBA files.
- `js/determinism.js` adds `coinToss(seed)`. `scripts/determinism_py.py` adds the equivalent `coin_toss(seed)`. Both resolve the hash of `(seed, 7001)` to `0` for left first or `1` for right first.
- `scripts/make_determinism_golden.js`, `shared/determinism_golden.json`, `scripts/test_determinism.js`, and `scripts/test_determinism_golden.py` carry 52 coin-toss vectors and test the result range over 10,000 seeds.
- `index.html` adds the pumpkin coin overlay, `showCoinToss`, and `beginOpeningTurn`. The overlay animates for 2.2 seconds, can be skipped by tap, and lands on the head or tail picture that matches the seeded result.
- `index.html` adds `seats.level`, `AI_LEVEL_MULTIPLIERS`, `levelKnobs`, `skillChanceFor`, and `matchSettings`. A built-in AI seat shows Easy, Normal, and Hard buttons. Normal preserves `AI_VIEW_POS_NOISE`, `AI_VIEW_WIND_NOISE`, and `AI_AIM_ERROR`; Easy applies `1.6` and does not use one-use skills; Hard applies `0.5` and uses one-use skills at `35%` rather than `20%`.
- `index.html` offers `Agent (MCP)` only when `?relay=` is present. The selected remote seat waits behind the curtain and displays the relay room code plus QR code. A match still requires a human seat.
- `assets/i18n/en.json` and `assets/i18n/zh-TW.json` add all opening, coin, AI-level, and agent-wait text keys.
- `scripts/test_opening.js` validates coin vectors, first-turn handling, the fixed-level rules, and conditional agent-seat wiring. `scripts/test_decisions_frozen.js` pins the three multipliers and the Hard skill chance.
- Generated assets were refreshed with `scripts/make_preload_links.py --apply`, `scripts/build_fonts.py`, and `scripts/make_sw_precache.py --apply`.

## Commands run

```sh
python3 -B scripts/install_coins.py
```

Last lines:

```text
OK assets/ui/coin_pumpkin_head.png from coin_pumpkin_head_v1_p4.png
OK assets/ui/coin_pumpkin_tail.png from coin_pumpkin_tail_v1_p4.png
```

```sh
node scripts/make_determinism_golden.js && node scripts/test_determinism.js && python3 -B scripts/test_determinism_golden.py
```

Last lines:

```text
wind:78 startX:104 moveDie:104 supplyDrop:78 bounceCount:156 nunStunPick:468 coinToss:52
test_determinism.js: 1040 golden vectors passed
test_determinism.js: 10000 seed property cases passed
test_determinism_golden.py: 1040 golden vectors passed
test_determinism_golden.py: 10000 seed property cases passed
```

```sh
node scripts/test_opening.js && node scripts/test_i18n.js && node scripts/test_seats_items.js && node scripts/test_join_flow.js && node scripts/test_ui_polish.js && python3 -B scripts/test_preload_links.py && python3 -B scripts/make_sw_precache.py --apply && python3 -B scripts/make_sw_precache.py --check && python3 -B scripts/test_pwa_files.py
```

Last lines:

```text
test_ui_polish: 6/6 checks passed
test_preload_links: OK (20 links)
OK wrote sw precache and cache name
OK sw precache is up to date (63 files; 20 preload assets; pk-493daf2f64)
Ran 3 tests in 0.061s

OK
```

```sh
python3 -B scripts/build_fonts.py && python3 -B scripts/test_fonts.py
```

Last lines:

```text
total font bytes: 1125204 (1.07 MB)
----------------------------------------------------------------------
Ran 36 tests in 0.457s

OK
```

```sh
node scripts/test_decisions_frozen.js && node scripts/test_opening.js && node scripts/test_i18n.js && node scripts/test_seats_items.js && node scripts/test_join_flow.js && node scripts/test_ui_polish.js && python3 -B scripts/test_preload_links.py
```

Last lines:

```text
test_decisions_frozen: 7/7 checks passed
opening coin toss, seat levels, and agent option: ok
26 passed, 0 failed (239 keys per language)
seats and symmetric one-use items: ok
join flow fake socket and QR wiring: ok
test_ui_polish: 6/6 checks passed
test_preload_links: OK (20 links)
```

```sh
git diff --check
python3 -B -c "from PIL import Image; from pathlib import Path; root=Path('assets/ui'); print(' '.join(f'{p.name}:{Image.open(p).mode}:{Image.open(p).size}' for p in sorted(root.glob('coin_pumpkin_*.png'))))"
```

Last lines:

```text
coin_pumpkin_head.png:RGBA:(512, 512) coin_pumpkin_tail.png:RGBA:(512, 512)
```

## Browser checks for the main line

1. Start a normal match and confirm the 2.2-second pumpkin coin flip appears. Tap **Tap to skip** before it finishes and confirm the selected seeded result starts the expected side.
2. Use seeds that produce both `Determinism.coinToss(seed) === 0` and `=== 1`. Confirm the head lands for left first and the tail lands for right first. A right-side built-in AI must begin its throw immediately. A right-side human must see the hand-off curtain.
3. Select the built-in AI on either seat row. Confirm the Easy, Normal, and Hard controls appear and Normal is selected by default. Confirm Easy does not consume Heal, Heavy, or Double; Hard can use those skills at the higher chance.
4. Open the page with `?relay=ws://localhost:8765`. Confirm each seat row offers **Agent (MCP)**. Select it, create a room, and confirm the room code and QR appear while the remote seat waits. Confirm the Agent option is absent without `?relay=`.

```sh
node scripts/test_opening.js && node scripts/test_i18n.js && node scripts/test_seats_items.js && node scripts/test_join_flow.js && node scripts/test_ui_polish.js && node scripts/test_decisions_frozen.js && python3 -B scripts/test_preload_links.py && python3 -B scripts/make_sw_precache.py --apply && python3 -B scripts/make_sw_precache.py --check && python3 -B scripts/test_pwa_files.py && python3 -B scripts/test_constants_sync.py && git diff --check
```

Last lines:

```text
test_decisions_frozen: 7/7 checks passed
test_preload_links: OK (20 links)
OK wrote sw precache and cache name
OK sw precache is up to date (63 files; 20 preload assets; pk-830ef48520)
Ran 3 tests in 0.040s

OK
OK: shared/constants.json matches index.html for all 13 constants and adaptive-level tables.
```

## What I could not verify

I could not open a browser in this run, so the visual animation, the rendered tail face, and a real relay join need the browser checks above.

I attempted the task-required complete runner:

```sh
for f in scripts/test_*.js; do node "$f" || exit $?; done; for f in scripts/test_*.py; do python3 -B "$f" || exit $?; done
```

The environment denied the request before it ran. Its only output was:

```text
The permission request failed before it was answered, so this call did not run; the user did not reject it.
```

Therefore I do not claim that every existing test passed. The focused opening, determinism, i18n, seat, relay, UI, preload, font, PWA, and decision-freeze checks listed above did pass.
