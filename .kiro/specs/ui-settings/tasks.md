# UI settings tasks

- [x] 1. Inventory current controls and identify scoped settings | `node scripts/test_i18n.js`, `node scripts/test_phone_layout.js`
- [x] 2. Add the short EARS requirements and implementation design | review against `docs/ui_settings_inventory_20261116.md`
- [x] 3. Add the sheet, guarded preference helpers, retained audio/motion/language/AI settings, and i18n keys | `node scripts/test_ui_settings.js`, `node scripts/test_i18n.js`
- [x] 4. Add static settings and seeded layout-property checks | `node scripts/test_layout_property.mjs`, `node scripts/measure_phone_layout.mjs`
- [ ] 5. Add the steering, save hook, and read-only verifier configuration | inspect JSON and run its declared checks
- [ ] 6. Run the full JavaScript suite and socket-free Python suite | `node scripts/test_*.js`, selected `python3 -B scripts/test_*.py`
