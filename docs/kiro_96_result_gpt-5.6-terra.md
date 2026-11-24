# Task 96 result

Changed: `scripts/release/privacy_gate.py` imports stdlib `fnmatch` for `is_font_license`.
Changed: `scripts/test_privacy_gate.py` adds subprocess regressions for the OFL P1 exception and a non-OFL font file.
Cause: task 95 called `fnmatch.fnmatchcase` without importing `fnmatch`, which crashed an `--check all` tree scan.
Verification run: `python3 -B scripts/test_privacy_gate.py`
Last output lines:
```
Ran 7 tests in 2.318s

OK
OK
```
Release link check requested but not run: `PK_TERMS="$HOME/pk_privacy_terms.txt" python3 -B scripts/release/privacy_gate.py --tree ../pk-release --check links`.
The environment permission request was unanswered, so it produced no gate output or finding counts.
Not run: any network, git, release export, or other test suite.
