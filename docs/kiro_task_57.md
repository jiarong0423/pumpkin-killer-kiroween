# Kiro task 57 — layered wind: strength and altitude

Read: docs/wind_design.md, docs/wind_test_record.md, scripts/verify_wind_table.py, js/wind_fx.js, scripts/sim_balance.js, scripts/mcp_game_server.py (wind constants), index.html (WIND_ACCEL, updatePhysics, simulateLandingX, drawTopHUD wind gauge), (not published) (newest rows last), (not published) notes if present.

Owner rule (2026-11-09): "give the wind a strength and a height". Today the wind is ONE signed integer per round, the same at every height (WIND_ACCEL 72 px/s^2 per notch).

OWNER ADDITION (2026-11-09, 'maybe eight directions'): the wind may blow in EIGHT directions: left, right, up, down and the four diagonals. A vertical component works as an up or down draft on the projectile. Include it in every item below (model with two components, gauge and leaves / mist showing the direction, effect on arcs, the AI rule of thumb, files to change, balance).

Design with numbers:
1. The model: wind strength (keep the signed notch scale of 1 to 4 or change it?) and an altitude profile (for example two or three bands: ground, mid, high, with a multiplier per band, or a smooth ramp). Give the formula for the acceleration at height y and the constants.
2. Reading it: what a human sees so the rule is fair (gauge with a height marker, leaves low and mist high in js/wind_fx.js moving at different speeds, a small arrow at the apex band). The AI and any external agent get exactly this public view, with the same random misreading rule (no true values).
3. Effect on arcs: landing shift per notch at 54 degrees for low arcs (power 60) and high lobs (power 90) so the owner can see the difference; check the wind-ignoring penalty (the no-simulator AI now adds 4 power units per notch).
4. The change list: every file and constant that must change together (index.html physics and simulateLandingX, the Python engines, scripts/verify_wind_table.py, scripts/sim_balance.js, (not published) tables, the sync test scripts/test_constants_sync.py) and what each test will need.
5. Balance: lobs vs flat shots, effect on the hit-rate (measured human 33 percent, AI 17 percent before the wind rule) and on match length (8 to 12 rounds).
6. A migration plan with a switch (LAYERED_WIND on/off) so the old behaviour stays available until the tests pass.
7. ANTI-CHEAT ANGLE (owner idea): a layered wind should make a leaked true coordinate worth less. Say honestly how much it helps: if the altitude profile is a fixed public formula, an agent with exact coordinates can still compute exactly; propose a per-round random profile shown only through visual cues (leaves low, mist high, a gauge with limited precision) so humans and agents must estimate it, and give the loss in hit rate for an agent that has the true coordinates but only the public wind view.
8. What you could not verify.

Write (not published) Do not edit index.html or js. Use `python3 -B` / `node` for scripts.
