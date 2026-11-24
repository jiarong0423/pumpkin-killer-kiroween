# UI polish: tasks

Done means the check in the last column passes in `node scripts/test_*.js` (and the browser check where noted). One writer for `index.html` at a time: the main line hands the lock over for the whole task and takes it back after verifying.

- [x] 1. `uiScale()` and `fs()`; route canvas texts and HP bars through them (R1.1, R1.2) | `test_ui_polish.js`
- [x] 2. `drawPlate(side)` with avatar, name, HP number, chips (R3.1 to R3.4) | `test_ui_polish.js`, browser look
- [x] 3. Touch target sizes and the lit help button under `(hover: none)` (R1.4); rotate hint check (R1.3) | CSS test in `test_ui_polish.js`
- [x] 4. Compact cards, responsive grid, failed-avatar `off` state (R2.1 to R2.5) | `test_ui_polish.js`, browser look at 900 x 700 and 393 x 852
- [x] 5. Wind arrow and number, weather effect line (R4.1, R4.3) | `test_ui_polish.js`
- [x] 6. Start button gate and background pose loading (R5) | browser network count
- [x] 7. English fit: apply the shorter texts, clamp floating texts with `measureText` (R6.2) | `test_i18n.js` and a width check
- [x] 8. `scripts/test_ui_polish.js` (R7) | runs in the full suite
