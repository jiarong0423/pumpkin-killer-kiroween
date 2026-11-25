# glm review (model zai-org/GLM-5.3, 2026-11-26 05:21)

# Code review — multiplayer room layer

## 1. Defects I am confident about

- **P0 — none.**

- **P1 — `pk_relay.py` `_round_hash`: any spectator can force a false `out_of_sync` for the whole room.** It checks `room.started` but never the sender's team, unlike `_action`/`_judge`. Sequence: join with `seat:"spectator"` (allowed in a started room), send `{"type":"round_hash","round":1,"hash":"deadbeef"}`; the digest is stored under `spectator-1`, `distinct > 1`, and the `out_of_sync` broadcast puts every client into the desync state (`relay_client.js` `applyMessage` → `setStatus('out_of_sync')`). Smallest fix: add `entry["team"] not in ("red", "white")` to the first validation (optionally also ignore `round < room.round`, which lets a player poison old rounds late).

- **P2 — `pk_relay.py` `_reap_idle_rooms`/`_handle_socket`: a quiet but live lobby is closed as idle.** `last_seen` is stamped only when a message *arrives*; the lobby page sends nothing while waiting (no heartbeat), so after `ROOM_IDLE_SECONDS` (30 min) the relay closes a fully occupied lobby with 1001 "room idle" (resume then gets `unknown_token`). User action: create a lobby, leave the tab open half an hour waiting for a friend. Fix: in `_reap_idle_rooms` also require `not room.clients` — the library's keepalive pings already cull dead sockets and `_expire_seat` deletes the empty room (alternative: a small client keepalive).

- **P2 — `pk_relay.py` `ready` (in `_dispatch`) vs `places_locked`: a "ready" seat can block the start with no visible cause.** `ready` accepts fewer `units` than the seat's `claim`, or none at all (claim 0). Then `all_players_ready()` is true but `places_locked()` stays false (`len(units) < claim` / `not seat["units"]`), so with `begin` pressed the countdown never fires while `LobbyModel.view` shows everyone locked, an empty `waiting` list — a zero-place seat is not even rendered. Trigger: a raw/old client joins a 3v3 without `claim`/`units`, then sends `{"type":"ready"}` (the page always sends claim-many units in `lobby-lock`). Fix: on the `ready` path, require a team-match player seat to list at least `max(claim, 1)` units, else `invalid_units`.

- **P2 — `relay_client.js` `receive`: early resend when a broadcast state overtakes the resume bootstrap.** Any unsequenced `room_state` while `awaitingAnswer` sets `resendAt`, but a broadcast state has no `last_seq`, so `resendAt = lastSeq` (stale) and `maybeResend()` fires before the relay's `_replay` is applied. In `resume`, another task's `_broadcast_state` can reach this socket between `room.clients[websocket] = entry` and `_send_state` (rare, but real). Result: duplicate `action`/`end_turn` → spurious `action_already_submitted` / `stale_or_out_of_turn`. Fix: set `resendAt` only when `typeof message.last_seq === 'number'`.

- **P2 — `pk_relay.py` `_origin_allowed`: prefix match accepts attacker domains.** With no `PK_RELAY_ORIGINS`, `startswith("http://localhost")` also passes `http://localhost.evil.com` (and `127.0.0.1.evil.com`), so a page served from such a domain may open the local relay. Fix: parse the origin and compare host exactly (`localhost` / `127.0.0.1`, any port).

## 2. Known open items — most likely root cause and fix

- **Old 1v1 rooms, several devices per side:** the one-seat-per-side guard in `_join` is gated `room.lobby and not room.team_match`; only lobby rooms get it. Fix: drop `room.lobby and` (relay-v0 multi-device clients then get `team_full`; gate on `client_version` if they must keep working).
- **Name rules differ on very new Unicode:** `clean_name` reads the Python interpreter's Unicode table, `cleanName` the browser's ICU; code points assigned after the older table are `Cn` to one side and letters to the other. Fix: keep the relay authoritative (the page already renders `seats[].name` from `room_state`), label the `askName` preview as approximate, extend `name_vectors.json` on Python upgrades.
- **Agent not reminded to re-pick after a match:** the pick notice (`_brief
