# Tasks: contest gap run
Written 2026-11-15 (task 141). Spec: `requirements.md` and `design.md` in this folder. Order follows `docs/SCORING_ALIGNMENT_20261115.md`.

Tick rule (same as `.kiro/specs/release-package/tasks.md`): a box is ticked only when the command output is pasted in the task's result file. A Kiro report alone is not proof. If a command is refused, the box stays empty. Do the tasks in order, one at a time. After task 3 stop; the main line reruns the commands before task 4.

Boundaries: never edit `index.html`, `.gitignore`, the export tree or any public repository. No network, no git, no secrets, credit numbers or personal names in any file.

## Task 1. Stage 1 evidence and text (B12, B14, B13). Requirements 1, 3, 5, 6, 7, 14
Files it may touch: `(not published)`, `(not published)` (disclosure section only), `(not published)` (new: English description and testing instructions), `scripts/release/check_draft_paths.py` (new), `scripts/test_check_draft_paths.py` (new), `docs/kiro_141_1_result_gpt-5.6-terra.md`.
Do: refresh `JUDGES.md` (8 topics, honest status, only export-visible paths); add a "Disclosure of pre-existing work" section to `CREDITS.md`; write `DEVPOST_TEXT.md` (description, pitch lines, testing instructions for judges, known limits); write the path checker and its test.
Proof:
- `python3 -B scripts/test_check_draft_paths.py` -> last line `OK`.
- `python3 -B scripts/release/check_draft_paths.py (not published) (not published) (not published)` -> last line `SUMMARY checked=N missing=0 excluded=0`, exit 0.
Expected: the two values above. Result file: `docs/kiro_141_1_result_gpt-5.6-terra.md`.
- [x] Task 1 done (output pasted in `docs/kiro_141_1_result_gpt-5.6-terra.md`; main line to rerun)

## Task 2. Technological Implementation evidence (B12 with B01, B02 state). Requirements 1, 8, 14
Files: `docs/kiro_evidence/TECH_EVIDENCE_20261115.md` (new), `scripts/release/tech_evidence_counts.py` (new), `docs/kiro_141_2_result_gpt-5.6-terra.md`.
Do: a read-only counting script; an evidence page that quotes its output and lists what was not used with the file that shows each fact.
Proof:
- `python3 -B scripts/release/tech_evidence_counts.py` -> exit 0 and lines for ledger, specs, hooks, steering, agents, powers, mcp, evidence files (the page quotes the same numbers).
- `python3 -B scripts/release/check_draft_paths.py docs/kiro_evidence/TECH_EVIDENCE_20261115.md` -> `SUMMARY ... missing=0 excluded=0`.
Expected: both exit 0; page numbers equal script numbers. Result file: `docs/kiro_141_2_result_gpt-5.6-terra.md`.
- [x] Task 2 done (output pasted in `docs/kiro_141_2_result_gpt-5.6-terra.md`; main line to rerun)

## Task 3. Design gaps that need no page edit (B07, B08). Requirements 9, 14
Files: `docs/ingest_mapping_20261115.md` (new), `scripts/release/check_missing_mapped.py` (new), `scripts/test_check_missing_mapped.py` (new), `docs/kiro_141_3_result_gpt-5.6-terra.md`. Existing `docs/audio_gap_options_20261115.md` is read, not changed.
Do: map every missing reference to its job, expected output name, install route and fallback; cover the three audio files with the existing options and the owner decision each needs; state the expected missing count for each outcome.
Proof:
- `python3 -B scripts/release/check_asset_refs.py` -> last line `SUMMARY refs=121 missing=7` today (the count falls as pictures and sounds are installed or references dropped).
- `python3 -B scripts/release/check_missing_mapped.py` -> every missing path printed as `MAPPED`, last line `SUMMARY missing=7 unmapped=0`, exit 0.
Expected: `unmapped=0`. Result file: `docs/kiro_141_3_result_gpt-5.6-terra.md`.
- [x] Task 3 done (output pasted in `docs/kiro_141_3_result_gpt-5.6-terra.md`; main line to rerun)

--- stop here; the main line reruns tasks 1 to 3 before the rest ---

## Task 4. Test gaps (B15). Requirements 8, 9
Files: `scripts/test_*.js` or `scripts/test_*.py` it names, `docs/kiro_141_4_result_gpt-5.6-terra.md`. Not started.
Do: make the clean checkout report missing references as failures (known blind spot in `(not published)` R5); list the optional-package tests; record `test_i18n.js` state after the main line wires English.
Proof: `bash scripts/release/clean_checkout.sh` output (main line runs it); `python3 -B scripts/release/check_asset_refs.py` exit code 1 while refs are missing. Expected: a missing reference fails the run.
- [x] Task 4 done (output pasted in `docs/kiro_141_4_result_gpt-5.6-terra.md`; main line to rerun)

## Task 5. Video shot list outline (B16). Requirements 4, 11
Files: `(not published)` (new), `docs/kiro_141_5_result_gpt-5.6-terra.md`. Not started.
Do: a shot list under three minutes in English with one line per shot and the file or command that shows it working. No script for narration in the owner's voice; the owner records.
Proof: `python3 -B scripts/release/check_draft_paths.py (not published)` -> `missing=0 excluded=0`; the shot durations add up to 180 seconds or less (stated in the file). Expected: both.
- [x] Task 5 done (output pasted in `docs/kiro_141_5_result_gpt-5.6-terra.md`; main line to rerun)

## Not for Kiro
| Item | Gap | Executor | Reason |
|---|---|---|---|
| Open the folder `pumpkin-killer` as the IDE workspace, save `index.html`, call `get_public_state` in IDE chat, check the Powers panel | B01 | owner, then main line files it | Only the owner can press save and see the IDE panels; the 11-15 session failed without a workspace |
| One task in Kiro Web on the new repository, a Crew mention only if used | B02 | owner | Needs the new repository and the owner's GitHub App |
| Deploy, ingress, live smoke test (`scripts/release/smoke_url.py <url>`) | B03 | owner, main line | Account, cloud and public URL |
| Page wiring: knight ultimate, AI level in the HUD, English interface (`js/i18n.js`), remaining heroes, dropping dead picture or sound references | B04, B05, B09, B21 | main line (one `index.html` writer) | `index.html` has one writer |
| Opening flow, coin toss, seat selection | B06 | main line after owner concept images | `index.html` and owner art |
| Colab pictures (`bg_belltower`, `bg_pumpkin_field`, `fx_feet_chain`, `unit_knight_unarmed`, hag set, scenes, character retakes) | B07 | owner | Only the owner runs Colab and Drive |
| Choose a sound source after listening; edit the audio map and `js/audio.js` | B08 | owner decides, main line edits | Needs a listen and a two-file edit that the test keeps identical |
| `~/pk_privacy_terms.txt`, answers to R0 | B10 | owner | Private values |
| Export `--apply`, privacy gate run, clean checkout on the export, private push, then Public, topic, About shows MIT | B10, B11 | main line, owner for Public | Push and visibility |
| Review and paste the Devpost text, choose category and bonus prizes, submit | B13, B18 | owner | The owner's account and decision |
| Record, narrate and upload the video | B16 | owner | The owner's voice, screen and YouTube account |
| Blog and Social Blitz posts | B17 | owner | Judged as the owner's own words |
| Redeem credit codes by 2026-12-04 | B18 | owner | Account |
| Local LLM seat | B20 | main line (licence check) | Model licence and local machine |
| 4 vs 4 | B19 | nobody | Frozen |
