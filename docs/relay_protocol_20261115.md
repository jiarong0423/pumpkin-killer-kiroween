# Room relay protocol (draft v0, owner decisions 2026-11-15; trust-based play between friends and agents, not anti-cheat)

Owner decisions this draft follows: everyone brings their own sub-agent or plays by hand; free choice of side, 3 v 3 allowed; the player opens the hosted game page (or scans its QR code), enters an invitation code, joins the room; every device computes the turn state itself; the attacker sends only the button action and the numbers of the flight formula (angle, power, start point; no path); the ATTACKED side's device runs the same fixed-step flight function, does the coordinate hit test and deducts its own HP; the owner's own server (Contabo + Coolify) only serves the page, issues invitation codes and forwards small messages; it never simulates a match.

Compatibility note: the engine formerly accepted 4 units per side; supported team sizes are now 1, 2, and 3 (section 9). Build and test locally; deploy only when the owner says.

## 1. Who does what
| Job | Done by |
|---|---|
| Serve page and assets, issue and match invitation codes, forward messages, number them in order | relay (one small process, rooms in memory, no database) |
| Choose an action, send angle, power, start point and its own computed landing point (a cheap cross-check) | the attacker's device |
| Hit test against its own unit's coordinates and hit box, HP, statuses, shield, reply with the small result | the attacked unit's owner device |
| Turn owner, round number, 12 s timer, wind (from the shared seed), status ticks at round start, game over | every device, from the same ordered message log |
| Pick a seat, go ready | each player |

## 2. Messages (JSON, one per WebSocket text frame, max 16 KB, max 10 per second per seat)
| type | from | content |
|---|---|---|
| `create_room` / `join` | player | invitation code or a request for one; seat choice (`red`, `white`, `spectator`; unit list of at most 3); client version. Only the creator (the host) may optionally include `host_side_choice` as `left`, `right`, or `computer`. |
| `resume` | reconnecting player | the private `seat_token` received in its bootstrap `room_state`, plus the last relay `seq` applied; the relay restores that seat for 60 seconds and replays every later ordered message |
| `room_state` | relay | seats taken, ready flags, shared `seed`, rules version; the private unsequenced bootstrap copy also carries the recipient's `seat`, `seat_id`, `seat_token`, and `last_seq` |
| `ready` | player | marks its seat ready. The room creator may optionally send or replace `host_side_choice` with `left`, `right`, or `computer` before the room starts. Invalid optional values are ignored without an error. |
| `start` | relay | after every present player is ready and each team has a player (or after the one ready player in a `solo: true` practice room): 31-bit non-zero integer `seed`, `scene` (`graveyard`, `church`, `school`, or `belltower`), first team (alternates each round, owner decision 8), and, when the host chose a valid side option, `host_side_choice` resolved to `left` or `right`. For `computer`, the relay stores a separate 31-bit `secrets` coin and resolves it once; it is never derived from the match seed. |
| `action` | seat owner on its turn | `seq`, `round`, `phase`, unit id, `kind` (throw, move, defend, ultimate), `angle`, `power`, `start` (x, y), `claimed_landing` (x, y), optional `die` (move result, integer 1–6), optional `bounce` (knight collision count, integer 1–6); the angle and power stay out of every other seat's PUBLIC view (only the landing and the coarse path are shown, owner decision 9), no `path` in the message |
| `judge` | the attacked unit's owner | `ref` (the action seq), `hit` (true/false), `unit`, `damage`, `hp_after`, `statuses`, `knockback` |
| `end_turn` | seat owner | `round`, `phase` (both required: a replay is ignored) |
| `round_hash` | every device | `round`, hash of its public state; a mismatch is shown to the room as "out of sync" |
| `leave` / `timeout` | any | the seat is released or played by the built-in practice level (the owner can choose) |

## 3. Order and safety rules
1. The relay stamps every message with a growing `seq`; devices apply messages in `seq` order only. A message with an old `round`/`phase` is dropped.
2. One move and one attack per turn. The relay keys each action by seat, round, phase and category: `move` for a move; `attack` for throw, defend or ultimate. It drops a second action in either category, but accepts a move followed by an attack.
3. The relay forwards only its action allowlist. Optional `die` and `bounce` must be integers from 1 to 6; invalid values are rejected with an explicit error. It never reads angle, power or paths for rules; it only checks size, rate, seat and phase.
4. Hidden information: shield position and enemy aim are never in a message to a seat that is not the owner (same views as `view_for(seat)` in the MCP server).
5. If the judge device does not answer within 5 s, the attacker's device shows "waiting for the other side"; after 15 s the room offers to skip the hit or to play the unit by the built-in level.
6. Central wall: its HP is a room fact. The attacker's device announces a wall hit in `action` (with the path point), every device applies it from the log, so it never needs a single owner.
7. The invitation code identifies a room. A random private seat token is issued only to that seat in its unsequenced bootstrap `room_state`; it exists only to reclaim the same seat for up to 60 seconds after a socket loss. The relay keeps the ordered room log in memory for the room life and replays entries after the reconnecting device's last applied `seq`.

## 4. Join flow
1. The player opens the hosted game page or scans the invitation QR code. No download or installation is required; PWA installation remains optional.
2. Host: press "create room", get an invitation code. Friend or agent: enter the code.
3. Host: choose left, right, or computer-decided side in `create_room` or before pressing ready. The relay accepts only those three values from the host and silently ignores an invalid optional value. It resolves `computer` once with a separate stored 31-bit `secrets` coin, then sends the resolved `left` or `right` value in `start` to every device. A host that sends no valid choice receives the existing `start` shape, so older clients retain today's behaviour. Each player then picks a seat or unit list; all press ready.
4. Agents connect through their own local MCP server (stdio, `--seat <side> --connect <relay>` later); the relay is not MCP.

## 5. Open points (need the owner or a test)
- Same physics in every device (owner 2026-11-15: send the numbers, not the path): the page and the .py engine must run ONE fixed-step flight function (fixed time step, seeded wind, no frame-time `dt`, no `Math.random` in the flight) so angle + power + start give the same landing everywhere. The page already steps physics at a fixed `PHYSICS_STEP` (accumulator in the main loop), so the main change left is to make the .py engine and the page use the SAME step and the same formula; remaining differences are tiny floating-point ones (different `Math.cos/sin/exp` implementations, ARM phone against x86 computer), which the 4 px tolerance below absorbs. A golden-vector test (same inputs, same landing in browser and Python, within a pixel) is the proof. If the target's computed landing differs from `claimed_landing` by more than 4 px, show "out of sync" and use the attacker's claimed landing for that hit.
- Both sides alive but disagreeing on a hit: `round_hash` shows it; there is no automatic repair in v0.
- Spectators and reconnect: a late joiner needs the log from `start`; keep the log in the relay memory for the room's life (small).
- 3 v 3: one judge per unit owner; built on 2026-11-17, see section 9 (the relay now carries team size, unit ids and the all-unit round hash).

## 6. Checks added after the web review (2026-11-15; sources in `(not published)`)
1. BOTH devices run the flight function. The attacker's and the target's devices each know whether the throw hits (positions are public). The target's `judge` stays authoritative for HP, but the attacker compares it with its own result; a difference shows "out of sync" for that turn instead of silently diverging.
2. `round_hash` covers: every unit's x, y, hp, alive, statuses; wall HP; round, phase, seed. On a mismatch the relay keeps the last matching round and the first diverging round plus the ordered message log, so the match can be replayed offline as a test.
3. Trust model: client-side hit judgement is the cheapest design and is open to cheating (the target can ignore a hit). It is accepted for friends and agents. If the game is later opened to strangers, add the attacker-side comparison as a hard check and a forfeit rule.
4. Loud failures: an out-of-sync turn is shown to everyone, never hidden.
5. Phones and computers differ in floating point: test the golden vectors on a phone browser and a desktop browser, not only in Node and Python.
6. Load: a handful of rooms (owner decision 12); the per-seat rate limit stays only as abuse protection.

## 7. How the hash is made (owner 2026-11-15: "just compare the hashes")
1. Build ONE canonical text: units sorted by id, each as `id,x,y,hp,alive,statuses` with x and y ROUNDED to whole pixels and hp to 0.1, statuses sorted; then wall HP, round, phase, seed. Rounding first is what stops a 0.0001 floating-point difference between a phone and a computer from raising a false alarm.
2. Hash that text with SHA-256 and send only the first 8 hex characters (32 bits; owner 2026-11-15: a short hash is enough) in `round_hash`, once per round after the last `judge` and status tick.
3. The relay compares the hashes of all seats for the same round. All equal: nothing is shown. A difference: broadcast `out_of_sync` with the round number and keep the log (section 6 item 2). It never tries to repair.
4. A golden test (Python and JavaScript produce the same hash text and the same hash for the same state) lives next to the flight golden vectors.

Why 8 is enough: this is an accidental-divergence check between friends, not a security check; the chance that two different states give the same 8 characters is about 1 in 4.3 billion per round. If the game ever faces strangers, go back to 16 or more.

## 8. What the MCP server does in this design (owner 2026-11-15: "later the MCP just sends the hash for comparison")
The agent's local MCP server stays a thin channel (owner decision 10): it holds no rules the device does not already hold. Its network jobs are only: (1) send the agent's `action` and `end_turn` to the relay, (2) receive the other seats' messages and apply them to the local engine, (3) compute the 8-character `round_hash` after each round and send it, (4) show the result of the comparison to the agent. The six tools stay the same.

`get_public_state.weather` is `{id, label, round, active}`. Offline practice reports `{id: "clear", active: false}` because weather effects are not applied; connected state has `active: true` and uses the selected relay `scene` with the shared match seed.
In connected mode storm adds its signed `windBonus` before the existing unequal tail/head wind flight step.
Connected mode applies the public attack and move multipliers before it reports resolved damage or movement.
`get_public_state.sync` is `{status: pending|ok|out_of_sync, round}`; the relay broadcasts `out_of_sync` when two reported hashes for a round differ.
`end_turn` sends the hash after a resolved round. Connected launch: `python3 -B scripts/mcp_stdio_server.py --seat <side> --connect <relay url> --code <invitation code>`. It waits for an explicit `request_ready()` call; add `--auto-ready` only for a practice client that should join ready. The relay itself is not MCP.

## 9. Team matches, 2 or 3 units per side (2026-11-17)
Rule: **one versus one is byte-identical to the text above.** Every addition below is written only for a room whose team size N is 2 or 3, and a room without `team_size` is N = 1.

### 9.1 Team size and heroes
| Message | New optional field | Rule |
|---|---|---|
| `create_room` | `team_size` (integer 1 to 3, default 1), `units` (this seat's hero ids) | A bad `team_size` (0, 4, 2.0, "2", true, null) gets `error invalid_team_size`; no room is made. |
| `join` | `units` | In a team match a seat may not list more units than N: `invalid_units`. After the match has started, a `red` or `white` join is refused with `error room_started` and no seat is created (spectators and `resume` are unchanged). |
| `ready` | `team_size` (creator only), `units` | Honoured only before the start. A bad value is an explicit error and the seat does NOT become ready (`invalid_team_size`, `invalid_units`; a team's lists together may not exceed N). Non-creator `team_size` is ignored. |
| `room_state` | `team_size` | Present only when N is 2 or 3 (absent means 1). |
| `start` | `team_size`, `heroes`, `owners` | Present only when N is 2 or 3. `heroes` = `{"left": [N ids], "right": [N ids]}` in WORLD frame (red is left, white is right), the seats' `units` lists joined in seat order, `null` where nobody named a hero. `owners` = unit id to seat id. One player seat on a team owns all its units; several seats split them in seat order by list length, but only if every seat sent a list and the lengths add up to N, otherwise that team has no owners entries and any of its seats may act for any of its units. |

### 9.2 Unit ids and what the relay checks
World unit ids: `left_0` to `left_2` for red, `right_0` to `right_2` for white (zero-based, fixed id order = rotation order). The MCP engine's `red_1` to `red_3` / `white_1` to `white_3` map to them one to one: `red_k` is `left_(k-1)`, `white_k` is `right_(k-1)` (`RoundHash.worldUnitId` in JS, `round_hash_py.world_unit_id` in Python). In a team match the wire carries only world ids; in N = 1 the relay still accepts any string, as before.
| Message | Team-match check (error code) |
|---|---|
| `action` | `unit` is `left_i`/`right_i` with i below N (`invalid_unit`); it is on the sender's own side (`unit_not_yours`); if `owners` names it, the sender owns it (`unit_not_yours`); the move and the attack of one turn come from the same unit (`unit_changed_in_turn`). The existing one-move-one-attack rule is unchanged. |
| `judge` | a hit names `unit` (`invalid_unit`); `unit` is on the judge's own side and owned by it (`unit_not_yours`); a second judge for the same `ref` and unit is dropped (`duplicate_judge`: devices apply the log, so a twin would deduct hp twice). One action may get several judges for different units (area effects). |
| `round_hash` | `hash` is exactly 8 lowercase hex characters (`invalid_round_hash`). |
Not checked, on purpose: whose turn it is inside a team (rotation after a throw, timeout or defend is still an open owner decision, TEAM_RULES item 8) and whether a unit is alive (the relay only sees the judge's report). Devices that disagree about either show up in `round_hash`.

### 9.3 Round hash over every unit
The text of section 7 is unchanged; what changes is what goes into it for a team match: ONE row for EVERY unit of BOTH teams, alive or not, a fallen unit stays in with `alive=false` and its hp. Rows are sorted by unit id (plain ASCII order), so `left_0, left_1, left_2, right_0, ...` in every language and every input order. Unit ids are ASCII `[A-Za-z0-9_.:-]` and unique. Inputs for N = 2 or 3: ids `left_i`/`right_i` in world frame, x and y in world frame, `wallHp`, `round` (the round that just finished), `phase` the literal `round_end`, `seed` the match seed; `teamSize` may be passed and is checked (both teams complete, ids exactly `left_0..`), it is not part of the text. A device sends it once per round after the last judge and status tick. N = 1 keeps whatever inputs it has today (the one-versus-one vectors `state-00` to `state-19` are frozen). Golden vectors: `shared/round_hash_golden.json` (`team-1-*`, `team-2-*`, `team-3-*` added; the same file is read by `scripts/test_round_hash.js`, `test_round_hash.py`, `test_round_hash_team.js`, `test_round_hash_team.py`; the JS test also pushes 300 random states through the Python implementation).

### 9.4 What each client must do
Page: `docs/relay_team_page_hooks.md`. MCP bridge (owned by the engine line): map engine ids to world ids at the relay boundary, send the hash with the inputs above, read `start.team_size`, `start.heroes` and `start.owners`.
