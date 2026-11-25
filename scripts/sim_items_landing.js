'use strict';
// Item (airdrop supply) landing, pickup and use, judged on the REAL inline script of index.html (scripts/page_harness.js, no browser, nothing written).
// Prints one JSON summary and one RESULT line; exit 1 on any violation.   usage: node scripts/sim_items_landing.js [--seeds 400] [--json out.json]
// Checks: (0) the crate lies where a unit of that side may STAND (the same limits the dice move clamps to), so it can always be picked up,
//             and not already under the unit it is dropped for (a crate is walked to, not handed over);
//         (1) the crate target x lies inside the canvas margin, never on or past the fence, on the side of the unit it is dropped for;
//         (2) distance from that unit stays reachable (one move is about 286 px, pickup radius 70 px);
//         (3) after the parachute descent the crate rests exactly at target x and at GROUND_Y - 20;
//         (4) a unit inside 70 px takes it, a unit outside does not; (5) heal adds 45 and never exceeds max hp, heavy adds one charge,
//         the slot empties; a newer pickup replaces the item; (6) item mix (heal/heavy) and side alternation over many seeds.
const { loadPage } = require('./page_harness');
const argv = process.argv;
const arg = (k, d) => { const i = argv.indexOf('--' + k); return i > 0 ? argv[i + 1] : d; };
const SEEDS = +arg('seeds', 400), JSON_OUT = arg('json', null);
const MOVE_REACH = 286, PICKUP = 70;
const violations = [];
const bad = (msg) => { if (violations.length < 40) violations.push(msg); };
const stats = {};

for (const team of [1, 2, 3]) {
  const MUTANTS = { '--mutant-band': [['const [lo, hi] = MOVE_ZONE[dropSide > 0 ? "player" : "ai"];', 'const [lo, hi] = dropSide > 0 ? [0, FENCE_X - FENCE_W / 2 - 60] : [FENCE_X + FENCE_W / 2 + 60, CANVAS_W];']], '--mutant-far': [['Math.round(210 + dice.offset * 0.575)', 'Math.round(510 + dice.offset * 0.575)']], '--mutant-fence': [['x = Math.max(lo, Math.min(hi, x));', '']] };   // negative controls: each MUST fail
  const mut = Object.keys(MUTANTS).find(k => argv.includes(k));
  const P = loadPage(mut ? { team, mutate: MUTANTS[mut] } : { team });
  const W = P.get('CANVAS_W'), FX = P.get('FENCE_X'), FW = P.get('FENCE_W'), GY = P.get('GROUND_Y');
  const lo = FX - FW / 2 - 60, hi = FX + FW / 2 + 60;
  // the zone is measured on the real page: roll the largest die both ways from the middle of each side and read where the unit stops
  const ZONE = {};
  for (const [side, owner] of [['left', 'player'], ['right', 'ai']]) {
    ZONE[side] = [1, -1].map(dir => {
      P.eval('resetGame(); TEAM_N > 1 && unitsOf("' + side + '").slice(1).forEach(u => { u.hp = 0; }); diceRoll = null;');
      P.place(side, [side === 'left' ? 400 : W - 400]);
      for (let i = 0; i < 12; i++) P.eval('startDiceRoll("' + owner + '", ' + dir + ', function () {}); diceRoll.final = 6; for (let k = 0; k < 300 && diceRoll; k++) stepDice(1/60); unitOf("' + side + '").x = unitOf("' + side + '").targetX;');
      return P.eval('unitOf("' + side + '").targetX');
    }).sort((a, b) => a - b);
  }
  const s = stats['team' + team] = { zoneLeft: ZONE.left.join('..'), zoneRight: ZONE.right.join('..'), outOfZone: 0, underUnit: 0, drops: 0, heal: 0, heavy: 0, sideLeft: 0, sideRight: 0, maxDist: 0, minDist: 1e9, beyondReach: 0, restX: 0, alternationBreaks: 0, xMin: 1e9, xMax: -1e9 };
  for (let seed = 1; seed <= SEEDS; seed++) {
    P.eval('resetGame(); matchSeed = ' + seed + '; carrier = null; drops = []; dropSide = -1; dropCount = 0; supply.player = null; supply.ai = null; cratesTaken.player = 0; cratesTaken.ai = 0;');
    let lastSide = 0;
    for (let round = 2; round <= 24; round += 2) {
      // unit positions: a spread across each side's legal half so clamps and the fence margin are exercised
      const lx = ZONE.left[0] + ((seed * 53 + round * 31) % (ZONE.left[1] - ZONE.left[0] + 1)), rx = ZONE.right[1] - ((seed * 71 + round * 17) % (ZONE.right[1] - ZONE.right[0] + 1));
      P.place('left', [lx]); P.place('right', [rx]);
      P.eval('roundNum = ' + round + '; carrier = null; drops = [];');
      P.eval('scheduleAirdrop()');
      const car = P.eval('carrier');
      if (!car) { bad('team' + team + ' seed' + seed + ' round' + round + ': no crate scheduled'); continue; }
      s.drops++;
      const side = P.get('dropSide'), unitX = side > 0 ? lx : rx, x = car.targetX, item = car.item;
      s[item] = (s[item] || 0) + 1; if (side > 0) s.sideLeft++; else s.sideRight++;
      if (lastSide && side === lastSide && team === 1) s.alternationBreaks++;
      lastSide = side;
      s.xMin = Math.min(s.xMin, x); s.xMax = Math.max(s.xMax, x);
      const zone = side > 0 ? ZONE.left : ZONE.right;
      if (x < zone[0] || x > zone[1]) { s.outOfZone++; if (s.outOfZone <= 3) bad('team' + team + ' seed' + seed + ' round' + round + ': crate x ' + x + ' where no unit of that side may stand (' + zone.join('..') + ')'); }
      if (Math.abs(x - unitX) <= PICKUP) { s.underUnit++; if (s.underUnit <= 3) bad('team' + team + ' seed' + seed + ' round' + round + ': crate ' + Math.round(Math.abs(x - unitX)) + ' px from its unit, taken without a move'); }
      if (!(x >= 300 && x <= W - 300)) bad('team' + team + ' seed' + seed + ': crate x ' + x + ' outside 300..' + (W - 300));
      if (x > lo && x < hi) bad('team' + team + ' seed' + seed + ': crate x ' + x + ' on the fence band ' + lo + '..' + hi);
      if (side > 0 && x > lo) bad('team' + team + ' seed' + seed + ': left-side crate past the fence ' + x);
      if (side < 0 && x < hi) bad('team' + team + ' seed' + seed + ': right-side crate past the fence ' + x);
      const dist = Math.abs(x - unitX); s.maxDist = Math.max(s.maxDist, dist); s.minDist = Math.min(s.minDist, dist);
      if (dist > MOVE_REACH + PICKUP) { s.beyondReach++; if (s.beyondReach <= 3) bad('team' + team + ' seed' + seed + ' round' + round + ': crate ' + Math.round(dist) + ' px from its unit (reach ' + (MOVE_REACH + PICKUP) + ')'); }
      if (item !== 'heal' && item !== 'heavy') bad('unknown item ' + item);
      // fly and drop with the page's own step until the crate lands
      for (let i = 0; i < 1200 && P.eval('drops.length === 0 || !drops[0].landed'); i++) P.eval('updateAirdrop(1/60)');
      const d = P.eval('drops[0]');
      if (!d || !d.landed) { bad('team' + team + ' seed' + seed + ': crate never landed'); continue; }
      if (Math.abs(d.x - x) > 1e-6 || Math.abs(d.y - (GY - 20)) > 1e-6) bad('team' + team + ' seed' + seed + ': rest point ' + d.x + ',' + d.y + ' differs from target ' + x + ',' + (GY - 20));
      s.restX++;
    }
  }
  // pickup radius and use (one fresh match per case)
  const pick = (dx, hpAi) => {
    P.eval('resetGame(); carrier = null; supply.player = null; supply.ai = null; cratesTaken.player = 0;');
    P.place('left', [400]); P.place('right', [W - 400]);
    P.eval('drops = [{ x: 400 + (' + dx + '), y: ' + (GY - 20) + ', vy: 0, landed: true, item: "heavy", born: roundNum, chute: 0 }]');
    P.eval('updateAirdrop(1/60)');
    return P.eval('supply.player');
  };
  for (const [dx, want] of [[0, 'heavy'], [69, 'heavy'], [-69, 'heavy'], [71, null], [-71, null], [200, null]]) {
    const got = pick(dx); if (got !== want) bad('team' + team + ': pickup at dx ' + dx + ' gave ' + got + ', want ' + want);
  }
  // heal never over max, adds 45; heavy adds a charge; slot empties; replacement
  for (const hp of [1, 50, 100, 140, 159]) {
    P.eval('resetGame(); turn = "player"; gameOver = null; isCharging = false; seats = { left: "human", right: "ai", level: seats.level };');
    P.place('left', [400]); const u = P.eval('unitOf("left")'); u.hp = Math.min(hp, u.maxHp); const before = u.hp, max = u.maxHp;
    P.eval('supply.player = "heal"; useSupply()');
    const after = P.eval('unitOf("left")').hp, want = Math.min(max, before + 45);
    if (after !== want) bad('team' + team + ': heal from ' + before + '/' + max + ' gave ' + after + ', want ' + want);
    if (P.eval('supply.player') !== null) bad('team' + team + ': slot not emptied after heal');
  }
  { P.eval('resetGame(); turn = "player"; gameOver = null; isCharging = false; seats = { left: "human", right: "ai", level: seats.level };');
    const before = P.eval('skillChargesOf("left").heavy'); P.eval('supply.player = "heavy"; useSupply()');
    const after = P.eval('skillChargesOf("left").heavy');
    if (after !== before + 1) bad('team' + team + ': heavy charges ' + before + ' to ' + after);
    if (P.eval('supply.player') !== null) bad('team' + team + ': slot not emptied after heavy');
    P.eval('supply.player = "heavy"; isCharging = true; useSupply()');
    if (P.eval('supply.player') !== 'heavy') bad('team' + team + ': supply used while charging (must be locked)');
  }
}
const out = { seeds: SEEDS, stats, violations, violationCount: violations.length };
if (JSON_OUT) require('fs').writeFileSync(JSON_OUT, JSON.stringify(out, null, 1));
console.log(JSON.stringify(out.stats));
violations.slice(0, 15).forEach(v => console.log('VIOLATION ' + v));
console.log('RESULT ' + (violations.length ? 'FAIL ' + violations.length + ' violations' : 'PASS 0 violations'));
process.exit(violations.length ? 1 : 0);
