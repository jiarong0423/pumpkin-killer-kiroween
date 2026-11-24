# Sound design (Kiro task 20)

Status: design plus code, **nobody has heard any of it.** Kiro cannot play audio. Every statement below about how something sounds is **unverified** and is a first guess for a listening pass. Numbers (Hz, ms, dB) are starting values to tune by ear.

Related files: `js/audio.js` (module), `docs/audio_event_map.json` (event data), `docs/audio_sources.md` (candidate CC0 files), `scripts/test_audio.js` (tests), `.kiro/specs/sound-design/`.

`docs/experience_design.md` does not exist yet, so its feedback table was not used. The event list below follows `docs/game_mode.md` and the task brief.

## 1. Today and what changes

Today `index.html` has no music. It has `playTone` and five beeps: `charge`, `throw`, `block`, `hit`, `heal`. They map to the new events like this:

| Old call | New event |
|---|---|
| `sfx.charge` | `charge` (looped hum that follows the power meter) |
| `sfx.throw` | `throw_spear`, `throw_shuriken`, `throw_cannon`, `throw_shield` (one per weapon) |
| `sfx.block` | `shield_block` |
| `sfx.hit` | `impact_unit` or `impact_unit_heavy` |
| `sfx.heal` | `heal` |

Wiring into `index.html` is not part of this task (the file is locked to another writer, see `docs/ROLES.md`).

## 2. Music plan

### 2.1 Moods

| Mood | When | What it is (unverified) |
|---|---|---|
| `title` | title screen, lobby | Bed only. Low D pad, a sparse bell now and then. The calmest mood. |
| `battle_calm` | battle, all units above 30% HP, no sky shield | Bed plus a soft rhythm layer at 60% level: a low thump on beats 1 and 3, a faint tick on off-beats. |
| `battle_tense` | any unit below 30% HP, or a sky shield is up | Rhythm layer at full level plus the tension layer (a dissonant, slowly pulsing high drone, an occasional cold bell). |
| `victory` | match won | Bed lowered to 40%. A victory layer: an upward bell arpeggio in D major, a warm pad. |
| `defeat` | match lost | Bed lowered to 30%. A defeat layer: a slow descending bell line over a low drone with a minor second. |

### 2.2 Layers

Five continuous layers, each with its own gain. A mood is a set of target gains (`music.moods` in the event map).

1. **Bed** always plays in every mood. Low pad plus sparse bells / celesta, with a soft choir-like pad chord every 4 bars.
2. **Rhythm** is added in battle moods.
3. **Tension** is added by game state. `setTension(0..1)` raises it continuously inside the battle moods. The tension layer level is `max(mood level, 0.9 × tension)` and the rhythm level is `max(mood level, 0.6 + 0.4 × tension)`.
4. **Victory** and **defeat** are used only in their moods.

How the game should drive it:

- `tension = 1` while any unit is below 30% HP, `0.7` while a sky shield is up, otherwise `0`. Use the larger value. Call `setTension` only when the value changes.
- Switch `playMusic('battle_tense')` when tension is at least 0.5 and back to `battle_calm` when it is below 0.3 and has stayed there for 6 s. The gap and the 6 s stop the music from flipping back and forth.

### 2.3 Loop, tempo, key, palette

| Item | Value |
|---|---|
| Key | D minor |
| Tempo | 80 BPM (range 70 to 90 allowed by the brief) |
| Loop length | 8 bars of 4/4 = 24 s (64 eighth-note steps) |
| Crossfade between moods | 1.5 s linear fade of the layer gains |
| Tension change ramp | 0.8 s |
| Palette | bells and celesta (inharmonic partials), low pad, soft choir-like triangle pads, a dark sub thump. No lead melody. |
| Bell notes | random walk on D F A C D F, so the line stays in the key and never forms a tune that competes with effects |

All layers run on one shared step clock, so rhythm, bed and tension stay in time in the synthesized version.

### 2.4 Files versus synthesis (open risk)

The synthesized music is a complete, synchronized system and needs no files. CC0 music tracks (see `docs/audio_sources.md`) are single tracks, not stems, and their tempo is unknown. So:

- A file may replace the **bed** and the **tension** layer. Both are tempo-free textures, so they can sit under the synthesized rhythm without sounding wrong (unverified).
- The synthesized **rhythm** layer is locked to 80 BPM and not to the file. If a file bed has a clearly different pulse, the thumps will fight it. In that case drop the rhythm layer for that file or keep the synthesized bed (unverified, decide by ear).
- A layer picks file or synthesis when it starts. A file that finishes loading later is used the next time that layer starts. Files are loaded at the first user gesture.

### 2.5 Mix rule

Music sits **12 dB under effects**: the music bus has a fixed trim of 10^(-12/20) = 0.251 in the code, so with the music and effects sliders both at 100%, music is 12 dB lower. It is tested.

## 3. Effect sound table

Columns: **Layers** are body (file if present, otherwise the code recipe) plus an optional synthesized sparkle on top. **Pitch** is the random variation per play, applied to both layers. **Prio** is 1 (least important) to 5 (never dropped for a lower one). Band is explained in section 4. "Intended sound" is unverified.

| Event | When it plays | Intended sound (unverified) | Layers | Dur | Pitch | Prio | Band |
|---|---|---|---|---|---|---|---|
| `charge` | While the player holds to charge | A quiet rising hum, pitch follows the power meter, stops on release | body: `hum` (sine 100 Hz and triangle 150 Hz, both × 2^(2.2 × power)) | loop, max 6 s | ±3% | 3 | mid |
| `throw_spear` | Spear released | A fast airy whoosh with a thin rising whistle | body: `whoosh_spear` | 0.6 s | ±6% | 4 | mid |
| `throw_shuriken` | Shuriken released | A quick high whirr | body: `whirr` | 0.5 s | ±6% | 4 | high |
| `throw_cannon` | Cannon fired | A deep boom with a pitch drop, then a short recoil thump and a low rumble | body: `boom_cannon`; recoil thump 140 ms after the boom | 1.3 s | ±6% | 5 | low |
| `throw_shield` | Knight throws the shield | A sideways spinning swish with a faint metal tone | body: `spin_shield` | 0.7 s | ±6% | 4 | mid |
| `flight_spear` | Spear in the air | A very quiet thin air whistle | `air_whistle` loop | loop, max 6 s | ±6% | 2 | mid |
| `flight_shuriken` | Shuriken in the air | A very quiet high buzz | `air_buzz` loop | loop, max 6 s | ±6% | 2 | high |
| `flight_cannon` | Cannonball in the air | A very quiet low rumble | `air_rumble` loop | loop, max 6 s | ±6% | 2 | low |
| `flight_shield` | Shield in the air | A quiet spinning flutter | `air_spin` loop | loop, max 6 s | ±6% | 2 | mid |
| `impact_unit` | Projectile hits a unit | A solid thud with a short crack | body: file `impact_unit_thud` or `thud_unit` | 0.5 s | ±6% | 4 | low |
| `impact_unit_heavy` | Cannon or ultimate hits a unit | A big low crash with a debris hiss | body: `thud_heavy` | 1.0 s | ±6% | 5 | low |
| `impact_fence` | Fence hit but not destroyed | A hollow wooden knock | body: `knock_wood` | 0.45 s | ±6% | 3 | mid |
| `impact_fence_break` | Fence destroyed | Low crunch plus a string of wood cracks | body: `splinter` | 1.0 s | ±6% | 4 | mid |
| `impact_ground` | Light projectile lands | A soft thump | body: `thump_soft` | 0.4 s | ±6% | 3 | low |
| `impact_ground_heavy` | Cannonball or poison shell lands | A deep crump with falling dust hiss | body: `thump_heavy` | 0.8 s | ±6% | 3 | low |
| `shield_block` | A sky shield stops a projectile | A metal clang with a ghostly shimmer on top | body: file `shield_block_clang` or `clang`; sparkle: `shimmer` | 1.0 s | ±6% | 4 | high |
| `shield_place` | The floating shield materialises | A rising spell sweep with shimmer | body: file or `spell_rise`; sparkle: `shimmer` | 1.1 s | ±3% | 3 | high |
| `dice_rattle` | Move die is rolling | Nine small clicks that fade | body: `dice_rattle` | 0.9 s | ±6% | 2 | mid |
| `dice_result` | The die settles | One bright tick | body: file `dice_tick` or `tick` | 0.15 s | ±6% | 3 | high |
| `move_step` | Each step of a move | A soft footfall | body: file `move_step` or `step` | 0.25 s | ±6% | 2 | low |
| `ko` | A unit is knocked out | A falling ghostly wail with filtered breath and shimmer | body: `ko`; sparkle: `shimmer` | 2.0 s | ±6% | 5 | mid |
| `poison_tick` | A poisoned unit takes damage | A short wet bubble pair | body: `bubble` | 0.4 s | ±6% | 2 | high |
| `ultimate_ready` | Ultimate counter reaches its trigger | A rising four-note bell arpeggio with shimmer | body: file `ultimate_ready_chime` or `arpeggio_up`; sparkle: `shimmer` | 1.5 s | ±1% | 5 | high |
| `round_start` | New round begins | One low bell strike with shimmer | body: `bell_strike`; sparkle: `shimmer` | 2.4 s | ±1% | 4 | mid |
| `round_end` | Round ends | Three falling bells | body: `bell_fall` | 2.0 s | ±1% | 4 | mid |
| `ui_click` | Any button pressed | A tiny soft tick | file `ui_click` or `click` | 0.12 s | ±6% | 3 | high |
| `ui_hover` | Pointer over a button | An even tinier tick, rate limited to once per 60 ms | file `ui_hover` or `hover` | 0.1 s | ±6% | 1 | high |
| `low_hp_heartbeat` | A unit is below 30% HP | A low lub-dub every 0.9 s, quiet | `heartbeat` loop | loop, max 12 s | none | 2 | low |
| `heal` | A unit is healed | Two rising chime notes with shimmer | body: `chime_two`; sparkle: `shimmer` | 1.0 s | ±1% | 3 | high |
| `item_pickup` | A unit takes a crate | A short rising blip | file `item_pickup` or `pickup` | 0.4 s | ±6% | 3 | high |

### Why some events vary less than ±6%

A pitch change of 6% is about one semitone. Bells, chimes and arpeggios sit in D minor, so they vary by only ±1% (about 17 cents) to stay in tune with the music. The hum varies ±3% and its power-driven rise is a separate, intended sweep, not random variation. The heartbeat has no variation. Nothing is ever above ±6%: the code clamps every map entry to that range.

### Looped events

`charge`, the four `flight_*` events and `low_hp_heartbeat` loop. Calling `play()` again for a loop that is already running does not start a second copy. It updates the parameters (for `charge`, the `power` option). The game stops a loop with `stop('charge')` when the throw is released and `stop('flight_spear')` when the projectile lands. If the game forgets, the loop ends on its own at the `duration` in the map. The heartbeat is kept alive by calling `play('low_hp_heartbeat')` each frame while the condition holds. It restarts every 12 s, and a gap of about one frame is possible (unverified).

## 4. Mix rules

| Rule | Value |
|---|---|
| Volumes | `master`, `music`, `sfx`, each 0 to 1, clamped. Defaults 0.8, 1, 1. A bad value (NaN, string) is ignored. |
| Mute | `mute(true)` sets the master gain to 0 and refuses new effect voices. The music keeps running silently, so unmuting is in time. |
| UI | One mute button and one volume slider (the slider sets `master`). Music and effects sliders are optional for a settings screen. |
| Music trim | Fixed -12 dB on the music bus. |
| Ducking | When an event marked `duck` plays (`throw_cannon`, `impact_unit_heavy`, `impact_fence_break`, `impact_ground_heavy`, `ko`), music drops 6 dB at once, holds for 400 ms, then returns over 300 ms. A new big event restarts the hold. `update(dt)` must be called every frame for the music to come back. |
| Max voices | 16 concurrent effect voices. Music layers are counted separately (at most 5). When full, the lowest-priority, oldest voice is replaced if the new sound has equal or higher priority. Otherwise the new sound is dropped. |
| Autoplay | Nothing plays before `unlock()`. Call `unlock()` from the first `pointerdown` or `keydown`. `playMusic` and volume calls made earlier are remembered and applied at unlock. |
| Clean-sound rule | No more than 3 effects start in the same band within 150 ms. A fourth replaces the weakest of the three if its priority is equal or higher, and is dropped otherwise. |
| Peak safety | A compressor sits before the output (threshold -10 dB, ratio 4). It stops a pile-up of loud effects from clipping. |
| Rate limit | `ui_hover` plays at most once per 60 ms. |

Bands (rough guide): **low** is thumps and booms below about 250 Hz. **mid** is whooshes, wood and bells between about 250 Hz and 2.5 kHz. **high** is ticks, shimmer and clangs above that. Each event has one band in the event map.

Two heavy events at once (for example the cannon boom and the heavy impact) are both in the low band. That is allowed (2 of 3). A third low sound in the same 150 ms, for example a step, competes with the other two for the cap.

## 5. Event map

`docs/audio_event_map.json` has, for each of the 30 event names: `sound` (sound id), `file` (planned path or null), `source` (key in `audio_sources.md` or `synth-only`), `synth` (fallback recipe), `sparkle`, `volume`, `pitch` (min and max multiplier), `priority`, `band`, `duration`, `loop`, `duck`, `cooldownMs`. It also has the `music` block (tempo, moods, layers).

The same data is embedded in `js/audio.js` as `DEFAULT_EVENT_MAP`, so the game has sound even if the JSON is not served. `node scripts/test_audio.js` checks that the two copies are equal.

## 6. How the game should call it

| Moment | Call |
|---|---|
| First click or key | `audio.unlock()` |
| Title screen / battle start | `audio.playMusic('title')` / `audio.playMusic('battle_calm')` |
| Each frame | `audio.update(dt)` |
| Tension changes | `audio.setTension(x)` |
| Hold to charge, every frame | `audio.play('charge', { power: p / 100 })` |
| Release | `audio.stop('charge')`, `audio.play('throw_cannon')`, `audio.play('flight_cannon')` |
| Landing | `audio.stop('flight_cannon')`, then the impact event for what was hit |
| Mute button / slider | `audio.mute(b)` / `audio.setVolumes({ master: v })` |

`createAudio({ ctx, loader, random, eventMap, log })`:

- `ctx` is an `AudioContext` or a function that returns one. A function is called at `unlock()`.
- `loader(url)` returns a Promise of an `AudioBuffer` (anything with a positive `duration` in tests), or null. An object with `.load(url)` also works. A failed or missing file is not an error: it leads to the synthesized sound, and one summary line is logged.
- `random()` returns a number in [0, 1). If absent, a fixed-seed generator is used. The module never calls `Math.random`.

## 7. What is not verified

- How anything sounds. No sound was played. Levels, frequencies, decays and the 12 dB gap are all untested by ear.
- Whether the synthesized recipes sound premium or cheap. Synthesized bells and whooshes can sound thin; the file layers are there to help, and the main line should listen first.
- Whether any candidate file exists as described, fits the mood, or is really CC0 (`docs/audio_sources.md`).
- Whether the file `bed` and the synthesized rhythm layer stay in time (section 2.4).
- Behaviour in a real browser. Tests use a fake `AudioContext` that records calls. It does not check that real Web Audio accepts every parameter value. Autoplay behaviour and `resume()` were not tried in a browser.
- CPU use on a weak machine. The synthesized music creates a few short-lived nodes per half second.

## 8. Open questions for the owner

1. Should the match end with a short stinger before the victory / defeat layer starts? (Not built.)
2. Is a separate music slider wanted in the first version, or only master plus mute?
3. May the tension mood also react to the timer (for example the last 3 seconds)? (Not built.)
