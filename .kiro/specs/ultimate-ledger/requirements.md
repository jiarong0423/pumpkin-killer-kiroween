# Requirements: ultimate ledger

Module: `js/ultimate.js` (`Ultimate.createLedger`). Rules come from `docs/ultimate_rules.md` and `(not published)` (the log wins). A "side" is one player or one AI (`'player'`, `'ai'` by default, any names through `sides`). Every requirement names the test in `scripts/test_ultimate.js` that checks it.

## Pips

1. When `registerHit(side, throwId)` is called for a known side with a valid, not yet counted `throwId`, and the side still has an ultimate left and fewer than `maxPips` pips, the ledger shall add exactly one pip and return `{ counted: true, pips, reason: null }`. (test: "a hit adds one pip ...")
2. If `registerHit` is called again with the same `throwId` for the same side, then the ledger shall add no pip and return the reason `duplicate_throw`. This holds when the first call came after the pips were full and after the ultimate was spent. A number `5` and a string `"5"` are two different ids. (test: "the same throwId never counts twice ...")
3. The ledger shall never hold more than `maxPips` (default 3) pips; a hit at full pips returns `pips_full`. (test: "a hit adds one pip ...")
4. Each side shall count its own pips; a hit, a KO or a reset of one side shall not change the other. (test: "each side counts its own pips")
5. While a side has used `maxUses` (default 2) ultimates, `registerHit` shall add no pip and return `no_ultimates_left`. (test: "at most two uses per side per match ...")
6. If `throwId` is not a finite number or a non-empty string, or the side is unknown, then the call shall return a reason (`bad_throw_id`, `unknown_side`) and change nothing. (test: "bad throw ids and unknown sides ...")

## Arming

7. `canArm(side, ctx)` with `ctx = { turn, side, round, defendTurn, dead }` shall return `{ ok, reason }` and shall return `ok: true` only when all of these hold: `ctx.turn` equals `side` (and `ctx.side`, if given, equals `side`); the unit is not dead; it is not a defend turn; the side is not already armed; the side has used fewer than `maxUses`; the side has not used one in `ctx.round`; the side has `maxPips` pips. (tests: "arming needs three pips", "arming only on the side own turn", "never on a defend turn, never when dead")
8. The refusal reasons shall be, in this order of checking: `wrong_phase`, `unit_dead`, `ultimate_with_defend`, `already_armed`, `no_ultimates_left`, `ultimate_used_this_round`, `ultimate_cooldown`, `ultimate_not_ready`. A missing context gives `bad_context`, a missing or non-finite round gives `bad_round`. (same tests)
9. There shall be no round-1 lockout and no "not two rounds in a row" lockout: a side with full pips may arm in round 1, and in the round after a use. (test: "lockout: no round-1 lockout ...")
10. Where `cooldownRounds` is above 0 (default 0, published as `ULT_COOLDOWN_ROUNDS`), the ledger shall refuse arming with `ultimate_cooldown` for the next `cooldownRounds` rounds after a use. (test: "cooldownRounds is the one lever ...")
11. `arm(side, ctx)` shall set the armed flag only when `canArm` says ok; otherwise it shall return the same refusal and leave the flag alone. `canArm` alone shall never arm. (tests: "arming needs three pips", "armed state can be cancelled ...")
12. `cancel(side)` shall clear the armed flag and shall leave pips and the used count unchanged. It shall report `wasArmed`. (test: "armed state can be cancelled for free ...")

## Spending

13. `consume(side, round, throwId?)` on an armed side shall set pips to 0, add 1 to the used count, clear the armed flag and remember `round` as the round of the last use, whether or not the throw later hits. (test: "consume spends the armed ultimate ...")
14. If the side is not armed, then `consume` shall return `not_armed` and change nothing. (same test)
15. If `consume` is given the ultimate throw's `throwId`, then later `registerHit` calls with that id shall add no pip (the ultimate throw gives 0 pips). (test: "the ultimate throw itself gives no pip ...")
16. At most one use per side per round shall be possible: after `consume` in round r, `canArm` in round r returns `ultimate_used_this_round`, even with full pips again. (test: "lockout ...")
17. When a unit is knocked out, `registerKO(side)` shall set its pips to 0 and clear its arming, and shall not change the used count. (test: "a KO loses the pips ...")

## State and robustness

18. `getState(side, round?)` shall return a new plain object with exactly the fields `ult_pips`, `ult_ready`, `ult_armed`, `ultimates_remaining`, `ultimates_used`, `ult_used_this_round` (names from `docs/ultimate_rules.md` 2g), and `null` for an unknown side. `ult_ready` shall be true only with `maxPips` pips and an ultimate left. Without `round`, it shall use the last round the ledger was given. (test: "getState: exact field names ...")
19. `reset()` shall clear every side, every pip, every use and every remembered throw id. (test: "reset clears every side ...")
20. `splitDamage(normal, strikes)` shall return `1.5 x normal / strikes` rounded to 0.1, and a finite non-negative number for any input. (test: "splitDamage ...")
21. The module shall not call `Math.random` or `Date` and shall not touch the DOM; the same calls shall give the same results. (tests: "no Math.random and no Date ...", "property: same script, same results")
22. No function shall throw for bad arguments; each shall return a reason and leave the state unchanged. (test: "garbage arguments never throw ...")
23. For 300 seeded random scripts of mixed calls, the ledger shall agree with a separately written shadow model and keep these invariants: `0 <= pips <= maxPips`; `used <= maxUses`; `used + remaining = maxUses`; an armed side has full pips. (test: "property: 300 random scripts ...")
