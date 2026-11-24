# Requirements: class stats

Module: `js/class_stats.js` (`ClassStats`). Numbers come from `docs/class_stats_judgement.md` (a hand model, never played; `scripts/sim_balance.js` is the check that plays it). The "provisional" table is what `index.html` holds today. Every requirement names its test in `scripts/test_class_stats.js`.

## The table

1. `CLASSES` shall hold exactly the seven keys `skeleton, wizard, bat, knight, bride, hunchback, reaper`, in this order, and each class shall have `hp, dmg, dTyp, hitHalfWidth, speedScale, gravityScale, windScale, launch, special`. (test: "seven classes ...", "the recommended numbers ...")
2. The recommended values shall be: HP / damage 100 / 24 (skeleton), 85 / 28 (wizard), 90 / 26 (bat), 120 / 30 total (knight), 75 / 27 centre (bride), 130 / 20 (hunchback), 110 / 22 (reaper); frost curse 20% for 2 throws; bride hit half width 105 px, speed 0.9, full damage within 40 px falling to 45% at the edge; hunchback speed 0.8 and knockback 50 px; reaper execute x1.5 at 30% HP; gravity and wind multipliers 1 for every class. (test: "the recommended numbers ...")
3. Every HP shall differ from every other, and every normal damage shall differ from every other. (test: "seven classes, every HP different ...")
4. `CLASSES` and `PROVISIONAL` shall be deep-frozen; `cloneTable` shall return an editable copy. (test: "the tables are frozen ...")
5. `PROVISIONAL` shall equal `index.html` for HP, damage and weapon of skeleton, wizard, bat and knight, the frost multiplier 0.7 and length 2, the volley share and fan, and `WIND_ACCEL = 72`; if `index.html` drifts the test shall fail. The bride, hunchback and reaper shall be marked as invented values. (test: "fixture: PROVISIONAL equals what index.html holds today ...")

## Hits to kill and the band

6. `hitsToKill(attacker, defender)` shall return `ceil(defender.hp / attacker.dTyp)` with a 1e-9 tolerance, so 90 / 30 and 110 / 22 are exactly 3 and 5. Option `damage: 'nominal'` shall use `dmg`; option `execute: true` shall play the reaper's execute rule hit by hit and change no other class. An unknown key shall throw `Unknown class`. (test: "hitsToKill: exact divisions ...")
7. `matrix()` shall return the 7 x 7 table (row = attacker, column = defender) and for the recommended table it shall equal the table of `docs/class_stats_judgement.md` section 5 cell for cell: minimum 3, maximum 7, 45 of 49 cells in 4 to 6, mean 238 / 49. (test: "matrix() is the 7 x 7 table ...")
8. `validate()` shall return the list of violations of the band: a cell under 3 (`below_min`) or over 8 (`above_max`), a class whose row mean leaves 4 to 6 (`row_mean`), fewer than 80% of the cells in 4 to 6 (`typical_share`). Each item shall have `kind`, `attacker`, `defender`, `hits`, `message`. For the recommended table the list shall be empty. (tests: "validate(): the recommended table ...", "validate(): finds cells ...")

## Expected damage

9. `expectedDamage(attacker, assumptions)` shall return expected HP damage of one throw at one standing target with `P x damage-when-hit x fence factor x class multiplier`, where P = half width / A (at most 1), A = 100 px and fence factor 0.88 for `aim: 'bot'`, A = 210 px and fence factor 1 for `aim: 'ai'`. (test: "expectedDamage reproduces the judgement table ...")
10. The class multipliers shall be: skeleton `1 / (1 - cut x (1 - (1 - P)^2))`; reaper `1 + 0.5 x 0.22`; bride damage-when-hit = mean of her falloff over the hit zone. (same test; test: "the two problems the judgement found ...")
11. The knight's expected damage shall include the die (1 to 6, even odds) and the ground-skip rule: rule `current` uses the hand tables of judgement section 3 scaled by total / 30, with basis `hand`, `measured` or `mid`; rule `A` (`docs/playtest_fixes.md` Fix 1) deals the full total on a unit contact and reaches from a ground skip with chance 0.4. `expectedDamageDetail` shall expose the per-die values. (test: "the knight: the die 1 to 6 and the ground skip are inside expectedDamage")
12. `powerTable()` shall give HP x expected damage per class and the mean, about 849 (aim `ai`) and 1571 (aim `bot`) for the recommended table. (test: "power = HP x expected damage ...")
13. Expected damage shall be finite and not rise when the aim spread widens, for any class and any (also invalid) assumptions. (test: "expectedDamage: wider aim spread ...")

## Comparison and ultimates

14. `compareTables(base, next)` shall list the changed fields and the changed matrix cells. From provisional to recommended: the wizard and knight shall be unchanged, the skeleton shall change only its frost curse, the bat only `dmg` and `dTyp`; the provisional table shall break the band and the recommended shall not. (test: "difference provisional -> recommended ...")
15. `ultimatePerUnit(key)` shall be `1.5 x dmg` rounded to 0.1; `ultimateOneTarget(key)` shall add the trigger hit (not for the bat); `oneShotRisks()` shall list pairs where one ultimate on a full-HP unit kills it. For the recommended table the list shall be exactly knight against bride (75 against 75 HP). (test: "ultimate numbers ...")
16. The module shall be deterministic and shall not call `Math.random` or `Date`, and its calls shall not change the tables. (test: "deterministic and pure ...")
