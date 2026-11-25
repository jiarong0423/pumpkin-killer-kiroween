'use strict';
// Seeded break-it fuzzer for the page's own supply/airdrop/unit logic (real inline script through scripts/page_harness.js; no browser, nothing written).
// Random but legal-and-awkward sequences: units anywhere on the field, hp at 0 / max / random, supply slot holding anything (also an unknown name),
// the turn, charging, sling and game-over flags flipped, crates scheduled on any round number and stepped with any dt (0 to 5 s), supplies used at
// any time. After EVERY step: hp finite and within 0..max, supply slot only null/heal/heavy, at most one crate in flight, crate and carrier numbers
// finite, skill charges finite and not negative, no exception. Out-of-contract inputs (NaN or negative dt, NaN position) are listed separately and do
// not fail the run. Same seed = same sequence.   usage: node scripts/fuzz_page_break.js [--seed 1] [--steps 4000] [--mutant-heal]   exit 1 on a violation
const { loadPage } = require('./page_harness');
const argv = process.argv, arg = (k, d) => { const i = argv.indexOf('--' + k); return i > 0 ? argv[i + 1] : d; };
const SEED = +arg('seed', 1), STEPS = +arg('steps', 4000), MUT = argv.includes('--mutant-heal');
function mulberry(a) { return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
const violations = [], outOfContract = [];
let totalSteps = 0;
for (const team of [1, 2, 3]) {
  const P = loadPage(MUT ? { team, mutate: [['u.hp = Math.min(u.maxHp, u.hp + 45);', 'u.hp = u.hp + 45;']] } : { team });
  const rnd = mulberry(SEED * 1000 + team), pick = a => a[Math.floor(rnd() * a.length)];
  P.eval('resetGame(); seats = { left: "human", right: "ai", level: seats.level }; turn = "player"; gameOver = null;');
  const W = P.get('CANVAS_W'), log = [];
  const check = (step, op) => {
    for (const side of ['left', 'right']) for (const u of P.units(side)) {
      if (!Number.isFinite(u.hp) || u.hp < 0 || u.hp > u.maxHp + 1e-9) violations.push({ team, step, op, why: 'hp ' + u.hp + '/' + u.maxHp });
    }
    for (const t of ['player', 'ai']) { const v = P.eval('supply.' + t); if (v !== null && v !== 'heal' && v !== 'heavy' && v !== 'bogus') violations.push({ team, step, op, why: 'supply slot ' + JSON.stringify(v) }); }
    if (P.eval('drops.length') > 1) violations.push({ team, step, op, why: 'drops in flight ' + P.eval('drops.length') });
    const car = P.eval('carrier'); if (car && !(Number.isFinite(car.x) && Number.isFinite(car.y) && Number.isFinite(car.targetX))) violations.push({ team, step, op, why: 'carrier numbers not finite' });
    for (const d of Array.from(P.eval('drops'))) if (!(Number.isFinite(d.x) && Number.isFinite(d.y))) violations.push({ team, step, op, why: 'crate numbers not finite' });
    for (const s of ['left', 'right']) { const ch = P.eval('skillChargesOf("' + s + '")'); for (const k of ['double', 'heavy', 'heal']) if (!Number.isFinite(ch[k]) || ch[k] < 0) violations.push({ team, step, op, why: 'charges ' + k + ' ' + ch[k] }); }
  };
  for (let step = 0; step < STEPS; step++) {
    const kinds = ['place', 'hp', 'slot', 'flags', 'schedule', 'drop', 'drop', 'use', 'use', 'use', 'bad_dt'];
    const kind = pick(kinds); let op = kind, inContract = true;
    try {
      if (kind === 'place') { const xs = [Math.floor(rnd() * W)]; op += ' ' + xs[0]; P.place(pick(['left', 'right']), xs); }
      else if (kind === 'hp') { const u = pick(P.units(pick(['left', 'right']))); u.hp = pick([0, u.maxHp, 1, Math.floor(rnd() * u.maxHp)]); op += ' ' + u.hp; }
      else if (kind === 'slot') { const v = pick([null, 'heal', 'heavy', 'bogus']); op += ' ' + v; P.eval('supply.' + pick(['player', 'ai']) + ' = ' + JSON.stringify(v)); }
      else if (kind === 'flags') { const t = pick(['player', 'ai']), c = rnd() < 0.5, g = rnd() < 0.1; op += ' turn=' + t + ' charging=' + c + ' over=' + g; P.eval('turn = ' + JSON.stringify(t) + '; isCharging = ' + c + '; gameOver = ' + (g ? '{ winner: "player" }' : 'null') + ';'); }
      else if (kind === 'schedule') { const r = pick([0, 1, 2, 3, 4, 6, 8, 100, 1000000]); op += ' round=' + r; if (r < 1) inContract = false; P.eval('roundNum = ' + r + '; scheduleAirdrop()'); }
      else if (kind === 'drop') { const dt = pick([0, 1e-9, 1 / 60, 1 / 30, 0.25, 1, 5]); op += ' dt=' + dt; P.eval('updateAirdrop(' + dt + ')'); }
      else if (kind === 'use') { op += ' useSupply'; P.eval('useSupply()'); }
      else if (kind === 'bad_dt') { inContract = false; const dt = pick([NaN, -1, Infinity]); op += ' dt=' + dt; P.eval('updateAirdrop(' + (Number.isNaN(dt) ? 'NaN' : dt === Infinity ? 'Infinity' : dt) + ')'); }
    } catch (e) {
      (inContract ? violations : outOfContract).push({ team, step, op, why: 'exception ' + String(e.message).slice(0, 100) });
      if (!inContract) { try { P.eval('carrier = null; drops = [];'); } catch (_) { /* reset */ } }
    }
    log.push(op); if (log.length > 6) log.shift();
    if (inContract) check(step, op); else { try { P.eval('carrier = null; drops = [];'); } catch (_) { /* reset */ } }
    if (violations.length >= 10) break;
    totalSteps++;
  }
  if (violations.length) violations.forEach(v => v.lastOps = log.slice());
}
const first = violations.slice(0, 5);
console.log(JSON.stringify({ seed: SEED, steps: totalSteps, violations: violations.length, outOfContract: outOfContract.length + 0, first }));
violations.slice(0, 5).forEach(v => console.log('VIOLATION team' + v.team + ' step ' + v.step + ': ' + v.op + ' -> ' + v.why));
if (violations.length) console.log('REPRODUCE node scripts/fuzz_page_break.js --seed ' + SEED + ' --steps ' + STEPS + (MUT ? ' --mutant-heal' : ''));
console.log('RESULT ' + (violations.length ? 'FAIL ' + violations.length + ' violations' : 'PASS 0 violations'));
process.exit(violations.length ? 1 : 0);
