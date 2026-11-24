'use strict';
const assert = require('assert');
const TeamBattle = require('../js/team_battle.js');
const Determinism = require('../js/determinism.js');
for (let n = 1; n <= 3; n++) {
  const units = Array.from({ length: n }, (_, i) => ({ id: `left_${i + 1}`, hp: i === 1 ? 0 : 10, alive: i !== 1 }));
  const living = TeamBattle.orderedAlive(units);
  assert.ok(living.every(unit => unit.hp > 0));
  assert.strictEqual(TeamBattle.nextActive(units, living[0].id).id, living[living.length > 1 ? 1 : 0].id);
  const slots = TeamBattle.slots(191 + n, 0, n, Determinism.startX);
  assert.strictEqual(slots.length, n);
  assert.ok(TeamBattle.spacing(slots), `N=${n} seeded slots must be at least 90 px apart`);
}
assert.strictEqual(TeamBattle.winner([{ hp: 1 }], [{ hp: 1 }]), null);
assert.strictEqual(TeamBattle.winner([{ hp: 0 }], [{ hp: 1 }]), 'right');
assert.strictEqual(TeamBattle.winner([{ hp: 0 }], [{ hp: 0 }]), 'draw');
const teams = {
  left: [{ id: 'left_0', hp: 10, angle: 54, item: 'heal', energy: 2, shield: { active: true } }],
  right: [{ id: 'right_0', hp: 10, angle: 60, item: null, energy: 1, shield: { active: false } }]
};
assert.strictEqual(TeamBattle.unitsOf(teams, 'left'), teams.left);
assert.strictEqual(TeamBattle.activeUnit(teams, 'right'), teams.right[0]);
assert.strictEqual(TeamBattle.unitState(teams, 'left', 'angle'), 54);
assert.strictEqual(TeamBattle.unitState(teams, 'left', 'item'), 'heal');
assert.strictEqual(TeamBattle.unitState(teams, 'left', 'energy'), 2);
assert.strictEqual(TeamBattle.unitState(teams, 'right', 'shield').active, false);
assert.throws(() => TeamBattle.slots(195, 0, 4, Determinism.startX), /count must be 1\.\.3/);
console.log('test_team_battle: rotation, alive lists, winners, N=1..3 slots, and N=1 accessors passed');
