# Design: Bilingual UI (zh-TW / en)

## Files

| File | Role |
|---|---|
| `assets/i18n/zh-TW.json`, `assets/i18n/en.json` | Flat key -> string maps, identical key sets |
| `js/i18n.js` | DOM-free core. Global `I18N` in the browser, `module.exports` in Node |
| `index.html` | Calls `t()`; `applyLang()` updates DOM text; language button |
| `scripts/test_i18n.js` | Node `assert` tests |

## Core API (`js/i18n.js`)

- `t(key, params)`: current language, then zh-TW, then the key. Replaces
  `{name}` with `params.name`; unknown placeholders stay as written.
- `setLang(code)`: accepts `en*` and `zh*` (all `zh*` map to the zh-TW
  dictionary). Returns `false` for unknown codes. Saves to `localStorage`.
- `getLang()`, `detect(nav?)` (`nav` is injectable for tests), `init()`
  (saved choice, else `detect()`; does not write storage).
- `loadDictionaries()`: `fetch("assets/i18n/<code>.json")` in a page,
  `fs.readFileSync` in Node. Returns a promise.
- `setDictionary(code, map)`: used by tests.
- Storage access is wrapped: reading the `localStorage` property, `getItem`
  and `setItem` each sit inside `try/catch`.

## Key naming

`area.thing[.detail]`, letters and digits only. Areas: `title`, `pill`
(tutorial box), `skill`, `hero`, `move`, `reset`, `lang`, `float` (floating
texts), `shield`, `defend`, `traj`, `unit`, `fence`, `hud`, `gameover`,
`common`, `positions`.

Whole sentences are keys. Words that change with state (forward/back, on/off,
whose turn) are their own keys passed as parameters, so each language controls
its own word order.

## index.html

- `const t = (k, p) => I18N.t(k, p)`. The local variable `t` in
  `drawAirborneShield` was renamed `tm` to avoid shadowing.
- DOM: `data-i18n` (textContent), `data-i18n-html` (innerHTML, for the tutorial
  box which has bold parts) and `data-i18n-title` (tooltip).
  `applyLang()` sets `<html lang>`, `document.title`, all three attribute
  kinds and calls `updateShieldButton()` (its tooltip depends on the selected
  hero).
- Canvas and floating texts call `t()` at draw or creation time. Canvas text is
  redrawn every frame, so a language switch shows at once. Floating texts that
  are already on screen keep the language they were created in until they fade
  (about 1.5 s).
- Hero tabs are `emoji + <span data-i18n>`. `switchHero(key, btn)` now receives
  the button instead of reading the global `event.target`, which would have
  hit the inner span.
- Start-up: `loadDictionaries()` then `init()` then `applyLang()`. A load
  failure is logged and `applyLang()` still runs.
- Language button in the right-hand control group: shows the other language
  (`EN` while in zh-TW, `中文` while in English).

## Decisions

- zh-TW is the fallback language because it is the authoring language.
- English strings are written, not translated word for word.
- The knight had two Chinese names ("南瓜盾衛" on the tab, "南瓜重裝盾衛" in a
  floating text). Both now use `hero.knight.name`.
- The page must be served over http (`fetch` does not read local files in
  Chrome). The project already runs on `http://localhost:8080`.

## Test plan (`scripts/test_i18n.js`)

Same keys, same placeholders, no empty values, key format, `t()` fallback
order, `detect()`, Node loading, throwing/missing `localStorage`, CJK scan of
`index.html` with comments removed, every key referenced in `index.html`
exists and every dictionary key is referenced.
