# ADR: per-unit seats with a chosen filler (2026-11-24, owner signed off in chat; code staged, see the ledger)

## Goal (owner, 2026-11-24, in the owner's words reduced to rules)
A room has 6 unit slots (red 3, white 3 in a 3v3; fewer in 1v1 and 2v2).
1. Humans may claim any number of slots, from 1 to all of them.
2. A claimed slot is never touched by a computer or an agent.
3. Every unclaimed slot is filled automatically by ONE chosen filler: the fixed computer (the built-in rule AI) or a sub-agent (an MCP seat). The choice is per room.
4. When every slot is claimed by humans, no filler runs.

## Remainder rule (owner, 2026-11-24: "seats are all independent, so the remainder is loaded by subtraction")
- Every seat is independent: it names only its own units and knows nothing about any other seat.
- The filler is not a side or a mode. It is one more independent seat that is computed last: for each team, `remainder = team size - (units claimed by all other seats of that team)`.
- The filler joins that team with exactly that many units, so the relay's own check ("every seat sent a list and the lengths add up to the team size") passes by construction and `owners` is written with no change to the relay.
- Order (owner, 2026-11-24: "the fill is computed last; the computer assigns the vacancies of the two teams at random"): (1) humans claim, (2) subtract per team to get each team's vacancies, (3) last, the computer assigns the vacancies at random. The random draw must come from the room seed (or be made once and carried in the `start` message's `heroes`), never from `Math.random` on each page, or the pages will disagree and the round hash will differ.
- A team with remainder 0 gets no filler. 6 human claims in a 3v3 therefore start no filler at all.
- The remainder is computed once, when the host presses Start (after every human seat has sent its list), not earlier; a human seat that leaves before Start only changes the subtraction.

## Cap (owner, 2026-11-24: "assume the cap is 6")
- At most 6 unit slots in a room (3 per team), so at most 6 independent seats can each own one unit (human seats and the filler seat together; spectators are not seats).
- The relay already fits this: it allows up to 4 seats per team (`MAX_TEAM_SEATS = 4`, `scripts/pk_relay.py` line 25) and a team of 3 units never needs more than 3. No relay change for the cap.
- Claims beyond the cap are refused by the existing checks (`invalid_units` when a list is longer than the team size, `team_full` when a team already has 4 seats). The slot picker must not offer a seventh slot.

## Facts that decide this (read from the code, 2026-11-24)
| Fact | Where |
|---|---|
| The relay already lets several seats share a team and splits the unit ids in seat order by the length of each seat's unit list; if every seat sent a list and the lengths add up to the team size it writes `owners` (unit id to seat id). | `scripts/pk_relay.py` lines 134-156, `docs/relay_protocol_20261115.md` section 9.1 |
| The relay rejects an action from a seat that does not own the unit (`unit_not_yours`). | `scripts/pk_relay.py` line 639 |
| The relay client already stores `owners` in the match snapshot. The page never reads it. | `js/relay_client.js` lines 105-118, 213-228; no `owners` in `index.html` |
| The page treats one side as one occupant: `seats = { left: "human" or "ai", right: "human" or "ai" or "agent" }`. One human seat controls the whole local team and sends the full unit list on ready. | `index.html` lines 1032, 1565-1569 |
| A computer (`ai`) side plays inside the page, not in a room; agents and headless seats join a room through the relay. | `index.html` lines 1332-1334; `scripts/hybrid_seat_headless.js` |

So the wire already supports the goal. The page does not: it cannot own one unit of a team and wait for a teammate seat for the others.

## Options
| | Idea | Cost | Risk |
|---|---|---|---|
| A (recommended) | Page learns per-unit ownership. The seat that owns a unit plays it; units owned by another seat are applied from the relay like enemy units are today. Filler is a headless seat started by the room host's machine side (agent: the MCP seat; fixed computer: `hybrid_seat_headless.js`, the page's own AI) that joins with a unit list for the empty slots. | Page: turn order and local-versus-remote unit handling; room UI: a slot picker. Relay: nothing. | Round-hash agreement with mixed ownership; turn flow when the next unit belongs to another seat. |
| B | Keep one occupant per side; add a fourth mode "mixed" that runs the computer for the units the human does not pick, inside the host page. | Smaller, but only works for fixed computer and a single human; no sub-agent fill, no two humans on one team. | Does not meet rule 3 for the agent. |
| C | Do nothing now; run the plain phone check (human red team of 3 versus an MCP white team of 3). | None. | Does not give the flexible fill the owner asked for. |

## Decision (proposed)
A, in this order, each step ending with its own test before the next starts:
1. Page: read `owners`; the local human controls only owned units; other units of any side are applied from the relay. Test: a page pair with a 1+2 split on red.
2. Page: slot picker in the room panel (who takes which slot); the host's `ready` carries the chosen filler. Test: the room panel with 0, 1, 3 and 6 claimed slots.
3. Filler: `scripts/` helper that watches the room and joins the empty slots with the chosen filler once the host starts. Test: selftest with no phone, then the real phone through `adb`.
4. Real-phone run, which also closes gap O3.

## Not decided, owner to answer
- Who starts the filler: the room host's machine (a command the owner runs once) or the relay itself. This ADR assumes a helper script on the Mac, because the relay holds no game rules (owner decision 10 in the relay protocol).
- DECIDED 2026-11-24 by the owner: reading 1. What "the computer assigns the vacancies at random" randomises. Reading 1: each human picks a team as today, the vacancies per team follow by subtraction, and the random draw only chooses which heroes fill them. Reading 2: humans do not pick a team; the computer also splits the humans and the vacancies over the two teams at random. Reading 2 needs a team-assignment step in the relay or the host and is larger.
- Whether the slot picker may be skipped on the phone (default: the host claims its own team, the other team stays unclaimed and is filled).

## Out of scope
Spectators, reconnect after a filler dies, more than 3 units per side, and any change to damage, rounds or the hash format.

## Rollback
Every step is behind the existing one-occupant path: with no `owners` entry the page behaves exactly as it does today. A backup of `index.html` and `js/relay_client.js` is taken before step 1, and the existing 151 tests must stay green.

## Review status
Owner sign-off: "開工" in chat, 2026-11-24 (after reading 1 and the cap were fixed). Not reviewed by an independent zero-context reviewer yet.

## Lock and formation record: DESIGN ONLY, NOT BUILT (red-team R1 A4: nothing below exists in the code yet; owner, 2026-11-24: "once the independent units are locked, record the hash, code, serial number and formation")
- Lock point: the relay's `start` (every seat ready). From then on no seat may change its unit list; the formation is final for the match.
- Record, one line per unit, in world-id order (`left_0..left_2`, `right_0..right_2`): serial (the world id), hero code, owner seat id, and `filler` true or false.
- Formation hash: the first 8 lowercase hex characters of a fixed hash over the canonical text `serial:hero:owner;` of those lines in that order (same 8-hex format as the round hash, so the relay accepts it unchanged).
- Every page computes it from the same `start` message (`heroes` and `owners`) and sends it as `round_hash` for round 0. The relay already compares hashes per round and broadcasts `out_of_sync` on a difference, so a seat that formed a different team is shown at once. No relay change.
- The record is kept in the match snapshot (`js/relay_client.js`) and written by the room check script to its log, so a later run can prove which team was played and who controlled each unit.
- The filler's random draw (above) is already inside `heroes`, so the hash covers it.
- Team code (owner, 2026-11-24: "the team I pick is given a code after the lock"): at the lock each team gets a short code made of its colour and the first 4 hex characters of the hash of that team's own lines, for example `red-3fa9`. A seat is told its team's code and its own unit serials, shown in the room panel and written to the record. The code is derived, not stored by the relay, so every page computes the same one.

## Page change list found by reading the turn code (2026-11-24, after sign-off). Status: P1 to P7 are BUILT (stages 1 and 2); the line references of the first draft are not kept, search the names
The page treats `left` as "my whole team" and `right` as "the remote team", and a team has ONE active unit per phase (rotation). The relay checks ownership only per action, and any seat of the phase team may send `end_turn`. A split team therefore needs these page changes, each with its own test:
| # | Change | Where (index.html) |
|---|---|---|
| P1 | Map `seat_id` to team from `relaySeats` (helper). | near `relaySeatId` |
| P2 | `relayApplyAction`: an action whose sender is on MY team (a teammate) runs on the LEFT unit (`executeThrow("player", ...)` with `remoteApplying`), not on the right side. | `relayApplyAction` |
| P3 | Judge duty: only the lowest seat id of a team answers a remote throw with `judge`; a second answer from the same team is never sent. | `relaySendJudges` |
| P4 | Turn gating: at my team's phase, if the active left unit is not owned by me, wait (`turn = "busy"`) for the teammate's action and `end_turn`. | `relayAfterTurn`, `beginRelayMatch`, `resolveRound` |
| P5 | `end_turn` from a teammate closes the local team turn like my own (without sending). | `relayOnMessage` |
| P6 | `relayUnitHeroes` sends only this seat's slice; unit profiles for all left units come from `start.heroes.left`. | `relayUnitHeroes`, `beginRelayMatch` |
| P7 | Slot picker in the room panel, and the filler choice on the host's `ready`. | room panel |
Backup before any edit: `(not published)`.

## Stage 2 as built (2026-11-24)
- The picker lives in the room panel (`#slot-picker`): "I take N units" (1 to the team size; the full team is the default and sends the old wire), the host's "invite link joins red or white" (adds `seat=red` to the link and the QR; white is the default and adds nothing), and a live open-slot line from the seats' named units (the subtraction of this ADR).
- A guest chooses the team and the claim through the invite link (`seat=red|white`, `claim=N`), because the relay fixes the team at join; the claim can still be changed in the panel until Start, because units travel on `ready`.
- The filler choice (fixed computer or sub-agent) is NOT on the wire: the relay would drop an unknown `ready` field. It becomes a flag of the stage 3 helper script (`--filler computer|agent`), which prints the command for the room.
- Locked after the match starts.


## Stage 3 as built, and what the real-phone runs found (2026-11-24)
- Filler: `scripts/fill_room.py` (placeholder seats, subtraction, one computer seat per team with open slots via `scripts/hybrid_seat_headless.js --claim K`). `--filler agent` is refused: the MCP bridge owns a whole side and cannot take part of a team.
- Relay change (the only one): `_start_if_ready` is now a helper and is also called after a seat leaves before the start, so a placeholder that held the start back can release it (3 new tests in `scripts/test_pk_relay.py`).
- Judge duty (found by the first real-relay selftest): the relay refuses a judge for a unit the sender does not own, so every owner judges its own unit and only the lowest seat answers a miss (`relayOwnsUnit`).
- Found only on a real phone: with two seats on one team a slow page missed the start of its round (the relay was already two rounds ahead) and waited for ever. Fix: in a room where a team has two or more seats, actions and end_turn are queued and handled one at a time in the relay's order (`relayOnMessage`, `relayInboxReady`, `relayDrain`), each only when the page has finished the turn before it; a page's "my turn" uses its place in the relay log (`relayCursor`). Rooms with one seat per team behave exactly as before (`relayQueueMode` is false). Test: `test_page_relay_split.js` "a slow page" (a frozen page catches up); with the queue switched off the same scenario stays stuck.
- Eye anchor: the pumpkin face glow now reads the eye spots from the picture that is drawn (`eyeCentersFromPixels`, `faceEyesOf`), so it follows every pose instead of one fixed offset. No clock read.
- Whole flow: `scripts/run_slot_room.py` (relay, page server, adb, the phone's Chrome over DevTools, an optional headless-Chrome desktop seat with `--with-desktop`, the filler, a verdict) and `scripts/phone_eval.py` (run JavaScript in the phone's tab, open a page, take a screenshot).

## Built versus not built (red-team R1, 2026-11-24)
| Item | Status |
|---|---|
| Per-unit ownership in the page (P1 to P6), slot picker (P7) | built, tested (test_page_relay_split 11, test_slot_picker 7) |
| Ordered handling of relay messages in rooms where a team has 2 or more seats | built, tested; rooms with one seat per team are unchanged (`relayQueueMode` false) |
| Filler helper `--filler computer` | built; real runs and selftests pass |
| Filler `--filler agent` | NOT built (refused with exit 5): the MCP bridge owns a whole side |
| Formation record, hash, team code, serial numbers | NOT built (design only, section above) |
| Filler started automatically when the host presses Start | NOT built: the helper still needs a terminal command |
| Judge sent in order with its action (a lagging page can show a false out-of-sync toast) | NOT built (P2, scheduled) |
| Bot takeover for a seat that leaves | NOT built: a seat that leaves forfeits its team (`relayOpponentLeft`, decided here, owner may overrule) |

## Behaviour changes to be honest about (red-team R1 B5)
- The relay now starts a room when a seat that held the start back LEAVES (`leave`) or EXPIRES (grace period). This applies to every room including one-versus-one, so "cannot change 1v1" is not true: a 1v1 room can now start when an extra unready seat disappears (pk_relay.py `_start_if_ready`, test_pk_relay.py and test_relay_seat_grace.py).
- The commit messages of 65f4a377 and 1411f2e0 say "relay unchanged": true for those two commits (the relay change came after, in the uncommitted stage 3, now committed separately).
- A human who leaves between the fill decision and the start cannot be repaired by the helper: it re-checks the human seats before releasing the placeholders and, if they changed, reports ERROR, keeps the room blocked for 60 s and exits 7. After that the relay's own trust-based fallback applies (docs/relay_protocol_20261115.md section 9.1).
- Operating note: start ONE helper per room; the relay allows 8 connections per address by default (PK_RELAY_MAX_PER_ADDR) and the humans on one machine, the helper's three sockets and the filler seats all count (the selftests raise it to 40).

## Rollback (red-team R1 B8)
See redteam/backups/bak_unit_slot_fill_20261124/ROLLBACK.md.

