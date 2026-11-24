# Sound design: tasks

- [x] 1. Read `docs/game_mode.md`, `docs/ROLES.md`, `js/particles.js`, and the `sfx` / `playTone` code in `index.html` (`docs/experience_design.md` does not exist)
- [x] 2. Write `docs/sound_design.md`: music plan, effect table, mix rules (R3, R6, R7, R8)
- [x] 3. Write `docs/audio_event_map.json` with 30 events and the music block (R3)
- [x] 4. Write `docs/audio_sources.md`: candidate CC0 sources, unverified, with the thrown-object gap (no download)
- [x] 5. Write `js/audio.js`: UMD module, graph, voices, ducking, music scheduler, synthesized fallbacks (R1 to R8)
- [x] 6. Write `scripts/test_audio.js` with a fake AudioContext (R1 to R8)
- [x] 7. Run `node scripts/test_audio.js` and fix failures (last line: `test_audio: 32 passed, 0 failed`, exit code 0)
- [ ] 8. Listening pass in a browser: tune recipes, levels and the 12 dB gap by ear (needs ears, main line / owner)
- [ ] 9. Owner approves the source list in `docs/audio_sources.md`
- [ ] 10. Main line downloads approved files, checks the license on each page, writes `assets/audio/CREDITS.md`, converts to OGG, uses the file names from the event map
- [ ] 11. Wire into `index.html` (after the file lock is free): load `js/audio.js`, call `unlock()` on the first gesture, replace `playTone` and `sfx.*`, call `update(dt)` each frame, add the mute button and volume slider
- [ ] 12. Check the clean-sound rule and the music / effects balance with the real game running
- [ ] 13. Decide the open questions in `docs/sound_design.md` section 8 (stinger, music slider, timer tension)
