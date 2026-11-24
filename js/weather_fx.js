/*
 * Deterministic canvas weather field. It is cosmetic only: match weather comes
 * from js/weather.js and supplies the id and shared seed.
 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) {
    module.exports = api;
  } else {
    root.WeatherFx = api;
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var DEFAULT_WIDTH = 1920;
  var DEFAULT_HEIGHT = 1080;
  var MAX_ITEMS_HIGH = 220;
  var MAX_ITEMS_LOW = 60;
  var LOW_RATIO = 0.25;
  var MAX_DT = 0.1;
  var TAU = Math.PI * 2;
  var COUNTS = { clear: 0, rain: 160, snow: 120, storm: 220, fog: 16 };

  function isNum(value) { return typeof value === 'number' && isFinite(value); }
  function clamp(value, low, high) { return value < low ? low : value > high ? high : value; }
  function posNum(value, fallback) { return isNum(value) && value > 0 ? value : fallback; }
  function wrap(value, size) {
    var out = value - Math.floor(value / size) * size;
    return out >= size || out < 0 ? 0 : out;
  }
  function seedToInt(value) { return isNum(value) ? Math.floor(value) | 0 : 1; }
  function cleanId(value) { return Object.prototype.hasOwnProperty.call(COUNTS, value) ? value : 'clear'; }
  function windUnit(wind) { return isNum(wind) ? clamp(wind / 4, -1, 1) : 0; }

  function mulberry32(seed) {
    var a = seed | 0;
    return function () {
      a = (a + 0x6d2b79f5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function itemCount(id, quality) {
    var base = COUNTS[id];
    if (quality === 'low') return Math.min(MAX_ITEMS_LOW, Math.floor(base * LOW_RATIO));
    return Math.min(MAX_ITEMS_HIGH, base);
  }

  function makeItems(rand, id, count, width, height) {
    var out = [];
    for (var i = 0; i < count; i++) {
      var item = {
        kind: id, x: rand() * width, y: rand() * height,
        phase: rand() * TAU, speed: 0, size: 0, alpha: 0, lean: 0
      };
      if (id === 'rain' || id === 'storm') {
        item.speed = id === 'storm' ? 580 + rand() * 260 : 360 + rand() * 180;
        item.size = id === 'storm' ? 16 + rand() * 14 : 11 + rand() * 12;
        item.alpha = id === 'storm' ? 0.35 + rand() * 0.25 : 0.25 + rand() * 0.22;
      } else if (id === 'snow') {
        item.speed = 16 + rand() * 22;
        item.size = 1.5 + rand() * 3.5;
        item.alpha = 0.5 + rand() * 0.35;
      } else if (id === 'fog') {
        item.speed = 8 + rand() * 12;
        item.size = 120 + rand() * 120;
        item.alpha = 0.07 + rand() * 0.07;
        item.y = height * (0.2 + 0.6 * rand());
      }
      out.push(item);
    }
    return out;
  }

  // Build a finite schedule at creation time. Update only consumes it, so
  // lightning timing cannot diverge because of a late frame or random draw.
  function makeLightningSchedule(rand) {
    var times = [];
    var at = 4 + rand() * 3;
    for (var i = 0; i < 180; i++) {
      times.push(at);
      at += 4 + rand() * 3;
    }
    return times;
  }

  function create(options) {
    var cfg = options && typeof options === 'object' ? options : {};
    var width = posNum(cfg.w, DEFAULT_WIDTH);
    var height = posNum(cfg.h, DEFAULT_HEIGHT);
    var id = cleanId(cfg.id);
    var quality = cfg.quality === 'low' ? 'low' : 'high';
    var rand = mulberry32(seedToInt(cfg.seed));
    var items = makeItems(rand, id, itemCount(id, quality), width, height);
    var lightning = id === 'storm' && quality === 'high' ? makeLightningSchedule(rand) : [];
    var time = 0;
    var nextLightning = 0;
    var flashUntil = -1;
    var currentWind = 0;

    function update(dt, wind) {
      if (!isNum(dt) || dt <= 0) return;
      var step = Math.min(dt, MAX_DT);
      currentWind = windUnit(wind);
      time += step;
      for (var i = 0; i < items.length; i++) {
        var item = items[i];
        if (id === 'rain' || id === 'storm') {
          item.lean = currentWind * (id === 'storm' ? 28 : 18);
          item.x = wrap(item.x + currentWind * (id === 'storm' ? 180 : 110) * step, width);
          item.y = wrap(item.y + item.speed * step, height);
        } else if (id === 'snow') {
          item.x = wrap(item.x + (currentWind * 30 + Math.sin(time * 1.4 + item.phase) * 12) * step, width);
          item.y = wrap(item.y + item.speed * step, height);
        } else if (id === 'fog') {
          item.x = wrap(item.x + (currentWind * 34 + item.speed) * step, width);
          item.y = clamp(item.y + Math.sin(time * 0.24 + item.phase) * 5 * step, 0, height - 1);
        }
      }
      if (nextLightning < lightning.length && time >= lightning[nextLightning]) {
        flashUntil = time + 0.15;
        nextLightning++;
      }
    }

    function draw(ctx) {
      if (!ctx) return;
      ctx.save();
      if (id === 'rain' || id === 'storm') {
        ctx.strokeStyle = id === 'storm' ? '#c9d9ff' : '#b8d7ff';
        for (var i = 0; i < items.length; i++) {
          var rain = items[i];
          ctx.globalAlpha = rain.alpha;
          ctx.lineWidth = id === 'storm' ? 1.5 : 1;
          ctx.beginPath();
          ctx.moveTo(rain.x, rain.y);
          ctx.lineTo(clamp(rain.x - rain.lean, 0, width), clamp(rain.y - rain.size, 0, height));
          ctx.stroke();
        }
      } else if (id === 'snow') {
        ctx.fillStyle = '#f5f8ff';
        for (var j = 0; j < items.length; j++) {
          var snow = items[j];
          ctx.globalAlpha = snow.alpha;
          ctx.beginPath();
          ctx.arc(snow.x, snow.y, snow.size, 0, TAU);
          ctx.fill();
        }
      } else if (id === 'fog') {
        ctx.fillStyle = '#d7dff0';
        for (var k = 0; k < items.length; k++) {
          var fog = items[k];
          ctx.globalAlpha = fog.alpha;
          ctx.beginPath();
          ctx.ellipse(fog.x, fog.y, fog.size, Math.max(20, fog.size * 0.14), 0, 0, TAU);
          ctx.fill();
        }
      }
      if (time < flashUntil) {
        ctx.globalAlpha = 0.35;
        ctx.fillStyle = '#fff3b0';
        ctx.fillRect(0, 0, width, height);
      }
      ctx.restore();
    }

    function state() {
      return items.map(function (item) {
        return {
          kind: item.kind, x: item.x, y: item.y, size: item.size,
          lean: item.lean, alpha: item.alpha
        };
      });
    }

    return {
      update: update,
      draw: draw,
      items: state,
      width: width,
      height: height,
      id: id,
      quality: quality,
      count: items.length
    };
  }

  return {
    create: create,
    MAX_ITEMS_HIGH: MAX_ITEMS_HIGH,
    MAX_ITEMS_LOW: MAX_ITEMS_LOW,
    LOW_RATIO: LOW_RATIO,
    COUNTS: COUNTS
  };
});
