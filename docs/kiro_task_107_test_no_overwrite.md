# Kiro task 107 — a test must never overwrite a deliverable (found by the main line, 2026-11-15)

Evidence: `python3 -B scripts/test_agent_levels.py` regenerates `docs/ai_levels_sweep_20261115.md` with a tiny run (50 throws per level, 6 percent, 6 percent, 2 percent), so running the tests destroys the real sweep (400 throws per level, 11.2 / 29.2 / 52.2 percent). The main line had to rerun `python3 -B scripts/sweep_agent_levels.py` to restore it.

Do, saving after each:
1. In `scripts/test_agent_levels.py` make the test that checks "the table file is produced" write to a temporary file (`tempfile`) instead of `docs/ai_levels_sweep_20261115.md`; add an assertion that the real report file's bytes are the same before and after the whole test run (read it first, compare at the end).
2. Search every other test in `scripts/test_*.py` and `scripts/test_*.js` for writes to a path under `docs/`, `assets/`, `shared/`, `.kiro/` or `scripts/` that is not a temp folder (grep for `open(`, `write_text`, `writeFileSync`, `--out`, `.write(`); list each hit with file and line in the result. Fix only those that overwrite a tracked file; leave temp-folder writes alone.
3. Run `python3 -B scripts/test_agent_levels.py`, then `git status --short docs/ai_levels_sweep_20261115.md` (it must show no change from the test) and paste both outputs. If a shell call is refused, say so and do not invent output.

Touch only the test files you fix and `(not published)` (max 15 lines: hits found, files changed, commands with last output lines, what you did not run). No network, no git (reading `git status` is allowed).
