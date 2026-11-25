#!/usr/bin/env node
'use strict';
// The real js/relay_client.js against the real scripts/pk_relay.py over real localhost WebSockets (red-team R6A: no test drove the client against a real relay).
// Needs sockets and Node 22+ (global WebSocket): listed with the other socket tests, run it in a normal terminal. Grace period 3 s (the client's first reconnect attempt comes after 1 s) so it takes about 12 s.
const assert = require('assert');
const { spawn } = require('child_process');
const path = require('path');
const net = require('net');
const RelayClient = require('../js/relay_client.js');

const sleep = ms => new Promise(r => setTimeout(r, ms));
async function until(fn, ms, what) { const t0 = Date.now(); while (Date.now() - t0 < ms) { if (fn()) return; await sleep(25); } throw new Error('timeout: ' + what); }
function freePort() { return new Promise(res => { const s = net.createServer(); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => res(p)); }); }); }

async function main() {
  const port = await freePort();
  const relay = spawn('python3', ['-B', path.join(__dirname, 'pk_relay.py')], { env: Object.assign({}, process.env, { PORT: String(port), HOST: '127.0.0.1', PK_RELAY_SEAT_GRACE_SECONDS: '3' }), stdio: ['ignore', 'ignore', 'pipe'] });
  let relayErr = ''; relay.stderr.on('data', d => { relayErr += d; });
  const url = 'ws://127.0.0.1:' + port + '/ws';
  const clients = [];
  function make(name) {
    const socks = [];
    const client = RelayClient.createClient({ socketFactory: () => { const w = new WebSocket(url); socks.push(w); return w; }, now: Date.now, setTimeoutFn: setTimeout });
    const seen = []; client.onMessage(m => seen.push(m));
    clients.push(client);
    return { name, client, socks, seen };
  }
  try {
    for (let i = 0; i < 100; i++) { try { await new Promise((res, rej) => { const c = net.connect(port, '127.0.0.1', res); c.on('error', rej); }); break; } catch (e) { await sleep(50); } }
    const red = make('red'), white = make('white');
    red.client.createRoom({});
    await until(() => red.seen.some(m => m.type === 'room_state' && m.code), 5000, 'red room_state');
    const code = red.seen.find(m => m.code).code;
    white.client.join(code, 'white');
    await until(() => white.seen.some(m => m.type === 'room_state'), 5000, 'white room_state');
    assert.strictEqual(white.client.state().status, 'waiting');

    // 1. the connection of white drops and comes back inside the grace period: it resumes by itself (no room code typed), red is told nothing
    white.socks[0].close();
    await until(() => white.client.state().status === 'reconnecting', 3000, 'white reconnecting');
    await until(() => white.client.state().status === 'waiting' && white.socks.length >= 2, 9000, 'white resumed');
    await sleep(3500);   // longer than the grace period: a resumed seat must not be swept
    assert.ok(!red.seen.some(m => m.type === 'seat_left'), 'no seat_left for a seat that came back');

    // 2. white leaves for good (the page is closed: its socket is gone and it never resumes): after the grace period red is told
    white.client.close();
    await until(() => red.seen.some(m => m.type === 'seat_left' && m.team === 'white'), 9000, 'red gets seat_left');
    assert.strictEqual(red.client.state().status !== 'closed', true);
    // 3. ROOM-FLOW R9: the host's AI filler is marked by the relay; when it is gone for good its units move to the person on its team
    const host = make('host'), mate = make('mate'), filler = make('filler');
    host.client.createRoom({ teamSize: 2, units: ['skeleton', 'bat'] });
    await until(() => host.seen.some(m => m.type === 'room_state' && m.code), 5000, 'host room_state');
    const room = host.seen.find(m => m.code).code;
    mate.client.join(room, 'white', { units: ['knight'] });
    await until(() => mate.seen.some(m => m.type === 'room_state'), 5000, 'mate room_state');
    filler.client.join(room, 'white', { units: ['wizard'], aiHostToken: host.client.seatToken() });
    await until(() => filler.seen.some(m => m.type === 'room_state'), 5000, 'filler room_state');
    assert.strictEqual(filler.seen.find(m => m.type === 'room_state').seats.find(s => s.seat_id === 'white-2').ai, true, 'the relay marks the filler');
    [host, mate, filler].forEach(p => p.client.sendReady({}));
    await until(() => mate.seen.some(m => m.type === 'start'), 5000, 'start');
    assert.strictEqual(mate.client.state().owners.right_1, 'white-2');
    filler.client.close();
    await until(() => mate.seen.some(m => m.type === 'seat_left' && m.ai), 9000, 'mate gets the AI seat_left');
    assert.strictEqual(mate.seen.find(m => m.type === 'seat_left' && m.ai).team_empty, false);
    assert.strictEqual(mate.client.state().owners.right_1, 'white-1');
    // 4. ROOM-FLOW R6b: back to the lobby and a second match with the same clients, and a guest who comes in after the reset
    const h2 = make('h2'), g2 = make('g2');
    h2.client.createRoom({ teamSize: 2, units: ['skeleton', 'bat'] });
    await until(() => h2.seen.some(m => m.type === 'room_state' && m.code), 5000, 'h2 room');
    const room2 = h2.seen.find(m => m.code).code;
    g2.client.join(room2, 'white', { units: ['knight', 'wizard'] });
    await until(() => g2.seen.some(m => m.type === 'room_state'), 5000, 'g2 room_state');
    h2.client.sendReady({}); g2.client.sendReady({});
    await until(() => g2.seen.some(m => m.type === 'start'), 5000, 'first start');
    h2.client.resetLobby();
    await until(() => g2.seen.some(m => m.type === 'lobby_reset') && h2.seen.some(m => m.type === 'lobby_reset'), 5000, 'both clients get lobby_reset');
    assert.strictEqual(g2.client.state().status, 'waiting', 'a reset room is waiting again');
    assert.strictEqual(g2.client.state().owners, null);
    const late = make('late');
    late.client.join(room2, 'spectator');
    await until(() => late.seen.some(m => m.type === 'room_state'), 5000, 'late guest room_state');
    h2.client.sendReady({ units: ['hag', 'bat'] }); g2.client.sendReady({ units: ['knight', 'reaper'] });
    await until(() => g2.seen.filter(m => m.type === 'start').length === 2, 5000, 'second start reaches a client that played the first match');
    await until(() => late.seen.some(m => m.type === 'start'), 5000, 'second start reaches a guest who joined after the reset');
    assert.deepStrictEqual(late.client.state().heroes.left, ['hag', 'bat']);
    // 5. cross-check: a kicked client stops (no resume with its dead seat token, no error after the kick)
    const k1 = make('k1'), k2 = make('k2'), sent = [];
    k1.client.createRoom({ teamSize: 2, lobby: true, claim: 1 });
    await until(() => k1.seen.some(m => m.type === 'room_state' && m.code), 5000, 'k1 room');
    const room3 = k1.seen.find(m => m.code).code;
    const spyFactory = k2.socks;
    k2.client.join(room3, 'white', { claim: 1 });
    await until(() => k2.seen.some(m => m.type === 'room_state' && m.seat_id), 5000, 'k2 seated');
    const origSend = WebSocket.prototype.send;
    k1.client.kick('white-1');
    await until(() => k2.seen.some(m => m.type === 'kicked'), 5000, 'k2 kicked');
    await sleep(2500);
    assert.strictEqual(k2.client.state().status, 'closed', 'a kicked client is closed');
    assert.strictEqual(k2.socks.length, 1, 'no reconnect socket after the kick');
    assert.ok(!k2.seen.some(m => m.type === 'error'), 'no error after the kick: ' + JSON.stringify(k2.seen.filter(m => m.type === 'error')));
    void spyFactory; void origSend; void sent;
    console.log('relay client against the real relay: resume inside the grace period, seat_left after it, AI seat hand-over, back to the lobby, a kicked client stops: ok');
  } finally {
    clients.forEach(c => { try { c.close(); } catch (e) { /* already closed */ } });
    relay.kill('SIGTERM');
    await sleep(200);
    if (relayErr.includes('Traceback')) console.error(relayErr.split('\n').slice(-6).join('\n'));
  }
}
main().then(() => process.exit(0), e => { console.error('FAIL ' + (e && e.stack || e)); process.exit(1); });
