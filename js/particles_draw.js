/*
 * Pumpkin Killer - particle drawing.
 *
 * Uses only the 2D canvas API on the ctx you pass in. No DOM access.
 * Works in Node (module.exports, for tests with a stub ctx) and in the
 * browser (globals `ParticlesDraw` and `drawParticles`).
 *
 * Passes, in order:
 *   layer 0 (BODY)  normal blending: smoke, dust, debris, drops
 *   layer 1 (GLOW)  additive blending ('lighter'): fire, sparks, rings, wisps
 *   layer 2 (TEXT)  normal blending: damage numbers
 *
 * Per particle, with t = 1 - life / maxLife (0 at birth, 1 at death):
 *   size   = lerp(size, sizeEnd, t)  (rings use an ease-out t)
 *   colour = lerp(color, colorEnd, t)
 *   alpha  = alpha * min(1, (1 - t) / fade)
 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) {
    module.exports = api;
  } else {
    root.ParticlesDraw = api;
    root.drawParticles = api.drawParticles;
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var TAU = Math.PI * 2;
  var MIN_ALPHA = 0.004;
  var colorCache = Object.create(null);
  var colorCacheSize = 0;

  function clamp01(v) {
    return v < 0 ? 0 : v > 1 ? 1 : v;
  }

  // '#rrggbb' -> [r, g, b]. Anything else gives white.
  function parseHex(c) {
    var hit = colorCache[c];
    if (hit) {
      return hit;
    }
    var m = typeof c === 'string' ? /^#([0-9a-fA-F]{6})$/.exec(c) : null;
    var rgb = m
      ? [parseInt(m[1].slice(0, 2), 16), parseInt(m[1].slice(2, 4), 16), parseInt(m[1].slice(4, 6), 16)]
      : [255, 255, 255];
    if (colorCacheSize >= 256) {
      colorCache = Object.create(null);
      colorCacheSize = 0;
    }
    colorCache[c] = rgb;
    colorCacheSize++;
    return rgb;
  }

  // Linear blend of two '#rrggbb' colours, t clamped to 0..1. Returns [r, g, b].
  function lerpRgb(a, b, t) {
    var ca = parseHex(a);
    var cb = parseHex(b);
    var k = clamp01(t);
    return [
      ca[0] + (cb[0] - ca[0]) * k,
      ca[1] + (cb[1] - ca[1]) * k,
      ca[2] + (cb[2] - ca[2]) * k
    ];
  }

  function rgbString(rgb) {
    return 'rgb(' + Math.round(rgb[0]) + ',' + Math.round(rgb[1]) + ',' + Math.round(rgb[2]) + ')';
  }

  function rgbaString(rgb, a) {
    return 'rgba(' + Math.round(rgb[0]) + ',' + Math.round(rgb[1]) + ',' + Math.round(rgb[2]) + ',' + a + ')';
  }

  var sprites = {};   // name -> drawable image, supplied by the game with setSprites()
  var tintCache = Object.create(null);
  var tintCacheCount = 0;

  function setSprites(map) {
    sprites = map && typeof map === 'object' ? map : {};
  }

  function quantizeChannel(v) {
    var q = Math.round(v / 16) * 16;
    return q < 0 ? 0 : q > 255 ? 255 : q;
  }

  // Returns a color-tinted offscreen canvas for white/alpha FX masks while
  // leaving pure white (#ffffff) or headless Node images untouched.
  function tintedSprite(img, name, rgb) {
    var r = quantizeChannel(rgb[0]);
    var g = quantizeChannel(rgb[1]);
    var b = quantizeChannel(rgb[2]);
    if (r >= 254 && g >= 254 && b >= 254) {
      return img;
    }
    if (typeof document === 'undefined' || typeof document.createElement !== 'function') {
      return img;
    }
    var key = (name || '') + '|' + r + ',' + g + ',' + b;
    if (Object.prototype.hasOwnProperty.call(tintCache, key)) {
      return tintCache[key];
    }
    var canvas = document.createElement('canvas');
    var w = Math.min(256, img.naturalWidth || img.width || 256);
    var h = Math.min(256, img.naturalHeight || img.height || 256);
    canvas.width = w > 0 ? w : 256;
    canvas.height = h > 0 ? h : 256;
    try {
      var cctx = canvas.getContext('2d');
      if (!cctx) {
        return img;
      }
      cctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      cctx.globalCompositeOperation = 'source-in';
      cctx.fillStyle = 'rgb(' + r + ',' + g + ',' + b + ')';
      cctx.fillRect(0, 0, canvas.width, canvas.height);
    } catch (e) {
      return img;
    }
    if (tintCacheCount >= 128) {
      tintCache = Object.create(null);
      tintCacheCount = 0;
    }
    tintCache[key] = canvas;
    tintCacheCount++;
    return canvas;
  }

  function layerOf(p) {
    return p.layer === 1 || p.layer === 2 ? p.layer : 0;
  }

  function drawOne(ctx, p) {
    var t = p.maxLife > 0 ? clamp01(1 - p.life / p.maxLife) : 1;
    var fade = p.fade > 0 ? Math.min(1, (1 - t) / p.fade) : 1;
    var alpha = p.alpha * fade;
    if (!(alpha > MIN_ALPHA)) {
      return;
    }
    var shape = p.shape;
    var te = shape === 'ring' ? 1 - (1 - t) * (1 - t) : t;
    var size = p.size + (p.sizeEnd - p.size) * te;
    if (!(size > 0)) {
      return;
    }
    var rgb = lerpRgb(p.color, p.colorEnd, t);
    ctx.globalAlpha = alpha > 1 ? 1 : alpha;

    if (shape === 'glow') {
      var grad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, size);
      grad.addColorStop(0, rgbaString(rgb, 1));
      grad.addColorStop(0.45, rgbaString(rgb, 0.55));
      grad.addColorStop(1, rgbaString(rgb, 0));
      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(p.x, p.y, size, 0, TAU);
      ctx.fill();
    } else if (shape === 'square') {
      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate(p.angle);
      ctx.fillStyle = rgbString(rgb);
      ctx.fillRect(-size, -size, size * 2, size * 2);
      ctx.restore();
    } else if (shape === 'streak') {
      var speed = Math.sqrt(p.vx * p.vx + p.vy * p.vy);
      var ang = speed > 1e-3 ? Math.atan2(p.vy, p.vx) : p.angle;
      ctx.strokeStyle = rgbString(rgb);
      ctx.lineWidth = p.lineWidth > 0 ? p.lineWidth : Math.max(1.2, size * 0.12);
      ctx.lineCap = 'round';
      ctx.beginPath();
      ctx.moveTo(p.x, p.y);
      ctx.lineTo(p.x - Math.cos(ang) * size, p.y - Math.sin(ang) * size);
      ctx.stroke();
    } else if (shape === 'ring') {
      ctx.strokeStyle = rgbString(rgb);
      ctx.lineWidth = p.lineWidth > 0 ? Math.max(0.5, p.lineWidth * (1 - 0.6 * t)) : Math.max(1, size * 0.06);
      ctx.beginPath();
      ctx.arc(p.x, p.y, size, 0, TAU);
      ctx.stroke();
    } else if (shape === 'sprite') {
      var img = sprites[p.sprite];
      if (!img || img.complete === false || img.naturalWidth === 0) {
        return;
      }
      var sx = typeof p.scaleX === 'number' && isFinite(p.scaleX) && p.scaleX !== 0 ? p.scaleX : 1;
      var sy = typeof p.scaleY === 'number' && isFinite(p.scaleY) && p.scaleY !== 0 ? p.scaleY : 1;
      var src = tintedSprite(img, p.sprite, rgb);
      ctx.save();
      ctx.translate(p.x, p.y);
      if (sx !== 1 || sy !== 1) {
        ctx.scale(sx, sy);
      }
      ctx.rotate(p.angle);
      ctx.drawImage(src, -size, -size, size * 2, size * 2);
      ctx.restore();
    } else if (shape === 'text') {
      if (typeof p.text !== 'string' || p.text === '') {
        return;
      }
      ctx.font = 'bold ' + Math.round(size) + 'px "Trebuchet MS", sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.lineJoin = 'round';
      ctx.lineWidth = Math.max(2, size * 0.2);
      ctx.strokeStyle = 'rgba(20,10,30,0.9)';
      ctx.strokeText(p.text, p.x, p.y);
      ctx.fillStyle = rgbString(rgb);
      ctx.fillText(p.text, p.x, p.y);
    } else {
      ctx.fillStyle = rgbString(rgb);
      ctx.beginPath();
      ctx.arc(p.x, p.y, size, 0, TAU);
      ctx.fill();
    }
  }

  // Draw every particle. Saves and restores the ctx state around the call.
  function drawParticles(ctx, particles) {
    if (!ctx || !particles || particles.length === 0) {
      return;
    }
    ctx.save();
    for (var layer = 0; layer <= 2; layer++) {
      ctx.globalCompositeOperation = layer === 1 ? 'lighter' : 'source-over';
      for (var i = 0; i < particles.length; i++) {
        var p = particles[i];
        if (layerOf(p) === layer) {
          drawOne(ctx, p);
        }
      }
    }
    ctx.restore();
  }

  return {
    drawParticles: drawParticles,
    setSprites: setSprites,
    lerpRgb: lerpRgb,
    parseHex: parseHex
  };
});
