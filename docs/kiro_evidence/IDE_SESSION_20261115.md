# IDE session notes, W2, 2026-11-15 (checked at 15:45 +0800 by `date`)
Written by Kiro. Everything below was read from files or command output in this session. Nothing was run in the IDE panels.

## Hooks in `.kiro/hooks` (files read)
| File | Event | Runs | Fires on save? |
|---|---|---|---|
| `test-engine-on-index-save.kiro.hook` | fileEdited `index.html` | `python3 -B scripts/test_mcp_game.py` | Yes by definition (enabled: true). Not seen firing. |
| `test-constants-sync-on-save.kiro.hook` | fileEdited `shared/constants.json`, `scripts/mcp_game_server.py` | `scripts/test_constants_sync.py` (file exists) | Yes by definition. Not seen firing. |
| `test-rig-on-save.kiro.hook` | fileEdited `js/rig.js`, `assets/rigs/*.json` | skips: `scripts/test_rig.js` is absent | No-op today. |
| `pk-checks.json` (3 hooks, trigger `PostFileSave`) | `index.html`; constants or engine; `the Kiro result files` | each appends to `docs/kiro_evidence/raw/hook_runs.log` | Unknown. Its schema differs from the `.kiro.hook` files. I cannot see which ones the IDE loads. |

## What `docs/kiro_evidence/raw/hook_runs.log` shows
13 "hook fired" lines: 1 labelled "manual dry run" (2026-11-09T15:50:11Z) and 12 "kiro result saved" (latest 2026-11-15T07:41:28Z). No line for an `index.html` save and none for constants or engine. I do not know which program fired the 12.

## Could not do
1. **Save `index.html` in the IDE.** I cannot press save in the editor, and I did not rewrite the file (one writer for `index.html`, no content change wanted). `raw/ide_hook_run.txt` is not created. Owner step: open `index.html` in the IDE, press Cmd+S, copy the hook output from the IDE and give it to the main line with the time. `test-engine-on-index-save.kiro.hook` writes no file, so its output exists only in the IDE.
2. **Call `get_public_state` from IDE chat.** No pumpkin-killer tool is in my tool list this session. `raw/ide_mcp_call.txt` is not created and I did not substitute a shell call. Likely cause (inference, not tested): this session's workspace is the empty `pumpkin-killer-kiroween` folder, while `.kiro/settings/mcp.json` with the `pumpkin-killer` server is in `~/Developer/pumpkin-killer`. `~/.kiro/settings/mcp.json` does not exist. Fix: open `~/Developer/pumpkin-killer` as the IDE workspace, check the MCP panel, then repeat.
3. **Powers panel.** I cannot see it. Facts from files: `~/.kiro/powers/installed.json` has `installedPowers: []`. `.kiro/powers/pumpkin-killer-seat/` holds `plugin.json`, `mcp.json` and `skills/play/SKILL.md`, and no `POWER.md`. I understand Kiro powers to be defined by a `POWER.md` (not verified here), so the folder may not be recognised as a power. Nothing was installed.

## Other
Only this file and `.kiro/specs/ultimates-v2/` were written. No GitHub action, no push.
