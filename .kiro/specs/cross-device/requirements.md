# Cross-device play: requirements

Scope: the page's relay client (`js/relay_client.js`, new), the start screen join flow, `scripts/pk_relay.py` (already running locally), the measurement script. Terms: **seat** is a side of a match; **code** is the invitation code; **join time** is the time from opening the join link to the first throw being possible.

## R1 Join
1. The host shall be able to create a room from the start screen and see the code and a QR code of the join link (`?room=<code>`); a friend who opens the link on any device joins the open seat without installing anything.
2. The host shall be able to put the built-in AI on an open seat with one tap; a match always has at least one human seat.
3. The join time shall be measured by `scripts/measure_join_time.py` (headless: relay plus two scripted clients) and the median of 20 runs written to `docs/join_time_20261116.md`.

## R2 Same match on both screens
1. The attacker's device sends only the numbers (angle, power, start point, dice and bounce counts); the other device runs the same flight function and applies the result (`docs/relay_protocol_20261115.md`).
2. After every round both devices send the 8-character round hash; a mismatch is shown to both players as "out of sync" and never hidden.
3. The turn timer is the same on both devices, driven by the relay's message order, not by the local clock alone.

## R3 Reconnect
1. If a device loses the connection (app switched away, network drop) it shall reconnect with the same seat token within 60 s and receive the ordered message log from the start, rebuild the state, and continue.
2. During the gap the other player sees "waiting for the other side"; after 15 s they may choose to let the built-in AI play that seat.
3. A reconnect test (`scripts/test_relay_reconnect.py`) shall drop one scripted client mid-match, reconnect it, and assert that the final round hashes of both clients are equal.

## R4 Touch
1. Aim angle and power shall be settable by one finger drag on a phone; a quick tap cancels (already implemented); targets are at least 44 px.
2. The game works on the latest Safari (iOS), Chrome (Android) and the desktop browsers; the list of tested devices goes into the submission text.

## R5 Naming and sources
1. No original game name, character or picture of the older Flash-era games appears in the page title, manifest, texts, comments that ship, or images; the story line is "inspired by Flash-era artillery games".
