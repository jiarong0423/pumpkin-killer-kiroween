# deepseek review (model deepseek-ai/DeepSeek-V4-Pro-0813, 2026-11-26 05:27)

## Defects

1. **P2** `pk_relay.py:_round_hash` — Spectators can send `round_hash`; it is stored under their `seat_id`, broadcast, and can trigger `out_of_sync`. Trigger: spectator joins started room, sends `{"type":"round_hash","round":1,"hash":"00000000"}`. Fix: reject unless `entry["team"] in ("red","white")`.

2. **P2** `pk_relay.py:_join` — In team matches, `claim = min(max(raw or 0, len(units)), free)` can leave `claim > len(units)` (e.g. `claim=3`, `units=["skeleton"]`). `places_locked()` then fails forever because `len(units) < claim`; seat cannot ready. Fix: after computing `claim`, set `claim = min(claim, len(units))` or reject `raw > len(units)`.

3. **P2** `pk_relay.py:_dispatch resume` — When `self.seat_grace_seconds <= 0` (grace disabled), the lazy expiration check still uses `SEAT_GRACE_SECONDS` (60 s), so a disconnected seat can be expired even though the sweeper is disabled. Fix: if `self.seat_grace_seconds <= 0`, skip the time check entirely.

4. **P2** `pk_relay.py:_dispatch join` / `note_connect_attempt` — Rate-limit checks use `>` after appending, allowing one extra attempt beyond the configured limit (e.g. 21 wrong codes before block). Fix: change to `>=` before append.

5. **P2** `pk_relay.py:_round_hash` — `mismatch_key = (round_number, tuple(sorted(hashes)))` uses only seat IDs, not hash values. After the first mismatch for a set of seats, later different hash values with the same seats are not reported. Fix: include `tuple(sorted(hashes.values()))` in the key.

## Known open items

- **1v1 multi-device**: `_join` only limits `room.lobby and not room.team_match`; apply the same one-seat-per-side rule to all 1v1 rooms.
- **Unicode name diff**: client JS uses `\p{C}` etc. with the browser’s Unicode version; Python uses its own. Rely on relay-cleaned name for display, or pin both to the same Unicode version.
- **MCP agent no repick reminder**: `_sweep_agents` auto-locks after `agent_pick_seconds` but sends no UI event. Add `agent_pick_deadline` to `room_state` for agent seats.
- **Coolify trust proxy**: `_addr` uses peer address unless `TRUST_PROXY=1`; behind tunnel peer is `127.0.0.1`. Set the env var or default to trusting `CF-Connecting-IP` when present.
- **Human+MCP no evidence**: not a code defect; run a live 2v2 with one MCP agent and observe.

## Change suggestions

1. Clamp `claim` to `len(units)` in `_join` (defect 2).
2. Add team check in `_round_hash` (defect 1).
3. Use `>=` for all rate-limit checks (defect 4).
4. Include hash values in `mismatch_key` (defect 5).
5. Skip resume expiration when `seat_grace_seconds <= 0` (defect 3).
6. In `relay_client.js:receive`, clear `buffered` on `lobby_reset` to avoid stale ordered messages.
7. In `_sweep_agents`, avoid duplicate hero fallback by cycling `HERO_IDS` instead of always `HERO_IDS[0]`.
8. In `_move`, if a host switches team, also release AI fillers tied to the old host seat.
