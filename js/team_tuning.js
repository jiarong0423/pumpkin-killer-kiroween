/* Team-match tuning (pure, no DOM): unit HP scale, late-round damage ramp and the round cap for 2 and 3 units per team.
   One unit per team: every function returns the neutral value, so the one-versus-one game is untouched.
   Constants come from shared/team_tuning.json (copied here and pinned equal by scripts/test_team_tuning.js). Python twin: scripts/team_tuning_py.py. */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) module.exports = api;
  else root.TeamTuning = api;
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  var HP_SCALE = { 2: 0.90, 3: 0.95 };
  var HP_FLOOR_HITS = 2.5;
  var RAMP_START = 13, RAMP_PER_ROUND = 0.08;
  var ROUND_CAP = { 1: 40, 2: 24, 3: 28 };   // 1: the duel limit (owner 2026-11-17: with the weaker computer 8 of 20,016 duels ran past 60 rounds without a winner)

  function teamMaxHp(hp, dmg, n) {
    if (n !== 2 && n !== 3) return hp;
    return Math.round(Math.max(hp * HP_SCALE[n], HP_FLOOR_HITS * dmg));
  }
  function rampMultiplier(round, n) {
    if (n !== 2 && n !== 3) return 1;
    if (round < RAMP_START) return 1;
    return Math.round((1 + RAMP_PER_ROUND * (round - (RAMP_START - 1))) * 1e6) / 1e6;
  }
  function roundCap(n) { return n === 1 || n === 2 || n === 3 ? ROUND_CAP[n] : Infinity; }
  // Winner when the cap is passed: 'left' | 'right'. teams = { left: [{hp, maxHp}], right: [...] }.
  function capWinner(teams) {
    function share(units) {
      var hp = 0, max = 0, alive = 0;
      units.forEach(function (u) { max += u.maxHp; if (u.hp > 0) { hp += u.hp; alive++; } });
      return { share: max > 0 ? hp / max : 0, alive: alive };
    }
    var l = share(teams.left), r = share(teams.right);
    if (l.share !== r.share) return l.share > r.share ? 'left' : 'right';
    if (l.alive !== r.alive) return l.alive > r.alive ? 'left' : 'right';
    return 'right';
  }
  return { teamMaxHp: teamMaxHp, rampMultiplier: rampMultiplier, roundCap: roundCap, capWinner: capWinner,
    CONSTANTS: { HP_SCALE: HP_SCALE, HP_FLOOR_HITS: HP_FLOOR_HITS, RAMP_START: RAMP_START, RAMP_PER_ROUND: RAMP_PER_ROUND, ROUND_CAP: ROUND_CAP } };
});
