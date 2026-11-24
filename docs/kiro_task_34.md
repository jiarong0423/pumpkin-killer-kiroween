# Kiro task 34 - make the game richer: a content-richness plan (design only)

## Owner words (2026-11-09)
After being told the game is "a playable 1 v 1 prototype": "What I want is something RICHER." Earlier: at least 6 classes, 4 v 4 on the field; attacks should differ; Halloween magic like a wizard school; screen must stay clean; ultimates (4-hit bar, max 2 per match) are NOT designed yet and must not be designed here; no extra spending; Colab makes the art.

## What exists now (read index.html, docs/game_mode.md, (not published), docs/airdrop_design.md, docs/sound_mapping.md, docs/wind_design.md)
1 v 1 duel, 4 classes (one unit per side), central black-iron fence (3 damage states), floating shield, wind that changes each round (physics 72 px/s^2 per unit, scene leaves/dust/fog), ghost airdrop with parachute crates and one supply slot (6 items designed), click menu above the head, thrown-path trail, real CC0 sounds and creature sprinkles, Colab-made UI plates and effect sprites.

## Do exactly this
1. Write docs/richness_plan.md: a ranked list of 12 to 16 content additions that make a match more varied and more fun WITHOUT making the screen messy. Cover at least these families, picking the best ideas in each: (a) battlefield variety (3 to 5 graveyard stages with different fence/terrain/background, destructible tombstones, hazards such as quicksand or ghost fire patches), (b) weather and time events (fog bank that hides the landing point, thunderstorm with lightning strikes, full moon boosting a class, rain changing wind), (c) status effects and combos (burn, poison tick, freeze or slow, curse, stun) and how thrown weapons apply them, (d) per-class passive traits (not ultimates), (e) neutral events and monsters (a wandering ghost that blocks shots, a bat swarm), (f) between-turn feedback (turn-start cue, kill-cam, combo text, damage numbers), (g) progression for a short demo (achievements, unlock order of classes, a daily seed), (h) game modes (1 v 1 duel, 4 v 4 skirmish, survival waves vs ghosts, practice range).
   For each item give: one-line fantasy, how it plays, what art it needs (Colab) and what sound (existing event or new), engine work (S/M/L), risk to the clean-screen rule, and a score for "wow per effort" (1 to 5). Mark clearly which items need the 4 v 4 roster (task 33) and which can be built now on the 1 v 1 engine.
2. End with: a recommended 3-step build order for the next 7 days, each step with a pass condition the main line can verify by an automated test or a screenshot, and a "demo script" of what a judge sees in the first 90 seconds that shows the richness.
3. Compare with 4 to 6 reference games' content richness (cite pages you read; mark snippet-only claims). Do not copy their art or names.
4. Write docs/richness_asset_requests.md: new Colab images for the top 8 items (name, size, one-sentence prompt, flat magenta background), highest impact first.
5. Do not touch index.html, assets/, js/, scripts/. Do not use git. Do not download or create images.
6. Finish with a 6-line summary and say what you could not verify.
