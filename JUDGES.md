# Judges' guide

Every claim here has a path and a command; run commands from the repository root. The game is described in `README.md`; the full, honest account of how Kiro was used is `docs/KIRO_USAGE_20261116.md` (read that first). Note: the public repository is a privacy-cleaned single-commit snapshot of the development repository (514+ development commits, 115 naming Kiro tasks); all published task briefs, result reports, and `.kiro/` artefacts are preserved here. Numbers below were recounted on 2026-11-25.

## The Kiro material at a glance

| Topic | What exists | Where | Reproduce |
|---|---|---|---|
| Specs | 32 spec folders with requirements, design and tasks, including the team battle spec | `.kiro/specs/` | `ls .kiro/specs` |
| Steering | 11 steering files (product, tech, rules, structure, assignment, art pipeline, UI aesthetics, UI settings...) | `.kiro/steering/` | `ls .kiro/steering` |
| Hooks | 7 hooks, all `PostFileSave`: constants sync, engine tests on save, orientation freeze on picture save, preload block check, ledger on result save... The hook log shows 176 save-triggered runs of the preload check | `.kiro/hooks/`, `docs/kiro_evidence/raw/hook_runs.log.txt` | `grep -c "hook fired: index.html saved" docs/kiro_evidence/raw/hook_runs.log.txt` |
| Custom agents | 8 agents (builder, tester, researcher, rules-reviewer, asset-inventory, daily-logger, committer, pk-player). Only some have recorded runs; the document says which | `.kiro/agents/` | `ls .kiro/agents` |
| MCP and power | A standard MCP server (stdio and HTTP `/mcp`) with seven game tools and three room tools wraps the Python engine (public information only; full-team or partial-unit `claim` seats in 1 v 1, 2 v 2 and 3 v 3 rooms) and a Kiro power for taking a seat | `scripts/mcp_stdio_server.py`, `.kiro/settings/mcp.json`, `.kiro/powers/pumpkin-killer-seat/` | `python3 -B scripts/test_mcp_stdio.py` and `python3 -B scripts/test_mcp_claim.py` |
| Property-based tests | Seeded properties: damage never negative, deterministic outputs, round hashes, weather bounds, flight terminates, every balance pairing finishes without a dominant hero; golden vectors shared by JS and Python | `scripts/test_properties.js`, `shared/determinism_golden.json` | `node scripts/test_properties.js` |
| Surfaces | Kiro CLI (task briefs through `kiro-cli chat`, later through the Agent Client Protocol with `scripts/kiro_acp_route.py`), the Kiro desktop app once (a hook run), Kiro Crew 0.12.2 (a read-only documentation audit). No record of Kiro Web | `scripts/kiro_route.py`, `scripts/kiro_acp_route.py`, `docs/crew_audit_usage_doc_result.md` | `ls docs/kiro_task_*.md \| wc -l` and `ls docs/kiro_*_result*.md \| wc -l` |

## How Kiro's output was checked

Every Kiro result is a report, not proof. A human-supervised main line re-ran results and recorded 38 verdicts in `docs/kiro_verified.json` (12 verified, 22 partly verified, 3 read-only, 1 not checked); 112 results are recorded in all, so not every one has a verdict. Defects found by re-running (see `docs/KIRO_USAGE_20261116.md`): a golden file reported written but missing, a simulator rewrite that dropped 18 tests, a poison model that did not match the page, a deployment README that lost its release steps, a Smart-opponent ordering that made "pick option 1" stronger than the Normal opponent, and a relay turn order that skipped one team's turn from round 2. Safety nets built by Kiro tasks and used in later tasks: a recorded match transcript proven byte-identical before and after a refactor (`docs/transcripts/`), a mutation smoke test, and a numeric UI review (`docs/ui_review_20261116.md`).

## What was measured on the finished build

| Claim | Number | Reproduce or read |
|---|---|---|
| Hit judging (fence down, every power up to the maximum): the page's judgement equals the rule | 425,861 flight steps in six tracks, 0 false hits, 0 missed hits (62,788 steps, 14.7 percent, are area or returning weapons and exempt from the false-hit check) | `docs/hit_coverage_20261119.svg`, `python3 -B scripts/rerun_hit_coverage.py` (heavy, run once) |
| Page flights equal the engine's flights, both directions, with wind and weather | 67,456 shots per direction, 0 mismatches | `docs/rear_rear_weather_wind_20261119.json` |
| Team rules at 1, 2 and 3 units per side | 6,667 matches per size, 20 rule checks, 0 failures. A first run of the same simulation showed 4 failures in one check; all four were a rounding difference at the third decimal in the test's own reference (it summed differently from the engine and the page), and the four seeds pass after the reference was changed to sum the same way | `redteam/evidence/sim_team_full_run2_20261122_summary.txt` |
| Computer opponent levels, hits per throw | easy 0.141, normal 0.332, hard 0.462 | `node scripts/test_page_ai_hit_rates.js` |
| Everything | 184 `test_*` scripts (+ `sim_team_headless.py`); full suite runs with 0 failures (`zsh scripts/run_full_suite.sh`): 178 run, 6 need local sockets and are skipped there (fill-room self-test, MCP stdio, phone room, late join, reconnect, seat grace); those 6, plus the relay, MCP claim, MCP risk and deploy-check suites, were run by hand and pass. A container built from `deploy/Dockerfile.coolify` was run and answered on page, relay and MCP | `redteam/evidence/recheck_full_suite_v3_20261125.txt`, `redteam/evidence/recheck_socket_v3_20261125.txt`, `redteam/evidence/prepush_docker_e2e_20261124.txt` |

## What was decided by people

The owner decided the game rules, the eight heroes, the one-direction rule (the player is always on the left; a right-seat player in a room gets a mapped point of view, never a flipped picture), the 3 v 3 limit, the category (evolved from an early 4 v 4 / Costume Contest draft recorded in `.kiro/steering/{product,tech,ui_aesthetics}.md` to the final 3 v 3 / Resurrection build), the maximum throw power, which sounds and pictures stay, and every public text. Open questions were settled by independent reviewers arguing from different roles (`docs/ARBITRATION_20261116.md` is the first record) and the owner approved each result. The art is generated by an image model on Colab and disclosed in `docs/ASSET_PROVENANCE.md`; licence confirmations still open are listed there.

## The five criteria

| Criterion | Where to look |
|---|---|
| Potential impact | A game people can start in seconds from a QR code on phone or computer, 1 to 3 heroes a side, with an optional agent seat; `README.md` |
| Technical implementation | The Kiro table above, the measured table, `docs/KIRO_USAGE_20261116.md`, `.kiro/`, the tests (`scripts/test_*.js`, `scripts/test_*.py`) |
| Design | The start screen, the battle screen and the phone layout; numbers in `docs/ui_review_20261116.md` |
| Innovation | Deterministic shared rules with a round hash over every unit so every device agrees; a relay that never simulates a match; an MCP seat that gets public information only; an optional online opponent that chooses among options the program computed |
| Presentation | The demo video and the Devpost page; the README |

## Reproduce

```sh
for t in scripts/test_*.js; do node "$t"; done
for t in scripts/test_*.py; do python3 -B "$t"; done   # the relay, MCP connection and smoke tests open local sockets
node scripts/record_match_transcript.mjs               # prints "baseline matches" (needs Chrome)
```
