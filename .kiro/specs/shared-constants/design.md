# Design — shared game constants

## Overview

Extract the values shared by the two rule implementations into
`shared/constants.json`, anchored to the browser game (`index.html`) as the
source of truth. The Python MCP server loads that file at import time; a
stdlib-only test re-parses `index.html` and compares it to the JSON so drift
is caught.

## Source of truth

`index.html` is the playable game, so its literals define the correct values:

| Key | index.html form | Value |
| --- | --- | --- |
| `GROUND_Y` | `const GROUND_Y = 860;` | 860 |
| `GRAVITY` | `const GRAVITY = 980.0;` | 980.0 |
| `V0_PER_POWER` | `const v0 = power * 13.8;` | 13.8 |
| `FENCE_X` | `const FENCE_X = 960;` | 960 |
| `FENCE_W` | `const FENCE_W = 130;` | 130 |
| `FENCE_H` | `const FENCE_H = 250;` | 250 |
| `WIND_MIN` | `(Math.random() - 0.5) * 8.0` | -4.0 |
| `WIND_MAX` | `(Math.random() - 0.5) * 8.0` | 4.0 |
| `THROW_ANGLE_DEFAULT` | `let playerAngle = 54;` | 54 |
| `TURN_SECONDS` | `const TURN_SECONDS = 12;` | 12 |

## Fence → wall conversion

The browser game stores the central fence as a centered rectangle; the Python
server previously used min/max edges and a top-y. The server derives its wall
rectangle from the fence fields:

```
WALL_X_MIN = FENCE_X - FENCE_W / 2   # 960 - 65 = 895
WALL_X_MAX = FENCE_X + FENCE_W / 2   # 960 + 65 = 1025
WALL_TOP_Y = GROUND_Y - FENCE_H      # 860 - 250 = 610
```

## Server loading

At import, the server resolves `shared/constants.json` relative to its own file
location (`(not published)`) and reads it once into module-level
constants. `GROUND_Y`, `GRAVITY`, `V0_PER_POWER`, `WIND_MIN`, `WIND_MAX` map
directly; the wall bounds are computed from the fence fields. All former
hard-coded literals (`880`, `890`, `1030`, `720`, `13.5`, `-4.5/4.5`) are
removed. The physics loop, collision checks, and damage logic are untouched, so
behaviour changes only through the corrected constant values.

## Drift test

`scripts/test_constants_sync.py` (stdlib only):
1. Reads `index.html` as text.
2. Uses regexes to capture each constant in its real source form, including the
   inline `const v0 = power * 13.8;`, `let playerAngle = 54;`, and the wind span
   `(Math.random() - 0.5) * 8.0` (range = ±span/2).
3. Loads `shared/constants.json`, checks key set equality, then compares each
   value with a small float tolerance.
4. Exits non-zero and prints the mismatches on any drift; exits zero otherwise.

## Values that changed in the server

Converging on the `index.html` source of truth moved several server values:

| Constant | Old server value | New value |
| --- | --- | --- |
| `GROUND_Y` | 880 | 860 |
| `V0_PER_POWER` (launch factor) | 13.5 | 13.8 |
| wall x min | 890 | 895 |
| wall x max | 1030 | 1025 |
| wall top y | 720 | 610 |
| wind range | ±4.5 | ±4.0 |
| `GRAVITY` | 980.0 | 980.0 (unchanged) |
| `FENCE_X` center | 960 | 960 (unchanged) |
