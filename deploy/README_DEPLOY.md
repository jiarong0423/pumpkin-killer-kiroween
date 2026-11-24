# Coolify deployment

This image is one deployable unit. Nginx serves the static game on port 80 and
proxies the public `/relay` path to the loopback-only room relay. Cloudflare
terminates TLS, so Nginx listens on HTTP only. The relay keeps rooms in memory;
a redeploy clears active rooms.

## Required environment variables

| Variable | Value |
|---|---|
| `PK_ALLOWED_ORIGINS` | Comma-separated browser origins allowed to use the relay. Set it to `https://<host>` and add any separate preview origin deliberately. Do not include a trailing slash. |
| `PK_RELAY_LOG_LEVEL` | Optional Python log level. The default is `WARNING`. |
| `PK_GEMINI_KEYS` | Optional comma-separated Gemini keys for the AI gateway. Set it as a Coolify **Secret**. Keep one active key except during an owner-approved replacement. |
| `PK_GEMINI_KEYS_FILE` | Optional path to a mounted Coolify secret file. The gateway rereads this file every 60 seconds. Use this instead of `PK_GEMINI_KEYS` when the platform can rotate file contents without rebuilding. |
| `PK_AI_DAILY_CAP` | Optional global maximum upstream AI calls per calendar day. The default is `200`. |

`HOST` and `PORT` are intentionally fixed inside the entrypoint to
`127.0.0.1:8765`. The optional gateway similarly listens only on
`127.0.0.1:8766`. Do not expose either port in Coolify. Nginx is the only
public listener.

## Bedrock AI gateway

Set the following Coolify variables. Mark credentials as **Secrets**. Do not
store a credential or account ID in this repository. The model ID is public
and lives in `shared/ai_models.json`.

| Variable | Purpose |
|---|---|
| `PK_AI_BACKEND=bedrock` | Selects Bedrock. It is also the default when `AWS_REGION` or `AWS_DEFAULT_REGION` is set. |
| `AWS_REGION` | AWS region for Bedrock Runtime. |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` | Optional standard AWS credentials, each a Coolify Secret. Prefer an instance or task role when available. |
| `PK_AI_PRICE_IN_PER_M`, `PK_AI_PRICE_OUT_PER_M` | **Required to enable the AI gateway.** Owner-provided USD prices per million input and output tokens from the official Bedrock price page. If either is missing the entrypoint prints an ERROR and does not start the gateway, because the dollar caps below cannot count spend without prices. |
| `PK_AI_DAILY_CAP` | Maximum upstream requests in a UTC day. Default: `200`. |
| `PK_AI_DAILY_USD` | Maximum recorded spend in the current UTC day. Default: `1.00`. |
| `PK_AI_TOTAL_USD` | Maximum recorded spend across restarts. Default: `20.00`. |
| `PK_AI_STATE_DIR` | Persistent writable counter directory. Default: `/tmp/pk_ai`; mount persistent storage when redeploys must retain the total cap. |

The owner must enable Bedrock model access for the selected model in the AWS
Bedrock console, then set its ID in `shared/ai_models.json`. Both provider
`default` values are intentionally `null`; the gateway refuses startup until
the selected provider has an owner-confirmed default ID. Browser requests
cannot select a model. `boto3` is packaged in `deploy/relay/requirements.txt`.

### Model target (owner decision 2026-11-16)

`bedrock.default` is `global.anthropic.claude-haiku-5-5`, the only allowed ID.
Claude Haiku 5.5 has no in-Region ID in `us-east-1` or `ap-northeast-1`, so a
profile ID is required. The `global` profile works from both Regions. Set
`AWS_REGION=us-east-1` (the owner's console Region). Tokyo
(`ap-northeast-1`) works too with the same ID.

**Check after the first real call.** The model card says Claude Haiku 5.5 is
"billed through AWS Marketplace", and AWS promotional credits may not apply to
Marketplace charges. One day after the first test calls, open Billing and Cost
Management > Credits (remaining amount) and Cost Explorer. If the credits did
not go down, switch `bedrock.default` (and `allowed`) to a first-party Bedrock
model chosen in the console, and set `PK_AI_PRICE_IN_PER_M` and
`PK_AI_PRICE_OUT_PER_M` to that model's official prices. The cheapest text
models on the pricing page were, per million input/output tokens: Google Gemma 4
E2B at 0.04/0.08 USD, NVIDIA Nemotron 3 Nano 30B at 0.06/0.24, Z AI GLM 4.7
Flash at 0.07/0.40. Their exact model IDs were not verified.

Set an AWS Budget alarm, for example at **USD 20**, in addition to these local
guards. The request cap blocks a request before calling Bedrock. The money
caps block later requests after recorded Bedrock token usage reaches a cap.
If either price variable is unset, the gateway logs one warning at startup and
keeps request caps active without recording spend.

To rotate credentials, add the new credential values as the second Coolify
secret values, restart and verify the workload, then delete the old values.
For role credentials, replace the role attachment under the platform's normal
rotation procedure. Never log or paste either credential into a shell command.

`/ai/health` exposes only configuration state, selected backend/model, slot
count, request count/cap, and current-day spend. It exposes no credentials or
account identifiers.

## Prepare the release

1. Create the empty target GitHub repository. Keep it private until the privacy
   and clean-checkout gates pass; the owner changes its visibility to Public as
   the release step.
2. Add the repository as a second remote without replacing the current remote:

   ```sh
   git remote add release <repository-url>
   ```

3. Set the owner-managed term file without printing its content. Choose a new or
   empty `../pk-release` directory, then run the release gate and make the
   export:

   ```sh
   export PK_TERMS="$HOME/pk_privacy_terms.txt"
   python3 -B scripts/release/privacy_gate.py --tree . --check all
   python3 -B scripts/release/export_tree.py --source . --manifest scripts/release/export_manifest.json --out ../pk-release --apply
   python3 -B scripts/release/privacy_gate.py --tree ../pk-release --check all
   ```

4. Follow the existing release-history procedure to make `../pk-release` a
   clean repository, then push only that approved export:

   ```sh
   git -C ../pk-release remote add origin <repository-url>
   git -C ../pk-release push -u origin main
   ```

5. Ask the main line to add this line immediately before the page scripts in
   `index.html`, then regenerate the service-worker precache if its procedure
   requires it:

   ```html
   <script src="relay-config.js"></script>
   ```

   `relay-config.js` sets `window.PK_RELAY` to the same-origin WebSocket URL.
   The Coolify Dockerfile copies it to the web root.

## Create the Coolify application

1. Create **New Application** from the approved GitHub repository.
2. Select build pack **Dockerfile** and set the Dockerfile path to
   `deploy/Dockerfile.coolify`.
3. Set the domain to `http://<host>`, disable **Redirect to HTTPS**, and use
   port `80`. Cloudflare performs the HTTPS redirect and TLS termination.
4. Set `PK_ALLOWED_ORIGINS=https://<host>`. Set `PK_RELAY_LOG_LEVEL=WARNING`
   only if a value is desired. Do not add `HOST` or `PORT`. Configure the
   optional AI settings only after selecting the verified pinned model:
   `PK_GEMINI_KEYS` must be marked as a Coolify **Secret**, or
   `PK_GEMINI_KEYS_FILE` must name a mounted secret file. Never put either
   value in the application source or build arguments.
5. Deploy from Coolify. The owner then runs the tunnel-route command in their
   own terminal:

   ```sh
   docs/ai-generated/2026Q4/20261020_coolify_full_migration/add_prod_ingress.sh <host>
   ```

## Smoke test after the Cloudflare route is live

```sh
curl -sI https://<host>/
curl -fsS https://<host>/relay
python3 -B scripts/smoke_deployed.py https://<host>
python3 -B scripts/smoke_deployed.py https://<host>
```

Each smoke-script invocation opens two `wss://<host>/relay` clients. The first
creates a room and the second joins it. Both commands must end with `OVERALL
PASS` before the owner makes the repository public.

For a local configuration-only check that does not require Docker:

```sh
python3 -B scripts/smoke_deployed.py --check-config deploy/nginx.conf
sh -n deploy/entrypoint.sh
```
## Relay configuration

| Variable | Purpose |
|---|---|
| `PK_ALLOWED_ORIGINS` | Comma-separated browser origins allowed to use the relay, such as `https://<host>`. |
| `PK_RELAY_LOG_LEVEL` | Optional relay log level. The default is `WARNING`. |

`HOST` and `PORT` are fixed to `127.0.0.1:8765`. The optional gateway uses
`127.0.0.1:8766`. Nginx is the only public listener.

## Cost guard in one place
- Nothing in this image costs money by itself: with no AI variables the gateway never starts and the game uses its built-in opponents.
- To enable the online opponent, set the AWS credentials (or role), `PK_AI_PRICE_IN_PER_M`, `PK_AI_PRICE_OUT_PER_M`, and choose the caps: `PK_AI_DAILY_CAP` (calls per day), `PK_AI_DAILY_USD`, `PK_AI_TOTAL_USD`. Defaults are 200 calls, 1.00 USD per day, 20.00 USD in total.
- The counters live in `PK_AI_STATE_DIR` (default `/tmp/pk_ai`); without persistent storage a redeploy resets the total.
- To switch the AI off at once, delete the AWS variables (or the prices) and redeploy.
