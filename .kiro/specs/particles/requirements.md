# Particles: requirements

Scope: `js/particles.js` (core), `js/particles_draw.js` (canvas drawing),
`scripts/test_particles.js` (tests). Wiring into `index.html` is out of scope
for this spec.

Terms: **system** is the object returned by `createSystem`. **Pool** is its
`particles` array. **Preset** is a named effect that emits particles.

## R1 Module shape

1. The core module shall not reference `window`, `document`, `performance`,
   `Date`, `Math.random` or any other I/O.
2. When loaded by Node, the core module shall export its API through
   `module.exports`.
3. When loaded by a browser script tag, the core module shall expose its API
   as the global `Particles`.
4. The drawing module shall use only methods and properties of the 2D context
   passed to it.
5. When loaded by a browser script tag, the drawing module shall expose
   `ParticlesDraw` and the global function `drawParticles`.

## R2 System API

1. `createSystem({seed, maxParticles})` shall return an object with `emit`,
   `update`, `particles` and `clear`.
2. Where `maxParticles` is absent or invalid, the system shall use 1500.
3. `clear()` shall empty the pool without replacing the `particles` array.

## R3 Determinism

1. The system shall draw all randomness from a mulberry32 generator seeded by
   `seed`.
2. When two systems have the same seed and receive the same sequence of
   `emit` and `update` calls, they shall hold identical particles.
3. `update` shall not consume random numbers.
4. `emit` shall not modify the `opts` object it is given.

## R4 Pool limit

1. The pool length shall never exceed `maxParticles`.
2. If an `emit` would exceed `maxParticles`, then the system shall remove the
   oldest particles first.
3. `emit` shall return the number of particles from that call that are in the
   pool afterwards.

## R5 Particle record

Every particle shall have finite numeric `x, y, vx, vy, life, maxLife, size,
sizeEnd, alpha, gravity, drag, spin, layer`, string `color` and `colorEnd` in
`#rrggbb` form, and a `shape` from `circle, glow, square, streak, ring, text`.
The record also carries `id` (increasing), `preset`, `angle`, `lineWidth`,
`fade` and `text`. `size` is the radius for circle, glow and ring, the length
for streak, the half side for square and the font size for text.

## R6 Presets

The system shall provide these presets, each taking `opts` with `dirX`
(sign decides direction), `scale` (clamped 0.1 to 4) and `team`
(`player` or `agent`):

1. `muzzle_flash`, `smoke_puff`, `impact_burst`, `hit_sparks`.
2. `poison_cloud`: green and large. It shall last `duration` seconds, or
   `rounds * secondsPerRound` (defaults 3 and 2) when `duration` is absent.
3. `poison_drip`: green drops on a poisoned unit.
4. `dart_rain`: many falling streaks across `opts.width`.
5. `shield_ricochet_sparks`, `shield_materialize_ripple` (expanding rings),
   `landing_ring_dust`.
6. `ko_wisps`: cyan and violet, rising.
7. `damage_number`: a text particle carrying `opts.text` (or `opts.amount`).

Each preset shall emit at least one particle for any `opts`, including
missing, `null`, non-numeric and non-finite values.

## R7 Preset guarantees

1. While a particle belongs to `poison_cloud`, its `color` and `colorEnd`, and
   every blend between them, shall have green above red and above blue.
2. When `dart_rain` is emitted at `x` with width `w`, every particle `x` shall
   lie in `[x - w/2, x + w/2]`.
3. When `poison_cloud` is emitted with duration `D`, every particle life shall
   be between `0.7 * D` and `D`.

## R8 Update

1. `update(dt)` shall reduce the `life` of every particle by exactly `dt`.
2. The system shall remove each particle whose `life` is zero or less.
3. `update(dt)` shall integrate position and velocity in closed form for
   constant gravity and linear drag, so that splitting `dt` into smaller steps
   gives the same state within floating point error.
4. If `dt` is not a positive finite number, then `update` shall do nothing.

## R9 Input safety

1. If the preset name is unknown, then `emit` shall throw an `Error`.
2. If `x` or `y` is not finite or exceeds 1e9 in magnitude, then `emit` shall
   add nothing and return 0.

## R10 Drawing

1. `drawParticles(ctx, particles)` shall draw layer 0 with normal blending,
   layer 1 with `lighter` blending, and layer 2 with normal blending, in that
   order.
2. `drawParticles` shall draw `ring` particles as stroked circles and `text`
   particles with `fillText`.
3. `drawParticles` shall leave the context state as it found it (balanced
   `save` and `restore`) and shall not change the particles.
4. While a particle has non-positive size or alpha below 0.004, the drawing
   module shall skip it.

## R11 Tests

`scripts/test_particles.js` shall check R3, R4, R5, R6 (emits and finite
values), R7, R8, R9 and R10 with at least 200 seeded cases per property and
exit non-zero on failure.
