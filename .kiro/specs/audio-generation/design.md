# Audio generation: design

Research, verdict and quality notes are in `docs/audio_generation_options.md`. This file covers how the files fit together.

## Flow

```
colab/audio_jobs.json  --upload-->  Drive: PumpkinKiller/inputs/audio_jobs.json
                                         |
                      colab/audio_job.py (Colab A100, Stable Audio Open 1.0, diffusers)
                                         |
          audio_raw/<id>_v<N>.wav  --postprocess-->  audio_out/<id>_v<N>.wav  + generation_log.jsonl
                                         |
              owner downloads, listens, picks one variant per job
                                         |
   scripts/postprocess_audio.py (optional re-run on raw files)  ->  OGG conversion  ->  assets/audio/...
```

## Decisions

| Decision | Why | Cost |
|---|---|---|
| Model: Stable Audio Open 1.0 through `diffusers` | Community License allows small-project use, SFX is its stronger side (card), and the card shows the full call, so the job follows documented code. Supports a negative prompt and a seed. | Older than Stable Audio 3. 44.1 kHz stereo output, 47 s maximum. |
| Stable Audio 3 not coded | The README does not show the return type, a negative prompt or a seed argument, and the install pins `torch==2.7.1`. | Possible quality gain left for later (task 13). |
| License gate (`LICENSE_ACK = False`) | Forces the owner to read the license pages before any model is downloaded. | One edit before the first run. |
| Raw files kept next to final files | Post-processing can be re-run with other settings without paying for generation again. Re-running on final files would apply fades and crossfades twice. | More Drive space (small WAV files). |
| Post-processing duplicated in the Colab job | A Colab cell cannot import from the repo. | Two copies. A test compares them byte for byte, so they cannot drift. |
| `gen_seconds` longer than `duration` for one-shots | Trim needs room, and a request of 0.1 s is far from anything the model was trained on. | Extra hits after the first are cut by the duration cut, not removed. |
| Loops use a crossfade and no fades | A fade-in and fade-out would dip at the seam. | Output is shorter than `duration` by the crossfade length (80 ms). |
| Trim threshold relative to the peak | Works for quiet and loud clips alike. | A long quiet tail (bell decay) is cut at 45 dB below the peak. |
| Mono for effects, stereo for music | Effects are positioned in the game, music is a bed. Halves file size. | Stereo effects detail is lost. |
| 16-bit PCM WAV output | The stdlib `wave` fallback and `soundfile` both write it. | Quantisation noise at 16 bit, below what the game mix hides (not heard). |
| `loop_seam_ratio` as the loop check | Cheap, numpy only, flags a click. | It sees only the step at the seam, not a change of pitch or rhythm. |
| Seed = seed base + variant number | Reruns give the same file for the same model version. | Not a promise across library versions. |

## Data

`audio_jobs.json`:

```
{ version, model, note, jobs: [ {
    id, kind: "sfx" | "music", prompt, negative_prompt,
    duration, gen_seconds, variants, seed_base, loop,
    post: { mono, trim_silence, trim_threshold_db, fade_in_ms, fade_out_ms, peak_dbfs, loop_crossfade_ms },
    note?
} ] }
```

`generation_log.jsonl`: one JSON object per finished file: `file`, `model`, `seed`, `steps`, `prompt`, `negative_prompt`, `license_note`.

## Failure handling

- A failed variant prints `ERR <id> v<N>: <reason>` and the loop continues. It is retried on the next run because no final file exists.
- A crash after the raw file and before the final file leaves a raw file only. The next run regenerates the variant and overwrites the raw file.
- The local script reports `ERR <file>` for an unreadable file and continues.

## Not decided

- Whether Stable Audio 3 sounds better for these 34 jobs (needs listening).
- Whether an 80 ms crossfade is long enough for the music beds (needs listening; raise it per job).
- How many steps are needed. The job uses 100; the model card example uses 200.
