/*
 * Pumpkin Killer i18n core. DOM-free.
 * Browser: global `I18N`. Node: `module.exports`.
 *
 *   I18N.loadDictionaries().then(() => { I18N.init(); ... });
 *   I18N.t("hud.round", { round: 3, dist: 800, turn: "..." });
 */
(function (root, factory) {
  var api = factory(root);
  if (typeof module === "object" && module.exports) module.exports = api;
  else { root.I18N = api; root.I18n = api; }   // I18n is an alias, same object
})(typeof globalThis !== "undefined" ? globalThis : this, function (root) {
  "use strict";

  var DEFAULT_LANG = "zh-TW";
  var SUPPORTED = ["zh-TW", "en"];
  var STORAGE_KEY = "pumpkinKiller.lang";

  var dictionaries = {};
  var current = DEFAULT_LANG;

  // Map any BCP-47 tag to a supported dictionary code, or null.
  function normalize(code) {
    if (typeof code !== "string") return null;
    var c = code.trim().toLowerCase();
    if (c === "en" || c.indexOf("en-") === 0 || c.indexOf("en_") === 0) return "en";
    if (c === "zh" || c.indexOf("zh-") === 0 || c.indexOf("zh_") === 0) return "zh-TW";
    return null;
  }

  // localStorage can be missing, blocked, or throw on access (private mode, sandboxed iframes).
  function storage() {
    try {
      return root.localStorage || null;
    } catch (e) {
      return null;
    }
  }

  function readSaved() {
    try {
      var s = storage();
      return s ? normalize(s.getItem(STORAGE_KEY)) : null;
    } catch (e) {
      return null;
    }
  }

  function writeSaved(code) {
    try {
      var s = storage();
      if (s) s.setItem(STORAGE_KEY, code);
      return !!s;
    } catch (e) {
      return false;
    }
  }

  // Language from the browser. `nav` is injectable for tests.
  function detect(nav) {
    var n = nav || (typeof root.navigator !== "undefined" ? root.navigator : null);
    if (!n) return DEFAULT_LANG;
    var list = [];
    if (n.languages && n.languages.length) list = Array.prototype.slice.call(n.languages);
    if (n.language) list.push(n.language);
    for (var i = 0; i < list.length; i++) {
      var code = normalize(list[i]);
      if (code) return code;
    }
    return DEFAULT_LANG;
  }

  function setLang(code) {
    var c = normalize(code);
    if (!c) return false;
    current = c;
    writeSaved(c); // a failed save never breaks the switch
    return true;
  }

  function getLang() {
    return current;
  }

  // Start-up: saved choice first, then browser language. Does not write storage.
  // `fallback` (optional, e.g. "zh-TW") replaces the browser-language guess, so the page can keep Chinese as the default.
  function init(fallback) {
    current = readSaved() || normalize(fallback) || detect();
    return current;
  }

  function interpolate(text, params) {
    if (!params) return text;
    return text.replace(/\{(\w+)\}/g, function (m, name) {
      return Object.prototype.hasOwnProperty.call(params, name) ? String(params[name]) : m;
    });
  }

  // Lookup order: current language, then zh-TW, then the key itself.
  function t(key, params) {
    var cur = dictionaries[current];
    var base = dictionaries[DEFAULT_LANG];
    var text;
    if (cur && typeof cur[key] === "string") text = cur[key];
    else if (base && typeof base[key] === "string") text = base[key];
    else return key;
    return interpolate(text, params);
  }

  function setDictionary(code, map) {
    dictionaries[code] = map;
  }

  // Flip between the two languages (the language-switch button). Returns the new code.
  function toggle() {
    setLang(current === "en" ? "zh-TW" : "en");
    return current;
  }

  // "title:key; aria-label:key2" -> [["title","key"],["aria-label","key2"]]
  function parseAttrSpec(spec) {
    var out = [];
    String(spec || "").split(";").forEach(function (part) {
      var i = part.indexOf(":");
      if (i > 0) {
        var attr = part.slice(0, i).trim(), key = part.slice(i + 1).trim();
        if (attr && key) out.push([attr, key]);
      }
    });
    return out;
  }

  // Fill a DOM tree (or any object with querySelectorAll): the textContent of every [data-i18n] element and
  // the attributes named in [data-i18n-attr]. Returns the number of writes. No DOM access happens at load time.
  function apply(rootEl) {
    if (!rootEl || typeof rootEl.querySelectorAll !== "function") return 0;
    var count = 0;
    Array.prototype.slice.call(rootEl.querySelectorAll("[data-i18n]")).forEach(function (node) {
      var key = node.getAttribute("data-i18n");
      if (key) { node.textContent = t(key); count++; }
    });
    Array.prototype.slice.call(rootEl.querySelectorAll("[data-i18n-attr]")).forEach(function (node) {
      parseAttrSpec(node.getAttribute("data-i18n-attr")).forEach(function (pair) {
        node.setAttribute(pair[0], t(pair[1]));
        count++;
      });
    });
    var de = rootEl.documentElement;
    if (de && typeof de.setAttribute === "function") de.setAttribute("lang", current);
    return count;
  }

  function isNode() {
    return typeof process !== "undefined" && !!(process.versions && process.versions.node) &&
      typeof root.document === "undefined";
  }

  // Browser: fetch("assets/i18n/<code>.json") relative to the page. Node: read the same files with fs.
  // `loader(code)` (optional) returns the dictionary object or a promise of it; with it neither fs nor fetch is used.
  function loadDictionaries(langs, loader) {
    var codes = langs || SUPPORTED;
    var loads = codes.map(function (code) {
      if (typeof loader === "function") {
        return new Promise(function (resolve) { resolve(loader(code)); }).then(function (map) {   // a throwing loader becomes a rejection
          dictionaries[code] = map;
          return code;
        });
      }
      if (isNode()) {
        return new Promise(function (resolve, reject) {
          try {
            var fs = require("fs");
            var path = require("path");
            var file = path.join(__dirname, "..", "assets", "i18n", code + ".json");
            dictionaries[code] = JSON.parse(fs.readFileSync(file, "utf8"));
            resolve(code);
          } catch (e) {
            reject(e);
          }
        });
      }
      return fetch("assets/i18n/" + code + ".json").then(function (res) {
        if (!res.ok) throw new Error("i18n: " + code + ".json -> HTTP " + res.status);
        return res.json();
      }).then(function (map) {
        dictionaries[code] = map;
        return code;
      });
    });
    return Promise.all(loads).then(function () { return dictionaries; });
  }

  return {
    DEFAULT_LANG: DEFAULT_LANG,
    SUPPORTED: SUPPORTED,
    STORAGE_KEY: STORAGE_KEY,
    t: t,
    setLang: setLang,
    getLang: getLang,
    lang: getLang,
    toggle: toggle,
    apply: apply,
    detect: detect,
    init: init,
    setDictionary: setDictionary,
    loadDictionaries: loadDictionaries
  };
});
