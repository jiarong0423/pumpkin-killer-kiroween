#!/usr/bin/env python3
"""Draw docs/overview/kiro_allocation_20261110.svg (documentation, not game art).
Layout rule: columns = dependency level, rows = work streams; every arrow leaves a box on its right side, bends only inside the empty gutter between columns
and enters the next box on its left side, so no arrow ever runs across a box. Run: python3 -B scripts/make_kiro_allocation_svg.py  (writes the file, exit 1 on failure)."""
import sys
import xml.dom.minidom

W, H = 1860, 1290
BW, BH = 360, 92
XS = {1: 60, 2: 520, 3: 980, 4: 1440}      # column left edges; gutters are 100 px wide
YS = {r: 150 + (r - 1) * 120 for r in range(1, 9)}
COL = {"Terra": "#4299e1", "Sonnet": "#48bb78", "Main": "#ecc94b", "Owner": "#fc8181"}
LEG = {"Terra": "Terra（GPT）程式／腳本／測試", "Sonnet": "Sonnet 規劃／文件／規格", "Main": "主線 調度／驗證／合併／出圖", "Owner": "需要你（使用者）動手"}
# id: (column, row, title, subtitle, who, owner_needed)
B = {
    "A1": (1, 1, "A1 開始畫面＋取名接線", "Terra・index.html（工作樹）", "Terra", 0),
    "C1": (2, 1, "C1 姿勢動畫接線", "Terra・js/pose_anim.js", "Terra", 0),
    "C2": (3, 1, "C2 58/60 修補＋手機版", "Terra・觸控 44px／橫向", "Terra", 0),
    "A2": (1, 2, "A2 屬性測試（PBT）", "Terra・同種子同結果", "Terra", 0),
    "B1": (2, 2, "B1 決定論規則核心", "Terra・Sonnet 審", "Terra", 0),
    "C3": (3, 2, "C3 四對四 S1…S7", "Terra・Sonnet 審", "Terra", 0),
    "A4": (1, 3, "A4 擲硬幣模組", "Terra・人頭／字、種子後產生", "Terra", 0),
    "C4": (3, 3, "C4 大廳＋隨機房間＋硬幣動畫", "Terra・邀請碼／隨機房／選座位", "Terra", 0),
    "A5": (1, 4, "A5 中繼站（可提前）", "Terra・邀請碼＋隨機房間／Coolify", "Terra", 0),
    "B3": (2, 4, "B3 MCP 通道（多人）", "Terra・加入隨機房／座位／公平", "Terra", 0),
    "S0": (1, 5, "MCP 通道規格（多人）", "Sonnet・協定／隨機房／座位", "Sonnet", 0),
    "A3": (1, 6, "A3 Kiro 原生證據", "Sonnet・agents／hooks／steering", "Sonnet", 1),
    "C5": (2, 6, "C5 缺的音效", "Terra・合成或 CC0", "Terra", 0),
    "M1": (2, 7, "主線：出圖（Colab／千問）", "風鬼、硬幣、鎖鏈；逐張驗", "Main", 0),
    "M2": (3, 7, "主線：重跑驗證＋合併", "核驗檔、總帳、提示詞紀錄", "Main", 0),
    "D1": (4, 1, "D1 README＋Kiro 使用說明", "Sonnet・八個主題、附檔案", "Sonnet", 1),
    "D2": (4, 2, "D2 三分鐘影片腳本", "Sonnet・你錄製並上傳", "Sonnet", 1),
    "D3": (4, 3, "D3 部落格＋社群貼文", "Sonnet・你發布", "Sonnet", 1),
    "D4": (4, 4, "D4 繳交前檢查", "Sonnet・對照官方規則", "Sonnet", 1),
}
# dependency arrows: (from, to)
E = [("A1", "C1"), ("C1", "C2"), ("A2", "B1"), ("A4", "B1"), ("B1", "C3"), ("A4", "C4"), ("A5", "B3"), ("S0", "B3"), ("B1", "B3"), ("B3", "C4")]


def box(i):
    c, r = B[i][0], B[i][1]
    return XS[c], YS[r]


def edge(a, b):
    ax, ay = box(a); bx, by = box(b)
    ca, cb = B[a][0], B[b][0]
    ra, rb = B[a][1], B[b][1]
    if ca == cb:   # same column: straight vertical from the bottom/top centre (the rows in between are empty by design)
        x = ax + BW / 2
        if rb > ra:
            return f"M{x},{ay + BH} L{x},{by}"
        return f"M{x},{ay} L{x},{by + BH}"
    x1, y1 = ax + BW, ay + BH / 2
    x2, y2 = bx, by + BH / 2
    gx = x1 + 50 if cb == ca + 1 else None
    if cb == ca + 1:
        return f"M{x1},{y1} L{gx},{y1} L{gx},{y2} L{x2},{y2}" if y1 != y2 else f"M{x1},{y1} L{x2},{y2}"
    # a jump over an empty slot in the middle column: it must be the same row (checked below)
    return f"M{x1},{y1} L{x2},{y2}"


def main():
    # self-check: a box must not sit on the path of a straight or jumping arrow
    for a, b in E:
        ca, cb = B[a][0], B[b][0]
        if cb - ca == 2:
            assert B[a][1] == B[b][1], "a long arrow must stay in its row: %s %s" % (a, b)
            mid = ca + 1
            assert not any(v[0] == mid and v[1] == B[a][1] for v in B.values()), "a box sits on the arrow %s->%s" % (a, b)
        if cb == ca:
            lo, hi = sorted((B[a][1], B[b][1]))
            assert not any(v[0] == ca and lo < v[1] < hi for v in B.values()), "a box sits between %s and %s" % (a, b)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="-apple-system,Helvetica,Arial,sans-serif">',
         '<defs><marker id="ar" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><path d="M0,0 L10,4 L0,8 z" fill="#cbd5e0"/></marker></defs>',
         f'<rect x="0" y="0" width="{W}" height="{H}" fill="#1a1625"/>',
         '<text x="60" y="52" font-size="34" font-weight="700" fill="#f7fafc">南瓜殺手：Kiro 任務分配圖（2026-11-10）</text>',
         '<text x="60" y="88" font-size="18" fill="#a0aec0">除了「生成圖片」，其餘預設交給 Kiro；主線只調度、重跑驗證、合併。同時最多 3 個任務；改 index.html 的一次一個、各用 git worktree。</text>']
    for c, t in ((1, "第一層（現在可開始）"), (2, "第二層（依賴第一層）"), (3, "第三層（遊戲本體）"), (4, "繳交包（11-20 起草）")):
        o.append(f'<text x="{XS[c]}" y="128" font-size="22" font-weight="700" fill="#e2e8f0">{t}</text>')
    for a, b in E:
        o.append(f'<path d="{edge(a, b)}" fill="none" stroke="#cbd5e0" stroke-width="2.5" marker-end="url(#ar)"/>')
    for i, (c, r, t, s, who, own) in B.items():
        x, y = XS[c], YS[r]
        col = COL[who]
        o.append(f'<rect x="{x}" y="{y}" width="{BW}" height="{BH}" rx="12" fill="{col}" fill-opacity="0.2" stroke="{col}" stroke-width="3"/>')
        o.append(f'<text x="{x + 16}" y="{y + 38}" font-size="21" font-weight="700" fill="#f7fafc">{t}</text>')
        o.append(f'<text x="{x + 16}" y="{y + 68}" font-size="16" fill="#cbd5e0">{s}</text>')
        if own:
            o.append(f'<circle cx="{x + BW - 24}" cy="{y + 24}" r="13" fill="{COL["Owner"]}"/><text x="{x + BW - 24}" y="{y + 30}" font-size="16" font-weight="700" text-anchor="middle" fill="#1a1625">你</text>')
    ly = 1010
    o.append(f'<text x="60" y="{ly}" font-size="22" font-weight="700" fill="#e2e8f0">圖例</text>')
    x = 60
    for k in ("Terra", "Sonnet", "Main", "Owner"):
        o.append(f'<rect x="{x}" y="{ly + 20}" width="26" height="26" rx="6" fill="{COL[k]}" fill-opacity="0.2" stroke="{COL[k]}" stroke-width="3"/><text x="{x + 36}" y="{ly + 40}" font-size="18" fill="#e2e8f0">{LEG[k]}</text>')
        x += 430
    notes = ["箭頭＝依賴：後面等前面合併、驗證後才開始。箭頭只在方塊之間的空隙轉彎，不穿過任何方塊。",
             "多人連線鏈全部是 Kiro 的：A5 中繼站（邀請碼＋隨機房間）→ B3 MCP 通道（加入隨機房／座位／公平）→ C4 大廳。主線不寫這條鏈，只驗證。",
             "Kiro 點數：已用 1,480.73／4,000（待確認是「已用」），12-31 到期。繳交截止：台灣時間 12-05 06:00。",
             "來源：docs/kiro_queue_20261110.md；總帳 docs/KIRO_LEDGER.md；由 scripts/make_kiro_allocation_svg.py 產生（文件，不是遊戲美術）。"]
    for k, t in enumerate(notes):
        o.append(f'<text x="60" y="{ly + 90 + k * 30}" font-size="17" fill="#a0aec0">{t}</text>')
    o.append("</svg>")
    s = "\n".join(o)
    xml.dom.minidom.parseString(s)
    with open("docs/overview/kiro_allocation_20261110.svg", "w", encoding="utf-8") as f:
        f.write(s)
    print("OK wrote docs/overview/kiro_allocation_20261110.svg (%d boxes, %d arrows)" % (len(B), len(E)))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print("ERROR %r" % (e,))
        sys.exit(1)
