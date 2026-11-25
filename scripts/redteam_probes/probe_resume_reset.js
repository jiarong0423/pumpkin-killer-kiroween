// F9: the real js/relay_client.js against the real relay. A seat that drops during a match and resumes after the host's reset_lobby
// never applies another sequenced message: the relay's log restarts after a gap the client cannot cross (expectedSeq stays below first_seq).
// Run: node scripts/redteam_probes/probe_resume_reset.js
const { spawn } = require('child_process');
const net = require('net');
const RelayClient = require(require('path').join(__dirname, '..', '..', 'js', 'relay_client.js'));
const sleep = ms => new Promise(r => setTimeout(r, ms));
function freePort() { return new Promise(res => { const s = net.createServer(); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => res(p)); }); }); }
(async () => {
  const port = await freePort();
  const relay = spawn('python3', ['-B', require('path').join(__dirname, '..', 'pk_relay.py')], { env: Object.assign({}, process.env, { HOST: '127.0.0.1', PORT: String(port) }), stdio: 'ignore' });
  try {
    await sleep(800);
    const url = `ws://127.0.0.1:${port}/ws`;
    const host = new WebSocket(url); const hostIn = [];
    host.onmessage = e => hostIn.push(JSON.parse(e.data));
    await new Promise(r => { host.onopen = r; });
    host.send(JSON.stringify({ type: 'create_room', seat: 'red' })); await sleep(200);
    const code = hostIn.find(m => m.code).code;
    let guestSock = null;
    const seen = [];
    const guest = RelayClient.createClient({ socketFactory: () => { guestSock = new WebSocket(url); return guestSock; }, now: Date.now, setTimeoutFn: setTimeout });
    guest.onMessage(m => seen.push(m.type + (typeof m.seq === 'number' ? '#' + m.seq : '')));
    await sleep(200);
    guest.join(code, 'white'); await sleep(200);
    host.send(JSON.stringify({ type: 'ready' })); guest.sendReady(); await sleep(300);
    const startedBefore = seen.some(t => t.startsWith('start'));
    guestSock.close();            // transient drop; the client reconnects after 1 s and resumes
    await sleep(250);
    host.send(JSON.stringify({ type: 'reset_lobby' })); await sleep(150);
    host.send(JSON.stringify({ type: 'set_name', name: 'after' })); await sleep(1800);
    const resetSeq = (hostIn.find(m => m.type === 'lobby_reset') || {}).seq;
    const afterResume = seen.slice(seen.lastIndexOf('room_state') + 0);
    const gotReset = seen.some(t => t.startsWith('lobby_reset'));
    console.log(JSON.stringify({ startedBefore, relayLobbyResetSeq: resetSeq, guestStatus: guest.state().status, guestSeen: seen }));
    console.log((startedBefore && !gotReset ? '[BREAK]' : '[HELD]') + ' F9 resumed client applies lobby_reset and later messages');
    console.log('    observed: guest saw lobby_reset=' + gotReset + ', status=' + guest.state().status + ' (still the old match)');
    console.log('    expected: lobby_reset#' + resetSeq + ' and the following room_state are applied after the resume');
    guest.close(); host.close();
  } finally { relay.kill('SIGTERM'); }
})();
