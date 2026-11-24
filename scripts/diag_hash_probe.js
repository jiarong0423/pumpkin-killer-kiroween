'use strict';
// Diagnostics only (gap N10): records every input the page gives to RoundHash.hash (the round hash of a team match) and writes it to
// $PK_DIAG_DIR/<label>.json every 300 ms, so a desync between two page seats can be traced to the unit field that differs.
// It wraps the function in the page's own vm context; it changes no page file and no result of the hash.
const fs = require('fs');
const path = require('path');

function install(P, label) {
  const dir = process.env.PK_DIAG_DIR;
  if (!dir) return;
  fs.mkdirSync(dir, { recursive: true });
  P.eval('(function () { var orig = RoundHash.hash; globalThis.__hashInputs = []; RoundHash.hash = function (state) { var out = orig.apply(this, arguments); try { globalThis.__hashInputs.push({ hash: out, state: JSON.parse(JSON.stringify(state)) }); } catch (e) { globalThis.__hashInputs.push({ hash: out, error: String(e) }); } return out; }; })()');
  const file = path.join(dir, label + '.json');
  const write = () => {
    try {
      const inputs = JSON.parse(JSON.stringify(P.eval('globalThis.__hashInputs')));
      const status = JSON.parse(JSON.stringify(P.eval('__hybridSeat.status()')));
      fs.writeFileSync(file + '.tmp', JSON.stringify({ label, pid: process.pid, inputs, status }));
      fs.renameSync(file + '.tmp', file);
    } catch (e) { /* diagnostics only */ }
  };
  setInterval(write, 300).unref();
  process.on('SIGTERM', () => { write(); process.exit(0); });
}
module.exports = { install };
