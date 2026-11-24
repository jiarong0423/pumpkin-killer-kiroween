# Kiro task 173 — the determinism contract: seeded pure functions in JavaScript AND Python with golden vectors (new files and tests only; NO edit to index.html)

Owner 2026-11-16: do all the gaps. The page still draws wind, dice, start positions, supply drops, the knight's bounce count and the nun's stun pick with `Math.random`; the Python engine uses its own `random.Random`. Two devices (or a device and the MCP engine) cannot agree on a match. This task builds the shared, seeded, pure part; the main line wires the page afterwards.

Read first: `js/weather.js` and `scripts/weather_py.py` and `scripts/test_weather_golden.py` plus its golden file (the exact pattern to copy: integer hash, no floats in the hash, the same output in both languages), `js/round_hash.js`, `scripts/round_hash_py.py`, `shared/constants.json`, `docs/relay_protocol_20261115.md` sections 5 to 7, and in `index.html` (read only) the places that call `Math.random` for state: search `Math.random` and ignore particles and effects.

Build (each function pure: `(seed, ...integers) -> integer or fixed-point value`; use a 32-bit integer hash such as mulberry32 or splitmix32 computed with `Math.imul` and `>>> 0` in JavaScript and masked integers in Python; no `Math.random`, no `Date`, no float in the hash path):
1. `js/determinism.js` (UMD like the other modules, global `Determinism`) and `scripts/determinism_py.py` with the SAME functions:
   - `wind(seed, round)` : the wind of a round as a number in [-4.0, 4.0] with one decimal; round 1 must equal what the page now computes for the first round: `parseFloat((((seed % 81) - 40) / 10).toFixed(1))`; later rounds use the hash of `(seed, round)` with the same range. Return a decimal-exact value (compute an integer tenths value and divide by 10).
   - `startX(seed, side, slot)` : the start x of a unit: left side in [220, 620], right side in [1280, 1680], multiples of 36 (the page's DICE_STEP_PX), by the hash of `(seed, side, slot)`.
   - `moveDie(seed, round, side)` : the dice step the unit moves, an integer 1 to 6 (the page currently asks a die; the relay carries the number instead, this function is for the practice and replay modes).
   - `supplyDrop(seed, round)` : `{ side: 0 or 1, item: 0 or 1, offset: integer pixels in [-120, 120] }`.
   - `bounceCount(seed, round, throwId)` : the knight's collision count, 1 to 6.
   - `nunStunPick(seed, round, throwId, n)` : which of `n` candidate targets is stunned, 0 to n-1.
2. Golden vectors: `shared/determinism_golden.json` with at least 40 inputs per function (include seeds 0, 1, 2^31-1, 4294967295, 1234567890 and rounds 1, 2, 3, 10, 99); `scripts/test_determinism.js` (Node) and `scripts/test_determinism_golden.py` (Python) both read the SAME file and assert equal outputs; also property checks over 10 000 seeds: every output inside its range, the wind has at most one decimal, `startX` is a multiple of 36, left x < right x always.
3. Document the functions in `docs/determinism_contract_20261116.md` (inputs, outputs, ranges, what the page should call it for, what must travel in an action instead: dice and bounce count).
4. Run `node scripts/test_determinism.js`, `python3 -B scripts/test_determinism_golden.py`, and the existing `node scripts/test_weather.js` if it exists; paste the last lines.

Touch only: `js/determinism.js`, `scripts/determinism_py.py`, `shared/determinism_golden.json`, `scripts/test_determinism.js`, `scripts/test_determinism_golden.py`, `docs/determinism_contract_20261116.md`. Final message: the file list, the golden count per function, test results.
