# Particles: design

## Files

| File | Role |
|---|---|
| `js/particles.js` | Pure core: PRNG, pool, presets, integration. UMD-style wrapper. |
| `js/particles_draw.js` | `drawParticles(ctx, particles)`, colour interpolation. |
| `scripts/test_particles.js` | Seeded property tests, Node `assert` only. |

Plain JS (ES2015 plus `Math.imul`, `Math.expm1`, `Object.assign`), no build
step, loaded with `<script src>` in the browser. This follows the task for
the current prototype. `.kiro/steering/tech.md` describes a TypeScript
layout; porting later is mechanical because there is no DOM or global state.

## Data flow

```
game code --emit(name, x, y, opts)--> preset(builder, x, y, opts) --> pool (array, oldest first)
game loop --update(dt)--------------> remove dead, integrate survivors
render    --drawParticles(ctx, pool)--> 3 passes: BODY, GLOW (lighter), TEXT
```

## Pool

`particles` is one array, oldest first, mutated in place so references stay
valid. `emit` pushes, then `splice(0, excess)` once if over `maxParticles`.
`update` compacts survivors in place. Objects are not recycled: a recycled
object could change under a caller holding a reference, and 1500 small
objects are cheap. If profiling shows GC spikes, add a free list behind
the same API.

## Determinism

`mulberry32(seed)` is created per system. Only `emit` calls it, in a fixed
order inside each preset (explicit loops, no object key iteration).
`update` is RNG free. `clear()` keeps the RNG state, so a demo that clears and
replays must create a new system to repeat itself.

## Integration (why dt-splitting is exact)

For `dv/dt = g - k v` the exact step is

```
e = exp(-k dt),  f = (1 - e) / k,  vt = g / k
x += vx * f                  vx *= e
y += vt * dt + (vy - vt) * f vy  = vt + (vy - vt) * e
```

When `k <= 1e-4` it falls back to `x += vx dt; y += vy dt + g dt^2 / 2;
vy += g dt`, also exact. Size, colour and alpha are not stored per step. They
are functions of `t = 1 - life / maxLife`, computed at draw time. Life is
decremented by exactly `dt`. The only possible disagreement between a coarse
and a fine run is a particle whose life is within float error of zero.

## Presets

`opts` is copied and normalised: `dirX` to -1 or 1 (negative means left),
`scale` to `[0.1, 4]`, `team` to `player` or `agent`. Counts grow with
`sqrt(scale)`, sizes and speeds linearly. Team only recolours
`muzzle_flash`, `impact_burst`, `hit_sparks` and the default `damage_number`
colour.

`dirX` means: firing direction (`muzzle_flash`), drift direction
(`smoke_puff`), direction the projectile was travelling (`impact_burst`,
`hit_sparks`, `shield_ricochet_sparks`; sparks leave the opposite way).

| Preset | Layers | Shapes | Notes |
|---|---|---|---|
| `muzzle_flash` | GLOW | glow, circle, streak | cone of 10 streaks along `dirX` |
| `smoke_puff` | BODY | glow | grey, rises, grows |
| `impact_burst` | GLOW, BODY | glow, ring, circle, square, glow | flash, ring, embers, debris, dust |
| `hit_sparks` | GLOW | glow, streak | back-scatter, gravity 900 |
| `poison_cloud` | BODY, GLOW | glow, circle | ellipse of radius 90 x 0.55 vertical, `duration` seconds |
| `poison_drip` | BODY, GLOW | circle, glow | 4 drops and a bubble per call |
| `dart_rain` | GLOW | streak | start height 0.6..1.4 x `height`, life = fall time, no drift |
| `shield_ricochet_sparks` | GLOW | glow, streak | cyan-white |
| `shield_materialize_ripple` | GLOW | ring x3, streak, circle | rings reach 0.35, 0.55, 0.8 x `width` |
| `landing_ring_dust` | GLOW, BODY | ring x2, glow | dust leaves sideways |
| `ko_wisps` | GLOW | glow | cyan and violet, floats up |
| `damage_number` | TEXT | text | rises and slows (drag 2.6) |

Poison lifetime: `duration` or `rounds * secondsPerRound` (3 and 2, so 6 s by
default, a guess; set it from the real round length). Each particle lives
70% to 100% of it.

`dart_rain` places x with `clamp(lo + rand * width, lo, hi)` so floating point
rounding cannot push a streak outside the area.

## Drawing

Three passes over the pool by `layer`. Glow particles use a radial gradient
(one allocation per soft particle per frame; acceptable at 1500, the first
thing to optimise if needed). Rings are stroked circles with an ease-out
radius. Streaks are lines along the velocity, or along `angle` when still.
Text is outlined, then filled. The module saves and restores the context
once, not per particle, except for rotated squares.

## Testing

Properties in `scripts/test_particles.js`, 300 cases each, seeded with
mulberry32 so failures reproduce:

determinism and seed sensitivity; pool cap and drop-oldest by id; each preset
emits >= 1 finite particle; life decreases exactly by `dt` and dead are
removed and the system drains; green poison colours including blends;
poison lifetime window; `dart_rain` bounds; dt splitting within 1e-6;
input safety; drawing against a recording stub context.

## Open points

- Round length in seconds for `poison_cloud` (default 6 s total is a guess).
- Whether `team` should mean attacker or victim for `hit_sparks`. The code
  treats it as the attacker's colours.
- Ultimate effects are unconfirmed in `docs/game_mode.md`. These presets are
  visual only and carry no damage, radius or cooldown rules.
