# Tasks: Pure physics module and property-based tests

- [x] 1. Write `(not published)` (UMD, pure, `CONSTANTS`, optional `shared/constants.json`)
  - [x] 1.1 `launchVelocity`
  - [x] 1.2 `stepProjectile` (no mutation)
  - [x] 1.3 `simulateLandingX` (1/60 s, 1200 steps cap)
  - [x] 1.4 `estimatePowerForTarget` (bisection, [10, 110], 40 iterations)
  - [x] 1.5 `blockedByFence`
- [x] 2. Write `(not published)` (mulberry32, `assert`, 200+ cases)
  - [x] 2.1 Determinism
  - [x] 2.2 Monotonic in power
  - [x] 2.3 Wind sign, both throw directions
  - [x] 2.4 Estimator within 2 px (achievable and arbitrary targets)
  - [x] 2.5 Mirror symmetry
  - [x] 2.6 Fixed step, trajectory never below GROUND_Y before the stop
  - [x] 2.7 Finite landing x and power
  - [x] 2.8 Fence box
- [x] 3. Write the spec in `.kiro/specs/physics-pbt/`
- [ ] 4. Run `node (not published)` and fix any failing property
  (not run by the author; no Node access in the authoring session)
- [ ] 5. Verify that the dependency on a hand estimate in design.md (monotonic
  domain, reach below 400 px under power 30) holds; widen or narrow the
  generators if a property fails
- [ ] 6. Later, separate task: make `index.html` use `Physics` instead of its
  inline copies
