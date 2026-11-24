# UI polish: requirements

Scope: `index.html` (screens, canvas HUD, controls), `css/*.css`, `assets/i18n/*.json`. Terms: **card** is `.pick-card`; **plate** is the top HUD name plate drawn on the canvas; **display scale** is `canvas.getBoundingClientRect().width / 1920`; **screen px** is a CSS pixel after that scale.

## R1 Legibility at any size
1. Canvas texts (turn line, weather line, round and distance line, floating texts, result panel) shall render at least 11 screen px: the drawn font size is `max(designed size, 11 / display scale)`.
2. The HP bar above a unit shall be at least 6 screen px high and 40 screen px wide at the smallest supported window (352 px wide).
3. In portrait on a screen narrower than 900 px the rotate hint (`#rotate-hint`) shall cover the game.
4. Under `(hover: none)` every control in `#top-controls` shall be at least 44 x 44 CSS px, and the help button shall be visible without hovering.

## R2 Hero selection screen
1. Eight cards, four per row at 900 px and wider, two per row under 600 px.
2. Each card shall show the avatar image `(not published)`, the name, a role badge, an HP bar and an ATK bar with numbers equal to `HERO_PROFILES[id].hp` and `.dmg`, and the status chips of the hero. The long description is the tooltip (`title`).
3. The selected card shall show a gold ring, a check mark and a raised shadow; hovering raises any card by 3 px.
4. At 900 x 700 the start button and the scene row shall be visible without scrolling the page (compact card height at most 200 px).
5. An avatar that fails to load shall not leave an emoji: the card is marked `off` and cannot be selected.

## R3 HUD name plate with head and status
1. Each top plate shall show a round avatar (36 screen px at the smallest window), the hero name, and the HP number next to a bar.
2. Under the bar the plate shall show a chip per active status with the remaining turns (bleed, poison, burn, frost, slow, stun), in the colours of the selection chips.
3. No status object shall turn above a head except the stun stars.
4. The plate of the side whose turn it is shall glow in the accent colour; the other plate is dimmed but readable (contrast at least 4.5:1).

## R4 Wind and weather
1. (Changed by the owner 2026-11-16: no number, no arrow chip.) The wind ghost is bound to the wind direction: it is mirrored to face the way the wind blows (positive wind blows toward the right side), the wisps flow the same way, and their speed and count show the strength.
2. When the weather changes a message of at least 18 screen px shall show for 2.5 s (the text keys `weather.notice.*`).
3. The HUD weather line shall name the effect (attacks -10 percent, movement halved, fog: atmosphere only).

## R5 Start-up cost
1. The start button shall become active when the picked hero, the picked scene background and the UI assets are loaded; the other heroes' pose images shall load afterwards.
2. The first screen shall not wait for more than 20 requests.

## R6 Texts
1. Every string on screen comes from the language files; both language files keep the same key set (`scripts/test_i18n.js`).
2. English texts shall fit their boxes (budgets in `docs/i18n_mapping_table_20261116.md`).

## R7 Evidence
1. `scripts/test_ui_polish.js` shall check R1.1, R1.2, R2.2, R2.4 and R3.2 by reading `index.html` and, where it needs a DOM, by a minimal fake DOM, and run in `node scripts/test_*.js`.
