#!/usr/bin/env python3
"""Draw the status board and the Gantt chart (documentation, not game art):
  docs/overview/status_board_20261110.svg   modules by status (done / built but unseen / in progress / planned / needs the owner)
  docs/overview/gantt_20261110.svg + gantt_20261110.mmd   schedule from 2026-11-10 to the deadline (2026-12-05 06:00 Taiwan time)
The dates are a PLAN written by the main line from docs/kiro_queue_20261110.md, not measured durations. Run: python3 -B scripts/make_status_gantt.py (exit 1 on failure)."""
import datetime as dt
import sys
import xml.dom.minidom

FONT = 'font-family="-apple-system,Helvetica,Arial,sans-serif"'
BG = "#1a1625"
COL = {"Terra": "#4299e1", "Sonnet": "#48bb78", "Main": "#ecc94b", "Owner": "#fc8181", "Mile": "#ed64a6"}
OUT = "docs/overview/"

# ---------------- status board ----------------
STATUS = [("done", "完成（看過或測過）", "#48bb78"), ("unseen", "已做、還沒實戰驗證", "#ecc94b"), ("doing", "進行中", "#4299e1"), ("plan", "已規劃、未開工", "#a0aec0"), ("owner", "等你動手", "#fc8181")]
MOD = {
    "done": ["核心物理與回合（倒數條）", "四個職業可玩", "頂部 HUD、聲音/重來/說明鈕", "底部 dock（無血量數字）", "靜態預載＋染色快取", "音效模組（Kiro）", "粒子特效＋屬性測試（Kiro）", "Kiro 路由／總帳／核驗紀錄", "官方規則對照檢查", "Python 引擎對齊（Kiro 80）"],
    "unseen": ["AI 對手（加風規則後命中率未量）", "狀態效果：流血／中毒／霜凍", "牆體 8% 受擊（暫定）", "浮空棺（紫色，左邊轉青）", "風鬼三格＋風旋（暫代圖）"],
    "doing": ["風鬼連續圖（千問／Colab，單張未出）", "Kiro 83 證據檔（待我驗）", "多人 MCP 通道規格", "字體／細節／框架整理（波次 E）"],
    "plan": ["4 對 4（S1…S7）", "決定論規則核心＋屬性測試", "擲硬幣＋南瓜硬幣動畫", "中繼站＋邀請碼＋隨機房間", "MCP 通道（座位／公平）", "大廳頁面", "手機版（觸控 44px／橫向）", "缺的音效", "README＋Kiro 使用說明", "三分鐘影片腳本"],
    "owner": ["公開 GitHub 倉庫＋授權可見", "部署到 Contabo／Coolify（網址）", "錄影＋上傳 YouTube", "Kiro IDE 存檔留 hook 紀錄", "部落格／社群貼文發布", "提交前最後按鈕"],
}


def status_board():
    W, H = 2000, 1000
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" {FONT}>', f'<rect x="0" y="0" width="{W}" height="{H}" fill="{BG}"/>',
         '<text x="50" y="56" font-size="34" font-weight="700" fill="#f7fafc">南瓜殺手：狀態圖（2026-11-10 收工時）</text>',
         '<text x="50" y="90" font-size="18" fill="#a0aec0">每個方塊是一個模組或交付項；欄＝目前狀態。狀態由主線依實際檢查判定，「已做、還沒實戰驗證」代表程式或測試過了但沒在真實對局看過。</text>']
    cw = 360
    for i, (k, label, c) in enumerate(STATUS):
        x = 50 + i * (cw + 20)
        o.append(f'<rect x="{x}" y="120" width="{cw}" height="52" rx="10" fill="{c}" fill-opacity="0.25" stroke="{c}" stroke-width="3"/>')
        o.append(f'<text x="{x + 16}" y="154" font-size="22" font-weight="700" fill="#f7fafc">{label}（{len(MOD[k])}）</text>')
        for j, m in enumerate(MOD[k]):
            y = 190 + j * 70
            o.append(f'<rect x="{x}" y="{y}" width="{cw}" height="58" rx="10" fill="{c}" fill-opacity="0.12" stroke="{c}" stroke-width="2"/>')
            o.append(f'<text x="{x + 14}" y="{y + 36}" font-size="18" fill="#edf2f7">{m}</text>')
    o.append(f'<text x="50" y="{H - 40}" font-size="16" fill="#718096">來源：docs/asset_inventory.json、docs/GAP_QUEUE_20261110.md、docs/kiro_queue_20261110.md；由 scripts/make_status_gantt.py 產生（文件，不是遊戲美術）。</text>')
    o.append("</svg>")
    return "\n".join(o)


# ---------------- Gantt ----------------
D0, D1 = dt.date(2026, 11, 10), dt.date(2026, 12, 5)
G = [  # (label, owner key, start, end inclusive, note)
    ("出圖：風鬼／硬幣／鎖鏈（Colab 千問）", "Main", "2026-11-11", "2026-11-13", ""),
    ("A1 開始畫面＋取名接線", "Terra", "2026-11-11", "2026-11-12", ""),
    ("A2 屬性測試", "Terra", "2026-11-11", "2026-11-12", ""),
    ("A3 Kiro 原生證據（agents／hooks）", "Sonnet", "2026-11-11", "2026-11-13", "你要在 Kiro IDE 存檔一次"),
    ("MCP 通道規格（含隨機房間）", "Sonnet", "2026-11-12", "2026-11-13", ""),
    ("A4 擲硬幣模組", "Terra", "2026-11-12", "2026-11-13", ""),
    ("A5 中繼站＋邀請碼＋隨機房", "Terra", "2026-11-12", "2026-11-16", ""),
    ("E1 字體整理", "Terra", "2026-11-13", "2026-11-14", ""),
    ("C1 姿勢動畫接線", "Terra", "2026-11-13", "2026-11-14", ""),
    ("B1 決定論規則核心", "Terra", "2026-11-14", "2026-11-19", ""),
    ("C5 缺的音效", "Terra", "2026-11-14", "2026-11-16", ""),
    ("C2 58/60 修補＋手機版", "Terra", "2026-11-15", "2026-11-18", ""),
    ("B3 MCP 通道（座位／公平）", "Terra", "2026-11-17", "2026-11-21", ""),
    ("C3 四對四（S1…S7）", "Terra", "2026-11-19", "2026-11-26", ""),
    ("C4 大廳＋硬幣動畫", "Terra", "2026-11-20", "2026-11-25", ""),
    ("E4 框架整理（拆模組）", "Terra", "2026-11-20", "2026-11-26", ""),
    ("E2 細節／E3 優化", "Terra", "2026-11-21", "2026-11-26", ""),
    ("D1–D3 README／說明／腳本／貼文草稿", "Sonnet", "2026-11-20", "2026-11-26", ""),
    ("公開倉庫＋部署＋網址（你）", "Owner", "2026-11-23", "2026-11-26", "需要你"),
    ("錄影＋YouTube 上傳（你）", "Owner", "2026-11-26", "2026-11-29", "需要你"),
    ("全面驗證、修錯、凍結後只修錯", "Main", "2026-11-27", "2026-12-03", ""),
    ("D4 繳交前檢查＋提交（你按鈕）", "Owner", "2026-12-03", "2026-12-05", "截止 12-05 06:00"),
]
MILES = [("凍結 11-27", "2026-11-27"), ("截止 12-05 06:00（台灣）", "2026-12-05")]


def d(s):
    return dt.date.fromisoformat(s)


def gantt():
    days = (D1 - D0).days + 1
    LM, TM, RW, ROW = 470, 150, 36, 38
    W = LM + days * RW + 60
    H = TM + len(G) * ROW + 190
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" {FONT}>', f'<rect x="0" y="0" width="{W}" height="{H}" fill="{BG}"/>',
         '<text x="50" y="56" font-size="34" font-weight="700" fill="#f7fafc">南瓜殺手：甘特圖（2026-11-10 到 12-05，台灣時間）</text>',
         '<text x="50" y="90" font-size="18" fill="#a0aec0">這是主線排的計畫，不是已量到的工期；每天收工用 scripts/end_of_day.py 重新對照。同時最多 3 個 Kiro 任務、改 index.html 的一次一個。</text>']
    for i in range(days):
        day = D0 + dt.timedelta(days=i)
        x = LM + i * RW
        weekend = day.weekday() >= 5
        o.append(f'<rect x="{x}" y="{TM - 30}" width="{RW}" height="{len(G) * ROW + 30}" fill="{"#2d2640" if weekend else "#211b30"}" stroke="#3b3354" stroke-width="1"/>')
        o.append(f'<text x="{x + RW / 2}" y="{TM - 8}" font-size="14" text-anchor="middle" fill="#cbd5e0">{day.day}</text>')
        if day.day == 1 or i == 0:
            o.append(f'<text x="{x + 2}" y="{TM - 36}" font-size="15" font-weight="700" fill="#e2e8f0">{day.month} 月</text>')
    for r, (label, who, s, e, note) in enumerate(G):
        y = TM + r * ROW
        o.append(f'<text x="50" y="{y + 25}" font-size="16" fill="#edf2f7">{label}</text>')
        x1 = LM + (d(s) - D0).days * RW + 3
        x2 = LM + ((d(e) - D0).days + 1) * RW - 3
        c = COL[who]
        o.append(f'<rect x="{x1}" y="{y + 6}" width="{x2 - x1}" height="{ROW - 12}" rx="8" fill="{c}" fill-opacity="0.85"/>')
        if note:
            nx = (x1 - 8, "end") if x2 > LM + (days - 3) * RW else (x2 + 8, "start")
            o.append(f'<text x="{nx[0]}" y="{y + 25}" font-size="14" text-anchor="{nx[1]}" fill="#cbd5e0">{note}</text>')
    for label, s in MILES:
        x = LM + ((d(s) - D0).days) * RW + (RW if s == "2026-12-05" else 0) * 0.25
        o.append(f'<line x1="{x}" y1="{TM - 30}" x2="{x}" y2="{TM + len(G) * ROW}" stroke="{COL["Mile"]}" stroke-width="3" stroke-dasharray="8 6"/>')
        o.append(f'<text x="{x - 6}" y="{TM + len(G) * ROW + 24}" font-size="16" font-weight="700" text-anchor="end" fill="{COL["Mile"]}">{label}</text>')
    ly = TM + len(G) * ROW + 60
    x = 50
    for k, t in (("Terra", "Terra（GPT）程式／測試"), ("Sonnet", "Sonnet 規劃／文件"), ("Main", "主線 出圖／驗證／合併"), ("Owner", "需要你（使用者）")):
        o.append(f'<rect x="{x}" y="{ly}" width="26" height="26" rx="6" fill="{COL[k]}" fill-opacity="0.85"/><text x="{x + 36}" y="{ly + 20}" font-size="17" fill="#e2e8f0">{t}</text>')
        x += 330
    o.append(f'<text x="50" y="{ly + 56}" font-size="15" fill="#718096">週末用較亮的底色。時程假設：點數足夠（已用 1,480.73／4,000）、Terra 不被長時間限流、Colab 取得 L4 或 A100。若有延誤，優先保 A5→B3→C4（多人）、公開倉庫、影片。</text>')
    o.append("</svg>")
    return "\n".join(o)


def mermaid():
    lines = ["gantt", "  title 南瓜殺手 甘特圖 2026-11-10 到 12-05", "  dateFormat YYYY-MM-DD", "  axisFormat %m-%d"]
    for label, who, s, e, note in G:
        lines.append("  %s :%s, %s, %s" % (label.replace(":", " "), "crit" if who == "Owner" else "active" if who == "Main" else "done", s, e))
    lines.append("  凍結 :milestone, 2026-11-27, 0d")
    lines.append("  截止（台灣 12-05 06:00） :milestone, 2026-12-05, 0d")
    return "\n".join(lines) + "\n"


def main():
    for name, s in (("status_board_20261110.svg", status_board()), ("gantt_20261110.svg", gantt())):
        xml.dom.minidom.parseString(s)
        with open(OUT + name, "w", encoding="utf-8") as f:
            f.write(s)
    with open(OUT + "gantt_20261110.mmd", "w", encoding="utf-8") as f:
        f.write(mermaid())
    print("OK wrote status_board_20261110.svg, gantt_20261110.svg, gantt_20261110.mmd")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("ERROR %r" % (e,))
        sys.exit(1)
