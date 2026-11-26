# 缺口表：房間／大廳流程（2026-11-25）— 依序實作，之後請 Gemini 驗證與測試

規則：每一列先寫台帳與備份、先寫會失敗的測試、改完才標「已實作」；實作完成者填證據檔，驗證者（Gemini）填「已驗」並附自己重跑的結果。不 push、不署名。規格見 `docs/room_flow_spec_20261125.md`。

狀態：未開始／進行中／已實作（Claude）／已驗（Gemini）

## A. Relay（`scripts/pk_relay.py`、`scripts/mcp_stdio_server.py`）
| 編號 | 缺口 | 現況證據 | 先失敗的測試 | 狀態 |
|---|---|---|---|---|
| R1 | 單位數裁到剩餘空位；隊伍沒有剩餘單位就拒絕加入（`team_full`）。**MCP `claim` 預設不改**（`test_mcp_claim.py` 明文要求預設整隊；Gemini 核對指出，Claude 已確認） | `mcp_stdio_server.py:1263` 預設整隊；今天白 1 占 2 個單位、白 2 沒單位（來源是網頁預設或 MCP 預設，兩者都是整隊，無法從座位表分辨） | `test_pk_relay.py` 新案例＋`test_mcp_claim.py` | 已實作（Claude）：`scripts/test_room_alloc.py` 6 支（先 2 失敗、後全綠），`test_pk_relay.py` 30、`test_mcp_claim.py`、`test_pk_relay_limits.py` 全綠；證據 `(not published)`；待 Gemini 驗 |（**R1b 已併入：** 加入時帶選填 `claim`（預設 1，不得小於已列英雄數），relay 記預留位子數，`room_state.seats[].claim` 帶出；壞的 `claim` 回 `invalid_units`）
| R2 | 只有 `seat` 缺省或為 `"auto"` 時，relay 依剩餘空位自動指派；其他無效字串（如 `"blue"`）仍回 `invalid_seat`（既有契約） | `join_room` 預設 `seat="white"` | 同上 | 已實作（Claude）：`test_room_alloc.py` 11 支（R2 的 4 支先失敗後全綠，含「明確 null 與其他字串仍回 `invalid_seat`」），relay 與 MCP 既有測試全綠；自動指派選剩餘單位最多的隊（平手紅）；證據 `(not published)` |
| R3 | `unready` 取消準備 | `pk_relay.py:658` 只會設 True | 新案例 | 已實作（Claude）：`unready`（開局前取消準備，開局後回 `room_started`）；`test_room_alloc.py` 18 支（2v2 與 3v3 都跑），relay 30、MCP、限流共 37 支全綠；證據 `(not published)` |
| R4 | 房主專用指令：非房主送來回 `host_only`（`room_options`）；房主離開時**僅限未開局的大廳階段**移交給最早入座者、沒人就關房，`room.started=True` 後離座仍判該隊負 | `host_seat_id` 只用在 `640,654` | 新案例 | 已實作（Claude）：`room_options`（`allow_ai`、`allow_mcp`，非房主回 `host_only`，壞值回 `invalid_options`，開局後回 `room_started`）、`kick`（僅房主、不能踢自己 `invalid_target`）、開戰前房主離開移交給最早入座的玩家座位（開局後不移交）；`test_room_alloc.py` 23 支（2v2 與 3v3），relay、MCP、重連、座位寬限、遲到加入測試全綠；證據 `(not published)` |
| R5 | （主人 2026-11-25：勾選改稱「允許代理人」，兩種代理都靠邀請單進房、座位標記為代理）`allow_mcp` 閘道：`allow_mcp=false` 時擋「帶閘道憑證者」與「`join` 宣告 `client_kind="mcp"` 者」（`mcp_stdio_server.py` 要送這個欄位；本機 `--connect` 的 stdio MCP 沒有閘道憑證）；`allow_mcp=true` 或舊客戶端一律放行。`client_kind` 只是提示、可偽造，不是安全邊界 | `pk_relay.py:56,204,333-338` | 新案例 | 已實作（Claude）：`allow_mcp=false` 時，宣告 `client_kind="mcp"` 或經閘道憑證的連線回 `mcp_disabled`（旁觀者不擋；錯誤憑證視為一般客戶端）；`mcp_stdio_server.py` 加送 `client_kind`；`test_room_alloc.py` 26 支，`test_mcp_risk_ab`、`test_mcp_stdio`、`test_pk_relay` 等全綠；證據 `(not published)` |
| R6 | `reset_lobby`（房主專用）：清開局狀態、保留座位與名字 | 全檔搜尋沒有 | 新案例 | 已實作（Claude）：`reset_lobby`（僅房主、僅開局後；清開局狀態、英雄、準備旗標，保留座位、預留數與房主；廣播 `lobby_reset` 與新 `room_state`；同一間房可再開一場）；`test_room_alloc.py` 28 支（2v2 與 3v3）；證據 `(not published)` |
| R7 | 名字欄位與淨化（NFC、控制／零寬／雙向／組合附標、寬度 10、1 個表情符號）；前後端共用黃金測資 | relay 沒有 `name` | 新 `test_name_rules` | 已實作（Claude）：relay `clean_name` 與 `RelayClient.cleanName`，`create_room`／`join`／`ready`／`set_name`（僅開戰前）收 `name`，非文字回 `invalid_name`；`scripts/name_vectors.json` 31 筆黃金測資＋4,000 筆隨機比對；已配置字元 60,000 筆比對 0 差異（Python 未收錄的新字元可能不同，以 relay 為準）；表情組合字（零寬連接）只留第一個；證據 `(not published)` |
| R8 | `room_state` 帶 `host_seat_id` 與每座位 `name` | 現況沒有 | 新案例 | 已實作（Claude）：`room_state` 帶 `host_seat_id`、`allow_ai`、`allow_mcp`，座位帶 `claim`、`ai`、`name`（`reset_lobby` 保留名字） |
| R9 | 內建 AI 補位座位不適用「離座判負」，並補測試 | 改前：`relayOpponentLeft` 與 MCP 的 `seat_left` 不分人或 AI | 新案例 | 已實作（Claude）：補位 `join` 帶 `ai_host_token`（房主自己的座位憑證），別人帶回 `host_only`，`allow_ai=false` 回 `ai_disabled`；座位帶 `ai`；AI 不會變房主，房主開戰前離開時 AI 座位一併移除；開戰後 AI 座位消失時單位交給同隊（真人優先）並隨 `seat_left` 帶新 `owners`，整隊沒座位則「本場不計勝負」；`test_ai_seat_leave.js` 7 支、`test_mcp_ai_seat.py` 4 支、`test_room_alloc.py` 38 支、真 relay 端到端、壓力測試含故意改壞的 relay；證據 `(not published)`、`full_suite_R9_20261126.txt` |
| R9b | 開戰後真人以 `leave` 離開，relay 只送 `room_state`、不送 `seat_left`，對手不會判定 | `pk_relay.py` `_remove_client` release 路徑 | 新案例（含「自己打完才離開」不得翻轉結果） | 已實作（Claude）：開戰後玩家主動離開一律送 `seat_left`（`reason: left`，旁觀者與開戰前不送）；網頁等畫面靜止 3 秒才判定（排隊訊息卡住最多 20 秒）；MCP 端補上「離開者角色已全倒就不判」；`test_room_alloc.py` 40 支、`test_seat_leave_dead.js` 11 支、`test_mcp_ai_seat.py` 5 支；證據 `(not published)`、`full_suite_R9b_20261126.txt` |
| R10 | 擴充 `fuzz_relay_break.py` 涵蓋新訊息 | 現有 fuzz 不含 | fuzz 自帶對照 | 已實作（Claude）：`scripts/stress_room_alloc.py`（固定種子、每步檢查 relay 內部不變量、12 人搶最後一格競爭測試）＋`test_room_stress.py`（含兩個故意改壞的 relay 必須被抓）；真 relay 種子 1 到 5 各 1500 步全過；**抓到兩個真問題並已修：** 只剩旁觀者的房間沒有房主（新入座玩家改成房主）、預設預留 1 格破壞補位流程（改成不帶 `claim` 就不預留）；證據 `(not published)`、`test_room_stress` 4 支 |
| R11（含：邀請後 30 秒沒選英雄就由系統挑預設英雄並鎖定） | **邀請單與任務說明：** 每位入座玩家都能為**自己**邀請代理（代理進邀請人同一隊、占該隊缺口，每人預設最多 1 個；邀請人開戰前離座則代理一併移除）。在缺口上按「邀請代理」，relay 產生一次性邀請（`invite_id`、邀請人座位、預留的位子、選填備註）；代理用 `join_room(room, invite=…)` 加入，座位記 `invited_by`，大廳顯示「由 某某 邀請」；加入結果多一段 `briefing`：你控制哪隊哪些單位與英雄、誰邀請你、可選英雄與「先自選英雄並鎖定、之後每回合自己出手」的指示、目標、輪到你的流程（`wait_for_turn` → `get_public_state` → `submit_action` → `end_turn`）、規則（只用公開資訊、代理階段 12 秒逾時、離座判該隊負）、邀請備註。邀請單 10 分鐘過期、只能用一次 | 現況：`join_room` 只回一行 `next`（`mcp_stdio_server.py` 約 2434），沒有邀請人概念（搜尋 `invited_by` 無結果） | 新測試（2v2、3v3） | 已實作（Claude）：`invite`／`invite_cancel`／`join` 帶 `invite`；邀請單占邀請人那隊一個位子、10 分鐘過期、一次性、關掉允許代理人即作廢、未用掉前不開戰；代理座位帶 `agent`、`invited_by`，不當房主，邀請人開戰前離座一併移除；30 秒沒選由系統挑沒人選的英雄鎖定；MCP `join_room(invite=, name=)` 回任務說明、新增 `lock_hero`；順修 R2b（自動分邊要算預留位子）；`test_room_invite.py` 13 支、`test_mcp_invite.py` 4 支（2v2、3v3）、壓力測試加邀請操作與第四個故意改壞的 relay；證據 `(not published)`；網頁邀請鈕在 F12 |
| R12 | **大廳房開始規則：** 建房帶 `lobby: true` 後不再「全員準備就開戰」；房主按開始（`begin`），且每個位子都有鎖定的英雄、沒有未用掉的邀請單，relay 倒數 3 秒才開戰，中途有人取消就停；有空位且關掉內建 AI 回 `not_full`。舊房間行為不變 | `_start_if_ready` 全員準備即開 | `test_room_lobby.py` | 已實作（Claude）：1v1、2v2、3v3；證據 `(not published)` |
| R6b | `reset_lobby` 後序號從 1 重來，瀏覽器客戶端收不到回大廳與之後的訊息（R6 測試用原始 socket 沒抓到） | 做 F9 時讀程式發現 | `test_relay_client_real.js` 第 4 段 | 已實作（Claude）：序號續編、新加入者由 `first_seq` 起算、客戶端收到 `lobby_reset` 清對戰狀態；證據 `(not published)` |
| R14 | 大廳房預設「允許代理人」關閉（主人：勾了才出現邀請代理）；舊房間維持開啟 | 截圖發現 | `test_room_lobby.py` | 已實作（Claude） |
| X1 | 寶箱落點撿不到（主人 2026-11-26）：移動範圍 640／1280 但落點只避開柵欄（781／1139） | 主人發現 | `sim_items_landing.js` 新增可站範圍檢查與第三個故意改壞版本 | 已實作（Claude）：共用 `MOVE_ZONE`；3,600 個落點撿不到由 923 降為 0；遮罩圖 `(not published)` |
| X2 | 防連點保護把「沒點過」當成時間 0：頁面快速載入後 0.35 秒內第一下被吞 | 新瀏覽器測試抓到 | `test_lobby_browser.js` | 已實作（Claude） |
| R13 | **換位：** `move`（`claim`、`team`）開戰前原地增減位子或整人換隊，座位編號換新、房主身分保留，自己的代理與邀請單一併收回 | 現況只能退房重進 | `test_room_lobby.py` | 已實作（Claude）：同上 |

## B. 頁面（`index.html`、`assets/i18n/*.json`、`sw.js`）
| 編號 | 缺口 | 先失敗的測試 | 狀態 |
|---|---|---|---|
| F1 | 第一頁左上「和朋友玩」，點一下自動建房進大廳；拿掉「建立房間」按鈕 | 頁面流程測試 | 已實作（Claude）：見台帳 ROOM-FLOW-F；`js/lobby_model.js`＋`scripts/test_lobby_model.js`、`scripts/test_lobby_browser.js`（真 Chrome＋真 relay：2v2、3v3 全流程含第二場、邀請代理、10 尺寸命中）；證據 `(not published)` |
| F2 | 名字輸入＋確認視窗（首次），存本機，設定可改 | 同上 | 已實作（Claude）：見台帳 ROOM-FLOW-F；`js/lobby_model.js`＋`scripts/test_lobby_model.js`、`scripts/test_lobby_browser.js`（真 Chrome＋真 relay：2v2、3v3 全流程含第二場、邀請代理、10 尺寸命中）；證據 `(not published)` |
| F3 | 大廳房號列：房號（點開 QR）、複製、刷新（有人入座鎖住）、人數 `x/總數` | 10 尺寸命中測試 | 已實作（Claude）：見台帳 ROOM-FLOW-F；`js/lobby_model.js`＋`scripts/test_lobby_model.js`、`scripts/test_lobby_browser.js`（真 Chrome＋真 relay：2v2、3v3 全流程含第二場、邀請代理、10 尺寸命中）；證據 `(not published)` |
| F4 | 位子兩欄（紅隊／白隊）：點空位坐、換座、一人同隊可多格、色塊 | 頁面流程測試 | 已實作（Claude）：見台帳 ROOM-FLOW-F；`js/lobby_model.js`＋`scripts/test_lobby_model.js`、`scripts/test_lobby_browser.js`（真 Chrome＋真 relay：2v2、3v3 全流程含第二場、邀請代理、10 尺寸命中）；證據 `(not published)` |
| F5 | 勾選「內建 AI 補位」「允許 MCP 代理」＋MCP 指令塊（網址＋房號＋複製） | 同上 | 已實作（Claude）：見台帳 ROOM-FLOW-F；`js/lobby_model.js`＋`scripts/test_lobby_model.js`、`scripts/test_lobby_browser.js`（真 Chrome＋真 relay：2v2、3v3 全流程含第二場、邀請代理、10 尺寸命中）；證據 `(not published)` |
| F6 | 開始鍵灰到人滿或有勾選；按開始補缺口（補進來的內建 AI 座位自動視為已鎖定）；真人與座位都滿後倒數 3 秒自動進對戰；等待寫「還在等：…」 | 同上 | 已實作（Claude）：見台帳 ROOM-FLOW-F；`js/lobby_model.js`＋`scripts/test_lobby_model.js`、`scripts/test_lobby_browser.js`（真 Chrome＋真 relay：2v2、3v3 全流程含第二場、邀請代理、10 尺寸命中）；證據 `(not published)` |
| F7 | 房主專用按鈕對非房主鎖住（灰、提示「只有房主能用」） | 命中測試加鎖定斷言 | 已實作（Claude）：見台帳 ROOM-FLOW-F；`js/lobby_model.js`＋`scripts/test_lobby_model.js`、`scripts/test_lobby_browser.js`（真 Chrome＋真 relay：2v2、3v3 全流程含第二場、邀請代理、10 尺寸命中）；證據 `(not published)` |
| F8 | 歡迎提示（房主「歡迎 名字 加入」、進來的人「歡迎加入房間 房號」，3 秒） | 頁面流程測試 | 已實作（Claude）：見台帳 ROOM-FLOW-F；`js/lobby_model.js`＋`scripts/test_lobby_model.js`、`scripts/test_lobby_browser.js`（真 Chrome＋真 relay：2v2、3v3 全流程含第二場、邀請代理、10 尺寸命中）；證據 `(not published)` |
| F9 | 打完回大廳（同房、同人、座位與名字保留，鎖定與準備重置） | 頁面流程測試 | 已實作（Claude）：見台帳 ROOM-FLOW-F；`js/lobby_model.js`＋`scripts/test_lobby_model.js`、`scripts/test_lobby_browser.js`（真 Chrome＋真 relay：2v2、3v3 全流程含第二場、邀請代理、10 尺寸命中）；證據 `(not published)` |
| F10 | 角色容器頭頂顯示名字（5 中文字或 10 英文字母＋1 表情符號），純文字、字型後備；高度要避開眩暈星與傷害浮字（頁面浮字約在 `u.y - 315`） | 靜態測試＋逐格出圖 | 已實作（Claude）：見台帳 ROOM-FLOW-F；`js/lobby_model.js`＋`scripts/test_lobby_model.js`、`scripts/test_lobby_browser.js`（真 Chrome＋真 relay：2v2、3v3 全流程含第二場、邀請代理、10 尺寸命中）；證據 `(not published)` |
| F11 | 刪除舊面板：左／右座位列、我控制、朋友加入的隊伍、紅白選擇、補位按鈕、AI 難度列 | `test_button_handlers.js` 更新 | 已實作（Claude）：見台帳 ROOM-FLOW-F；`js/lobby_model.js`＋`scripts/test_lobby_model.js`、`scripts/test_lobby_browser.js`（真 Chrome＋真 relay：2v2、3v3 全流程含第二場、邀請代理、10 尺寸命中）；證據 `(not published)` |
| F12 | 缺口旁「邀請代理」按鈕（每位入座玩家都有，只能替自己那隊的缺口邀請，隊伍沒缺口時灰掉）；顯示邀請單內容（MCP 網址＋房號＋邀請碼＋複製）；入座的代理座位顯示「由 某某 邀請」 | 命中測試＋流程測試 | 已實作（Claude）：見台帳 ROOM-FLOW-F；`js/lobby_model.js`＋`scripts/test_lobby_model.js`、`scripts/test_lobby_browser.js`（真 Chrome＋真 relay：2v2、3v3 全流程含第二場、邀請代理、10 尺寸命中）；證據 `(not published)` |

## C. 驗證與收尾
| 編號 | 項目 | 驗證者 | 狀態 |
|---|---|---|---|
| V1 | 10 尺寸真實命中＋按鈕審查更新 | Claude 寫、Gemini 重跑 | 已驗（Gemini，2026-11-26：`test_lobby_browser.js` 10 尺寸＋`layout.js en/zh-TW` 全過） |
| V2 | relay 與頁面破壞測試擴充後各多個種子 | Claude 寫、Gemini 重跑 | 已驗（Gemini，2026-11-26：`stress_room_alloc.py` seeds 1–8 全過、`redteam_probes` 僅預期 F2/F2b/F15/F15b） |
| V3 | 全套、同步 v3、隱私閘門、複本測試 | Claude | 開發庫全套已驗（2026-11-26 `run_full_suite.sh` 193 PASS / 0 FAIL / 13 SKIP，見 `(not published)`）；同步 v3 與部署待主人執行 |
| V3b | **兩組紅隊交叉掃描（主人 2026-11-26）：** 兩個無記憶審查員各自做破壞性、多維度測試，再交換發現互相驗證。維度：relay 協定濫用與資源耗盡、競態與重連、權限繞過（房主、AI 座位、代理邀請單）、名字與其他輸入注入、頁面亂點與 10 尺寸版面、2v2 與 3v3 分配、對戰判定與離座、資安與隱私外洩。每個發現附可重現指令；Claude 自己重跑確認後才記台帳、修正 | Claude 主持 | 已實作（Claude）：三輪（各自掃描、交叉、只驗最新修正）；A 21 項、B 9 項、交叉 4 項全修或註明保留；第三輪無新缺陷；台帳 REDTEAM-V3b-*；探針 `scripts/redteam_probes/` |
| V3c | **遊戲設計師整體優化（主人 2026-11-26）：** 以遊戲設計師角度審「開始畫面 → 大廳 → 對戰 → 回大廳」整體體驗，列出優化清單，分「凍結前做」與「之後」；改平衡或玩法的項目先問主人 | Claude 主持 | 已實作（Claude）：設計師審查，已在程式確認的項目已修（台帳 DESIGN-1）；改規則或平衡的 5 項待主人 |
| V3d | **彙整給 Gemini（主人 2026-11-26）：** Claude 記錄每個發現與修正（台帳、證據），修完重跑，最後彙整成一份給 Gemini（取代 `(not published)` 的範圍，涵蓋全部列） | Claude | 已實作（Claude）：`(not published)` |
| LIVE-3V3-1..4 | 混合 3v3 同步與受邀代理根治（同隊一回合一角、`owns_wire_unit`、`maybeTriggerFillerTurn` 同步修復、受邀代理全面改用 `PageJudgeRelay`＋容器裝 `nodejs`） | Gemini | 已實作並本機驗證（2026-11-26：`test_mcp_invite_page`＋`PageJudgeRelay` 14/14 OK；雙無頭瀏覽器＋雙受邀 HTTP `/mcp` 代理＋AI 補位連打 2 場 3v3 `driver=0 red_agent=0 white_agent=0 out_of_sync=0`；證據 `(not published)`）；待部署上線 |
| V4 | 真機一場：主人手機＋遠端 `/mcp` 代理，打完再回大廳一場 | 主人、Gemini | 未開始（待部署 `pk-9550d33c65` 上線後執行） |
| V5 | Gemini 逐列驗證與測試（只讀＋跑測試，附自己重跑的輸出） | Gemini | 已驗（Gemini，2026-11-26：全部指令＋額外 5 條真瀏覽器情境＋雙本機 Claude Code 交叉審查；另依主人指示完成 `GEMINI-POLISH-1` 與 `LIVE-3V3-1..4` 修正與重驗） |

## 實作順序
R1 → R2 → R3 → R4 → R8 → R5 → R6 → R9 → R9b → R7 → R11 → R10 → F11＋F1 → F3 → F4 → F5 → F12 → F7 → F6 → F2 → F8 → F9 → F10 → V1 到 V3 → V3b → V3c → V3d → V5 → V4（真機 12-01；若紅隊修正趕不及，真機先跑已完成部分，修正後再驗）。
