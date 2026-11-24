# Kiro task 93 — workstream W1: files for a public URL and a smoke test (no deployment)

Read: `docs/PLAN_20261115.md` (W1), `(not published)`, `(not published)` (Testing: the page must be free and unrestricted for judges until 2027-01-29), `scripts/release/check_asset_refs.py`, `scripts/release/export_manifest.json`. Do not deliberate at length: save each file as soon as it is written.

The page is static: `index.html`, `css/`, `js/`, `assets/`, `shared/`. Deployment itself is done by the owner on their own host; you write only files.

Write:
1. `deploy/Dockerfile` — `nginx:alpine` copying only `index.html`, `css/`, `js/`, `assets/`, `shared/` (no docs, build, scripts, `.kiro`, colab) to the web root; `EXPOSE 80`.
2. `deploy/nginx.conf` — `try_files`, gzip for text and json, correct types for `.woff2` and `.ogg`, long cache for `assets/` and short for `index.html`, a plain 404 page, no directory listing, no server tokens.
3. `deploy/.dockerignore` and `deploy/README.md` (max 25 lines: build and run commands, `docker build -f deploy/Dockerfile -t pumpkin-killer .` from the repository root, the port, what is copied).
4. `scripts/release/smoke_url.py <base_url> [--timeout 10]` — stdlib only: fetch `/`, require 200 and that the body contains `Pumpkin Killer`; fetch every `(not published)` path found by `check_asset_refs.py` (import its `scan`/`missing`; use only `REF` entries) and count responses that are not 200; print four lines (index status, paths checked, non-200 count and the first five paths, overall PASS/FAIL); exit 0 only on PASS. No credentials, no cookies, no retries beyond one.
5. `scripts/test_smoke_url.py` — `unittest`: start `http.server` from a temp folder on a free local port inside the test, check PASS on a good tree and FAIL when one referenced file is removed.

Run `python3 -B scripts/test_smoke_url.py` and, if you can, `docker build --check` is NOT required (do not run docker). Write `(not published)` (max 30 lines): files, commands with last output lines, what you did not run. Touch no other file. No network, no git.
