#!/usr/bin/env python3
"""Build the web fonts for Pumpkin Killer (Kiro task 48).

Input : build/fonts_src/   (downloaded by the main line, this script downloads nothing)
          CinzelDecorative-Bold.ttf   OFL-CinzelDecorative.txt
          NotoSerifTC[wght].ttf       OFL-NotoSerifTC.txt
          NotoSansTC[wght].ttf        OFL-NotoSansTC.txt
Output: assets/fonts/
          CinzelDecorative-Bold.ttf   copied byte for byte (reserved font name, never modified)
          pk-display-cjk-900.woff2    Noto Serif TC pinned at wght 900, subset
          pk-body-400.woff2           Noto Sans TC pinned at wght 400, subset
          pk-body-700.woff2           Noto Sans TC pinned at wght 700, subset
          OFL-*.txt, charset.txt, build_info.json, README.md
        (.woff instead of .woff2 when the brotli package is missing)

The character set is computed, not guessed (see collect_screen_chars):
  1. every non-ASCII character that can appear on screen in index.html, js/*.js, css/*.css,
     assets/i18n/*.json, the string table in docs/ui_reskin_plan.md and docs/fonts_sample.html.
     Comments are dropped. Emoji are dropped: they come from the system font.
  2. a fixed base: ASCII, Latin-1, punctuation, CJK punctuation, fullwidth ASCII.
  3. a margin: the first N characters of Big5 Level 1 (Python's own "big5" codec), so later text
     changes do not show tofu boxes. Default N = 2000. See big5_level1 for the limits of this rule.

Usage (from the repo root):
  python3 scripts/build_fonts.py                  build everything
  python3 scripts/build_fonts.py --charset-only   only write assets/fonts/charset.txt (needs no fontTools)
  python3 scripts/build_fonts.py --margin all     use all 5401 Big5 Level 1 characters as margin
  python3 scripts/build_fonts.py --list-canvas-fonts   print every ctx.font assignment with its line
"""
import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, "build", "fonts_src")
OUT_DIR = os.path.join(ROOT, "assets", "fonts")

DEFAULT_MARGIN = 2000

# key -> (file name the main line downloads, license file name next to it)
SOURCES = {
    "cinzel": ("CinzelDecorative-Bold.ttf", "OFL-CinzelDecorative.txt"),
    "serif": ("NotoSerifTC[wght].ttf", "OFL-NotoSerifTC.txt"),
    "sans": ("NotoSansTC[wght].ttf", "OFL-NotoSansTC.txt"),
}

# Faces built from a variable font: stem, source key, weight, name table values.
# Name table: family (ID 1), style (ID 2, RIBBI only), full name (ID 4), PostScript name (ID 6).
FACES = [
    {"stem": "pk-body-400", "source": "sans", "wght": 400,
     "family": "PK Body", "style": "Regular", "full": "PK Body Regular", "ps": "PKBody-Regular"},
    {"stem": "pk-body-700", "source": "sans", "wght": 700,
     "family": "PK Body", "style": "Bold", "full": "PK Body Bold", "ps": "PKBody-Bold"},
    {"stem": "pk-display-cjk-900", "source": "serif", "wght": 900,
     "family": "PK Display CJK", "style": "Regular", "full": "PK Display CJK Black", "ps": "PKDisplayCJK-Black"},
]

# Fixed part of the character set (code point ranges, inclusive).
BASE_RANGES = [
    (0x0020, 0x007E),   # ASCII
    (0x00A0, 0x00FF),   # Latin-1 (middle dot, degree sign, multiplication sign)
    (0x2010, 0x2027),   # dashes, quotes, bullet, ellipsis
    (0x2190, 0x2193),   # arrows
    (0x25B6, 0x25B6),   # black right-pointing triangle (die result)
    (0x25C0, 0x25C0),   # black left-pointing triangle (die result)
    (0x3000, 0x303F),   # CJK punctuation
    (0xFF01, 0xFF5E),   # fullwidth ASCII variants
]

# Emoji and emoji glue: these must NOT be in the subset, the system draws them.
EMOJI_RANGES = [
    (0x1F000, 0x1FAFF),  # pictographs, emoticons, transport, supplemental symbols
    (0x2300, 0x23FF),    # misc technical (stopwatch U+23F1)
    (0x2600, 0x27BF),    # misc symbols and dingbats
    (0x2B00, 0x2BFF),    # misc symbols and arrows (star U+2B50)
    (0x200D, 0x200D),    # zero width joiner
    (0x20E3, 0x20E3),    # combining keycap
    (0xFE00, 0xFE0F),    # variation selectors
    (0xE0020, 0xE007F),  # tag characters
    (0x3297, 0x3297), (0x3299, 0x3299),
]


# ----------------------------------------------------------------------------------------------
# Character set
# ----------------------------------------------------------------------------------------------

def _in_ranges(cp, ranges):
    return any(lo <= cp <= hi for lo, hi in ranges)


def is_screen_char(ch):
    """True for a non-ASCII character that belongs in the font subset."""
    cp = ord(ch)
    if cp < 0x80:
        return False
    if _in_ranges(cp, EMOJI_RANGES):
        return False
    return unicodedata.category(ch)[0] not in ("C", "Z") or cp == 0x00A0


def strip_css_comments(text):
    return re.sub(r"/\*.*?\*/", " ", text, flags=re.S)


def strip_html_comments(text):
    return re.sub(r"<!--.*?-->", " ", text, flags=re.S)


def _end_of_string(src, i):
    """Index just after the string literal that starts at src[i]."""
    quote = src[i]
    j = i + 1
    n = len(src)
    while j < n:
        ch = src[j]
        if ch == "\\":
            j += 2
            continue
        if ch == quote:
            return j + 1
        if quote != "`" and ch == "\n":
            return j  # unterminated (probably a regex literal): stop at the line end, lose nothing
        j += 1
    return n


def strip_js_comments(src):
    """Remove // and /* */ comments but keep string and template literals whole."""
    out = []
    i = 0
    n = len(src)
    while i < n:
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if c == "/" and nxt == "/":
            j = src.find("\n", i)
            i = n if j == -1 else j
            continue
        if c == "/" and nxt == "*":
            j = src.find("*/", i + 2)
            i = n if j == -1 else j + 2
            out.append(" ")
            continue
        if c in "\"'`":
            j = _end_of_string(src, i)
            out.append(src[i:j])
            i = j
            continue
        out.append(c)
        i += 1
    return "".join(out)


def html_visible_text(html):
    """HTML with comments removed; inline <script> and <style> are cleaned with their own rules."""
    html = strip_html_comments(html)
    parts = []

    def take_script(m):
        parts.append(strip_js_comments(m.group(2)))
        return " "

    def take_style(m):
        parts.append(strip_css_comments(m.group(2)))
        return " "

    html = re.sub(r"<script\b([^>]*)>(.*?)</script>", take_script, html, flags=re.S | re.I)
    html = re.sub(r"<style\b([^>]*)>(.*?)</style>", take_style, html, flags=re.S | re.I)
    parts.append(html)
    return "\n".join(parts)


def json_strings(value):
    """All string values (not keys) inside a parsed JSON document."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            for s in json_strings(v):
                yield s
    elif isinstance(value, list):
        for v in value:
            for s in json_strings(v):
                yield s


def docs_string_table(md):
    """Table rows of section 'd1' (the zh-TW / English string keys) in docs/ui_reskin_plan.md."""
    out = []
    inside = False
    for line in md.splitlines():
        if line.startswith("### d1"):
            inside = True
            continue
        if inside and (line.startswith("## ") or line.startswith("### ")):
            break
        if inside and line.lstrip().startswith("|"):
            out.append(line)
    return "\n".join(out)


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def screen_sources(root=ROOT):
    """List of (relative path, kind). Only files that exist are returned."""
    found = []

    def add(rel, kind):
        if os.path.isfile(os.path.join(root, rel)):
            found.append((rel, kind))

    add("index.html", "html")
    for p in sorted(glob.glob(os.path.join(root, "js", "*.js"))):
        found.append((os.path.relpath(p, root).replace(os.sep, "/"), "js"))
    for p in sorted(glob.glob(os.path.join(root, "css", "*.css"))):
        found.append((os.path.relpath(p, root).replace(os.sep, "/"), "css"))
    for p in sorted(glob.glob(os.path.join(root, "assets", "i18n", "*.json"))):
        found.append((os.path.relpath(p, root).replace(os.sep, "/"), "json"))
    add("docs/ui_reskin_plan.md", "docs-table")
    add("docs/fonts_sample.html", "html")
    return found


def text_of(root, rel, kind):
    raw = _read(os.path.join(root, rel))
    if kind == "html":
        return html_visible_text(raw)
    if kind == "js":
        return strip_js_comments(raw)
    if kind == "css":
        return strip_css_comments(raw)
    if kind == "json":
        return "\n".join(json_strings(json.loads(raw)))
    if kind == "docs-table":
        return docs_string_table(raw)
    raise ValueError("unknown kind " + kind)


def collect_screen_chars(root=ROOT):
    """Return (set of characters, {relative path: set of characters it contributed})."""
    total = set()
    per_file = {}
    for rel, kind in screen_sources(root):
        chars = {c for c in text_of(root, rel, kind) if is_screen_char(c)}
        per_file[rel] = chars
        total |= chars
    return total, per_file


def base_chars():
    chars = set()
    for lo, hi in BASE_RANGES:
        chars.update(chr(cp) for cp in range(lo, hi + 1))
    return chars


def big5_level1():
    """Big5 Level 1 ("frequently used", 5401 characters) in code order, from Python's own codec.

    Code order is stroke-count order, NOT frequency order. So 'the first N' means 'the N characters
    with the fewest strokes', which misses common characters that have many strokes. Python has no
    frequency table and this project adds no dependency, so this is an approximate rule. The real
    safety net is test_fonts.py: it fails when an on-screen character is not in the built font,
    whatever the margin is. Use --margin all for the whole 5401.
    """
    chars = []
    trail = list(range(0x40, 0x7F)) + list(range(0xA1, 0xFF))
    for hi in range(0xA4, 0xC7):
        for lo in trail:
            if ((hi << 8) | lo) > 0xC67E:
                break
            try:
                ch = bytes([hi, lo]).decode("big5")
            except UnicodeDecodeError:
                continue
            if len(ch) == 1 and 0x4E00 <= ord(ch) <= 0x9FFF:
                chars.append(ch)
    return chars


def margin_chars(count):
    chars = big5_level1()
    if count is None or count < 0:
        return chars
    return chars[:count]


def compute_charset(root=ROOT, margin=DEFAULT_MARGIN):
    screen, per_file = collect_screen_chars(root)
    base = base_chars()
    extra = set(margin_chars(margin))
    allc = screen | base | extra
    return {
        "screen": screen,
        "per_file": per_file,
        "base": base,
        "margin": extra,
        "all": sorted(allc, key=ord),
    }


def write_charset_file(chars, out_dir=OUT_DIR):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "charset.txt")
    lines = ["".join(chars[i:i + 64]) for i in range(0, len(chars), 64)]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    return path


def read_charset_file(path):
    return {c for c in _read(path) if c not in "\r\n"}


# ----------------------------------------------------------------------------------------------
# Licenses
# ----------------------------------------------------------------------------------------------

def reserved_font_names(ofl_text):
    """Reserved Font Names declared in the copyright header of an OFL.txt (text before the first rule line)."""
    head = re.split(r"^-{5,}", ofl_text, maxsplit=1, flags=re.M)[0]
    names = []
    for line in head.splitlines():
        if re.search(r"Reserved Font Name", line, flags=re.I):
            tail = re.split(r"Reserved Font Names?", line, maxsplit=1, flags=re.I)[1]
            names.extend(n.strip() for n in re.findall(r"[\"'\u201c\u2018]([^\"'\u201d\u2019]+)[\"'\u201d\u2019]", tail))
    return names


# ----------------------------------------------------------------------------------------------
# Output flavor
# ----------------------------------------------------------------------------------------------

def has_brotli():
    try:
        import brotli  # noqa: F401
        return True
    except ImportError:
        return False


def choose_flavor(brotli_available):
    return "woff2" if brotli_available else "woff"


# ----------------------------------------------------------------------------------------------
# Canvas font audit
# ----------------------------------------------------------------------------------------------

_FONT_ASSIGN = re.compile(r"\.font\s*=\s*((?:\"[^\"]*\"|'[^']*'|`[^`]*`|[^;\"'`])+)")


def find_canvas_font_assignments(root=ROOT):
    """[(relative path, line number, right-hand side)] for every `<something>.font = ...`."""
    found = []
    files = ["index.html"] + sorted(
        os.path.relpath(p, root).replace(os.sep, "/") for p in glob.glob(os.path.join(root, "js", "*.js")))
    for rel in files:
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            continue
        for no, line in enumerate(_read(path).splitlines(), 1):
            for m in _FONT_ASSIGN.finditer(line):
                found.append((rel, no, m.group(1).strip()))
    return found


# ----------------------------------------------------------------------------------------------
# Building (needs fontTools)
# ----------------------------------------------------------------------------------------------

def require_fonttools():
    try:
        import fontTools
        return fontTools.version
    except ImportError:
        sys.stderr.write(
            "ERROR: the Python package fontTools is not installed.\n"
            "  Install it with:  python3 -m pip install fonttools brotli\n"
            "  (Anaconda ships fontTools; check with: python3 -c \"import fontTools\")\n")
        sys.exit(2)


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def pin_weight(font, wght):
    """Turn a variable font into a static one at one weight. Subsetting first keeps this fast."""
    if "fvar" not in font:
        return font
    from fontTools.varLib import instancer
    axes = {a.axisTag: (a.minValue, a.maxValue) for a in font["fvar"].axes}
    if "wght" not in axes or not (axes["wght"][0] <= wght <= axes["wght"][1]):
        raise SystemExit("ERROR: weight %s is outside the font's wght axis %s" % (wght, axes.get("wght")))
    font = instancer.instantiateVariableFont(font, {"wght": wght}, inplace=True)
    if "STAT" in font:
        del font["STAT"]  # its axis records point at an fvar that no longer exists
    return font


def rename_font(font, face):
    """Give the modified font our own name. Copyright (ID 0) and license (IDs 13, 14) stay untouched."""
    name = font["name"]
    for nid in (1, 2, 3, 4, 6, 16, 17, 21, 22, 25):
        name.removeNames(nameID=nid)
    for pid, eid, lid in ((3, 1, 0x409), (1, 0, 0)):
        name.setName(face["family"], 1, pid, eid, lid)
        name.setName(face["style"], 2, pid, eid, lid)
        name.setName(face["ps"] + ";pk-build", 3, pid, eid, lid)
        name.setName(face["full"], 4, pid, eid, lid)
        name.setName(face["ps"], 6, pid, eid, lid)
    os2 = font["OS/2"]
    os2.usWeightClass = face["wght"]
    bold = face["style"] == "Bold"
    os2.fsSelection = (os2.fsSelection & ~0x61) | (0x20 if bold else 0x40)
    font["head"].macStyle = (font["head"].macStyle & ~0x01) | (0x01 if bold else 0)


def subset_options(flavor):
    from fontTools import subset
    opts = subset.Options()
    opts.layout_features = ["*"]      # keeps tnum / pnum / lnum if the font has them
    opts.hinting = False
    opts.notdef_outline = True
    opts.name_IDs = ["*"]             # keep copyright and license records
    opts.glyph_names = False
    opts.flavor = flavor
    return opts


def build_face(face, src_path, codepoints, flavor, out_dir):
    from fontTools import subset
    from fontTools.ttLib import TTFont
    font = TTFont(src_path)
    sub = subset.Subsetter(options=subset_options(flavor))
    sub.populate(unicodes=codepoints)
    sub.subset(font)
    font = pin_weight(font, face["wght"])
    rename_font(font, face)
    font.flavor = flavor
    out_path = os.path.join(out_dir, "%s.%s" % (face["stem"], flavor))
    font.save(out_path)
    other = os.path.join(out_dir, "%s.%s" % (face["stem"], "woff" if flavor == "woff2" else "woff2"))
    if os.path.exists(other):
        os.remove(other)  # never leave a stale file of the other flavor
    return out_path


def cmap_of(path):
    from fontTools.ttLib import TTFont
    font = TTFont(path)
    cmap = dict(font.getBestCmap())
    font.close()
    return cmap


def missing_in_source(src_path, codepoints):
    cmap = cmap_of(src_path)
    return sorted(cp for cp in codepoints if cp not in cmap)


def family_name_strings(path):
    """The name records that name the font (IDs 1, 2, 4, 6, 16, 17), as plain strings."""
    from fontTools.ttLib import TTFont
    font = TTFont(path)
    names = [rec.toUnicode() for rec in font["name"].names if rec.nameID in (1, 2, 4, 6, 16, 17)]
    font.close()
    return names


def reserved_names_in_family(path, reserved):
    """Reserved Font Names (OFL rule 3) that still appear in the font's own name records."""
    names = " | ".join(family_name_strings(path)).lower()
    return [r for r in reserved if r.lower() in names]


def feature_tags(path):
    from fontTools.ttLib import TTFont
    font = TTFont(path)
    tags = set()
    if "GSUB" in font and font["GSUB"].table.FeatureList:
        tags = {r.FeatureTag for r in font["GSUB"].table.FeatureList.FeatureRecord}
    font.close()
    return tags


def human(n):
    return "%.1f KB" % (n / 1024.0) if n < 1 << 20 else "%.2f MB" % (n / float(1 << 20))


def write_readme(path, info):
    lines = []
    w = lines.append
    w("# assets/fonts")
    w("")
    w("Generated by `scripts/build_fonts.py`. Do not edit by hand: run the script again.")
    w("")
    w("Built with fontTools %s, output format `%s`%s." % (
        info["fonttools"], info["flavor"],
        "" if info["flavor"] == "woff2" else " (the brotli package is missing, so .woff was written instead)"))
    w("")
    w("| File | What it is | Source | License file |")
    w("|---|---|---|---|")
    w("| `CinzelDecorative-Bold.ttf` | Cinzel Decorative Bold, UNMODIFIED copy (reserved font name `Cinzel`) | "
      "https://github.com/google/fonts/tree/main/ofl/cinzeldecorative | `OFL-CinzelDecorative.txt` |")
    for face in FACES:
        src = {"sans": "https://github.com/google/fonts/tree/main/ofl/notosanstc",
               "serif": "https://github.com/google/fonts/tree/main/ofl/notoseriftc"}[face["source"]]
        w("| `%s.%s` | %s, weight %d, subset, renamed `%s` | %s | `%s` |" % (
            face["stem"], info["flavor"], "Noto Serif TC" if face["source"] == "serif" else "Noto Sans TC",
            face["wght"], face["family"], src, SOURCES[face["source"]][1]))
    w("")
    w("All three fonts are licensed under the SIL Open Font License 1.1. Each license file sits next to the fonts.")
    w("Modified files (the three subsets) carry our own family names and keep the original copyright and license")
    w("records in their name tables. Cinzel keeps its Reserved Font Name, so it is copied byte for byte.")
    w("")
    w("## Character set")
    w("")
    w("The exact text file used for the subsets is `charset.txt` in this folder (%d characters)." % info["charset_total"])
    w("")
    w("| Part | Count | How it is computed |")
    w("|---|---|---|")
    w("| On-screen text | %d non-ASCII characters | Scan of index.html, js/*.js, css/*.css, assets/i18n/*.json, "
      "the d1 string table in docs/ui_reskin_plan.md and docs/fonts_sample.html. Comments dropped, emoji dropped. |"
      % info["charset_screen"])
    w("| Base | %d | ASCII, Latin-1, U+2010-2027, arrows, two triangles, CJK punctuation, fullwidth ASCII |" % info["charset_base"])
    w("| Margin | %d | Big5 Level 1 (Python `big5` codec, stroke-count order), setting `%s` |" % (
        info["charset_margin"], info["margin"]))
    w("")
    w("Characters that a source font does not contain are listed per font in `build_info.json` under"
      " `not_in_source`; the system font draws them.")
    w("")
    w("## Files and sizes")
    w("")
    w("| File | Bytes | SHA-256 |")
    w("|---|---|---|")
    for name, entry in sorted(info["files"].items()):
        w("| `%s` | %d (%s) | `%s` |" % (name, entry["bytes"], human(entry["bytes"]), entry["sha256"]))
    w("")
    w("Total: %d bytes (%s)." % (info["total_bytes"], human(info["total_bytes"])))
    w("")
    w("## Tabular figures")
    w("")
    for name, tags in sorted(info["features"].items()):
        have = [t for t in ("tnum", "pnum", "lnum") if t in tags]
        w("- `%s`: GSUB features present: %s" % (name, ", ".join(have) if have else "none of tnum/pnum/lnum"))
    w("")
    w("Where `tnum` is missing, draw numbers in equal cells (see docs/fonts_report.md).")
    w("")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


def build(src_dir, out_dir, margin):
    fonttools_version = require_fonttools()
    flavor = choose_flavor(has_brotli())
    if flavor == "woff":
        sys.stderr.write("NOTE: the brotli package is missing, writing .woff instead of .woff2 "
                         "(pip install brotli, then run again, for smaller files).\n")

    missing = []
    for key, (font_name, ofl_name) in SOURCES.items():
        for fn in (font_name, ofl_name):
            if not os.path.isfile(os.path.join(src_dir, fn)):
                missing.append(os.path.join(src_dir, fn))
    if missing:
        sys.stderr.write("ERROR: missing input files (the main line downloads them, see docs/fonts_report.md):\n")
        sys.stderr.write("".join("  %s\n" % m for m in missing))
        return 1

    os.makedirs(out_dir, exist_ok=True)
    cs = compute_charset(ROOT, margin)
    codepoints = [ord(c) for c in cs["all"]]
    write_charset_file(cs["all"], out_dir)

    info = {
        "fonttools": fonttools_version, "flavor": flavor,
        "margin": "all" if margin is None or margin < 0 else margin,
        "charset_total": len(cs["all"]), "charset_screen": len(cs["screen"]),
        "charset_base": len(cs["base"]), "charset_margin": len(cs["margin"]),
        "reserved_font_names": {}, "not_in_source": {}, "features": {}, "files": {},
    }

    # Licenses first: they decide what we may touch.
    for key, (font_name, ofl_name) in SOURCES.items():
        shutil.copyfile(os.path.join(src_dir, ofl_name), os.path.join(out_dir, ofl_name))
        info["reserved_font_names"][key] = reserved_font_names(_read(os.path.join(out_dir, ofl_name)))

    # Cinzel: copy only. The OFL defines a Modified Version as including a change of format, so even a
    # subset or a .woff2 conversion would be a modification and could not keep the name Cinzel.
    cinzel_src = os.path.join(src_dir, SOURCES["cinzel"][0])
    cinzel_out = os.path.join(out_dir, SOURCES["cinzel"][0])
    shutil.copyfile(cinzel_src, cinzel_out)
    if sha256_of(cinzel_src) != sha256_of(cinzel_out):
        sys.stderr.write("ERROR: the Cinzel copy differs from its source\n")
        return 1
    # css/fonts.css gives Cinzel only U+0020-007E; list what it lacks there so the range can be narrowed.
    info["not_in_source"]["cinzel"] = [chr(cp) for cp in missing_in_source(cinzel_src, range(0x20, 0x7F))]
    info["features"][SOURCES["cinzel"][0]] = sorted(feature_tags(cinzel_src))

    wanted = set(codepoints)
    for face in FACES:
        src_path = os.path.join(src_dir, SOURCES[face["source"]][0])
        if face["source"] not in info["not_in_source"]:
            lacking = missing_in_source(src_path, codepoints)
            info["not_in_source"][face["source"]] = [chr(cp) for cp in lacking]
            info["features"][SOURCES[face["source"]][0]] = sorted(feature_tags(src_path))
        out_path = build_face(face, src_path, codepoints, flavor, out_dir)
        have = cmap_of(out_path)
        allowed_missing = {ord(c) for c in info["not_in_source"][face["source"]]}
        lost = sorted(cp for cp in wanted if cp not in have and cp not in allowed_missing)
        if lost:
            sys.stderr.write("ERROR: %s lost characters it should have: %s\n" % (
                os.path.basename(out_path), "".join(chr(cp) for cp in lost[:40])))
            return 1
        bad = reserved_names_in_family(out_path, info["reserved_font_names"][face["source"]])
        if bad:
            sys.stderr.write("ERROR: %s still uses the reserved font name %s\n" % (os.path.basename(out_path), bad))
            return 1
        print("built %s  %s" % (os.path.relpath(out_path, ROOT), human(os.path.getsize(out_path))))

    total = 0
    for fn in sorted(os.listdir(out_dir)):
        p = os.path.join(out_dir, fn)
        if fn.endswith((".woff2", ".woff", ".ttf")):
            size = os.path.getsize(p)
            total += size
            info["files"][fn] = {"bytes": size, "sha256": sha256_of(p)}
    info["total_bytes"] = total
    info["cinzel_source_sha256"] = sha256_of(cinzel_src)

    with open(os.path.join(out_dir, "build_info.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(info, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")
    write_readme(os.path.join(out_dir, "README.md"), info)
    print("total font bytes: %d (%s)" % (total, human(total)))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build the Pumpkin Killer web fonts.")
    ap.add_argument("--src", default=SRC_DIR, help="folder with the downloaded fonts (default build/fonts_src)")
    ap.add_argument("--out", default=OUT_DIR, help="output folder (default assets/fonts)")
    ap.add_argument("--margin", default=str(DEFAULT_MARGIN),
                    help="how many Big5 Level 1 characters to add as margin, or 'all' (default %d)" % DEFAULT_MARGIN)
    ap.add_argument("--charset-only", action="store_true", help="only write charset.txt, build no fonts")
    ap.add_argument("--list-canvas-fonts", action="store_true", help="print every .font assignment and exit")
    args = ap.parse_args(argv)

    if args.list_canvas_fonts:
        for rel, no, rhs in find_canvas_font_assignments():
            print("%s:%d  %s" % (rel, no, rhs))
        return 0

    margin = -1 if args.margin == "all" else int(args.margin)
    if args.charset_only:
        cs = compute_charset(ROOT, margin)
        path = write_charset_file(cs["all"], args.out)
        print("wrote %s: %d characters (screen %d, base %d, margin %d)" % (
            os.path.relpath(path, ROOT), len(cs["all"]), len(cs["screen"]), len(cs["base"]), len(cs["margin"])))
        return 0
    return build(args.src, args.out, margin)


if __name__ == "__main__":
    sys.exit(main())
