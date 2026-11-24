# Three-reviewer playtest, 2026-11-16 (designer, veteran player, judge; 9 valid matches through scripts/playtest_harness.js; numbers are the reviewers' own harness output, small sample)

## Matches (player hero first)
| Reviewer | Match | Winner | Rounds | Player HP left | Ults used |
|---|---|---|---|---|---|
| designer | bride vs knight | player | 11 | 65 | 2 (first bat swarm missed: enemy HP 61 to 59) |
| designer | hunchback vs wizard | player | 7 | 76 | 1 |
| designer | nun vs necromancer | player | 8 | 95 (never touched) | 1 |
| veteran (skill 0.92) | skeleton vs hunchback | player | 5 | 36 | 1 |
| veteran | bat vs bride | player | 4 | 66 | 1 |
| veteran | knight vs nun | player | 11 | 120 (never touched) | 2 |
| judge (skill 0.5) | wizard vs skeleton | player | 15 | 7 | 1 |
| judge | necromancer vs knight | player | 15 | 105 (never touched) | 1 |
| judge | bride vs nun | player | 8 | 55 | 1 |
Nine wins out of nine. The built-in opponent landed 0 to 3 hits per match.

## Agreed by all three
1. The built-in opponent is too weak (even against a skill 0.5 player). Every hero looks easy, so no balance number can be trusted until it aims like the player.
2. Bride ultimate trigger (hit within 40 px of the wave centre) is too strict: a miss wastes the whole ultimate.
3. Hit feedback differs per hero: the skeleton spear shows white silhouette flash plus blast (clear); the knight shows a small burst only. Owner's standard: the skeleton spear (wind-up, hit reaction, effect).
4. The nun's stun and the necromancer's burn are not visible or not implemented.

## Single-reviewer findings
- Veteran: knight does far less than its paper 30 (11 rounds, about 8.6 per round); first-mover with the same opening wind (2.4) every match; head/tail wind barely punishes a strong aimer.
- Judge: the small HP bar over the heads is hard to read; green tint on skeleton and nun lowers recognisability; the enemy wind-up is hard to see.
- Designer: nun 22 damage overlaps the bat; add a landing-distance hint so a 40 px rule can be learned.

## Tool notes
- Back-to-back PT.match failed before commit 3c7f6f3 (gameOver not reset); fixed and checked with two consecutive matches.
- A browser tab in the background freezes the physics; front the tab.
