# Event gaps from the baseline (2026-11-23)

Baseline: `docs/event_baseline_20261123.json`, built by `python3 -B scripts/event_baseline.py --build` from `(not published)` (20000 page matches, source sha256 `4e5a725c9d400a12`).
Rule (owner 2026-11-23): an event that does not show up is a gap. Compare a later run with `python3 -B scripts/event_baseline.py --compare <merged audit json>`.

## A. Events that never fired in 20,000 matches (12 of 52)
| # | Event | Why it does not fire in computer-versus-computer matches | Gap |
|---|---|---|---|
| EB-01 | `charge` | human charge swell while the pointer is held | wired in the page, not exercised by a scripted run (N8) |
| EB-02 | `coin_flip` | human coin toss on the start of a match | wired in the page, not exercised by a scripted run (N8) |
| EB-03 | `flight_cannon` | flight loop started from the human throw path | wired in the page, not exercised by a scripted run (N8) |
| EB-04 | `flight_shield` | flight loop started from the human throw path | wired in the page, not exercised by a scripted run (N8) |
| EB-05 | `flight_shuriken` | flight loop started from the human throw path | wired in the page, not exercised by a scripted run (N8) |
| EB-06 | `flight_spear` | flight loop started from the human throw path | wired in the page, not exercised by a scripted run (N8) |
| EB-07 | `low_hp_heartbeat` | human HUD, low hit points of the human unit | wired in the page, not exercised by a scripted run (N8) |
| EB-08 | `round_end` | human UI round banner | wired in the page, not exercised by a scripted run (N8) |
| EB-09 | `shield_place` | human placing of the shield | wired in the page, not exercised by a scripted run (N8) |
| EB-10 | `ui_click` | human UI path (button press) | wired in the page, not exercised by a scripted run (N8) |
| EB-11 | `ui_hover` | human UI path (pointer over a control) | wired in the page, not exercised by a scripted run (N8) |
| EB-12 | `ultimate_ready` | human HUD, raised when the energy marks reach three for the human seat | wired in the page, not exercised by a scripted run (N8) |

## B. Events that fire in the 20,000 matches but not in the role graph scenarios (10)
These are not event gaps; the role graph (`(not published)`) did not drive them. List: `round_start`, `impact_fence`, `impact_fence_break`, `shield_block`, `dice_rattle`, `dice_result`, `move_step`, `poison_tick`, `item_pickup`, `ult_knight`.

## C. Status and sound gaps measured in the role graph (gap N9)
- status without a cue sound when it is applied: bleed (skeleton, hunchback)
- status without a cue sound when it is applied: poison (wizard, bride)
- status without a cue sound when it is applied: burn (reaper)
- roles that borrow the skeleton face glow (no glow of their own): only face_glow_skeleton and face_glow_pumpkin exist (wizard, bat, knight, reaper, bride, hunchback, hag)
- status without a lasting visual on the unit: burn (no reference in the unit status drawing block) (-)
- status without any sound event: bleed (-)
- status without any sound event: burn (-)

## D. Back end
- EB-BACK: the engine simulation (`scripts/sim_team_headless.py`) counts rule checks, not events, so there is no engine-side event baseline. Needed: a tally of engine events (throw outcomes: hit, ground, wall, shield block, ultimate kinds, each status applied and expired, KO, round end) per hero and team size, from a fresh run (heavy: needs the resource assessment table and the owner's word first). Until then the back-end comparison is the golden hashes and the 20,001-match checks only.

Unclassified events: 0.

### D1. EB-BACK result (2026-11-23, tree 931720c9, `scripts/event_tally_backend.py`, baseline `docs/event_baseline_backend_20261123.json`)
3,000 engine matches (1v1, 2v2, 3v3 x 1,000), 0 engine exceptions, 368 s, 97,074 throws, 54 event kinds fired, **0 expected events never fired**, **0 hero rows empty** (throw, ultimate, KO for all 8 heroes). `--compare` against itself: 0 FAIL, 0 WARN, 0 NOTE.
Not gaps, by design or by counting rule: `throw.near_miss` is off (owner decision, listed as disabled_by_design); the knight's ultimate is a wall (`knight_wall.set` 1,374, `ultimate.used` for the knight) and never a throw, so `throw.kind.ultimate` has no knight row; 24 percent of tool calls the bot makes are refused moves and defends (3,026 rejected, all `submit_action:move` 824 and `defend` 2,202: a slowed unit cannot move, a shield needs two remembered paths), which is the bot, not the engine.
Known limits: the bot fires an ultimate whenever energy is three, so it does not cover "ultimate held back"; wind and weather come from the match seed only (the weather / wind sweep stays in `rear_rear_weather_wind.py`); only hit-rate style events are counted, not hit points.
