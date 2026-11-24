# Page hooks for team matches over the relay (2026-11-17)

For the main line, to apply to `index.html` in one pass. Protocol: `docs/relay_protocol_20261115.md` section 9. Line numbers are those of `index.html` on 2026-11-17 and will drift; the function names are the anchors. With N = 1 (`TEAM_N === 1`) every change below must leave the wire exactly as today.

Already done and tested outside the page (no page change needed): `js/relay_client.js` (`createRoom(options)`, `join(code, seat, options)`, `sendReady(options)`, team-aware `sendAction`/`sendJudge`/`sendRoundHash`, `state().teamSize|heroes|owners`, `RelayClient.isTeamUnitId`), `js/round_hash.js` (`teamSize` check, id sort, `worldUnitId`, `unitIds`), and the relay.

Facts found in the page today (so the list below is complete): `relayClient` is used only for `createRoom`, `join`, `sendAction`, `sendRoundHash`, `state`, `setPerspective`. The page never sends `ready`, `judge` or `end_turn`, and the `onMessage` handler (`connectRelay`) handles only `room_state` and `start`; remote `action` and `judge` messages are not applied. Items 1, 5 and 7 are therefore needed for ANY room to be played from the page; items 2, 3, 4 and 6 are what team matches add.

## 1. Create, join, ready (`buildRoomControls`, `startMatch`, `connectRelay`)
- `room-create` click: `client.createRoom({ teamSize: TEAM_N, units: ownHeroIds() })`; remember `isRoomHost = true`. `ownHeroIds()` = `unitsOf("left").map(u => u.profile)` (one hero id string per unit, the per-unit pick of step 5; until then the picked hero repeated).
- `room-join` click and the `?room=` auto-join: call `client.join(code, "white")` WITHOUT `units` (the joiner does not know N yet; a list longer than N is refused with `invalid_units`). The hero list goes in `ready`.
- `connectRelay` `onMessage`, `room_state` branch: `const n = message.team_size || 1;` (the relay omits the key for N = 1). If `n !== TEAM_N` the joiner must adopt it: `localStorage.setItem("pk_team_n", n)` and reload with `?team=n&room=<code>` (same code as the team-size button handler; `TEAM_N` is a const fixed at load, so a reload is the only way). A reload cannot loop: after it `TEAM_N === n`. Also store `relaySeatId = message.seat_id` when present.
- `startMatch`, when `relayClient && relayRoomCode`: `relayClient.sendReady(isRoomHost ? { teamSize: TEAM_N, units: ownHeroIds() } : { units: ownHeroIds() })`. Only the creator's `teamSize` counts; do not send it from a joiner. A bad value comes back as `error` (`invalid_team_size`, `invalid_units`) and the seat is NOT ready: show it (item 6).
- `connectRelay` `onMessage`, `start` branch (today it only sets `matchSeed`): add
  `const n = message.team_size || 1; if (n !== TEAM_N) { /* refuse: show a line, do not start */ }`
  `const st = relayClient.state(); relayHeroes = st.heroes; relayOwners = st.owners;`
  `st.heroes` is already in the page's frame (`heroes.left` is the page's own team, `heroes.right` the opponent) with `null` for a slot nobody named; use it for the per-unit hero setup of step 5 (`null` = keep the default hero).

## 2. How seats map to units
Seat `red` is world `left`, seat `white` is world `right` (`relaySeatPerspective`, unchanged). The page always sees its own team as local `left`; `relayClient` flips side and x on the way in and out (`Perspective.unitId` keeps the index, so local `left_1` becomes world `right_1` on the white seat). A page seat controls ALL units of its local `left` team (one seat per team is the normal case: a human, or an MCP agent). When a team has several seats, `state().owners` (local frame, unit id to seat id) says who owns which unit; first version: if `owners` holds more than one seat id for either team, show "one seat per team" and do not start. Do not build the split until the owner asks.

## 3. Unit id in actions (`broadcastLocalAction` callers)
- `stepDice`, the move: replace `unit: localSide + "_0"` with `unit: u.id` (`u` is the moving unit; its `id` is `left_k` / `right_k`, local frame).
- `executeThrow`, the throw: replace `unit: localSide + "_0"` with `unit: u.id` (`u` is `thrower || active unit`, so a double shot's second shell still names the unit that fired).
- `broadcastSmartAiThrow`: `unit: TEAM_N > 1 ? ai.id : "right"` (N = 1 stays `"right"`, as today).
For N = 1, `u.id` is `left_0` / `right_0`, equal to what `localSide + "_0"` gives, so the wire does not change. The move and the throw of one turn must name the same unit (`unit_changed_in_turn`): the rotation happens in `rotateAfterTurn` after the throw, so the active unit is stable during the turn. If the owner later lets the player pick the unit (TEAM_RULES item 8), the pick must happen before the move.

## 4. Round hash (`currentRoundHash`, `broadcastCurrentRoundHash`, `resolveRound`)
- `currentRoundHash`: keep the existing body for `TEAM_N === 1`. For `TEAM_N > 1` return
```js
RoundHash.hash({
  teamSize: TEAM_N,
  units: allUnits().map(u => ({ id: localPerspective.worldUnitId(u.id), x: localPerspective.x(u.x), y: u.y,
    hp: u.hp, alive: u.hp > 0, statuses: publicStatusWords(u) })),
  wallHp, round: roundNum, phase: "round_end", seed: matchSeed
})
```
  `allUnits()` already lists every unit of both teams including fallen ones (they stay in the hash with `alive: false`); never filter it. `worldUnitId` maps local ids to world ids (`left_1` to `right_1` on the white seat); `localPerspective.x` mirrors x for the white seat.
- Moment: once per round, after the last judge and the status ticks. In `resolveRound`, immediately BEFORE `roundNum++` (after the `allUnits().forEach(... tickPoison ...)` line) call `if (TEAM_N > 1) broadcastCurrentRoundHash();` so `roundNum` is the round that just finished. In `advanceAfterAttack` change `broadcastCurrentRoundHash();` to `if (TEAM_N === 1) broadcastCurrentRoundHash();` (N = 1 keeps its after-each-attack hash).
- `relayClient.sendRoundHash` already refuses anything but 8 lowercase hex for N >= 2.
- The MCP bridge must use the same inputs (ids `left_i`/`right_i` through `round_hash_py.world_unit_id`, `teamSize`, `phase: "round_end"`, the match seed, world x). Rooms that mix the page and an MCP seat at N = 1 already hash different inputs today (page: ids `left`/`right`, phase `throws:...`; MCP: `red_1`, relay team, engine seed); I did not change N = 1.

## 5. Applying remote messages (not in the page yet)
When the handler for remote `action` is written (messages arrive in the page's local frame, `unit` already local):
- attacker = the unit in `teams` whose `id === message.unit`; run the shared flight function with `message.angle`, `power`, `start`, `dirX`; compare with `claimed_landing` within 4 px.
- Judge only OWN units (the local `left` team): the first living unit the shot touches (TEAM_RULES item 4) gets `relayClient.sendJudge({ ref: message.seq, hit: true, unit: hit.id, damage, hp_after, statuses, knockback })`; an area effect sends one judge per own unit it hits (never two for the same unit and `ref`); a miss is `sendJudge({ ref: message.seq, hit: false })`. `sendJudge` throws if a hit has no unit id.
- Apply a received `judge` with `message.unit` (local frame) to that unit's hp; do not apply your own judge twice (it comes back through the ordered log).
- The sender learns its action's `seq` from the private `action_ack` (`message.seq`, no unit); the judge's `ref` is that `seq`.

## 6. Errors to show (`onMessage`, `message.type === "error"`; ignored today)
`invalid_team_size`, `invalid_units`, `invalid_unit`, `unit_not_yours`, `unit_changed_in_turn`, `duplicate_judge`, `invalid_round_hash`: log with `console.warn("relay", message.code, message.message)` and show one plain line from the i18n table (e.g. `relay.error`). Protocol section 6 item 4: failures are loud, never hidden. `out_of_sync` already sets `state().status === "out_of_sync"`; show it to the player.

## 7. `end_turn`
The page does not send `end_turn` today, so the relay's phase never advances from a page seat. Wire `relayClient.endTurn(relayState.round, relayState.phase)` where a turn ends (`rotateAfterTurn`, timeout, defend, skip) before any room can play more than one turn.

## Checks after applying
`node scripts/test_relay_client_team.js`, `node scripts/test_round_hash_team.js`, `node scripts/record_match_transcript.mjs` must still match `docs/transcripts/n1_baseline.json` (N = 1 unchanged), and in the owner's terminal `python3 -B scripts/test_pk_relay.py`, `python3 -B scripts/test_relay_reconnect.py`, `python3 -B scripts/e2e_local.py`.
