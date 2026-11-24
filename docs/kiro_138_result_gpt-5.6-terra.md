# Task 138 result — gpt-5.6-terra

Changed `js/class_stats.js`: added `attack`, provisional `defense`, computed full-power `range`, `statsOf`, and defense-aware `hitsToKill`.
Changed `scripts/test_class_stats.js`: four-stat bounds, unchanged zero-defense matrix, 20% defense case, and range monotonicity.
Added `docs/hero_stats_table_20261115.md`; `index.html` was not edited.
Verification run:
`node scripts/test_class_stats.js` → `test_class_stats: all 12 tests passed`
`node scripts/test_sim_balance.js` → `test_sim_balance: all 27 tests passed`
`node scripts/test_ultimate_fx.js` → `test_ultimate_fx: all 6 tests passed`
Could not verify a populated Apple Hag row: `hag` has no `js/class_stats.js` profile or code-backed combat values, so the table leaves it blank rather than inventing values.
An auxiliary `node -e` display command did not run because its permission request was not answered; it was not a required verification command.
