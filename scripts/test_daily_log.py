#!/usr/bin/env python3
"""Offline tests for scripts/daily_log.py. Everything runs on synthetic folders under a temp directory.
No network, no real project files, no scheduler. Run from the repo root: python3 -B scripts/test_daily_log.py"""
import contextlib
import datetime as dt
import io
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import daily_log as dl  # noqa: E402

DAY = dt.date(2026, 11, 10)

GAP_TEXT = """# Gap queue 2026-11-10

## 二、美術（art）
| ID | 缺口 | P | 負責 | 狀態 | 下一步 |
|---|---|---|---|---|---|
| A1 | wind ghost | P1 | Colab | 進行中（loading） | check |
| A2 | feet chain | P1 | Qwen | 等你貼 | paste |

## 三、流程與系統（flow）
| ID | 缺口 | P | 負責 | 狀態 | 下一步 |
|---|---|---|---|---|---|
| B1 | four vs four | P0 | Sonnet | **已定：要做** | plan |
| B7 | facing | P0? | 主線 | **待查** | check |

## 六、工具與流程
| ID | 項目 | 狀態 |
|---|---|---|
| E1 | route task | 待查／待收 |
| E4 | overview svg | 已做未看 |
"""

OWNER_TEXT = """# Owner feedback log
| Topic | Owner said | Status |
|---|---|---|
| Coffins (owner 2026-11-10: 'too small') | both purple | done |
| Old row (owner 2026-11-09) | something | done |
| Open thing | question from 2026-11-10 | OPEN: decide |
"""

INVENTORY = ('{"generated": "2026-11-10 09:00", "totals": {"folders": 1, "files": 2},'
             ' "modules": [{"module": "wall", "status": "built_unseen"}],'
             ' "open_art": [{"item": "portraits", "status": "waiting_owner", "route": "image2"}]}')


def touch(path, day=DAY):
    ts = dt.datetime(day.year, day.month, day.day, 12, 0).timestamp()
    os.utime(path, (ts, ts))


def put(base, rel, text, day=DAY):
    p = os.path.join(base, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    touch(p, day)
    return p


def make_project(parent):
    """Synthetic project <parent>/proj plus one worktree <parent>/proj_kiro1."""
    root = os.path.join(parent, "proj")
    put(root, "docs/GAP_QUEUE_20261109.md", GAP_TEXT.replace("wind ghost", "OLD wind ghost"), dt.date(2026, 11, 9))
    put(root, "docs/GAP_QUEUE_20261110.md", GAP_TEXT)
    put(root, "docs/owner_feedback_log.md", OWNER_TEXT)
    put(root, "docs/asset_inventory.json", INVENTORY)
    put(root, "docs/kiro_70_review_x.md", "review")
    put(root, "docs/kiro_task_80.md", "brief")
    put(root, "assets/units/a.png", "x")
    put(root, "assets/units/old.png", "x", dt.date(2026, 11, 1))
    put(root, "kiro_route_kiro_task_70.log", "19:00:00 model m attempt 1\n19:10:00 result ok (exit 0)\n19:10:00 DONE with m\n")
    put(root, "kiro_route_kiro_task_72.log",
        "10:00:00 model a attempt 1\n10:00:30 result throttled (exit 1)\n10:01:30 model a attempt 2\n"
        "10:02:00 result throttled (exit 1)\n10:02:00 ERROR every model in route 'design' failed\n")
    put(root, "kiro_route_kiro_task_73.log", "12:00:00 model c attempt 1\n")
    put(parent, "proj_kiro1/kiro_route_kiro_task_71.log",
        "11:00:00 model b attempt 1\n11:01:00 result failed (exit 1)\n11:01:00 ERROR every model in route 'design' failed\n")
    os.makedirs(os.path.join(root, "scripts"), exist_ok=True)
    return root


def invoke(args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stderr(err):
        code = dl.run(args, out)
    return code, out.getvalue(), err.getvalue()


def snapshot(base):
    files, dirs = {}, set()
    for dp, dn, fn in os.walk(base):
        dirs.update(os.path.join(dp, d) for d in dn)
        for f in fn:
            p = os.path.join(dp, f)
            files[p] = (os.path.getsize(p), os.path.getmtime(p))
    return files, dirs


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class ParsingTests(unittest.TestCase):
    def test_parse_log_row_three_cells(self):
        r = dl.parse_log_row("| Coffins (owner 2026-11-10) | both purple | done: seen |")
        self.assertEqual(r["topic"], "Coffins (owner 2026-11-10)")
        self.assertEqual(r["said"], "both purple")
        self.assertEqual(r["status"], "done: seen")

    def test_parse_log_row_two_cells_and_skipped_lines(self):
        r = dl.parse_log_row("| Kiro 64 scripts copied | scripts/ |")
        self.assertEqual((r["topic"], r["said"], r["status"]), ("Kiro 64 scripts copied", "", "scripts/"))
        for line in ("| Topic | Owner said | Status |", "|---|---|---|", "plain text", "", "| |"):
            self.assertIsNone(dl.parse_log_row(line), line)

    def test_date_filter(self):
        self.assertTrue(dl.has_date("owner 2026-11-10: x", DAY))
        self.assertFalse(dl.has_date("owner 2026-11-09: x", DAY))
        self.assertFalse(dl.has_date("build 2026-11-101", DAY))
        self.assertFalse(dl.has_date("v12026-11-10", DAY))

    def test_gap_ids_columns_and_categories(self):
        rows = dl.parse_gap_queue(GAP_TEXT)
        self.assertEqual([r["id"] for r in rows], ["A1", "A2", "B1", "B7", "E1", "E4"])
        a1 = rows[0]
        self.assertEqual((a1["category"], a1["role"], a1["prio"], a1["status"]), ("美術", "Colab", "P1", "in_progress"))
        self.assertEqual(rows[2]["status"], "decided")
        self.assertEqual(rows[3]["prio"], "P0?")
        self.assertEqual(rows[4]["role"], "-")          # the 3-column table has no owner column
        self.assertEqual(rows[4]["category"], "工具與流程")
        self.assertEqual(len({r["fp"] for r in rows}), 6)

    def test_gap_parser_ignores_other_tables(self):
        text = "| Topic | Said |\n|---|---|\n| A1 | not a gap table |\n"
        self.assertEqual(dl.parse_gap_queue(text), [])

    def test_normalize_status(self):
        cases = {"進行中（x）": "in_progress", "等你貼": "waiting_owner", "等出圖": "waiting_other", "待查": "to_verify",
                 "待做": "todo", "未開始": "not_started", "已做未看": "built_unseen", "已排進任務檔，未跑": "queued",
                 "**已定：要做**；Kiro": "decided", "已完成（看過）": "done", "持續": "ongoing", "": "unknown", "???": "unknown"}
        for text, want in cases.items():
            self.assertEqual(dl.normalize_status(text), want, text)

    def test_status_counting(self):
        order, per, total = dl.count_status(dl.parse_gap_queue(GAP_TEXT))
        self.assertEqual(order, ["美術", "流程與系統", "工具與流程"])
        self.assertEqual(per["美術"]["in_progress"], 1)
        self.assertEqual(per["美術"]["waiting_owner"], 1)
        self.assertEqual(sum(total.values()), 6)
        self.assertEqual(total["to_verify"], 2)

    def test_route_log_states(self):
        ok = dl.parse_route_log("19:00:00 model m attempt 1\n19:10:00 result ok (exit 0)\n19:10:00 DONE with m\n")
        self.assertEqual((ok["status"], ok["model"], ok["first"], ok["last"]), ("ok", "m", "19:00:00", "19:10:00"))
        retry = dl.parse_route_log("1:00:00 junk\n10:00:00 model a attempt 1\n10:00:30 result throttled (exit 1)\n10:01:30 model a attempt 2\n10:02:00 result ok (exit 0)\n10:02:00 DONE with a\n")
        self.assertEqual(retry["status"], "ok")
        waiting = dl.parse_route_log("10:00:00 model a attempt 1\n10:00:30 result throttled (exit 1)\n")
        self.assertEqual(waiting["status"], "throttled")
        failed = dl.parse_route_log("10:00:00 model a attempt 1\n10:00:30 result ok (exit 0)\n10:00:30 ERROR exit 0 but expected file is missing: x\n10:00:30 ERROR every model in route 'design' failed\n")
        self.assertEqual(failed["status"], "failed")
        self.assertEqual(dl.parse_route_log("12:00:00 model c attempt 1\n")["status"], "running")
        self.assertEqual(dl.parse_route_log("")["status"], "running")

    def test_dates_stale_and_table_roundtrip(self):
        rows = dl.parse_gap_queue(GAP_TEXT)
        prev = {"A1": {"fp": rows[0]["fp"], "date": dt.date(2026, 11, 1)},        # unchanged: keeps the old date
                "B1": {"fp": "deadbeef", "date": dt.date(2026, 11, 2)},           # edited: gets the file date
                "X9": {"fp": "00000000", "date": dt.date(2026, 11, 2)}}           # gone from the queue
        removed = dl.assign_dates(rows, prev, DAY, DAY)
        by_id = {r["id"]: r for r in rows}
        self.assertEqual(by_id["A1"]["last_change"], dt.date(2026, 11, 1))
        self.assertEqual(by_id["B1"]["last_change"], DAY)
        self.assertEqual(by_id["A2"]["last_change"], DAY)
        self.assertEqual(removed, ["X9"])
        self.assertEqual([r["id"] for r in dl.stale_rows(rows, DAY)], ["A1"])
        again = dl.parse_previous_table(dl.build_progress_table(rows, DAY, "GAP_QUEUE_20261110.md"))
        self.assertEqual(set(again), set(by_id))
        self.assertEqual(again["A1"]["date"], dt.date(2026, 11, 1))
        self.assertEqual(again["A1"]["fp"], rows[0]["fp"])

    def test_test_lines_carry_over(self):
        text = "# x\n## 5. Tests\n- `test_a.py`: PASS (exit 0, 1.0 s) ok\n- `test_b.py`: FAIL (exit 1, 2 s) bad\n  - `test_c.py`: TIMEOUT (exit -, 9 s) t\n## 6. Open risks\n- `test_z.py`: PASS\n"
        self.assertEqual([l.split("`")[1] for l in dl.parse_test_lines(text)], ["test_a.py", "test_b.py", "test_c.py"])

    def test_fake_test_runner_and_format(self):
        tmp = tempfile.mkdtemp()
        try:
            root = make_project(tmp)
            put(root, "scripts/test_one.py", "")
            put(root, "scripts/test_two.py", "")
            put(root, "scripts/test_daily_log.py", "")      # must be skipped: it would recurse
            put(root, "scripts/other.py", "")
            seen = []

            def fake(r, name):
                seen.append(name)
                return {"name": name, "code": 0 if name == "test_one.py" else 1, "seconds": 0.5, "tail": "done"}
            ctx = dl.Ctx(root, DAY, dl.make_logger(None))
            results = dl.collect_tests(ctx, runner=fake)
            self.assertEqual(seen, ["test_one.py", "test_two.py"])
            self.assertIn("PASS", dl.fmt_test(results[0]))
            self.assertIn("FAIL", dl.fmt_test(results[1]))
            self.assertIn("TIMEOUT", dl.fmt_test({"name": "t.py", "code": None, "seconds": 1, "tail": ""}))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class RunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.root = make_project(self.tmp)
        self.args = ["--root", self.root, "--date", "2026-11-10", "--no-regen"]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def table_path(self):
        return os.path.join(self.root, "docs", "PROGRESS_TABLE.md")

    def day_path(self):
        return os.path.join(self.root, "docs", "daily", "20261110.md")

    def test_dry_run_is_the_default_and_writes_nothing(self):
        before = snapshot(self.tmp)
        code, out, err = invoke(self.args)
        self.assertEqual(code, 0, err)
        self.assertEqual(snapshot(self.tmp), before)
        self.assertIn("DRY RUN", out)
        self.assertIn("+++ docs/PROGRESS_TABLE.md (proposed)", out)
        self.assertIn("+++ docs/daily/20261110.md (proposed)", out)
        self.assertFalse(os.path.exists(os.path.join(self.root, "docs", "daily")))

    def test_explicit_dry_run_flag_also_writes_nothing(self):
        before = snapshot(self.tmp)
        code, _, err = invoke(self.args + ["--dry-run"])
        self.assertEqual(code, 0, err)
        self.assertEqual(snapshot(self.tmp), before)

    def test_apply_writes_both_files_run_log_and_backup(self):
        put(self.root, "docs/PROGRESS_TABLE.md", "old table\n")
        code, out, err = invoke(self.args + ["--apply"])
        self.assertEqual(code, 0, err)
        self.assertIn("DAILY_FILE=docs/daily/20261110.md", out)
        table, day = read(self.table_path()), read(self.day_path())
        self.assertIn("| A1 | 美術 | wind ghost | P1 | Colab | in_progress |", table)
        self.assertIn("| **All** | 6 |", table)
        self.assertNotIn("OLD wind ghost", table)               # only the newest queue is read
        backups = os.listdir(os.path.join(self.root, "docs", "daily", "backup"))
        self.assertEqual(len(backups), 1)
        self.assertTrue(backups[0].endswith("_PROGRESS_TABLE.md"))
        self.assertEqual(read(os.path.join(self.root, "docs", "daily", "backup", backups[0])), "old table\n")
        self.assertTrue(os.path.getsize(os.path.join(self.root, "docs", "daily", "daily_log.run.log")) > 0)
        self.assertIn("Owner log rows dated 2026-11-10 (2)", day)
        self.assertIn("Coffins", day)
        self.assertNotIn("Old row", day)
        self.assertIn("| 70 | . | ok | m |", day)
        self.assertIn("| 71 | proj_kiro1 | failed |", day)
        self.assertIn("| 72 | . | throttled |", day)
        self.assertIn("| 73 | . | running |", day)
        self.assertIn("kiro_70_review_x.md", day)
        self.assertIn("Briefs written or edited today: 80", day)
        self.assertIn("a.png", day)
        self.assertNotIn("old.png", day)
        self.assertIn("Gap A2 waits for you", day)
        self.assertIn("Owner log row marked OPEN: Open thing", day)
        self.assertIn("Art waits for you: portraits", day)
        self.assertIn("wall", day)                              # built but not looked at
        self.assertIn("Not run in this pass", day)

    def test_unchanged_table_is_not_rewritten_or_backed_up_again(self):
        put(self.root, "docs/PROGRESS_TABLE.md", "old table\n")
        self.assertEqual(invoke(self.args + ["--apply"])[0], 0)
        first = read(self.table_path())
        self.assertEqual(invoke(self.args + ["--apply"])[0], 0)
        self.assertEqual(read(self.table_path()), first)
        table_backups = [n for n in os.listdir(os.path.join(self.root, "docs", "daily", "backup")) if n.endswith("PROGRESS_TABLE.md")]
        self.assertEqual(len(table_backups), 1)

    def test_summary_block_survives_a_rewrite(self):
        self.assertEqual(invoke(self.args + ["--apply"])[0], 0)
        day = read(self.day_path())
        self.assertIn(dl.SUMMARY_PLACEHOLDER, day)
        with open(self.day_path(), "w", encoding="utf-8") as f:
            f.write(day.replace(dl.SUMMARY_PLACEHOLDER, "ten lines by the agent"))
        put(self.root, "docs/owner_feedback_log.md", OWNER_TEXT + "| Extra (owner 2026-11-10) | more | done |\n")
        self.assertEqual(invoke(self.args + ["--apply"])[0], 0)
        again = read(self.day_path())
        self.assertIn("ten lines by the agent", again)
        self.assertNotIn(dl.SUMMARY_PLACEHOLDER, again)
        self.assertIn("(3)", again)                             # the rest was regenerated

    def test_stale_rows_listed_after_three_days(self):
        rows = dl.parse_gap_queue(GAP_TEXT)
        dl.assign_dates(rows, {}, DAY, DAY)
        rows[0]["last_change"] = dt.date(2026, 11, 6)           # 4 days old, text unchanged
        put(self.root, "docs/PROGRESS_TABLE.md", dl.build_progress_table(rows, DAY, "GAP_QUEUE_20261110.md"))
        self.assertEqual(invoke(self.args + ["--apply"])[0], 0)
        table = read(self.table_path())
        stale = table.split("## Stale rows", 1)[1]
        self.assertIn("- A1 (last change 2026-11-06, 4 days", stale)
        self.assertNotIn("- A2 ", stale)

    def test_missing_gap_queue_is_fatal_and_writes_no_output(self):
        os.remove(os.path.join(self.root, "docs", "GAP_QUEUE_20261109.md"))
        os.remove(os.path.join(self.root, "docs", "GAP_QUEUE_20261110.md"))
        code, _, err = invoke(self.args + ["--apply"])
        self.assertEqual(code, 1)
        self.assertIn("GAP_QUEUE", err)
        self.assertFalse(os.path.exists(self.table_path()))
        self.assertFalse(os.path.exists(self.day_path()))

    def test_gap_queue_without_rows_keeps_the_old_table(self):
        put(self.root, "docs/GAP_QUEUE_20261110.md", "# empty\nnothing here\n")
        put(self.root, "docs/PROGRESS_TABLE.md", "precious\n")
        code, _, _ = invoke(self.args + ["--apply"])
        self.assertEqual(code, 1)
        self.assertEqual(read(self.table_path()), "precious\n")

    def test_unreadable_input_still_writes_but_exits_nonzero(self):
        os.remove(os.path.join(self.root, "docs", "owner_feedback_log.md"))
        code, _, _ = invoke(self.args + ["--apply"])
        self.assertEqual(code, 3)
        self.assertIn("## 8. Input problems", read(self.day_path()))
        self.assertTrue(os.path.exists(self.table_path()))

    def test_bad_arguments_exit_2(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as cm:
                dl.run(["--apply", "--dry-run"], io.StringIO())
        self.assertEqual(cm.exception.code, 2)

    def test_earlier_test_results_are_carried_not_rerun(self):
        put(self.root, "docs/daily/20261109.md", "# old\n## 5. Tests\n- `test_a.py`: PASS (exit 0, 1.0 s) ok\n## 6. Open risks\n", dt.date(2026, 11, 9))
        code, out, err = invoke(self.args)
        self.assertEqual(code, 0, err)
        self.assertIn("[from 20261109.md]", out)
        self.assertIn("not re-run", out)


if __name__ == "__main__":
    unittest.main()
