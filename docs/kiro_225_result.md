# Task 225 result — 2026-11-16

## What changed

- `scripts/e2e_local.py`: added `RelayTrace`, `TracedQueue`, `_turn_from_message`, `trace_bridge`, and `agreed_relay_turn`.
- `run_e2e()` now records every send and receive at each bridge boundary to a fresh redacted JSONL file under `$TMPDIR`. It redacts the invitation code and seat token.
- `run_e2e()` now obtains its current `(round, active team)` from the `start`, started `room_state`, and `end_turn.next_*` messages received by **both** bridges. It waits until both local sessions applied that relay state before submitting an action. It no longer hard-codes `relay_round` or `relay_active`.
- `run_e2e()` now fails at the first divergent relay/local turn instead of submitting the stale action that the prior driver generated.

No MCP or relay implementation files were changed, as required by the task lock.

## First rejected message and cause

The original driver’s first rejected message is the red bridge action with `round: 2`, `phase: "red"`, sent after the relay had accepted white’s round-2 end turn and advanced to round 3/red. The relay correctly replied `{"type":"error","code":"stale_or_out_of_turn"}`.

The redacted bridge trace establishes this ordered relay sequence:

1. `start`: round 1/red.
2. Red action and judge, then `end_turn`: next round 1/white.
3. White action and judge, then `end_turn`: next round 2/white. Both round-1 hashes are sent.
4. White action and judge in round 2, then `end_turn`: `next_round: 3`, `next_phase: "red"`.

At step 4, both bridge sessions remain at engine round 2 rather than adopting relay round 3. The error is therefore not a driver timing error after the updated wait logic.

The defect is in `scripts/mcp_stdio_server.py`, which this task may not edit. In connected `Session._tool_end_turn()`, round 2 makes `first_team` equal `"white"`. When white ends that relay turn, the `relay_team == first_team` branch only calls `set_relay_phase("red")`; it does not call `_resolve_round()`. The relay’s `RelayServer._end_turn()` correctly increments its one-team-per-round protocol state from round 2/white to round 3/red. The local engine remains round 2 while the relay is round 3. The old e2e driver then sent the stale round-2 red action, which caused the reported rejection.

A fresh redacted trace is written for every run under `$TMPDIR` and includes every bridge send/receive in order. It contains no code or seat-token value.

## Commands run and real last lines

```text
cd <repo> && python3 -B scripts/test_e2e_local.py
```

Ran after the updated driver, three times:

```text
AssertionError: relay advanced to round 3/red but a bridge did not apply its opponent end turn; trace=<TMPDIR>/pk-e2e-*.jsonl
Ran 1 test in 5.486s
FAILED (failures=1)
```

All three runs reached the same round-3/red bridge defect. The test cannot pass until the connected bridge/engine turn transition is fixed by the owner of `scripts/mcp_stdio_server.py`.

```text
cd <repo> && python3 -B scripts/test_pk_relay.py
```

```text
Ran 11 tests in 2.387s

OK
```

```text
cd <repo> && python3 -B scripts/test_mcp_connect.py
```

```text
AssertionError: 2 != 1
Ran 5 tests in 0.550s
FAILED (failures=1)
```

`test_mcp_connect.py` was untouched. Its existing `test_round_hashes_agree_and_replayed_end_turn_is_dropped` check also failed in this workspace because the two round-1 hashes differed. I did not change the MCP implementation or its test because both are outside this task’s lock.

## Not verified

- Three complete relay rounds cannot be verified because both connected sessions stop at local round 2 after the relay announces round 3/red.
- Equal hashes for three completed rounds and the final no-private-item-data assertion cannot be reached until the connected round-transition defect is repaired.
- I could not keep `scripts/test_mcp_connect.py` green: it failed twice with the recorded hash mismatch. `scripts/test_pk_relay.py` passed.
