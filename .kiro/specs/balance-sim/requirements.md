# Requirements: balance simulator

Module and command line: `scripts/sim_balance.js` (`SimBalance`). It plays 1 v 1 matches headlessly with the physics of `index.html` and a seeded bot, to check the class numbers of `docs/class_stats_judgement.md`. Tests: `scripts/test_sim_balance.js`. "Round" = the left side throws, then the right side throws.

## Physics (same as index.html)

1. The simulator shall use a fixed step of 1/60 s, gravity 980, wind acceleration 72 px/s^2 per wind unit (`vx += wind x 72 x dt`), launch speed `power x 13.8` times the class `speedScale`, ground y 860, fence x 960 / width 130 / height 250 with 100 HP and 15 damage per hit, a hit box of `|dx| <= half width` (70; bride 105) and a 190 px body, and the integration order of `updatePhysics` (velocity, then position; fence, unit, ground in that order). (tests: "constants equal index.html and shared/constants.json", "launch point per class ...", "simulateLandingX ...")
2. Wind shall be rerolled every round, uniform in [-4, 4] with one decimal. Start positions shall be drawn as `randomizePositions` does (left 220..620, right 1280..1680); moves are limited to 160..850 and 1070..1760 and use the 36 px die. (test: "constants equal index.html ...")
3. The left side shall act first in each round, one throw per unit per turn, and a knockout shall end the match at once. (tests: "the match always ends ...", "knockout ends the match at once ...")

## Rules played

4. Frost curse: a skeleton hit that does not kill shall make the victim weak for 2 throws at the class cut (20% recommended, 30% provisional). (test: "frost curse ...")
5. Reaper: a hit on a target at 30% HP or less shall deal x1.5. (test: "reaper execute ...")
6. Hunchback: a hit that does not kill shall push the target away from the thrower by the class knockback, kept inside the move range. (test: "hunchback knockback ...")
7. Bride: the wave shall hurt one unit, with `waveDamage` of the distance measured at the first touch of the box (`waveRule: 'first_contact'`, default, as in the judgement) or at body-centre height (`'centre'`, a proposal). The provisional bouquet shall burst on landing and deal 12 to a unit within 90 px. (tests: "bride wave ...", "provisional bouquet ...")
8. Knight, `shieldRule: 'current'` (default): every collision with unit, ground or fence uses one of the die's 1..6 collisions; a unit contact deals an even share and hops back; the numbers of `index.html`. `shieldRule: 'A'` (`docs/playtest_fixes.md` Fix 1): the die sets the number of ticks on the same unit, 0.12 s apart, summing to the total; one free ground skip; the fence ends the shield. (tests: "knight, current rule ...", "knight, rule A ...")
9. Cat: the normal throw is one shuriken. When the ledger allows it, the bot may use the 5-shuriken volley (fan -8, -4, 0, +4, +8 degrees, extra four with speed x0.95..1.05, each `1.5 x normal / 5`); it is spent at release, hit or miss, and gives no pip. The bot uses it when it can finish the enemy or has held it for 3 turns. Other classes' ultimates are not played; their pips are counted. (tests: "cat volley ...", "the cat uses its volley at most twice ...")
10. One throw shall give at most one pip, through `Ultimate.createLedger`. (tests: "a point weapon deals its damage once ...", "cat volley ...")

## The bot

11. The bot shall solve the power for the true wind and the true target x with the class's own integrator and add a uniform error of +-`aimError` power units (default 9, clamped to 30..100). If full power falls short it shall roll the move die once toward the enemy and solve again. (tests: "solvePower ...", "the bot makes bounded mistakes ...")
12. With `aimError` 0, 9 and 30 the hit rate of a mirror match shall fall in that order, the 0 case above 70% and the default case between 35% and 70% (index.html comment: error 9 gives 52%). (test: "the bot makes bounded mistakes ...")

## Determinism and ending

13. `simulateMatch` and `runPairings` shall be deterministic for a fixed seed: the same options give the same result; a different seed gives a different one; `Math.random` and `Date` shall not be used. (test: "a fixed seed gives the same match ...")
14. No result shall contain NaN or Infinity; HP shall stay in 0..maxHp; the winner of a knockout has HP left and the loser none. (test: "no NaN anywhere ...")
15. Every match shall end, by knockout or at `maxRounds` (timeout, decided by HP share). The damage a side dealt shall equal the HP the other side lost. (test: "the match always ends ...")
16. Unknown class keys shall throw `two class keys`. (same test)

## Pairings

17. `runPairings({ classes, matchesPerPairing, seed })` shall play every unordered pair and every class against itself, alternating the left side match by match, and return the win-rate matrix, the average rounds per pairing and overall, hits to kill per class, damage per hitting throw, per-class throw statistics, class averages, first-mover win rate of the mirror match, the list of violations and `pass`. (test: "runPairings: win rates add up ...")
18. The matrix shall be symmetric in totals: `rate[i][j] + rate[j][i] = 1`, `wins[i][j] + wins[j][i] = matchesPerPairing`, the diagonal is 0.5, the rounds matrix is symmetric, and the class averages add up to 3.5 for seven classes. (same test)
19. The bands shall be those of `docs/class_stats_judgement.md` section 8: a pairing outside 40 to 60% and a class average outside 45 to 55% (with more than two classes) is a violation; `pass` is true only without violations. The match length band 8 to 14 rounds is reported as `lengthOk` and does not decide `pass`. (tests: "runPairings: a lopsided table ...", "runPairings: the sides alternate ...")
20. Hits to kill measured in play shall be within 1.0 of the hand table for every class. (test: "hits to kill from play are near the hand table")

## Command line

21. `node scripts/sim_balance.js --matches N --seed S` shall print the matrix, the length matrix, the class table and the bands, and set the exit code to 1 for a violated band, 0 otherwise, 2 for a bad option. Options: `--table recommended|provisional`, `--aim-error`, `--max-rounds`, `--classes a,b`, `--shield-rule current|A`, `--wave-rule first_contact|centre`, `--json`. (test: "command line ...")

## Out of scope (stated)

22. No sky shield, airdrop, heal, skills, 4 v 4, or ultimates other than the cat's. The bot knows the wind and the target exactly. These make the numbers an upper bound of how much skill the game rewards, not a prediction of human results.
