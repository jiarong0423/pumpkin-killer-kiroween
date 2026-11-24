# Requirements: Pure physics module and property-based tests

## Introduction

The browser game integrates projectile flight inside `index.html`. This spec
moves that math into `(not published)`, a pure module that runs in Node and in the
browser, and pins its behavior with seeded property-based tests. `index.html`
is not changed by this spec.

## Requirements

### 1. Pure module

**User story:** As a developer, I want the flight math in one DOM-free module,
so that I can test it without a browser and reuse it for the AI aim.

1. THE module SHALL export `launchVelocity`, `stepProjectile`,
   `simulateLandingX`, `estimatePowerForTarget`, `blockedByFence` and one
   `CONSTANTS` object.
2. THE module SHALL NOT read or write the DOM, the clock or any random source.
3. WHEN the module is loaded with `require` in Node, THEN it SHALL return the
   exports through `module.exports`.
4. WHEN the module is loaded by a script tag in the browser, THEN it SHALL
   define a global `Physics` with the same exports.
5. WHEN `shared/constants.json` exists in Node, THEN the module SHALL use its
   finite numeric values for matching keys. IF the file does not exist, THEN
   the module SHALL use the literal values from `index.html`.
6. `stepProjectile` SHALL return a new state and SHALL NOT change its input.

### 2. Same integration as the game

**User story:** As a player, I want the AI's aim to use the same physics as my
throws, so that its misses come from its aim error and not from a model
mismatch.

1. WHEN a projectile is stepped, THEN the module SHALL apply, in this order,
   `vx += wind * 48 * dt`, `vy += 980 * dt`, `x += vx * dt`, `y += vy * dt`.
2. THE launch speed SHALL be `power * 13.8`, with `vx = v0 * cos(angle) * dirX`
   and `vy = -v0 * sin(angle)`.
3. WHEN `simulateLandingX` runs, THEN it SHALL step with `dt = 1/60` and stop
   at the first step with `y >= GROUND_Y` and `vy > 0`, or after 1200 steps.
4. THE landing x SHALL be the x of the landing step, without interpolation.
5. `blockedByFence` SHALL return true WHEN `x` is within half the fence width of
   the fence center, inclusive, and `y >= GROUND_Y - fence.height`.

### 3. Aim estimator

**User story:** As a sub-agent, I want a power estimate for a target, so that I
can aim with the public wind value.

1. WHEN `estimatePowerForTarget` runs, THEN it SHALL bisect power in
   `[10, 110]` for 40 iterations on the landing distance in the throw direction.
2. THE returned power SHALL be inside `[10, 110]`.
3. WHEN the target x is the landing x of some throw with power in `[30, 110]`
   at the default angle, THEN the estimator SHALL land within 2 px of it.
4. WHEN the target sits in a landing jump (see design), THEN the estimator
   SHALL return the power at the edge of that jump.

### 4. Properties checked by `(not published)`

1. THE test script SHALL use a seeded mulberry32 generator, Node `assert` and
   no npm package.
2. THE test script SHALL run at least 200 random cases per property.
3. IF a case fails, THEN the script SHALL print the property name, the case
   seed and the inputs, and SHALL exit with a non-zero code.
4. THE script SHALL check these properties:
   1. Determinism: the same inputs give an identical landing x.
   2. Monotonic: for default angle, power in `[30, 110]` and a drop of 60 to
      160 px, landing distance strictly increases with power.
   3. Wind sign: a wind blowing in the throw direction increases the landing
      distance and one blowing against it decreases it, for both directions.
   4. Estimator: for wind in `[-4, 4]` and target distance in `[400, 1400]`,
      the landing is within 2 px of the target, except where the target falls in
      a landing jump.
   5. Symmetry: `(dirX, wind) -> (-dirX, -wind)` mirrors the landing distance
      within 1e-6 px.
   6. Fixed step: two runs at `dt = 1/60` give identical trajectories, and
      every point before the stop condition has `y < GROUND_Y`.
   7. Sanity: landing x and estimated power are finite for all generated inputs.
   8. Fence: points in the fence box are blocked, points outside are not.
