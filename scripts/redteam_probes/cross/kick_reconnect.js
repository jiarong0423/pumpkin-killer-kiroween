// After a kick the relay closes the socket; does RelayClient reconnect and send a resume with the dead token (counted as a bad resume per address)?
const { spawn } = require('child_process'), net = require('net');
const RelayClient = require('../../../js/relay_client.js');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const freePort = () => new Promise(r => { const s = net.createServer(); s.listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => r(p)); }); });
(async () => {
  const port = await freePort();
  const relay = spawn('python3', ['-B', require('path').join(__dirname, '..', '..', 'pk_relay.py')], { env: Object.assign({}, process.env, { HOST: '127.0.0.1', PORT: String(port) }), stdio: 'ignore' });
  await sleep(2500);
  const url = 'ws://127.0.0.1:' + port + '/ws'; const sent = [];
  const mk = (log) => RelayClient.createClient({ socketFactory: () => { const ws = new WebSocket(url); const s = ws.send.bind(ws); ws.send = d => { if (log) sent.push(JSON.parse(d).type); return s(d); }; return ws; }, now: () => Date.now(), setTimeoutFn: (f, ms) => setTimeout(f, ms) });
  const host = mk(false), guest = mk(true); const got = [], statuses = [];
  let code = null, gseat = null;
  host.onMessage(m => { console.log('host got', m.type, m.code||'', m.message||''); if (m.type === 'room_state' && m.code) code = m.code; });
  guest.onMessage(m => { got.push(m.type + (m.code ? ':' + m.code : '') + (m.reason ? ':' + m.reason : '')); if (m.type === 'room_state' && m.seat_id) gseat = m.seat_id; });
  guest.onStatus && guest.onStatus(s => statuses.push(s));
  host.createRoom({ lobby: true, teamSize: 2, claim: 1, name: 'H' });
  await sleep(500);
  guest.join(code, 'auto', { name: 'G', claim: 1 });
  await sleep(500);
  host.kick(gseat);
  await sleep(3500);
  console.log('guest messages', JSON.stringify(got));
  console.log('guest sent', JSON.stringify(sent), 'statuses', JSON.stringify(statuses));
  console.log(sent.filter(t => t === 'resume').length ? 'BROKEN-ish: kicked client reconnects and sends resume with its dead token (one bad resume per kick)' : 'HELD: no resume after kick');
  host.close(); guest.close(); relay.kill(); process.exit(0);
})();
