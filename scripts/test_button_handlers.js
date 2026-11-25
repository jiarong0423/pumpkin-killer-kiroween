'use strict';
// Code-only button audit (no browser, no screen): every static <button> in index.html must have a handler somewhere in the page code, and a
// panel that is position:fixed inside transformed, overflow-clipped ancestors must not be sized in viewport units (the viewport is larger than the
// visible game area, so the lower part of the panel, and any button there, is clipped and cannot be clicked).
// usage: node scripts/test_button_handlers.js [--json out.json]   exit 1 on any finding
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..');
const html = fs.readFileSync(path.join(ROOT, 'index.html'), 'utf8');
const srcs = [...html.matchAll(/<script src="(js\/[^"]+)"><\/script>/g)].map(m => m[1]);
const inline = [...html.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]).join('\n');
const corpus = inline + '\n' + srcs.map(s => { try { return fs.readFileSync(path.join(ROOT, s), 'utf8'); } catch (_) { return ''; } }).join('\n');
const css = [...html.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)].map(m => m[1]).join('\n');
const markup = html.replace(/<script[\s\S]*?<\/script>/g, '').replace(/<style[\s\S]*?<\/style>/g, '');
const findings = [], rows = [];
const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

const BIND = /onclick|addEventListener|onpointerdown|onpointerup|\.on[a-z]+\s*=|\.click\(|bindButton|wire\(/;
for (const m of markup.matchAll(/<button\b([^>]*)>/g)) {
  const attrs = m[1];
  const id = (attrs.match(/\bid="([^"]+)"/) || [])[1], cls = (attrs.match(/\bclass="([^"]+)"/) || [])[1] || '';
  const dataN = (attrs.match(/\bdata-n="([^"]+)"/) || [])[1];
  let how = null;
  const inl = attrs.match(/\bonclick="([^"]*)"/);
  if (inl) {   // an inline handler: the function it calls must exist in the page code
    const called = [...inl[1].matchAll(/([A-Za-z_$][\w$]*)\s*\(/g)].map(x => x[1]).filter(n => !/^(if|return|event|function)$/.test(n));
    const missing = called.filter(n => !new RegExp('function\\s+' + esc(n) + '\\b|\\b(const|let|var)\\s+' + esc(n) + '\\b|\\b' + esc(n) + '\\s*[:=]\\s*(async\\s*)?(function|\\()').test(corpus) && !/^(document|window|navigator|\w+\.\w+)$/.test(n));
    how = missing.length ? null : 'inline onclick -> ' + called.join(', ');
    if (missing.length) findings.push('button ' + (id || attrs.slice(0, 40)) + ' calls ' + missing.join(', ') + ' which is not defined anywhere');
  }
  if (!how && id) {
    const ref = new RegExp('(getElementById|\\$|byId|qs|querySelector)\\(\\s*["\'`]#?' + esc(id) + '["\'`]');
    const lines = corpus.split('\n').filter(l => l.includes('"' + id + '"') || l.includes("'" + id + "'") || l.includes('#' + id));
    if (lines.some(l => ref.test(l) && BIND.test(l))) how = 'bound on its own line';
    else if (lines.length) how = 'referenced (' + lines.length + ' line(s), binding on another line or delegated)';
    else if (new RegExp('#' + esc(id) + '\\b').test(css) && !lines.length) how = null;
  }
  if (!how && cls) {
    for (const c of cls.split(/\s+/).filter(Boolean)) if (new RegExp('[.\'"` ]' + esc(c) + '\\b').test(corpus.replace(/\bclassName\b/g, ''))) { how = 'class .' + c + ' used in code'; break; }
  }
  if (!how) for (const dm of attrs.matchAll(/\bdata-([a-z-]+)=/g)) { if (!/^(i18n|i18n-attr)$/.test(dm[1]) && new RegExp('\\[data-' + esc(dm[1]) + '[\\]=]').test(corpus)) { how = 'data-' + dm[1] + ' selector used in code'; break; } }
  if (!how && dataN !== undefined && /team-size/.test(corpus)) how = 'data-n inside #team-size (delegated)';
  const key = id || ('.' + (cls || '(no id, no class)') + (dataN ? '[data-n=' + dataN + ']' : ''));
  rows.push({ button: key, binding: how || 'NONE FOUND' });
  if (!how) findings.push('button ' + key + ' has no handler reference in index.html or js/*.js');
}

// panel clip check: friends panel sized in viewport units inside transformed + overflow:hidden ancestors
const rule = css.match(/#start-screen\.seats-open #friends-panel\s*\{[^}]*\}/);
const startRule = (css.match(/#start-screen\s*\{[^}]*\}/g) || []).join(' ');
const clipped = /overflow\s*:\s*hidden/.test(startRule) || /overflow\s*:\s*hidden/.test(css.match(/#game-container\s*\{[^}]*\}/g) ? css.match(/#game-container\s*\{[^}]*\}/g).join(' ') : '');
const vh = rule && /max-height\s*:[^;]*\d+d?vh/.test(rule[0]);
const vhMedia = /#start-screen\.seats-open #friends-panel\s*\{[^}]*max-height\s*:[^;]*d?vh[^}]*\}/.test(css);
const sizedByViewport = !!(rule && (vh || vhMedia));
rows.push({ check: 'friends panel max-height in viewport units while ancestors clip', sizedByViewport, ancestorsClip: clipped });
if (sizedByViewport && clipped) findings.push('#friends-panel max-height uses vh/dvh but #start-screen/#game-container clip with overflow:hidden: the panel can be taller than the visible area, so its lower buttons (Copy link) are clipped and unclickable');

const out = { buttons: rows.filter(r => r.button).length, findings };
const j = process.argv.indexOf('--json'); if (j > 0) fs.writeFileSync(process.argv[j + 1], JSON.stringify({ out, rows }, null, 1));
console.log('static buttons audited: ' + out.buttons);
findings.forEach(f => console.log('FINDING ' + f));
console.log('RESULT ' + (findings.length ? 'FAIL ' + findings.length + ' finding(s)' : 'PASS 0 findings'));
process.exit(findings.length ? 1 : 0);
