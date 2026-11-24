# Audio sources (candidates from 2026-11-09, plus the files that were wired in 2026-11-18)

Update 2026-11-19 (red-team H1 R1-B7): the rule below (CC0 only) applies to the 2026-11-09 candidate list. Since 2026-11-18 the project also uses the owner's Gemini-generated sounds (`owner-gemini-sfx-v3`, the throw sounds and the ultimates): they are NOT CC0; the owner states they may be used commercially, and that statement is recorded in `assets/audio/CREDITS.md`. Kenney sounds are CC0.

Status (2026-11-09 candidate pack list): **nothing in the 2026-11-09 candidate sections below has been checked** (wired packs such as Kenney CC0 and `owner-gemini-sfx-v3` record their own verification status in their sections). Every 2026-11-09 candidate entry comes from a web-search snippet found on 2026-11-09 and passed to Kiro in `docs/kiro_task_20.md`. Kiro had no web access and no download access in this task. Every license below is "as stated in that snippet". An entry is **not usable** until the main line opens the page, reads the license on the page itself, and records the result.

Rules for this project:

- Only CC0 / public domain, or sounds synthesized in code. License unknown means **do not use**.
- No CC-BY or attribution-required file is listed here. If the main line finds a better CC-BY file, it must be flagged to the owner first, not added.
- Files are downloaded by the main line only after the owner approves this list.
- The `Key` in each entry is the value of `source` in `docs/audio_event_map.json`. A test checks that every key used in the map appears in this file.

## Sound effect packs

### Key: kenney-interface
- Name: Kenney, "Interface Sounds"
- URL: https://kenney.nl/assets/interface-sounds
- Contains (per snippet): 100 OGG files of interface sounds (clicks, switches, ticks and similar). Exact file names unknown.
- License as stated: CC0
- verified: NO - search snippet only
- Could cover: `ui_click`, `ui_hover`, `dice_result` (a tick), `item_pickup`. Kiro has not heard them, so whether a given file fits the haunted mood is unknown. If they sound too plastic, the synthesized `click`, `hover`, `tick` and `pickup` recipes stay in use.

### Key: kenney-rpg
- Name: Kenney, "RPG Audio" (version in the archive, by Kenney Vleugels)
- URL: https://kenney.nl/assets/rpg-audio
- Downloaded 2026-11-18 by the main line through the site's own download button flow (964,837 bytes, 52 OGG files); licence text in `assets/audio/_licenses/kenney_rpg-audio_License.txt`: Creative Commons Zero (CC0).
- verified: licence text read in the archive; the sounds were NOT listened to (durations measured: footstep05 0.28 s, chop 0.24 s).
- Used for: `move_step` (footstep05 as `move_step_footstep.ogg`), `throw_axe` (chop as `throw_axe_chop.ogg`; later replaced by the owner's Gemini axe), `coin_flip` (handleCoins as `coin_flip.ogg`, the coin toss).

### Key: kenney-impact
- Name: Kenney, "Impact Sounds"
- URL: https://kenney.nl/assets/impact-sounds
- Downloaded 2026-11-18 by the main line through the site's own download button flow (800,850 bytes, 130 OGG files); licence text in `assets/audio/_licenses/kenney_impact-sounds_License.txt`: Creative Commons Zero (CC0).
- verified: licence text read in the archive; the sounds were NOT listened to (durations measured: bell 0.65 s, glass 0.21 s, soft 0.18 s).
- Used for: `throw_cross` (impactBell_heavy_003 as `throw_cross_bell.ogg`), `ultimate_ready` (impactGlass_light_001 as `ultimate_ready_glass.ogg`), `poison_tick` (impactSoft_medium_001 as `poison_tick_soft.ogg`).

### Key: owner-gemini-sfx-v3
- Name: "pumpkin_slayer_sfx_v3" sound set made by the owner with Gemini (files 02_rocket_launch, 03_throw_shuriken, 06_ghost_doll_sonic, 07_throw_axe, 08_throw_cross), delivered 2026-11-18 as 48 kHz stereo WAV.
- Role-specific throw sounds (the shield, 04_fling_shield, was added the same evening for `throw_shield`): rocket launch = the pumpkin wizard's cannon shell (`throw_cannon`), shuriken = the cat-bat (`throw_shuriken`), ghost doll sonic = the bride's wave (`throw_soundwave`), axe = the hunchback (`throw_axe`), cross = the nun (`throw_cross`).
- Processing by the main line: mono, 44.1 kHz, silence trimmed at both ends (-50 dB), peak normalised to -3 dBFS before encoding, 5 ms fade in and up to 30 ms fade out, encoded with the FFmpeg built-in Vorbis encoder (stereo, 160 kbit/s; the encoder cannot write mono); decoded peak about -6 dBFS.
- Licence: made by the owner with a generation tool; the owner is responsible for confirming that the output may be used commercially (the tool's terms); not a CC0 material.
- Also from the owner (2026-11-18): `12_evil_spell_impact.wav` (48 kHz stereo, 2.65 s) = the necromancer's flame HIT sound (`impact_flame`, played when a ghost flame hits a unit non-fatally; on 2026-11-19 trimmed to 0.85 s with an 80 ms fade-out and gated behind `!(opp.hp <= 0)` per owner H16). First wired as an ultimate cast sound and corrected the same evening after the owner's note.
- Ultimates set (2026-11-18, `pumpkin_slayer_ultimates_sfx.zip`, 8 files of 2.1 to 2.85 s, 48 kHz stereo WAV, one per role, each a whole cast + flight + impact clip): allocated one to one to the role events `ult_skeleton`, `ult_wizard`, `ult_bat`, `ult_knight`, `ult_reaper`, `ult_bride`, `ult_hunchback`, `ult_hag`; because the clips contain the impact, all seven thrown ultimates are split into a cast part and an `_hit` part (`ult_skeleton_hit` at 1.20 s, `ult_wizard_hit` at 0.65 s, `ult_bride_hit` at 0.90 s, `ult_bat_hit` at 0.82 s, `ult_reaper_hit` at 1.10 s, `ult_hunchback_hit` at 0.93 s, `ult_hag_hit` at 0.78 s) that plays only when the move lands; `ult_knight` is a shield-wall placement and plays whole at the lock. The cut points are guesses from loudness, not from listening.
- verified: files decode and durations measured; the sounds were NOT listened to by the main line.

### Key: owner-status-sfx-20261122
- Name: four status sounds supplied by the owner on 2026-11-22 as MP3 files named 冰霜 (frost), 電擊 (shock), 減速 (slow), 暈眩 (stun), received at 48 kHz stereo (frost, 4.7 s) and 44.1 kHz mono (shock 0.78 s, slow 19.5 s, stun 1.99 s).
- Allocation: `status_frost` = 冰霜 (the "weak" status of the javelin hit), `status_shock` = 電擊 (the nun's cross shock), `status_slow` = 減速 (the cat-bat's shuriken slow), `status_stun` = 暈眩 (head crit and nun stun). The synthesized recipes of the same names stay in `js/audio.js` as the fallback.
- Cuts by the main line (the owner's files are longer than a cue): frost 0.6 s to 2.5 s (1.9 s, 8 ms fade in, 0.5 s fade out), shock 0.0 to 0.72 s, slow the first 1.2 s of 19.5 s (the file repeats chain sounds), stun the first 1.5 s of 1.99 s; peak normalised to -3 dBFS before encoding (stun +14 dB, it was very quiet), encoded with the FFmpeg built-in Vorbis encoder (stereo, 112 kbit/s), decoded peak about -3 dBFS.
- Licence: the owner stated on 2026-11-23 ("c00抓的沒問題", read as: the files were taken from CC0 sources and that is fine). RECORDED AS THE OWNER'S STATEMENT, NOT VERIFIED by the main line: the exact source pages, authors and licence texts of the four files are not recorded; if the owner still has the page links they should be added here and to `assets/audio/CREDITS.md` before the release export.
- verified: files decode and durations measured; the sounds were NOT listened to by the main line.

### Key: kenney-scifi
- Name: Kenney, "Sci-Fi Sounds"
- URL: https://opengameart.org/content/sci-fi-sounds
- Contains (per snippet): sci-fi effects (the exact list is unknown).
- License as stated: CC0 per OpenGameArt. The Kenney site itself was not checked.
- verified: NO - search snippet only
- Could cover: `shield_place` (a force-field or power-up style rise), `ultimate_ready` (power-up chime). Sci-fi timbre may clash with the graveyard setting; the synthesized `spell_rise` and `arpeggio_up` recipes are the default.

### Key: oga-sword-clashes
- Name: StarNinjas, "20 sword sound effects attacks and clashes"
- URL: https://opengameart.org/content/20-sword-sound-effects-attacks-and-clashes
- Contains (per title): 20 sword attack and clash sounds.
- License as stated: CC0
- verified: NO - search snippet only
- Could cover: the body of `shield_block` (metal clang). The ghost shimmer is synthesized on top. Swing sounds in the pack might also work as extra layers for the spear whoosh, but that is not planned.

### Key: oga-fantasy-weapons
- Name: "Fantasy Weapons and Apparel SFX Library" by Jan Schupke
- URL: https://opengameart.org/content/fantasy-weapons-and-apparel-sfx-library
- Contains (per title): weapon and apparel (armour, cloth) sounds. Exact file list unknown.
- License as stated: CC0
- verified: NO - search snippet only
- Could cover: `impact_unit` (weapon hit), `move_step` (armour / cloth movement). Fallbacks: `thud_unit`, `step`.

## Music

### Key: oga-lanterns-hollowed-forest
- Name: "Lanterns in the Hollowed Forest"
- URL: not provided in the brief. Find it by title on opengameart.org.
- Contains (per title): ambient forest music. Tempo, key and loop point unknown.
- License as stated: CC0 per search, October 2025
- verified: NO - search snippet only
- Planned use: the `bed` layer (file `assets/audio/music/bed_ambient.ogg`).

### Key: oga-horror-loop-tinyworlds
- Name: "Horror Loop" by TinyWorlds
- URL: not provided in the brief.
- License as stated: **not stated in the brief**. **Blocked: do not use until the license is read on the page and is CC0.**
- verified: NO
- Planned use if cleared: the `tension` layer (file `assets/audio/music/tension_drone.ogg`). If it is not cleared, the synthesized tension layer stays.

### Key: oga-creepy-ambient-epb9000
- Name: "Creepy Ambient Loop" by epb9000
- URL: not provided in the brief.
- License as stated: **not stated in the brief**. **Blocked: do not use until the license is read on the page and is CC0.**
- verified: NO
- Planned use if cleared: an alternative for the `bed` layer. Not in the event map.

### Key: oga-void-estate-chiptune
- Name: "Haunting Chiptune Loop [Void Estate]"
- URL: https://opengameart.org/content/haunting-chiptune-loop-void-estate
- License as stated: **not stated in the brief**. **Blocked: do not use until the license is read on the page and is CC0.**
- verified: NO
- Planned use: none. A chiptune sound probably clashes with the bell and pad palette in `docs/sound_design.md` (unverified). Listed as a backup only.

## Event coverage

| Event | Source key | Fallback if no file |
|---|---|---|
| ui_click, ui_hover | kenney-interface | `click`, `hover` |
| dice_result, item_pickup | kenney-interface | `tick`, `pickup` |
| shield_place, ultimate_ready | kenney-scifi | `spell_rise`, `arpeggio_up` |
| shield_block | oga-sword-clashes | `clang` (+ `shimmer`) |
| impact_unit, move_step | oga-fantasy-weapons | `thud_unit`, `step` |
| music `bed` | oga-lanterns-hollowed-forest | synthesized bell and pad bed |
| music `tension` | oga-horror-loop-tinyworlds (blocked) | synthesized dissonant drone |
| everything else | synth-only | the code recipe is the sound |

## The gap: no CC0 pack was found for thrown objects

The search found no CC0 pack for thrown spears, shuriken, cannon fire, or a thrown spinning shield. These are made in code with Web Audio (`js/audio.js`), and the same applies to the other events marked `synth-only`:

| Event | Synthesized recipe |
|---|---|
| throw_spear | `whoosh_spear`: band-pass noise sweep 500 to 3200 Hz plus a faint rising sine |
| throw_shuriken | `whirr`: high band-pass noise with a 30 Hz tremolo |
| throw_cannon | `boom_cannon`: low sine drop 120 to 36 Hz, noise burst, a delayed recoil thump, a rumble tail |
| throw_shield | `spin_shield`: band-pass noise with a 16 Hz tremolo, a faint metal tone |
| flight_* | `air_whistle`, `air_buzz`, `air_rumble`, `air_spin`: quiet looped filtered noise |
| impact_unit_heavy, impact_ground*, impact_fence* | `thud_heavy`, `thump_soft`, `thump_heavy`, `knock_wood`, `splinter` |
| charge | `hum`: two oscillators whose pitch follows the power meter |
| dice_rattle, poison_tick, ko, low_hp_heartbeat | `dice_rattle`, `bubble`, `ko`, `heartbeat` |
| round_start, round_end, heal | `bell_strike`, `bell_fall`, `chime_two` |
| status_bleed, status_poison, status_burn, bleed_tick, burn_tick (2026-11-23, gap N9) | `status_bleed` (wet slash, thud, two drips), `status_poison` (hiss, three rising bubbles), `status_burn` (ignition whoomp, five crackles), `bleed_tick` (one drip), `burn_tick` (three crackles); no file, no licence; nobody has listened to them yet |

How these sound is unverified. The numbers are first guesses and need a listening pass.

## Checklist for the main line before any download

1. Open the page. Read the license text on the page, not the snippet.
2. Open the file list. Confirm the file names that match the events above.
3. Listen. Write down the verdict per file. Reject anything that does not fit.
4. For every file kept: record name, author, URL, license and date in `assets/audio/CREDITS.md`, even for CC0.
5. Convert to OGG if needed, trim silence, normalise peaks to about -3 dBFS, and name the file as in `docs/audio_event_map.json`.
6. Re-run `node scripts/test_audio.js`, then listen to the whole mix. Check the clean-sound rule and the 12 dB music gap by ear.

## Installed files (2026-11-09, verified on the page, see `assets/audio/CREDITS.md` and `assets/audio/_licenses/`)

| source key | page | file in the game | role | license seen |
|---|---|---|---|---|
| oga-creepy-ambient-epb9000 | https://opengameart.org/content/creepy-ambient-loop | `assets/audio/music/bed_ambient.ogg` | music bed | CC0 |
| oga-lost-in-a-bad-place | https://opengameart.org/content/lost-in-a-bad-place-horror-ambience-loop | `assets/audio/music/tension_drone.ogg` | tension layer | CC0 |
| oga-short-jingle | https://opengameart.org/content/short-jingle | `assets/audio/music/victory_sting.ogg` | victory sting | CC0, public domain |
| oga-game-over-dark | https://opengameart.org/content/game-over-dark-short-music-clips | `assets/audio/music/defeat_sting.ogg` | defeat sting | CC0 |

## Installed sound-effect files (2026-11-09; licenses in `assets/audio/_licenses/`, credits in `assets/audio/CREDITS.md`)

| source key | page | file in the game | event | license seen |
|---|---|---|---|---|
| kenney-interface | https://opengameart.org/content/interface-sounds (Kenney) | `ui_click.ogg`, `ui_hover.ogg`, `dice_tick.ogg` | click, hover, dice result | Kenney License.txt: CC0 |
| kenney-casino | https://opengameart.org/content/54-casino-sound-effects-cards-dice-chips (Kenney) | `dice_rattle.ogg` | dice rolling | Kenney License.txt: CC0 |
| kenney-scifi | https://opengameart.org/content/sci-fi-sounds (Kenney) | `shield_place_spell.ogg`, `throw_cannon_boom.ogg`, `fence_break.ogg` | shield placed, cannon, fence breaks | Kenney License.txt: CC0 |
| bigsoundbank-s0573 | https://bigsoundbank.com/whoosh-2-s0573.html | `whoosh_spear.ogg` | spear throw | CC0 |
| bigsoundbank-s0770 | https://bigsoundbank.com/heartbeat-3-s0770.html | `heartbeat.ogg` | low-HP heartbeat | CC0 |

## Chosen by the owner from the audition page (2026-11-09)

| source key | page | file in the game | event | license seen |
|---|---|---|---|---|
| oga-magic-spell-sfx | https://opengameart.org/content/magic-spell-sfx | `spell_magic.ogg` | shield_place | License(s): CC0 |
| oga-magic-words-healing | https://opengameart.org/content/magic-words-healing-sound-effect | `heal_harp.ogg` | heal | License(s): CC0 |
| oga-80-cc0-rpg-sfx | https://opengameart.org/content/80-cc0-rpg-sfx | `roar_ko.ogg` | ko, impact_ground | License(s): CC0 |
| oga-80-cc0-rpg-sfx | https://opengameart.org/content/80-cc0-rpg-sfx | `stone_ground.ogg` | ko, impact_ground | License(s): CC0 |
| oga-punch-qubodup | https://opengameart.org/content/punch | `punch_hit.ogg` | impact_unit(_heavy) | License(s): CC0 |
| oga-punch-qubodup | https://opengameart.org/content/punch | `punch_heavy.ogg` | impact_unit(_heavy) | License(s): CC0 |
| oga-swishes | https://opengameart.org/content/swishes-sound-pack | `swish_throw.ogg` | throw_shuriken, throw_shield | License(s): CC0 |
| oga-thwack | https://opengameart.org/content/thwack-sounds | `thwack_wood.ogg` | impact_fence | License(s): CC0 |
| oga-metal-impact | https://opengameart.org/content/metal-impact-sounds | `metal_bing.ogg` | shield_block | License(s): CC0 |
| oga-ghost-ogrebane | https://opengameart.org/content/ghost | `ghost_real.ogg` | ambient ghost (real voice) | License(s): CC0 |
| oga-ambient-horror | https://opengameart.org/content/ambient-horror | `tension_drone.ogg` | music tension layer | License(s): CC0 |

## Chosen by the owner from the Kiro audition pages (2026-11-09), wired per docs/sound_mapping.md

| source | page | file in the game | use | license seen |
|---|---|---|---|---|
| bigsoundbank | https://bigsoundbank.com (crow, meow-cat-3, meow, church-bell-long, cluster-chimes, thunder-2, wind-whistle, forest-night, feet-leaves) | `ambient/crow, cat_meow, cat_growl(unused), thunder, wind_bed, night_bed`; `sfx/bell_round, chime_single, step_leaf` | creature layer, beds, round bells, shimmer, step | BigSoundBank: CC0 (Kiro opened the pages) |
| oga-ghost-moans-qubodup | https://opengameart.org/content/ghost-moans (GhostMoan01, GhostMoan03) | `ambient/ghost_moan1, ghost_moan3` | creature layer | License(s): CC0 |
| oga-witch-cackle / oga-evil-laugh | https://opengameart.org/content/witch-cackle , laugh-evil-1 | `ambient/witch_cackle, evil_laugh(unused)` | creature layer | License(s): CC0 |
| oga-zombie-moans | https://opengameart.org/content/zombie-moans (darsycho) | `ambient/zombie_moan` | creature layer | License(s): CC0 |
| oga-bones | https://opengameart.org/content/bones-2 | `sfx/bones_rattle` | ko layer | License(s): CC0 |
| oga-breaking-rock | https://opengameart.org/content/breaking-rock | `sfx/rock_break` | impact_ground_heavy layer | License(s): CC0 |
| oga-80-cc0-creature-sfx | https://opengameart.org/content/80-cc0-creature-sfx | `ambient/dog_bark` (barking_01) | creature layer | License(s): CC0 (page re-read 2026-11-09) |
| oga-ghostly-cackle-laugh-1 | https://opengameart.org/content/ghostly-cackle-laugh-1 | `ambient/ghost_cackle` | creature layer | License(s): CC0 (page re-read 2026-11-09) |

## Background music chosen (2026-11-09; found by Kiro task 24, license lines re-read on the pages by the main line)

| source key | page | file in the game | use | license seen |
|---|---|---|---|---|
| oga-artifact-room-fupi | https://opengameart.org/content/artifact-room | `music/bed_artifact_room.ogg` | battle bed (all moods) | License(s): CC0 (tags: magic, mysterious, celestial choir, harp) |
| oga-4-music-box-tracks | https://opengameart.org/content/4-music-box-tracks | `music/alt_music_box_waltz.ogg` (spooky waltz) | stored for scene use (bell tower), not wired yet | CC0. No credit required. |
| oga-haunted-track-gena-sealov | https://opengameart.org/content/haunted-track | `music/alt_haunted_track.ogg` (minor) | stored for scene use (pumpkin field), not wired yet | License(s): CC0 |

## CC0 additions verified and wired (2026-11-19)

### Key: oga-catching-fire
- Name: "Catching Fire" (`flame.ogg`)
- URL: https://opengameart.org/content/catching-fire
- License: CC0 1.0 Universal (`assets/audio/_licenses/LICENSE_oga-catching-fire.txt`)
- Used for: `throw_flame` (`assets/audio/sfx/throw_flame_fire.ogg`, 0.45 s)

### Key: oga-magic-spell-sfx
- Name: "Magic Spell SFX" (`magical_1.ogg`)
- URL: https://opengameart.org/content/magic-spell-sfx
- License: CC0 1.0 Universal (`assets/audio/_licenses/LICENSE_oga-magic-spell-sfx.txt`)
- Used for: `shield_place` (`assets/audio/sfx/spell_magic.ogg`); `charge` uses the 4-layer rising synth `R.hum` in `js/audio.js`

### Key: oga-wind-whoosh-loop
- Name: "Wind Whoosh Loop" (`wind woosh loop.ogg`)
- URL: https://opengameart.org/content/wind-whoosh-loop
- License: CC0 1.0 Universal (`assets/audio/_licenses/LICENSE_oga-wind-whoosh-loop.txt`)
- Used for: `flight_spear` (`assets/audio/sfx/flight_spear_whoosh.ogg`, 5.96 s loop)

### Key: oga-air-whoosh
- Name: "Air Whoosh" (`whoosh2_0.wav`)
- URL: https://opengameart.org/content/air-whoosh
- License: CC0 1.0 Universal (`assets/audio/_licenses/LICENSE_oga-air-whoosh.txt`)
- Used for: `flight_cannon` (`assets/audio/sfx/flight_cannon_wind.ogg`)

### Key: oga-short-wind
- Name: "Short Wind Sound" (`short wind sound.wav`)
- URL: https://opengameart.org/content/short-wind-sound
- License: CC0 1.0 Universal (`assets/audio/_licenses/LICENSE_oga-short-wind.txt`)
- Used for: `flight_shield` (`assets/audio/sfx/flight_shield_wind.ogg`)

### Key: oga-cinematic-percussion-loop
- Name: "Cinematic Percussion Loop" (`Cinematic percussion loop 2.wav`)
- URL: https://opengameart.org/content/cinematic-percussion-loop
- License: CC0 1.0 Universal (`assets/audio/_licenses/LICENSE_oga-cinematic-percussion-loop.txt`)
- Used for: `music.layers.rhythm` (`assets/audio/music/rhythm_percussion_loop.ogg`, 12.00 s loop)
