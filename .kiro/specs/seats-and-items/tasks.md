# Seats and items: tasks

Starts after `ui-polish` is verified (one writer for `index.html`).

- [x] 1. `seats` state, `activeSide()`, `unitOf(side)`; replace `turn === "player"` and `"ai"` branches in input, dock and timer by the active side (R1.2) | `test_seats_items.js`
- [x] 2. Start screen seat rows and the validity rule (R1.1) | `test_seats_items.js`
- [ ] 3. Curtain between human turns, mirrored aim for the right side (R1.3, R1.4) | browser check with two human seats
- [x] 4. Result texts for two human seats (R1.5) | `test_i18n.js`
- [x] 5. Per-side skill charges, AI use rules, supply item fix (R2.1 to R2.3) | `test_seats_items.js`
- [ ] 6. `scripts/test_seats_items.js` (R3) | full suite
