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
    console.log('relay client against the real relay: resume inside the grace period, seat_left after it: ok');
  } finally {
    clients.forEach(c => { try { c.close(); } catch (e) { /* already closed */ } });
    relay.kill('SIGTERM');
    await sleep(200);
    if (relayErr.includes('Traceback')) console.error(relayErr.split('\n').slice(-6).join('\n'));
  }
}
main().then(() => process.exit(0), e => { console.error('FAIL ' + (e && e.stack || e)); process.exit(1); });
