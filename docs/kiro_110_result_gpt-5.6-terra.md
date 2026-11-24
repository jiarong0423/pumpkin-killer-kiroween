# Task 110 result — gpt-5.6-terra

## Changed
- `scripts/release/clean_checkout.sh`: added `--worktree`, `copy_worktree`, scanner `MISSING`/`CASE` failure counting, first-five-path reporting, and copy-mode summary.
- `scripts/test_clean_checkout.py`: added `CleanCheckoutTests` with a temporary worktree fixture that checks missing then restored assets.

## Commands and results
- `bash -n scripts/release/clean_checkout.sh` was denied before approval and did not run: `The permission request failed before it was answered, so this call did not run; the user did not reject it.`
- `python3 -B scripts/test_clean_checkout.py` passed. Last lines:
```text
Ran 1 test in 1.008s

OK
```

## Not verified
- Shell syntax was not verified because the required `bash -n` command did not run.
