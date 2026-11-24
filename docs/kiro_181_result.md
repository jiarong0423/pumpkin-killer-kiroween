# Task 181 result — property triage

## What changed

- `js/ultimate_fx.js`: added stable chronological ordering for every direct ultimate timeline producer.
- `scripts/test_ultimate_fx.js`: made timeline ordering an invariant and added a 0.05-second-flight regression case.
- `scripts/test_properties.js`: corrected the round-hash rounding property, limited flight range comparison to wall-clearing ground landings, accepted valid canvas-exit termination, and kept the seeded balance check.
- `js/class_stats.js`: synchronized the default simulator table with `shared/heroes.json`, added the eighth page hero (`hag`, the Ghost Nun identity), modeled the bride's stepped 40/75/105 px wave bands, and added page-equivalent poison data for the wizard and bride.
- `scripts/sim_balance.js`: added refreshed, lethal two-turn poison and its accounting. Poison can end a match at round start, so the turn-accounting test now permits that page-equivalent outcome.
- `scripts/test_class_stats.js`: retained and updated the existing assertions for the synchronized eight-hero table, and added direct shared-table checks.
- `scripts/test_sim_balance.js`: retained and updated the existing old-value assertions; added poison refresh/KO coverage and stepped-wave coverage.

No change was required to `docs/KIRO_USAGE_20261116.md`: its statements remain true.

## Verification commands run

```text
node scripts/test_properties.js
node scripts/test_class_stats.js && node scripts/test_sim_balance.js && node scripts/test_ultimate_fx.js
node scripts/test_round_hash.js
node scripts/test_flight_golden.js
python3 -B scripts/test_heroes_sync.py && python3 -B scripts/test_round_hash.py && python3 -B scripts/test_flight_golden.py
node scripts/sim_balance.js --matches 56 --seed 179 --agent-level normal --json
```

Last lines of the successful checks:

```text
test_properties: all 6 properties passed
test_ultimate_fx: all 13 tests passed
test_sim_balance: all 28 tests passed
test_class_stats: all 13 tests passed
PASS: 20 round-hash goldens; sub-pixel stable and one-pixel sensitive
PASS: 66 flight goldens, 500 Python/JS cases, 30 page parity cases
PASS: 66 flight goldens, 500 Python/JS cases
```

The required full-suite commands were attempted after the fixes but the local command permission request was not answered, so neither command ran and no full-suite pass is claimed:

```text
for f in scripts/test_*.js; do node "$f" || exit 1; done
for f in scripts/test_*.py; do case "$f" in scripts/test_mcp_connect.py|scripts/test_mcp_connect_weather.py|scripts/test_pk_relay.py|scripts/test_pk_mcp_health.py|scripts/test_smoke_url.py) continue ;; esac; python3 -B "$f" || exit 1; done
```

Each attempt ended with:

```text
The permission request failed before it was answered, so this call did not run; the user did not reject it.
```

## Triage

### 1. UltimateFx timeline order — module defect, fixed

**Evidence:** `skeletonTripleJavelin()` constructed an impact event at `flightTime` and then began the next spear's fall event at `flightTime * 0.65`. For the generated `flightTime: 0.05` case, the returned sequence contained `0.05` followed by `0.0325`. Independently, `necroGhostfireTrio()` could append its `fires_vanish` at `0.35` after a later impact. Direct timeline producers returned their construction order, while `scripts/test_properties.js` required nondecreasing `t`.

**Change:** `ordered(events)` decorates events with their original index, sorts by time then index, and is used by every non-empty direct timeline producer. Equal-time event order remains stable. The ultimate test now enforces ordering and exercises every direct producer at a 0.05-second flight.

**Final status:** `test_ultimate_fx: all 13 tests passed`; the timeline property passed all 2,000 seeded cases.

### 2. Round hash sub-0.4 px stability — property test flaw, fixed

**Evidence:** `js/round_hash.js` serializes coordinates through `fixed(value, 0)`, which calls `roundHalfUp`. The original witness moves `0.49` by `0.31` to `0.80`; those values round to `0` and `1`, respectively, so different hashes are correct. `scripts/round_hash_py.py` uses the same half-up rule, and both JavaScript/Python golden checks passed.

**Change:** the property now checks that coordinates which round to the same integer have the same hash, while coordinates whose rounded integers differ have different hashes. It uses a `0.001` same-cell delta and retains the generated `0.31` boundary-crossing delta.

**Final status:** `PASS: 20 round-hash goldens; sub-pixel stable and one-pixel sensitive`; the hash property passed all 2,000 seeded cases.

### 3. Flight monotonicity — property test flaw, fixed; no flight-module defect found

**Evidence:** `js/flight.js` checks the central fence before ground collision. The original stronger zero-wind shot can hit the fence differently from the weaker shot, so obstacle-terminated `landingX` is not a free-flight range measurement. The initial revised property also revealed that valid high-power trajectories can exit the canvas, which is an explicit `hit: 'out'` return in both `js/flight.js` and `scripts/flight_py.py`.

**Change:** the property still requires a finite, bounded-step terminal result, now accepts `ground`, `wall`, or `out`, and compares range only when both shots clear the fence and land on the ground. Its comment records why the obstacle cases are excluded. Neither flight implementation nor `shared/flight_golden.json` changed.

**Final status:** `PASS: 66 flight goldens, 500 Python/JS cases, 30 page parity cases`; the flight property passed all 2,000 seeded cases.

### 4. Balance pairings — simulator/model defects, fixed

**Evidence:** the default `ClassStats.CLASSES` table contained stale HP/damage values, stale projectile metadata, no eighth hero row, a linear bride wave that differed from the page's `SoundWave.BANDS` (40/75/105 px at 100/75/50 percent), and no implementation of the poison listed for wizard and bride in `shared/heroes.json`. Before poison modeling, the property still reported `bride average win rate is outside 20 to 80 percent: 18.4%`. The page calls poison application for both cannonballs and sound waves; the simulator had only non-lethal reaper burn.

**Change:** the default simulator table now mirrors `shared/heroes.json` and uses the canonical page id `hag` for the Ghost Nun. The brief calls this hero `nun`, but `shared/heroes.json`, `HERO_PROFILES`, and `scripts/test_heroes_sync.py` establish `hag` as the canonical identifier. The simulator now refreshes and applies the page-equivalent two-turn, lethal poison. The bride wave model now exactly uses the page's stepped bands. No page HP or damage number changed.

**Final seeded run:** 2,016 matches, seed 179, normal public-agent level, 56 matches per unordered pairing, zero timeouts.

| Hero | Average win rate |
|---|---:|
| skeleton | 47.7% |
| wizard | 56.4% |
| bat | 44.4% |
| knight | 75.3% |
| bride | 24.0% |
| hunchback | 49.7% |
| reaper | 39.8% |
| hag (Ghost Nun) | 62.8% |

The bride is now inside the property’s 20–80% wide band. The stricter simulator report still has matchup/class-average violations, notably knight at 75.3% and bride at 24.0%; this task did not change page numbers to tune those balance results.

**Final status:** `test_sim_balance: all 28 tests passed`; `test_properties: all 6 properties passed`.

## Not verified

The complete JavaScript suite and the complete non-socket Python suite did not run because both shell-loop commands were denied before permission was answered. The focused affected JavaScript tests and relevant Python hash/flight/hero-sync checks above did run successfully. Main-line re-verification and its `docs/kiro_verified.json` update remain required.
