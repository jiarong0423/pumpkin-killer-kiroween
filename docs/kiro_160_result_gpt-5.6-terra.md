# Task 160 result — gpt-5.6-terra

What changed: no implementation files changed. `scripts/mcp_stdio_server.py` cannot meet the required remote apply/judge contract with the locked relay currently present.
Verification commands: `python3 -B scripts/test_mcp_connect.py` → `python3: can't open file .../scripts/test_mcp_connect.py: [Errno 2] No such file or directory` (exit 2).
`python3 -B scripts/test_mcp_stdio.py` → `Ran 27 tests in 0.787s` / `OK`.
`python3 -B scripts/test_mcp_seats.py` → `Ran 6 tests in 0.003s` / `OK`.
`python3 -B scripts/test_mcp_turns.py` → `Ran 5 tests in 0.001s` / `OK`.
`python3 -B scripts/test_pk_headless_match.py` → `Ran 4 tests in 0.077s` / `OK`.
`python3 -B scripts/test_pk_relay.py` → `Ran 5 tests in 1.314s` / `OK`.
Could not verify: no `--connect` code or requested integration test was written, so the K7 behaviours are unverified.
Needed change outside this task's allowed files: `pk_relay.py:Room._action` discards `angle`, `power`, `start`, and `claimed_landing` from the forwarded `action` message. The target therefore cannot run `flight_py`, compare the claimed landing, apply the action, or issue the required `judge`; the sender also receives no stamped action/`seq`.
A relay/protocol decision is also needed for the known engine drift: MCP round resolution uses `WIND_PUSH` while `flight_py` uses `WIND_ACCEL`; changing either is explicitly out of scope.
