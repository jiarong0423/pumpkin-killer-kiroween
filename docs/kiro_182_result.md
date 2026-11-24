# Task 182 result

## What changed

- Added `js/relay_client.js`: UMD `RelayClient.createClient`, strict sequence buffering, old-round handling, ordered-log state snapshots, token resume messages, injected reconnect scheduling (1/2/4/8 s, 60 s limit), and visible `out_of_sync` state.
- Added `scripts/test_relay_client.js`: fake socket/clock checks for ordering, filled gaps, old rounds, token reconnect with replayed sequence, 60-second give-up, and divergent round hashes.
- Added `scripts/measure_join_time.py` and generated `docs/join_time_20261116.md`: 20 loopback host/friend join-to-first-accepted-action measurements. The recorded median is 1.45 ms, p90 1.72 ms, min 1.36 ms, and max 1.86 ms.
- Added `scripts/test_relay_reconnect.py`: two relay clients complete two rounds, one disconnects and resumes by token, both complete two more rounds, and the test compares their ordered logs and round hash.
- Updated `scripts/pk_relay.py` and `scripts/test_pk_relay.py`: the relay previously had neither seat tokens nor `resume`. It now retains disconnected seats for up to 60 seconds, reclaims a token-bound seat, replays missed stamped messages, and sends global stamped messages to every current seat so clients never see sequence gaps. The relay integration suite includes a resume/replay test.
- Updated `docs/relay_protocol_20261115.md` with the private bootstrap token and `resume` message contract.
- Marked cross-device tasks 1, 2, 4, and 5 complete in `.kiro/specs/cross-device/tasks.md`.

## Verification commands and real output tails

```sh
node scripts/test_relay_client.js && node scripts/test_round_hash.js && node scripts/test_determinism.js
```

Output tail:

```text
relay client reconnect and hash checks: ok
PASS: 20 round-hash goldens; sub-pixel stable and one-pixel sensitive
test_determinism.js: 988 golden vectors passed
test_determinism.js: 10000 seed property cases passed
```

```sh
python3 -B scripts/test_pk_relay.py && python3 -B scripts/test_relay_reconnect.py && python3 -B scripts/measure_join_time.py && python3 -B scripts/test_round_hash.py && python3 -B scripts/test_determinism_golden.py
```

Output tail:

```text
Ran 9 tests in 2.365s

OK
relay reconnect ordered log: ok
join-time runs=20 median_ms=1.45
PASS: 20 round-hash goldens; sub-pixel stable and one-pixel sensitive
test_determinism_golden.py: 988 golden vectors passed
test_determinism_golden.py: 10000 seed property cases passed
```

```sh
git diff --check -- js/relay_client.js scripts/test_relay_client.js scripts/measure_join_time.py scripts/test_relay_reconnect.py docs/join_time_20261116.md scripts/pk_relay.py scripts/test_pk_relay.py docs/relay_protocol_20261115.md .kiro/specs/cross-device/tasks.md
```

The command exited 0 with no output.

## Could not verify

- Browser join-screen wiring, QR generation, and real mobile or internet latency were not tested. They are outside this task's allowed files and belong to task 183.
- Loopback socket tests ran successfully in this shell, so no owner-terminal fallback was needed. The measurement remains local-only and does not establish cross-device timing.
- `scripts/pk_relay_client.py` remains the minimal initial-connect test client. The reconnect test sends the documented raw WebSocket `resume` message because that file is outside this task's allowed edit list.
