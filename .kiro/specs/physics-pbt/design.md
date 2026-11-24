# Design: Pure physics module and property-based tests

## Files

- `(not published)`: the module. UMD wrapper: `module.exports` in Node, global
  `Physics` in the browser.
- `(not published)`: property tests. Run with
  `node (not published)`.
- `index.html` is not touched. Switching it to `Physics` is a separate task.

## Module

State is `{x, y, vx, vy}` in screen coordinates (+y down). All functions are
pure and take plain numbers or plain objects.

| Function | Notes |
| --- | --- |
| `launchVelocity(power, angleDeg, dirX)` | `{vx, vy}`, speed `power * 13.8` |
| `stepProjectile(state, wind, dt)` | semi-implicit Euler, returns a new state |
| `simulateLandingX(power, startX, startY, dirX, angleDeg, wind)` | loops `stepProjectile` at 1/60 s, max 1200 steps |
| `estimatePowerForTarget(startX, startY, targetX, dirX, angleDeg, wind)` | bisection, power in [10, 110], 40 iterations |
| `blockedByFence(x, y, fence)` | box test, inclusive edges; `fence` defaults to `CONSTANTS.FENCE` |

Constants: `GROUND_Y 860`, `GRAVITY 980`, `LAUNCH_SPEED_PER_POWER 13.8`,
`WIND_ACCEL_PER_UNIT 48`, `WIND_MAX 4`, `DEFAULT_ANGLE_DEG 54`,
`STEP_DT 1/60`, `MAX_STEPS 1200`, `POWER_MIN 10`, `POWER_MAX 110`,
`ESTIMATOR_ITERATIONS 40`, `FENCE {x 960, width 130, height 250}`.

Source of constants: `shared/constants.json` exists on another branch, not
here. In Node the module reads it when present and takes finite numeric values
for matching key names; the key names of that file are not known yet, so
unmatched keys silently fall back to the literals. The browser always uses the
literals. A comment in `(not published)` states this.

## Landing is a staircase in power

The game returns the x of the first step at or below the ground, not an
interpolated crossing. Consequences:

- Within one landing step `n`, x is linear and increasing in power.
- When power crosses the value where the landing step changes from `n` to
  `n+1`, x jumps by `vx * dt` (about 5 to 15 px at the ranges in the game).
  Segment length and jump are about equal, so roughly half of all target
  positions fall in a jump that no power hits.
- Hence "lands within 2 px of any reachable target" is false in general. The
  test splits it in two:
  - achievable target (built from a real throw): within 2 px, strict.
  - arbitrary target between the reach at power 10 and at power 110: within
    2 px, or the estimator returns the edge of a jump larger than 2 px
    (bracket check at power +/- 1e-10). The test prints how many cases
    were of the second kind.

The module keeps the game's behavior on purpose. Interpolating the crossing
would make the AI aim for a point the real projectile does not land on.

## Domain of the monotonic property

Wind does not change `y`, so the landing step does not depend on wind. For a
fixed step, x grows with power. Across a step change, x grows only if
`vx > 0` at landing. With a strong headwind and a low power, `vx` reverses
before landing, and x then drops across the jump, so strict monotonicity fails
in a corner. Hand estimate: wind 4 against the throw, angle 54, drop 100 px,
power 10 reverses at about 0.42 s and lands at about 0.58 s.

The monotonic test therefore uses default angle, power 30 to 110 and a drop of
60 to 160 px. At power 30 and a drop of 160 px, `vx` reverses after about
1.27 s and the throw lands after about 1.01 s. The estimator bisects over
[10, 110], but with targets at 400 px or more the low powers all land short
of the target, so the non-monotone corner does not affect the result. That
reach bound (under 400 px for power below 30) is a hand estimate.

## Tests

Seeded mulberry32. Per-case seed = `BASE_SEED + (i+1) * 0x9e3779b1`.
`PBT_SEED`, `PBT_CASES` (minimum 200, default 300) and `PBT_REPLAY` (run one
case with a printed seed) are environment variables. A failure prints the
property, the seed and the inputs as JSON, and sets exit code 1.

Properties: see requirements section 4. Tolerances: 2 px for the estimator,
1e-6 px for mirror symmetry (the only error source is rounding of
`startX + delta`). Strict comparisons elsewhere.

## Not covered

- Collision with units, shields or the fence during flight (only the fence
  box test exists).
- Equivalence with `index.html` beyond the formulas copied here.
- Any angle other than the default for the monotonic and estimator properties.
