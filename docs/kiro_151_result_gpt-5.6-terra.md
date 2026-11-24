# Task 151 result — 2026-11-15

**Changed:** `scripts/make_download_package.py` (`stage_package`, `run_privacy_gate`, `write_zip`); `scripts/test_make_download_package.py`; `docs/PLAY.md`; and `(not published)`.
**Behaviour:** the builder stages the manifest-selected public tree, adds the play kit, gates that temporary tree, writes sorted fixed-timestamp ZIP members and payload checksums (the checksum manifest cannot hash itself).
**Verify:** `python3 -B scripts/test_make_download_package.py`
Last output: `Ran 5 tests in 0.310s` / `OK`.
**Repository dry run:** `python3 -B scripts/make_download_package.py --out dist/pumpkin-killer-2026-11-15.zip --dry-run` returned `ERROR privacy gate could not read its required terms file`.
**Attempt with terms:** `PK_TERMS="$HOME/pk_privacy_terms.txt" python3 -B scripts/make_download_package.py --out dist/pumpkin-killer-2026-11-15.zip --dry-run` was denied before an answer, so it did not run.
I could not verify the repository file count, total size, ZIP size, or referenced-only asset saving. No repository ZIP was created or uploaded.
The current permitted MCP server supports `--seat` but not `--connect` or `--code`; the agent launchers reject relay arguments pending the relay task.
