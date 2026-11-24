# Cross-device play: tasks

Starts after `ui-polish` and `seats-and-items` are verified (one writer for `index.html`).

- [x] 1. `scripts/measure_join_time.py` and `docs/join_time_20261116.md` (R1.3) | the script runs headless
- [x] 2. `js/relay_client.js` with an injectable socket, message order, token, log replay (R2.1, R3.1) | `scripts/test_relay_client.js` with a fake socket
- [x] 3. Join flow on the start screen: create room, code, QR code (offline QR generator, no network library), join by link, AI on an open seat (R1.1, R1.2) | `scripts/test_join_flow.js`
- [x] 4. Round hash exchange and the out-of-sync message (R2.2) | `scripts/test_relay_client.js`
- [x] 5. Reconnect (R3) | `scripts/test_relay_reconnect.py`
- [ ] 6. Rename leftovers: page title, manifest, comments that ship (R5) | `(not published)` greps the shipped files for the banned words
