# Kiro task 36 - REVIEW and reconcile the converged character / scene / design documents (review only)

## Why
The owner asked: "send it to Kiro to review". Three sub-agents and several Kiro design tasks produced documents that overlap and disagree. You are the reviewer: find contradictions, check every number against the code and the owner's confirmed rules, and give ONE reconciled decision list. Do not rewrite the other documents.

## Read (read only; the owner log overrides everything, newest rows at the bottom)
(not published), docs/converge_characters.md, docs/converge_scenes.md, docs/converge_crosscheck.md (if present), docs/roster_design.md, docs/ultimates_design.md, docs/richness_plan.md, docs/ui_reskin_plan.md, docs/airdrop_design.md, (not published), docs/game_mode.md, and index.html (HERO_PROFILES, throw and hit code, SCENES, start screen, drawTopHUD).
Owner rules to hold every document to: the 4-hit ultimate bar (each player counts own, max 2 per match); an ultimate = a trigger hit first, then follow-up strikes whose total is 1.5 x the class's normal attack, split evenly, the trigger hit's own damage is a normal hit; the grim reaper throws skulls (ultimate: after a skull hits, three scythe slashes); the ghost bride attacks with SOUND WAVES (an area effect); the hunchback is a bell-tower character; at least 6 classes, at most 4 v 4 on the field; attacks must differ in behaviour, not only damage; the knight's shield bounces (die 1 to 6 collisions, damage split evenly); the cat-bat throws a 5-shuriken scatter; the javelin applies a frost curse (-30% for the unit's next 2 throws); one character and one scene are chosen at the start and the character cannot be switched; screen stays clean; free CC0 sounds only; art made on Colab, never faked by code.

## Do exactly this
1. Write docs/review_reconcile.md (Traditional Chinese for the owner-facing summary, English allowed for tables):
   a. CONTRADICTIONS: a table, each row = topic, which documents disagree (quote each file with the value), what index.html really does, and the ONE value you recommend with a one-line reason. Cover at least: HP per class, damage numbers per class, heal amount (button +35 vs crate +30), turn timer, wind model and factor (client 72 px/s^2 vs MCP 67.5 push), the bride's attack (now sound wave: list every place that still says bouquet), the reaper's ultimate numbers, scene wind and hazards, ultimate bar rules, 4 v 4 turn flow, class count and names, file names of art assets.
   b. NUMBERS CHECK: recompute the time-to-kill (hits needed to take 100 HP) for each class from the final numbers and show it is within a band of 4 to 6 normal hits; flag classes outside it and give the smallest change that fixes it.
   c. RISKS: the 10 biggest risks to a working demo in the remaining time (the owner said about 20 days remain in the contest), ranked, each with a cheaper alternative.
   d. DECISIONS FOR THE OWNER: at most 8 yes/no or one-word questions, each with your recommended answer.
   e. BUILD ORDER: 8 to 12 small steps, in order, each with a pass condition the main line can verify by an automated test or a screenshot; steps that need new Colab art must say which asset names.
2. Do not edit any other file. Do not touch index.html, assets/, js/, scripts/. Do not use git. Do not download or create images.
3. Finish with a 6-line summary and say what you could not verify.
