# Design: weapon effects v2

## What changed in the code

One block was inserted into `js/particles.js` directly before `var PRESET_NAMES = Object.keys(PRESETS);`. It starts with the marker `// ---- weapon effects v2 (appended, Kiro task 42) ----`. Nothing above the marker or from `var PRESET_NAMES` on was edited. Because `PRESET_NAMES` is built after the block, the new names are exported and every generic property of `scripts/test_particles.js` already loops over them.

`scripts/test_particles.js`: new properties were put in front of the runner block (the runner has to stay last because it calls `process.exit`). The old properties were not edited.

## The seven presets

| Preset | Use | Particles at default | Notes |
|---|---|---|---|
| `weapon_trail_wave` | bride's wave, call every 6th step | 2 or 3 | ring 10 to 56 px lilac, soft glow, 40% a note glyph; ring centre jitters +-3 px |
| `impact_wave` | wave hits a unit; scale = damage share | 8 | three rings (radius 10/6/2 to 110/100/90, life 0.5/0.6/0.7), flash, 4 notes |
| `weapon_trail_bell` | bell in flight, every step | 1 or 2 | bronze dust; a thin ring about every 15th call (0.25 s at 60 calls per second) |
| `weapon_trail_skull` | skull in flight, every step | 1 or 2 | soul-green glow; `fx_ghostfire` sprite about every 3rd call |
| `scythe_slash_fx` | one slash lands, option `index` 0..2 | 11 | flash, 8 soul-green streaks leaving one way (flips with `index`), 2 rising motes |
| `frost_shatter` | frost curse lands | 9 | flash and 8 falling ice shards |
| `bounce_ring` | shield skips off ground or fence | 3 | gold ring 6 to 54 px and two glints running along the ground |

Sizes follow `cnt(base, scale)` (grows with the square root of the scale), so a scale 4 emit stays under 30.

## Decisions

| Question | Choice | Why |
|---|---|---|
| Change old presets (the doc lists `weapon_trail_dart` colours, `impact_burst` palette, ...) | No | The task says old presets must stay byte-identical. The doc's "existing presets to change" list is left to the main line. |
| How is "byte-identical" proven | sha256 of the file text before the block and from `PRESET_NAMES` on, recorded in the test | The hashes were taken from the unedited file before the first edit. Any later edit of old code fails the test, also a legitimate one: then the hashes must be updated on purpose. |
| Bell impact stack | A reduced stack is tested (66 particles) | The doc's own stack counts 95 with the old presets. The old presets cannot be lowered in this task. |
| Squash for `bounce_ring` | Not added | It needs a new field in the particle record and the drawer; both are existing code. |
| Colours | Lowercase `#rrggbb` only | The test and the drawer parse that form. |
| Note glyphs | `\u266a`, `\u266b` (escapes in the source) | Keeps the file ASCII. The drawer uses `fillText`; the font may not have them, **unverified**. |

## Not covered

- How anything looks or sounds. No game was opened, no pixel was compared (the contrast test of the doc needs screenshots).
- Hit-stop, shake and sound events of the doc (`docs/playtest_fixes.md` 1c) are game code, not presets.
- The new sprite names (`fx_ghostfire` is the only one used) need no new art. `fx_frost_burst`, `fx_note_burst`, `fx_soulfire`, `fx_bronze_shock` of the doc are not used.
