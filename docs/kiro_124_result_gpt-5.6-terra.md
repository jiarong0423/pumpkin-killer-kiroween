# Task 124 result — MCP health check

Changed: `scripts/pk_mcp_health.py` adds `config_command`, `RpcClient`, and `run`; it validates the configured stdio MCP handshake, tool list, public-state privacy, clean shutdown, and writes the dated evidence log.
Changed: `scripts/test_pk_mcp_health.py` covers the real server, missing executable, invalid-JSON timeout/shutdown path, and home-directory redaction in the log.
H1 observed unchanged: `--from-temp` reports `FAIL initialize server closed stdout`, because the configured relative `scripts/mcp_stdio_server.py` cannot resolve outside the repository; the config was not edited.

Verification run:
`python3 -B scripts/test_pk_mcp_health.py` → `Ran 4 tests in 10.484s` / `OK`
`python3 -B scripts/pk_mcp_health.py` → `ok stdin close` / `PASS`
`python3 -B scripts/pk_mcp_health.py --from-temp` → `FAIL stdin close server exited with status 2` / `FAIL`
`python3 -B scripts/test_mcp_stdio.py` → `Ran 27 tests in 1.169s` / `OK`

Not verified: Kiro IDE GUI startup and its MCP logs were not run; this check verifies the configured command from controlled working directories only.
