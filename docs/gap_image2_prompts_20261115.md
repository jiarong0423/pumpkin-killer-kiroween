# Remaining image gaps: image2 prompts

This is an owner-run, one-image-per-prompt queue. `fx_ghostfire_orbit3` is conditional: make it only if the current ghost-fire sprite cannot read as three separate fires. The necromancer keeps its established purple flame accent; no new blue-violet aura is introduced.

## A. Inventory

| Picture name | What it is for | File it must become | Status | Hero or system | Source |
|---|---|---|---|---|---|
| `unit_knight_unarmed` | Empty-handed post-throw knight | `assets/units/unit_knight_unarmed.png` | missing | knight | `check_asset_refs.py` output; `jobs_missing` |
| `fx_feet_chain` | Slow-status ankle shackles | `assets/fx/sprites/fx_feet_chain.png` | missing | bat status | `check_asset_refs.py` output; `jobs_missing` |
| `coin_pumpkin_head` | Coin-toss pumpkin-face side | `assets/ui/coin_pumpkin_head.png` | missing, optional | opening flow | `jobs_missing`; gap matrix §2 |
| `coin_pumpkin_tail` | Coin-toss stem-and-vine side | `assets/ui/coin_pumpkin_tail.png` | missing, optional | opening flow | `jobs_missing`; gap matrix §2 |
| `ghoststar_blow` | Normal wind ghost blow | `assets/fx/sprites/fx_ghost_blow.png` | exists; retain | wind UI | gap matrix §2; assets filename list |
| `ghoststar_blow_hard` | Strong wind ghost blow | `assets/fx/sprites/fx_ghost_blow_hard.png` | exists; retain | wind UI | gap matrix §2; assets filename list |
| `necro_ult_point` | Empty-hand pointing ultimate pose | `assets/poses/necro_ult_point.png` | missing | necromancer | character matrix §1; `jobs_characters` |
| `necro_idle2` | Second idle-frame flicker | `assets/poses/necro_idle2.png` | missing | necromancer | character matrix §1; `jobs_characters` |
| `necro_charge2` | Middle charge frame | `assets/poses/necro_charge2.png` | missing | necromancer | character matrix §1; `jobs_characters` |
| `necro_front` | Retaken face portrait | `(not published)` | exists but wrong | necromancer | character matrix §1; `jobs_characters` |
| `wizard_release` | Cannon release pose | `(not published)` | missing | wizard | character matrix §1; `jobs_characters` |
| `bride_front` | Retaken face portrait | `assets/portraits/bride_front.png` | exists but wrong | ghost bride | character matrix §1; `jobs_characters` |
| `hunchback_front` | Retaken face portrait | `assets/portraits/hunchback_front.png` | exists but wrong | hunchback | character matrix §1; `jobs_characters` |
| `ui_frost_curse` | Frost-curse status icon | `(not published)` | missing, optional polish | skeleton status | character matrix §1; `jobs_characters` |
| `ui_bleed_drop` | Bleed status icon | `(not published)` | missing, optional polish | skeleton/hunchback status | character matrix §1; `jobs_characters` |
| `ui_burn_flame` | Burn status icon | `(not published)` | missing, optional polish | necromancer status | character matrix §1; `jobs_characters` |
| `ui_cross_curse` | Cross-curse status icon | `(not published)` | missing, optional polish | ghost nun status | `hag_face_spec`; current assets UI list |
| `ult_pip_socket` | Shared three-pip socket art | `(not published)` | missing, optional | ultimate UI | ultimate mapping §5 |
| `ult_spectral_spear` | Ghost-javelin ultimate art | `(not published)` | missing, optional | skeleton ultimate | ultimate mapping §5 |
| `ult_ricochet_shield` | Shield-chain ultimate art | `(not published)` | missing, optional | knight ultimate | ultimate mapping §5 |
| `fx_shockwave_ring` | Impact-ring ultimate art | `(not published)` | missing, optional | wizard/hunchback ultimate | ultimate mapping §5 |
| `ui_hallucination_mark` | Turn-skip hallucination status mark | `(not published)` | missing | necromancer ultimate | ultimate mapping §1b row 7 |
| `fx_ghostfire_orbit3` | Three readable orbiting fires | `(not published)` | conditional: current sprite may be enough | necromancer ultimate | `assets/fx/sprites/fx_ghostfire_purple.png`; ultimate mapping §1c |
| `hero_eighth_concept_a`, `hero_eighth_concept_b` | Scarecrow and web-spinner concepts | none | **obsolete: replaced by the ghost nun; skip** | eighth-hero concepts | `PROMPT_LOG` P18–P19; task brief |

The scene files `bg_belltower` and `bg_pumpkin_field` are missing according to the command output, but task 153 owns scenes, so this file intentionally skips them. The three missing audio files in that output are not pictures.

## B. image2 prompt blocks

### `unit_knight_unarmed`
**Attach:** first `assets/units/unit_skeleton.png` for style; second `assets/units/unit_knight.png` for identity.
```text
Use the first reference only for the shared Pumpkin Killer character style and the second for the exact pumpkin shield knight identity. Edit the second reference: preserve the identical glowing pumpkin face, armour, cape, full-body pose, direction, scale, palette, position, and feet baseline. Remove the held shield completely and leave its gauntlet as one empty relaxed hand in the same position. Dark-fantasy 2D cartoon, chibi with a big round head about one third of her whole height (a single head), soft dark outlines, thin warm-orange outer glow, rich stylised game art in the look of a polished Halloween mobile-game concept painting: layered depth, soft volumetric lighting, glowing light sources that tint nearby surfaces, fine surface texture, soft dark outlines, no flat cel shading, clean noise-free #FF00FF background, no ground or shadow. Do not include text, extra limbs, other characters, any known film or game character or item, a background other than flat magenta, shields, weapons, replacement props, or magenta inside the character.
```
**Check:** Face, silhouette, scale, direction, and feet baseline match `unit_knight`; neither hand holds anything.

### `fx_feet_chain`
**Attach:** `assets/weapons/small_shield.png` for shared item rendering only.
```text
Draw one wide, low pair of rusty dark-iron ankle shackles joined by four chunky slack chain links, side view, readable at small size, no feet or legs. Dark-fantasy 2D cartoon item, soft dark outlines, thin warm-orange outer glow, rich stylised game art in the look of a polished Halloween mobile-game concept painting: layered depth, soft volumetric lighting, glowing light sources that tint nearby surfaces, fine surface texture, soft dark outlines, no flat cel shading, restrained cold-grey metal highlights, centred with margin on a clean noise-free #FF00FF background. Do not include text, extra limbs, other characters, any known film or game character or item, a background other than flat magenta, feet, body parts, ground, or cast shadow.
```
**Check:** The full horizontal shackle-and-chain silhouette fits in frame and remains readable at status-effect size.

### `coin_pumpkin_head`
**Attach:** `assets/units/unit_knight.png` for the pumpkin-face palette only.
```text
Draw one perfectly front-facing round gold-orange coin with a thick embossed rim and a smiling carved jack-o'-lantern face, triangle eyes and jagged grin glowing warm orange. Dark-fantasy 2D cartoon item, soft dark outlines, thin warm-orange outer glow, rich stylised game art in the look of a polished Halloween mobile-game concept painting: layered depth, soft volumetric lighting, glowing light sources that tint nearby surfaces, fine surface texture, soft dark outlines, no flat cel shading, centred with margin on a clean noise-free #FF00FF background. Do not include text, extra limbs, other characters, any known film or game character or item, a background other than flat magenta, letters, numbers, hands, ground, or cast shadow.
```
**Check:** The coin reads as a round face side at small size and has no lettering.

### `coin_pumpkin_tail`
**Attach:** `assets/units/unit_knight.png` for pumpkin palette only.
```text
Draw one perfectly front-facing round gold-orange coin matching the head-side coin in size, rim, outline, and palette; its centre has only an embossed pumpkin stem, curling vine, and one leaf, with no face. Dark-fantasy 2D cartoon item, soft dark outlines, thin warm-orange outer glow, rich stylised game art in the look of a polished Halloween mobile-game concept painting: layered depth, soft volumetric lighting, glowing light sources that tint nearby surfaces, fine surface texture, soft dark outlines, no flat cel shading, centred with margin on a clean noise-free #FF00FF background. Do not include text, extra limbs, other characters, any known film or game character or item, a background other than flat magenta, letters, numbers, faces, hands, ground, or cast shadow.
```
**Check:** It pairs visually with the head side while remaining clearly the reverse.

### `ghoststar_blow`
**Attach:** `assets/fx/sprites/fx_ghost_idle.png`.
```text
Edit the reference into the same round wind ghost facing the same direction, with its mouth open in a small O and a short white mist puff leaving its mouth; keep normal cheeks, wide eyes, body scale, teal edge treatment, and placement unchanged. Dark-fantasy 2D cartoon sprite, soft dark outlines, thin warm-orange outer glow, rich stylised game art in the look of a polished Halloween mobile-game concept painting: layered depth, soft volumetric lighting, glowing light sources that tint nearby surfaces, fine surface texture, soft dark outlines, no flat cel shading, clean noise-free #FF00FF background. Do not include text, extra limbs, other characters, any known film or game character or item, a background other than flat magenta, extra objects, ground, or cast shadow.
```
**Check:** Generate only if the existing `fx_ghost_blow.png` needs replacement; the new frame must match idle size exactly.

### `ghoststar_blow_hard`
**Attach:** `assets/fx/sprites/fx_ghost_idle.png`.
```text
Edit the reference into the same round wind ghost facing the same direction, mouth opened widest, eyes squeezed shut, body stretched slightly forward, and one strong white air stream blowing forward; keep the ghost's identity, scale, teal edge treatment, and placement unchanged. Dark-fantasy 2D cartoon sprite, soft dark outlines, thin warm-orange outer glow, rich stylised game art in the look of a polished Halloween mobile-game concept painting: layered depth, soft volumetric lighting, glowing light sources that tint nearby surfaces, fine surface texture, soft dark outlines, no flat cel shading, clean noise-free #FF00FF background. Do not include text, extra limbs, other characters, any known film or game character or item, a background other than flat magenta, extra objects, ground, or cast shadow.
```
**Check:** Generate only if the existing hard-blow frame needs replacement; it must look stronger than normal blow without changing scale.

### `necro_ult_point`
**Attach:** first `assets/poses/necro_windup.png`; second `assets/fx/sprites/fx_ghostfire_purple.png` for fire shape only.
```text
Use the first reference for the exact necromancer. Same character as the attached picture, same scale and feet baseline, facing the same direction as the attached picture: strict side view facing LEFT. Edit to an ultimate command pose: the flame-holding hand reaches forward left, palm down, with only one index finger pointing; the other hand is empty; nothing burns in either hand. Exactly three separate purple ghost fires float behind him on the right at head height. Dark-fantasy 2D cartoon sprite, soft dark outlines, thin warm-orange outer glow, rich stylised game art in the look of a polished Halloween mobile-game concept painting: layered depth, soft volumetric lighting, glowing light sources that tint nearby surfaces, fine surface texture, soft dark outlines, no flat cel shading, clean noise-free #FF00FF background. Do not include text, extra limbs, other characters, any known film or game character or item, a background other than flat magenta, scythes, staffs, skulls, more or fewer than three fires, pink sparks, or ground.
```
**Check:** Count exactly three detached fires; verify LEFT direction, empty hands, unchanged scale, and baseline.

### `necro_idle2`
**Attach:** `assets/poses/necro_idle.png`.
```text
Edit the reference into the same necromancer one moment later. Same character as the attached picture, same scale and feet baseline, facing the same direction as the attached picture. Change only a slight breath, a tiny hood-and-robe sway, and a different small flicker shape in the single raised purple hand flame; keep face, hand, position, and calm expression unchanged. Dark-fantasy 2D cartoon sprite, soft dark outlines, thin warm-orange outer glow, rich stylised game art in the look of a polished Halloween mobile-game concept painting: layered depth, soft volumetric lighting, glowing light sources that tint nearby surfaces, fine surface texture, soft dark outlines, no flat cel shading, clean noise-free #FF00FF background. Do not include text, extra limbs, other characters, any known film or game character or item, a background other than flat magenta, weapons, a second flame, changed direction, or ground.
```
**Check:** It must differ visibly but subtly from idle1, with the same hand and identical baseline.

### `necro_charge2`
**Attach:** first `assets/poses/necro_idle.png`; second `assets/poses/necro_windup.png`.
```text
Use the first reference for the exact necromancer identity and the second for the full-charge endpoint. Same character as the attached picture, same scale and feet baseline, facing the same direction as the second attached picture: strict side view facing LEFT. Draw the middle charge: the same flame hand pulls back halfway between idle and full wind-up, with one flame larger than idle and smaller than full charge; body leans back slightly and face strains. Dark-fantasy 2D cartoon sprite, soft dark outlines, thin warm-orange outer glow, rich stylised game art in the look of a polished Halloween mobile-game concept painting: layered depth, soft volumetric lighting, glowing light sources that tint nearby surfaces, fine surface texture, soft dark outlines, no flat cel shading, clean noise-free #FF00FF background. Do not include text, extra limbs, other characters, any known film or game character or item, a background other than flat magenta, weapons, a second flame, a copy of either reference pose, changed hand, or ground.
```
**Check:** The frame reads clearly between idle and wind-up, facing LEFT with unchanged scale and baseline.

### `necro_front`
**Attach:** first `assets/poses/skeleton_idle1.png` for style; second `assets/units/unit_reaper_idle.png` for identity.
```text
Use the first reference only for shared style and the second for the exact necromancer identity. Draw one head-and-shoulders portrait, cropped at the upper chest: the same cream skull and jaw, ragged purple-black hood, purple inner lining, angry brows, glowing purple flame-shaped eyes, collar, and robe shoulders, three-quarter view slightly right. Dark-fantasy 2D cartoon portrait, soft dark outlines, thin warm-orange outer glow, rich stylised game art in the look of a polished Halloween mobile-game concept painting: layered depth, soft volumetric lighting, glowing light sources that tint nearby surfaces, fine surface texture, soft dark outlines, no flat cel shading, clean noise-free #FF00FF background. Do not include text, extra limbs, other characters, any known film or game character or item, a background other than flat magenta, full body, hands, flames in hands, bottles, scythes, weapons, or ground.
```
**Check:** Compare against the reaper unit: face, hood, and purple eye accent must match; crop contains no hands.

### `wizard_release`
**Attach:** first `assets/poses/skeleton_idle1.png` for style; second `assets/units/unit_wizard.png` for identity.
```text
Use the first reference only for style and the second for the exact pumpkin wizard. Same character as the attached picture, same scale and feet baseline, facing the same direction as the attached picture: strict side view facing LEFT. Draw the release: the same brass shoulder cannon fires left with an orange muzzle flash and one small grey smoke puff; body recoils, robe flares, pumpkin face roars, and the other hand is empty. Dark-fantasy 2D cartoon sprite, soft dark outlines, thin warm-orange outer glow, rich stylised game art in the look of a polished Halloween mobile-game concept painting: layered depth, soft volumetric lighting, glowing light sources that tint nearby surfaces, fine surface texture, soft dark outlines, no flat cel shading, clean noise-free #FF00FF background. Do not include text, extra limbs, other characters, any known film or game character or item, a background other than flat magenta, cannonballs, projectiles in flight, a second cannon, changed hat, changed hand, or ground.
```
**Check:** Match the wizard's face, cannon hand, scale, LEFT direction, and baseline; the cannonball is absent.

### `bride_front`
**Attach:** first `assets/poses/skeleton_idle1.png` for style; second `assets/portraits/bride_front.png` for identity.
```text
Use the first reference only for shared style and the second for the exact ghost bride identity. Redraw one front head-and-shoulders portrait at upper-chest crop: pale round face, huge black oval eyes with soft cyan underglow, tiny nose dot, no mouth, purple rose crown with green leaves, straight black hair with grey-teal strands, translucent teal-and-lilac veil, and black high collar. Dark-fantasy 2D cartoon portrait, soft dark outlines, thin warm-orange outer glow, rich stylised game art in the look of a polished Halloween mobile-game concept painting: layered depth, soft volumetric lighting, glowing light sources that tint nearby surfaces, fine surface texture, soft dark outlines, no flat cel shading, clean noise-free #FF00FF background. Do not include text, extra limbs, other characters, any known film or game character or item, a background other than flat magenta, full body, hands, skirt, bouquet, weapon, added mouth, or ground.
```
**Check:** The black oval eyes, crown, veil, and mouthless face remain identifiable at portrait size.

### `hunchback_front`
**Attach:** first `assets/poses/skeleton_idle1.png` for style; second `assets/portraits/hunchback_front.png` for identity.
```text
Use the first reference only for shared style and the second for the exact bell-tower hunchback identity. Redraw one head-and-shoulders portrait at upper-chest crop: grey-green skin, short spiky dark hair, thick angry brows, small tusks, frown, pointed ears, and broad shoulders in a torn olive vest, front view turned slightly left. Dark-fantasy 2D cartoon portrait, soft dark outlines, thin warm-orange outer glow, rich stylised game art in the look of a polished Halloween mobile-game concept painting: layered depth, soft volumetric lighting, glowing light sources that tint nearby surfaces, fine surface texture, soft dark outlines, no flat cel shading, clean noise-free #FF00FF background. Do not include text, extra limbs, other characters, any known film or game character or item, a background other than flat magenta, full body, hands, axe, bell, rope belt, weapons, or ground.
```
**Check:** Green skin, tusks, brows, and olive vest match the existing identity; the crop excludes axe and hands.

### `ui_frost_curse`
**Attach:** `assets/weapons/dart.png` for compact item style only.
```text
Draw one small frost-curse status icon: three pale ice crystals wrapped by one thin curl of cold mist, readable at tiny size, no face. Dark-fantasy 2D cartoon item, soft dark outlines, thin warm-orange outer glow, rich stylised game art in the look of a polished Halloween mobile-game concept painting: layered depth, soft volumetric lighting, glowing light sources that tint nearby surfaces, fine surface texture, soft dark outlines, no flat cel shading, centred on a clean noise-free #FF00FF background. Do not include text, extra limbs, other characters, any known film or game character or item, a background other than flat magenta, letters, numbers, hands, snowmen, ground, or cast shadow.
```
**Check:** The three-crystal silhouette remains legible at the intended UI icon size.

### `ui_bleed_drop`
**Attach:** `assets/weapons/dart.png` for compact item style only.
```text
Draw one small bleed status icon: one large glossy deep-red blood drop with a small highlight and two smaller drops below it, readable at tiny size, no gore. Dark-fantasy 2D cartoon item, soft dark outlines, thin warm-orange outer glow, rich stylised game art in the look of a polished Halloween mobile-game concept painting: layered depth, soft volumetric lighting, glowing light sources that tint nearby surfaces, fine surface texture, soft dark outlines, no flat cel shading, centred on a clean noise-free #FF00FF background. Do not include text, extra limbs, other characters, any known film or game character or item, a background other than flat magenta, weapons, skulls, splatter pools, hands, ground, or cast shadow.
```
**Check:** It reads as a three-drop silhouette at icon size without becoming gory.

### `ui_burn_flame`
**Attach:** `assets/fx/sprites/fx_flame_comet.png` for flame rendering only.
```text
Draw one small burn status icon: a compact warm-orange flame with three tongues, black inner ember shapes, and no blue-violet glow, readable at tiny size. Dark-fantasy 2D cartoon item, soft dark outlines, thin warm-orange outer glow, rich stylised game art in the look of a polished Halloween mobile-game concept painting: layered depth, soft volumetric lighting, glowing light sources that tint nearby surfaces, fine surface texture, soft dark outlines, no flat cel shading, centred on a clean noise-free #FF00FF background. Do not include text, extra limbs, other characters, any known film or game character or item, a background other than flat magenta, hands, sparkles, faces, ground, or cast shadow.
```
**Check:** The orange-and-black flame is distinct from the necromancer's purple projectile at UI scale.

### `ui_cross_curse`
**Attach:** `assets/weapons/dart.png` for compact item style only.
```text
Draw one small curse status icon: one simple dark wooden cross surrounded by a compact curl of black smoke and a tiny warm-orange ember, readable at tiny size and with no religious scene. Dark-fantasy 2D cartoon item, soft dark outlines, thin warm-orange outer glow, rich stylised game art in the look of a polished Halloween mobile-game concept painting: layered depth, soft volumetric lighting, glowing light sources that tint nearby surfaces, fine surface texture, soft dark outlines, no flat cel shading, centred on a clean noise-free #FF00FF background. Do not include text, extra limbs, other characters, any known film or game character or item, a background other than flat magenta, churches, people, hands, prayer symbols, ground, or cast shadow.
```
**Check:** The cross and smoke remain readable as one status icon without adding a scene.

### `ult_pip_socket`
**Attach:** `assets/ui/socket_special.png` for UI material style only.
```text
Draw one small empty ultimate-pip socket: a dark gothic-metal round recess with gold trim and a dim warm-orange inner rune, made to repeat three times in a row. Dark-fantasy 2D cartoon UI item, soft dark outlines, thin warm-orange outer glow, rich stylised game art in the look of a polished Halloween mobile-game concept painting: layered depth, soft volumetric lighting, glowing light sources that tint nearby surfaces, fine surface texture, soft dark outlines, no flat cel shading, centred on a clean noise-free #FF00FF background. Do not include text, extra limbs, other characters, any known film or game character or item, a background other than flat magenta, letters, numbers, faces, hands, filled gems, ground, or cast shadow.
```
**Check:** The socket stays readable when repeated three times and does not resemble a fourth pip.

### `ult_spectral_spear`
**Attach:** `assets/weapons/proj_spear_colab.png` for spear shape only.
```text
Draw one long spectral javelin pointing diagonally down-left, with a dark wooden shaft, pale bone-metal spearhead, and a thin translucent ghost trail in cyan-white; this is an effect item, not a held weapon. Dark-fantasy 2D cartoon sprite, soft dark outlines, thin warm-orange outer glow, rich stylised game art in the look of a polished Halloween mobile-game concept painting: layered depth, soft volumetric lighting, glowing light sources that tint nearby surfaces, fine surface texture, soft dark outlines, no flat cel shading, centred on a clean noise-free #FF00FF background. Do not include text, extra limbs, other characters, any known film or game character or item, a background other than flat magenta, hands, skeletons, blood, ground, or cast shadow.
```
**Check:** The spear silhouette remains clear during a falling animation and is distinct from the normal projectile.

### `ult_ricochet_shield`
**Attach:** `assets/weapons/small_shield.png`.
```text
Edit the attached small shield into one spinning ricochet ultimate shield, three-quarter tilt, with a short gold-orange motion arc and tiny black metal sparks; preserve its compact pumpkin-guard shield identity. Dark-fantasy 2D cartoon sprite, soft dark outlines, thin warm-orange outer glow, rich stylised game art in the look of a polished Halloween mobile-game concept painting: layered depth, soft volumetric lighting, glowing light sources that tint nearby surfaces, fine surface texture, soft dark outlines, no flat cel shading, centred on a clean noise-free #FF00FF background. Do not include text, extra limbs, other characters, any known film or game character or item, a background other than flat magenta, hands, a character, duplicate shields, blue-violet glow, ground, or cast shadow.
```
**Check:** The shield must read as one item in motion, not as a character-held shield or a second shield.

### `fx_shockwave_ring`
**Attach:** `assets/fx/sprites/fx_sonic_ring.png` for effect scale only.
```text
Draw one wide, thin ground-impact shockwave ring, a broken warm-orange and black ellipse with three short outward dust ticks, no blue-violet glow and no character. Dark-fantasy 2D cartoon effect sprite, soft dark outlines, thin warm-orange outer glow, rich stylised game art in the look of a polished Halloween mobile-game concept painting: layered depth, soft volumetric lighting, glowing light sources that tint nearby surfaces, fine surface texture, soft dark outlines, no flat cel shading, centred on a clean noise-free #FF00FF background. Do not include text, extra limbs, other characters, any known film or game character or item, a background other than flat magenta, hands, weapons, debris piles, ground plane, or cast shadow.
```
**Check:** The ellipse is thin and wide enough to read as a ground ring rather than a portal.

### `ui_hallucination_mark`
**Attach:** `assets/ui/icon_heavy.png` for compact UI style only.
```text
Draw one small hallucination turn-skip status icon: a single black spiral eye-shaped mark with three uneven warm-orange echo lines around it, readable at tiny size, no face and no blue-violet glow. Dark-fantasy 2D cartoon UI item, soft dark outlines, thin warm-orange outer glow, rich stylised game art in the look of a polished Halloween mobile-game concept painting: layered depth, soft volumetric lighting, glowing light sources that tint nearby surfaces, fine surface texture, soft dark outlines, no flat cel shading, centred on a clean noise-free #FF00FF background. Do not include text, extra limbs, other characters, any known film or game character or item, a background other than flat magenta, letters, numbers, hands, real eyes, skulls, ground, or cast shadow.
```
**Check:** It is legible at status-icon size and does not look like a poison or frost icon.

### `fx_ghostfire_orbit3` (conditional)
**Attach:** `assets/fx/sprites/fx_ghostfire_purple.png`.
```text
Edit the reference into exactly three separate compact ghost fires arranged in a loose orbit arc, each with the same established purple core and a thin warm-orange outer edge, no blue-violet mist, no pink sparks, and enough empty space to separate them after keying. Dark-fantasy 2D cartoon effect sprite, soft dark outlines, rich stylised game art in the look of a polished Halloween mobile-game concept painting: layered depth, soft volumetric lighting, glowing light sources that tint nearby surfaces, fine surface texture, soft dark outlines, no flat cel shading, centred on a clean noise-free #FF00FF background. Do not include text, extra limbs, other characters, any known film or game character or item, a background other than flat magenta, hands, a necromancer, more or fewer than three fires, ground, or cast shadow.
```
**Check:** Skip this prompt if three copies of the existing ghost-fire sprite already read clearly; otherwise count exactly three detached fires.

## C. How to use and generation order

1. Attach only the files named in each block, in the stated order: style first, identity second.
2. Generate one picture per prompt from the original reference, never from a previously edited output.
3. Key the noise-free `#FF00FF` background tightly and reject magenta spill or a wide leftover halo.
4. Compare characters against their attachment for face, hand, direction, scale, and feet baseline before accepting them.
5. Compare every item at its intended small in-game size; reject unreadable outlines, text, or accidental extra objects.
6. Order: knight unarmed; wizard release; necromancer pose and portrait; bride/hunchback portraits; feet chain; status/UI/ultimate icons; coins; conditional ghost-fire; retain existing ghost blows unless replacement is needed.
