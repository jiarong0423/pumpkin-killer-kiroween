# Kiro task 71 — wind pictures ingest script (Terra writes it; main line re-runs every test itself)

Owner 2026-11-10: the wind artwork (continuous blowing ghost + gust streaks) is generated in Colab by the main line; Kiro writes the script that turns the generated pictures into game assets. Art is NEVER drawn by code.

Read first: scripts/ingest_queue.py, scripts/ingest_sheets.py, scripts/check_continuity.py, scripts/test_ingest_sheets.py, docs/image2_ghost_blow_prompt.md, (not published)

Create ONLY these two files (do not edit index.html, assets/ or any existing script):
- scripts/ingest_wind_sheets.py
- scripts/test_ingest_wind_sheets.py

Behaviour of ingest_wind_sheets.py (complete and deployable, no placeholders, logging to a file (not published), non-zero exit on any failure, layered exception handling):
1. Input mode A (sheets): --ghost-sheet PATH (2048x1024, 4x2 cells of 512x512, 24 px magenta #FF00FF gutters, 8 frames in reading order) and --fx-sheet PATH (2048x512, 4 cells: gust small, medium, large, swirl).
   Input mode B (single pictures from Colab): --ghost-dir DIR holding wind_ghost_1.png .. wind_ghost_8.png, each already on a flat magenta background, and --fx-dir DIR with wind_gust_s/m/l.png and wind_swirl.png.
2. Key magenta with the SAME tight keying the project uses (import and reuse the helper from scripts/ingest_queue.py or ingest_sheets.py; do not write a second keyer). Reject (exit non-zero) a picture that is empty, touches its edge, or whose ghost bbox centre drifts more than 6 px from frame 1; ghost frames must keep one anchor (feet/tail row) and one scale.
3. Run check_continuity.py logic on the 8 ghost frames when importable; fail on its failure.
4. Outputs, only on full PASS and only with --apply (default is --dry-run: write previews to a temp dir, print the list of files it WOULD write with sizes, exit 0): (not published) .. wind_ghost_f8.png (tight-keyed, same canvas and anchor), wind_gust_s.png, wind_gust_m.png, wind_gust_l.png, wind_swirl.png. Back up any file it would overwrite to (not published)<timestamp>/ first. Also write (not published) with frame count, canvas size and anchor.
5. test_ingest_wind_sheets.py: offline unit tests with synthetic magenta sheets and folders (good sheet, empty cell, cell touching edge, drifted ghost, dry-run writes nothing, apply writes 12 files plus manifest, backup made on overwrite). `python3 -B scripts/test_ingest_wind_sheets.py` must pass with no network.

Write a short result note to docs/kiro_71_result_gpt-5.6-terra.md (max 20 lines: what exists, how to run, what you could not verify). Do not claim the tests passed unless you ran them.
