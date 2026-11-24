---
inclusion: always
---
# Aesthetics steering (owner 2026-11-16: "the point is to get the aesthetics right: the head avatar, the status and the selection")

> *Historical snapshot (2026-11-16): the final submission targets the Kiroween **Resurrection** category while keeping every readability and layout rule below.*

The contest category is the Costume Contest, so the first ten seconds and the selection screen decide the score. These rules bind every UI task; the spec `.kiro/specs/ui-polish/` turns them into testable requirements.

1. One world: deep blue-violet night, pumpkin orange for what is selectable or selected, ghost cyan for information, a warm gold for the selected state. Never add a fourth accent colour.
2. Every hero is introduced the same way: a square head avatar (`(not published)`, never an emoji placeholder, never a cropped or partly missing picture), the name, a role badge (tank, glass cannon, balanced, control), HP and ATK bars read from `HERO_PROFILES`, and at most four status chips. Long text lives in the tooltip.
3. Nothing important is smaller than 11 screen pixels on a phone. Canvas text and bars scale with the display scale; HP bars are at least 6 screen pixels high; touch targets are at least 44 px under `(hover: none)`.
4. Status is shown on the HUD name plate as chips with the remaining turns (bleed, poison, burn, frost, slow, stun), not as objects above the head (owner rule 2026-11-10: only the stun stars turn above a head).
5. A phone in portrait shows the rotate hint; the game is played in landscape.
6. Whatever the screen says must match the code: numbers on cards come from `HERO_PROFILES`, texts from `assets/i18n/*.json` in both languages, no hard-coded strings.
7. Incomplete pictures are never shipped. If a picture is missing the hero is not selectable until it exists.
8. Every UI task ends with a check by script (DOM measurement, `scripts/test_*.js`), not only a screenshot.
