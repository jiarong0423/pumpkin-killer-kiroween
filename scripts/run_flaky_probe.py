#!/usr/bin/env python3
"""Run test_mcp_connect.py N times (default 24), pre-importing pk_relay first so the relay path is pinned and recorded (red-team R2B-P1-2).

Usage:
  python3 -B scripts/run_flaky_probe.py --test redteam/backups/bak_g4_3_20261124/test_mcp_connect.py --out redteam/evidence/test_mcp_connect_flaky_before_20261124.txt
  python3 -B scripts/run_flaky_probe.py --test scripts/test_mcp_connect.py --out redteam/evidence/test_mcp_connect_flaky_after_20261124.txt
"""
import argparse
import importlib.util
import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

RUNNER_CODE = r"""
import importlib.util, io, json, sys, unittest
from pathlib import Path

relay_path = Path(sys.argv[1]).resolve()
test_path = Path(sys.argv[2]).resolve()
scripts_dir = Path(sys.argv[3]).resolve()

# Pre-import pk_relay into sys.modules BEFORE the test module runs `sys.path.insert(0, str(HERE))`
# so the exact relay module under test is pinned and verifiable (R2B-P1-2).
sys.path.insert(0, str(scripts_dir))
spec_r = importlib.util.spec_from_file_location("pk_relay", str(relay_path))
mod_r = importlib.util.module_from_spec(spec_r)
sys.modules["pk_relay"] = mod_r
spec_r.loader.exec_module(mod_r)

spec_t = importlib.util.spec_from_file_location("test_mcp_connect_probe", str(test_path))
mod_t = importlib.util.module_from_spec(spec_t)
spec_t.loader.exec_module(mod_t)

suite = unittest.defaultTestLoader.loadTestsFromModule(mod_t)
buf = io.StringIO()
runner = unittest.TextTestRunner(stream=buf, verbosity=2)
res = runner.run(suite)

failed_items = []
for test, tb in list(res.failures) + list(res.errors):
    lines = [ln for ln in tb.strip().splitlines() if ln.strip()]
    tail = lines[-3:] if len(lines) >= 3 else lines
    failed_items.append({"test": str(test), "msg3": tail})

out = {
    "ok": res.wasSuccessful(),
    "tests_run": res.testsRun,
    "failures": len(res.failures),
    "errors": len(res.errors),
    "relay_file": str(getattr(mod_r, "__file__", "")),
    "has_start_if_ready": hasattr(mod_r.RelayServer, "_start_if_ready"),
    "failed_items": failed_items,
}
print("PROBE_JSON:" + json.dumps(out))
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--test", default=str(SCRIPTS / "test_mcp_connect.py"))
    parser.add_argument("--relay", default=str(SCRIPTS / "pk_relay.py"))
    parser.add_argument("--runs", type=int, default=24)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    test_path = (ROOT / args.test).resolve() if not os.path.isabs(args.test) else Path(args.test).resolve()
    relay_path = (ROOT / args.relay).resolve() if not os.path.isabs(args.relay) else Path(args.relay).resolve()
    out_path = (ROOT / args.out).resolve() if not os.path.isabs(args.out) else Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Flaky probe: test_mcp_connect.py (R2B-P1-2)",
        "date: %s" % time.strftime("%Y-%m-%d %H:%M:%S"),
        "test_file: %s" % os.path.relpath(test_path, ROOT),
        "relay_file: %s" % os.path.relpath(relay_path, ROOT),
        "runs: %d" % args.runs,
        "method: subprocess pre-imports pk_relay into sys.modules before loading test_file",
    ]
    passed = 0
    failed = 0
    header_checked = False

    for idx in range(1, args.runs + 1):
        proc = subprocess.run(
            [sys.executable, "-B", "-c", RUNNER_CODE, str(relay_path), str(test_path), str(SCRIPTS)],
            cwd=str(ROOT), capture_output=True, text=True, timeout=60,
        )
        payload = None
        for ln in proc.stdout.splitlines():
            if ln.startswith("PROBE_JSON:"):
                payload = json.loads(ln[len("PROBE_JSON:"):])
        if payload is None:
            failed += 1
            err_lines = (proc.stderr or proc.stdout).strip().splitlines()[:3]
            row = "%02d/%02d FAIL <process_error rc=%d> | %s" % (idx, args.runs, proc.returncode, " // ".join(err_lines))
            lines.append(row)
            print(row, flush=True)
            continue
        if not header_checked:
            lines.append("verified_pk_relay_file: %s (has_start_if_ready=%s)" % (payload["relay_file"], payload["has_start_if_ready"]))
            lines.append("")
            header_checked = True
        if payload["ok"]:
            passed += 1
            row = "%02d/%02d PASS (ran=%d)" % (idx, args.runs, payload["tests_run"])
            lines.append(row)
            print(row, flush=True)
        else:
            failed += 1
            names = ", ".join(item["test"] for item in payload["failed_items"])
            row = "%02d/%02d FAIL %s" % (idx, args.runs, names)
            lines.append(row)
            print(row, flush=True)
            for item in payload["failed_items"]:
                for msg_line in item["msg3"]:
                    detail = "      " + msg_line
                    lines.append(detail)
                    print(detail, flush=True)

    summary = "TOTAL: passed=%d failed=%d runs=%d" % (passed, failed, args.runs)
    lines.append("")
    lines.append(summary)
    print(summary, flush=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
