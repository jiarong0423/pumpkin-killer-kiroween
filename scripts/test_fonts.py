#!/usr/bin/env python3
"""Font tests (Kiro task 48).

Run from the repo root:  python3 -B scripts/test_fonts.py

Always runs (no font files needed): the character-set scan, the build script helpers, the CSS in
css/fonts.css, the docs. The checks that need built fonts SKIP with a message while assets/fonts/ has
no font file, and FAIL once any font file is there and something is missing or wrong.
fontTools is required: without it the test fails with an install hint.
"""
import json
import os
import re
import sys
import unittest

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPTS)
sys.path.insert(0, SCRIPTS)

import build_fonts as bf  # noqa: E402  (stdlib only at import time)

FONTS_DIR = os.path.join(ROOT, "assets", "fonts")
CSS_PATH = os.path.join(ROOT, "css", "fonts.css")
MAX_TOTAL_BYTES = 6 * 1024 * 1024
FONT_EXT = (".woff2", ".woff", ".ttf")


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def built_font_files():
    if not os.path.isdir(FONTS_DIR):
        return []
    return sorted(f for f in os.listdir(FONTS_DIR) if f.lower().endswith(FONT_EXT))


BUILT = bool(built_font_files())
SKIP_MSG = "assets/fonts/ has no font files yet: run scripts/build_fonts.py (see docs/fonts_report.md). Skipped."


def _fonttools_ok():
    try:
        import fontTools  # noqa: F401
        return True
    except ImportError:
        return False


# ----------------------------------------------------------------------------------------------
# CSS parsing (no dependency)
# ----------------------------------------------------------------------------------------------

def parse_unicode_range(value):
    ranges = []
    for token in value.split(","):
        token = token.strip()
        m = re.fullmatch(r"U\+([0-9A-Fa-f]+)(?:-([0-9A-Fa-f]+))?", token)
        if not m:
            raise AssertionError("unicode-range token not understood: %r" % token)
        lo = int(m.group(1), 16)
        hi = int(m.group(2), 16) if m.group(2) else lo
        ranges.append((lo, hi))
    return ranges


def parse_font_faces(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    faces = []
    for m in re.finditer(r"@font-face\s*\{(.*?)\}", css, flags=re.S):
        decl = {k.lower(): v.strip() for k, v in re.findall(r"([\w-]+)\s*:\s*([^;]+);", m.group(1))}
        src = re.findall(r"url\(\s*[\"']?([^\"')]+)[\"']?\s*\)\s*(?:format\(\s*[\"']?([^\"')]+)[\"']?\s*\))?",
                         decl.get("src", ""))
        faces.append({
            "family": decl.get("font-family", "").strip("\"' "),
            "weight": int(decl["font-weight"]) if decl.get("font-weight", "").isdigit() else None,
            "display": decl.get("font-display"),
            "ranges": parse_unicode_range(decl["unicode-range"]) if "unicode-range" in decl else None,
            "src": src,
            "raw": decl,
        })
    return faces


def in_ranges(cp, ranges):
    return ranges is None or any(lo <= cp <= hi for lo, hi in ranges)


def existing_src(face):
    for url, _fmt in face["src"]:
        path = os.path.normpath(os.path.join(os.path.dirname(CSS_PATH), url))
        if os.path.isfile(path):
            return path
    return None


def source_key_for(path):
    name = os.path.basename(path)
    if name.startswith("Cinzel"):
        return "cinzel"
    if name.startswith("pk-display-cjk"):
        return "serif"
    if name.startswith("pk-body"):
        return "sans"
    return None


def load_build_info():
    path = os.path.join(FONTS_DIR, "build_info.json")
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# ----------------------------------------------------------------------------------------------
# Environment
# ----------------------------------------------------------------------------------------------

class TestEnvironment(unittest.TestCase):
    def test_fonttools_importable(self):
        if not _fonttools_ok():
            self.fail("fontTools is not installed. Install it with: python3 -m pip install fonttools brotli "
                      "(Anaconda already has it; check: python3 -c \"import fontTools\")")

    def test_brotli_note(self):
        if not bf.has_brotli():
            self.skipTest("brotli is not installed: build_fonts.py will write .woff instead of .woff2 "
                          "(pip install brotli for smaller files)")


# ----------------------------------------------------------------------------------------------
# Character set scan
# ----------------------------------------------------------------------------------------------

class TestScanHelpers(unittest.TestCase):
    def test_is_screen_char(self):
        for ch in ("\U0001F383", "\U0001F6E1", "\u2B50", "\u23F1", "\uFE0F", "\u200D", "\U0001F480"):
            self.assertFalse(bf.is_screen_char(ch), "emoji or glue must not be in the subset: %r" % ch)
        for ch in ("\u5357", "\u00B7", "\u25B6", "\u25C0", "\u00B0", "\u2014", "\uFF0C"):
            self.assertTrue(bf.is_screen_char(ch), "text character must be kept: %r" % ch)
        self.assertFalse(bf.is_screen_char("a"))

    def test_js_comments_dropped_strings_kept(self):
        js = ('var a = "\u4f60\u597d"; // \u8a3b\u89e3\n'
              '/* \u584a\u8a3b */ var b = `\u6a21\u677f${x}`; var u = "http://x.y/\u4e0d";')
        got = {c for c in bf.strip_js_comments(js) if bf.is_screen_char(c)}
        self.assertTrue({"\u4f60", "\u597d", "\u6a21", "\u677f", "\u4e0d"} <= got)
        self.assertFalse({"\u8a3b", "\u89e3", "\u584a"} & got)

    def test_html_visible_text(self):
        html = ('<!-- \u96b1 --><p title="\u6a19">\u5b57</p>'
                '<script>/*\u8a3b*/var s="\u78bc";</script><style>/*\u5f0f*/ .a{content:"\u6a23"}</style>')
        got = {c for c in bf.html_visible_text(html) if bf.is_screen_char(c)}
        self.assertTrue({"\u6a19", "\u5b57", "\u78bc", "\u6a23"} <= got)
        self.assertFalse({"\u96b1", "\u8a3b", "\u5f0f"} & got)

    def test_docs_string_table(self):
        md = "## c\n| x | y |\n### d1. Keys\n| `a` | \u6211\u65b9 | You |\ntext\n### d2\n| `b` | \u5047 | no |\n"
        table = bf.docs_string_table(md)
        self.assertIn("\u6211\u65b9", table)
        self.assertNotIn("\u5047", table)

    def test_choose_flavor(self):
        self.assertEqual(bf.choose_flavor(True), "woff2")
        self.assertEqual(bf.choose_flavor(False), "woff")

    def test_reserved_font_names(self):
        header = ('Copyright (c) 2012 Natanael Gama (www.ndiscovering.com), with Reserved Font Name "Cinzel".\n\n'
                  'This Font Software is licensed under the SIL Open Font License, Version 1.1.\n'
                  '-----------------------------------------------------------\n'
                  'SIL OPEN FONT LICENSE Version 1.1\n'
                  '"Reserved Font Name" refers to any names specified as such after the copyright statement(s).\n')
        self.assertEqual(bf.reserved_font_names(header), ["Cinzel"])
        none = "Copyright 2012 Google Inc. All Rights Reserved.\n\nThis Font Software...\n-----\n"
        self.assertEqual(bf.reserved_font_names(none), [])
        two = "Copyright (c) 2014, with Reserved Font Names 'Source' and 'Han'.\n\n-----\n"
        self.assertEqual(bf.reserved_font_names(two), ["Source", "Han"])


class TestCharsetScan(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cs = bf.compute_charset(ROOT, bf.DEFAULT_MARGIN)

    def test_sources_found(self):
        rels = [rel for rel, _ in bf.screen_sources(ROOT)]
        self.assertIn("index.html", rels)
        self.assertTrue(any(r.startswith("js/") for r in rels))
        self.assertTrue(any(r.startswith("css/") for r in rels))

    def test_game_text_is_in_the_scan(self):
        for ch in "\u5357\u74dc\u6bba\u624b\u56de\u5408\u8ddd\u96e2\u98a8":  # title and HUD words
            self.assertIn(ch, self.cs["screen"], "on-screen character missing from the scan: %r" % ch)

    def test_no_emoji_in_charset(self):
        for ch in self.cs["all"]:
            self.assertFalse(bf._in_ranges(ord(ch), bf.EMOJI_RANGES), "emoji in charset: U+%04X" % ord(ch))
        for ch in ("\U0001F383", "\U0001F6E1", "\u2B50", "\u23F1"):
            self.assertNotIn(ch, self.cs["all"])

    def test_charset_has_base_and_margin(self):
        allset = set(self.cs["all"])
        self.assertTrue(set(chr(c) for c in range(0x20, 0x7F)) <= allset)
        self.assertTrue(self.cs["margin"] <= allset)
        self.assertEqual(len(self.cs["margin"]), bf.DEFAULT_MARGIN)
        self.assertTrue(2300 <= len(allset) <= 8000, "unexpected charset size %d" % len(allset))

    def test_big5_level1(self):
        chars = bf.big5_level1()
        self.assertTrue(5000 <= len(chars) <= 5401, "Big5 Level 1 count %d" % len(chars))
        self.assertEqual(chars[0], "\u4e00")  # A440
        self.assertEqual(chars[1], "\u4e59")  # A441
        self.assertEqual(len(bf.margin_chars(2000)), 2000)
        self.assertEqual(len(bf.margin_chars(-1)), len(chars))

    def test_canvas_font_audit(self):
        found = bf.find_canvas_font_assignments(ROOT)
        self.assertTrue(found, "no .font assignment found in index.html or js/*.js")
        for rel, no, rhs in found:
            self.assertTrue(rhs and no > 0)

    def test_charset_file_covers_scan_when_present(self):
        path = os.path.join(FONTS_DIR, "charset.txt")
        if not os.path.isfile(path):
            self.skipTest("assets/fonts/charset.txt not written yet (python3 scripts/build_fonts.py --charset-only)")
        have = bf.read_charset_file(path)
        lacking = sorted(self.cs["screen"] - have)
        self.assertFalse(lacking, "charset.txt is out of date, new on-screen characters: %s. "
                         "Run scripts/build_fonts.py again." % "".join(lacking[:60]))


# ----------------------------------------------------------------------------------------------
# css/fonts.css
# ----------------------------------------------------------------------------------------------

class TestCss(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.css = _read(CSS_PATH)
        cls.faces = parse_font_faces(cls.css)

    def test_four_faces_swap_and_local_paths(self):
        self.assertEqual(len(self.faces), 4)
        for f in self.faces:
            self.assertEqual(f["display"], "swap", "font-display must be swap: %s" % f["raw"])
            self.assertIn(f["family"], ("PK Display", "PK Body"))
            self.assertTrue(f["src"], "no src in %s" % f["raw"])
            for url, fmt in f["src"]:
                self.assertFalse(re.match(r"[a-z]+:", url), "font must be local, not remote: %s" % url)
                self.assertTrue(url.startswith("../assets/fonts/"), url)
                self.assertTrue(fmt, "give every src a format(): %s" % url)

    def test_expected_weights(self):
        got = sorted((f["family"], f["weight"]) for f in self.faces)
        self.assertEqual(got, [("PK Body", 400), ("PK Body", 700), ("PK Display", 700), ("PK Display", 700)])

    def test_display_faces_split_latin_and_cjk(self):
        disp = [f for f in self.faces if f["family"] == "PK Display"]
        self.assertEqual(len(disp), 2)
        for f in disp:
            self.assertIsNotNone(f["ranges"], "display faces need a unicode-range")
        cinzel = [f for f in disp if any("CinzelDecorative" in u for u, _ in f["src"])]
        serif = [f for f in disp if any("pk-display-cjk" in u for u, _ in f["src"])]
        self.assertEqual((len(cinzel), len(serif)), (1, 1))
        self.assertTrue(in_ranges(ord("A"), cinzel[0]["ranges"]) and in_ranges(ord("7"), cinzel[0]["ranges"]))
        self.assertFalse(in_ranges(0x4E00, cinzel[0]["ranges"]))
        self.assertTrue(in_ranges(0x4E00, serif[0]["ranges"]) and in_ranges(0x00B7, serif[0]["ranges"]))
        self.assertFalse(in_ranges(ord("A"), serif[0]["ranges"]))

    def test_unicode_ranges_do_not_overlap_in_a_family(self):
        disp = [f for f in self.faces if f["family"] == "PK Display"]
        a, b = disp[0]["ranges"], disp[1]["ranges"]
        for lo1, hi1 in a:
            for lo2, hi2 in b:
                self.assertTrue(hi1 < lo2 or hi2 < lo1, "overlap U+%X-%X and U+%X-%X" % (lo1, hi1, lo2, hi2))

    def test_cinzel_is_the_original_file(self):
        for f in self.faces:
            for url, _ in f["src"]:
                if "CinzelDecorative" in url:
                    self.assertTrue(url.endswith("CinzelDecorative-Bold.ttf"), url)
                    self.assertEqual(len(f["src"]), 1, "Cinzel has one src: the unmodified .ttf")

    def test_stacks(self):
        for var, first, generic in (("--font-display", "PK Display", "serif"), ("--font-body", "PK Body", "sans-serif")):
            m = re.search(re.escape(var) + r"\s*:\s*([^;]+);", self.css)
            self.assertIsNotNone(m, var + " not defined")
            items = [s.strip().strip("\"'") for s in m.group(1).split(",")]
            self.assertEqual(items[0], first)
            self.assertEqual(items[-1], generic, var + " must end with a generic family")
            self.assertGreaterEqual(len(items), 4, var + " needs system fallbacks")

    def test_lite_mode_drops_our_fonts(self):
        m = re.search(r"html\.pk-lite\s*\{(.*?)\}", self.css, flags=re.S)
        self.assertIsNotNone(m, "html.pk-lite block missing")
        self.assertNotIn("PK Display", m.group(1))
        self.assertNotIn("PK Body", m.group(1))
        self.assertIn("--font-display", m.group(1))
        self.assertIn("--font-body", m.group(1))


class TestDocs(unittest.TestCase):
    def test_files_exist(self):
        for rel in ("docs/fonts_report.md", "docs/fonts_sample.html", ".kiro/specs/fonts/requirements.md",
                    ".kiro/specs/fonts/design.md", ".kiro/specs/fonts/tasks.md", "assets/fonts/README.md"):
            self.assertTrue(os.path.isfile(os.path.join(ROOT, rel)), "missing " + rel)

    def test_sample_page_uses_the_stylesheet(self):
        self.assertIn('href="../css/fonts.css"', _read(os.path.join(ROOT, "docs", "fonts_sample.html")))


# ----------------------------------------------------------------------------------------------
# Built fonts
# ----------------------------------------------------------------------------------------------

@unittest.skipUnless(BUILT, SKIP_MSG)
class TestBuiltFonts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.faces = [(f, existing_src(f)) for f in parse_font_faces(_read(CSS_PATH))]
        cls.info = load_build_info()

    def test_every_css_face_has_a_file(self):
        for f, path in self.faces:
            self.assertIsNotNone(path, "no file exists for @font-face %s %s; tried %s" % (
                f["family"], f["weight"], [u for u, _ in f["src"]]))

    def test_no_stray_font_files(self):
        used = {os.path.basename(p) for _, p in self.faces if p}
        for name in built_font_files():
            self.assertIn(name, used, "assets/fonts/%s is not used by css/fonts.css" % name)

    def test_license_next_to_each_font(self):
        want = {"cinzel": "OFL-CinzelDecorative.txt", "serif": "OFL-NotoSerifTC.txt", "sans": "OFL-NotoSansTC.txt"}
        for _, path in self.faces:
            if not path:
                continue
            key = source_key_for(path)
            self.assertIsNotNone(key, "unknown font file " + path)
            lic = os.path.join(os.path.dirname(path), want[key])
            self.assertTrue(os.path.isfile(lic), "license file missing next to %s: %s" % (os.path.basename(path), want[key]))
            text = _read(lic)
            self.assertGreater(len(text), 1000)
            self.assertIn("SIL OPEN FONT LICENSE", text.upper())
            self.assertIn("1.1", text)

    def test_total_size_under_6_mb(self):
        total = 0
        for dirpath, _dirs, files in os.walk(FONTS_DIR):
            total += sum(os.path.getsize(os.path.join(dirpath, n)) for n in files)
        self.assertLess(total, MAX_TOTAL_BYTES, "assets/fonts is %d bytes, limit %d" % (total, MAX_TOTAL_BYTES))

    def test_readme_and_charset_exist(self):
        self.assertGreater(os.path.getsize(os.path.join(FONTS_DIR, "README.md")), 200,
                           "assets/fonts/README.md is empty: run scripts/build_fonts.py")
        self.assertTrue(os.path.isfile(os.path.join(FONTS_DIR, "charset.txt")), "charset.txt missing")

    def test_charset_file_covers_every_on_screen_character(self):
        have = bf.read_charset_file(os.path.join(FONTS_DIR, "charset.txt"))
        screen, _ = bf.collect_screen_chars(ROOT)
        lacking = sorted(screen - have)
        self.assertFalse(lacking, "text changed since the last build, characters not in charset.txt: %s. "
                         "Run scripts/build_fonts.py again." % "".join(lacking[:60]))

    def test_cinzel_is_unmodified(self):
        path = os.path.join(FONTS_DIR, "CinzelDecorative-Bold.ttf")
        self.assertTrue(os.path.isfile(path), "CinzelDecorative-Bold.ttf missing")
        with open(path, "rb") as f:
            data = f.read()
        self.assertNotIn(data[:4], (b"wOFF", b"wOF2"), "Cinzel must stay a .ttf, converting is a modification")
        src = os.path.join(bf.SRC_DIR, "CinzelDecorative-Bold.ttf")
        if os.path.isfile(src):
            with open(src, "rb") as f:
                self.assertEqual(f.read(), data, "Cinzel differs from build/fonts_src: it must be an exact copy")
        elif self.info.get("cinzel_source_sha256"):
            self.assertEqual(bf.sha256_of(path), self.info["cinzel_source_sha256"])
        self.assertLess(len(data), 200 * 1024, "Cinzel Decorative Bold is about 62 KB; this file is too big")


@unittest.skipUnless(BUILT, SKIP_MSG)
@unittest.skipUnless(_fonttools_ok(), "fontTools missing (see TestEnvironment)")
class TestBuiltFontContents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.faces = [(f, existing_src(f)) for f in parse_font_faces(_read(CSS_PATH))]
        cls.info = load_build_info()
        screen, _ = bf.collect_screen_chars(ROOT)
        cls.required = set(screen) | {chr(c) for c in range(0x20, 0x7F)}

    def _exempt(self, key):
        return set(self.info.get("not_in_source", {}).get(key, []))

    def test_body_faces_cover_every_on_screen_character(self):
        seen = 0
        for f, path in self.faces:
            if f["family"] != "PK Body" or not path:
                continue
            seen += 1
            cmap = bf.cmap_of(path)
            lacking = sorted(c for c in self.required if ord(c) not in cmap and c not in self._exempt("sans"))
            self.assertFalse(lacking, "%s lacks on-screen characters: %s" % (os.path.basename(path), "".join(lacking[:60])))
        self.assertEqual(seen, 2, "expected two PK Body files")

    def test_display_faces_cover_every_character_in_their_range(self):
        for f, path in self.faces:
            if f["family"] != "PK Display" or not path:
                continue
            cmap = bf.cmap_of(path)
            key = source_key_for(path)
            if key == "serif":
                lacking = sorted(c for c in self.required
                                 if in_ranges(ord(c), f["ranges"]) and ord(c) not in cmap and c not in self._exempt("serif"))
                self.assertFalse(lacking, "%s lacks characters in its unicode-range: %s" % (
                    os.path.basename(path), "".join(lacking[:60])))
            else:
                # Cinzel: letters and digits are mandatory. Other ASCII punctuation it lacks falls through
                # to the system serif, so it is reported by build_info.json, not failed here.
                must = [c for c in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"]
                lacking = [c for c in must if ord(c) not in cmap]
                self.assertFalse(lacking, "Cinzel lacks %s" % "".join(lacking))

    def test_noto_files_are_static_renamed_and_weighted(self):
        from fontTools.ttLib import TTFont
        want_weight = {"pk-body-400": 400, "pk-body-700": 700, "pk-display-cjk-900": 900}
        for _f, path in self.faces:
            if not path or source_key_for(path) == "cinzel":
                continue
            stem = os.path.splitext(os.path.basename(path))[0]
            font = TTFont(path)
            try:
                self.assertNotIn("fvar", font, stem + " is still a variable font")
                self.assertEqual(font["OS/2"].usWeightClass, want_weight[stem])
                family = font["name"].getDebugName(1)
                self.assertTrue(family.startswith("PK "), "family name was not replaced: %r" % family)
            finally:
                font.close()

    def test_no_reserved_font_name_in_modified_fonts(self):
        want = {"serif": "OFL-NotoSerifTC.txt", "sans": "OFL-NotoSansTC.txt"}
        for _f, path in self.faces:
            key = source_key_for(path) if path else None
            if key not in want:
                continue
            reserved = bf.reserved_font_names(_read(os.path.join(FONTS_DIR, want[key])))
            self.assertEqual(bf.reserved_names_in_family(path, reserved), [],
                             "%s still carries a Reserved Font Name" % os.path.basename(path))

    def test_digit_feature_report(self):
        # Informational: say whether fixed-width digits are available. Never fails.
        feats = self.info.get("features", {})
        if not feats:
            self.skipTest("build_info.json has no feature list")
        lacking = [n for n, tags in feats.items() if "tnum" not in tags]
        if lacking:
            sys.stderr.write("\nNOTE: no 'tnum' feature in: %s. Use equal digit cells (docs/fonts_report.md).\n" % ", ".join(lacking))


if __name__ == "__main__":
    unittest.main(verbosity=2)
