# Kiro task 06 — particle effects module (pure, testable)

Context: Pumpkin Killer, plain-JS canvas game (`index.html`). Rules and effect wishes: `docs/game_mode.md`. Effects are currently
ad-hoc `spawnParticles(...)` calls. We want one reusable module with presets. The owner stresses particle effects and interaction feel.

## Do exactly this
1. Create `js/particles.js`: DOM-free core (works in Node via `module.exports` and in the browser as global `Particles`):
   - `createSystem({seed, maxParticles: 1500})` -> `{ emit(presetName, x, y, opts), update(dt), particles, clear() }`
   - Seeded PRNG (mulberry32) so the same seed + same calls give identical particles (needed for tests and for the demo mode).
   - Fixed pool: never exceeds `maxParticles` (drop the oldest when full).
   - Each particle: `{x,y,vx,vy,life,maxLife,size,sizeEnd,color,colorEnd,alpha,gravity,drag,shape,spin,layer}`.
   - Presets (each a function of `opts` such as direction `dirX`, `scale`, `team`): `muzzle_flash`, `smoke_puff`, `impact_burst`,
     `hit_sparks`, `poison_cloud` (green, large area, lingers 3 rounds worth of seconds: configurable), `poison_drip` (green drops on a poisoned unit),
     `dart_rain` (many streaks falling over an area width `opts.width`), `shield_ricochet_sparks`, `shield_materialize_ripple`
     (expanding ring), `landing_ring_dust`, `ko_wisps` (cyan/violet ghost fire rising), `damage_number` (text particle with `text`).
2. Create `js/particles_draw.js`: `drawParticles(ctx, particles)` using only the 2D canvas API (additive blending for fire/sparks,
   normal for smoke/text, rings drawn as stroked circles). No DOM access besides the ctx passed in.
3. Create `scripts/test_particles.js` (Node `assert` only, seeded property tests, at least 200 cases each):
   determinism per seed; pool cap never exceeded; every preset emits >= 1 particle and all values finite; life strictly decreases and
   dead particles are removed; `poison_cloud` colors stay in the green hue range (g channel dominant); `dart_rain` x positions lie
   inside [x - width/2, x + width/2]; `update(dt)` with dt split in many small steps gives the same result as one 1/60 step sequence within a tolerance.
4. Spec in `.kiro/specs/particles/` (`requirements.md` EARS, `design.md`, `tasks.md` checkbox list).
5. Do NOT edit `index.html` or anything outside `js/particles*.js`, `scripts/test_particles.js`, `.kiro/specs/particles/`. No git commands.
6. Finish with a 6-line summary: files, presets, any property you doubted, what you could not run (you cannot run Node; the reviewer will).
