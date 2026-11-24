# Kiro task 218 result

## What changed

- Reworked `scripts/pk_ai_gateway.py` for explicit `bedrock` and `gemini` backends. Bedrock is selected by default when an AWS region variable is present. It refuses an unset provider default in `shared/ai_models.json`, keeps legacy top-level Gemini configuration readable, imports `boto3` only in the Bedrock backend, uses Converse with the fixed system template, 60 output tokens, temperature 0.2, six-second client timeouts, and one immediate throttling retry.
- Added persistent UTC-day request and spend accounting in `PK_AI_STATE_DIR`. It enforces the existing client limits, daily request cap, daily spend cap, and total spend cap before later upstream calls. `/ai/health` returns only the required safe operational fields.
- Added constrained `pick` validation and its template to `shared/ai_prompts.json`. The model can choose only one supplied candidate ID.
- Changed `shared/ai_models.json` to the separate Bedrock and Gemini provider sections with owner-selected defaults intentionally `null`.
- Updated `scripts/test_ai_gateway.py` and added `scripts/test_bedrock_backend.py`. The Bedrock tests inject a fake client and use no network, credential, or boto3 import.
- Pinned `boto3==1.34.162` in `deploy/relay/requirements.txt`, updated gateway startup selection in `deploy/entrypoint.sh`, listed empty environment-variable placeholders in `.env.example`, and replaced the optional AI deployment notes in `deploy/README_DEPLOY.md`.

## Commands run

```text
python3 -B scripts/test_ai_gateway.py
....
----------------------------------------------------------------------
Ran 4 tests in 0.006s

OK

python3 -B scripts/test_bedrock_backend.py
........
----------------------------------------------------------------------
Ran 8 tests in 0.568s

OK

python3 -B scripts/test_no_secrets_in_tree.py
test_no_secrets_in_tree: no secrets detected in tracked files

sh -n deploy/entrypoint.sh
(exit 0; no output)
```

## Not verified

- No real Bedrock request was made. The owner must select and enable a Bedrock model, configure the server's standard AWS credentials or task/instance role, and set the official input/output prices.
- `scripts/test_no_secrets_in_tree.py` was not changed. Task step 5 asks to extend it, but the task LOCK does not permit that path. The existing checker was run successfully; the main line should make the specified AWS-pattern extension in a separately authorised task.
- The checker scans Git-tracked files. The task files remain untracked until the main line stages them, so the main line must rerun it after staging or equivalent tracking.

## Environment variables

`PK_AI_BACKEND`, `AWS_REGION`, `AWS_DEFAULT_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `PK_AI_PRICE_IN_PER_M`, `PK_AI_PRICE_OUT_PER_M`, `PK_AI_DAILY_CAP`, `PK_AI_DAILY_USD`, `PK_AI_TOTAL_USD`, `PK_AI_STATE_DIR`, `PK_ALLOWED_ORIGINS`, `PK_RELAY_LOG_LEVEL`, `PK_GEMINI_KEYS`.

## Model target

Owner decision 2026-11-16. `shared/ai_models.json`: `bedrock.default` and `bedrock.allowed` are `global.anthropic.claude-haiku-5-5` (profile ID; Converse supported; no in-Region ID in us-east-1 or ap-northeast-1). `gemini.default` stays `null`. `deploy/README_DEPLOY.md` sets `AWS_REGION=us-east-1` (Tokyo works with the same ID) and tells the owner to check Credits and Cost Explorer one day after the first calls, because the model is billed through AWS Marketplace and credits may not apply; fallback is a first-party Bedrock model with its official prices in `PK_AI_PRICE_IN_PER_M` and `PK_AI_PRICE_OUT_PER_M`. No real Bedrock call was made. No key or account ID was written.

Tests (last lines):
- `python3 -B scripts/test_ai_gateway.py`: `Ran 4 tests in 0.006s` / `OK`
- `python3 -B scripts/test_bedrock_backend.py`: `Ran 8 tests in 0.569s` / `OK`
