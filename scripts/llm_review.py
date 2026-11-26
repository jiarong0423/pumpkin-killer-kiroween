#!/usr/bin/env python3
"""Ask an external model on Nebius Token Factory (OpenAI-compatible API) to attack and review the room / lobby code (owner 2026-11-26: GLM and DeepSeek).

Two tasks:
  attack  -> a JSON file of break-it cases (message sequences against the relay) for scripts/llm_attack_runner.py to execute locally
  review  -> a Markdown file of defects, debugging notes on known open items, and change suggestions (text only; Claude checks every claim in the code)

What is sent: scripts/pk_relay.py, js/relay_client.js, js/lobby_model.js, the lobby block of index.html, and the known-issues list of
docs/gemini_verify_room_flow_20261126.md. No key, token or personal data is sent. The API key is read from NEBIUS_API_KEY or, if absent, from the one
NEBIUS_API_KEY line of ../.workspace_auth.env; it is never printed or written.

Usage (needs the network; run outside the sandbox):
  python3 -B scripts/llm_review.py --match glm --task attack --out docs/llm/glm_attack.json
  python3 -B scripts/llm_review.py --match deepseek --task review --out docs/llm/deepseek_review.md
  python3 -B scripts/llm_review.py --list            # model ids only
Log: logs_local/llm_review.log (one line per call: model, task, seconds, token usage, result). Exit 0 ok, 1 call failed, 2 setup error.
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.environ.get("NEBIUS_BASE_URL", "https://api.studio.nebius.com/v1").rstrip("/")
LOG = os.path.join(ROOT, "logs_local", "llm_review.log")
UA = "pumpkin-killer-review/1.0"


def log(line):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as handle:
        handle.write(time.strftime("%Y-%m-%d %H:%M:%S ") + line + "\n")


def api_key():
    key = os.environ.get("NEBIUS_API_KEY", "").strip()
    if key:
        return key
    path = os.path.join(os.path.dirname(ROOT), ".workspace_auth.env")
    try:
        with open(path, encoding="utf-8") as handle:
            for raw in handle:
                line = raw.strip()
                if line.startswith("export "):
                    line = line[7:].strip()
                if line.startswith("NEBIUS_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


def call(path, key, body=None, timeout=600):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, method="POST" if body is not None else "GET",
                                 headers={"Authorization": "Bearer " + key, "Content-Type": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def pick_model(key, match):
    ids = [m.get("id", "") for m in call("/models", key).get("data", [])]
    want = [i for i in ids if match.lower() in i.lower()]
    if not want:
        raise SystemExit("ERROR no model matches %r; available: %s" % (match, ", ".join(ids[:60])))
    def rank(model):   # newest version first, then the bigger / pro variant, then a plain name (no -fast, -mini)
        nums = [float(n) for n in re.findall(r"(\d+(?:\.\d+)?)", model.split("/")[-1])[:2]] or [0.0]
        low = model.lower()
        return (nums, ("pro" in low) - ("fast" in low or "mini" in low or "flash" in low or "air" in low))
    return sorted(want, key=rank)[-1], ids


def read(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as handle:
        return handle.read()


def package():
    html = read("index.html").split("\n")
    start = next(i for i, l in enumerate(html) if "ROOM-FLOW lobby, the second page" in l)
    end = next(i for i in range(start, len(html)) if "const SHOW_COMING_SOON" in html[i])
    known = read("docs/gemini_verify_room_flow_20261126.md")
    known = known[known.index("## 四、"):] if "## 四、" in known else ""
    parts = [("scripts/pk_relay.py", read("scripts/pk_relay.py")), ("js/relay_client.js", read("js/relay_client.js")),
             ("js/lobby_model.js", read("js/lobby_model.js")), ("index.html (lobby block, lines %d-%d)" % (start + 1, end), "\n".join(html[start:end])),
             ("known open items (do not report again)", known)]
    return "\n\n".join("=== FILE: %s ===\n%s" % (name, body) for name, body in parts)


CONTEXT = ("You review a turn-based browser game's multiplayer room layer: a Python WebSocket relay (pk_relay.py), its browser client (relay_client.js), "
           "a lobby view model (lobby_model.js) and the lobby page code. Teams are red and white, 1v1, 2v2 or 3v3; a seat holds one or more places (units) of its team; "
           "a lobby room starts only after the host's `begin`, every place locked, and a countdown. Computer filler seats join with `ai_host_token` (the host's seat token); "
           "invited agents join with a one-use `invite` ticket. Two earlier red-team rounds already fixed many issues; the known open items are listed at the end.")

ATTACK = CONTEXT + """

TASK: write break-it test cases that a local runner will execute against the real relay. Output ONLY one JSON object, no prose, no code fences:
{"cases": [{"id": "short-id", "why": "the invariant or rule you try to break, one sentence", "team_size": 1|2|3, "lobby": true|false,
  "steps": [ {"client": "A", "send": {...message...}} | {"client": "B", "connect": true} | {"client": "A", "close": true} | {"sleep": 0.05} | {"expire": "B"} ],
  "expect": "what a correct relay must do, one sentence"}]}
Rules for steps: the first step of every client is {"client": X, "connect": true}; then "send" sends one JSON message on that client's socket.
Placeholders the runner replaces: "$CODE" = the room code from the first create_room answer, "$TOKEN:A" = client A's seat token, "$SEAT:A" = A's seat id,
"$INVITE:A" = the last invite ticket A received. {"expire": "B"} drops B's socket and ends its grace period at once (as if 60 s passed). {"sleep": s} waits s seconds (max 1).
Write 25 cases. Aim at: places per team above the team size, two hosts or no host, an AI or agent seat as host, a seat acting after it was removed, starting without every place locked,
a countdown that survives a change, invites (expiry, reuse, wrong team, cancelled, inviter moved), move/claim races, reset_lobby and resume, malformed and oversized input,
1v1 lobby rules, rate limits per socket. Mix many steps per case (up to 30). Use only message types and fields that exist in pk_relay.py."""

REVIEW = CONTEXT + """

TASK: a careful code review in Markdown, at most 60 lines:
1. Defects you are confident about: severity P0/P1/P2, file and line (or function), what goes wrong, a concrete message sequence or user action that triggers it, and the smallest fix.
2. Debugging: for each known open item at the end, the most likely root cause and a fix you would make.
3. Change suggestions for robustness or clarity (no rewrites, no new features), most valuable first, at most 8.
Do not report the known open items as new defects. Say "none" where you have nothing. Cite real function names from the code; do not invent APIs."""


FIXREVIEW = CONTEXT + """

INCIDENT (live 3v3 room, 2026-11-26): red team = a browser player (red-1, the host; its page also drives the computer seats), an MCP agent (red-2, over the
hosted MCP bridge in mcp_stdio_server.py) and a computer seat (red-3); white the same with a phone browser. One unit acts per team turn; units rotate in id order.
1. The agent threw for left_1 and called end_turn only seconds later. 120 ms after the throw landed, the host page's computer-seat driver
   (maybeTriggerFillerTurn) acted for its local next unit left_2 in the SAME relay turn and ended it; the relay accepted a second unit's throw because its
   one-unit rule was keyed per seat. Host and phone then disagreed on whose turn it was: the match stalled.
2. The agent's bridge judged an enemy hit on a teammate's unit (owned by another seat) and named it; the relay refused (unit_not_yours) and the bridge's
   failure flag ended the agent's play.
3. After fixing 1, the computer seat was never started when the agent's end_turn arrived later (it was only triggered 120 ms after a throw landed).
The diff below is the fix (relay: one-unit rule per team; page: relayPhaseTaken guard + a filler check on every end_turn; bridge: judge only owned units,
and submit_action names the end_turn call).

TASK: review THIS FIX in Markdown, at most 50 lines. 1) Defects in the fix you are confident about: P0/P1/P2, function, a concrete sequence of messages
or player actions that still stalls or desyncs a match (agents slow, timeouts, a seat that left, an AI hand-over, a double shot, a move then a throw,
dead units skipped in rotation, the second match after reset_lobby, reconnect/resume replay), and the smallest change. 2) Cases the fix does not cover yet
that a mixed room (browser players + agents + computer seats) will hit. 3) Say "none" where you have nothing. Cite real function names only."""


def fix_package():
    import subprocess
    diff = subprocess.run(["git", "diff", "-U60", "--", "scripts/pk_relay.py", "index.html", "scripts/mcp_stdio_server.py"], cwd=ROOT,
                          capture_output=True, text=True, check=True).stdout
    html = read("index.html")
    for name in ("function relayDispatch(", "function relayInboxReady(", "function relayAfterTurn("):
        at = html.find(name)
        if at >= 0 and name not in diff:
            diff += "\n=== context: index.html %s ===\n%s" % (name, html[at:at + 2500])
    return "=== GIT DIFF (the fix, with context) ===\n" + diff


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--match", default="glm", help="substring of the model id (glm, deepseek)")
    ap.add_argument("--model", default="", help="exact model id (overrides --match)")
    ap.add_argument("--task", choices=("attack", "review", "fixreview"), default="review")
    ap.add_argument("--out", default="")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--from-raw", default="", help="attack: parse a saved raw answer instead of calling the model")
    ap.add_argument("--think", choices=("model", "off", "low", "medium"), default="model", help="off: chat_template_kwargs thinking false; low/medium: reasoning_effort (measured 2026-11-26: the default thinking used up 60000 tokens without an answer)")
    ap.add_argument("--max-tokens", type=int, default=60000, help="reasoning models spend much of it thinking before they answer (16000 left the answer empty)")
    args = ap.parse_args()
    key = api_key()
    if not key:
        print("ERROR NEBIUS_API_KEY missing (env or ../.workspace_auth.env)")
        return 2
    try:
        if args.list:
            ids = [m.get("id", "") for m in call("/models", key).get("data", [])]
            print("\n".join(i for i in ids if re.search(r"glm|deepseek", i, re.I)))
            return 0
        model = args.model or pick_model(key, args.match)[0]
    except urllib.error.HTTPError as exc:
        print("ERROR models HTTP %s" % exc.code); log("ERROR models HTTP %s" % exc.code); return 1
    except (urllib.error.URLError, OSError) as exc:
        print("ERROR models %s" % type(exc).__name__); log("ERROR models %s" % type(exc).__name__); return 1
    prompt = FIXREVIEW + "\n\n" + fix_package() if args.task == "fixreview" else (ATTACK if args.task == "attack" else REVIEW) + "\n\n" + package()
    body = {"model": model, "temperature": 0.2, "max_tokens": args.max_tokens, "messages": [{"role": "user", "content": prompt}]}
    if args.think == "off":
        body["chat_template_kwargs"] = {"thinking": False, "enable_thinking": False}
    elif args.think in ("low", "medium"):
        body["reasoning_effort"] = args.think
    t0 = time.time()
    try:
        resp = call("/chat/completions", key, body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        print("ERROR chat HTTP %s %s" % (exc.code, detail)); log("ERROR chat model=%s task=%s HTTP %s %s" % (model, args.task, exc.code, detail)); return 1
    except (urllib.error.URLError, OSError) as exc:
        print("ERROR chat %s" % type(exc).__name__); log("ERROR chat model=%s task=%s %s" % (model, args.task, type(exc).__name__)); return 1
    choice = (resp.get("choices") or [{}])[0]
    text = choice.get("message", {}).get("content") or ""
    if not text.strip() or choice.get("finish_reason") == "length":
        log("WARN model=%s task=%s finish=%s content_chars=%d reasoning_chars=%d" % (model, args.task, choice.get("finish_reason"), len(text), len(choice.get("message", {}).get("reasoning_content") or "")))
    text = re.sub(r"^\s*<think>.*?</think>\s*", "", text, flags=re.S)
    seconds = round(time.time() - t0, 1)
    out = args.out or os.path.join(ROOT, "docs", "llm", "%s_%s.%s" % (args.match, args.task, "json" if args.task == "attack" else "md"))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if args.task == "attack" and args.from_raw:
        with open(args.from_raw, encoding="utf-8") as handle:
            text = handle.read()
    if args.task == "attack":
        raw = text.strip().strip("`")
        raw = raw[raw.find("{"): raw.rfind("}") + 1] if "{" in raw else raw
        raw = re.sub(r'"((?:[^"\\]|\\.){0,8})"\.repeat\((\d+)\)', lambda m: json.dumps(json.loads('"' + m.group(1) + '"') * min(20000, int(m.group(2)))), raw)   # a model wrote "x".repeat(20000) inside the JSON
        try:
            cases = json.loads(raw)["cases"]
        except (ValueError, KeyError, TypeError) as exc:
            with open(out + ".raw.txt", "w", encoding="utf-8") as handle:
                handle.write(text)
            print("ERROR the answer is not the JSON asked for (%s); raw answer in %s.raw.txt" % (type(exc).__name__, out))
            log("ERROR attack json model=%s seconds=%s" % (model, seconds)); return 1
        with open(out, "w", encoding="utf-8") as handle:
            json.dump({"model": model, "cases": cases}, handle, ensure_ascii=False, indent=1)
        result = "%d cases" % len(cases)
    else:
        with open(out, "w", encoding="utf-8") as handle:
            handle.write("# %s review (model %s, %s)\n\n%s\n" % (args.match, model, time.strftime("%Y-%m-%d %H:%M"), text.strip()))
        result = "%d lines" % len(text.splitlines())
    usage = resp.get("usage") or {}
    log("OK model=%s task=%s seconds=%s prompt_tokens=%s completion_tokens=%s %s out=%s" % (model, args.task, seconds, usage.get("prompt_tokens"), usage.get("completion_tokens"), result, out))
    print("OK model=%s task=%s %s seconds=%s tokens in/out %s/%s -> %s" % (model, args.task, result, seconds, usage.get("prompt_tokens"), usage.get("completion_tokens"), out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
