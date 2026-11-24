# Kiro task 143 — turn the i18n wiring plan into a checked apply script (work block B09)

`docs/i18n_wiring_plan_20261115.md` lists 57 edit groups for `index.html`. The main line will apply them with a script that you write; you do NOT edit `index.html` yourself.

Read: `docs/i18n_wiring_plan_20261115.md`, `js/i18n.js`, `scripts/test_i18n.js`, `assets/i18n/zh-TW.json`, `assets/i18n/en.json`, and `index.html` (read only, with `grep -n`/`sed -n`; one command per call, no `&&`).

Do, saving after each:
1. Write `scripts/apply_i18n_plan.py` (stdlib only): a table `EDITS = [(id, old, new), ...]` with EXACT strings copied from the current `index.html` (not line numbers: line numbers drift), one entry per edit of the plan, plus the `<script src="js/i18n.js">` line and the language switch. Behaviour: `--dry-run` (default) reads `index.html`, checks every `old` occurs exactly once (or states the expected count when the plan needs `replace all`), prints one line per edit `OK id` / `FAIL id reason`, writes nothing and exits 1 on any FAIL; `--apply` first copies `index.html` to `(not published)`, applies all edits in memory, aborts without writing when any check fails, writes once, and prints the count. Strings built in JS use `I18n.t('key', {...})`; markup gets `data-i18n`. The Chinese text stays the default: the page must look identical until the switch is used.
2. Make sure every key used by the script exists in BOTH json files (add missing keys to both with the English draft; keys only, same set in both).
3. Write `(not published)` (`unittest`, on a temp copy of `index.html`, never the real one): dry run writes nothing, apply on the copy gives a page where `node scripts/test_i18n.js` page checks would pass (run the checks of the key scan against the copy if the test script allows a path argument, otherwise scan in the unit test), a second apply reports nothing left to do, a changed `old` string makes the dry run FAIL.
4. Run `python3 -B scripts/apply_i18n_plan.py --dry-run` against the real `index.html` and paste the OK/FAIL counts; run `python3 -B (not published)`; paste the last lines. If a shell call is refused, say so; do not invent output.

Touch only `scripts/apply_i18n_plan.py`, `(not published)`, the two json files (new keys only) and `docs/kiro_143_result_gpt-5.6-terra.md` (max 12 lines). Never write `index.html`. No network, no git.
