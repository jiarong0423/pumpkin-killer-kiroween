# crew C3 result: honest wind-reach test (2026-11-16)

Edited files: `scripts/test_wind_reach.js` (rewritten pair checks), this file. No game file, zone or constant was touched.

## Parameters used (read from `js/flight.js`, `shared/constants.json`)
- Flight.simulate, fixed step 1/60, wall and canvas edge included (it is the real model).
- Hit = ground landing within 70 px of target x. Muzzle = shooter x + 58 * dirX, startY = 860 - 110 = 750.
- Angles 25..80 integer, power 15..100 step 0.5 (55 x 171 shots per shooter/direction/wind).
- Left shooter dirX +1 to right targets, right shooter dirX -1 to left targets.
- START: left 252..612, right 1296..1656, step 36 (11 x 11). DICE: left 160..760, right 1160..1760, step 40 (16 x 16).

## Commands
```
node scripts/test_wind_reach.js > $TMPDIR/out.txt 2>&1; echo exit=$?   # run time about 6 s, no sockets
```
Last lines (exit=1):
```
ok   - INFO proposed zones left 240..680, right 1240..1680 (step 40): pair counts at winds -4..4, -5..5, -6..6 (always passes)
ok   - the same wind holds a shot back against the wind clearly more than it carries a shot with the wind
test_wind_reach: 1 FAILED
```
Tests: constants ok; START ranges winds -5..5 ok (0 unhittable); DICE-MOVE FAIL (left failing on purpose, exit 1); INFO ok; legacy wind-shift ok.

## Numbers
START ranges, winds -5..5, both directions: 0 unhittable of 2662 pairs (passes).

DICE-MOVE zones, 512 pairs per wind (256 each direction), unhittable pairs by wind:

| wind | -6 | -5 | -4 | -3..3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|---|
| bad | 58 | 25 | 7 | 0 | 7 | 25 | 58 |

Totals: winds -4..4: 14; winds -5..5: 64; winds -6..6: 180 of 6656.
Examples: wind -4: left 160 -> right 1760, left 760 -> right 1560..1760. Wind 4: right 1160 -> left 160..360, right 1760 -> left 160. Wind 5/-5 also add left 760 and right 1160 as the shooter or target at the nearest edge. The full per-wind pair list is printed by the test.

Proposed zones left 240..680, right 1240..1680 (step 40, 11 x 11 x 2 = 242 pairs per wind):
- winds -4..4: 2592 of 2592 hittable
- winds -5..5: 3168 of 3168 hittable
- winds -6..6: 3738 of 3744 hittable; 6 not: wind -6 left 240 -> right 1640, 1680 and left 280 -> right 1680; wind 6 mirrored (right 1640, 1680 -> left 240; right 1680 -> left 280)

## Could not verify / differences from the brief
- Your expectation was about 42 bad pairs of 1452 at winds -5,-4,-3,3,4,5. My run gives 0 at winds +-3, 7 at +-4, 25 at +-5 (64 over -5..5), and 6656 total pairs for -6..6 (13 winds x 512). I could not reproduce 1452 or the wind +-3 failures; I do not know which grid produced them. The qualitative result (fails from |wind| 4, left 160 -> right 1760 and left 760 -> right 1560..1760 at -4, right 1160 -> left 160..360 at 4) matches.
- Landings are cached per shooter x, direction and wind, and a binary search on the sorted landing list decides each target; this is equivalent to scanning every shot per pair because the landing does not depend on the target.
- Only ground landings count as hits; a shot that ends in the wall or out of the canvas is not a hit.
- Not tested: other power or angle step sizes, other muzzle heights, the browser build (no browser run).
