# 場景收斂規格 converge_scenes（2026-11-09）

範圍：三個戰場場景的唯一規格。主人說的話以 `owner_feedback_log.md` 為準（第 56 行：開局選一個場景、再擴兩個：鐘樓＋另一個，第二個是我猜的）。
已讀：owner_feedback_log、game_mode、wind_design、airdrop_design、index.html、js/wind_fx.js、assets/env 清單。
**不存在（未讀）：** docs/richness_plan.md、docs/ui_reskin_plan.md、docs/roster_design.md（Kiro 任務可能還在跑）。這三份出來後要回頭對一次。

## 0. 程式與素材現況（實測，不是推測）
| 項目 | 值 | 出處 |
|---|---|---|
| 畫布 | 1920x1080 | CANVAS_W/H |
| 地面線 | GROUND_Y = 860；單位腳底、空投落地(840)、圍籬底都靠它 | index.html 397 |
| 圍籬 | 中心 x 960，寬 130（895..1025），高 250（頂在 y 610） | FENCE_*；shared/constants.json |
| 單位起點 | 玩家 x 340、AI x 1560，y 860 | index.html 505-530 |
| 移動範圍 | 玩家 160..850、AI 1070..1760（MCP 引擎 835/1085） | stepDice |
| bg_graveyard.png | **1536x864**（16:9），繪製時拉伸成 1920x1080（放大 1.25 倍） | file 指令 |
| ground_strip.png | 1536x384，畫在 y 820..1080（GROUND_Y-40 起，高 260） | draw() |
| fence_black_intact.png | 709x850；**程式目前沒引用**，圍籬仍是程式畫的棕色木板 | grep 無結果 |
| 風場 | WindFx.createWindField，種子 7，禁區只有頂部 [0,0,1920,100]；霧／靈塵／落葉／火焰／燈籠 | index.html 500 |
| 環境音 | ambient_sfx 有 night、wind 兩條底噪（2 秒交叉淡入）＋ thunder 等單發；`setBed("wind")` 為預設 | ambient_sfx.js 347 |
| SCENES | 三筆已在：graveyard / belltower(bg_belltower.png) / pumpkin(bg_pumpkin_field.png)；缺檔的卡片顯示「製作中」且不可選 | index.html 330 |

## 1. 三個場景總表
| | 月夜墓園（已有） | 鐘樓（主人點名） | 南瓜田（第三個，我確認） |
|---|---|---|---|
| id / 檔名 | graveyard / bg_graveyard.png | belltower / bg_belltower.png | pumpkin / bg_pumpkin_field.png |
| 色調 | 深藍紫、冷月光 | 暗石灰＋青銅金＋橘色燭火 | 橘紫黃昏、暖光 |
| 基調 | 基準場，不加任何機制 | 高處、風大、沉重 | 開闊、霧、安靜 |
| 音樂氛圍 | 神秘華爾茲（現有） | 低沉合唱＋遠處鐘聲，稍慢 | 輕快詭異的鐵琴／弦樂，稍輕 |

第三個場景結論：**確認南瓜田**，不換。理由：遊戲名就是南瓜殺手、與墓園（藍）和鐘樓（暗金）色調分得開、橫向開闊正好給「中央一道圍籬」。備選（不採用）：廢棄教堂，與鐘樓太像。

## 2. 月夜墓園（現有，只補規則）
- 外觀：滿月、枯樹、遠景墓碑與薄霧，近景一條平地；整體冷藍。
- 現有 bg 是 1536x864，不重做；若 Colab 有餘力再出 1920x1080 版，非必要。
- 圍籬：換用 fence_black_intact.png（見第 6 節，三個場景共用同一套鐵欄杆）。
- 玩法：無，作為平衡基準。風 −4..+4 均勻抽（現況不變）。
- 天氣事件：每 25 到 40 秒一次遠雷閃光，只有畫面微亮 0.15 秒＋ thunder.ogg，不影響彈道（INVENTED，建議 30 秒）。
- 風粒子：現有全套（霧、靈塵、落葉、火焰、燈籠）不動，這是風場的原始設定。
- 環境音：night_bed 為底；風大時 wind_bed 依 wind_design 第 4 節疊上。

## 3. 鐘樓（新）
外觀：哥德式鐘樓頂層的露天平台，背後是巨大的拱形窗與遠處夜空下的城市剪影，上方吊著一口青銅大鐘，兩側石柱頂有滴水獸（gargoyle）石像。畫面上方 1/3 是鐘與拱頂，下方 1/3 是石板平台，整體暗灰石色，只有燭火與青銅的暖光。

**Colab 背景要求**
| 項目 | 規格 |
|---|---|
| 尺寸 | 1920x1080 目標；至少 16:9（可 1536x864，程式會拉伸，和現有一致） |
| 完全留空（不可畫任何物件） | 地面帶 y 780..1000 整條要平、同一個石板面，不可有台階、碎石堆、陰影塊 |
| 中央空柱 | x 880..1040（圍籬 895..1025 外各留約 15 px），從 y 560 到 y 1000 不可有柱子、鐘繩、滴水獸 |
| 左右對稱 | 玩家區 x 160..850、AI 區 x 1070..1760 的亮度與雜訊量要接近，不偏一邊 |
| 上方 HUD 安全區 | y 0..110 要暗且低對比（不放亮窗、亮鐘），血條板才讀得清 |
| 下方 dock 安全區 | y 880..1080 低對比、不放細碎花紋（約 200 px 被 dock 蓋住） |
| 大鐘位置 | 鐘中心靠上、約 y 150..420，水平置中偏左右皆可，但不得進入 x 880..1040 的 y 560 以下 |
| 滴水獸 | 放兩側遠景 x < 300 或 x > 1620、y 250..600，不遮單位 |
| 禁止 | 人物、文字、浮水印、鐘面數字、透明背景（背景是不透明的） |

**地面與圍籬皮**：地面沿用 ground_strip.png（深色石板版另請 Colab 出 `ground_strip_belltower.png`，1536x384，上緣 40 px 要和 bg 地面色接上）；圍籬用黑鐵欄杆，頂端加小尖飾即可，不另畫。

**輕量玩法（小，且兩邊公平）**
| 項目 | 數值 | 標記 |
|---|---|---|
| 風傾向 | 風大小偏強：|wind| 抽 1.5..4（方向仍左右隨機、各 50%）。不偏向任何一方 | INVENTED，建議 1.5 |
| 鐘響事件 | 每 4 回合開始響一次：畫面震動 0.3 秒（振幅 ≤ 4 px）＋ 下一回合 |wind| 加 0.5（上限 4） | INVENTED，建議 4 回合、+0.5 |
| 傷害型危險 | 無 | 刻意不加，平衡不變 |
| 風粒子 | 灰塵、碎石屑、少量飄落灰燼；落葉少（≤ 10）；鐘上積塵在鐘響時抖落 | 數量 INVENTED |
| 環境音 | wind_bed 當底（風強），night_bed 降到 0.4；鐘響用鐘聲音效（本地無，見待定 3） |  |
| 燈籠擺動 | 懸掛的燭台／鐵鏈用 swayAngle，最多 6 個 | wind_design 現有 |

## 4. 南瓜田（新）
外觀：黃昏轉夜的開闊田地，遠處低丘與一座歪斜的稻草人，地面散落各種南瓜與南瓜燈（亮橘光），天空橘紫漸層，低處一層薄霧。要溫暖但帶詭異。

**Colab 背景要求**
| 項目 | 規格 |
|---|---|
| 尺寸 | 1920x1080 目標；至少 16:9 |
| 完全留空 | 地面帶 y 780..1000 保持平整土面，**南瓜與南瓜燈只能在遠景 y < 760，或在 y > 1000 的最前緣**；中間這條不可有南瓜、石頭、田埂 |
| 中央空柱 | x 880..1040、y 560..1000 不可有稻草人、樹、柵欄、大南瓜 |
| 稻草人 | 放在 x < 300 或 x > 1620 的遠景，不擋單位 |
| 上方 HUD 安全區 | y 0..110 以暗紫天空為主，不放亮月、亮雲 |
| 下方 dock 安全區 | y 880..1080 低對比、泥土為主 |
| 禁止 | 人物、文字、浮水印、透明背景；不要把南瓜臉畫在畫面正中央（會和南瓜彈混淆） |

**地面與圍籬皮**：泥土＋短草的 `ground_strip_pumpkin.png`（1536x384，上緣 40 px 接 bg 土色）；圍籬同黑鐵欄杆，可在欄杆底部纏藤蔓（程式疊小綠線，不另出圖）。

**輕量玩法**
| 項目 | 數值 | 標記 |
|---|---|---|
| 風傾向 | 風偏弱：|wind| 抽 0..2.5，方向隨機 | INVENTED，建議 2.5 |
| 天氣事件 | 每 20 到 35 秒一群烏鴉飛過天空（crow.ogg），純視覺 | INVENTED，建議 28 秒 |
| 傷害型危險 | 無 | |
| 風粒子 | 霧加量（8，alpha 加 30%）、南瓜葉與乾草屑代替落葉、靈塵偏橘金 | 數量 INVENTED |
| 環境音 | night_bed 為底、wind_bed 低；偶發 crow / cat_meow / dog_bark（ambient_sfx 已有） | |

## 5. 風粒子與場景的對照（交給 wind_fx 的「主題」參數）
| 粒子 | 墓園 | 鐘樓 | 南瓜田 |
|---|---|---|---|
| 霧團 | 6 | 3（灰） | 8（橘紫） |
| 靈塵 | 32（紫青金） | 20（金） | 32（橘金） |
| 落葉 | 26 | 8（灰燼、碎屑色） | 20（乾草、南瓜葉色） |
| 吊飾搖擺 | 燈籠、樹枝 | 鐵鏈燭台 | 稻草人破布 |
實作建議：createWindField 增加 `theme` 選項（只換數量與顏色表），不改物理公式。禁區再加：HUD 頂 [0,0,1920,110]、dock [0,880,1920,200]（現在只擋頂部 100 px，見待定 5）。

## 6. 開始畫面縮圖規則
- 縮圖直接用該場景 bg 當 `background-image`（現況已如此），不另出縮圖檔。
- 卡片比例固定 16:9，裁切取中央；中央 x 880..1040 空柱讓縮圖也乾淨。
- 檔案不存在或載入失敗：卡片灰掉、顯示「製作中」、不可點（現況已如此）。通過驗收條件：三張卡的縮圖互相一眼分得出（色調差異，截圖肉眼確認）。

## 7. 換場景的程式做法與驗收清單
做法（現況已有骨架）：
1. SCENES 陣列每筆 `{id, name, bg}`；擴充欄位 `ground`（地面條檔名）、`fence`（欄杆圖）、`wind`（{min, max}）、`theme`、`bed`（"night"/"wind"）、`event`。
2. initStartScreen 預載每個 bg 到 `images.bg_scene_cache[id]`；startMatch 時 `images.bg = cache[id]`、同時換 `images.ground`、重設風場主題、呼叫 `ambientSfx.setBed(...)`。
3. 抽風處（index.html 1205 一帶 `Math.random()-0.5)*8`）改讀場景的 {min,max}；MCP 引擎若也抽風需同步（見待定 4）。
4. 回到開始畫面（showStartScreen）時重設為 graveyard 的設定，避免殘留。

換完必驗（主線用截圖＋讀值，Playwright／瀏覽器皆可）：
| # | 檢查 | 通過條件 |
|---|---|---|
| 1 | 地面線對齊 | 截圖中單位腳底 y 與背景地面平台的視覺地平在 ±8 px 內；ground_strip 上緣與 bg 無明顯接縫（接縫處肉眼看不出斷層） |
| 2 | 圍籬佔地 | 圍籬底寬落在 x 895..1025，背景中央 x 880..1040 沒有任何物件被圍籬遮到或與之重疊 |
| 3 | 單位腳 | 玩家 x 340、AI x 1560 的腳底都踩在地面帶內，沒有踩在花紋、台階或陰影塊上 |
| 4 | 移動端點 | 單位走到 160、850、1070、1760 時腳底仍在地面帶，且背景左右邊界沒有突兀物件 |
| 5 | HUD 可讀 | 頂部板的名字與血條在 y 0..110 內對比清楚；用顏色取樣，文字亮度與背景亮度差 ≥ 3:1（INVENTED 門檻）|
| 6 | dock 可讀 | y 880..1080 區域 dock 圖示邊緣清楚，背景不搶（肉眼確認，無花紋穿透） |
| 7 | 空投落點 | 空投區（玩家側約 300..835、AI 側約 1085..1620）落地的箱子 y=840 站在地面帶上，不被背景物遮住 |
| 8 | 風場 | 設 wind 為 −4、0、+4 各截一張，粒子方向對、數量符合第 5 節、沒有粒子壓在 HUD 上 |
| 9 | 聲音 | 切換後 console 無 404；底噪確實換成該場景指定的 bed |
| 10 | 回頭驗 | 換場景後再換回墓園，畫面與開局第一次完全一致 |

## 8. 衝突與待定
| # | 衝突或缺口 | 建議 |
|---|---|---|
| 1 | 背景實際是 1536x864，你要的是 1920x1080 | 兩種都接受，程式本來就拉伸；新圖直接給 1920x1080 較清楚 |
| 2 | fence_black_intact.png 已存在但程式仍畫棕色木板；破損／斷版還沒做 | 主線新增圍籬貼圖路徑：完好用 fence_black_intact，80%→0% 用 damaged／broken；沒到之前維持程式畫法。圖 709x850 要縮成 130 寬（比例不同，要決定縮放：建議高 250、寬自動，並保證在 895..1025 內） |
| 3 | 本地沒有鐘聲音效 | 先用 night_bed ＋合成鐘聲；CC0 鐘聲交給 Kiro 查證、主線下載（不花錢） |
| 4 | 風是 client 與 MCP 引擎兩套（wind_design 第 0 節）；場景風傾向要兩邊都生效 | 在 shared/constants.json 加 SCENE_WIND 表，兩邊讀同一份（INVENTED，不影響現行測試） |
| 5 | 風場禁區只擋頂部 100 px，HUD 已是 110 px、dock 約 200 px | 禁區改為 [0,0,1920,110] 與 [0,880,1920,200]，粒子在 24 px 內淡出（wind_design 已有此機制） |
| 6 | 風傾向會改變 AI 的難度（AI 也受風）| 場景的風範圍同時給 AI 看，AI 照現有公式補償；不另調 AI |
| 7 | 空投 airdrop_design 的落點區固定，場景換了不改 | 維持；落點在地面帶內，驗收第 7 項檢查 |
| 8 | richness_plan / ui_reskin_plan / roster_design 缺檔 | 補檔後核對：特效不得進入 HUD／dock 安全區；鐘樓怪人的鐘不與背景大鐘混淆（建議 UI 玩法上的鐘永遠在單位手上，不在背景） |
| 9 | 數字 INVENTED 一覽 | 鐘樓風 1.5..4、鐘響每 4 回合 +0.5、南瓜田風 ≤ 2.5、雷 30 秒、烏鴉 28 秒、HUD 對比 3:1、粒子數量（第 5 節） |
| 10 | 角色出現在三個場景是否有「特效色」差異 | 不做；單位不隨場景調色，避免再要 Colab 出圖 |

## 9. Colab 提示詞（共 2 張背景，皆 16:9、不含角色、不透明）
1. 鐘樓：`Wide 16:9 painterly background, top floor of a gothic bell tower at night, huge bronze bell hanging high at the top, stone gargoyles on distant side pillars, pointed arched window with a distant city silhouette, flat empty stone floor band in the lower middle with nothing on it, completely empty clear center column, dark grey stone with warm candle glow, no characters, no text, no watermark.`
2. 南瓜田：`Wide 16:9 painterly background, open pumpkin field at dusk with orange-purple sky, distant leaning scarecrow and glowing jack-o-lanterns only in the far background, low mist, flat empty dirt ground band in the lower middle with no pumpkins or rocks on it, completely empty clear center column, warm spooky Halloween mood, no characters, no text, no watermark.`
補充：地面條另各出一張（`ground_strip_belltower`、`ground_strip_pumpkin`，1536x384，上緣 40 px 要貼合背景地面色）。

## 摘要
1. 三場景定案：月夜墓園（基準）、鐘樓（風強＋每 4 回合鐘響）、南瓜田（風弱＋霧＋烏鴉），第三個確認南瓜田。
2. 背景硬規則：地面帶 y 780..1000 全空、中央柱 x 880..1040 全空、頂 110／底 200 px 低對比。
3. 現況落差：bg 其實 1536x864；黑鐵圍籬圖有了但程式還畫棕木；風場禁區太小。
4. 玩法全部很小：只動風大小分布與氣氛，不加傷害，方向不偏任何一方。
5. 換場景有 10 項截圖驗收；SCENES 擴欄位（ground/fence/wind/theme/bed）即可。
6. 缺檔：richness_plan、ui_reskin_plan、roster_design；INVENTED 數字已標，並附 2 句 Colab 提示詞。
