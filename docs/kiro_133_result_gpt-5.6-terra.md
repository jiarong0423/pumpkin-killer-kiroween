# Task 133 result — gpt-5.6-terra

Changed `docs/ultimate_mapping.md` row 7 and `docs/converge_characters.md` to the owner’s purple-flame Necromancer design; both mark the skull-and-scythe design superseded on 2026-11-15.
Changed `js/class_stats.js` (`reaperFlameProfile`, `hitsToKill`, `expectedDamageDetail`) and `scripts/sim_balance.js` (`applyHit`) to use internal id `reaper`, 23 normal damage, 2 damage for 3 non-lethal burn ticks, and no execute rule; the duplicate `necromancer` key is removed.
Changed `js/ultimate_fx.js` (`necroGhostfireTrio`, `timeline`, `damageFor`): deleted `reaperTripleSlash`; `reaper_flame_trio` aliases the retained ghost-fire trio, with three 11.5-damage flames.
Updated `scripts/test_class_stats.js`, `scripts/test_sim_balance.js`, and `scripts/test_ultimate_fx.js` for the flame profile and removed combo.
Commands run: `node scripts/test_class_stats.js`; `node scripts/test_sim_balance.js`; `node scripts/test_ultimate_fx.js`; `node scripts/test_particles.js`.
Last lines: `test_class_stats: all 8 tests passed`; `test_sim_balance: all 27 tests passed`; `test_ultimate_fx: all 5 tests passed`; `48/48 properties passed`.
Left untouched per brief: `js/particles.js` presets `scythe_slash_fx` and `weapon_trail_skull`; candidates for later cleanup.
Could not verify browser gameplay, art, sound playback, or owner approval of the task-53 working damage and burn values.
