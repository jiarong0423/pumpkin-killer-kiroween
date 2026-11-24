# Kiro 80 result (claude-sonnet-5.5)
**NOT RUN.** I had no shell, so none of the three test commands ran and there is no output tail. Files were read and edited only.
Run: `python3 -B scripts/test_mcp_game.py`, `python3 -B scripts/test_mcp_stdio.py`, `python3 -B scripts/test_constants_sync.py`

Changed:
- `shared/constants.json`: added `WALL_HIT_DMG: 8` (11 keys). `test_constants_sync.py` now parses `const WALL_HIT_DMG` from `index.html`. It does not compare `sim_balance.js` `WALL_DMG`.
- `mcp_game_server.py`: line 39 `WALL_HIT_DMG` replaces `- 20`; lines 44-45 `START_X_RANGE` (red 220..620, white 1280..1680) and `MOVE_X_LIMITS` (160..760 / 1160..1760, the page's zones); lines 105-108 `_start_x` (seeded `self.rng`, once at start). Per-round random re-placement removed from `resolve_round`.
- `mcp_stdio_server.py:69`: `TEAM_X_LIMITS = engine.MOVE_X_LIMITS` (was 100..835 / 1085..1820).
- `test_mcp_game.py`: tests 2, 3, 5 pin `red_4` x=560. New: `test_wall_loses_8_per_hit`, `test_unmoved_units_keep_x_across_rounds`, `test_start_x_ranges_and_determinism`.
- `test_mcp_stdio.py`: `test_move_uses_engine_die` expects the 760 clamp; `test_sample_path_matches_engine_landing` pins x. New: `..._did_not_move_keeps_x_across_rounds`, `test_start_x_ranges_match_the_page`, `test_only_the_move_action_changes_x`, `test_move_zones_match_the_page`.
- `.kiro/steering/tech.md`: wind 72 (page) vs 67.5 (engine), "eleven keys", "27 tests" (23 + 4 by count, not by running).

Not verified / notes:
- All of the above is unrun. Round-1 wind per seed is unchanged; wind from round 2 differs because the per-round position draws are gone.
- `eval_agent_learning.py` (outside my list) pins units to spawn, now random per seed, and its docstring is stale. Re-run before quoting numbers.
- `structure.md` still says "Ten numbers" (outside my list). Unused `x` in the spawn tables is left with a comment.
- Page comment says red range to 640, code gives 220..620; I followed the code.
