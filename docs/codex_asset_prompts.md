# 給 Codex 生圖的素材指令（微調版）

依據：Codex 從概念圖拆出的提示詞檔（`(not published)`），再按我們的需求調整：身體與手臂分層、純白背景、不含任何文字數字與 UI、面向一致。

## 通用規則（每張圖都套用）

- 不含任何文字、數字、血條、按鈕、浮水印、標誌。
- 素材圖一律純白背景（#FFFFFF），主體完整不裁切，周圍留邊，無地面影子，無投影。
- 角色與武器面向右側，側面全身，站姿，Q 版比例。
- 風格後綴（接在每個提示詞後）：

```text
polished 2D cartoon game art, thick clean dark outlines, rich painterly shading, cute spooky chibi style, vivid saturated colors, deep navy and violet shadows, cyan ghost flames, warm pumpkin orange highlights, cinematic rim lighting, highly detailed, production-quality game asset
```

- 負面（若支援）：

```text
photorealistic, text, letters, numbers, UI, health bar, watermark, logo, cropped, blurry, low resolution, flat lighting, washed out colors, extra limbs, malformed hands, gore, blood, ground shadow, background scenery
```

## 檔名與尺寸

| 檔名 | 尺寸 | 說明 |
|---|---|---|
| bg_graveyard.png | 1920x1080 | 背景，不含地面、角色、平台、文字，這張不用白底 |
| ground_strip.png | 1920x240 | 可左右拼接的地面帶，白底 |
| platform_coffin_blue.png | 640x240 | 左側藍火棺材平台，白底 |
| platform_coffin_purple.png | 640x240 | 右側紫火棺材平台，白底 |
| platform_skull_plank.png | 640x240 | 骷髏木板平台，白底 |
| ghost_lantern.png | 512x640 | 白幽靈吊南瓜燈籠（空投），白底 |
| unit_bat_body.png / unit_bat_arm.png | 768x768 / 768x384 | 蝙蝠貓刺客 |
| unit_wizard_body.png / unit_wizard_arm.png | 768x768 / 768x384 | 南瓜巫師炮手 |
| unit_skeleton_body.png / unit_skeleton_arm.png | 768x768 / 768x384 | 骷髏長矛兵 |
| unit_knight_body.png / unit_knight_arm.png | 768x768 / 768x384 | 南瓜重裝盾兵 |
| proj_spear.png | 640x128 | 骷髏長矛飛行物，白底，矛尖向右 |
| fx_charge_glow.png | 512x512 | 蓄力光，白底 |
| fx_hit_spark.png | 512x512 | 命中火花，白底 |
| fx_impact_burst.png | 768x768 | 落地爆炸，白底 |

右隊角色由程式水平翻轉並換色，不另外生成。

## 場景

背景（bg_graveyard）：

```text
A haunted Halloween graveyard at night, enormous pale full moon behind a distant gothic castle with many pointed spires and narrow orange-lit windows, layered blue-gray clouds, flying black bats, huge twisted dead trees framing the upper left and upper right corners, atmospheric fog, deep navy sky. No ground, no characters, no platforms, no text. 16:9 side-view game background, symmetrical composition.
```

地面（ground_strip）：

```text
Seamless horizontal strip of uneven cracked stone cemetery ground, dark rocky soil on the cross-section, dead grass tufts on top, small broken gravestone stubs, tiny orange pumpkins and candle clusters along the edge, flat horizontal top surface, left and right ends tile seamlessly, isolated on solid white background.
```

## 平台與空投

藍色棺材平台：

```text
Floating wooden coffin-like magical platform, horizontal, rough dark planks, metal corner reinforcements, glowing cyan rune symbol on the flat top surface, blue magical flames around the edges, icy blue energy dripping downward, front view, isolated on solid white background.
```

紫色棺材平台：同上，把 cyan、blue 改成 violet、purple，符文改為紫色。

骷髏木板平台：

```text
Suspended wooden battle plank platform, dark weathered timber, metal brackets, a skull ornament on the front, several lit candles on top, pale blue ghostly flames and mist hanging underneath, flat top surface, front view, isolated on solid white background.
```

幽靈空投：

```text
Cute floating white ghost with a rounded sheet-like body, tiny black oval eyes, happy open mouth with a pink tongue, small ghost arms holding a thin rope, a metal-framed wooden jack-o'-lantern lantern box hanging below it with a warm orange glowing face, soft pale blue aura, isolated on solid white background.
```

## 角色（身體層與手臂層分開生成）

通用句：身體層最後加 `completely missing both arms and held weapons, shoulders left plain with no sleeves attached`；手臂層最後加 `single arm and weapon only, extending horizontally to the right, clear round shoulder joint at the left end`。

蝙蝠貓刺客，身體：

```text
Small black bat-like cat warrior, oversized pointed ears with orange inner ears, mischievous expression, dark cape and black outfit, tiny bat wings folded on the back, cute chibi proportions, orange and cyan rim lighting, standing side view facing right.
```

蝙蝠貓刺客，手臂：

```text
Black furry clawed arm in a dark sleeve holding a short silver dagger, pointing horizontally right.
```

南瓜巫師炮手，身體：

```text
Cute pumpkin-headed witch, glowing carved jack-o'-lantern face with a wide grin, tall purple witch hat, flowing dark purple cloak with gold trim, chibi Halloween game character, standing side view facing right.
```

南瓜巫師炮手，手臂：

```text
Arm in a purple sleeve carrying a large brass pumpkin cannon, orange firelight on the barrel, barrel pointing horizontally right.
```

骷髏長矛兵，身體：

```text
Small cartoon skeleton warrior, exposed white bones, round skull, minimal dark armor scraps, slightly hunched combat stance, playful spooky expression, chibi proportions, standing side view facing right.
```

骷髏長矛兵，手臂：

```text
Skeleton arm bones in a throwing grip, open bony hand with fingers curled as if holding a spear, no spear in the hand, arm extending horizontally right, clear round shoulder joint at the left end.
```

骷髏長矛（飛行物，另一張圖，出手後由程式沿彈道移動與旋轉）：

```text
A single long wooden spear with a sharp metal spearhead and a few wrapped leather bindings, horizontal, spearhead pointing right, slightly worn wood grain, faint cyan spectral glow on the tip, isolated on solid white background.
```

南瓜重裝盾兵，身體：

```text
Heavy pumpkin-headed knight, glowing jack-o'-lantern head with a green pumpkin stem, large dark cloak, bulky black armor, strong silhouette, chibi fantasy game character, standing side view facing right.
```

南瓜重裝盾兵，手臂：

```text
Armored arm holding a tall wooden shield with a pale cross symbol, shield held upright in front, clear round shoulder joint at the left end.
```

## 特效

```text
Magical charging energy swirl, blazing yellow core with violet and cyan sparks, radial swirling arcs, isolated on solid white background.
```

```text
Sharp 8-point golden yellow impact flash with tiny orange sparks and shards, cartoon combat hit effect, isolated on solid white background.
```

```text
Cannon blast impact explosion, billowing cartoon mushroom smoke puff in bright orange fading to deep purple edges, flying dark dirt clumps and glowing embers, thick outline, isolated on solid white background.
```

## 流程

1. 先生成背景與地面，鎖定色調。
2. 生成南瓜巫師身體，確認風格，再生成其他三位。
3. 生成四位的手臂層，與身體並排檢查肩膀接點。
4. 生成平台、空投、特效。
5. 每張交回後，由我在 Colab 去背（rembg）並記錄轉軸點，放入 repo 的 `assets/`。

UI 外框、血條、文字與數字由程式繪製，不請 Codex 生成。
