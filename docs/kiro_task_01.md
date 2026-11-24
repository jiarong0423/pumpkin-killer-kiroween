# Kiro task 01 — shared game constants (small, to measure credit cost)

Repo: Pumpkin Killer, a turn-based artillery-style throwing game (Kiroween 2026, Costume Contest).
Two implementations of the rules exist and have drifted:

- `index.html` (browser game, plain canvas JS)
- `scripts/mcp_game_server.py` (MCP rule engine, Python)

## Do exactly this (and nothing else)

1. Create `shared/constants.json` holding the values both sides must agree on:
   `GROUND_Y`, `GRAVITY`, `V0_PER_POWER` (launch speed per power point), `FENCE_X`, `FENCE_W`,
   `FENCE_H`, `WIND_MIN`, `WIND_MAX`, `THROW_ANGLE_DEFAULT`, `TURN_SECONDS`.
   Where they live in `index.html`: `const GROUND_Y`, `const FENCE_X/FENCE_W/FENCE_H`, `const GRAVITY`,
   `const TURN_SECONDS` are plain constants; `V0_PER_POWER` is the inline `const v0 = power * 13.8;`;
   `THROW_ANGLE_DEFAULT` is `let playerAngle = 54;`; wind is `(Math.random() - 0.5) * 8.0` so range is +/-4.0
   (`WIND_MIN`=-4.0, `WIND_MAX`=4.0). Parse each of those forms in the test.
   Use the values in `index.html` as the source of truth (the browser game is the playable
   version). Fence: x center = `FENCE_X`, width = `FENCE_W`, height = `FENCE_H` measured up from `GROUND_Y`.
2. Make `scripts/mcp_game_server.py` load those values from `shared/constants.json` instead of its own
   hard-coded copies (`GROUND_Y`, `WALL_*`, `GRAVITY`, the `13.5` launch factor, wind range).
   Convert the wall rectangle from the fence fields. Keep behaviour otherwise unchanged.
3. Add `scripts/test_constants_sync.py`: a stdlib-only test that parses the constants out of
   `index.html` (regex on the `const NAME = value;` lines near the top of the script) and asserts
   they equal `shared/constants.json`. It must fail if either side drifts.
4. Do NOT edit `index.html`. Do NOT touch `assets/`. Do NOT run git commands.
5. Write the spec for this work in `.kiro/specs/shared-constants/` as `requirements.md`
   (EARS style acceptance criteria), `design.md`, and `tasks.md` (checkbox list, mark finished items).
6. Finish with a 5-line summary: files created/changed, any value that differed between the two
   sides (old server value -> new value), and anything you could not do.

Existing test to keep passing: `python3 -B scripts/test_mcp_game.py` (it will be run by the reviewer,
you do not need to run it).
