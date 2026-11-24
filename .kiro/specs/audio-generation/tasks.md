# Audio generation: tasks

- [x] 1. Read `docs/audio_event_map.json`, `docs/sound_design.md`, `docs/audio_sources.md`, `colab/pumpkin_assets_job.py`
- [x] 2. Research Stable Audio Open 1.0 and Small, MusicGen, AudioLDM 2, Tango 2, TangoFlux, Stable Audio 3, MOSS-SoundEffect v2.0, ACE-Step 1.5 on the public pages (R1)
- [x] 3. Write `docs/audio_generation_options.md`: model tables, verdict, quality notes, what Kiro can and cannot do (R1, R6)
- [x] 4. Write `colab/audio_jobs.json`: 30 events plus 4 music jobs, 3 variants each (R2)
- [x] 5. Write `colab/audio_job.py` (R1, R3, R4)
- [x] 6. Write `scripts/postprocess_audio.py` (R4)
- [x] 7. Write `scripts/test_postprocess_audio.py` (R5)
- [ ] 8. Run `python3 -B scripts/test_postprocess_audio.py` and fix failures (NOT DONE in the task that wrote it: Kiro had no shell. The owner or the main line runs it. Expected last line: `test_postprocess_audio: 26 passed, 0 failed`)
- [ ] 9. Owner reads the license pages in `docs/audio_generation_options.md` section 2.3, registers with Stability AI, accepts the model terms on Hugging Face, checks the contest rules
- [ ] 10. Owner uploads `colab/audio_jobs.json` to `MyDrive/PumpkinKiller/inputs/`, opens a fresh Colab A100 runtime, runs cell 1 and then `colab/audio_job.py` with `LICENSE_ACK = True` and `ONLY = ["throw_spear"]` first
- [ ] 11. Owner listens to every variant and picks one per job. Reports problems per job ("voice", "too long", "loop clicks")
- [ ] 12. Kiro re-tunes the prompts in `audio_jobs.json` for the rejected jobs. Owner re-runs those jobs
- [ ] 13. Optional: try Stable Audio 3 `small-sfx` on the weakest jobs and compare by ear
- [ ] 14. Main line converts the chosen WAV files to OGG, names them as in `docs/audio_event_map.json`, writes `assets/audio/CREDITS.md` with the model, license and the Stability credit line
- [ ] 15. Kiro updates `docs/audio_event_map.json` (`file`, `source`) and `js/audio.js` defaults for the files that exist, and extends `scripts/test_audio.js`
- [ ] 16. Tell the entry that the audio is AI generated (Stability's acceptable use policy asks not to mislead people about AI-made content)
