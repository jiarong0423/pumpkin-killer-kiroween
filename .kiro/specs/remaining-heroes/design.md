# Design: remaining heroes
Written 2026-11-15. Requirements: `requirements.md` (numbers in brackets). Nothing here was run. I read `index.html` lines 1 to 620 only, so everything about the throw, hit, draw and status code is a proposal that task 1 checks.

## Order and gates
One hero at a time: hunchback, then necromancer, then bride (the owner's brief; the hunchback needs the least new code because `BLEED_DMG`, `proj_axe` and the bleed status are already anticipated, and the bride changes the most). Each hero goes through the same steps. A hero reaches the start screen last [2].

| Step | Where | Who |
|---|---|---|
| 1 stats | one table, pure | Kiro CLI, parallel |
| 2 rules (status and hit logic) | `(not published)`, pure | Kiro CLI, parallel |
| 3 profile and weapon | `index.html` | main line, one task at a time |
| 4 poses | `index.html` | main line |
| 5 normal attack | `index.html` | main line |
| 6 sounds | `index.html` | main line |
| 7 ultimate | `index.html` and `js/ultimate_fx.js` timelines | main line |
| 8 balance run | `scripts/sim_balance.js` | main line |
| 9 card and `ULT_BUILT` | `index.html` | main line |

## Pure modules (Kiro CLI can build these in parallel)
Both follow the pattern of `js/ultimate.js` and `js/class_stats.js`: work in Node and the browser, no `Math.random`, no `Date`, bad arguments return `{ ok: false, reason }` and never throw.

### `(not published)` and `(not published)` (new, proposed)
| Function | Does | Tests [req] |
|---|---|---|
| `applyBleed(unit)`, `tickBleed(unit)` | Sets `bleed = 2`, a second hit refreshes and does not stack; each round start deals `BLEED_DMG` and counts down. Lethal or not follows open question 4 (a named constant). | "bleed applies and refreshes" [8] |
| `applyBurn(unit, table)`, `tickBurn(unit, table)` | Burn of `BURN_DAMAGE` for `BURN_TURNS`, refresh not stack, never below 1 HP. | "burn refreshes, does not stack", "burn is non-lethal" [16] |
| `knockback(unit, dir, px, limits)` | New x clamped to the side's range and the fence. | "knockback direction", "knockback is clamped" [8, 9] |
| `firstUnitHit(path, units, halfWidth)` | For the bride's ring: the first unit along the path inside the half-width, or none. | "ring hits one unit" [21] |
| `ultimateTargets(heroId, trigger, units)` | Hunchback: A plus up to 2 neighbours fixed at impact. Bride: A plus up to 3 farther units. Necromancer: per fire, the unit it touches. | "tower toll damage and targets", "piercing wail damage and targets" [10, 22] |
| `ultimateStrikes(heroId, N)` | Per-strike damage list; the sum on one unit is at most 1.5 N, each rounded to 0.1. | "three flames total at most 1.5 N", "property: ultimate damage never exceeds 1.5 N" [17, 26] |

The module takes plain objects (`{ x, hp, bleed, burn }`), not DOM or page globals, so Node tests need no browser. The hit test itself stays in the page; the module decides what a hit does.

### Stats table
`js/class_stats.js` is the single source of numbers [1]. Proposed edits (a CLI task, tested by the existing `scripts/test_class_stats.js`, which also reads `index.html` and fails if the real classes drift):
- Keep one table per hero. After the owner's answer to question 2, delete the other bride and hunchback rows from `PROVISIONAL` and `CURRENT` or mark them obsolete.
- Rename the necromancer row's key to `reaper` and drop the old skull `reaper` row, so `CLASS_KEYS` has seven entries, or keep the key `necromancer` and add an alias in the page. Recommendation: the first, because the owner said the internal id is `reaper`. This changes the 7 x 7 matrix size; `validate()` and its band check are reused.
- Change the hunchback `weapon` to `proj_axe` and the necromancer constants block stays the place for its numbers.
- Replace `reaper_combo` (obsolete) and the `soulflameVolley` count with the necromancer ultimate in requirement 17.

## Page changes (main line, one task at a time)
### Profile and weapon [6, 14, 19]
Add the entry to `HERO_PROFILES` (fields as the four existing heroes), and `DOCK_PORTRAIT`, `DOCK_GLYPH`, `HERO_BLURB`. Add `proj_axe` and `fx_axe_thrown` to `imgList` only when the files exist; the preload gate counts `IMG_TOTAL` from `imgList`, so a path that does not exist would delay the start button by up to 15 s. Task 1 confirms which files exist (I could not list `assets/`). Add the weapon to `THROW_SOUND` [12].

### Poses [7, 15, 20]
Today the page keeps one image key per pose (`pose_skel_windup` and so on) and loads two heroes' poses. Proposal: a table `POSE_SET[hero] = { idle1, idle2, charge1, charge2, charge3, release, empty, hit }` of image keys, loaded for every built hero, and one lookup `poseFor(hero, state, t)` that returns the frame and falls back to `idle1`, then to `unit_*` / the glyph, when a key is missing [4]. The three heroes use the standard 1024 x 1024 canvas, except the necromancer's legacy files, which `check_pose_set.py` already marks as legacy (1536 x 1024). The draw code must handle both sizes with the shared foot baseline; task 1 reads how the skeleton and bat poses are placed and reuses it. State mapping: `idle` alternates idle1 and idle2; `charge` steps charge1, 2, 3 by power; `throw` shows release, then `empty` while the weapon flies; `hit` shows hit.

### Normal attacks [8, 16, 21]
- Hunchback: a slow, heavy axe: the stats table `speedScale` below 1, a spinning sprite (`fx_axe_thrown`), the existing bleed status (`BLEED_DMG`), then `knockback` from `(not published)`.
- Necromancer: the flame is pushed forward from the hand, not thrown in an arc, so it uses a low launch (`LAUNCH_FORWARD`, `LAUNCH_UP` in the constants block). A burn status is added next to bleed and poison.
- Bride: the projectile is the ring. A hit test along the flight path uses `firstUnitHit`; rings widen along the path as a visual only [21]. The path does not damage anything else.

### Ultimates [10, 17, 22, 25, 26]
Each ultimate is a timeline of `{ t, preset, anchor }` steps in `js/ultimate_fx.js`, like the three in `ultimates-v2`, plus `ultimateStrikes`. Preset names are checked against `js/particles.js` before use (the same rule as `ultimates-v2` requirement 7).
- Hunchback: axe hits A, then a ground ring (the `shock_ring`/`landing_ring_dust` presets, or code-made) from the impact x, 0.1 s after the hit; strikes at A and the neighbours.
- Necromancer: three `fx_ghostfire_purple` sprites orbit behind the hero while the player holds the power; on release they change colour and fly as three projectiles, 0.12 s apart; each one that touches a unit strikes it for 1.5 N / 3. Fires that touch nothing do nothing.
- Bride: the ring passes each unit in line order; one strike each.
All timings, spacings and caps are INVENTED and are named constants.

### Sounds [12, 24]
Use event names that already exist (`throw_spear`, `throw_shuriken`, `throw_cannon`, `throw_shield`, `impact_unit`, `impact_unit_heavy`, `impact_ground_heavy`, `charge`, `ultimate_ready`). I propose: axe uses `throw_spear` and `impact_unit_heavy`; flame uses `throw_cannon` quietened or `charge`, and `impact_unit`; ring uses `charge` and `impact_unit`. These are first guesses by name only; I have not heard any of them and did not read `docs/audio_event_map.json`. Task 1 checks every name and lists the files that do not exist. New events (`throw_soundwave`, `impact_soundwave`, `throw_bell`) are not added in this spec; they would need CC0 sources.

### Start screen [8, 11, 18, 23]
`buildStartScreen` already makes a card for every key of `HERO_PROFILES`. So adding the profile makes the card appear, and the order of steps above keeps it last: the profile entry is written in step 3 but the card stays hidden until step 9. Mechanism: a `READY_HEROES` list (the heroes that may appear), checked in `buildStartScreen` and in the `aiClass` pick. At step 9 the hero is added to `READY_HEROES`, removed from `COMING_HEROES`, and added to `ULT_BUILT` when its ultimate passes. The hard-coded four-name arrays in `startMatch` and the initial `aiClass` read from `READY_HEROES` [3]. This is a small shared change and is its own first `index.html` task. `SHOW_COMING_SOON` stays `false`.

### Balance [13]
After each hero, the main line runs `scripts/sim_balance.js` with the new hero in the pool and records the win rates; the hit-to-kill matrix from `ClassStats.validate()` is the quick check before the run. I did not read `scripts/sim_balance.js`, so task 1 checks whether it reads the stats table, `index.html`, or its own numbers. If it has its own, the new numbers go through the table first.

## Conflicts with other specs
- `levels-ui` (requirements 17 to 19) asks for the grey cards to be gone. The page already has `SHOW_COMING_SOON = false` and the comment "owner choice 2026-11-15 (option 1)", so those requirements may already be met. Its task 5 should check the page before editing. A hero leaving `COMING_HEROES` in this spec does not conflict.
- `ultimates-v2` queues `index.html` tasks (its tasks 3 and 5). Tasks here queue behind them.
- `docs/ultimate_mapping.md` rows 5 to 7 are stale. This spec does not edit docs outside its folder; task 2 reports the corrections and the main line applies them.

## Risks
- I have not read the throw, hit, draw or status code in `index.html` (after line 620), the weapon and bleed code the main line says exists, `DOCK_PORTRAIT` or `DOCK_GLYPH`.
- The eighth hero is undecided (open question 1). Seven heroes are planned.
- Each wiring step is a browser check. A test cannot judge how a hero looks, so every step ends in a recorded run the owner can watch.
- Missing or legacy art: the necromancer's pose files are on an older canvas for five frames.
- `index.html` allows one task at a time. Three heroes with about nine steps each is a long queue; the pure-module work in parallel is what shortens it.
