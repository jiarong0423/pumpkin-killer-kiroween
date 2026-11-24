# 美術風格統一指南（所有新圖必須照這份；主線修飾 Kiro 提示詞時以此為準）2026-11-09

來源：現有角色圖 (not published){skeleton,wizard,bat,knight}.png 與 assets/poses/（骷髏、貓的出手姿勢）。看過實圖後歸納，不是憑想像。

## 一、角色（人物、姿勢、肖像）
| 項目 | 現有角色的做法 | 新圖必須 |
|---|---|---|
| 比例 | 二頭身，大頭、小身體、短手短腳；頭約佔全高 40% | 一律二頭身，不可畫成寫實或三頭身以上 |
| 輪廓 | 粗而乾淨的深色（近黑）描邊，外面再包一圈細的**暖橘色外輪廓** | 同樣：粗黑描邊＋細橘色外緣光圈 |
| 上色 | 賽璐珞三階層次（亮／中／暗），柔和高光，沒有寫實紋理或漸層噴霧 | 同樣，不要照片感、不要塑膠光澤 |
| 色調 | 深色衣服（黑、深藍、深紫）配**單一飽和點綴色**：骷髏＝青色眼火、南瓜＝橘色發光、貓＝橘耳、巫師＝紫與金邊 | 新角色也是「深色主體＋一個點綴色」：新娘＝冰藍冷光，怪人＝古銅與暗褐，死神＝深靛與紫色眼光 |
| 表情 | 眼睛大而有神，表情誇張鮮明（冷眼、咧嘴笑） | 同樣誇張卡通，不寫實 |
| 手 | 小而簡化的手，沒有細緻指節紋理 | 同樣 |
| 視角 | 待機：三分之四側面朝右；動作姿勢：嚴格側面朝左 | 同樣 |
| 背景 | 純洋紅 #FF00FF，沒有地面與投影 | 同樣，且主體內部不可出現洋紅或粉紅色調 |
| 邊緣空白 | 主體置中，四周留約 10% 空白 | 同樣 |

## 二、物件（武器、道具、UI 零件）
粗深色描邊，同一套賽璐珞上色；質感只在材質（木紋、石裂、鐵鏽、蠟）上加強，不改變卡通感；暖色燭光主光從左上，冷青色邊緣光在右下。

## 三、場景背景
與現有墓園一致：深藍紫夜空、巨大滿月、前景暗色輪廓、少量橘色燈光點綴；扁平卡通繪畫，粗而柔的輪廓；畫面中下段留空（地面帶），頂端與底部留給介面。

## 四、共用提示詞區塊（Colab 的 style 欄位直接套用）
角色：`Dark-fantasy 2D cartoon game character, chibi two-heads-tall proportions with a big head and small body, thick clean near-black outline plus a thin warm orange outer outline glow, flat three-tone cel shading with soft highlights, a dark outfit with ONE saturated accent colour, large expressive cartoon eyes, small simplified hands. One character, full body, centered, 10 percent empty margin. Flat solid magenta background #FF00FF, no ground, no cast shadow, no text, no watermark.`
物件：`Dark-fantasy 2D cartoon game item, thick clean near-black outline, flat three-tone cel shading with soft highlights, warm candle key light from the upper left and a cool cyan rim light, one object centered, 12 percent empty margin. Flat solid magenta background #FF00FF, no ground, no shadow, no text, no watermark.`
負向：`realistic, photo, 3D render, painterly gradient, plastic shine, thin line art, text, letters, watermark, cast shadow, ground, extra characters, magenta or pink tones inside the subject`

## 五、一致性檢查（每批圖出來後主線做）
1. 與 assets/units 並排縮圖，目視比對頭身比、描邊粗細、橘色外緣、色調數量。
2. 量測：主體外緣是否有橘色圈（有）、頭高占比（約 40%）、主體內是否有洋紅色（無）。
3. 不合格的圖用同一提示詞換種子重畫，或加強「two-heads-tall、thick outline、orange outer glow」字句；仍不合格則改提示詞，不手動修圖（不用程式假造）。
