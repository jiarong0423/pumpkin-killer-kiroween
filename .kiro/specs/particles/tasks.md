# Particles: tasks

- [x] 1. Core `js/particles.js`: wrapper for Node and browser, mulberry32, pool with cap (R1, R2, R3, R4)
- [x] 2. Particle record and builder defaults (R5)
- [x] 3. Closed-form `update(dt)` with dead-particle removal (R8)
- [x] 4. Presets: `muzzle_flash`, `smoke_puff`, `impact_burst`, `hit_sparks` (R6.1)
- [x] 5. Presets: `poison_cloud`, `poison_drip` with configurable duration (R6.2, R6.3, R7.1, R7.3)
- [x] 6. Presets: `dart_rain` with clamped x range (R6.4, R7.2)
- [x] 7. Presets: `shield_ricochet_sparks`, `shield_materialize_ripple`, `landing_ring_dust` (R6.5)
- [x] 8. Presets: `ko_wisps`, `damage_number` (R6.6, R6.7)
- [x] 9. Input safety: unknown preset, bad coordinates, bad dt (R8.4, R9)
- [x] 10. `js/particles_draw.js`: three passes, additive glow layer, rings stroked, text outlined (R10)
- [x] 11. `scripts/test_particles.js`: property tests, 300 cases each (R11)
- [ ] 12. Run `node scripts/test_particles.js` and fix failures (not run by the author, no Node access in that session)
- [ ] 13. Visual pass in a browser: tune counts, sizes and colours per preset (needs eyes on a canvas)
- [ ] 14. Wire into `index.html`: load both scripts, replace `spawnParticles` calls, call `update` in the fixed step and `drawParticles` after units (separate task, `index.html` untouched here)
- [ ] 15. Set the poison duration from the real round length once the round timer is final
- [ ] 16. Demo mode: create the system with a fixed seed and replay a call script
