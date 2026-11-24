# Design: ultimate ledger

## What it is

`js/ultimate.js` is a small state holder. It counts pips, decides if an ultimate may be armed, and spends it. It does not know classes, damage, projectiles or the UI. The game (or the MCP engine) calls it at five moments and draws what `getState` returns.

```
registerHit(side, throwId)     a throw of `side` damaged a unit            -> +1 pip (once per throw)
canArm / arm(side, ctx)        the unit's own turn, menu entry or tool call -> armed
cancel(side)                   Esc, Move, Attack, Defend, unit switch      -> armed off
consume(side, round, throwId)  the armed throw leaves the hand             -> pips 0, uses +1
registerKO(side)               the unit died                               -> pips 0, armed off
```

## State per side

`{ pips, uses, armed, lastUseRound, counted }`. `counted` is a set of throw ids (as `typeof:value` keys, so `5` and `"5"` differ). It is also filled by `consume`, which is how the ultimate throw gets 0 pips.

## Decisions

| Question | Choice | Why |
|---|---|---|
| Pips per side or per unit | Per side, as `index.html` counts today (`energy = { player, ai }`) | 1 v 1 has one unit per side. `docs/ultimate_rules.md` asks for per-unit counters in 4 v 4; then create one ledger per unit and let `maxUses` be enforced by the caller, or add a unit key to `sides`. Not built (no 4 v 4 flow is confirmed). |
| Does a hit while armed count | Yes, capped at `maxPips` | A hit cannot arrive while armed in the confirmed flow; the cap makes it harmless. |
| Where is "frozen / stunned" | Not in `ctx` | No such state exists in the code (`docs/ultimate_rules.md` 2f). The caller can pass `dead: true` for any state that must block. |
| Lockout | Exactly `docs/ultimate_rules.md` 2a: none, except one use per side per round, plus `cooldownRounds` (default 0) as the published lever | The document argues the other lockouts never trigger. |
| Order of refusal reasons | wrong_phase, unit_dead, ultimate_with_defend, already_armed, no_ultimates_left, ultimate_used_this_round, ultimate_cooldown, ultimate_not_ready | The cheapest and most useful message first; the most common "not yet" last. |
| `consume` without arming | Refused (`not_armed`) | The ultimate is never automatic. The built cat branch fires for the AI without arming; the wiring note says to call `arm` first. |
| Ultimate throw gives pips | No. Pass its `throwId` to `consume` | `docs/ultimate_rules.md` 2d. The built code gives 1; this is an engine change. |
| Reasons as strings | The six names of `docs/ultimate_rules.md` 2g plus `ultimate_cooldown`, `already_armed`, `not_armed`, `bad_*`, `duplicate_throw`, `pips_full`, `unknown_side` | The six can go straight into the MCP rejection list. |

## Additions to the API in the brief

The brief lists `registerHit, canArm, arm, cancel, consume, getState, reset`. Added: `registerKO(side)` (a KO'd unit loses its pips needs an entry point), an optional third argument `throwId` of `consume`, an optional second argument `round` of `getState`, `splitDamage`, the constants and `REASONS`. Nothing in the brief was removed or renamed.

## Not covered

- A real timer. `consume` is called by the caller at release, including a release forced by the 12 s timer.
- Persistence. The ledger is rebuilt by `reset()` at each match start.
- The AI's decision to use the ultimate (`docs/ultimate_rules.md` 2h). The simulator (`scripts/sim_balance.js`) has a stand-in; the real one belongs to `triggerAITurn`.
