# Kiro task 133 — the reaper is the flame-magic necromancer: remove the stale skull and scythe design (work block B21)

Owner decision (restated 2026-11-15): the reaper (id `reaper`) is the necromancer, a FLAME MAGIC attacker. Normal attack: a purple flame held in the palm, pushed forward. Ultimate: the finger points forward and three ghost fires behind the caster change colour and fly out. No scythe, no knife, no skull. Wait for task 118 to finish before you start (it edits `js/class_stats.js`); if `docs/kiro_118_result_gpt-5.6-terra.md` does not exist yet, stop and write only a result file saying so.

Read: `docs/kiro_118_result_gpt-5.6-terra.md`, `js/class_stats.js` (the reaper rows and the `reaper_combo`/execute rule), `scripts/test_class_stats.js`, `scripts/sim_balance.js`, `js/ultimate_fx.js` (`reaper_triple_slash` and `necro_ghostfire_trio`), `scripts/test_ultimate_fx.js`, `docs/ultimate_mapping.md` (row 7 and the sound/effect column), `docs/converge_characters.md`, `js/particles.js` (obsolete presets `scythe_slash_fx`, `weapon_trail_skull`), `(not published)` rows about the flame redesign (read only; do not copy private remarks).

Do, saving after each:
1. `docs/ultimate_mapping.md` row 7 and `docs/converge_characters.md`: rewrite the reaper/necromancer entry to the flame design (name, normal attack, ultimate, effects, sounds), mark every number that was invented for the old skull/scythe as obsolete and keep a flame number only if a source gives it; add one line "superseded 2026-11-15, owner" where the old text was.
2. `js/class_stats.js`: remove the skull/scythe combo and the 30 percent execute rule from the reaper entry; replace with a flame profile (normal damage and burn from the owner log or task 53 if it states them, else named constants marked `PROVISIONAL, owner to confirm`). `scripts/sim_balance.js` and both tests follow.
3. `js/ultimate_fx.js`: delete `reaper_triple_slash` and its tests; keep `necro_ghostfire_trio`; make `timeline("reaper_flame_trio", input)` an alias of it for the id used by the page.
4. Do not delete the obsolete particle presets (`js/particles.js`): list them in the result file as candidates for a later clean-up.
5. Run `node scripts/test_class_stats.js`, `node scripts/test_sim_balance.js`, `node scripts/test_ultimate_fx.js`, `node scripts/test_particles.js`; paste the last lines. If a shell call is refused, say so; do not invent output.

Touch only `docs/ultimate_mapping.md`, `docs/converge_characters.md`, `js/class_stats.js`, `scripts/sim_balance.js`, `scripts/test_class_stats.js`, `scripts/test_sim_balance.js`, `js/ultimate_fx.js`, `scripts/test_ultimate_fx.js` and the result file exactly named `docs/kiro_133_result_gpt-5.6-terra.md` (max 15 lines). Do not edit `index.html`. No network, no git.
