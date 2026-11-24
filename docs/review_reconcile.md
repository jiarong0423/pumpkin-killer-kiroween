# Kiro 任務 36：審查與整合（review only）

日期：2026-11-09。範圍：只讀、只寫這一份檔。沒有改 index.html、assets/、js/、scripts/，沒用 git，沒下載、沒做圖。
優先順序：1) `owner_feedback_log.md`（愈後面愈新，最大）2) `index.html` 實際程式 3) 其他文件。
所有數字都是我讀程式、用手算的，**沒有跑過遊戲、沒有跑測試、沒有看過任何圖**。標 `INVENTED` 的是文件自己發明的數字。

## 0. 給主人的摘要（繁體中文）

1. **先確認一件事：任務單寫「4 次命中」，但 owner log 最底下新增的一列寫「3 次命中、頭上三顆點、取代先前的 4 次」。** 我照 log（你說 log 最大）。converge_characters、ultimates_design、game_mode、GAP_QUEUE 都還寫 4。另外 log 說「三顆點已完成」，但我在 index.html 裡搜不到任何能量點程式（搜過 pip、ultimate、energy、能量），所以這句「完成」我無法證實。
2. **最危險的文件是 `roster_design.md`。** 它是在你說「鬼娃新娘、鐘樓怪人、死神」之前寫的，所以設計了「瘟疫醫生」和「提燈守墓鬼」兩個你沒要的職業，也把蝙蝠寫成 3 枚、把標槍寫成穿刺、把盾衛寫成擊退。它的「第 2 節數字表」全部作廢，只有「4 打 4 回合流程」那一節值得留。`roster_asset_requests.md` 的 `unit_doctor.png`、`unit_warden.png`、`proj_vial.png` **不要送去 Colab**。
3. **`ultimates_design.md` 也和你的規則不合。** 它的大招是「單一目標、上限 40、沒有先命中再追擊」；你的規則是「先命中（算一次普通傷害）、再追擊，追擊合計 = 1.5 倍普攻、平均分」。照你的規則，七個職業的大招全部可以用同一套機制（命中 → 三下追擊），只換外觀。
4. **蝙蝠一次齊射最多 40 傷害（5 枚 x 8），3 次就死，是全職業最強，且不在 4 到 6 次的範圍。** 最小修法：每枚 8 改 6（把 0.4 改 0.3），一次齊射最多 30，需要 4 次。同時 100 血、3 次命中點亮大招時，蝙蝠 40 + 60 = 100，會從滿血一擊殺。
5. **南瓜巫師目前只是「傷害比較大的球」，違反「攻擊行為要不同」。** 建議加一圈小範圍爆炸（70 到 110 px 內 8 傷害）。需要你點頭（決策 7）。
6. **風：瀏覽器是「加速度」72，MCP 伺服器是「固定漂移速度」67.5，不是同一個模型。** 風 4、飛行 1.4 秒時，瀏覽器偏移約 282 px，伺服器約 378 px，差約 96 px。程式註解寫「match」不實。建議 MCP 改成加速度 72，並把 `WIND_ACCEL` 放進 `shared/constants.json`。
7. **血量一律 100；補血一律 30（按鈕 35 改 30，物資箱不動）；回合計時 12 秒（3 個以上單位一邊時才用 8 秒）。**
8. **網頁版的 AI 用精確的彈道模擬器加真實風值與真實站位算力度（再加 ±14 誤差）**，這和 `product.md`「AI 不能作弊、沒有彈道模擬器」直接衝突，而且 AI 每回合隨機換職業。它是示範主秀，建議改成「只看自己過去落點修正」（約 20 行）。
9. **20 天內最大風險是 4 打 4 的單位陣列改寫**（全檔都是 `player` / `ai` 全域變數）。「最多 4 打 4」是上限不是下限，建議先保 1 對 1 + 7 職業，2 對 2 當加碼。
10. 要你回答的只有 8 題（第 d 節），每題都有建議答案。

---

## a. CONTRADICTIONS（矛盾表）

讀法：「文件說」欄引用各檔原值；「index.html 實際」欄是我讀程式的結果；「建議」只給一個值。行號是我讀到時的行號，可能會因主線改檔而偏移。

### a1. 數字與規則

| # | 主題 | 文件各說什麼 | index.html 實際 | 建議的唯一值 | 一句理由 |
|---|---|---|---|---|---|
| C1 | 每職業血量 | `game_mode.md`：蝙蝠 90 / 巫師 85 / 骷髏 100 / 盾衛 120。`scripts/mcp_game_server.py` `HERO_TEMPLATES`：同上。`richness_plan.md` 第 5 節：巫師 (85)、蝙蝠 (90)、盾衛 (120)。`roster_design.md`：「HP 100 for every class」。`converge_characters.md`：「先維持全員 100」 | `player` / `ai` 都是 `hp: 100, maxHp: 100`（約 521-537 行）；`HERO_PROFILES` 沒有 hp 欄位 | **全員 100** | 這是唯一可玩版本的值；擊殺次數才不會看受害者職業而變；MCP 與 game_mode.md 的表要改 |
| C2 | 每職業普攻傷害 | `index.html HERO_PROFILES`：24 / 28 / 20 / 22。MCP 引擎：骷髏 18、巫師 26、蝙蝠 16、盾衛 20。`roster_design.md` 2b：骷髏 26（穿刺 13）、巫師 24（爆 5）、蝙蝠 3x9、盾衛 20、醫生 14+9、守墓鬼 12+14。`converge_characters.md`：24 / 28 / 8x5 / 22，新職業 INVENTED 12（新娘）、22（怪人）、18（死神） | 骷髏 24、巫師 28、蝙蝠 20 x 0.4 取整 = 每枚 8 共 5 枚、盾衛 22 平均分給 1 到 6 次碰撞 | **骷髏 24、巫師 28、蝙蝠 5 x 6 = 30、盾衛 22、怪人 22、死神 18、新娘 18（中心）** | 瀏覽器值是玩家看到的；蝙蝠與新娘依 b 節修到 4 到 6 次擊殺 |
| C3 | 蝙蝠散射枚數與單枚傷害 | `game_mode.md`：「throwing darts」，沒有枚數。`roster_design.md`：3 枚、-3/0/+3 度、每枚 9。`ultimates_design.md` 範圍彈 #3：5 枚、-8 到 +8 度、每枚 4。`owner log`：「scatter of 5」，「+/-8 deg fan, 8 damage each」 | 原彈 + `spread=[-8,-4,4,8]` = 5 枚；每枚 `round(20 x 0.4)` = 8；原彈速度不變，其他 4 枚速度 x0.95 到 1.05 | **5 枚、每枚 6（0.4 改 0.3）、最多 30** | 見 b 節：現在滿中 40，3 次擊殺，過強 |
| C4 | 補血量 | 按鈕：`index.html` 221 行 title「+35 HP」，732 行 `+ 35`。物資箱：1295 行 `SUPPLY_ITEMS.heal` +30。`airdrop_design.md`：「Existing heal skill +35」，新設計 `candy_heal` +25。`converge_characters.md` #4：「技能 +35、物資箱 +30 先並存」 | 兩個數字並存（35 與 30） | **30，一個常數 `HEAL_AMOUNT`** | 只改按鈕一行；物資箱已是 30；airdrop 的 25 作廢（箱子仍需「缺 20 血以上才給」） |
| C5 | 回合計時 | `index.html` `TURN_SECONDS = 12`；`shared/constants.json` 12；`game_mode.md`：「12 s ... mockup shows 8 s: undecided」；`roster_design.md`：每單位 8 秒；`owner log` 問題 4 仍 OPEN | 12 秒，到時放棄 | **12 秒；一邊 3 個以上單位時改 8 秒（模式常數）** | 12 在程式、常數、MCP、測試都一致；8 秒只在 4 打 4 才有意義 |
| C6 | 風的模型與係數 | `index.html` 501 行：`vx += wind * 72 * dt`（加速度）。`mcp_game_server.py` 329 行：`cur_x += (vx + wind * 67.5) * dt`；`mcp_stdio_server.py` 57、98 行 `WIND_PUSH = 67.5`（固定漂移速度），註解「kept at 1.5x to match WIND_ACCEL 72」。`game_mode.md`：「wind * 48」。`wind_design.md`：48 / 45，建議 96。`ui_reskin_plan.md`：48 / 45。`converge_characters.md`：72 | 加速度 72 | **加速度模型、`WIND_ACCEL = 72`，MCP 改成 `vx += wind * 72 * dt`，並加進 `shared/constants.json` 與同步測試** | 手算風 4、飛行 1.4 秒：瀏覽器 0.5 x 72 x 4 x 1.4^2 = 282 px，MCP 4 x 67.5 x 1.4 = 378 px；兩者只在 t = 1.875 s 相等。96 沒被採用，72 是主線已上線值，主人的「太弱」還要實測確認 |
| C7 | 風範圍與縮放殘留 | `shared/constants.json`：WIND_MIN/MAX = -4/+4。`index.html` 504 行註解「-5 to +5」，1203 行 `(Math.random() - 0.5) * 8.0` | 實際 -4 到 +4；環境風聲用 `abs(wind) / 5`（306、1409 行），最大只到 0.8 | **範圍 -4..+4；風聲縮放改 `/ 4`** | 與常數一致；ui_reskin_plan 發現 3 的同一個問題 |
| C8 | 新娘的攻擊（音波，不是花束） | `owner log`：音波攻擊、半透明音波環、範圍效果。**仍寫花束的地方：** `converge_characters.md` 17 行（`proj_bouquet`、丟花束）、29 行（花束落地半徑 90 px、12 傷害）、41 行（花束劃弧、`throw_bouquet`、`impact_bouquet`）、64 行（COMING 文案「花束炸彈」）、65 行（沿用花束範圍炸）、68 行（音效事件）、94-95 行（Colab 清單 `proj_bouquet`、`fx_bouquet_burst`）。`GAP_QUEUE_20261109.md` B2 行：「新娘（範圍花束）」。`converge_characters.md` 文末「更正」只更正了文字，沒更正 3c 的 Colab 清單 | `COMING_HEROES` 已寫「音波攻擊：尖叫放出音波環，攻擊範圍寬，飛行路徑上都會受傷」（326 行）。HERO_PROFILES 沒有新娘 | **音波：普通彈道，命中範圍橫向 +/-200 px；70 px 內 18，線性降到 200 px 處 9；每個敵方單位每次最多算一次；仍會被圍籬與天空盾擋下** | 這是最小可做的「範圍」；沒有任何文件給過音波數字，這組是我的建議（INVENTED），18 讓擊殺次數落在 6 |
| C9 | 死神大招數字 | `converge_characters.md` 31 行：「骷髏 18 + 三鐮各 8 = 42」；同檔「更正」：三鐮各 9、合計 27、整招 45。`owner log`：骷髏頭命中是觸發，三下合計 = 1.5 x 普攻，各 0.5 x，骷髏頭自己的傷害是一次普通命中 | 無任何大招程式 | **普攻 18；骷髏頭命中 18（普通）；之後三鐮各 9；單一目標合計 45；骷髏頭被擋或沒命中就不觸發** | 與 owner log 一致；31 行的 42 要視為作廢 |
| C10 | 大招能量條規則 | 任務單：4 次。`owner log` 最後新增列：**3 次**、頭上三顆點、「取代先前的 4 次」、每人算自己的、整場最多 2 次、一次投擲只算一次。`game_mode.md`：全域 4 次，另有舊的各職業 3/3/4/3；`ultimates_design.md`：4 顆點，每單位一條，**上限 2 次算每一邊**，點顯示在 dock 與血條下；`converge_characters.md` 31、`GAP_QUEUE` B3：4 次；MCP `ultimates_remaining` 每隊 2；`converge_characters` #12：每個單位各計；`owner log` 問題 1、2、3 仍 OPEN | 找不到任何能量點程式（log 說完成，我證實不了） | **3 次命中；每位玩家（= 每個單位）自己的條；每位玩家整場最多 2 次；只有「造成傷害」的投擲算，一次投擲算 1 點，被擋或落空不算；用完歸零；點畫在頭上** | 照 log 最後一列。另有算術理由：100 血、4 到 6 次擊殺時，4 次的條會在巫師與蝙蝠的最後一擊才滿（大招沒機會用），3 次才有意義 |
| C11 | 大招傷害模型與目標數 | `ultimates_design.md`：每目標上限 40、隊伍上限 25%、單目標期望 1.5 到 2.1 倍；骷髏 3x13（無觸發命中）、巫師 24 + 毒 9、蝙蝠雨 10x4、盾衛 12 x 最多 4 次。`owner log`：先命中（普通傷害）+ 追擊合計 1.5 x 普攻、平均分；大招打**多個**單位，1.5 x 是每個單位各算還是共享（OPEN，log 建議每個單位各算） | 無 | **規則取代 ultimates_design 的數字：觸發命中 = 普通傷害；之後固定 3 下追擊，每下 = 0.5 x 普攻；追擊對「觸發點 150 px 內的每個敵方單位」各算一次（每單位最多 1.5 x）。上限 40 作廢** | 一台機器七個職業共用；b 節驗算沒有任何職業從滿血被一個大招殺死 |
| C12 | 4 打 4 回合流程 | `game_mode.md` 同檔內兩種：「Per round every unit picks one action ... then presses Lock. Human units resolve first」vs「opposing side attacks in sequence, one unit after another」。`roster_design.md`：人類階段每個活著的單位依序行動一次（可點選未行動單位），再換 AI 階段，8 秒，7 回合上限。MCP 引擎：收集所有待投擲，回合結束依單位 id 結算，**並把每個單位的 x 重新隨機（220 到 640）**。`airdrop_design.md`：4 打 4 的參考單位是「placeholder」 | 1 對 1：玩家投完 → 投射物清完 +1 秒 → AI → +0.8 秒 → `resolveRound`；位置只因移動骰子改變 | **採 roster_design 的依序流程（人類階段 → AI 階段，各單位各一次）；Lock 只留給盾衛放天空盾；MCP 取消 x 重新隨機** | 「Lock + 同時結算」沒有任何程式與測試，且和「感覺優先、立刻看到結果」相反 |
| C13 | 誰控制幾個單位 | `roster_design.md`：每邊從 6 職業挑 4 個（不重複，盲選），人類一個人控制自己的 4 個。`owner log`：「Choose ONE character at the start」。`product.md`：「up to four humans versus four sub-agents」 | 開始畫面選 1 個職業；AI 每回合隨機換職業 | **每位人類選 1 個職業；一邊單位數 = 人類數（示範版 1 到 2）；AI 在開局用種子從公開卡中抽出同樣數量、不重複的職業，整場固定** | 與主人的規則和 product.md 同時一致；roster_design 的「挑 4 個」作廢 |
| C14 | 職業數量與名稱 | 主人：至少 6、最多 4 打 4；新增鬼娃新娘、鐘樓怪人，另有死神。`roster_design.md`：「Six」= 原 4 + 瘟疫醫生 + 提燈守墓鬼。`converge_characters.md`：7 = 原 4 + 新娘 + 怪人 + 死神。名稱：`HERO_PROFILES` 蝙蝠刺客 / 南瓜巫師；MCP 蝙蝠貓刺客 / 南瓜巫師炮手（`CLASS_BY_NAME` 以名稱反查，改名會壞）；`roster_design` 蝙蝠貓刺客、Pumpkin Guard | 4 可玩 + `COMING_HEROES` 3 張灰卡 = 7 | **7 職業，id 為 skeleton / wizard / bat / knight / reaper / hunchback / bride；MCP 與測試只用 id，顯示名用 `HERO_PROFILES.name`；丟掉醫生與守墓鬼** | 達到 6 只要再做兩個新職業；先做死神（骷髏頭是單體彈，最便宜） |
| C15 | 攻擊行為要不同（主人規則） | `converge_characters.md`：巫師「無額外效果」；`roster_design.md` 給巫師爆炸、骷髏穿刺（都不是主人要的）；`game_mode.md` 毒彈是「大招」 | 骷髏：單體 + 霜咒（有行為）；巫師：只是 28 傷害的球（**無行為**）；蝙蝠：散射；盾衛：彈跳 | **巫師加爆炸圈：70 到 110 px 內其他敵人 8 傷害；直擊 28 不變** | 不加就違反規則；手算期望傷害 +16%（9.2 到 10.7），需實測 |
| C16 | 逐職業物理差異 | `roster_design.md`：每職業速度 / 重力 / 風倍率、蓄力掃描 1.2 到 1.4 秒、AI 力度誤差 13.0 到 15.2。`converge_characters.md` #10：每職業 `windK`，怪人 x0.6、速度 x0.85。`product.md`：「the same published aim error as everyone else」 | 全職業共用：初速 = 力度 x 13.8、重力 980、`WIND_ACCEL` 72、蓄力 1.3 秒、`AI_AIM_ERROR` 14 | **全職業共用一套物理，不加逐職業倍率** | product.md 明講同一個誤差；MCP 裡的 `speed_scale` 從沒被用過；差異靠行為，不靠倍率 |
| C17 | 盾衛彈跳細節 | `owner log`：骰 1 到 6 次碰撞，傷害平均分。`converge_crosscheck.md` 缺陷 1：撞圍籬或地面也消耗一次碰撞卻 0 傷害 | 1506、1578 行：`bouncesLeft--` 在圍籬與地面也扣；`bounceDmg = round(dmg / N x 10) / 10` | **只有「撞到單位」才扣碰撞次數**（圍籬與地面彈跳不扣） | 否則骰到 6 卻彈在地上，總傷害少於 22，「平均分」就不成立 |
| C18 | 舊技能鈕（雙發 / 重彈 / 回血）和 dock | `owner log` 問題 6 仍 OPEN；`game_mode.md`：雙發需要能量條；`roster_design.md`：4 打 4 版隱藏；`airdrop_design.md`：重彈與補血改由空投給 | 218-221 行三顆技能鈕仍在，各 2 次 | **示範版保留回血與重彈，隱藏雙發（沒有規格）；2 對 2 以上全部隱藏，只留空投** | 雙發沒有任何規格；少一個沒設計的功能 |

### a2. 場景與美術

| # | 主題 | 文件各說什麼 | index.html 實際 | 建議 | 一句理由 |
|---|---|---|---|---|---|
| C19 | 場景清單 | `owner log`：開局選一個場景，鐘樓 + 一個（第二個是主線的猜測）。`converge_scenes.md`：月夜墓園 / 鐘樓 / 南瓜田。`richness_plan.md` 項目 10：Haunted Hollow / Pumpkin Patch / Crypt Court / Bone Marsh，由種子隨機挑，**沒有鐘樓** | `SCENES` 三筆 `{id, name, bg}`；只有 graveyard 圖存在；`startMatch` 只換背景圖 | **墓園 + 鐘樓 + 南瓜田，開局由玩家選；richness 的四個舞台與「種子隨機選」作廢** | 主人說「開局選」；鐘樓是主人點名的 |
| C20 | 場景風與危害 | `converge_scenes.md`：墓園 -4..+4；鐘樓 abs(wind) 1.5 到 4，每 4 回合鐘響 +0.5 與震動；南瓜田 abs(wind) 0 到 2.5；「傷害型危險：無」。`richness_plan.md`：火焰地塊、流沙、墓碑、雷擊 12 傷害、霧、雨每階段風 +/-1、滿月 +15% 傷害、每日種子 | **完全沒有場景風、地塊、天氣**；風每回合都是 -4..+4 均勻隨機（1203 行） | **只做 converge_scenes 的「每場景風範圍」三行資料；鐘響、雷、烏鴉等純視覺事件延後；richness_plan 全部延到示範之後** | 20 天；richness 的雷擊傷害與滿月加成會改平衡但沒有一項被主人要過 |
| C21 | 鐘的混淆 | `converge_scenes.md` 待定 3：「本地沒有鐘聲音效」。`converge_characters.md` 42 行：`bell_round.ogg` 已在 assets/audio/sfx。背景有大鐘、怪人丟大鐘、鐘樓鐘響事件 | `assets/audio/sfx/bell_round.ogg` 存在（我列了目錄） | **鐘聲用 `bell_round.ogg`；遊戲玩法上的鐘只出現在怪人手上，不出現在背景互動** | 兩份 converge 互相矛盾，檔案其實有；避免玩家把背景鐘誤認為可打目標 |
| C22 | 美術檔名 | 同一物件三種叫法。柵欄：檔案 `assets/env/fence_black_intact.png`、`ui_reskin_plan` 叫 `env_fence_intact / damaged / broken`、`converge_scenes` 叫 `fence_black_intact`。介面板：檔案 `plate_normal.png` / `plate_active.png` / `lock_plate.png` / `top_plate_left.png` / `dock_frame.png`；`dock_asset_requests` 叫 `dock_plate_normal` / `dock_lock_plate`；`ui_reskin_plan` 叫 `ui_plate_normal` / `ui_lock_plate` / `ui_top_plate_left`。肖像：只有 `assets/ui/portrait_wizard.png`；`colab/jobs.json` 叫 `skeleton_portrait_neutral`；dock 要 `portrait_{...}` 與 12 張 `portrait_cutin_*`。新職業：`converge_characters` 叫 `bride_*` / `hunch_*` / `reaper_*`；`roster_asset_requests` 叫 `unit_doctor` / `unit_warden`。武器鍵 vs 檔案：`proj_spear` ↔ `proj_spear_colab.png`、`proj_shuriken` ↔ `shuriken.png`、`proj_shield` ↔ `small_shield.png` | 只有柵欄圖存在但**沒有被引用**（程式仍畫棕色木板）；圖 709x850，與柵欄碰撞框 130x250 比例不同（converge_scenes 量得，我沒驗證） | **以磁碟上的實際檔名為準；每份需求單必須寫「最終磁碟檔名」；新增一個測試：index.html 與 css 引用的每個 assets 路徑都存在** | 現在靠人眼對名字；缺檔只會 404 不會報錯（crosscheck 列了 6 個缺檔） |

### a3. 誠信與架構

| # | 主題 | 文件各說什麼 | index.html 實際 | 建議 | 一句理由 |
|---|---|---|---|---|---|
| C23 | AI 公平性 | `product.md`：「no trajectory simulator, no trial throws」，只拿公開風值與過去落點。`game_mode.md`：「AI aiming accounts for wind (it simulates with the same integrator...)」且同檔「Sub-agents ... no ballistic simulator」。`owner log` 問題 5 OPEN。`GAP_QUEUE` B6：AI 偏強、全知 | `aiAttackNow`（約 1130 行）呼叫 `estimatePowerForTarget` → `simulateLandingX`，用真實風與真實站位二分搜尋力度，再加 +/-14 誤差；`triggerAITurn`（約 1159 行）每回合隨機換職業 | **改成只用自己的落點紀錄：下次力度 = 上次力度 + (目標 x - 上次落點 x) / 20，起手用中間值；AI 的職業開局抽一次、整場固定** | 這是 product.md 的核心賣點「雙方逐回合進步」；約 20 行；舊模擬器可留作測試用 |
| C24 | 「已完成」宣稱和程式不符 | `owner log`：三顆點完成；`converge_crosscheck`：「絕招不要做 PASS」；`ui_reskin_plan`：棕色柵欄、除錯座標 `x=` 仍在 | 找不到能量點；柵欄圖未引用；場景只換背景；`ground_strip` 沒有場景變體 | **「完成」要附一個測試或截圖才算，不接受口述** | 避免示範當天才發現 |
| C25 | 技術規則 vs 實際專案 | `.kiro` 的 tech 規則：TypeScript、`engine/` 純規則、`mcp/`、`web/`、`agents/`、fast-check | 實際：單檔 `index.html` + Python MCP（`scripts/mcp_*.py`）+ Node/Python 測試腳本 | **20 天內不遷移；在 README 寫一句對應關係** | 遷移成本遠大於收益 |

---

## b. NUMBERS CHECK（擊殺次數）

定義：「一次完整命中」= 一次投擲打出該職業的完整傷害（蝙蝠 = 5 枚全中；盾衛 = 所有碰撞都落在單位上；新娘 = 中心）。擊殺次數 = ceil(100 / 完整傷害)。範圍 4 到 6。

### b1. 最終數字下的表

| 職業 | 完整傷害（最終） | 100 血需要幾次 | 在 4 到 6 內？ | 被霜咒（x0.7）時 | 大招單一單位合計（觸發 + 1.5 x，三下各 =） |
|---|---|---|---|---|---|
| 骷髏 | 24 | 5（4 次 = 96） | 是 | 16.8 → 6 | 24 + 36 = 60（各 12） |
| 巫師 | 28（另有 70-110 px 圈 8） | 4（3 次 = 84） | 是（下緣） | 19.6 → 6 | 28 + 42 = 70（各 14） |
| **蝙蝠 現況** | 5 x 8 = **40** | **3** | **否（太快）** | 5 x round(14 x 0.4 = 5.6) = 6 → 30 → 4 | 40 + 60 = **100（滿血一擊殺）** |
| **蝙蝠 建議** | 5 x 6 = 30 | 4（3 次 = 90） | 是 | 5 x 4 = 20 → 5 | 30 + 45 = 75（各 15） |
| 盾衛 | 22 | 5（4 次 = 88） | 是 | 15.4 → 7 | 22 + 33 = 55（各 11） |
| 鐘樓怪人 | 22（INVENTED，沿用） | 5 | 是 | 15.4 → 7 | 22 + 33 = 55（各 11） |
| 死神 | 18（INVENTED，沿用） | 6（5 次 = 90） | 是（上緣） | 12.6 → 8 | 18 + 27 = 45（各 9） |
| **新娘 舊（花束 12）** | 12 | **9** | **否（太慢）** | — | — |
| 新娘 建議（音波中心 18） | 18（邊緣 9） | 6（邊緣要 12 次） | 是（中心） | 12.6 → 8 | 18 + 27 = 45（各 9） |

大招欄位的前提：觸發命中是一次普通命中；追擊固定 3 下；全部打在同一個單位。沒有任何一個建議後的大招能從滿血一擊殺（最高 75）。每位玩家整場最多 2 次，同一目標兩次大招最壞 150，會殺死，這是可接受的（要先連中三次才有第一次）。

### b2. 標出範圍外的職業與最小修法

| 職業 | 問題 | 最小修法 | 修法後 |
|---|---|---|---|
| 蝙蝠 | 完整傷害 40，3 次擊殺，且大招組合 100 | 單枚傷害係數 0.4 改 0.3（index.html 約 908 行 `Math.round(pj.dmg * 0.4)` 一個常數） | 完整 30 → 4 次；大招組合 75 |
| 新娘（舊花束 12） | 9 次擊殺 | 該數字已隨「花束」作廢；音波中心傷害設 18 | 6 次 |
| 巫師 | 4 次，剛好在下緣；如果加爆炸圈會再提高期望傷害 | 不改直擊 28；圈只給 8 | 擊殺次數不變 |

### b3. 蝙蝠為什麼要修：手算期望（不是實測）

假設：地面水平、忽略 110 px 發射高度與風；目標距離 D = 1000 px；原彈完美瞄準（不受速度隨機影響）；其他 4 枚的角度為 46 / 50 / 58 / 62 度，射程比 = sin(2 x 角度) 與 54 度（0.951）相比 = +5.1% / +3.5% / -5.5% / -12.8%，即落點偏移 +51 / +35 / -55 / -128 px；再加速度 x0.95 到 1.05 的隨機（射程約 +/-10%，+/-100 px）；判定窗 +/-70 px。

| 枚 | 落點偏移 | 命中機率 |
|---|---|---|
| 原彈 | 0 | 1.00 |
| 50 度那枚（+35） | +35 +/- 100 | 0.66 |
| 46 度那枚（+51） | +51 +/- 100 | 0.58 |
| 58 度那枚（-55） | -55 +/- 100 | 0.59 |
| 62 度那枚（-128） | -128 +/- 100 | 0.22 |

D = 1000 時期望命中約 3.05 枚：每枚 8 → 24.4；每枚 6 → 18.3。距離 500 px 時偏移減半，4 到 5 枚都中，所以「完整 40」在近距離是常態，不是理論值。

### b4. 順帶發現

- 蝙蝠現況（每枚 8）：完整傷害 40 是其他職業（22 到 28）的 1.4 到 1.8 倍。遠距離（1000 px）完美瞄準時期望約 24.4，和別人差不多；近距離 5 枚幾乎全中，就是 40。所以「過強」只發生在近距離（單位最近可靠到 220 px），修 0.3 後近距離 30、遠距離約 18。
- 大招使用機會：3 顆點時，巫師 3 次命中（84 血）後還有 16 血，大招可用；4 顆點時巫師第 4 次命中就死了，大招永遠用不到（ultimates_design 發現 1 也有同樣觀察）。這是支持「3」的算術理由。

---

## c. RISKS（20 天內的 10 大風險，由大到小）

| 排名 | 風險 | 證據 | 較便宜的替代方案 |
|---|---|---|---|
| 1 | **4 打 4 單位陣列改寫** | GAP_QUEUE B1 標 P0；全檔以全域 `player` / `ai` 寫成；roster_design 的步驟 8a 到 8f 牽動命中、AI、HUD、dock、天空盾、空投、移動。我沒量過行數，只確定 `player.` / `ai.` 到處都是 | 「最多 4 打 4」是上限。**先保 1 對 1 + 7 職業；2 對 2 只當加碼（步驟 10）**。若做陣列，也只做 N = 2 並保留 1 對 1 的煙霧測試 |
| 2 | **Colab 出圖量與序列時間** | NEW1 三個職業各 9 到 13 張 + 2 張背景 + 2 張地面條 + U2 的 31 張 UI + DROP1 + 大招 + richness 的 6 張；Colab 序列執行、每次重跑要載模型（GAP A 節）；NEW1 提示詞只存在 Colab 儲存格，jobs.json 查不到（我 grep 過 `bride`、`reaper`、`skull`、`hunch`：無） | **每個新職業只要 idle / windup / release / hit 4 張 + 1 張肖像 + 1 個投射物，另一隊鏡像**；砍掉多表情肖像、大招專用貼圖（改用程式粒子）。職業卡「圖載入成功才可選」（開始畫面已有 `sceneOk` 同款機制） |
| 3 | **「完成」無法證實 + 17 個未合併分支擠進單檔 index.html** | owner log 說三顆點完成但搜不到；crosscheck 說沒實機驗證；GAP E2 列 17、18、19、21、23、24、26-29、31-35 未合併，C7 說 i18n 分支會與 index.html 衝突 | 今天先做煙霧測試（載入、按開始、投一次、無 console 錯誤、截圖）；合併一次一個、每次先跑 6 個測試腳本。i18n 分支最後再合，或丟掉 |
| 4 | **網頁版 AI 作弊 / 與 MCP 脫節** | C23；product.md 說「一個規則引擎，人與子代理都用 MCP」，實際瀏覽器直接改狀態、MCP 是另一套物理 | **不統一程式，只統一資料與物理常數**（步驟 1）；AI 改成看落點紀錄（步驟 3）；子代理示範用 `scripts/eval_agent_learning.py` 在無頭模式跑，不接進瀏覽器 |
| 5 | **七種大招各有動畫、音效、剪入** | ultimates_design 工程量表 S/M/L，總計約 11 步；剪入 0.45 秒 + 整段約 3 秒；owner log 說大招尚未建造 | **一台機器七種外觀**：觸發命中 → 三下追擊（每下 0.5 x），先做死神（鐮刀斬）當樣板，其他職業只換粒子顏色與音效；**不做剪入畫面、不做慢動作** |
| 6 | **兩套規則引擎數字漂移** | C1、C2、C6、C14：血量、傷害、風、命中框、釋放點、移動邊界（850/1070 對 835/1085）、職業名稱全不同 | 新增 `(not published)` 與 `WIND_ACCEL`、`HEAL_AMOUNT`、`AI_AIM_ERROR`；測試：兩邊對 20 組（角度、力度、風）算出的落點差 ≤ 3 px |
| 7 | **平衡數字全是手算或 INVENTED** | 新三職業的傷害全是發明；蝙蝠 40；AI 命中率 33% 是主線量的、1 對 1 約需 15 次投擲才擊殺（5 次命中 / 0.33），一場約 3 到 4 分鐘（手算，未量） | 寫一個無頭模擬：把 `updatePhysics` 的整合式抄進 node，兩個機器人對打 200 場，看各職業勝率 40 到 60%；做不到就只做擊殺次數表（本檔 b 節）並在試玩時計時 |
| 8 | **場景圖有嚴格留白規則，Colab 不保證做得到** | converge_scenes：地面帶 y 780..1000 全空、中央柱 x 880..1040 全空、頂 110 與底 200 低對比；GAP A5：Colab 能否出 16:9 未確認；現有背景 1536x864 被拉伸到 1920x1080 | 先出**一張**鐘樓；用墓園背景當參考圖做 img2img 保留版面；驗收用截圖四點檢查；失敗就只上墓園 + 一個新場景。柵欄圖比例不合，先維持程式畫柵欄 |
| 9 | **設計文件的範圍膨脹** | richness_plan 16 項（有 7 天建造計畫）、ui_reskin_plan 40 列加字型子集與 31 張圖、ultimates_design 14 個特效與「平靜模式」 | 範圍凍結清單：保留現有特效；只加「擊殺鏡頭」「回合提示環」兩個最便宜項；字型、天氣、地塊、雷、滿月、每日種子、生存模式全部延到示範之後 |
| 10 | **音效：只能用 CC0、新事件沒有檔、沒人聽過** | GAP D1：`move_step`、`item_pickup`、`ultimate_ready_chime` 缺檔（audio.js 指向 `ultimate_ready_chime.ogg`，目錄裡沒有）；D3：主線沒聽過；新事件 `throw_skull`、`scythe_slash`、音波、鐘 | **重用已有檔**：音波 → `spell_magic.ogg`；鐘 → `bell_round.ogg`；骷髏頭 → `whoosh_spear.ogg` + `bones_rattle.ogg`；鐮刀 → `swish_shield.ogg`；大招就緒 → `chime_single.ogg`。在凍結前不下載新檔；排一次主人試聽 |

---

## d. DECISIONS FOR THE OWNER（最多 8 題）

| # | 問題（一字或是/否） | 我的建議答案 |
|---|---|---|
| 1 | 大招能量條是 **3** 次還是 **4** 次命中？（log 最後一列寫 3，任務單與多份文件寫 4） | **3** |
| 2 | 示範版是否接受「每位人類只控制 1 個單位、場上 1 對 1（加碼 2 對 2），4 打 4 不做」？ | **是** |
| 3 | 大招的 1.5 倍是**對範圍內每個敵方單位各算**（不是平分）？ | **是**（範圍 = 觸發點 150 px 內） |
| 4 | 「整場最多 2 次大招」是**每位玩家各 2 次**（不是每邊共 2 次）？ | **是** |
| 5 | 新娘的音波可以一次打到多個敵人（唯一能這樣的普攻）？ | **是** |
| 6 | 蝙蝠每枚手裡劍 8 改 6（一次齊射最多 40 改 30）？ | **是** |
| 7 | 南瓜巫師加一圈小爆炸（70 到 110 px 內 8 傷害）以符合「攻擊行為要不同」？ | **是** |
| 8 | 第二個新場景定「南瓜田」（原本是主線猜的）？ | **是** |

已在矛盾表直接決定、主人若不同意再推翻：血量 100、補血 30、計時 12 秒、風加速度 72、大招固定三下追擊、AI 改看落點紀錄、丟掉瘟疫醫生與提燈守墓鬼。

---

## e. BUILD ORDER（建造順序，12 步，約 20 天）

規則：每步完成後都要能玩；每步的通過條件由主線用自動測試或截圖驗證；**第 16 天功能凍結**，17 到 20 天只修錯與補截圖。新美術名稱用 `converge_characters.md` 的命名，**真實輸出檔名要由主線從 Colab 的 Drive `out` 資料夾核對（我開不了）**；標 `(提議)` 的名稱是我取的。

| # | 天 | 做什麼 | 通過條件 | 需要的新 Colab 美術 |
|---|---|---|---|---|
| 0 | 1 | 基準與煙霧測試：跑現有 6 個測試腳本；新增無頭瀏覽器煙霧測試 | 6 個腳本全過（`test_audio`、`test_ambient_sfx`、`test_particles`、`test_wind_fx`、`test_constants_sync`、`test_mcp_game`）；煙霧測試：載入頁面、按開始、投一次、`console.error` 為 0；存 1 張開始畫面與 1 張戰鬥截圖 | 無 |
| 1 | 1-2 | **單一資料來源**：`(not published)`（id、顯示名、hp 100、傷害）；`shared/constants.json` 加 `WIND_ACCEL`=72、`HEAL_AMOUNT`=30、`AI_AIM_ERROR`=14；MCP 風改加速度；MCP 血量改 100、傷害同步、職業用 id | `test_constants_sync.py` 涵蓋新常數且通過；新測試：20 組（角度、力度、風）瀏覽器整合式與 MCP 落點差 ≤ 3 px；`test_mcp_game.py` 通過 | 無 |
| 2 | 2-3 | **數字修正**（index.html）：蝙蝠 0.4→0.3；補血按鈕 35→30；風聲縮放 `/5`→`/4`；盾衛只在撞到單位才扣碰撞；巫師爆炸圈；AI 職業開局固定 | 無頭測試：蝙蝠 5 枚全中 = 30；盾衛 100 次近距離投擲總傷害在 21.7 到 22.3；巫師離目標 90 px 落地 = 8、50 px = 28、130 px = 0；AI 職業在 10 回合內不變；截圖：補血浮字 +30 | 無 |
| 3 | 3-4 | **AI 改看落點紀錄**（取代 `estimatePowerForTarget` 的呼叫） | 腳本：同一風與站位下跑 20 回合，第 6 到 10 回合的平均落點誤差比第 1 到 3 回合小至少 30%；程式搜尋：AI 路徑不再呼叫 `simulateLandingX`；風 -4、0、+4 各一次不出錯 | 無 |
| 4 | 4-5 | **場景資料表**：`SCENES` 加 `wind: {min, max}`、`ground`；`resolveRound` 讀場景風範圍；回到開始畫面重設 | 測試：鐘樓 200 回合 abs(wind) 全在 1.5 到 4，南瓜田全在 0 到 2.5，墓園 -4..+4；截圖：開始畫面三張卡（缺圖者灰色「製作中」）；切換再切回墓園畫面與第一次相同 | `bg_belltower.png`（16:9，留白規則見 converge_scenes 第 3 節）；可選 `ground_strip_belltower.png`；南瓜田：`bg_pumpkin_field.png`、`ground_strip_pumpkin.png` |
| 5 | 5-8 | **死神 + 骷髏頭**（第 5 職業）：加入 `HERO_PROFILES`、`HAND_RIG`、`HELD_WEAPON`；圖載入成功才可選 | 無頭測試：骷髏頭 18 傷害、被天空盾擋下 0 傷害；開始畫面死神卡可選；截圖：骷髏頭飛行中、朝向與運動方向一致（兩隊） | `reaper_idle`、`reaper_windup`、`reaper_release`、`reaper_hit`、`reaper_portrait_neutral`、`proj_skull`（`reaper_scythe`、`reaper_slash_1..3` 留到第 9 步） |
| 6 | 8-11 | **鐘樓怪人 + 大鐘**（第 6 職業，達成「至少 6 職業」） | 無頭測試：22 傷害；擊退 100 px，被限制在移動邊界內且不穿過柵欄；截圖：大鐘飛行與撞擊 | `hunch_idle`、`hunch_windup`、`hunch_release`、`hunch_hit`、`hunch_portrait_neutral`、`proj_bell` |
| 7 | 10-12 | **鬼娃新娘 + 音波**（第 7 職業） | 無頭測試：離落點 50 px = 18、135 px = 13.5、200 px = 9、210 px = 0；被柵欄與天空盾擋下；截圖：音波環（半透明）+ 範圍 | `bride_idle`、`bride_windup`、`bride_release`、`bride_hit`、`bride_portrait_neutral`、`proj_soundwave`（提議，取代 `proj_bouquet` 與 `fx_bouquet_burst`，這兩個**不要出**） |
| 8 | 11-13 | **大招能量條**：3 次命中、每位玩家各自計、整場最多 2 次、一次投擲算 1 點、頭上三顆點、用完歸零 | 單元測試：被擋、落空、打圍籬不加點；一次投擲打到兩個單位只加 1 點；第 3 點亮起；大招用完歸零；每位玩家第 3 次大招被拒；截圖：頭上 0/1/2/3 顆點 | 無（點用現有 `fx_ghostfire` 繪製） |
| 9 | 13-15 | **大招機器**：觸發命中（普通傷害）→ 固定 3 下追擊，每下 = 0.5 x 普攻，觸發點 150 px 內每個敵人各算一次；死神樣板，其餘職業換粒子與音效 | 測試：七職業追擊總和 = 1.5 x 完整傷害（誤差 ≤ 1）；觸發被擋或落空 → 無追擊；任一職業單目標合計 ≤ 75；用完歸零。截圖：死神三道鐮刀斬 | `reaper_scythe`、`reaper_slash_1..3`（可退回程式畫弧線特效；其餘職業不出圖） |
| 10 | 15-17（加碼） | **單位陣列 N = 2（2 對 2）**，每位人類 1 個單位，依序行動 | 1 對 1 煙霧測試仍過；100 場種子化無頭對局：每個活著的單位每回合只行動一次、死亡單位跳過、同隊單位距離 ≥ 160 px；截圖：4 個單位 + 4 條血量，無重疊 | 無 |
| 11 | 17-20 | **MCP 公開狀態一致 + 最後美術 + 凍結**：公開狀態含能量點、職業 id；不得洩漏種子；補柵欄與缺圖 | `test_mcp_game.py` 與 `test_mcp_stdio.py` 通過；新測試：公開狀態序列化後不含私有欄位，被拒絕的呼叫（大招未就緒、已用完 2 次、錯誤階段）各有測試；新測試：所有被引用的 assets 路徑存在；三張 1920x1080 截圖（墓園 / 鐘樓 / 大招中）頂部 110 px 與底部 200 px 無特效遮擋 | `fence_black_damaged.png`、`fence_black_broken.png`（提議名）、`portrait_skeleton.png`、`portrait_bat.png`、`portrait_knight.png`、`drop_parachute.png` |

若美術晚到：第 5 到 7 步先用 `unit_skeleton.png` 當暫代圖並標示「暫代」，通過條件的數字測試不需要新圖；**職業卡只有圖載入成功才可選**，所以美術延遲不會讓示範壞掉，只會少一個職業。

---

## f. 我沒辦法驗證的事

- 沒有跑遊戲、測試或腳本；沒有開瀏覽器；沒有看任何圖片，也不知道圖的真實尺寸（柵欄 709x850 是 `converge_scenes.md` 的說法）。
- 沒有完整讀完的檔：`richness_plan.md` 只讀到第 8 節開頭（第 3 步以後沒讀）；`ui_reskin_plan.md` 只讀到 c3（沒讀 d 與建造步驟）；`airdrop_design.md` 只用搜尋讀到第 0、1 節的一部分；`roster_design.md`、`ultimates_design.md`、`game_mode.md`、`GAP_QUEUE`、兩份 converge、crosscheck、owner log 全文讀過。`asset_mapping_table.md`、`wind_design.md` 全文、`mcp_agent_protocol.md`、`colab/jobs.json` 全文沒讀（`jobs.json` 只用關鍵字搜尋）。
- Colab 的 NEW1 批次提示詞和輸出檔名只存在 Colab 儲存格，我看不到；`hunch_*` 與 `proj_soundwave` 是否與實際輸出一致未知。
- owner log 說「三顆點已完成」，index.html 搜不到對應程式；可能是我手上的 index.html 版本比較舊，或程式在別的分支。
- roster_design.md 第 0 節說 MCP 的命中框是 45 x 65、釋放點 (25, 65)；我只確認了釋放點常數 `RELEASE_DX = 25`、`RELEASE_DY = 65`，命中框沒重查。
- 所有期望傷害、命中機率與對局時間都是手算，沒有模擬；AI 命中率 33% 引用 index.html 502 行的註解。
- 行號是這次讀檔時的行號。
