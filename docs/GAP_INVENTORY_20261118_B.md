# Gap inventory B (2026-11-18, evening): effects per role, sounds, music, MCP, release

Owner 2026-11-18: "match which role uses which effect", "sounds also", "background music also", "finish the gap inventory", "the most important, the MCP", "I will put it online after you have done everything". Facts below come from the code and the files (commands in the last section), nothing was heard.

## 1. Roles and effects (what exists, what is a stand-in, what the new CC0 pack fills)
New pack: Kenney "Particle Pack 1.1", CC0, 80 sprites 512 x 512, downloaded 2026-11-18 from kenney.nl (licence text in `assets/fx/kenney/License.txt` once copied; credit line goes into `(not published)`).

| role | weapon | throw sound | flight trail | hit / status | ultimate | gap | proposed match (Kenney) |
|---|---|---|---|---|---|---|---|
| skeleton | proj_spear | throw_spear (own) | weapon_trail_spear (own) | bleed (blood spray) | triple javelin (ULT module `skeleton_triple_javelin`) | none big | cold light streak: `trace_*` behind the spear (optional) |
| wizard | cannonball (code-drawn pumpkin) | throw_cannon (own) | weapon_trail_cannon (own) | poison puff | pumpkin blast (module `wizard_pumpkin_blast`) | none big | `flame_*` embers on the shell (optional) |
| bat | proj_shuriken | throw_shuriken (own) | weapon_trail_dart (own) | slow text | shuriken rain (module `bat_shuriken_rain`) | none big | `spark_*` on the hit |
| knight | proj_shield | throw_shield (own) | falls back to weapon_trail_shield (right one) | lifesteal text | shield wall (own code) | none big | `circle_03` ring where the wall stands |
| reaper | proj_flame | stand-in: throw_shuriken | own purple embers | burn | hallucination flames (own code) | own throw sound | `flame_*` already similar; `magic_05` glow on the palm |
| hag (nun) | proj_cross | stand-in: throw_shuriken | falls back to weapon_trail_shield (WRONG) | shock spark | double cross, stun (own code) | own throw sound, own trail | `star_06` + `magic_03` behind the cross |
| bride | proj_soundwave | stand-in: throw_shuriken | none (rings) | poison | bat swarm (own code) | own throw sound, vortex look | `twirl_02` / `twirl_03` as the rotating vortex under the rings (replaces the Colab vortex job, `docs/COLAB_SPEC_BRIDE_WAVE_20261118.md`) |
| hunchback | proj_axe | stand-in: throw_spear | falls back to weapon_trail_shield (WRONG) | bleed, knockback | boomerang axe (own code) | own throw sound, own trail | `slash_*` arc behind the axe |
| ALL | armed ultimate aura | - | - | - | white-hot core, light pillar, sparks (code only, drawn 2026-11-18) | the owner finds it weak | `circle_05` core, `star_06` sparks, `circle_03` ground ring, tinted per role colour (`ULT_RING_COLOR`) |

## 2. Sounds
- 30 events in `js/audio.js` DEFAULT_EVENT_MAP (same as `docs/audio_event_map.json`); every file the map names exists (0 missing).
- 10 events have NO file and play the synthesized fallback only: round_start, round_end, charge, flight_spear, flight_shuriken, flight_cannon, flight_shield, move_step, poison_tick, ultimate_ready.
- The design `docs/sound_mapping.json` already assigns files that sit in `assets/audio/sfx` (bell_round.ogg, step_leaf.ogg, ...) to these events, but the event map was never updated: wiring only.
- Throw sounds: 4 own events (spear, shuriken, cannon, shield); flame, soundwave, axe, cross borrow them (`THROW_SOUND` stand-ins, index.html:933). Missing: throw_flame, throw_soundwave, throw_axe, throw_cross, and ultimate cast / impact sounds per role (only `ultimate_ready` exists, with no file).
- 64 audio files in `assets/audio` (sfx, ambient, music); licences in `assets/audio/CREDITS.md`.

## 3. Music
- Files: bed_ambient, alt_haunted_track, bed_artifact_room, tension_drone, victory_sting, defeat_sting, alt_music_box_waltz (all `assets/audio/music`).
- Moods in the code: `battle_calm`, `battle_tense`, victory, defeat. The page starts `battle_calm` on the first gesture and at match start; `battle_tense` is defined but no page call switches to it.
- Missing: start-screen music (silent until a gesture), a switch to the tense mood at low HP or late rounds, volume slider mapping is in the settings sheet (checked 2026-11-17, not rechecked).

## 4. MCP (most important, the demo story)
- Proven in the sandbox: engine rules and seats tests, MCP bridge in a phone-created 1v1 room (fixed a KeyError 'hero' on 2026-11-18), page versus engine flights: 5,040 shots, 0 mismatches after the engine sweep (this evening).
- Not proven: one run on the real phone (`scripts/phone_room_check.py --white mcp --turns 6 --require-phone`, needs `adb reverse tcp:8765 tcp:8765` and `tcp:8080`), socket tests after tonight's engine change (`test_mcp_stdio.py`, `test_relay_*.py`, `e2e_local.py`): they need the owner's terminal; a terminal run is started below.
- Known: Kiro power install `pumpkin-killer-seat` not verified (owner's Kiro UI).

## 5. Release (the owner puts it online after everything is done)
- Hosting plan: Contabo + Coolify behind the Cloudflare tunnel; deploy, push and URL are the owner's step (needs the owner's word, nothing is pushed).
- Before upload: privacy gate (`release-boundary-safety-gate`), clean export, service worker precache regenerated (done with every change), English text check, video.
- Local commits are many and never pushed (latest: see `git log`).

## 6. Other open items from today
- Start screen (`test_start_screen_fit.js`) red until the layout answer (G2b); the seats panel overlay and the map list are fixed.
- Hit rule: area skills (wizard blast 234 px, bride wave 105 px, swarm) still hurt units that were not touched: decided earlier as "both sides count", asked again, no answer yet.
- Real phone checks for the direct arrow drag, the move arrow and the map loop.

## How these facts were gathered
`node -e` on `js/audio.js` (event map against files and `snd(` ids in index.html), `ls assets/audio`, `grep` of `THROW_SOUND`, `ULT_FX_ID`, `ULT_RING_STYLE` in index.html, `docs/sound_mapping.json`, `(not published)`, the Kenney page and archive (`License.txt` read).
