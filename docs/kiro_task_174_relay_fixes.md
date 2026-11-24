# Kiro task 174 — relay fixes found by the MCP sweep (Python only: `scripts/pk_relay.py`, `scripts/pk_relay_client.py`, `scripts/mcp_stdio_server.py`, their tests; NO edit to index.html)

Owner 2026-11-16: do all the gaps. Do not run any test that opens a network socket yourself if the shell refuses it; write the tests, and say which ones the owner must run in a terminal (`test_pk_relay.py`, `test_mcp_connect.py`, `test_mcp_connect_weather.py`).

Read first: `docs/relay_protocol_20261115.md`, `docs/mcp_architecture_opus_20261115.md`, `scripts/pk_relay.py`, `scripts/pk_relay_client.py`, `scripts/mcp_stdio_server.py` (the connect mode), `scripts/test_pk_relay.py`, `scripts/test_mcp_connect.py`.

Fix, one commit-sized change each, saving after each:
1. The seed: `pk_relay.py` makes a 64-bit seed with `secrets.randbits(64)`. JavaScript cannot hold it exactly and the page's `matchSeed` is 32-bit. Use `secrets.randbits(31) or 1` (never 0, because the engine treats 0 as unset), and keep it an int in JSON. Update the tests.
2. One action per turn blocks "move then attack": the dedup key is `(seat, round, phase)`. Make the key `(seat, round, phase, category)` with category `move` or `attack` (throw, defend and ultimate are `attack`), so a seat may send one move and one attack per turn, never two of the same category. Keep the 16 KB size, the rate limit and the old-round drop.
3. Whitelist: the relay forwards only listed fields of an action; add `die` (the dice step the mover rolled, integer 1 to 6) and `bounce` (the knight's collision count, integer 1 to 6), validated as integers in range, rejected otherwise with a loud error message.
4. Start condition: the relay starts when every PRESENT player is ready, so one early player starts alone and the later seat never gets `start`. Require at least one player on each team (red and white) to be present and ready, unless the room was created with `solo: true` (practice against the built-in opponent). In `mcp_stdio_server.py` stop auto-ready on the first `room_state`; ready only when asked or when `--auto-ready` is passed.
5. Scene: the `start` message carries `scene` (the page's scene id: graveyard, church, school, belltower); `mcp_stdio_server.py` uses it instead of the fixed "graveyard" (line near 346).
6. Offline public state: when not connected, `get_public_state` must not claim weather effects that are not applied; report weather id `clear` with `active: false`.
7. `.kiro/settings/mcp.json`: add `--opponent builtin:normal` to the args so a single Kiro client does not wait 12 s for a missing red player every turn.
8. Add `deploy/relay/requirements.txt` note and a `PLAY.md` line `pip install websockets` for the download package (the file may live under `scripts/release/` or `docs/`; search `PLAY.md`).
9. Tests: update `scripts/test_pk_relay.py` and the connect tests for items 1 to 5 (seed range, two actions per turn, `die` and `bounce`, start rules, scene). Run the Python tests that do not need a socket and paste the last lines; list the socket tests the owner must run.

Touch only the files named above, `.kiro/settings/mcp.json`, the PLAY.md found, and `docs/relay_protocol_20261115.md` (update sections 2, 3 and 8 to match). Final message: files changed, which tests ran, which the owner must run.
