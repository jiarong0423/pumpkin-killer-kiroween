# Kiro task 221 result

## What changed

- `scripts/test_qr_decode.py`: replaced the UTF-8-only skipped loop with a deterministic ASCII proof plan: 300 random 10–120-byte ASCII payloads, each exercised at L and M, with URL punctuation (`?`, `=`, `&`, `%`, `/`, `:`), six-pixel modules, and four-module quiet zones. It also adds boundary cases for L versions 1–10 and M versions 1–7, while retaining a clearly labelled non-ASCII ECI decoder SKIP.
- `scripts/test_qr_code.js`: pins the 51-byte hosted join link to version 4-M and version 3-L. The prior result document already stated those actual capacities, so it was not changed under this task's file lock.
- `scripts/test_no_secrets_in_tree.py`: scans tracked UTF-8 text only, adds AWS access-key ID shapes, and detects an assigned 40-character base64-looking value only when the assignment name contains `secret` or `key`. Findings print only `file:line`. Its in-memory self-test constructs fake credentials at runtime and confirms that a SHA-1 hash comment does not match.
- `scripts/pk_relay.py`: accepts a valid host-only `host_side_choice` in `create_room` or the host's `ready` message. `computer` uses and stores a separate 31-bit `secrets` coin in the room. A valid option emits resolved `left` or `right` in `start`; missing or invalid options preserve the old start-message shape with no client error.
- `scripts/test_pk_relay.py`: adds socket integration coverage for fixed, computer-resolved, ready-message override, invalid, and absent host-side choices.
- `docs/relay_protocol_20261115.md`: documents the create/ready fields, relay-side computer coin, resolved `start` value, and backward-compatible omission.

## Commands run

```text
node scripts/test_qr_code.js
qr code capacity L v1-v10 and M v1-v7: ok

python3 -B scripts/test_no_secrets_in_tree.py
test_no_secrets_in_tree: no secrets detected in tracked text files (self-test passed)

python3 -B scripts/test_pk_relay.py
----------------------------------------------------------------------
Ran 11 tests in 3.656s

OK

git diff --check
# exit 0; no output
```

## Could not verify

```text
python3 -B scripts/test_qr_decode.py
AssertionError: decode mismatch at M case 5: expected '<ASCII payload>', got '' (matrix 45x45)
```

The new ASCII proof correctly fails rather than skipping. The failure occurs on an ASCII level-M version-7 matrix, before the non-ASCII ECI limitation matters. Targeted local checks showed the installed OpenCV decoder can decode an OpenCV-generated version-7 QR at six pixels per module, but cannot decode this encoder's level-M version-7 output; L versions 7–10 also fail. I did not claim the required QR proof passed and did not install a decoder. The QR encoder needs a focused compatibility fix before this test can pass.

The relay socket tests ran successfully in this environment. Before deployment, the owner or main line should rerun `python3 -B scripts/test_pk_relay.py` in the target Python environment; no deployment or relay process was started here.
