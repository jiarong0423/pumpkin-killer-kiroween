#!/usr/bin/env node
/*
 * i18n tests (Node `assert` only). Run: node scripts/test_i18n.js
 *
 *  1. zh-TW.json and en.json have exactly the same keys
 *  2. the {param} set of every key is the same in both languages
 *  3. no empty / non-string values
 *  4. t() fallback order: current language -> zh-TW -> the key itself
 *  5. index.html has no CJK characters outside comments
 *  6. every key used in index.html exists, and every key in the dictionaries is used
 *  7. setLang / init / detect survive a throwing localStorage
 */
"use strict";

const assert = require("assert");
const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..");
const I18N = require(path.join(ROOT, "js", "i18n.js"));

function readJson(file) {
  return JSON.parse(fs.readFileSync(path.join(ROOT, "assets", "i18n", file), "utf8"));
}
const zh = readJson("zh-TW.json");
const en = readJson("en.json");

// Checks run one after another (some are async), in the order they are declared.
const tests = [];
function check(name, fn) { tests.push([name, fn]); }
// Checks that read index.html. `node scripts/test_i18n.js --no-page` skips them (module and dictionary checks only),
// so the library can be tested before the main line has wired the page.
const NO_PAGE = process.argv.includes("--no-page");
function pageCheck(name, fn) { if (!NO_PAGE) tests.push([name, fn]); }

function params(text) {
  const out = new Set();
  const re = /\{(\w+)\}/g;
  let m;
  while ((m = re.exec(text)) !== null) out.add(m[1]);
  return Array.from(out).sort();
}

// ---------------------------------------------------------------------------
// 1-3. Dictionary shape
// ---------------------------------------------------------------------------
check("both dictionaries have exactly the same keys", () => {
  const onlyZh = Object.keys(zh).filter(k => !(k in en));
  const onlyEn = Object.keys(en).filter(k => !(k in zh));
  assert.deepStrictEqual({ onlyZh, onlyEn }, { onlyZh: [], onlyEn: [] },
    "missing from en.json: " + onlyZh.join(", ") + " | missing from zh-TW.json: " + onlyEn.join(", "));
});

check("{param} sets match for every key", () => {
  const bad = [];
  for (const k of Object.keys(zh)) {
    if (!(k in en)) continue;
    const pz = params(zh[k]), pe = params(en[k]);
    if (pz.join(",") !== pe.join(",")) bad.push(k + "  zh=[" + pz + "]  en=[" + pe + "]");
  }
  assert.strictEqual(bad.length, 0, "param mismatch:\n" + bad.join("\n"));
});

check("no empty or non-string values", () => {
  const bad = [];
  for (const [name, dict] of [["zh-TW", zh], ["en", en]]) {
    for (const [k, v] of Object.entries(dict)) {
      if (typeof v !== "string" || v.trim() === "") bad.push(name + ": " + k);
    }
  }
  assert.strictEqual(bad.length, 0, "empty or non-string: " + bad.join(", "));
});

check("keys are stable ids (letters, digits, dots)", () => {
  const bad = Object.keys(zh).filter(k => !/^[A-Za-z][A-Za-z0-9]*(\.[A-Za-z0-9]+)+$/.test(k));
  assert.strictEqual(bad.length, 0, "bad key names: " + bad.join(", "));
});

check("en.json has no CJK text except the language-switch strings", () => {
  const cjk = /[\u3000-\u303F\u3400-\u4DBF\u4E00-\u9FFF\uFF00-\uFFEF]/;
  const allowed = new Set(["lang.title", "lang.label"]); // they name the other language
  const bad = Object.keys(en).filter(k => !allowed.has(k) && cjk.test(en[k]));
  assert.strictEqual(bad.length, 0, "CJK found in en.json: " + bad.join(", "));
});

// ---------------------------------------------------------------------------
// 4. t() behaviour
// ---------------------------------------------------------------------------
check("t(): current language, then zh-TW, then the key itself", () => {
  I18N.setDictionary("zh-TW", { only_zh: "中文", both: "中", withp: "你好 {name}" });
  I18N.setDictionary("en", { both: "EN", withp: "Hello {name}" });

  assert.strictEqual(I18N.setLang("en"), true);
  assert.strictEqual(I18N.t("both"), "EN");
  assert.strictEqual(I18N.t("only_zh"), "中文", "falls back to zh-TW");
  assert.strictEqual(I18N.t("no.such.key"), "no.such.key", "falls back to the key");

  assert.strictEqual(I18N.setLang("zh-TW"), true);
  assert.strictEqual(I18N.t("both"), "中");
  assert.strictEqual(I18N.t("no.such.key"), "no.such.key");
});

check("t(): {name} parameters are replaced, missing ones stay visible", () => {
  I18N.setLang("en");
  assert.strictEqual(I18N.t("withp", { name: "Ann" }), "Hello Ann");
  assert.strictEqual(I18N.t("withp", { name: 0 }), "Hello 0", "0 is a valid value");
  assert.strictEqual(I18N.t("withp"), "Hello {name}");
  assert.strictEqual(I18N.t("withp", {}), "Hello {name}");
  I18N.setLang("zh-TW");
  assert.strictEqual(I18N.t("withp", { name: "Ann" }), "你好 Ann");
});

check("t(): works before any dictionary is loaded", () => {
  I18N.setDictionary("zh-TW", undefined);
  I18N.setDictionary("en", undefined);
  assert.strictEqual(I18N.t("anything"), "anything");
});

check("setLang rejects unknown codes and keeps the current language", () => {
  I18N.setLang("en");
  assert.strictEqual(I18N.setLang("fr"), false);
  assert.strictEqual(I18N.setLang(undefined), false);
  assert.strictEqual(I18N.getLang(), "en");
});

check("detect(): maps navigator.language to a dictionary, default zh-TW", () => {
  assert.strictEqual(I18N.detect({ language: "en-US" }), "en");
  assert.strictEqual(I18N.detect({ language: "en" }), "en");
  assert.strictEqual(I18N.detect({ language: "zh-TW" }), "zh-TW");
  assert.strictEqual(I18N.detect({ language: "zh-Hant-HK" }), "zh-TW");
  assert.strictEqual(I18N.detect({ language: "fr-FR" }), "zh-TW");
  assert.strictEqual(I18N.detect({ languages: ["fr", "en-GB"], language: "fr" }), "en");
  assert.strictEqual(I18N.detect({}), "zh-TW");
});

check("loadDictionaries() reads the real files in Node and t() uses them", async () => {
  await I18N.loadDictionaries();
  I18N.setLang("en");
  assert.strictEqual(I18N.t("gameover.win"), en["gameover.win"]);
  I18N.setLang("zh-TW");
  assert.strictEqual(I18N.t("gameover.win"), zh["gameover.win"]);
  assert.strictEqual(I18N.t("hud.round", { round: 3, dist: 700, turn: "X" }),
    zh["hud.round"].replace("{round}", "3").replace("{dist}", "700").replace("{turn}", "X"));
  I18N.setLang("en");
  assert.ok(!/\{\w+\}/.test(I18N.t("hud.hp", { hp: 1, max: 2, charges: 3, rounds: 4 })), "no placeholder left over");
});

// ---------------------------------------------------------------------------
// apply(), toggle(), injected loader, alias (task 139)
// ---------------------------------------------------------------------------
function fakeEl(attrs, text) {
  const a = Object.assign({}, attrs);
  return {
    textContent: text === undefined ? "" : text,
    getAttribute: n => (n in a ? a[n] : null),
    setAttribute: (n, v) => { a[n] = String(v); },
    attrs: a
  };
}
function fakeTree(elements) {
  const root = {
    attrs: {},
    documentElement: { attrs: {}, setAttribute(n, v) { this.attrs[n] = v; } },
    querySelectorAll(sel) {
      const name = sel.slice(1, -1); // "[data-i18n]" -> "data-i18n"
      return elements.filter(e => e.getAttribute(name) !== null);
    }
  };
  return root;
}

check("apply(): textContent from data-i18n and attributes from data-i18n-attr", () => {
  I18N.setDictionary("zh-TW", { "a.text": "中文字", "a.title": "中文提示", "a.aria": "中文標籤" });
  I18N.setDictionary("en", { "a.text": "English text", "a.title": "English title", "a.aria": "English label" });
  const e1 = fakeEl({ "data-i18n": "a.text" }, "old");
  const e2 = fakeEl({ "data-i18n-attr": "title:a.title; aria-label:a.aria" });
  const e3 = fakeEl({ "data-i18n": "no.such.key" }, "old");
  const e4 = fakeEl({}, "untouched");
  const tree = fakeTree([e1, e2, e3, e4]);
  I18N.setLang("en");
  assert.strictEqual(I18N.apply(tree), 4);
  assert.strictEqual(e1.textContent, "English text");
  assert.strictEqual(e2.attrs.title, "English title");
  assert.strictEqual(e2.attrs["aria-label"], "English label");
  assert.strictEqual(e3.textContent, "no.such.key", "a missing key shows the key");
  assert.strictEqual(e4.textContent, "untouched");
  assert.strictEqual(tree.documentElement.attrs.lang, "en");
  I18N.setLang("zh-TW");
  I18N.apply(tree);
  assert.strictEqual(e1.textContent, "中文字");
  assert.strictEqual(e2.attrs.title, "中文提示");
  assert.strictEqual(tree.documentElement.attrs.lang, "zh-TW");
});

check("apply() ignores bad input and a malformed data-i18n-attr", () => {
  assert.strictEqual(I18N.apply(null), 0);
  assert.strictEqual(I18N.apply({}), 0);
  const e = fakeEl({ "data-i18n-attr": "nocolon; :nokey; attr:" });
  assert.strictEqual(I18N.apply(fakeTree([e])), 0);
});

check("toggle() flips zh-TW and en and 'zh' is accepted as zh-TW", () => {
  I18N.setLang("zh");
  assert.strictEqual(I18N.getLang(), "zh-TW");
  assert.strictEqual(I18N.toggle(), "en");
  assert.strictEqual(I18N.lang(), "en");
  assert.strictEqual(I18N.toggle(), "zh-TW");
});

check("loadDictionaries(langs, loader) uses the injected loader and no fs or fetch", async () => {
  const asked = [];
  const loader = code => { asked.push(code); return code === "en" ? { k: "E" } : Promise.resolve({ k: "Z" }); };
  await I18N.loadDictionaries(["zh-TW", "en"], loader);
  assert.deepStrictEqual(asked, ["zh-TW", "en"]);
  I18N.setLang("en");
  assert.strictEqual(I18N.t("k"), "E");
  I18N.setLang("zh-TW");
  assert.strictEqual(I18N.t("k"), "Z");
  await assert.rejects(I18N.loadDictionaries(["en"], () => { throw new Error("no network"); }));
});

check("deterministic: the same inputs give the same output over 300 calls", () => {
  I18N.setDictionary("zh-TW", { p: "第 {n} 回合" });
  I18N.setDictionary("en", { p: "Round {n}" });
  I18N.setLang("en");
  const first = [];
  for (let i = 0; i < 300; i++) first.push(I18N.t("p", { n: i }));
  const second = [];
  for (let i = 0; i < 300; i++) second.push(I18N.t("p", { n: i }));
  assert.deepStrictEqual(first, second);
  assert.strictEqual(first[299], "Round 299");
});

check("browser load: the file defines the globals I18N and I18n (same object) and does not touch the DOM", () => {
  const vm = require("vm");
  const ctx = { navigator: { language: "en-US" } };
  vm.createContext(ctx);
  vm.runInContext(fs.readFileSync(path.join(ROOT, "js", "i18n.js"), "utf8"), ctx);
  assert.ok(ctx.I18N && typeof ctx.I18N.t === "function");
  assert.strictEqual(ctx.I18n, ctx.I18N);
});

// ---------------------------------------------------------------------------
// 7. localStorage failures
// ---------------------------------------------------------------------------
function withStorage(descriptor, fn) {
  const saved = Object.getOwnPropertyDescriptor(globalThis, "localStorage");
  Object.defineProperty(globalThis, "localStorage", Object.assign({ configurable: true }, descriptor));
  try {
    fn();
  } finally {
    if (saved) Object.defineProperty(globalThis, "localStorage", saved);
    else delete globalThis.localStorage;
  }
}

check("setLang survives localStorage.setItem/getItem throwing", () => {
  const boom = () => { throw new Error("QuotaExceededError"); };
  withStorage({ value: { getItem: boom, setItem: boom }, writable: true }, () => {
    assert.strictEqual(I18N.setLang("en"), true);
    assert.strictEqual(I18N.getLang(), "en");
    assert.doesNotThrow(() => I18N.init());
  });
});

check("setLang survives the localStorage property itself throwing (blocked storage)", () => {
  withStorage({ get() { throw new Error("SecurityError"); } }, () => {
    assert.strictEqual(I18N.setLang("zh-TW"), true);
    assert.strictEqual(I18N.getLang(), "zh-TW");
    assert.doesNotThrow(() => I18N.init());
  });
});

check("init(fallback): saved choice first, then the fallback, then the browser language", () => {
  const mem = {};
  const fake = { getItem: k => (k in mem ? mem[k] : null), setItem: (k, v) => { mem[k] = String(v); } };
  const savedNav = Object.getOwnPropertyDescriptor(globalThis, "navigator");
  Object.defineProperty(globalThis, "navigator", { value: { language: "en-US" }, configurable: true });
  try {
    withStorage({ value: fake, writable: true }, () => {
      assert.strictEqual(I18N.init("zh-TW"), "zh-TW", "nothing saved: the fallback wins over an English browser");
      assert.strictEqual(I18N.init(), "en", "no fallback: the browser language");
      mem[I18N.STORAGE_KEY] = "en";
      assert.strictEqual(I18N.init("zh-TW"), "en", "a saved choice wins over the fallback");
    });
  } finally {
    if (savedNav) Object.defineProperty(globalThis, "navigator", savedNav);
    else delete globalThis.navigator;
  }
});

check("setLang survives a missing localStorage", () => {
  withStorage({ value: undefined, writable: true }, () => {
    assert.strictEqual(I18N.setLang("en"), true);
    assert.strictEqual(I18N.getLang(), "en");
  });
});

check("the choice is saved by setLang and restored by init()", () => {
  const mem = {};
  const fake = { getItem: k => (k in mem ? mem[k] : null), setItem: (k, v) => { mem[k] = String(v); } };
  withStorage({ value: fake, writable: true }, () => {
    I18N.setLang("zh-TW");
    I18N.setLang("en");
    assert.strictEqual(mem[I18N.STORAGE_KEY], "en");
    I18N.setLang("zh-TW"); // simulate a reload: the module state is reset by init()
    I18N.setLang("en");
    assert.strictEqual(I18N.init(), "en");
    mem[I18N.STORAGE_KEY] = "zh-TW";
    assert.strictEqual(I18N.init(), "zh-TW");
    mem[I18N.STORAGE_KEY] = "garbage";
    assert.doesNotThrow(() => I18N.init());
  });
});

// ---------------------------------------------------------------------------
// 5-6. index.html scan
// ---------------------------------------------------------------------------
const indexSrc = fs.readFileSync(path.join(ROOT, "index.html"), "utf8");
const CJK = /[\u2E80-\u2FDF\u3000-\u303F\u3040-\u30FF\u3100-\u312F\u31C0-\u32FF\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\uFE30-\uFE4F\uFF00-\uFFEF]/;

// Remove comments line by line: /* ... */ (also multi-line), <!-- ... -->, and // to end of line
// ("//" right after ":" is a URL scheme, not a comment).
function codeWithoutComments(src) {
  const out = [];
  let closer = null; // "*/" or "-->" while inside a block comment
  src.split("\n").forEach((line, i) => {
    let kept = "";
    let pos = 0;
    while (pos < line.length) {
      if (closer) {
        const end = line.indexOf(closer, pos);
        if (end < 0) { pos = line.length; break; }
        pos = end + closer.length;
        closer = null;
        continue;
      }
      const candidates = [];
      const a = line.indexOf("/*", pos); if (a >= 0) candidates.push([a, "*/", 2]);
      const b = line.indexOf("<!--", pos); if (b >= 0) candidates.push([b, "-->", 4]);
      let c = line.indexOf("//", pos);
      while (c > 0 && line[c - 1] === ":") c = line.indexOf("//", c + 2);
      if (c >= 0) candidates.push([c, null, 2]);
      if (!candidates.length) { kept += line.slice(pos); break; }
      candidates.sort((x, y) => x[0] - y[0]);
      const [at, close, len] = candidates[0];
      kept += line.slice(pos, at);
      if (close === null) break; // line comment: drop the rest
      closer = close;
      pos = at + len;
    }
    out.push({ n: i + 1, text: kept });
  });
  return out;
}

pageCheck("index.html has no CJK characters outside comments", () => {
  const offenders = codeWithoutComments(indexSrc).filter(l => CJK.test(l.text));
  assert.strictEqual(offenders.length, 0,
    "CJK left in index.html (move it into assets/i18n/*.json):\n" +
    offenders.map(l => "  line " + l.n + ": " + l.text.trim()).join("\n"));
});

pageCheck("index.html loads js/i18n.js before the game script", () => {
  const lib = indexSrc.indexOf('src="js/i18n.js"');
  const game = indexSrc.indexOf("<script>");
  assert.ok(lib >= 0, 'missing <script src="js/i18n.js">');
  assert.ok(lib < game, "js/i18n.js must come before the inline game script");
});

const NAMESPACES = new Set(Object.keys(zh).map(k => k.split(".")[0]));

// A key may stand alone in quotes ("hud.round") or follow "attr:" / sit between ";" in a data-i18n-attr value ("title:dock.angle;aria-label:dock.power").
pageCheck("every translation key used in index.html exists in both dictionaries", () => {
  const keyLike = /["'`:;]([a-z]+(?:\.[A-Za-z0-9]+)+)["'`;]/g;
  const used = new Set();
  let m;
  while ((m = keyLike.exec(indexSrc)) !== null) {
    if (NAMESPACES.has(m[1].split(".")[0])) used.add(m[1]);
  }
  assert.ok(used.size > 0, "found no keys in index.html: is the scan broken?");
  const missing = Array.from(used).filter(k => !(k in zh) || !(k in en));
  assert.strictEqual(missing.length, 0, "keys used but not defined: " + missing.join(", "));
});

pageCheck("every key in the dictionaries is used in index.html", () => {
  const unused = Object.keys(zh).filter(k =>
    !new RegExp("[\"'`:;]" + k.replace(/\./g, "\\.") + "[\"'`;]").test(indexSrc));
  assert.strictEqual(unused.length, 0, "keys never referenced: " + unused.join(", "));
});

// ---------------------------------------------------------------------------
(async () => {
  let passed = 0;
  const failed = [];
  for (const [name, fn] of tests) {
    try {
      await fn();
      passed++;
      console.log("ok   - " + name);
    } catch (err) {
      failed.push(name);
      console.log("FAIL - " + name + "\n       " + String(err.message).split("\n").join("\n       "));
    }
  }
  console.log("\n" + passed + " passed, " + failed.length + " failed (" + Object.keys(zh).length + " keys per language)");
  process.exit(failed.length ? 1 : 0);
})();
