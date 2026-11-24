#!/usr/bin/env python3
"""Build the owner's review page for the overnight art: docs/audition/review.html (+ docs/audition/review/<id>.jpg thumbnails).

Every generated picture is shown on a dark backdrop with my verdict and a tick box. Pictures I flagged as a problem are listed first
and pre-ticked "redo". The owner ticks, then presses "save to project" (POST to the local snapshot receiver on 127.0.0.1:8081, scripts/snapshot_server.py)
or "copy text". The ticks are also kept in the browser (localStorage) so a refresh loses nothing. Local only; no external requests.
Usage: python3 -B scripts/make_review_html.py [--drive-out DIR]
"""
import argparse
import html
import json
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.environ.get("PK_DRIVE_DIR", "<DRIVE_DIR>")
BG = (36, 32, 66)

PROBLEMS = {   # id -> why I flagged it (Traditional Chinese, plain words)
    "pose_hunchback_idle2": "和待機圖幾乎一樣，沒有呼吸的差別",
    "pose_hunchback_charge1": "和待機圖一樣，斧頭沒有被舉起來",
    "pose_hunchback_charge3": "和待機圖一樣，斧頭沒有往後拉",
    "pose_hunchback_release": "和待機圖一樣，仍然扛著斧頭，沒有雙手投擲",
    "pose_hunchback_empty": "和待機圖一樣，手上還有斧頭",
    "pose_hunchback_hit": "和待機圖一樣，沒有受擊動作",
    "pose_skeleton_idle2": "畫成戴兜帽的灰色僧侶，不是原本的骷髏兵",
    "pose_skeleton_empty": "比其他格瘦小，站姿和待機不一致（我沒量大小）",
    "pose_reaper_charge3": "兩隻手都有火，違反「同一隻手」",
    "pose_wizard_release": "砲管和砲口火光被切到圖片邊緣",
    "portrait_front_bat": "耳朵和肩膀被切到圖片邊緣",
    "portrait_front_bride": "畫成全身，不是正臉大頭貼",
    "portrait_front_hunchback": "畫成全身而且拿著斧頭，不是正臉大頭貼",
    "fx_molotov_fire": "火焰後面有一塊暗紅色方框（去背沒有乾淨）",
    "pose_bride_charge1": "和待機幾乎一樣，只有表情不同",
    "pose_bride_charge2": "和待機幾乎一樣，只有表情不同",
    "pose_bride_charge3": "和待機幾乎一樣，只有表情不同",
}
NOTES = {   # things that look fine but deserve a look
    "pose_skeleton_charge1": "槍尖朝下，姿勢有點怪，請看一下",
    "pose_knight_empty": "手臂向左伸直，像在指東西，請確認是不是你要的空手",
}


def thumb(src, dst, size=360):
    im = Image.open(src).convert("RGB")
    a = np.asarray(im).astype(float)
    mag = (a[..., 0] + a[..., 2]) / 2 - a[..., 1]
    alpha = np.clip((160 - mag) / 50, 0, 1)[..., None]
    bg = np.zeros_like(a) + np.array(BG, dtype=float)
    out = Image.fromarray((a * alpha + bg * (1 - alpha)).astype(np.uint8))
    out.thumbnail((size, size))
    out.save(dst, quality=82)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--drive-out", default=DEFAULT_OUT)
    a = ap.parse_args(argv)
    with open(os.path.join(ROOT, "colab", "jobs_queue_20261109.json"), encoding="utf-8") as f:
        jobs = json.load(f)["jobs"]
    os.makedirs(os.path.join(ROOT, "docs", "audition", "review"), exist_ok=True)
    items = []
    for j in jobs:
        jid = j["id"]
        src = os.path.join(a.drive_out, "%s_v1_q1.png" % jid)
        if not os.path.exists(src):
            print("ERROR missing %s" % jid, file=sys.stderr)
            continue
        thumb(src, os.path.join(ROOT, "docs", "audition", "review", jid + ".jpg"))
        kind = jid.split("_")[0]
        items.append({"id": jid, "kind": kind, "problem": PROBLEMS.get(jid), "note": NOTES.get(jid)})
    items.sort(key=lambda x: (x["problem"] is None, x["id"]))
    cards = []
    for it in items:
        bad = it["problem"] is not None
        verdict = ("<div class='why bad'>" + html.escape(it["problem"]) + "</div>") if bad else (("<div class='why note'>" + html.escape(it["note"]) + "</div>") if it["note"] else "<div class='why ok'>我看起來可以</div>")
        cards.append(
            "<label class='card %s' data-id='%s'><img loading='lazy' src='review/%s.jpg' alt=''>"
            "<div class='id'>%s</div>%s"
            "<div class='row'><input type='checkbox' class='redo' %s><span>重畫</span></div></label>"
            % ("bad" if bad else "good", it["id"], it["id"], html.escape(it["id"]), verdict, "checked" if bad else ""))
    page = """<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>整夜生成審核</title>
<style>
:root{--bg:#171428;--card:#241f40;--line:#3a3466;--tx:#ece8ff;--mut:#a9a2d4;--bad:#ff7675;--ok:#55d6a8;--note:#ffd32a;--acc:#8f7bff}
@media (prefers-color-scheme: light){:root:not([data-theme=dark]){--bg:#f4f2fb;--card:#fff;--line:#d9d3f0;--tx:#241f40;--mut:#6a6490}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.5 system-ui,"Noto Sans TC",sans-serif}
header{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:12px 16px;display:flex;flex-wrap:wrap;gap:10px;align-items:center}
h1{font-size:18px;margin:0 12px 0 0}button{background:var(--acc);color:#fff;border:0;border-radius:8px;padding:9px 14px;font:inherit;cursor:pointer;min-height:40px}
button.sec{background:transparent;color:var(--tx);border:1px solid var(--line)}#count{color:var(--mut)}
main{padding:16px;max-width:1500px;margin:auto}h2{font-size:16px;margin:22px 0 10px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:12px}
.card{display:block;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:10px;cursor:pointer}
.card.bad{border-color:var(--bad)}.card img{width:100%;aspect-ratio:1;object-fit:contain;border-radius:8px;background:#242042}
.id{font-size:12px;color:var(--mut);word-break:break-all;margin-top:6px}.why{font-size:13px;margin:4px 0}.why.bad{color:var(--bad)}.why.ok{color:var(--ok)}.why.note{color:var(--note)}
.row{display:flex;gap:8px;align-items:center;margin-top:6px}.row input{width:22px;height:22px}#out{width:100%;min-height:90px;margin-top:10px;background:var(--card);color:var(--tx);border:1px solid var(--line);border-radius:8px;padding:8px;font:12px/1.4 ui-monospace,monospace}
</style></head><body>
<header><h1>整夜生成審核</h1><span id="count"></span>
<button id="save">存到專案</button><button class="sec" id="copy">複製文字</button><button class="sec" id="allok">全部取消勾選</button><button class="sec" id="allbad">只勾我標記的</button><span id="msg" class="mut"></span></header>
<main><p>勾選＝這張要重畫。紅框是我判斷有問題的（已預先勾選），其餘是我覺得可以的（沒勾）。你可以自由改。按「存到專案」我就會讀到你的選擇。</p>
<h2>有問題（我預先勾了）</h2><div class="grid" id="g1">@@BAD@@</div>
<h2>我覺得可以（你也看一下）</h2><div class="grid" id="g2">@@GOOD@@</div>
<textarea id="out" readonly></textarea></main>
<script>
(function(){
  var KEY='pk_review_v1', cards=[].slice.call(document.querySelectorAll('.card'));
  var g1=document.getElementById('g1'), g2=document.getElementById('g2');
  cards.forEach(function(c){(c.classList.contains('bad')?g1:g2).appendChild(c);});
  var saved={};try{saved=JSON.parse(localStorage.getItem(KEY)||'{}');}catch(e){}
  cards.forEach(function(c){var id=c.dataset.id,box=c.querySelector('.redo');if(id in saved)box.checked=!!saved[id];box.addEventListener('change',update);});
  function state(){var o={};cards.forEach(function(c){o[c.dataset.id]=c.querySelector('.redo').checked;});return o;}
  function update(){var s=state();try{localStorage.setItem(KEY,JSON.stringify(s));}catch(e){}
    var redo=Object.keys(s).filter(function(k){return s[k];});
    document.getElementById('count').textContent='要重畫 '+redo.length+' 張 / 共 '+cards.length+' 張';
    document.getElementById('out').value=JSON.stringify({redo:redo,accept:Object.keys(s).filter(function(k){return !s[k];})},null,1);}
  document.getElementById('copy').onclick=function(){var t=document.getElementById('out');t.select();try{document.execCommand('copy');document.getElementById('msg').textContent='已複製';}catch(e){document.getElementById('msg').textContent='請手動複製下方文字';}};
  document.getElementById('save').onclick=function(){var m=document.getElementById('msg');m.textContent='存檔中…';
    fetch('http://127.0.0.1:8081/save?name=review_result.json',{method:'POST',body:document.getElementById('out').value}).then(function(r){return r.text();}).then(function(t){m.textContent=t==='ok'?'已存到專案 ✔':'存檔失敗，請用「複製文字」';}).catch(function(){m.textContent='接收器沒開，請用「複製文字」貼給我';});};
  document.getElementById('allok').onclick=function(){cards.forEach(function(c){c.querySelector('.redo').checked=false;});update();};
  document.getElementById('allbad').onclick=function(){cards.forEach(function(c){c.querySelector('.redo').checked=c.classList.contains('bad');});update();};
  update();
})();
</script></body></html>
"""
    page = page.replace("@@BAD@@", "".join(c for c in cards if "class='card bad'" in c)).replace("@@GOOD@@", "".join(c for c in cards if "class='card good'" in c))
    with open(os.path.join(ROOT, "docs", "audition", "review.html"), "w", encoding="utf-8") as f:
        f.write(page)
    bad = sum(1 for i in items if i["problem"])
    print("review.html: %d pictures, %d flagged" % (len(items), bad))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
