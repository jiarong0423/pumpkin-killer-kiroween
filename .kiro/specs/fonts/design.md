# Design: fonts

## Overview

Three open fonts, one build script, one stylesheet. The page asks for `PK Display` and `PK Body`
through two CSS variables. Canvas text reads the same variables. Everything has a system fallback.

## Fonts

| Role | Latin and digits | Traditional Chinese | File |
|---|---|---|---|
| Display | Cinzel Decorative Bold (unmodified) | Noto Serif TC, wght 900, subset | `CinzelDecorative-Bold.ttf`, `pk-display-cjk-900.woff2` |
| Body | Noto Sans TC (its own Latin) | Noto Sans TC, wght 400 and 700, subset | `pk-body-400.woff2`, `pk-body-700.woff2` |

All SIL OFL 1.1. Source: `google/fonts` on GitHub (URLs in `docs/fonts_report.md`).

## Files

```
build/fonts_src/                       input, downloaded by the main line, not committed
  CinzelDecorative-Bold.ttf   OFL-CinzelDecorative.txt
  NotoSerifTC[wght].ttf       OFL-NotoSerifTC.txt
  NotoSansTC[wght].ttf        OFL-NotoSansTC.txt

assets/fonts/                          output of scripts/build_fonts.py
  CinzelDecorative-Bold.ttf            exact copy
  pk-display-cjk-900.woff2             (.woff if brotli is missing)
  pk-body-400.woff2
  pk-body-700.woff2
  OFL-CinzelDecorative.txt  OFL-NotoSerifTC.txt  OFL-NotoSansTC.txt
  charset.txt                          the subset text, one block of characters
  build_info.json                      counts, hashes, characters missing from the sources, GSUB features
  README.md                            names, sources, licences, sizes
```

## Build pipeline

```
scan sources --> character set --> charset.txt
                                       |
 NotoXxxTC[wght].ttf --subset--> --instancer (pin wght)--> drop STAT --> rename --> woff2
 Cinzel ----------------------- copy, compare SHA-256 ----------------------------> ttf
                                       |
 verify: output cmap has every requested character the source has; no Reserved Font Name left
```

Subsetting runs before pinning the weight. The result is the same as the other order and the
variable-font work is much smaller.

Why Cinzel is copied: the OFL calls a change of format a modification, and a modified file may not use
the Reserved Font Name `Cinzel`. A subset could be renamed, but the task said to keep Cinzel unmodified,
and the file is about 62 KB.

Why the Noto files are renamed: Noto Sans TC lists the Reserved Font Name `Source`. Renaming costs
nothing and makes the question moot. Copyright and licence records stay.

## Character set

`compute_charset()` returns the on-screen set, the base set, the margin and their union. The scanner
removes comments with a small tokenizer (strings and template literals are kept whole, `//` and `/* */`
outside strings are dropped), reads HTML text and attributes, inline `<script>` and `<style>`
separately, reads JSON string values, and takes the table rows under the heading `### d1` of the
re-skin plan. Emoji ranges are removed: U+1F000-1FAFF, U+2300-23FF, U+2600-27BF, U+2B00-2BFF,
variation selectors, joiner, keycap, tags.

The margin is a stated approximation (see `docs/fonts_report.md`, section 3): Big5 Level 1 comes in
stroke-count order, so "the first N" is the N simplest characters.

## Stylesheet (`css/fonts.css`)

| Face | Family | Weight | unicode-range | File |
|---|---|---|---|---|
| 1 | PK Display | 700 | U+00A0-00FF, U+2000-206F, U+2190-21FF, U+25A0-25FF, U+2E80-9FFF, U+F900-FAFF, U+FF00-FFEF | `pk-display-cjk-900` |
| 2 | PK Display | 700 | U+0020-007E | `CinzelDecorative-Bold.ttf` |
| 3 | PK Body | 400 | all | `pk-body-400` |
| 4 | PK Body | 700 | all | `pk-body-700` |

Faces 1 and 2 never overlap, so the browser never has to pick between two matching faces. Every `src`
lists `.woff2` then `.woff` (Cinzel: `.ttf` only). `font-display: swap` everywhere.

Variables: `--font-display` and `--font-body`. `html.pk-lite` redefines both without `PK` names. A face
downloads only when an element uses it, so lite mode means zero font requests.

## Canvas

`FONT` object with one entry per role, families from `getComputedStyle(document.documentElement)`,
`loadFonts()` with a 2.5 s race, the digit-cell helper for numbers. Full code in
`docs/fonts_report.md`, section 5. The main line wires it; this spec does not edit `index.html`.

## Tests (`scripts/test_fonts.py`)

| Group | Needs fonts | Needs fontTools |
|---|---|---|
| Environment (fontTools import, brotli note) | no | the test itself |
| Scan helpers and charset (comments, emoji, Big5, canvas audit) | no | no |
| CSS (faces, swap, local paths, ranges, stacks, lite) | no | no |
| Docs exist | no | no |
| Built files (files exist, licences, size, charset current, Cinzel exact) | yes (skips otherwise) | no |
| Built contents (cmap coverage, static, renamed, no Reserved Font Name) | yes (skips otherwise) | yes |

"Built" means at least one `.woff2`, `.woff` or `.ttf` is in `assets/fonts/`.

## Risks

| Risk | Handling |
|---|---|
| The margin rule is not frequency based | The test fails on any on-screen character that is missing, whatever the margin |
| Total size 1.4 to 2.8 MB (estimate) | `--margin` option, lite mode, 6 MB test limit |
| fontTools calls never ran in this task | First real build is the check; `build_fonts.py` verifies its own output |
| Cinzel may lack some ASCII punctuation | `build_info.json` lists them; the browser falls back to the next family for that glyph |
| `tnum` may be missing | Equal-cell drawing works for any font |
