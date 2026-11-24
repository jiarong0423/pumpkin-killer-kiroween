# Airdrop asset requests for Colab (Kiro task 31)

Only images needed **beyond** the ghost, the crate and the parachute, which are already being generated. These must be made on Colab (Qwen-Image-Edit) and never faked with code. Nothing here has been generated or checked; I cannot see images.

Conventions (same as `docs/dock_asset_requests.md` and `colab/jobs.json`): flat solid magenta background `#FF00FF` (chroma-keyed afterwards), no text, no watermark, no cast shadow outside the object, dark-fantasy 2D cartoon art with thick clean outlines. Palette: stone `#2a2337`, wood `#4a2e1a`, candle gold `#ffcf5a`, pumpkin orange `#ff8a1f`, spectral cyan `#5df2ee`, violet `#a98bff`.

Item icons are 96 x 96 each. The supply slot draws them at about 34 to 44 px, so every icon is **one object, one dominant colour, thick outline, no fine detail**, and the six colours below must stay distinguishable at that size. Each icon also appears over the landed crate and next to the opponent's HP bar, so none may need text to be understood. The emoji in `docs/airdrop_design.md` stay as the fallback until the images are reviewed in the game.

| # | Name | Size | What it shows | Prompt (one sentence) | Where it is used |
|---|---|---|---|---|---|
| 1 | `icon_candy_heal` | 96x96 | A small glass jar of glowing green Halloween candy with a cork. Dominant colour: green. | A small glass jar full of glowing green Halloween candy with a cork lid, front view, thick outline, 2D dark-fantasy cartoon style, flat magenta background. | Slot, landed crate, status next to HP bar |
| 2 | `icon_heavy_shell` | 96x96 | A round black bomb with a short lit fuse and an orange glow. Dominant colour: black and orange. | A round black cannon bomb with a short lit fuse and an orange glow, front view, thick outline, 2D dark-fantasy cartoon style, flat magenta background. | Slot, crate |
| 3 | `icon_second_die` | 96x96 | Two ivory dice stacked at an angle, pips in dark red. Dominant colour: ivory. | Two ivory six-sided dice stacked at an angle with dark red pips, front view, thick outline, 2D dark-fantasy cartoon style, flat magenta background. | Slot, crate, status |
| 4 | `icon_shield_patch` | 96x96 | A small cyan hammer resting on a cracked wooden coffin-lid slab. Dominant colour: cyan. | A small glowing cyan hammer resting on a cracked wooden coffin-lid slab, front view, thick outline, 2D dark-fantasy cartoon style, flat magenta background. | Slot, crate |
| 5 | `icon_calm_wind` | 96x96 | A pale violet swirl of wind with a small calm still centre. Dominant colour: pale violet. | A pale violet spiral of wind that ends in a calm round centre, no arrows, front view, thick outline, 2D dark-fantasy cartoon style, flat magenta background. | Slot, crate, status |
| 6 | `icon_bone_ward` | 96x96 | A bone-white ribcage breastplate with a tiny orange glow in the middle. Dominant colour: bone white. | A bone-white ribcage breastplate with a tiny orange glow in the centre, front view, thick outline, 2D dark-fantasy cartoon style, flat magenta background. | Slot, crate, status |

Optional, lower priority (the prototype fades the canopy and has no release pose):

| # | Name | Size | What it shows | Prompt (one sentence) | Where it is used |
|---|---|---|---|---|---|
| 7 | `chute_collapsed` | 192x128 | The parachute canopy crumpled on the ground, with its lines slack. | A pale crumpled parachute canopy lying slack on the ground with loose lines, side view, thick outline, 2D dark-fantasy cartoon style, flat magenta background. | Replaces the canopy fade for the 0.8 s after landing |
| 8 | `ghost_release_pose` | 256x384 | The carrier ghost with both arms raised and a wide laughing mouth, hands empty, facing left like the other characters. | The same carrier ghost as the reference image with both arms raised, hands empty and a wide laughing mouth, facing left, thick outline, 2D dark-fantasy cartoon style, flat magenta background. | The 0.3 s pause at the release; mirrored for the right-facing flight. Size is a guess from the prototype's 120x180 draw size; match whatever size the main ghost image uses |

Notes
- Review items 1 to 6 on the real dock first, at 34 px. If two icons look alike, redo the one with the weaker colour.
- Status icons next to the HP bar are the same files scaled down to 32 px; no separate request.
- The landing ring, dust, wisp and glow are programmatic effects (the existing particle system), not images, so they are not requested.
