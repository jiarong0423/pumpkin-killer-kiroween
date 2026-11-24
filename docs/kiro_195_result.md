# Kiro task 195 result

## What changed

- Added `shared/ai_models.json` with no guessed Gemini model ID. Its `default` is `null`, so `scripts/pk_ai_gateway.py` refuses startup with one clear error until the owner or main line verifies and pins the lowest-cost Gemini model. `allowed` remains the ordered fallback list.
- Added `shared/ai_prompts.json` with fixed `aim` and test-only `taunt` templates. `aim` accepts only public computer-opponent fields and requires an exact in-range angle/power JSON response.
- Added `scripts/pk_ai_gateway.py`. `GatewayState`, `gateway_request`, and `GatewayHandler` enforce a 400-byte request limit, fixed templates, per-client 3-second and hourly limits, a daily cap, six-second upstream timeout, one ordered model fallback, strict result validation, safe 160-character output handling, and code-only logs. Key slots are sourced from the environment or a file reread every 60 seconds; only 401/403 triggers a 10-minute-cooldown rotation. A 429 never rotates keys.
- Added `scripts/test_ai_gateway.py`, which starts a fake local upstream and covers null-model startup refusal, default model selection, a one-time 404 fallback, 429 without key rotation, 401 rotation, invalid input and body size, rate/daily caps, log redaction, and `/ai/health` output.
- Added `scripts/test_no_secrets_in_tree.py`, which scans Git-tracked files for the specified Gemini and `AQ.` key shapes while printing only file names and line numbers on failure.
- Added Nginx `/ai` and `/ai/health` loopback proxies, forwarded client-address headers for gateway limits, and conditional gateway startup in `deploy/entrypoint.sh` only when a key source is configured.
- Updated `deploy/README_DEPLOY.md`, `.env.example`, and `.gitignore` with secret-only Coolify configuration, rotation guidance, and an explicit prohibition on browser, URL, source, documentation, and test keys.

## Commands run

```text
python3 -B scripts/test_ai_gateway.py
.......
----------------------------------------------------------------------
Ran 7 tests in 6.091s

OK

python3 -B scripts/test_no_secrets_in_tree.py
test_no_secrets_in_tree: no secrets detected in tracked files
```

I also attempted the following configuration check twice, but the tool permission request failed before execution. It produced no test output and is not claimed as passing.

```text
sh -n deploy/entrypoint.sh && python3 -B scripts/smoke_deployed.py --check-config deploy/nginx.conf
```

## Not verified / main-line follow-up

- No Gemini request, Coolify configuration, deployment, or real key was used. The fake upstream test is fully local.
- `sh -n deploy/entrypoint.sh` and `scripts/smoke_deployed.py --check-config deploy/nginx.conf` were not run because the execution permission was not granted.
- `deploy/Dockerfile.coolify` currently does not copy `scripts/pk_ai_gateway.py` into `/app`. The brief forbids touching that file, so the main line must add and verify the required copy instruction before enabling the gateway in Coolify.
- The secret guard deliberately scans Git-tracked files. The new untracked task files are not in its scan until the main line stages or otherwise tracks them; the main line must rerun it after that step.
