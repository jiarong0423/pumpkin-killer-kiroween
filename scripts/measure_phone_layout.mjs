#!/usr/bin/env node
/*
 * Browser geometry regression for task 190. It deliberately uses Chrome DevTools
 * Protocol rather than a test dependency. Node 22+ supplies the WebSocket client.
 *
 * --review adds a DOM-only numerical audit for task 204b. It never reads pixels
 * from screenshots: Canvas text and gradient/translucent backgrounds are reported
 * as outside the scope of DOM/computed-style measurement.
 */
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import http from "node:http";
import os from "node:os";
import path from "node:path";

const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const PROPERTY_MODE = process.argv.includes("--property");
const COLLECT = process.env.PK_COLLECT === "1";   // collect every failing viewport instead of stopping at the first (the 200 random viewports of --property: one known failure must not hide the rest)
const SHOOT_MODE = process.argv.includes("--shots") || process.argv.includes("--review");
const REVIEW_MODE = process.argv.includes("--review");
const START_MODE = process.argv.includes("--start");
const PROPERTY_SEED = 19120261116;
const fixedViewports = [
  { width: 640, height: 360, dpr: 2.5 }, { width: 720, height: 405, dpr: 2.5 }, { width: 800, height: 450, dpr: 2.5 }, { width: 854, height: 480, dpr: 2.5 }, { width: 960, height: 540, dpr: 2.5 },
  { width: 873, height: 392, dpr: 2.5 }, { width: 915, height: 412, dpr: 2.5 }, { width: 844, height: 390, dpr: 2.5 }, { width: 932, height: 430, dpr: 2.5 }, { width: 667, height: 375, dpr: 2.5 },
  { width: 873, height: 330, dpr: 2.5 }, { width: 915, height: 350, dpr: 2.5 }, { width: 844, height: 330, dpr: 2.5 }, { width: 932, height: 365, dpr: 2.5 }, { width: 667, height: 300, dpr: 2.5 }
];
const shotViewports = fixedViewports.concat({ width: 1440, height: 900, dpr: 1 });
function seeded(seed) { let state = seed >>> 0; return () => { state = (state + 0x6D2B79F5) >>> 0; let t = state; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
function propertyViewports() { const random = seeded(PROPERTY_SEED); return Array.from({ length: 200 }, () => ({ width: 560 + Math.floor(random() * 441), height: 300 + Math.floor(random() * 181), dpr: +(1.5 + random() * 1.5).toFixed(2) })); }
const viewports = (SHOOT_MODE || REVIEW_MODE) ? shotViewports : (PROPERTY_MODE ? propertyViewports() : fixedViewports);
const shotDirectory = path.join(root, "docs", "ui_shots");
const port = 43800 + Math.floor(Math.random() * 1000);
const debugPort = port + 1000;
const chromeCandidates = process.env.CHROME_PATH ? [process.env.CHROME_PATH] : [
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "/usr/bin/google-chrome", "/usr/bin/chromium", "/usr/bin/chromium-browser"
];
const chromePath = chromeCandidates.find(existsSync);

function delay(ms) { return new Promise(resolve => setTimeout(resolve, ms)); }
function getJson(url) {
  return new Promise((resolve, reject) => {
    http.get(url, response => {
      let data = "";
      response.on("data", chunk => { data += chunk; });
      response.on("end", () => { try { resolve(JSON.parse(data)); } catch (error) { reject(error); } });
    }).on("error", reject);
  });
}
async function waitFor(url, attempts = 80) {
  let last;
  for (let i = 0; i < attempts; i++) {
    try { return await getJson(url); } catch (error) { last = error; await delay(100); }
  }
  throw last || new Error("timed out waiting for " + url);
}
async function waitForHttp(url, attempts = 80) {
  let last;
  for (let i = 0; i < attempts; i++) {
    try {
      const status = await new Promise((resolve, reject) => http.get(url, response => {
        response.resume(); response.on("end", () => resolve(response.statusCode));
      }).on("error", reject));
      if (status >= 200 && status < 400) return;
      last = new Error("HTTP " + status);
    } catch (error) { last = error; }
    await delay(100);
  }
  throw last || new Error("timed out waiting for " + url);
}
async function stopProcess(child) {
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
      const message = JSON.parse(event.data);
      const pending = this.pending.get(message.id);
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

async function captureShot(cdp, view, name) {
  const image = await cdp.call("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
  await writeFile(path.join(shotDirectory, `${name}-${view.width}x${view.height}.png`), Buffer.from(image.data, "base64"));
}
async function waitForPageReady(cdp, attempts = 80) {
  for (let i = 0; i < attempts; i++) {
    const result = await cdp.call("Runtime.evaluate", { expression: "document.readyState === 'complete' && typeof startMatch === 'function' && !!document.getElementById('start-go').onclick", returnByValue: true });
    if (result.result.value) return;
    await delay(100);
  }
  throw new Error("page did not expose the start-match controls");
}
async function startBattle(cdp) {
  const result = await cdp.call("Runtime.evaluate", { expression: "startMatch(); document.getElementById('coin-toss-skip').click(); hideFirstHint(); !document.getElementById('start-screen').classList.contains('hidden')", returnByValue: true, awaitPromise: true });
  if (result.result.value) throw new Error("startMatch left the start screen visible");
  await delay(450);
}
async function captureViews(cdp, view) {
  await captureShot(cdp, view, "start");
  await startBattle(cdp);
  await captureShot(cdp, view, "battle");
  await cdp.call("Runtime.evaluate", { expression: "gameOver = 'player'; turn = 'over';", awaitPromise: true });
  await delay(120);
  await captureShot(cdp, view, "result");
  await cdp.call("Runtime.evaluate", { expression: "toggleSettings(true);", awaitPromise: true });
  await delay(80);
  await captureShot(cdp, view, "settings");
}

async function startGeometry(cdp) {
  const expression = `(() => {
    const viewport = window.visualViewport || { width: innerWidth, height: innerHeight };
    const vp = { left:0, top:0, right:viewport.width, bottom:viewport.height };
    const rect = e => { const r=e.getBoundingClientRect(); return {left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height}; };
    const visible = e => { const r=e.getBoundingClientRect(), s=getComputedStyle(e); return s.display !== "none" && !e.hidden && s.visibility !== "hidden" && r.width > 0 && r.height > 0; };
    const hit = (a,b) => Math.max(a.left,b.left)<Math.min(a.right,b.right) && Math.max(a.top,b.top)<Math.min(a.bottom,b.bottom);
    const inside = r => r.left >= -.5 && r.top >= -.5 && r.right <= vp.right + .5 && r.bottom <= vp.bottom + .5;
    const interactive = Array.from(document.querySelectorAll("#start-screen button, #settings-btn")).filter(visible).map(e => ({ id:e.id || e.className, rect:rect(e) }));
    const cardIssues = Array.from(document.querySelectorAll(".pick-card")).flatMap(card => { const cr=rect(card); return Array.from(card.querySelectorAll(".chip")).filter(visible).filter(chip => { const r=rect(chip); return r.left<cr.left || r.top<cr.top || r.right>cr.right || r.bottom>cr.bottom; }).map(chip => chip.className); });
    const cards = Array.from(document.querySelectorAll(".pick-card")).filter(visible).map(rect);
    const overlaps=[]; for(let i=0;i<interactive.length;i++) for(let j=i+1;j<interactive.length;j++) if(hit(interactive[i].rect,interactive[j].rect)) overlaps.push(interactive[i].id+"/"+interactive[j].id);
    const cardOverlaps=[]; for(let i=0;i<cards.length;i++) for(let j=i+1;j<cards.length;j++) if(hit(cards[i],cards[j])) cardOverlaps.push(i+"/"+j);
    const title=rect(document.querySelector(".start-topbar h1")); const titleHits=interactive.filter(x=>hit(title,x.rect)).map(x=>x.id);
    const hero = document.querySelector("#pick-heroes .pick-card").dataset.k; let cycleOk=false; for(let i=0;i<8;i++){ document.getElementById("hero-next").click(); if(document.querySelector("#pick-heroes .pick-card").dataset.k===hero) cycleOk=true; }   /* the carousel skips heroes locked by the other team slots (3 versus 3: only 6 are selectable), so it returns to the start hero after the number of selectable heroes, not always after 8 (red-team R6B-3) */
    return { viewport, scroll: { width:document.documentElement.scrollWidth, height:document.documentElement.scrollHeight }, interactive, inside:interactive.every(x=>inside(x.rect)), overlaps, cardOverlaps, cardIssues, titleInside:inside(title), titleHits, cycleOk };
  })()`;
  const result = await cdp.call("Runtime.evaluate", { expression, returnByValue:true, awaitPromise:true });
  return result.result.value;
}
function assertStartGeometry(viewportInput, state) {
  const { width, height } = viewportInput;
  if (state.scroll.width > state.viewport.width + 1 || state.scroll.height > state.viewport.height + 1) throw new Error(`${width}x${height}: start screen scrolls ${state.scroll.width}x${state.scroll.height}`);
  if (!state.inside || !state.titleInside) throw new Error(`${width}x${height}: a start control or title leaves the viewport`);
  if (state.overlaps.length || state.cardOverlaps.length || state.cardIssues.length || state.titleHits.length) throw new Error(`${width}x${height}: start intersections ${state.overlaps.concat(state.cardOverlaps, state.cardIssues, state.titleHits).join(", ")}`);
  const small = state.interactive.filter(row => row.rect.width < 44 || row.rect.height < 44); if (small.length) throw new Error(`${width}x${height}: undersized start controls ${small.map(row=>row.id).join(", ")}`);
  if (!state.cycleOk) throw new Error(`${width}x${height}: the hero-next button never returned to the selected hero in 8 presses`);
}
async function geometry(cdp) {
  const expression = `(() => {
    const rect = element => { const r = element.getBoundingClientRect(); return { left:r.left, top:r.top, right:r.right, bottom:r.bottom, width:r.width, height:r.height }; };
    const canvas = document.getElementById("gameCanvas");
    const canvasRect = rect(canvas), stage = rect(document.getElementById("game-container"));
    const logical = (x, y, w, h) => ({ left: canvasRect.left + x / 1920 * canvasRect.width, top: canvasRect.top + y / 1080 * canvasRect.height, right: canvasRect.left + (x + w) / 1920 * canvasRect.width, bottom: canvasRect.top + (y + h) / 1080 * canvasRect.height, width:w / 1920 * canvasRect.width, height:h / 1080 * canvasRect.height });
    const named = [["player-name-plate", logical(16, 12, 430, 116)], ["opponent-name-plate", logical(1474, 12, 430, 116)], ["countdown-board", logical(740, 6, 440, 110)], ["player-supply", rect(document.getElementById("supply-slot"))], ["opponent-supply", rect(document.getElementById("supply-slot-ai"))], ["dock", rect(document.getElementById("bottom-dock"))]];
    for (const button of document.querySelectorAll("#top-controls button")) named.push([button.id, rect(button)]);
    const visible = named.filter(([, r]) => r.width > 0 && r.height > 0);
    const overlaps = [];
    for (let i = 0; i < visible.length; i++) for (let j = i + 1; j < visible.length; j++) {
      const [aName, a] = visible[i], [bName, b] = visible[j];
      if (Math.max(a.left, b.left) < Math.min(a.right, b.right) && Math.max(a.top, b.top) < Math.min(a.bottom, b.bottom)) overlaps.push(aName + " / " + bName);
    }
    const settingSheet = rect(document.getElementById("settings-sheet"));
    const board = logical(740, 6, 440, 110), dock = rect(document.getElementById("bottom-dock"));
    const intersects = (a, b) => Math.max(a.left, b.left) < Math.min(a.right, b.right) && Math.max(a.top, b.top) < Math.min(a.bottom, b.bottom);
    const settingOverlaps = [["countdown-board", board], ["dock", dock]].filter(([, r]) => intersects(settingSheet, r)).map(([name]) => name);
    const hud = window.__pkHud || {}, hudRect = value => value ? logical(value.left, value.top, value.right - value.left, value.bottom - value.top) : null;
    const hudRects = Object.fromEntries(Object.entries(hud).map(([name, value]) => [name, hudRect(value)]));
    const viewport = window.visualViewport || { width: innerWidth, height: innerHeight };
    return { stage, dock, settings: settingSheet, settingOverlaps, hudRects, viewport:{width:viewport.width, height:viewport.height}, fill:getComputedStyle(document.body, "::before").backgroundImage, overlaps };
  })()`;
  const result = await cdp.call("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  return result.result.value;
}

function assertGeometry(viewportInput, result) {
  const { width, height } = viewportInput, epsilon = 1.1;
  const { stage, dock, settings, hudRects, viewport, overlaps } = result;
  const fullyVisible = stage.left >= -epsilon && stage.top >= -epsilon && stage.right <= viewport.width + epsilon && stage.bottom <= viewport.height + epsilon;
  if (!fullyVisible) throw new Error(`${width}x${height}: stage leaves visual viewport`);
  if (dock.width > 0 && dock.height > 0 && dock.bottom > viewport.height + epsilon) throw new Error(`${width}x${height}: dock bottom ${dock.bottom.toFixed(1)} exceeds ${viewport.height.toFixed(1)}`);
  const dockIntersectsStage = Math.max(stage.left, dock.left) < Math.min(stage.right, dock.right) && Math.max(stage.top, dock.top) < Math.min(stage.bottom, dock.bottom);
  const feetBottom = stage.top + stage.height * .804;
  if (dockIntersectsStage && dock.top < feetBottom + 6 - epsilon) throw new Error(`${width}x${height}: dock top ${dock.top.toFixed(1)} covers feet at ${feetBottom.toFixed(1)}`);
  const settingsVisible = settings.width > 0 && settings.height > 0 && settings.left >= -epsilon && settings.top >= -epsilon && settings.right <= viewport.width + epsilon && settings.bottom <= viewport.height + epsilon;
  if (!settingsVisible) throw new Error(`${width}x${height}: settings sheet does not fit`);
  if (overlaps.length) throw new Error(`${width}x${height}: HUD intersections: ${overlaps.join(", ")}`);
  if (!hudRects.roundWeather || !hudRects.countdown || (Math.max(hudRects.roundWeather.left, hudRects.countdown.left) < Math.min(hudRects.roundWeather.right, hudRects.countdown.right) && Math.max(hudRects.roundWeather.top, hudRects.countdown.top) < Math.min(hudRects.roundWeather.bottom, hudRects.countdown.bottom))) throw new Error(`${width}x${height}: HUD round/weather intersects countdown`);
  if (!result.fill || result.fill === "none") throw new Error(`${width}x${height}: side fill layer is not painted`);
  const ratio = viewport.width / viewport.height, fill = stage.width / viewport.width, stageRatio = stage.width / stage.height;
  // owner 2026-11-17: the stage is full width (a 16:9 core plus mirrored side scenery); its ratio runs from 16:9 up to the 2.6 cap, the old fixed 16:9 rule no longer applies
  if (stageRatio < 16 / 9 - 0.01 || stageRatio > 2.6 + 0.02) throw new Error(`${width}x${height}: stage ratio ${stageRatio.toFixed(2)} is outside 16:9 to 2.6`);
  const requestedMinimum = ratio <= 2.2 ? 0.85 : 0, physicalMaximum = Math.min(1, (16 / 9) / ratio);
  return { width, height, fill, ratio, requestedMinimum, physicalMaximum, stage, dock, margins: Math.max(0, (viewport.width - stage.width) / 2), overlaps: overlaps.length };
}

async function reviewMetrics(cdp) {
  const expression = `(() => {
    const viewport = window.visualViewport || { width: innerWidth, height: innerHeight };
    const vp = { left: 0, top: 0, right: viewport.width, bottom: viewport.height };
    const rect = e => { const r = e.getBoundingClientRect(); return { left:+r.left.toFixed(1), top:+r.top.toFixed(1), right:+r.right.toFixed(1), bottom:+r.bottom.toFixed(1), width:+r.width.toFixed(1), height:+r.height.toFixed(1) }; };
    const intersect = (a, b) => Math.max(a.left,b.left) < Math.min(a.right,b.right) && Math.max(a.top,b.top) < Math.min(a.bottom,b.bottom);
    const visible = e => { const s = getComputedStyle(e), r = e.getBoundingClientRect(); return s.display !== "none" && s.visibility !== "hidden" && +s.opacity !== 0 && r.width > 0 && r.height > 0 && intersect(rect(e), vp); };
    const label = e => e.id ? "#" + e.id : e.className && typeof e.className === "string" ? e.tagName.toLowerCase() + "." + e.className.trim().split(/\\s+/).slice(0,2).join(".") : e.tagName.toLowerCase();
    const directText = e => Array.from(e.childNodes).some(n => n.nodeType === Node.TEXT_NODE && n.textContent.trim());
    const rgba = value => { const m = value.match(/rgba?\\(([^)]+)\\)/); if (!m) return null; const p = m[1].split(",").map(Number); return p.length >= 3 ? { r:p[0], g:p[1], b:p[2], a:p.length > 3 ? p[3] : 1 } : null; };
    const luminance = c => { const f = x => { x /= 255; return x <= .04045 ? x / 12.92 : Math.pow((x + .055) / 1.055, 2.4); }; return .2126*f(c.r)+.7152*f(c.g)+.0722*f(c.b); };
    const contrast = (a, b) => { const x=luminance(a), y=luminance(b); return (Math.max(x,y)+.05)/(Math.min(x,y)+.05); };
    const clippedBy = e => { const r = rect(e); if (r.left < vp.left || r.top < vp.top || r.right > vp.right || r.bottom > vp.bottom) return "viewport"; for (let p=e.parentElement; p && p !== document.documentElement; p=p.parentElement) { const s=getComputedStyle(p), pr=rect(p); if ((/(hidden|clip|scroll|auto)/.test(s.overflowX) && (r.left < pr.left || r.right > pr.right)) || (/(hidden|clip|scroll|auto)/.test(s.overflowY) && (r.top < pr.top || r.bottom > pr.bottom))) return label(p); } return null; };
    const solidBackground = e => { for (let p=e; p && p !== document.documentElement; p=p.parentElement) { const c=rgba(getComputedStyle(p).backgroundColor); if (c && c.a === 1) return c; } return null; };
    const textLineCount = e => Array.from(e.childNodes).filter(n => n.nodeType === Node.TEXT_NODE && n.textContent.trim()).reduce((count, node) => { const range=document.createRange(); range.selectNodeContents(node); return count + range.getClientRects().length; }, 0);
    const text = [], controls = [], clipped = [], wraps = [], lowContrast = [];
    for (const e of document.querySelectorAll("body *")) {
      if (!visible(e)) continue;
      const s=getComputedStyle(e), r=rect(e), name=label(e), textValue=(directText(e) ? e.textContent.trim() : "");
      if (textValue || e.hasAttribute("aria-label")) {
        const record={ element:name, cssPx:+parseFloat(s.fontSize).toFixed(2), devicePx:+(parseFloat(s.fontSize)*devicePixelRatio).toFixed(2), text:textValue.slice(0,60) };
        text.push(record);
        const fg=rgba(s.color), bg=solidBackground(e);
        if (fg && bg) { const ratio=contrast(fg,bg); if (ratio < 4.5) lowContrast.push({ element:name, ratio:+ratio.toFixed(2), text:record.text }); }
      }
      if (e.matches("button,input,select,textarea,a[href],[role=button],[onclick]")) controls.push({ element:name, width:r.width, height:r.height, small:r.width < 44 || r.height < 44 });
      const clipParent=clippedBy(e); if (clipParent) clipped.push({ element:name, by:clipParent, rect:r });
      const lines=textLineCount(e); if (e.matches("button,.chip,.role") && lines > 2) wraps.push({ element:name, lines, text:e.textContent.trim().slice(0,60) });
    }
    const focusable = Array.from(document.querySelectorAll("button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),a[href],[tabindex]:not([tabindex='-1'])")).filter(visible).filter(e => e.tabIndex >= 0);
    const focusOrder=[]; for (const e of focusable) { e.focus({preventScroll:true}); focusOrder.push(label(document.activeElement)); } document.body.focus({preventScroll:true});
    const stage=rect(document.getElementById("game-container")), area=viewport.width*viewport.height, stageArea=stage.width*stage.height;
    const namedIds=["start-screen","side-picker","seat-picker","room-picker","start-go","top-controls","supply-slot","supply-slot-ai","bottom-dock","settings-sheet","settings-btn","help-btn","sound-btn","reset-btn","lang-btn"];
    const named=namedIds.map(id => document.getElementById(id)).filter(e => e && visible(e)).map(e => ({ element:label(e), rect:rect(e) }));
    const overlaps=[]; for (let i=0;i<named.length;i++) for (let j=i+1;j<named.length;j++) if (intersect(named[i].rect,named[j].rect)) overlaps.push(named[i].element+" / "+named[j].element);
    const settingsElement = document.getElementById("settings-sheet"), settingsRect = rect(settingsElement);
    const settingsInfo = { rect: settingsRect, clientHeight: settingsElement.clientHeight, scrollHeight: settingsElement.scrollHeight, scrollable: settingsElement.scrollHeight > settingsElement.clientHeight };
    return { viewport:{width:viewport.width,height:viewport.height,dpr:devicePixelRatio}, coverage:{stagePercent:+(stageArea/area*100).toFixed(1), marginPercent:+((1-stageArea/area)*100).toFixed(1), stage}, text, controls, clipped, wraps, lowContrast, focusOrder, named, overlaps, settingsInfo };
  })()`;
  const result = await cdp.call("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  return result.result.value;
}

function reviewSummary(view, state, metrics) {
  const smallText = metrics.text.filter(row => row.cssPx < 11);
  const smallControls = metrics.controls.filter(row => row.small);
  const unique = list => [...new Set(list)];
  const ids = rows => unique(rows.map(row => row.element)).join(",") || "-";
  const sizeRows = rows => rows.map(row => `${row.element}=${row.width}x${row.height}`).join(",") || "-";
  const textRows = rows => rows.map(row => `${row.element}=${row.cssPx}css/${row.devicePx}device`).join(",") || "-";
  const wrapRows = rows => rows.map(row => `${row.element}=${row.lines}lines`).join(",") || "-";
  const settings = metrics.settingsInfo ? ` settings=${metrics.settingsInfo.rect.width}x${metrics.settingsInfo.clientHeight}/${metrics.settingsInfo.scrollHeight} scroll=${metrics.settingsInfo.scrollable}` : "";
  console.log(`review ${view.width}x${view.height} ${state}: stage=${metrics.coverage.stagePercent}% margin=${metrics.coverage.marginPercent}% text=${metrics.text.length} below11=${smallText.length}[${textRows(smallText)}] controls=${metrics.controls.length} below44=${smallControls.length}[${sizeRows(smallControls)}] clipped=${metrics.clipped.length}[${ids(metrics.clipped)}] wraps=${metrics.wraps.length}[${wrapRows(metrics.wraps)}] contrast<4.5=${metrics.lowContrast.length}[${ids(metrics.lowContrast)}] overlaps=${metrics.overlaps.length}[${metrics.overlaps.join(",") || "-"}] focus=${metrics.focusOrder.join(">")}${settings} `);
}

if (!chromePath) throw new Error("Chrome or Chromium was not found. Set CHROME_PATH to run this measured check.");
let server, chrome, tempDir, cdp;
try {
  server = spawn("python3", ["-B", "scripts/dev_server.py", String(port)], { cwd: root, stdio: "ignore" });
  await waitForHttp(`http://127.0.0.1:${port}/`);
  tempDir = await mkdtemp(path.join(os.tmpdir(), "pk-phone-layout-"));
  chrome = spawn(chromePath, ["--headless=new", `--remote-debugging-port=${debugPort}`, `--user-data-dir=${tempDir}`, "--no-first-run", "--no-default-browser-check", "about:blank"], { stdio: "ignore" });
  const targets = await waitFor(`http://127.0.0.1:${debugPort}/json/list`), pageTarget = targets.find(target => target.type === "page");
  if (!pageTarget) throw new Error("Chrome did not open a page target");
  cdp = new Cdp(pageTarget.webSocketDebuggerUrl);
  await cdp.open(); await cdp.call("Page.enable"); await cdp.call("Runtime.enable");
  if (SHOOT_MODE) await mkdir(shotDirectory, { recursive: true });
  const rows = [];
  const geometryFailures = [];
  const startFailures = [];
  for (const viewport of viewports) {
    const { width, height, dpr } = viewport;
    await cdp.call("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: dpr, mobile: true, screenWidth: width, screenHeight: height });
    const isPhone = width !== 1440;
    await cdp.call("Emulation.setEmulatedMedia", { features: [{ name: "hover", value: isPhone ? "none" : "hover" }, { name: "pointer", value: isPhone ? "coarse" : "fine" }] });
    await cdp.call("Page.navigate", { url: `http://127.0.0.1:${port}/index.html?phone-layout-test=${width}x${height}` });
    await waitForPageReady(cdp);
    await delay(PROPERTY_MODE ? 350 : 900);
    if (START_MODE) {
      const startState = await startGeometry(cdp);
      try { assertStartGeometry(viewport, startState); }
      catch (error) { startFailures.push(error.message); }
      // team of three: the slot chips are on screen too (owner 2026-11-17: each unit has its own hero); the same geometry rules must hold with them
      await cdp.call("Page.navigate", { url: `http://127.0.0.1:${port}/index.html?phone-layout-test=${width}x${height}&team=3` });
      await waitForPageReady(cdp);
      await delay(350);
      const teamState = await startGeometry(cdp);
      const chips = await cdp.call("Runtime.evaluate", { expression: "document.querySelectorAll('#hero-slots .slot-chip').length", returnByValue: true });
      try { if (chips.result.value !== 3) throw new Error(`${width}x${height}: team of 3 shows ${chips.result.value} slot chips`); assertStartGeometry(viewport, teamState); }
      catch (error) { startFailures.push("team=3 " + error.message); }
    }
    if (REVIEW_MODE) { await captureShot(cdp, viewport, "start"); reviewSummary(viewport, "start", await reviewMetrics(cdp)); }
    else if (SHOOT_MODE) await captureViews(cdp, viewport);
    if (REVIEW_MODE) { await startBattle(cdp); await captureShot(cdp, viewport, "battle"); reviewSummary(viewport, "battle", await reviewMetrics(cdp)); await cdp.call("Runtime.evaluate", { expression: "gameOver = 'player'; turn = 'over';", awaitPromise: true }); await delay(120); await captureShot(cdp, viewport, "result"); reviewSummary(viewport, "result", await reviewMetrics(cdp)); await cdp.call("Runtime.evaluate", { expression: "toggleSettings(true);", awaitPromise: true }); await delay(80); await captureShot(cdp, viewport, "settings"); reviewSummary(viewport, "settings", await reviewMetrics(cdp)); }
    await cdp.call("Runtime.evaluate", { expression: "if (typeof fitVisibleViewport === 'function') fitVisibleViewport(); if (typeof startMatch === 'function' && !matchStarted) startMatch(); if (typeof toggleSettings === 'function') toggleSettings(true);", awaitPromise: true });
    await delay(PROPERTY_MODE ? 160 : 350);
    const geometryResult = await geometry(cdp);
    { // the page's own verdict of its layout (owner 2026-11-17: detectable by coordinates, never silently wrong): stage inside the viewport, dock INSIDE the stage and below the feet
      const reportCall = await cdp.call("Runtime.evaluate", { expression: "typeof layoutReport === 'function' ? JSON.stringify(layoutReport()) : 'missing'", returnByValue: true });
      if (reportCall.result.value === "missing" && process.env.PK_ALLOW_MISSING_REPORT !== "1") throw new Error(`${width}x${height}: layoutReport() is missing`);   // PK_ALLOW_MISSING_REPORT=1 only to measure an older page for comparison
      const report = reportCall.result.value === "missing" ? { ok: true } : JSON.parse(reportCall.result.value);
      if (!report.ok) { const message = `${width}x${height}: layoutReport says stageInside=${report.stageInside} dockInStage=${report.dockInStage} feetClear=${report.feetClear} stage=${JSON.stringify(report.stage)} dock=${JSON.stringify(report.dock)}`; if (COLLECT) geometryFailures.push(message); else throw new Error(message); }
    }
    if (REVIEW_MODE) {
      try { rows.push(assertGeometry(viewport, geometryResult)); }
      catch (error) { geometryFailures.push(error.message); rows.push({ width, height, fill: geometryResult.stage.width / geometryResult.viewport.width, stage: geometryResult.stage, dock: geometryResult.dock, margins: Math.max(0, (geometryResult.viewport.width - geometryResult.stage.width) / 2), overlaps: geometryResult.overlaps.length }); }
    } else { try { rows.push(assertGeometry(viewport, geometryResult)); } catch (error) { if (!COLLECT) throw error; geometryFailures.push(error.message); } }
  }
  console.log("viewport    stage(w×h)       fill   margin  dock-bottom  overlaps");
  for (const row of rows) console.log(`${row.width}x${row.height}`.padEnd(12) + `${row.stage.width.toFixed(1)}×${row.stage.height.toFixed(1)}`.padEnd(18) + `${row.fill.toFixed(3)}`.padEnd(7) + `${row.margins.toFixed(1)}`.padEnd(8) + `${row.dock.bottom.toFixed(1)}`.padEnd(13) + row.overlaps);
  console.log(`measure_phone_layout: ${rows.length}/${viewports.length} viewports passed${PROPERTY_MODE ? ` (seed ${PROPERTY_SEED})` : ""}${REVIEW_MODE ? " (review)" : ""}`);
  if (startFailures.length) {
    console.error(`measure_phone_layout: ${startFailures.length} start-screen failures`);
    for (const failure of startFailures) console.error("  " + failure);
    process.exitCode = 1;
  }
  if (geometryFailures.length) {
    console.error(`measure_phone_layout: ${geometryFailures.length} geometry failures${REVIEW_MODE ? " during review" : ""}`);
    for (const failure of geometryFailures) console.error("  " + failure);
    process.exitCode = 1;
  }
} catch (error) {
  if (PROPERTY_MODE) console.error(`measure_phone_layout: seed ${PROPERTY_SEED}; first failing viewport: ${error.message}`);
  throw error;
} finally {
  if (cdp) cdp.close(); await stopProcess(chrome); await stopProcess(server);
  if (tempDir) await rm(tempDir, { recursive: true, force: true, maxRetries: 5, retryDelay: 150 });
}
