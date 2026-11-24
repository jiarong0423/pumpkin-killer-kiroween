---
inclusion: always
rewritten-by: Kiro, 2026-11-08
updated-by: Kiro task 18, to match the repo today
---

# Tech

> *Historical snapshot (2026-11-08): preserved to show early architecture; the final shipped build adds `js/relay_client.js`, `js/determinism.js`, team rooms (1v1–3v3), HTTP `/mcp`, partial-unit `claim`, and 183 automated tests (see `docs/ARCHITECTURE_FULL_20261124.md`).*

## Stack

- Client: plain JavaScript on an HTML canvas. The game and its rules are in `index.html`. Two helper scripts
  are loaded by it: `js/particles.js` (particle system, seeded) and `js/particles_draw.js` (canvas drawing for
  those particles). No frameworks, no bundler, no TypeScript.
- Rule engine: Python 3, stdlib only, `scripts/mcp_game_server.py`. It owns the ballistic step, the fence, wind,
  shields and the round resolution.
- MCP server: `scripts/mcp_stdio_server.py` is the standard MCP server over stdio (newline-delimited JSON-RPC 2.0:
  `initialize`, `notifications/initialized`, `ping`, `tools/list`, `tools/call`). It subclasses the engine
  (`TrackedGameState`) and does not edit it. Tools: `get_public_state`, `get_history`, `submit_action`,
  `end_turn`, `set_notes`, `get_notes`. Protocol: `docs/mcp_agent_protocol.md`. Client config for Kiro:
  `.kiro/settings/mcp.json`.
- The browser game does not call the MCP server. It runs its own JavaScript rules and AI. Do not describe the
  two as connected.
- Shared numbers: `shared/constants.json` (eleven keys, incl. `WALL_HIT_DMG = 8`) is read by the engine and checked against `index.html`.
- Tests (run from the repo root):
  - `python3 -B scripts/test_mcp_game.py` (engine, example-based)
  - `python3 -B scripts/test_mcp_stdio.py` (MCP server, 27 tests)
  - `python3 -B scripts/test_constants_sync.py` (`index.html` vs `shared/constants.json`)
  - `node scripts/test_particles.js` (particles, 32 seeded property loops with Node `assert`, 300 cases each; not
    fast-check)
  - There is no test for the browser game itself and no property test for the engine.
- Asset tooling (Python, not runtime): `scripts/bake_sprites.py`, `bake_fx.py`, `make_*.py` (gifs, muzzle flash,
  unarmed variants), and the Colab keying scripts `scripts/key_magenta_items.py` and
  `scripts/key_skeleton_poses.py`. Art generation runs on Colab (`colab/`: `jobs.json`,
  `pumpkin_assets_job.py`, `PumpkinKiller_inputs.zip`). Image scripts need numpy, Pillow and (unarmed scripts)
  OpenCV; the game and tests need none of them.

## Physics (client, `index.html`)

- Fixed step `PHYSICS_STEP = 1/60 s`, driven by an accumulator capped at 6 steps per frame. Never tie physics to
  the frame rate.
- `GRAVITY = 980`. Launch speed = `power * 13.8`, power in 0..100.
- Wind is a horizontal acceleration: tailwind uses `vx += wind * 56 * dt` and headwind uses `vx += wind * 84 * dt` (px/s² per wind unit). Wind is rerolled each round, range +/-4, one decimal.
- Canvas is 1920 x 1080 logical pixels. `GROUND_Y = 860`, fence at `x = 960`, width 130, height 250.
- Move die: `DICE_STEP_PX = 36` per pip.
- AI aiming must use the same integrator as projectiles (`simulateLandingX` mirrors the projectile update).

## Sprites and art folders

- One mirror rule for every character: art is drawn once, facing LEFT, and mirrored with `ctx.scale(-1, 1)` for
  the team that faces right. Do not add per-hero flip cases.
- Unarmed variants (`assets/units/*_unarmed.png`, made by `scripts/make_unarmed_*.py`) exist so a thrown weapon
  really leaves the hand.
- `assets/poses/`: Colab-generated skeleton action poses (`skel_windup`, `skel_release`, `skel_hit`), keyed by
  `scripts/key_skeleton_poses.py`.
- `assets/weapons/`: Colab-generated items (small shield, dart, dart bag, spear), keyed by
  `scripts/key_magenta_items.py`.
- `assets/ui/`: Colab-generated shield slabs, keyed by `scripts/key_magenta_items.py`.
- Provenance of every art folder: `docs/ASSET_PROVENANCE.md`.

## Known drift between client and engine

Launch speed, ground height, fence and wind range now come from `shared/constants.json`, and
`scripts/test_constants_sync.py` fails if `index.html` disagrees. One difference is not covered by that test.
Do not fix one side silently; ask first.

| Value | `index.html` | MCP engines |
|---|---|---|
| Wind effect | Tailwind: `vx += wind * 56 * dt`; headwind: `vx += wind * 84 * dt` (px/s² per wind unit) | Constant push: tailwind `52.5`, headwind `78.75` per wind unit; approximate by design and matched near a 1.9 s flight time |

## Conventions

- Keep functions small. Comments explain why, not what.
- Public state is a separate shape from internal state, so hidden fields cannot reach clients or agents.
- Engine code must stay deterministic for a given seed and inputs.
- Do not add dependencies without asking.
