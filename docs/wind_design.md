# Wind design (Kiro task 25)

Owner feedback (`(not published)`): "the wind factor does not feel big" and "the reaction should be inside" (visible in the scene, not only a number at the top). Settled items in that log are not re-opened here.

Sources read: `owner_feedback_log.md`, `game_mode.md`, `mcp_agent_protocol.md`, `shared/constants.json`, `js/particles.js`, and the wind code in `index.html`, `scripts/mcp_game_server.py`, `scripts/mcp_stdio_server.py`. **`(not published)` does not exist in this checkout**, so principle 6 (wind in two channels) was not read. Section 2 and 4 follow the brief's wording (a visible channel in the scene and a heard channel); check them against that principle when the file is available.

Code: `js/wind_fx.js` (scene layer and helpers), `scripts/test_wind_fx.js` (tests), `.kiro/specs/wind-design/` (spec).

## 0. Finding: the client and the engine use two different wind models

| Where | Model | Effect of wind 4 on a 1.4 s flight |
|---|---|---|
| `index.html` (`vx += wind * 48 * dt`, in `updatePhysics` and `simulateLandingX`) | acceleration, 48 px/s² per wind unit | about 190 px (measured by the main line) |
| `scripts/mcp_game_server.py` (`cur_x += (vx + wind * 45.0) * dt`) and `scripts/mcp_stdio_server.py` (`WIND_PUSH = 45.0`, used by `sample_path`) | constant velocity offset, 45 px/s per wind unit | about 45 × 4 × 1.4 = 252 px (my arithmetic, not measured) |

`game_mode.md` says wind is a horizontal acceleration, so the client model is the confirmed one. The engine's re-integration (and the paths agents read in `get_history`) therefore disagrees with what the player sees. The recommendation below uses the acceleration model everywhere.

## 1. Strength

**Recommendation: one factor, `WIND_ACCEL = 96` px/s² per wind unit, range stays −4..+4.** That doubles today's 48.

Numbers (power 65, angle 50, flight about 1.4 s, from the brief; no-wind landing 807 px, field 1920 px wide):

| Factor | Landing at −4 / +4 | Shift | Band the same throw sweeps | Share of field |
|---|---|---|---|---|
| 48 (today) | 617 / 998 | ±190 | 381 px | 20 % |
| **96 (recommended)** | 426 / 1188 | ±381 | 762 px | 40 % |
| 140 | 252 / 1363 | ±555 | 1111 px | 58 % |

Why 96:
- At 48 the wind moves a landing by about two character widths (assuming a width of about 100 px; the art size was not measured). The owner already finds that too small. At 96 it moves about four. At 140 more than half the field is in play and the wind decides the shot, not the player.
- Range stays −4..+4. Changing the range and the factor together makes the two hard to tell apart in playtests, and the shared constant, the server draw `uniform(WIND_MIN, WIND_MAX)` and the `-5 to +5` comment in `index.html` (stale) all stay valid.
- One wind unit moves a landing by about 95 px. A player can read "wind 2 = about 190 px" and correct by feel. That is the learning loop the product wants.

What happens to:
- **Fence** (130 px wide at x 895..1025, 250 px tall). The same throw sweeps about 6 fence widths at 96, against about 3 at 48. A headwind pulls a lob down into the fence face; a tailwind carries it over. The fence gets hit and destroyed more often in a headwind. That is intended: the wind changes which throws the fence matters for.
- **Floating shield.** A remembered path shifts by about 94 px per wind unit of difference (0.5 × 96 × 1.4²). If the wind changed by 2 or more units since that throw, the path is off by at least 188 px, more than the default 160 px effect width in `shield_materialize_ripple`. The shield pays off most when the wind is steady. Mitigation: show `wind_at_throw` (already in `get_history`) next to each remembered path in the Defend panel. See open question 4.
- **Agent learning curve.** The agent sees `wind` and each past throw's `wind_at_throw` and landing. At 95 px per wind unit, the wind effect is larger than any plausible aim error, so a regression of landing error on wind is learnable from 2 to 3 of its own throws. At 48 it would be about half as large and harder to separate from noise. I could not find the published aim-error value in the files read, so the ratio is unchecked (see section 5, last bullet).
- **Reach into a headwind.** With flat-ground arithmetic (`scripts/test_wind_fx.js`), full power at the best angle reaches 1318 px into a −4 headwind. A steep 60° lob reaches only 534 px, against a 710 px no-wind target at 65 power. So a steep lob into a strong headwind cannot be fixed by power alone; the player has to lower the angle. That is a real skill step, but it must not make an enemy unreachable. The reach floor below is the guard.

**The cheap test that decides it** (all four are in `scripts/test_wind_fx.js`, flat-ground model, the client's own per-step integration):
1. Ignoring max wind (±4) misses a fixed target by at least 3 character widths (300 px). At 96 it misses by about 376 px. At 48 it would be about 190 px and fail.
2. A player who corrects (one proportional correction, then one secant correction) lands within 50 px on the third throw for wind ±4, ±2, ±2.4 at angles 40, 50, 54. Measured worst case: 44.8 px (wind −4, angle 54). Passing needs a hit radius of at least 45 px; the 50 px radius (half a character width) is my assumption.
3. The same corrections never need more than power 100.
4. Reach floor: full power into a −4 headwind reaches at least 1200 px. Measured 1318. The 1200 px floor is a placeholder. **Replace it with the real largest enemy distance from the unit spawn positions**, which I did not read. If it fails, lower the factor to 80 before touching the range.

## 2. Scene reaction

All values use the normalised wind `n = clamp(w / 4, −1, 1)` and strength `s = |n|`. Positive `w` blows toward +x. The field in `js/wind_fx.js` eases toward a new wind with a 0.6 s time constant and adds a gust (up to +50 % speed, fading with a 1 s time constant) when the wind changes, so a new round's wind arrives as a gust and does not snap.

Clean-screen budget: **64 drifting items by default, 96 at most** (6 fog puffs, 26 leaves, 32 dust at the default). Nothing is drawn closer than 1 px to a keep-out rectangle, and items fade out over the last 24 px before one. Pass these rectangles with `avoid` or `setAvoid`: the top bar, the timer, the wind readout, the bottom dock, and every unit's HP bar. HP bars move when units move (36 to 216 px steps), so call `setAvoid` after a move. Setting `count: 0` turns the layer off.

| Element | Moves with wind as | Count | Layer | Calm | Strong (|w| = 4) |
|---|---|---|---|---|---|
| Fog banks (soft round puffs, radius 90 to 170 px, low in the frame, y at 72 % to 96 % of height) | `vx = g + n × 90 × k`, k 0.6 to 1.0, g within ±4 px/s. Linear, clamped | 6 (cap 8) | behind characters, over the ground | alpha 0.05, thin and blue-white, almost still | alpha 0.09, a little denser and paler, crawling at about 50 to 90 px/s |
| Ghost-dust (violet, cyan and gold motes, additive) | `vx = g + n × 260 × k`, k 0.6 to 1.2, g within ±10. Rises 8 to 24 px/s. Linear, clamped | 32 | over the background, behind characters | round motes, drifting up slowly | motes stretched to 3.5× along the wind, alpha up by 30 %, sweeping at about 150 to 310 px/s |
| Dry leaves (brown ellipses, tumbling) | `vx = g + n × 420 × k`, k 0.7 to 1.3, g within ±14. Fall 40 to 90 px/s. Spin ×(1 + 3s). Linear, clamped | 26 | in front of characters, under the HUD | fall almost straight, tumble slowly | cross the screen in about 3.5 to 6.5 s, nearly horizontal, tumble 4× faster |
| Candle and ghost-fire flames | tip leans by `flameLean(w)` = 0.6 rad × n (34° at max), linear, clamped. Flame particles also get `vx += n × 60` px/s | no new items | on the flame sprite | upright, flicker only | leaning 34° and streaming sparks downwind |
| Hanging lanterns and branches | `swayAngle(w, t)`: mean lean −0.30 rad × n, plus a swing of (0.04 + 0.10s) rad at 0.6 Hz and 0.02s rad at 1.7 Hz. Clamped to ±0.5 rad. Positive wind gives a negative angle (the free end swings toward +x) | at most 6 on screen | behind characters | gentle 2° to 3° swing around upright | leaning 17° with a 9° swing |
| Flight ribbon (the real path, drawn after the throw, fading after impact) | the path itself is never moved; it is the true trajectory. The fading tail drifts downwind by `n × 40 px × (fade progress)` and gains a ripple of 2 to 6 px. Clamped at 40 px | n/a | existing ribbon layer | straight tail | tail bends up to 40 px downwind as it fades |
| Floating text (damage numbers) | add `n × 60` px/s to the start `vx` of the `damage_number` particle. At most about 25 px of extra drift over its 1.1 s life | n/a | text layer | rises straight | rises with a small lean |

Calm means `|w| < 1`. All motion is a function of the wind value and time only. The only random draw is placing the items once from the seed, so replays and tests are exact.

## 3. HUD (top bar)

Keep the existing arrow and number, change how they behave. No extra widgets.
- **Number**: always show the sign (`+3.2`, `−1.0`, `0.0`), one decimal.
- **Arrow**: length `24 + 56 × |n|` px (24 px at calm, 80 px at max), pointing the way the wind blows. At 0 show a short dot instead of an arrow.
- **Motion**: three small chevrons slide along the arrow in the wind direction at `60 + 120 × |n|` px/s. They stop at 0.
- **Colour by strength**: `|w| < 1.5` pale blue-white `#cfd8ff`; `1.5 ≤ |w| < 3` warm gold `#ffd27a`; `|w| ≥ 3` ember orange `#ff8a4d`. Colour changes only the arrow and the number, never the bar background.
- **Round start**: when a new wind arrives, the arrow grows from the old length to the new one in 0.4 s, in step with the gust (section 4).
- The scene layer is the second channel; the HUD alone must still be enough for a player who turns the scene effects off.

## 4. Sound (design only; the audio module belongs to the sound design)

- **Bed**: looped filtered noise. Level rises with strength: gain `0.015 + 0.105 × s` (0.015 calm, 0.12 at max), band-pass centre `250 + 600 × s` Hz. Pitch and level both follow the eased wind (the same 0.6 s ease as the visuals).
- **Gust at round start**: when the wind changes, swell the bed by up to ×1.8 for about 1.2 s and sweep the centre up by about 200 Hz, scaled by the size of the change. No gust when the wind stays the same.
- **Whistle**: a quiet narrow band at 900 to 1400 Hz fading in only above `s = 0.75`.
- **Pan**: `0.6 × n`, so the wind is heard from the side it blows toward. Keep it under the music and under impact sounds; the bed must never mask a hit.
- Only synthesized or verified CC0 sources, as for all sound.

## 5. Agent fairness

The agents must see the same public wind value and the same factor, from one constant.

- Add `WIND_ACCEL: 96` to `shared/constants.json`. Files that must read it:
  1. `shared/constants.json` (the source).
  2. `index.html`: the two uses of `48` (`updatePhysics`, `simulateLandingX`). Also fix the `-5 to +5` comment on `let wind`.
  3. `scripts/mcp_game_server.py`: `wind * 45.0` in the integration loop and the `-3.2` power compensation of the built-in AI.
  4. `scripts/mcp_stdio_server.py`: `WIND_PUSH = 45.0` and its use in `sample_path`. It must switch from a velocity offset to the acceleration model so `get_history` paths match what the player sees.
  5. `scripts/test_constants_sync.py`: add `WIND_ACCEL` to the keys it checks against the client and the engine.
  6. `js/wind_fx.js` does not need the factor. It takes a wind value in game units and the maximum (`windMax`, default 4, from `WIND_MAX`).
- The public state exposes `wind` only. It must not expose the factor as a helper, a landing predictor or a trial throw.
- **Conflict to settle**: `index.html` has `simulateLandingX` and `estimatePowerForTarget`, which the AI uses to solve its power with the exact wind model. `game_mode.md` says the AI simulates with the integrator; `product.md` says no simulator. With a doubled factor a simulating AI cancels the wind exactly, which makes the stronger wind pointless for one side. I recommend following `product.md` (see open question 5, the owner's existing question 5).
- Built-in AI wind compensation `-3.2` power per wind unit is hard-coded for the old model. At 96 one wind unit moves a landing about 95 px, and power moves it about 25 px per point at this throw (2 × 807 / 65), so the matching value would be about 3.8. A fixed number the AI never learns is the same as a hidden simulator; it should be replaced by learning from `get_history` or removed.
- Unchecked: the published aim error is not in the files I read. The wind effect per unit (95 px) should be at least 3 times larger than the aim error spread, or the agent cannot separate them.

## 6. Open questions for the owner (one word each, my recommendation first)

1. Double the wind factor to 96 and keep the range −4..+4? **Yes.**
2. Make the engine and the MCP paths use the same acceleration model as the client (today they differ)? **Yes.**
3. Add the scene reaction (fog, dust, leaves, leaning flames, swaying lanterns, bending ribbon) at 64 items by default? **Yes.**
4. Limit the wind change between rounds to at most 2 units, so remembered paths and the sky shield stay useful? **Yes.**
5. (Same as owner question 5 in the feedback log) AI with a simulator or without? **Without** (`product.md` holds; remove `simulateLandingX` use and the fixed `-3.2` compensation from the AI).
6. Wind sound on by default? **Yes** (low, under the music).
