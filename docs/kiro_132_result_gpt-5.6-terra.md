# Task 132 result — gpt-5.6-terra
Changed `scripts/ingest_missing_20261115.py`: `newest_output`, `prepare`, `apply_install`, and `append_provenance` add dry-run, keyed/copy mappings, guarded backups, logging, and apply-only provenance rows.
Changed `scripts/test_ingest_missing.py`: `IngestMissingTests` covers dry run, install/backup, missing output, and 4:3 rejection.
`docs/ASSET_PROVENANCE.md` was not edited; the new script changes its table only with `--apply`.
Uses (file:line): `index.html:368`, `index.html:369`, `index.html:455`, `index.html:475`, `index.html:2155`; no `js/` hits.
Verification commands:
- `python3 -B scripts/test_ingest_missing.py` → last line: `OK`
- `python3 -B scripts/test_ingest_sheets.py` → last line: `test_ingest_sheets: OK`
- `python3 -B scripts/test_ingest_wind_sheets.py` → last line: `test_ingest_wind_sheets: OK`
Not verified: no owner Drive output was available, so no real-repository `--apply`, owner review, or real provenance row was performed.
