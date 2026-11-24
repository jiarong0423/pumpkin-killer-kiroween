# Tasks: Bilingual UI (zh-TW / en)

- [x] 1. Write `assets/i18n/zh-TW.json` from the existing strings (req 1)
- [x] 2. Write `assets/i18n/en.json` with the same keys and placeholders (req 1, 4.3)
- [x] 3. Write `js/i18n.js`: `t`, `setLang`, `getLang`, `detect`, `init`,
      `loadDictionaries`, safe storage (req 2, 3, 5)
- [x] 4. Refactor `index.html` HTML: `data-i18n`, `data-i18n-html`,
      `data-i18n-title`, title, tutorial box, skill buttons, hero tabs (req 4)
- [x] 5. Refactor `index.html` script: floating texts, HUD, banners, angle
      label, dice result, shield labels, fence label, unit labels (req 4)
- [x] 6. Add `applyLang()`, the language button and start-up loading (req 3, 5)
- [x] 7. Write `scripts/test_i18n.js` (req 1, 2, 3.4, 4.1)
- [ ] 8. Run `node scripts/test_i18n.js` and the Python engine test
      (not run by the author: no shell access in that session)
- [ ] 9. Play in a browser over http: switch language mid-round, reload,
      check that the choice persists and no Chinese remains in English mode
- [ ] 10. Native-speaker review of both dictionaries
