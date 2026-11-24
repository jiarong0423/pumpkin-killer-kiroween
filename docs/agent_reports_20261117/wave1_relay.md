# Wave 1 relay report (2026-11-17, networking)

## Protocol changes (docs/relay_protocol_20261115.md section 9; page work in docs/relay_team_page_hooks.md)
- One versus one is byte-identical: every new key exists only when N is 2 or 3 (a room without `team_size` is N = 1). Tests pin the exact N = 1 `start` key set and the client's N = 1 wire strings.
- `create_room` / `ready` (creator only) carry `team_size` 1..3; `create_room` / `join` / `ready` carry `units` (hero ids). Bad values give an explicit error and the seat does not become ready. `room_state` and `start` carry `team_size`; `start` also `heroes` {left, right} (null for unnamed slots) and `owners` (unit id to seat id).
- Action unit ids are world ids `left_0..left_2` / `right_0..right_2`; in N >= 2 the relay checks: format and index below N (`invalid_unit`), the sender's own side and owner (`unit_not_yours`), same unit for the move and the attack of one turn (`unit_changed_in_turn`). Judge: a hit names a unit of the judge's side, one judge per (ref, unit) (`duplicate_judge`), several units per action allowed. Round hash: 8 lowercase hex in team matches.
- Not enforced on purpose: whose turn inside a team and whether a unit is alive (not cheap or safe: rotation after timeout/defend is still undecided, TEAM_RULES item 8).

## Hash design
- Canonical text of protocol section 7 is unchanged; rows are now sorted explicitly by id (ASCII only, unique), `teamSize` (optional) is checked (both teams complete, ids exactly `left_0..`), not hashed. New helpers `RoundHash.worldUnitId/unitIds` and `world_unit_id/unit_ids` (MCP `red_k`/`white_k` to `left_(k-1)`/`right_(k-1)`). Team inputs: world ids, `phase: "round_end"`, match seed, once per round after the last judge and status tick.
- `shared/round_hash_golden.json` grew from 20 to 33 cases (team-1/2/3-*, shuffled input order, a fallen unit); the first 20 are byte-identical to before (`state-00` still `696f9f69`).

## Tests run here (last lines)
- `node scripts/test_round_hash_team.js`: `cross-runtime fuzz: 300 states identical in JS and Python` / `PASS: team round hash (13 vectors for N=1..3; ...)`
- `python3 -B scripts/test_round_hash_team.py` and `test_round_hash.py`: `PASS: team round hash (13 vectors ...)`, `PASS: 33 round-hash goldens; ...`; `node scripts/test_round_hash.js` same.
- `node scripts/test_relay_client_team.js`: `relay client team options, hero lists and unit ids: ok`; `test_relay_client.js`, `test_perspective.js` still ok.
- `python3 -B -m unittest test_pk_relay.RelayTeamLogicTests` (13 socket-free tests, incl. 2 v 2 and 3 v 3 five-round match with both devices hashing, in-process relay): `Ran 13 tests ... OK`.
- All 54 `node scripts/test_*.js`: 53 pass; `test_start_screen_fit.js` fails with `connect EPERM` (sandbox). All `test_*.py`: 47 pass (incl. mcp_game, mcp_seats, mcp_stdio, mcp_units, determinism). Failing here, none from my files: socket tests (`test_pk_relay` 14 socket tests, `test_relay_reconnect`, `test_e2e_local`, `test_mcp_connect*`, `test_smoke_*`), `test_bedrock_backend` (PermissionError), `test_fonts` (characters 提賽較隊 missing, page text changed by someone else).

## Needs the main line
- `test_pwa_files.py` reports `STALE sw precache` (not checked whether it was stale before my edits; other lines also changed files today): `js/relay_client.js`, `js/round_hash.js` and `shared/round_hash_golden.json` are in the precache and I changed them. Regenerate `sw.js` (scripts/make_sw_precache.py) after the page hooks are applied; I do not own `sw.js`.

## Owner terminal (socket tests written, not runnable here: bind refused)
```
cd <repo>
python3 -B scripts/test_pk_relay.py          # 12 old tests + 2 new socket tests (test_team_start_carries_size_heroes_and_owners, test_one_versus_one_start_is_unchanged_on_the_wire) + 13 logic tests = 27
python3 -B scripts/test_relay_reconnect.py   # expects both: "relay reconnect ordered log: ok" and "relay reconnect team match (3 v 3 unit ids replayed): ok"
python3 -B scripts/e2e_local.py              # MCP 1 v 1 as before, then 2 v 2 and 3 v 3 over real sockets (about 25 s each)
python3 -B scripts/test_e2e_local.py         # unchanged MCP 1 v 1 check
```

## Could not decide / risks
- Page is not a full relay peer today: it never sends `ready`, `judge` or `end_turn` and does not apply remote `action`/`judge` (hooks doc items 1, 5, 7). Team play from the page needs those first.
- Pre-existing, untouched: page and MCP bridge hash different inputs at N = 1 (ids `left`/`right` against `red_1`, phase `throws:...` against the relay team, seed), so a page + MCP room reports out_of_sync. The team recipe fixes it for N >= 2 only if the MCP line adopts it; moving N = 1 too would change the frozen one-versus-one hash, owner's call.
- Several seats per team: relay supports owner splits by list length; the page hook says refuse for now.
- `scripts/pk_relay_client.py` (not mine) cannot send `team_size`; tests use raw sockets.
- MCP line must map engine ids with `world_unit_id` at the relay boundary; the relay does not translate.
