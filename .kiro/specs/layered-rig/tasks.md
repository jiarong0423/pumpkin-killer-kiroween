# Tasks — Layered Character Rig

- [x] 1. Implement `(not published)` as a pure, DOM-free module (browser global + Node export).
  - [x] 1.1 `validateRig` — schema, unknown layer/anchor references, missing states, bad numbers.
  - [x] 1.2 Keyframe sampling with `linear`, `easeOutCubic`, `easeInOutCubic`, `spring` easings.
  - [x] 1.3 `evalRig` returning `{ layers, anchors, events }`, layers sorted by z.
  - [x] 1.4 `releaseTime` and `muzzle`.
- [x] 2. Author rig data.
  - [x] 2.1 `(not published)` (body `unit_skeleton_unarmed`, procedural arm, spear weapon behind body).
  - [x] 2.2 `(not published)` (body `unit_bat_unarmed`, procedural arm, dagger weapon).
  - [x] 2.3 States `idle`, `charge`, `throw`, `hit` using the numbers from the current code.
  - [x] 2.4 Events: `throw.release = 0.36`; weapon visible before release, hidden after; visible again in `idle` (resupply).
- [x] 3. `(not published)` — Node `assert` tests.
  - [x] 3.1 Validation passes for both rigs; fails for broken copies.
  - [x] 3.2 `releaseTime === 0.36`.
  - [x] 3.3 Weapon invisible for every `t >= release` in `throw`.
  - [x] 3.4 Deterministic and continuous (no jump > epsilon per 1/60).
  - [x] 3.5 Anchors `hand`, `shoulder`, `projectile` exist; layers sorted by z.
- [x] 4. Write the spec (`requirements.md`, `design.md`, `tasks.md`).
- [ ] 5. Run `node (not published)` and `python3 -B scripts/test_mcp_game.py` to verify.
      (Blocked: the current non-interactive agent session cannot execute shell
      commands. The tests are authored and traced by hand; a reviewer with a
      shell can run both. MCP test is unaffected — no shared files were changed.)
