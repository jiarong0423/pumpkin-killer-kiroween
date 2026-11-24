# Kiro task 91 — phase 2: plan the opening flow as a spec, starting from the concept images

Read: `docs/phase2/OWNER_STEPS.md`, `docs/phase2/CONCEPTS.md`, every image in `(not published)`, `docs/art_style_guide.md`, `docs/owner_decisions_20261110_agents_headless.md` (decided rules, never reopen), `docs/kiro_queue_20261110.md` (items A1, coin toss, seats), `.kiro/steering/*.md`, `.kiro/specs/release-package/` (the file style you used), and the opening-screen code in `index.html` (find it with grep for the start screen, coin toss and seat functions; do not edit it).

FIRST CHECK: if `(not published)` has no image, or `docs/phase2/CONCEPTS.md` does not exist, STOP. Write only `(not published)` saying so. Do not invent concepts and do not describe images you have not opened.

Otherwise write, saving each file as soon as it is written, in `(not published)`:
1. `requirements.md` — EARS acceptance criteria per screen, taken from what the concept images actually show (name the image each criterion comes from) plus the decided rules: coin toss decides first turn (owner picks heads or tails before the seed is generated), seats are agent / human / built-in AI, 4 vs 4 is the target but the prototype is 1 vs 1 today, names accept Chinese and English letters only, max 8.
2. `design.md` — components, data flow between the three screens and the game, which existing code is reused and which is replaced, how it is tested (property tests where they fit), and the assets still needed (list file names; art is made by the owner, not by code).
3. `tasks.md` — a checklist of small tasks, each with files, a verify command and the requirement it satisfies; an `index.html` task is always alone (one at a time). Tick nothing: no task has run.

Use today's real date in every file header. No back-dating, no claim about who made the concept images beyond what `CONCEPTS.md` says.

Then write `(not published)` (max 30 lines): paths, the images you opened, what you did not verify. Touch no other file. No network, no git.
