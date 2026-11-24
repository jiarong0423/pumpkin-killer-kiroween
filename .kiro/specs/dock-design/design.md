# Dock design: design

Full prose design, tables and the clearance arithmetic are in `docs/dock_design.md`. This file records the structure and the decisions.

## Files

| File | Role |
|---|---|
| `css/dock.css` | The stylesheet. Scoped under `#bottom-dock`. |
| `(not published)` | Standalone preview with the proposed markup and sample data. Loads `(not published)`. |
| `docs/dock_design.md` | Design document. |
| `docs/dock_asset_requests.md` | Twelve Colab image requests. |

## Markup structure

```
#bottom-dock  (.is-my-turn, .is-charging)
  i.dock-candle.left / .right                 decoration, tier L only
  .dock-hero
    .dock-portrait (.is-charging .is-shout .is-hit)  > .dock-portrait-art
    .dock-id
      .dock-name-row > .dock-name, .dock-hp-num
      .dock-hp (--hp, .is-mid, .is-low) > .dock-hp-fill, .dock-hp-inner
      .hero-selector > .hero-tab (.active) > .hero-glyph, .hero-name   x4
  i.dock-sep
  .skill-bar > .skill-btn x4 (+ hidden #skill-shield)
  i.dock-sep
  .dock-readouts
    .dock-plate.dock-angle > .dock-label, .dock-value
    .dock-plate.dock-power > .dock-power-head, .power-meter (--power) > .power-track, .power-fill
  i.dock-sep
  .dock-slots > .dock-slot.dock-ammo, .dock-slot.dock-special (.is-full)
  button.dock-lock (hidden unless needed)
  .dock-utility > .skill-btn.dock-reset
```

## Decisions

1. **Dock under the ground line, not floating.** The canvas ground is at 79.6 % of the height, so the strip below it is free. Floating pills (today) can drift over feet. A fixed plate in that strip guarantees a clean field; the clearance table in the design document gives the numbers per width.
2. **Three size tiers set by custom properties.** Media queries only change variables (`--dock-h`, `--tile-w`, ...) plus a few hide rules, so the markup is the same in all tiers. Alternative considered: `calc()` with one scale factor; rejected because 44 px minimums and 12 px text do not scale linearly.
3. **Keep `#skill-shield` hidden in the DOM.** `toggleShieldDefend`, `lockShield`, `cancelDefendMode` and `updateShieldButton` read and write it. Removing it would need a code change in a locked file. The cost is one hidden button.
4. **Lock button instead of a second press on the shield button.** The click menu enters defend placement but cannot confirm it. A single orange Lock, shown only during placement, is also the future 4 vs 4 round Lock, so it is not wasted work.
5. **Angle is read-only.** The pointer sets the angle (owner constraint). The mockup's arrows would duplicate it.
6. **Power meter shows the charge, not the result.** No preview, per the product rule "no preview or confirm step before a throw".
7. **Segmented meter by mask.** A repeating-gradient mask cuts a continuous bar into 20 segments; `clip-path` hides the unfilled part. One element pair, one custom property, no JavaScript layout. Partial segments appear at the cut unless the value is a multiple of 5; the game should round to 5.
8. **Cooldown sweep by `conic-gradient`.** One custom property, no extra markup.
9. **Cyan means "me", orange means "selected shot".** Prevents two selected states competing.
10. **Portrait doubles as the attacker cut-in.** Three state classes cover charge, release and hit. The portrait is hidden in tiers M and S to save width, where the active hero chip stands in.
11. **Images stay optional.** Every surface works with gradients. Colab images replace surfaces one by one through `background-image`.

## Risks

| Risk | Mitigation |
|---|---|
| Not rendered by the author | The preview page exists for the owner to judge; tasks 9 to 12 need eyes on a screen. |
| Tier L is 12 px from overflow with the Lock visible | Power meter is flexible and shrinks first. Task 11 checks it in a browser. |
| Tier M overflows with the Lock below about 1,000 px | Rare (Lock shows only in shield placement). Fix: hide the special slot while the Lock shows. |
| Below about 720 px wide the dock meets the characters' feet | Out of scope until Phase B; Phase B rebuilds the layout for landscape phones. |
| Emoji icons differ per OS | Asset request 3 replaces them. |
| `switchHero()` relies on `event.target` | `pointer-events: none` on chip children (in `dock.css`). Better: use `currentTarget` when `index.html` is next edited. |
