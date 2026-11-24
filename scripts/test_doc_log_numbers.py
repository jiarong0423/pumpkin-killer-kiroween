#!/usr/bin/env python3
"""The numbers the documents state about the old start-screen failures must be the numbers in the saved evidence files (red-team R3B-3, R4B-4, R5B-2, R7B-1: four rounds of wrong counts).
Every figure is recomputed from redteam/evidence/two_old_failures_20261118.txt and compared in BOTH directions: each recomputed number must appear in the ask file in the exact phrase, and the
ask file must not contain any figure of the old wrong lists. The ask file is pasted to an outside reader: it must not carry repository paths, evidence file names or the withdrawn carousel item."""
import os, re, sys, unittest
ROOT = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(ROOT)
EV = os.path.join(ROOT, "redteam", "evidence")
ASK = os.path.join(ROOT, "docs", "EXTERNAL_ASK_START_AND_SETTINGS_20261118.md")
REC = os.path.join(ROOT, "docs", "LAYOUT_REBUILD_RECORD_20261117.md")

def read(path):
    with open(path, encoding="utf-8") as f: return f.read()

def facts():
    """Recomputed from the saved run of the current build after the G2 change (the section of test_start_screen_fit.js)."""
    lines = read(os.path.join(EV, "start_screen_after_g2_20261118.txt")).split("\n")
    start = lines.index("=== test_start_screen_fit.js")
    section = []
    for line in lines[start + 1:]:
        if line.startswith("exit=") or line.startswith("=== "): break
        if line.startswith("  "): section.append(line.strip())
    under = [l for l in section if "undersized" in l]
    inter = [l for l in section if "start intersections" in l]
    size = lambda l: re.search(r"(\d+)x(\d+):", l).group(0)[:-1]
    sizes = sorted({size(l) for l in section}, key=lambda z: (int(z.split("x")[0]), int(z.split("x")[1])))
    return {"lines": len(section), "undersized": len(under), "intersections": len(inter), "sizes": len(sizes),
            "under_sizes": sorted({size(l) for l in under}), "inter_sizes": sorted({size(l) for l in inter}),
            "thumb_sizes": sorted({size(l) for l in under if "hero-thumb" in l}), "chips_sizes": sorted({size(l) for l in under if "slot-chip" in l}),
            "first": sizes[0].replace("x", " x "), "buttons_only": sorted({size(l) for l in under if "hero-thumb" not in l}),
            "viewports": len(re.findall(r"^\d+x\d+ +", "\n".join(lines[start:start + 20]), re.M))}

@unittest.skipUnless(
    os.path.exists(os.path.join(EV, "start_screen_after_g2_20261118.txt"))
    and os.path.exists(os.path.join(EV, "two_old_failures_20261118.txt")),
    "internal working-repo evidence logs absent in clean release export",
)
class DocNumbers(unittest.TestCase):
    def test_facts_and_ask_file_agree_both_ways(self):
        f = facts(); ask = read(ASK)
        self.assertEqual((f["lines"], f["undersized"], f["intersections"], f["sizes"], f["viewports"]), (14, 14, 0, 7, 15), f)
        self.assertEqual(f["under_sizes"], sorted(["640x360", "720x405", "667x375", "667x300", "873x330", "915x350", "844x330"]))
        self.assertIn("at 15 viewport sizes (widths 640 to 960, heights 300 to 540)", ask)
        self.assertIn("printed %d failing lines at %d of the %d sizes" % (f["lines"], f["sizes"], f["viewports"]), ask)
        self.assertIn("the other %d sizes pass" % (f["viewports"] - f["sizes"]), ask)
        self.assertIn('Every failing line is "undersized start controls"', ask)
        self.assertIn("The %d sizes:" % f["sizes"], ask)
        for size in f["under_sizes"]:
            self.assertIn(size.replace("x", " x "), ask)
        # which controls fail at which size: recomputed from the lines, compared with the two list items of the ask file
        with_thumbs = sorted({z for z in f["under_sizes"] if z in f["thumb_sizes"]})
        self.assertEqual(with_thumbs, sorted(["640x360", "720x405", "667x375", "667x300"]))
        self.assertEqual(sorted(set(f["under_sizes"]) - set(with_thumbs)), sorted(["873x330", "915x350", "844x330"]))
        self.assertEqual(f["chips_sizes"], f["under_sizes"], "in the 3 versus 3 mode the slot chips are undersized at every one of the 7 sizes")
        self.assertIn("no control overlaps another any more at the 15 sizes", ask)
        for wrong in ("24 failing lines", "25 failing lines", "21 failing lines", "13 viewport sizes", "12 viewport sizes", "22 start-screen", "EVERY viewport", "316 px", "16 of 200", "650 x 275", "start intersections", "behind the", "Where should the three slot chips"):
            self.assertNotIn(wrong, ask)
        for outsider_unfriendly in ("redteam/", "scripts/", "exit=0", "logs_local", "red-team", "hero-next", "hero \"next\"", "does not return to the selected hero"):
            self.assertNotIn(outsider_unfriendly, ask)
        self.assertNotIn("after 8 presses", ask)   # the withdrawn carousel question
        self.assertIn("ask_5_start_screen_3v3_667x375_current.jpg", ask)
        self.assertTrue(os.path.exists(os.path.join(ROOT, "docs", "media", "ask_5_start_screen_3v3_667x375_current.jpg")))
        self.assertIn("answer 1 to 5", ask)
        self.assertEqual(len(re.findall(r"^[1-5]\. For a start screen|^[1-5]\. The scale|^[1-5]\. For the settings|^[1-5]\. What minimum|^[1-5]\. What is the smallest", ask, re.M)), 5)
        table = read(os.path.join(ROOT, "docs", "PHONE_SCALE_TABLE_20261117.md"))   # the source of the real phone's two viewports
        self.assertRegex(table, r"756\s*[x×]\s*266")
        self.assertIn("The 15 sizes tested have widths from 640 to 960 css px and heights from 300 to 540 css px.", ask)
        script = read(os.path.join(ROOT, "scripts", "measure_phone_layout.mjs"))   # the tested sizes come from the script, not from memory
        listed = re.search(r"const fixedViewports = \[(.*?)\];", script, re.S)
        self.assertIsNotNone(listed)
        pairs = re.findall(r"width: (\d+), height: (\d+)", listed.group(1))
        self.assertEqual(len(pairs), 15)
        self.assertEqual((min(int(w) for w, h in pairs), min(int(h) for w, h in pairs), max(int(w) for w, h in pairs), max(int(h) for w, h in pairs)), (640, 300, 960, 540))
        page = read(os.path.join(ROOT, "index.html"))   # the design constants the ask file states
        self.assertIn("Math.min(width / 800, height / 360)", page)
        self.assertIn("min(width / 800, height / 360)", ask)
        self.assertIn("left:20px; top:8px; transform:none; z-index:58;", page)   # the Friends button in the top-left corner, as the ask file says
        for (w, h), shown in (((667, 300), "36.7 px at 667 x 300"), ((873, 330), "40 px at 873 x 330")):
            fit = min(w / 800.0, h / 360.0)
            self.assertIn(shown, ask)
            self.assertEqual(shown.split(" ")[0], ("%.1f" % (44 * fit)) if shown.startswith("36") else "%d" % round(44 * fit))
        self.assertIn("756 x 266 css px with the browser bars showing", ask)
        self.assertIn("756 x 360 css px at devicePixelRatio 3 in fullscreen", ask)
        shot_fit = min(667 / 800.0, 375 / 360.0)   # the screenshot section: the scale of the 667 x 375 view
        self.assertIn("min(667 / 800, 375 / 360) = %.2f here, so a 44 px control is %.1f px" % (shot_fit, 44 * shot_fit), ask)
        self.assertIn("enlarged to 800 x 450", ask)
        self.assertNotIn("scaled to 0.93", ask)
        owner = read(os.path.join(ROOT, "docs", "owner_feedback_log.md"))   # every owner quote the gap queue uses must exist in the decision log
        queue = read(os.path.join(ROOT, "docs", "GAP_QUEUE_OPEN_20261118.md"))
        self.assertIn('section "2026-11-18 decisions"', queue)
        for words in ("我是覺得物件可以大", "之後再補", "一場七八分鐘而已", "下一場再重連就好"):
            self.assertIn(words, owner)

    def test_ask_file_is_frozen_text(self):
        """The ask file is sent outside. After the semantic checks above pass for a deliberate edit, refresh the hash with:
        python3 -B scripts/test_doc_log_numbers.py --refresh-hash   (any number nobody pinned above is covered by this hash, so no figure can change silently)."""
        import hashlib
        digest = hashlib.sha256(read(ASK).encode("utf-8")).hexdigest()
        self.assertEqual(digest, read(ASK + ".sha256").split()[0], "the ask file changed: review it, then run with --refresh-hash")

    def test_record_counts(self):
        rec = read(REC)
        self.assertIn("25 failing lines at 13 viewport sizes", rec)
        self.assertNotIn("EVERY viewport", rec)
        if "22 start-screen failures" in rec:   # the record may quote the count only together with the two saved logs that print it
            for name in ("start_fit_before_20261118.txt", "start_fit_after_r1fix.txt"):
                self.assertIn(name, rec)
                self.assertIn("22 start-screen failures", read(os.path.join(EV, name)), name)

if __name__ == "__main__":
    if "--refresh-hash" in sys.argv:
        import hashlib
        with open(ASK + ".sha256", "w", encoding="utf-8") as f: f.write(hashlib.sha256(read(ASK).encode("utf-8")).hexdigest() + "  " + os.path.basename(ASK) + "\n")
        print("hash refreshed")
    else:
        unittest.main()
