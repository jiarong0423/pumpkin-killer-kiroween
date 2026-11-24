# Task 155 result
Changed: `js/flight.js` (`Flight.simulate`, `Flight.coarsePath`) and `scripts/flight_py.py` (`simulate`, `coarse_path`).
Changed: `scripts/gen_flight_golden.py` generated `shared/flight_golden.json` with 66 cases.
Changed: `js/round_hash.js` (`canonicalText`, `sha256`, `hash`) and `scripts/round_hash_py.py` (`canonical_text`, `hash_state`, `generate_golden`).
Changed: generated `shared/round_hash_golden.json` with 20 states, plus the four named golden test scripts.
Verified: `node scripts/test_flight_golden.js`
Last line: `PASS: 66 flight goldens, 500 Python/JS cases, 30 page parity cases`
Verified: `python3 -B scripts/test_flight_golden.py`
Last line: `PASS: 66 flight goldens, 500 Python/JS cases`
Verified: `node scripts/test_round_hash.js` / `python3 -B scripts/test_round_hash.py`
Last lines: `PASS: 20 round-hash goldens; sub-pixel stable and one-pixel sensitive` (both).
Could not verify browser or phone execution; the checks ran in Node and Python only.
A separate SHA diagnostic command was not run because its permission request was unanswered; the four required tests ran successfully.
