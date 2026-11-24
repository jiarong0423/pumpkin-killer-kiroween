# Kiro task 71 result

Created `scripts/ingest_wind_sheets.py` with sheet and single-picture modes.
It reuses `ingest_queue.key_full`, validates empty or clipped art, ghost anchor, scale and centre drift, and runs continuity metrics when importable.
Dry runs render named previews in a system temp directory and list file sizes.
`--apply` installs 12 keyed PNGs plus the manifest and backs up replacements under `(not published)`.
Default logging is `(not published)`.
Run a sheet dry run: `python3 -B scripts/ingest_wind_sheets.py --ghost-sheet GHOST.png --fx-sheet FX.png`.
Run an install: add `--apply` to that command, or use `--ghost-dir DIR --fx-dir DIR --apply`.
Created offline synthetic coverage in `scripts/test_ingest_wind_sheets.py`.
I did not run `python3 -B scripts/test_ingest_wind_sheets.py`; this environment does not provide a test-running tool.
I could not verify generated Colab artwork because no wind input images were supplied.
