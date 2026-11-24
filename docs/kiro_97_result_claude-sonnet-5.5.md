# Kiro 97 result (claude-sonnet-5.5)

## What changed
- NEW `docs/kiro_97_ide_config_findings_claude-sonnet-5.5.md`: causes for the empty IDE MCP panel and the greyed `pk-checks.json` hooks. Each statement is marked [doc] with file and line, or [guess].
- NEW this file.
- NO change to `.kiro/settings/mcp.json`, to the three `.kiro.hook` files or to `pk-checks.json`. No backup folder `(not published)` was created, because nothing was altered.

## Why no conversion
No local doc says what format the IDE's "Migrate" button writes (`(not published)` lines 35-36 describe only the old `.kiro.hook` format and the v1 JSON format). The brief says to write the open question and stop. The questions are at the end of the findings file. The most useful one: click Migrate on one hook in the IDE and keep the file it writes. The second: read the IDE's Output tab "Kiro - MCP Logs" after a restart.

## Commands
- `python3 -B scripts/test_mcp_stdio.py` and `python3 -B scripts/test_mcp_game.py`: NOT RUN. The shell tool returned "The permission request failed before it was answered" twice (exit -1), so no output exists to quote. Both are required only after a change, and no tracked file was changed. Please re-run them yourself if you want a fresh baseline.

## Not verified
- Every [guess] in the findings file, including the relative-path/working-directory theory for the IDE MCP launch.
- That the IDE or CLI loads `.kiro/powers/pumpkin-killer-seat/` or `pk-checks.json`.
- I read no screenshots (.jpg), only the two text evidence notes.
