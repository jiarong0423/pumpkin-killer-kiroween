---
inclusion: always
---
# UI settings

- The page has one settings sheet opened only from `#settings-btn`.
- Effects sound, music volume, reduced motion, language, and the right built-in AI level are saved through guarded `localStorage`; blocked storage keeps working defaults.
- On a no-hover device, each settings control has a 44 px target. In landscape, the sheet must remain inside the visible area and not cover the countdown board or dock.
- Reduced motion removes screen shake and hit flash and limits particles to small bursts. It never changes input, combat, physics, timing, or AI multipliers.
- Visible settings text and accessibility labels use literal keys in both `assets/i18n` dictionaries. English contains no CJK except the established language-switch keys.
- Run `node scripts/test_ui_settings.js`, `node scripts/test_phone_layout.js`, `node scripts/test_i18n.js`, and `node scripts/test_layout_property.mjs` after a settings change.
