# Kiro task 55 — retune the strength of every class (owner: opponents die in two or three hits)

Read: (not published) (newest rows last), docs/class_stats_v2.md, docs/kiro_51_recommendations.md (sections 2 and 5), js/class_stats.js (CURRENT = what index.html holds), scripts/sim_balance.js, (not published) (12 real matches with the current AI) and (not published) (the earlier AI).

Owner complaint (2026-11-09): "the cat is too strong; the opponent dies in two or three hits". Target (docs/class_stats_v2.md): 4 to 6 hits to kill, 8 to 12 rounds per match, and no class more than about 15 percent from the roster mean in the power table.

Changes the main line already applied (take them as given):
- Head-shot crit (x1.25 and 7 s stun) now needs the contact in the top quarter AND within 35 px of the unit centre (was the whole top face: 82 percent of hits were crits).
- Cat-bat damage 26 -> 22. POISON_DMG 3 -> 2. AI_AIM_ERROR 6 with the no-simulator AI.
- Current values: HP skeleton 100, wizard 85, bat 90, knight 120, bride 75, hunchback 130, reaper 110 (the reaper is now the fire-throwing necromancer, see task 53); damage skeleton 24, wizard 28, bat 22, knight 30, bride 27, hunchback 20 (see index.html and js/class_stats.js).

Do:
1. Recompute hits-to-kill per class (crit share about 27 percent now, ticks included, 5-shuriken cat volley and head crit separately) and the expected rounds per match at a 40 percent human hit rate and a 30 percent AI hit rate.
2. Propose the new HP and damage for every class, including the three not yet playable, so that all land in the target. Say which classes you keep unchanged and why.
3. Give an honest list of what you could not verify (you cannot run the page).
Write (not published) with a table of old and new numbers. Do not edit index.html or js. Use `python3 -B` / `node` for any scripts.
