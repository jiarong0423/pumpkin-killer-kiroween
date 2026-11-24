# 投稿故事草稿（Resurrection 類別；中文初稿，英文與最終用字由你定稿；2026-11-16）

## 一句話（你的說法，我只整理成句子）
以前常常坐在電腦前面玩的 Flash 遊戲，現在已經很少人在玩了；現在有新的技術，想玩隨時都能玩：多人連線，加上 AI 對戰。

英文草稿：We used to sit at a desk and play Flash games. Almost nobody plays them now. With today's web, you can play any time you like: online with friends, and against an AI.

影片字幕可縮成：Flash 沒了。現在，隨時開打：連線 + AI。（Flash is gone. Now you can play any time: online + AI.）

## 為什麼是 Resurrection
- 過時的技術：Flash（以及它上面那一整批雙人砲台小遊戲）。
- 現代的重新想像：免安裝的網頁應用（手機、電腦都能玩）、用網址或 QR code 加入的跨裝置對戰、AI 代理透過 MCP 以玩家身分補位、確定性引擎加雜湊讓每一場都能重現。
- 畫面正中央那道會被打壞的圍欄，呼應原本遊戲裡的那道牆。
- 遊戲的規則：真人開局，空位可以讓 AI 補上；不做 AI 對 AI。

## 說法的界線
- 對外只說「靈感來自 Flash 時代的砲台對戰遊戲」。不寫原作名稱，不用原作的角色、圖片或畫面。
- 開場講「Flash 消失，那個年代的遊戲也跟著消失」，不講「某某遊戲的復刻」（國際評審不一定玩過）。

## 影片大綱（3 分鐘內，前 10 秒是重點）
1. 0 到 10 秒：手機與電腦並排，同一場對戰；掃 QR code，幾秒後開打；AI 補上空位。字幕一行：Flash is gone. The game is back.
2. 10 到 25 秒：當年（兩個人擠在同一台電腦共用鍵盤）對比現在（手機對電腦、開網址、AI 補位）。
3. 25 到 40 秒：快速閃過八個角色與四個場景，天氣與風。
4. 40 到 100 秒：一整場對戰，包含一次大招；展示手機手指拖曳瞄準。
5. 100 到 150 秒：Kiro 的部分：規格、steering、hooks、MCP 代理坐上座位、屬性測試與黃金向量證明兩邊結果一樣。
6. 結尾：一個量得到的數字（從掃碼到開打幾秒；測過哪些裝置與瀏覽器）。畫面填滿，上方不留黑邊。

## 要揭露的（照實寫）
- 圖片：由 Qwen-Image-Edit-2511（加 Lightning LoRA）在 Google Colab 上，依團隊自己的參考圖生成；授權條款由你確認後再寫進來（目前是「待確認」）。
- 音效：CC0 來源與逐檔授權在 `assets/audio/CREDITS.md`。字型：三份 OFL 授權檔在 `assets/fonts/`。
- Claude Code 的角色：頁面接線與審查、重跑每一項 Kiro 成果；Kiro 的角色：引擎、MCP 伺服器、中繼、規則模組、測試、部署檔，以及從 2026-11-16 起依 `ui-polish` 規格做的介面。詳見 `docs/KIRO_USAGE_20261116.md`。

## 還沒有證據、不能寫進去的
- 「從掃碼到開打幾秒」：要等 Kiro 182 的量測腳本跑出來。
- 「在哪些裝置與瀏覽器測過」：要你實機測過才能列。
- 斷線重連：要等重連測試通過。
