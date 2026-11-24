# Task 135 result

Changed `js/ultimate_fx.js`: `NECRO_VOLLEY_MULT`, `necroVolleyDamage`, and `necroGhostfireTrio` now emit the point, escalating three-flame volley, first-hit hallucination mark, and final fire removal.
Added `js/hallucination.js`: `apply`, `startOfTurn`, `clear`/`onKO`, and `publicState`; added its 200-seed shadow-model test in `scripts/test_hallucination.js`.
Extended `scripts/test_ultimate_fx.js`; updated Necromancer row 7 in `docs/ultimate_mapping.md` with the owner 2026-11-15 decision.
Preset substitutions: none. The timeline uses existing `weapon_charge_aura`, `sprite_ghostfire`, `hit_sparks`, `sprite_rune_circle`, and `ko_wisps` presets.

`node scripts/test_ultimate_fx.js` → `test_ultimate_fx: all 6 tests passed`
`node scripts/test_hallucination.js` → `test_hallucination: all 6 tests passed`
`node scripts/test_ultimate.js` → `test_ultimate: all 24 tests passed`
`node scripts/test_particles.js` → `48/48 properties passed`

Not run: browser integration or any `index.html` change, as excluded by this task. No network or git commands were run.
