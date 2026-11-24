# Requirements — shared game constants

## Introduction

Two implementations of the Pumpkin Killer rules have drifted: the playable
browser game (`index.html`, canvas JS) and the MCP rule engine
(`scripts/mcp_game_server.py`, Python). This work extracts the values both
sides must agree on into a single `shared/constants.json`, makes the Python
server consume it, and adds a test that fails on drift. `index.html` is the
source of truth and must not be edited.

## Requirements

### Requirement 1 — Single shared constants file

**User story:** As a maintainer, I want one file holding every value both rule
implementations share, so the two sides cannot silently drift.

**Acceptance criteria**

1. THE SYSTEM SHALL provide `shared/constants.json` containing the keys
   `GROUND_Y`, `GRAVITY`, `V0_PER_POWER`, `FENCE_X`, `FENCE_W`, `FENCE_H`,
   `WIND_MIN`, `WIND_MAX`, `THROW_ANGLE_DEFAULT`, and `TURN_SECONDS`.
2. THE SYSTEM SHALL set each value to the value found in `index.html`, treated
   as the source of truth.
3. WHERE wind in `index.html` is `(Math.random() - 0.5) * 8.0`, THE SYSTEM SHALL
   record `WIND_MIN` = -4.0 and `WIND_MAX` = 4.0.

### Requirement 2 — Server consumes the shared file

**User story:** As a maintainer, I want the MCP server to read the shared
constants instead of its own copies, so there is one source of truth.

**Acceptance criteria**

1. WHEN `scripts/mcp_game_server.py` is imported, THE SYSTEM SHALL load
   `shared/constants.json` and use its values for `GROUND_Y`, `GRAVITY`, the
   launch-speed factor (`V0_PER_POWER`), and the wind range.
2. THE SYSTEM SHALL derive the central wall rectangle from the fence fields:
   `WALL_X_MIN` = `FENCE_X - FENCE_W/2`, `WALL_X_MAX` = `FENCE_X + FENCE_W/2`,
   `WALL_TOP_Y` = `GROUND_Y - FENCE_H`.
3. THE SYSTEM SHALL NOT retain any hard-coded copy of `GROUND_Y`, the wall
   bounds, `GRAVITY`, the `13.5` launch factor, or the wind range.
4. THE SYSTEM SHALL otherwise keep game behaviour unchanged.

### Requirement 3 — Drift test

**User story:** As a reviewer, I want a test that fails if either side drifts,
so sync is enforced automatically.

**Acceptance criteria**

1. THE SYSTEM SHALL provide `scripts/test_constants_sync.py` using only the
   Python standard library.
2. THE SYSTEM SHALL parse each constant from `index.html` in its real source
   form (`const NAME = value;`, the inline `const v0 = power * 13.8;`,
   `let playerAngle = 54;`, and the `(Math.random() - 0.5) * 8.0` wind form).
3. WHEN any parsed `index.html` value differs from `shared/constants.json`, THE
   SYSTEM SHALL exit non-zero (fail).
4. WHEN all values match, THE SYSTEM SHALL exit zero (pass).

### Requirement 4 — Scope limits

**Acceptance criteria**

1. THE SYSTEM SHALL NOT edit `index.html`.
2. THE SYSTEM SHALL NOT modify anything under `assets/`.
3. THE SYSTEM SHALL NOT run git commands.
4. THE SYSTEM SHALL keep `scripts/test_mcp_game.py` passing.
