# Requirements: wind design

Background: `docs/wind_design.md`. Every number below is checkable by a test. "The wind unit" is the value in `get_public_state.wind`, range −4..+4. "Normalised wind" `n` is `clamp(wind / 4, −1, 1)`.

## Strength and fairness

1. The game shall define one wind factor, `WIND_ACCEL = 96` (px/s² per wind unit), in `shared/constants.json`.
2. The client, the rule engine, the MCP stdio server and the built-in opponent shall read `WIND_ACCEL` from that constant and shall not contain any other wind factor (no `48`, `45.0` or `WIND_PUSH` literal).
3. The client, the rule engine and the paths returned by `get_history` shall apply wind as a horizontal acceleration: `vx += wind × WIND_ACCEL × dt` at each fixed step.
4. The wind range shall stay `WIND_MIN = −4` and `WIND_MAX = +4`.
5. When a player throws a fixed target's no-wind shot at wind ±4, the landing shall differ from the target by at least 300 px.
6. When a player corrects the power from the observed miss (one proportional step, then one secant step), the third throw shall land within 50 px of the target, for wind ±4, ±2 and ±2.4 at angles 40, 50 and 54, and shall never need power above 100.
7. While the wind is −4 (headwind), a throw at power 100 and the best angle shall reach at least 1200 px. The floor shall be raised to the largest real enemy distance once spawn positions are known; if it fails, the factor shall be lowered to 80 first.
8. The public state and the tools shall expose only the wind value. They shall not expose a landing predictor, a trial throw, or the factor as a helper.
9. If the opponent's power choice uses a fixed wind compensation or a trajectory simulator, then the design shall be treated as non-compliant with `product.md`. (Open question 5 in `docs/wind_design.md`.)

## Scene reaction

10. When the wind value changes, the wind field shall ease toward the new value with a time constant of 0.6 s and add a gust that fades with a time constant of 1.0 s.
11. The wind field shall hold at most `MAX_ITEMS = 96` items (fog puffs, dust, leaves) and shall default to `DEFAULT_COUNT = 64`; at most `MAX_FOG = 8` of them shall be fog.
12. The wind field shall draw nothing whose bounding square is closer than 1 px to any rectangle in `avoid`, and shall fade items out over the last 24 px before one.
13. When the wind is positive, the horizontal velocity of the mean leaf, dust mote and fog puff shall be positive; when it is negative, negative.
14. While the eased wind is 0, every item's horizontal speed shall be at most 15 px/s.
15. When an item leaves the field, it shall wrap to the other side, and every item centre shall stay inside `[0, width) × [0, height)` for any wind and any `dt`.
16. The wind field shall give the same state and the same draw calls for the same seed and the same calls, and shall not use `Math.random`.
17. If `dt` is not a positive finite number, then `update` shall ignore it; if `dt` is above 0.1 s, then `update` shall use 0.1 s.
18. `flameLean(w)` shall return a finite angle in `[−0.6, 0.6]` rad, linear in `w` between −4 and +4 and with the sign of `w`, for any `w` including NaN, ±Infinity and non-numbers (NaN and non-numbers give 0).
19. `swayAngle(w, t)` shall return a finite angle in `[−0.5, 0.5]` rad for any `w` and any `t`, with a mean of `−0.3 × n` rad (a hanging end swings toward the wind), and a swing that is wider at wind 4 than at wind 0.
20. When the scene effects are off (`count = 0`), the wind field shall draw nothing and the HUD indicator shall still show the wind.

## HUD and sound

21. The top bar shall show the wind with its sign and one decimal, an arrow of length `24 + 56 × |n|` px, and the colour `#cfd8ff` below 1.5, `#ffd27a` from 1.5 to below 3, and `#ff8a4d` from 3 up.
22. The wind bed shall have gain `0.015 + 0.105 × |n|` and a band-pass centre of `250 + 600 × |n|` Hz, and shall stay below the music and impact sounds. (Design only; implemented by the sound module.)
