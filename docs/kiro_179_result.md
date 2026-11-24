# Task 179 result

## Changed

- Added `scripts/test_properties.js`: `mulberry32`, `forAll`, and six seeded cross-module properties for damage/timelines, deterministic values, round hashes, weather, flight, and all balance pairings.
- Added `docs/KIRO_USAGE_20261116.md`: an English contest-process record covering specs, steering, hooks, agents, MCP, the seat power, golden vectors, balance simulation, routing, and roles.

## Commands run

```text
node scripts/test_properties.js
```

Exit code: `1`.

Last lines of the real output:

```text
ok   - weather is known, bounded, and deterministic
FAIL - flight ends and power is monotonic without wind
       case 0: {"angle":31.563952296273783,"lowPower":83.34476620098576,"highPower":88.67397859727909}
       landing x must not decrease as power increases without wind
FAIL - all balance pairings finish without numerical dominance
       bride average win rate is outside 20 to 80 percent: 16.9%
test_properties: 4 of 6 properties FAILED
```

I also requested this required documentation-count command:

```text
git ls-files '.kiro/*' '.kiro/**/*' | awk -F/ 'NF >= 3 { count[$2]++ } END { for (name in count) print name, count[name] }' | sort
```

It did not run because its local command permission request was not answered. `docs/KIRO_USAGE_20261116.md` therefore does not invent tracked-file counts.

## Failing properties for the main line

The runner completes the full generated sample before reporting each first counterexample. These are the smallest generated witnesses, retained at case zero where applicable; no rule module was changed.

- **Ultimate timeline time order:** case 0, `{"distance":-500,"normal":1,"targets":[],"flightTime":0.05,"enemies":[]}`. `UltimateFx` emitted time `0.0325` after `0.05` (`UltimateFx event 8 is out of time order: 0.05 then 0.0325`).
- **Round-hash sub-pixel stability:** case 0, `{"x":0.49,"y":0.49,"delta":0.31,"hp":50}`. Changing both coordinates by 0.31 px changes the hash (`6a838304` to `139eff33`), although the stated property expects changes below 0.4 px to preserve it.
- **Flight power monotonicity:** first generated witness, `{"angle":31.563952296273783,"lowPower":83.34476620098576,"highPower":88.67397859727909}`. The higher-power zero-wind shot lands to the left of the lower-power shot.
- **Balance wide band:** all current `ClassStats.CLASS_KEYS` pairings, seed `179`, normal agent level, and 72 matches per pairing (2,016 total matches). Bride's average win rate is 16.9%, below the requested 20% floor. The simulator reported no timeout before this rate check.

## Not verified

The property runner did not pass. The tracked `.kiro` file counts could not be obtained because the required `git ls-files` command did not run. The main line still needs to rerun the property test and independently record the outcome in `docs/kiro_verified.json`.
