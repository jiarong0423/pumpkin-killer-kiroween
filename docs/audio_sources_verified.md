# Audio sources, verified on the web (Kiro task 22)

Method: every page below was opened with web fetch. No audio file was downloaded, played or heard. All "sounds like" statements come from file names or page descriptions and are **unverified by ear**.

Date: this task has no clock. Pages were fetched after 2026-11-09 (the date in `docs/audio_sources.md`). The main line writes the real date into each `LICENSE_<source>.txt` when it saves the file.

Limits of the fetch tool, which affect what could be verified:

- On many OpenGameArt (OGA) pages the fetch output drops the "License(s)" row and the file list. When the license text was not in the output, the source is **rejected as unclear**, even if a search snippet or a comment says CC0.
- Kenney pages for Interface Sounds and Casino Audio did not show the license row. Their license is taken from the Kenney support page (all assets CC0) and from the OGA copies ("attribution not mandatory"). Treat this as accepted, but the main line should read the license file inside each zip.
- Kenney file names were read from third-party GitHub listings (Calinou and Mcamento8, section 1b), not from kenney.nl. The real zips may differ in folder layout or extension. Confirm names when the zip is opened.
- BigSoundBank pages show no file name or file size. Names below are planned local names.

## (a) Sources actually opened

### 1a. The eight candidates from `docs/audio_sources.md`

| Source key | Page URL | Opened | Title / author seen | License text on the page (quote) | Files / formats seen | Verdict |
|---|---|---|---|---|---|---|
| kenney-interface | https://kenney.nl/assets/interface-sounds | yes | "Interface Sounds", Kenney; v1.0, released 2020 | no license row rendered. Site FAQ (https://kenney.nl/support): "public domain licensed (CC0)" | no file list on page. OGA copy (https://opengameart.org/content/interface-sounds): 100 OGG, zip 834.5 Kb. Download button, donation prompt with "Continue without donating", no login prompt seen | **accepted** (license from site FAQ and OGA "this is not mandatory") |
| kenney-scifi | https://opengameart.org/content/sci-fi-sounds and https://kenney.nl/assets/sci-fi-sounds | yes, both | "Sci-Fi Sounds", Kenney | kenney.nl: "Creative Commons CC0". OGA: "this is not mandatory" | 70 OGG, OGA zip `sci-fi_sounds.zip` 5.9 Mb | **accepted** |
| oga-sword-clashes | https://opengameart.org/content/20-sword-sound-effects-attacks-and-clashes | yes | "20 Sword Sound Effects (Attacks and Clashes)", StarNinjas (from comments) | **not shown** by the fetch | comments say 10 clashes/blocks were added; no file list or size | **rejected: license not visible**. Kenney impact sounds replace it |
| oga-fantasy-weapons | https://opengameart.org/content/fantasy-weapons-and-apparel-sfx-library | yes | "Fantasy Weapons and Apparel SFX Library", site links to janschupke.eu | "Copyright/Attribution Notice: CC0." with the CC0 1.0 link | 126 files, 44.1 kHz 16 bit, zip `weapons-apparel.zip` 12.6 Mb; included sounds: arrows, quiver, belt, leather boots, knife/sheath, seax/sheath, sword. File names not shown | **accepted, but not assigned** to any event (no file names visible, no clear match) |
| oga-lanterns-hollowed-forest | https://opengameart.org/content/lanterns-in-the-hollowed-forest | yes | "Lanterns in the Hollowed Forest", description: short looping soft-horror Halloween track | **not shown** | no file list, no size, no author | **rejected: license not visible** |
| oga-horror-loop-tinyworlds | https://opengameart.org/content/horror-loop | yes | "Horror Loop"; the fetch showed only a comment. Mirror https://lpc.opengameart.org/content/horror-loop showed an empty page (date 2015-09-01) | **not shown**, no author shown (so TinyWorlds is not confirmed) | none | **rejected: license and author not visible** |
| oga-creepy-ambient-epb9000 | https://opengameart.org/content/creepy-ambient-loop | yes | "Creepy Ambient Loop", author epb9000, 2024-09-16 | "License(s): CC0" | `creepyloop-v2.ogg` 1 Mb, `creepyloop.ogg` 1.2 Mb, `creepyloop-v2-a.mid` 561 b. Tags: ambiance, Halloween, spooky. Description: low synth notes, vibraphone and music box | **accepted** |
| oga-void-estate-chiptune | https://opengameart.org/content/haunting-chiptune-loop-void-estate | yes | "Haunting Chiptune Loop [Void Estate]" | **not shown** | description: .wav and .ogg, clean and "haunted arcade" versions | **rejected: license not visible** (and a chiptune clashes with the palette) |

Result: 4 of the 8 original candidates accepted (kenney-interface, kenney-scifi, oga-fantasy-weapons, oga-creepy-ambient-epb9000), 4 rejected.

### 1b. Additional pages opened

| Source key | Page URL | Opened | License text on the page (quote) | Files / formats / size seen | Verdict |
|---|---|---|---|---|---|
| kenney-impact | https://kenney.nl/assets/impact-sounds | yes | "Creative Commons CC0" | 130 files. Names from https://github.com/Mcamento8/open-game-sfx-index/tree/main/audio/impact-sounds (OGG). Zip size not shown | **accepted** |
| kenney-casino | https://kenney.nl/assets/casino-audio and https://opengameart.org/content/54-casino-sound-effects-cards-dice-chips | yes, both | kenney.nl: no license row. OGA: "this is not mandatory" | 54 OGG (12 dice sounds). OGA zip `kenney_casino-audio.zip` 876.8 Kb. Names from https://github.com/Mcamento8/open-game-sfx-index/tree/main/audio/casino-audio | **accepted** |
| kenney-rpg | https://kenney.nl/assets/rpg-audio | yes | "Creative Commons CC0" | 50 files (foley, footsteps, weapons). Names from the Mcamento8 `rpg-audio` folder | accepted, not assigned |
| kenney-jingles | https://kenney.nl/assets/music-jingles | yes | "Creative Commons CC0" | 85 files, families HIT, NES, PIZZI, SAX, STEEL (Mcamento8 `music-jingles` folder). No dark or sting-for-defeat naming | accepted, not assigned |
| kenney-faq | https://kenney.nl/support | yes | "public domain licensed (CC0)"; attribution "not required" | n/a | used as license evidence |
| github-calinou-interface | https://github.com/Calinou/kenney-interface-sounds (and `/tree/master/addons/kenney_interface_sounds`) | yes | "Licensed under CC0 1.0 Universal" | file name list of the interface pack as WAV (Godot conversion): `click_001`..`click_005`, `tick_001`, `tick_002`, `tick_004`, `confirmation_001`..`004`, `select_001`..`008`, `pluck_001`, `pluck_002` and more | name source only |
| github-mcamento8-index | https://github.com/Mcamento8/open-game-sfx-index (README, `SOURCES.md`, `audio/` and the five pack folders) | yes | "all audio is Creative Commons CC0 1.0" | third-party mirror, lists Kenney names and the official zip URLs. Not an official source | name source only, never download from it |
| oga-lost-in-a-bad-place | https://opengameart.org/content/lost-in-a-bad-place-horror-ambience-loop | yes | "License(s): CC0" | author congusbongus, 2022-10-04. `lost.ogg` 2.8 Mb. "Dark string pads", seamless loop | **accepted** |
| oga-4-atmospheric-ghostly-loops | https://opengameart.org/content/4-atmospheric-ghostly-loops | yes | "License(s): CC0" | author Independent.nu, `independent_nu_ljudbank-atmosphere_moody.7z` 3.4 Mb (archive, 4 loops, inner file names unknown) | accepted, not assigned (inner names unknown) |
| oga-game-over-dark | https://opengameart.org/content/game-over-dark-short-music-clips | yes | "License(s): CC0" | author Robin Lamb, 2022-12-31. `gameoverdark.ogg` 168.8 Kb, `gameoverdark.wav` 1.8 Mb, `gameoverstrangesounding.ogg` 124.1 Kb, `.wav` 1.5 Mb | **accepted** |
| oga-game-over-sad | https://opengameart.org/content/game-over-sad-short-music-clips | yes | "License(s): CC0" | Robin Lamb. `sadending1.ogg` 209.1 Kb, `sadending2.ogg` 241.4 Kb, `sadending3.ogg` 231.8 Kb (plus WAV) | accepted, backup |
| oga-lose-game | https://opengameart.org/content/lose-game-short-music-clip | yes | "License(s): CC0" | Robin Lamb, 2022-07-21. `losegamemusic.ogg` 135.2 Kb, `.wav` 1.2 Mb | accepted, backup |
| oga-short-jingle | https://opengameart.org/content/short-jingle | yes | "License(s): CC0"; "Public Domain. No attribution needed." | author OO, 2019-05-01. `PositiveChoice.ogg` 83.7 Kb | **accepted** |
| bigsoundbank-licenses | https://bigsoundbank.com/licenses.html | yes | "Creative Commons CC0 1.0 Universal" | site-wide license page. Credit is optional ("Nothing is mandatory") | license evidence |
| bigsoundbank-s0573 | https://bigsoundbank.com/whoosh-2-s0573.html | yes | "CC0 license (public-domain equivalent)" | "Whoosh #2", Joseph Sardin. 13 s, mono, 48 kHz 16 bit. WAV and MP3. Page says no account needed | **accepted** |
| bigsoundbank-s0770 | https://bigsoundbank.com/heartbeat-3-s0770.html | yes | same CC0 text | "Heartbeat #3", Joseph Sardin. 33 s, mono, 48 kHz 16 bit. WAV and MP3 | **accepted** |
| bigsoundbank-s0243 | https://bigsoundbank.com/heartbeat-1-s0243.html | yes | same CC0 text | "Heartbeat #1", Denis Chardonnet. 1 s, stereo, 44.1 kHz 16 bit. One dry beat | accepted, backup |
| bigsoundbank-s0218 | https://bigsoundbank.com/heart-beat-s0218.html | yes | same CC0 text | "Heart Beat", ten beats, "slight background noise" | accepted, not used (noise) |
| bigsoundbank-s2081 | https://bigsoundbank.com/chimes-dream-3-s2081.html | yes | same CC0 text | "Chimes dream #3", Joseph Sardin. 2 s, mono, 48 kHz 24 bit | **accepted** |
| bigsoundbank-s1799 | https://bigsoundbank.com/whoosh-6-s1799.html | yes | same CC0 text | "Whoosh #6", wooden sheet, 1 s, stereo, 48 kHz 24 bit | accepted, backup for `throw_shield` (weak fit) |
| bigsoundbank-s0582 / s0583 | https://bigsoundbank.com/four-dice-on-wooden-table-s0582.html and https://bigsoundbank.com/four-dice-in-hand-s0583.html | yes | same CC0 text | 23 s and 13 s, mono, 48 kHz | accepted, backup for dice (Kenney casino is the main pick) |

### 1c. Opened and rejected

| Page URL | Opened | What the page showed | Verdict |
|---|---|---|---|
| https://opengameart.org/content/horror-unsettling-victory-loop | yes | "License(s): CC-BY 4.0", Clement Panchout, 4.2 Mb WAV | **rejected: CC-BY** |
| https://opengameart.org/content/victory-song | yes | "CC-BY 3.0" and "OGA-BY 3.0" | **rejected: attribution required** |
| https://opengameart.org/content/victory-fanfare-short | yes | no license row; author asks to be contacted and to join a mailing list for permission | **rejected: conditions** |
| https://opengameart.org/content/win-jingle, /ambient-horror-track-01, /defeat | yes | description only, license not shown | **rejected: license not visible** |
| https://opengameart.org/content/heartbeat-sounds (also via lpc mirror), /heartbeat-single-sound, /2-dice-roll-29-throws, /wooden-dice-on-wodden-table-roll, /swishes-sound-pack, /swish-bamboo-stick-weapon-swhoshes, /ghost, /100-cc0-sfx, /ancient-caverns-horror-ambient-loop, /abandoned-passages-horror-ambience-loop, /sound-effects-11, /cc0-special-effects, /special-effects-cc0 | yes | no license row (some show only a date). Comments on two pages say "CC0", which is not the page license | **rejected: license not visible** |
| https://opengameart.org/content/rpg-sound-archive-spooky-and-monsters | yes | collection of links, no license | not usable as a source |

### 1d. Could not open

| URL | Result |
|---|---|
| https://dnd.opengameart.org/... (6 pages tried) | could not open: certificate name mismatch |
| https://lpc.opengameart.org/content/20-sword-sound-effects-attacks-and-clashes and `/lanterns-in-the-hollowed-forest` | could not open: HTTP 403 |
| https://www.opengameart.org/... | not followed: 301 to another origin |
| https://opengameart.org/art-search-advanced?... (CC0 filter) | opened, only the empty search form came back |
| https://bigsoundbank.com/search?q=swish and `?q=magical` | opened, result lists did not render |
| https://github.com/Calinou/kenney-casino-audio, `kenney-sci-fi-sounds`, `kenney-music-jingles` | could not open: HTTP 404 |
| Pixabay sound pages | not opened. Rejected by policy: the Pixabay license is not CC0 |

## (b) Event -> chosen file

All are candidates. Nobody has heard them. "Fit" is judged from the file name or page description only. File names for Kenney packs come from the third-party listings in 1b. Attribution note for every row: **none required, credit as a courtesy** (Kenney, Joseph Sardin / BigSoundBank, or the OGA author named).

| Event | Page URL (pack) | File name inside the pack | Format | License | Fit note (unverified) |
|---|---|---|---|---|---|
| ui_click | https://kenney.nl/assets/interface-sounds | `click_001.ogg` | OGG | CC0 | name-based |
| ui_hover | https://kenney.nl/assets/interface-sounds | `tick_001.ogg` | OGG | CC0 | name-based |
| dice_result | https://kenney.nl/assets/interface-sounds | `tick_002.ogg` | OGG | CC0 | name-based. `tick_003` does not exist in the pack |
| item_pickup | https://kenney.nl/assets/interface-sounds | `confirmation_001.ogg` | OGG | CC0 | name-based |
| dice_rattle | https://kenney.nl/assets/casino-audio | `dice-shake-1.ogg` | OGG | CC0 | name-based. The map says nine clicks in 0.9 s, so a trim may be needed |
| round_start | https://kenney.nl/assets/impact-sounds | `impactBell_heavy_000.ogg` | OGG | CC0 | name-based |
| impact_unit | https://kenney.nl/assets/impact-sounds | `impactPunch_medium_000.ogg` | OGG | CC0 | name-based |
| impact_unit_heavy | https://kenney.nl/assets/impact-sounds | `impactPunch_heavy_000.ogg` | OGG | CC0 | name-based |
| impact_fence | https://kenney.nl/assets/impact-sounds | `impactPlank_medium_000.ogg` | OGG | CC0 | name-based (wood) |
| impact_ground | https://kenney.nl/assets/impact-sounds | `impactGeneric_light_000.ogg` | OGG | CC0 | weak fit, name-based |
| shield_block | https://kenney.nl/assets/impact-sounds | `impactMetal_heavy_000.ogg` | OGG | CC0 | name-based. Synthesized `shimmer` stays on top |
| move_step | https://kenney.nl/assets/impact-sounds | `footstep_grass_000.ogg` | OGG | CC0 | name-based (graveyard grass) |
| throw_cannon | https://kenney.nl/assets/sci-fi-sounds | `lowFrequency_explosion_000.ogg` | OGG | CC0 | name-based. Sci-fi timbre may not fit |
| impact_ground_heavy | https://kenney.nl/assets/sci-fi-sounds | `lowFrequency_explosion_001.ogg` | OGG | CC0 | weak fit, name-based |
| shield_place | https://kenney.nl/assets/sci-fi-sounds | `forceField_000.ogg` | OGG | CC0 | name-based. Synthesized `shimmer` stays on top |
| poison_tick | https://kenney.nl/assets/sci-fi-sounds | `slime_000.ogg` | OGG | CC0 | name-based |
| ultimate_ready | https://opengameart.org/content/short-jingle | `PositiveChoice.ogg` (83.7 Kb) | OGG | CC0 | description "a few musical notes, somewhat positive". Not a confirmed four-note rise |
| throw_spear | https://bigsoundbank.com/whoosh-2-s0573.html | not shown; planned `whoosh-2.wav` (13 s) | WAV or MP3, convert to OGG | CC0 | page says sword or arrow whoosh. Trim to one swoosh |
| low_hp_heartbeat | https://bigsoundbank.com/heartbeat-3-s0770.html | not shown; planned `heartbeat-3.wav` (33 s) | WAV or MP3, convert to OGG | CC0 | trim a 12 s loop or less |
| heal | https://bigsoundbank.com/chimes-dream-3-s2081.html | not shown; planned `chimes-dream-3.wav` (2 s) | WAV or MP3, convert to OGG | CC0 | weak fit: a chime cluster, not two rising notes |

**20 of 30 events have a candidate.**

Music layers (not events, not added to the JSON):

| Layer | Page URL | File | Size | License | Note |
|---|---|---|---|---|---|
| bed | https://opengameart.org/content/creepy-ambient-loop | `creepyloop-v2.ogg` | 1 Mb | CC0 | replaces the rejected Lanterns track. Tempo and loop point unknown |
| tension | https://opengameart.org/content/lost-in-a-bad-place-horror-ambience-loop | `lost.ogg` | 2.8 Mb | CC0 | replaces the rejected Horror Loop. Space-horror pads |
| defeat sting | https://opengameart.org/content/game-over-dark-short-music-clips | `gameoverdark.ogg` | 168.8 Kb | CC0 | backups: `gameoverstrangesounding.ogg`, `losegamemusic.ogg` (https://opengameart.org/content/lose-game-short-music-clip, 135.2 Kb) |
| victory sting | none | none | n/a | n/a | no dark victory sting passed the license check. `PositiveChoice.ogg` is positive in tone and may not fit |

The sound-design rule for the file bed (section 2.4 of `docs/sound_design.md`) still holds: a file layer does not follow the 80 BPM step clock.

## (c) Uncovered events (keep the synthesized fallback)

| Event | Why |
|---|---|
| charge | no source searched for a power-following hum. Synthesized by design |
| throw_shuriken | no CC0 whirr with a visible license found |
| throw_shield | only `Whoosh #6` (wooden sheet) was found, a weak fit, left unassigned |
| flight_spear, flight_shuriken, flight_cannon, flight_shield | looped air textures, no source searched. Synthesized by design |
| impact_fence_break | no wood-splinter sound with a visible license found. Kenney `impactPlank_medium_*` could be tried by ear |
| round_end | needs three falling bells. Only single bell strikes exist (`impactBell_heavy_*`) |
| ko | no ghost wail with a visible license found. The OGA "Ghost" page had no license row |

Ghost shimmer (the `shimmer` sparkle layer): `Chimes "dream" #3` (bigsoundbank-s2081) is a possible source, but it is not wired to any event as a sparkle. Decide by ear.

## (d) Download plan

Rules: the main line downloads only after the owner approves this list. Keep one folder per pack, only the listed files, plus a `LICENSE_<source>.txt`. Convert WAV/MP3 to OGG, trim silence, normalize peaks to about -3 dBFS. Record each kept file in `assets/audio/CREDITS.md` as the task 20 checklist says.

| Folder | Download page | Whole-pack size seen | Files to keep | Login | License file to write |
|---|---|---|---|---|---|
| `(not published)` | https://kenney.nl/assets/interface-sounds | 834.5 Kb (OGA copy) | `click_001.ogg`, `tick_001.ogg`, `tick_002.ogg`, `confirmation_001.ogg` | none seen | `LICENSE_kenney-interface.txt`: URL, date, "Creative Commons CC0" from the zip's license file, plus the FAQ URL https://kenney.nl/support |
| `(not published)` | https://kenney.nl/assets/casino-audio | 876.8 Kb (OGA copy) | `dice-shake-1.ogg` | none seen | `LICENSE_kenney-casino.txt` (same form) |
| `(not published)` | https://kenney.nl/assets/impact-sounds | not shown | `impactBell_heavy_000.ogg`, `impactPunch_medium_000.ogg`, `impactPunch_heavy_000.ogg`, `impactPlank_medium_000.ogg`, `impactGeneric_light_000.ogg`, `impactMetal_heavy_000.ogg`, `footstep_grass_000.ogg` | none seen | `LICENSE_kenney-impact.txt`, text seen: "Creative Commons CC0" |
| `(not published)` | https://kenney.nl/assets/sci-fi-sounds | 5.9 Mb (OGA copy) | `lowFrequency_explosion_000.ogg`, `lowFrequency_explosion_001.ogg`, `forceField_000.ogg`, `slime_000.ogg` | none seen | `LICENSE_kenney-scifi.txt`, text seen: "Creative Commons CC0" |
| `(not published)` | https://opengameart.org/content/short-jingle | file 83.7 Kb | `PositiveChoice.ogg` | none stated for download | `LICENSE_oga-short-jingle.txt`: URL, date, "License(s): CC0", "Public Domain. No attribution needed." |
| `(not published)` | https://opengameart.org/content/creepy-ambient-loop | 1 Mb | `creepyloop-v2.ogg` | none stated | `LICENSE_oga-creepy-ambient-epb9000.txt`: "License(s): CC0", author epb9000 |
| `(not published)` | https://opengameart.org/content/lost-in-a-bad-place-horror-ambience-loop | 2.8 Mb | `lost.ogg` | none stated | `LICENSE_oga-lost-in-a-bad-place.txt`: "License(s): CC0", author congusbongus |
| `(not published)` | https://opengameart.org/content/game-over-dark-short-music-clips | 168.8 Kb | `gameoverdark.ogg` (backup `gameoverstrangesounding.ogg`, 124.1 Kb) | none stated | `LICENSE_oga-game-over-dark.txt`: "License(s): CC0", author Robin Lamb |
| `(not published)` | https://bigsoundbank.com/whoosh-2-s0573.html | not shown | one WAV or MP3, saved as `whoosh-2.wav` | page says no account needed | `LICENSE_bigsoundbank-s0573.txt`: URL, date, CC0 text, also https://bigsoundbank.com/licenses.html |
| `(not published)` | https://bigsoundbank.com/heartbeat-3-s0770.html | not shown | one WAV or MP3, saved as `heartbeat-3.wav` | page says no account needed | `LICENSE_bigsoundbank-s0770.txt` |
| `(not published)` | https://bigsoundbank.com/chimes-dream-3-s2081.html | not shown | one WAV or MP3, saved as `chimes-dream-3.wav` | page says no account needed | `LICENSE_bigsoundbank-s2081.txt` |

Each `LICENSE_<source>.txt` must contain the page URL, the date of the check, and the license wording as shown on that day. For the Kenney packs, also copy the license file shipped inside the zip.

Not in the plan: `oga-fantasy-weapons` (accepted, unused), `kenney-rpg`, `kenney-jingles`, and the backups in 1b. Add them only if a listening pass picks one.

## Items for the owner and main line

1. **Test conflict.** The new `candidate_file` field makes `scripts/test_audio.js` fail the test "the JSON file and the map embedded in js/audio.js are identical", because `DEFAULT_EVENT_MAP` in `js/audio.js` has no such field and this task forbids changing that file. Not run (no shell). Fix when wiring: add the field to the embedded map, or compare without it.
2. The existing `file` paths (`assets/audio/sfx/*.ogg`) and `source` keys in the map are unchanged. They do not yet match the folder plan above, and the rejected sources `oga-sword-clashes`, `oga-lanterns-hollowed-forest` and `oga-horror-loop-tinyworlds` are still named in the map and in `docs/audio_sources.md`.
3. Every fit is a guess from a file name. A listening pass is required before wiring any of these.
