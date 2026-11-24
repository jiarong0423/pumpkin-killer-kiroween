---
inclusion: fileMatch
fileMatchPattern: "colab/*.json,docs/kiro_task_*.md,docs/PROMPT_LOG.md,docs/kiro_*art*"
---
# Prompt engineering rules for pictures (from docs/PROMPT_LOG.md, learned on 2026-11-10)
1. A reference PICTURE beats a style sentence. Give style first, identity second, and call them "first reference" and "second reference" in the prompt.
2. Subject and action go in `prompt`; the look goes in `style`; never repeat the style in both.
3. Edit from the ORIGINAL picture, never from an already edited one: noise accumulates (P03). One picture per prompt; no sprite sheets.
4. Ask for a flat, noise-free magenta background; the main line keys it with a tight ramp and cuts glow halos.
5. No text inside pictures (Qwen writes Chinese unreliably).
6. Every prompt states its goal, its exact reference files, recommended settings and 3 checks the main line can measure; the main line records the run in (not published)
7. Pictures are generated only by the main line on Colab (Qwen); Kiro writes the prompts and specs.
