# Kiro task 93 result

Changed: `deploy/Dockerfile`, `deploy/nginx.conf`, `deploy/.dockerignore`, and `deploy/README.md` define the static nginx image and its local run instructions. `scripts/release/smoke_url.py` adds `fetch`, `check`, and `main`; `scripts/test_smoke_url.py` tests passing and missing-asset local HTTP trees.

Verified with:
```sh
python3 -B scripts/test_smoke_url.py
```
Last output lines:
```text
Ran 2 tests in 1.181s

OK
```

Not run: Docker commands, including `docker build`, as required by the brief. No external URL or deployment was contacted.
