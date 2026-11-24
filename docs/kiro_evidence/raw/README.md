# Raw evidence (real outputs, not summaries)
- hook_runs.log: appended by the v1 hooks in .kiro/hooks/pk-checks.json every time one fires (UTC time, which hook, the command output). If this file stays empty after a Kiro CLI session saved index.html, the CLI did not load the hook file: record that fact in docs/kiro_evidence/<date>.md.
- Test runs: docs/kiro_evidence/<date>_tests.md from `python3 -B scripts/end_of_day.py --apply`.
- Put here later: rules-reviewer and asset-inventory outputs, an MCP session transcript, `git worktree list`.
