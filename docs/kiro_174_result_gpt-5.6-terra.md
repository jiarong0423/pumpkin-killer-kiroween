# Kiro task 174 result (gpt-5.6-terra)

## What changed
- `scripts/pk_relay.py`: `Room`, readiness handling, and action forwarding now use non-zero 31-bit seeds; require both ready teams unless a room was created with `solo: true`; carry an allowed scene in `start`; permit one move and one attack per turn; and forward validated `die` and `bounce` fields only when they are integer values from 1 to 6.
- `scripts/pk_relay_client.py`: `RelayClient` and its CLI can create a solo room and choose an allowed scene.
- `scripts/mcp_stdio_server.py`: `Session.public_weather` reports inactive clear weather offline; relay starts apply the selected scene; `ConnectedRelay` waits for `request_ready()` by default; and `--auto-ready` opts in to automatic readiness after a relay join.
- `scripts/test_pk_relay.py`, `scripts/test_mcp_connect.py`, `scripts/test_mcp_connect_weather.py`, and `scripts/test_mcp_stdio.py`: cover seed bounds, start eligibility, scene propagation, default explicit readiness, move-plus-attack categories, `die`/`bounce` validation, and offline weather state.
- `docs/relay_protocol_20261115.md`, `docs/PLAY.md`, and `deploy/relay/requirements.txt`: document the new relay behavior and the optional `websockets` installation.

## Commands run (from the repository root)
- `python3 -B scripts/test_mcp_stdio.py`
  - Last lines: `Ran 27 tests in 1.647s` / `OK`
- `python3 -B scripts/test_mcp_game.py`
  - Last lines: `✅ Start x ranges and determinism Passed!` / `🎉 ALL NEW POSITION / WALL TESTS PASSED!`
- `python3 -B scripts/test_constants_sync.py`
  - Last line: `OK: shared/constants.json matches index.html for all 13 constants and adaptive-level tables.`
- `python3 -B scripts/test_pk_relay.py`
  - Last lines: `Ran 8 tests in 1.468s` / `OK`
- `python3 -B scripts/test_mcp_connect.py`
  - Last lines: `Ran 5 tests in 0.683s` / `OK`
- `python3 -B scripts/test_mcp_connect_weather.py`
  - Last lines: `Ran 1 test in 0.281s` / `OK`
- `git diff --check`
  - Exit status: `0`.

## What I could NOT verify
- The socket tests did run in this environment because the shell allowed local loopback sockets. The owner or main line should still rerun `scripts/test_pk_relay.py`, `scripts/test_mcp_connect.py`, and `scripts/test_mcp_connect_weather.py` in their terminal before accepting this work.
- The required `.kiro/settings/mcp.json` change was blocked by the workspace `kiro-scope` permission rule. It remains unchanged and needs this exact args addition after `"--seat", "white"`: `"--opponent", "builtin:normal"`.
- I did not modify unrelated pre-existing working-tree changes shown by `git status`.
