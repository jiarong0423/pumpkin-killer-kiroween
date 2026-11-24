# Coverage table (2026-11-17)

Formulas and sources: header of `scripts/coverage_table.py`. World px; phone px = world px x s.

## 1. Single-target reach (a shot at one unit)

| Weapon | Projectile | Radius added | Reach left/right of the unit centre | Reach above the feet | Phone px (s=0.285) |
|---|---|---|---|---|---|
| spear | 210x33 | 21.6 | 91.6 | 211.6 | 52.3 wide, 60.4 high |
| cannonball | 40x40 | 0.0 | 70.0 | 190.0 | 39.9 wide, 54.2 high |
| shuriken | 58x58 | 9.0 | 79.0 | 199.0 | 45.1 wide, 56.8 high |
| flame | 150x55 | 25.4 | 95.4 | 215.4 | 54.4 wide, 61.4 high |
| cross | 118x82 | 29.2 | 99.2 | 219.2 | 56.6 wide, 62.5 high |
| axe | 130x130 | 45.0 | 115.0 | 235.0 | 65.6 wide, 67.0 high |
| shield | 62x92 | 17.8 | 87.8 | 207.8 | 50.1 wide, 59.3 high |
| reaper as target | - | - | 57 | 165 | 32.5 wide, 47.1 high |

## 2. Area effects

| Effect | Reach | World px | Phone px (s=0.285) |
|---|---|---|---|
| Bride wave | left/right of the landing point, 40 px above the ground | 105, steps 35/70/105 = 100/75/50 percent | 29.9 (11.4 / 21.4 / 29.9) |
| Wizard blast | radius around the landing point | 234 | 66.7 |
| Bat swarm | every living enemy unit after ANY hit of the armed ultimate wave (since 2026-11-18; it was a precise hit inside 55 px) | whole team | - |

## 3. What an area effect covers at the team start slots

Centre on each unit in turn (a shot that lands exactly on it); 'covered' = the other units of the same team inside the reach.

| Team size | Slots | Spacing | Wave: neighbours covered (damage percent) | Blast: neighbours covered |
|---|---|---|---|---|
| 2 | 252/612 | 360 | centre unit0: none; centre unit1: none | centre unit0: none; centre unit1: none |
| 3 | 252/432/612 | 180 | centre unit0: none; centre unit1: none; centre unit2: none | centre unit0: unit1; centre unit1: unit0, unit2; centre unit2: unit1 |

## 4. Spacing needed

- The wave covers a neighbour when spacing <= 105 px; 100 percent at <= 35, 75 at <= 70. The minimum unit spacing is 90 px, so the wave can reach a neighbour only at the tightest spacing (and then at 50 percent).
- The blast (234 px) covers a neighbour at any spacing <= 234 px: at 3 v 3 (180 px) it covers the adjacent unit, and the far one only when centred on the middle unit (180 px each side); at 2 v 2 (360 px) it never covers the teammate.
- The designer's proposal (spacing 130 px for 3 v 3, 160 px for 2 v 2) would put neighbours inside the blast and outside the wave.

## 5. Phone size of the same reaches

| Phone case | s | Wave half-width | Blast radius | Hit box (140 x 190) |
|---|---|---|---|---|
| owner phone fullscreen (800x360) | 0.285 | 29.9 | 66.7 | 39.9 x 54.2 |
| owner phone with address bar (760x266) | 0.198 | 20.8 | 46.4 | 27.7 x 37.6 |
| iPhone 17 Pro Max fullscreen | 0.359 | 37.7 | 84.1 | 50.3 x 68.3 |
