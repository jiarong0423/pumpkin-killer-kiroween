# 角色細節收斂表（單一定案版）2026-11-09

來源優先序：1) owner_feedback_log.md（使用者確認，最高）2) index.html 實際程式 3) game_mode.md、airdrop_design.md、asset_mapping_table.md。
**缺檔**：ui_reskin_plan.md、roster_design.md、ultimates_design.md、richness_plan.md 都不存在（Kiro 任務 33、35 仍在做），所以新職業與絕招只能以 owner log 加我的推定為準，推定數字一律標 INVENTED。
讀過 docs/audio_event_map.json 的事件名（見第 4 欄音效）。程式狀態是讀 index.html 得到，沒有實跑。

## 1. 七職業總表（拆成三張，避免橫向過寬）

### 1a. 身分與武器

| 職業 | 稱號 | 幻想（一句） | 武器／投擲物美術名 | 程式狀態 |
|---|---|---|---|---|
| 骷髏長矛兵 | 骷髏長矛兵 | 肩扛長矛的亡靈標槍手 | `proj_spear`（assets/weapons/proj_spear_colab.png） | 已實作 |
| 南瓜巫師 | 南瓜巫師 | 扛砲的南瓜法師炮手 | `cannonball`（砲彈，肩上砲管） | 已實作 |
| 蝙蝠刺客 | 蝙蝠刺客 | 披風低伏、腰袋抽手裡劍的貓刺客 | `proj_shuriken`（assets/weapons/shuriken.png）＋`item_dart_bag`（shuriken_bag.png） | 已實作 |
| 南瓜重裝盾衛 | 南瓜重裝盾衛 | 重甲南瓜騎士，飛盾彈跳 | `proj_shield`（small_shield.png，側轉如硬幣） | 已實作 |
| 鬼娃新娘 | 鬼娃新娘 | 原創鬼新娘（不抄任何電影角色），丟花束 | `proj_bouquet`（暫名，花束炸彈） | 僅有開始畫面灰卡「製作中」；設計中；美術待出 |
| 鐘樓怪人 | 鐘樓怪人 | 駝背敲鐘人，把大鐘砸出去 | `proj_bell`（暫名，青銅大鐘） | 同上 |
| 死神 | 死靈法師（internal id `reaper`） | 黑袍兜帽的火焰死靈法師，手心托紫焰並向前推出 | `proj_flame`（紫色幽冥火） | 同上；絕招用空手指向姿勢與三團背後鬼火 |

superseded 2026-11-15, owner: the former skull-and-scythe reaper design is obsolete.

### 1b. 傷害與彈道（所有職業共用：發射速度 = 力度 x 13.8，重力 980，風加速度 = 風值 x 72）

| 職業 | 單發傷害／一次攻擊總傷害 | 弧線／速度／風敏感 | 特殊效果（數字） |
|---|---|---|---|
| 骷髏 | 24／24（直擊） | 標準拋物線；無額外係數；風敏感＝標準 | 霜咒：命中後被擊中者「下 2 次投擲」傷害 x0.7（-30%）；擊中後仍存活才套用 |
| 巫師 | 28／28 | 標準拋物線，彈重；砲口後座＋鏡頭震 0.18 s；風敏感＝標準 | 無額外效果。（game_mode 草案的毒彈是「絕招」，未定案，不做） |
| 蝙蝠 | 每枚 8（20 x 0.4 取整），5 枚共 40／全中 40 | 5 枚扇形 -8、-4、0、+4、+8 度（程式 spread 列表只有 4 個加原彈 = 5 枚），速度 x0.95~1.05 隨機；輕物，風敏感＝標準 | 散落小範圍，中幾枚算幾枚；空中高速自旋 |
| 盾衛 | 22 為總量；碰撞次數 N=骰 1~6，每次 22/N（四捨五入到 0.1）／最多 22 | 標準拋物線；撞柵欄、撞單位、落地各算一次碰撞；撞到單位會小跳 vy=-330、vx x-0.12 回落同一單位 | 骰子決定彈數，總傷害平均分攤（N 越大單次越輕但更穩中） |
| 鬼娃新娘 | 12／12（INVENTED） | 高弧、落地才炸；中等速度；風敏感＝標準 | 花束落地散開半徑 90 px 範圍傷害，圈內全員 12，靠近友軍也會被波及（INVENTED；官方說法只有「落地散開一小圈範圍傷害」） |
| 鐘樓怪人 | 22／22（INVENTED） | 低弧、慢速（速度係數 0.85，INVENTED）；重物，風敏感 x0.6（INVENTED） | 命中把目標往後撞 100 px（INVENTED；官方說法只有「往後撞開一段距離」） |
| 死靈法師 | 普攻 23／23（task 53 working value）；絕招三團鬼火各 11.5、全中 34.5（1.5 x 23） | 紫焰標準拋物線；速度、重力、風係數均 1.0（task 53） | 每次命中刷新燃燒：每回合開始 2 點、共 3 次、不疊加、不可致死（task 53）。舊骷髏／三鐮／30% 處決數字均 **OBSOLETE**。 |

### 1c. 反制、蓄力手感、需要的姿勢圖、音效

| 職業 | 反制（對手怎麼應付） | 蓄力手感 | 美術需要的姿勢 | 可重用音效事件（audio_event_map.json） |
|---|---|---|---|---|
| 骷髏 | 站遠、用盾衛天空盾擋、接受霜咒後用輕攻 | 慢拉長弓感，手臂越過肩 | idle（矛擱肩）／windup／release／hit／portrait；現成 windup、release、hit，idle 暫借 windup，站姿 idle 生成中 | `charge`、`throw_spear`、`flight_spear`、`impact_unit` |
| 巫師 | 砲彈弧度高，靠移動閃避、天空盾 | 砲管蓄光 | idle／aim／fire／hit／portrait（現成 unit_wizard_*_arm_charge、arm_throw、hit_react；肖像已有） | `charge`、`throw_cannon`、`flight_cannon`、`impact_unit_heavy` |
| 蝙蝠 | 5 枚散射靠走位只吃 1~2 枚；天空盾只擋一次 | 低蹲、扇形三枚在手 | idle／draw（伸手進袋）／windup／release／hit／portrait（現成 bat_draw、windup、release、hit） | `throw_shuriken`、`flight_shuriken`、`impact_unit` |
| 盾衛 | 骰運氣；站柵欄旁避免被彈兩次；自己的天空盾 | 重、慢、甩臂 | idle／windup／release／defend／hit／portrait（現成 unit_knight_* 全套，defend 有；Colab 的 knight_pose_* 待套用） | `throw_shield`、`flight_shield`、`shield_block`、`shield_place` |
| 鬼娃新娘 | 不靠太近站位；範圍圈外站開 | 輕盈甩袖，花束劃弧 | idle／windup／release／hit／portrait（5 張） | 重用 `throw_shield` 的揮動音當暫代；新：`throw_bouquet`、`impact_bouquet`（NEW） |
| 鐘樓怪人 | 被撞開後離柵欄遠、移動補位 | 兩手舉鐘過頭，沉重 | idle／windup／release／hit／portrait（5 張） | `impact_unit_heavy`＋`bell_round.ogg`（assets/audio/sfx 已有）；新：`throw_bell`（NEW） |
| 死靈法師 | 普攻火球可走位躲開；被燃燒者需在 3 次回合開始前結束戰鬥或承受最多 6 點額外傷害 | 手心紫焰，前推放出；絕招時手空、手指向前 | idle（肩旁抬手、掌心紫焰）／windup／release／hit／portrait／ult（空手指向）；無鐮刀與骷髏素材 | 新事件：`flame_throw`、`flame_hit`、`burn_tick`、`soulfire_volley`（task 53，皆待 CC0 確認） |

血量：見第 2 節衝突 1（程式全員 100；文件有 90/85/100/120）。

## 2. 衝突與待定

| # | 矛盾或發明的數字 | 建議值 | 一句理由 |
|---|---|---|---|
| 1 | 血量：game_mode.md 寫蝙蝠 90／巫師 85／骷髏 100／盾衛 120；index.html 開局把雙方 `hp = 100`（line 1233~1234），HERO_PROFILES 沒有 hp 欄位；MCP 引擎有 hp 但傷害是 16/26/18/20 | 先維持全員 100（現行可玩、AI 與玩家對等）；若要差異化再由使用者決定 | 沒有使用者確認過差異血量，先不動 |
| 2 | 傷害：index.html 24/28/20x(0.4x5)/22；MCP 引擎 18/26/16/20 | 以 index.html 為準，MCP 另案同步 | 瀏覽器是可玩版本 |
| 3 | 蝙蝠散射「5 枚」：owner 要 5 枚；程式是原彈＋4 個 spread，共 5 枚，OK；game_mode 仍寫「飛鏢」 | 以 5 枚手裡劍為準，game_mode 文字待改 | owner log 最新 |
| 4 | 補血：按鈕寫 +35、line 732 是 +35；物資箱 `SUPPLY_ITEMS.heal` 是 +30；airdrop_design 寫現有 +35 | 技能 +35、物資箱 +30 先並存，但應統一成一個值 | 同一個「補血」兩種數字會讓玩家困惑 |
| 5 | 盾衛盾牌「單發 22」：owner 說骰子決定碰撞次數、傷害平均分；game_mode.md 的絕招章節仍把「彈跳」寫成絕招 | 彈跳已是普攻（owner log 已確認），絕招另設計，game_mode 的絕招段需改 | owner 2026-11-09 較新 |
| 6 | 盾衛 `defend`：game_mode 說「只有盾衛能防禦」，owner 說點角色出選單「移動／攻擊／防禦（盾衛才有）」；新職業是否有防禦？ | 新職業無防禦 | 與現行規則一致 |
| 7 | 絕招：owner 說 4 次命中填滿、整場最多 2 次、各自計算；game_mode 又寫各職業 3/4 次觸發；owner log 第 1 節也寫「絕招本身尚未設計、不得建造任何效果或音效」 | 全域 4 次命中；各職業獨立觸發條件作廢，直到使用者拍板；程式目前沒有任何絕招 | 較新的 owner 條文覆蓋 game_mode 的早期草案 |
| 8 | 死神絕招的「骷髏命中」：是否一定先命中才觸發？被天空盾擋掉算不算？ | 必須命中單位才觸發；被擋＝不觸發 | owner 原話「after a skull hits」 |
| 9 | 死神三鐮傷害、鐘擊退距離、新娘範圍、新娘／怪人傷害、速度係數、風敏感係數 | 見 1b 表中標 INVENTED 的值 | 沒有任何文件給數字；以現有 18~28 的傷害帶為準 |
| 10 | 風敏感：沒有任何職業有獨立風係數，全是共用 `WIND_ACCEL=72`；怪人 x0.6 是我發明的 | 新增一個每職業 `windK` 欄位，預設 1，怪人 0.6 | 讓「重物不太受風」成立 |
| 11 | 回合計時 12 s（程式）vs 8 s（mockup） | 維持 12 s | 程式與測試是 12 |
| 12 | 4 打 4 的「玩家」＝每個單位還是每個控制者；每人各計命中 | 每個單位各計 | owner 說「每個玩家自己算」，單位是最小單位 |
| 13 | 柵欄：美術表說完好圖已出但未接；損毀圖待出 | 非角色範圍，略 | 本檔只管角色 |
| 14 | 開始畫面：COMING_HEROES 三卡的文案（新娘「花束炸彈」、怪人「青銅大鐘」）是主線先寫的，不是 owner 說過的 | 保留為暫定，待 Kiro 任務 33 確認 | 武器名稱 owner 沒指定 |
| 15 | 鬼娃新娘、鐘樓怪人的武器是什麼：owner 只說角色，沒說武器；「攻擊要明顯不同」 | 沿用 14 的暫定（花束範圍炸、大鐘擊退） | 與其他四種機制（直擊／高彈道／散射／彈跳）都不同 |
| 16 | colab/jobs.json 共 76 項，沒有任何 bride/hunchback/reaper flame 項目；log 說已排入 tier NEW1 | 補寫進 jobs.json 並讓主線確認；舊 `proj_skull` 工作項 **OBSOLETE** | 檔案裡找不到，無法證實「已排隊」 |
| 17 | asset_mapping_table.md 沒有列出 Drive 的 out 資料夾名稱清單（只列物件表） | 由主線在 Drive out 確認後補一份檔名 | 不能憑空報檔名 |
| 18 | 音效：新職業的事件（`throw_bouquet`、`throw_bell`、`flame_throw`、`flame_hit`、`burn_tick`、`soulfire_volley`）不在 audio_event_map.json | 先用表中的暫代事件，新事件走 Kiro 音效任務，且只用 CC0；舊 `throw_skull`／`scythe_slash` **OBSOLETE** | 使用者規則：免費、只用無版權音效 |

## 3. 給 Colab 的最終素材清單（只含角色）

規則：圖由 Colab 生成，臉朝左一次畫、另一隊靠鏡像；武器朝向要與運動方向一致；不抄任何電影角色；死神參考圖有浮水印，不照抄。

### 3a. 已存在（assets/ 內，現成可用）

| 類別 | 檔案 |
|---|---|
| 四職業整張立繪 | (not published){skeleton,wizard,bat,knight}.png（+ _raw、skeleton／bat 的 _unarmed） |
| 四職業精靈（紅白兩隊，8 狀態：idle、arm_charge、arm_throw、defend、hit_react、die、move_forward、move_back） | (not published){skeleton,wizard,bat,knight}_{red,white}_*.png（共 64 張） |
| 姿勢 | (not published){windup,release,hit}.png、bat_{draw,windup,release,hit}.png |
| 武器 | assets/weapons/{proj_spear_colab,shuriken,shuriken_bag,small_shield,dart,dart_bag}.png；assets/env/{proj_spear,proj_dagger,proj_pumpkin}.png |
| 肖像 | assets/ui/portrait_wizard.png（只有巫師） |

### 3b. 已在 colab/jobs.json 內但還沒落地的角色項目（依檔案，看不出是否已出圖）

skeleton_pose_{charge,release,follow,hit}、skeleton_javelin_windup、skeleton_portrait_{neutral,charge,throw,hit}；bat_pose_{charge,release,follow,hit}、bat_shuriken_{draw,windup,item,bag}、bat_portrait_*；knight_pose_{charge,release,follow,defend,hit}、knight_small_shield_alone、knight_body_no_shield、knight_portrait_*；wizard_pose_{aim,fire,hit}、wizard_portrait_{neutral,charge,throw,hit}、wizard_cannonball_item。

### 3c. 必須新增（尚未在 jobs.json；log 說「排在 tier NEW1」，檔內查不到，請主線補進）

| 檔名（建議） | 內容 | 張數 |
|---|---|---|
| bride_idle / bride_windup / bride_release / bride_hit | 鬼娃新娘四姿勢，面朝左 | 4 |
| bride_portrait_{neutral,charge,throw,hit} | 肖像四表情 | 4 |
| proj_bouquet | 花束炸彈，單件、朝運動方向 | 1 |
| fx_bouquet_burst | 落地散開的花瓣範圍圈（半透明） | 1 |
| hunch_idle / hunch_windup / hunch_release / hunch_hit | 鐘樓怪人四姿勢 | 4 |
| hunch_portrait_{neutral,charge,throw,hit} | 肖像四表情 | 4 |
| proj_bell | 青銅大鐘，單件 | 1 |
| reaper_idle / reaper_windup / reaper_release / reaper_hit / reaper_ult | 死靈法師五姿勢：掌心紫焰；絕招空手指向 | 5 |
| reaper_portrait_{neutral,charge,throw,hit} | 肖像四表情 | 4 |
| proj_flame | 紫色幽冥火，單件、帶鬼火尾跡 | 1 |
| fx_flame_impact / fx_burn_body | 紫焰命中與燃燒身體特效 | 2 |
| `proj_skull`、`reaper_scythe`、`reaper_slash_{1,2,3}` | **OBSOLETE**：已由 2026-11-15 owner flame redesign supersede | 0 |
| bg_belltower、bg_pumpkin_field | 場景（非角色，備註用） | 2 |

另缺（舊四職業）：portrait_{skeleton,bat,knight}（DROP1 排隊）。

## 4. 本次收斂結果摘要（6 行）

1. 七職業的稱號、武器、傷害、姿勢、音效、狀態已在一份表裡；舊四職業的數字以 index.html 實際程式為準。
2. 新三職業的名字與攻擊概念來自 owner log；傷害、範圍、擊退、速度、風係數全是我推定，已標 INVENTED。
3. 文件與程式有 18 條衝突，最大的是血量（文件 90/85/100/120，程式全 100）、補血 35 對 30、MCP 引擎傷害與瀏覽器不同。
4. 四份設計文件（roster、ultimates、richness、ui_reskin）都不存在；絕招整體仍是「不得建造」，死神絕招只列規格。
5. colab/jobs.json 查不到新職業任務，Drive out 資料夾名單也沒有，主線需補寫與核對。
6. 要使用者決定：(a) 血量要不要差異化；(b) 新娘與怪人的武器（花束／大鐘）；(c) 死神絕招被擋算不算；(d) 補血統一 30 或 35；(e) 12 秒或 8 秒。


## 更正（主線，2026-11-09 之後）
1. 鬼娃新娘的攻擊是**音波攻擊**（使用者定案），不是丟花束；表中「花束落地散開」「proj_bouquet」作廢。投射物改為半透明同心音波環；花束只留在她手上當道具。音波本質是範圍攻擊：建議「寬弧、沿飛行路徑多點判定、傷害隨距離衰減」，細節由 Kiro 任務 33 的 roster_design.md 為準。
2. 死神大招數字作廢：原表寫「骷髏 18 + 三鐮各 8 = 42」；依使用者規則（命中觸發，三下合計＝普通攻擊 1.5 倍，各 0.5 倍，骷髏頭那下不計入）：普攻 18 時三鐮各 9，合計 27，整招 45。
3. NEW1 批次的提示詞目前只存在 Colab 儲存格內，尚未存入 colab/jobs.json（子代理查到的缺口屬實）；待出圖後補存 colab/jobs_new1.json。
