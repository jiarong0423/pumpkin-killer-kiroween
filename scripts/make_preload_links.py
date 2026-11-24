#!/usr/bin/env python3
"""Static preload: write <link rel="preload" as="image"> tags for the first-screen pictures into index.html between
<!-- PRELOAD-BEGIN --> and <!-- PRELOAD-END -->, computed ONCE from the imgList of index.html (not at run time).
Default is --check (prints what would change, exit 0 when up to date, 3 when the block is stale or missing, 1 on error);
--apply rewrites the block (backup to docs/audition/backup_index_preload_<time>.html first). Logs to docs/audition/preload_links.log."""
import os
import re
import shutil
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(ROOT, "index.html")
LOG = os.path.join(ROOT, "docs", "audition", "preload_links.log")
BEGIN, END = "<!-- PRELOAD-BEGIN -->", "<!-- PRELOAD-END -->"
# first-screen pictures: the background, the top HUD pieces, the units and their poses, the coffin and the wind ghost
PREFIXES = ("bg", "ui_banner_", "ui_top_plate_", "unit_", "wind_ghost", "ghost_idle")   # the pose frames are no longer preloaded (2026-11-16): with 8 heroes they were 41 MB of first-screen weight; the page still loads them right after the first paint


def log(msg):
    line = time.strftime("%H:%M:%S ") + msg
    print(line, flush=True)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def wanted(html):
    a = html.index("const imgList = {")
    b = html.index("\n    };", a)
    pairs = re.findall(r'(\w+):\s*"(assets/[^"]+)"', html[a:b])
    out, seen = [], set()
    for k, path in pairs:
        if k == "bg" or any(k.startswith(p) for p in PREFIXES):
            if path not in seen and os.path.exists(os.path.join(ROOT, path)):
                seen.add(path)
                out.append(path)
    return out


def webp_set():
    """The PNG paths that have a .webp sibling (js/webp_manifest.js, written by scripts/make_webp_assets.py)."""
    path = os.path.join(ROOT, "js", "webp_manifest.js")
    if not os.path.exists(path):
        return set()
    text = open(path, encoding="utf-8").read()
    start = text.index("PK_WEBP = ") + len("PK_WEBP = ")
    import json
    return set(json.loads(text[start:text.index("];", start) + 1]))


def block(paths):
    listed = webp_set()
    # a picture with a smaller .webp sibling is preloaded as the .webp (the page loads that one through assetUrl)
    lines = [BEGIN] + ['  <link rel="preload" as="image" href="%s">' % (p[:-4] + ".webp" if p in listed else p) for p in paths] + ["  " + END]
    return "\n".join(lines)


def main(argv):
    apply = "--apply" in argv
    try:
        with open(INDEX, encoding="utf-8") as f:
            html = f.read()
        new = block(wanted(html))
        if BEGIN in html and END in html:
            i = html.index(BEGIN); j = html.index(END) + len(END)
            cur = html[i:j]
            updated = html[:i] + new + html[j:]
        else:
            cur = None
            k = html.index("</head>")
            updated = html[:k] + "  " + new + "\n" + html[k:]
        if cur is not None and cur.replace("\n  ", "\n") == new.replace("\n  ", "\n"):
            log("OK preload block is up to date (%d links)" % (new.count("<link")))
            return 0
        log("STALE preload block: would write %d links" % new.count("<link"))
        if not apply:
            return 3
        bak = os.path.join(ROOT, "docs", "audition", "backup_index_preload_%s.html" % time.strftime("%Y%m%d_%H%M%S"))
        shutil.copy2(INDEX, bak)
        with open(INDEX, "w", encoding="utf-8") as f:
            f.write(updated)
        log("OK wrote %d links; backup %s" % (new.count("<link"), bak))
        return 0
    except Exception as e:
        log("ERROR %r" % (e,))
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
