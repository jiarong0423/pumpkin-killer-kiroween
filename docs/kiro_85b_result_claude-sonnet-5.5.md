# Kiro 85b result (claude-sonnet-5.5): release package spec

## Paths written
- `.kiro/specs/release-package/requirements.md` (10 requirements in EARS style, one per fixed rule of `docs/kiro_task_85_release_delivery.md` plus clean clone and upload gating)
- `.kiro/specs/release-package/design.md` (components, data flow, gate order G0 to G10, failure handling, command-to-claim table)
- `.kiro/specs/release-package/tasks.md` (T1 to T6, each with files, verify commands, requirement numbers)
- `docs/kiro_85b_result_claude-sonnet-5.5.md` (this file)

## What I checked by reading files
- `scripts/release/` holds `check_asset_refs.py`, `export_manifest.json`, `export_tree.py`. `scripts/test_export_tree.py` and `scripts/test_check_asset_refs.py` exist.
- Their option names (`--root`, `--source`, `--manifest`, `--out`, `--dry-run`, `--apply`) come from the code. The manifest's last rule is the catch-all EXCLUDE.
- Only those file-existence boxes are ticked in T1. T2 to T6 have no ticks because none of their files was found or looked for beyond `scripts/release/`.

## What I did not run
- No shell command ran. Every `execute_bash` call failed with "permission request failed before it was answered", so I did not run any test, the export dry run, `git`, or `date`.
- Because the clock was not readable, the date in the spec (2026-11-11) is the latest dated record in the repository (`docs/KIRO_LEDGER.md`, generated 2026-11-11 19:04). Today's real date may be later. Please check it and correct the three headers if needed.
- The test results in `docs/kiro_85_R1_result_gpt-5.6-terra.md` (both OK, `selected=548`) are the 85a report. I did not see them, so the matching T1 boxes are empty.
- I did not check whether `(not published)`, `(not published)`, `(not published)` or `(not published)` exist.
- The upload mechanism (Kiro IDE signed in, or the Kiro Agent GitHub app) is taken from the delivery document and was not tested.
- Plan numbers from `docs/kiro_84_release_plan_claude-sonnet-5.5.md` (73 `.kiro` files, the 22 milestones, the P1 to P16 patterns) are carried over unchecked.

## Notes for the main line
- Requirement 4.2 adds a rule not in the delivery document: the gate fails if `$PK_TERMS` points inside the tree. It follows from "outside the tree" and can be removed if unwanted.
- The delivery document says Kiro performs the upload, yet no Kiro agent here can push. `design.md` section 6 records that as open.
- No task of the checklist was started. Nothing outside `.kiro/specs/release-package/` and this file was written.
