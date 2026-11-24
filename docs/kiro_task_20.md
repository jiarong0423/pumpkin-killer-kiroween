# Kiro task 20 - sound design: music and effect sounds (design + one JS module + its tests)

## Why
The owner says the music is too thin and wants more effect sounds. Today the game has NO music; sound is a few oscillator beeps in `index.html` (`playTone`, `sfx.charge/throw/block/hit/heal`).
The owner wants YOU to design the sound. Use copyright-free (CC0) sounds only. You cannot hear anything and you cannot download files: you design, write the module and the tests,
and list the exact sources; the main line downloads files only after the owner approves, then re-tests everything. Mark every statement about how something sounds as "unverified".

## Do exactly this
1. Read `docs/game_mode.md`, `docs/ROLES.md`, `docs/experience_design.md` if present (the feedback table has sound ideas), `js/particles.js` (preset names only), and the `sfx` and `playTone` code in `index.html` (read only).
2. Write `docs/sound_design.md`:
   a. **Music plan**: the moods (title/lobby, battle calm, battle tense when a unit is below 30% HP or the shield is up, victory, defeat), how they layer (a base ambient bed that always plays + a rhythm layer + a tension layer
      added by game state), loop length, crossfade 1.5 s, key and tempo suggestions (Halloween: minor key, 70-90 BPM, bells / celesta, low pad, soft choir, no melody that fights the sound effects), and the mix rule that music sits 12 dB under effects.
   b. **Effect sound table** for every event: charge (rising hum that follows the power meter), release per weapon (spear whoosh, shuriken whirr, cannon boom with recoil thump, thrown-shield sideways spin), flight, impact on a unit, on the fence, on the ground,
      shield block (metal clang + ghost shimmer), floating-shield placed, dice rattle and result tick, move step, KO, poison tick, ultimate ready, round start / end, UI click and hover, low-HP heartbeat. For each: layers (e.g. body + sparkle), duration, pitch variation (+/- 6 %) so repeats do not sound the same, and priority.
   c. **Mix rules**: master / music / effects volumes, a mute button and a volume slider, ducking (music drops 6 dB for 400 ms on big impacts), max concurrent voices (16), no sound before the first user gesture (browser autoplay rule), and a clean-sound rule: never more than 3 effects at the same moment in the same band.
   d. **Event map**: `docs/audio_event_map.json` mapping every game event name to a sound id, volume, pitch range, priority and the file to load.
3. Write `docs/audio_sources.md`: candidate CC0 sources only, each with name, URL, what it contains, license as stated, `verified: NO - search snippet only`, and which events it could cover. Start from these (found by web search on 2026-11-09, unverified):
   Kenney "Interface Sounds" (CC0, 100 OGG files, https://kenney.nl/assets/interface-sounds), Kenney "Sci-Fi Sounds" (CC0 per OpenGameArt, https://opengameart.org/content/sci-fi-sounds),
   StarNinjas "20 sword sound effects attacks and clashes" (CC0, https://opengameart.org/content/20-sword-sound-effects-attacks-and-clashes), "Fantasy Weapons and Apparel SFX Library" by Jan Schupke (CC0, https://opengameart.org/content/fantasy-weapons-and-apparel-sfx-library),
   music: "Lanterns in the Hollowed Forest" (CC0 per search, Oct 2025), "Haunting Chiptune Loop [Void Estate]" (https://opengameart.org/content/haunting-chiptune-loop-void-estate), "Horror Loop" by TinyWorlds, "Creepy Ambient Loop" by epb9000.
   Exclude anything that is CC-BY or needs attribution unless you flag it clearly. Note the gap: no CC0 pack was found for thrown-object sounds, so say which synthesized sounds (code-made with Web Audio) fill the gap.
4. Write `js/audio.js` (a UMD module like `js/particles.js`: works in Node via `module.exports` and in the browser as global `GameAudio`): `createAudio({ctx, loader, random})` with `unlock()`, `playMusic(mood)`, `setTension(0..1)`, `play(eventName, opts)`, `setVolumes({master, music, sfx})`, `mute(bool)`,
   `update(dt)`. It reads the event map, loads files through the injected `loader` (so tests need no network), and FALLS BACK to a Web Audio synthesized sound for every event when a file is missing, so the game is never silent. Include the synthesized fallbacks
   (whoosh = filtered noise sweep, boom = low sine drop + noise burst, clang = inharmonic partials, shimmer = detuned high sines, heartbeat, dice rattle, bell loop for music). Never throw: on any error log once and keep the game running. Keep the voice limit.
5. Write `scripts/test_audio.js` (Node, `assert`, no network, a fake AudioContext recorder): unlock before play, voice limit never exceeded, mute silences everything, volumes clamp to 0..1, pitch variation stays within +/- 6 %, ducking lowers then restores the music gain, missing-file fallback still plays, unknown event does not throw,
   the event map file parses and every event has a valid entry. Run it with `node scripts/test_audio.js` and put the real last line in your summary.
6. Write the spec `.kiro/specs/sound-design/` (requirements in EARS form, design, tasks).
7. Do not touch `index.html`, `assets/`, other `js/` files or other scripts. Do not download anything. Do not use git. Do not create images.
8. Finish with a 7-line summary and say what you could not verify (you cannot hear the result).

## Owner constraints
- Halloween magic mood, premium feel, but the screen and the sound must not be messy; effects stay readable over the music.
- Only CC0 / public-domain sound files, or sounds synthesized in code. State the license of every file; unknown means "do not use".
- Kiro never generates images; this task is sound only.
