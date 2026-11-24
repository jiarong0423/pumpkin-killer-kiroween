# Task 108 result — knight point placement and team protection

Changed `js/knight_ult.js`: `place(pathId, s)` now accepts normalized, non-monotonic path positions; `answer({ projectilePath, targetId })` gates blocks on the knight's `teamIds`, with optional throw bookkeeping.
Changed `scripts/test_knight_ult.js`: added named requirements 21 and 22 tests, including another-team targeting, and extended the 300-seed shadow model.

Verification run:
- `node scripts/test_knight_ult.js` → `test_knight_ult: all 13 tests passed`
- `node scripts/test_ultimate.js` → `test_ultimate: all 24 tests passed`

Not run: browser wiring or gameplay checks, because `index.html` was explicitly out of scope.
