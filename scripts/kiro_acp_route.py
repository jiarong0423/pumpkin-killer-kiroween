#!/usr/bin/env python3
"""Run one Kiro task through the Agent Client Protocol (ACP) instead of `kiro-cli chat`.

Why: ACP gives a live, structured view (every tool call, every permission request, the stop reason) and a cancel call; `kiro_route.py`
captures nothing. This client speaks newline-delimited JSON-RPC 2.0 over the stdio of `kiro-cli acp --agent-engine v3` (docs:
https://kiro.dev/docs/cli/acp/ and https://kiro.dev/docs/cli/v3/acp-migration/).

Usage:
  python3 -B scripts/kiro_acp_route.py --brief docs/kiro_task_NNN_x.md --expect docs/kiro_NNN_result.md [--model gpt-5.6-terra]
      [--mode builder] [--timeout 3600] [--prompt "free text instead of the brief"] [--dry-policy]

Policy for permission requests (the agent asks before shell and file tools): allow once when the request is plainly inside this
repository and not on the deny list; reject otherwise. The deny list is the same set the committer agent denies plus network and
destructive commands. Everything the agent says or does is appended to `kiro_acp_<task>.log` (git-ignored) as readable lines and
to `kiro_acp_<task>.jsonl` as raw messages.

Exit codes: 0 done and the expected file exists; 2 agent finished but the expected file is missing; 3 timeout (cancelled);
4 protocol or start-up error; 5 a permission request was rejected by policy and the turn ended in refusal.
"""
import argparse
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DENY = [r"\bgit\s+push\b", r"\bgit\s+remote\b", r"\bgit\s+config\b", r"\bgit\s+reset\b", r"\bgit\s+clean\b", r"\bgit\s+checkout\b",
        r"\bgit\s+commit\b", r"\bcurl\b", r"\bwget\b", r"\bssh\b", r"\bscp\b", r"\bsudo\b", r"\brm\s+-rf?\s+/", r"\brm\s+-rf\b",
        r"\bkirocrew\b", r"\bpip3?\s+install\b", r"\bnpm\s+(install|i)\b", r"\bbrew\b", r"\bdocker\b", r"\.env\b", r"PK_TERMS",
        r"\bGEMINI_API_KEY\b", r"\bPK_GEMINI_KEYS\b"]
DEFAULT_MODEL = "gpt-5.6-terra"


class Acp:
    def __init__(self, cwd, log_path, raw_path, model, mode):
        self.cwd, self.model, self.mode = cwd, model, mode
        self.log = open(log_path, "a", encoding="utf-8")
        self.raw = open(raw_path, "a", encoding="utf-8")
        self.proc = subprocess.Popen(["kiro-cli", "acp", "--agent-engine", "v3"], cwd=cwd, stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
        self.inbox = queue.Queue()
        self.next_id = 0
        self.denied = 0
        self.tool_calls = 0
        self.text = []
        threading.Thread(target=self._reader, daemon=True).start()
        threading.Thread(target=self._stderr, daemon=True).start()

    def say(self, line):
        stamp = time.strftime("%H:%M:%S")
        self.log.write("%s %s\n" % (stamp, line))
        self.log.flush()

    def _reader(self):
        for line in self.proc.stdout:
            line = line.strip()
            if not line:
                continue
            self.raw.write("<< " + line + "\n")
            self.raw.flush()
            try:
                self.inbox.put(json.loads(line))
            except ValueError:
                self.say("NONJSON " + line[:200])
        self.inbox.put(None)

    def _stderr(self):
        for line in self.proc.stderr:
            self.say("stderr " + line.rstrip()[:300])

    def send(self, obj):
        line = json.dumps(obj)
        self.raw.write(">> " + line + "\n")
        self.raw.flush()
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def request(self, method, params, deadline):
        self.next_id += 1
        rid = self.next_id
        self.send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        return self.wait(rid, deadline)

    def wait(self, rid, deadline):
        """Pump messages until the response to rid arrives; answer the agent's own requests on the way."""
        while True:
            left = deadline - time.time()
            if left <= 0:
                raise TimeoutError("no response to request %s" % rid)
            try:
                msg = self.inbox.get(timeout=min(left, 5))
            except queue.Empty:
                continue
            if msg is None:
                raise RuntimeError("kiro-cli acp closed its output")
            if "method" in msg:
                self.handle_incoming(msg)
            elif msg.get("id") == rid:
                if "error" in msg:
                    raise RuntimeError("ACP error for request %s: %s" % (rid, json.dumps(msg["error"])[:400]))
                return msg.get("result")

    def handle_incoming(self, msg):
        method, params = msg.get("method"), msg.get("params") or {}
        if method == "session/update":
            self.on_update(params.get("update") or {})
        elif method == "session/request_permission":
            self.send({"jsonrpc": "2.0", "id": msg["id"], "result": self.decide(params)})
        elif "id" in msg:   # any other request from the agent: say "not supported" instead of hanging it
            self.send({"jsonrpc": "2.0", "id": msg["id"], "error": {"code": -32601, "message": "method not supported by this client"}})
            self.say("unsupported request %s" % method)
        else:
            self.say("notification %s" % method)

    def on_update(self, update):
        kind = update.get("sessionUpdate")
        if kind == "agent_message_chunk":
            content = update.get("content") or {}
            if content.get("type") == "text":
                self.text.append(content.get("text", ""))
        elif kind == "tool_call":
            self.tool_calls += 1
            self.say("tool %s [%s] %s" % (update.get("toolCallId", "")[:8], update.get("kind", ""), update.get("title", "")[:160]))
        elif kind == "tool_call_update":
            status = update.get("status")
            if status in ("completed", "failed"):
                self.say("tool %s %s" % (update.get("toolCallId", "")[:8], status))
        elif kind in ("agent_thought_chunk", "user_message_chunk", "available_commands_update", "current_mode_update", "config_option_update"):
            pass
        elif kind == "session_info_update":
            pass
        else:
            self.say("update %s" % kind)

    def decide(self, params):
        call = params.get("toolCall") or {}
        options = params.get("options") or []
        blob = json.dumps(call, ensure_ascii=False)
        bad = [p for p in DENY if re.search(p, blob)]
        want = "reject_once" if bad else "allow_once"
        choice = next((o for o in options if o.get("kind") == want), None) or next((o for o in options if str(o.get("kind", "")).startswith("reject")), None)
        if bad:
            self.denied += 1
            self.say("DENY %s (%s)" % ((call.get("title") or "")[:120], bad[0]))
        else:
            self.say("allow %s" % (call.get("title") or "")[:120])
        if not choice:
            return {"outcome": {"outcome": "cancelled"}}
        return {"outcome": {"outcome": "selected", "optionId": choice.get("optionId")}}

    def close(self):
        try:
            self.proc.stdin.close()
        except Exception:
            pass
        try:
            self.proc.terminate()
        except Exception:
            pass


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--brief")
    ap.add_argument("--prompt")
    ap.add_argument("--expect")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--mode", default="builder", help="Kiro custom agent / mode id (V3 takes it in session/new _meta.kiro.modeId)")
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--name")
    args = ap.parse_args(argv)
    if not args.brief and not args.prompt:
        print("ERROR give --brief or --prompt", file=sys.stderr)
        return 4
    name = args.name or re.sub(r"[^A-Za-z0-9_]+", "_", os.path.splitext(os.path.basename(args.brief or "prompt"))[0])
    log_dir = os.path.join(ROOT, "logs_local", "kiro")
    os.makedirs(log_dir, exist_ok=True)
    log_path, raw_path = os.path.join(log_dir, "kiro_acp_%s.log" % name), os.path.join(log_dir, "kiro_acp_%s.jsonl" % name)
    text = args.prompt or ("Read %s and carry out that task exactly." % args.brief)
    deadline = time.time() + args.timeout
    acp = Acp(ROOT, log_path, raw_path, args.model, args.mode)
    acp.say("START %s model=%s mode=%s" % (name, args.model, args.mode))
    code = 4
    try:
        init = acp.request("initialize", {"protocolVersion": 1, "clientCapabilities": {"fs": {"readTextFile": False, "writeTextFile": False}, "terminal": False},
                                          "clientInfo": {"name": "pumpkin-killer-acp-route", "version": "1"}}, deadline)
        acp.say("initialized agent=%s" % json.dumps((init or {}).get("agentInfo"))[:120])
        meta = {"kiro": {"modeId": args.mode, "modelId": args.model}}
        try:
            session = acp.request("session/new", {"cwd": ROOT, "mcpServers": [], "_meta": meta}, deadline)
        except RuntimeError as err:   # an unknown mode or model id: retry once with no meta and say so
            acp.say("session/new with meta failed (%s); retrying without it" % str(err)[:200])
            session = acp.request("session/new", {"cwd": ROOT, "mcpServers": []}, deadline)
        sid = (session or {}).get("sessionId")
        if not sid:
            raise RuntimeError("session/new returned no sessionId: %s" % json.dumps(session)[:200])
        acp.say("session %s" % sid[:8])
        result = acp.request("session/prompt", {"sessionId": sid, "prompt": [{"type": "text", "text": text}]}, deadline)
        stop = (result or {}).get("stopReason")
        acp.say("STOP %s tool_calls=%d denied=%d" % (stop, acp.tool_calls, acp.denied))
        summary = "".join(acp.text).strip()
        if summary:
            acp.say("SUMMARY " + summary[-600:].replace("\n", " | "))
        if args.expect and not os.path.exists(os.path.join(ROOT, args.expect)):
            acp.say("ERROR agent finished but expected file is missing: %s" % args.expect)
            code = 2
        elif stop == "refusal" or (acp.denied and stop != "end_turn"):
            code = 5
        else:
            code = 0
    except TimeoutError as err:
        acp.say("TIMEOUT %s; cancelling" % err)
        try:
            acp.send({"jsonrpc": "2.0", "method": "session/cancel", "params": {"sessionId": (locals().get("sid") or "")}})
        except Exception:
            pass
        code = 3
    except Exception as err:   # protocol or start-up problem: leave a greppable ERROR and a non-zero exit
        acp.say("ERROR %s" % str(err)[:400])
        code = 4
    finally:
        acp.close()
    print("kiro_acp_route: %s exit %d (log: %s)" % (name, code, os.path.relpath(log_path, ROOT)))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
