# Hit range measured from the page code (2026-11-17)

Method: `scripts/probe_hit_range.js` cuts the page's own `touches` rule and `projHitRadius` out of `index.html` and sweeps a projectile around a unit in 0.5 px steps (x from -400 to 400, height from -60 to 320). The numbers below are what the game really judges.

| Target | Weapon | Half-width reached | Height reached above feet | Lowest point (negative = below feet) | Formula half / height | Check |
|---|---|---|---|---|---|---|
| skeleton | spear | 91.5 | 177.5 | -21.5 | 91.6 / 211.6 | inside the box |
| skeleton | cannonball | 70.0 | 156.0 | 0.0 | 70.0 / 190.0 | inside the box |
| skeleton | shuriken | 79.0 | 165.0 | -9.0 | 79.0 / 199.0 | inside the box |
| skeleton | flame | 95.0 | 181.5 | -25.0 | 95.4 / 215.4 | inside the box |
| skeleton | cross | 99.0 | 185.0 | -29.0 | 99.2 / 219.2 | inside the box |
| skeleton | axe | 115.0 | 201.0 | -45.0 | 115.0 / 235.0 | inside the box |
| skeleton | shield | 87.5 | 173.5 | -17.5 | 87.8 / 207.8 | inside the box |
| reaper | spear | 78.5 | 186.5 | -21.5 | 78.6 / 186.6 | inside the box |
| reaper | cannonball | 57.0 | 165.0 | 0.0 | 57.0 / 165.0 | inside the box |
| reaper | shuriken | 66.0 | 174.0 | -9.0 | 66.0 / 174.0 | inside the box |
| reaper | flame | 82.0 | 190.0 | -25.0 | 82.4 / 190.4 | inside the box |
| reaper | cross | 86.0 | 194.0 | -29.0 | 86.2 / 194.2 | inside the box |
| reaper | axe | 102.0 | 210.0 | -45.0 | 102.0 / 210.0 | inside the box |
| reaper | shield | 74.5 | 182.5 | -17.5 | 74.8 / 182.8 | inside the box |
| skeleton | wave | 105.0 | 40.0 | 0.0 | 105 / 40 | match |

