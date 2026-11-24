# Hit mask table: pixel coordinates (2026-11-17)

> NOTE 2026-11-18 (red-team round 2): the numbers below were produced with the FIRST mask version (one picture per hero). The masks are state-specific now (see docs/LAYOUT_REBUILD_RECORD_20261117.md); regenerate with the inline script before quoting.

Coordinates are world px relative to the unit: x to the right, y up is NEGATIVE, feet line y = 0 (ground 860), art bottom y = +15. Window x -130..129, y -230..39 (260 x 270 cells, 1 cell = 1 world px). Figures as drawn facing LEFT (hunchback: right). Box = decided hit box.

| hero | faces | 1-cells | x range of 1s | y range of 1s (top..bottom) | 90 percent body x | box (w x h) | 1s inside box | empty cells in box |
|---|---|---|---|---|---|---|---|---|
| skeleton | left | 11923 | -90..90 | -176..-1 | -48..59 | 140x190 | 11342 | 15258 |
| wizard | left | 14513 | -73..62 | -192..4 | -52..42 | 140x190 | 14386 | 12214 |
| bat | left | 16309 | -70..73 | -188..0 | -50..51 | 140x190 | 16244 | 10356 |
| knight | left | 17314 | -84..94 | -188..4 | -67..62 | 140x190 | 16088 | 10512 |
| bride | left | 18780 | -83..82 | -170..9 | -55..53 | 140x190 | 17276 | 9324 |
| reaper | left | 18960 | -76..75 | -198..-5 | -57..53 | 114x165 | 15021 | 3789 |
| hag | left | 17035 | -47..85 | -189..0 | -34..63 | 140x190 | 16505 | 10095 |
| hunchback | right | 19722 | -93..92 | -174..9 | -71..71 | 140x190 | 17332 | 9268 |
