# Tasks: fonts

Done by Kiro (task 48):

- [x] 1. Write `scripts/build_fonts.py`: character-set scan, Big5 margin, subset, weight pinning, rename,
  Cinzel copy, self-verification, README and `build_info.json`.
- [x] 2. Write `css/fonts.css`: four `@font-face` rules, `font-display: swap`, disjoint `unicode-range`,
  `--font-display` and `--font-body`, `html.pk-lite`, small helper classes.
- [x] 3. Write `scripts/test_fonts.py`: tests that run without fonts, tests that skip until fonts are built
  and fail afterwards.
- [x] 4. Write `docs/fonts_sample.html`.
- [x] 5. Write `docs/fonts_report.md` (commands, sizes, canvas table and snippets, readability rules,
  strings, fallbacks, browser checklist).
- [x] 6. Write this spec.
- [x] 7. Create the empty `assets/fonts/README.md`.
- [x] 8. Run `python3 -B scripts/test_fonts.py` (no font files yet: font checks skip).

For the main line:

- [ ] 9. Download the six files into `(not published)` with the commands in `docs/fonts_report.md`.
- [ ] 10. Add `(not published)` to `.gitignore`.
- [ ] 11. Run `python3 -B scripts/build_fonts.py`. Read its output and `assets/fonts/README.md`. If a step
  fails, report the exact message; the fontTools calls have never run.
- [ ] 12. Run `python3 -B scripts/test_fonts.py`. Expect no skips except the brotli note. Fix anything
  that fails: a missing character means the font lacks it (see `build_info.json`) or the text changed
  after the build.
- [ ] 13. Open `docs/fonts_sample.html` over `http://localhost` and go through the checklist in
  `docs/fonts_report.md`, section 9. Send the owner a screenshot of sections 1, 2 and 5.
- [ ] 14. Check the tabular-figure answer in `assets/fonts/build_info.json` (`features`). Decide between
  `tnum` and equal cells.
- [ ] 15. In `index.html`: add the `<link>` to `css/fonts.css` above the `dock.css` link, add the lite
  script to `<head>`, replace the `ctx.font` strings with the `FONT` roles, add `loadFonts()` before the
  first `requestAnimationFrame(loop)`. Replace `--serif` and `--sans` in `css/dock.css` with the new
  variables. Replace the family in `js/particles_draw.js` line 150.
- [ ] 16. Raise the canvas text that is under 17 px, together with the HUD redesign (plan step 3). Keep
  the HP number at its current size until the new HP bar exists.
- [ ] 17. Owner approves the look (Cinzel Decorative with Noto Serif TC 900). If not, use the alternates
  in plan b1 (plain Cinzel, or Chiron Sung HK) and run the build again.
- [ ] 18. Run all test scripts listed in `.kiro/steering/tech.md`, plus `scripts/test_fonts.py`.
