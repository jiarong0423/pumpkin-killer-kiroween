# 收斂交叉檢查（獨立第三方）

檢查對象：`index.html`（2623 行）對照 `(not published)` 第 1、6 節。全部是我自己讀程式、自己跑測試，沒採信別人的報告。沒改任何其他檔、沒用 git。

## 一、逐條對照

| 老闆說的 | 應該在哪 | 程式實際做的（關鍵行） | 判定 | 最小修法 |
|---|---|---|---|---|
| 開局只選 1 個角色 + 1 個場景，不能自由切換 | `buildStartScreen` 335-360、`startMatch` 361 | `startMatch` 呼叫 `switchHero(pickedHero)` 後把 `#start-screen` 加 hidden。能切角色的 `.hero-tab` 按鈕在 209-212，但整塊 `.dock-hero` 被 CSS `display:none !important`（11 行）。鍵盤 `keydown`（1077）沒有切角色的鍵。 | PASS | 無。（HTML 裡死按鈕可留著，不影響） |
| 場景：墓園 + 鐘樓 + 南瓜田 | `SCENES` 330-334、`sceneOk` | 只有 `graveyard` 預設 true；另兩張圖檔不存在，卡片顯示「製作中」且 `onclick` 直接 return | PARTIAL（資料到位、背景圖未做，符合 log「Colab 排隊」） | 等圖，不需改碼 |
| 左上/右上板：頭像+稱號+血條；底部 dock 的英雄區隱藏 | `unitPanel` 2382-2411；CSS 11 行 | 板內畫頭像（圖檔不在就畫 emoji）、`HERO_PROFILES[heroKey].name` 當稱號、血條與數字、盾數。`ctx.fillText(DOCK_GLYPH[heroKey]...)` 為備援。dock-hero 隱藏成立。 | PASS | 無 |
| 騎士盾：骰 1..6 次碰撞，傷害平均分 | 手擲 915、碰撞 1506/1543/1564/1578 | `pj.bounceN = 1 + Math.floor(Math.random() * 6)`；`bounceDmg = round(dmg/bounceN*10)/10`；擊中單位時 `bouncesLeft--` 並彈回同一單位 | PARTIAL | 打到圍籬(1506)或地面(1578)的彈跳也扣一次碰撞但 0 傷害，所以「平均分」只在全部碰撞都打在人身上才成立；骰到 6 卻彈在地上，總傷害會少於 dmg。最小修：圍籬/地面彈跳不扣 `bouncesLeft`（只有打到單位才扣），或在 log 寫明「落空的碰撞不給傷害」。另外 `Math.round(...*10)/10` 讓 6 次合計可能差 0.1~0.3。 |
| 貓蝙蝠：5 枚飛鏢散射 | 908-914 | 本體 + `spread=[-8,-4,4,8]` 四枚 = 5 枚，`dmg*0.4`（log 寫每枚 8，若基礎傷害 20 就是 8） | PASS | 無 |
| 標槍霜咒：被打的單位下 2 次投擲 -30% | 命中 1558；扣傷 895；計次 903 | `opp.weak = 2`；之後該單位 `executeThrow` 時 `dmg * (weak>0 ? 0.7 : 1)`，並 `su.weak--`。`resetGame` 1230 歸零。 | PASS（小瑕疵：霜咒沒擋住分裂鏢的重複扣減，因為 weak 只在投擲時扣一次，5 枚都吃 0.7，是對的） | 無 |
| 空投：第一個箱子給人類方 | `dropSide=-1` 1299；1303 先翻轉 | 第一次 `dropSide = -(-1) = +1` → `u = player` | PASS | 無 |
| 空投：落點限制 | 1305-1309 | 距離 140~279px；玩家側 `x=min(x,lo)`、AI 側 `x=max(x,hi)`，不落在圍籬或對面；再夾 300~1620 | PASS | 無 |
| 空投：3 回合失效 | 1348 | `roundNum - d.born >= 3`（只對已落地的箱子；`born` 是放箱時的回合） | PASS | 無 |
| 補給欄：新的取代舊的、只有一格 | 236 行；1338 | `supply.player = d.item`（直接覆蓋） | PASS | 無 |
| 空投：AI 只有受傷才撿 | 1341 | `if (ai.hp > ai.maxHp - 20) { d.taken=false; return; }`，即缺血 ≥20 才撿，撿了只吃補血 | PASS（AI 即使箱子是「重彈」也只補血，可接受） | 無 |
| 風：WIND_ACCEL=72，客戶端 3 處 | 501、1114、1486、2464 | 4 處引用同一常數（AI 估算 1114、真實彈道 1486、預覽線 2464；501 是定義）都用 72 | PASS | 無 |
| 風：伺服器 67.5 | `scripts/mcp_game_server.py:329`、`mcp_stdio_server.py:57` | 兩個伺服器都是 67.5，**而且是 `cur_x += (vx + wind*67.5)*dt`（風當成固定漂移速度），客戶端是 `vx += wind*72*dt`（風當成加速度）**。兩邊物理模型不同，不是只差 6%。 | PARTIAL | 老闆規則沒要求完全一致，但 `mcp_stdio_server.py:57` 註解寫「kept at 1.5x to match WIND_ACCEL 72」不實。最小修：改註解寫明「近似、非同模型」，或把伺服器改成加速度式 `vx += wind*72*dt`。 |
| AI_AIM_ERROR | 502、1143 | `const AI_AIM_ERROR = 14`；`aiPower += (rand-0.5)*2*14`，再夾 30~100 | PASS | 無（`shared/constants.json` 的同步測試沒涵蓋 AI_AIM_ERROR 與 WIND_ACCEL，見缺陷 8） |
| 音效接線 | `snd()` 308、`sfx` 310、`ensureGameAudio` 287 | 我把 index.html 所有 `snd("…")`、`sfx.hit/throw("…")` 的事件名對照 `js/audio.js`，全部都存在；開局按鈕呼叫 `ensureGameAudio()`（367）取得使用者手勢 | PASS | 無 |
| 絕招不要做 | log 第 1 節 OPEN | `grep` 沒看到絕招特效或音效實作（只有 4 次命中計數說明） | PASS | 無 |
| 新職業（鬼娃新娘、鐘樓怪人、死神）製作中 | `COMING_HEROES` 325-329 | 只是灰色卡片，無法選 | PASS（符合 log） | 無 |
| 老闆沒確認的：未選任何職業之外的 AI 職業 | 1159-1160 | AI 每次輪到都從四個可選職業隨機換（`keys=["skeleton","wizard","bat","knight"]`），沒有選到不可選的職業 | PASS，但見缺陷 6 | 無 |

## 二、測試實跑結果（最後幾行，全部是我本機剛跑的）

| 指令 | 結果 |
|---|---|
| `node scripts/test_audio.js` | `test_audio: 32 passed, 0 failed` |
| `node scripts/test_ambient_sfx.js` | `test_ambient_sfx: 13 passed, 0 failed` |
| `node scripts/test_particles.js` | `38/38 properties passed` |
| `node scripts/test_wind_fx.js` | `test_wind_fx: all 19 tests passed` |
| `python3 -B scripts/test_constants_sync.py` | `OK: shared/constants.json matches index.html for all 10 constants.` |
| `python3 -B scripts/test_mcp_game.py` | `ALL MCP GAME ENGINE TESTS PASSED!` |

註：`(not published)` 是之前就存在的，我沒有新增。

## 三、遺留問題掃描

- 被 JS 引用但不存在的 DOM id：腳本掃描 `getElementById` 與 `g("…")`，**0 個缺漏**。dock-hero 改版後沒有懸空的 id。
- 殘留的英雄選擇器：`switchHero`（796）仍在，但現在只由 `startMatch`（364）呼叫；`.hero-tab` 按鈕在被隱藏的 dock-hero 內，點不到。`document.addEventListener("click", … .hero-tab …)`（932 附近）是無害殘留。
- 開局前會丟例外的風險：我沒實機跑瀏覽器。靜態看，`initStartScreen()`、`showStartScreen()`、`requestAnimationFrame(loop)` 在 2617-2619 依序呼叫，所用的 `HERO_PROFILES`、`HERO_BLURB`、`DOCK_PORTRAIT`、`portraitOk` 都在更早位置定義，沒有看到 TDZ（暫時性死區）問題。**未實機驗證**。
- 會被請求但不存在的檔案（共 6 個，圖片載入失敗不會丟例外，只是 404）：
  1. `assets/env/bg_belltower.png`
  2. `(not published)`
  3. `assets/env/drop_parachute.png`
  4. `assets/ui/portrait_skeleton.png`
  5. `assets/ui/portrait_bat.png`
  6. `assets/ui/portrait_knight.png`
  （`portrait_wizard.png` 存在。）
- 另外 `drop_ghost.png`、`crate_fire.png` 有存在（沒被列為缺漏）。
- AI 選到不可選職業：沒有。但 AI 每一次出手都隨機換職業（1160），右上板的頭像與稱號會每回合跳動，也和「開局選一個角色」的精神不一致。

## 四、前 10 大缺陷（排序）

| 排名 | 級別 | 位置 | 問題 | 最小修法 |
|---|---|---|---|---|
| 1 | P1 | `index.html:1506-1509`、`1578-1581` | 騎士盾打到圍籬/地面也消耗一次碰撞卻 0 傷害，與「傷害平均分給每次碰撞」不符（骰 6 但打在地上就少傷害） | 只在打到單位時扣 `bouncesLeft`；圍籬/地面彈跳改用另一個計數，或老闆確認接受 |
| 2 | P1 | `index.html:1160` | AI 每回合隨機換職業，右上板頭像/稱號跳動，且 AI 騎士盾邏輯（1165）時有時無 | 開局時固定一次 `ai.profile`（`startMatch`/`resetGame` 內抽一次），`triggerAITurn` 不再抽 |
| 3 | P1 | `scripts/mcp_stdio_server.py:57`、`mcp_game_server.py:329`、`:98` | 伺服器把風當固定漂移速度，客戶端是加速度；註解宣稱「match」不實，AI 協作/評估會偏 | 改成 `vx += wind*72*dt`，或註解改為「近似」 |
| 4 | P2 | `shared/constants.json`、`scripts/test_constants_sync.py` | 同步測試只涵蓋 10 個常數，不含 `WIND_ACCEL`、`AI_AIM_ERROR`、伺服器 67.5，所以上面 3 號測不出來 | 把 `WIND_ACCEL`、`AI_AIM_ERROR` 加進 json 與測試；伺服器值加比值檢查 |
| 5 | P2 | `index.html:325-334`、檔案缺漏 | 鐘樓/南瓜田背景、降落傘、3 張頭像缺檔，開局頁兩張場景卡只顯示「製作中」 | 等 Colab 圖；在此之前不用改碼 |
| 6 | P2 | `index.html:1348` | 箱子失效條件只對「已落地」箱子算；箱子空中時不計。目前降落約 4~5 秒，影響很小 | 不需要改，記入 log 即可 |
| 7 | P2 | `index.html:1341` | AI 不撿箱子時 `d.taken=false; return;` 然後玩家若同時在 70px 內，順序是玩家先，OK；但 AI 站在箱子上且滿血時，箱子會一直擋著 `drops.length`，直到 3 回合到期才會有下一個空投 | 可接受；若想更頻繁，可以讓 AI 滿血時也推開箱子（需老闆決定） |
| 8 | P2 | `index.html:209-212`、`932` | 死按鈕與 `switchHero` 的浮字「切換職業」在開局時仍會跳出一次（364 呼叫 `switchHero`） | `startMatch` 前先設 `currentHero`，用不帶浮字的內部函式 |
| 9 | P2 | `index.html:1141-1143` | AI 角度固定 54°，只靠力度加誤差；`AI_AIM_ERROR=14` 命中率是註解的實測值，沒有測試保護 | 加一個小測試或在 log 記錄量測方式 |
| 10 | P2 | `index.html:2617-2619`（未實機驗證） | 開局頁與遊戲迴圈同時在跑，若有人從 console 呼叫 `resetGame` 以外的入口可繞過開局頁；`matchStarted` 只擋了回合計時（1419） | 若要嚴格，所有操作入口加 `if(!matchStarted) return` |

## 五、6 行摘要

1. 老闆已確認的規則在 index.html 裡大多成立：開局選角色/場景、頭像+稱號+血條進上板、dock 英雄區隱藏、5 鏢散射、霜咒 -30%×2、空投各規則、WIND_ACCEL 72 三處（外加定義處）、AI_AIM_ERROR 14、音效事件名都對得上。
2. 騎士盾「平均分」只在每次碰撞都打到人時成立，打到地面/圍籬會吃掉次數卻沒傷害（P1，`index.html:1506`、`1578`）。
3. AI 每回合換職業（`index.html:1160`），與「選一個角色」精神不一致，板上頭像會跳（P1）。
4. 伺服器風力模型與客戶端不同（漂移 vs 加速度，67.5 vs 72），註解寫「match」不實；常數同步測試沒涵蓋（P1/P2）。
5. 6 個測試/指令全部通過；缺的 6 個圖檔（鐘樓背景、南瓜田背景、降落傘、3 張頭像）只造成 404，沒有看到會丟例外的地方，DOM id 缺漏 0 個。
6. 我沒有開瀏覽器實機驗證開局頁，上面「不會丟例外」是靜態判斷；絕招與新職業確實沒做，符合 log。
