#!/usr/bin/env node
/*
 * Chrome seat of the hybrid room test: the REAL index.html in a real Chrome (desktop: a headless Chrome started here; phone: the phone's Chrome
 * over a forwarded DevTools port, like scripts/run_page_matrix_cdp.mjs --phone), joined to a relay room by the page's own RelayClient, playing a
 * whole team with the page's own computer shot (scripts/hybrid_seat_core.js).
 *
 *   node scripts/hybrid_seat_chrome.mjs --kind desktop|phone --page-url http://127.0.0.1:8080/index.html --relay ws://127.0.0.1:8765
 *        --code ABC234 --team red --heroes skeleton,wizard,bat --level normal --rng 7 [--speed 0] [--max-s 300] [--gap-ms 130] [--cdp-port 9333]
 *
 * Prints one line "HYBRID_SEAT_RESULT {json}" when the match is over; exit code 0 when the match reached a winner, 1 otherwise.
 * Only the owner's terminal can start it (Chrome and sockets do not start in the Claude Bash sandbox). The runner scripts/run_hybrid_room.py starts it.
 * Phone: adb reverse tcp:8080 tcp:8080 (page server), adb reverse tcp:<relay port> tcp:<relay port> (run the runner with --relay-port <fixed>),
 * adb forward tcp:9333 localabstract:chrome_devtools_remote; keep the phone awake with Chrome open.
 */
import { spawn } from "node:child_process";
import { existsSync, rmSync } from "node:fs";
import { mkdtemp, readFile, rm } from "node:fs/promises";
import http from "node:http";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";

const require = createRequire(import.meta.url);
const core = require("./hybrid_seat_core.js");

const argv = process.argv.slice(2);
const opt = (name, def) => { const i = argv.indexOf("--" + name); return i >= 0 && argv[i + 1] !== undefined ? argv[i + 1] : def; };
const kind = opt("kind", "desktop"), pageUrl = opt("page-url", ""), relay = opt("relay", ""), code = opt("code", ""), team = opt("team", "red"), level = opt("level", "normal");
const heroes = opt("heroes", "").split(",").filter(Boolean);
const rng = Number(opt("rng", 1)), speed = Number(opt("speed", 0)), maxS = Number(opt("max-s", 300)), gapMs = Number(opt("gap-ms", 130)), cdpPort = Number(opt("cdp-port", 9333));
if (!pageUrl || !relay || !code || !heroes.length || !["desktop", "phone"].includes(kind)) { console.error("usage: hybrid_seat_chrome.mjs --kind desktop|phone --page-url URL --relay ws://host:port --code CODE --team red|white --heroes a,b,c [--level L] [--rng N] [--speed S] [--max-s N] [--gap-ms N] [--cdp-port N]"); process.exit(2); }

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
function request(url, method = "GET") {
  return new Promise((resolve, reject) => {
    const req = http.request(url, { method }, response => { let data = ""; response.on("data", c => { data += c; }); response.on("end", () => resolve({ status: response.statusCode, body: data })); });
    req.on("error", reject); req.setTimeout(10000, () => req.destroy(new Error("timeout " + url))); req.end();
  });
}
async function json(url, method = "GET") { const r = await request(url, method); if (r.status < 200 || r.status >= 300) throw new Error("HTTP " + r.status + " for " + url); return JSON.parse(r.body); }
async function waitFor(fn, what, attempts = 100, ms = 100) { let last; for (let i = 0; i < attempts; i++) { try { const v = await fn(); if (v) return v; } catch (e) { last = e; } await delay(ms); } throw last || new Error("timed out waiting for " + what); }

class Cdp {
  constructor(url) { this.url = url; this.id = 0; this.pending = new Map(); this.closed = false; }
  async open() {
    this.socket = new WebSocket(this.url);
    await new Promise((resolve, reject) => { this.socket.addEventListener("open", resolve, { once: true }); this.socket.addEventListener("error", () => reject(new Error("DevTools socket error")), { once: true }); });
    this.socket.addEventListener("message", event => { const m = JSON.parse(event.data), p = this.pending.get(m.id); if (!p) return; this.pending.delete(m.id); if (m.error) p.reject(new Error(m.error.message)); else p.resolve(m.result); });
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

// A phone page goes full screen only from a user gesture (the Start button calls enterPhoneFullscreen). A seat joins a room by script and never presses Start, so the address bar stayed on
// screen and the stage was smaller (owner 2026-11-17, screenshot of the phone). CDP can run code as a gesture: userGesture true.
async function evaluateAsGesture(cdp, expression) {
  const result = await cdp.call("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true, userGesture: true }, 30000);
  return result.result && result.result.value;
}

let chrome = null, tempDir = null, cdp = null, tabId = null, browserBase = null, exitCode = 1;
for (const signal of ["SIGTERM", "SIGINT"]) process.on(signal, () => {   // the runner stops a stuck seat with SIGTERM: take Chrome and its profile with us
  try { if (chrome && chrome.exitCode === null) chrome.kill("SIGKILL"); } catch (_) { /* gone */ }
  try { if (tempDir) rmSync(tempDir, { recursive: true, force: true }); } catch (_) { /* best effort */ }
  process.exit(1);
});
try {
  if (kind === "desktop") {
    const candidates = process.env.CHROME_PATH ? [process.env.CHROME_PATH] : ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/Applications/Chromium.app/Contents/MacOS/Chromium", "/usr/bin/google-chrome", "/usr/bin/chromium"];
    const chromePath = candidates.find(existsSync);
    if (!chromePath) throw new Error("Chrome or Chromium was not found. Set CHROME_PATH.");
    tempDir = await mkdtemp(path.join(os.tmpdir(), "pk-hybrid-"));
    chrome = spawn(chromePath, ["--headless=new", "--remote-debugging-port=0", `--user-data-dir=${tempDir}`, "--no-first-run", "--no-default-browser-check", "--disable-background-timer-throttling", "--disable-renderer-backgrounding", "--window-size=1280,720", "about:blank"], { stdio: "ignore" });
    // port 0: Chrome picks a free port and writes it to DevToolsActivePort in the profile folder (no collision between two seats or with an orphan)
    const debugPort = await waitFor(async () => { const t = await readFile(path.join(tempDir, "DevToolsActivePort"), "utf8"); const n = Number(t.split("\n")[0]); return n > 0 ? n : null; }, "Chrome DevToolsActivePort", 300, 100);
    browserBase = `http://127.0.0.1:${debugPort}`;
  } else {
    browserBase = `http://127.0.0.1:${cdpPort}`;
  }
  await waitFor(() => json(`${browserBase}/json/version`), "Chrome DevTools at " + browserBase, 100, 200);
  let target;
  if (kind === "desktop") {
    const list = await waitFor(async () => { const t = await json(`${browserBase}/json/list`); return t.find(x => x.type === "page") ? t : null; }, "Chrome page target");
    target = list.find(x => x.type === "page");
  } else {
    const openUrl = "about:blank";
    target = null;
    try { target = await json(`${browserBase}/json/new?${encodeURIComponent(openUrl)}`, "PUT"); } catch (_) { try { target = await json(`${browserBase}/json/new?${encodeURIComponent(openUrl)}`); } catch (_2) { target = null; } }
    if (target) tabId = target.id;   // only a tab this script opened is closed at the end
    else {   // the phone's Chrome answers HTTP 405 to /json/new (2026-11-17 run: 20 of 20 phone matches never started): use the page the phone already has open and navigate it
      const list = await json(`${browserBase}/json/list`);
      target = list.find(x => x.type === "page");
      if (!target) throw new Error("no page target on the phone: open Chrome on it first");
      for (const other of list.filter(x => x.type === "page" && x.id !== target.id)) { try { await request(`${browserBase}/json/close/${other.id}`); } catch (_) { /* a tab that is already gone */ } }   // the owner wants no spare tabs: the visible tab must be the one that plays (2026-11-17: the screen showed an idle tab while the seat played in another)
    }
  }
  cdp = new Cdp(target.webSocketDebuggerUrl);
  await cdp.open();
  await cdp.call("Page.enable"); await cdp.call("Runtime.enable");
  if (kind === "phone") { try { await cdp.call("Page.bringToFront"); } catch (_) { /* older Chrome: the tab is the only one anyway */ } }
  await cdp.call("Page.addScriptToEvaluateOnNewDocument", { source: core.pacedSocketPageSource(gapMs) });   // before any page script: the page's WebSocket is the paced one
  const n = heroes.length;
  await cdp.call("Page.navigate", { url: `${pageUrl}?team=${n}&relay=${encodeURIComponent(relay)}` });
  await waitFor(() => evaluate(cdp, "document.readyState === 'complete' && typeof updatePhysics === 'function' && typeof startMatch === 'function' && typeof leftAiShot === 'function' && typeof TEAM_N !== 'undefined' && TEAM_N === " + n), "page", 600, 100);
  await waitFor(() => evaluate(cdp, "(function () { var b = document.getElementById('start-go'); return !!b && !b.disabled; })()"), "start button enabled (assets loaded)", 1200, 100);   // a phone may need a minute
  if (kind === "phone") { await evaluateAsGesture(cdp, "(typeof enterPhoneFullscreen === 'function') ? (enterPhoneFullscreen(), true) : false"); await delay(800); }
  const config = { team, heroes, level, rngSeed: rng, speed, maxRealSeconds: maxS, paintMs: kind === "phone" ? 100 : 0 };
  await evaluate(cdp, "(" + core.installSource + ")(" + JSON.stringify(config) + ")");
  await evaluate(cdp, "__hybridSeat.join(" + JSON.stringify(code) + ")");
  const started = Date.now();
  let result = null;
  while (!result) {
    await delay(500);
    result = await evaluate(cdp, "__hybridSeatResult");
    if (!result && Date.now() - started > (maxS + 30) * 1000) result = { reason: "host_timeout", errors: ["host gave up"] };
  }
  exitCode = result.reason === "game_over" && !(result.errors || []).length ? 0 : 1;
  console.log("HYBRID_SEAT_RESULT " + JSON.stringify(result));
} catch (error) {
  console.error("hybrid_seat_chrome: " + (error && error.stack ? error.stack : error));
  console.log("HYBRID_SEAT_RESULT " + JSON.stringify({ reason: "host_error", errors: [String(error && error.message ? error.message : error)] }));
  exitCode = 1;
} finally {
  if (cdp) cdp.close();
  if (kind === "phone" && tabId) { try { await request(`${browserBase}/json/close/${tabId}`); } catch (_) { /* tab may already be gone */ } }
  if (chrome && chrome.exitCode === null) { chrome.kill(); await Promise.race([new Promise(r => chrome.once("exit", r)), delay(3000)]); }
  if (tempDir) await rm(tempDir, { recursive: true, force: true, maxRetries: 5, retryDelay: 150 });
}
process.exit(exitCode);
