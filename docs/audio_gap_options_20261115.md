# Audio gap options (Kiro task 94, 2026-11-15)

Read only. Nothing was downloaded, played or heard. Durations of the source files are not recorded in `docs/audio_sources_verified.md` or `docs/audio_sources.md`; the only numbers below are the planned lengths in the event map.

## Missing-file behaviour (`js/audio.js`)
A missing file falls back silently to the synthesized recipe, and the game is not silenced. `preload()` stores `cache[f] = null` when the loader rejects or returns no buffer (lines 1403-1413). `usableBuffer` then returns null (1382-1384). `play` runs the synth recipe `R[entry.synth]` called with the event `E` when no file was used (1584-1588). The only trace is one `warnOnce('missing-files', ...)` line after preload. Not verified: whether the loader in `index.html` logs a 404 per file.

## move_step (`(not published)`, planned 0.25 s)
- Candidate: `footstep_grass_000.ogg`, Kenney Impact Sounds, https://kenney.nl/assets/impact-sounds, "Creative Commons CC0" (audio_sources_verified.md, section b and 1b). The name came from a third-party listing, not from the zip. The pack is not in `assets/audio/_licenses/` yet, so adding it needs a new `LICENSE_kenney-impact.txt`.
- Already covered: the event map (and the copy in `js/audio.js`, lines 603-634) lists `assets/audio/sfx/step_leaf.ogg` as a `variant` extra with chance 0.5. That file exists and has a CREDITS row (source recorded only as "CC0 (see docs/audio_sources.md)"). Half of the steps play it, the other half play the synth `step`, and nothing is ever loaded from `move_step.ogg`.
- Recommendation: drop the `file` reference (set it to null in both copies of the map). No new licence work, and `step_leaf.ogg` stays.

## item_pickup (`(not published)`, planned 0.4 s)
- Candidate: `confirmation_001.ogg`, Kenney Interface Sounds, https://kenney.nl/assets/interface-sounds, CC0 per https://kenney.nl/support (no licence row on the page itself). Name-based fit only; "confirmation" may sound too clean for a haunted game.
- The pack is already used: `ui_click`, `ui_hover` and `dice_tick` come from it, and `LICENSE_kenney-interface.txt` exists. The cost is one more file and one CREDITS row.
- Fires today: `index.html` calls `snd("item_pickup")` for the player and for the AI when a crate is taken (lines 1501 and 1505).
- Recommendation: add the file only if the owner likes it after one listen; otherwise set `file` to null. Do not add it unheard.

## ultimate_ready_chime (`(not published)`, planned 1.5 s)
- Verified candidate: only `PositiveChoice.ogg`, OGA "Short Jingle" by OO, CC0, 83.7 Kb (audio_sources_verified.md). The file is already in the game as `music/victory_sting.ogg`, and the doc calls it "not a confirmed four-note rise". The mapped source `kenney-scifi` has no verified file name for a chime.
- Not verified: no CC0 source with a visible licence is recorded for this event.
- Nothing calls it: `index.html` has no `ultimate_ready` call, and `docs/kiro_74_flow_plan_claude-sonnet-5.5.md` (section on sound) records "defined, never fired". The owner has not designed the ultimate cues.
- Recommendation: drop the file reference (null) and keep `arpeggio_up` plus `shimmer`. Revisit when ultimates are wired.

## Note for whoever changes the map
`docs/audio_event_map.json` and the `DEFAULT_EVENT_MAP` in `js/audio.js` must stay identical (`node scripts/test_audio.js` checks it). Edit both together. Not done in this task.
