import math, os, sys
G=980.0; DY=110.0; SPEED=65*13.8; DT=1/60
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"docs","wind_test_record.md")
RAW="""30,48,867,121,-121,1.12;30,72,867,182,-182,1.12;30,96,867,243,-243,1.12;30,140,867,354,-354,1.12;
40,48,916,173,-173,1.33;40,72,916,259,-259,1.33;40,96,916,346,-346,1.33;40,140,916,504,-504,1.33;
50,48,884,228,-228,1.53;50,72,884,342,-342,1.53;50,96,884,456,-456,1.53;50,140,884,665,-665,1.53;
60,48,770,286,-286,1.72;60,72,770,428,-428,1.72;60,96,770,571,-571,1.72;60,140,770,833,-833,1.72;
70,48,562,326,-326,1.83;70,72,562,488,-488,1.83;70,96,562,651,-651,1.83;70,140,562,950,-950,1.83"""
rows=[tuple(float(v) if '.' in v else int(v) for v in r.strip().split(',')) for r in RAW.replace('\n','').split(';')]
def sim(ang,F,wind,interp=False):
    a=math.radians(ang); vx=SPEED*math.cos(a); vy=-SPEED*math.sin(a); x=y=0.0; t=0.0
    while True:
        px,py,pt=x,y,t
        vx+=wind*F*DT; vy+=G*DT; x+=vx*DT; y+=vy*DT; t+=DT
        if vy>0 and y>=DY:
            if interp and y!=py:
                f=(DY-py)/(y-py); return px+(x-px)*f, pt+DT*f
            return x,t
def run():
    res=[]
    for ang,F,calm,tail,head,air in rows:
        c,t=sim(ang,F,0); tl,_=sim(ang,F,4); hd,_=sim(ang,F,-4)
        ts=tl-c; hs=hd-c; cf=0.5*4*F*t*t
        res.append(dict(ang=ang,F=F,calm=c,tail=ts,head=hs,t=t,cf=cf,
            dc=c-calm,dt_=ts-tail,dh=hs-head,dT=t-air))
    return res
res=run()
L=[]
L.append("# 風力物理測試紀錄\n")
L.append("## 測試設定（主線在瀏覽器遊戲量得，實際常數）\n")
L.append("- GRAVITY = 980 px/s^2，GROUND_Y = 860")
L.append("- 射手手高：sy = player.y - 110 = 750，手在地面線上方 110 px（落地條件 y_rel >= 110）")
L.append("- 初速 = power * 13.8 px/s，power = 65；固定步長 1/60 s")
L.append("- 每步：vx += wind*F*dt；vy += GRAVITY*dt；x += vx*dt；y += vy*dt（y 向下，vy0 = -speed*sin(angle)）")
L.append("- F = 風力係數候選（48 為目前遊戲值）；風 = 0、+4（順風）、-4（逆風）\n")
L.append("## 主線量測表（原樣轉錄，單位 px、秒）\n")
L.append("| 角度 | F | 無風落點 | 順風偏移 | 逆風偏移 | 滯空 s |\n|---|---|---|---|---|---|")
for ang,F,calm,tail,head,air in rows:
    L.append(f"| {ang} | {F} | {calm} | {tail} | {head} | {air:.2f} |")
L.append("\n## 獨立重算（python3 -I，第一個 y>=110 的步即落地，不內插）\n")
L.append("| 角度 | F | 無風落點 | 順風偏移 | 逆風偏移 | 滯空 s | 差:無風 | 差:順風 | 差:逆風 | 差:時間 | 閉式 0.5*4*F*t^2 | 閉式-順風重算 |\n|---|---|---|---|---|---|---|---|---|---|---|---|")
flags=[]
for r in res:
    bad=max(abs(r['dc']),abs(r['dt_']),abs(r['dh']))>3 or abs(r['dT'])>0.03
    if bad: flags.append((r['ang'],r['F']))
    L.append(f"| {r['ang']} | {r['F']} | {r['calm']:.1f} | {r['tail']:.1f} | {r['head']:.1f} | {r['t']:.3f} | {r['dc']:+.1f} | {r['dt_']:+.1f} | {r['dh']:+.1f} | {r['dT']:+.3f} | {r['cf']:.1f} | {r['cf']-r['tail']:+.1f} |")
# per-angle pass
L.append("\n## 各角度判定（門檻：位置差 <= 3 px 且時間差 <= 0.03 s）\n")
maxd=0
for ang in sorted({r['ang'] for r in res}):
    sub=[r for r in res if r['ang']==ang]
    m=max(max(abs(r['dc']),abs(r['dt_']),abs(r['dh'])) for r in sub)
    mt=max(abs(r['dT']) for r in sub); maxd=max(maxd,m)
    L.append(f"- {int(ang)} 度：{'PASS' if m<=3 and mt<=0.03 else 'FAIL'}（最大位置差 {m:.2f} px，最大時間差 {mt:.3f} s）")
cfmax=max(abs(r['cf']-r['tail']) for r in res); cfrel=max(abs(r['cf']-r['tail'])/r['tail'] for r in res)
L.append(f"\n## 閉式比對\n- 風造成的水平偏移 ~ 0.5*wind*F*t^2 與重算順風偏移最大差 {cfmax:.2f} px（最大相對 {cfrel*100:.2f}%）。閉式一律略低於離散結果，差值吻合半隱式積分的 0.5*a*t*dt 項（a=wind*F，如 30 度 F=48 為 1.79 px），屬步長效應而非錯誤。")
# proportionality
pr=[]
for ang in sorted({r['ang'] for r in res}):
    d={r['F']:r for r in res if r['ang']==ang}
    for F in (72,96,140):
        pr.append(abs(d[F]['tail']/d[48]['tail']-F/48))
L.append(f"- 偏移對 F 的比例（72/48、96/48、140/48）：重算比值與理想比值最大差 {max(pr):.2e}")
mtab=[]
for ang in sorted({r['ang'] for r in res}):
    d={r[1]:r for r in rows if r[0]==ang}
    for F in (72,96,140):
        mtab.append(round(d[F][3]/d[48][3],3))
L.append(f"- 主線表 tail 比值（四捨五入至 px 後）範圍 {min(mtab)}–{max(mtab)}，理想 1.5/2/2.917")
sym=max(abs(r['tail']+r['head']) for r in res)
L.append(f"- 順逆風對稱：重算 |tail+head| 最大 {sym:.3f} px（>0 代表非完全對稱）；主線表 tail 與 head 逐列互為相反數：{all(r[3]==-r[4] for r in rows)}")
L.append(f"- 超過門檻的列：{flags if flags else '無'}；最大位置差 {maxd:.2f} px")
def _i(ang,F,w): return sim(ang,F,w,True)
idiff=max(abs((_i(a,F,4)[0]-_i(a,F,0)[0])-t) for a,F,c,t,h,ar in rows)
L.append(f"- 補充：改用線性內插落地點時，順風偏移與主線表最大差 {idiff:.1f} px（內插版較不貼近主線，主線應是不內插）")
open(OUT,"w").write("\n".join(L)+"\n")
print("\n".join(L[[i for i,l in enumerate(L) if '各角度判定' in l][0]:]))
print(f"RESULT: rows={len(res)} flagged={len(flags)} max_pos_diff={maxd:.2f}px closed_form_max_diff={cfmax:.2f}px")
