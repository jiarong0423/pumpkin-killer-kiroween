'use strict';
/* Page-source parity coverage for the owner-fixed Shield Wall rule. */
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const constants = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'shared', 'constants.json'), 'utf8'));
const zone = constants.KNIGHT_ZONE;
const height = constants.SHIELD_WALL_COFFIN_HEIGHT;
const expiry = constants.SHIELD_WALL_EXPIRES_AFTER_ATTACKS;

function crossesCoffin(point, shot) {
  return Math.abs(shot.x - point.x) <= zone && Math.abs(shot.y - point.y) <= height / 2;
}
function answerWall(state, shot) {
  if (!state.points.length) return { blocked: false, state };
  const pointIndex = shot.hunchback ? -1 : state.points.findIndex(point => crossesCoffin(point, shot));
  if (pointIndex >= 0) state.points.splice(pointIndex, 1);
  state.attacks++;
  if (state.attacks >= expiry || !state.points.length) state.points = [];
  return { blocked: pointIndex >= 0, state };
}

assert.strictEqual(zone, 70);
assert.strictEqual(height, 18);
assert.strictEqual(expiry, 3);
assert.match(html, /Math\.abs\(q\.x - g\.x\) <= KNIGHT_ZONE && Math\.abs\(q\.y - g\.y\) <= SHIELD_WALL_COFFIN_HEIGHT \/ 2/);
assert.match(html, /!p\.ultBoom && p\.ultBlock/);
assert.match(html, /knightRoundsLeft = SHIELD_WALL_EXPIRES_AFTER_ATTACKS/);

let state = { points: [{ x: 500, y: 500 }, { x: 600, y: 500 }, { x: 700, y: 500 }], attacks: 0 };
answerWall(state, { x: 400, y: 500 });
answerWall(state, { x: 400, y: 500 });
answerWall(state, { x: 400, y: 500 });
assert.deepStrictEqual(state.points, [], 'expires after three enemy throws');

state = { points: [{ x: 500, y: 500 }], attacks: 0 };
assert.strictEqual(answerWall(state, { x: 500, y: 470 }).blocked, false, 'high shot passes above 18 px coffin');
state = { points: [{ x: 500, y: 500 }], attacks: 0 };
assert.strictEqual(answerWall(state, { x: 500, y: 500, hunchback: true }).blocked, false, 'hunchback bypasses the wall');
state = { points: [{ x: 700, y: 500 }, { x: 800, y: 500 }, { x: 900, y: 500 }], attacks: 0 };
answerWall(state, { x: 400, y: 500 });
answerWall(state, { x: 400, y: 500 });
assert.strictEqual(state.attacks, 2, 'two enemy throws in one round count separately');
console.log('test_shield_wall: all page and rule parity cases passed');
