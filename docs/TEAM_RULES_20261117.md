# Team battle rules and plan (2026-11-17)

Rules as built and as decided from the owner's messages today. Source for each: the code named in brackets.

1. **One active unit per team.** The yellow ring marks it. The whole screen follows that unit: top plate and HP, the dock (angle, power, items, skills), aiming, movement, crate pick-up. [`setActiveUnit`, `player` and `ai` point at the active unit]
2. **Units not on turn sit out.** They stand still in the idle pose, do not move, throw or pick up crates. [`computePose` idle branch]
3. **Rotation.** After a team has thrown, its next living unit in fixed id order becomes active; a unit that fell while waiting is skipped without changing the order of the others. [`rotateTeam`, `nextLivingAfter`; same rule in `scripts/mcp_stdio_server.py` `_active_unit`]
4. **Judgment is per unit, in world coordinates.** A shot hits the first living enemy unit it touches (nearest to the path when two boxes are touched in one step); box 70 x 190 (reaper 57 x 165) plus the drawn projectile radius. Teammates never block their own shots. [`touches`, `foes`]
5. **Area effects hit every living enemy unit in range, each once per attack, by its own distance.** Built for the wizard blast (234 px). Not yet built for the bride wave, the bat swarm and the nun cross, which still hit only the unit that was touched. [`ultBlast` block]
6. **Status effects** (poison, bleed, burn) tick on every unit of both teams at each round start; slow ends for the unit that acted. [`resolveRound`]
7. **The match ends when a whole team has no living unit.** The check runs after all damage of one attack. [`teamDown`]
8. **Team tuning (2 or 3 units per team only; one unit per team never reads it).** Unit hp = round(max(hero hp x 0.60 for 2 units or x 0.45 for 3, 2.5 x hero dmg)); from round 9 every hit is multiplied by 1 + 0.08 x (round - 8); round limit 18 (2 units) or 20 (3 units): the team with the larger HP share wins, then more living units, then the right side. Source: `shared/team_tuning.json`, `js/team_tuning.js`, `scripts/team_tuning_py.py`, vectors `shared/team_tuning_vectors.json`. [`unitStartHp`, `rampDmg`, `resolveRound`]
9. **Team size is chosen on the start screen (1v1, 2v2, 3v3).** The choice is saved in localStorage and the page reloads with `?team=N`; online rooms and MCP seats still carry one unit per side until the relay hooks are applied. [`#team-size`]
10. **Not yet decided (owner):** whether a throw-less turn (timeout, defend) also passes the turn to the next unit; whether the player may choose the unit instead of the fixed rotation.

Plan: area effects for wave, swarm, cross; per-unit item rules and crate sides (3b); HUD avatar row (4); start-screen team size (5); AI aims at the best enemy unit (6); relay and MCP unit ids and round hash (8). Checkpoint 2026-11-25: the stage reached ships; one unit per team is always stable.
