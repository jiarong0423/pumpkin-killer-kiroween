# Eight-hero balance run — 2026-11-15

Command: `node scripts/sim_balance.js --matches 100 --seed 20261115 --agent-level normal`

This is a fixed-seed 8 × 8 round robin: 100 matches for every unordered pairing, including mirrors, for 3,600 matches. The simulator completed within three minutes. Bots use the `normal` public-information noise values copied from `scripts/agent_levels.py`: target x ±80 px, wind ±0.8, and post-choice power ±6. They do not use exact target position or wind.

## Win rate matrix

Each cell is the row hero's win rate against the column hero. Mirror cells are omitted.

| row \ column | skeleton | wizard | bat | knight | bride | hunchback | reaper | necromancer |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| skeleton | — | 65 | 67 | 80 | 82 | 61 | 52 | 57 |
| wizard | 35 | — | 47 | 56 | 75 | 55 | 44 | 50 |
| bat | 33 | 53 | — | 59 | 81 | 45 | 43 | 38 |
| knight | 20 | 44 | 41 | — | 67 | 27 | 25 | 22 |
| bride | 18 | 25 | 19 | 33 | — | 20 | 19 | 12 |
| hunchback | 39 | 45 | 55 | 73 | 80 | — | 45 | 30 |
| reaper | 48 | 56 | 57 | 75 | 81 | 55 | — | 53 |
| necromancer | 43 | 50 | 62 | 78 | 88 | 70 | 47 | — |

Mean match length was **7.23 rounds**. No match timed out.

## Per-class results

| class | average win | mean damage / throw | hit rate | burn damage |
|---|---:|---:|---:|---:|
| skeleton | 66.3% | 12.7 | 58.7% | 0.0 |
| wizard | 51.7% | 15.2 | 60.2% | 0.0 |
| bat | 50.3% | 14.2 | 60.6% | 0.0 |
| knight | 35.1% | 9.5 | 59.0% | 0.0 |
| bride | 20.9% | 12.2 | 71.7% | 0.0 |
| hunchback | 52.4% | 9.2 | 48.7% | 0.0 |
| reaper | 60.7% | 12.6 | 58.8% | 0.0 |
| necromancer | 62.6% | 13.7 | 59.5% | 8,688.8 |

## Outliers and un-applied numeric proposals

Average-win target is 40–60%. These changes are proposals only; this run changed no balance number.

| outlier | result | one suggested numeric change |
|---|---:|---|
| skeleton | 66.3% | frost cut 20% → 10% |
| knight | 35.1% | shield total damage 30 → 34 |
| bride | 20.9% | HP 75 → 90 |
| reaper | 60.7% | execute multiplier 1.5 → 1.3 |
| necromancer | 62.6% | burn turns 3 → 2 |

The report does not apply these proposals. The existing seven profiles remain unchanged; all necromancer values are provisional pending owner confirmation.
