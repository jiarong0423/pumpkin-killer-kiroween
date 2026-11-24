#!/usr/bin/env python3
"""Write the daily log (docs/daily/YYYYMMDD.md) and the progress table (docs/PROGRESS_TABLE.md) from project files.

Default is --dry-run: it prints a diff and writes nothing (not even the run log). --apply writes the two files, first
copying the old versions into docs/daily/backup/. Standard library only, no network, no scheduler.

Reads: docs/owner_feedback_log.md, the newest docs/GAP_QUEUE_YYYYMMDD.md, docs/asset_inventory.json (regenerated with
scripts/make_asset_inventory.py on --apply), docs/kiro_NN_*.md, kiro_route_*.log in the project and in the sibling
worktrees <project>_kiro*, and (only with --run-tests) scripts/test_*.py.

Exit codes: 0 ok; 1 fatal, nothing written (no gap queue, no rows, unwritable output, unexpected error);
2 bad arguments; 3 files written but an input could not be read; 4 files written but a project test failed.
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STALE_DAYS = 3
TEST_TIMEOUT = 600
SUMMARY_START = "<!-- SUMMARY:START -->"
SUMMARY_END = "<!-- SUMMARY:END -->"
SUMMARY_PLACEHOLDER = "(10-line summary not written yet. Run the daily-logger agent to fill this block.)"
ROWS_HEADING = "## Rows"
EXIT_OK, EXIT_FATAL, EXIT_BAD_ARGS, EXIT_INPUT, EXIT_TEST = 0, 1, 2, 3, 4

# Canonical status keys, in the order they are shown. The gap queue is written in Chinese, so the match is by keyword.
STATUS_ORDER = ["done", "built_unseen", "in_progress", "queued", "decided", "todo", "not_started", "to_verify",
                "waiting_owner", "waiting_other", "ongoing", "unknown"]
STATUS_RULES = [   # first rule that matches wins, so the specific words come before the general ones
    ("built_unseen", ("已做未看",)),
    ("in_progress", ("進行中", "執行中")),
    ("queued", ("排隊", "已排進", "任務檔已寫")),
    ("waiting_owner", ("等你",)),
    ("waiting_other", ("等出圖", "等設計", "等盤點", "等")),
    ("to_verify", ("待查", "待驗", "待收")),
    ("todo", ("待做",)),
    ("not_started", ("未開始",)),
    ("decided", ("已定",)),
    ("done", ("已完成", "已處理", "已做")),
    ("ongoing", ("持續", "規則")),
]

_SEP = re.compile(r"^:?-{3,}:?$")
ID_RE = re.compile(r"^\*{0,2}([A-Z]\d{1,3})\*{0,2}$")
GAP_NAME = re.compile(r"^GAP_QUEUE_(\d{8})\.md$")
DAILY_NAME = re.compile(r"^(\d{8})\.md$")
ROUTE_LOG_RE = re.compile(r"^kiro_route_.*\.log$")
TASK_NUM_RE = re.compile(r"kiro_route_.*?(\d+)")
KIRO_DOC_RE = re.compile(r"^kiro_(\d+)_.*\.md$")
BRIEF_RE = re.compile(r"^kiro_task_(\d+)\.md$")
LOG_LINE_RE = re.compile(r"^(\d\d:\d\d:\d\d) (.*)$")
TEST_LINE_RE = re.compile(r"^\s*- `(test_[^`]+)`: (PASS|FAIL|TIMEOUT)\b")
MEDIA_EXT = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".mp3", ".wav", ".ogg")


class FatalError(Exception):
    """Something that makes any output untrustworthy: stop before writing."""


class Ctx:
    """Run context: project root, the day being logged, the logger, and non-fatal input problems."""

    def __init__(self, root, day, log):
        self.root = root
        self.day = day
        self.log = log
        self.problems = []

    def path(self, *parts):
        return os.path.join(self.root, *parts)

    def problem(self, msg):
        self.problems.append(msg)
        self.log.warning(msg)


# ---------------------------------------------------------------- small helpers

def clip(text, n):
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= n else text[:n - 1] + "…"


def cell(text, n=80):
    return clip(text, n).replace("|", "/")


def read_text(path):
    with open(path, encoding="utf-8") as f:   # strict decoding: a broken file is reported, not silently patched
        return f.read()


def file_date(path):
    return dt.date.fromtimestamp(os.path.getmtime(path))


def guarded(ctx, name, fn, default):
    """Run one input collector. Expected I/O and format errors become a recorded problem; bugs still propagate."""
    try:
        return fn()
    except (OSError, ValueError, subprocess.SubprocessError) as e:   # JSONDecodeError and UnicodeDecodeError are ValueErrors
        ctx.problem("%s: %s: %s" % (name, type(e).__name__, e))
        return default


def split_row(line):
    s = line.strip()
    if not s.startswith("|"):
        return None
    s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def has_date(text, day):
    return re.search(r"(?<![\d-])%s(?!\d)" % re.escape(day.isoformat()), text) is not None


# ---------------------------------------------------------------- owner log

def parse_log_row(line):
    """Parse one markdown table row of the owner log. Returns None for non-rows, headers and separators."""
    cells = split_row(line)
    if not cells or not any(cells) or all(_SEP.match(c) for c in cells) or cells[0].lower() == "topic":
        return None
    topic = cells[0]
    if len(cells) == 1:
        said, status = "", ""
    elif len(cells) == 2:
        said, status = "", cells[1]
    else:
        said, status = cells[1], " | ".join(cells[2:])
    return {"topic": topic, "said": said, "status": status, "raw": line.strip()}


def collect_owner_rows(ctx):
    text = read_text(ctx.path("docs", "owner_feedback_log.md"))
    rows = []
    for line in text.splitlines():
        row = parse_log_row(line)
        if row and has_date(row["raw"], ctx.day):
            rows.append(row)
    return rows


# ---------------------------------------------------------------- gap queue and progress table

def newest_gap_queue(root):
    best = None
    docs = os.path.join(root, "docs")
    try:
        names = os.listdir(docs)
    except OSError:
        return None
    for n in names:
        m = GAP_NAME.match(n)
        if m and (best is None or m.group(1) > best[0]):
            best = (m.group(1), os.path.join(docs, n))
    return best[1] if best else None


def normalize_status(text):
    clean = (text or "").replace("*", "")
    for key, words in STATUS_RULES:
        if any(w in clean for w in words):
            return key
    return "unknown"


def fingerprint(cells):
    return hashlib.sha1("|".join(cells).encode("utf-8")).hexdigest()[:8]


def _column(header, cells, names):
    for i, h in enumerate(header):
        if h in names and i < len(cells):
            return cells[i]
    return ""


def short_category(heading):
    text = re.sub(r"^#+\s*", "", heading).strip()
    text = re.sub(r"^[零一二三四五六七八九十0-9]+[、.．]\s*", "", text)
    return re.split(r"[（(]", text)[0].strip() or text


def parse_gap_queue(text):
    """Return one dict per gap id found in the tables whose header row starts with 'ID'."""
    rows = []
    category = ""
    header = None
    for line in text.splitlines():
        if line.startswith("#"):
            category = short_category(line)
            header = None
            continue
        cells = split_row(line)
        if cells is None:
            header = None
            continue
        if all(_SEP.match(c) for c in cells):
            continue
        if cells[0] == "ID":
            header = cells
            continue
        if header is None:
            continue
        m = ID_RE.match(cells[0])
        if not m:
            continue
        status_raw = _column(header, cells, ("狀態", "Status")).replace("*", "")
        rows.append({
            "id": m.group(1),
            "category": category,
            "gap": _column(header, cells, ("缺口", "項目", "Gap", "Item")),
            "prio": _column(header, cells, ("P",)),
            "role": _column(header, cells, ("負責", "Owner", "Role")) or "-",
            "status_raw": status_raw,
            "status": normalize_status(status_raw),
            "next": _column(header, cells, ("下一步", "Next")),
            "fp": fingerprint(cells),
        })
    return rows


def parse_previous_table(text):
    """Read the rows of an earlier PROGRESS_TABLE.md: {id: {fp, date, status}}. It is the state that carries last-change dates."""
    prev = {}
    in_rows = False
    for line in text.splitlines():
        if line.startswith("## "):
            in_rows = line.strip() == ROWS_HEADING
            continue
        if not in_rows:
            continue
        cells = split_row(line)
        if not cells or len(cells) < 9 or not ID_RE.match(cells[0]):
            continue
        try:
            when = dt.date.fromisoformat(cells[7])
        except ValueError:
            continue
        prev[cells[0]] = {"fp": cells[8], "date": when, "status": cells[5]}
    return prev


def assign_dates(rows, prev, source_date, today):
    """Set row['last_change']. A new or edited row gets the queue file's date (never later than today); an unchanged row keeps its old date.
    Returns the ids that were in the previous table but are gone now."""
    stamp = min(source_date, today)
    for r in rows:
        old = prev.get(r["id"])
        if old is None:
            r["last_change"] = stamp
        elif old["fp"] == r["fp"]:
            r["last_change"] = old["date"]
        else:
            r["last_change"] = max(old["date"], stamp)
    ids = {r["id"] for r in rows}
    return [i for i in prev if i not in ids]


def count_status(rows):
    """Return (categories in file order, {category: Counter}, Counter of all)."""
    order, per, total = [], {}, Counter()
    for r in rows:
        if r["category"] not in per:
            order.append(r["category"])
            per[r["category"]] = Counter()
        per[r["category"]][r["status"]] += 1
        total[r["status"]] += 1
    return order, per, total


def stale_rows(rows, day, days=STALE_DAYS):
    return [r for r in rows if (day - r["last_change"]).days >= days]


def build_progress_table(rows, day, source_name):
    order, per, total = count_status(rows)
    present = [s for s in STATUS_ORDER if total[s]]
    L = ["# Progress table", "",
         "Generated by scripts/daily_log.py for %s from docs/%s. Rewritten on every `--apply` run; the previous copy goes to docs/daily/backup/. Do not edit by hand." % (day.isoformat(), source_name),
         "Last change = the date the row's text first differed from the previous table, or the queue file's date for a new row. It is not a per-row edit history.", "",
         "## Status summary by category", "",
         "| Category | Total | " + " | ".join(present) + " |",
         "|---|---|" + "---|" * len(present)]
    for c in order:
        L.append("| %s | %d | %s |" % (cell(c, 40), sum(per[c].values()), " | ".join(str(per[c][s]) for s in present)))
    L.append("| **All** | %d | %s |" % (len(rows), " | ".join(str(total[s]) for s in present)))
    L += ["", ROWS_HEADING, "",
          "| ID | Category | Gap | P | Owner role | Status | Original status | Last change | Fingerprint |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            r["id"], cell(r["category"], 30), cell(r["gap"], 70), cell(r["prio"], 8), cell(r["role"], 30), r["status"],
            cell(r["status_raw"], 50), r["last_change"].isoformat(), r["fp"]))
    stale = stale_rows(rows, day)
    L += ["", "## Stale rows (not touched for %d days or more)" % STALE_DAYS, ""]
    if stale:
        for r in stale:
            L.append("- %s (last change %s, %d days, %s): %s" % (r["id"], r["last_change"].isoformat(), (day - r["last_change"]).days, r["status"], cell(r["gap"], 70)))
    else:
        L.append("None.")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- Kiro tasks (route logs and result files)

def parse_route_log(text):
    """Status of one kiro_route log: ok / failed / throttled / running (no end marker yet)."""
    status, model, first, last, last_result = "running", "", "", "", ""
    for line in text.splitlines():
        m = LOG_LINE_RE.match(line.strip())
        if not m:
            continue
        t, msg = m.groups()
        first = first or t
        last = t
        if msg.startswith("model "):
            mm = re.match(r"model (\S+) attempt", msg)
            if mm:
                model = mm.group(1)
            status = "running"
        elif msg.startswith("DONE with "):
            status, model = "ok", msg[len("DONE with "):].strip()
        elif msg.startswith("result "):
            parts = msg.split()
            last_result = parts[1] if len(parts) > 1 else ""
            if last_result == "throttled":
                status = "throttled"
            elif last_result in ("failed", "bad_model"):
                status = "failed"
        elif msg.startswith("ERROR every model"):
            status = "throttled" if last_result == "throttled" else "failed"
        elif msg.startswith("ERROR"):
            status = "failed"
    return {"status": status, "model": model, "first": first, "last": last}


def project_dirs(ctx):
    """The project root plus sibling worktrees named <project>_kiro*."""
    dirs = [(".", ctx.root)]
    parent, base = os.path.dirname(ctx.root), os.path.basename(ctx.root)
    try:
        for name in sorted(os.listdir(parent)):
            p = os.path.join(parent, name)
            if name.startswith(base + "_kiro") and os.path.isdir(p):
                dirs.append((name, p))
    except OSError as e:
        ctx.problem("cannot list %s for worktrees: %s" % (parent, e))
    return dirs


def collect_tasks(ctx):
    tasks = []
    for label, d in project_dirs(ctx):
        try:
            names = sorted(os.listdir(d))
        except OSError as e:
            ctx.problem("cannot list %s: %s" % (d, e))
            continue
        for name in names:
            if not ROUTE_LOG_RE.match(name):
                continue
            p = os.path.join(d, name)
            try:
                info = parse_route_log(read_text(p))
                when = file_date(p)
            except (OSError, ValueError) as e:
                ctx.problem("route log %s: %s" % (p, e))
                continue
            m = TASK_NUM_RE.search(name)
            info.update(name=name, label=label, number=int(m.group(1)) if m else None, date=when)
            tasks.append(info)
    tasks.sort(key=lambda t: (t["number"] if t["number"] is not None else -1, t["label"]))
    return tasks


def kiro_docs(ctx):
    """Every docs/kiro_NN_*.md in the project and the worktrees: (label, name, number, date)."""
    out = []
    for label, d in project_dirs(ctx):
        docs = os.path.join(d, "docs")
        try:
            names = sorted(os.listdir(docs))
        except OSError:
            continue   # a worktree without docs/ simply has no results
        for n in names:
            m = KIRO_DOC_RE.match(n)
            if not m:
                continue
            try:
                out.append((label, n, int(m.group(1)), file_date(os.path.join(docs, n))))
            except OSError:
                continue   # file vanished between listing and stat
    return out


def briefs_on(ctx):
    docs = ctx.path("docs")
    out = []
    for n in sorted(os.listdir(docs)):
        m = BRIEF_RE.match(n)
        if m and file_date(os.path.join(docs, n)) == ctx.day:
            out.append(int(m.group(1)))
    return sorted(out)


# ---------------------------------------------------------------- art and inventory

def assets_changed_on(ctx):
    base = ctx.path("assets")
    if not os.path.isdir(base):
        raise OSError("no assets/ folder")
    out = {}
    for dp, dn, fn in os.walk(base):
        dn[:] = sorted(d for d in dn if not d.startswith("."))
        for f in sorted(fn):
            if not f.lower().endswith(MEDIA_EXT):
                continue
            try:
                if file_date(os.path.join(dp, f)) == ctx.day:
                    out.setdefault(os.path.relpath(dp, ctx.root), []).append(f)
            except OSError:
                continue   # file vanished between listing and stat
    return out


def _regenerate_inventory(ctx):
    script = ctx.path("scripts", "make_asset_inventory.py")
    r = subprocess.run([sys.executable, "-B", script], cwd=ctx.root, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise ValueError("make_asset_inventory.py exit %d: %s" % (r.returncode, clip((r.stdout + r.stderr)[-300:], 200)))
    ctx.log.info("asset inventory regenerated")


def _load_inventory(ctx):
    with open(ctx.path("docs", "asset_inventory.json"), encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("asset_inventory.json is not a JSON object")
    return data


def read_inventory(ctx, regen):
    if regen:
        guarded(ctx, "asset inventory regeneration", lambda: _regenerate_inventory(ctx), None)   # on failure the old file is still read
    else:
        ctx.log.info("asset inventory not regenerated; reading the existing docs/asset_inventory.json")
    return guarded(ctx, "docs/asset_inventory.json", lambda: _load_inventory(ctx), None)


# ---------------------------------------------------------------- tests

def discover_tests(root):
    names = os.listdir(os.path.join(root, "scripts"))
    return sorted(n for n in names if n.startswith("test_") and n.endswith(".py") and n != "test_daily_log.py")


def run_one_test(root, name, timeout=TEST_TIMEOUT):
    start = time.time()
    try:
        p = subprocess.run([sys.executable, "-B", os.path.join("scripts", name)], cwd=root, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"name": name, "code": None, "seconds": round(time.time() - start, 1), "tail": "timeout after %d s" % timeout}
    lines = [x for x in ((p.stdout or "") + (p.stderr or "")).splitlines() if x.strip()]
    return {"name": name, "code": p.returncode, "seconds": round(time.time() - start, 1), "tail": lines[-1] if lines else ""}


def collect_tests(ctx, runner=run_one_test):
    """Run the test scripts one after the other (never in parallel: 16 GB machine)."""
    results = []
    for name in discover_tests(ctx.root):
        ctx.log.info("running %s", name)
        results.append(runner(ctx.root, name))
    return results


def fmt_test(t):
    verdict = "PASS" if t["code"] == 0 else ("TIMEOUT" if t["code"] is None else "FAIL")
    return "- `%s`: %s (exit %s, %s s) %s" % (t["name"], verdict, "-" if t["code"] is None else t["code"], t["seconds"], cell(t["tail"], 100))


def parse_test_lines(text):
    out, in_sec = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            in_sec = "Tests" in line
            continue
        if in_sec and TEST_LINE_RE.match(line):
            out.append(line.strip())
    return out


def carried_tests(ctx):
    """Newest earlier record of test results in docs/daily/ (this day's file first). Returns (file name, lines)."""
    daily = ctx.path("docs", "daily")
    if not os.path.isdir(daily):
        return "", []
    limit = ctx.day.strftime("%Y%m%d")
    names = sorted(n for n in os.listdir(daily) if DAILY_NAME.match(n) and n[:8] <= limit)
    for n in reversed(names):
        lines = parse_test_lines(read_text(os.path.join(daily, n)))
        if lines:
            return n, [l if "[from " in l else "%s [from %s]" % (l, n) for l in lines]
    return "", []


# ---------------------------------------------------------------- the day's log

def extract_summary(text):
    m = re.search(re.escape(SUMMARY_START) + r"\s*(.*?)\s*" + re.escape(SUMMARY_END), text or "", re.S)
    if not m:
        return None
    body = m.group(1).strip()
    return None if (not body or body == SUMMARY_PLACEHOLDER) else body


def summarize_inventory(inv):
    if not inv:
        return None
    mods = [m for m in inv.get("modules", []) if isinstance(m, dict)]
    art = [a for a in inv.get("open_art", []) if isinstance(a, dict)]
    totals = inv.get("totals") if isinstance(inv.get("totals"), dict) else {}
    return {"generated": inv.get("generated", "?"), "folders": totals.get("folders", "?"), "files": totals.get("files", "?"),
            "modules": mods, "open_art": art}


def open_risks(ctx, d):
    r = []
    for g in d["gap_rows"]:
        if g["prio"].startswith("P0") and g["status"] != "done":
            r.append("P0 not done: %s %s [%s]" % (g["id"], cell(g["gap"], 70), g["status_raw"] or g["status"]))
    for t in d["tasks"]:
        if t["status"] in ("failed", "throttled") and t["date"] == ctx.day:
            r.append("Kiro task %s (%s) %s on the last attempt (model %s)" % (t["number"], t["label"], t["status"], t["model"] or "?"))
        if t["status"] == "running" and t["date"] < ctx.day:
            r.append("Kiro task %s (%s): route log has no DONE or ERROR line, last written %s; the run may have died" % (t["number"], t["label"], t["date"].isoformat()))
    if d["tests"] is not None:
        for t in d["tests"]:
            if t["code"] != 0:
                r.append("Test failed: %s" % t["name"])
    elif not d["carried"][1]:
        r.append("No test result is recorded yet (tests are off by default; run with --run-tests)")
    inv = d["inventory"]
    if inv:
        unseen = [m.get("module", "?") for m in inv["modules"] if m.get("status") == "built_unseen"]
        if unseen:
            r.append("Built but not looked at on screen (asset inventory): " + "; ".join(unseen))
    if d["stale"]:
        r.append("%d gap rows untouched for %d days or more (see docs/PROGRESS_TABLE.md)" % (len(d["stale"]), STALE_DAYS))
    if d["problems"]:
        r.append("%d input problems during this run (section 8)" % len(d["problems"]))
    return r


def owner_decisions(d):
    out = []
    for g in d["gap_rows"]:
        if g["status"] == "waiting_owner":
            out.append("Gap %s waits for you: %s. Next: %s" % (g["id"], cell(g["gap"], 70), cell(g["next"], 70) or "-"))
    for o in d["owner_rows"]:
        if re.search(r"\bOPEN\b", o["raw"]):
            out.append("Owner log row marked OPEN: %s" % cell(o["topic"], 90))
    inv = d["inventory"]
    if inv:
        for a in inv["open_art"]:
            if a.get("status") == "waiting_owner":
                out.append("Art waits for you: %s (%s)" % (cell(str(a.get("item", "?")), 70), cell(str(a.get("route", "?")), 60)))
    return out


def build_daily(ctx, d):
    day = ctx.day.isoformat()
    L = ["# Daily log %s" % day, "", SUMMARY_START, d["summary"] or SUMMARY_PLACEHOLDER, SUMMARY_END, "",
         "Written by scripts/daily_log.py from the files named in each section. The block above is written by the daily-logger agent.", ""]

    L += ["## 1. Owner log rows dated %s (%d)" % (day, len(d["owner_rows"])), ""]
    if d["owner_rows"]:
        for o in d["owner_rows"]:
            L.append("- **%s**: %s Status: %s" % (cell(o["topic"], 80), cell(o["said"], 220), cell(o["status"], 180) or "-"))
    else:
        L.append("No row in docs/owner_feedback_log.md carries this date.")

    _, _, total = count_status(d["gap_rows"])
    touched = [g for g in d["gap_rows"] if g["last_change"] == ctx.day]
    L += ["", "## 2. Gap queue (docs/%s, %d rows)" % (d["gap_name"], len(d["gap_rows"])), "",
          "Status now: " + ", ".join("%s %d" % (s, total[s]) for s in STATUS_ORDER if total[s]) + ".",
          "Rows with last change %s: %d" % (day, len(touched)) + (" (no earlier table existed, so these are the baseline)." if not d["had_previous"] else ".")]
    for g in touched:
        L.append("- %s [%s] %s" % (g["id"], g["status"], cell(g["gap"], 70)))
    if d["removed"]:
        L.append("Ids in the previous table but not in the queue now: " + ", ".join(d["removed"]))

    L += ["", "## 3. Kiro tasks", ""]
    today_tasks = [t for t in d["tasks"] if t["date"] == ctx.day]
    if today_tasks:
        L += ["| Task | Where | Status | Model | Log times | Result files |", "|---|---|---|---|---|---|"]
        for t in today_tasks:
            files = ["%s (%s)" % (n if lab == "." else "%s:%s" % (lab, n), when.isoformat()) for lab, n, num, when in d["kiro_docs"] if num == t["number"]]
            L.append("| %s | %s | %s | %s | %s-%s | %s |" % (t["number"] if t["number"] is not None else t["name"], t["label"], t["status"],
                                                          t["model"] or "-", t["first"] or "?", t["last"] or "?", cell("; ".join(files), 160) or "none yet"))
    else:
        L.append("No route log was written on this date.")
    if d["briefs"]:
        L.append("Briefs written or edited today: " + ", ".join(str(n) for n in d["briefs"]))
    newest = sorted(d["kiro_docs"], key=lambda x: (x[3], x[2]), reverse=True)[:8]
    if newest:
        L += ["", "Newest result files by modification time:"]
        L += ["- %s (%s%s)" % (n, when.isoformat(), "" if lab == "." else ", " + lab) for lab, n, num, when in newest]

    L += ["", "## 4. Art generated", ""]
    changed = d["art_changed"]
    if changed is None:
        L.append("Could not scan assets/ (section 8).")
    elif changed:
        L.append("Picture and sound files under assets/ modified on %s: %d in %d folders." % (day, sum(len(v) for v in changed.values()), len(changed)))
        for folder in sorted(changed)[:20]:
            names = changed[folder]
            L.append("- %s: %s%s" % (folder, ", ".join(names[:6]), " (+%d more)" % (len(names) - 6) if len(names) > 6 else ""))
    else:
        L.append("No picture or sound file under assets/ was modified on %s." % day)
    inv = d["inventory"]
    if inv:
        by_art = Counter(a.get("status", "?") for a in inv["open_art"])
        L.append("Inventory (docs/asset_inventory.json, generated %s): %s files in %s folders. Open art: %s." % (
            inv["generated"], inv["files"], inv["folders"], ", ".join("%s %d" % kv for kv in sorted(by_art.items())) or "none"))
        for a in inv["open_art"]:
            if a.get("status") != "done":
                L.append("- %s [%s]: %s" % (cell(str(a.get("item", "?")), 70), a.get("status", "?"), cell(str(a.get("route", "?")), 80)))
    else:
        L.append("The asset inventory could not be read (section 8).")
    L.append("Pictures that exist only on Colab or Drive are not counted.")

    L += ["", "## 5. Tests", ""]
    if d["tests"] is not None:
        L.append("Run in this pass with --run-tests (one at a time; PASS means exit code 0):")
        L += [fmt_test(t) for t in d["tests"]] or ["- no scripts/test_*.py found"]
    else:
        L.append("Not run in this pass (`--run-tests` is off by default to protect the 16 GB machine).")
        src, lines = d["carried"]
        if lines:
            L.append("Last recorded results, not re-run (from docs/daily/%s):" % src)
            L += ["  " + l for l in lines]
        else:
            L.append("No earlier result is recorded in docs/daily/.")

    risks = open_risks(ctx, d)
    L += ["", "## 6. Open risks", ""] + (["- " + x for x in risks] or ["None found in the inputs."])
    decisions = owner_decisions(d)
    L += ["", "## 7. Owner decisions needed", ""] + (["- " + x for x in decisions] or ["None found in the inputs."])
    if d["problems"]:
        L += ["", "## 8. Input problems", ""] + ["- " + clip(p, 240) for p in d["problems"]]
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- orchestration

def generate(ctx, run_tests, regen):
    """Collect every input and build both files. Returns (daily_text, table_text, tests_failed)."""
    if not os.path.isdir(ctx.path("docs")):
        raise FatalError("no docs/ folder under %s" % ctx.root)
    gap_path = newest_gap_queue(ctx.root)
    if not gap_path:
        raise FatalError("no docs/GAP_QUEUE_YYYYMMDD.md found")
    try:
        gap_rows = parse_gap_queue(read_text(gap_path))
        source_date = file_date(gap_path)
    except (OSError, ValueError) as e:
        raise FatalError("cannot read %s: %s" % (gap_path, e))
    if not gap_rows:
        raise FatalError("no gap ids parsed from %s; refusing to overwrite the progress table" % gap_path)
    ids = [g["id"] for g in gap_rows]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        ctx.problem("gap id %s appears more than once in %s" % (dup, os.path.basename(gap_path)))

    table_path = ctx.path("docs", "PROGRESS_TABLE.md")
    prev_text = guarded(ctx, "docs/PROGRESS_TABLE.md", lambda: read_text(table_path), "") if os.path.exists(table_path) else ""
    prev = parse_previous_table(prev_text)
    removed = assign_dates(gap_rows, prev, source_date, ctx.day)

    day_path = ctx.path("docs", "daily", ctx.day.strftime("%Y%m%d") + ".md")
    old_day = guarded(ctx, day_path, lambda: read_text(day_path), "") if os.path.exists(day_path) else ""

    tests = guarded(ctx, "test scripts", lambda: collect_tests(ctx), []) if run_tests else None
    d = {
        "gap_rows": gap_rows, "gap_name": os.path.basename(gap_path), "had_previous": bool(prev), "removed": removed,
        "stale": stale_rows(gap_rows, ctx.day),
        "owner_rows": guarded(ctx, "docs/owner_feedback_log.md", lambda: collect_owner_rows(ctx), []),
        "tasks": guarded(ctx, "kiro route logs", lambda: collect_tasks(ctx), []),
        "kiro_docs": guarded(ctx, "docs/kiro_NN_*.md", lambda: kiro_docs(ctx), []),
        "briefs": guarded(ctx, "docs/kiro_task_NN.md", lambda: briefs_on(ctx), []),
        "art_changed": guarded(ctx, "assets scan", lambda: assets_changed_on(ctx), None),
        "inventory": summarize_inventory(read_inventory(ctx, regen)),
        "tests": tests,
        "carried": ("", []) if run_tests else guarded(ctx, "earlier test results", lambda: carried_tests(ctx), ("", [])),
        "summary": extract_summary(old_day),
        "problems": ctx.problems,
    }
    failed = bool(tests) and any(t["code"] != 0 for t in tests)
    return build_daily(ctx, d), build_progress_table(gap_rows, ctx.day, d["gap_name"]), failed


def write_atomic(path, text):
    folder = os.path.dirname(path)
    os.makedirs(folder, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=folder, prefix=".tmp_", suffix=".md")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def backup_file(path, backup_dir, stamp):
    os.makedirs(backup_dir, exist_ok=True)
    dest = os.path.join(backup_dir, "%s_%s" % (stamp, os.path.basename(path)))
    n = 1
    while os.path.exists(dest):
        n += 1
        dest = os.path.join(backup_dir, "%s_%d_%s" % (stamp, n, os.path.basename(path)))
    shutil.copy2(path, dest)
    return dest


def show_diff(rel, old, new, out):
    diff = list(difflib.unified_diff(old.splitlines(), new.splitlines(), fromfile=rel + (" (current)" if old else " (new file)"), tofile=rel + " (proposed)", lineterm=""))
    print("\n".join(diff) if diff else "%s: no change" % rel, file=out)


def write_outputs(ctx, outputs, apply, out):
    """outputs: [(path, new_text)]. Dry run prints diffs only. Apply backs up every existing file first, then writes."""
    stamp = time.strftime("%Y%m%d_%H%M%S")
    pending = []
    for path, new in outputs:
        rel = os.path.relpath(path, ctx.root)
        old = read_text(path) if os.path.exists(path) else None
        if not apply:
            show_diff(rel, old or "", new, out)
        elif old == new:
            ctx.log.info("%s unchanged; not rewritten", rel)
        else:
            pending.append((path, rel, old, new))
    if not apply:
        print("DRY RUN: nothing was written. Use --apply to write these files.", file=out)
        return
    for path, rel, old, _ in pending:
        if old is not None:
            ctx.log.info("backup %s", os.path.relpath(backup_file(path, ctx.path("docs", "daily", "backup"), stamp), ctx.root))
    for path, rel, _, new in pending:
        write_atomic(path, new)
        ctx.log.info("wrote %s", rel)


def make_logger(logfile):
    lg = logging.getLogger("daily_log")
    lg.setLevel(logging.INFO)
    lg.propagate = False
    for h in list(lg.handlers):
        lg.removeHandler(h)
        h.close()
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(fmt)
    lg.addHandler(sh)
    if logfile:   # only on --apply: a dry run must leave the disk untouched
        os.makedirs(os.path.dirname(logfile), exist_ok=True)
        fh = logging.FileHandler(logfile, encoding="utf-8")
        fh.setFormatter(fmt)
        lg.addHandler(fh)
    return lg


def parse_args(argv):
    ap = argparse.ArgumentParser(description="Write the daily log and the progress table (dry run by default).")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="print the diff, write nothing (default)")
    mode.add_argument("--apply", action="store_true", help="write docs/daily/YYYYMMDD.md and docs/PROGRESS_TABLE.md, with backups")
    ap.add_argument("--run-tests", action="store_true", help="also run scripts/test_*.py one at a time (off by default)")
    ap.add_argument("--no-regen", action="store_true", help="do not call scripts/make_asset_inventory.py on --apply")
    ap.add_argument("--date", type=dt.date.fromisoformat, default=None, help="day to log, YYYY-MM-DD (default: today)")
    ap.add_argument("--root", default=ROOT, help="project root (default: the folder above scripts/)")
    return ap.parse_args(argv)


def _run(ctx, args, out):
    day = ctx.day
    try:
        ctx.log.info("start day=%s mode=%s run_tests=%s", day.isoformat(), "apply" if args.apply else "dry-run", args.run_tests)
        daily_text, table_text, tests_failed = generate(ctx, args.run_tests, args.apply and not args.no_regen)
        outputs = [(ctx.path("docs", "daily", day.strftime("%Y%m%d") + ".md"), daily_text), (ctx.path("docs", "PROGRESS_TABLE.md"), table_text)]
        write_outputs(ctx, outputs, args.apply, out)
    except FatalError as e:
        ctx.log.error("fatal: %s", e)
        return EXIT_FATAL
    except OSError as e:
        ctx.log.error("cannot read or write a file: %s", e)
        return EXIT_FATAL
    except Exception:   # last layer: a bug must still end with a non-zero exit and a traceback in the run log
        ctx.log.error("unexpected error:\n%s", traceback.format_exc())
        return EXIT_FATAL
    if args.apply:
        print("DAILY_FILE=docs/daily/%s.md" % day.strftime("%Y%m%d"), file=out)
        print("PROGRESS_TABLE=docs/PROGRESS_TABLE.md", file=out)
    code = EXIT_TEST if tests_failed else (EXIT_INPUT if ctx.problems else EXIT_OK)
    ctx.log.info("done exit=%d problems=%d", code, len(ctx.problems))
    return code


def run(argv, out=None):
    out = out or sys.stdout
    args = parse_args(argv)   # argparse exits with 2 on bad arguments
    root = os.path.abspath(args.root)
    day = args.date or dt.date.today()
    try:
        log = make_logger(os.path.join(root, "docs", "daily", "daily_log.run.log") if args.apply else None)
    except OSError as e:
        print("ERROR cannot open the run log: %s" % e, file=sys.stderr)
        return EXIT_FATAL
    try:
        return _run(Ctx(root, day, log), args, out)
    finally:
        for h in list(log.handlers):   # release the run log file so callers can move or delete the folder
            h.close()
            log.removeHandler(h)


if __name__ == "__main__":
    sys.exit(run(sys.argv[1:]))
