# Kiro 101 result (claude-sonnet-5.5): INCOMPLETE, steps 2 (backup only), 1 (analysis only); steps 3 and 4 not done
Cause: every write, edit, or delete into `.kiro/hooks/` and most `execute_bash` calls failed with "permission request failed before it was answered" (not rejected by the user). Only `pwd` and writes under `docs/` worked.

## Done
- Backup (written with the file tool, not `cp`; copied from the contents I read, so not byte-compared): `(not published)` has the 3 old `.kiro.hook` files and `pk-checks.json`.
- `.kiro/hooks/` is UNCHANGED: the 3 `.kiro.hook`, 3 IDE `.json` and `pk-checks.json` are all still there, so one save can still fire a hook twice.

## Differences found (old `.kiro.hook` vs IDE `.json`)
- Event: `fileEdited` -> `PostFileSave`; same commands, same `enabled: true`. No command differs.
- engine: old pattern `index.html` (exact name); new matcher `index\.html$` has no left anchor, so it also matches `real_index.html`, `backup_index_*.html`. Fix to apply: `"matcher": "(^|/)index\\.html$"` (as in pk-checks). NOT applied.
- constants: patterns and matcher equivalent. Description still says the script "does not exist yet" but `scripts/test_constants_sync.py` exists (text only, behaviour correct).
- rig: patterns and matcher equivalent; the command is still a no-op (`(not published)` absent).

## Not done, with the plan
- Remove the 3 `.kiro.hook` files and `pk-checks.json` after the three single-hook files exist.
- Split `pk-checks.json` into `preload-block-fresh-on-index-save.json`, `constants-sync-on-engine-save.json`, `ledger-on-kiro-result-save.json` in the IDE shape: `version v1`, one `hooks[]` entry, keep `timeout: 60` and the log-line echo, and add `"enabled": true` (the IDE's own files have it, pk-checks lacked it; it may be why the panel greyed them, unverified). No local doc says the IDE ignores `timeout` (checked `(not published)`, which lists it as valid).
- Double fire to expect: after the split, a save of `shared/constants.json` or `scripts/mcp_game_server.py` fires both `test-constants-sync-on-save` and `constants-sync-on-engine-save`. Merging them is a decision for the main line.

## Commands
- JSON validation of every file in `.kiro/hooks/`, `test_constants_sync.py`, `test_mcp_game.py`: NOT RUN (shell calls failed). No output to quote.
- Never touched: `index.html`, git, network.
