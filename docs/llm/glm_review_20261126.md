# glm review (model zai-org/GLM-5.3, 2026-11-26 05:26)

# Code review: multiplayer room layer

## 1. Confident defects

**P1 — MCP client cannot create a lobby room** — `pk_relay.py`, `create_room` handler + `_join`.
`create_room` with `lobby: true` sets `room.allow_mcp = False` *before* the creator's own `_join` runs; `_join` then rejects any non-spectator with `client_kind == "mcp"` (or a `mcp:` address) with `mcp_disabled`, and the fresh room is deleted.
Trigger: `create_room {lobby:true, seat:"red", client_kind:"mcp"}` → error `mcp_disabled`, room gone.
Fix (small): skip the mcp gate when `message.get("type") == "create_room"` (the creator is the host and can re-enable agents), or default `allow_mcp = True` in lobby rooms and let `room_options` turn it off.

**P1 — bootstrap errors on the initial socket leave the client stuck in `connecting`** — `relay_client.js`, `attachSocket`/`receive`.
`awaitingAnswer` is set only when the bootstrap is re-sent on a *reconnect* socket (`if (isReconnect) awaitingAnswer = true`). On the first socket an error reply (e.g. `server_busy` when `MAX_ROOMS` is reached, or `invalid_scene`) falls through to the no-seq branch: it is merely notified, the socket stays open, no reconnect and no `closed` status — and `server_busy` is in `TRANSIENT_ERRORS` but is never acted on.
Trigger: fill the relay to `max_rooms`, open a fresh lobby page, press "Play with friends" → one toast, client zombie.
Fix: set `awaitingAnswer = true` whenever `bootstrapMsg` is written (initial too); the existing error path then reconnects transient errors and closes permanent ones.

**P2 — a broadcast `room_state` clears `out_of_sync`** — `relay_client.js`, `updateFromRoomState`.
Any room_state sets `waiting`/`playing`. Sequence: a `round_hash` mismatch sets `out_of_sync`; the next seat join/leave broadcasts a room_state → status silently back to `waiting`. Fix: in `setStatus` (or `updateFromRoomState`) never downgrade from `out_of_sync`.

**P2 — `ackEcho` can ack the wrong entry** — `relay_client.js`, `ackEcho`.
It matches the *first* unacked entry of the same `kind`, ignoring round/phase. With an `end_turn` for round N and another for N+1 both unacked, the echo for N removes N+1's entry, which is then never resent after a drop. Fix: compare `message.round`/`message.phase` (stored in the entry) as well.

**P2 — `_invite` note filter is dead code for newlines** — `pk_relay.py`, `_invite`.
The category filter deliberately keeps `\n`/`\t`, but the following `" ".join(...split())` collapses all whitespace anyway, so multi-line notes are silently flattened and the exception misleads. Fix: drop the `\n\t` exception, or split on `" "` only.

**P2 — a 1v1 agent can be auto-locked with no hero** — `pk_relay.py`, `_sweep_agents`.
The fallback hero is assigned only `if room.team_match and not seat["units"]`. In a 1v1 room an agent that never picks is set `ready = True` with `units == []`, and `places_locked` (= `places_taken` there) lets the match start with an agent that named nothing. Fix: give non-team-match agents a fallback hero too (or hold the start until it picks).

## 2. Debugging the known open items

- **Multi-device 1v1 in old rooms**: root cause is the gate in `_join`: `room.lobby and not room.team_match and room.team_count(team) >= 1` — only lobby rooms are capped. Fix: drop the `room.lobby` term once old clients are gone (it is a one-token change, currently deliberate).
- **Name rules diverge on very new Unicode**: Python `unicodedata` (version of the relay's Python build) vs the browser's Unicode tables disagree on newly assigned codepoints (Cn in one, letter in the other). The relay already re-cleans and is authoritative; fix is to pin the divergence in `scripts/name_vectors.json` and document "relay wins", not to chase parity.
- **MCP agent not reminded after returning to lobby**: `reset_lobby` resets `joined_at` (fresh 30 s) but sends only a generic `lobby_reset`. Fix: on reset, re-send the agent seat's `briefing` (the `_send_state` path already includes it pre-start) or a small `pick_again` note.
- **Settings page has no rename**: the lobby already has the `askName` + `relayClient.setName` path; reuse it — no new API needed.
- **Old friends panel DOM**: dead code kept for `?room=` links; gate its wiring on that query param and delete the rest.
- **Coolify without `PK_RELAY_TRUST_PROXY=1`**: `_addr` returns `127.0.0.1` for every browser, so `MAX_CONNECTIONS_PER_ADDR = 8` caps the whole site. Fix: set the env var (and forward `CF-Connecting-IP`) in Coolify; until then raise `PK_RELAY_MAX_PER_ADDR`.
- **No human+MCP full-match evidence**: add a scripted MCP seat (join via `invite` ticket, play `action`/`judge`/`end_turn`/`round_hash` for 3 rounds against a scripted human) as a smoke test next to `relay_load_probe.py`.

## 3. Change suggestions (most valuable first)

1. In `lobbyOnState`, set `relaySeatId = m.seat_id` from every private room_state — `_move` changes the seat id on a side switch and the relay re-sends it; one line keeps "mine", host and lock working (verify `connectRelay` does this today).
2. Give `unacked` entries round/phase and match them in `ackEcho` (fixes defect 4 generally).
3. Don't `stamp` the `countdown` broadcasts into the log (treat them like `room_state`), so a replay after resume cannot resurrect a stale timer in `lobbyOnMessage`.
4. In `_dispatch`'s `kick` else-branch (grace-period target), broadcast the same `seat_left`/state sequence `_expire_seat` uses, so a kicked disconnected seat is announced identically.
5. `LobbyModel.view`'s `count.seated` counts agent places like people; exclude `agent` as `ai` is excluded, so "n/6" means humans.
6. Add a regression test for the create-room-by-MCP sequence once defect 1 is fixed.
7. `_error`'s one-line-per-second throttle could also include the remote address at `DEBUG` level to make the FLOOD-1 blocks diagnosable.

Otherwise: none — the seat/place accounting (`held_places`, `places_locked`, `_check_team_units`) and the reconnect/unacked machinery are consistent between relay and client as far as I could trace.
