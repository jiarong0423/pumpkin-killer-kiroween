# Gameplay experience: tasks

Nothing is started. All tasks wait for the owner's approval of `docs/experience_design.md` (questions in section h).
"T" means a Node test that can run without a browser. "H" means a human has to look or listen.

- [ ] 1. `(not published)`: frozen `FX_BUDGET` with every number from R1 and R2. (T: values equal the requirements)
- [ ] 2. `(not published)`: hit-stop, shake, flash, slow motion with the R2 limits and "larger shake wins". (T)
- [ ] 3. `(not published)`: last 4 landings, alpha 1.0/0.7/0.45/0.25, "short N / long N" tag. (T)
- [ ] 4. `(not published)`: three-hint state machine and local flag. (T)
- [ ] 5. New preset `shock_ring` in `js/particles.js`. (T: emits 1 particle for any opts)
- [ ] 6. New presets `landing_pillar`, `ash_fall`, `shield_dissolve`, `pip_pop`. (T)
- [ ] 7. New presets `ultimate_ready_pulse`, `banner_embers`. (T)
- [ ] 8. New presets `wind_motes`, `turn_marker_wisp`. (T: live count under the ambient budget over 60 s of calls)
- [ ] 9. New preset `weapon_trail_shuriken`. (T)
- [ ] 10. Measure the real particle count of every preset at scale 1.25 and write it to `(not published)`; compare with the table in `docs/experience_design.md` section c. (T)
- [ ] 11. `(not published)`: event to plan for hit, block, ground, fence. (T: preset names, screen values from R3.3-R3.5, R3.13)
- [ ] 12. Director: release, flight and charge events. (T: R3.1, R3.2)
- [ ] 13. Director: KO, poison applied, poison tick. (T: R3.6-R3.8)
- [ ] 14. Director: shield placed, ultimate ready, pip, round start. (T: R3.9-R3.12)
- [ ] 15. Director: budget enforcement, drop order, half scale first. (T: R1.1-R1.5, R4.4, R4.5)
- [ ] 16. Director: rolling 1000 ms one-shot limit. (T: R1.4)
- [ ] 17. Director: HUD rectangle clipping. (T: R4.1)
- [ ] 18. Director: reduced effects mode. (T: R2.6)
- [ ] 19. Director: determinism and no forbidden globals. (T: R5.1, R5.2)
- [ ] 20. Stress test: scripted 60 s match, assert peak live count at most 300 normal and 450 in an ultimate, hard cap never reached. (T: R1.1, R1.2, R1.3)
- [ ] 21. Poison mist duration: use 5 s and update task 15 of the `particles` spec to match. (T: `poison_cloud` life between 3.5 and 5 s)
- [ ] 22. Pity pip logic in the rules engine (needs owner "yes" to question 6). (T) [RULE CHANGE]
- [ ] 23. Round-1 timer grace (needs owner "yes" to question 9). (T) [RULE CHANGE]
- [ ] 24. Wire the director, screen_fx and landing pillars into `index.html` (main line, after `index.html` is free). (H)
- [ ] 25. Move the charge gauge off the body, add text plates for instruction lines. (H, unverified)
- [ ] 26. Agent "thinking" swirl and learning ticker from `set_notes`. (T for the text cap and no extra info; H for the look)
- [ ] 27. Game-over recap overlay from public history. (T for the data; H for the look)
- [ ] 28. CC0 sounds and mute button, started after the first press. (T for pitch function and mute; H for the sound)
- [ ] 29. Human tuning pass with the checklist: flash and shake do not hurt, effects never hide a character or HUD, the first throw can be done without reading, the three demo moments in `docs/experience_design.md` section g can be filmed. (H, unverified)
