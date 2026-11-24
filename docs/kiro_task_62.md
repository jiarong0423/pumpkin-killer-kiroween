# Kiro task 62 — write the image-edit prompts for the art redo (you are one of TWO independent authors)

Owner request (2026-11-10): "I suggest Kiro generates the image prompts." The first set was written by the main line from a template; it produced faces that changed, copies of the idle picture, and wrong weapons. You write a better set. Another author (another model) writes the same job independently; the main line will compare and merge. Do not look for the other author's file.

Read first: docs/pose_spec.md (the standard: 8 frames per class, one direction, one hand, one size, face lock, the item disappears at the throw), (not published) (which pictures the owner wants redone: the 'redo' list), (not published) and (not published) (two art reviewers looked at every frame: per-frame verdicts and a canonical FACE and ITEM description per class), (not published) (measured: which frames came back as copies, which faces drifted), colab/jobs_queue_20261109.json (the FIRST prompts, to improve), scripts/make_art_queue.py (how they were built), (not published) (newest rows last: rules about direction, hands, faces, expressions, the necromancer's flame, the hunchback's two-handed axe throw, the sky target, the front portraits).

The picture model is Qwen-Image-Edit-2511 (an instruction-following EDIT model: input = the reference picture of the class idle, output = the same character in a new pose). What we learned the hard way:
- A prompt that describes a new picture is ignored: the model copies the reference. It must be an EDIT INSTRUCTION ("Edit this image: change the pose to ... keep everything else identical") with a big visible change.
- Very long prompts (450 words) dilute the instruction. Aim for 120 to 180 words per prompt, the rules in short sentences, the canonical face and item descriptions shortened to one sentence each.
- The model redraws a face when asked for an expression: ask for a SMALL change (mouth opening, eyebrow angle) and say the rest of the face is untouched.
- The model keeps a weapon in the hands unless told 'the picture contains no <item> at all' (say it twice, in different words).
- The picture must keep the character inside the frame: a canvas of 1536x1024 is used; say where the character stands and where the empty margin is.

Write (not published)<your model>.json = {"model": "<your model name>", "jobs": [ {"id": "pose_wizard_charge1", "prompt": "...", "negative": "...", "why": "one sentence: what you changed against the first prompt and why it should work"} ... ]} for EVERY id in the 'redo' list of (not published) (39 ids; pose_*, portrait_front_*, fx_molotov_fire). Prompts for portraits must ask for a CLOSE FRONT-FACING head-and-shoulders portrait (the head fills the picture). Keep the style sentence out of the prompt (the main line appends the shared style and the magenta background sentence).
Also write 8 lines at the end of (not published)<your model>.md: the three rules you believe matter most, and what you could not verify (you cannot see pictures unless your model can: say so).
Do not edit any other file. Use `python3 -B` for any check, for example a word-count check of your own file.
