# Task 89 R5 result — gpt-5.6-terra

## Delivered
- Created `scripts/release/clean_checkout.sh`.
- The script parses `--src`, `--log`, and optional `--keep`; copies only to a `mktemp -d` directory by local `git clone --no-hardlinks` or `cp -R`; and removes that directory on exit unless kept.
- It finds a local free port with Python, starts `python3 -m http.server` in the copy, waits for `/index.html`, fetches every `REF` path from `check_asset_refs.py`, stops its exact server PID, then uses `lsof` to verify the port has no listener.
- It logs individual Node and Python test output plus PASS/FAIL exit codes, preserves the listed known failures unchanged, and prints/logs the required five-line summary.

## Commands attempted
```text
bash -n scripts/release/clean_checkout.sh
bash scripts/release/clean_checkout.sh --src . --log docs/audition/clean_checkout_run1.log
```
Both requests were denied before approval (`The permission request failed before it was answered`), so neither command ran. There are no real summary lines or test results to quote. The T5 boxes remain unchanged because no command output was observed.

## Not verified
- Shell syntax and the real clean-checkout run.
- The expected current failure caused by missing assets and the known failing test.
- Linux, Docker, and a clean `(not published)` checkout.
