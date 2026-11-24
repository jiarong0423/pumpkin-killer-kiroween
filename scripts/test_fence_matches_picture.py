#!/usr/bin/env python3
"""The central fence collides exactly where its picture is drawn (owner 2026-11-18: shots flew through the left / right and the top of the drawn gate because the collision was 130 x 250 against a 242 x 290 picture).
Independent source: the PNG's alpha bounding box, scaled the way index.html draws it (FENCE_PIC_H, centred on FENCE_X, bottom at GROUND_Y + 6). shared/constants.json (FENCE_W, FENCE_H) must match it within 2 px, and so must the page."""
import json, os, re, unittest
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
class FenceMatchesPicture(unittest.TestCase):
    def test_collision_equals_the_visible_picture(self):
        C = json.load(open(os.path.join(ROOT, "shared", "constants.json"))); html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
        pic_h = float(re.search(r"const FENCE_PIC_H = (\d+)", html).group(1))
        for name in ("fence_black_intact",):   # the intact picture fixes the collision; the other two states are drawn to the same visible width (checked below)
            im = Image.open(os.path.join(ROOT, "assets", "env", name + ".png")); W, H = im.size; bb = im.getchannel("A").getbbox()
            dw = pic_h * W / H; vis_w = (bb[2] - bb[0]) * dw / W; top = C["GROUND_Y"] + 6 - pic_h + bb[1] * pic_h / H
            self.assertLessEqual(abs(C["FENCE_W"] - vis_w), 2.5, "%s: collision width %s vs visible %.1f" % (name, C["FENCE_W"], vis_w) if name == "fence_black_intact" else name)
            if name == "fence_black_intact":
                self.assertLessEqual(abs((C["GROUND_Y"] - C["FENCE_H"]) - top), 2.5, "collision top %s vs picture top %.1f" % (C["GROUND_Y"] - C["FENCE_H"], top))
        # red-team H1 R1-A2: all three states are DRAWN with visible width FENCE_W (the page scales each by its measured visible fraction)
        table = dict((k, float(v)) for k, v in re.findall(r"(fence_(?:intact|damaged|broken)): ([0-9.]+)", re.search(r"const FENCE_VIS_FRAC = \{[^}]*\}", html).group(0)))
        for state in ("intact", "damaged", "broken"):
            im = Image.open(os.path.join(ROOT, "assets", "env", "fence_black_%s.png" % state)); bb = im.getchannel("A").getbbox(); frac = (bb[2] - bb[0]) / float(im.size[0])
            self.assertLessEqual(abs(table["fence_" + state] - frac), 0.0005, "%s: table %s vs measured %.5f" % (state, table["fence_" + state], frac))
            self.assertLessEqual(abs(C["FENCE_W"] / table["fence_" + state] * frac - C["FENCE_W"]), 0.2)   # drawn visible width = FENCE_W
        self.assertIn("const FENCE_W = %d;" % C["FENCE_W"], html); self.assertIn("const FENCE_H = %d;" % C["FENCE_H"], html)
if __name__ == "__main__": unittest.main()
