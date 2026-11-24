# Kiro task 25 - design the wind: how strong, and how the scene reacts (design + one JS module + tests)

## Why
The owner played and said: "the wind factor does not feel big", and "the reaction should be inside" (visible in the scene, not only a number at the top). Read `(not published)` first.
You design the wind; the main line integrates your module into `index.html` and the rule engine and re-tests everything.

## Facts (measured by the main line with the game's own integrator, power 65, angle 50, flight about 1.4 s)
- Today: acceleration = wind * 48 px/s^2 (client `index.html`, `windValue * 48 * dt` and `wind * 48 * dt`); the rule engine `scripts/mcp_game_server.py` uses `wind * 45.0` as a velocity push and `wind * -3.2` power compensation for its built-in AI; `scripts/mcp_stdio_server.py` has `WIND_PUSH`. Wind range is -4..+4 (`shared/constants.json`).
- Landing shift at wind -4 / +4 versus no wind (no-wind landing 807 px): factor 48 -> 617 / 998 (-190 / +191); factor 96 -> 426 / 1188 (-381 / +381); factor 140 -> 252 / 1363 (-555 / +556). The playfield is 1920 px wide with a fence in the middle.
- Wind is drawn today only as a number and an arrow in the top bar.

## Do exactly this
1. Read `(not published)`, `docs/game_mode.md`, `(not published)` (principle 6: wind in two channels), `docs/mcp_agent_protocol.md`, `shared/constants.json`, and the wind code named above (read only).
2. Write `docs/wind_design.md`:
   a. **Strength**: recommend ONE wind factor (and whether the range stays -4..+4) with reasons, using the numbers above; say what happens to the fence, the shield and the agent's learning curve; give the cheap test that decides it (for example: at max wind a player who ignores the wind should miss a fixed target by at least one character width, and a player who corrects should hit within three throws).
   b. **Scene reaction** (the owner's "reaction inside"): what moves with the wind and how much: drifting leaves and ghost-dust, fog banks, candle and ghost-fire flames leaning, hanging lanterns / branches swaying, the flight ribbon bending, floating text drifting. For each: speed and lean as a function of wind (linear / clamped), count budget (the clean-screen budget: nothing covers HP bars, wind, timer), draw layer, and a calm-wind look versus a strong-wind look.
   c. **HUD**: how the top-bar indicator should change (arrow length, number, colour at strong wind) without clutter.
   d. **Sound**: how the wind is heard (a low bed whose volume and pitch follow the strength; gusts at round start). Design only; the audio module belongs to the sound design.
   e. **Agent fairness**: the agents must see the same public wind value and the same factor from one shared constant; list every file that must read the same constant.
   f. **Open questions** for the owner, each with your recommendation, answerable in one word.
3. Write `js/wind_fx.js` (UMD like `js/particles.js`: Node `module.exports` and browser global `WindFx`): `createWindField({width, height, seed, count})` with `setWind(w)`, `update(dt)`, `draw(ctx)` (leaves / ghost-dust / fog drifting with the wind, deterministic from the seed, no `Math.random`, no DOM, 2D canvas calls only), `flameLean(w)`, `swayAngle(w, t)` helpers, and a hard particle budget. It must keep everything off the HUD rectangles you pass in `avoid: [[x0,y0,x1,y1], ...]`.
4. Write `scripts/test_wind_fx.js` (Node `assert`, a recording stub canvas): determinism for the same seed, count never above the budget, nothing drawn inside an avoid rectangle, drift direction follows the sign of the wind, zero wind drifts only gently, wrap-around keeps every item inside the field, `flameLean` and `swayAngle` are clamped and finite for any wind including NaN. Run `node scripts/test_wind_fx.js` and quote the real last line.
5. Write the spec `.kiro/specs/wind-design/` (requirements in EARS form, design, tasks; the factor and the budget as numbers a test can check).
6. Do not touch `index.html`, `assets/`, other `js/` files, or other scripts. Do not use git. Do not create images.
7. Finish with a 6-line summary and say what you could not verify (you cannot see the screen).
