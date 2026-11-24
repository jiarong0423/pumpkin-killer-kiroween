# Tasks — shared game constants

- [x] 1. Create `shared/constants.json` with the ten shared keys, using
  `index.html` values as the source of truth (wind range ±4.0 from the
  `* 8.0` span).
- [x] 2. Make `scripts/mcp_game_server.py` load `shared/constants.json` at
  import and use it for `GROUND_Y`, `GRAVITY`, `V0_PER_POWER`, and the wind
  range.
- [x] 2a. Derive `WALL_X_MIN`/`WALL_X_MAX`/`WALL_TOP_Y` from the fence fields.
- [x] 2b. Remove all hard-coded copies (`880`, `890`, `1030`, `720`, `13.5`,
  `±4.5`) and keep the rest of the behaviour unchanged.
- [x] 3. Add `scripts/test_constants_sync.py` (stdlib only) that parses the
  constants from `index.html` and asserts equality with
  `shared/constants.json`, failing on drift.
- [x] 4. Respect scope limits: no edits to `index.html`, no changes under
  `assets/`, no git commands.
- [x] 5. Write this spec (`requirements.md`, `design.md`, `tasks.md`).
- [ ] 6. Reviewer runs `python3 -B scripts/test_mcp_game.py` (left to the
  reviewer per the task; not run here).
