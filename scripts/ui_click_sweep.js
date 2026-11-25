/* UI click sweep: evaluated INSIDE the real page (dev server, browser pane):
 *   const r = await eval(await (await fetch('/scripts/ui_click_sweep.js')).text());   // returns a JSON-able report
 * Clicks every visible, enabled <button> of the start screen (except a few that leave the page or start the match), then starts one match
 * and clicks the in-match buttons (supply slot, ultimate, skills, menu, mute, panels). Records: thrown errors, unhandled rejections,
 * console.error lines, and whether the click changed anything (DOM size, hidden panels, class or aria changes). Reads the page only:
 * nothing is stored, no network call is made by the sweep itself (a button's own handler may fetch the page's own relay).
 */
(async () => {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const errors = [], consoleErrors = [];
  const onErr = (e) => errors.push(String((e && (e.message || e.reason)) || e).slice(0, 160));
  window.addEventListener('error', onErr); window.addEventListener('unhandledrejection', onErr);
  const origErr = console.error; console.error = function () { consoleErrors.push(Array.from(arguments).join(' ').slice(0, 160)); return origErr.apply(console, arguments); };
  const SKIP = /(^|-)(start|daily|fullscreen|download|share|reload|install)(-|$)|start-?match|go-?fullscreen/i;
  const visible = (el) => { const r = el.getBoundingClientRect(), cs = getComputedStyle(el); return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && !el.closest('[hidden]'); };
  const label = (el) => (el.id || el.getAttribute('data-i18n') || el.className || el.tagName).toString().slice(0, 40) + ' | ' + (el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 24);
  const snap = () => Array.from(document.querySelectorAll('button')).map((b) => b.className + (b.getAttribute('aria-pressed') || '') + (b.disabled ? 'd' : '')).join('|') + '#' + document.body.getElementsByTagName('*').length + ':' + document.querySelectorAll('[hidden]').length + ':' + document.querySelectorAll('.hidden,.open,.active,.on,[aria-pressed="true"],[aria-expanded="true"]').length + ':' + document.body.innerText.length;
  const report = { phases: {}, errors: null };
  async function sweep(name) {
    const rows = [];
    const buttons = Array.from(document.querySelectorAll('button')).filter((b) => !b.closest('#bug-report'));
    for (const b of buttons) {
      const row = { button: label(b), visible: visible(b), disabled: !!b.disabled };
      if (!row.visible || row.disabled) { row.action = 'not clickable'; rows.push(row); continue; }
      if (b.closest('#team-size')) { row.action = 'skipped (leaves the page or starts the match)'; row.note = 'reloads the page with ?team=N by design'; rows.push(row); continue; }
      if (SKIP.test(b.id || '') || SKIP.test(b.getAttribute('data-i18n') || '')) { row.action = 'skipped (leaves the page or starts the match)'; rows.push(row); continue; }
      { const r = b.getBoundingClientRect(), top = document.elementFromPoint(Math.min(innerWidth - 1, Math.max(0, r.left + r.width / 2)), Math.min(innerHeight - 1, Math.max(0, r.top + r.height / 2)));   // what a real finger would hit
        if (!top || !(top === b || b.contains(top))) { row.action = 'covered'; row.coveredBy = top ? ((top.id || top.className || top.tagName) + '').toString().slice(0, 40) : 'nothing'; rows.push(row); continue; } }
      const e0 = errors.length, c0 = consoleErrors.length, s0 = snap();
      try { b.click(); } catch (e) { errors.push('click threw: ' + e.message); }
      await sleep(120);
      row.changed = snap() !== s0; row.newErrors = errors.slice(e0).concat(consoleErrors.slice(c0));
      row.action = 'clicked';
      rows.push(row);
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })); await sleep(40);   // close any panel the click opened
    }
    report.phases[name] = { total: rows.length, clicked: rows.filter((r) => r.action === 'clicked').length, notClickable: rows.filter((r) => r.action === 'not clickable').length, covered: rows.filter((r) => r.action === 'covered').map((r) => r.button + ' <- ' + r.coveredBy), skipped: rows.filter((r) => r.action === 'skipped (leaves the page or starts the match)').length, noEffect: rows.filter((r) => r.action === 'clicked' && !r.changed).map((r) => r.button), withErrors: rows.filter((r) => r.newErrors && r.newErrors.length).map((r) => ({ button: r.button, errors: r.newErrors })), rows };
  }
  await sweep('start_screen');
  try { pickedHero = 'skeleton'; pickedScene = 'graveyard'; startMatch(); for (let i = 0; i < 80 && !(turn === 'player' && !isCharging && !document.querySelector('#coin-overlay:not([hidden]), .coin-overlay:not([hidden])')); i++) await sleep(100); report.turnWhenSwept = typeof turn !== 'undefined' ? turn : null; await sweep('in_match'); } catch (e) { report.startMatchError = String(e.message || e); }
  report.errors = { uncaught: errors.length, consoleErrors: consoleErrors.length, first: errors.concat(consoleErrors).slice(0, 8) };
  window.removeEventListener('error', onErr); window.removeEventListener('unhandledrejection', onErr); console.error = origErr;
  for (const k of Object.keys(report.phases)) report.phases[k].rows = report.phases[k].rows.map((r) => r.button + ' -> ' + r.action + (r.action === 'covered' ? ' (covered by ' + r.coveredBy + ')' : '') + (r.action === 'clicked' ? (r.changed ? ' (changed)' : ' (no visible change)') + (r.newErrors.length ? ' ERR ' + r.newErrors.join('; ') : '') : ''));
  return report;
})()
