#!/usr/bin/env python3
"""The page-judged MCP room for 1v1 and 2v2 (owner 2026-11-22: "MCP, 1v1 to 3v3"). scripts/test_page_judge_relay.py runs the real page as the judge only at 3v3; this file runs the same room tests (the agent and the page stay in step with equal
round hashes, only plain throws and no formula in the public view, the ultimate is rejected before 3 energy) at team size 1 and 2. The 3v3 ultimate test stays 3v3 only (it needs three energy marks inside ten rounds)."""
import subprocess, sys, time, unittest
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import test_page_judge_relay as base
import mcp_stdio_server as srv
from pk_relay import Room

def make(n):
    class Sized(base.PageJudgeRoomTest):
        SIZE = n
        def setUp(self):
            self.host = base.RelayThread(); self.code = "JUDGE%d" % n
            self.host.relay.rooms[self.code] = Room(self.code, scene="graveyard", team_size=n)
            self.port = self.host.relay.bound_port; self.procs = []; self.bridge = None
        def start_pair(self):
            url = "ws://127.0.0.1:%d" % self.port; red = ["bride", "hunchback", "reaper"][:n]; white = ["hag", "skeleton", "wizard"][:n]
            self.procs.append(subprocess.Popen(["node", str(HERE / "hybrid_seat_headless.js"), "--relay", url, "--code", self.code, "--team", "white", "--heroes", ",".join(white),
                                                "--level", "normal", "--rng", "5", "--speed", "8", "--max-s", "120"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=str(base.ROOT)))
            session = srv.Session(seed=1, units=n, seat="red", hero_red=red, hero_white=white, turn_seconds=3600, human_turn_seconds=3600)
            self.bridge = srv.PageJudgeRelay(session, url + "/ws", self.code, "red", speed=8.0, rng=7)
            self.server = srv.McpServer(session); self.server.relay = self.bridge; self.session = session
            self.bridge.start(); base.wait_for(lambda: self.bridge.started, "the bridge's page did not see the room start"); time.sleep(0.5)
        test_3v3_ultimate_over_page_judge_relay = None
        test_hag_ultimate_over_page_judge_relay = None      # 3v3 only (the hag needs a pierce target set); added 2026-11-23, Z4 check
        test_reaper_ultimate_is_refused_in_a_page_judged_room = None   # builds its own 3v3 team; the refusal is size-independent and tested at 3v3
    Sized.__name__ = "PageJudgeRoom%dv%d" % (n, n)
    return Sized
PageJudgeRoom1v1 = make(1); PageJudgeRoom2v2 = make(2)
if __name__ == "__main__":
    suite = unittest.TestSuite()
    for cls in (PageJudgeRoom1v1, PageJudgeRoom2v2): suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    result = unittest.TextTestRunner(verbosity=2).run(suite); sys.exit(0 if result.wasSuccessful() else 1)
