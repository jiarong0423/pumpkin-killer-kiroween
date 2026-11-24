# Kiro task 56 — re-check the strength retune against the NEW measured data

Read: (not published) (your earlier answer), (not published) (12 real matches with the CURRENT settings, 126 rounds), (not published) (newest rows last).

New facts (measured in the real page, not hand arithmetic):
- Human hit rate 33.3 percent, AI hit rate 16.7 percent (your model assumed 40 and 30). Damage per hit about 22 (human) and 24 (AI).
- 8 of 12 matches finished, mean 8.8 rounds; 4 reached the 14-round cap; overall mean 10.5. Human won 6 of 8 finished.
- Damage per round as the human: wizard 11.9, knight 7.5, skeleton 5.9, bat 5.7. As the AI: skeleton 7.2, wizard 5.5, bat 4.4, knight 0.6 (2 hits in 36 rounds; the AI knight may spend many turns on the floating shield, unverified).
- Already applied: head crit needs the top quarter AND within 35 px of the centre; cat damage 22; poison 2; AI without a ballistic simulator, aim error now 3 (was 6); wizard damage now 24 (was 28).
- Owner direction: do NOT apply the across-the-board damage cuts; raise the AI to about 25 percent hit rate; treat the wizard alone.

Do:
1. Re-run your power-model with the measured hit rates (33 and 17, and the target 40 and 25) and say which classes are really out of band now.
2. Is wizard 24 right, or 22 or 26? Give hits-to-kill and the match-length effect.
3. Estimate what aim error gives an AI hit rate of about 25 percent for THIS no-simulator AI (use (not published) notes in docs if present, and the numbers in scripts/sim_ai_nosim.js: exact error 16 gave 27 percent, prior-based error 8 gave 25 percent in the simulation but the real page gave 22.5 percent at 8 and 16.7 percent at 6; explain the gap).
4. Why does the AI knight hit so rarely? Read index.html (triggerAITurn) and say how many of its turns go to the shield and what a fair fix is.
5. List what you could not verify.
Write (not published) Do not edit index.html or js. Use `python3 -B` / `node` for scripts.
