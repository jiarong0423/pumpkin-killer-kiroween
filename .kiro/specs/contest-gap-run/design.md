# Design: contest gap run
Written 2026-11-15. Requirements: `requirements.md` (numbers in brackets). Nothing here was run when written; `tasks.md` and the result files hold the runs.

## Order
The order follows `docs/SCORING_ALIGNMENT_20261115.md`: Stage 1 first, then Technological Implementation, then visible Design gaps, then tests, then the video outline. Kiro can do only the parts that need neither the owner nor `index.html`. Everything else is in "Not for Kiro" in `tasks.md`.

| Order | Work | Gaps | Criterion | Why this place |
|---|---|---|---|---|
| 1 | `JUDGES.md` 8 topics, disclosure list, English description and testing text | B12, B14, B13 | Stage 1 and Presentation | A failed stage 1 item scores nothing else. Text is cheap and checkable. |
| 2 | Evidence page with counts from a command | B12 (B01, B02 state) | Technological Implementation | 20 percent, and it is the contest's own theme. |
| 3 | Missing-picture and missing-sound mapping | B07, B08 | Design | Shows judges no hole; needs no page edit until the pictures arrive. |
| 4 | Test gaps | B15 | Technological Implementation | Clean checkout must report missing refs as failures. |
| 5 | Video shot list outline | B16 | Presentation | Outline only; the owner records. |

## Evidence rules
- A claim cites a file or a command. If neither exists, the claim is "not done" or "not used".
- Status words are fixed: done, partly, not done, not used. `docs/kiro_verified.json` is quoted as the main line's record and is never edited here. A Kiro result file is never counted as verification.
- Failures are written down: the IDE MCP call failed, the knight test failed, `physics-pbt` ticks files that do not exist. A judge reads honesty as skill.

## The path checker (`scripts/release/check_draft_paths.py`)
Why: `docs/WORK_QUEUE_20261115.md` B12 says "every backticked path exists". The manifest also excludes many `docs/` files (for example `(not published)`, `(not published)`). A path that exists locally but is excluded from the export is a dead link for the judge. The checker reuses `load_manifest`, `choose_rule` and `source_files` from `scripts/release/export_tree.py`, so it uses the same rules as the export.
- Reads each given Markdown file and collects backticked tokens that look like repository paths (contain `/` and a known top-level folder, or are a root file name). Skips tokens with spaces, `*`, `<`, `>` or `://`.
- Strips a trailing `:line` or `:line-line`.
- `README.md`, `JUDGES.md` and `CREDITS.md` mean the files that the main line copies to the root from `(not published)`; they count as present when the draft exists.
- For each path prints `OK`, `MISSING path (file:line)` or `EXCLUDED path (rule, file:line)`. Final line `SUMMARY checked=N missing=M excluded=E`. Exit 1 if either is above 0.
- Test: `scripts/test_check_draft_paths.py` builds a toy tree and manifest in a temp folder.

## Evidence page (`docs/kiro_evidence/TECH_EVIDENCE_20261115.md`)
Numbers come from `scripts/release/tech_evidence_counts.py`, which only reads files: verified-ledger entries and their words, spec folders with tick counts from each `tasks.md`, hook files and their events, steering files with `inclusion: always`, agent files, MCP config server names, power folders, evidence files present. The page quotes the script output, then lists what was not used (Web, Crew, a power activating from a chat, an IDE MCP call that worked) with the file that shows it.

## Mapping page (`docs/ingest_mapping_20261115.md`)
One table row per missing reference from `check_asset_refs.py`: path, job id and queue file, the output file name the runner writes, the install route (an existing script or "needs a reviewed mapping"), and the fallback if the picture or sound does not arrive (drop the reference, a one-line change made by the main line). `scripts/release/check_missing_mapped.py` fails if a missing path is not in the table, so the page cannot go stale when the count changes.

## Risks
- `JUDGES.md` statuses can go stale as the main line ships. Every row names its source file so the main line can recheck.
- The path checker only sees backticked paths. Plain-text mentions are not checked.
- I cannot run git, the browser, Colab or a deploy. First-commit date and clean-checkout results come from the main line.
- `index.html` has one writer. Every item that needs it is listed under "Not for Kiro".
