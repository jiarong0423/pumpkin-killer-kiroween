# Sound mapping (Kiro task 30)

Status: **design only. Nothing here has been heard.** Kiro cannot play audio. Every claim about how a sound "feels" or "fits" is **unverified** and comes from the file name, the stated length, the source page and the game design. Numbers (volume, delay, gap) are first guesses for a listening pass.

Machine-readable copy: `docs/sound_mapping.json` (same data; load that instead of retyping).

## 0. What I could and could not check

- `assets/audio/ambient/` does **not exist** in this checkout, and none of the five new SFX files (`bell_round`, `chime_single`, `bones_rattle`, `step_leaf`, `rock_break`) are in `assets/audio/sfx/`. The brief says they are converted and ready. I took the names and lengths from the brief. Paths and the `.ogg` extension below are **assumed** and must be checked when wiring.
- `(not published)` does **not exist** here. I cannot list real file names from it. Section 4 names only the sound types the brief mentions.
- I did not open `assets/audio/CREDITS.md`. The five new SFX and eleven ambient files need credit lines there before they ship (main line).
- Files that `docs/audio_event_map.json` names but that are missing from `assets/audio/sfx/` (`item_pickup.ogg`, `ultimate_ready_chime.ogg`, `move_step.ogg`) fall back to synthesis as before. Because `move_step.ogg` is missing, the "current step sound" in the `move_step` row below is today the synthesized `step` recipe.

## 1. Rules used for every table

- At most **2 layers per event**. A synthesized `sparkle` (`shimmer`) counts as a layer. Where an event already has file + sparkle, a new layer **replaces** the sparkle.
- Pitch range stays inside the ±6% clamp in `js/audio.js` (`0.94` to `1.06`). Nothing below asks for a bigger pitch change.
- New layers keep the event's `priority`. Each layer carries its own `band` so the "3 per band in 150 ms" rule sees the real band (band values are guesses, unverified).
- Volume is the layer's own gain before the sfx bus, same scale as `volume` in `audio_event_map.json`.
- Every new file keeps the old synthesized recipe as the fallback if the file fails to load.

## 2a. EVENT table

Events not listed stay exactly as in `audio_event_map.json`. That includes all `throw_*`, `flight_*`, `charge`, `shield_block`, `impact_unit*`, `impact_fence*`, `impact_ground`, `dice_*`, `poison_tick`, `low_hp_heartbeat`, `ui_*`, `item_pickup`. `ultimate_ready` is untouched on purpose: the owner has not designed ultimates, so no ultimate sound is added.

| Event | New file(s) | Role | Volume | Pitch | Delay | Layers after | Reason (all fit claims unverified) |
|---|---|---|---|---|---|---|---|
| `round_start` | `bell_round` (5 s church bell) | replace synth `bell_strike` body; keep `shimmer` sparkle | 0.75 | 0.99 to 1.01 | 0 | bell + shimmer = 2 | A church bell at round start suits the graveyard. The event is 2.4 s, the file is 5 s, so cut at 2.6 s with a 600 ms fade. Pitch stays near 1.0 because a bell next to the D minor music can sound sour if detuned (unverified). |
| `round_end` | `bell_round` | replace synth `bell_fall` | 0.5 | 0.94 to 0.96 | 0 | 1 | Same bell, lower and quieter and cut at 1.8 s with a 500 ms fade, so start and end are different gestures. 0.94 is the lowest the clamp allows. If it still sounds the same as `round_start`, give `round_end` the synth `bell_fall` back. |
| `move_step` | `step_leaf` (0.5 s) | random variant (50/50) with the current step sound | 0.4 | 0.94 to 1.06 | 0 | 1 | Leaves on a graveyard path. A pool of two stops the same footfall repeating on every step. Cut at 0.3 s with a 100 ms fade (the event is 0.25 s). Add `cooldownMs` 120 so a fast move does not stack steps. |
| `impact_ground_heavy` | `rock_break` (0.4 s) | extra layer on top of current `stone_ground_heavy` | 0.45 | 0.94 to 1.06 | 30 ms | stone + rock = 2 | Adds crack to the dull thump of a cannonball or poison shell. Layer band `mid` so it does not fill a second low slot. Do not add it to `impact_ground` (light): too busy. |
| `ko` | `bones_rattle` (1.1 s) | extra layer; **replaces** the `shimmer` sparkle on top of `roar_ko` | 0.5 | 0.94 to 1.06 | 250 ms | roar + rattle = 2 | The owner's roar stays as the main sound. The rattle after it reads as "knocked apart" and ends before the 2 s event ends. Not `zombie_moan` here: 4 s is twice the event and it would be a third voice over the roar (see reject list). |
| `shield_place` | `chime_single` (2.5 s) | **replaces** the `shimmer` sparkle on top of `spell_magic` | 0.35 | 0.99 to 1.01 | 300 ms | spell + chime = 2 | The chime lands as the shield settles. Cut at 1.4 s with a 500 ms fade. Narrow pitch because a single chime has a clear note (unverified) and must not fight the music. |
| `heal` | `chime_single` | **replaces** the `shimmer` sparkle on top of `heal_harp` | 0.3 | 0.99 to 1.01 | 200 ms | harp + chime = 2 | Brief asked for it. Lower than `shield_place` because the harp is already musical. **First thing to drop if heal sounds busy** (harp + chime may clash in pitch, unverified). Cut at 1.2 s. |

### Considered and left out

| Idea from the brief | Decision | Why |
|---|---|---|
| Wind layer on `charge` or `flight_*` | Not added | The `flight_*` loops are quiet synth air sounds and each event already has its layers. A 20 s bed started on every throw would restart audibly and, with the bed playing in battle anyway, double the wind (unverified). The wind link goes through the bed instead (section 2b: bed volume follows the public wind value). |
| `ko` with `zombie_moan` | Not added | Too long (4 s), a third voice over the roar. Rare ambient use instead. |
| `chime_single` on `ultimate_ready`, `item_pickup` | Not added | Ultimates are not designed. `item_pickup` has its own file or recipe. |

## 2b. AMBIENT sprinkle table

Scope: the creature layer in `js/ambient_sfx.js` (gap 9 to 22 s between sounds, at most 2 at once, `BASE_GAIN` 0.5 x volume 0.8). The synthesized `bat` stays. The existing synthesized `ghost` stays as the fallback. Volumes below are per-kind gains **before** the creature bus, so the effective level is volume x 0.4.

Files are in `assets/audio/ambient/` (assumed `.ogg`). `ghost_real` is the existing owner-picked file in `assets/audio/sfx/`.

| Kind | File | Len | Weight | Min gap since this kind (s) | Volume | Pan (random in) | Pitch | Family | Notes (unverified) |
|---|---|---|---|---|---|---|---|---|---|
| `bat` | synth (existing) | ~1 s | 4 | 12 | 1.0 | -0.8 to 0.8 | n/a | `animal` | Keep as is. |
| `crow` | `crow` | 0.5 s | 4 | 25 | 0.45 | -0.9 to 0.9 | 0.95 to 1.05 | `animal` | Shortest sound, cheapest to place. Hard pan makes it feel far away. |
| `cat_meow` | `cat_meow` | 1.8 s | 1 | 60 | 0.35 | -0.9 to -0.5 or 0.5 to 0.9 | 0.97 to 1.03 | `animal` | The cat is a playable unit. A meow from nowhere could be read as that unit reacting, so it is rare, quiet, and never near the centre. Drop it if testers notice. |
| `ghost_real` | `sfx/ghost_real` | ~4 s cap | 2 | 30 | 0.8 | -0.6 to 0.6 | 0.97 to 1.03 | `moan` | Owner-picked, plays through the existing echo path. |
| `ghost_moan1` | `ghost_moan1` | 3 s | 2 | 30 | 0.7 | -0.6 to 0.6 | 0.97 to 1.03 | `moan` | Same echo path. |
| `ghost_moan3` | `ghost_moan3` | 4 s | 1 | 40 | 0.7 | -0.6 to 0.6 | 0.97 to 1.03 | `moan` | Longest ghost. Lower weight. |
| `zombie_moan` | `zombie_moan` | 4 s | 1 | 60 | 0.4 | -0.7 to 0.7 | 0.97 to 1.03 | `moan` | Low voice, rare. Quiet because it overlaps the music bed in range (unverified). |
| `witch_cackle` | `witch_cackle` | 1.2 s | 2 | 45 | 0.5 | -0.8 to 0.8 | 0.95 to 1.05 | `voice` | Short, good for variety. |
| `thunder` | `thunder` | 4 s | 1 | 90 | 0.5 | -0.3 to 0.3 | 0.94 to 1.06 | `weather` | Low and long. Must not sit on a cannon boom (see rules). A matching lightning flash in the scene would help but is not designed here. |

Weights sum to 18. Bat plus the four ghost kinds are 9 of 18 (50%), so the owner's original "bats and ghosts" request stays dominant. All `moan` kinds together are 6 of 18 but the family gap below keeps them from clustering.

### Selection rules

1. **Gate**: draw the next time with the existing 9 to 22 s gap. At that time, pick by weight from kinds that pass every rule below. If none pass, try again in 1 s (not a new 9 to 22 s wait).
2. **No back-to-back repeat**: never the same kind as the last sound, and never the same file as either of the last 2 sounds. Pools with more than one variant (ghost) never repeat the last variant.
3. **Per-kind gap**: a kind is skipped until its "min gap" has passed.
4. **Family gap**: after any sound of a family, no sound of that family for 30 s (`moan`), 12 s (`animal`), 45 s (`voice`), 90 s (`weather`). This is on top of rule 3.
5. **Long sounds**: at most **one** sound of 3 s or more at a time (ghost_real, ghost_moan1, ghost_moan3, zombie_moan, thunder). Short sounds may overlap it, up to the existing max of 2.
6. **Never during a throw**: blocked from the `throw_*` event until 0.8 s after the matching `impact_*` event (or until the `flight_*` loop stops, whichever is later). Also blocked while the charge loop runs.
7. **Never during a KO**: blocked from the `ko` event until 3 s later.
8. **Round bells**: blocked for 3 s after `round_start` and `round_end` (the bell is 2 to 5 s and the ambient would cover its tail).
9. **Thunder and heavy hits**: thunder is blocked for 6 s after any `duck` event (`throw_cannon`, `impact_unit_heavy`, `impact_fence_break`, `impact_ground_heavy`, `ko`). Both are low-band.
10. **Already playing when a window opens**: a sound of 1 s or longer fades out over 250 ms when a throw or KO window opens. Shorter sounds finish.
11. **Moods**: no creature sounds in `victory` or `defeat` (the stings need space). Everything else as above.
12. **Mute and volume**: the existing `setMuted` and `setVolume` apply to the whole creature bus unchanged.

### Beds

Beds are continuous loops on their own bus, **not** through the creature `BASE_GAIN`. They are not counted in the "max 2 creature sounds".

| Bed | File | Len | Plays in | Base volume | Range | Crossfade | Notes (unverified) |
|---|---|---|---|---|---|---|---|
| `night_bed` | `night_bed` (forest night) | 28 s | `title` mood | 0.08 | fixed | 2 s | Quiet forest night for the lobby and title. It fades out as the battle starts. |
| `wind_bed` | `wind_bed` | 20 s | `battle_calm`, `battle_tense` | 0.04 | 0.04 to 0.14, follows `abs(wind) / maxWind` | 2 s | Battle bed. Volume rises with the public wind value, so a strong wind is audible as well as visible (owner: wind feels too weak). The change is smoothed over 1 s so it does not jump between rounds. |

Bed rules:

- **Under the music**: the music bus is fixed at 0.251 (-12 dB). Beds at 0.08 and 0.14 peak sit about 10 dB and 5 dB under that (rough, unverified). If the music bed and `night_bed` mask each other, lower `night_bed` first.
- **One bed at a time**: only one bed is audible, except during the 1.5 s mood crossfade (use the music's `crossfadeSeconds`). `title` to battle: `night_bed` fades out, `wind_bed` fades in.
- **Looping**: the brief calls `wind_bed` "loop-ish", so a seamless loop is not assumed. Use two overlapping copies: the next copy starts `len - 2` s after the first, with an equal-power 2 s fade in while the old one fades out.
- **Random start offset** for each bed when it begins, so it does not always open on the same moment.
- **Victory and defeat**: both beds fade to 0 over 1.5 s, so the sting is clear. They do not come back until the next `title` or battle mood.
- **Mute**: both beds follow the master mute and the sfx volume.

## 2c. REJECT list

| Candidate | Decision | Why (unverified) |
|---|---|---|
| `cat_growl` (5 s) | Reject | Too long for an ambient sprinkle: 5 s occupies the "one long sound" slot. A growl also reads as a threat from a unit, and the cat is a player character. |
| `evil_laugh` (2.5 s) | Reject for ambient and for all events above | A laugh fits one moment only: the match result when the agents win. Played at random it would feel like the game laughing at the player mid-turn. There is no such event in `audio_event_map.json` today, and a defeat sting already exists. If the owner wants it, add a new event `match_lost_laugh` as a layer on the defeat sting (not designed here). |
| `zombie_moan` as `ko` layer | Reject for that use | See section 2a. Kept as a rare ambient kind. |
| `bell_round` on `charge`, `ultimate_ready`, or UI events | Reject | A 5 s bell is a punctuation mark. More uses would dull it. Round start and end only. |
| `chime_single` on `ultimate_ready` | Reject for now | Ultimates are not designed. Revisit with that design. |
| `wind_bed` and `night_bed` together | Reject | Two noise beds at once would blur the music bed and the sound effects. One at a time. |
| Any new layer on `throw_*` | Reject | Throws are the core feedback loop and have their own file or recipe. Adding layers risks muddying the one moment players listen for. |

## 3. Checks for the main line

- Layer count: every event above ends with 1 or 2 layers. `round_start` is bell plus synth shimmer. `ko`, `shield_place`, `heal` and `impact_ground_heavy` are file plus file.
- The voice cap (16) and band rule count each layer as a voice. The extra layers add at most 2 voices to `ko` and `impact_ground_heavy` moments.
- `ambient_sfx.js` today supports only one real buffer (`setBuffer('ghost', ...)`) and two kinds. Using this table needs more kinds, variant pools, family gaps and the throw/KO gates. That is wiring work for the main line, not done here.
- Where the old `step` recipe or any listed file is missing, the fallback recipe plays, as today.

## 4. Files I would ask the owner to pick from `(not published)`

The folder is not in this checkout, so I cannot name files. By the types the brief lists, I would ask for:

1. **One wolf howl**: distant, one-shot, for the ambient `animal` family at very low weight. A graveyard night usually has one. It would take the `weather`-style long-sound slot.
2. **One coffin lid or door creak (short)**: a candidate for `shield_place` (the coffin-lid slab shield) as the body instead of the chime, or as a lobby UI accent. Pick the shortest.
3. **One owl hoot or night-bird call**, if the folder has one: a second short `animal` sound next to `crow`.
4. **No roars or monsters** for now: the only matching events (`ko`, ultimates) are already filled or not designed.

## 5. What I could not verify

- How any sound actually sounds, including whether `bell_round` is a clean single strike, whether `chime_single` and `heal_harp` clash in pitch, whether `wind_bed` and `night_bed` loop smoothly, and whether `rock_break` is a crack or a rumble. Band guesses for the new layers come from the names only.
- That the new files, the `ambient` folder and `(not published)` exist where the brief says. They do not exist in this checkout.
- That the levels leave the music audible (the -12 dB music trim is from `docs/sound_design.md`, also untested by ear).
- That the extra voices stay inside the 16-voice cap in a busy round. Not tested.
