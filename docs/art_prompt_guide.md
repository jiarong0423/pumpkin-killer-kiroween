# Art prompt guide for the Colab UI and fence art (Kiro task 26)

Model: Qwen-Image-Edit-2509. It is an edit model: every job gets one reference image and one prompt. Kiro writes prompts and checks them against this guide. Kiro does not generate images.
Jobs: `colab/ui_jobs_kiro.json` (39 jobs, tier `U2`). Run order: `docs/art_job_order.md`. Earlier work: `docs/dock_design.md`, `docs/dock_asset_requests.md`.

## a. Style bible (10 lines)

1. **Palette.** Outline ink `#0c0913`. Stone `#120e1a`, `#1d1828`, `#2a2337`. Wood `#26160b`, `#4a2e1a`, `#6c4526`. Iron `#6f6580`. Bone `#e8dcc0`. Candle gold `#ffcf5a`. Pumpkin orange `#ff8a1f`. Spectral cyan `#5df2ee`. Blue-violet `#a98bff`. Healing green `#62e88a`. Danger red `#ff5d6c`. These match `css/dock.css`.
2. **Line weight.** Even dark-ink outline about 4 px on the 1024 px canvas, inner detail lines 2 px. No line thinner than 2 px: it disappears when the object is shown at 100 px.
3. **Light direction.** Key light from the upper left in warm candle gold, cool cyan rim light on the lower right. Top edges brighter, bottom edges darker, on every object, so the pieces look like one set.
4. **Shading.** Three painted tones plus one highlight, with visible brush texture. No single smooth gradient across a whole object.
5. **Materials.** Wood: grain lines along the long axis, chipped corners. Stone: fine cracks, chips, a few moss patches. Iron: domed rivets, rust flecks around them, a thin bright edge highlight. Wax: rounded, soft drips, warm cream. Bone: cream with hairline cracks.
6. **Warm glow** (candle gold, pumpkin orange) means selected, ready or hot. **Cool glow** means spectral things: cyan for the human side and ghost fire, blue-violet for the agent side and the special slot.
7. **Glow rule.** Glow stays inside the outline or hugs it in a halo no wider than 2 percent of the object. No soft bloom that reaches the magenta, no smoke, no transparency.
8. **Avoid.** Flat vector look, text, letters, numbers, logos, watermark, plastic or airbrushed shine, photo realism, cast shadow, ground, scenery behind the object. Nothing pink, magenta or red-violet inside the object: the chroma key will eat it. Violet must lean blue (`#a98bff`).
9. **Silhouette.** One bold readable shape per image, at most three large details. Key details are at least 6 percent of the object width.
10. **Consistency.** Round domed rivets, one per corner on plates. Same wording for every state of the same object (see recipes), so normal, hover, active and disabled differ only in the stated way.

## b. Writing prompts for an edit model

Pipeline facts (from `colab/pumpkin_assets_job.py`, read, not run):
- The reference is padded onto a square magenta canvas and the output is a 1024 x 1024 square. A wide bar or a tall fence therefore occupies only part of the square. Crop to the object afterwards.
- A 4 : 1 object gets roughly 870 x 220 px of real detail. The 1920 px dock frame must be used as a 9-slice (fixed corners, stretched plain middle), never stretched as a whole.
- The script passes `negative_prompt=" "` and ignores the `negative` field of each job. The field is in the file for a script change (see `art_job_order.md`).
- The style string is appended to every prompt. Jobs have no per-job `style`, so the global one applies.

Rules:
1. Start with the verb that matches the job: "Redraw as ..." when the shape comes from the reference (bars, plates), "Draw only ..." when the object is new and the reference is only a style source.
2. One object per image. Say "Draw only", name the object once, and end with "Nothing else" for icons.
3. Give the aspect ratio in words ("about 4 : 1", "about 1 : 2") and say "symmetrical left to right" or "front view".
4. Give exact counts: rivets per corner, planks, bars, flame tongues, rune marks, ticks. Edit models follow counts of 12 or fewer. Beyond that they drift.
5. Say where glow goes ("along the bottom edge", "inside the crack") and that it stays inside the outline.
6. Name what must stay empty: "flat, smooth, empty dark panel kept free for text". Never write the actual text.
7. Describe material by name (oak, stone, rusted iron, bone, wax), not by adjectives like "premium" or "epic".
8. Keep each prompt under 90 words. No artist, brand or game names.
9. When the reference shows something you do not want (a character, a horizontal bar), say so in the prompt: "Nothing else: no wizard, no character, no hat, no hands."
10. Centered, 15 percent empty margin on every side, flat magenta `#FF00FF` background. These are in the global style string, so do not repeat them in the job prompt.

## c. Recipes per object type

| Type | Aspect | Recipe | Jobs |
|---|---|---|---|
| Frame (bar frame, dock frame) | 4 : 1 to 8 : 1 | Border material + exact rivet count + end caps + "interior empty and plain". For the dock frame say "built for stretching in the middle". Symmetrical. | `ui_dock_frame`, `ui_hp_frame`, `ui_wind_frame` |
| Name or info plate | 4 : 1, 5 : 2 | Plank or brass + rivet in each corner + end ornaments + one thin glow line + "large centre flat, empty, free for text". Team colour only in the rune line. | `ui_top_plate_left`, `ui_top_plate_right`, `ui_top_center_plate`, `ui_lock_plate` |
| Button plate | 4 : 5 | Copy the same first sentence in all four states. Only the state sentence changes: normal = no glow; hover = polished gold rim; active = orange rune plus inner light; disabled = grey, extra cracks, cobweb. | `ui_plate_*`, `ui_hero_chip_*` |
| Icon | 1 : 1 | "Draw only a square game icon: ...", one subject, one glow colour, "readable at small size", "Nothing else: no character, no hands". Use the wizard reference only for pumpkin or bomb icons. | `ui_icon_*`, `ui_btn_*` |
| Bar fill | 8 : 1 | No frame at all. Colour, highlight line on the upper third, flat darker lower edge, rounded ends, opaque. Draw green only; CSS tints amber and red with a hue filter. | `ui_hp_fill` |
| Flame strip | 4 : 1 | Exact tongue count (7), flat bottom edge, opaque layers (white core, bright body, dark outer rim), equal heights at both ends so it tiles. | `ui_ghostfire_*` |
| Meter segment | 3 : 5 | Same stone, same crack, same chips in all three states. Only the glow changes (none, orange, white-hot gold). | `ui_power_*` |
| Socket | 1 : 1 | Rim material + corner studs + "recess completely empty". Special socket: ring of twelve dashed runes, no gold. | `ui_socket_*` |
| Fence | tall, 1 : 2 | BLACK wrought iron, two thick end posts, four thin bars, two crossbars, one hanging jack-o'-lantern. The damaged and broken states say "same footprint". The game fence is 130 x 250 px, so keep it tall and narrow with large simple parts. | `env_fence_*` |
| Portrait | 1 : 1 | "Redraw this same <character>", face RIGHT, "same colours and outline", crop below the chest, expression in one sentence. The unit images face LEFT, so the model has to turn the head. If it keeps facing left, flip the file and note it. | `portrait_*` |

## d. QA checklist for each result

Check both variants. Keep the better one and note the reason.

1. Silhouette: shrink to 100 px wide. The object is still recognisable, no detail turns to mush.
2. No text, letters, numbers, logos or fake runes that look like letters. Rune marks must be abstract.
3. Magenta key: the background is one flat `#FF00FF`. No gradient, no pink halo, no magenta pixels inside the object.
4. Edges: no glow or haze blending into the background. Outline is closed and dark.
5. Symmetry: where the prompt says symmetrical (plates, frames, lock plate, dock frame), the left and right halves match in rivet count and ornaments.
6. Counts: rivets, bars, flame tongues, rune marks, ticks match the prompt, or are within one.
7. Empty areas stay empty: plate centres, sockets, trough interiors, button recesses carry no marks.
8. Aspect: the object has the stated proportion after cropping. A fence that comes out wide or square is rejected.
9. State sets (plates, power segments, chips, fence): the states share shape, size and rivet layout, so they can swap in place.
10. Palette: hues match the hex values in the style bible, and violet leans blue.
11. No leaked character from the reference (a wizard hat on an icon, a pumpkin head on a fence).
12. Weapon or arrow direction: the wind arrow points right. Portraits face right.

## e. Reference images on Drive (`MyDrive/PumpkinKiller/inputs/`)

| File | Shows | Use for |
|---|---|---|
| `ref_bar_from_video.png` | A thin glossy horizontal bar | Default for everything that is not a pumpkin or a character: frames, plates, strips, segments, sockets, chips, round buttons, candle, potion, fence. It carries no character, so nothing leaks. |
| `unit_wizard.png` | Pumpkin wizard with a brass shoulder cannon | `portrait_wizard`, the three wizard cut-ins, and the pumpkin or bomb icons (`ui_icon_normal`, `ui_icon_double`, `ui_icon_heavy`). |
| `unit_skeleton.png` | Skeleton spearman | `portrait_skeleton` only. |
| `unit_bat.png` | Bat-cat assassin | `portrait_bat` only. |
| `unit_knight.png` | Pumpkin knight with coffin shield | `portrait_knight` only. |

Fallbacks if a result is wrong:
- A wide reference pulls tall objects (fence, candle, power segments) toward a horizontal layout. If two variants fail, switch the job `ref` to `knight` (tall, dark metal) and add "Nothing else: no knight, no pumpkin head, no shield".
- If a unit reference leaks a character into an icon, switch that icon to `bar` and describe the pumpkin in words.
- If a plate state set drifts apart, generate the normal plate first, then re-run the other states with the same seed by keeping the sentence identical.

## Not verified

- No image was generated or seen. Every claim about what the model will do comes from the reference list and the script, not from results.
- Counts above 5 or 6 (ten runes, twelve dashes, eight rivets) are the most likely to come out wrong. They are marked as risky in the job order notes.
- Whether the edit model respects "about 4 : 1" inside a square canvas is untested.
