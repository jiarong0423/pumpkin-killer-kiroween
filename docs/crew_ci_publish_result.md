# Crew result: CI and publish (2026-11-16)

Surface: Kiro Crew through ACP. No push, commit, or network call was made.

## Part A: CI (done)
Created: `(not published)`, and this file. Nothing else was touched.

- Triggers: push and pull request to `main`. Permissions: `contents: read`. No secrets.
- Job `tests` (Node 20, Python 3.10): installs `pillow numpy websockets`, runs every `scripts/test_*.js` and `scripts/test_*.py` in one loop (prints each name, keeps going, fails at the end), then `test_no_secrets_in_tree.py` and `make_sw_precache.py --check` (the flag exists).
- Job `browser-measure`: `measure_phone_layout.mjs` with `CHROME_PATH=/usr/bin/google-chrome`, `continue-on-error: true`. Reason: Chrome should be on the runner image, but a measured layout check can vary, so it does not block.
- Versions: no `package.json`, `.nvmrc` or `.python-version` exist. Node 20 is the oldest with built-in `fetch` that the scripts use. Python 3.10 is the oldest I could run locally (3.10.22). Older ones are untested.
- YAML check: `yaml` module is not installed, so I checked the structure by reading only. Not machine-validated.

## Local run (Python 3.10.22, Node v26.13.0; 100 scripts, 5 min cap each)
- 86 pass, 14 fail.
- 11 fail only because a library is missing here (PIL, numpy, websockets). The CI install step covers them. Not re-run with the libraries.
- 3 fail on their own, need a look: `test_fonts.py` (1 failure), `test_mcp_seats.py` (1 failure), `test_pwa_files.py` (1 failure).
- `make_sw_precache.py --check` says `STALE sw precache: would write 69 files; 20 preload assets`. CI would fail on this step until the owner runs `--apply`. I did not change it.
- Socket-bound tests were not isolated; failures seen were import errors, not sandbox errors.

## Uncertain
- The 3 failures may come from other agents editing this folder right now.
- First real CI run may differ (Linux, fonts, Python 3.10 with pip libraries).

## Part B: publish (NOT DONE, gated)
- G1 `docs/PRIVACY_GATE_OK.txt`: MISSING (`ls` says no such file). STOP.
- G2 to G4: not checked. `(not published)` has only a `docs` folder so far.
- Needed from the owner: run `python3 -B scripts/release/privacy_gate.py --tree . --check all` with their `PK_TERMS`, save the output to `docs/PRIVACY_GATE_OK.txt`, produce `(not published)` with `export_tree.py ... --apply`, and say "push pumpkin-killer-kiroween" in chat.
