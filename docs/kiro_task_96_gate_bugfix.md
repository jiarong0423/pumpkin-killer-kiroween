# Kiro task 96 — fix a crash your task 95 introduced in the privacy gate, and the test that missed it

The main line re-exported and ran `PK_TERMS=<terms file> python3 -B scripts/release/privacy_gate.py --tree ../pk-release --check all` (log: `(not published)`). It crashed:
`NameError: name 'fnmatch' is not defined` at `scripts/release/privacy_gate.py` in `is_font_license` (about line 168), called from `scan_text_checks` (about line 183). Your task 95 added the OFL font-licence exception for check P1 and used `fnmatch` without importing it. `python3 -B scripts/test_privacy_gate.py` still printed OK, so no test reaches that code with a real tree.

Do, in this order, saving after each:
1. Fix the missing import in `scripts/release/privacy_gate.py` (stdlib `fnmatch`). Change nothing else in that file unless a test in step 2 proves another defect.
2. In `scripts/test_privacy_gate.py` add tests that run the gate as a subprocess (`python3 -B scripts/release/privacy_gate.py --tree <temp tree> --check all`, with `PK_TERMS` pointing at a temp terms file built in the test) on a temp tree that contains: (a) `(not published)` with an email-shaped string assembled from parts inside the test: expect exit 0 and no P1 hit for that file; (b) the same string in `(not published)`: expect exit 1 and a P1 hit for that file; (c) an ordinary clean file: no hit. Also assert the process does not crash (no `Traceback` in stderr) for a tree that has a `assets/fonts` folder with a non-OFL file.
3. Run `python3 -B scripts/test_privacy_gate.py` and paste the last lines. Then run `python3 -B scripts/release/privacy_gate.py --tree ../pk-release --check links` (read-only; the exit code is information) with `PK_TERMS` set to the file `~/pk_privacy_terms.txt`; do not read that file and do not print any hit text, only the count of lines per class.

Write `(not published)` (max 20 lines): the cause, the files changed, the commands with last output lines, what you did not run. Touch no other file. No network, no git.
