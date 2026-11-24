#!/usr/bin/env python3
"""The damage number a hero card shows the player must be the hero's real damage (red-team R11A-P1-1: after the role change the cards still said 22 / 30 / 36 / 21 / 21 while shared/heroes.json said 24 / 36 / 40 / 19 / 22).
Reads assets/i18n/en.json and zh-TW.json and shared/heroes.json; no number is copied here. The page's own table (index.html HERO_PROFILES) must agree with heroes.json too."""
import json, os, re, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as f: return json.load(f)

HEROES = load("shared/heroes.json")
EN = load("assets/i18n/en.json")
ZH = load("assets/i18n/zh-TW.json")

class BlurbNumbers(unittest.TestCase):
    def test_every_card_states_the_real_damage_in_both_languages(self):
        for hero, row in HEROES.items():
            en = EN["hero.%s.blurb" % hero]; zh = ZH["hero.%s.blurb" % hero]
            with self.subTest(hero=hero):
                self.assertEqual([int(x) for x in re.findall(r"(\d+)(?: total)? damage", en)][:1], [row["dmg"]], en)
                self.assertEqual([int(x) for x in re.findall(r"傷害 (\d+)", zh)][:1], [row["dmg"]], zh)

    def test_the_bride_card_describes_the_wave_as_it_works_now(self):
        en = EN["hero.bride.blurb"]; zh = ZH["hero.bride.blurb"]
        self.assertIn("35 px", en); self.assertIn("both sides of the centre", en); self.assertNotIn("friend or foe", en); self.assertNotIn("only the unit it is aimed at", en); self.assertNotIn("Lowest HP", en)
        self.assertIn("35 px", zh); self.assertIn("左右兩邊", zh); self.assertNotIn("不分哪一邊", zh); self.assertNotIn("只打瞄準", zh); self.assertNotIn("血量最少", zh)

    def test_nobody_claims_to_have_the_lowest_hp_except_the_hero_who_has_it(self):
        lowest = min(HEROES, key=lambda h: HEROES[h]["hp"])
        for hero in HEROES:
            if hero == lowest: continue
            self.assertNotIn("Lowest HP", EN["hero.%s.blurb" % hero], hero)
            self.assertNotIn("血量最少", ZH["hero.%s.blurb" % hero], hero)

    def test_the_page_table_matches_heroes_json(self):
        with open(os.path.join(ROOT, "index.html"), encoding="utf-8") as f: page = f.read()
        start = page.index("const HERO_PROFILES")
        for hero, row in HEROES.items():
            m = re.search(r"\b%s: \{.*?\bhp: (\d+),.*?\bdmg: (\d+)," % hero, page[start:start + 20000], re.S)
            self.assertIsNotNone(m, hero)
            self.assertEqual((int(m.group(1)), int(m.group(2))), (row["hp"], row["dmg"]), hero)

if __name__ == "__main__":
    unittest.main()
