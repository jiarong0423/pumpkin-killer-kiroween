#!/usr/bin/env python3
"""Run one Kiro CLI task with automatic model routing.

Tries the models of a route in order. A model is skipped (next one tried) when its output shows throttling / high traffic
or an unknown model; a throttled model gets RETRIES retries with a growing pause first. The run succeeds only when the
CLI exits 0 AND, when --expect is given, the expected output file exists afterwards. Everything is logged to a file.

Usage (run it in the worktree of the task, outside the sandbox: Kiro needs the network):
  python3 -B scripts/kiro_route.py --brief docs/kiro_task_53.md --expect docs/kiro_53_recommendations.md [--route design] [--agent researcher]

Routes live in scripts/kiro_models.json ({"routes": {"design": ["claude-sonnet-5.5", ...]}}). Model ids not verified on this
machine are simply skipped when the CLI rejects them. Exit codes: 0 done, 1 every model failed, 2 bad arguments / config.
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
THROTTLE = ("modelthrottleerror", "high traffic", "unexpectedly high load", "throttling", "rate limit", "too many requests")
BAD_MODEL = ("unknown model", "invalid model", "model not found", "not a valid model", "unsupported model", "does not exist")


def classify(text, code):
    """Return 'ok', 'throttled', 'bad_model' or 'failed' from the CLI output and exit code."""
    low = (text or "").lower()
    if code == 0:
        return "ok"   # an exit 0 run is a success even if its text mentions "does not exist" or "high traffic" (task 83 was wrongly marked bad_model 2026-11-10 after it wrote its evidence file)
    if any(k in low for k in THROTTLE):
        return "throttled"
    if any(k in low for k in BAD_MODEL):
        return "bad_model"
    return "failed"


def load_route(name, path):
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    route = cfg.get("routes", {}).get(name)
    if not route or not all(isinstance(m, str) and m for m in route):
        raise ValueError("route %r missing or invalid in %s" % (name, path))
    return route, int(cfg.get("retries", 1)), float(cfg.get("pause_seconds", 20))


def run_cli(model, brief, agent, cwd, timeout):
    cmd = ["kiro-cli", "chat", "--agent-engine", "v3", "--no-interactive", "--trust-workspace", "--agent", agent, "--model", model,
           "Read %s and carry out that task exactly." % brief]
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def route_run(route, brief, expect, agent, cwd, retries, pause, timeout, log, runner=run_cli, sleep=time.sleep):
    """Core loop, injectable for tests. Returns (status, model_used or None)."""
    for model in route:
        for attempt in range(retries + 1):
            log("model %s attempt %d" % (model, attempt + 1))
            try:
                code, out = runner(model, brief, agent, cwd, timeout)
            except subprocess.TimeoutExpired:
                log("ERROR timeout with %s" % model)
                break
            except OSError as e:
                log("ERROR cannot start kiro-cli: %r" % (e,))
                return "failed", None
            state = classify(out, code)
            log("result %s (exit %s)" % (state, code))
            if state == "ok":
                if expect and not glob.glob(os.path.join(cwd, expect)):   # the expected file may carry the model name: a glob such as docs/kiro_62_prompts_*.json is accepted
                    log("ERROR exit 0 but expected file is missing: %s" % expect)
                    break
                return "ok", model
            if state == "throttled" and attempt < retries:
                sleep(pause * (attempt + 1))
                continue
            break
    return "failed", None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--brief", required=True)
    ap.add_argument("--expect", default="")
    ap.add_argument("--route", default="design")
    ap.add_argument("--agent", default="researcher")
    ap.add_argument("--config", default=os.path.join(HERE, "kiro_models.json"))
    ap.add_argument("--cwd", default=os.getcwd())
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--log", default="")
    a = ap.parse_args(argv)
    try:
        route, retries, pause = load_route(a.route, a.config)
    except (OSError, ValueError) as e:
        print("ERROR config: %s" % e, file=sys.stderr)
        return 2
    logpath = a.log or os.path.join(a.cwd, "kiro_route_%s.log" % os.path.basename(a.brief).replace(".md", ""))

    def log(msg):
        line = time.strftime("%H:%M:%S ") + msg
        print(line, flush=True)
        with open(logpath, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    status, model = route_run(route, a.brief, a.expect, a.agent, a.cwd, retries, pause, a.timeout, log)
    if status == "ok":
        log("DONE with %s" % model)
        return 0
    log("ERROR every model in route %r failed" % a.route)
    return 1


if __name__ == "__main__":
    sys.exit(main())
