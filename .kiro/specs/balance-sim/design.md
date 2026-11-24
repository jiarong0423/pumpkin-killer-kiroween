# Design: balance simulator

## Shape

```
scripts/sim_balance.js
  UMD factory(ClassStats, Ultimate)      node: require('../js/class_stats.js'), require('../js/ultimate.js'); browser: globals
    simulateLandingX / solvePower        the bot's aiming model, same steps as the projectile
    makeProjectile / stepProjectile      one physics step, fence -> unit -> ground
    resolveThrow                         plays every projectile and every timed follow-up hit
    takeTurn                             aim, maybe move, maybe volley, throw
    simulateMatch(options)               one match
    runPairings(options)                 all pairs, matrices, bands
    formatReport(result)                 the text the command line prints
  command line (Node only)               --matches --seed --table --aim-error --max-rounds --classes --shield-rule --wave-rule --json
```

All randomness comes from one `mulberry32(seed)` per match, drawn in a fixed order (start positions, then per round: wind, then per throw: move die, aim error, shield die, volley jitter). `runPairings` gives each match its own seed with `mixSeed(seed, i, j, match)`.

## Same as index.html, and how it is checked

The test reads `index.html` and checks the source of every number it uses: `WIND_ACCEL`, `GRAVITY`, `GROUND_Y`, fence size, the 13.8 launch factor, the `<= 70` / `190` hit box, `wallHp - 15`, the wind reroll, the move limits, the start ranges, the hop numbers of the knight (0.12, -330, 0.42, 0.55, 0.3, -90), the muzzle offsets. If a line moves, the test fails and the simulator has to be re-read.

## Decisions

| Question | Choice | Why |
|---|---|---|
| Who aims | A bot with exact wind and target knowledge plus a uniform power error | Same as the playtest bot and the in-page AI; the error (`aimError`) is the only skill knob. Default 9 reproduces the 52% hit rate that `index.html` quotes for error 9 (measured here: 55%). |
| Movement | Only the forward die when full power falls short | The slow classes cannot cross the field otherwise. The hunchback moves in 22% of its throws, the bride in 7%. A free tactical move is not modelled. |
| Draws | Counted as half a win; a timeout is decided by HP share | No timeouts happened in any reported run. |
| Alternating sides | match by match inside a pairing | Cancels the first-mover advantage between two different classes; the mirror match reports it (the left side won 47 to 67% of mirror matches per class, 57% on average, 200 matches each, so the noise is large). |
| Ultimates | Only the cat's volley is played; the other classes' pips are counted by the ledger and never spent | The task lists only the cat's volley. The ledger is the real `js/ultimate.js`, so the rules (3 pips, 2 uses, once per round, arm before use, no pip from the ultimate throw) are the real ones. |
| Knight rule | `current` is the default | `docs/class_stats_judgement.md` says do not touch the knight before the robot run. `A` is available because the brief says "the rules you recommended"; at a total of 30 it is far too strong (92% average), it was designed around 22. |
| Wave distance | `first_contact` is the default; `centre` is an option | The judgement defines it at first touch. With a 190 px tall box the first touch is almost always near the edge, so her average damage per hit is 18 and not 22.4. `centre` measures at body-centre height (20 to 23). The option exists to show that this is not the main reason the bride loses. |
| Provisional bride | Bouquet bursts on landing | `docs/converge_characters.md` (invented) describes a 90 px burst. |
| Band check | The two win-rate bands decide `pass` | The brief names the 40 to 60 band. The class-average band (45 to 55) is in the judgement section 8. The match length is informational because it depends on `aimError`. |

## Cost

5600 matches (200 per pairing, 28 pairings) take a few seconds. Each solve bisects 30 times over about 150 steps.

## Not covered

- Sky shield, airdrops, heal and skills, 4 v 4, human behaviour (a human does not know the wind exactly).
- The in-page AI (`aiAttackNow`) uses `Math.random` and a fixed 54 degrees; the simulator's bot also uses 54 but a seeded generator.
- A statistical test beyond the plain band: 200 matches give about +-3.5 points (one standard deviation), so a win rate near 40 or 60 is a coin flip about the band.
