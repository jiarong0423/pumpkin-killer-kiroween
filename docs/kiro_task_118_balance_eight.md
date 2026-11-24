# Kiro task 118 — balance table for eight heroes (scripts only; work block B21)

Owner goal (2026-11-15): 8 heroes. The simulator and the class table already cover seven classes (skeleton, wizard, cat-bat, knight, ghost bride, hunchback, reaper) from the 2026-11-09 design; the necromancer is new.

Read: `scripts/sim_balance.js`, `scripts/test_sim_balance.js`, `js/class_stats.js`, `scripts/test_class_stats.js`, `docs/class_stats_v2.md`, `docs/class_stats_judgement.md`, `docs/strength_test_20261109.md` (old result and its limits: the simulated bots knew exact wind and coordinates; they must not), `docs/ultimate_mapping.md` (normal damage `N` per class, INVENTED values marked), `docs/owner_decisions_20261110_agents_headless.md` (hit-rate target about 25 to 30 percent, one class per team).

Do, saving after each:
1. Add the necromancer to `js/class_stats.js` and the simulator (profile: purple ghost fire pushed forward, medium damage, burning effect as in the owner text; every number you choose is a named constant marked `PROVISIONAL, owner to confirm`). Keep the other seven unchanged.
2. Change the simulated bots so they see only what a public agent sees (a noisy position and wind, as in `scripts/agent_levels.py`: use its normal level knobs, imported or copied with a comment naming the source); report the hit rate per class.
3. Run an 8 x 8 round robin (at least 100 matches per pairing, fixed seeds) and write `docs/balance_eight_20261115.md` (plain markdown): win-rate matrix, mean rounds per match, mean damage per throw, the classes outside 40 to 60 percent average win rate, and one suggested change per outlier as a number (not applied). Keep the file under 80 lines.
4. Extend `scripts/test_sim_balance.js` and `scripts/test_class_stats.js` for the new class and the public-information bots; keep all existing tests passing. Run both tests and the simulation; paste the last lines. If the full round robin takes more than 3 minutes, reduce the match count and say so.

Touch only `js/class_stats.js`, `scripts/sim_balance.js`, `scripts/test_sim_balance.js`, `scripts/test_class_stats.js`, `docs/balance_eight_20261115.md` and the result file exactly named `docs/kiro_118_result_gpt-5.6-terra.md` (max 20 lines). Do not edit `index.html`. No network, no git.
