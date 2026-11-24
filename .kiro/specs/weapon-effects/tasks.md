# Tasks: weapon effects v2

Kiro task 42 (all done):
- [x] 1. Read `docs/playtest_fixes.md` section 1c, `js/particles.js`, `js/particles_draw.js`, `scripts/test_particles.js`.
- [x] 2. Record the sha256 of `js/particles.js` before and after the insertion point, from the unedited file (temporary property, removed after use).
- [x] 3. Append the seven presets before `var PRESET_NAMES` (Req 1, 4 to 9).
- [x] 4. Append the properties to `scripts/test_particles.js`: byte-identical check (Req 1 to 3), one property per new preset (Req 4 to 6), stacks (Req 10, 11), palettes (Req 9), shape details (Req 7, 8).
- [x] 5. Run `node scripts/test_particles.js` and record the last line in `docs/implementation_report.md`.
- [x] 6. Write the wiring note for the main line in `docs/implementation_report.md`.

Handed to the main line (not part of task 42):
- Call the presets from `index.html` (trail names per weapon, impact per hit, slash index 0..2).
- Cut the old hit stack to the budget (the doc's list of changes to old presets).
- Add `squash` to the particle record and the drawer, then switch `bounce_ring` to a flat ellipse.
