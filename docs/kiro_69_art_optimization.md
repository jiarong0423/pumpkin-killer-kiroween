# Kiro 69：美術設計優化，對齊概念稿

**比較基準。** 目標是 `(not published)`；現況是 `(not published)`。後者只含 Canvas，刻意不含 DOM 底欄，因此底欄不能以「畫面沒有」判定為未做。以下判斷也核對了 Q1 審核圖、`assets/ui/`、`assets/env/`、`assets/fx/sprites/`、`assets/units/`、`docs/game_style_brief.md`、`docs/art_style_guide.md`、`docs/pose_spec.md` 與回饋紀錄最後的 2026-11-10 條目。

## 缺口表

| 概念元素 | 現況 | 圖像觀察 | 建議修正 | 備註／應保留項目 |
|---|---|---|---|---|
| 左上《南瓜殺手》標誌 | 缺少 | 概念稿以暖橘手寫標誌和小南瓜建立第一眼識別；現況左側只有角色名牌。 | **ART + CODE**：做透明式切圖標誌，固定在左端飾框內，不壓到隊伍名牌。 | 新圖中的中文字必須由 owner 審稿，模型常會把字畫錯。 |
| 橫跨頂端的哥德式頂幅 | 部分具備 | 現況有左、中、右三塊真實金屬／石雕框，質感比舊的純繪製面板好；但三塊之間視覺上仍像三個獨立元件，概念稿是一條連續橫幅。 | **CODE**：在 1920 基準座標把三塊對齊成同一水平線，留出規律間距；不重畫既有 banner。 | **保留現況的青／紫隊色與真實邊框資產。** |
| Players / Agents 與存活菱形 | 部分具備 | 概念稿各有 4 個菱形；現況以名稱面板、青／紫菱形表達陣營，但目前 1v1 畫面不能驗證四人數量。 | **CODE**：4v4 流程確認後，菱形要對應活著單位，不可用作隱藏狀態。 | `ui_diamond_*` 已存在，不需要新圖。 |
| 回合與倒數計時 | 部分具備 | 概念稿中央清楚同時顯示「第 3 回合」與「08」；現況截圖可見「第 1 回合」和距離步數，未能在這一張靜圖確認倒數數字。 | **CODE**：把回合、倒數、距離分成不重疊的固定欄位；倒數優先於距離。 | 回饋紀錄說計時已放進 HUD，但此張圖無法獨立驗證。 |
| 風向與風力 | 部分具備，且現況更好 | 概念稿是箭頭加數字；現況已有大鬼吹霧，方向、霧量、速度可讀，符合 owner 最新「只用鬼表現風」的決定。現用圖仍像從燈籠鬼裁下來。 | **ART + CODE**：以 4 格專用吹風鬼替換裁切圖；程式只依風力切換、循環和移動霧。 | **保留無數字、以動態鬼和霧讀風的做法。** 不要回到箭頭／數字。 |
| 左右漂浮棺材平台與青／紫鬼火 | 缺少於現況舞台，但素材已具備 | `platform_coffin_blue.png` 與 `platform_coffin_purple.png` 已有粗黑線、藍／紫火、木棺和滴落輪廓；概念稿把它們放在高空左右以平衡大月亮。現況截圖未放入。 | **CODE**：先以現成兩張圖縮放、分層、慢速上下浮動；避開 HUD、拋物線及空中目標。 | 不必重生圖。這是以小成本最接近概念構圖的項目。 |
| 鬼以繩子吊著補給箱 | 部分具備 | `drop_ghost.png` 是帶繩的貨運鬼，`drop_crate.png` 是南瓜補給箱；概念稿是兩隻可愛鬼各吊一箱。現況截圖沒有空投事件。既定玩法目前是鬼／降落傘空投。 | **CODE；是否改成概念稿兩鬼吊箱需 owner 決定。** 把現有鬼、繩、箱錨點正確合成，先不要改規則。 | 不能因為好看就把既定的降落傘空投靜默換掉。 |
| 單位上方的編號菱形與 HP 數字 | 部分具備 | 概念稿在每個角色正上方放 1–4／A–D 菱形、`90/90` 與短 HP 條。現況可見隊側血條／能量點，但此截圖沒有可核對的「角色頭上編號＋HP 數字」完整組合。 | **CODE**：復用現成菱形，文字直接排在單位頭頂上方；單位、名字、血條、能量火不能互相覆蓋。 | 文字是資訊，不是以程式畫美術；菱形本體用既有圖。 |
| 角色剪影、兩隊面向和武器辨識 | 部分具備，部分現況更好 | 概念稿四種角色輪廓清楚。Q1 肖像與姿勢圖已有七種角色的色彩語言、厚近黑描邊與橘外緣；現況截圖的骨兵已可讀，但全角色動作尚未連貫。 | **ART + CODE**：優先裝入七組連貫動作表；程式只換幀、淡入和鏡像。 | **保留現有 2 頭身、粗邊、青／紫對隊色和一套左右鏡像規則。** |
| 前景地帶的墓碑、蠟燭、南瓜燈 | 部分具備 | 概念稿以密集前景帶壓住畫面底部。`ground_strip.png` 已有裂石台、左右墓碑、蠟燭、南瓜和青火；現況已有舞台邊緣與大墓碑，但前景層次較稀。 | **CODE**：把現成 `ground_strip.png` 分成下前景層，維持角色腳線、落點與可點擊區完全露出。 | 不要生一條更花的地面圖，先把已有資產擺對。 |
| 中央柵欄 | 部分具備 | 概念稿是低矮鐵欄與南瓜燈；現況中央是高而寬的鐵門／籠狀圖，辨識度強但把中間空域堵得太滿。`fence_black_intact.png` 有合適的黑鐵欄和南瓜吊飾。 | **CODE**：以既有 intact／damaged／broken 三態，按物理碰撞高度安放，讓月亮與彈道留空。 | **保留可破壞的三態機制。** 不可只為接近概念稿而改變碰撞尺寸。 |
| 落點塵圈 | 部分具備 | 概念稿有明亮橘黃落點圈和落箭。`ui_target_ring.png` 已存在，現況靜圖沒有投射後狀態可確認。 | **CODE**：命中／落地時在真實落點短暫顯示，跟著地面高度，淡出；不提供預測落點。 | 現有命中火花、衝擊和真實飛行軌跡已是概念稿沒有的回饋，應保留。 |
| 虛線瞄準弧線 | 缺少，且是正確缺少 | 概念稿顯示一條長的黃色預覽拋物線；現行規則明定投擲前不顯示瞄準線，現況只在投出後顯示真實飛行軌跡。 | **不修正。** | 這是「手感先於預覽」和公平規則，不能為了還原概念稿加回。 |
| 底部英雄肖像、名字和 HP | 部分具備，但本截圖不能視覺驗證 | 概念稿底欄把巫師大頭、名稱、`85/85`、動作、角度、蓄力、格子放成一條。`dock_frame.png`、四張既有肖像、HP 框、動作牌和插槽皆在；但本次 current canvas 特意不包括 DOM dock。 | **ART + CODE**：先在實頁以不同視窗寬度檢查 dock；為新三職補正面肖像，將已存在的框、按鈕與數值重新排到不重疊。 | 不能根據這張不含 dock 的截圖宣稱 dock 缺失。 |
| 鎖定按鈕 | 部分具備，但本截圖不能視覺驗證 | 概念稿右端橘色大「鎖定」。`lock_plate.png` 已有厚框石板／金邊底圖；回饋紀錄已確認點擊問題修正。 | **CODE**：在 DOM dock 中維持末端大目標和正常／hover／禁用三狀態，文字只用清楚的中文。 | 不需另生鎖定按鈕圖。 |
| 概念稿的 4v4 排列與完整底欄 | 缺少，屬未確認流程 | 概念是 4 對 4；目前是 1 對 1 原型。 | **OWNER DECISION + CODE**：等 owner 確認 4v4 回合／Lock 流程才排版。 | 不可先做一套看似完成的 4v4 操作流。 |

## 優化優先序

凍結日是 **2026-11-27**，交付日是 **2026-12-04**。凍結前只做可見、可回退、且不改規則的項目；生成圖必須先由 owner 審圖和核准既有 credit 使用。

| 優先 | 項目 | 玩家視覺收益 | 成本 | owner 決定？ | 所需美術／執行界線 |
|---|---|---|---|---|---|
| 1 | 七職的 18 格連貫動作表與切換 | 每次蓄力、出手、受擊都看得到因果，直接消除「站著，武器飛出」的最大落差。 | 大 | **要核准**生成與每組採用版本 | 新七張動作表；程式只讀格、交叉淡入、鏡像和依蓄力選格。詳見後段。 |
| 2 | 放入左右棺材平台 | 一眼回到概念稿的高低層次，補足現況中央天空空白。 | 小 | 否 | 只使用現有藍／紫棺材平台圖，程式浮動；不可遮住空中目標。 |
| 3 | 以專用四格吹風鬼取代裁切鬼 | 頂部風向成為活的場景訊號，而不是抽象 UI。 | 中 | **要核准**生成 | 一張四格鬼圖；霧線用現有／已排程特效，程式依風力切換節奏。 |
| 4 | 補上並安裝《南瓜殺手》標誌 | 建立品牌錨點，讓頂欄從角色資訊列變成遊戲介面。 | 小 | **要核准**中文標誌可讀性 | 一張 cut-out 標誌；程式固定放置、不能與左 banner 疊壓。 |
| 5 | 單位頭頂標記、HP 數字、短 HP 條的無重疊版面 | 多單位時立即知道「誰是誰、誰快倒」，也符合概念稿。 | 中 | 否 | 復用菱形和 HP 資產；程式布局與縮放，不做新美術。 |
| 6 | 使用既有黑鐵柵欄三態，降低中央高門的視覺重量 | 保留破壞目標，同時讓月亮、彈道和角色成為畫面主角。 | 中 | 否 | `fence_black_intact/damaged/broken.png`；程式位置須與引擎碰撞一致。 |
| 7 | 將現有地帶做成下前景層 | 墓碑、燭光、南瓜燈將畫面收邊，提升景深而不增加雜訊。 | 小 | 否 | `ground_strip.png`；只做前後景層級與裁切。 |
| 8 | 落點圈與真實飛行軌跡的時序 | 每一投都能讀到「落在哪、為何要修正」，支持玩家和 AI 從公開結果學習。 | 小 | 否 | 復用 `ui_target_ring.png` 與現有效果；絕不加投前預測弧。 |
| 9 | 把頂欄三段的基線、間距、回合／計時／距離欄位量化 | 消除「拼接感」，讓資訊掃讀順序固定為隊伍、回合、風、敵方。 | 小 | 否 | 無新圖；只調整既有 banner 和文字矩形。 |
| 10 | Dock 實頁視覺審核，並補齊新三職正面肖像 | 讓角色選擇和操作欄有一致的大頭識別，避免 4v4 前才發現 DOM 疊壓。 | 中 | **要核准**肖像 | 新娘、鐘樓怪人、死靈法師三格肖像；現有 dock、鎖定板和四張肖像保持。 |
| 11 | 現有鬼、繩、箱的空投合成校正 | 補給事件更接近概念稿，又不改已定的補給規則。 | 小 | 否 | 使用 `drop_ghost.png`、`drop_crate.png`、必要時 `drop_parachute.png`；位置錨點和運動是程式。 |
| 12 | 「兩隻鬼各吊箱」是否取代既定降落傘空投 | 視覺可更貼概念稿，但可能改變已確認玩法，收益不值得在 freeze 前冒險。 | 中 | **是，先決定** | owner 明確改規則後才需新合成或重畫；未決前不做。 |

### Freeze 前的收斂順序

1. 先完成第 2、5、7、8、9、11 項的定位與不重疊檢查。它們主要復用已驗證的圖片。
2. 同時讓 owner 審第 1、3、4、10 項的生成結果。沒有被選中的版本不安裝。
3. 新圖通過臉、尺寸、邊緣留白檢查後才接程式。第 1 項若在 11-27 前沒有合格整表，可保留既有靜態圖及單圖 fallback，不阻塞凍結。
4. 4v4 鎖定流程和空投形式留待 owner 確認，不能從概念稿倒推成已定規則。

## 靜態／UI 美術提示詞

以下英文文字給 owner 直接貼入 OpenAI 圖像模型。每個 prompt 都指定應附上的參考圖。所有切圖都採 `#FF00FF` 純洋紅底，交給既有 keying 流程處理，不手工塗改。

### A. 遊戲標誌：`1200 × 300`

附圖：`(not published)`，只取左上標誌的位置與構圖；不可複製概念稿中的其他場景物件。

```text
Create one cut-out game title logo for a Halloween artillery game, target canvas 1200 x 300 pixels. The attached concept mockup is composition reference only. Draw the exact Traditional Chinese title “南瓜殺手” as clear, correctly formed brush-lettered characters, plus one small smiling carved pumpkin charm at the lower right. Use thick clean near-black outlines, a thin warm orange outer glow, flat three-tone cel shading, dark charcoal shadow accents, and warm pumpkin-orange lettering. Keep the logo wide, compact, and readable at small HUD size. Center it with at least 10 percent empty margin. Flat solid magenta background #FF00FF for keying. No scene, no banner frame, no ground, no cast shadow, no extra text, no English letters, no watermark, no emoji, no photorealism, no 3D render, no painterly gradients.
```

### B. 風鬼四格動畫：`2048 × 512`，4 個等大格

附圖：`(not published)` 供 HUD 比例與現行吹風閱讀方式；`(not published)` 只供可愛幽靈語氣。每格 512 × 512，格與格之間留 24 px 洋紅間距。

```text
Create one four-cell horizontal sprite strip, target canvas 2048 x 512 pixels. Attach the current HUD screenshot for scale and the concept mockup only for the friendly ghost mood. Four equal 512 x 512 cells with 24 pixel magenta gutters: cell 1 sleeping calm wind ghost, eyes closed and no breath; cell 2 cheeks puffed, preparing to blow; cell 3 mouth open in a round O, blowing toward the RIGHT; cell 4 widest open mouth, body leaning back, blowing hardest toward the RIGHT. This is a dedicated wind-HUD character, not a lantern, not a crate carrier. Keep exactly the same cute ghost face, body proportions, outline thickness, and center position in all cells. Thick clean near-black outline, thin warm orange outer glow, flat three-tone cel shading, cold cyan rim light. Leave clear space in front of the mouth for code-driven mist. Flat solid magenta background #FF00FF in every cell, no ground, no cast shadow, no text, no labels, no arrows, no numbers, no watermark, no emoji, no extra characters, no photorealism, no 3D render.
```

程式可鏡像此圖表示另一方向，不能另做一套左右鬼。

### C. 三位新職的 Dock 正面肖像表：`3072 × 1024`，3 個等大格

附圖：`(not published)` 供同一批肖像風格與裁切比例；另附 `assets/units/unit_bride_idle.png`、`assets/units/unit_hunchback_idle.png`、`assets/units/unit_reaper_idle.png` 作為各角色臉部鎖定來源。

```text
Create one three-cell horizontal front-portrait sheet for a dark-fantasy 2D cartoon game UI, target canvas 3072 x 1024 pixels. Attach the existing portrait sheet for crop and style, plus the three named idle-character references for exact face identity. Make three equal 1024 x 1024 cells with 32 pixel solid-magenta gutters. Cell 1: ghost bride, front-facing head and shoulders, same pale face, large dark eyes, flower crown, pale teal veil, and calm haunted expression as her attached reference. Cell 2: bell-tower hunchback, front-facing head and shoulders, same grey-green heavy face, flat hairline, ragged clothes, and rusty axe handle only if it stays behind the shoulder; exactly one head. Cell 3: necromancer, front-facing hooded skull head and shoulders, same skull face and dark indigo robe, one small purple flame above the raised hand, no scythe. Each portrait has chibi two-heads-tall design language, thick clean near-black outlines, a thin warm orange outer glow, flat three-tone cel shading, and the character’s one saturated accent colour. Keep each head large and centered with 12 percent margin. Flat solid magenta background #FF00FF in every cell. No ground, no cast shadow, no names, no letters, no watermark, no emoji, no extra limbs, no extra heads, no photo, no 3D render, no painterly gradient.
```

## 連貫動作提示詞

### 共用版面與驗收規格

`docs/kiro_task_63.md` 和 `(not published)` 在此工作區**找不到，無法開啟**，因此無法逐字重用前一版文字。以下依本任務指定的 4／6／5／3 格格式，並按 `docs/pose_spec.md` 與最新回饋統一成單一版本。

每位角色各生一張 **3072 × 2048** 圖：6 欄 × 4 列、每格 **512 × 512**、格間 **16 px** `#FF00FF` 間距。

- 第 1 列為 `idle 1–4`。是可以無縫反覆的小呼吸／小火焰循環，第四格自然接回第一格。
- 第 2 列為 `charge 1–6`。第 1–2 格是低蓄力、第 3–4 格是中蓄力、第 5–6 格是滿蓄力；每格都只比前格多一小步。
- 第 3 列為 `throw 1–5`。第 1 格是釋放瞬間；持有的投擲物在這一格起已離手。後四格是小幅跟隨、回正與無武器姿勢，不得把物品變回手上。
- 第 4 列為 `hit 1–3`。由受擊一瞬、踉蹌、防護頭部構成；第 4–6 格純洋紅空白。
- 除臉部表情在冷靜、吃力、吼叫、疼痛間的必要改變外，**臉、頭型、比例、衣服、顏色、手、腳線、朝向均須相同**。所有角色嚴格側面朝左，投擲也朝左。對手只由程式 `scale(-1, 1)` 鏡像，絕不畫另一套方向。
- 每格的角色完整置中，腳底在完全相同的 baseline；物品可以越過身體前方，但不得切到格邊。所有格都是一個角色，不能混入其他角色。
- 美術只在模型圖中產生；程式只做切格、移動、淡化與鏡像。釋放／空手規則由圖和程式共同遵守。

若只有一格錯，不應要求整張重畫。owner 可附原始表並指出列／欄，例如：

```text
Redo only row 2, column 5 of this attached sprite sheet. Keep every other cell unchanged. Match the exact same face, scale, left-facing direction, throwing hand, baseline, outline, colours, and adjacent-frame motion. Replace only the incorrect cell; use a flat solid magenta #FF00FF background and preserve the 16 pixel gutters.
```

### 1. 骷髏長矛兵

附圖：`assets/units/unit_skeleton.png` 作為臉、比例、服裝和真實持矛手的唯一角色參考；`(not published)` 只供現有姿勢品質比對。

```text
Create one 3072 x 2048 pixel sprite sheet for the skeleton spear soldier. Attach unit_skeleton.png as the exact character reference. Use 6 equal columns and 4 equal rows, 512 x 512 pixels per cell, with 16 pixel solid-magenta #FF00FF gutters. Strict side view facing LEFT in every cell; the throw goes LEFT. Keep the exact same skull face, cyan eye fire, armour, body size, scale, proportions, feet baseline, and the same real throwing hand in every cell. One full-body chibi two-heads-tall character per cell, centered with margin. Row 1, cells 1 to 4: a seamless idle breathing loop, long wooden javelin resting on the shoulder in the real throwing hand. Row 2, cells 1 to 6: six consecutive charge steps, low in cells 1 to 2, mid in cells 3 to 4, full in cells 5 to 6; pull the javelin farther behind the body each step, lean back gradually, calm face to strained face. Row 3, cells 1 to 5: five consecutive throw steps; at cell 1 the javelin has left the hand and travels LEFT, the hand is empty, the body lunges forward, face roars; cells 2 to 5 are small follow-through and recovery steps with an empty hand. Row 4, cells 1 to 3: three consecutive hit steps, startled impact, stagger, then eyes shut with arms protecting the skull; cells 4 to 6 are blank #FF00FF. Thick clean near-black outline, thin warm orange outer glow, flat three-tone cel shading, no ground, no shadow, no text, no labels, no watermark, no extra limbs, no extra head, no weapon in empty-hand frames, no photo, no 3D render, no painterly gradient.
```

### 2. 南瓜巫師砲手

附圖：`assets/units/unit_wizard.png` 作為唯一臉、南瓜雕刻、帽子、斗篷和肩砲參考；`(not published)` 只供現有姿勢品質比對。

```text
Create one 3072 x 2048 pixel sprite sheet for the pumpkin wizard gunner. Attach unit_wizard.png as the exact character reference. Use 6 equal columns and 4 equal rows, 512 x 512 pixels per cell, with 16 pixel solid-magenta #FF00FF gutters. Strict side view facing LEFT in every cell; the shot goes LEFT. Keep the exact same carved pumpkin face, hat, robe, shoulder cannon, body size, scale, proportions, feet baseline, and cannon-side hand in every cell. One full-body chibi two-heads-tall character per cell, centered with margin. Row 1, cells 1 to 4: a seamless idle breathing loop, shoulder cannon held in its normal resting position. Row 2, cells 1 to 6: six consecutive charge steps, low in cells 1 to 2, mid in cells 3 to 4, full in cells 5 to 6; the cannon draws back slightly with the body, muzzle glow grows, body leans back, face changes calm to strain. Row 3, cells 1 to 5: five consecutive firing steps; at cell 1 a cannonball has left the muzzle and travels LEFT, with muzzle flash and smoke, the shoulder cannon remains worn but its barrel holds no cannonball, the body lunges and face roars; cells 2 to 5 are small recoil, follow-through, and recovery steps. Row 4, cells 1 to 3: three consecutive hit steps, impact, stagger, then eyes squeezed shut with arms shielding the head; cells 4 to 6 are blank #FF00FF. Thick clean near-black outline, thin warm orange outer glow, flat three-tone cel shading, no ground, no shadow, no text, no labels, no watermark, no extra limbs, no extra head, no loose hand-held weapon, no photo, no 3D render, no painterly gradient.
```

### 3. 蝙蝠貓刺客

附圖：`assets/units/unit_bat.png` 作為唯一臉、耳朵、翼、腰包、服裝和持鏢手參考；`(not published)` 只供現有姿勢品質比對。

```text
Create one 3072 x 2048 pixel sprite sheet for the black cat-bat assassin. Attach unit_bat.png as the exact character reference. Use 6 equal columns and 4 equal rows, 512 x 512 pixels per cell, with 16 pixel solid-magenta #FF00FF gutters. Strict side view facing LEFT in every cell; the throw goes LEFT. Keep the exact same cat face, orange inner ears, bat wings, dark assassin clothes, belt bag, body size, scale, proportions, feet baseline, and same throwing hand in every cell. One full-body chibi two-heads-tall character per cell, centered with margin. Row 1, cells 1 to 4: a seamless low-crouch idle loop, one small shuriken held in the throwing hand and the belt bag visible. Row 2, cells 1 to 6: six consecutive fast charge steps, low in cells 1 to 2, mid in cells 3 to 4, full in cells 5 to 6; draw the shuriken hand back in small increments, coil the body, ears and wings react subtly, calm face to fierce strain. Row 3, cells 1 to 5: five consecutive flick-throw steps; at cell 1 the shuriken has left the hand and travels LEFT, the throwing hand is empty, the belt bag remains, body snaps forward and face roars; cells 2 to 5 continue the small fast follow-through and recover with empty hand. Row 4, cells 1 to 3: three consecutive hit steps, flinch, stumble, then eyes shut and arms protect the head; cells 4 to 6 are blank #FF00FF. Thick clean near-black outline, thin warm orange outer glow, flat three-tone cel shading, no ground, no shadow, no text, no labels, no watermark, no extra limbs, no extra head, no weapon in empty-hand frames, no photo, no 3D render, no painterly gradient.
```

### 4. 南瓜重盾騎士

附圖：`assets/units/unit_knight.png` 作為唯一南瓜臉、盔甲、披風、盾牌和持盾手參考；`(not published)` 只供現有姿勢品質比對。

```text
Create one 3072 x 2048 pixel sprite sheet for the pumpkin heavy shield knight. Attach unit_knight.png as the exact character reference. Use 6 equal columns and 4 equal rows, 512 x 512 pixels per cell, with 16 pixel solid-magenta #FF00FF gutters. Strict side view facing LEFT in every cell; the thrown small shield goes LEFT. Keep the exact same pumpkin face, dark armour, cape, small shield, body size, scale, proportions, feet baseline, and same shield-holding hand in every cell. One full-body chibi two-heads-tall character per cell, centered with margin. Row 1, cells 1 to 4: a seamless solid idle loop, small shield held in the throwing hand. Row 2, cells 1 to 6: six consecutive charge steps, low in cells 1 to 2, mid in cells 3 to 4, full in cells 5 to 6; pull the shield back farther behind the body in each step, body leans back, face calm to straining. Row 3, cells 1 to 5: five consecutive throw steps; at cell 1 the small shield has left the hand and spins sideways like a flipping coin toward LEFT, the hand is empty, body lunges and face roars; cells 2 to 5 are small follow-through and recovery steps with empty hand. Row 4, cells 1 to 3: three consecutive hit steps, impact, stagger, then eyes shut with arms protecting the pumpkin head; cells 4 to 6 are blank #FF00FF. Thick clean near-black outline, thin warm orange outer glow, flat three-tone cel shading, no ground, no shadow, no text, no labels, no watermark, no extra limbs, no extra head, no shield in empty-hand frames, no floating defend shield, no photo, no 3D render, no painterly gradient.
```

### 5. 鬼娃新娘

附圖：`assets/units/unit_bride_idle.png` 作為唯一臉、花冠、面紗、裙子和手勢參考；`(not published)` 只供現有姿勢品質比對。

```text
Create one 3072 x 2048 pixel sprite sheet for the original ghost bride. Attach unit_bride_idle.png as the exact character reference. Use 6 equal columns and 4 equal rows, 512 x 512 pixels per cell, with 16 pixel solid-magenta #FF00FF gutters. Strict side view facing LEFT in every cell; her sound-wave attack goes LEFT. Keep the exact same pale face, large dark eyes, flower crown, pale teal veil, black dress, body size, scale, proportions, feet baseline, and same leading hand in every cell. One full-body chibi two-heads-tall character per cell, centered with margin. Row 1, cells 1 to 4: a seamless gentle ghostly idle loop, hands empty, veil and hem moving only slightly. Row 2, cells 1 to 6: six consecutive singing charge steps, low in cells 1 to 2, mid in cells 3 to 4, full in cells 5 to 6; leading hand and upper body draw back in small increments, mouth opens gradually, calm face to strained haunting song. Row 3, cells 1 to 5: five consecutive sound-wave release steps; at cell 1 a translucent circular sound wave has left her open mouth and travels LEFT, both hands are empty, body leans forward and face gives a strong scream; cells 2 to 5 are small follow-through and recovery steps, no bouquet, no held weapon. Row 4, cells 1 to 3: three consecutive hit steps, flinch, sway, then eyes shut with arms protecting the head; cells 4 to 6 are blank #FF00FF. Thick clean near-black outline, thin warm orange outer glow, flat three-tone cel shading, no ground, no shadow, no text, no labels, no watermark, no extra limbs, no extra head, no copied film character, no photo, no 3D render, no painterly gradient.
```

### 6. 鐘樓怪人

附圖：`assets/units/unit_hunchback_idle.png` 作為唯一臉、灰綠身形、破衣、巨斧和雙手參考；`(not published)` 只供現有姿勢品質比對。

```text
Create one 3072 x 2048 pixel sprite sheet for the bell-tower hunchback. Attach unit_hunchback_idle.png as the exact character reference. Use 6 equal columns and 4 equal rows, 512 x 512 pixels per cell, with 16 pixel solid-magenta #FF00FF gutters. Strict side view facing LEFT in every cell; the giant axe goes LEFT. Keep the exact same one grey-green head, flat hairline, grumpy face, ragged clothes, giant rusty battle axe, body size, scale, proportions, feet baseline, and the same two hands on the axe in every cell. One full-body chibi two-heads-tall character per cell, centered with margin. Row 1, cells 1 to 4: a seamless heavy idle breathing loop, giant axe held securely in both hands. Row 2, cells 1 to 6: six consecutive two-handed charge steps, low in cells 1 to 2, mid in cells 3 to 4, full in cells 5 to 6; pull the axe farther back behind the body in each step, weight shifts back, face changes calm to hard strain. Row 3, cells 1 to 5: five consecutive two-handed throw steps; at cell 1 the axe has left both hands and travels LEFT, both hands are empty, body lunges and face roars; cells 2 to 5 are small follow-through and recovery steps with empty hands. Row 4, cells 1 to 3: three consecutive hit steps, impact, stagger, then eyes shut with arms protecting the head; cells 4 to 6 are blank #FF00FF. Thick clean near-black outline, thin warm orange outer glow, flat three-tone cel shading, no ground, no shadow, no text, no labels, no watermark, no extra limbs, exactly one head, no axe in empty-hand frames, no neck bolts, no forehead stitches, no photo, no 3D render, no painterly gradient.
```

### 7. 死靈法師

附圖：`assets/units/unit_reaper_idle.png` 作為唯一頭骨臉、帽兜、深靛法袍、抬起手和紫焰參考；`(not published)` 只供現有姿勢品質比對。

```text
Create one 3072 x 2048 pixel sprite sheet for the necromancer. Attach unit_reaper_idle.png as the exact character reference. Use 6 equal columns and 4 equal rows, 512 x 512 pixels per cell, with 16 pixel solid-magenta #FF00FF gutters. Strict side view facing LEFT in every cell; the flame shot goes LEFT. Keep the exact same single skull face, hood, dark indigo robe, body size, scale, proportions, feet baseline, and same raised casting hand in every cell. One full-body chibi two-heads-tall character per cell, centered with margin. Row 1, cells 1 to 4: a seamless idle loop, one small upright purple flame hovering above the raised fingertips, other hand empty. Row 2, cells 1 to 6: six consecutive charge steps, low in cells 1 to 2, mid in cells 3 to 4, full in cells 5 to 6; draw the raised casting hand back a little farther each step, the purple flame intensifies but remains one flame, body leans back, calm face to strain. Row 3, cells 1 to 5: five consecutive release steps; at cell 1 the casting arm is extended forward with palm DOWN, the purple flame has been shot out as a horizontal comet toward LEFT, the hand is completely empty, body lunges and face roars; cells 2 to 5 are small follow-through and recovery steps with empty hand. Row 4, cells 1 to 3: three consecutive hit steps, flinch, stagger, then eyes shut with arms protecting the skull; cells 4 to 6 are blank #FF00FF. Thick clean near-black outline, thin warm orange outer glow, flat three-tone cel shading, no ground, no shadow, no text, no labels, no watermark, no extra limbs, exactly one head, no scythe, no second flame, no flame in release or recovery hand, no photo, no 3D render, no painterly gradient.
```

## 不要做

- **不要重開投前虛線瞄準弧或預測落點。** 投出後的真實軌跡與落點圈足夠，預覽違反既定手感與公平規則。
- **不要顯示敵方私密盾牌點、私密路徑或任何 agent 看不到的資訊。** 圖像品質不能凌駕公平性。
- **不要讓 HUD、頭頂數字、火焰、空投、平台、彈道互相覆蓋。** 每個元件先有量測矩形與縮放規則，再談特效。
- **不要用 emoji 當鬼、南瓜、按鈕或狀態圖。** 也不要用程式手繪新美術；程式只能移動、切格、淡化、鏡像既有圖。
- **不要為了概念稿一次重畫現有好素材。** 棺材平台、地帶、柵欄三態、dock 框、鎖定底板、菱形和落點圈已存在，優先正確安放。
- **不要在 freeze 前未經確認建 4v4 Lock 流程，或把降落傘空投改成兩鬼吊箱。** 兩者都還需要 owner 決策。
- **不要在七職動作圖中接受換臉、換手、換方向、變大、腳線漂移、雙頭、釋放後手上仍有武器。** 任一錯誤只重做該一格。

## 無法驗證項目

- `docs/kiro_task_63.md` 與 `(not published)` 不存在於此工作區，**無法開啟**。因此無法復用它們的原文或確認其精確格位說明；本文件採用本任務明列的 idle 4、charge 6、throw 5、hit 3 格規格。
- `top_hud_now.png` 不含 DOM dock，故無法從該圖驗證底欄、鎖定按鈕在實際頁面上的最終視覺；本文件僅依現有 dock 資產與回饋紀錄判為部分具備。
- 目前靜態畫面沒有投射、落點、空投或平台事件，故不能由截圖驗證它們的執行中動畫；判斷改以現有素材、規則與回饋紀錄為準。
- 所有本文件實際開啟的 PNG（概念稿、現況 Canvas、Q1 UI／FX／肖像／姿勢審核圖，以及抽查的 dock、平台、地帶、柵欄、鬼、補給箱）均可檢視；沒有把看不到的圖片內容當作已驗證事實。
