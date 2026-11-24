# Crew audit of docs/KIRO_USAGE_20261116.md (2026-11-16)

Surface: Kiro Crew, running through ACP (agent "kirocrew", model chosen automatically). Read-only audit; only this file was written. `git status` shows the usage doc is modified and uncommitted, so I audited the working copy.

| Claim | Where checked | Verdict | Evidence |
|---|---|---|---|
| CLI: `scripts/kiro_route.py` routes briefs to Kiro CLI | `ls scripts/kiro_route.py` | supported | file exists |
| Route log of task 173 shows a completed task | `tail kiro_route_kiro_task_173_determinism.log` | supported | last line `03:34:53 DONE with gpt-5.6-terra` |
| `docs/KIRO_LEDGER.md` records results and verification | `head docs/KIRO_LEDGER.md` | supported | table has a "main-line verification" column, 70 rows |
| IDE: one save ran the engine-test hook, with approval | `docs/kiro_evidence/raw/ide_hook_run_20261115.txt` | supported | "asked for approval ... After the owner-requested approval ... Random Assignment Passed!" |
| IDE hook was "the predecessor" of `test-engine-on-index-save` | same file; `git log` | supported | IDE ran `(not published)`; current file is `.json` (commit e72efade) |
| IDE MCP call failed (no tool in session) | `ide_mcp_attempt_20261115.txt` | supported | "NO successful MCP call from the IDE yet" |
| Kiro Web not used | `grep -ril "kiro web" docs` not run in depth; no Web evidence in `docs/kiro_evidence/` | cannot tell | absence only; say "no record", not "not used" |
| **Kiro Crew: not used. No `docs/crew_*_result.md` exists** | `ls docs/crew_*` | **not supported** | `(not published)`, `(not published)` exist (C4 re-ran Kiro 185/188 tests); this file is a third |
| Specs under `.kiro/specs/` incl. shared-constants, particles, mcp-standard, balance-sim, physics-pbt, i18n, ultimates-v2, ui-polish | `ls .kiro/specs` | supported | all 8 names listed (32 spec folders total) |
| Task 173 needed golden file + both runtime tests | `docs/kiro_task_173_determinism.md` line 15 | supported | names `shared/determinism_golden.json`, `test_determinism.js`, `test_determinism_golden.py` |
| Those tests exist; commit `a835958` added it | `ls`; `git show -s a835958` | supported | `a8359588 Determinism contract (Kiro 173, verified) ...` |
| Main line rejected 170 rewrite (18 tests); copy in `(not published)`; commit `0011b1f` | git, ls, DEV_LOG line 62 | supported | `0011b1fc ... dropped 18 tests; a copy stays untracked under (not published)` |
| Task 181 called poison page-equivalent but lethal | `docs/kiro_181_result.md` lines 8-9 | supported | "lethal two-turn poison ... page-equivalent" |
| DEV_LOG recorded the mismatch; 187 restored 1 HP floor | `DEV_LOG` line 73; `kiro_187_result.md` line 6 | supported | "cannot reduce a living target below 1 HP" |
| Steering has product, rules, tech, structure, assignment, team-plan, progress, art, UI | `ls .kiro/steering` | supported | 11 files; extra: `prompt_engineering.md`, `ui_settings.md` |
| `structure.md` makes `index.html` one-writer | not opened in this audit | cannot tell | open `.kiro/steering/structure.md` to confirm |
| 8 custom agents with listed names | `ls .kiro/agents` | supported | exactly the 8 names |
| `pk-player` is MCP-only | `.kiro/agents/pk-player.json` | supported | `"tools": ["@mcp"]`, "no shell, no file access, no web" |
| 162 records one main-line-verified match | `docs/kiro_162_result_gpt-5.6-terra.md` | partly | file says "re-checked by the main line": 364 entries, 68 accepted. But `kiro_route_kiro_task_162_play_via_mcp.log` ends `ERROR every model in route 'gpt' failed`, and `docs/kiro_verified.json` has no 162 entry |
| "All current hooks use PostFileSave" | `.kiro/hooks/*.json` | supported | 7 files, all `"trigger": "PostFileSave"` (doc lists 7 hooks) |
| Preload hook: only a manual dry run, no save-triggered run | `docs/kiro_evidence/raw/hook_runs.log` | **not supported** | log has 458 lines `hook fired: index.html saved`, e.g. line 7400 then `OK preload block is up to date (20 links)`. The trigger program is unknown, but the log does not support "no save-triggered run" |
| Same dry run reported a stale block | `hook_runs.log` line 1-2 | supported | `STALE preload block: would write 22 links` |
| `test-rig-on-save` is a no-op, `(not published)` missing | `ls (not published)` | supported | "No such file or directory" |
| No recorded catch for constants/orientation hooks | `grep` on hook_runs.log | cannot tell | not searched line by line (log is about 7,400 lines) |
| MCP server has six tools | `grep scripts/mcp_stdio_server.py` | supported | lines 352-358 map all six |
| `.kiro/settings/mcp.json` configures white seat | `cat` | supported | `"--seat", "white"` |
| Power `pumpkin-killer-seat/plugin.json` exists | `ls (not published)` | supported | `mcp.json plugin.json skills` |
| Seeded test has six properties | `scripts/test_properties.js` lines 285-290 | supported | `properties` array; run output "4 of 6" in 179 |
| 2,016 balance matches | `test_properties.js` lines 21, 270-273 | supported | `CASES = 2000`; 36 pairings x ceil(2000/36)=56 = 2016 (not run) |
| Task 179: four failures | `kiro_179_result.md` line 25 | supported | "4 of 6 properties FAILED" |
| Current runner passes all six | `kiro_181_result.md` | cannot tell | I did not run it (host memory tight); owner should run `node scripts/test_properties.js` |
| Flight test: 66 goldens, 500 cases, 30 page cases | `scripts/test_flight_golden.js` line 84 | supported | `PASS: 66 flight goldens, 500 Python/JS cases, 30 page parity cases` (message text, not run) |
| Round hash: 20 goldens | `scripts/test_round_hash.js` line 19 | supported | `PASS: 20 round-hash goldens` (message text, not run) |
| Golden file covers wind, starts, dice, drops, bounces, nun, coin | `shared/determinism_golden.json` | partly | 8 vector groups, 1,092 values; coin toss not checked by name |
| `balance_matrix_20261116.md`, `ASSET_PROVENANCE.md` exist; Qwen-Image-Edit on Colab | `ls`; ASSET_PROVENANCE lines 8-14 | supported | "Qwen-Image-Edit-2509"; licence "unknown - owner to confirm" |
| "Kiro CLI route logs identify the models used" | route logs | supported | e.g. `model gpt-5.6-terra attempt 1` |
| Who wrote what: Kiro wrote briefs, specs, tests; main line wired pages | `git shortlog -sn` | cannot tell | 321 commits, one author (`<owner> sun`), so git cannot separate people from agents. Rely on `kiro_verified.json` and DEV_LOG only |

## Delete or soften
1. Delete "Kiro Crew: not used". Say Crew ran independent checks (C3 wind test, C4 re-run of Kiro 185/188) and this audit.
2. Soften "Kiro Web: not used" to "no repository record of a Web session".
3. Soften the preload hook line: the log holds many `index.html saved` entries with `OK preload block is up to date`; the trigger is unknown.
4. Soften "main-line verified match" for 162: add that the route log failed and `kiro_verified.json` has no 162 row, or add the row after a re-run.
5. Do not use git authorship to show who wrote what; the history has one author.

## Not covered that the official page asks for
- Differences between IDE, CLI, Web and Crew, in one short table (what each did here).
- Spec-driven against ad-hoc coding: only one example (173). Add one before/after, e.g. a spec task against the first ad-hoc fix.
- Property-based testing: named, but state the seed and number of cases per property, and that the 4 failures were fixed.
- Agent hooks: say that the IDE and CLI load different hook files (IDE ignored `pk-checks.json`).
- MCP and third-party tools: covered; add that the IDE MCP link is still not working.
- Custom agents: only `pk-player` has a recorded run; say so for the other seven (already stated, keep it).
