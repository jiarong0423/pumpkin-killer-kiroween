# Team battle tuning proposal (2v2 / 3v3), 2026-11-17 (read-only analysis; no repo file edited)

Tags: [M] measured (command given), [P] proposed (not yet measured in a real team sim), [D] derived by hand from repo numbers.
Scratch tools (outside repo): `<scratch>/{team_mc.js,geom.js,reach.js}`, run with `node <file>`.

**Baseline.** [M] `node scripts/sim_balance.js --matches 100 --seed 7` (a few seconds): 1v1 = 8.66 rounds, bot hit rate 60-77%, hits-to-kill 4.9-7.3 (pair win-rate bands still show 29 violations; not our scope). `sim_balance.js` has no team mode (1 unit per side, no skills/crates). [M] `team_mc.js` (abstract: one throw per team per round, p = hit rate, h = hits to kill) gives 9.0 for 1v1 at p=0.69, h=6.6, so it tracks the real sim within 4%. Key fact: a team still throws once per round however many units are alive, so rounds ~ N x h / p. Untuned 2v2 = 18.6 rounds, 3v3 = 28.4 [M, team_mc.js].

## (a) Match length
| Mode | Target rounds (bots, p=.69) | Lever | Predicted [M, team_mc.js] | at p=.5 / p=.4 |
|---|---|---|---|---|
| 2v2 | 8-11 (about 4 min at ~25 s/round [P]) | h=4 hits/unit, k=0.61 | 10.3 (p10 8, p90 12) | 13.8 / 17.0 |
| 3v3 | 10-13 (about 5 min) | h=3 hits/unit, k=0.45 | 11.7 (p10 10, p90 14) | 15.7 / 19.4 |
- [P] Lever = scale HP in team matches only, not damage: `teamMaxHp = round(max(hp1 x k, 2.5 x dmg))`, k = h_N / 6.6 (k2 0.61, k3 0.45). `shared/heroes.json` is untouched. Example: skeleton 150 -> 92 / 68; wizard 113 -> 75 / 75 (floor); knight 210 -> 128 / 94 [D]. A damage multiplier is rejected: it inflates ultimates (skeleton triple javelin = 3 x 1.5 x 22 = 99 [D]).
- [P] Ultimate cap vs one unit in team mode: `min(ultDmg, 0.7 x teamMaxHp)`. Heal skill 35 and heal crate 45 scale with k (35 x k, 45 x k) so heal stays about 23-29% of a unit. Status ticks (2) stay.
- [P] Guard for weak human aim (adaptive band 15-40%, `shared/constants.json`): from round 10 (2v2) / 12 (3v3) all throws get `+10% x (round - R)` damage (cumulative, team mode only). Test: sweep p = .3 .4 .5 .69 in a new scratch sim (do not edit sim_balance.js; reuse `SimBalance.internals`), accept if p90 <= 16 / 18 rounds with the ramp.
- Target policy does not change length [M, team_mc.js: focus-front 10.3/11.7 vs random 10.4/11.7].

## (b) Spacing and shielding
[M] `geom.js` (shot from x=432, angle 54, wind 0, power 0-100; first box met). Power window that hits each enemy unit:
| Layout (right team) | front | 2nd | 3rd | back/front |
|---|---|---|---|---|
| 3v3 current slots, S=180 | 10.9 | 6.8 | 5.8 | 0.62 |
| 3v3 S=120 | 10.9 | 4.7 | 4.2 | 0.43 |
| 3v3 S=90 (minimum) | 10.9 | 3.4 | 3.4 | 0.31 |
| 2v2 current, S=360 | 10.9 | 8.8 | - | 0.81 |
- Finding: shielding comes only from the descending arc; windows are contiguous (60-71, 71-78, 78-84), so a long shot at the front hits the next unit and no unit is fully covered unless boxes overlap (S < 140). Same pattern at angle 40/70 and wind +-3.
- [P] Hittable but not trivial = back/front 0.45-0.55: 3v3 S=130, left 352/482/612, right 1296/1426/1556; 2v2 S=160, left 452/612, right 1296/1456 (all inside the start zones 252-612 / 1296-1656). Rear-to-rear reach drops from 1404 to 1204 px; at headwind -3 the back unit at 1656 needed power 95-100 only [M], max reach at wind -4 is 1768 from x=252 [M, reach.js].
- [P] Rules: overlap region goes to the unit nearest the shooter; the hit box uses the drawn feet y (14 px stagger shifts it); a moving unit may not stop within 120 px of a living teammate (min 90 stays as the hard floor); stagger 14 px >= bar height 13, so adjacent HP bars (150 wide, 20 px overlap at S=130) do not collide: assert disjoint rects in `test_team_battle.js`.

## (c) Crates and pity
- [D] Current rule (index.html ~2898-2955): crate only on even rounds, none in flight, alternating side, 3-round expiry, 210-279 px from the unit, one slot that replaces; 1v1 gives at most about 4 per match.
- [P] Keep the even-round cadence and 1 crate alive: 2v2 about 5, 3v3 about 5-6 per match (2.5-3 per side, about 1 per unit; each unit already has the 3 guaranteed skills). Next side = fewer crates PICKED UP; tie -> lower team hp%; tie -> the side that did not get the last one. Anchor the drop on the side's next-to-act unit so one pickup is always reachable (best single move about 286 px per the code comment); frozen units never pick up; the item goes to the picker's own slot.
- Test [P]: 10,000 seeds with random pickups; assert no side waits more than 4 rounds while drops run, picked-up counts differ by at most 1, crates per match 4-6.

## (d) What the player sees (phone: 16:9 box = (360-52) px high, so scale about 0.285 [D from index.html:186]; verify with `measure_phone_layout`)
| Element | Proposal [P] |
|---|---|
| Active ring | one steady #ffd32a ellipse about 100 x 24 world px (28 x 7 CSS), stroke at least 2 CSS px, at each unit's own feet y; no tween on handover |
| HP bars | frozen 150 x 13 per unit; number only on the active unit and the top plate |
| Avatar row | under each plate; order = next-to-act first, dead greyed and last; about 24 CSS px, 3 px hp bar |
| Freeze look | idle frame held, no bob/breath/timers; optional 15% desaturation (needs owner OK, ring stays the only marker) |
| Handover | 0.6 s plate toast "2/3 NAME", timer back to 12 s, input locked 0.3 s |
Sizes: unit box 220 -> about 63 CSS px, body 140 -> 40 CSS px, S=130 -> 37 CSS px; bodies just touch, so the stagger and back-to-front draw order carry readability.

## (e) AI target choice
[P] For each alive enemy unit: `score = pHit x (min(dmg, hp)/maxHp + 0.5 x [hp <= dmg])`, `pHit = erf(W / (2 sqrt2 sigma))`, W = exposed width (front 140, back min(140, gap to the unit in front)), sigma = the level's perception noise (easy 180, normal 80, hard 20 px). Pick the best; easy always the front unit, normal picks the 2nd best 15% of turns, hard 5%; no switching inside a turn. Test: 1,000 seeded matches per level, assert hard wins at least 55% against easy and rounds stay inside the table in (a).

## Three changes first
1. Team HP scale k=0.61/0.45 with the 2.5-hit floor plus the 0.7 ultimate cap (length 18.6/28.4 -> about 10/12).
2. New slots (S=130 for 3v3, S=160 for 2v2), 120 px move clamp, nearest-shooter overlap rule, hit box at drawn y.
3. Crate pity by picked-up count plus the late-round damage ramp.

## Risk
All lengths come from an abstract model fed with the bot's 0.69 hit rate; humans sit at 15-40%, so real matches could run 1.7-2.3x longer (17-19 rounds at p=.4). A real team simulator (new file, built on `SimBalance.internals`) must confirm k and the ramp before the 2026-11-25 checkpoint.
