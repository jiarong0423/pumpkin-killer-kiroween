# Sound design: design

Full sound design and the effect table are in `docs/sound_design.md`. This file covers how `js/audio.js` is built.

## Graph

```
voice gain -> sfx bus ----------------------> master -> compressor -> destination
layer gain -> music bus (-12 dB trim) -> duck -> master
```

- `master` takes the master volume and the mute.
- `sfx` takes the effects volume.
- `music` takes the music volume times 0.251.
- `duck` is driven by the ducking envelope.
- Each of the 5 music layers has its own gain into the music bus.

## Injection

`ctx`, `loader`, `random`, `eventMap` and `log` are injected. The module never reads a global. This lets `scripts/test_audio.js` run in Node with a fake context that records created nodes and parameter values.

## Play path

1. Reject if locked, muted, or the name is unknown.
2. Prune voices that have ended (time based, from `ctx.currentTime`).
3. If a loop with this name is running, update it and return.
4. Apply the cooldown, then the band cap and the voice limit (replace or drop).
5. Pick the pitch from the injected `random`.
6. Build the body: the loaded file if there is one, otherwise the synthesized recipe. If the file throws, use the recipe.
7. Add the sparkle recipe if the entry has one.
8. Register the voice. If the entry has the duck flag, start the duck.

## Recipes

Each recipe is a function `E -> duration` (or `{dur, update}` for loops). They use four primitives: `osc` (decaying oscillator), `noise` (filtered noise burst, optional tremolo), `sustainedOsc` and `sustainedNoise` (for loops), and `bell` (inharmonic partials). A shared 2 s noise buffer is made at unlock from the injected `random`. If it cannot be made, noise parts are skipped and oscillator parts still play.

## Music scheduler

All synthesized layers share one clock of 64 eighth-note steps (8 bars, 24 s at 80 BPM). `update()` schedules every step that falls inside the next 0.4 s, at most 16 per call. Drones (bed, tension, defeat) are long-lived oscillators created when the layer starts and stopped when it ends. Notes are short oscillators that stop themselves.

## Ducking

`update(dt)` advances a small state machine: hold for 0.4 s at 0.501 (-6 dB), then release linearly over 0.3 s. Parameter changes use `setTargetAtTime` with a 15 ms constant to avoid clicks.

## Decisions

| Decision | Why | Cost |
|---|---|---|
| Synthesis first, files optional | The game is never silent, and the work is testable now. | Synthesized sound may be thin. Needs a listening pass. |
| Embedded default map plus JSON copy | Works when the JSON is not served. | Two copies. A test keeps them equal. |
| Time-based voice expiry | Needs no `onended` callbacks, so it is the same in Node and browser. | A voice may count a few ms after it ends. |
| Effects counted apart from music | Music has a fixed small number of layers. | Total sources can exceed 16. |
| Loops end on their own | A forgotten `stop()` cannot leave a sound stuck. | A loop restarts after its duration, with a gap of about one frame. |
| Tonal events vary only ±1% | Stay in key. | Less variation on bells. |

## Not decided

- Whether a file bed and the synthesized rhythm layer stay in time (needs a listening test).
- Whether a stinger plays before the victory and defeat layers.
