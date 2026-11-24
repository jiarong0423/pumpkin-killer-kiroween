# Design: class stats

## What it is

`js/class_stats.js` is data plus the hand model of `docs/class_stats_judgement.md`. It has two tables with the same shape, so any function takes `{ table }`:

| Table | Meaning |
|---|---|
| `CLASSES` (= `RECOMMENDED`) | The numbers recommended in the judgement |
| `PROVISIONAL` | What `index.html` holds today, plus the invented numbers of `docs/converge_characters.md` for the three classes that are not in the game yet |

## Fields

`hp`, `dmg` (the knight's is the TOTAL over its collisions), `dTyp` (what the hits-to-kill table uses: equals `dmg` except the bride, 22.4 = mean of her falloff, and the knight, 20 = the hand estimate of what the bounces really deal), `hitHalfWidth` (70; bride 105), `speedScale` (launch speed factor), `gravityScale`, `windScale`, `launch` (hand offset: forward and up, as in `executeThrow`), `special` (frost, volley, bounce, wave, knockback, execute, splash), `ultKind`, `ultStrikes`.

## The hand model (judgement section 2)

- Landing error uniform in +-A px. Hit chance of a point weapon P = halfWidth / A (at most 1). `bot` A = 100, `ai` A = 210.
- Fence and wind keep 0.88 of the throws (bot only; the judgement applies no factor to the knight).
- Power = HP x expected damage. Equal power means equal win chances.
- Skeleton: the curse covers `1 - (1 - P)^2` of the victim's throws and cuts them by `cut`, so the skeleton's own damage counts for `1 / (1 - cut x cover)`.
- Reaper: `1 + 0.5 x 0.22` (the 22% is a guess in the judgement).
- Knight: judgement tables for the die: direct hit `[30, 24.1, 20.5, 17.6, 15.4, 13.7]`, ground-first `[0, 15, 12, 9.8, 7.8, 6.8]` (total 30). The playtest-measured end of the range is 4.8 (ai) and 10.1 (bot).

## Decisions

| Question | Choice | Why |
|---|---|---|
| Throw on unknown class | `throw new Error('Unknown class: ...')` | A wrong key is a programming error, like an unknown particle preset. |
| Rounding of hits to kill | `ceil(x - 1e-9)` | 90 / 30 and 110 / 22 are exact; floating error must not add a hit. |
| What `validate` calls a violation | Hard cells under 3 / over 8, row means outside 4 to 6, fewer than 80% of cells in 4 to 6 | The brief says "typical 4 to 6, never below 3 or above 8". The 80% and the row mean are my reading of "typical". The recommended table has 91.8% and row means 4.14 to 5.43. |
| Reaper execute in the matrix | Off by default, `execute: true` plays it | The judgement table is without it (it mentions the 6 to 5 change only as a note). |
| `windScale` 1 for all | Yes | The judgement says "no separate wind factor". The provisional hunchback keeps the invented 0.6 so the difference shows. |
| Launch offsets of bride, hunchback, reaper | The default hand (58, 110) | No art and no hand position exist for them. |

## Findings kept visible in code and tests

- At 30 total damage the knight can kill a full-HP bride (75 HP) with trigger plus follow-up, 30 + 45 = 75 (`oneShotRisks`). `docs/ultimate_mapping.md` used 22 for the knight and claimed no one-shot.
- The provisional table breaks the band: the bride with 12 damage needs 8 to 10 hits, 10 against the knight.

## Not covered

Nothing here moves a projectile. Hit chances are the hand model; `scripts/sim_balance.js` plays the real physics, and its results differ from this model for the bride (see `docs/implementation_report.md`).
