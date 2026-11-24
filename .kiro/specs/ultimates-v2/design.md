# Design: ultimates v2
Written 2026-11-15. Requirements: `requirements.md` (numbers in brackets). Nothing here was run.

## Split
The page is one large file with one writer (the main line), so the new logic goes into two DOM-free modules that Node can test. The page only calls them.

| Piece | File | Does | Tested by |
|---|---|---|---|
| Effect timelines | `js/ultimate_fx.js` | Returns, for a hero id, a list of `{ t, preset, anchor }` steps (seconds after release; anchor = `muzzle`, `impact`, `unit`, `ground`). Also the damage helpers `strikeDamage(N, strikes)` and the blast rule. Pure data and functions. [4 to 9, 1 to 3] | `scripts/test_ultimate_fx.js` |
| Knight points | `js/knight_ult.js` | State machine for A, B, C: `place`, `cancel`, `lock`, `answer(attack)`, `publicView()`. Takes recorded paths as plain arrays. [10 to 17] | `scripts/test_knight_ult.js` |
| Wiring | `index.html` | Calls both modules from `executeThrow`, the defend-mode code and the draw loop; adds `"knight"` to `ULT_BUILT` last. [18] | main line run, recorded |

Both modules follow the pattern of `js/ultimate.js`: works in Node (`module.exports`) and in the browser (global), no `Math.random`, no `Date`, bad arguments return `{ ok: false, reason }` and never throw.

## Timelines (first drafts, the numbers are guesses to be tuned in a recorded run)
| Id | Steps |
|---|---|
| `bat_shuriken_rain` | 0.00 `weapon_charge_aura` at muzzle; 0.00 `weapon_trail_dart` per shuriken; each landing `hit_sparks` and `damage_number` |
| `skeleton_triple_javelin` | 0.00 `weapon_charge_aura`, `face_glow_skeleton`; flight `weapon_trail_spear`; landing `sprite_ghostfire`, `impact_burst` |
| `wizard_pumpkin_blast` | 0.00 `muzzle_flash`, `smoke_puff`; flight `weapon_trail_cannon`; landing `impact_burst`, `landing_ring_dust`, new `shock_ring` (ground ellipse, 0.35 s) |
The preset names come from `docs/ultimate_mapping.md` section 1c, whose author said the preset list he saw may be incomplete. Task 1 checks every name against `js/particles.js` before any timeline is written; a name that does not exist is replaced or added as a new code-made preset, never left silent [7].

## Knight state machine
States: `idle`, `placing(n)` (n = 0, 1, 2 points set), `locked(points)`, `spent`.
- `idle -> placing`: needs 3 pips, own turn, defend mode, uses < 2 [10].
- `placing -> idle` on cancel, nothing spent [11].
- `placing(2) -> locked` on the third lock: pips 0, uses +1, turn ends [11]. A turn timeout with 1 or 2 points goes to `locked` with those points [12].
- `locked`: each enemy attack calls `answer(attack)`. The oldest unused point whose zone the first projectile crosses blocks it and is used up; otherwise nothing happens [13, 14]. After 3 answered attacks or a KO the state is `spent` [16].
- A point is a position on one recorded enemy path plus a half-width (provisional 70 px). Positions never leave the module except through `answer` (reveal for 1.4 s) [15].
Property tests: the number of blocked projectiles never exceeds 3; a point never blocks twice; the same inputs give the same outputs over 300 seeded scripts; `publicView()` contains no coordinate key [14, 15, 17].

### Back-and-forth placement and teammate protection [21, 22]
Placement: `place(pathId, s)` takes a path id and a position `s` along that path (0 to 1). It checks only that the path exists and `s` is in range. It does not compare `s` with earlier points, so a later point may sit before an earlier one on the same path or on another path. Two points at the same position are allowed (assumption, see Risks). Answer order stays the placement order A, B, C, not path order.

Zone check: `answer(attack)` takes `{ projectilePath, targetId }`, where `targetId` is the unit the thrower aimed at, as recorded when the throw is made. The module is created with `knightId` and a `teamIds` list (the knight and its teammates; in 1 v 1 just the knight). The check has two steps, in this order:
1. Target gate: if `targetId` is not in `teamIds`, return "not blocked" and use up nothing.
2. Zone test: the oldest unused point whose zone the first projectile's path crosses blocks it and is used up, as in the state machine above.
The zone test uses only the point and the projectile path. It never uses the knight's position or the target's position, so a point can stop a shot that would hit a teammate far from the knight. Unit ids come from the page's team list at lock time; if a teammate is knocked out later, its id stays in `teamIds` (the point still answers an attack aimed at it, which cannot happen, so this has no effect).
Tests: "placement allows back-and-forth positions" (points at s = 0.8, 0.2, 0.5 on one path are all accepted and answer in that order); "point protects a teammate" (a projectile aimed at a teammate and crossing the zone is blocked; the same projectile aimed at an enemy-team unit is not; a 1 v 1 setup blocks only shots aimed at the knight).

## Sound and credits
Task 6 looks for a CC0 chime through the sources already listed in `docs/audio_sources.md`, adds `ultimate_ready_chime.ogg`, and adds its line to `assets/audio/CREDITS.md`. If none is found by 2026-11-22 the synthesized fallback stays and the result file says so [19].

## Risks
- Open: whether two points may share a position, and how the page reports each throw's intended target (`targetId`) to `answer`. I did not read the page's throw code for this. Task 4 uses the assumption above, and task 5 checks the page.
- The knight numbers are not decided (no result for task 54). The tests use named constants so the numbers change in one place.
- I did not read the skeleton chain code or the wizard fire code, only their comments. Task 1 reads them and corrects requirements 5 and 6 if they differ.
- `index.html` allows one task at a time; wiring tasks are queued behind each other.
- Effects cannot be judged by a test. The check for "looks right" is a recorded run watched by the owner, not a screenshot.
