# How Kiro was used in Pumpkin Killer

This is an evidence record for judges. It names repository files and separates
recorded use from configuration that has no recorded run.

## Update (2026-11-26 — pre-freeze addendum)

The inventory below was first measured on 2026-11-16 (`333` commits, `103` test files). Between 2026-11-17 and 2026-11-26 the repository grew to **524+ non-merge commits** and **200+ `(not published)` files**, adding 1v1/2v2/3v3 team battles, Streamable HTTP `/mcp` (`scripts/pk_mcp_http.py`), the Play with Friends lobby (`js/lobby_model.js`, `R1–R14`, `F1–F12`), and 3-round adversarial red-team testing (`scripts/redteam_probes/`):

- **MCP tools (11 total):** 7 game tools (`get_public_state`, `get_roster`, `get_history`, `submit_action`, `end_turn`, `set_notes`, `get_notes`) and 4 room tools (`join_room` with `invite=` / `claim=`, `lock_hero`, `leave_room`, `wait_for_turn`), exposed over both stdio and Streamable HTTP `/mcp`. Live hosted `/mcp` end-to-end match verification is scheduled for V4 (2026-12-01); prior live checks verified `/mcp` initialize `200` and browser-driven matches.
- **Role & external-model disclosure:** Kiro (CLI, ACP, IDE, Crew, 32 Specs, 11 Steering docs, 7 `PostFileSave` hooks, 8 custom agents, and the `pumpkin-killer-seat` Power) built the core Python engine, determinism/golden vectors, initial WebSocket relay, MCP stdio server, and foundational tests. Subsequent lobby/UI integration, red-team fixes, and verification were completed by the main-line AI coding assistants under the owner's direction using spec-first and failing-test-first discipline (lowering Kiro's raw commit share as integration work accumulated). In `LLM-REVIEW-1` (`4ca44af9`), external models **GLM-5.3** and **DeepSeek V4 Pro** (via Nebius Token Factory API) generated 45 adversarial relay cases (0 breaks) and surfaced 9 findings verified and fixed with tests (`docs/llm/llm_findings_verdict_20261126.md`).

## Kiro interfaces

- **CLI:** `scripts/kiro_route.py` routes a task brief to Kiro CLI. The route log
  `kiro_route_kiro_task_173_determinism.log` records a completed CLI task, and
  `docs/KIRO_LEDGER.md` records task results and main-line verification status.
- **Desktop app / IDE:** one saved `index.html` edit ran the engine-test hook.
  `docs/kiro_evidence/raw/ide_hook_run_20261115.txt` records the approval and
  displayed engine-test output. The attempted IDE MCP call failed because that
  session had no Pumpkin Killer tool; see `docs/kiro_evidence/raw/ide_mcp_attempt_20261115.txt`.
- **Kiro Web:** no repository record of a Web session.
- **Kiro Crew (0.12.2, through ACP):** installed on 2026-11-16 and used once, for a read-only audit of this document (`docs/crew_audit_usage_doc_result.md`; Crew wrote only that file). It wrote no game code. The files `docs/audit_C3_wind_reach_result.md` and `docs/audit_C4_kiro185_188_result.md` were written by Claude sub-agents, not by Crew. The Kiro CLI tasks run through `scripts/kiro_route.py` do not use ACP.

## Spec-driven work, not ad-hoc claims

The project keeps requirements, design, and task files under `.kiro/specs/`.
Examples include `shared-constants` for client/engine values, `particles` for
seeded effects, `mcp-standard` for the stdio public-information boundary,
`balance-sim` for headless match measurements, `physics-pbt` for fixed-step
flight checks, `i18n` for paired dictionaries, `ultimates-v2` for triggers, and
`ui-polish` for card readability and touch sizing.

The workflow makes deliverables testable instead of relying on a completion
message. Task 173 required `shared/determinism_golden.json` and both runtime
tests in `docs/kiro_task_173_determinism.md`; the route log only says the task
completed. The current file is proved by `scripts/test_determinism.js` and
`scripts/test_determinism_golden.py`, and commit `a835958` records its addition.
No surviving result file proves the earlier reported-but-missing-vector incident,
so this record does not claim more than that evidence.

The main line rejected task 170's smaller simulator rewrite because it removed
18 tests. The rejected copy remains at `(not published)`; see
commit `0011b1f` and `docs/DEV_LOG_20261116.md`. Task 181 then described its
poison as page-equivalent but lethal (`docs/kiro_181_result.md`). The development
log recorded that as a mismatch, and task 187 restored the page rule that status
ticks leave a living unit at one HP (`docs/kiro_187_result.md`,
`scripts/test_sim_balance.js`).

## Steering and custom agents

`.kiro/steering/` carries product, rules, technical, structure, assignment,
team-plan, progress, art-pipeline, and UI-aesthetics instructions. For example,
`structure.md` makes `index.html` a one-writer file, limiting parallel edits.

`.kiro/agents/` defines `asset-inventory`, `builder`, `committer`,
`daily-logger`, `pk-player`, `researcher`, `rules-reviewer`, and `tester`.
Their JSON files specify roles and permissions. `pk-player` is a restricted
MCP-only player; `docs/kiro_162_result_gpt-5.6-terra.md` records one match played
through its public-information tools, which the main line re-read; the final route
log of task 162 ends in an error and `docs/kiro_verified.json` has no row for it, so
it is not counted as verified. Definitions alone do not
prove runs for the other agents.

## Hooks

All current hooks use `PostFileSave` and are configured in `.kiro/hooks/`.

- The predecessor of `test-engine-on-index-save` is the only recorded IDE
  save-triggered run. It ran the engine test once, but no record says it caught a defect.
- `preload-block-fresh-on-index-save`: `docs/kiro_evidence/raw/hook_runs.log.txt` holds 176 `hook fired: index.html saved` entries (the hook command writes that line itself), 150 `OK preload block is up to date` lines and 27 `STALE preload block` lines (some of the STALE lines come from a manual dry run). The log does not say whether the IDE or the CLI fired them.
- `constants-sync-on-engine-save` and `test-constants-sync-on-save` both
  configure constants checks. No recorded save-triggered catch exists.
- `ledger-on-kiro-result-save` logs ledger check-mode output, but the log does
  not prove which program triggered its recorded entries.
- `orientation-frozen-on-picture-save` is configured to compare hero pictures
  with the frozen orientation set. No recorded catch exists.
- `test-rig-on-save` is configured but is a no-op until `(not published)`
  exists. No recorded catch exists.

## MCP and the seat power

`scripts/mcp_stdio_server.py` provides `get_public_state`, `get_history`,
`submit_action`, `end_turn`, `set_notes`, and `get_notes`. Its comments and
`public_throw()` omit seeds, pending actions, dice streams, and opponent aim.
`.kiro/settings/mcp.json` configures the white seat. The `pk-player` agent and
`.kiro/powers/pumpkin-killer-seat/plugin.json` restrict a match player to the
public game view. The recorded IDE MCP attempt failed, while the main-line
verified player record above proves one CLI-routed match.

## Seeded properties, golden vectors, and balance

`scripts/test_properties.js` generates seeded cases for six properties:
non-negative finite damage and ordered ultimate timelines; deterministic values
in range; canonical round hashes; known, bounded deterministic weather; bounded
flight with monotonic clear-flight range; and 2,016 balance matches with no
timeouts or hero average outside 20--80 percent.

Task 179 recorded four failures: timeline ordering, an invalid rounded-hash
assumption, flight comparison through the fence, and Bride's balance band
(`docs/kiro_179_result.md`). Task 181 corrected the tests or models, and the
current property runner passes all six (`docs/kiro_181_result.md`).

The JavaScript and Python determinism tests read the same
`shared/determinism_golden.json` values for wind, starts, move dice, supply
drops, bounce counts, nun stun selection, and coin tosses. `test_weather_golden`
checks shared weather vectors in both runtimes. `test_flight_golden.js` and
`.py` check 66 flight vectors plus 500 cross-runtime cases; the JavaScript test
also compares 30 page-helper cases. `test_round_hash.js` and `.py` check 20
canonical hash vectors.

`scripts/sim_balance.js` is a deterministic headless 1-vs-1 simulator, not a
browser-play claim. `docs/balance_matrix_20261116.md` records its matchup rates,
current balance-band violations, and un-applied in-memory proposals.

## Third-party tools and roles

Qwen-Image-Edit runs on Colab in the owner's art pipeline. Versions, provenance,
and remaining licence confirmations are disclosed in `docs/ASSET_PROVENANCE.md`.
The repository's test and rule tools are Node and Python; Kiro CLI route logs
identify the models used for recorded tasks.

Kiro wrote task briefs, specs, scripts, tests, and result reports identified by
`docs/kiro_task_*.md` and `docs/kiro_*_result*.md`. The main line performed page
wiring and independent re-checks recorded in `docs/DEV_LOG_20261116.md` and
`docs/kiro_verified.json`. The owner made game decisions and ran the Colab art
pipeline. A Kiro result is a report, not main-line verification.

## Share of the work (a rough measurement, 2026-11-16)

Method: `git log --no-merges --numstat` over 320 commits; lines added in code and documents (generated files, fonts, goldens, baselines and binaries excluded). A commit counts as Kiro-sourced when its message names a Kiro task. Result: 103 of 320 commits and 53,586 of 89,000 added lines (60 percent) are Kiro-sourced; the rest is main-line integration, verification, fixes and the owner's decisions. Limits: git has one author, so authorship cannot be read from history; Kiro output that the main line committed inside a general commit counts as main line; Kiro tasks 191 to 197 were not committed yet when this was measured. 35 Kiro tasks are marked verified in `docs/kiro_verified.json`. The Kiro work ran through Kiro CLI (`scripts/kiro_route.py`, `kiro-cli chat --agent-engine v3 --no-interactive`) with custom agents; the share is re-measured with the same command before submission.

### Full inventory (counted from the files and git, 2026-11-16 evening)

| Item | Count |
|---|---|
| Spec folders in `.kiro/specs/` | 32 (91 files) |
| Steering files / hooks / custom agents / powers | 11 / 7 / 8 / 1 (plus `.kiro/settings/mcp.json`) |
| Task briefs `docs/kiro_task_*.md` | 196 (numbers 1 to 227, 191 distinct) |
| Result files `docs/kiro_*_result*.md` | 112 |
| Tasks with a recorded verdict in `docs/kiro_verified.json` | 35 (the other 157 briefs have no recorded verdict; most were re-run by the main line through tests, but that is not written down per task) |
| Hook runs on file save (`hook fired: index.html saved`) | 176 (150 OK, 27 STALE lines) |
| Local Kiro logs (git-ignored) | 17 ACP, 113 `kiro-cli chat`; Crew files in `docs/`: 5 |
| Tests | 49 JS, 54 Python |
| Commits (no merges) | 333; 109 name a Kiro task |

Re-measured share with a looser file filter than the first run: 109 of 333 commits and about 67,940 of 113,688 added lines (59.8 percent) are Kiro-sourced. The phone-layout work of 2026-11-16 evening (commits `142feccc`, `92efc12d`, `1f5f8edc`) was done by the main line after Kiro's last task (227), so it counts as main line and lowers the Kiro share a little over time. Same limits as above: one git author, Kiro output inside a general commit counts as main line.

## Spec-driven development compared with work without a spec

Most of the engine, the relay, the MCP server and the tests were built from task briefs and specs under `.kiro/specs/`. Some work had no spec: the phone-layout pass on the evening of 2026-11-16 (commits `142feccc`, `92efc12d`, `1f5f8edc`) was done by the main line by looking at screenshots and measuring the page. The two ways failed differently, and the record shows it.

- **With a spec and a test:** Kiro task 225 wrote an end-to-end test with two MCP seats; it failed with "stale or out of turn", and that exposed a relay that silently skipped one team's turn from round 2. The fix was one function (`c41cef5b`). Task 187 restored the poison rule after a simulator and the page disagreed. In both cases the failure came from a check written before the code was trusted.
- **Without a spec:** `scripts/test_phone_layout.js` pins strings in `index.html`, so it passed 9 of 9 while the eight hero tiles had disappeared (a `//` comment had swallowed the line that adds them), and while an old media rule kept the title at 16 px whatever size was asked for. Both were found only by measuring the page and by clicking through it at 800 x 360, not by a test.
- **What this says:** a spec gives a failing check before the work is accepted; screenshots and measurements find layout problems the strings never see, but only after someone looks. Where a test pins text instead of behaviour, it can pass while the screen is wrong.

## Kiro interfaces not used and powers

- **Kiro Web:** not used (no record in the repository).
- **Kiro powers:** one power was written for this project, `.kiro/powers/pumpkin-killer-seat/` (a `plugin.json`, an `mcp.json` that starts `scripts/mcp_stdio_server.py`, and a `play` skill). It lets an agent take a seat and read only its public view. It has not been installed and activated in the Kiro Powers panel, so its keyword activation is untested. No official power from the registry was used; none matched a need of this game.

## Pre-existing material and disclosure

- The first commit is dated 2026-10-31, after the start of the submission period (2026-10-30). The repository contains no code written before that date.
- The game page is plain HTML, canvas and JavaScript; the engine and relay are Python. No game framework is used.
- Third-party material, sounds and fonts are listed with their licences in `CREDITS.md`; the pictures are generated with Qwen-Image-Edit on Colab and described in `docs/ASSET_PROVENANCE.md` (some licence confirmations are still open there).
- Code and documents were written by Kiro (CLI, ACP, Crew) from task briefs and by a second AI coding assistant outside Kiro, working under the owner's direction (integration, verification, fixes). The owner decided the rules and every public text.
