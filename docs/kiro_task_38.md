# Kiro task 38 - multi-party ARBITRATION of the current game balance (spawn sub-agents)

## Owner words (2026-11-09)
"Have Kiro start sub-agents to arbitrate the current game balance from several sides."

## What to do
Run a structured arbitration with SEPARATE sub-agents, then rule. If your environment lets you start sub-agents (a delegate or sub-agent tool), start at least FIVE independent ones, each with its own brief and role; do not tell one what another said until the rebuttal round. If you cannot start sub-agents, say so at the top of the report and write the roles as separate sections anyway, clearly marked "NOT independent" (do not pretend).

Roles (one sub-agent each):
1. ADVOCATE-SKELETON-WIZARD: argues the javelin (frost curse) and cannon classes are right-sized or too strong.
2. ADVOCATE-KNIGHT: argues for the bouncing-shield knight (die 1 to 6 collisions, damage split evenly), asks for the fairest buff.
3. ADVOCATE-CAT: argues for the cat-bat (one shuriken normally; the 5-shuriken volley is the ultimate).
4. NEW-PLAYER: a first-time human who cannot read wind well: cares about fun, fairness, comeback chances, match length.
5. AI-DIFFICULTY: argues about the opponent's accuracy (aim error 14 power units, about 33% hit chance in calm wind; it knows the exact wind and target) and what is a fair, readable difficulty ladder.
6. (optional) ULTIMATE-ECONOMY: argues about the 3-pip energy (3 hits, max 2 per match, ultimates deal 1.5 x per unit hit, trigger-then-follow-up structure).

## Evidence (read only)
docs/playtest_20261109.md and (not published) (65 scripted rounds; the bot knows the exact wind), (not published) (owner rules win), docs/roster_design.md, docs/ultimates_design.md, docs/playtest_fixes.md and docs/review_reconcile.md if present, index.html (HERO_PROFILES, throw and hit code, the knight bounce code, executeThrow, AI_AIM_ERROR, energy and ultUsed). Hit box: a unit is hit when |dx| <= 70 px and the projectile is inside a 190 px tall body box.

## Procedure (three rounds)
Round 1: each role writes an opening claim with numbers (what to change, by how much, why, evidence rows).
Round 2: each role rebuts the two claims that most conflict with its own.
Round 3: you act as the JUDGE: rule on each disputed number, give the single value you adopt, and state which role you sided with and why.

## Output
Write (not published) (Traditional Chinese summary for the owner at the top, tables below):
a. ONE adopted balance table for the 4 existing classes: HP, damage, special rule numbers (frost curse %, number of throws, bounce rule, die range, shuriken ultimate split), AI aim error, energy rule. Each number with the winning argument in one line.
b. DISSENTS: the arguments that lost and the condition under which they would be right.
c. A VERIFICATION PLAN the main line can run with the existing bot harness idea (fixed seed, N matches per pairing, class vs class win-rate band 40 to 60 percent, hits-to-kill 4 to 6, average match length): give the exact thresholds and the number of matches needed so the result is statistically meaningful.
d. The 5 questions only the owner can answer (one word each) with your recommended answer.
Do not touch index.html, assets/, js/, scripts/. Do not use git. Do not download or create images. Finish with a 6-line summary and say what you could not verify (including whether the sub-agents were really independent).
