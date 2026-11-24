# Task 100 result — gpt-5.6-terra

Changed `js/knight_ult.js`: `createKnightUlt`, `begin`, `place`, `lock`, `endTurn`, `cancel`, `answer`, `getReveal`, `registerKO`, `publicView`, and `getStatus` implement the deterministic hidden A/B/C point state machine.
Changed `scripts/test_knight_ult.js`: named requirement 10–17 tests plus a 300-seed shadow-model property test covering capacity, one-answer-per-point, public-view secrecy, and deterministic twin runs.

Verification commands and final output lines:
```text
node scripts/test_knight_ult.js
test_knight_ult: all 10 tests passed
node scripts/test_ultimate.js
test_ultimate: all 24 tests passed
```

Provisional values retained as named constants: `POINT_HALF_WIDTH = 70` px, `REVEAL_SECONDS = 1.4` s, and unused points expire after 3 answered enemy attacks.
Not run: browser wiring or a visual playthrough. `index.html` was not edited, as required. Main-line verification remains outstanding.
