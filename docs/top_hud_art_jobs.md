# Top HUD art jobs (reference: (not published); owner 2026-11-09: refined, no HP bar, real Colab art)

Layout from the mockup, one dark ornate banner across the top:
- LEFT: game title logo area, then a "PLAYERS" strip with one diamond per living unit of the player's side (cyan).
- CENTRE: "round N" with the turn timer.
- Then the wind: an arrow that shows the direction plus the strength number.
- RIGHT: an "AGENTS" strip with one diamond per living unit of the opponent (violet).
- NO health bars in the banner. HP stays above each unit (small number and bar, as in the mockup) and in the bottom hero block.

Pictures to draw on Colab (tier TOP1, style docs/art_style_guide.md, flat magenta background for keying):
1. ui_top_banner_left  — the left third of a dark gothic metal banner: black iron with fine filigree, small bat-wing ornaments, thin cyan edge glow, empty dark panel in the middle for text. Wide horizontal.
2. ui_top_banner_centre — the centre piece: a notched dark plate with a pumpkin-lantern ornament on top, empty panel for "round N" and the timer, thin gold edge.
3. ui_top_banner_right — the right third, mirrored feel, thin violet edge glow.
4. ui_diamond_cyan_on / ui_diamond_cyan_off — a lit and a dark cyan diamond gem in a small metal setting.
5. ui_diamond_violet_on / ui_diamond_violet_off — the same in violet.
6. ui_wind_plate — a small dark plate with a socket for the wind arrow and the number.
All are separate files so the code can stretch the banner pieces and tile the diamonds.

## Job: blue twin of the purple floating coffin (owner 2026-11-10: "the purple one has more quality")
Same picture as assets/env/platform_coffin_purple.png (three-quarter view, riveted metal corner plates, dark planks, glowing runes along the lid, ghost-flame drips below), but the glow, runes and drips are CYAN instead of violet. Same camera, same size, same plank texture, transparent or flat magenta background for keying. Until it exists, index.html tints the purple one with hue-rotate(-95deg) on the left side.
