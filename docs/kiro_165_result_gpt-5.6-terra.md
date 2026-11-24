# Task 165 result — gpt-5.6-terra

## What changed
- Added `js/sound_wave.js` (`SoundWave.damageAt`, `SoundWave.pickTarget`, `HIT_HALF_WIDTH`, and stepped `BANDS`) and `scripts/test_sound_wave.js` with 300 seeded cases.
- Updated `js/ultimate_fx.js`: `BRIDE_NORMAL_DAMAGE = 25`; added `brideBatSwarm` and the `bride_bat_swarm` timeline. It requires `hitDistance` strictly inside 40 px, emits a 25-damage precise hit, then one non-blockable 32.5-damage swarm event per supplied enemy. The timeline deduplicates repeated enemy IDs.
- Retained `brideSoulDirge` and its existing tests.
- Added deterministic `bat_swarm` preset to `js/particles.js`, and coverage in `scripts/test_particles.js` and `scripts/test_ultimate_fx.js`.

## Verification commands
```text
node scripts/test_sound_wave.js
node scripts/test_ultimate_fx.js
node scripts/test_particles.js
node scripts/test_class_stats.js
git diff --check
```

## Actual final output
```text
test_sound_wave: all 7 tests passed
test_ultimate_fx: all 11 tests passed
65/65 properties passed
test_class_stats: all 12 tests passed
git diff --check: exit code 0 (no output)
```

## Not verified / open questions
- No browser or `index.html` wiring was performed or tested. The page must calculate and pass `hitDistance`, supply living enemies, and apply poison after `SoundWave.pickTarget` selects the target.
- The 40/75/105 px stepped-band boundaries are marked INVENTED in code, as required by the brief.
- Main-line verification remains required.
