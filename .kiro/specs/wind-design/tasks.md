# Tasks: wind

Done by Kiro (task 25):
- [x] `docs/wind_design.md`
- [x] `js/wind_fx.js` (requirements 10 to 19)
- [x] `scripts/test_wind_fx.js` (requirements 5, 6, 7 on a flat-ground model; 10 to 19 on the module)
- [x] this spec

Main line (needs owner answers to the open questions first; do not start before they are answered):
- [ ] 1. Add `"WIND_ACCEL": 96` to `shared/constants.json`. (Req 1, 2)
- [ ] 2. `scripts/test_constants_sync.py`: check `WIND_ACCEL` in the client and the engine. (Req 2)
- [ ] 3. `index.html`: replace both `48` literals with the constant; fix the `-5 to +5` comment. (Req 2, 3)
- [ ] 4. `scripts/mcp_game_server.py`: switch to `vx += wind × WIND_ACCEL × dt`; remove the fixed `-3.2` compensation or replace it with learning from history. (Req 2, 3, 9)
- [ ] 5. `scripts/mcp_stdio_server.py`: remove `WIND_PUSH`; use the acceleration model in `sample_path`. (Req 2, 3)
- [ ] 6. Measure the real unit spawn distances and the real character width; replace the 1200 px floor and the 100 px width in `scripts/test_wind_fx.js`. (Req 7)
- [ ] 7. Decide the AI simulator (open question 5); if removed, delete the `simulateLandingX` use for AI power. (Req 8, 9)
- [ ] 8. `index.html`: create the wind field, wire `setWind`, `update`, `draw` layers, `setAvoid` for HUD and HP bars. (Req 10 to 20)
- [ ] 9. HUD arrow, number, colour and chevrons. (Req 21)
- [ ] 10. Wire `flameLean`, `swayAngle`, flame and damage-number `vx`, and the ribbon tail drift. (`docs/wind_design.md` section 2)
- [ ] 11. Wind bed and gust in the audio module. (Req 22)
- [ ] 12. Replay the match at wind ±4 and check the agent's miss distance drops across rounds. (fairness, learning curve)
- [ ] 13. Screen test: nothing from the wind layer covers the top bar, timer, wind readout, HP bars or dock; compare calm and strong wind screenshots.
