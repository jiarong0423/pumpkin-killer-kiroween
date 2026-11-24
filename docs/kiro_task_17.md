# Kiro task 17 - gameplay experience + particle effects design (read and write files only)

## Why
The owner decided on 2026-11-09 that Kiro owns the DESIGN of the play experience and of the particle / visual effects. The main line (Claude Code) builds what you propose
after the owner approves, and re-tests everything. You cannot play the game or open a browser: you work from the files and screenshots listed below, and you must
mark every claim that depends on seeing the game as "unverified".

## Do exactly this
1. Read: `docs/game_mode.md` (confirmed rules, owner wishes), `docs/ROLES.md`, `(not published)`, `(not published)` if it exists,
   `docs/playtest/LOG.md` and the images in `(not published)` (look at 4-5 of them), `(not published)`, `js/particles.js` (preset names and options only),
   `docs/mcp_agent_protocol.md`, `.kiro/steering/*.md`.
2. Write `docs/experience_design.md` with these sections:
   a. **Turn flow as the player lives it**: one round from "my turn" to "result", beat by beat, with what the player sees, hears and decides at each beat (aim by pointer,
      press anywhere to charge, release to throw; move with a die; the guard may place the floating shield instead of attacking).
   b. **Feedback table ("game feel")**: for every event (charge, release, flight, hit, block, miss/ground, KO, poison, shield placed, ultimate ready, round start/end) give the effect,
      the sound idea, the screen reaction (shake, hit-stop, flash), and the duration in ms. Keep durations short; hit-stop at most 80 ms.
   c. **Particle and visual effects design**: for each event the existing preset to use (names from `js/particles.js`) or a NEW preset to build, with the look in words, colour palette
      (Halloween magic: ghost-fire green/cyan, violet, gold stardust, orange pumpkin glow), count per call, and a CLEAN-SCREEN BUDGET (max particles on screen, max effects per second, characters
      and the HUD must never be hidden). Say which effects are weapon effects (spear, shuriken, cannonball, thrown shield) and which are face/body micro-motions.
   d. **Onboarding**: the first 60 seconds for a new player (the 3-step hint replacing the permanent tutorial box), what is taught by doing, what is never explained.
   e. **Pacing and difficulty**: round length (12 s turn timer), how the agent opponent gets harder (it learns from public history), comeback mechanics, how long a match should last.
   f. **Per-class feel**: skeleton javelin (real hand, windup, overhead release), cat shuriken (assassin: low crouch, quick flick, three shuriken fanned), pumpkin wizard (cannon recoil),
      pumpkin guard (thrown small shield spinning sideways, floating shield). One paragraph each: what makes it satisfying.
   g. **Demo moments**: the 3 most impressive 5-second moments to put in the 3-minute video, and what must be on screen in each.
   h. **Open questions for the owner**, each with your recommended answer, so the owner can answer with one word.
3. Write the spec `.kiro/specs/gameplay-experience/` (requirements in EARS form, design, tasks). Tasks must be small and testable; the effect budget must be a number a test can check.
4. Do not touch `index.html`, `assets/`, `scripts/`, `js/`. Do not use git. Do not create images.
5. Finish with a 6-line summary and say what you could not verify.

## Facts and constraints
- Owner feedback to respect: the screen must not be messy; effects must feel polished ("have texture"); Halloween magic like a wizard-school spell; weapon effects such as a glowing spearhead.
- Confirmed already (do not redesign): the 4 classes and their weapons; the guard is the only class with the floating shield; moving does not use the turn (one move, then one attack);
  the cat throws shuriken from a belt bag; the knight throws a small shield; ultimates unlock after 4 successful hits (max 2 per match); art is generated on Colab, not by Kiro.
- Desktop first; the phone landscape version comes later (touch: press and drag to aim).
- Current effects in the game (built by the main line): weapon trails as soft ribbons, glowing spearhead, rune halo on release, gold-violet stardust, muzzle flash, impact burst, hit sparks,
  ricochet sparks, landing dust, KO wisps, charge aura, jack-o'-lantern face glow, skeleton eye flame. Effects scale 1.25x, particle cap 500.
