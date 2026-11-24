# Kiro task 08 — bilingual (zh-TW / en) mapping for the whole game UI

Context: Pumpkin Killer, plain-JS canvas game in `index.html`. All visible text is hard-coded (mostly Traditional Chinese, some English).
The owner wants a Chinese <-> English mapped version: every visible string comes from a dictionary, with a language switch.
You OWN `index.html` for this task (nobody else edits it meanwhile). Read `docs/game_mode.md` and `docs/ROLES.md` first.

## Do exactly this
1. Create `assets/i18n/zh-TW.json` and `assets/i18n/en.json`: flat key -> string maps with IDENTICAL key sets. Keys are stable ids such as
   `hud.round`, `skill.shield.tip`, `float.timeout`, `defend.hint`, `move.chooseDir`, `gameover.win`. Parameters use `{name}` placeholders and must be the same set in both languages.
2. Create `js/i18n.js` (DOM-free core, works in Node via `module.exports` and in the browser as global `I18N`): `t(key, params)` (falls back to zh-TW, then to the key itself),
   `setLang(code)`, `getLang()`, `detect()` (from `navigator.language`, default zh-TW), persistence through `localStorage` wrapped in try/catch (private mode must not crash),
   and `loadDictionaries()` that works with `fetch` in the browser (relative URLs `(not published)`) and `fs` in Node.
3. Refactor `index.html`: replace EVERY user-visible string with `t()` (HTML via `data-i18n="key"` / `data-i18n-title="key"` attributes updated by a `applyLang()` function; canvas texts, floating texts, HUD, banners, tutorial box, game over, angle label, dice results, shield pips text, tooltips/titles, the `<title>`). Keep the game logic and layout untouched.
   Hero names and skill names are part of the dictionary too. The language switch is a small button (zh/EN) in the existing control area; it re-renders immediately and remembers the choice.
4. Create `scripts/test_i18n.js` (Node `assert` only): both dictionaries have exactly the same keys; every `{param}` set matches per key; no empty strings; `t()` fallback order works;
   a scan of `index.html` finds NO remaining CJK characters outside comments and the dictionary-loading code (print the offending lines when it fails); `setLang` survives a throwing `localStorage`.
5. Spec in `.kiro/specs/i18n/` (`requirements.md` EARS, `design.md`, `tasks.md`).
6. Write natural English, not word-for-word: game terms: Pumpkin Guard (南瓜盾衛), floating shield, fence, wind, power, angle, Lock/Confirm, Move, Defend, Ultimate.
7. Do NOT touch `(not published)`, `scripts/mcp_game_server.py`, or generate images. No git commands. The reviewer will run `node scripts/test_i18n.js`, the Python engine test and play it in a browser.
8. Finish with a 6-line summary: files, number of keys, how many strings were canvas vs DOM, anything you could not do or are unsure about.
