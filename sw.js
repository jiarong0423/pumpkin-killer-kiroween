try { importScripts("js/webp_manifest.js"); } catch (e) { /* no manifest: pictures stay PNG */ }
const WEBP_SET = new Set(self.PK_WEBP || []);
// A PNG whose smaller .webp sibling exists is fetched as the .webp (same content, about 90 percent fewer bytes) and cached under the PNG address, so the page code and the CSS keep their PNG paths.
function webpUrlFor(requestUrl) {
  const u = new URL(requestUrl, self.location.href);
  const rel = u.pathname.replace(/^\//, "");
  return WEBP_SET.has(rel) ? u.origin + "/" + rel.replace(/\.png$/, ".webp") : null;
}
function fetchPreferWebp(request) {
  const alt = webpUrlFor(request.url);
  const accepts = (request.headers && request.headers.get("accept") || "").indexOf("image/webp") >= 0 || request.destination === "image";
  if (!alt || !accepts) return fetch(request);
  return fetch(alt).then((response) => (response.ok ? response : fetch(request))).catch(() => fetch(request));
}
const CACHE_NAME = "pk-8be6619e2a";
const PRECACHE_URLS = [
// PWA-PRECACHE-BEGIN
  "index.html",
  "css/dock.css",
  "css/dock_art.css",
  "css/dock_stage.css",
  "css/fonts.css",
  "css/room_phone.css",
  "js/adaptive_level.js",
  "js/ai_levels_page.js",
  "js/ambient_sfx.js",
  "js/audio.js",
  "js/boomerang.js",
  "js/class_stats.js",
  "js/comeback.js",
  "js/determinism.js",
  "js/electric_stun.js",
  "js/element_fx.js",
  "js/flight.js",
  "js/hallucination.js",
  "js/hit_masks.js",
  "js/hit_report.js",
  "js/i18n.js",
  "js/knight_ult.js",
  "js/knockback.js",
  "js/lobby_model.js",
  "js/nun_ult.js",
  "js/particles.js",
  "js/particles_draw.js",
  "js/perspective.js",
  "js/qr_code.js",
  "js/round_hash.js",
  "js/scene_layers.js",
  "js/smart_candidates.js",
  "js/sound_wave.js",
  "js/team_battle.js",
  "js/team_tuning.js",
  "js/ultimate.js",
  "js/ultimate_fx.js",
  "js/weather.js",
  "js/weather_fx.js",
  "js/webp_manifest.js",
  "js/wind_fx.js",
  "shared/ai_models.json",
  "shared/ai_prompts.json",
  "shared/comeback.json",
  "shared/comeback_vectors.json",
  "shared/constants.json",
  "shared/determinism_golden.json",
  "shared/flight_golden.json",
  "shared/heroes.json",
  "shared/hit_masks.json",
  "shared/hit_report_vectors.json",
  "shared/orientation_frozen.json",
  "shared/round_hash_golden.json",
  "shared/size_frozen.json",
  "shared/team_tuning.json",
  "shared/team_tuning_vectors.json",
  "shared/weather_golden.json",
  "assets/fonts/pk-body-400.woff2",
  "assets/fonts/pk-body-700.woff2",
  "assets/fonts/pk-display-cjk-900.woff2",
  "assets/i18n/en.json",
  "assets/i18n/zh-TW.json",
  "relay-config.js",
  "assets/env/bg_graveyard.webp",
  "assets/ui/ui_top_banner_left.webp",
  "assets/ui/ui_top_banner_centre.webp",
  "assets/ui/ui_top_banner_right.webp",
  "assets/fx/sprites/fx_ghost_idle.webp",
  "assets/env/ghost_lantern.webp",
  "assets/ui/top_plate_left.webp",
  "assets/ui/top_plate_right.webp",
  "assets/units/unit_skeleton.webp",
  "assets/units/unit_wizard.webp",
  "assets/units/unit_bat.webp",
  "assets/units/unit_knight.webp",
  "assets/poses/bride_idle1.webp",
  "assets/poses/hunchback_idle1.webp",
  "assets/poses/necro_idle.webp",
  "assets/units/unit_skeleton_unarmed.webp",
  "assets/units/unit_bat_unarmed.webp",
  "assets/units/unit_knight_unarmed.webp",
  "assets/units/unit_hag_idle.webp",
  "assets/poses/hunchback_unarmed.webp",
// PWA-PRECACHE-END
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => Promise.all(PRECACHE_URLS.map((url) => {
        const request = new Request(url);
        return fetchPreferWebp(request).then((response) => { if (!response.ok) throw new Error("precache " + url + " " + response.status); return cache.put(request, response); });
      })))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(
        keys
          .filter((key) => key.startsWith("pk-") && key !== CACHE_NAME)
          .map((key) => caches.delete(key))
      ))
      .then(() => self.clients.claim())
  );
});

function isHtmlRequest(request, url) {
  return request.mode === "navigate" || url.pathname === "/" || url.pathname.endsWith(".html");
}

function cacheFirst(request) {
  return caches.match(request).then((cached) => {
    if (cached) return cached;
    return fetchPreferWebp(request).then((response) => {
      if (response.ok) {
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
      }
      return response;
    });
  });
}

// Text files (the page, scripts, styles, language files) go to the network first so a new build never shows old strings or old rules (2026-11-17: a phone showed raw language keys from a cached language file); pictures and sounds stay cache first, which is what makes the second load fast (0 KB transferred, 0.4 s).
function networkFirst(request) {
  return fetch(request)
    .then((response) => {
      if (response.ok) {
        const copy = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
      }
      return response;
    })
    .catch(() => caches.match(request));
}

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  event.respondWith(
    (isHtmlRequest(request, url) || url.pathname === "/relay-config.js" || /\.(?:json|js|css)$/.test(url.pathname)) ? networkFirst(request) : cacheFirst(request)
  );
});
