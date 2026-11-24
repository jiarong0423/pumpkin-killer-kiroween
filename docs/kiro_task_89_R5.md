# Kiro task 89 — stage R5 / spec task T5: clean-checkout script

Execute task T5 from `.kiro/specs/release-package/tasks.md` (your own spec). Read first: that T5 section and the requirements it cites, `docs/kiro_task_85_release_delivery.md` stage R5, `docs/kiro_84_release_plan_claude-sonnet-5.5.md` section 5. Save the file as soon as it is written.

Write `scripts/release/clean_checkout.sh` (bash, `set -u`, no network, no git push, no remote):
- Usage: `bash scripts/release/clean_checkout.sh --src <dir> --log <file> [--keep]`. It copies `--src` (a plain directory; if it has a `.git` folder use `git clone --no-hardlinks` into the temp folder, otherwise `cp -R`) into a fresh `mktemp -d` folder and works only inside that copy; it deletes the temp folder at exit unless `--keep`.
- In the copy: start `python3 -m http.server` on a free port in the background (find the port with python), wait until `/index.html` answers, fetch `index.html` and check it returns 200; fetch every `assets/` path found by `python3 -B scripts/release/check_asset_refs.py --root <copy>` (use its `REF` lines) and count HTTP 404s; stop the server with the exact PID it started and verify with `lsof` that no listener remains on that port (the same command that starts the server must also stop it).
- Run every `node scripts/test_*.js` and `python3 -B scripts/test_*.py` of the copy, one by one, recording PASS or FAIL with the exit code. Known failing tests are listed, never edited and never hidden. Do NOT edit any test (the owner has not approved turning tests into SKIP).
- Everything goes to the file named by `--log` (full output) and a summary of five lines to stdout: server 200 yes/no, 404 count, tests passed, tests failed (names), and the overall result. Exit 0 only when index is 200, 404 count is 0 and no test failed; otherwise exit 1.

Run `bash -n scripts/release/clean_checkout.sh`, then one real run: `bash scripts/release/clean_checkout.sh --src . --log (not published)` (the folder `(not published)` is git-ignored). Exit 1 is expected today because of known missing files and the known failing test; report the exact summary lines.

Write `(not published)` (max 40 lines): file created, commands run with the summary lines, what you did not run (Linux, Docker). Update only the T5 boxes of `tasks.md` that a command output you saw proves. Touch no other file. Stdlib and system tools only.
