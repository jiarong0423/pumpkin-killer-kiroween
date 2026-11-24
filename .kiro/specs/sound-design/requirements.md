# Sound design: requirements

Scope: `js/audio.js` (module), `docs/audio_event_map.json` (event data), `scripts/test_audio.js` (tests), and the design in `docs/sound_design.md`. Candidate files are in `docs/audio_sources.md`. Wiring into `index.html` and downloading files are out of scope for this spec.

Terms: **module** is `js/audio.js`. **Event** is a game event name such as `throw_cannon`. **Voice** is one playing effect. **Layer** is one continuous music track (bed, rhythm, tension, victory, defeat). **Mood** is a set of target layer levels. **Fallback** is a sound made in code with Web Audio.

All statements about how a sound sounds are unverified. No requirement below can be checked by listening in this task.

## R1 Module shape

1. The module shall not reference `window`, `document`, `Math.random`, `Date` or any other I/O.
2. When loaded by Node, the module shall export its API through `module.exports`.
3. When loaded by a browser script tag, the module shall expose its API as the global `GameAudio`.
4. `createAudio({ctx, loader, random, eventMap, log})` shall return an object with `unlock`, `playMusic`, `setTension`, `play`, `setVolumes`, `mute` and `update`.
5. Where `random` is absent, the module shall use a fixed-seed generator.
6. Where `ctx` is a function, the module shall call it at `unlock()` and not before.

## R2 Autoplay

1. While `unlock()` has not been called, `play()` shall start no sound and return null.
2. When `unlock()` is called, the module shall build the audio graph, call `ctx.resume()` once, and start loading files through the loader.
3. When `playMusic`, `setVolumes` or `mute` is called before `unlock()`, the module shall remember the value and apply it at unlock.

## R3 Event map

1. The module shall read the event map passed as `eventMap`, or its embedded `DEFAULT_EVENT_MAP` where none is passed.
2. `docs/audio_event_map.json` shall contain, for each of the 30 events, a sound id, file, source, fallback recipe, volume, pitch range, priority 1 to 5, band, duration, loop flag, duck flag and cooldown.
3. The embedded map shall be identical to the JSON file.
4. Where a map entry is invalid, the module shall ignore that entry.

## R4 Fallback and failure

1. Where an event has no loaded file, the module shall play its synthesized fallback.
2. Where a loader returns null, rejects, throws, or returns a buffer without a positive duration, the module shall treat the file as missing and log one summary line.
3. If playing a loaded file throws, then the module shall play the fallback for that call.
4. If any Web Audio call throws, then the module shall catch the error, count it, log it once per message, and keep running.
5. When `play()` is called with an unknown event name or a non-string, the module shall return null and log once per name.
6. No public method shall throw.

## R5 Pitch variation

1. When a sound plays, the module shall pick a pitch multiplier uniformly in the entry's pitch range using the injected `random`.
2. The module shall clamp every pitch range to 0.94 to 1.06.
3. The same seed and the same calls shall give the same pitches.

## R6 Voices and clean sound

1. The module shall keep at most 16 effect voices at once.
2. When a new sound arrives and 16 voices exist, the module shall replace the lowest-priority, oldest voice if the new priority is equal or higher, and otherwise drop the new sound.
3. When 3 voices of one band started within 150 ms and a fourth arrives, the module shall apply the same replace-or-drop rule within that band.
4. When a loop event is played while it is running, the module shall update it and not start a second voice.
5. When a loop has run for its `duration`, the module shall end it.
6. While an event is within its `cooldownMs` of the last play, the module shall ignore the call.

## R7 Volume, mute, ducking

1. `setVolumes({master, music, sfx})` shall clamp each value to 0 to 1 and ignore values that are not finite numbers.
2. The music bus shall have a fixed -12 dB trim, so music with both sliders at 1 is 12 dB under effects.
3. While muted, the master gain shall be 0 and `play()` shall start no sound.
4. When an event with the duck flag plays, the module shall lower the music gain by 6 dB, hold it for 400 ms, then restore it over 300 ms as `update(dt)` advances.
5. When another duck event plays during the hold, the module shall restart the hold.

## R8 Music

1. When `playMusic(mood)` is called with a known mood, the module shall fade the layer levels to the mood's targets over 1.5 s.
2. The bed layer shall have a level above 0 in every mood.
3. When `setTension(x)` is called with a finite number, the module shall clamp it to 0 to 1 and, in battle moods, raise the tension and rhythm layers over 0.8 s.
4. While a layer's target is 0 and its fade has finished, the module shall stop its sources.
5. Where a layer has a loaded file, the module shall loop the file. Otherwise the module shall play the synthesized layer from the shared 80 BPM step clock.
6. If the clock jumps by more than 1 s, then the module shall restart the scheduler and not schedule a backlog.
