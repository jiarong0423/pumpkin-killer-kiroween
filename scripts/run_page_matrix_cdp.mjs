#!/usr/bin/env node
/*
 * Front-end matrix in a REAL Chrome over the DevTools protocol (docs/MATRIX_SPEC_20261117.md): 8 heroes x 3 sizes x 10 seeds = 240 matches
 * of the page's own code, driven by scripts/page_match_driver.js (fake clock, no real waiting inside a match).
 *
 *   node scripts/run_page_matrix_cdp.mjs --desktop                  launch headless Chrome + the local dev server, write logs_local/matrix_page_desktop.json
 *   node scripts/run_page_matrix_cdp.mjs --phone                    use a phone Chrome forwarded to 127.0.0.1:9333, write logs_local/matrix_page_phone.json
 *   node scripts/run_page_matrix_cdp.mjs --print-snippet --size N   print JavaScript to paste into a browser pane / console tool (no connection, no file)
 *
 * Options: --per-cell N (default 10)   --hero NAME   --size N   --out FILE   --resume (skip seeds already in the output file)
 *          --url URL (phone page, default http://localhost:8080/index.html)   --port N (phone DevTools port on the Mac, default 9333; --cdp-port is the same)   --timeout-s N (one match, default 300)
 *          --rich: the page full AI (ultimates, skills, shield, items) instead of plain throws only (default plainOnly)
 *          --print-snippet: --size N (required) [--hero NAME] [--seeds K per hero, default 2]
 *
 * Phone setup (owner's terminal, phone on wifi adb):
 *   adb reverse tcp:8080 tcp:8080                                    (the phone reaches the dev server at http://localhost:8080)
 *   python3 -B scripts/dev_server.py 8080 &                          (serve the repository on the laptop)
 *   adb -s <phone-ip>:5555 forward tcp:9333 localabstract:chrome_devtools_remote   (the laptop reaches the phone Chrome DevTools socket; 9222 is taken on the Mac)
 *   keep Chrome on the phone open and the screen on while it runs. The script reuses the open tab whose url starts with http://localhost:8080/
 *   (else opens a new one with /json/new), navigates it to index.html?team=N&seed=S for every match, and leaves that tab open at the end (a tab it opened itself is closed).
 * A phone is slower than a laptop: the whole matrix can take well over an hour; --resume continues after a dropped connection.
 * Each match loads index.html?team=N&seed=S fresh (no state is carried over), injects the driver and calls runPageMatch(config).
 * Exit code 1 when any match recorded an error or the run could not finish. No data leaves the machine except the local dev server and the DevTools socket.
 */
import { spawn } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import http from "node:http";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const require = createRequire(import.meta.url);
const driver = require("./page_match_driver.js");

const argv = process.argv.slice(2);
const flag = name => argv.includes("--" + name);
const opt = (name, def) => { const i = argv.indexOf("--" + name); return i >= 0 && argv[i + 1] !== undefined ? argv[i + 1] : def; };
const mode = flag("phone") ? "phone" : flag("desktop") ? "desktop" : flag("print-snippet") ? "snippet" : null;
if (!mode) { console.error("usage: node scripts/run_page_matrix_cdp.mjs --desktop | --phone | --print-snippet --size N [--per-cell N] [--hero NAME] [--size N] [--out FILE] [--resume]"); process.exit(2); }
const perCell = Number(opt("per-cell", 10));
const plainOnly = !flag("rich");   // default: plain throws only on both seats (like the engine bot); --rich = the page's full AI
const onlyHero = opt("hero", null), onlySize = opt("size", null);
const outFile = path.resolve(opt("out", path.join(root, "logs_local", mode === "phone" ? "matrix_page_phone.json" : "matrix_page_desktop.json")));
const matchTimeoutMs = Number(opt("timeout-s", 300)) * 1000;
const cdpPort = Number(opt("port", opt("cdp-port", 9333)));
const phoneUrl = opt("url", "http://localhost:8080/index.html");

if (mode === "snippet") {   // text for a pane without a socket: open http://localhost:8080/index.html?team=N once, paste this into its javascript tool; it returns the records as an array
  const size = Number(opt("size", 0));
  if (![1, 2, 3].includes(size)) { console.error("--print-snippet needs --size 1|2|3"); process.exit(2); }
  const seeds = Number(opt("seeds", 2));
  const list = driver.cells(seeds).filter(c => c.size === size && (!onlyHero || c.hero === onlyHero)).map(c => (plainOnly ? c : Object.assign({}, c, { plainOnly: false })));
  const body = driver.source.split("\n").filter(line => !/^\s*\/\/ /.test(line)).join("\n");
  console.log("// Pumpkin Killer matrix snippet: page must be loaded as " + phoneUrl + "?team=" + size + " (the driver refuses another size). " + list.length + " matches, synchronous (about " + Math.ceil(list.length * (size === 1 ? 0.3 : size === 2 ? 0.5 : 1)) + " s on a laptop; split with --hero / --seeds if the tool times out).");
  console.log(body);
  console.log("JSON.stringify(" + JSON.stringify(list) + ".map(function (c) { return runPageMatch(c); }))");
  process.exit(0);
}

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
function request(url, method = "GET") {
  return new Promise((resolve, reject) => {
    const req = http.request(url, { method }, response => {
      let data = "";
      response.on("data", chunk => { data += chunk; });
      response.on("end", () => resolve({ status: response.statusCode, body: data }));
    });
    req.on("error", reject);
    req.setTimeout(10000, () => req.destroy(new Error("timeout " + url)));
    req.end();
  });
}
async function json(url, method = "GET") {
  const r = await request(url, method);
  if (r.status < 200 || r.status >= 300) throw new Error("HTTP " + r.status + " for " + url);
  return JSON.parse(r.body);
}
async function waitFor(fn, what, attempts = 100, ms = 100) {
  let last;
  for (let i = 0; i < attempts; i++) { try { const v = await fn(); if (v) return v; } catch (e) { last = e; } await delay(ms); }
  throw last || new Error("timed out waiting for " + what);
}
async function stop(child) {
  if (!child || child.exitCode !== null) return;
  const exited = new Promise(resolve => child.once("exit", resolve));
  child.kill();
  await Promise.race([exited, delay(3000)]);
}

class Cdp {
  constructor(url) { this.url = url; this.id = 0; this.pending = new Map(); this.closed = false; }
  async open() {
    this.socket = new WebSocket(this.url);
    await new Promise((resolve, reject) => {
      this.socket.addEventListener("open", resolve, { once: true });
      this.socket.addEventListener("error", () => reject(new Error("DevTools socket error")), { once: true });
    });
    this.socket.addEventListener("message", event => {
      const message = JSON.parse(event.data), pending = this.pending.get(message.id);
      if (!pending) return;
      this.pending.delete(message.id);
      if (message.error) pending.reject(new Error(message.error.message)); else pending.resolve(message.result);
    });
    this.socket.addEventListener("close", () => { this.closed = true; for (const p of this.pending.values()) p.reject(new Error("DevTools socket closed")); this.pending.clear(); });
  }
  call(method, params = {}, timeoutMs = 30000) {
    const id = ++this.id;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => { this.pending.delete(id); reject(new Error("CDP timeout: " + method)); }, timeoutMs);
      this.pending.set(id, { resolve: v => { clearTimeout(timer); resolve(v); }, reject: e => { clearTimeout(timer); reject(e); } });
      try { this.socket.send(JSON.stringify({ id, method, params })); } catch (e) { clearTimeout(timer); this.pending.delete(id); reject(e); }
    });
  }
  close() { try { this.socket.close(); } catch (_) { /* already closed */ } }
}
async function evaluate(cdp, expression, timeoutMs) {
  const result = await cdp.call("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true }, timeoutMs || 30000);
  if (result.exceptionDetails) throw new Error((result.exceptionDetails.exception && result.exceptionDetails.exception.description) || result.exceptionDetails.text || "page evaluation failed");
  return result.result.value;
}

// The page must not run its own animation loop while a match is being played synchronously; the driver fakes time itself.
const prePageScript = "window.requestAnimationFrame = function () { return 0; };";

function errorRecord(cell, message) {
  return { options: { plainOnly }, end: "page", hero: cell.hero, hero_right: null, size: cell.size, seed: cell.seed, tier_left: null, tier_right: null, winner: "none", rounds: 0, hp_share_left: null, hp_share_right: null, units_left_alive: null, units_right_alive: null, throws: 0, direct_hits: 0, near_misses: null, pity_triggers: null, comeback_hits: null, ultimates_left: null, ultimates_right: null, errors: [message] };
}

let server, chrome, tempDir, cdp, tabId = null, baseUrl, browserBase;
async function openTarget() {
  if (mode === "desktop") {
    const targets = await waitFor(async () => { const t = await json(`${browserBase}/json/list`); return t.find(x => x.type === "page") ? t : null; }, "Chrome page target");
    return targets.find(x => x.type === "page");
  }
  // Phone: reuse the open tab on the page's origin, else open a new one (Chrome wants PUT for /json/new; older builds accept GET).
  const list = await json(`${browserBase}/json/list`);
  const origin = new URL(phoneUrl).origin + "/";
  const existing = list.find(t => t.type === "page" && typeof t.url === "string" && t.url.startsWith(origin));
  if (existing) return existing;
  let tab;
  try { tab = await json(`${browserBase}/json/new?${encodeURIComponent(phoneUrl)}`, "PUT"); }
  catch (_) { tab = await json(`${browserBase}/json/new?${encodeURIComponent(phoneUrl)}`); }
  tabId = tab.id;   // only a tab this script opened is closed at the end
  return tab;
}
async function connect() {
  const target = await openTarget();
  cdp = new Cdp(target.webSocketDebuggerUrl);
  await cdp.open();
  await cdp.call("Page.enable"); await cdp.call("Runtime.enable");
  await cdp.call("Page.addScriptToEvaluateOnNewDocument", { source: prePageScript });
}
async function loadPage(size, seed) {
  await cdp.call("Page.navigate", { url: `${baseUrl}?team=${size}&seed=${seed}` });
  await waitFor(() => evaluate(cdp, "location.search === '?team=" + size + "&seed=" + seed + "' && document.readyState === 'complete' && typeof updatePhysics === 'function' && typeof beginOpeningTurn === 'function' && typeof TEAM_N !== 'undefined' && TEAM_N === " + size), "page " + size + "/" + seed, 600, 100);
  await evaluate(cdp, driver.source + "\n;typeof runPageMatch");
}
async function playOne(cell, attempt = 0) {
  const t0 = Date.now();
  try {
    await loadPage(cell.size, cell.seed);
    const rec = await evaluate(cdp, "runPageMatch(" + JSON.stringify(Object.assign({}, cell, { plainOnly })) + ")", matchTimeoutMs);
    rec.ms = Date.now() - t0;
    return rec;
  } catch (e) {
    if (attempt === 0 && (cdp.closed || /socket|timeout/i.test(String(e)))) {   // one reconnect (phone Chrome may drop the socket), then give up on this cell
      try { cdp.close(); await connect(); return await playOne(cell, 1); } catch (e2) { return Object.assign(errorRecord(cell, "cdp: " + String(e2.message || e2)), { ms: Date.now() - t0 }); }
    }
    return Object.assign(errorRecord(cell, "cdp: " + String(e.message || e)), { ms: Date.now() - t0 });
  }
}

function summary(matches) {
  const mean = a => a.reduce((s, v) => s + v, 0) / (a.length || 1);
  const lines = ["hero       size   n  rounds  left win  errors"];
  for (const hero of driver.HEROES) for (const size of [1, 2, 3]) {
    const m = matches.filter(x => x.hero === hero && x.size === size);
    if (!m.length) continue;
    const win = m.filter(x => x.winner === "left" || x.winner === "cap_left").length / m.length;
    lines.push(`${hero.padEnd(10)} ${String(size).padStart(4)} ${String(m.length).padStart(3)} ${mean(m.map(x => x.rounds)).toFixed(1).padStart(7)} ${((win * 100).toFixed(0) + "%").padStart(8)} ${String(m.reduce((s, x) => s + x.errors.length, 0)).padStart(7)}`);
  }
  return lines.join("\n");
}

let exitCode = 0;
const started = new Date().toISOString();
let matches = [], userAgent = null;
try {
  if (mode === "desktop") {
    const chromeCandidates = process.env.CHROME_PATH ? [process.env.CHROME_PATH] : [
      "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/Applications/Chromium.app/Contents/MacOS/Chromium",
      "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"];
    const chromePath = chromeCandidates.find(existsSync);
    if (!chromePath) throw new Error("Chrome or Chromium was not found. Set CHROME_PATH.");
    const port = 44800 + Math.floor(Math.random() * 1000), debugPort = port + 1000;
    server = spawn("python3", ["-B", "scripts/dev_server.py", String(port)], { cwd: root, stdio: "ignore" });
    await waitFor(async () => (await request(`http://127.0.0.1:${port}/`)).status < 400, "dev server", 100, 100);
    tempDir = await mkdtemp(path.join(os.tmpdir(), "pk-matrix-"));
    chrome = spawn(chromePath, ["--headless=new", `--remote-debugging-port=${debugPort}`, `--user-data-dir=${tempDir}`, "--no-first-run", "--no-default-browser-check", "--disable-background-timer-throttling", "--disable-renderer-backgrounding", "--window-size=1280,720", "about:blank"], { stdio: "ignore" });
    browserBase = `http://127.0.0.1:${debugPort}`;
    baseUrl = `http://127.0.0.1:${port}/index.html`;
  } else {
    browserBase = `http://127.0.0.1:${cdpPort}`;
    baseUrl = phoneUrl.split("?")[0];
    await waitFor(() => json(`${browserBase}/json/version`), "phone Chrome on 127.0.0.1:" + cdpPort + " (adb -s <phone-ip>:5555 forward tcp:" + cdpPort + " localabstract:chrome_devtools_remote)", 20, 500);
  }
  await connect();
  userAgent = await evaluate(cdp, "navigator.userAgent");

  const cells = driver.cells(perCell).filter(c => (!onlyHero || c.hero === onlyHero) && (!onlySize || String(c.size) === String(onlySize)));
  if (flag("resume") && existsSync(outFile)) {
    try { const old = JSON.parse(readFileSync(outFile, "utf8")); matches = (old.matches || []).filter(m => !m.errors || !m.errors.length); } catch (_) { matches = []; }
  }
  const done = new Set(matches.map(m => m.hero + "|" + m.size + "|" + m.seed));
  const todo = cells.filter(c => !done.has(c.hero + "|" + c.size + "|" + c.seed));
  await mkdir(path.dirname(outFile), { recursive: true });
  const save = () => writeFile(outFile, JSON.stringify({ end: "page", source: "chrome-" + mode, userAgent, options: { plainOnly }, started, finished: null, matches }, null, 1) + "\n");
  const t0 = Date.now();
  for (const cell of todo) {
    const rec = await playOne(cell);
    matches.push(rec);
    if (matches.length % 5 === 0) { await save(); console.error(`  ${matches.length}/${cells.length} matches, ${((Date.now() - t0) / 1000).toFixed(0)} s`); }
  }
  await writeFile(outFile, JSON.stringify({ end: "page", source: "chrome-" + mode, userAgent, options: { plainOnly }, started, finished: new Date().toISOString(), matches }, null, 1) + "\n");
  console.log(summary(matches));
  const errored = matches.filter(m => m.errors.length);
  console.log(`run_page_matrix_cdp (${mode}): ${matches.length} matches in ${((Date.now() - t0) / 1000).toFixed(0)} s, ${errored.length} with errors -> ${path.relative(root, outFile)}`);
  for (const m of errored.slice(0, 10)) console.log(`ERROR seed ${m.seed} (${m.hero} x${m.size}): ${String(m.errors[0]).slice(0, 200)}`);
  if (errored.length) exitCode = 1;
} catch (error) {
  console.error("run_page_matrix_cdp: " + (error && error.stack ? error.stack : error));
  exitCode = 1;
} finally {
  if (cdp) cdp.close();
  if (mode === "phone" && tabId) { try { await request(`${browserBase}/json/close/${tabId}`); } catch (_) { /* tab may already be gone */ } }
  await stop(chrome);
  await stop(server);
  if (tempDir) await rm(tempDir, { recursive: true, force: true, maxRetries: 5, retryDelay: 150 });
}
process.exit(exitCode);
