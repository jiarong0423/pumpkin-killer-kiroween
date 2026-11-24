# Wave 1 + round 2: browser-free harness for the team-battle rules (QA)

Files (new only): `scripts/page_harness.js`, `scripts/test_page_team_exec.js`, this report. `index.html` and all other files untouched; no commit, no network.

## How it works
`loadPage({team, search, storage, storageBlocked, mutate})` runs every `<script src="(not published)">` of the page (read from index.html, so `js/team_tuning.js` is picked up in page order) and the REAL inline script in one Node `vm` (DOM/canvas/Audio/Image/URL stubs, queued timers that never run, `fetch` never settles, seeded `Math.random`, weather pinned to clear, `#team-size` buttons as capturing stubs, `localStorage` seedable or blocked). Page top-level `let/const` stay reachable via later `vm.runInContext`, so tests read/write the real `teams`, `projectiles`, `gameOver`, `roundNum`, `diceRoll` and call the real functions. **No export hook is needed.** Run: 0.3 to 1 s, 10/10 identical runs, writes nothing (log to `(not published)` only on failure).

## Executed now (real functions, real objects)
- Rotation (`rotateTeam`, `nextLivingAfter`, `rotateAfterTurn`, `ensureLivingActive`), `teamDown` and last-kill `gameOver` (shot and blast), nearest-living-box hit loop, thrower-team rotation after a landed shot
- Area effects: wizard blast 234 px, bride wave 100/75/50 by own distance + poison, bat swarm on every living enemy (and none at 60 px)
- `aiTarget`, `reportTarget`, move clamp 120 px in `stepDice` (both teams, dead mate, zone floor), status ticks on benched units (`resolveRound`), interpolation/resupply of all units, end to end `executeThrow` -> physics -> rotation
- NEW (1) team hp: `applyClassStats` for N = 1/2/3 x all 8 heroes, both sides, hp = maxHp = value computed from `shared/team_tuning.json` (independent of the js module); N = 1 plain hero hp; `switchHero` refills ALL left units
- NEW (2) ramp: real hit, blast, wave primary + splash, swarm at rounds 8/9/12 (x1/1.08/1.32), N = 2 and 3; N = 1 at round 12 unchanged
- NEW (3) round cap: N = 2 (18) and N = 3 (20): winner mapped to player/ai (left ahead, right ahead, tie -> right), toast `team.roundCap`, `turn = "over"`, early return (no new wind), cap-1 goes on, finished match not re-decided; N = 1 at round 100: nothing
- NEW (4) selector: `pk_team_n` without `?team=` -> TEAM_N, URL wins, junk -> 1, clamp 3, blocked storage; real click handler writes storage and sets `location.href` to `?team=N`, no-op on the current size, works with blocked storage; aria-pressed
- NEW (5) double shot: real `releaseAndThrow` + queued 260 ms shell run after `rotateTeam`: second shell leaves the first thrower (x 358, not the rotated unit), rotated unit stays armed, power x 1.04

## Negative checks
88 checks, 65 of them mutants (one exact text edit each, e.g. `.every`->`.some`, `[player].forEach`, `rampDmg = x => x`, cap `> 1000`, no `return`, no `localStorage.setItem`, `, unit` dropped). Each MUST fail with an AssertionError; a wrong-reason death or a missing mutation target fails the test (the strings are exact substrings of index.html: a rewrite of those lines shows MUTATION_NOT_FOUND).

## Still only regex (`scripts/test_team_rules.js`)
Rule 1 declarations, rule 2 drawing (benched unit stands still, ring colours), `rotateAfterTurn` call-site count, the AI's own double-shot call (`queueAiThrow`, same pattern, not driven), start-screen DOM markup/i18n keys of `#team-size`, `team.ramp` toast. Nothing is trapped in a closure.

## Last lines of the run (exit 0)
```
ok   - double shot: ... [negative: the thrower argument is dropped from the queued shell must be caught]
ok   - double shot: ... [negative: executeThrow ignores the thrower argument must be caught]
ok   - end to end: the real executeThrow builds p, the real physics lands it, the thrower team rotates (no projectile hand-built)
test_page_team_exec: 88 ok, 0 failed (1.4 s)
```

## Round 3 (tuning change, opener, comeback)
- Tuning-proof: hp scale, floor, ramp start/per_round and round caps are read from `shared/team_tuning.json` (rounds start-1, start, start+3; ramp toast when entering start_round). The two failures were hard-coded 0.45 / round 9 / 1.08 / 1.32. Changing the json (and `js/team_tuning.js`) no longer needs a test edit.
- NEW opener: `openerOfRound` (null = left always opens; coin via real `beginOpeningTurn`), `routeAfterTurn` and `advanceAfterAttack` (timer function and delay checked), `resolveRound` starting the right side in its opener rounds (`triggerAITurn` replaced by a counter); N = 1 keeps the old order even with `firstOpener = "ai"`. 6 mutants.
- NEW comeback: real hit = base x min(2.3, underdog x (1 + pity)): x1, x2, x1.5, x1.8, x2.1 (below cap), capped 5.2/2.8/2.6 -> x2.3; pity reset after the hit; wave primary + swarm on far units use the capped numbers; N = 1 none. 6 mutants (module `js/comeback.js` cap constant / no `Math.min`, page uncapped formula, page ignoring it, comeback at N = 1, swarm skipping it). Harness got `mutateFiles` for module mutants.
- Not executed: nun pierce, daily match (`test_page_wave2a.js` is the other engineer's, 14 passed), near miss, pity counting of missed throws.
- Run: `node scripts/test_page_team_exec.js` 88 ok, 0 failed, 1.4 s, 10/10 identical runs.
