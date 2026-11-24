# Task 187 result — simulator status parity and fresh balance matrix

## What changed

- `scripts/sim_balance.js`
  - `applyStatus`, `applyPoison`, `applyBleed`, `applyBurn`, and the three tick functions now refresh duration without stacking and apply `Math.min(DMG, Math.max(0, hp - 1))`. Poison, bleed, and burn therefore cannot reduce a living target below 1 HP.
  - `applyHit`, `makeUnit`, and `simulateMatch` now model page bleed for Skeleton and Hunchback, and tick statuses in the page order: poison, bleed, burn.
  - Added fixed-weather simulation support. `--weather clear|rain|snow|storm|fog` uses `js/weather.js` values for attack damage, movement, and storm wind. `--adjust hero:hp|dmg:0.9..1.1` measures a bounded in-memory proposal without modifying page data.
  - Added status-damage accounting to per-hero simulator statistics.
- `js/class_stats.js`: the default page-synchronized Skeleton and Hunchback profiles now contain their 2-damage, 2-turn non-lethal bleed effects.
- `scripts/test_sim_balance.js`: replaced the old lethal-poison expectation, added poison/bleed/burn 1-HP floor coverage, and covered weather and bounded CLI adjustments.
- `scripts/test_class_stats.js`: added page-status data assertions.
- `docs/balance_matrix_20261116.md` and `.json`: replaced the stale matrix with the four fresh 200-match-per-pairing results, flags, and measured bounded proposals.

No page file, `shared/heroes.json`, or persistent hero stat was changed.

## Verification commands run

```text
node scripts/test_class_stats.js
node scripts/test_sim_balance.js
node scripts/test_properties.js
node scripts/sim_balance.js --matches 200 --seed 7 --weather clear --json
node scripts/sim_balance.js --matches 200 --seed 7 --weather rain --json
node scripts/sim_balance.js --matches 200 --seed 7 --weather storm --json
node scripts/sim_balance.js --matches 200 --seed 7 --weather snow --json
node scripts/sim_balance.js --matches 200 --seed 7 --weather clear --adjust skeleton:dmg:0.9 --json
node scripts/sim_balance.js --matches 200 --seed 7 --weather snow --adjust wizard:dmg:0.9 --json
node scripts/sim_balance.js --matches 200 --seed 7 --weather clear --adjust knight:dmg:0.9 --json
node scripts/sim_balance.js --matches 200 --seed 7 --weather clear --adjust bride:dmg:1.1 --json
node scripts/sim_balance.js --matches 200 --seed 7 --weather rain --adjust hunchback:dmg:0.9 --json
node scripts/sim_balance.js --matches 200 --seed 7 --weather clear --adjust reaper:dmg:1.1 --json
node scripts/sim_balance.js --matches 200 --seed 7 --weather clear --adjust hag:dmg:0.9 --json
```

Last lines of successful test output:

```text
test_class_stats: all 14 tests passed
test_sim_balance: all 29 tests passed
test_properties: all 6 properties passed
```

Each matrix and proposal command completed and emitted its JSON result. Its exit code was 1 because the simulator correctly reports existing balance-band violations, not because execution failed.

## Could not verify

The required full JavaScript command was attempted after the changes:

```text
for f in scripts/test_*.js; do node "$f"; done
```

The command did not run because its permission request was not answered. Its complete output was:

```text
The permission request failed before it was answered, so this call did not run; the user did not reject it.
```

No full-suite pass is claimed. Main-line re-verification and `docs/kiro_verified.json` remain required.
