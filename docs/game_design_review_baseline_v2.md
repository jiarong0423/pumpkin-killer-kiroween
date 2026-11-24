# 《南瓜殺手 (Pumpkin Killer)》遊戲企劃與設計合理性終審報告 (Baseline 0.2)
> 產出日期：2026-11-07  
> 審查機制：5 位子代理跨領域 3 輪極限交叉答辯（硬核高玩、休閒評測、數值平衡、關卡幾何、MCP架構）

完整詳細報告已留存於系統產物，核心定案規格收斂如下：

## 一、 核心新機制與 Baseline 0.2 定案規範

### 1. 盾牌手浮空阻擋 (Airborne Floating Shield)
- **三檔卡榫式切換**：
  - **貼地檔** ($y \in [0.0, 1.6]$)：耐久 **45 HP**，擋平射與滾地彈，與浮棺底完美咬合消除縫隙。
  - **中空檔** ($y \in [1.5, 3.0]$)：耐久 **32 HP**，擋中弧度拋物線與彈射反彈線。
  - **天幕檔** ($y \in [3.0, 4.5]$)：耐久 **24 HP**，精準攔截 $50^\circ \sim 65^\circ$ 超高仰角迫擊砲。24 HP 剛好可被砲手（26 傷害）一發敲碎！
- **破盾過量傷害貫穿 (Overkill Piercing)**：
  - 杜絕「1 HP 神盾吸收整發 26 重砲」的漏洞。當傷害 $D > \text{盾耐久 } S$，溢出部分 $(D - S) \times 80\%$ 繼續沿原軌跡下墜。
- **全新四職業動態相克食物鏈**：
  $$\text{巫師砲手 (剋後排)} \longrightarrow \text{盾衛浮空盾 (防空剋砲手)} \longrightarrow \text{骷髏彈射手 (零重力平射穿襠剋浮空盾)} \longrightarrow \text{盾衛地盾 (剋彈射手)}$$

### 2. 回合雙段任意路徑移動與記憶座標 (Two-waypoint Pathing & Memory Anchors)
- **平地一維雙向光軌**：角色純平地移動，操作簡化為水平滑軌，放開手指/滑鼠即自動提交（Auto-commit），徹底刪除多餘的【確認按鈕】！
- **轉向動能稅 (Turnaround Tax)**：單回合內若進行反向折返（夾角 $>90^\circ$），扣除固定 **0.5 格移動預算**（刺客 3 格極限折返為往返 1.25 格），防止零成本探頭。
- **空投拾取唯一性**：拾取判定**嚴格綁定在路徑終點 P2**，途經 P1 路過不給吃，搶箱必須以身犯險站在開闊地結算。
- **記憶錨點對敵公開**：對手畫面上會顯示半透明符文錨點，形成「預判盲狙記憶點」的高階心理博弈。
- **欺敵稻草人 (Decoy Scarecrow)**：刺客折返時原地留下假人，若騙到敵方砲火，稻草人爆開彩帶並跳出浮動文字 *「Missed Me! 👻😜」*。

### 3. 終局加速：第 10~12 回合【血月狂暴 (Blood Moon)】
- 第 10 回合起兩側邊界降下鬼火雨逼向中央，所有普通彈傷害提升 25%，根除殘局「滿場跑溜狗」的無聊比分局，確保產生決勝翻盤點。

---

## 二、 MCP 協定規格：單一多態工具 `submit_action`

採用 Tagged Union 架構，保證「投射／移動／防禦／待命」四選一的原子性，防止 AI 模型幻覺連拋動作：

```typescript
export interface SubmitActionInput {
  match_id: string;
  round: number;
  unit_id: string; // 如 h1~h4, a1~a4
  draft_version: number;
  action:
    | { kind: 'throw'; payload: { angle: number; charge: number; weapon_type: string; direction: 'left' | 'right' } }
    | { kind: 'move'; payload: { waypoints_x: number[]; use_boomerang: boolean; pickup_claim: boolean } }
    | { kind: 'defend'; payload: { stance: 'shield_wall' | 'crouch'; shield_tier: 'ground' | 'mid' | 'high'; facing?: 'left' | 'right' } }
    | { kind: 'idle'; payload: { reason?: string } };
}
```

### 並發時序三段式管線
- `0.0s ~ 8.0s`：AI 推理並發出 `submit_action`。
- `10.0s`：AI 硬截止（逾時強制注入安全 `idle fallback`，不亂耗盾牌次數）。
- `12.0s`：全場共同封盤，由純物理引擎進行原子確定性結算。
- **決策期絕對遮蔽**：12 秒內所有單位的盾牌高度檔位與移動路徑對敵方 100% 遮蔽，嚴防透視作弊。
