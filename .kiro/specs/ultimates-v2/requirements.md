# Requirements: ultimates v2 (workstream W3)
Written 2026-11-15 by Kiro from `docs/ultimate_mapping.md`, `docs/ultimate_rules.md`, `(not published)` (the log wins), `docs/kiro_task_54.md`, and the page's `ULT_BUILT` list. Plan dates: `docs/PLAN_20261115.md` (W3: 2026-11-19 to 2026-11-24; range freeze 2026-12-02 06:00).
Nothing here was run. "Built" means I read the code in `index.html`; I did not play it.

## Facts read today
- `index.html:573`: `ULT_BUILT = ["bat", "skeleton", "wizard"]`. The knight shows "still being made".
- The page keeps its own counters (`energy`, `ultUsed`, `ultArmed`). It does not load `js/ultimate.js` (no script tag, no `Ultimate.` call). The ledger spec `ultimate-ledger` is tested by `scripts/test_ultimate.js` alone.
- Built: bat = 5 shuriken, each 1.5 N / 5. Skeleton = 3 javelins, each 1.5 N / 3 (code comment: +5 percent per hit, head crit when all three hit). Wizard = shell plus blast of 1.5 N (code comment: molotov fire about 468 px wide). `N` is the class's normal damage.
- Knight ultimate (owner 2026-11-09): defend mode, three hidden points A, B, C, each answers one of the enemy's next three attacks in order, uses the whole turn (no throw), max 2 per match, pips public, a point is shown for 1.4 s when it blocks. `docs/kiro_task_54.md` asked for numbers; no result file exists, so every knight number below is provisional.
- `ultimate_ready_chime.ogg` is named in `docs/audio_event_map.json:638` and `js/audio.js:688` but is not in `assets/audio/sfx/`; the synthesized arpeggio plays instead.

## Requirements
Damage (all four heroes)
1. For any ultimate, the follow-up damage on one unit shall total at most 1.5 x `N`, each strike rounded to 0.1. (test: "property: ultimate damage never exceeds 1.5 N")
2. The trigger or normal hit shall not count toward the 1.5 x. The bat has no trigger hit. (test: "trigger hit is separate")
3. While a unit is weakened by the frost curse, `N` shall be the weakened value. (test: "weakened N")

Effects (bat, skeleton, wizard: built mechanics, effects to finish)
4. When a bat ultimate is released, the system shall launch 5 shuriken in a fan (-8, -4, 0, 4, 8 degrees as built) and play the effect timeline `bat_shuriken_rain`. (test: "bat timeline")
5. When a skeleton ultimate is released, the system shall launch 3 javelins at 1.5 x `N` / 3 each; later successful hits gain 5 percent per prior hit and the third successful hit is a head crit, then play `skeleton_triple_javelin`. (checked against code 2026-11-15; test: "skeleton timeline")
6. When a wizard ultimate shell lands, the system shall apply the 1.5 x `N` blast to the single opposing unit within 234 horizontal px, create 13 ghost-fire steps across 468 px, and play `wizard_pumpkin_blast`. (checked against code 2026-11-15; test: "wizard timeline")
7. Every particle preset name used by a timeline shall exist in `js/particles.js`; a missing name shall fail the test, not draw nothing. `shock_ring` is not a preset, so the wizard timeline uses existing landing effects instead. (checked against code 2026-11-15; test: "every preset name exists")
8. A timeline shall be data (time, preset, anchor), deterministic, and free of `Math.random` and `Date`. (test: "timelines are pure")
9. While the page is in reduced-motion mode or a timeline is unknown, the ultimate shall still deal its damage. (test: "damage without effects")

Knight (defend-mode ultimate, provisional numbers)
10. When the knight has 3 pips, it is the knight's own turn, and defend mode is on, the system shall let the player place three points A, B, C, one after the other, on the enemy's recorded paths (last up to 4 enemy shots). (test: "placement needs 3 pips and defend mode")
11. When the third point is locked, the system shall set pips to 0, add 1 to uses, and end the turn without a throw. Cancelling before the third lock shall cost nothing. (test: "spend on third lock, cancel is free")
12. If the turn ends with fewer than three points placed, then the placed points shall stay and the use shall be spent only when at least one point was placed. (decision 6; test: "partial placement")
13. When an enemy attack (one throw) is made, the system shall check the oldest unused point first, in order A, B, C. A point whose zone (provisional half-width 70 px) the attack's first projectile crosses shall block that projectile fully and be used up. (decisions 4 and 5; the 70 px half-width is provisional; test: "points answer attacks in order")
14. Each point shall answer at most one attack; extra projectiles of the same throw are not blocked. (test: "one point, one answer")
15. The public state and the opponent's view shall show only the count of unused points (`ult_points_left`), never their positions; a point's position is shown for 1.4 s when it blocks. (test: "public state has no coordinates")
16. Unused points shall last until three enemy attacks have been answered or the knight is knocked out. (provisional; test: "points expire")
17. Given the same recorded paths, the same placements and the same enemy throws, the result shall be identical. (test: "property: deterministic, 300 seeds")
18. `ULT_BUILT` shall include `"knight"` only after requirements 10 to 17, 21 and 22 pass and the page plays the full flow. (check: main line reads the line)

Knight clarification (owner, 2026-11-15): predictive three-turn defense
21. While the knight is placing points, the system shall accept each of the three points at any position on any remembered enemy path, including a position earlier or later on the path than the previous point (back and forth). Positions need not be monotonic along a path or in time. Every point is a prediction: the system shall not check a point against what the enemy throws later. (test: "placement allows back-and-forth positions")
22. When an enemy attack's first projectile crosses an unused point's zone, and the attack's intended target is the knight or any teammate of the knight, the point shall block that projectile as in requirement 13. The projectile need not pass through or near the knight. An attack whose intended target is not on the knight's team shall not be blocked. In a 1 v 1 match the only teammate is the knight. (test: "point protects a teammate")

Sound and records
19. `(not published)` shall exist, with a CC0 credit line in `assets/audio/CREDITS.md`. Until then the synthesized fallback stays. (check: file exists; credit line found)
20. Each task shall end with the test output pasted into its result file and rerun by the main line, which records it in `docs/kiro_verified.json`. Kiro's own report never counts as verification.

## Out of scope
Reaper, bride, hunchback; 4 v 4 target selection; new pictures (owner, Colab); English labels (W6); replacing the page's counters with `js/ultimate.js` (decision 3).

## Decisions (owner answered "all as recommended" on 2026-11-15, relayed in chat)
1. Skeleton: keep the built three javelins on one unit.
2. Wizard: keep the built blast and fire.
3. Do not swap the page's pip counters for `js/ultimate.js` before the freeze.
4. Knight point against a multi-projectile throw: blocks the first projectile only.
5. Knight block: full for that projectile.
6. Fewer than three points placed: the use is spent if at least one point is placed.
7. Knight clarification, owner, 2026-11-15: the ultimate is a predictive three-turn defense. The shield is moved three times along remembered enemy trajectories, back and forth allowed; every point is a prediction; a point also protects teammates (requirements 21, 22). It is most useful in multiplayer and matters less in 1 v 1. This adds to, and does not replace, the 2026-11-09 rules above.
The knight's numbers (half-width 70 px, expiry, 1.4 s reveal) are still provisional: the owner has not set them and task 54 has no result.
