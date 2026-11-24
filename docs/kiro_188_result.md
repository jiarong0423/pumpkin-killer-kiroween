# Task 188 result — release and Coolify deployment preparation

## Changed

- Added `deploy/Dockerfile.coolify` and `deploy/entrypoint.sh`. The image serves
the static page with Nginx on port 80 and runs `scripts/pk_relay.py` on
loopback port 8765 in the same container.
- Updated `deploy/nginx.conf` with the `/relay` proxy. Upgrade requests route
to relay `/ws`; ordinary HTTP requests route to relay `/health`. The proxy
sets `Upgrade` and `Connection` headers and uses one-hour socket timeouts.
- Added `deploy/relay-config.js`, which sets `window.PK_RELAY` to the
same-origin `/relay` WebSocket URL. `deploy/README_DEPLOY.md` names the single
script tag the main line must add to `index.html`.
- Added `scripts/smoke_deployed.py`. Its `check`, `relay_room_check`, and
`config_is_valid` functions check the page title, service worker, manifest,
representative avatar, relay health endpoint, Nginx proxy directives, and two
WebSocket clients that create and join a room.
- Added `scripts/test_smoke_deployed.py`, including a local fake HTTP/WebSocket
deployment and an `sh -n` entrypoint check.
- Fixed the release export manifest and `scripts/test_export_tree.py`: the
manifest now exports `deploy/`, includes the deployment package, and excludes
the two unused audio files named in `docs/EXPORT_EXCLUDE_20261116.md`.
- Added `docs/RELEASE_READINESS_20261116.md` with the release-gate table and
owner deployment commands.

## Verification commands run

```sh
python3 -B scripts/test_smoke_deployed.py
python3 -B scripts/smoke_deployed.py --check-config deploy/nginx.conf
python3 -B scripts/test_check_deploy_files.py
python3 -B scripts/test_export_tree.py
python3 -B scripts/test_privacy_gate.py
python3 -B scripts/test_pwa_files.py
python3 -B scripts/test_make_download_package.py
python3 -B scripts/release/export_tree.py --help
python3 -B scripts/release/export_tree.py --source . --manifest scripts/release/export_manifest.json --out build/pk-release-dry-run --dry-run
```

The final output lines were:

```text
scripts/test_smoke_deployed.py
Ran 3 tests in 1.539s
OK
RELAY_WS url=ws://127.0.0.1:<port>/relay room=yes clients=2
OVERALL PASS

scripts/smoke_deployed.py --check-config deploy/nginx.conf
NGINX_CONFIG PASS

scripts/test_check_deploy_files.py
Ran 3 tests in 0.005s
OK

scripts/test_export_tree.py
Ran 8 tests in 1.369s
OK

scripts/test_privacy_gate.py
Ran 9 tests in 4.539s
OK

scripts/test_pwa_files.py
Ran 3 tests in 0.047s
OK

scripts/test_make_download_package.py
Ran 5 tests in 0.389s
OK

scripts/release/export_tree.py --source . --manifest scripts/release/export_manifest.json --out build/pk-release-dry-run --dry-run
SUMMARY selected=1158 skipped_symlinks=0
DRY RUN: wrote nothing
```

A tracked-name and export-selection check found:

```text
FORBIDDEN_SENSITIVE_NAMES=none
KIRO_TRACKED=True
KIRO_IGNORED=False
LICENSE_ROOT=True
EXCLUSIONS_EXPORTED=none
DEPLOY_FILES_EXPORTED=yes
EXPORT_DRY_RUN files=1159 bytes=96172301
```

## Not verified

- The owner-managed privacy gate was not run. The attempted command was:

  ```sh
  PK_TERMS="$HOME/pk_privacy_terms.txt" python3 -B scripts/release/privacy_gate.py --tree . --check all
  ```

  It was denied before execution. Its last output was:

  ```text
  The permission request failed before it was answered, so this call did not run; the user did not reject it.
  ```

- The requested full JavaScript non-socket suite was not run. The attempted
  command was `for test_file in scripts/test_*.js; do node "$test_file" || exit
  $?; done`; it was denied before execution with the same message above.
- No Docker build, local container run, live domain smoke test, tunnel command,
Git push, or Coolify operation was run.
- The main line still needs to add the script tag below to `index.html` and
regenerate any required service-worker precache before deployment.

```html
<script src="relay-config.js"></script>
```

The owner must provide the target repository URL and the public domain before
release commands can be completed.
