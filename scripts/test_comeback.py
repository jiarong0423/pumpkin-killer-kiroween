import json, os, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import comeback_py as C

with open(os.path.join(os.path.dirname(HERE), "shared", "comeback_vectors.json"), encoding="utf-8") as fh:
    VEC = json.load(fh)


class ComebackTwin(unittest.TestCase):
    def test_near_miss(self):
        for v in VEC["nearMiss"]:
            self.assertEqual(C.near_miss_damage(v["base"], v["e"]), v["expected"], v)

    def test_underdog(self):
        for v in VEC["underdog"]:
            self.assertEqual(C.underdog_multiplier(v["own"], v["enemy"]), v["expected"], v)

    def test_pity(self):
        for v in VEC["pity"]:
            self.assertEqual(C.pity_bonus(v["misses"]), v["expected"], v)

    def test_final_and_share(self):
        for v in VEC["final"]:
            self.assertEqual(C.final_damage(v["base"], v["own"], v["enemy"], v["misses"]), v["expected"], v)
        for v in VEC["share"]:
            self.assertEqual(C.hp_share(v["units"]), v["expected"], v)


if __name__ == "__main__":
    unittest.main()
