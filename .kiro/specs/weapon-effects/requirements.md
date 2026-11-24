# Requirements: weapon effects v2

Module: seven presets appended to `js/particles.js`, checked by properties appended to `scripts/test_particles.js`. Design: `docs/playtest_fixes.md` section 1c. "Budget" means the 70 particles of one unit hit (all sources). No preset can be seen or heard here; everything below is about numbers, shapes and counts.

## Presets

1. `PRESET_NAMES` shall list the 27 old presets first, unchanged and in the same order, followed by the seven new ones in this order: `weapon_trail_wave`, `impact_wave`, `weapon_trail_bell`, `weapon_trail_skull`, `scythe_slash_fx`, `frost_shatter`, `bounce_ring`. (test: "old presets stay byte-identical ...")
2. The source text of `js/particles.js` before the new block and from `var PRESET_NAMES` on shall hash to the sha256 values recorded in the test (`12806d0e...` and `abedba6d...`, taken before the edit), so the old presets stay byte-identical. (same test)
3. The old presets' names and particle counts at the default options shall equal the recorded table (hand-derived from the old code; the trail presets as a range because their second particle is random), and the hash of that table shall equal the recorded value. (same test)

## Per preset

4. Each new preset shall emit at least one particle for any options (random scale 0.05 to 5, NaN scale, either team, either direction), and every particle shall have finite numbers, a valid shape, `#rrggbb` colours, alpha and fade in 0..1, and `life <= 1.0 s`. (test: "new preset <name> emits >= 1 particle ...", 300 cases each)
5. At the default options the particle count of one emit shall not exceed: `weapon_trail_wave` 3, `impact_wave` 12, `weapon_trail_bell` 2, `weapon_trail_skull` 2, `scythe_slash_fx` 14, `frost_shatter` 12, `bounce_ring` 3. At any scale (clamped to 4) no emit shall exceed 30. (same test)
6. The same seed and options shall give the same particles; the presets shall use only the builder's generator. (same test)
7. `impact_wave` shall emit exactly three rings. `weapon_trail_skull` shall add a `fx_ghostfire` sprite particle on about a third of the calls (between 25% and 42% over 3000 calls). `scythe_slash_fx` with `index` 0, 1, 2 shall send its sparks one way, the other, the first again. `frost_shatter` shall emit at least eight square shards. `bounce_ring` shall start a ring at radius 6, grow it to 54 and let it live 0.35 s. (test: "new presets: skull trail ghost-fire sprite ...")
8. The glow of the bell and skull trails shall not move ahead of the weapon (`vx x dirX <= 0`). (same test)
9. Palettes shall differ by weapon: wave lilac (blue >= red >= green), bell and bounce ring bronze or gold (red > green > blue), skull soul-green (green dominant), slash green, frost ice-blue (blue >= green >= red). (test: "new presets: palettes differ per weapon")

## Budget

10. Each of these unit-hit stacks shall emit 70 particles or fewer (worst of 50 seeds, real emits): javelin (`hit_sparks` 0.9, `impact_burst` 0.8, `sprite_impact_flash`, `frost_shatter`, `sprite_stardust`); bride (`impact_wave`, flash); reaper skull; the three reaper slashes together; the bell with the reduced stack (`impact_burst` 1, `hit_sparks` 0.8, flash 1.2, `landing_ring_dust` 0.5, `smoke_puff` 0.5); shield bounce (`bounce_ring`, `shield_ricochet_sparks` 0.5, `landing_ring_dust` 0.5). (test: "each weapon unit-hit stack stays at 70 particles or fewer")
11. The bell stack as written in `docs/playtest_fixes.md` (`impact_burst` 1.4, `hit_sparks` 1.0, flash, `landing_ring_dust` 0.8, three `smoke_puff` 0.7) shall be reported as over the budget (95 particles with the old presets). (same test, as a finding)
12. All new presets shall pass the existing generic properties (all presets are looped there), including drawing with the stub canvas.

## Known gaps (stated, not hidden)

13. `bounce_ring` is a circle, not the flat ellipse of the design, because `js/particles_draw.js` has no `squash` and may not be edited in this task.
14. `impact_wave` has no 80 ms stagger between rings, because the system has no start delay; the rings start at different radii instead.
15. `scythe_slash_fx` draws sparks only; the crescent pictures `reaper_slash_1..3` are the game's job.
