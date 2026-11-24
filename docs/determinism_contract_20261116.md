# Determinism contract

`js/determinism.js` and `scripts/determinism_py.py` expose the same pure,
seeded functions. Each accepts only unsigned 32-bit integer inputs. The shared
32-bit integer hash uses no clock, random generator, or floating-point value in
its hash path. JavaScript uses `Math.imul` and `>>> 0`; Python masks each
operation to 32 bits. `shared/determinism_golden.json` is the portable contract
between the implementations.

## Functions

| Function | Inputs | Output and range |
| --- | --- | --- |
| `wind(seed, round)` | match seed; round `>= 1` | A tenths value divided by 10, from `-4.0` through `4.0`. Round 1 preserves the page formula: `((seed % 81) - 40) / 10`. |
| `startX(seed, side, slot)` | match seed; side `0` left or `1` right; unit slot | A multiple of 36. Left values are 252 through 612, within `[220, 620]`; right values are 1296 through 1656, within `[1280, 1680]`. |
| `moveDie(seed, round, side)` | match seed; round; side | Integer die result 1 through 6. |
| `supplyDrop(seed, round)` | match seed; round | `{side, item, offset}`. `side` and `item` are 0 or 1; `offset` is an integer from -120 through 120 pixels. |
| `bounceCount(seed, round, throwId)` | match seed; round; throw id | Integer collision count 1 through 6. |
| `nunStunPick(seed, round, throwId, n)` | match seed; round; throw id; candidate count `n >= 1` | Target index from 0 through `n - 1`. |

## Page and relay use

The page should call `wind` at round setup, `startX` when it places a selected
unit, and `supplyDrop` when it schedules a crate. Practice and replay modes may
call `moveDie`, `bounceCount`, and `nunStunPick` to reproduce their local
outcomes.

A relay action must carry the selected move die and the resolved knight bounce
count. These values are player action or collision results, respectively, and
must travel in the action record rather than being re-rolled by another device.
The action still carries its normal angle, power, start point, and claimed
landing under `docs/relay_protocol_20261115.md`. The page must never use
`Math.random` to derive match state once it is wired to this contract.

## Verification

Run the same shared vectors and 10,000-seed range checks in both runtimes:

```sh
node scripts/test_determinism.js
python3 -B scripts/test_determinism_golden.py
```
