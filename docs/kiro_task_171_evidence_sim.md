# Kiro task 171 — gather balance and rule EVIDENCE from the repository itself (read only; one report file)

Owner 2026-11-16: collect evidence in parallel. Do not change any code or data. Sources are local only (no web).

Question set (answer each with file, line or measured number; say "not found" instead of guessing):
1. Every place `index.html` and `js/*.js` use `Math.random` (the determinism gap): list function name, what it decides (wind, dice, supply drop, knight bounce die, nun electric stun pick, AI aim noise, particles), and whether it affects game state or only visuals. Output a table with a column "state or visual".
2. Every rule a player-only control has that the built-in opponent does not (heal 2 x 35 free, double shot, heavy 1.5 x, move dice choice, shield placing): file and line, and what the opponent does instead.
3. For each of the 8 heroes: normal attack effect, status, ultimate (name, damage factor, number of hits, whether it can be blocked, whether it can miss) from `index.html`, `js/ultimate_fx.js`, `js/nun_ult.js`, `js/boomerang.js`, `js/sound_wave.js`, `js/knight_ult.js`, `js/knockback.js`. One table row per hero. Mark any value that differs between two files.
4. Weather and wind: for every rule that uses `Weather.applyAttack`, `moveMult`, `windBonus` or `effWind`, list the code path; list every damage source that does NOT apply the weather multiplier (bride swarm, wizard blast, boomerang return, status damage, knight bounces).
5. Evidence of tests that pin balance numbers: for each hero number (hp, damage, ultimate factor, hit width) list the test files that assert it, so a later change knows what to update.
6. Playtest evidence: read `docs/playtest_round1_20261116.md`, `docs/playtest_round2_20261116.md` and `docs/PLAYTEST_REVIEW_20261116.md`; extract every measured number into one table (match, rounds, hp left, hits). Note which numbers came from the harness before it set the turn to busy (round 1 and the first run of round 2 are affected).

Write ONE file: `docs/evidence_report_20261116.md`. Touch nothing else. Final message: the file path and the three most surprising findings in three lines.
