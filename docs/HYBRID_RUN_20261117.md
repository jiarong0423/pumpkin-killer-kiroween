# Hybrid room run (2026-11-17)

Plan: `docs/SIX_SEAT_HYBRID_PLAN_20261117.md`, option A (two seats per match, each seat plays a whole team of 3 units, mixed teams per `docs/MATRIX_SPEC_20261117.md`, red opens every round, strength hidden and random per seat). Runner: `scripts/run_hybrid_room.py`. Full records (one per match, matrix record format plus `seat_left`, `seat_right`, `relay_errors`, `hash_mismatches`): `(not published)` (not committed, `logs_local` is ignored). Code state of the run: commit f29cb8d7 (page AI already weakened).

## Result

Target: zero relay errors and zero round-hash mismatches in every pair. **Reached in all six pairs: 60 of 60 matches clean, 0 relay errors, 0 hash mismatches.** 10 matches per pair, both seat kinds play both sides alternately. Seats: headless page (real `index.html` in Node), desktop Chrome (real page, CDP), MCP agent (`scripts/mcp_stdio_server.py`, now judged by the page, see below). Code state: the page pairs ran at f29cb8d7, the three MCP pairs at 79daf91f (`(not published)` holds the 60 records, `logs_local` is ignored).

| seat pair | matches | win share of the first-named kind | left seat win share | rounds mean | relay errors | hash mismatches | other errors | seconds per match |
|---|---|---|---|---|---|---|---|---|
| desktop vs desktop | 10 | 100% (10/10) | 60% | 21.6 | 0 | 0 | 0 | 26 |
| desktop vs headless | 10 | 60% (6/10) | 30% | 22.3 | 0 | 0 | 0 | 26 |
| desktop vs mcp | 10 | 70% (7/10) | 80% | 22.7 | 0 | 0 | 0 | 26 |
| headless vs headless | 10 | 100% (10/10) | 70% | 21.4 | 0 | 0 | 0 | 25 |
| headless vs mcp | 10 | 50% (5/10) | 40% | 23.8 | 0 | 0 | 0 | 26 |
| mcp vs mcp | 10 | 100% (10/10) | 30% | 25.1 | 0 | 0 | 0 | 26 |

Columns: win share of the first-named kind, win share of the left (red) seat, mean rounds, relay errors, round-hash mismatches (rounds in which the two seats hashed different states, summed), matches with another error (a seat that never saw the end, hp disagreement), mean seconds per match. Strength is hidden and random per seat, so the win shares say nothing about the seat kinds.

An earlier run of the MCP pairs with the bridge's own engine judging (commit e02c4c5c) had 0 clean matches of 30 in the first two pairs and a few clean ones in mcp vs mcp; its causes are kept below because they are why the judge moved to the page.

Not run: **phone** (needs the owner's phone: `adb reverse tcp:8080 tcp:8080`, `adb reverse tcp:8765 tcp:8765`, `adb forward tcp:9333 localabstract:chrome_devtools_remote`, then `python3 -B scripts/run_hybrid_room.py --kinds headless,phone,desktop --relay-port 8765 --matches 10`; `scripts/hybrid_seat_chrome.mjs --kind phone` is the desktop code with a forwarded DevTools port and is untested on a phone). **Claude** seat: built (`--kinds ...,claude`: the turn is written to `(not published)`, the answer read from `action.json`), not run; it is an MCP-bridge seat and would now work like the mcp seat.

Watching a match on one page: the runner serves `http://127.0.0.1:8099/` (`scripts/hybrid_viewer.html`): both teams, hp bars, every shot, the last messages, the finished matches. Slow it down with `--speed 4` (fake seconds per real second; default 8, 1 is real time).

## What the room test found and fixed (all in this branch, tests added)

1. Axe knockback in team matches only moved `x`; the page glides every unit back to `targetX` within a second, so two devices hashing at slightly different moments disagreed by a pixel or two (a hash mismatch every third round). Team matches now set `targetX` too (`scripts/test_team_knockback.js`). One unit per team is unchanged (the push still slides back): decision for the owner.
2. The 12 s turn clock kept running while the own throw was in the air. A stunned or shocked unit has 3 s, the flight ran it out and the page passed the turn a second time (`stale_or_out_of_turn`). The clock now stops while projectiles are in the air (`scripts/test_page_relay_pair.js`).
3. Page seats must run at the same rate. A seat that races ahead acts before the other page has landed its own throw and the pages part (a kill that one page never sees). The runner holds both pages to the same rate (`--speed`, default 8) and flushes the send queue before a seat ends; the pacing also keeps each socket under the relay's 10 messages a second.
4. MCP bridge in team rooms (`scripts/mcp_stdio_server.py`): it sent `red_1` where the relay needs `left_0`, never sent its heroes in `ready`, never read the room's heroes, judged by unit order instead of path order, named `unit: null` on a miss, ignored the fence, ended its turn before the other device's judge arrived (the round then resolved on the engine's own flight), used the engine's own random wind instead of the room's seeded wind (round 1 of one seed was 2.0 on the page and -3.0 in the engine), and could burst past the relay rate limit. All fixed. The engine's team start positions were a seeded shuffle of 240/460/680; they are now the page's slots 252/432/612 and 1296/1476/1656 (`mcp_referee_baseline_145.json` regenerated).

## The MCP bridge in a room: the page is the judge

The bridge's own engine only approximated the page (a constant wind push instead of the wind acceleration, one unit hit per throw with no wave area, no stepped wave distances, pity and underdog counters not advanced for relayed throws), so every pair with an MCP seat drifted from round 2. Instead of porting the page's hit rules into Python a second time, `PageJudgeRelay` (`scripts/mcp_stdio_server.py`) runs `scripts/page_judge_seat.js`: the real `index.html` in a Node vm, joined to the room like any page seat. The page simulates every throw, judges its own units, hashes the round and ends turns by its own rules; the bridge's `Session` is only the agent's public view, overwritten from the page's state after every change (positions, hp, statuses, fence, round, phase, landed throws). New page rules (wave landing, knight wall, caps, hero numbers) reach the agent seat with no second copy to keep in step.
- The agent still sees the public tools only (`get_public_state`, `get_roster`, `get_history`, `submit_action`, `end_turn`, notes); no flight formula, constant or judge goes to it (checked by `scripts/test_page_judge_relay.py`).
- Plain throws only (the relay carries nothing else yet); a move, skill or ultimate is refused with a message. Needs Node 22+; At the time of this run `--page-judge off` kept the old engine bridge (default `auto`); since 2026-11-27 the page judge is the only path and `auto` and `off` are refused. `--page-speed` must equal the opposing page's rate (1 for a human on a normal page).
- The page's 12 s clock does not run while the agent decides; the bridge's own clock does.

## Reproduce

`python3 -B scripts/run_hybrid_room.py --kinds headless,mcp,desktop --matches 10 --match-timeout 70 --report (not published)<date>.md` from the owner's terminal (sockets and Chrome do not start in the Claude sandbox). Only page seats: `--kinds headless,desktop`. `scripts/hybrid_show.py <result.json>` prints one line per match; failing matches keep their ordered messages and, per round, each page's hash inputs for tracing the first difference.
