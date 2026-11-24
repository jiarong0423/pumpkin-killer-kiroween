# Kiro task 12 — playtest review (look at the frames, give opinions, record them)

You cannot run a browser, so you review a recorded scripted match: `(not published)` (read each image) and `docs/playtest/LOG.md` (what each frame shows
and what is missing from the canvas frames). Also read `docs/game_mode.md` (confirmed rules, owner wishes), `(not published)` (target look) and skim `index.html`.

## Do exactly this (documents only)
1. Write `docs/playtest/kiro_review.md` with these sections, in plain English, concrete and short:
   - **First impression (10 seconds)**: what a judge sees and understands, what confuses them.
   - **Readability**: character size vs scene, who is acting, what is the player supposed to do next, wind/aim/power information, HP visibility. Quote the frame names as evidence.
   - **Game feel**: feedback on throw, hit, block, move, dice, game over (what feels missing: sound, particles, screen shake, slow motion, numbers).
   - **Rules clarity**: do the frames make Move / Defend / one-throw-per-turn / the shield's valid paths understandable without reading text?
   - **Against the mockup**: the 8 biggest visual gaps (platforms, ghosts with crates, bottom bar with portrait, landing rings, ...), each with a size guess S/M/L.
   - **Empty space and composition**: the middle of the screen, where the eye goes, what to add or remove.
   - **Top 10 improvements** ranked by (impact / effort), each one line with an owner suggestion (main line, Kiro, Colab art).
   - **Things I could not judge** from canvas-only frames (the HTML dock and tutorial box are missing) and what recording would let you judge them.
2. Write `docs/playtest/RECORD.md`: a table with columns Date, Build (commit 8233fe3), Reviewer (Kiro CLI, model), Frames reviewed, Top 3 findings, Open questions for the owner.
3. Do NOT edit any other file. No git commands. Do not invent features that are not visible in the frames or documented.
4. Finish with a 6-line summary: the top 3 findings and the single most valuable change.
