# Daily log and progress table: how to use it

Script: `scripts/daily_log.py` (Python 3, standard library only). Run everything from the repo root.

## Run by hand
- `python3 -B scripts/daily_log.py` is a dry run: it prints a diff for both files and writes nothing, not even the run log.
- `python3 -B scripts/daily_log.py --apply` writes the two files. Add `--date 2026-11-10` to log another day.
- `--run-tests` also runs every `scripts/test_*.py` (except its own test), one at a time. It is off by default because the machine has 16 GB.
- `--no-regen` skips the asset inventory regeneration on `--apply`.
- Exit codes: 0 ok, 1 fatal (nothing written), 2 bad arguments, 3 written but an input was unreadable, 4 written but a test failed.
- Unit tests: `python3 -B scripts/test_daily_log.py` (offline, synthetic folders).

## What `--apply` writes
- `(not published)`: owner log rows with that date, gap queue changes, Kiro tasks with status and result files, art files changed, tests, open risks, owner decisions needed, input problems.
- `docs/PROGRESS_TABLE.md`: one row per gap id with status, owner role and last change date, a status summary by category, and a stale list (3 days or more without a change).
- `(not published)`: the old copy of each file that is about to change. An identical file is not rewritten and not backed up.
- `(not published)`: the run log.
- It also calls `scripts/make_asset_inventory.py`, which rewrites `docs/asset_inventory.json` and `(not published)`.
- The 10-line summary between the `SUMMARY` markers at the top of the day file is written by the `daily-logger` agent. A later run keeps it.

## The agent
`.kiro/agents/daily-logger.json` runs `--apply` (never `--run-tests`), then writes the summary in Traditional Chinese. Example: `kiro-cli chat --agent daily-logger --no-interactive "Write today's daily log."`

## Scheduling later (description only)
The project has no scheduler. If the owner wants one, a user-level job (launchd on macOS, or cron) can run `cd <repo> && python3 -B scripts/daily_log.py --apply` once in the evening, then the agent command above. Nothing is installed, and the owner decides.

## What it deliberately does not do
- No network, no git, no push, no deploy, no cloud write.
- No tests unless `--run-tests`; no image generation; it never edits the gap queue, the owner log, rules or code.
- No judgement: statuses are keyword matches on the gap queue text, and a row's last change date is the day its text first differed, not an edit history.
- Route logs carry only a time of day, so a log counts for the day of its last write. A log with no DONE or ERROR line shows as `running`.
- It does not see pictures that exist only on Colab or Drive.
