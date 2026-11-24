# Kiro task 85a — stage R1 only (export tree), run by Kiro CLI

Read ONLY: `docs/kiro_task_85_release_delivery.md` section 1 (fixed rules) and stage R1, and `docs/kiro_84_release_plan_claude-sonnet-5.5.md` section 1 (export manifest). Do not read other files unless a command below needs them. Do not deliberate at length: write each file as soon as you know what it contains.

State at start (checked by the main line): `scripts/release/export_manifest.json` already exists, is valid JSON, has 60 ordered rules (first match wins) and ends with the catch-all `{"match": "*", "decision": "EXCLUDE"}`. Keep it; edit it only if a test you run proves a rule wrong. The other R1 files do not exist yet.

Write, in this order, saving each file immediately:
1. `scripts/release/check_asset_refs.py` — as specified in stage R1 of the delivery document. Scans `index.html`, `js/*.js`, `css/*.css`; picks up literal `(not published)` paths and CSS `url(...)` resolved relative to the CSS file; ignores dynamically built paths; case-sensitive existence check (a case mismatch counts as missing, printed as `CASE`); prints `REF` and `MISSING` lines plus a summary; exit 1 when anything is missing. Expose `scan(root)` and `missing(root)` so `export_tree.py` can import it.
2. `scripts/release/export_tree.py` — as specified in stage R1. Rules: ordered list, first match wins, patterns are an exact path, a `dir/` prefix, or an fnmatch glob on posix relative paths. `.git` is always skipped, symlinks are not followed and are counted as skipped. Dry run is the default and writes nothing. `--apply` refuses a non-empty `--out`, refuses `--out` inside the source tree, copies INCLUDE files, runs the four named transforms (`.gitignore` rewrite that aborts if any line mentions `.kiro`, `steering_refs` replacing references to `(not published)` and `(not published)` with `(not published)`, `drop_credit_sentence` that must match exactly one sentence or abort, `route_log_txt` renaming `kiro_route_kiro_task_*.log` to `.txt` under `docs/kiro_evidence/raw/route_logs/`), and writes `docs/kiro_evidence/EXPORT_NOTES.md` into the output (deterministic, no timestamps, no private values). Assets not referenced by `check_asset_refs.py` are excluded with the reason "not referenced". Exit 0 ok, 2 on any manifest or transform error.
3. `scripts/test_check_asset_refs.py` and `scripts/test_export_tree.py` — stdlib `unittest`, toy trees built in a temp folder at test time, `subprocess` for the CLIs. Cover: reference found, missing file exit 1, case mismatch, dry run writes nothing, apply copies and transforms, non-empty out refused, out inside source refused, missing catch-all is a manifest error.

Then run, and paste the real output lines into the result file:
- `python3 -B scripts/test_check_asset_refs.py`
- `python3 -B scripts/test_export_tree.py`
- `python3 -B scripts/release/export_tree.py --source . --manifest scripts/release/export_manifest.json` (dry run on the real tree; it writes nothing)

Finish with `docs/kiro_85_R1_result_gpt-5.6-terra.md` (max 60 lines): files created, the exact commands you ran with the last line of each output, what you did not run, what you could not verify. Do not claim a test passed unless you saw its output. Do not touch GitHub, git remotes, or any file outside `scripts/release/`, `scripts/test_*.py` named above, and the result file. Python stdlib only. No network.
