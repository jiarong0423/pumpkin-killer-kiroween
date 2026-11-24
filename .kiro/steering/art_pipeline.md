---
inclusion: always
---
# Art pipeline

Pictures are made with Qwen-Image-Edit on Google Colab by the owner's pipeline. Kiro owns the art rules, naming, manifest, automatic checks, and integration. This steering governs generated picture acceptance; it does not permit code-drawn substitute art.

## Palette

Use one deep blue-violet night world. The approved interface palette is deep blue-violet `#120A22`, violet `#5A328C`, pumpkin orange `#FF8A1F` for selectable controls, ghost cyan `#A5F3FF` for information, and warm gold `#FFD32A` for the selected state. Character art may use a thin warm-orange outer glow `#FF9D3C`. Do not introduce another accent colour.

## Character acceptance rules

- Characters are chibi. The head is about one third of the full character height.
- Each pictured character has one head and two arms, with a soft dark outline and a thin warm-orange outer glow.
- The Pumpkin Knight and Pumpkin Wizard keep their carved jack-o-lantern faces.
- The Ghost Nun has a pale ghost-white face, never green. The Hunchback is the only green-skinned hero.
- A keyed unit or pose is exactly 1024 x 1024 with a transparent background. An avatar is exactly 256 x 256, square, and has a complete head with clear margin on every side. A front portrait may have any dimensions but must show a complete subject.
- The key colour is `#FF00FF`. Key it out before installation. No magenta remains inside an opaque character.
- Do not ship an incomplete picture. A hero with a required picture missing or rejected by the pipeline is not selectable.

## File names

Use `unit_<hero>_*.png` for unit art, `pose_*` or `<hero>_windup|release|hit*.png` for poses, `avatar_<hero>.png` for avatars, `<hero>_front.png` for front portraits, `fx_*.png` for effects, and `bg_<scene>.png` for backgrounds. Existing legacy names are recorded by the manifest until their replacement is installed.

## Avatar prompt template

Goal: turn `<reference picture>` into the finished avatar for `<hero>` without changing that hero's identity.

> Edit the reference into a square HEAD-AND-SHOULDERS character avatar icon (a game head shot). Preserve the IDENTICAL face, colours, outline, proportions and art style of the reference: same character, same expression shape, no redesign. Frame: `<complete hero-specific head, hair, ears, horns, hat, hood, veil, stem, and shoulders>`. The whole head is COMPLETE and centred with a clear margin on every side (about 8 percent of the canvas): NOTHING is cut off by the canvas edge, no ear, hat, hood, veil, hair, horn or stem is clipped; shoulders and upper chest fade out at the bottom edge inside the frame. Slight three-quarter turn toward the viewer's left like the reference, eyes looking out. Dark-fantasy 2D cartoon, chibi proportions, soft dark outlines, thin warm-orange outer glow, rich stylised game art like a polished Halloween mobile-game character portrait: layered depth, soft volumetric lighting, fine surface texture, no flat cel shading, clean noise-free #FF00FF background, no ground, no shadow plate, no frame, no border. Do not include text, extra heads, extra faces, extra hands, other characters, any known film or game character, a background other than flat magenta, or magenta inside the character.

Use the style reference first and `<reference picture>` second. Generate at 1024 x 1024 with a clean `#FF00FF` background, key it to RGBA, then install it as `(not published)` at 256 x 256. Main-line acceptance checks are: the complete head has an approximately 8 percent margin; the keyed file is 256 x 256 RGBA with transparent corners; and no opaque pixel is magenta-like.

## Disclosure

Pictures are generated with Qwen-Image-Edit-2511 (and a Lightning LoRA) on Google Colab from the team's own reference drawings; Kiro owns the art rules, the asset pipeline, the automatic checks and the integration. Licence: Apache-2.0 per the Hugging Face model cards (model pages read 2026-11-16; see `docs/ASSET_PROVENANCE.md`).

## Orientation is frozen (owner 2026-11-16)
Native art faces LEFT; the page mirrors the player's side. `shared/orientation_frozen.json` pins `ART_FACES_RIGHT` (only the hunchback is true) and the hash of every picture under `assets/poses` and `assets/units`; `scripts/test_orientation_frozen.js` fails if any of them changes. A new or replaced hero picture must face LEFT before it is installed (look at it, then run `python3 -B scripts/freeze_orientation.py --write`). Never fix a facing by flipping in code for one frame: flip the file once and re-freeze. The wind ghost is bound to the wind direction and carries no number.
