# Kiro task 51 — analyse the human-vs-AI matches and recommend AI / balance adjustments

Read first: docs/human_vs_ai_report.md (recorder's independent check), (not published) (owner rules, newest rows last), (not published)

Inputs (fill in by the main line when the 12-match run ends):
- (not published) (first 24-round run, AI hit 2/24, human 11/24)
- (not published) (12 matches, 93 rounds, final AI settings; 8 finished, 4 stopped at the 10-round cap; per round: my damage, AI damage)
- Summary: my hit rate 44 percent, AI 28 percent; average damage per hit 23.6 (me) / 23.7 (AI); finished matches last 6.6 rounds on average, player won 6 of 8. AI wizard hit 11/23 (48 percent) versus 5/20 to 5/29 for the other classes; wizard hits do 38 (crit 28 x 1.25 plus splash), skeleton / bat / knight 24 to 32.
- Owner asks: is the damage too high? Judge it against HP 85 to 120 and a target of about 8 to 12 rounds per match.

Questions:
1. Is the AI's hit rate (target about 30 percent with the random view) acceptable for a human player who hits about 40 to 45 percent? Recommend AI_AIM_ERROR, AI_VIEW_POS_NOISE, AI_VIEW_WIND_NOISE values, with numbers from the data.
2. The AI ignores the fence. Should it avoid it (a human sees the fence)? Recommend a fair rule that does not read exact coordinates.
3. Remaining exact-information points in aiAttackNow / the knight shield / dice-move decisions (report section 6): list the minimal fix for each, public information only.
4. Win rate per class pairing: which classes are over or under tuned against the data, and which numbers in js/class_stats.js to change.

5. Owner (2026-11-09): add a knight part where the shield is NOT thrown. Propose one or two readings (for example a held-up block turn, or a close shield bash that keeps the shield in hand with the 50 px knockback), with damage / block numbers, energy and ultimate interaction and fair-information limits. Do not pick for the owner; list both with a recommendation.

Rules: fair information only (what a human sees); do not edit index.html; write recommendations to docs/kiro_51_recommendations.md with the numbers and your reasoning; if you run scripts, use `python3 -B` / `node` and report the commands. The main line re-runs every test and applies changes itself.
