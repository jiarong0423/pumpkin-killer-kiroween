# Kiro task 149 result

Changed `scripts/pk_relay.py` (`RelayServer`, `Room`) and `scripts/pk_relay_client.py` (`RelayClient`) for the in-memory WebSocket relay and headless client.
Added real-localhost integration coverage in `scripts/test_pk_relay.py` and pinned non-root container files in `deploy/relay/`.
Verification command run: `python3 -B scripts/test_pk_relay.py`
Last output lines:
```text
----------------------------------------------------------------------
Ran 5 tests in 1.248s

OK
```
Could not verify a Docker build or deployment; deployment remains the owner's task.
Several earlier per-save static-check commands were refused before approval; the required final test ran successfully.
