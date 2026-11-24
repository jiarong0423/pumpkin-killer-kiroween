/*
 * Hero-specific normal-attack effects.
 *
 * Declarative, deterministic data for index.html. This module owns neither
 * particles nor canvas state; callers pass its entries to fxEmit.
 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) {
    module.exports = api;
  } else {
    root.ElementFx = api;
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var UNKNOWN = {
    id: 'unknown', heroIds: [], colours: ['#f5f5f5', '#a3a3a3', '#404040'],
    trailPreset: 'weapon_enchant_stardust', launchPresets: [], impactPresets: [],
    statusIcon: 'none', soundEvent: 'impact_unit', screenShake: 0
  };

  // Colour triplets are used by the page for rings and status accents.
  var ELEMENTS = [
    { id: 'frost', heroIds: ['skeleton'], colours: ['#ffffff', '#9fd8ff', '#3b6fe0'], trailPreset: 'trail_frost', launchPresets: ['weapon_charge_aura'], impactPresets: ['frost_shatter', 'hit_sparks'], statusIcon: 'ui_frost_curse', soundEvent: 'throw_spear', screenShake: 0.08 },
    { id: 'poison', heroIds: ['wizard'], colours: ['#9dff7a', '#3fbf3f', '#c2410c'], trailPreset: 'trail_toxic', launchPresets: ['muzzle_flash', 'smoke_puff'], impactPresets: ['poison_cloud', 'poison_drip', 'impact_burst'], statusIcon: 'ui_poison_bubble', soundEvent: 'throw_cannon', screenShake: 0.18 },
    { id: 'shadow', heroIds: ['bat'], colours: ['#f6d365', '#6b4a1a', '#09090b'], trailPreset: 'trail_shadow', launchPresets: ['weapon_rune_halo'], impactPresets: ['ko_wisps', 'hit_sparks'], statusIcon: 'ui_slow_shadow', soundEvent: 'throw_shuriken', screenShake: 0.05 },
    { id: 'iron', heroIds: ['knight'], colours: ['#f2ffff', '#94a3b8', '#334155'], trailPreset: 'trail_iron_sparks', launchPresets: ['bounce_ring'], impactPresets: ['shield_ricochet_sparks', 'bounce_ring'], statusIcon: 'ui_shield_guard', soundEvent: 'throw_shield', screenShake: 0.12 },
    { id: 'soulfire', heroIds: ['reaper', 'necromancer'], colours: ['#f5d0fe', '#a855f7', '#581c87'], trailPreset: 'trail_soulfire', launchPresets: ['sprite_ghostfire', 'weapon_rune_halo'], impactPresets: ['sprite_rune_circle', 'hit_sparks'], statusIcon: 'ui_hallucination_mark', soundEvent: 'flame_throw', screenShake: 0.1 },
    { id: 'sound', heroIds: ['bride'], colours: ['#fff7fb', '#f9a8d4', '#9d174d'], trailPreset: 'weapon_trail_wave', launchPresets: ['weapon_charge_aura'], impactPresets: ['soundwave_rings', 'impact_wave'], statusIcon: 'ui_sound_wave', soundEvent: 'throw_soundwave', screenShake: 0.07 },
    { id: 'blood_bronze', heroIds: ['hunchback'], colours: ['#ef4444', '#cd7f32', '#6b1d1d'], trailPreset: 'weapon_trail_bell', launchPresets: ['weapon_charge_aura', 'smoke_puff'], impactPresets: ['blood_spray', 'bell_toll_rings'], statusIcon: 'ui_bleed_drop', soundEvent: 'throw_bell', screenShake: 0.16 },
    { id: 'holy_lightning', heroIds: ['hag'], colours: ['#fffde7', '#facc15', '#c2410c'], trailPreset: 'trail_holy_lightning', launchPresets: ['cross_spin_trail', 'spark_electric'], impactPresets: ['spark_electric', 'hit_sparks'], statusIcon: 'ui_cross_curse', soundEvent: 'throw_cross', screenShake: 0.11 }
  ];

  function freeze(value) {
    if (value && typeof value === 'object' && !Object.isFrozen(value)) {
      Object.keys(value).forEach(function (key) { freeze(value[key]); });
      Object.freeze(value);
    }
    return value;
  }

  ELEMENTS.forEach(freeze);
  freeze(UNKNOWN);

  function forHero(heroId) {
    for (var i = 0; i < ELEMENTS.length; i++) {
      if (ELEMENTS[i].heroIds.indexOf(heroId) !== -1) return ELEMENTS[i];
    }
    return UNKNOWN;
  }

  function entry(preset, scale, dirX) {
    return { preset: preset, scale: scale, dirX: dirX };
  }

  function trail(heroId, isHeavy) {
    return { preset: forHero(heroId).trailPreset, scale: isHeavy ? 1.4 : 1 };
  }

  function launch(heroId) {
    var element = forHero(heroId);
    return element.launchPresets.map(function (preset) { return entry(preset, 1, 1); });
  }

  function impact(heroId, kind) {
    var element = forHero(heroId);
    var scale = kind === 'wall' ? 0.8 : kind === 'ground' ? 0.9 : 1;
    return element.impactPresets.map(function (preset) { return entry(preset, scale, 1); });
  }

  return { ELEMENTS: ELEMENTS, forHero: forHero, trail: trail, launch: launch, impact: impact };
});
