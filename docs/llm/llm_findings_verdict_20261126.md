# 外部模型（Nebius Token Factory）暴力測試與審查：核對結果（2026-11-26）

主人要求用命令列呼叫外部 API 做暴力測試、除錯與意見。呼叫腳本 `scripts/llm_review.py`，模型 `zai-org/GLM-5.3` 與 `deepseek-ai/DeepSeek-V4-Pro-0813`，紀錄 `(not published)`。送出內容只有遊戲程式（relay、客戶端、大廳模型、大廳區塊）與已知未修清單，沒有金鑰或個人資料。

## 呼叫過程（失敗也記下）
- 第一輪：輸出上限 16000，兩個推理模型把額度全花在思考，回答空白或 JSON 截斷（原始輸出留在開發庫，未隨發佈）。
- 第二輪：上限 60000，仍各想約 20 萬字沒寫完；只有 GLM 審查留下 21 行（`docs/llm/glm_review_partial_20261126.md`，原始輸出留在開發庫，未隨發佈）。
- 第三輪：攻擊案例關閉思考（`chat_template_kwargs`），審查用低度思考，兩份審查完整。DeepSeek 在 JSON 裡寫了 `"x".repeat(20000)`，解析器改成展開它；GLM 攻擊答案重複到截斷，逐筆撈出 17 個完整案例。

## 暴力測試
`scripts/llm_attack_runner.py` 對本機真 relay 實跑：DeepSeek 28 個、GLM 17 個，共 45 個，**0 個打破規則或讓 relay 出錯**（`(not published)`，訊息紀錄 `llm_attack_*_transcript_20261126.jsonl`）。模型自己寫的「預期」抽查 4 個與實際相符。

## 審查意見逐條核對（Claude 先在程式確認，成立的先寫會失敗的測試再修）
| 來源 | 意見 | 核對 | 處理 |
|---|---|---|---|
| GLM、DeepSeek | 旁觀者送 `round_hash` 可讓全房顯示不同步 | 成立 | 修：只收紅白座位（`test_a_spectator_round_hash_is_refused`） |
| GLM | 本機預設 Origin 用前綴比對，`http://localhost.evil.com` 可連 | 成立（只影響沒設 `PK_RELAY_ORIGINS` 的開發環境） | 修：主機名精確比對（`test_the_default_origin_rule_is_exact_localhost`） |
| GLM、DeepSeek | 準備時列的英雄少於持有位子，開始被卡住卻看不出原因 | 成立（原始客戶端才會） | 修：大廳房準備必須每個位子都有英雄 |
| GLM | 重連時被廣播的房間狀態搶先，提早重送 | 成立（房間狀態改成快照後更常見） | 修（`test_relay_client_review.js`） |
| GLM | 第一次建房／加入的錯誤回覆沒處理，客戶端卡在連線中 | 成立 | 修：暫時性錯誤重連、永久性錯誤關閉 |
| GLM | 房間狀態把「不同步」狀態蓋掉 | 成立 | 修 |
| GLM | MCP 客戶端建不了大廳房 | 成立 | 修：建房者不受代理人勾選限制 |
| GLM | 倒數訊息被記入紀錄，新加入者會看到舊倒數 | 成立 | 修：倒數改為不記錄的通知 |
| GLM | 大廳安靜 30 分鐘會被當閒置房關掉 | 成立 | 修：大廳每 4 分鐘送 `ping`，relay 不回應只記活動 |
| GLM | 1 對 1 代理沒選英雄就被鎖定 | 不成立：1 對 1 邀請人佔滿自己那邊，邀請回 `team_full`（新測試證明） | 防禦性補上預設英雄 |
| GLM | `ackEcho` 只比對種類不比對回合 | 程式確是如此；要同時有兩個未確認的同類訊息才會發生 | 未修，列入已知（P2） |
| GLM | 邀請備註的換行例外是無效程式 | 成立但只影響文字格式 | 未修（P2 外觀） |
| GLM | 大廳人數把代理算成人 | 主人定案代理算已入座 | 不改 |
| DeepSeek | 寬限停用時重連仍用 60 秒判過期 | 只在測試設定出現 | 未修，記下 |
| DeepSeek | 頻率限制差一（`>` 應為 `>=`） | 成立，影響一次 | 未修（P2） |
| DeepSeek | 不同步回報只用座位當鍵 | 鍵含回合，同回合再次不同才漏報 | 未修（P2） |
| DeepSeek | 回大廳要清 `buffered` | 不成立：序號續編，沒有過期訊息 | 不改 |
| DeepSeek | 代理預設英雄都是第一個 | 不成立：選該隊沒人用的 | 不改 |
| DeepSeek | 房主換隊要放掉 AI 座位 | 不成立：房主仍是房主，AI 座位照用 | 不改 |
| 兩者 | 已知未修項目的除錯建議 | 與 Claude 的判斷一致（以 relay 為準、Coolify 設 `PK_RELAY_TRUST_PROXY`） | 已在 `(not published)` 第四節 |

證據：`(not published)`（12 個新測試先失敗）、`llm_review_after_20261126.txt`。
