import json, os, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import team_tuning_py as T

with open(os.path.join(os.path.dirname(HERE), "shared", "team_tuning_vectors.json"), encoding="utf-8") as fh:
    VEC = json.load(fh)


class TeamTuningTwin(unittest.TestCase):
    def test_team_max_hp_vectors(self):
        for v in VEC["teamMaxHp"]:
            self.assertEqual(T.team_max_hp(v["hp"], v["dmg"], v["n"]), v["expected"], v)

    def test_ramp_vectors(self):
        for v in VEC["ramp"]:
            self.assertEqual(T.ramp_multiplier(v["round"], v["n"]), v["expected"], v)

    def test_round_cap_vectors(self):
        for v in VEC["cap"]:
            want = float("inf") if v["expected"] is None else v["expected"]
            self.assertEqual(T.round_cap(v["n"]), want)

    def test_cap_winner_vectors(self):
        for v in VEC["capWinner"]:
            self.assertEqual(T.cap_winner(v["teams"]), v["expected"])


if __name__ == "__main__":
    unittest.main()
