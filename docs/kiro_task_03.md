# Kiro task 03 — object detail inventory (read the mockup, read the game mode, write the inventory)

Inputs (read all of them first):
- `(not published)` — the concept mockup of the finished game (read it as an image).
- `docs/game_mode.md` — confirmed rules and the 4 vs 4 target mode.
- `assets/units/unit_*.png`, `assets/env/`, `assets/fx/`, `(not published)` — what exists today.
- `docs/animation_plan.md` — earlier animation plan (draft).

## Do exactly this (documents only; no code, no images)

1. Write `docs/object_inventory.md`: every visual object you can see in the mockup or that the rules require,
   grouped as: characters (8 units: 4 classes x 2 teams, plus number/letter markers), held weapons,
   projectiles, floating shield, environment (platforms, ghosts with hanging crates, graveyard props,
   moon/castle background, fence), effects (muzzle flash, impact, landing ring, aim arc, smoke), UI
   (top bar, per-unit HP bars, bottom control bar parts, buttons, portraits).
2. For EVERY object give: id, what it looks like (colours, materials, silhouette), approximate on-screen size
   in px at 1920x1080, which states/frames it needs, whether layers are required (body / arm / weapon),
   facing rule (art faces LEFT, mirrored in code), whether it already exists in the repo (path) or must be
   generated, and for generated ones the best method: "Colab image-edit from a reference", "text-to-image",
   "draw in code (UI/effects only)".
3. Mark anything you are unsure about as `UNSURE` with the question. Do not invent details that are not visible.
4. Write the same data as `docs/object_inventory.json` (an array of objects with the fields above), valid JSON.
5. Then compare the inventory with the existing asset library (`assets/`, its `manifest.json` files, `docs/`)
   and write `docs/asset_gap_report.md`: a table of every object -> status (EXISTS_OK / EXISTS_NEEDS_REWORK /
   MISSING), why, and the recommended way to fill it (Colab image-edit, text-to-image, code-drawn,
   re-use). Finish the report with a prioritised recommendation list (what to generate first for the biggest visual gain,
   what can stay as is, what to cut), and an estimate of how many Colab images that means.
   Known problems to check against: the held weapons and hands (the original painted weapons look better than
   re-drawn ones; a real arm-swing needs separate arm poses), the floating shield (thin glossy horizontal bar,
   reference `(not published)`), the knight has no throwable item of its own.
6. Include the "throw cut-in" in the inventory: when a unit throws, a large portrait ("big head") of the attacker
   appears in the bottom bar with a dramatic reaction (the mockup's bottom-left portrait panel). List the portrait
   art needed per class (neutral, charging, throwing, hit), the frame/animation around it, and the effects.
7. Do NOT edit any other file. Do NOT run git commands.
8. Finish with a 6-line summary: counts per group, how many already exist, how many need generation, the five
   most important UNSURE questions.
