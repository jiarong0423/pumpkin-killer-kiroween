# 新職業美術提示詞、武器與大招（Kiro 任務 40，Part B）

日期：2026-11-09。對象：鬼娃新娘、鐘樓怪人、死神，加上四個舊職業的大招代表特效貼圖。機器可讀版本：`colab/jobs_new_classes.json`（26 個任務，tier `NEW2`）。數值來源：`docs/class_stats_judgement.md`。
我沒有產生或下載任何圖片，沒有碰 index.html、assets/、js/、scripts/，沒有用 git。所有「看起來會怎樣」都是**未驗證**，我看不到生成結果。

## 0. 跑之前先看（三個會讓任務失敗或變形的地方）

1. **要分兩階段。** Colab 腳本是從參照圖重畫，可用參照只有 skeleton、wizard、bat、knight、bar。新職業的姿勢圖需要「已核准的待機圖」當參照，否則會被舊角色拉歪。順序：先只跑 `run_order.stage1_idle_first` 三張（`ONLY = [...]`），挑出滿意的一張，主線把它複製到 Drive 的 inputs 並命名 `unit_bride.png`、`unit_hunchback.png`、`unit_reaper.png`，再跑 stage 2。直接用 `TIERS = ["NEW2"]` 會在缺檔時出錯。
2. **腳本不會用 negative。** 現在的 `colab/pumpkin_assets_job.py` 寫死 `negative_prompt=" "`，要改成 `negative_prompt=j.get("negative", " ")`。另外該檔輸出路徑用了 `{TAG}`，但檔內沒有定義 `TAG`（我只讀程式，沒有執行），第一次跑可能就 NameError，請主線確認。
3. **「三色調手繪陰影（three-tone painted shading）」不是現有風格字串。** 我 grep 了 `colab/jobs.json` 與 `docs/ui_asset_requests_2.md`，現有字串只有「thick clean outlines」「Flat solid magenta background (#FF00FF), no ground, no cast shadow, no text, no watermark」，沒有 three-tone。任務書要求加，所以我加在新字串裡；結尾的洋紅背景句子逐字沿用現有寫法。若新舊圖風格對不上，先拿掉 three-tone 那句再試。
4. **待機圖朝右（四分之三視角）是任務書指定的**，但 game_mode.md 說所有角色圖畫一次、朝左、對隊伍用鏡射，現有 `assets/units/*` 也朝左。待機朝右的圖進遊戲時要由主線決定是否鏡射。我照任務書做，並標為風險。

### 風格字串（JSON 內每個任務都帶自己的 style，對應腳本的 `j.get('style', spec['style'])`）

| 代號 | 用在 | 內容 |
|---|---|---|
| S_SIDE | 動作姿勢 | Keep the same chibi 2D dark-fantasy cartoon style as the reference image: thick clean dark outline with a thin orange rim glow, three-tone painted shading, big head and small body. Strict side view facing LEFT. Flat solid magenta background (#FF00FF), no ground, no cast shadow, no text, no watermark. |
| S_IDLE | 待機 | 同 S_SIDE，但 "Strict side view facing LEFT" 換成 "Three-quarter view facing RIGHT, relaxed standing pose, full body." |
| S_PORTRAIT | 肖像 | 同 S_SIDE，去掉 "big head and small body"，換成 "Head-and-shoulders bust portrait facing RIGHT." |
| S_ITEM | 武器與特效單件 | Dark-fantasy 2D cartoon art with thick clean dark outline and three-tone painted shading. One object drawn alone, centered, 16 px magenta margin. Flat solid magenta background (#FF00FF), no ground, no cast shadow, no text, no watermark.（特效再加 "Opaque colors, no soft glow into the background."） |

為什麼特效要「不透明」：洋紅背景要被去背，半透明的光暈會留下粉紅邊。半透明請由遊戲用 alpha 做。

## 1. 鬼娃新娘（Ghost Bride）

### 角色表

| 項目 | 內容 |
|---|---|
| 外型 | Q 版（大頭小身）。裂紋瓷娃娃臉，眼睛是中空黑洞，帶一點青色微光。黑色直長髮，破舊象牙白頭紗，頭上戴一圈枯萎的紫色玫瑰。破損的象牙白禮服，裙擺化成霧絲，沒有腳，輕微漂浮。雙手在身前輕握。 |
| 顏色 | 瓷白/象牙 `#efe6d8`、枯萎紫 `#a98bff`、眼睛青 `#5df2ee`、頭髮 `#14111a`，外輪廓沿用現有單位的細橘色外光 |
| 道具 | 只有玫瑰頭冠（沒有花束，攻擊是聲音，不丟東西） |
| 剪影 | 上窄下寬的鐘形裙擺加垂下的長髮與頭紗，與巫師的尖帽、盾衛的方肩都不同 |
| 原創性 | 避開電影裡的「科學怪人新娘」（閃電條紋髮）、「僵屍新娘」（藍皮膚）、恰吉類兇偶（紅髮、縫線兇偶）。我沒有看過這些角色的圖，只靠名字避開；owner 看到成品要自己再確認一次 |
| 參照 | wizard（長袍、大頭），待機核准後改用 `bride` |

### 圖片提示詞（每條 <= 80 字；完整 negative 在 JSON）

| id | ref | prompt | negative（精簡） | 風險 |
|---|---|---|---|---|
| bride_idle | wizard | Redraw the reference as a chibi ghost bride, original design: cracked porcelain-white doll face with hollow black eyes glowing faint cyan, long straight black hair, ragged ivory veil under a crown of withered violet roses, torn ivory gown whose hem fades into wisps with no feet, hands loosely clasped in front. Same height and proportions as the reference. | pumpkin head, witch hat, cannon, blue skin, lightning-streak hair, red dress | 中：參照圖的南瓜頭與帽子可能殘留。備案：Draw a new character in the same chibi style and size as the reference: a ghost bride with a cracked porcelain face, black hair, ivory veil and gown that fades into wisps. |
| bride_pose_windup | bride | Same ghost bride as the reference, strict side view facing LEFT: deep-breath wind-up, chest puffed out, head tilted slightly back, both hands cupped at the chest, mouth closed, veil lifting upward, hem wisps swirling. Same size and proportions. | sound waves, rings, music notes, speech bubble | 低到中 |
| bride_pose_release | bride | Same ghost bride, strict side view facing LEFT: a huge sustained scream, head thrown back, mouth wide open with a dark hollow throat, both arms flung wide with open empty hands, veil and hair blown forward, hem wisps streaming back. Same size and proportions. | sound waves, rings, music notes, speech bubble, lines around the mouth | **高**：模型常把聲波或音符畫進圖裡。備案：把 scream 換成 "a long loud shout", 並刪掉 "sustained"；音波是另一張貼圖 |
| bride_pose_hit | bride | Same ghost bride, strict side view facing LEFT: flinching backward, eyes squeezed shut, one hand raised to the cheek, a new crack across the porcelain face, veil whipped sideways, hem wisps scattering. Same size and proportions. | blood, sound waves | 低 |
| bride_portrait | bride | Head-and-shoulders bust portrait of this ghost bride, facing RIGHT: eerie calm half-smile, cracked porcelain skin, cyan glowing eyes, crown of withered violet roses, ragged veil, shoulders only. | full body, hands | 低 |

### 武器：音波（proj_soundwave）

| id | ref | prompt | negative | 風險與備案 |
|---|---|---|---|---|
| proj_soundwave | bar | Three nested curved arcs of a sound wave bulging to the LEFT, the direction of travel, each larger than the last, pale violet and white bold outlines with a thin cyan inner line, solid opaque colors, no transparency, drawn alone. | person, face, mouth, hands, music notes, text | 中：可能畫成半透明漸層、同心圓或像括號的文字。備案：Three concentric half-ring outlines, only the left half of each ring visible, pale violet, thick and opaque. |

### 大招：〈泣嫁輓歌〉 Bridal Dirge

| 項目 | 規則 |
|---|---|
| 觸發命中 | 先裝填（自己的回合），下一發音波**必須命中一個單位**（普攻命中：衰減後最多 27，平均 22.4）。被柵欄、天空盾擋下或落空 = 不觸發 |
| 後續打擊 | 三次「迴響環」，間隔 0.25 秒，圓心 = 觸發命中的單位中心（命中瞬間），半徑 260 px（200 px 站距時最多罩住 3 個單位）。每一環對圈內每個敵方單位造成 0.5 x D = **13.5**，沒有衰減 |
| 目標 | 圈內所有敵方單位（含觸發單位），不傷友軍 |
| 傷害算式 | 每個被罩住的單位 = 3 x 13.5 = 40.5 = 1.5 x 27。觸發的那個單位另外吃一次普攻命中（不算進 1.5 倍）：最多 27 + 40.5 = 67.5，低於最小血量 75，不會從滿血被秒殺 |
| 範例 | 敵方四個單位站 1160 / 1360 / 1560 / 1760。音波落在 1360 的骷髏（HP 100）中心 30 px 內：核心全額 27，骷髏剩 73。三環 x 13.5：骷髏再 -40.5 剩 32.5；1160 的盾衛（距 200 px，HP 120）-40.5 剩 79.5；1560 的巫師（距 200 px，HP 85）-40.5 剩 44.5；1760 的貓距 400 px，不受影響。合計 27 + 3 x 40.5 = 148.5 點傷害分散在三個單位上 |
| 次數 | 沿用全域：三格能量、整場最多 2 次、裝填後才能用 |

**3 秒節拍表**（飛行時間以典型 1.4 秒計，落點後的節拍綁在命中事件上）

| 時間 | 節拍 | 畫面與效果 |
|---|---|---|
| 0.00 到 0.45 | 切入 | 新娘肖像（`bride_portrait`）沿斜帶滑入，紫色調，名稱金字；兩側壓暗到 30%；點一下可跳過 |
| 0.45 到 0.75 | 蓄力 | 腳下 `sprite_rune_circle`；14 個 `fx_spirit_mist` 光點被吸向嘴；頭紗向上飄 |
| 0.75 | 出手 | 使用 `bride_pose_release`；`proj_soundwave` 放大 1.6 倍飛出 |
| 0.75 到 2.15 | 飛行 | 真實拋物線；音波殘影（每 0.06 秒一個 alpha 0.5 的拷貝） |
| 2.15 | 觸發命中 | 普攻命中演出 + 0.12 秒 hit-stop；`fx_dirge_ring` 在目標腳下展開 |
| 2.40 / 2.65 / 2.90 | 迴響 1 到 3 | 三個 `fx_dirge_ring` 由 40 px 擴到 260 px 半徑（寬 520 x 高 130 的橢圓）；圈內每個單位各冒一個 -13.5 與 `hit_sparks` |
| 2.90 到 3.30 | 餘波 | 被打到的單位頭紗/衣角晃動 0.4 秒；能量格熄滅；控制權回到玩家 |

**特效貼圖與粒子**

| 需要 | 內容 |
|---|---|
| 新貼圖 | `proj_soundwave`（武器）、`fx_dirge_ring`（迴響環），提示詞見 JSON |
| 現有預設 | `sprite_rune_circle`、`sprite_mist`、`weapon_charge_aura`、`weapon_rune_halo`、`hit_sparks`、`sprite_impact_flash`、`damage_number`、`landing_ring_dust` |
| 新預設（提案，js/particles.js 裡沒有） | `bride_sing_motes`：14 個 `fx_spirit_mist`，size 24 到 8，life 0.4，朝嘴部匯聚。`soundwave_afterimage`：每 0.06 秒複製一次投射物貼圖，alpha 0.5，life 0.25。`dirge_echo_ring`：`fx_dirge_ring` 由 40 px 擴到 260 px，life 0.5，alpha 0.9 到 0 |
| 預算 | 整個大招 <= 120 顆粒子（ultimates_design.md 的單一大招預算是 200） |

## 2. 鐘樓怪人（Bell-tower Hunchback）

### 角色表

| 項目 | 內容 |
|---|---|
| 外型 | Q 版，人類臉，咧嘴歪笑，一隻眼比另一隻大，亂蓬蓬深色頭髮；圓拱的駝背；苔綠色補丁背心套在灰米色襯衫上，繩索腰帶；手很大；雙臂抱著一口大青銅鐘 |
| 顏色 | 苔綠 `#5b6b3a`、灰米 `#d9c9a0`、青銅 `#b07a3a`、膚色 `#c99a6b`、頭髮 `#2a2018`，細橘色外光 |
| 道具 | 大青銅鐘（也是投射物）、繩帶 |
| 剪影 | 寬、矮、背部隆起，雙臂抱圓形大鐘，和長矛的細高線條、盾衛的方形都不同 |
| 原創性 | 迪士尼版的服色（紫、棕、紅）我刻意避開，改用綠與米色；沒有看過那些角色的圖，只靠名字避開 |
| 參照 | knight（寬矮身形），待機核准後改用 `hunchback` |

### 圖片提示詞

| id | ref | prompt | negative（精簡） | 風險 |
|---|---|---|---|---|
| hunchback_idle | knight | Redraw the reference as a chibi bell-tower hunchback, original design: human head with a big crooked grin and one eye larger than the other, tangled dark hair, strong rounded hunched back, moss-green patched vest over a dusty cream shirt, rope belt, big hands carrying a large bronze bell low in both arms. Same height as the reference. No pumpkin head, no armor, no shield. | pumpkin head, armor, shield, cape, red tunic, purple tunic | 中到高：鎧甲、南瓜頭、披風容易殘留。備案：Draw a new character in the same chibi style and size as the reference: a stocky hunchbacked bell ringer in a green patched vest holding a big bronze bell. |
| hunchback_pose_windup | hunchback | Same hunchback as the reference, strict side view facing LEFT: heavy wind-up, both arms swung far back and up over the head with open hands gripping nothing, knees bent, hump rounded, face straining. Same size and proportions. | bell, object in the hands, weapon | **高**：模型傾向保留鐘，或把手握成拳。備案 A：with open palms facing up as if lifting a heavy invisible ball。備案 B：接受「手上有鐘」的版本，當蓄力圖用，遊戲在蓄力時不再疊鐘貼圖 |
| hunchback_pose_release | hunchback | Same hunchback, strict side view facing LEFT: mighty overhand throw, both arms thrust forward and down with open empty hands, body lunging, hump forward, mouth roaring. Same size and proportions. | bell, object in the hands, weapon | **高**，同上 |
| hunchback_pose_hit | hunchback | Same hunchback, strict side view facing LEFT: staggering backward, both arms covering his head, hump hunched higher, eyes shut, rope belt swinging. Same size and proportions. | bell, blood | 低 |
| hunchback_portrait | hunchback | Head-and-shoulders bust portrait of this hunchback, facing RIGHT: big crooked grin, one eye larger, tangled dark hair, hump visible behind the shoulder, moss-green vest collar. | full body, bell | 低 |

### 武器：大青銅鐘（proj_bell）

| id | ref | prompt | negative | 風險與備案 |
|---|---|---|---|---|
| proj_bell | knight | A single large bronze church bell, rounded flared bowl with a thick riveted rim, a dark iron clapper hanging inside, a short rope loop on top, green verdigris patches and warm orange rim light, drawn alone, side view, slightly tilted. | person, hands, character, tower | 低到中：可能畫成鐘樓或加上人。備案：刪掉 "church"，改成 "bronze handbell the size of a barrel" |

### 大招：〈喪鐘三響〉 Triple Toll

| 項目 | 規則 |
|---|---|
| 觸發命中 | 下一發鐘**必須直擊一個單位**（普攻：20 傷害 + 擊退 50 px）。落空/被擋 = 不觸發 |
| 後續打擊 | 三次「鐘聲震波」，間隔 0.30 秒，圓心 = 鐘擊中的位置（擊退前的 x），半徑 240 px。每次對圈內每個敵方單位 0.5 x 20 = **10** |
| 目標 | 圈內所有敵方單位（含被直擊的），最多 3 個（200 px 站距） |
| 傷害算式 | 每單位 3 x 10 = 30 = 1.5 x 20；被直擊的單位另吃 20 + 擊退，合計 50 |
| 範例 | 鐘直擊 1560 的盾衛（HP 120）：-20 剩 100，被推到 1610。三響：盾衛 -30 剩 70；1360 的骷髏（距 200 px，HP 100）-30 剩 70；1760 的巫師（距 200 px，HP 85）-30 剩 55；1160 的單位距 400 px 不受影響。合計 20 + 3 x 30 = 110 |
| 備註 | 擊退 50 px 不影響圓心；被推出圈外的機會不存在（50 < 240 - 0） |

**3 秒節拍表**

| 時間 | 節拍 | 畫面與效果 |
|---|---|---|
| 0.00 到 0.45 | 切入 | `hunchback_portrait` 滑入，銅金色調，名稱金字 |
| 0.45 到 0.75 | 蓄力 | 鐘在手中發暖金光；鐘舌晃動；腳下塵土 |
| 0.75 | 出手 | `hunchback_pose_release`；`proj_bell` 慢速旋轉飛出（速度係數 0.8，注意飛行時間較長，節拍綁在命中事件） |
| 0.75 到 2.15 | 飛行 | 鐘尾跡用 `weapon_trail_shield` 的同風格銅色變體（新預設見下） |
| 2.15 | 觸發命中 | 重擊 + hit-stop 0.12 秒；鏡頭震動一次 |
| 2.45 / 2.75 / 3.05 | 三響 | 每響：`fx_toll_ring` 由 40 px 擴到 240 px 半徑（寬 480 x 高 120），圈內單位各冒 -10 與小 hit_sparks，畫面微震 (4, 3) px 0.18 秒 |
| 3.05 到 3.40 | 餘波 | 塵土落下，鐘落地冒煙；控制權回來 |

**特效貼圖與粒子**

| 需要 | 內容 |
|---|---|
| 新貼圖 | `proj_bell`、`fx_toll_ring` |
| 現有預設 | `impact_burst`、`hit_sparks`、`landing_ring_dust`、`smoke_puff`、`sprite_impact_flash`、`damage_number`、`weapon_trail_shield` |
| 新預設（提案） | `bell_toll_ring`：`fx_toll_ring` 由 40 px 擴到 240 px，life 0.45，alpha 0.9 到 0，另撒 10 顆銅金色小光點。`bell_trail`：每 3 步一顆暖金色小星，life 0.4 |
| 預算 | <= 100 顆粒子 |

## 3. 死神（Grim Reaper）

### 角色表

| 項目 | 內容 |
|---|---|
| 外型 | Q 版小死神。破爛的黑紫色連帽長袍，下襬漂浮、沒有腳；兜帽裡是蒼白的骨頭頭骨，兩團紫色火焰當眼睛；細瘦骨手；腰間掛一個小沙漏；一手把長鐮刀扛在肩上，另一手掌心朝上 |
| 顏色 | 袍子 `#1c1530`、袍邊紫 `#6b4bd6`、骨白 `#e8e0cc`、火焰紫 `#a98bff`、鐮刀刃 `#cdbdff`，細橘色外光 |
| 道具 | 鐮刀（大招用）、沙漏（裝飾）、骷髏頭（攻擊用投射物，由手掌冒出紫色鬼火） |
| 剪影 | 尖兜帽 + 漂浮長袍 + 長鐮刀斜線，與骷髏長矛兵的細高骨架、青色火焰明顯不同（紫 vs 青） |
| 原創性 | owner 給的兩張帶浮水印圖我沒有看到，也沒有照抄；設計只依 owner 文字（丟骷髏頭、三鐮斬） |
| 參照 | skeleton（骨架），待機核准後改用 `reaper` |

### 圖片提示詞

| id | ref | prompt | negative（精簡） | 風險 |
|---|---|---|---|---|
| reaper_idle | skeleton | Redraw the reference as a chibi grim reaper, original design: tattered black-violet hooded robe with a ragged floating hem and no feet, a pale bone skull face inside the hood with two violet flame eyes, thin bone hands, a small hourglass on the belt, one hand holding a long scythe with a pale violet blade resting on the shoulder, the other palm open. Same height as the reference. | spear, armor, helmet, cyan fire, cyan eyes, bare skeleton without a robe | 中：容易長得像原本的骷髏兵。備案：加 "a deep hood covering the top of the skull, a long black robe covering the whole body" 並刪掉 "thin bone hands" |
| reaper_pose_windup | reaper | Same grim reaper as the reference, strict side view facing LEFT: throwing wind-up, throwing arm cocked far back with an empty open hand, other arm forward, hood tilted, robe hem billowing, violet flame eyes flaring. No scythe, no skull in the hand. | scythe, skull in hand, spear, cyan fire | **高**：鐮刀或骷髏頭常留在手上。備案：用 "both hands empty, the scythe leaning far behind the body"，或接受有鐮刀的版本，只用在蓄力 |
| reaper_pose_release | reaper | Same grim reaper, strict side view facing LEFT: arm snapped forward and up with an open empty hand, robe whipping backward, hood flung back showing the skull, violet flames streaming from the eyes. No scythe. | scythe, skull in hand, spear, cyan fire | 中到高，備案同上 |
| reaper_pose_hit | reaper | Same grim reaper, strict side view facing LEFT: recoiling backward, hood slipping, jaw dropped, violet flame eyes squeezed, robe fluttering, bone hands raised. No scythe. | scythe, spear, cyan fire, blood | 低到中 |
| reaper_portrait | reaper | Head-and-shoulders bust portrait of this grim reaper, facing RIGHT: hooded bone skull, violet flame eyes narrowed, faint smirk, bone fingers at the hood edge. | full body, scythe, cyan fire | 低 |

### 武器：飛行骷髏頭與鐮刀

| id | ref | prompt | negative | 風險與備案 |
|---|---|---|---|---|
| proj_skull | skeleton | A single small flying human skull, cracked ivory bone, grinning with the jaw slightly open, facing LEFT, with a violet ghost-flame trail streaming behind it to the right, solid opaque flame shapes, drawn alone, horizontal. | body, ribcage, hands, cyan fire | 中：火焰尾巴可能變成半透明、洋紅邊。備案：只畫骷髏頭（刪掉 trail 句），尾跡由粒子預設 `skull_flame_trail` 負責 |
| reaper_scythe_item | skeleton | A single long grim reaper scythe, dark gnarled wooden shaft, one large curved pale-violet blade with a faint glowing edge, a ragged cloth strip tied below the blade, drawn alone, horizontal, blade at the LEFT end curving downward. | person, hands, skeleton | 中：刃的彎曲方向容易反。備案：把方向句改成 "blade at the left end, curving down like a sickle" |

### 大招：〈亡魂三鐮斬〉 Soul Scythe Triple

（owner 已定案：骷髏頭必須先命中，三次鐮斬合計 1.5 倍；單體連擊）

| 項目 | 規則 |
|---|---|
| 觸發命中 | 下一發骷髏頭**必須命中一個單位**（普攻 22；目標 <= 30% 血時 33）。落空/被擋 = 不觸發 |
| 後續打擊 | 三次鐮斬，同一個單位，間隔 0.18 秒，每斬 0.5 x 22 = **11**（不套用處決） |
| 目標 | 被骷髏頭命中的那一個單位（4v4 完成後可再討論是否擴大） |
| 傷害算式 | 斬擊合計 33 = 1.5 x 22；骷髏頭的 22 是普攻，不算進 1.5 倍；單體合計 55，低於最小血量 75 |
| 範例 | 骷髏頭命中巫師（HP 85）：-22 剩 63；三斬 -11 -11 -11 剩 30。若巫師只剩 25 血（29.4%，<= 30%）：骷髏頭處決 33 直接收掉，後面的斬擊不播 |

**3 秒節拍表**

| 時間 | 節拍 | 畫面與效果 |
|---|---|---|
| 0.00 到 0.45 | 切入 | `reaper_portrait` 滑入，紫色調，名稱金字 |
| 0.45 到 0.75 | 蓄力 | 手掌冒出紫色鬼火，骷髏頭在掌心旋轉；袍擺揚起；沙漏微光 |
| 0.75 | 出手 | `reaper_pose_release`；`proj_skull` 飛出 |
| 0.75 到 2.15 | 飛行 | `skull_flame_trail` 紫色火尾 |
| 2.15 | 觸發命中 | 骷髏頭撞擊 + hit-stop 0.12 秒；骷髏頭化成紫色鬼火散開 |
| 2.30 / 2.48 / 2.66 | 三斬 | 每斬在目標身上播 `fx_scythe_slash_arc`，角度依序 -35 度、+35 度、0 度（第三斬放大 1.3 倍）；每斬 -11 與小 hit_sparks；每斬 hit-stop 0.05 秒；`reaper_scythe_item` 在目標後方半透明劃過 |
| 2.66 到 3.10 | 餘波 | 目標身上殘留紫色火星 0.4 秒；`sprite_mist`；控制權回來 |

**特效貼圖與粒子**

| 需要 | 內容 |
|---|---|
| 新貼圖 | `proj_skull`、`reaper_scythe_item`、`fx_scythe_slash_arc` |
| 現有預設 | `hit_sparks`、`sprite_impact_flash`、`sprite_mist`、`sprite_ghostfire`（偏青，是否能染紫要看 `particles_draw.js`，我沒查）、`damage_number`、`ko_wisps` |
| 新預設（提案） | `skull_flame_trail`：每步 3 顆紫色（`#a98bff`）圓形粒子，size 14 到 4，life 0.35，不依賴貼圖。`scythe_slash_arc`：`fx_scythe_slash_arc` 依指定角度出現，life 0.16，size 1.0 到 1.3 倍，alpha 1 到 0 |
| 預算 | <= 90 顆粒子 |

## 4. 舊四職業的大招代表特效（各一張，讓每個職業都有招牌）

owner 只定了貓（5 枚手裡劍）與死神；其他三個職業的大招內容還沒定案（game_mode.md 的骷髏三連投、巫師毒彈、盾衛彈跳只是草案，盾衛的彈跳現在已經是普攻）。所以下面是「通用」的視覺，不綁死機制，owner 改規則時仍可用。docs/ultimates_asset_requests.md 已有舊設計的貼圖（`ult_spectral_spear`、`ult_poison_shell`、`ult_shuriken_shadow`、`ult_ricochet_shield`），這四張是不同用途的補充，名稱加 `ult2_` 以免重複。

| id | ref | 用途與假設 | prompt | 風險 |
|---|---|---|---|---|
| ult2_bat_volley_trail | bat | 貓 5 枚手裡劍扇形尾跡（owner 已定案） | Five thin curved motion streaks fanning out from one point on the right toward the left, each ending in a tiny silver four-pointed shuriken, violet and orange glow lines, solid opaque colors, drawn alone, horizontal. | 中：可能畫成一堆星星。備案：改成 "five straight diverging speed lines" |
| ult2_skeleton_ghost_javelin_trail | skeleton | 骷髏連投長矛的幽靈殘影（草案：三連投） | A long cyan ghost javelin streaking to the LEFT with three fading afterimage copies behind it and thin mist wisps, glowing spearhead, solid opaque pale colors, drawn alone, horizontal. | 中：殘影可能糊成一條。備案：只畫一根幽靈矛，殘影由粒子預設做 |
| ult2_wizard_toxic_burst | wizard | 巫師毒彈爆開（草案：毒彈） | A round burst of toxic green smoke with glowing spores, small drips and pumpkin-seed shapes flying outward, bright green core, drawn alone, side view, solid opaque colors. | 低到中 |
| ult2_knight_aegis_ring | knight | 盾衛通用金色符文震波環（大招內容未定案） | A flat elliptical ring of gold and orange runes seen from a low side angle, four small shield-shaped sparks orbiting it, dust on the rim, solid opaque colors, drawn alone. | 中：橢圓常被畫成正圓。備案：加 "very flat ellipse, three times wider than tall" |

## 5. 音效事件

先用現有檔案組合；`assets/audio/CREDITS.md` 把下列檔案都標為 CC0。**我沒有聽過任何檔案**，音色是否合適要靠耳朵驗收。

| 事件 | 狀態 | 用途 | 建議組合（現有檔案） |
|---|---|---|---|
| `charge` | 現有 | 蓄力 | 現有合成嗡聲 |
| `ultimate_ready` | 現有 | 三格滿 | 現有 |
| `impact_unit`、`impact_unit_heavy` | 現有 | 命中 | 現有 |
| `shield_block` | 現有 | 被天空盾擋下（大招不觸發） | 現有 |
| `throw_wave` | 新 | 新娘出手 | `ambient/ghost_moan3.ogg` 縮到 0.9 秒 + `sfx/chime_single.ogg` 音量 0.3 |
| `impact_wave` | 新 | 音波命中 | `sfx/chime_single.ogg` + `sfx/metal_bing.ogg` 音量 0.2 |
| `ult_dirge_echo` | 新（播三次） | 迴響環 | `ambient/ghost_moan1.ogg`，三次音高 0.94 / 1.00 / 1.06（沿用現有 +-6% 範圍） |
| `throw_bell` | 新 | 怪人出手 | `sfx/swish_throw.ogg` 音高 0.94 + `sfx/thwack_wood.ogg` 音量 0.3 |
| `impact_bell` | 新 | 鐘命中 | `sfx/bell_round.ogg` + `sfx/punch_heavy.ogg`（sfx 已有 bell_round.ogg） |
| `ult_toll` | 新（播三次） | 三響 | `sfx/bell_round.ogg` 音高 0.94 / 0.97 / 0.94 + `sfx/stone_ground_heavy.ogg` 音量 0.4 |
| `throw_skull` | 新 | 死神出手 | `sfx/whoosh_spear.ogg` 音高 1.06 + `sfx/bones_rattle.ogg` 音量 0.2 |
| `impact_skull` | 新 | 骷髏頭命中 | `sfx/punch_hit.ogg` + `sfx/bones_rattle.ogg` |
| `scythe_slash` | 新（播三次） | 鐮斬 | `sfx/swish_throw.ogg` 音高 1.06 + `sfx/metal_bing.ogg` 音量 0.2，三次之間間隔 0.18 秒 |
| `ult_cutin` | 新（程式合成） | 切入 | 沿用 ultimates_design.md 的程式合成提案 |

真正的缺口（需要新找 CC0，**我沒有搜尋也沒有驗證任何來源**）：一段真人合唱或女聲「啊」的長音（給新娘的蓄力與迴響用）。搜尋關鍵字建議：`opengameart choir ahh single note CC0`、`freesound female ahh sustained CC0`；找到後必須記錄來源頁、授權、sha256 到 CREDITS.md，由主線下載。

## 6. 容易失敗的提示詞總表（含備案）

| id | 風險 | 備案句型 |
|---|---|---|
| bride_idle | 南瓜頭/帽子殘留 | Draw a new character in the same chibi style and size as the reference: a ghost bride... |
| hunchback_idle | 鎧甲、南瓜頭殘留 | Draw a new character in the same chibi style and size as the reference: a stocky hunchbacked bell ringer... |
| reaper_idle | 長得像骷髏兵 | a deep hood covering the top of the skull, a long black robe covering the whole body |
| bride_pose_release | 畫進音波或音符 | a long loud shout（刪掉 sustained、scream） |
| hunchback_pose_windup / release | 保留鐘或握拳 | open palms facing up as if lifting a heavy invisible ball；或接受有鐘版本 |
| reaper_pose_windup / release | 鐮刀或骷髏頭留在手上 | both hands empty, the scythe leaning far behind the body |
| proj_soundwave | 半透明、像括號文字 | Three concentric half-ring outlines, only the left half visible |
| proj_skull | 火尾半透明、洋紅邊 | 只畫骷髏頭，尾跡用粒子 |
| fx_dirge_ring / fx_toll_ring / ult2_knight_aegis_ring | 橢圓被畫成正圓 | very flat ellipse, three times wider than tall |
| 全部待機圖 | 朝右四分之三與遊戲「朝左再鏡射」的規則不同 | 主線決定是否鏡射；若造成錯位，把 S_IDLE 的 "Three-quarter view facing RIGHT" 換成 "Three-quarter view facing LEFT" 重跑 |

## 7. 共通大招規則（三個新職業與舊職業一致）

- 裝填只能在自己的回合；三格能量、整場最多 2 次；沒有友軍傷害。
- 觸發命中必須是普攻命中。被柵欄、天空盾擋下或落空：本回合浪費，**能量與次數保留**（我的建議，owner 尚未回答，見 class_stats_judgement.md Q2）。
- 追加打擊每次 0.5 x D（三次），觸發命中不算進 1.5 倍。
- 單一單位從滿血最多承受：新娘 67.5、怪人 50、死神 55，都低於最小血量 75。
- 節拍表是「施放到控制權回來約 3 秒」，飛行時間會讓整體多出約 0.9 秒；省動畫模式（calm mode）縮到約 1.2 秒。

## 8. 六行總結

1. 三個新職業各有角色表、5 張姿勢/肖像提示詞、1 個武器提示詞，全部 <= 80 字，並各有 negative。
2. 每個新職業有大招：名稱、觸發命中、追加打擊、目標、傷害算式、實例、3 秒節拍、特效貼圖與粒子、音效事件。
3. `colab/jobs_new_classes.json` 共 26 個任務（待機 3、姿勢與肖像 12、武器 3、鐮刀 1、新大招貼圖 3、舊職業招牌 4），分三階段跑。
4. 音效只用現有 CC0 檔案重組，另有一個缺口（真人合唱長音）要新找。
5. 風險最高的是怪人和死神的「空手」姿勢、新娘的「張口尖叫」姿勢、各種橢圓特效環，備案句型在第 6 節。
6. 沒有改 index.html/assets/js/scripts，沒有 git，沒有產圖。

## 9. 我沒有驗證的事

- 沒有跑 Qwen-Image-Edit，所有提示詞都沒有實際生成過，風險標記是推測。
- 沒有看到 owner 的兩張死神參考圖，也沒有看過任何電影角色圖，「避開」只是靠名字與特徵描述。
- 音效檔我沒聽過；新事件的音色與音高疊法是提案。
- 新粒子預設（`bride_sing_motes` 等）不存在於 js/particles.js；`sprite_ghostfire` 能否染紫我沒查。
- 沒有讀 `docs/audio_sources.md`，授權只引用 `assets/audio/CREDITS.md` 的標示。
- `colab/pumpkin_assets_job.py` 的 `TAG` 問題是讀程式碼推得，沒有執行。
- 傷害數值來自 class_stats_judgement.md 的手算模型，未模擬。
