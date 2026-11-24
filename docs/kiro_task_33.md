# Kiro task 33 - roster of at least 6 classes, 4 vs 4 on the field, clearly different attacks (design only)

## Owner words (2026-11-09)
"In the end I think we need multiple characters." "At least six." "But at most 4 vs 4 on the field." "The characters' attack power is not very different from each other."

## Facts from the code (read index.html, HERO_PROFILES, executeThrow, hit code; scripts/mcp_game_server.py; docs/game_mode.md)
- Today 4 classes (skeleton javelin, pumpkin wizard cannon, cat-bat assassin shuriken, pumpkin knight thrown small shield) but only ONE unit per side is on the field; hero tabs just change which class you control. Damage and flight are nearly the same across classes (e.g. dmg 24 vs others close), so they play alike.
- Hit test: a projectile hits a unit if |dx| <= 70 px and it is inside the 190 px tall body box; the shield bar blocks by its own box; wind factor now 72 px/s^2 per wind unit; gravity 980; launch speed = power * 13.8.
- Ultimates are NOT designed and must not be designed here. Art is made on Colab (not by you). Sound events already exist per class (throw_spear, throw_shuriken, throw_cannon, throw_shield).

## Do exactly this
1. Write docs/roster_design.md:
   a. ROSTER: 6 to 8 classes (keep the existing 4, add 2 to 4 new ones that fit the Halloween graveyard: give name, one-line fantasy, weapon, silhouette idea for Colab, and why a player would pick it).
   b. ATTACK DIFFERENCE TABLE: one row per class with numbers the engine can use: damage, projectile speed multiplier, gravity multiplier (flat shot vs lob), hit-box size or splash radius, wind sensitivity multiplier, special property (pierce, bounce, delay, multi-hit, poison tick, shield break, heal-on-hit), charge time, and counter-play (what beats it). Make classes feel different in what they do, not only in damage: for each, the shot arc and what a player must do differently. State how you keep time-to-kill similar (target: a full-HP unit dies in about the same number of hits regardless of class, but through different routes) and cite the HP and damage numbers.
   c. 4 vs 4 RULES: choose 4 of the roster (duplicates allowed or not: recommend), line-up order, turn order (one unit acts per turn? one per side? all four?), turn timer, what happens when a unit dies, win condition, how the fence and floating shield work with 4 units per side, how wind and airdrops (docs/airdrop_design.md) apply, how many characters fit on the 1920 px field (spacing rule so units do not overlap), who the human controls (one at a time with a click on the unit; the others are agents), how long a full match takes (target under 8 minutes) and the number of turns that implies.
   d. ENGINE NEEDS: a list of what must change in index.html (units array instead of player/ai, per-class stats table, turn queue, hit tests, HUD and dock for 4 units) and in scripts/mcp_game_server.py and mcp_stdio_server.py (public state fields only, field names only), split into small steps in a sensible order, each with a checkable pass condition.
   e. BALANCE TEST PLAN: how the main line can check balance automatically (a script that plays class A vs class B with a fixed-seed bot over 200 matches, win-rate band 40 to 60 percent, plus a "same-damage-different-route" check). Give the pass bands.
   f. COMPARISON: briefly compare with how team turn-based artillery games (Worms-style team rosters, Gunbound-style distinct tank classes) differentiate units; cite pages you read, mark snippet-only claims.
2. Write docs/roster_asset_requests.md: new Colab art needed for the new classes (idle, windup, release, hit poses, portrait, projectile, 1 sentence prompt each, flat magenta background), highest priority first, at most 16 items. Do not repeat existing art.
3. Do not touch index.html, assets/, js/, scripts/. Do not use git. Do not download or create images.
4. Finish with a 6-line summary and say what you could not verify.
