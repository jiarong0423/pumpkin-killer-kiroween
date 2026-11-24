# Kiro task 110 — close the two blind spots of the clean-checkout script (work block B15)

Known limits of `scripts/release/clean_checkout.sh` (main line, 2026-11-15): (1) its "404 count" only fetches paths that `check_asset_refs.py` prints as `REF`, so a referenced file that is missing on disk is never counted; (2) with a `.git` folder it uses `git clone`, which copies only committed files, so uncommitted work is not tested.

Read: `scripts/release/clean_checkout.sh`, `scripts/release/check_asset_refs.py`, `scripts/test_check_asset_refs.py`, `docs/kiro_85_R5_result_gpt-5.6-terra.md`.

Do, saving after each:
1. In `clean_checkout.sh` count every `MISSING` and `CASE` line of `check_asset_refs.py` run on the copy as a failure; print them in the summary as `missing references: N` and include the first five paths; the overall result is FAIL when N is above 0.
2. Add a `--worktree` flag: copy the working tree with `cp -R` (excluding `.git`, `(not published)`, `node_modules`) instead of `git clone`, so uncommitted files are tested; the default stays `git clone`. Print which mode ran in the first summary line.
3. Add `scripts/test_clean_checkout.py` (`unittest`, stdlib): build a toy project in a temp folder (an `index.html` that references one existing and one missing asset, a passing test file), run the script with `--worktree` and `--log <temp file>`, and assert exit 1 and `missing references: 1`; then add the missing file and assert exit 0. Because the sandbox may block local ports, the test must skip with a clear message if the script cannot bind a port (do not fail).
4. Run `bash -n scripts/release/clean_checkout.sh` and `python3 -B scripts/test_clean_checkout.py`; paste the last lines. If a shell call is refused, say so; do not invent output.

Touch only `scripts/release/clean_checkout.sh`, `scripts/test_clean_checkout.py` and the result file exactly named `docs/kiro_110_result_gpt-5.6-terra.md` (max 15 lines). No network, no git.
