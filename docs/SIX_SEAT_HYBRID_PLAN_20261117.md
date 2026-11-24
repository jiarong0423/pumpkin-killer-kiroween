# Six-unit hybrid session: plan (owner 2026-11-17)

Owner's words (paraphrased): one 3v3 match of six units where desktop page, phone page, MCP sub-agents (headless pages and a Python engine bot) and Claude all play against each other in the SAME room; the owner watches the whole match on one page; the MCP join method and the headless page are not built yet; after this run the AI strength is lowered. Option A below was proposed as the default (cheaper, uses the room mechanism that exists); option B (one seat per unit) was offered and not chosen.

## Option A (default): two seats per match, each seat controls a whole team of 3 units
- Seat kinds (any kind can be left or right): desktop Chrome page, phone Chrome page, headless page (the real `index.html` in the Node vm, real WebSocket to the relay), MCP agent (Python bridge `scripts/mcp_stdio_server.py` joined to the relay by room code), Claude.
- A match = left seat kind x right seat kind, 3v3, mixed teams (the hero rule of `docs/MATRIX_SPEC_20261117.md`), fixed first team, random hidden strength where the seat is an AI.
- Runner `scripts/run_hybrid_room.py` (to build): starts the relay, opens a room, starts the two seats, plays to the end, writes one record per match in the matrix record format plus `seat_left`, `seat_right`, `hash_mismatches`, `relay_errors`.
- One spectator page: the relay has a spectator seat; the page (or a small viewer page) shows the live state of both teams so the owner sees the whole match.
- Done when: every pair of seat kinds plays >= 10 matches with zero relay errors and zero round-hash mismatches, and the table (seat pair x win share, rounds, errors) is in `(not published)`.

## Option B (not chosen): six seats, one unit each
The page does not know teammate seats (`owners` of `start` is parsed in `js/relay_client.js` but never read by `index.html`), so the page must learn to treat units of other seats on its own team as remote. About 2 to 3 days.

## After the run: AI tuning (owner: 'three items together', plus item 4 added the same day)
1. every AI shot a random angle (25 to 80 degrees, flat and lobbed), power from `simulateLandingX` (bisection), not the closed form for 54 degrees;
2. the wind misread grows with the wind (proportional part plus a small base) instead of a fixed 0.5 / 1.2 / 3.2 units;
3. the position misread (view noise) larger;
4. (owner 2026-11-17: 'so it can see the formula') the AI must not use the game's own flight formula: `simulateLandingX` and the wind constants are the real physics. Give the AI its own imperfect model (gravity and wind coefficient off by a few percent, drawn once per match and per level) and let it correct itself only from where its earlier shots really landed, like a human does;
target hit rates (direct hits per throw, 1v1, plain throws, both sides the same level): easy 0.15, normal 0.30, hard 0.45 (measured now: 0.43 / 0.54 / 0.87). Calibrate with `scripts/sweep_page_ai_levels.js`; knobs in `js/ai_levels_page.js` and `normalAiAim` in `index.html`.

## Constraints
No push by Claude, no Co-Authored-By, API keys only by the owner (never read or printed), sub-agent results re-run by the main session, one unit per team stays byte-identical except the deliberate changes (crit 1.1, wave landing).
