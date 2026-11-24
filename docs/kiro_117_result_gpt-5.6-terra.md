# Task 117 result — gpt-5.6-terra

Changed `js/ultimate_fx.js`: `brideSoulDirge`, `hunchbackTowerToll`, `reaperTripleSlash`, `necroGhostfireTrio`, their `timeline()` registrations, and damage helpers.
Changed `scripts/test_ultimate_fx.js`: named-timeline, preset, order, canvas-boundary, damage-total, purity, and 100-case seeded-property coverage.
INVENTED constants: `BRIDE_NORMAL_DAMAGE = 12`, `HUNCHBACK_NORMAL_DAMAGE = 22`, `REAPER_NORMAL_DAMAGE = 18` (each marked `INVENTED, owner to confirm`).
Preset substitutions: bride rings use `weapon_trail_wave`; toll ground ring, shockwave, and dust use `bounce_ring`, `impact_wave`, and `landing_ring_dust`; reaper uses `scythe_slash_fx`; necromancer fires use `sprite_ghostfire`.
Verified: `node scripts/test_ultimate_fx.js`
Last line: `test_ultimate_fx: all 10 tests passed`
Verified: `node scripts/test_ultimate.js`
Last line: `test_ultimate: all 24 tests passed`
Verified: `node scripts/test_particles.js`
Last line: `48/48 properties passed`
Not verified: browser/page wiring and visual rendering; this task intentionally did not edit `index.html`.
