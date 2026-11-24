# Dock design: tasks

Done means the file exists and was written against the requirement. Items marked "needs eyes" cannot be checked without a browser.

## Design files (this task)

- [x] 1. Read the mockup, `game_mode.md`, `ROLES.md` and the dock markup and CSS of `index.html` (R1, R2)
- [x] 2. Write `docs/dock_design.md`: mockup inventory, current controls table, layouts for tiers L and S, states, visual language (R1 to R8)
- [x] 3. Write `css/dock.css` with tokens, frame, hero cluster, shot buttons, readouts, slots, Lock, utility, motion (R3 to R9)
- [x] 4. Add the tier M and tier S `@media` blocks, including `@media (max-width: 900px)` (R3.3, R3.4)
- [x] 5. Write `(not published)` with sample data and a few lines of state-toggle script (R9.6)
- [x] 6. Write `docs/dock_asset_requests.md` with 12 items (R10)
- [x] 7. Write this spec

## Checks that need a browser (owner or main line)

- [ ] 8. Open `(not published)` at 1400x787: the dock sits below the dashed ground line, nothing covers the sample units (R3.1, R3.5) needs eyes
- [ ] 9. Resize to 1200, 1000, 900, 800 px: tiers switch, no horizontal overflow, clear gap at least 7 px at 901 px (R3.1 to R3.4) needs eyes
- [ ] 10. Check the 800 px iframe in the preview, with and without the Lock (R3.4) needs eyes
- [ ] 11. Check the Lock fits at 1201 px (tier L tight case) (R3.2) needs eyes
- [ ] 12. Toggle every state button in the preview: hover, pressed, disabled, cooldown, ready, focus look distinct (R5.1) needs eyes
- [ ] 13. Check text contrast with a tool on the dock text colours (R4.4)
- [ ] 14. Confirm no element in the dock is below 44x44 px using the browser inspector (R4.1)
- [ ] 15. Open with `prefers-reduced-motion` on: nothing animates (R8.3)
- [ ] 16. Owner reviews the look and picks changes (colour, glow strength, tile shape)

## Integration (separate task, needs the `index.html` lock)

- [ ] 17. Link `css/dock.css` after the inline `<style>`
- [ ] 18. Replace the dock markup with the block from the preview; keep `#skill-shield` and `#badge-shield` with `dock-hidden`
- [ ] 19. Re-add `onclick` for the four hero chips and the four shot buttons
- [ ] 20. Delete the old `.skill-bar`, `.skill-btn`, `.hero-selector`, `.hero-tab` rules and the inline styles from `index.html`
- [ ] 21. Add `updateDock()` called each frame: `--hp`, HP text, `.is-mid` / `.is-low`, angle text, `--power` rounded to 5, `.is-charging`, `.is-my-turn`, badge numbers, `.locked`, `.ready`, `.cooldown` (R6)
- [ ] 22. Set `lockBtn.hidden = !defendMode`, and `lockBtn.onclick = toggleShieldDefend` (R2.3, R2.4)
- [ ] 23. Set the portrait state classes from the throw animation: `.is-charging` on press, `.is-shout` on release, `.is-hit` on damage (R7)
- [ ] 24. Change `switchHero()` to use `currentTarget` or a lookup by `data-hero` (R9.5)
- [ ] 25. Run the existing test scripts and play a full round with each class; check that no console error mentions the dock

## Art (after Colab)

- [ ] 26. Generate asset requests 1 to 3 on Colab, chroma-key, review on the real dock
- [ ] 27. Replace CSS surfaces with the images one request at a time; keep the CSS as fallback
- [ ] 28. Generate requests 4 and 5 (portraits and cut-in faces); set `--portrait-img` per class
