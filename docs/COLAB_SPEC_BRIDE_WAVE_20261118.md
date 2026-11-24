# Colab spec: the bride's sound-wave vortex (draft, nothing generated yet)

Owner 2026-11-18: the bride's wave "was originally big and looked like a vortex"; the texture of the shrunk version is very different. "If you really lack a picture, generate it in Colab, there is quota left."
Owner rule (docs/COLAB_SPEC_MAP_GROUND_20261117.md): before any external generation the current state, the size and the style are written down. Nothing has been queued; opening a job needs the owner's Colab session and one word.

## What exists today (compared 2026-11-18)
| item | where | what it is | verdict |
|---|---|---|---|
| ring sprite | `assets/fx/sprites/fx_sonic_ring.png` (666 x 661, RGBA, 657 KB; `.webp` twin) | concentric neon rings, cyan and violet, dark core; circular, symmetric | good as a ring; a rotation is INVISIBLE because it is rotationally symmetric, so it cannot look like a spinning vortex |
| travelling wave | `index.html` draw of `proj_soundwave` | three copies of the ring that swell and fade | was 60 to 204 px, shrunk to 24 to 68 px by commit beb21001, restored to 0.35 to 1.2 x `wLen` on 2026-11-18 |
| landing marker | `index.html` `landRings` | before: one fixed 210 px `land_ring` picture; now: three swelling copies of the ring up to 210 px | 210 px is the full hit width |
| particles | `js/ultimate_fx.js` event `soundwave_rings` (bride's ultimate only), `js/particles.js` | spawn rings at the landing point for the ultimate | not used by the normal wave |
| spiral or vortex sprite | none in `assets/fx/sprites` (the set: sonic ring, rune circle, wind swirl (a 626 x 307 gust), ghost puff, spirit mist, stardust, impact flash and others) | MISSING | this is the one real gap |

## Spec: `fx_sonic_vortex`
- Purpose: a vortex that visibly SPINS when the page rotates it (a spiral arm structure, not concentric rings), drawn over the same ring so the wave keeps its current colours.
- Size: **768 x 768**, RGBA, transparent background, centred, the outer 6 percent empty (no cut at the edge), so it can be drawn up to 240 px on screen without blur.
- Content: a top-down spiral whirlpool of sound: 3 or 4 curved arms winding into a dark violet core; thin cyan neon edge lines; soft violet glow; faint musical-note-like sparkles allowed but no text, no characters, no hands.
- Style: the same as `fx_sonic_ring.png` (deep violet `#3b0a52` to `#b455d8`, cyan `#35e8f0` lines, white-violet highlights), glowing neon on a dark core, flat cartoon with soft glow like the rest of `assets/fx/sprites`; no photographic texture.
- Variants: 4 seeds (seed = 1000 + 17 x variant, like the pipeline), pick one; the arms must not be mirror symmetric (so a rotation reads).
- Reference pictures (the pipeline can take one reference per job): `assets/fx/sprites/fx_sonic_ring.png` for palette and glow.
- Prompt (English, the model is Qwen-Image-Edit-2511 in `docs/colab_pipeline_excerpt.md`): "top-down spiral vortex of sound, four curved arms winding into a dark violet core, glowing neon cyan edge lines, soft violet glow, same palette as the reference ring, flat stylised game effect sprite, transparent background, centred, no text, no character".
- Negative: photo, realistic smoke, text, letters, hands, face, frame, square border, background scenery.
- Files to deliver: `(not published)` and `.webp` (the same pair as the other sprites; `scripts/make_sw_precache.py --apply` after adding).

## Acceptance (checked by script, then by the owner's eyes)
1. 768 x 768, RGBA, alpha 0 in all four corners and in the outer 6 percent ring (script).
2. NOT rotationally symmetric: the picture compared with itself rotated by 90 degrees differs by more than 10 percent of the pixels (script), otherwise a spin would be invisible.
3. The dominant colours fall inside the palette above (script, hue histogram).
4. The owner looks at it drawn at 60, 150 and 240 px on the real stage.

## Code (small, done after the picture exists, behind a file check)
`images.proj_soundwave_vortex` is drawn rotating at about 0.7 turns per second under the ring in the travelling wave and in the three landing rings; when the file is missing the code keeps the ring only. Hit width, damage and the cell bands do not change.
