# Requirements — Layered Character Rig

## Introduction

Character animation in Pumpkin Killer is currently hard-coded inside
`index.html` (`computePose`, `drawThrowingHand`, and the inline skeleton spear
layer). This spec makes the animation data-driven, inspired by Ragnarok Online
layer composition: a character is a stack of layers (body, arm, weapon); each
frame gives every layer a transform, a draw order (z) and anchor points. A
weapon "leaves the hand" purely by its layer ceasing to be drawn at the release
frame. The engine (`(not published)`) is pure and DOM-free so it runs in the browser
and under Node for tests.

## Requirements

### Requirement 1 — Pure, portable rig engine
**User story:** As a developer, I want a DOM-free rig module, so that it runs in
the browser and under Node tests without a build step.

#### Acceptance criteria
1. WHEN `(not published)` is loaded as a plain `<script>` THEN it SHALL expose a global `Rig`.
2. WHEN `(not published)` is required under Node THEN it SHALL export the same API via `module.exports`.
3. The module SHALL NOT reference any DOM or browser-only global.

### Requirement 2 — Rig validation
**User story:** As a developer, I want to validate a rig document, so that broken
data is caught before rendering.

#### Acceptance criteria
1. WHEN `validateRig(rig)` is called with a well-formed rig THEN it SHALL return `{ ok: true, errors: [] }`.
2. WHEN a required state (`idle`, `charge`, `throw`, `hit`) is missing THEN `validateRig` SHALL return `ok: false` with an error naming the state.
3. WHEN a state track references an unknown layer id THEN `validateRig` SHALL return `ok: false` with an error naming the layer.
4. WHEN a limb layer references an anchor that does not exist THEN `validateRig` SHALL return `ok: false` with an error naming the anchor.
5. WHEN a keyframe value, `z`, `duration`, or anchor coordinate is not a finite number THEN `validateRig` SHALL return `ok: false`.

### Requirement 3 — Frame evaluation
**User story:** As a renderer, I want a per-frame layer list, so that I can draw
each layer with its transform and order.

#### Acceptance criteria
1. WHEN `evalRig(rig, state, t)` is called with normalized `t` in 0..1 THEN it SHALL return `{ layers, anchors, events }`.
2. Each entry in `layers` SHALL contain `id, x, y, rot, sx, sy, alpha, z, visible`.
3. Coordinates SHALL be art fractions of the 1024px box with forward = -x; rotations SHALL be in degrees.
4. `layers` SHALL be sorted ascending by `z` (back to front).
5. Keyframes SHALL interpolate linearly by default, and SHALL support named easings `easeOutCubic`, `easeInOutCubic`, and `spring` (damped cosine `exp(-k*q)*cos(w*q)`).
6. WHEN the same `(rig, state, t)` is evaluated twice THEN the output SHALL be identical (deterministic).
7. Between `t` and `t + 1/60` the output SHALL NOT jump by more than a small epsilon (continuity).

### Requirement 4 — Release event and weapon handoff
**User story:** As a renderer, I want a release event and weapon visibility, so
that the projectile leaves the hand at the correct frame.

#### Acceptance criteria
1. WHEN `releaseTime(rig, "throw")` is called THEN it SHALL return `0.36`.
2. WHEN a state has no `release` event THEN `releaseTime` SHALL return `null`.
3. WHEN `evalRig(rig, "throw", t)` is evaluated for any `t >= 0.36` THEN the `weapon` layer SHALL have `visible === false`, and for `t < 0.36` it SHALL be `true`.
4. In state `idle` the `weapon` layer SHALL be visible again (resupplied).

### Requirement 5 — Anchors and muzzle
**User story:** As a renderer, I want anchor points, so that limbs and the
projectile spawn at the right place.

#### Acceptance criteria
1. `evalRig(...).anchors` SHALL include `hand`, `shoulder`, and `projectile`.
2. WHEN `muzzle(rig, state, t)` is called THEN it SHALL return the `projectile` anchor position in art fractions.

### Requirement 6 — Faithful numbers
**User story:** As a maintainer, I want the rig to reproduce the existing motion,
so that the look does not change when switching to data.

#### Acceptance criteria
1. The rig SHALL use the timing and pose numbers taken from the current code without "improving" them.
2. WHEN evaluated at the release frame of `throw` THEN the body pose SHALL equal the LUNGE pose; the follow-through SHALL be `LUNGE * exp(-4.2 q) * cos(5.5 q)`, `q = (t - 0.36) / 0.64`.
3. The `hit` state SHALL reproduce `imp = exp(-5 t) * cos(9 t)` with `rot 26*imp`, `back 48*imp`, `up -6*exp(-8 t)`, `sx 1+0.05*exp(-7 t)`, `sy 1-0.07*exp(-7 t)`.

### Requirement 7 — Non-regression
**User story:** As a reviewer, I want existing tests to keep passing.

#### Acceptance criteria
1. WHEN `python3 -B scripts/test_mcp_game.py` runs THEN it SHALL still pass.
2. `index.html` and `(not published)` SHALL NOT be modified by this work.
