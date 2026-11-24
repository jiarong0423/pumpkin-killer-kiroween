# Release readiness — 2026-11-16

This is Kiro's preparation report. Main line verification is still required.
No repository was pushed, no container was built, and no cloud service was
contacted.

| Gate | Status | Reason or evidence |
|---|---|---|
| Privacy gate | NOT RUN | The command requiring the owner-managed `PK_TERMS` file was denied before execution. Run the command below; it prints locations only. |
| Secrets by name | PASS | The tracked-name check found no credential-bearing `.env`, `.pem`, `.p12`, `id_rsa`, `.netrc`, key, or token file forms. `scripts/key_*.py` are image-keying source files, not credential files. |
| `.kiro` present | PASS | `.kiro/` has tracked files and `git check-ignore -q .kiro` returned false. |
| Licence | PASS | Root `LICENSE` exists. |
| Export size | PASS | Manifest dry run selected 1,212 files. It wrote nothing. |
| Excluded files | PASS | The four files named in `docs/EXPORT_EXCLUDE_20261116.md` are not selected by the manifest. |
| Deploy files | PASS | `scripts/test_smoke_deployed.py` passed its Nginx directive, Dockerfile, entrypoint syntax, and fake deployment checks. |
| Smoke script | PASS | The fake deployment test checked page title, service worker, manifest, image, `/relay` health, and two WebSocket clients that create and join a room. |

## Checks run

```sh
python3 -B scripts/test_smoke_deployed.py
python3 -B scripts/smoke_deployed.py --check-config deploy/nginx.conf
python3 -B scripts/test_check_deploy_files.py
python3 -B scripts/test_export_tree.py
python3 -B scripts/test_privacy_gate.py
python3 -B scripts/test_pwa_files.py
python3 -B scripts/release/export_tree.py --help
python3 -B scripts/release/export_tree.py --source . --manifest scripts/release/export_manifest.json --out build/pk-release-dry-run --dry-run
```

The requested complete JavaScript suite command was denied before execution, so
it is not recorded as passing. The `PK_TERMS` privacy-gate command was also
denied before execution.

## Owner release commands

Set the target repository URL and public domain before starting. Do not replace
an existing remote. Use an unused or empty `(not published)` directory; the
export command refuses a non-empty destination.

```sh
git remote add release <repository-url>
export PK_TERMS="$HOME/pk_privacy_terms.txt"
python3 -B scripts/release/privacy_gate.py --tree . --check all
python3 -B scripts/release/export_tree.py --source . --manifest scripts/release/export_manifest.json --out ../pk-release --apply
python3 -B scripts/release/privacy_gate.py --tree ../pk-release --check all
```

After the main line completes the approved clean-history procedure in the
export directory:

```sh
git -C ../pk-release remote add origin <repository-url>
git -C ../pk-release push -u origin main
```

In Coolify, create an application from the approved GitHub repository, select
Dockerfile build pack, set Dockerfile path `deploy/Dockerfile.coolify`, domain
`http://<host>`, port `80`, and disable redirect to HTTPS. Set
`PK_ALLOWED_ORIGINS=https://<host>`. The owner runs the tunnel route command in
their own terminal:

```sh
docs/ai-generated/2026Q4/20261020_coolify_full_migration/add_prod_ingress.sh <host>
```

Then run:

```sh
curl -sI https://<host>/
curl -fsS https://<host>/relay
python3 -B scripts/smoke_deployed.py https://<host>
python3 -B scripts/smoke_deployed.py https://<host>
```

The main line must add the following exact line before the page scripts in
`index.html`:

```html
<script src="relay-config.js"></script>
```
