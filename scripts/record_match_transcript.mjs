#!/usr/bin/env node
/*
 * Deterministic N=1 browser transcript recorder. CDP drives only the existing
 * fixed-step match code; requestAnimationFrame is disabled so each recorded
 * frame is advanced by exactly PHYSICS_STEP.
 */
import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync } from "node:fs";
import { mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import http from "node:http";
import os from "node:os";
import path from "node:path";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const baselinePath = path.join(root, "docs", "transcripts", "n1_baseline.json");
const baselineHashPath = path.join(root, "docs", "transcripts", "n1_baseline.sha256");
const writeBaseline = process.argv.includes("--write-baseline");
const port = 44800 + Math.floor(Math.random() * 1000);
const debugPort = port + 1000;
const chromeCandidates = process.env.CHROME_PATH ? [process.env.CHROME_PATH] : [
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"
];
const chromePath = chromeCandidates.find(existsSync);
const matches = [
  { seed: 208001, throws: [[48, 30], [54, 32], [60, 34], [52, 31], [56, 33], [50, 35]] },
  { seed: 208002, throws: [[55, 29], [49, 33], [58, 31], [53, 35], [47, 32], [61, 30]] },
  { seed: 208003, throws: [[51, 34], [57, 30], [46, 33], [59, 29], [54, 35], [50, 31]] }
];

function delay(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
function json(url) {
  return new Promise((resolve, reject) => http.get(url, response => {
    let data = "";
    response.on("data", chunk => { data += chunk; });
    response.on("end", () => { try { resolve(JSON.parse(data)); } catch (error) { reject(error); } });
  }).on("error", reject));
}
async function waitFor(url, attempts = 80) {
  let lastError;
  for (let attempt = 0; attempt < attempts; attempt++) {
    try { return await json(url); } catch (error) { lastError = error; await delay(100); }
  }
  throw lastError || new Error("timed out waiting for " + url);
}
async function waitForHttp(url, attempts = 80) {
  let lastError;
  for (let attempt = 0; attempt < attempts; attempt++) {
    try {
      const status = await new Promise((resolve, reject) => http.get(url, response => {
        response.resume(); response.on("end", () => resolve(response.statusCode));
      }).on("error", reject));
      if (status >= 200 && status < 400) return;
      lastError = new Error("HTTP " + status);
    } catch (error) { lastError = error; }
    await delay(100);
  }
  throw lastError || new Error("timed out waiting for " + url);
}
async function stop(child) {
  if (!child || child.exitCode !== null) return;
  const exited = new Promise(resolve => child.once("exit", resolve));
  child.kill();
  await Promise.race([exited, delay(3000)]);
}
class Cdp {
  constructor(url) { this.url = url; this.id = 0; this.pending = new Map(); }
  async open() {
    this.socket = new WebSocket(this.url);
    await new Promise((resolve, reject) => {
      this.socket.addEventListener("open", resolve, { once: true });
      this.socket.addEventListener("error", reject, { once: true });
    });
    this.socket.addEventListener("message", event => {
      const message = JSON.parse(event.data), pending = this.pending.get(message.id);
      if (!pending) return;
      this.pending.delete(message.id);
      if (message.error) pending.reject(new Error(message.error.message));
      else pending.resolve(message.result);
    });
  }
  call(method, params = {}) {
    const id = ++this.id;
    this.socket.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }));
  }
  close() { if (this.socket) this.socket.close(); }
}

const prePageScript = `(() => {
  let state = 0x208001;
  const clock = 0;
  Math.random = () => {
    state = (state + 0x6D2B79F5) >>> 0;
    let t = state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  Date.now = () => clock;
  try { Object.defineProperty(Performance.prototype, "now", { configurable: true, value: () => clock }); } catch (_) {}
  window.requestAnimationFrame = () => 0;
})();`;

const runMatch = (match) => `(() => {
  const snapshot = label => ({
    label,
    units: [player, ai].map((unit, index) => ({
      id: index === 0 ? "left_0" : "right_0",
      x: Number(unit.x.toFixed(4)), y: Number(unit.y.toFixed(4)), hp: Number(unit.hp.toFixed(4)),
      statuses: publicStatusWords(unit)
    })),
    turn,
    wind: Number(wind.toFixed(4)),
    weather: currentWeather().id,
    roundHash: currentRoundHash(),
    damageTexts: floatTexts.map(text => text.text),
    energy: { left: energy.player, right: energy.ai },
    items: { left: supply.player ? 1 : 0, right: supply.ai ? 1 : 0 }
  });
  const settle = () => {
    for (let step = 0; projectiles.length && step < 1200; step++) updatePhysics(PHYSICS_STEP);
    if (projectiles.length) throw new Error("projectile did not resolve");
  };
  // The page's Normal AI remains selected. Scripted throws make this a stable
  // regression fixture rather than a test of AI accuracy.
  currentHero = "skeleton";
  aiClass = "wizard";
  ai.profile = "wizard";
  seats = { left: "human", right: "ai", level: { left: "normal", right: "normal" } };
  resetGame();
  currentHero = "skeleton";
  aiClass = "wizard";
  ai.profile = "wizard";
  applyClassStats();
  player.x = player.targetX;
  ai.x = ai.targetX;
  matchStarted = true;
  turn = "player";
  advanceAfterAttack = () => {};
  const records = [snapshot("start")];
  ${JSON.stringify(match.throws)}.forEach((shot, index) => {
    turn = "player";
    executeThrow("player", shot[1], shot[0]);
    settle();
    records.push(snapshot("round " + (index + 1) + " player"));
    turn = "ai";
    executeThrow("ai", shot[1], shot[0]);
    settle();
    records.push(snapshot("round " + (index + 1) + " ai"));
    resolveRound();
    records.push(snapshot("round " + (index + 1) + " resolved"));
  });
  return { seed: matchSeed, heroes: { left: currentHero, right: ai.profile }, aiLevel: levelFor("right"), records };
})()`;

async function evaluate(cdp, expression) {
  const result = await cdp.call("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text || "page evaluation failed");
  return result.result.value;
}
async function recordSuite(cdp) {
  const output = { version: 1, mode: "n1", matches: [] };
  for (const match of matches) {
    await cdp.call("Page.navigate", { url: `http://127.0.0.1:${port}/index.html?seed=${match.seed}` });
    for (let attempt = 0; attempt < 80; attempt++) {
      const ready = await evaluate(cdp, "typeof updatePhysics === 'function' && typeof resetGame === 'function'");
      if (ready) break;
      if (attempt === 79) throw new Error("page match API did not initialize");
      await delay(50);
    }
    output.matches.push(await evaluate(cdp, runMatch(match)));
  }
  return JSON.stringify(output, null, 2) + "\n";
}

if (!chromePath) throw new Error("Chrome or Chromium was not found. Set CHROME_PATH to run this measured check.");
let server, chrome, tempDir, cdp;
try {
  server = spawn("python3", ["-B", "scripts/dev_server.py", String(port)], { cwd: root, stdio: "ignore" });
  await waitForHttp(`http://127.0.0.1:${port}/`);
  tempDir = await mkdtemp(path.join(os.tmpdir(), "pk-transcript-"));
  chrome = spawn(chromePath, ["--headless=new", `--remote-debugging-port=${debugPort}`, `--user-data-dir=${tempDir}`, "--no-first-run", "--no-default-browser-check", "about:blank"], { stdio: "ignore" });
  const targets = await waitFor(`http://127.0.0.1:${debugPort}/json/list`);
  const page = targets.find(target => target.type === "page");
  if (!page) throw new Error("Chrome did not open a page target");
  cdp = new Cdp(page.webSocketDebuggerUrl);
  await cdp.open();
  await cdp.call("Page.enable");
  await cdp.call("Runtime.enable");
  await cdp.call("Page.addScriptToEvaluateOnNewDocument", { source: prePageScript });
  const first = await recordSuite(cdp);
  const second = await recordSuite(cdp);
  if (first !== second) {
    const firstIndex = Array.from({ length: Math.min(first.length, second.length) }, (_, index) => index).find(index => first[index] !== second[index]);
    throw new Error("two recordings differed under the same seeds at byte " + (firstIndex === undefined ? Math.min(first.length, second.length) : firstIndex));
  }
  const hash = createHash("sha256").update(first).digest("hex");
  if (writeBaseline) {
    await mkdir(path.dirname(baselinePath), { recursive: true });
    await writeFile(baselinePath, first);
    await writeFile(baselineHashPath, hash + "  n1_baseline.json\n");
    console.log(`record_match_transcript: wrote deterministic N=1 baseline (${hash})`);
  } else {
    const baseline = await readFile(baselinePath, "utf8");
    if (baseline !== first) throw new Error("N=1 transcript differs from docs/transcripts/n1_baseline.json");
    console.log(`record_match_transcript: baseline matches (${hash})`);
  }
  console.log("record_match_transcript: two recordings are byte-identical");
} finally {
  if (cdp) cdp.close();
  await stop(chrome);
  await stop(server);
  if (tempDir) await rm(tempDir, { recursive: true, force: true, maxRetries: 5, retryDelay: 150 });
}
