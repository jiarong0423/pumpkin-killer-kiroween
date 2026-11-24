# Task 166 result — gpt-5.6-terra

## What changed
- `js/knockback.js`: added global `Knockback`, `ZONES`, `eligible`, and `apply` for the decided 50 px, zone-clamped direct-hit rule.
- `scripts/test_knockback.js`: added 300 seeded direction and boundary cases plus fatal/fence/ground/shield rejection checks.
- `js/boomerang.js`: added global `Boomerang.resolve`; outbound hits pierce living targets, ignore shields, and return over the reversed outbound polyline at the INVENTED 1400 px/s speed.
- `scripts/test_boomerang.js`: added ordering, shield, no-hit, reverse-path timing, purity, and 300 seeded cases.
- `js/ultimate_fx.js`: set `HUNCHBACK_NORMAL_DAMAGE` to 21; added `hunchbackBoomerang` / `hunchback_boomerang`; retained compatible `hunchbackTowerToll`.
- `js/particles.js`: added `axe_spin_trail` and `boomerang_return`; corresponding coverage is in `scripts/test_particles.js`.
- `scripts/test_ultimate_fx.js`: added the boomerang timeline test for phases, 21/31.5 damage, 1.5x return cap, and preset availability.

## Verification commands and final output
- `node scripts/test_knockback.js` → `test_knockback: all 3 tests passed`
- `node scripts/test_boomerang.js` → `test_boomerang: all 6 tests passed`
- `node scripts/test_ultimate_fx.js` → `test_ultimate_fx: all 12 tests passed`
- `node scripts/test_particles.js` → `67/67 properties passed`
- `git diff --check` exited 0 with no output.

## Not verified
- The browser integration and projectile-loop wiring are owned by the main line and were not changed or browser-tested.
- The 1400 px/s return speed is explicitly INVENTED by this task brief and still needs owner confirmation.
