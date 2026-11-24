# Arbitration result, 2026-11-16 (seven arbiters + one coverage auditor, majority per item; owner told us to decide by sub-agent arbitration and implement)

Sources: arbiter reports on the fix list (3), asset list (3), full sweeps of gameplay, UI/phone, MCP/relay/tests (3) and the coverage auditor. Numbers marked "est" are hand or proxy-simulation estimates; every changed number is re-measured with `scripts/sim_balance.js` and the harness before it is called final.

## Batch 1: page-only, low risk (implemented in this order, each with the tests named)
| Item | Votes | Decision |
|---|---|---|
| Built-in opponent: use the wind the gauge shows (storm included) | bug found by arbiter 2, nobody objected | DO (`effWind()` in the AI's wind read) |
| Opponent noise | cut hard (150/1.2/6 to 90-100/0.8/4) vs proxy sim says already 49% | CHANGE small: position noise 150 to 120, wind noise 1.2 to 1.0, aim error stays 6; measure the real hit rate afterwards |
| Enemy wind-up readable | arbiter 3, UI sweep | DO: charge held 0.9 s instead of 0.6 s |
| Bride swarm radius 40 | 46 / 55 / 75 | 55 (median; module, page and test changed together) |
| Knight bounce loses damage on the fence | 2 of 3 | DO: a fence bounce no longer uses a collision (at most 2 per throw) |
| Uniform hit feedback | 3 of 3 | DO: hit burst scales with the throw damage; knight bounce hits show the burst |
| HP bar size | 135 to 154 wide, 12 to 14 high | 150 x 13 with a thin outline |
| Poison green tint over the whole sprite | arbiter 3, UI sweep | CHANGE: lower alpha, only while poisoned |
| First-round wind always 2.4 | 3 of 3 DO | DO, from the match seed |
| Necromancer burn (2 damage, 3 round starts, never lethal) | 2 DO, 1 SKIP | DO (matches `js/class_stats.js` BURN_TURNS 3) |
| Nun stun marker | 2 SKIP, 1 small change | SKIP (stars and the stun word already exist) |
| Hammer boomerang blocked by the floating shield | gameplay sweep | DO: `!p.ultBoom` in the shield check |
| Wind gauge uses the effective wind | gameplay + UI sweeps | DO |
| A tap shorter than 0.25 s or under 12 power cancels | UI sweep | DO |
| Both sides of the hunchback mirrored | owner 2026-11-16 | DONE (`ART_FACES_RIGHT.unit_hunchback = true`) |

## Batch 2: balance (owner: some heroes high HP, some high attack; eight heroes are enough)
Medians of the four tables (the three arbiters and the gameplay sweep). Ultimate multipliers are NOT changed in this batch (they are pinned by several tests and the sweep measured them on a small sample); only hp, normal damage and the named special numbers.
| Hero | Archetype | hp | normal dmg | special |
|---|---|---|---|---|
| knight | tank | 120 to 140 | 30 | fence fix raises the real damage |
| hunchback | tank/bruiser | 110 to 115 | 21 | |
| nun (hag) | control | 95 to 105 | 22 to 24 | ultimate hit factor 0.5 to 0.575 |
| skeleton | balanced | 100 | 24 to 22 | |
| bat | control | 90 to 95 | 22 | |
| reaper | balanced, narrow | 105 to 95 | 23 to 22 | hit half-width 50 to 57, burn |
| bride | glass cannon | 75 to 70 | 25 to 28 | swarm radius 55 |
| wizard | glass cannon | 85 to 75 | 24 to 30 | |
Same-change list: `index.html` HERO_PROFILES, reaper hit width, `js/class_stats.js`, `js/nun_ult.js`, `js/ultimate_fx.js` constants, `scripts/test_class_stats.js`, `test_sim_balance.js`, `test_nun_ult.js`, `test_ultimate_fx.js`, `scripts/make_roster_json.py` output, `docs/character_plan_20261116.json`.

## Not done now (needs an owner decision, risk, or a larger feature)
- Free player-only skills (heal 2x35, double shot, heavy shot) have no AI equivalent: the gameplay sweep calls this the biggest cause of 9 wins out of 9 and of unfairness for two humans. Owner call: make them symmetric, one use each, costing the turn?
- Ultimate multipliers: skeleton and bat ultimates measure about equal to a normal hit; wizard ultimate 60 total, necromancer 45 plus a skipped turn, nun weakest; the sweep proposes 2.0x for skeleton/bat/hunchback/bride/wizard, 1.56x necromancer, nun 1.8x. Owner call.
- Dice-move landing corners that cannot be hit; storm wind bonus 1.5 to 1.0 (touches the weather golden vectors).
- Seat assignment (human / agent / built-in on both sides), relay client in the page, deterministic seed contract (wind, start, dice), shared hero table, status words in the round hash, engine with 8 heroes: big features, ordered A to I in the MCP sweep; they come after the batches above.
- Phone: portrait is unplayable (393 px wide), canvas text too small in landscape, preload gate waits for 95 images (86 MB transferred). UI sweep P0/P1 list, next batch after balance.
- Licence paperwork, README rewrite, public-export hygiene (listed in `docs/GAP_STATUS_20261116.md`).
