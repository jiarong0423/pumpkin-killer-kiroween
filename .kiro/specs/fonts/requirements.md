# Requirements: fonts

## Introduction

The game needs embedded fonts: a display face for titles and numbers, a body face for small text, both
able to show Traditional Chinese, all free under the SIL Open Font License 1.1 (owner, 2026-11-09:
"Include the fonts."). The choice and the licence reading are in `docs/ui_reskin_plan.md` (section b)
and `docs/fonts_report.md`. This spec covers the build script, the stylesheet, the tests and the
rules for the canvas. The main line downloads the source files and edits `index.html`.

Terms: "Source folder" is `(not published)`. "Font folder" is `assets/fonts/`. "On-screen text" is
every non-ASCII, non-emoji character found in the code and string tables listed in Requirement 2.

## Requirements

### Requirement 1: Build script

**User story:** As a maintainer, I want one command that turns the downloaded fonts into the files the
page loads, so the build is repeatable.

**Acceptance criteria**

1. WHEN `python3 scripts/build_fonts.py` runs and the Source folder holds the three font files and
   three licence files, THE SYSTEM SHALL write the files listed in `design.md` into the Font folder.
2. THE SYSTEM SHALL download nothing.
3. IF fontTools is not installed, THEN THE SYSTEM SHALL stop with a message that names the package and
   the install command.
4. IF the brotli package is missing, THEN THE SYSTEM SHALL write `.woff` files instead of `.woff2` and
   print that it did so.
5. IF an input file is missing, THEN THE SYSTEM SHALL list every missing path and exit with a non-zero
   code without writing partial output.
6. WHEN a face is built, THE SYSTEM SHALL pin Noto Sans TC to weights 400 and 700 and Noto Serif TC to
   weight 900 with `fontTools.varLib.instancer`.
7. THE SYSTEM SHALL copy `CinzelDecorative-Bold.ttf` byte for byte and SHALL NOT subset, instance or
   convert it.
8. THE SYSTEM SHALL give each modified Noto font the family name `PK Body` or `PK Display CJK`, keep the
   copyright and licence records in the font, and fail if a Reserved Font Name from the licence header
   is still in the family name records.
9. WHEN a built font lacks a requested character that its source font has, THE SYSTEM SHALL fail.
10. THE SYSTEM SHALL write `README.md` (names, sources, licences, counts, sizes, SHA-256) and
    `build_info.json` into the Font folder.

### Requirement 2: Computed character set

**User story:** As a maintainer, I want the characters in the font computed from the code, so no
on-screen character shows as a tofu box.

**Acceptance criteria**

1. THE SYSTEM SHALL scan `index.html`, `js/*.js`, `css/*.css`, `assets/i18n/*.json` (when present), the
   section d1 table of `docs/ui_reskin_plan.md` and `docs/fonts_sample.html`.
2. THE SYSTEM SHALL ignore comments in HTML, JavaScript and CSS.
3. THE SYSTEM SHALL NOT include emoji or emoji joiners in the character set.
4. THE SYSTEM SHALL add a base set: ASCII, Latin-1, U+2010-2027, U+2190-2193, U+25B6, U+25C0,
   U+3000-303F, U+FF01-FF5E.
5. THE SYSTEM SHALL add a margin of the first N characters of Big5 Level 1 from Python's `big5` codec,
   with N = 2000 unless `--margin` says otherwise (`all` means all of Level 1).
6. THE SYSTEM SHALL write the full set to `assets/fonts/charset.txt` and use that file as the subset
   text.

### Requirement 3: Stylesheet

**User story:** As a player on a slow connection, I want text to show at once and the fonts to arrive
later, so I never wait on a blank page.

**Acceptance criteria**

1. THE SYSTEM SHALL provide `css/fonts.css` with `@font-face` rules for `PK Display` (Cinzel Decorative
   Bold for U+0020-007E, Noto Serif TC 900 subset for the other ranges) and `PK Body` (400 and 700).
2. THE SYSTEM SHALL set `font-display: swap` on every rule.
3. THE SYSTEM SHALL keep the `unicode-range` of the two `PK Display` faces disjoint.
4. THE SYSTEM SHALL define `--font-display` and `--font-body`, each starting with its `PK` family and
   ending with a generic family, with system fonts between.
5. WHEN the class `pk-lite` is on the `html` element, THE SYSTEM SHALL define both variables without any
   `PK` family, so the browser requests no font file.
6. THE SYSTEM SHALL reference only local files under `(not published)`.

### Requirement 4: Canvas text

**User story:** As a player, I want canvas text in the same fonts as the page, from one place in the
code.

**Acceptance criteria**

1. THE SYSTEM SHALL document one constant per text role (HUD name, small label, number, big number,
   floating text, button, banner) and the rows of `index.html` and `js/particles_draw.js` that each role
   replaces.
2. THE SYSTEM SHALL document that the canvas family strings are read from the CSS variables.
3. WHEN the game starts, THE SYSTEM SHALL (per the documented snippet) call `document.fonts.load` with
   text that contains Chinese and Latin characters, and SHALL NOT wait longer than 2.5 s.
4. THE SYSTEM SHALL document an equal-cell way to draw digits for fonts without `tnum`.

### Requirement 5: Tests

**User story:** As a reviewer, I want a test that tells me whether the fonts are present and complete.

**Acceptance criteria**

1. THE SYSTEM SHALL provide `scripts/test_fonts.py`, run with `python3 -B scripts/test_fonts.py`.
2. WHEN fontTools is missing, THE SYSTEM SHALL fail a test with the install hint.
3. THE SYSTEM SHALL always test the character-set scan, the build helpers and the CSS, whether or not
   font files exist.
4. WHILE `assets/fonts/` holds no font file, THE SYSTEM SHALL skip the checks that need built fonts and
   print why.
5. WHILE `assets/fonts/` holds at least one font file, THE SYSTEM SHALL fail if: a file referenced by
   `css/fonts.css` is missing; a licence file is missing next to a font; the total size is 6 MB or more;
   a character from the on-screen text is not in the built charset; a character the source font has is
   not in the built font; Cinzel is not an exact copy; a Reserved Font Name is left in a modified font.

### Requirement 6: Documentation

**Acceptance criteria**

1. THE SYSTEM SHALL provide `docs/fonts_report.md` with the download and build commands, expected sizes,
   the canvas table, readability rules, strings, fallbacks and a browser checklist.
2. THE SYSTEM SHALL provide `docs/fonts_sample.html`, which uses `css/fonts.css` and shows every face,
   digit widths, outlined text, lite mode and canvas text.

### Requirement 7: Scope limits

**Acceptance criteria**

1. THE SYSTEM SHALL NOT edit `index.html`, `css/dock.css`, `js/*.js` or any image.
2. THE SYSTEM SHALL NOT add a dependency beyond fontTools (and brotli, optional).
3. THE SYSTEM SHALL NOT run git commands.
