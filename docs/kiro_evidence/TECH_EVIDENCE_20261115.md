# Kiro evidence page (Technological Implementation), 2026-11-15

Written by Kiro for judges. Numbers below are the output of one command, `python3 -B scripts/release/tech_evidence_counts.py`, which only reads files. Brief, result and box counts grow while work continues; the other counts are stable. Statuses use four words: done, partly, not done, not used. `docs/kiro_verified.json` is the main line's own record of what it re-ran; a Kiro report never counts as proof.

## Strategy in one paragraph
Work is cut into one brief per task. A router (`scripts/kiro_route.py`) runs Kiro CLI on a brief, a result file comes back, and a ledger row (`docs/KIRO_LEDGER.md`) records it. The main line (a Claude Code session) re-runs the checks and writes only what it saw into `docs/kiro_verified.json`. Larger modules start from a spec (requirements, design, tasks) so the order and the proof are visible. Steering files carry the confirmed rules into every session. Hooks and a stdio MCP server connect Kiro to the game checks. Tests include seeded property loops. The experiments with art prompts are logged in `docs/PROMPT_LOG.md`.

## The numbers (output of the command, 2026-11-15)
```
ledger entries=38 not_checked=1 partly=22 read_only=3 verified=12
specs folders=26 with_requirements_design_tasks=25 boxes_ticked=158 boxes_open=250
specs incomplete folder=core-throw-loop requirements/design/tasks=[True, False, False]
hooks json_files=6 hooks=6 triggers: PostFileSave=6 old_format_kiro_hook_files=0
steering files=8 inclusion_always=6 (kiro_assignment.md, progress_snapshot.md, rules.md, structure.md, team_plan.md, tech.md)
agents files=7 names=asset-inventory,builder,committer,daily-logger,researcher,rules-reviewer,tester attach_mcp_server=0
powers folders=1 names=pumpkin-killer-seat
mcp servers=1 names=pumpkin-killer tool_names_found_in_server_file=6
briefs task_files=128 result_files=52
evidence files_present=12 of 12
```

## What each Kiro feature did, and its status
| Kiro feature | Used for | Evidence | Status |
|---|---|---|---|
| Kiro CLI | Most modules, tests and drafts, one brief per task, with a ledger row each | `scripts/kiro_route.py`, `docs/KIRO_LEDGER.md`, `docs/kiro_verified.json` | done (12 ledger entries verified by the main line, 22 partly) |
| Kiro IDE | One hook run, one failed MCP call, spec and draft writing on 2026-11-15 | `docs/kiro_evidence/raw/ide_hook_run_20261115.txt`, `docs/kiro_evidence/raw/ide_mcp_attempt_20261115.txt`, `docs/kiro_evidence/IDE_SESSION_20261115.md` | partly |
| Kiro Web | not used | no file | not used |
| Kiro Crew | not used | no file | not used |
| Specs | Module work and this submission's own gap list | `.kiro/specs/` (26 folders), `.kiro/specs/contest-gap-run/tasks.md` | partly (25 of 26 folders have all three files; 158 boxes ticked, 250 open) |
| Steering | Rules, tech facts, team plan and a progress snapshot loaded in every session | `.kiro/steering/` (8 files, 6 always loaded) | done (no saved session log shows the load) |
| Hooks | Run engine tests, constants checks, preload check and the ledger when files are saved | `.kiro/hooks/` (6 files), `docs/kiro_evidence/raw/ide_hook_run_20261115.txt` | partly (see "What did not work") |
| Custom agents | Seven roles: researcher, builder, tester, rules-reviewer, asset-inventory, daily-logger, committer | `.kiro/agents/` | partly (files exist; run output saved for none beyond the researcher's routed tasks) |
| MCP | A stdio server with six tools (public information only) that lets an agent take a seat | `.kiro/settings/mcp.json`, `scripts/mcp_stdio_server.py`, `docs/kiro_evidence/raw/mcp_health_20261115.log` | partly (CLI sees it, IDE call failed) |
| Property-based tests | Seeded loops for particles, ultimates, knight hidden points, hallucination status | `scripts/test_particles.js`, `scripts/test_ultimate.js`, `scripts/test_knight_ult.js`, `scripts/test_hallucination.js` | partly (none for the game rules or the engine) |
| Powers | `pumpkin-killer-seat` (join a match, play from the public view) | `.kiro/powers/pumpkin-killer-seat/plugin.json`, `docs/kiro_evidence/raw/powers_install_20261115.txt` | partly (installed by the CLI; activation from a chat not shown) |

## What did not work or is not proven
- **IDE MCP call.** Asked to call `get_public_state`, the IDE chat found no such tool, in two sessions. The CLI lists the same server from the same file. The cause is not known. (`docs/kiro_evidence/raw/ide_mcp_attempt_20261115.txt`, `docs/kiro_evidence/IDE_SESSION_20261115.md`)
- **Hook format.** The only hook run seen in the IDE came from an older `.kiro.hook` file. That file is not in `.kiro/hooks/` any more (`old_format_kiro_hook_files=0`). The six current files use a `PostFileSave` trigger with a path matcher, the same layout as a file the IDE did not seem to load on 2026-11-15. So the six are not shown firing in the IDE. Next step for the owner: save `index.html` in the IDE and save the output.
- **Hook log.** `docs/kiro_evidence/raw/hook_runs.log` shows commands that ran, not what triggered them.
- **False ticks.** `.kiro/specs/physics-pbt/tasks.md` ticks two files (js/physics.js and scripts/test_physics_props.js) that are not in the repository.
- **Ledger.** 22 of 38 entries say "partly"; they were copied into the main line and not fully checked.
- **Agents.** None of the seven attaches the MCP server, and the repository holds no run output for six of them.
- **Power.** The folder was installed by the CLI. No file shows it activating from its keywords.

## Experimentation
Art prompts were run as logged experiments with a verdict and a next change each (`docs/PROMPT_LOG.md`). The computer opponent has three scripted levels measured by a sweep (`docs/ai_levels_sweep_20261115.md`), and a learning check (`scripts/eval_agent_learning.py`) fails if an agent that learns only from public history does not improve.

## Reproduce
- `python3 -B scripts/release/tech_evidence_counts.py` prints the block above.
- `python3 -B scripts/make_kiro_ledger.py` rebuilds the ledger in check mode (writes nothing).
- `python3 -B scripts/test_mcp_stdio.py` and `python3 -B scripts/test_mcp_game.py` check the MCP server and engine.
- `python3 -B scripts/release/check_draft_paths.py docs/kiro_evidence/TECH_EVIDENCE_20261115.md` checks that every path on this page exists and is in the export.
