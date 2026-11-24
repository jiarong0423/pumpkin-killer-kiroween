#!/usr/bin/env python3
"""Multi-agent MCP acceptance matrix (zero gate Z5): team sizes 1v1, 2v2, 3v3 against these cells, each run one short room played through the real MCP tool path
(`McpServer._call_tool`) over a local relay, with the real page (node vm) as the judge of every agent seat (`PageJudgeRelay`).

Cells
  A  one agent seat against a headless page seat (the computer); the agent also fires illegal actions every turn (wrong round, wrong unit, power above 115, angle below 25,
     an unknown field, a repeated end_turn, an action after end_turn): each must be refused and leave the public state unchanged (cell C of the owner's list);
     a spectator is attached the whole time, must see the room's traffic and must be refused when it tries to act (cell E); every round hash of both seats must be equal (cell F)
  B  two agents, one per side, each in its own thread (cell b: two agents at once), same illegal probes against each other's units and phases
  D  disconnect: the white page's socket is cut once in the middle of the run (it must reconnect inside the grace period and the match go on with equal hashes);
     every second run the RED agent's own page socket is cut instead (the agent's seat reconnects)
  L  long wait: the agent's turn timer is short (--late-turn-seconds, default 3) and the agent lets it run out while polling get_public_state once a second
     (--late-seconds, default 5) before it acts. Either answer is acceptable (the turn moved on, or the late action was accepted or cleanly refused), but never a hang,
     an out_of_sync state, a crash or different round hashes. The notes say which one happened.
  H  hero coverage (Z1 / Z5 / Z8 widened to the 8 heroes): for each hero and each team size, runs until at least --min-ult ultimate attempts (fired, or refused for the knight
     and the necromancer, whose room ultimates are refused on purpose) and --min-plain plain throws of that hero. The focal hero is the first unit of the red team, the agent aims
     with the engine's own flight, and every focal throw is logged (round, unit, kind, the page's result, statuses, whether both seats' round hash agreed). A refused ultimate must
     leave the state unchanged. The result is an 8 x scenario matrix: heroes x {plain, ultimate} x {1v1, 2v2, 3v3} with runs, throws and desync counts. Any desync stops the run.
  G  grace expiry: the white page process is killed and never returns; with a short grace period the relay must announce `seat_left`, and the agent must not hang
     (the state shows a result or a sync problem within --after-seconds). The expected reaction was not specified before this matrix; the first runs MEASURE it.

A run PASSES when: no relay error, no hang (a phase wait longer than --hang-seconds is a failure), every illegal probe refused with the state unchanged, no `out_of_sync` in the
agent's state, all round hashes equal, at least one hash round compared. Any failure stops the matrix (`--keep-going` to continue), is written to the run log with the details,
and exit code is 1.

Needs localhost sockets and Node 22+: run in the owner's terminal, not the Claude sandbox. One run at a time, one process tree, no extra workers.
    python3 -B scripts/mcp_acceptance_matrix.py --cells A --sizes 1,2,3 --runs 2 --turns 4 --label trial        # small trial first
    python3 -B scripts/mcp_acceptance_matrix.py --cells A,B,D --sizes 1,2,3 --runs 100 --label z5                # the full matrix (long; resource table first)
Output: logs_local/mcp_matrix/<label>/runs.jsonl (one line per run, appended, resumable with --resume), summary in redteam/evidence/mcp_matrix_<label>_summary.json,
last line RESOURCE_RELEASED. Exit: 0 all passed, 1 a run failed, 2 setup problem.
"""
import argparse
import asyncio
import json
import os
import random
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import mcp_stdio_server as srv  # noqa: E402
from pk_relay import RelayServer, Room  # noqa: E402

HEROES = ["bat", "bride", "hag", "hunchback", "reaper", "skeleton", "wizard", "knight"]
LOG_BASE = ROOT / "logs_local" / "mcp_matrix"
EVIDENCE = ROOT / "redteam" / "evidence"
NODE = shutil.which("node")


class Failure(Exception):
    pass


class RelayHost:
    """A relay on its own thread and event loop (like the room tests), with settable limits."""

    def __init__(self, **limits):
        self.loop = asyncio.new_event_loop()
        self.ready = threading.Event()
        self.errors = []
        self.limits = limits
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        if not self.ready.wait(5):
            raise RuntimeError("relay did not start")

    def _run(self):
        asyncio.set_event_loop(self.loop)
        outer = self

        class Counting(RelayServer):
            async def _error(self, websocket, code, message=None):
                outer.errors.append(code)
                await super()._error(websocket, code, message)
        self.relay = Counting("127.0.0.1", 0, **self.limits)
        self.loop.run_until_complete(self.relay.start())
        self.ready.set()
        self.loop.run_forever()
        self.loop.run_until_complete(self.relay.close())
        self.loop.close()

    def call(self, coroutine, timeout=10):
        return asyncio.run_coroutine_threadsafe(coroutine, self.loop).result(timeout)

    def close(self):
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join(5)


def wait_for(predicate, message, seconds):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.05)
    raise Failure(message)


def fingerprint(state):
    """What an illegal action must not change: every unit, the round, the phase, the energy."""
    units = {uid: [u.get("x"), u.get("y"), u.get("hp"), u.get("alive"), sorted(u.get("statuses") or [])] for uid, u in sorted(state["units"].items())}
    return json.dumps({"units": units, "round": state["round"], "phase": state["phase"], "energy": state.get("ultimate_energy"), "winner": state.get("winner")}, sort_keys=True)


class Agent:
    """One MCP agent seat: a Session + McpServer + PageJudgeRelay, plus the script that plays it."""

    def call(self, tool, arguments=None):
        result = self.server._call_tool(tool, arguments or {})
        return result["isError"], json.loads(result["content"][0]["text"])

    def state(self):
        error, payload = self.call("get_public_state")
        if error:
            raise Failure("%s get_public_state failed: %s" % (self.name, payload))
        return payload

    def refused(self, label, arguments, tool="submit_action"):
        """An illegal call: must be refused and leave the public state unchanged."""
        before = fingerprint(self.state())
        error, payload = self.call(tool, arguments)
        after = fingerprint(self.state())
        self.stats["probes"] += 1
        if not error:
            raise Failure("%s: illegal %s was ACCEPTED: %s -> %s" % (self.name, label, arguments, json.dumps(payload)[:200]))
        if before != after and "turn" not in label:
            raise Failure("%s: illegal %s changed the state" % (self.name, label))
        self.stats["refused"] += 1

    def probes(self, st, unit, others, enemy):
        rnd = st["round"]
        self.refused("wrong round", {"unit": unit, "round": rnd + 1, "action": {"type": "throw", "angle": 50, "power": 60}})
        if others:
            self.refused("wrong unit (frozen teammate)", {"unit": others[0], "round": rnd, "action": {"type": "throw", "angle": 50, "power": 60}})
        if enemy:
            self.refused("enemy unit", {"unit": enemy, "round": rnd, "action": {"type": "throw", "angle": 50, "power": 60}})
        self.refused("power above 115", {"unit": unit, "round": rnd, "action": {"type": "throw", "angle": 50, "power": 116}})
        self.refused("angle below 25", {"unit": unit, "round": rnd, "action": {"type": "throw", "angle": 24, "power": 60}})
        self.refused("unknown field", {"unit": unit, "round": rnd, "action": {"type": "throw", "angle": 50, "power": 60, "cheat": 1}})
        self.refused("end_turn of the wrong phase", {"round": rnd, "phase": "agent" if self.my_phase == "human" else "human"}, tool="end_turn")

    def play(self, turns, hang_seconds, stop):
        done = 0
        last_key = None
        deadline = time.monotonic() + hang_seconds
        while done < turns and not stop.is_set():
            st = self.state()
            if st["winner"] or st["phase"] == "over":
                return "over"
            if st.get("sync", {}).get("status") == "out_of_sync":
                raise Failure("%s: the state says out_of_sync" % self.name)
            if st["phase"] == self.my_phase and (st["round"], st["phase"]) != last_key:
                deadline = time.monotonic() + hang_seconds
                if self.late_seconds:
                    until = time.monotonic() + self.late_seconds
                    while time.monotonic() < until:   # the long wait: poll once a second, do not act
                        self.state()
                        time.sleep(1.0)
                    st2 = self.state()
                    if st2["winner"] or st2["phase"] == "over":
                        return "over"
                    if (st2["round"], st2["phase"]) != (st["round"], st["phase"]):
                        self.notes.append("turn timer moved the match on while the agent waited (round %s phase %s -> round %s phase %s)" % (st["round"], st["phase"], st2["round"], st2["phase"]))
                        last_key = (st["round"], st["phase"])
                        done += 1
                        self.stats["turns"] += 1
                        self.turns_own += 1
                        continue
                    st = st2
                    self.notes.append("the turn was still open after the long wait")
                mine = [uid for uid, u in sorted(st["units"].items()) if u["team"] == self.session.team_name and u["alive"]]
                enemy = next((uid for uid, u in sorted(st["units"].items()) if u["team"] != self.session.team_name and u["alive"]), None)
                unit = mine[0]
                # find the active unit without acting: an invalid power is refused AFTER the active-unit check, so a refusal that names the active unit tells which one it is
                error, payload = self.call("submit_action", {"unit": unit, "round": st["round"], "action": {"type": "throw", "angle": 50, "power": 116}})
                if not error:
                    raise Failure("%s: power 116 was accepted" % self.name)
                if "active unit is" in payload.get("error", ""):
                    unit = payload["error"].rsplit("active unit is ", 1)[1].strip()
                self.probes(st, unit, [m for m in mine if m != unit], enemy)
                angle, power = self.rng.randint(30, 75), self.rng.randint(40, 110)
                error, payload = self.call("submit_action", {"unit": unit, "round": st["round"], "action": {"type": "throw", "angle": angle, "power": power}})
                if error:
                    raise Failure("%s: a legal throw was refused: %s" % (self.name, payload))
                error, payload = self.call("end_turn", {"round": st["round"], "phase": st["phase"]})
                if error:
                    raise Failure("%s: end_turn refused: %s" % (self.name, payload))
                again, _ = self.call("end_turn", {"round": st["round"], "phase": st["phase"]})
                self.stats["probes"] += 1
                if not again:
                    raise Failure("%s: a repeated end_turn was accepted" % self.name)
                self.stats["refused"] += 1
                after_end, _ = self.call("submit_action", {"unit": unit, "round": st["round"], "action": {"type": "throw", "angle": 50, "power": 60}})
                self.stats["probes"] += 1
                if not after_end:
                    raise Failure("%s: an action after end_turn was accepted" % self.name)
                self.stats["refused"] += 1
                last_key = (st["round"], st["phase"])
                done += 1
                self.stats["turns"] += 1
                self.turns_own += 1
            else:
                if time.monotonic() > deadline:
                    raise Failure("%s: HANG, no turn for %ds (phase %s, round %s, sync %s)" % (self.name, hang_seconds, st["phase"], st["round"], st.get("sync")))
                time.sleep(0.1)
        return "turns"

    def play_focal(self, focal, max_turns, hang_seconds, stop, sim, log):
        """Cell H: the focal hero throws plain until the team has three energy marks and the focal hero is active; then it attempts its ultimate once."""
        turns, last_key, ult_done, after_ult = 0, None, False, 0
        deadline = time.monotonic() + hang_seconds
        while turns < max_turns and not stop.is_set() and after_ult < 2:
            st = self.state()
            if st["winner"] or st["phase"] == "over":
                return "over"
            if st.get("sync", {}).get("status") == "out_of_sync":
                raise Failure("%s: the state says out_of_sync" % self.name)
            if st["phase"] == self.my_phase and (st["round"], st["phase"]) != last_key:
                deadline = time.monotonic() + hang_seconds
                mine = [uid for uid, u in sorted(st["units"].items()) if u["team"] == self.session.team_name and u["alive"]]
                unit = mine[0]
                error, payload = self.call("submit_action", {"unit": unit, "round": st["round"], "action": {"type": "throw", "angle": 50, "power": 116}})
                if "active unit is" in payload.get("error", ""):
                    unit = payload["error"].rsplit("active unit is ", 1)[1].strip()
                hero = st["units"][unit]["class"]
                energy = (st.get("ultimate_energy") or {}).get(self.session.team_name, 0)
                eng_unit = self.session.engine.units[unit]
                angle, power, _t = sim.aim(self.rng, self.session.engine, eng_unit, None)
                angle, power = max(25, min(80, int(round(angle)))), max(20, min(115, int(round(power))))
                kind = "plain"
                if hero == focal and not ult_done and energy >= 3:
                    kind = "ultimate"
                    ult_done = True
                    before = fingerprint(st)
                    error, payload = self.call("submit_action", {"unit": unit, "round": st["round"], "action": {"type": "ultimate", "angle": angle, "power": power}})
                    if error:
                        # a refusal is the expected answer for the knight and the necromancer, a failure for the other heroes
                        if focal in ("knight", "reaper"):
                            if fingerprint(self.state()) != before:
                                raise Failure("%s: the refused %s ultimate changed the state" % (self.name, focal))
                            log.append({"round": st["round"], "unit": unit, "hero": hero, "kind": "ultimate_refused", "error": payload.get("error", "")[:120]})
                            self.stats["ult_refused"] = self.stats.get("ult_refused", 0) + 1
                            kind = "plain"
                        else:
                            raise Failure("%s: the %s ultimate was refused although it is allowed in a room: %s" % (self.name, focal, payload))
                    else:
                        if focal in ("knight", "reaper"):
                            raise Failure("%s: the %s ultimate was ACCEPTED in a room (it must be refused)" % (self.name, focal))
                        self.stats["ult_fired"] = self.stats.get("ult_fired", 0) + 1
                if kind == "plain":
                    error, payload = self.call("submit_action", {"unit": unit, "round": st["round"], "action": {"type": "throw", "angle": angle, "power": power}})
                    if error:
                        raise Failure("%s: a legal plain throw was refused: %s" % (self.name, payload))
                    if hero == focal:
                        self.stats["plain_focal"] = self.stats.get("plain_focal", 0) + 1
                log.append({"round": st["round"], "unit": unit, "hero": hero, "kind": kind, "angle": angle, "power": power})
                error, payload = self.call("end_turn", {"round": st["round"], "phase": st["phase"]})
                if error:
                    raise Failure("%s: end_turn refused: %s" % (self.name, payload))
                last_key = (st["round"], st["phase"])
                turns += 1
                self.stats["turns"] += 1
                self.turns_own += 1
                if ult_done:
                    after_ult += 1
            else:
                if time.monotonic() > deadline:
                    raise Failure("%s: HANG, no turn for %ds (phase %s, round %s, sync %s)" % (self.name, hang_seconds, st["phase"], st["round"], st.get("sync")))
                time.sleep(0.1)
        return "done"


def make_agent(name, team, size, url, code, red, white, speed, rng_seed, stats, play_rng, turn_seconds=3600):
    session = srv.Session(seed=1, units=size, seat=team, hero_red=red, hero_white=white, turn_seconds=turn_seconds, human_turn_seconds=turn_seconds)
    server = srv.McpServer(session)
    bridge = srv.PageJudgeRelay(session, url + "/ws", code, team, speed=speed, rng=rng_seed)
    server.relay = bridge
    session.team_name = team
    agent = Agent.__new__(Agent)
    agent.name, agent.session, agent.server, agent.bridge, agent.rng, agent.stats = name, session, server, bridge, play_rng, stats
    agent.my_phase = "human" if team == "red" else "agent"
    agent.turns_own = 0
    agent.late_seconds = 0
    agent.notes = []
    return agent


class Spectator:
    """A spectator socket on the relay's loop: collects message types, then tries to act."""

    def __init__(self, host, url, code):
        import websockets
        self.host, self.messages, self.refusal = host, [], None

        async def connect():
            self.ws = await websockets.connect(url + "/ws", max_size=16 * 1024)
            await self.ws.send(json.dumps({"type": "join", "code": code, "seat": "spectator", "client_version": "matrix"}))
            self.task = asyncio.ensure_future(self.pump())
        host.call(connect())

    async def pump(self):
        try:
            async for raw in self.ws:
                try:
                    self.messages.append(json.loads(raw))
                except ValueError:
                    pass
        except Exception:
            pass

    def try_to_act(self):
        async def act():
            await self.ws.send(json.dumps({"type": "action", "round": 1, "phase": "red", "unit": "left_0", "kind": "throw", "angle": 50, "power": 60}))
            await asyncio.sleep(1.0)
        before = len(self.messages)
        self.host.call(act())
        new = self.messages[before:]
        self.refusal = next((m for m in new if m.get("type") == "error"), None)

    def close(self):
        try:
            self.host.call(self.ws.close(), 3)
        except Exception:
            pass


def start_white_page(url, code, white, size, rng_seed, speed):
    return subprocess.Popen(["node", str(HERE / "hybrid_seat_headless.js"), "--relay", url, "--code", code, "--team", "white", "--heroes", ",".join(white), "--level", "normal",
                             "--rng", str(rng_seed), "--speed", str(speed), "--max-s", "300"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=str(ROOT))


def cut_socket(host, code, seat_prefix):
    """Close the relay's side of one seat's socket (a network drop); the page's relay client must reconnect and resume."""
    room = host.relay.rooms[code]
    for websocket, entry in list(room.clients.items()):
        if str(entry.get("seat_id", "")).startswith(seat_prefix):
            host.call(websocket.close(code=1012, reason="matrix cut"), 5)
            return True
    return False


def verify_room(host, code, agents, spectator, min_rounds):
    problems = []
    errors = list(host.errors)
    if spectator is not None and spectator.refusal is not None:
        code_refused = spectator.refusal.get("code") or spectator.refusal.get("error")
        if code_refused in errors:
            errors.remove(code_refused)   # the spectator's own refused attempt is the one expected relay error
    if errors:
        problems.append("relay errors: %s" % errors[:5])
    room = host.relay.rooms.get(code)
    hashes = room.round_hashes if room else {}
    compared = 0
    for number, by_seat in sorted(hashes.items()):
        if len(by_seat) >= 2:
            compared += 1
        if len(set(by_seat.values())) > 1:
            problems.append("round %s hash differs: %s" % (number, by_seat))
    if compared < min_rounds:
        problems.append("only %d hash rounds were compared (need %d)" % (compared, min_rounds))
    for agent in agents:
        st = agent.state()
        if st.get("sync", {}).get("status") == "out_of_sync":
            problems.append("%s ends with sync out_of_sync" % agent.name)
    if spectator is not None:
        kinds = {m.get("type") for m in spectator.messages}
        if not ({"action", "end_turn", "round_hash"} & kinds):
            problems.append("the spectator saw no game traffic: %s" % sorted(kinds))
        if spectator.refusal is None:
            problems.append("the spectator's attempt to act was not answered with an error")
        else:
            problems_note = spectator.refusal.get("code") or spectator.refusal.get("error")
            if not problems_note:
                problems.append("the spectator's refusal has no error code: %s" % spectator.refusal)
    return problems, compared


def scenario_of(cell, stats, agents, spectator, compared, notes, args):
    """What the cell is supposed to exercise, expected versus actual; a run whose scenario did not happen is a gap, not a pass (main window rule 2026-11-23)."""
    spectator_msgs = len([m for m in (spectator.messages if spectator else []) if m.get("type") in ("action", "end_turn", "round_hash", "judge")])
    seat_left = bool(spectator and any(m.get("type") == "seat_left" for m in spectator.messages))
    actual = {"turns": stats.get("turns", 0), "probes": stats.get("probes", 0), "refused": stats.get("refused", 0), "hash_rounds": compared, "spectator_game_messages": spectator_msgs,
              "turns_per_agent": [a.turns_own for a in agents]}
    expected = {"turns_at_most": args.turns, "min_hash_rounds": 1}
    if cell == "A":
        occurred = actual["turns"] >= 1 and actual["probes"] >= 7 and actual["refused"] == actual["probes"] and spectator_msgs > 0 and compared >= 1
        expected.update({"min_turns": 1, "min_probes": 7, "spectator_game_messages": ">0"})
    elif cell == "B":
        occurred = len(actual["turns_per_agent"]) == 2 and min(actual["turns_per_agent"]) >= 1 and compared >= 1 and actual["refused"] == actual["probes"]
        expected.update({"each_agent_min_turns": 1})
    elif cell == "D":
        occurred = bool(stats.get("cut_ok")) and stats.get("turns", 0) > stats.get("turns_at_cut", 10 ** 9) and compared >= 1 and not seat_left
        actual.update({"cut_ok": bool(stats.get("cut_ok")), "turns_at_cut": stats.get("turns_at_cut"), "seat_left_seen": seat_left})
        expected.update({"cut_ok": True, "turns_after_cut": ">=1", "seat_left_seen": False})
    elif cell == "G":
        occurred = seat_left and any("agent state" in n and "NO REACTION" not in n for n in notes)
        actual.update({"seat_left_seen": seat_left})
        expected.update({"seat_left_seen": True, "agent_reaction": "result or sync problem"})
    elif cell == "L":
        waited = sum(1 for a in agents for n in getattr(a, "notes", []) if "after the long wait" in n or "turn timer moved" in n)
        occurred = actual["turns"] >= 1 and waited >= 1 and actual["refused"] == actual["probes"]
        actual.update({"long_waits": waited})
        expected.update({"long_waits": ">=1"})
    else:
        occurred = True
    return {"expected": expected, "actual": actual, "occurred": bool(occurred)}


def run_cell(cell, size, index, args):
    rng = random.Random(args.seed_base + size * 1000 + index * 7 + ord(cell))
    red = [rng.choice(HEROES) for _ in range(size)]
    white = [rng.choice(HEROES) for _ in range(size)]
    code = "MX%s%d%03d" % (cell, size, index % 1000)
    limits = {"seat_grace_seconds": args.grace} if cell in ("D", "G") else {}
    host = None
    procs, agents, spectator, stop = [], [], None, threading.Event()
    stats = {"probes": 0, "refused": 0, "turns": 0}
    started = time.time()
    notes = []
    try:
        host = RelayHost(**limits)
        host.relay.rooms[code] = Room(code, scene="graveyard", team_size=size)
        url = "ws://127.0.0.1:%d" % host.relay.bound_port
        speed = args.speed
        red_agent = make_agent("agent-red", "red", size, url, code, red, white, speed, rng.randint(1, 9999), stats, random.Random(rng.random()),
                               turn_seconds=args.late_turn_seconds if cell == "L" else 3600)
        if cell == "L":
            red_agent.late_seconds = args.late_seconds
        agents.append(red_agent)
        if cell == "B":
            white_agent = make_agent("agent-white", "white", size, url, code, red, white, speed, rng.randint(1, 9999), stats, random.Random(rng.random()))
            agents.append(white_agent)
        else:
            procs.append(start_white_page(url, code, white, size, rng.randint(1, 9999), speed))
        for agent in agents:
            agent.bridge.start()
        for agent in agents:
            wait_for(lambda a=agent: a.bridge.started, "%s: its page did not see the room start" % agent.name, 30)
        time.sleep(0.5)
        spectator = Spectator(host, url, code) if cell in ("A", "B", "D", "G", "L") else None
        results, errors = {}, []

        def drive(agent):
            try:
                results[agent.name] = agent.play(args.turns, args.hang_seconds, stop)
            except Exception as exc:  # reported after the join
                errors.append("%s: %s" % (agent.name, exc))
                stop.set()
        threads = [threading.Thread(target=drive, args=(agent,), daemon=True) for agent in agents]
        for thread in threads:
            thread.start()
        if cell == "D":
            wait_for(lambda: stats["turns"] >= 2 or errors, "no turn was played before the cut", args.hang_seconds)
            cut_which = "red" if index % 2 else "white"
            cut_ok = cut_socket(host, code, cut_which + "-")
            notes.append("cut %s socket: %s" % (cut_which, cut_ok))
            stats["turns_at_cut"] = stats["turns"]
            stats["cut_ok"] = bool(cut_ok)
            if not cut_ok:
                errors.append("could not find the %s seat's socket to cut" % cut_which)
        if cell == "G":
            wait_for(lambda: stats["turns"] >= 2 or errors, "no turn was played before the kill", args.hang_seconds)
            procs[0].kill()
            notes.append("killed the white page process")
            wait_for(lambda: any(m.get("type") == "seat_left" for m in spectator.messages), "the relay never announced seat_left after the grace period", args.grace + 15)
            t_left = time.time()
            notes.append("seat_left seen")
            deadline = time.time() + args.after_seconds
            outcome = None
            while time.time() < deadline and not errors:
                st = red_agent.state()
                if st["winner"] or st["phase"] == "over":
                    outcome = "result: winner %s" % st["winner"]
                    break
                if st.get("sync", {}).get("status") in ("out_of_sync", "peer_left", "left"):
                    outcome = "sync: %s" % st["sync"]["status"]
                    break
                time.sleep(0.5)
            notes.append("agent state %.1fs after seat_left: %s" % (time.time() - t_left, outcome or "NO REACTION (still waiting)"))
            stop.set()
            if outcome is None:
                errors.append("after seat_left the agent state showed no result and no sync problem within %ds (the agent would wait for ever)" % args.after_seconds)
        for thread in threads:
            thread.join(args.hang_seconds + 30 + args.turns * (args.late_seconds if cell == "L" else 0))
        stop.set()
        if any(thread.is_alive() for thread in threads):
            errors.append("an agent thread did not finish (hang)")
        if spectator is not None and cell != "G":
            spectator.try_to_act()
        time.sleep(1.0)
        if cell == "G":
            problems, compared = [], 0
        else:
            problems, compared = verify_room(host, code, agents, spectator, max(1, min(args.turns, 3) - 1))
        problems = errors + problems
        for agent in agents:
            notes.extend(getattr(agent, "notes", [])[:3])
        if procs and cell != "G" and procs[0].poll() is not None:
            problems.append("the white page process exited early (code %s)" % procs[0].returncode)
        scenario = scenario_of(cell, stats, agents, spectator, compared, notes, args)
        if not scenario["occurred"]:
            problems.append("SCENARIO DID NOT HAPPEN (counts as a gap, not a pass): %s" % json.dumps(scenario["actual"], sort_keys=True))
        return {"cell": cell, "size": size, "run": index, "ok": not problems, "scenario": scenario, "seconds": round(time.time() - started, 1), "problems": problems, "stats": stats, "hash_rounds": compared,
                "heroes": {"red": red, "white": white}, "notes": notes, "load1": round(os.getloadavg()[0], 2)}
    except Exception as exc:
        return {"cell": cell, "size": size, "run": index, "ok": False, "seconds": round(time.time() - started, 1), "problems": ["%s: %s" % (type(exc).__name__, exc)], "stats": stats,
                "heroes": {"red": red, "white": white}, "notes": notes, "load1": round(os.getloadavg()[0], 2)}
    finally:
        stop.set()
        for agent in agents:
            try:
                agent.bridge.close()
            except Exception:
                pass
        for proc in procs:
            if proc.poll() is None:
                proc.kill()
        if spectator is not None:
            spectator.close()
        if host is not None:
            host.close()


def run_h_one(hero, size, index, args, sim):
    """One cell-H run: the focal hero leads the red team; returns the row."""
    rng = random.Random(args.seed_base + size * 10007 + index * 131 + sum(map(ord, hero)))
    others = [h for h in HEROES if h != hero]
    red = [hero] + [rng.choice(others) for _ in range(size - 1)]
    computer_pool = ["bat", "bride", "hag", "hunchback", "skeleton", "wizard"]   # heroes whose room ultimates are allowed, so a computer seat cannot fire a refused one
    white = [rng.choice(computer_pool) for _ in range(size)]
    code = "MXH%d%03d" % (size, (index + sum(map(ord, hero))) % 1000)
    host, procs, agents, spectator, stop = None, [], [], None, threading.Event()
    stats = {"probes": 0, "refused": 0, "turns": 0}
    log, started = [], time.time()
    try:
        host = RelayHost()
        host.relay.rooms[code] = Room(code, scene="graveyard", team_size=size)
        url = "ws://127.0.0.1:%d" % host.relay.bound_port
        agent = make_agent("agent-red", "red", size, url, code, red, white, args.speed, rng.randint(1, 9999), stats, random.Random(rng.random()))
        agents.append(agent)
        procs.append(start_white_page(url, code, white, size, rng.randint(1, 9999), args.speed))
        agent.bridge.start()
        wait_for(lambda: agent.bridge.started, "the agent's page did not see the room start", 30)
        time.sleep(0.5)
        result = {}
        errors = []

        def drive():
            try:
                result["end"] = agent.play_focal(hero, args.max_turns, args.hang_seconds, stop, sim, log)
            except Exception as exc:
                errors.append(str(exc))
                stop.set()
        thread = threading.Thread(target=drive, daemon=True)
        thread.start()
        thread.join(args.hang_seconds + 60 + args.max_turns * 6)
        if thread.is_alive():
            errors.append("the agent thread did not finish (hang)")
            stop.set()
        time.sleep(1.0)
        problems = list(errors)
        room = host.relay.rooms.get(code)
        hashes = room.round_hashes if room else {}
        desync = [number for number, by_seat in sorted(hashes.items()) if len(set(by_seat.values())) > 1]
        compared = sum(1 for by_seat in hashes.values() if len(by_seat) >= 2)
        if host.errors:
            problems.append("relay errors: %s" % host.errors[:5])
        for number in desync:
            problems.append("round %s hash differs: %s" % (number, hashes[number]))
        if compared < 1 and not problems:
            problems.append("no round hash was compared")
        # what the page did with the focal hero's throws (the engine's throw log is the public view built from the page's results)
        focal_throws = []
        for rec in agent.session.engine.throw_log:
            unit = agent.session.engine.units.get(rec.get("unit"))
            if unit and unit["team"] == "red" and unit["hero"] == hero:
                focal_throws.append({"round": rec["round"], "unit": rec["unit"], "ultimate": bool(rec.get("ultimate")), "hit_type": rec.get("hit_type"),
                                     "damage": rec.get("damage_dealt"), "statuses": rec.get("statuses"), "hash_equal": rec["round"] not in desync})
        if agent.state().get("sync", {}).get("status") == "out_of_sync":
            problems.append("the agent ends with sync out_of_sync")
        ult = ("fired" if stats.get("ult_fired") else "refused" if stats.get("ult_refused") else "not_reached")
        return {"cell": "H", "hero": hero, "size": size, "run": index, "ok": not problems, "seconds": round(time.time() - started, 1), "problems": problems, "stats": stats, "ult": ult,
                "hash_rounds": compared, "desync_rounds": desync, "focal_throws": focal_throws, "turn_log": log, "heroes": {"red": red, "white": white}, "load1": round(os.getloadavg()[0], 2)}
    except Exception as exc:
        return {"cell": "H", "hero": hero, "size": size, "run": index, "ok": False, "seconds": round(time.time() - started, 1), "problems": ["%s: %s" % (type(exc).__name__, exc)], "stats": stats, "ult": "error",
                "hash_rounds": 0, "desync_rounds": [], "focal_throws": [], "turn_log": log, "heroes": {"red": red, "white": white}, "load1": round(os.getloadavg()[0], 2)}
    finally:
        stop.set()
        for a in agents:
            try:
                a.bridge.close()
            except Exception:
                pass
        for proc in procs:
            if proc.poll() is None:
                proc.kill()
        if host is not None:
            host.close()


def h_matrix(rows):
    """heroes x sizes: runs, focal plain throws, ultimate attempts (fired / refused), results seen, statuses seen, desyncs."""
    matrix = {}
    for r in rows:
        if r.get("cell") != "H":
            continue
        cell = matrix.setdefault("%s_%dv%d" % (r["hero"], r["size"], r["size"]), {"hero": r["hero"], "size": r["size"], "runs": 0, "plain_throws": 0, "ult_fired": 0, "ult_refused": 0,
                                                                              "ult_not_reached": 0, "desync_runs": 0, "failed_runs": 0, "results": {}, "statuses": {}})
        cell["runs"] += 1
        cell["plain_throws"] += r["stats"].get("plain_focal", 0)
        cell["runs_with_plain"] = cell.get("runs_with_plain", 0) + (1 if r["stats"].get("plain_focal", 0) else 0)
        cell["runs_with_ult_attempt"] = cell.get("runs_with_ult_attempt", 0) + (1 if r["ult"] in ("fired", "refused") else 0)
        cell["ult_fired"] += 1 if r["ult"] == "fired" else 0
        cell["ult_refused"] += 1 if r["ult"] == "refused" else 0
        cell["ult_not_reached"] += 1 if r["ult"] == "not_reached" else 0
        cell["desync_runs"] += 1 if r["desync_rounds"] else 0
        cell["failed_runs"] += 0 if r["ok"] else 1
        for t in r["focal_throws"]:
            key = ("ultimate:" if t["ultimate"] else "plain:") + str(t["hit_type"])
            cell["results"][key] = cell["results"].get(key, 0) + 1
            for word in t.get("statuses") or []:
                name = str(word).split(":")[0]
                cell["statuses"][name] = cell["statuses"].get(name, 0) + 1
    return matrix


def run_h(args, rows, jsonl, done):
    import importlib
    os.environ.setdefault("PK_SIM_LOG", str(ROOT / "logs_local" / "mcp_matrix_sim.log"))
    sim = importlib.import_module("sim_team_headless")
    heroes = [h.strip() for h in args.heroes.split(",") if h.strip()]
    failed = False
    for hero in heroes:
        for size in [int(x) for x in args.sizes.split(",")]:
            while True:
                mine = [r for r in rows if r.get("cell") == "H" and r["hero"] == hero and r["size"] == size]
                plain = sum(r["stats"].get("plain_focal", 0) for r in mine)
                attempts = sum(1 for r in mine if r["ult"] in ("fired", "refused"))
                index = len(mine)
                if (plain >= args.min_plain and attempts >= args.min_ult) or index >= args.max_runs:
                    break
                row = run_h_one(hero, size, index, args, sim)
                rows.append(row)
                with jsonl.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                print(time.strftime("%H:%M:%S"), "H %-9s %dv%d run %03d %s %.1fs ult %s plain %d hash rounds %s load1 %.2f%s" % (
                    hero, size, size, index, "OK" if row["ok"] else "FAIL", row["seconds"], row["ult"], row["stats"].get("plain_focal", 0), row["hash_rounds"], row["load1"],
                    "" if row["ok"] else " :: " + "; ".join(row["problems"])[:300]), flush=True)
                if not row["ok"]:
                    failed = True
                    if not args.keep_going:
                        return True
            mine = [r for r in rows if r.get("cell") == "H" and r["hero"] == hero and r["size"] == size]
            print("    %s %dv%d: runs %d, plain %d, ultimates fired %d refused %d not reached %d" % (hero, size, size, len(mine), sum(r["stats"].get("plain_focal", 0) for r in mine),
                  sum(1 for r in mine if r["ult"] == "fired"), sum(1 for r in mine if r["ult"] == "refused"), sum(1 for r in mine if r["ult"] == "not_reached")), flush=True)
    return failed


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cells", default="A,B,D")
    ap.add_argument("--sizes", default="1,2,3")
    ap.add_argument("--runs", type=int, default=100)
    ap.add_argument("--turns", type=int, default=5, help="own turns each agent plays per run")
    ap.add_argument("--speed", type=float, default=8.0)
    ap.add_argument("--grace", type=float, default=4.0, help="seat grace period (s) for cells D and G")
    ap.add_argument("--hang-seconds", type=int, default=60)
    ap.add_argument("--heroes", default=",".join(HEROES), help="cell H: heroes to cover")
    ap.add_argument("--min-ult", type=int, default=30, help="cell H: ultimate attempts (fired or refused) wanted per hero and size")
    ap.add_argument("--min-plain", type=int, default=30, help="cell H: plain throws of the focal hero wanted per hero and size")
    ap.add_argument("--max-runs", type=int, default=90, help="cell H: give up on a hero and size after this many runs")
    ap.add_argument("--max-turns", type=int, default=18, help="cell H: own turns per run at most")
    ap.add_argument("--late-turn-seconds", type=float, default=3.0, help="cell L: the agent session's turn timer")
    ap.add_argument("--late-seconds", type=float, default=5.0, help="cell L: how long the agent waits (polling) before it acts")
    ap.add_argument("--after-seconds", type=int, default=30, help="cell G: how long the agent may take to show a reaction after seat_left")
    ap.add_argument("--seed-base", type=int, default=20261123)
    ap.add_argument("--label", default="matrix")
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--keep-going", action="store_true")
    args = ap.parse_args()
    cells = [c.strip().upper() for c in args.cells.split(",") if c.strip()]
    sizes = [int(s) for s in args.sizes.split(",")]
    if NODE is None or not set(cells) <= set("ABDGLH") or not set(sizes) <= {1, 2, 3} or args.runs < 1:
        print("ERROR bad arguments or node missing", file=sys.stderr)
        return 2
    out_dir = LOG_BASE / args.label
    out_dir.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    jsonl = out_dir / "runs.jsonl"
    done = set()
    rows = []
    if args.resume and jsonl.exists():
        for line in jsonl.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
                done.add((row["cell"], row["size"], row["run"]))
                rows.append(row)
            except ValueError:
                pass
    elif jsonl.exists():
        jsonl.rename(out_dir / ("runs.%d.jsonl.old" % int(time.time())))
    interrupted = []
    signal.signal(signal.SIGINT, lambda *_: interrupted.append(1))
    signal.signal(signal.SIGTERM, lambda *_: interrupted.append(1))
    failed = False
    print(time.strftime("%H:%M:%S"), "matrix %s: cells %s sizes %s runs %d turns %d" % (args.label, cells, sizes, args.runs, args.turns), flush=True)
    for cell in cells:
        if cell == "H":
            if not interrupted:
                failed = run_h(args, rows, jsonl, done) or failed
            if failed and not args.keep_going:
                break
            continue
        for size in sizes:
            for index in range(args.runs):
                if (cell, size, index) in done:
                    continue
                if interrupted:
                    break
                row = run_cell(cell, size, index, args)
                if row["problems"] and row["problems"][0].startswith("RuntimeError: relay did not start"):
                    print("ERROR setup: the relay could not start (a localhost socket is needed; run this in a normal terminal, not the Claude sandbox)", file=sys.stderr)
                    return 2
                rows.append(row)
                with jsonl.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                print(time.strftime("%H:%M:%S"), "%s %dv%d run %03d %s %.1fs probes %d/%d hash rounds %s load1 %.2f%s" % (
                    cell, size, size, index, "OK" if row["ok"] else "FAIL", row["seconds"], row["stats"]["refused"], row["stats"]["probes"], row.get("hash_rounds", "-"), row["load1"],
                    "" if row["ok"] else " :: " + "; ".join(row["problems"])[:300]), flush=True)
                for note in row.get("notes", []):
                    if cell in ("G", "L") or not row["ok"]:
                        print("    note:", note, flush=True)
                if not row["ok"]:
                    failed = True
                    if not args.keep_going:
                        break
            if failed and not args.keep_going:
                break
        if failed and not args.keep_going:
            break
    summary = {"label": args.label, "cells": cells, "sizes": sizes, "runs_per_cell_size": args.runs, "turns": args.turns, "total_runs": len(rows),
               "passed": sum(1 for r in rows if r["ok"]), "failed": sum(1 for r in rows if not r["ok"]),
               "by_cell_size": {}, "first_failures": [r for r in rows if not r["ok"]][:5], "finished": time.strftime("%Y-%m-%d %H:%M:%S"), "interrupted": bool(interrupted)}
    for r in rows:
        if r["cell"] == "H":
            continue
        key = "%s_%dv%d" % (r["cell"], r["size"], r["size"])
        cell = summary["by_cell_size"].setdefault(key, {"runs": 0, "passed": 0, "probes": 0, "refused": 0})
        cell["runs"] += 1
        cell["passed"] += 1 if r["ok"] else 0
        cell["probes"] += r["stats"]["probes"]
        cell["refused"] += r["stats"]["refused"]
    occurrence = {}
    gaps = []
    for r in rows:
        if r["cell"] == "H":
            continue
        key = "%s_%dv%d" % (r["cell"], r["size"], r["size"])
        occ = occurrence.setdefault(key, {"expected_runs": args.runs, "ran": 0, "scenario_occurred": 0})
        occ["ran"] += 1
        if r.get("scenario", {}).get("occurred"):
            occ["scenario_occurred"] += 1
        else:
            gaps.append({"cell": r["cell"], "size": r["size"], "run": r["run"], "actual": r.get("scenario", {}).get("actual", "not recorded")})
    summary["scenario_occurrence"] = occurrence
    summary["scenario_gaps"] = gaps[:20]
    summary["scenario_gap_count"] = len(gaps)
    short = []
    if "H" in cells:
        summary["h_matrix"] = h_matrix(rows)
        for hero in [h.strip() for h in args.heroes.split(",") if h.strip()]:
            for size in sizes:
                c = summary["h_matrix"].get("%s_%dv%d" % (hero, size, size))
                attempts = (c["ult_fired"] + c["ult_refused"]) if c else 0
                if not c or c["plain_throws"] < args.min_plain or attempts < args.min_ult:
                    short.append("%s %dv%d: plain %d (want %d), ultimate attempts %d (want %d)" % (hero, size, size, c["plain_throws"] if c else 0, args.min_plain, attempts, args.min_ult))
        summary["h_coverage_shortfall"] = short
    expected_runs = len([c for c in cells if c != "H"]) * len(sizes) * args.runs
    summary["total_runs_non_h"] = sum(1 for r in rows if r["cell"] != "H")
    summary["result"] = "PASS" if summary["failed"] == 0 and not interrupted and summary["total_runs_non_h"] >= expected_runs and not short and not gaps else "FAIL"
    (EVIDENCE / ("mcp_matrix_%s_summary.json" % args.label)).write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
    print(time.strftime("%H:%M:%S"), "RESULT %s runs %d passed %d failed %d (redteam/evidence/mcp_matrix_%s_summary.json)" % (summary["result"], summary["total_runs"], summary["passed"], summary["failed"], args.label), flush=True)
    print("RESOURCE_RELEASED", flush=True)
    return 130 if interrupted else (1 if summary["failed"] else 0)


if __name__ == "__main__":
    sys.exit(main())
