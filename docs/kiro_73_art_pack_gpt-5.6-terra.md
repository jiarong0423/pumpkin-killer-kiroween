# Kiro 73 — Qwen art-gap design pack

## Recheck notes
- Confirmed missing: `bg_belltower.png`, `bg_pumpkin_field.png`, `unit_knight_unarmed.png`, `wizard_release.png`, `skeleton_charge2.png`, `bat_front.png`, and `necro_front.png`.
- `platform_coffin_blue.png` exists, but it is not a faithful cyan twin of the purple reference: it lacks the purple asset's readable lid runes and its flame treatment differs. Replace it with job A4 below.
- Reaper has `idle1`, `idle2`, `charge1`, and `charge3`; it lacks `charge2`, `release`, `empty`, and `hit`.
- `fence_black_intact.png` (709×850), damaged (759×871), and broken (823×929) have clearly different silhouettes when rendered at the current 290 px height. No redraw is recommended.
- The requested `docs/kiro_69_art_optimization.md` could not open because it is absent. `docs/kiro_task_69.md` is only its brief, so no completed art pack could be excluded beyond the current files.

## Shared Qwen production rules
- Generate exactly one output image per prompt. Never make a sprite sheet or a multi-cell contact sheet.
- Cut-outs are 1024×1024 PNGs on flat `#FF00FF`; full battlefield backgrounds are 1536×864, 16:9, with no magenta.
- Preserve thick near-black outlines, a thin warm-orange outer glow, and flat three-tone cel shading. No text, watermark, ground, cast shadow, photorealism, 3D, or painterly gradients.
- For a pose chain, attach the listed preceding frame as well as the stable idle reference. Do not use an earlier character's different phase as the only identity reference.

## A8. Bell-tower battlefield — `assets/env/bg_belltower.png`
- **Purpose:** selectable battlefield with the same playable ground horizon and central fence clearance as the graveyard.
- **Canvas/background:** 1536×864, full opaque 16:9 scene; no magenta.
- **Attach:** `assets/env/bg_graveyard.png`; `assets/env/fence_black_intact.png` only as a scale and clearance guide.
- **EN prompt:** Create one 1536×864 16:9 haunted bell-tower battlefield background. Same as `bg_graveyard.png`: the ground/playable floor begins at the same vertical height, the centre has a clear quiet fence zone, dark blue-violet night, thick clean near-black outlines, flat three-tone cel shading, warm orange candles and cyan ghost fire. Replace the distant castle with one crooked gothic bell tower on a hill, large moon behind it, bare trees and gravestones framing the edges, not the centre. No fence, character, UI, text, watermark, or magenta background.
- **中文提示詞：** 製作一張 1536×864、16:9 的鬧鬼鐘樓戰場背景。與 `bg_graveyard.png` 完全相同：地面／可站立地板開始的垂直高度相同，中央要留出乾淨安靜的圍籬位置，深藍紫夜晚、粗乾淨近黑描邊、平面三層賽璐璐、暖橙蠟燭和青色鬼火。遠方城堡改成山上的一座歪斜哥德鐘樓，後面有大月亮，枯樹和墓碑只框住兩側，不要放在中央。不要圍籬、角色、UI、文字、水印或洋紅背景。
- **Same-as lock:** Same ground-line height, centre clearance, camera framing, line weight, moonlit palette, and readable depth as `bg_graveyard.png`.
- **Acceptance:** exactly 1536×864; central 260 px-wide fence area remains visually uncluttered; its playable floor starts on the same y-coordinate as `bg_graveyard.png`.

## A8. Pumpkin-field battlefield — `(not published)`
- **Purpose:** second selectable battlefield that does not obscure projectiles, units, or the centre fence.
- **Canvas/background:** 1536×864, full opaque 16:9 scene; no magenta.
- **Attach:** `assets/env/bg_graveyard.png`; `assets/env/fence_black_intact.png` only for centre clearance.
- **EN prompt:** Create one 1536×864 16:9 moonlit pumpkin-field battlefield background. Same as `bg_graveyard.png`: identical ground/playable-floor height, identical camera framing and clear central fence zone. Show neat rows of glowing jack-o-lantern pumpkins and low crooked corn or dead vines receding at both sides, a huge moon, distant haunted farmhouse silhouette, bare trees, sparse cyan wisps, deep blue-violet night. Keep the centre calm and darker than the sides for projectile readability. No fence, character, UI, text, watermark, or magenta background.
- **中文提示詞：** 製作一張 1536×864、16:9 的月夜南瓜田戰場背景。與 `bg_graveyard.png` 完全相同：地面／可站立地板高度相同、鏡頭構圖相同、中央保留乾淨圍籬位置。兩側有整齊延伸的發光南瓜燈、低矮歪斜玉米或枯藤，大月亮、遠方鬼屋農舍剪影、枯樹、少量青色鬼火、深藍紫夜晚。中央要安靜且比兩側更暗，方便看飛行物。不要圍籬、角色、UI、文字、水印或洋紅背景。
- **Same-as lock:** Same ground-line height, centre clearance, camera framing, line weight, moonlit palette, and readable depth as `bg_graveyard.png`.
- **Acceptance:** exactly 1536×864; central 260 px-wide fence area remains clear; no foreground prop rises into the unit silhouette space at either side.

## A4. Cyan floating coffin — `assets/env/platform_coffin_blue.png`
- **Purpose:** player-side floating platform, a true colour twin of the higher-quality violet platform.
- **Canvas/background:** 1280×768; flat `#FF00FF` background.
- **Attach:** `assets/env/platform_coffin_purple.png`; existing `assets/env/platform_coffin_blue.png` only to show the output filename, not as style authority.
- **EN prompt:** Edit the attached purple floating coffin into one cyan version, 1280×768. Same as the reference in every shape and camera detail: exact three-quarter coffin view, dark wood plank layout, riveted metal corner plates, glowing runes across the lid, and ghost-flame drips below. Change only violet light, runes, and flames to luminous cyan. Preserve the same crop, proportions, near-black outlines, orange edge glow, and three-tone cel shading. Flat solid magenta `#FF00FF` background, no text or watermark.
- **中文提示詞：** 把附上的紫色浮空棺材編輯成一張青色版本，1280×768。每一個形狀和鏡頭細節都與參考圖完全相同：完全相同的四分之三棺材視角、深色木板排列、鉚釘金屬角片、棺蓋上的發光符文、下方滴落的鬼火。只把紫色光、符文和火焰改為明亮青色。保留相同裁切、比例、近黑描邊、橙色外光和三層賽璐璐。純色洋紅 `#FF00FF` 背景，不要文字或水印。
- **Same-as lock:** Same silhouette, wood cracks, rivet locations, rune count and placement, flame silhouette, scale, and camera as `platform_coffin_purple.png`.
- **Acceptance:** exactly 1280×768; cyan runes are present across the lid; overlay comparison finds matching coffin silhouette and corner-plate positions to the purple reference.

## Pose frame: wizard release — `(not published)`
- **Purpose:** the cannonball has just left the shoulder cannon; the throwing hand is empty and the wizard lunges left.
- **Canvas/background:** 1024×1024; flat `#FF00FF`.
- **Attach:** `assets/poses/wizard_charge3.png`, `assets/poses/wizard_idle1.png`, `assets/units/unit_wizard.png`.
- **EN prompt:** Edit this pumpkin cannon wizard into the release frame, 1024×1024. Same as the reference: exact same pumpkin face, purple hat, coat, shoulder cannon, body scale, feet baseline, strict side view facing LEFT, and the same support hand. The cannonball has left the cannon and is a short orange fire streak ahead toward the LEFT; the hand and cannon muzzle are empty. Body lunges forward, coat follows, face roars, small muzzle flash and smoke only at the muzzle. One character, full body. Flat solid magenta `#FF00FF` background, no ground, shadow, text, watermark, extra limbs, or extra weapon.
- **中文提示詞：** 把這個南瓜肩炮巫師編輯成釋放幀，1024×1024。與參考圖完全相同：相同南瓜臉、紫帽、外套、肩炮、身體大小、腳底基線、嚴格側面朝左、同一隻支撐手。炮彈已離開肩炮，向左前方是一小段橙色火焰軌跡；手和炮口是空的。身體向前衝、外套向後、臉在吶喊，炮口只保留小型閃光和煙。只有一個全身角色。純色洋紅 `#FF00FF` 背景，不要地面、影子、文字、水印、多餘手腳或多餘武器。
- **Same-as lock:** Same face, head size, cannon geometry, left-facing direction, baseline, and character crop as `wizard_idle1.png`.
- **Acceptance:** exactly 1024×1024; both feet touch the idle baseline; no cannonball remains in the cannon or hand.

## Pose frame: skeleton charge MID — `(not published)`
- **Purpose:** the middle hold-power step between the existing low and full spear charge frames.
- **Canvas/background:** 1024×1024; flat `#FF00FF`.
- **Attach:** `assets/poses/skeleton_charge1.png`, `assets/poses/skeleton_charge3.png`, `assets/poses/skeleton_idle1.png`, `assets/units/unit_skeleton.png`.
- **EN prompt:** Create the missing MID charge frame for this skeleton spearman, 1024×1024. Same as the attached charge1 and charge3 references: exact same skeleton face, armour, long wooden spear, scale, feet baseline, strict side view facing LEFT, and the same throwing hand. This is the consecutive middle moment: spear pulled farther behind the body than charge1 but less than charge3, torso leaning back halfway, face tightening, other hand empty at the side. One character, full body. Flat solid magenta `#FF00FF` background, no ground, shadow, text, watermark, extra limbs, or extra weapon.
- **中文提示詞：** 為這個骷髏長矛兵製作缺少的中段蓄力幀，1024×1024。與附上的 charge1 和 charge3 參考圖完全相同：相同骷髏臉、盔甲、長木矛、大小、腳底基線、嚴格側面朝左、同一隻投擲手。這是連續的中間動作：長矛比 charge1 更往身後拉、但比 charge3 少，軀幹向後傾一半，表情更緊繃，另一隻手空著放在側邊。只有一個全身角色。純色洋紅 `#FF00FF` 背景，不要地面、影子、文字、水印、多餘手腳或多餘武器。
- **Same-as lock:** Same face, spear hand, left-facing direction, scale, and baseline as the adjacent charge frames.
- **Acceptance:** exactly 1024×1024; spear-backward distance is visually between charge1 and charge3; feet and skull size align with `skeleton_idle1.png`.

## Reaper chain, 4 single-image jobs — `assets/poses/reaper_*.png`
- **Purpose:** complete the required eight-frame reaper set without changing the hooded skull face or purple-flame hand.
- **Canvas/background:** each 1024×1024; flat `#FF00FF`.
- **Stable attach to every job:** `assets/poses/reaper_idle1.png`, `assets/poses/reaper_idle2.png`, `assets/units/unit_reaper_idle.png`.

### 1. Reaper charge MID — `reaper_charge2.png`
- **Attach in addition:** `reaper_charge1.png`, `reaper_charge3.png`.
- **EN prompt:** Create one 1024×1024 consecutive MID charge frame for this hooded skull reaper. Same as the attached reaper references: exact same skull face, hood, robe, purple flame, raised throwing hand, left-facing strict side view, scale, and feet baseline. Purple flame and raised hand are farther back than charge1 but less far than charge3; body leans back halfway and face strains. Other hand stays empty at the side. Flat `#FF00FF`; no ground, shadow, text, watermark, extra limb, or new weapon.
- **中文提示詞：** 製作一張 1024×1024、連續的死靈法師中段蓄力幀。與附上的死靈法師參考圖完全相同：相同骷髏臉、兜帽、長袍、紫火、舉起的投擲手、嚴格側面朝左、大小和腳底基線。紫火和舉手比 charge1 更往後、但少於 charge3；身體向後傾一半，臉緊繃。另一隻手空著放在側邊。純色 `#FF00FF`，不要地面、影子、文字、水印、多餘肢體或新武器。
- **Same-as lock:** Same identity and baseline as idle; this is exactly between charge1 and charge3.
- **Acceptance:** 1024×1024; backward flame position lies between adjacent frames; same hood/skull silhouette at idle scale.

### 2. Reaper release — `reaper_release.png`
- **Attach in addition:** newly accepted `reaper_charge2.png`, `reaper_charge3.png`.
- **EN prompt:** Edit this same reaper into one 1024×1024 release frame. Same face, hood, robe, scale, feet baseline, strict side view facing LEFT, and same raised throwing hand as the references. The purple flame has fully left that hand as a short flame streak ahead to the LEFT; the raised hand is empty. The body lunges forward and the skull face roars. Other hand remains empty at the side. Flat `#FF00FF`; no ground, shadow, text, watermark, extra limb, or second flame in the hand.
- **中文提示詞：** 把同一個死靈法師編輯成一張 1024×1024 的釋放幀。臉、兜帽、長袍、大小、腳底基線、嚴格側面朝左，以及舉起的投擲手都與參考圖完全相同。紫火已完全離開那隻手，向左前方是一小段火焰軌跡；舉起的手是空的。身體向前衝，骷髏臉在吶喊。另一隻手仍空著放在側邊。純色 `#FF00FF`，不要地面、影子、文字、水印、多餘肢體或手中第二團火。
- **Same-as lock:** Same reaper face, hand, scale, and baseline as the accepted charge2 frame.
- **Acceptance:** 1024×1024; casting hand has no flame; flame streak points left and character retains the idle head size.

### 3. Reaper empty — `reaper_empty.png`
- **Attach in addition:** newly accepted `reaper_release.png`, `reaper_idle1.png`.
- **EN prompt:** Create one 1024×1024 empty stance for this same reaper. Same as `reaper_idle1.png` in face, hood, robe, strict left-facing side view, scale, crop, and feet baseline. Return to the calm idle body stance, but the former flame-holding raised hand is empty and lowered naturally; the other hand is also empty. No purple flame anywhere. Flat `#FF00FF`; no ground, shadow, text, watermark, extra limb, or new weapon.
- **中文提示詞：** 為同一個死靈法師製作一張 1024×1024 的空手站姿。臉、兜帽、長袍、嚴格左側面、大小、裁切和腳底基線都與 `reaper_idle1.png` 完全相同。回到平靜的待機身體姿勢，但原本拿火的舉手是空的並自然放低；另一隻手也空著。任何地方都不要紫火。純色 `#FF00FF`，不要地面、影子、文字、水印、多餘肢體或新武器。
- **Same-as lock:** Same idle pose and face; only the held flame is absent.
- **Acceptance:** 1024×1024; both hands are empty; feet and head align with `reaper_idle1.png`.

### 4. Reaper hit — `reaper_hit.png`
- **Attach in addition:** newly accepted `reaper_empty.png`, `reaper_idle1.png`.
- **EN prompt:** Create one 1024×1024 hit frame for this same reaper. Same skull face, hood, robe, strict side view facing LEFT, scale, crop, and feet baseline as the idle reference. He staggers backward slightly with eyes shut, both empty arms shielding his skull, robe reacting to the movement; no flame and no weapon. Keep one head and two arms only. Flat `#FF00FF`; no ground, shadow, text, watermark, gore, or extra characters.
- **中文提示詞：** 為同一個死靈法師製作一張 1024×1024 的受擊幀。骷髏臉、兜帽、長袍、嚴格側面朝左、大小、裁切和腳底基線都與待機參考圖完全相同。他微微向後踉蹌、眼睛閉上、兩隻空手護住骷髏頭，長袍跟著動作；不要火焰和武器。只保留一個頭和兩隻手臂。純色 `#FF00FF`，不要地面、影子、文字、水印、血腥或其他角色。
- **Same-as lock:** Same idle identity, body scale, and baseline; hit emotion is pain only.
- **Acceptance:** 1024×1024; eyes are shut and both hands shield the head; no flame, weapon, extra head, or extra limbs.

## Knight empty-hand base — `assets/units/unit_knight_unarmed.png`
- **Purpose:** make the thrown shield genuinely leave the Pumpkin Guard's hand.
- **Canvas/background:** 1024×1024; flat `#FF00FF`.
- **Attach:** `assets/units/unit_knight.png`, `assets/poses/knight_empty.png`.
- **EN prompt:** Edit this Pumpkin Guard into an unarmed base image, 1024×1024. Same as `unit_knight.png` in exact pumpkin face, black armour, cape, standing pose, camera angle, scale, crop, feet placement, near-black outline, and orange glow. Remove the shield completely. Both hands are visibly empty and relaxed; do not add another weapon, arm, or hand. Flat solid magenta `#FF00FF` background, no ground, shadow, text, or watermark.
- **中文提示詞：** 把這個南瓜盾衛編輯成空手基礎圖，1024×1024。與 `unit_knight.png` 完全相同：南瓜臉、黑色盔甲、披風、站姿、鏡頭角度、大小、裁切、雙腳位置、近黑描邊和橙色外光。完全移除盾牌。兩隻手都清楚空著且自然放鬆；不要新增武器、手臂或手。純色洋紅 `#FF00FF` 背景，不要地面、影子、文字或水印。
- **Same-as lock:** Same silhouette and feet as `unit_knight.png`; only shield pixels may change to empty-hand anatomy.
- **Acceptance:** exactly 1024×1024; overlay aligns head, torso, cape, and both boots; no shield or substitute weapon remains.

## Front portrait: Bat assassin — `assets/portraits/bat_front.png`
- **Purpose:** bottom-bar and large attacker portrait for the black cat assassin.
- **Canvas/background:** 1024×1024; flat `#FF00FF`.
- **Attach:** `assets/units/unit_bat.png`, `assets/poses/bat_idle1.png`, `assets/portraits/wizard_front.png`.
- **EN prompt:** Create one 1024×1024 front portrait of this black bat-cat assassin. Same as the attached unit: exact same black cat face, huge pointed ears with orange inner ears, stern eyes, black outfit, bat wings, orange accent, and warm orange outer glow. Face forward, crop from upper chest to ears like the existing front portraits, with no thrown weapon, no hands, no text. Thick near-black outlines and flat three-tone cel shading. Flat solid magenta `#FF00FF` background, no watermark.
- **中文提示詞：** 為這個黑色蝙蝠貓刺客製作一張 1024×1024 正面肖像。與附上的單位圖完全相同：黑貓臉、很大的尖耳和橙色耳內、嚴肅眼神、黑色服裝、蝙蝠翅膀、橙色點綴、暖橙色外光。正面朝前，像現有正面肖像一樣從上胸裁到耳朵，不要投擲武器、手或文字。粗近黑描邊、平面三層賽璐璐。純色洋紅 `#FF00FF` 背景，不要水印。
- **Same-as lock:** Same cat face markings, ear shape, eye expression, costume, and portrait crop language as the attached references.
- **Acceptance:** exactly 1024×1024; character faces forward; ear tips and shoulders remain inside canvas with no weapon or text.

## Front portrait: Necromancer — `(not published)`
- **Purpose:** bottom-bar and large attacker portrait for the purple-flame necromancer.
- **Canvas/background:** 1024×1024; flat `#FF00FF`.
- **Attach:** `assets/units/unit_reaper_idle.png`, `assets/poses/reaper_idle1.png`, `assets/portraits/reaper_front.png`.
- **EN prompt:** Create one 1024×1024 front portrait of this hooded skull necromancer. Same as the attached unit: exact same skull face, black-purple hood, purple eye-fire, robe collar, and thin cool rim light. Face forward, crop from shoulders to hood top like the existing front portraits. Show no hands, weapon, or floating flame. Thick near-black outlines, warm orange outer glow, and flat three-tone cel shading. Flat solid magenta `#FF00FF` background, no text or watermark.
- **中文提示詞：** 為這個兜帽骷髏死靈法師製作一張 1024×1024 正面肖像。與附上的單位圖完全相同：相同骷髏臉、黑紫色兜帽、紫色眼火、長袍衣領和細冷色邊光。正面朝前，像現有正面肖像一樣從肩膀裁到兜帽頂部。不要手、武器或漂浮火焰。粗近黑描邊、暖橙色外光和平面三層賽璐璐。純色洋紅 `#FF00FF` 背景，不要文字或水印。
- **Same-as lock:** Same skull proportions, hood opening, eye-fire colour, and crop hierarchy as `reaper_front.png`.
- **Acceptance:** exactly 1024×1024; face is frontal and recognisably matches the unit; no hand, flame, weapon, text, or watermark.

## A5. Fence-state audit — no generation job
- **Purpose:** intact, damaged, and destroyed wall-health states must read without labels.
- **Canvas/background:** existing keyed cut-outs, 709×850, 759×871, and 823×929; no replacement required.
- **Attach:** `fence_black_intact.png`, `fence_black_damaged.png`, `fence_black_broken.png` when main line playtests at the current 290 px drawn height.
- **Prompt / continuity:** none. The three inspected files have distinct silhouettes, structural loss, and decoration at that size; redraw prompts would add cost without a verified visual failure.
- **Acceptance:** render each at 290 px high; a reviewer identifies intact/damaged/broken in order without reading labels; verify the respective `wallHp` branches load these three filenames.

## Order, batching, and risk fallback
1. Generate both background jobs and the cyan coffin independently. These are parallel jobs, never one sheet.
2. Generate `wizard_release`, `skeleton_charge2`, and `unit_knight_unarmed` independently using their fixed references.
3. Generate the reaper chain strictly in order: charge2 → release → empty → hit, attaching the accepted previous frame each time.
4. Generate the two portraits independently after the character art has been accepted. Audit the existing fence states last in a real scene.
5. No prompts may be generated in one sprite sheet. The only safe batch is multiple independent Qwen jobs submitted separately.
6. **Face/style risk:** all character edits, especially the four reaper frames and two portraits, may drift in face or hand identity. Fallback: re-run only the failed single frame with the stable idle image and its accepted preceding frame attached, stating “copy this exact face, hood/ears, head size, baseline, and hand; change only the named pose.”
