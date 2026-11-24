# Kiro task 73 — art gap design pack (Terra = art design; main line verifies everything)

**IMAGE GENERATOR RULE (owner 2026-11-10, DECIDED): the owner has NO ChatGPT/Codex image generation ("image2" does not exist for us). Every picture is made by QWEN (千問): either the Colab notebook with Qwen-Image-Edit (one picture per job, a reference picture attached, 1024x1024, flat magenta background) or the owner pasting a prompt into the Qwen (千問) chat. So: write prompts for Qwen, ONE picture per prompt (no 8-cell or 12-cell sprite sheets: Qwen does not keep many frames consistent), each with the reference file to attach, the exact "same as the reference" lines, and a simple Chinese version next to the English one (Qwen reads Chinese well). For continuity across frames, give a chain: frame 1 from the reference, frame 2 from frame 1, and so on. Replace every "image2" / "ChatGPT" / "Codex image" wording in your answer with Qwen.**


Owner 2026-11-10: GPT (Terra) does the ART DESIGN part of the gap queue. Read first: (not published) (section 二), docs/game_style_brief.md, docs/pose_spec.md, docs/top_hud_art_jobs.md, docs/image2_ghost_blow_prompt.md, docs/kiro_69_art_optimization.md (do not repeat what it already solved), and the existing pictures you need to match: assets/env/platform_coffin_purple.png, assets/env/bg_*.png, assets/portraits/*.png, assets/poses/*.png, assets/env/fence_black_*.png (look at them, you can read images).

Verified gap facts from the inventory (main line re-checked none yet; say so if a fact looks wrong when you look at the file):
1. assets/env/bg_belltower.png and bg_pumpkin_field.png are referenced by the scene picker (index.html:343-344) and DO NOT EXIST. Need two battlefield backgrounds in the same style and 16:9 framing as the current moonlit-graveyard background, with the same ground line height and a clear fence spot in the centre.
2. A blue twin of assets/env/platform_coffin_purple.png (same three-quarter view, riveted corners, glowing runes, ghost-flame drips; cyan instead of violet).
3. Pose frames missing or misnamed: wizard release, reaper (only idle1, idle2, charge1, charge3 exist; needs the 8-frame set), skeleton charge2; the standard is in (not published)
4. assets/units/unit_knight_unarmed.png (the knight with empty hands, same size and pose as unit_knight.png).
5. Front portraits missing: bat and necromancer (match assets/portraits/*.png).
6. Fence damaged and broken states: check assets/env/fence_black_damaged.png and fence_black_broken.png; if they do not read clearly different from intact at game size, write redraw prompts.

Deliver ONE file: docs/kiro_73_art_pack_gpt-5.6-terra.md (max 250 lines):
- Per gap: purpose, exact size and canvas, background rule (flat #FF00FF unless a full background), attach-list (which existing files to attach as references), the English image prompt (paste-ready for Qwen: Colab job or the 千問 chat; one picture per prompt), the "same as" continuity lines, and 3 acceptance checks the main line can measure.
- A recommended order and which prompts can be generated in one sheet.
- For any prompt you are unsure will keep the same face/style, say so and give the fallback.
Do NOT edit any other file and do NOT claim anything was generated. Art is never drawn by code.
