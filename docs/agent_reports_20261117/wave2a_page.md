# Wave 2a page report (2026-11-17), page engineer
Files changed: index.html, assets/i18n/en.json + zh-TW.json (5 new keys each, equal), sw.js (only via make_sw_precache --apply), new test (not published) No commit, no push, no network.

## What changed (all new rules guarded by TEAM_N > 1)
- P1 comeback: `<script src="js/comeback.js">` after team_tuning. New helpers next to `rampDmg`: `cbBegin`, `cbDmg` (always `Comeback.finalDamage`, so the 2.3 cap applies everywhere), `cbThrowEnded`, `cbNearMiss`; state `pityMisses`, `throwHadHit`. Hooks: direct hit (after `dmgNow = rampDmg`), wave splash, swarm, wizard blast, boomerang return hit, nun second contact, near miss at ground contact (skipped for ultimate throws and the wave), miss counting where a projectile leaves the list. Reset in `resetGame` beside `cratesTaken`. Text: "Comeback +X%" (real combined % after the cap) on a hit, "Pity +X%" when a miss raises the charge, near-miss "-dmg" text. Keys: team.comeback, team.pity, team.nearMiss.
- P2 opener: `firstOpener` (set in `beginOpeningTurn`), `openerOfRound`, `routeAfterTurn`, `beginLeftTurnMidRound`, `leftTurnStatuses` (the stun/shock/slow block moved out of resolveRound into a function, called at the same place for N=1). Routed: `advanceAfterAttack`, timeout, player defend, AI defend, AI hallucination skip, dice move; resolveRound tail starts the right side (`triggerAITurn`, which covers human-right curtain and agent wait). Left agent/AI seat covered in `beginLeftTurnMidRound`. `firstOpener` is null until a coin is tossed = old order (left opens every round).
- P3 daily: footer button `#daily-btn` (right of Start, x 522..672, y 305..349 in the fixed 800x360 box), `dailySeedOf` (UTC yyyymmdd), `startDailyMatch` (room-start seed path then `startMatch`), `syncDailyButton` (disabled for rooms/non-AI seats), AI hero from the seed, code shown in the result panel (`daily.code`), cleared in `resetGame`. Keys: start.daily, daily.code. No layout redesign needed.
- P4 nun pierce: team matches only; `p.pierced`/`p.nunTouched`, cross continues until 3 distinct units, 2 contacts each; `nunPierceFinish` calls `NunUlt.resolve` over the contact order for the one stunned unit.

## Tests (last lines, all run here)
test_page_team_exec: 74 ok, 0 failed | test_page_wave2a (new): 14 checks passed (incl. 5 mutants) | test_team_rules 10/10 | test_decisions_frozen 10/10 | test_size_frozen 5/5 | test_phone_layout 9/9 | test_ui_polish 6/6 | test_i18n 26 passed (284 keys) | test_orientation_frozen 5/5 | test_side_choice passed | test_pwa_files OK (3) | test_comeback 5/5 | test_team_tuning 5/5.
Layout measured in Chrome pane at 800x360: daily button [522,305,672,349], Start [290,305,510,349], team-size [310,110,490,154], no overlaps among 8 elements.

## Pinned lines
None moved or rewritten. Swarm: the pinned `v.hp = Math.max(0, v.hp - swarm);` stays and a new line subtracts the extra (`swarmExtra`). `teamDown(sideOfUnit(` count stays 4 (near miss uses a local). Round-cap test (line ~383) only passes because firstOpener defaults to null.

## Not verified / open
- `node scripts/record_match_transcript.mjs` cannot run in my sandbox (EPERM socket): N=1 identity rests on the guards; owner must run it.
- test_fonts.py still fails (4): characters 提賽較隊 from the existing keys team.roundCap/ramp/teamSize, not from mine (my zh strings use only charset characters). Needs scripts/build_fonts.py (not my file).
- Relay phase and Python engine/MCP do not know the alternating opener or the comeback numbers (page only); relay `phase`/round could disagree in team rooms.
- Wind after round 1 is Math.random (existing), so the daily match fixes wind of round 1, starts, weather, crates, coin, opponent hero only.
- Choices: a double shot counts as two throws for pity; a blast that burns a unit counts as a hit; near miss gets no underdog/pity; boomerang return now also takes the late ramp in team matches.
