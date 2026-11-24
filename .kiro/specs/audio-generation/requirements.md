# Audio generation: requirements

Scope: `docs/audio_generation_options.md`, `colab/audio_jobs.json`, `colab/audio_job.py`, `scripts/postprocess_audio.py`, `scripts/test_postprocess_audio.py`. Wiring finished files into `js/audio.js` and `docs/audio_event_map.json` is a later step (tasks 10 to 12). Related spec: `.kiro/specs/sound-design/`.

Terms: **job** is one entry of `audio_jobs.json`. **Variant** is one generated file for a job (`<id>_v<N>.wav`). **Raw file** is the model output before post-processing. **One-shot** is a job with `loop` false. **Loop** is a job with `loop` true. **License gate** is the constant `LICENSE_ACK` in the Colab job.

Nothing here is verified by listening or by running the Colab job. Kiro cannot hear audio, run Colab or download models.

## R1 Model choice and license

1. The Colab job shall use only a model whose weights license, as written on its model page, permits use in a contest entry. The job shall name the model in the constant `MODEL_ID` and the license in the constant `MODEL_LICENSE_NOTE`.
2. The documentation shall list, for every model researched, the page that was opened, the weights license as written, and whether the page was opened (yes or no).
3. The documentation shall name every model with non-commercial weights as not to be used.
4. The documentation shall list the exact page URLs the owner must read before generating.
5. While `LICENSE_ACK` is false, the Colab job shall stop before it mounts Drive or loads a model.
6. The Colab job shall write one line per generated file to `generation_log.jsonl` with the model, seed, steps and prompt.

## R2 Job file

1. `audio_jobs.json` shall contain one job for each of the 30 events in `docs/audio_event_map.json`, using the event name as the id.
2. `audio_jobs.json` shall contain jobs `music_bed`, `music_tension_drone`, `music_victory_sting` and `music_defeat_sting`.
3. Each job shall have an id, prompt, negative prompt, duration in seconds, generation length, variant count, seed base, loop flag and post-processing settings.
4. Each job for an event shall have the duration and loop flag of that event in the event map.
5. Each job shall have 3 variants.
6. No prompt or negative prompt shall contain an artist, brand or game name.
7. Where a job is a loop, its post-processing shall use an 80 ms loop crossfade and no fades. Where a job is a one-shot, its post-processing shall use a 5 ms fade in, a 30 ms fade out and no crossfade.
8. Each job shall trim silence and normalise the peak to -3 dBFS.
9. Seed bases shall be unique, and seeds used shall be the seed base plus the variant number.

## R3 Colab job

1. The Colab job shall read `audio_jobs.json` from `MyDrive/PumpkinKiller/inputs/`.
2. For each job and variant, the Colab job shall generate audio with the seed from R2.9, write the raw file, post-process it, and write the result to `MyDrive/PumpkinKiller/audio_out/<id>_v<N>.wav`.
3. When the output file for a variant already exists, the Colab job shall skip that variant.
4. If one variant fails, then the Colab job shall print an `ERR` line and continue with the next variant.
5. When a variant is finished, the Colab job shall print an `OK` line.
6. When all variants have been tried, the Colab job shall print the counts of done, skipped and failed files.
7. If the model output contains NaN, infinity or is silent, then the Colab job shall treat the variant as failed.
8. The Colab job shall write the final file after the raw file, so that an existing final file means the variant is finished.
9. The Colab job shall use numpy and soundfile only for post-processing.

## R4 Post-processing

1. The post-processing shall perform, in this order: optional mono mix, silence trim, cut to the job duration, then crossfade (loops) or fades (one-shots), then peak normalisation.
2. The silence trim shall cut samples below the trim threshold relative to the clip peak, keeping 2 ms before and 10 ms after the sound.
3. When the clip is entirely silent, the trim and the normalisation shall return it unchanged and shall not produce NaN.
4. The loop crossfade shall return a clip shorter than its input by the crossfade length in samples.
5. If the clip is shorter than twice the crossfade length, then the loop crossfade shall raise an error.
6. The peak normalisation shall set the largest absolute sample to the requested dBFS value.
7. A fade longer than the clip shall not raise an error.
8. The loop-check function shall return the step between the last and first sample divided by the mean sample step.
9. The post-processing code in `colab/audio_job.py` shall be identical to the code in `scripts/postprocess_audio.py`.
10. The local script shall process files named `<id>_v<N>.wav` from an input folder to an output folder using the settings in `audio_jobs.json`, and shall continue after a bad file.

## R5 Tests

1. `scripts/test_postprocess_audio.py` shall test silence trim, fades, normalisation and loop crossfade length with synthetic signals.
2. The tests shall check `audio_jobs.json` against R2, including the match with the event map.
3. The tests shall check that the two post-processing copies are identical.
4. The tests shall parse `colab/audio_job.py` without running it.
5. The tests shall print `test_postprocess_audio: <n> passed, <m> failed` as the last line and exit 1 when any test fails.
6. The Colab job shall not be run by any test.

## R6 Honesty

1. The documentation shall state that the Colab job is not tested.
2. The documentation shall state that no generated sound has been heard.
3. Kiro shall not generate, download or convert any audio.
