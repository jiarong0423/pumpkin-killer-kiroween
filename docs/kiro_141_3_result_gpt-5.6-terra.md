# Kiro 141 task 3 result (missing pictures and sounds, no page edit), 2026-11-15
Files: `docs/ingest_mapping_20261115.md` (new), `scripts/release/check_missing_mapped.py` and `scripts/test_check_missing_mapped.py` (new). `index.html` and `docs/audio_gap_options_20261115.md` not changed.
Command 1: `python3 -B scripts/release/check_asset_refs.py` -> `SUMMARY refs=121 missing=7` (4 pictures: bg_belltower, bg_pumpkin_field, fx_feet_chain, unit_knight_unarmed; 3 sounds: move_step, ultimate_ready_chime, item_pickup).
Command 2: `python3 -B scripts/release/check_missing_mapped.py` -> seven `MAPPED ... (MISSING)` lines, `SUMMARY missing=7 unmapped=0`, exit 0. Test: `python3 -B scripts/test_check_missing_mapped.py` -> `OK` (4 tests).
The page gives job, install route (`scripts/ingest_missing_20261115.py`, dry run by default), fallback and the expected missing count per outcome (7 now, 3 with pictures, 0 with pictures and the three sound references nulled).
Found: the `colab/jobs_missing_20261115.json` jobs `fx_feet_chain`, ghoststar and coin use ref keys (`bar`, `knight`, `out:...`) absent from its `refs` table; ghoststar outputs install under names the page does not load; `assets/i18n/` is excluded by the export manifest.
Not run: Colab, the ingest script (the local `python3` has no Pillow, so `scripts/test_ingest_missing.py` could not run), the browser, any audio listening.
Stopped after task 3 as asked; the main line reruns tasks 1 to 3 before task 4.
