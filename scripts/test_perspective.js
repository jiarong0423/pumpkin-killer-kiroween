'use strict';
const assert = require('assert');
const Perspective = require('../js/perspective.js');
const RelayClient = require('../js/relay_client.js');

const left = Perspective.create('left');
const right = Perspective.create('right');
assert.strictEqual(left.mirrored, false);
assert.strictEqual(right.mirrored, true);

let state = 0x223c0de;
function random() {
  state = (state * 1664525 + 1013904223) >>> 0;
  return state / 0x100000000;
}
for (let i = 0; i < 1000; i++) {
  const x = random() * Perspective.CANVAS_WIDTH;
  assert.strictEqual(left.x(left.x(x)), x, 'left x inverse at ' + i);
  assert.strictEqual(right.x(right.x(x)), x, 'right x inverse at ' + i);
}

for (const wind of [-4, -1.3, 0, 2.7, 4]) {
  assert.strictEqual(left.wind(wind), wind, 'left wind identity');
  assert.strictEqual(right.wind(wind), -wind, 'right wind sign');
  assert.strictEqual(right.wind(right.wind(wind)), wind, 'right wind inverse');
}
assert.strictEqual(left.side('left'), 'left');
assert.strictEqual(left.side('right'), 'right');
assert.strictEqual(right.side('left'), 'right');
assert.strictEqual(right.side('right'), 'left');
assert.strictEqual(right.unitId('left_0'), 'right_0');
assert.strictEqual(right.unitId('right'), 'left');
assert.strictEqual(right.worldUnitId('left_3'), 'right_3');
assert.strictEqual(right.dirX(1), -1);
assert.strictEqual(right.worldDirX(1), -1);
assert.strictEqual(right.angle(54), 54);
assert.strictEqual(right.diceDirection(-1), 1, 'world backward is local forward on the right');
assert.strictEqual(right.worldDiceDirection(1), -1, 'local forward becomes world left on the right');

const socket = { sent: [], send(text) { this.sent.push(JSON.parse(text)); }, close() {} };
const relay = RelayClient.createClient({
  perspective: right,
  socketFactory: () => socket,
  now: () => 0,
  setTimeoutFn: () => {}
});
relay.sendAction({ unit: 'left_0', kind: 'throw', start: { x: 320, y: 750 }, claimed_landing: { x: 610, y: 860 }, dirX: 1 });
assert.deepStrictEqual(socket.sent[0], {
  type: 'action', unit: 'right_0', kind: 'throw', start: { x: 1600, y: 750 }, claimed_landing: { x: 1310, y: 860 }, dirX: -1
}, 'right local action becomes its unchanged world-frame wire action');
let incoming;
relay.onMessage(message => { incoming = message; });
socket.onmessage({ data: JSON.stringify({ type: 'action', seq: 1, unit: 'right_0', start: { x: 1600, y: 750 }, claimed_landing: { x: 1310, y: 860 }, dirX: -1 }) });
assert.deepStrictEqual(incoming, { type: 'action', seq: 1, unit: 'left_0', start: { x: 320, y: 750 }, claimed_landing: { x: 610, y: 860 }, dirX: 1 }, 'world relay action becomes local before listeners use it');

const leftZone = [240, 680], rightZone = [1240, 1680];
assert.deepStrictEqual(rightZone.map(right.x).reverse(), leftZone, 'right zone maps onto left zone');
assert.deepStrictEqual(leftZone.map(right.x).reverse(), rightZone, 'left zone maps onto right zone');
for (const x of [252, 288, 360, 432, 540, 612]) {
  const local = right.x(x);
  assert.ok(local >= rightZone[0] && local <= rightZone[1], 'world left start maps inside local opponent zone');
}
for (const x of [1296, 1332, 1404, 1476, 1584, 1656]) {
  const local = right.x(x);
  assert.ok(local >= leftZone[0] && local <= leftZone[1], 'world right start maps inside local me zone');
}

console.log('test_perspective: 1000 inverse coordinate vectors passed');
console.log('test_perspective: wind, side, unit, direction, and angle mappings passed');
console.log('test_perspective: mirrored start ranges remain inside legal local zones');

const RoundHash = require('../js/round_hash.js');
const Determinism = require('../js/determinism.js');
const page = require('fs').readFileSync(require('path').join(__dirname, '..', 'index.html'), 'utf8');

function worldHash(world) {
  return RoundHash.hash({ units: world.units, wallHp: world.wallHp, round: world.round, phase: world.phase, seed: world.seed });
}
function localState(world, perspective) {
  function unit(localSide) {
    const worldSide = perspective.worldSide(localSide);
    const source = world.units.find(item => item.id === worldSide + '_0');
    return { id: localSide + '_0', x: perspective.x(source.x), y: source.y, hp: source.hp, alive: source.alive, statuses: source.statuses.slice() };
  }
  return { units: [unit('left'), unit('right')], wind: perspective.wind(world.wind), weather: world.weather, round: world.round, phase: world.phase, seed: world.seed, wallHp: world.wallHp };
}
function localHash(local, perspective) {
  return RoundHash.hash({
    units: local.units.map(unit => ({ id: perspective.worldUnitId(unit.id), x: perspective.x(unit.x), y: unit.y, hp: unit.hp, alive: unit.alive, statuses: unit.statuses })),
    wind: perspective.wind(local.wind), wallHp: local.wallHp, round: local.round, phase: local.phase, seed: local.seed
  });
}
const mirroredWorld = {
  seed: 2230001, round: 1, phase: 'throws:left:54:48', wallHp: 100,
  wind: Determinism.wind(2230001, 1), weather: 'clear',
  units: [
    { id: 'left_0', x: Determinism.startX(2230001, 0, 0), y: 860, hp: 100, alive: true, statuses: [] },
    { id: 'right_0', x: Determinism.startX(2230001, 1, 0), y: 860, hp: 85, alive: true, statuses: [] }
  ]
};
const mirroredRecords = [];
const scriptedRounds = [
  { side: 'left', delta: 72, damage: 13, status: 'burn:2' },
  { side: 'right', delta: -108, damage: 9, status: 'slow:1' },
  { side: 'left', delta: 36, damage: 17, status: 'poison:2' }
];
for (const action of scriptedRounds) {
  const actor = mirroredWorld.units.find(unit => unit.id === action.side + '_0');
  const target = mirroredWorld.units.find(unit => unit !== actor);
  actor.x += action.delta;
  target.hp -= action.damage;
  target.statuses = [action.status];
  mirroredWorld.phase = 'throws:' + action.side + ':54:48';
  mirroredWorld.wind = Determinism.wind(mirroredWorld.seed, mirroredWorld.round);
  const leftDevice = localState(mirroredWorld, left);
  const rightDevice = localState(mirroredWorld, right);
  const expectedWorldHash = worldHash(mirroredWorld);
  assert.strictEqual(localHash(leftDevice, left), expectedWorldHash, 'left device world hash round ' + mirroredWorld.round);
  assert.strictEqual(localHash(rightDevice, right), expectedWorldHash, 'right device world hash round ' + mirroredWorld.round);
  assert.strictEqual(rightDevice.units[0].x, 1920 - mirroredWorld.units[1].x, 'right device me is the mirrored world-right unit');
  assert.strictEqual(rightDevice.units[1].x, 1920 - mirroredWorld.units[0].x, 'right device opponent is the mirrored world-left unit');
  mirroredRecords.push({ round: mirroredWorld.round, world: JSON.parse(JSON.stringify(mirroredWorld)), left: leftDevice, right: rightDevice, roundHash: expectedWorldHash });
  mirroredWorld.round++;
}
const twoSeatsTranscript = { version: 1, mode: 'two_seats_mirror', records: mirroredRecords };
const transcriptPath = require('path').join(__dirname, '..', 'docs', 'transcripts', 'two_seats_mirror.json');
const transcriptText = require('fs').readFileSync(transcriptPath, 'utf8');
assert.deepStrictEqual(JSON.parse(transcriptText), twoSeatsTranscript, 'two-seat recording must match the simulated devices');
assert.strictEqual(require('crypto').createHash('sha256').update(transcriptText).digest('hex'), 'df2bfc3c4db1eb950d1583794c044d76cd1a01fc6837e1e09a827289350f6eb4', 'two-seat transcript sha256');
console.log('test_perspective: two-seat simulated rounds agree in world state and round hash');
console.log('test_perspective transcript sha256: df2bfc3c4db1eb950d1583794c044d76cd1a01fc6837e1e09a827289350f6eb4');

const renderStart = page.indexOf('function drawFullArtCharacter');
assert.ok(renderStart >= 0, 'drawFullArtCharacter is present');
assert.ok(!page.slice(renderStart).includes('Perspective'), 'rendering functions must not depend on Perspective');
const orientationTable = page.match(/const ART_FACES_RIGHT = \{[^}]*\};/);
assert.ok(orientationTable && !orientationTable[0].includes('Perspective'), 'orientation table must not depend on Perspective');
assert.match(page, /localPerspective\.worldUnitId\("left"\).*localPerspective\.x\(player\.x\)/s, 'round hash maps the local player back to world values');
assert.match(page, /wind: localPerspective\.wind\(wind\)/, 'round hash receives world-frame wind');
console.log('test_perspective: rendering and orientation tables remain perspective-free');
