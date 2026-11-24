# Kiro 141 task 4 result (test gaps), 2026-11-15
Files: `scripts/release/clean_checkout.sh` (stale known-failures line corrected), `docs/kiro_141_4_result_gpt-5.6-terra.md`. `index.html` untouched.
`bash -n scripts/release/clean_checkout.sh` -> `bash -n: OK`.
`python3 -B scripts/test_clean_checkout.py` -> `Ran 1 test in 0.968s` / `OK` (exit 0). The test creates an isolated tree with `(not published)`, then proves clean checkout exits 1 and logs `missing references: 1`; after creating the file it exits 0 and logs `missing references: 0`.
`node scripts/test_i18n.js` -> `26 passed, 0 failed (158 keys per language)` (exit 0). I removed it from clean checkout's stale known-failures text.
`python3 -B scripts/release/check_asset_refs.py` -> seven `MISSING` lines and `SUMMARY refs=121 missing=7` (exit 1, expected): bg_belltower, bg_pumpkin_field, fx_feet_chain, unit_knight_unarmed, move_step, ultimate_ready_chime, item_pickup.
Known optional dependency tests remain listed, including the omitted `test_ingest_missing.py` (Pillow). Not run: a whole clean-checkout pass on this worktree, because its outcome is already expected to fail on the seven refs and optional packages; main line runs that release check.
