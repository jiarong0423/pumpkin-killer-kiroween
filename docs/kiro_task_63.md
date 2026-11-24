# Kiro task 63 — write prompts for OpenAI's image model (image2) that the owner will paste by hand

Owner request (2026-11-10): "have gpt-5.6-terra write the image2 prompts". image2 = OpenAI's image model (the owner's ChatGPT, a reference picture is ATTACHED to the message). The owner pastes your text and the reference picture into ChatGPT, then downloads the result. Nobody calls an API.

Why: the other model (Qwen edit) redraws the face in every frame and copies the idle picture. A model that makes ONE picture with the whole set in it keeps the face, the colours and the size identical across the frames. So the unit of work is a SPRITE SHEET, not one frame.

Read: docs/pose_spec.md (the standard), (not published) and agent_b_review.json (a canonical FACE and ITEM description per class), (not published), (not published) (newest rows last: direction LEFT, the same hand, the item disappears at the throw and returns next turn, the necromancer's single purple flame, the hunchback's two-handed axe throw, the wind ghost with an open mouth, the sky target). The reference pictures live in assets/poses/<class>_idle1.png (the class idle) and assets/units/.

Write (not published) (plain text the owner can copy; one fenced block per prompt; Traditional Chinese for the instructions to the owner, English for the prompt text):
1. For EACH of the 7 classes (skeleton, wizard, bat, knight, bride, hunchback, reaper): ONE prompt that asks for a sprite sheet of the 8 frames in a 4 x 2 grid on a flat solid magenta (#FF00FF) background with equal cells and the character fully inside each cell with margin: idle1, idle2, charge 1, charge 2, charge 3, release, empty, hit, in that order, each labelled by its position only (NO text in the picture). Include the face lock, the same direction (the reference's direction), the same hand, the same size and feet line in every cell, the item rules (gone in release and empty), and the expression changes that are allowed. Say how the owner should ask for a re-do of ONE cell without changing the others (a follow-up message that keeps the rest).
2. A second short prompt per class for a FRONT-FACING close head-and-shoulders portrait.
3. A third block: the wind ghost, 4 frames in a 2 x 2 grid (asleep, cheeks puffed, mouth wide open blowing, widest mouth leaning back), facing right, flat magenta background.
4. Practical notes for the owner (max 10 lines): how many sheets to ask for per chat, how to attach the reference, what to check on each result (the checklist: same face, same direction, same hand, item rules, nothing cut at the edge), and how to save the files with the names ingest expects: <class>_sheet.png.
Do not edit any other file. State what you could not verify (you cannot see the pictures image2 will make).

## ADDENDUM (owner 2026-11-10: 'this model is more accurate; ask him to write CONTINUOUS ones')
Continuity is the point. The frames of a sheet must read as CONSECUTIVE MOMENTS of one motion, each a small step from the previous one, not eight separate poses. Write the prompts as animation STRIPS:
1. IDLE LOOP strip: 4 frames, a slow breath (chest and cloth rise and fall, the flame or cloth sways); frame 4 flows back into frame 1 (a seamless loop).
2. CHARGE strip: 6 frames of one smooth build-up: the item starts to move, then a growing pull back, the body leaning more each frame, the face tightening a little each frame, ending at the fullest pull (the frames are evenly spaced in the motion, each almost the same as its neighbour).
3. THROW strip: 5 frames: the last charge pose, the forward snap (release, the item leaves the hand), the follow-through with the arm stretched, the arm coming back, and the empty relaxed stance (which then returns to idle frame 1).
4. HIT strip: 3 frames: the impact jolt, the stagger, the recovery to idle.
Each strip: the same camera, the same feet line, the same size, the pivot (the feet) does not slide, the same face. State in each prompt that every cell differs from its neighbours only by a small step, and that cell N+1 is the natural next moment after cell N. Keep the earlier per-class sheet (8 frames) as an alternative, but the strips come first. Also give the owner a checklist for continuity: flip through the cells in order (or scrub them in a GIF) and check that nothing jumps (a face change, a size change, a weapon appearing again).
