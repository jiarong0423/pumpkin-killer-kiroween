# Design: wind

Full reasoning, tables and open questions: `docs/wind_design.md`. This file lists the decisions and the interfaces.

## Decisions

| Item | Value |
|---|---|
| Wind model | horizontal acceleration, everywhere |
| `WIND_ACCEL` | 96 px/s² per wind unit (today 48 in the client, 45 velocity offset in the engine) |
| Range | −4..+4 (unchanged) |
| Same throw at power 65, angle 50 | lands at 426 / 1188 px for wind −4 / +4 (no wind 807) |
| Scene budget | default 64 items, hard cap 96, fog ≤ 8 |
| Wind ease / gust | 0.6 s / 1.0 s time constants |

## Module `js/wind_fx.js` (UMD, global `WindFx`)

- `createWindField({width, height, seed, count, avoid, windMax})` returns `{setWind, setAvoid, update, draw, getState, getWind, width, height, count}`.
  - `setWind(w)`: game wind units; NaN and non-numbers give 0; clamped to ±`windMax`.
  - `update(dt)`: seconds.
  - `draw(ctx, layer)`: layer `'fog'`, `'dust'`, `'leaf'` or omitted for all. The caller draws `'fog'` behind the characters and `'dust'`, `'leaf'` at the layers named in `docs/wind_design.md`.
  - `avoid`: `[[x0, y0, x1, y1], ...]`, any corner order; invalid entries are dropped.
- `flameLean(w, windMax)`: angle for `ctx.rotate` on something pointing up from its base.
- `swayAngle(w, t, windMax)`: angle for `ctx.rotate` on something hanging down from a pivot (negative for positive wind).
- Constants: `MAX_ITEMS`, `DEFAULT_COUNT`, `MAX_FOG`, `FLAME_LEAN_MAX` (0.6), `SWAY_MAX` (0.5).

## Item model

| Kind | `vx` (px/s) | `vy` (px/s) | Look |
|---|---|---|---|
| fog | `g + n × 90 × k` | ±3 wobble | radial-gradient circle, alpha 0.05 + 0.04 s |
| dust | `g + n × 260 × k` | −8..−24 plus wobble | additive halo plus ellipse stretched by 1 + 2.5 s |
| leaf | `g + n × 420 × k` | +40..+90 plus wobble | rotating ellipse, spin × (1 + 3 s) |

`g` is a per-item calm drift (fog ±4, dust ±10, leaf ±14). `k` is a per-item responsiveness. The wind part is multiplied by `1 + 0.25 s sin(2π t / 3.1) + 0.5 gust`.

## Integration points (main line)

- `index.html`: create the field once with the canvas size and a seed, call `setWind` when the round's wind changes, `update(dt)` every frame, `draw` at the layers above. Pass HUD and HP-bar rectangles with `setAvoid` after units move. Apply `flameLean` and `swayAngle` to flame and lantern drawing, and add `n × 60` px/s to flame and damage-number particle `vx`.
- Engine and stdio server: replace the velocity offset with the acceleration model and read `WIND_ACCEL`.
- Sound module: wind bed and gust, per `docs/wind_design.md` section 4.

## Not decided

Open questions 1 to 6 in `docs/wind_design.md` section 6. Reach floor of 1200 px is a placeholder until real spawn distances are known.
