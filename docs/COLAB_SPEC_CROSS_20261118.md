# Colab spec: the nun's thrown silver cross (draft, nothing generated yet)

Owner 2026-11-18: "the cross does not look like a cross", "the material is too ugly", "or you generate it"; he showed pendant photos (slender silver Latin crosses, long shaft, shorter bar high up, flared ends, bevelled metal).
Owner rule: before any external generation the current state, the size and the style are written down. Opening a job needs the owner's Colab session and one word.

## Current state (2026-11-18)
| item | where | verdict |
|---|---|---|
| old picture | `assets/fx/sprites/item_cross_silver_plain.png` | owner: ugly; still used as the item icon |
| in-game flying cross | drawn in code since 2026-11-18 (`index.html`, branch `p.weapon === "proj_cross"`): slim silver Latin cross, flared kite-shaped ends, bevel, glow, turning 3 times a second | a clean fallback; a painted sprite would replace it |

## Spec: `fx_cross_silver`
- Size: **512 x 512**, RGBA, transparent background, the cross centred and upright, the outer 8 percent empty (it spins on screen, so no cut at the edge).
- Content: ONE slender silver Latin cross (shaft about 4 times the bar width, the bar high up at about 30 percent from the top, arm length about 0.64 of the shaft), the four ends flaring slightly (gothic / fleur style), polished bevelled metal with a bright specular line, a thin dark outline; no chain, no hand, no ring at the top, no text.
- Style: the same flat cartoon with soft glow as `assets/fx/sprites/*` (thick-ish dark outline, simple gradient shading), cool silver to pale blue highlights; no photographic texture.
- Prompt (English): "a single slender silver latin cross, upright, long shaft and shorter crossbar high up, slightly flared gothic ends, polished bevelled metal with a bright highlight line, thin dark outline, flat stylised game item sprite with soft glow, centred, transparent background, no chain, no text".
- Negative: photo, jewelry model, hand, necklace chain, bail ring, background scenery, text, frame.
- Reference pictures: the owner's pendant photos (pasted in the session, not stored in the repository).
- Variants: 4 seeds (1000 + 17 x variant); pick one.
- Files: `assets/fx/sprites/fx_cross_silver.png` and `.webp`, then `scripts/make_sw_precache.py --apply`; the page draws it instead of the code-drawn cross when the file exists (small code change, behind a file check).

## Acceptance
1. 512 x 512, RGBA, alpha 0 in the four corners and in the outer 8 percent (script).
2. The picture is NOT rotationally symmetric by 90 degrees (a cross is: the check is that shaft and bar differ in length, script on the alpha bounding box ratio between 1.4 and 2.2).
3. The owner looks at it at 60, 120 and 160 px turning on the real stage.
