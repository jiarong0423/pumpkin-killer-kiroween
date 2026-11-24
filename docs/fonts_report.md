# Fonts report (Kiro task 48)

Owner words (2026-11-09): "Include the fonts." "Let him (Kiro) be responsible."

What exists now: `scripts/build_fonts.py`, `scripts/test_fonts.py`, `css/fonts.css`, `docs/fonts_sample.html`, the spec in `.kiro/specs/fonts/`, and an empty `assets/fonts/README.md` (the build fills it). No font file is in the repo yet. `index.html`, `css/dock.css` and `js/*.js` were not touched.

## 1. Commands for the main line

All commands run from the repo root. The download is the only step that needs the network.

```
mkdir -p build/fonts_src

curl -fL -o "build/fonts_src/CinzelDecorative-Bold.ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/cinzeldecorative/CinzelDecorative-Bold.ttf"
curl -fL -o "build/fonts_src/OFL-CinzelDecorative.txt"  "https://raw.githubusercontent.com/google/fonts/main/ofl/cinzeldecorative/OFL.txt"

curl -fL -o "build/fonts_src/NotoSerifTC[wght].ttf"     "https://raw.githubusercontent.com/google/fonts/main/ofl/notoseriftc/NotoSerifTC%5Bwght%5D.ttf"
curl -fL -o "build/fonts_src/OFL-NotoSerifTC.txt"       "https://raw.githubusercontent.com/google/fonts/main/ofl/notoseriftc/OFL.txt"

curl -fL -o "build/fonts_src/NotoSansTC[wght].ttf"      "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanstc/NotoSansTC%5Bwght%5D.ttf"
curl -fL -o "build/fonts_src/OFL-NotoSansTC.txt"        "https://raw.githubusercontent.com/google/fonts/main/ofl/notosanstc/OFL.txt"

python3 -B scripts/build_fonts.py
python3 -B scripts/test_fonts.py
```

The quotes around names with `[wght]` are needed in zsh (the brackets are a glob). `-f` makes curl fail on a 404 instead of saving an error page. The URLs are the ones from `docs/ui_reskin_plan.md` section b3; I did not open them in this task.

Source sizes the plan read from the GitHub API on 2026-11-09 (they can change upstream): Cinzel Decorative Bold 62,300 bytes, Noto Serif TC variable 16,851,596 bytes, Noto Sans TC variable 11,941,968 bytes. If a download is far from these, stop and look at the file (a saved HTML error page is the usual cause).

Useful extra commands:

| Command | What it does |
|---|---|
| `python3 -B scripts/build_fonts.py --charset-only` | Writes only `assets/fonts/charset.txt`. Needs no fontTools and no font files. |
| `python3 -B scripts/build_fonts.py --margin all` | Margin = all 5,401 Big5 Level 1 characters instead of 2,000. Bigger files. |
| `python3 -B scripts/build_fonts.py --margin 0` | No margin, only the scanned text and the base set. Smallest files. |
| `python3 -B scripts/build_fonts.py --list-canvas-fonts` | Prints every `.font =` assignment with file and line (section 5). |

`(not published)` is not in `.gitignore` (I was not allowed to edit it). Add `(not published)` before the first commit, or the 28 MB of source fonts get committed.

Run the build again whenever on-screen text changes. `test_fonts.py` fails (not skips) when a character in the code is missing from `assets/fonts/charset.txt` and tells you to rebuild.

## 2. What the build does

1. Reads the three licenses and records their Reserved Font Names (`Cinzel`, `Source` for Noto Sans TC per the plan, none for Noto Serif TC per the plan; the script reads the real `OFL.txt` header and does not assume).
2. Computes the character set (section 3) and writes `assets/fonts/charset.txt`.
3. Copies `CinzelDecorative-Bold.ttf` byte for byte and compares SHA-256 of source and copy. No subset, no .woff2.
4. For each Noto face: subset the variable font first (fast), then pin the weight with `fontTools.varLib.instancer` (Sans 400 and 700, Serif 900), drop `STAT`, give the font our own name (`PK Body`, `PK Display CJK`) and weight class, save as `.woff2`. If `brotli` is missing it writes `.woff` and says so.
5. Opens each output and checks that every requested character that the source font has is in the output `cmap`. It also checks that no Reserved Font Name is left in the name records (IDs 1, 2, 4, 6, 16, 17).
6. Writes `assets/fonts/README.md` (names, sources, licenses, counts, sizes, SHA-256) and `assets/fonts/build_info.json` (the same data for tests, plus the characters each source font lacks, and which OpenType features each source has).

Layout features are kept as `*`, so `tnum`, `pnum` and `lnum` survive if the source has them. `build_info.json` has the answer per font under `features`.

### License decision (re-checked)

- Cinzel: the OFL defines a Modified Version to include a change of format. A subset or a .woff2 conversion is therefore a modification, and a modified file may not use the Reserved Font Name `Cinzel`. I did not find, and cannot prove from the `OFL.txt` alone, that a subset may keep the name. So Cinzel ships whole, as a `.ttf` (about 62 KB).
- Noto: the plan said no rename was needed. I changed that. Noto Sans TC lists the Reserved Font Name `Source` (plan b2). The family name does not contain it, but the cost of renaming is zero, so every modified Noto file gets our own name and the build checks the name records. Copyright (ID 0) and license (IDs 13, 14) records stay in the font.
- Each font's `OFL.txt` sits next to it in `assets/fonts/`.
- This is my reading of the license text, not legal advice.

## 3. Character set

Computed by `scripts/build_fonts.py`, in three parts:

| Part | Rule |
|---|---|
| On-screen text | Non-ASCII characters from `index.html` (text, attributes, inline script strings, inline CSS), `js/*.js`, `css/*.css`, `assets/i18n/*.json` (when it exists), the zh-TW/English table (section d1) of `docs/ui_reskin_plan.md`, and `docs/fonts_sample.html`. Comments are dropped. Emoji (U+1F000-1FAFF, U+2300-23FF, U+2600-27BF, U+2B00-2BFF, variation selectors, joiner) are dropped: the system draws them. |
| Base | ASCII, Latin-1, U+2010-2027, arrows U+2190-2193, the two triangles U+25B6 and U+25C0, CJK punctuation U+3000-303F, fullwidth ASCII U+FF01-FF5E. |
| Margin | The first 2,000 characters of Big5 Level 1, taken from Python's own `big5` codec. |

About the margin. fontTools has no Big5 table, and the fonts carry no frequency data, so the "common 2,000" cannot be derived exactly. Big5 Level 1 is the 5,401 "frequently used" characters, but its order is by stroke count, not by use. "First 2,000" therefore means the 2,000 simplest characters. That favours short characters and leaves out common many-stroke ones. The real protection against tofu boxes is `test_fonts.py`: whatever the margin, a character in the code that the built font lacks makes the test fail. Use `--margin all` if you want every Level 1 character.

Counts. Measured: none (my shell was refused for everything except the test run). From the rules: base 379, margin 2,000, so at least 2,379 characters; the test requires the total to be between 2,300 and 8,000, and it passes.

## 4. Expected sizes

Estimates only. Nothing was built. Basis: I assume 150 to 350 bytes per CJK glyph after woff2, and about 2,400 to 3,200 glyphs per file.

| File | Estimate |
|---|---|
| `CinzelDecorative-Bold.ttf` | 62,300 bytes (plan reading) |
| `pk-body-400.woff2` | 0.4 to 0.9 MB |
| `pk-body-700.woff2` | 0.4 to 0.9 MB |
| `pk-display-cjk-900.woff2` | 0.5 to 1.0 MB (heavier outlines) |
| Total | about 1.4 to 2.8 MB |
| With `--margin 0` | about 0.2 to 0.4 MB |

Two limits. `test_fonts.py` fails above 6 MB. The plan's own budget (task 32) was 600 KB, written for a few hundred characters; the 2,000-character margin breaks that budget on purpose. If 1.4 MB or more on first load is too much, build with a smaller `--margin` and rely on the test to catch gaps.

The first load fetches only the files the page uses: a face downloads when text on the page uses it (`unicode-range` and CSS stacks decide). The start screen uses body 400 and the display faces.

## 5. Canvas text (index.html)

`css/fonts.css` cannot reach canvas text. Every `ctx.font =` in the game is a fixed `sans-serif` string. Run `python3 -B scripts/build_fonts.py --list-canvas-fonts` to print the live list. The table below is from reading `index.html` on this checkout (I could not run that command; compare its output with this table, expected 24 rows in `index.html` and 1 in `js/particles_draw.js`).

| # | Line | Current value | What it draws | Proposed role |
|---|---|---|---|---|
| 1 | 1417 | `34px sans-serif` | airdrop item icon (emoji) | `emoji` |
| 2 | 1822 | `bold 18px sans-serif` | floating text popups | `floatText` |
| 3 | 1873 | `bold 11px sans-serif` | landing tag `軌跡 [R n]` | `smallLabel` |
| 4 | 1927 | `bold 12px sans-serif` | sky shield label | `smallLabel` |
| 5 | 1961 | `bold 12px sans-serif` | sky shield label (second draw path) | `smallLabel` |
| 6 | 2263 | `20px sans-serif` | stun stars (emoji) | `emoji` |
| 7 | 2337 | `bold 18px sans-serif` | pumpkin on the launcher (emoji) | `emoji` |
| 8 | 2343 | `bold 14px sans-serif` | fence health text | `smallLabel` |
| 9 | 2373 | `bold 22px sans-serif` | charge power percent | `numberBig` |
| 10 | 2505 | `34px sans-serif` | portrait fallback glyph (emoji) | `emoji` |
| 11 | 2508 | `bold 15px sans-serif` | HUD hero title | `hudName` |
| 12 | 2517 | `bold 12px sans-serif` | HP number in the bar | `number` |
| 13 | 2519 | `bold 13px sans-serif` | shield count `🛡 n/4` | `number` |
| 14 | 2532 | `bold 15px sans-serif` | HUD `第 N 回合 · 距離 D` | `hudName` |
| 15 | 2545 | `bold 14px sans-serif` | wind word `風 強風` | `smallLabel` |
| 16 | 2622 | `bold 20px sans-serif` | action menu button label | `button` |
| 17 | 2637 | `bold 20px sans-serif` | move arrows `◀ 後退` / `前進 ▶` | `button` |
| 18 | 2650 | `bold 16px sans-serif` | move needle hint | `smallLabel` |
| 19 | 2666 | `bold 26px sans-serif` | die result `▶ 3` | `numberBig` |
| 20 | 2673 | `bold 26px sans-serif` | turn timer `⏱ n` | `numberBig` |
| 21 | 2676 | `bold 18px sans-serif` | angle `角度 54°` | `smallLabel` |
| 22 | 2685 | `bold 34px sans-serif` | angle plate label (behind `SHOW_ANGLE_PLATES`) | `button` |
| 23 | 2692 | `bold 72px sans-serif` | game over title | `banner` |
| 24 | 2695 | `bold 26px sans-serif` | game over subtitle | `bannerSub` |
| 25 | `js/particles_draw.js` 150 | `'bold ' + size + 'px "Trebuchet MS", sans-serif'` | particle text (damage numbers) | `number`, family from a global |

DOM and CSS places that also set a family: `index.html` line 14 (`#start-screen`, `font-family: sans-serif`), line 36 (`body` system stack), line 166 (`#help-btn`, `font: bold 18px sans-serif`), `css/dock.css` lines 54 and 55 (`--serif`, `--sans`), line 95 (`font-family: var(--sans)`), line 276 (`font: 700 var(--fs-name) / 1 var(--serif)`).

### One place for the family

Define once, near the top of the game script (after `ctx` exists). The family strings come from the CSS variables, so `html.pk-lite` switches the canvas too.

```js
// Fonts: one place. Families come from css/fonts.css (--font-display, --font-body).
const _cssVars = getComputedStyle(document.documentElement);
const FAMILY_DISPLAY = _cssVars.getPropertyValue("--font-display").trim();
const FAMILY_BODY = _cssVars.getPropertyValue("--font-body").trim();
const FAMILY_EMOJI = '"Apple Color Emoji","Segoe UI Emoji","Noto Color Emoji",sans-serif';
const FONT = {
  hudName:    `700 20px ${FAMILY_BODY}`,      // rows 11, 14
  smallLabel: `700 17px ${FAMILY_BODY}`,      // rows 3, 4, 5, 8, 15, 18, 21
  button:     `700 20px ${FAMILY_BODY}`,      // rows 16, 17, 22
  number:     `700 17px ${FAMILY_DISPLAY}`,   // rows 12, 13, 25
  numberBig:  `700 32px ${FAMILY_DISPLAY}`,   // rows 9, 19, 20
  floatText:  `700 34px ${FAMILY_DISPLAY}`,   // row 2
  banner:     `700 72px ${FAMILY_DISPLAY}`,   // row 23
  bannerSub:  `700 26px ${FAMILY_BODY}`,      // row 24
  emoji: (px) => `${px}px ${FAMILY_EMOJI}`,   // rows 1, 6, 7, 10
};
```

Then each line becomes `ctx.font = FONT.smallLabel;` and so on. Emoji sizes stay as they are. The sizes in the table are proposals that follow `docs/ui_reskin_plan.md` (pop-ups 34 px display, timer 32 px display, nothing under 17 px). The main line should look at the sample page and the real screen before it fixes them. Rows 12 and 13 sit in an 18 px high HP bar today, so 17 px text does not fit there until the new `ui_hp_bar` lands; keep row 12 at its current size until then.

Row 13 and the others with emoji in the string (`🛡`, `⏱`, `🎃`, `💀`): the plan (rule 13) removes emoji from canvas text. Until then the emoji comes from the system font through the fallback stack, at the size of the surrounding text.

### Wait for the fonts before the first frame

A canvas does not trigger a web font download by itself, and `ctx.font` with a font that is not loaded yet draws the fallback for that frame. Put this before the first `requestAnimationFrame(loop)` (today `index.html` line 2731). The start screen is DOM and shows while this runs.

```js
// Wait for the web fonts, but never longer than 2.5 s (slow network: the fallback stack is fine).
async function loadFonts(timeoutMs = 2500) {
  if (!document.fonts || document.documentElement.classList.contains("pk-lite")) return;
  const SAMPLE = "第回合你的距離風0123456789ABCabc";   // Chinese and Latin: loads both display files
  const loads = Promise.all([
    document.fonts.load(`700 28px ${FAMILY_DISPLAY}`, SAMPLE),
    document.fonts.load(`400 17px ${FAMILY_BODY}`, SAMPLE),
    document.fonts.load(`700 17px ${FAMILY_BODY}`, SAMPLE),
  ]).catch(() => {});                                  // a failed load must not stop the game
  await Promise.race([loads, new Promise((r) => setTimeout(r, timeoutMs))]);
}
loadFonts().then(() => requestAnimationFrame(loop));
```

The second argument (`SAMPLE`) matters: without text the browser loads only the faces whose `unicode-range` covers a space.

### Lite switch (slow network)

Put this in `<head>` before the `<link>` to `fonts.css`:

```html
<script>
  (function () {
    var c = navigator.connection || {};
    var slow = c.saveData || /(^|-)2g$/.test(c.effectiveType || "");
    if (slow || /[?&]lite\b/.test(location.search)) document.documentElement.classList.add("pk-lite");
  })();
</script>
```

`html.pk-lite` removes our families from both stacks, so the browser requests no font file at all, and the canvas (which reads the same variables) uses system fonts too. Safari and Firefox do not implement `navigator.connection`, so they always get the full fonts unless the page is opened with `?lite`. Not tested.

## 6. Readability rules

| Rule | Value | Why |
|---|---|---|
| Smallest canvas text | 17 px | The 1920 px canvas is shown at most 1400 px wide, so 1 canvas px is 0.729 CSS px (plan finding 1). 17 px is about 12.4 CSS px. Today ten assignments are 11 to 16 px (rows 3, 4, 5, 8, 11, 12, 13, 14, 15, 18). |
| Smallest DOM text | 12 px | Same as the dock rule (`--fs-label`). Body copy 14 px or more. |
| Display font size | 22 px or more | Cinzel Decorative is an inscription face with swash capitals. Use it for titles and numbers. Do not set sentences in it, and do not use it below 22 px. |
| Weights | 400 and 700 only | Those are the files that exist. No `font-weight: 300/500/600/800`: the browser would fake them. |
| Outline | Over the scene, always: `lineJoin = "round"`, stroke first, fill second, stroke width about 0.2 x font size (min 3 px), colour `rgba(10,4,20,0.85)` | This is what the HUD already does (`index.html` 2509, `particles_draw.js` 154). In DOM use `.pk-outline` (3 px stroke, `paint-order: stroke fill`, 1.5 px visible). |
| Glow | `shadowBlur` only on big text (floating pop-ups, banner) | Blurred shadow on every label costs frame time. In calm mode drop it (below). |
| Text on plates | `#f6ecd8` on dark | Plan rule 16. The 4.5:1 contrast check is still open (no tool run). |
| Pop-up length | At most 8 Chinese or 14 Latin characters | Plan rule 12. Cinzel capitals are wide. |

### Fixed-width digits

Numbers such as `1111` and `8888` must not change the width of a plate while they count.

1. Check the font. `build_info.json` (key `features`) lists the GSUB features of each source. If `tnum` is there, `font-variant-numeric: tabular-nums` (class `.pk-num`) works in DOM text. For the canvas there is no `font-variant-numeric` in the 2D API on all browsers, so use step 3. I did not check whether any of the three fonts has `tnum`.
2. Cinzel Decorative is shipped unmodified, so we cannot add features to it.
3. Equal cells, works with any font. Measure the widest digit once after the fonts have loaded, then centre each digit in that width:

```js
let DIGIT_CELL = 0;
function measureDigitCell(font) {            // call once after loadFonts(), and again if the font changes
  ctx.save(); ctx.font = font;
  DIGIT_CELL = Math.max(...[..."0123456789"].map((d) => ctx.measureText(d).width));
  ctx.restore();
}
function drawDigits(text, x, y, align = "center") {   // text: digits only, e.g. "120"
  const w = DIGIT_CELL * text.length;
  const x0 = align === "center" ? x - w / 2 : align === "right" ? x - w : x;
  ctx.textAlign = "center";
  [...text].forEach((d, i) => { ctx.strokeText(d, x0 + DIGIT_CELL * (i + 0.5), y); ctx.fillText(d, x0 + DIGIT_CELL * (i + 0.5), y); });
}
```

   `docs/fonts_sample.html` section 7 shows this and prints the plain width of `1111` and `8888` next to the cell width. Call `measureDigitCell` once per font role that draws numbers (`FONT.number`, `FONT.numberBig`).
4. DOM text without `tnum`: wrap each digit in `<span style="display:inline-block;width:0.62em;text-align:center">`, or use the body font for numbers (section 4 of the sample page says whether it has fixed-width digits).

## 7. Strings (zh-TW and English)

The strings below are the contract from `docs/ui_reskin_plan.md` section d1 plus the strings that exist today. They are scanned into the character set (the d1 table directly). English appears in Cinzel (display) or Noto Sans (body). The owner has not read the wind words yet (plan, "Not verified").

| Key | zh-TW | English |
|---|---|---|
| `team.me` / `team.agent` | 我方 / 子代理 | You / Agents |
| `hud.round` | 第 {n} 回合 | Round {n} |
| `hud.gap` | 距離 {n} | Gap {n} |
| `hud.thinking` | 對手思考中 | Thinking |
| `wind.0` to `wind.5` | 無風 微風 和風 強風 烈風 狂風 | Calm Breeze Gentle Strong Gale Storm |
| `wind.tail` / `wind.head` | 順風 / 逆風 | Tailwind / Headwind |
| `turn.yours` | 你的回合 | Your turn |
| `end.win` / `end.lose` | 你贏了！ / 子代理獲勝 | You win! / Agents win |
| `end.restart` | 點一下畫面重新開始 | Click to play again |
| `menu.move` / `menu.attack` / `menu.defend` | 移動 / 攻擊 / 防禦 | Move / Attack / Defend |
| `fx.hit` / `fx.block` / `fx.fence` / `fx.miss` | 命中 / 攔截！ / 圍籬！ / 偏了 | Hit / Blocked! / Fence! / Miss |
| `fx.fence_down` | 圍籬倒了 | Fence down |
| `drop.coming` / `drop.got` | 物資來了 / 拿到物資 | Supply drop / Got supply |
| `help.title` | 玩法 | How to play |
| start screen today | 選一個角色（開局後不能換）/ 選一個戰場 / 開始戰鬥 | not translated yet |

`assets/i18n/zh-TW.json` and `en.json` do not exist yet (Kiro task 08 is only in `js/i18n.js`). The scan reads `assets/i18n/*.json` as soon as they appear, so those strings join the character set without a script change.

## 8. Fallbacks

| Situation | What the player sees | Mechanism |
|---|---|---|
| Fonts still loading | System fonts first, our fonts swap in when they arrive | `font-display: swap` on every face. The stacks name system fonts after `PK ...`. |
| Font file missing or 404 | System fonts, console error | `src` lists `.woff2` then `.woff`; if neither loads the stack continues. |
| Character not in the subset | That one character from the system font | Stack order. `test_fonts.py` fails on any such character that is in the code. |
| Slow network (2g, Save-Data, `?lite`) | System fonts only, no font download | `html.pk-lite` (section 5). The canvas waits at most 2.5 s for the fonts and starts anyway. |
| Calm mode | Same fonts. Only the glow is cheaper | Calm mode (`docs/ultimates_design.md`, section 1d) is a lighter effects budget. Fonts do not animate, so nothing about them needs to change except `shadowBlur` on text: drop it and keep the outline. Calm mode does not force lite mode, because its saving is frame time, and system fonts do not draw faster. |
| `file://` | Unknown | The plan did not check it either. Browsers can block fonts loaded from another folder on `file://` (Firefox does for folders outside the page's folder). Test on `http://localhost`, see section 9. |

## 9. What to check in the browser

1. Serve the repo: `python3 -m http.server 8000` (the owner starts it), then open `http://localhost:8000/docs/fonts_sample.html`.
2. Section 8 (Load status) shows `OK` for PK Display (Latin and Chinese) and PK Body 400 and 700. Any `NOT LOADED`: open DevTools, Network, filter `Font`.
3. Section 1: Latin and digits look like Cinzel Decorative capitals, Chinese looks like a heavy Ming serif. This is the taste check from the plan; the owner approves or asks for the alternates in plan b1.
4. Section 2: weights 400 and 700 differ clearly. 12 px and 14 px lines are readable on the real display.
5. Section 4: read the width differences. A default difference above 0.5 px means proportional digits. If `tabular-nums` still shows a difference, the font has no `tnum`: use equal cells (section 6).
6. Section 5: the outlined lines stay readable over the orange-to-teal gradient, the plain lines do not.
7. Section 6: the triangles, degree and multiplication signs come from PK Body; emoji come from the system.
8. Section 7: the canvas lines use the same fonts; the log shows the stacks, the plain widths and the cell width.
9. Click "切換 lite 模式": section 8 reports lite mode ON, no font request appears in the Network tab, the text uses system fonts.
10. Throttle to "Slow 3G" in DevTools and reload: text appears at once in system fonts and switches when the files arrive.
11. After wiring `index.html`: `document.fonts.check('700 28px "PK Display"', '你的回合')` returns `true` in the console, and a screenshot of `第 3 回合` and `Round 3` at 28 px goes to the owner (plan step 2 pass condition).

## 10. Plan versus real code (what I changed from `docs/ui_reskin_plan.md`)

| Plan | Real code or reason | What I did |
|---|---|---|
| Collect characters with a one-liner (`cat` the files into `python3`) | That one-liner includes comments and every non-ASCII character, emoji too | The script strips comments and drops emoji. |
| Four font files at most 600 KB | The 2,000-character margin (owner task 48) makes that impossible | Limit in the test is 6 MB (task 48). Estimate 1.4 to 2.8 MB. |
| Serif 900 face only for CJK ranges | The HUD string `第 N 回合 · 距離 D` has a middle dot (U+00B7). Cinzel may not have it | Serif face also covers Latin-1, U+2000-206F, arrows, shapes. Cinzel gets ASCII only (U+0020-007E). The two ranges do not overlap, and a test checks that. |
| No rename for Noto | Noto Sans TC lists the Reserved Font Name `Source` | Renamed anyway, and the build and test check the name records. |
| Canvas constants written out as strings | One place to switch, including lite mode | Families are read from the CSS variables. |
| `document.fonts.load` before the first frame | No timeout, no lite mode | Added a 2.5 s timeout and the lite check. |
| "no `ctx.font` below 17 px" (plan step 3) | Ten assignments are below 17 px today (section 6) | Listed them in section 5. Not changed. |
| Plan b5 said link `fonts.css` "before `dock.css`" | `index.html` line 7 links `dock.css` first | Main line adds the `<link>` above line 7. |

## 11. What I could not verify

- Nothing was downloaded or built, so the sizes, the `tnum` question, the real glyph coverage, the Cinzel punctuation coverage and the look of the fonts are all unchecked.
- `python3 -B scripts/build_fonts.py` itself has not been run. Its character-set functions are covered by `test_fonts.py` (which passes); the fontTools calls (`subset`, `instancer`, name edits, `save`) have never run.
- The shell was refused for every command except `python3 -B scripts/test_fonts.py`. So the dependency check (`import fontTools`, `import brotli`) was done only through the test: `test_fonttools_importable` passed, and `test_brotli_note` was not skipped, which means both packages are installed here.
- The canvas table in section 5 comes from text search and reading, not from running `--list-canvas-fonts`. The search tool cut off long result lists, so I repeated it by font size; a missed assignment is possible.
- Whether `file://` loads the fonts.
- The OFL FAQ passage on subsetting was not read (the plan also did not); the Cinzel decision is the conservative one.
