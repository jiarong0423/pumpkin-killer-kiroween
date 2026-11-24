# Eight-hero balance matrix — 2026-11-16

## Method

Each condition ran this command once:

```text
node scripts/sim_balance.js --matches 200 --seed 7 --weather <clear|rain|storm|snow> --json
```

Each run contains 7,200 deterministic matches: 200 matches for every unordered pairing, including mirrors. Rows are the row hero's win rate against the column hero. Draws count as half a win. The command exits with code 1 because the reported balance bands are violated; all four simulations completed and emitted their JSON results.

The simulator table mirrors `shared/heroes.json`. It applies the page's non-lethal status ticks: poison 2 damage for 2 round starts, bleed 2 for 2, and burn 2 for 3. A status refresh retains the longer duration, and any tick leaves a living target with at least 1 HP. It also applies the fixed selected weather's page effect: rain and storm reduce direct attack damage to 90%, snow halves moves, and storm adds 1.5 to non-zero wind magnitude.

The complete machine-readable result, including the raw matrices, per-hero values, and proposal measurements, is [`balance_matrix_20261116.json`](balance_matrix_20261116.json).

## Summary

| Weather | Average rounds | First-mover range | Hero-average range | Flagged hero averages (outside 42–58%) |
|---|---:|---:|---:|---|
| Clear | 6.43 | 54.0–59.5% | 16.7–70.4% | skeleton 58.1%, knight 70.4%, bride 16.7%, reaper 38.6%, hag 58.2% |
| Rain | 7.16 | 54.0–61.0% | 21.2–73.8% | knight 73.8%, bride 21.2%, hunchback 63.0%, reaper 36.7% |
| Storm | 9.37 | 47.5–63.5% | 30.5–60.6% | skeleton 60.6%, bride 30.5%, hunchback 58.6% |
| Snow | 6.37 | 51.5–59.0% | 16.9–71.0% | skeleton 58.6%, wizard 56.4%, knight 71.0%, bride 16.9%, reaper 39.1% |

No simulation timed out. The full per-hero data below gives average win rate, hits to kill for winners, and mirror first-mover win rate.

| Weather | Hero | Average | Hits to kill | First mover |
|---|---|---:|---:|---:|
| Clear | skeleton | 58.1% | 4.43 | 57.5% |
| Clear | wizard | 56.3% | 3.57 | 55.5% |
| Clear | bat | 46.1% | 4.40 | 58.0% |
| Clear | knight | 70.4% | 5.13 | 55.0% |
| Clear | bride | 16.7% | 4.60 | 59.5% |
| Clear | hunchback | 55.6% | 4.83 | 57.0% |
| Clear | reaper | 38.6% | 4.23 | 59.5% |
| Clear | hag | 58.2% | 4.34 | 54.0% |
| Rain | skeleton | 57.6% | 5.06 | 56.5% |
| Rain | wizard | 52.4% | 3.73 | 55.5% |
| Rain | bat | 46.0% | 4.94 | 55.5% |
| Rain | knight | 73.8% | 5.41 | 56.0% |
| Rain | bride | 21.2% | 5.09 | 61.0% |
| Rain | hunchback | 63.0% | 5.20 | 54.0% |
| Rain | reaper | 36.7% | 4.86 | 59.0% |
| Rain | hag | 49.3% | 5.00 | 54.0% |
| Storm | skeleton | 60.6% | 5.08 | 56.5% |
| Storm | wizard | 51.9% | 3.77 | 59.0% |
| Storm | bat | 48.7% | 5.11 | 51.5% |
| Storm | knight | 54.9% | 5.95 | 58.0% |
| Storm | bride | 30.5% | 5.20 | 55.5% |
| Storm | hunchback | 58.6% | 5.26 | 52.0% |
| Storm | reaper | 42.9% | 4.95 | 47.5% |
| Storm | hag | 51.9% | 5.08 | 63.5% |
| Snow | skeleton | 58.6% | 4.43 | 58.0% |
| Snow | wizard | 56.4% | 3.57 | 55.5% |
| Snow | bat | 45.7% | 4.42 | 58.5% |
| Snow | knight | 71.0% | 5.13 | 51.5% |
| Snow | bride | 16.9% | 4.58 | 58.5% |
| Snow | hunchback | 54.3% | 4.81 | 53.5% |
| Snow | reaper | 39.1% | 4.24 | 59.0% |
| Snow | hag | 57.9% | 4.34 | 56.5% |

## Win-rate matrices

### Clear

| Row \ column | skeleton | wizard | bat | knight | bride | hunchback | reaper | hag |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| skeleton | — | 43.5 | 61.5 | 37.5 | 90.0 | 49.5 | 73.5 | 51.0 |
| wizard | 56.5 | — | 59.0 | 36.5 | 69.5 | 47.5 | 72.0 | 53.0 |
| bat | 38.5 | 41.0 | — | 28.0 | 89.0 | 42.5 | 50.5 | 33.0 |
| knight | 62.5 | 63.5 | 72.0 | — | 88.0 | 65.5 | 74.5 | 67.0 |
| bride | 10.0 | 30.5 | 11.0 | 12.0 | — | 21.5 | 21.0 | 11.0 |
| hunchback | 50.5 | 52.5 | 57.5 | 34.5 | 78.5 | — | 63.5 | 52.0 |
| reaper | 26.5 | 28.0 | 49.5 | 25.5 | 79.0 | 36.5 | — | 25.5 |
| hag | 49.0 | 47.0 | 67.0 | 33.0 | 89.0 | 48.0 | 74.5 | — |

### Rain

| Row \ column | skeleton | wizard | bat | knight | bride | hunchback | reaper | hag |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| skeleton | — | 48.5 | 57.5 | 33.5 | 82.5 | 46.0 | 69.0 | 66.0 |
| wizard | 51.5 | — | 50.0 | 36.5 | 74.0 | 42.0 | 60.0 | 53.0 |
| bat | 42.5 | 50.0 | — | 21.0 | 79.0 | 29.0 | 59.5 | 41.0 |
| knight | 66.5 | 63.5 | 79.0 | — | 91.5 | 64.0 | 84.5 | 67.5 |
| bride | 17.5 | 26.0 | 21.0 | 8.5 | — | 15.5 | 38.5 | 21.5 |
| hunchback | 54.0 | 58.0 | 71.0 | 36.0 | 84.5 | — | 77.5 | 60.0 |
| reaper | 31.0 | 40.0 | 40.5 | 15.5 | 61.5 | 22.5 | — | 46.0 |
| hag | 34.0 | 47.0 | 59.0 | 32.5 | 78.5 | 40.0 | 54.0 | — |

### Storm

| Row \ column | skeleton | wizard | bat | knight | bride | hunchback | reaper | hag |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| skeleton | — | 54.0 | 60.0 | 56.0 | 78.0 | 52.0 | 57.5 | 66.5 |
| wizard | 46.0 | — | 53.5 | 50.5 | 65.0 | 45.5 | 54.5 | 48.0 |
| bat | 40.0 | 46.5 | — | 39.5 | 75.5 | 32.5 | 61.5 | 45.5 |
| knight | 44.0 | 49.5 | 60.5 | — | 71.0 | 49.5 | 60.0 | 49.5 |
| bride | 22.0 | 35.0 | 24.5 | 29.0 | — | 33.5 | 42.5 | 27.0 |
| hunchback | 48.0 | 54.5 | 67.5 | 50.5 | 66.5 | — | 67.0 | 56.5 |
| reaper | 42.5 | 45.5 | 38.5 | 40.0 | 57.5 | 33.0 | — | 43.5 |
| hag | 33.5 | 52.0 | 54.5 | 50.5 | 73.0 | 43.5 | 56.5 | — |

### Snow

| Row \ column | skeleton | wizard | bat | knight | bride | hunchback | reaper | hag |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| skeleton | — | 44.0 | 61.5 | 39.5 | 92.5 | 49.5 | 73.0 | 50.0 |
| wizard | 56.0 | — | 60.0 | 37.5 | 67.0 | 49.0 | 71.5 | 54.0 |
| bat | 38.5 | 40.0 | — | 28.5 | 87.5 | 43.5 | 50.0 | 32.0 |
| knight | 60.5 | 62.5 | 71.5 | — | 89.0 | 70.0 | 74.5 | 69.0 |
| bride | 7.5 | 33.0 | 12.5 | 11.0 | — | 21.0 | 22.0 | 11.5 |
| hunchback | 50.5 | 51.0 | 56.5 | 30.0 | 79.0 | — | 61.0 | 52.0 |
| reaper | 27.0 | 28.5 | 50.0 | 25.5 | 78.0 | 39.0 | — | 26.0 |
| hag | 50.0 | 46.0 | 68.0 | 31.0 | 88.5 | 48.0 | 74.0 | — |

## Outside-band pairings

Pairings outside 40–60% are listed as `winner-rate%` for the named row hero.

- **Clear:** skeleton/bat 61.5%, skeleton/knight 37.5%, skeleton/bride 90.0%, skeleton/reaper 73.5%, wizard/knight 36.5%, wizard/bride 69.5%, wizard/reaper 72.0%, bat/knight 28.0%, bat/bride 89.0%, bat/hag 33.0%, knight/bride 88.0%, knight/hunchback 65.5%, knight/reaper 74.5%, knight/hag 67.0%, bride/hunchback 21.5%, bride/reaper 21.0%, bride/hag 11.0%, hunchback/reaper 63.5%, reaper/hag 25.5%.
- **Rain:** skeleton/knight 33.5%, skeleton/bride 82.5%, skeleton/reaper 69.0%, skeleton/hag 66.0%, wizard/knight 36.5%, wizard/bride 74.0%, bat/knight 21.0%, bat/bride 79.0%, bat/hunchback 29.0%, knight/bride 91.5%, knight/hunchback 64.0%, knight/reaper 84.5%, knight/hag 67.5%, bride/hunchback 15.5%, bride/reaper 38.5%, bride/hag 21.5%, hunchback/reaper 77.5%.
- **Storm:** skeleton/bride 78.0%, skeleton/hag 66.5%, wizard/bride 65.0%, bat/knight 39.5%, bat/bride 75.5%, bat/hunchback 32.5%, bat/reaper 61.5%, knight/bride 71.0%, bride/hunchback 33.5%, bride/hag 27.0%, hunchback/reaper 67.0%.
- **Snow:** skeleton/bat 61.5%, skeleton/knight 39.5%, skeleton/bride 92.5%, skeleton/reaper 73.0%, wizard/knight 37.5%, wizard/bride 67.0%, wizard/reaper 71.5%, bat/knight 28.5%, bat/bride 87.5%, bat/hag 32.0%, knight/bride 89.0%, knight/hunchback 70.0%, knight/reaper 74.5%, knight/hag 69.0%, bride/hunchback 21.0%, bride/reaper 22.0%, bride/hag 11.5%, hunchback/reaper 61.0%, reaper/hag 26.0%.

## Bounded proposals, not applied to the page

Each measurement used a cloned simulator table and `--adjust`, which accepts only a 0.9–1.1 multiplier. The page, `shared/heroes.json`, and the default simulator table remain unchanged. The table uses the representative condition in which the hero was outside 42–58%.

| Flagged hero | Proposal | Weather | Before average / hits | After average / hits |
|---|---|---|---:|---:|
| skeleton | Damage 22 → 19.8 (-10%) | Clear | 58.1% / 4.43 | 48.0% / 5.03 |
| wizard | Damage 30 → 27 (-10%) | Snow | 56.4% / 3.57 | 51.2% / 3.75 |
| knight | Damage 23 → 20.7 (-10%) | Clear | 70.4% / 5.13 | 64.1% / 5.38 |
| bride | Damage 28 → 30.8 (+10%) | Clear | 16.7% / 4.60 | 21.6% / 4.39 |
| hunchback | Damage 21 → 18.9 (-10%) | Rain | 63.0% / 5.20 | 57.4% / 5.42 |
| reaper | Damage 22 → 24.2 (+10%) | Clear | 38.6% / 4.23 | 44.0% / 3.99 |
| hag | Damage 24 → 21.6 (-10%) | Clear | 58.2% / 4.34 | 44.4% / 4.94 |

The maximum allowed number-only adjustment improves the individual average in each measured condition but does not cure the broad pairing imbalance. Knight and bride remain the largest outliers after their bounded changes. Treat these as owner-review proposals, not balance changes.

## Verification

```text
node scripts/test_class_stats.js
node scripts/test_sim_balance.js
for f in scripts/test_*.js; do node "$f"; done
```

The first two focused tests passed after the code change. The full JavaScript suite result is recorded in `docs/kiro_187_result.md`.
