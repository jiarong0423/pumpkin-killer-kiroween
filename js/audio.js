/*
 * Pumpkin Killer - audio: music layers + effect sounds.
 *
 * UMD module. Works in Node (module.exports) and in the browser (global
 * `GameAudio`). It never touches the DOM and never calls Math.random: the
 * Web Audio context, the file loader and the random source are injected, so
 * tests need no browser and no network.
 *
 *   var audio = GameAudio.createAudio({ ctx: new AudioContext(), loader: loadFn, random: rng });
 *   button.onpointerdown = function () { audio.unlock(); };   // first user gesture
 *   audio.playMusic('battle_calm');
 *   audio.play('throw_cannon');
 *   audio.update(dt);                                        // once per frame
 *
 * Design: docs/sound_design.md. Event map: docs/audio_event_map.json (the same
 * data is embedded below as DEFAULT_EVENT_MAP, a test keeps both in sync).
 * Every statement about how a sound "sounds" is unverified: the author cannot
 * listen.
 *
 * Every event has a synthesized fallback (Web Audio oscillators and filtered
 * noise), so a missing or broken file never makes the game silent. No public
 * method throws: an error is logged once per message and the game continues.
 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module && module.exports) {
    module.exports = api;
  } else {
    root.GameAudio = api;
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  var MAX_VOICES = 16;          // concurrent effect voices (music is separate)
  var BAND_CAP = 3;             // max effects starting in the same band ...
  var BAND_WINDOW = 0.15;       // ... within this many seconds
  var PITCH_LIMIT = 0.06;       // random pitch variation: +/- 6 %
  var MUSIC_TRIM = Math.pow(10, -12 / 20);  // music sits 12 dB under effects
  var DUCK_GAIN = Math.pow(10, -6 / 20);    // music drops 6 dB on big impacts
  var DUCK_HOLD = 0.4;          // seconds
  var DUCK_RELEASE = 0.3;       // seconds
  var LOOKAHEAD = 0.4;          // music scheduler look-ahead, seconds
  var BANDS = ['low', 'mid', 'high'];
  var LAYER_NAMES = ['bed', 'rhythm', 'tension', 'victory', 'defeat'];
  var DEFAULT_VOLUMES = { master: 0.8, music: 1, sfx: 1 };

  // ---------------------------------------------------------------------
  // default event map (identical to docs/audio_event_map.json)

  var DEFAULT_EVENT_MAP = {
    "version": 1,
    "note": "Every file path is a PLANNED path. No file exists yet. When a file is missing the module plays the synthesized recipe named in 'synth'. All file/source statements are unverified, see docs/audio_sources.md.",
    "music": {
      "bpm": 80,
      "key": "D minor",
      "loopSeconds": 24,
      "crossfadeSeconds": 1.5,
      "tensionRampSeconds": 0.8,
      "trimDb": -12,
      "layers": {
        "bed": {
          "file": "assets/audio/music/bgm_title_phantom_v1.m4a",
          "source": "flow-phantom-trajectory",
          "synth": "music_bed"
        },
        "rhythm": {
          "file": "assets/audio/music/bgm_battle_ghoul_v1.m4a",
          "source": "flow-artillery-ghoul",
          "synth": "music_rhythm"
        },
        "tension": {
          "file": "assets/audio/music/tension_drone.ogg",
          "source": "oga-ambient-horror",
          "synth": "music_tension"
        },
        "victory": {
          "file": "assets/audio/music/victory_sting.ogg",
          "source": "oga-short-jingle",
          "synth": "music_victory"
        },
        "defeat": {
          "file": "assets/audio/music/defeat_sting.ogg",
          "source": "oga-game-over-dark",
          "synth": "music_defeat"
        }
      },
      "moods": {
        "title": {
          "battle": false,
          "bed": 1,
          "rhythm": 0,
          "tension": 0,
          "victory": 0,
          "defeat": 0
        },
        "battle_calm": {
          "battle": true,
          "bed": 0.01,
          "rhythm": 1,
          "tension": 0,
          "victory": 0,
          "defeat": 0
        },
        "battle_tense": {
          "battle": true,
          "bed": 0.01,
          "rhythm": 1,
          "tension": 0.35,
          "victory": 0,
          "defeat": 0
        },
        "victory": {
          "battle": false,
          "bed": 0.3,
          "rhythm": 0,
          "tension": 0,
          "victory": 1,
          "defeat": 0
        },
        "defeat": {
          "battle": false,
          "bed": 0.25,
          "rhythm": 0,
          "tension": 0,
          "victory": 0,
          "defeat": 1
        }
      }
    },
    "events": {
      "ui_click": {
        "sound": "ui_click",
        "file": "assets/audio/sfx/ui_click.ogg",
        "source": "kenney-interface",
        "synth": "click",
        "sparkle": null,
        "volume": 0.5,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 3,
        "band": "high",
        "duration": 0.12,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "ui_hover": {
        "sound": "ui_hover",
        "file": "assets/audio/sfx/ui_hover.ogg",
        "source": "kenney-interface",
        "synth": "hover",
        "sparkle": null,
        "volume": 0.25,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 1,
        "band": "high",
        "duration": 0.1,
        "loop": false,
        "duck": false,
        "cooldownMs": 60
      },
      "round_start": {
        "sound": "round_start_bell",
        "file": null,
        "source": "synth-only",
        "synth": "bell_strike",
        "sparkle": "shimmer",
        "volume": 0.8,
        "pitch": [
          0.99,
          1.01
        ],
        "priority": 4,
        "band": "mid",
        "duration": 2.4,
        "loop": false,
        "duck": false,
        "cooldownMs": 0,
        "extras": [
          {
            "file": "assets/audio/sfx/bell_round.ogg",
            "role": "replace",
            "volume": 0.75,
            "pitch": [
              0.99,
              1.01
            ],
            "delayMs": 0,
            "maxSeconds": 2.6,
            "fadeOutMs": 600
          }
        ]
      },
      "round_end": {
        "sound": "round_end_bells",
        "file": null,
        "source": "synth-only",
        "synth": "bell_fall",
        "sparkle": null,
        "volume": 0.7,
        "pitch": [
          0.99,
          1.01
        ],
        "priority": 4,
        "band": "mid",
        "duration": 2.0,
        "loop": false,
        "duck": false,
        "cooldownMs": 0,
        "extras": [
          {
            "file": "assets/audio/sfx/bell_round.ogg",
            "role": "replace",
            "volume": 0.5,
            "pitch": [
              0.94,
              0.96
            ],
            "delayMs": 0,
            "maxSeconds": 1.8,
            "fadeOutMs": 500
          }
        ]
      },
      "charge": {
        "sound": "charge_hum",
        "file": null,
        "source": "synth-only",
        "synth": "hum",
        "sparkle": null,
        "volume": 0.45,
        "pitch": [
          0.97,
          1.03
        ],
        "priority": 3,
        "band": "mid",
        "duration": 6,
        "loop": true,
        "duck": false,
        "cooldownMs": 0
      },
      "throw_spear": {
        "sound": "spear_whoosh",
        "file": "assets/audio/sfx/whoosh_spear.ogg",
        "source": "bigsoundbank-s0573",
        "synth": "whoosh_spear",
        "sparkle": null,
        "volume": 0.7,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "mid",
        "duration": 0.6,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "throw_shuriken": {
        "sound": "shuriken_whirr",
        "file": "assets/audio/sfx/throw_shuriken_gemini.ogg",
        "source": "owner-gemini-sfx-v3",
        "synth": "whirr",
        "sparkle": null,
        "volume": 0.6,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "high",
        "duration": 0.5,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "throw_cannon": {
        "sound": "cannon_boom",
        "file": "assets/audio/sfx/throw_cannon_rocket.ogg",
        "source": "owner-gemini-sfx-v3",
        "synth": "boom_cannon",
        "sparkle": null,
        "volume": 1.0,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 5,
        "band": "low",
        "duration": 1.3,
        "loop": false,
        "duck": true,
        "cooldownMs": 0
      },
      "throw_bomb": {
        "sound": "bomb_boom",
        "file": "assets/audio/sfx/throw_cannon_boom.ogg",
        "source": "kenney-scifi",
        "synth": "boom_cannon",
        "sparkle": null,
        "volume": 1.0,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 5,
        "band": "low",
        "duration": 1.3,
        "loop": false,
        "duck": true,
        "cooldownMs": 0
      },
      "throw_shield": {
        "sound": "shield_spin_throw",
        "file": "assets/audio/sfx/throw_shield_gemini.ogg",
        "source": "owner-gemini-sfx-v3",
        "synth": "spin_shield",
        "sparkle": null,
        "volume": 0.65,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "mid",
        "duration": 0.7,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "throw_flame": {
        "sound": "flame_cast",
        "file": "assets/audio/sfx/throw_flame_fire.ogg",
        "source": "oga-catching-fire",
        "synth": "spell_rise",
        "sparkle": null,
        "volume": 0.6,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "mid",
        "duration": 0.6,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "throw_cross": {
        "sound": "cross_spin",
        "file": "assets/audio/sfx/throw_cross_gemini.ogg",
        "source": "owner-gemini-sfx-v3",
        "synth": "whirr",
        "sparkle": null,
        "volume": 0.6,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "high",
        "duration": 0.84,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "throw_axe": {
        "sound": "axe_heave",
        "file": "assets/audio/sfx/throw_axe_gemini.ogg",
        "source": "owner-gemini-sfx-v3",
        "synth": "spin_shield",
        "sparkle": null,
        "volume": 0.7,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "low",
        "duration": 0.64,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "throw_soundwave": {
        "sound": "wave_chime",
        "file": "assets/audio/sfx/throw_soundwave_sonic.ogg",
        "source": "owner-gemini-sfx-v3",
        "synth": "chime_two",
        "sparkle": null,
        "volume": 0.7,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "mid",
        "duration": 0.94,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "coin_flip": {
        "sound": "coin_flip",
        "file": "assets/audio/sfx/coin_flip.ogg",
        "source": "kenney-rpg",
        "synth": "pickup",
        "sparkle": null,
        "volume": 0.7,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 3,
        "band": "high",
        "duration": 0.85,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "impact_flame": {
        "sound": "flame_impact",
        "file": "assets/audio/sfx/impact_flame_evil_spell.ogg",
        "source": "owner-gemini-sfx-v3",
        "synth": "spell_rise",
        "sparkle": null,
        "volume": 0.9,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "mid",
        "duration": 0.85,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "flight_spear": {
        "sound": "flight_spear_air",
        "file": "assets/audio/sfx/flight_spear_whoosh.ogg",
        "source": "oga-wind-whoosh-loop",
        "synth": "air_whistle",
        "sparkle": null,
        "volume": 0.25,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 2,
        "band": "mid",
        "duration": 6,
        "loop": true,
        "duck": false,
        "cooldownMs": 0
      },
      "flight_shuriken": {
        "sound": "flight_shuriken_buzz",
        "file": null,
        "source": "synth-only",
        "synth": "air_buzz",
        "sparkle": null,
        "volume": 0.2,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 2,
        "band": "high",
        "duration": 6,
        "loop": true,
        "duck": false,
        "cooldownMs": 0
      },
      "flight_cannon": {
        "sound": "flight_cannon_rumble",
        "file": "assets/audio/sfx/flight_cannon_wind.ogg",
        "source": "oga-air-whoosh",
        "synth": "air_rumble",
        "sparkle": null,
        "volume": 0.2,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 2,
        "band": "low",
        "duration": 6,
        "loop": true,
        "duck": false,
        "cooldownMs": 0
      },
      "flight_shield": {
        "sound": "flight_shield_spin",
        "file": "assets/audio/sfx/flight_shield_wind.ogg",
        "source": "oga-short-wind",
        "synth": "air_spin",
        "sparkle": null,
        "volume": 0.25,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 2,
        "band": "mid",
        "duration": 6,
        "loop": true,
        "duck": false,
        "cooldownMs": 0
      },
      "impact_unit": {
        "sound": "impact_unit_thud",
        "file": "assets/audio/sfx/punch_hit.ogg",
        "source": "oga-punch-qubodup",
        "synth": "thud_unit",
        "sparkle": null,
        "volume": 0.85,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "low",
        "duration": 0.5,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "impact_unit_heavy": {
        "sound": "impact_unit_heavy_crash",
        "file": "assets/audio/sfx/punch_heavy.ogg",
        "source": "oga-punch-qubodup",
        "synth": "thud_heavy",
        "sparkle": null,
        "volume": 1.0,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 5,
        "band": "low",
        "duration": 1.0,
        "loop": false,
        "duck": true,
        "cooldownMs": 0
      },
      "impact_fence": {
        "sound": "impact_fence_knock",
        "file": "assets/audio/sfx/thwack_wood.ogg",
        "source": "oga-thwack",
        "synth": "knock_wood",
        "sparkle": null,
        "volume": 0.8,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 3,
        "band": "mid",
        "duration": 0.45,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "impact_fence_break": {
        "sound": "impact_fence_splinter",
        "file": "assets/audio/sfx/fence_break.ogg",
        "source": "kenney-scifi",
        "synth": "splinter",
        "sparkle": null,
        "volume": 0.95,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "mid",
        "duration": 1.0,
        "loop": false,
        "duck": true,
        "cooldownMs": 0
      },
      "impact_ground": {
        "sound": "impact_ground_thump",
        "file": "assets/audio/sfx/stone_ground.ogg",
        "source": "oga-80-cc0-rpg-sfx",
        "synth": "thump_soft",
        "sparkle": null,
        "volume": 0.7,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 3,
        "band": "low",
        "duration": 0.4,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "impact_ground_heavy": {
        "sound": "impact_ground_crump",
        "file": "assets/audio/sfx/stone_ground_heavy.ogg",
        "source": "oga-80-cc0-rpg-sfx",
        "synth": "thump_heavy",
        "sparkle": null,
        "volume": 0.9,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 3,
        "band": "low",
        "duration": 0.8,
        "loop": false,
        "duck": true,
        "cooldownMs": 0,
        "extras": [
          {
            "file": "assets/audio/sfx/rock_break.ogg",
            "role": "layer",
            "volume": 0.45,
            "pitch": [
              0.94,
              1.06
            ],
            "delayMs": 30,
            "maxSeconds": 0.4,
            "fadeOutMs": 80
          }
        ]
      },
      "shield_block": {
        "sound": "shield_block_clang",
        "file": "assets/audio/sfx/metal_bing.ogg",
        "source": "oga-metal-impact",
        "synth": "clang",
        "sparkle": "shimmer",
        "volume": 0.9,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "high",
        "duration": 1.0,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "shield_place": {
        "sound": "shield_place_spell",
        "file": "assets/audio/sfx/spell_magic.ogg",
        "source": "oga-magic-spell-sfx",
        "synth": "spell_rise",
        "sparkle": "shimmer",
        "volume": 0.6,
        "pitch": [
          0.97,
          1.03
        ],
        "priority": 3,
        "band": "high",
        "duration": 1.1,
        "loop": false,
        "duck": false,
        "cooldownMs": 0,
        "extras": [
          {
            "file": "assets/audio/sfx/chime_single.ogg",
            "role": "layer",
            "volume": 0.35,
            "pitch": [
              0.99,
              1.01
            ],
            "delayMs": 300,
            "maxSeconds": 1.4,
            "fadeOutMs": 500,
            "replaceSparkle": true
          }
        ]
      },
      "dice_rattle": {
        "sound": "dice_rattle",
        "file": "assets/audio/sfx/dice_throw_short.ogg",
        "source": "kenney-casino",
        "synth": "dice_rattle",
        "sparkle": null,
        "volume": 0.55,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 2,
        "band": "mid",
        "duration": 0.5,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "dice_result": {
        "sound": "dice_tick",
        "file": "assets/audio/sfx/dice_tick.ogg",
        "source": "kenney-interface",
        "synth": "tick",
        "sparkle": null,
        "volume": 0.6,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 3,
        "band": "high",
        "duration": 0.15,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "move_step": {
        "sound": "move_step",
        "file": "assets/audio/sfx/move_step_footstep.ogg",
        "source": "kenney-rpg",
        "synth": "step",
        "sparkle": null,
        "volume": 0.4,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 2,
        "band": "low",
        "duration": 0.25,
        "loop": false,
        "duck": false,
        "cooldownMs": 120,
        "extras": [
          {
            "file": "assets/audio/sfx/step_leaf.ogg",
            "role": "variant",
            "volume": 0.4,
            "pitch": [
              0.94,
              1.06
            ],
            "delayMs": 0,
            "maxSeconds": 0.3,
            "fadeOutMs": 100,
            "chance": 0.5
          }
        ]
      },
      "ko": {
        "sound": "ko_wail",
        "file": "assets/audio/sfx/roar_ko.ogg",
        "source": "oga-80-cc0-rpg-sfx",
        "synth": "ko",
        "sparkle": "shimmer",
        "volume": 1.0,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 5,
        "band": "mid",
        "duration": 2.0,
        "loop": false,
        "duck": true,
        "cooldownMs": 0,
        "extras": [
          {
            "file": "assets/audio/sfx/bones_rattle.ogg",
            "role": "layer",
            "volume": 0.5,
            "pitch": [
              0.94,
              1.06
            ],
            "delayMs": 250,
            "maxSeconds": 1.1,
            "fadeOutMs": 200,
            "replaceSparkle": true
          }
        ]
      },
      "poison_tick": {
        "sound": "poison_bubble",
        "file": "assets/audio/sfx/poison_tick_soft.ogg",
        "source": "kenney-impact",
        "synth": "bubble",
        "sparkle": null,
        "volume": 0.35,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 2,
        "band": "high",
        "duration": 0.4,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "status_stun": {
        "sound": "status_stun_bonk",
        "file": "assets/audio/sfx/status_stun_owner.ogg",
        "source": "owner-status-sfx-20261122",
        "synth": "status_stun",
        "sparkle": null,
        "volume": 0.7,
        "pitch": [
          0.97,
          1.03
        ],
        "priority": 3,
        "band": "mid",
        "duration": 1.55,
        "loop": false,
        "duck": false,
        "cooldownMs": 150
      },
      "status_slow": {
        "sound": "status_slow_chain",
        "file": "assets/audio/sfx/status_slow_owner.ogg",
        "source": "owner-status-sfx-20261122",
        "synth": "status_slow",
        "sparkle": null,
        "volume": 0.55,
        "pitch": [
          0.97,
          1.03
        ],
        "priority": 2,
        "band": "high",
        "duration": 1.25,
        "loop": false,
        "duck": false,
        "cooldownMs": 150
      },
      "status_shock": {
        "sound": "status_shock_zap",
        "file": "assets/audio/sfx/status_shock_owner.ogg",
        "source": "owner-status-sfx-20261122",
        "synth": "status_shock",
        "sparkle": null,
        "volume": 0.6,
        "pitch": [
          0.97,
          1.03
        ],
        "priority": 3,
        "band": "high",
        "duration": 0.75,
        "loop": false,
        "duck": false,
        "cooldownMs": 150
      },
      "status_frost": {
        "sound": "status_frost_chime",
        "file": "assets/audio/sfx/status_frost_owner.ogg",
        "source": "owner-status-sfx-20261122",
        "synth": "status_frost",
        "sparkle": null,
        "volume": 0.55,
        "pitch": [
          0.98,
          1.02
        ],
        "priority": 2,
        "band": "high",
        "duration": 1.95,
        "loop": false,
        "duck": false,
        "cooldownMs": 150
      },
      "status_bleed": {
        "sound": "status_bleed_slash",
        "file": null,
        "source": "synth-only",
        "synth": "status_bleed",
        "sparkle": null,
        "volume": 0.55,
        "pitch": [
          0.97,
          1.03
        ],
        "priority": 2,
        "band": "mid",
        "duration": 0.55,
        "loop": false,
        "duck": false,
        "cooldownMs": 150
      },
      "status_poison": {
        "sound": "status_poison_hiss",
        "file": null,
        "source": "synth-only",
        "synth": "status_poison",
        "sparkle": null,
        "volume": 0.5,
        "pitch": [
          0.97,
          1.03
        ],
        "priority": 2,
        "band": "high",
        "duration": 0.75,
        "loop": false,
        "duck": false,
        "cooldownMs": 150
      },
      "status_burn": {
        "sound": "status_burn_ignite",
        "file": null,
        "source": "synth-only",
        "synth": "status_burn",
        "sparkle": null,
        "volume": 0.55,
        "pitch": [
          0.97,
          1.03
        ],
        "priority": 2,
        "band": "mid",
        "duration": 0.85,
        "loop": false,
        "duck": false,
        "cooldownMs": 150
      },
      "bleed_tick": {
        "sound": "bleed_drip",
        "file": null,
        "source": "synth-only",
        "synth": "bleed_tick",
        "sparkle": null,
        "volume": 0.35,
        "pitch": [
          0.97,
          1.03
        ],
        "priority": 2,
        "band": "mid",
        "duration": 0.25,
        "loop": false,
        "duck": false,
        "cooldownMs": 150
      },
      "burn_tick": {
        "sound": "burn_crackle",
        "file": null,
        "source": "synth-only",
        "synth": "burn_tick",
        "sparkle": null,
        "volume": 0.35,
        "pitch": [
          0.97,
          1.03
        ],
        "priority": 2,
        "band": "mid",
        "duration": 0.35,
        "loop": false,
        "duck": false,
        "cooldownMs": 150
      },
      "ultimate_ready": {
        "sound": "ultimate_ready_chime",
        "file": "assets/audio/sfx/ultimate_ready_glass.ogg",
        "source": "kenney-impact",
        "synth": "arpeggio_up",
        "sparkle": "shimmer",
        "volume": 0.8,
        "pitch": [
          0.99,
          1.01
        ],
        "priority": 5,
        "band": "high",
        "duration": 1.5,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "low_hp_heartbeat": {
        "sound": "heartbeat",
        "file": "assets/audio/sfx/heartbeat.ogg",
        "source": "bigsoundbank-s0770",
        "synth": "heartbeat",
        "sparkle": null,
        "volume": 0.5,
        "pitch": [
          1,
          1
        ],
        "priority": 2,
        "band": "low",
        "duration": 12,
        "loop": true,
        "duck": false,
        "cooldownMs": 0
      },
      "heal": {
        "sound": "heal_chime",
        "file": "assets/audio/sfx/heal_harp.ogg",
        "source": "oga-magic-words-healing",
        "synth": "chime_two",
        "sparkle": "shimmer",
        "volume": 0.55,
        "pitch": [
          0.99,
          1.01
        ],
        "priority": 3,
        "band": "high",
        "duration": 1.0,
        "loop": false,
        "duck": false,
        "cooldownMs": 0,
        "extras": [
          {
            "file": "assets/audio/sfx/chime_single.ogg",
            "role": "layer",
            "volume": 0.3,
            "pitch": [
              0.99,
              1.01
            ],
            "delayMs": 200,
            "maxSeconds": 1.2,
            "fadeOutMs": 400,
            "replaceSparkle": true
          }
        ]
      },
      "item_pickup": {
        "sound": "item_pickup",
        "file": "assets/audio/sfx/chime_single.ogg",
        "source": "bigsoundbank",
        "synth": "pickup",
        "sparkle": null,
        "volume": 0.5,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 3,
        "band": "high",
        "duration": 0.4,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "ult_skeleton": {
        "sound": "ult_skeleton",
        "file": "assets/audio/sfx/ult_skeleton.ogg",
        "source": "owner-gemini-sfx-v3",
        "synth": "spell_rise",
        "sparkle": null,
        "volume": 0.9,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "mid",
        "duration": 1.25,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "ult_skeleton_hit": {
        "sound": "ult_skeleton_hit",
        "file": "assets/audio/sfx/ult_skeleton_hit.ogg",
        "source": "owner-gemini-sfx-v3",
        "synth": "spell_rise",
        "sparkle": null,
        "volume": 0.9,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "mid",
        "duration": 1.0,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "ult_wizard": {
        "sound": "ult_wizard",
        "file": "assets/audio/sfx/ult_wizard.ogg",
        "source": "owner-gemini-sfx-v3",
        "synth": "spell_rise",
        "sparkle": null,
        "volume": 0.9,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "mid",
        "duration": 0.7,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "ult_wizard_hit": {
        "sound": "ult_wizard_hit",
        "file": "assets/audio/sfx/ult_wizard_hit.ogg",
        "source": "owner-gemini-sfx-v3",
        "synth": "spell_rise",
        "sparkle": null,
        "volume": 0.9,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "mid",
        "duration": 2.25,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "ult_bat": {
        "sound": "ult_bat",
        "file": "assets/audio/sfx/ult_bat.ogg",
        "source": "owner-gemini-sfx-v3",
        "synth": "spell_rise",
        "sparkle": null,
        "volume": 0.9,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "mid",
        "duration": 0.87,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "ult_bat_hit": {
        "sound": "ult_bat_hit",
        "file": "assets/audio/sfx/ult_bat_hit.ogg",
        "source": "owner-gemini-sfx-v3",
        "synth": "spell_rise",
        "sparkle": null,
        "volume": 0.9,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "mid",
        "duration": 1.3,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "ult_knight": {
        "sound": "ult_knight",
        "file": "assets/audio/sfx/ult_knight.ogg",
        "source": "owner-gemini-sfx-v3",
        "synth": "spell_rise",
        "sparkle": null,
        "volume": 0.9,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "mid",
        "duration": 2.22,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "ult_reaper": {
        "sound": "ult_reaper",
        "file": "assets/audio/sfx/ult_reaper.ogg",
        "source": "owner-gemini-sfx-v3",
        "synth": "spell_rise",
        "sparkle": null,
        "volume": 0.9,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "mid",
        "duration": 1.15,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "ult_reaper_hit": {
        "sound": "ult_reaper_hit",
        "file": "assets/audio/sfx/ult_reaper_hit.ogg",
        "source": "owner-gemini-sfx-v3",
        "synth": "spell_rise",
        "sparkle": null,
        "volume": 0.9,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "mid",
        "duration": 1.55,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "ult_bride": {
        "sound": "ult_bride",
        "file": "assets/audio/sfx/ult_bride.ogg",
        "source": "owner-gemini-sfx-v3",
        "synth": "spell_rise",
        "sparkle": null,
        "volume": 0.9,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "mid",
        "duration": 0.95,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "ult_bride_hit": {
        "sound": "ult_bride_hit",
        "file": "assets/audio/sfx/ult_bride_hit.ogg",
        "source": "owner-gemini-sfx-v3",
        "synth": "spell_rise",
        "sparkle": null,
        "volume": 0.9,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "mid",
        "duration": 1.75,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "ult_hunchback": {
        "sound": "ult_hunchback",
        "file": "assets/audio/sfx/ult_hunchback.ogg",
        "source": "owner-gemini-sfx-v3",
        "synth": "spell_rise",
        "sparkle": null,
        "volume": 0.9,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "mid",
        "duration": 0.98,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "ult_hunchback_hit": {
        "sound": "ult_hunchback_hit",
        "file": "assets/audio/sfx/ult_hunchback_hit.ogg",
        "source": "owner-gemini-sfx-v3",
        "synth": "spell_rise",
        "sparkle": null,
        "volume": 0.9,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "mid",
        "duration": 1.55,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "ult_hag": {
        "sound": "ult_hag",
        "file": "assets/audio/sfx/ult_hag.ogg",
        "source": "owner-gemini-sfx-v3",
        "synth": "spell_rise",
        "sparkle": null,
        "volume": 0.9,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "mid",
        "duration": 0.83,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      },
      "ult_hag_hit": {
        "sound": "ult_hag_hit",
        "file": "assets/audio/sfx/ult_hag_hit.ogg",
        "source": "owner-gemini-sfx-v3",
        "synth": "spell_rise",
        "sparkle": null,
        "volume": 0.9,
        "pitch": [
          0.94,
          1.06
        ],
        "priority": 4,
        "band": "mid",
        "duration": 1.6,
        "loop": false,
        "duck": false,
        "cooldownMs": 0
      }
    }
  };



  // ---------------------------------------------------------------------
  // small helpers

  function isNum(v) {
    return typeof v === 'number' && isFinite(v);
  }

  function clamp(v, lo, hi) {
    return v < lo ? lo : v > hi ? hi : v;
  }

  function has(obj, key) {
    return Object.prototype.hasOwnProperty.call(obj, key);
  }

  function midi(m) {
    return 440 * Math.pow(2, (m - 69) / 12);
  }

  function mulberry32(seed) {
    var a = seed | 0;
    return function () {
      a = (a + 0x6d2b79f5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  // ---------------------------------------------------------------------
  // synthesis primitives. E is the build environment of one sound:
  //   ctx, out (destination GainNode), t0 (start time), pitch (multiplier),
  //   rand, noise (shared noise AudioBuffer or null), nodes (sources to stop),
  //   dur (loop length), opts (play options)

  function envGain(c, dest, t, peak, attack, dur) {
    var g = c.createGain();
    var a = Math.min(attack === undefined ? 0.005 : attack, dur * 0.5);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.linearRampToValueAtTime(Math.max(peak, 0.0002), t + a);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    g.connect(dest);
    return g;
  }

  function tremolo(E, g, freq, depth, t, dur) {
    var c = E.ctx;
    var lfo = c.createOscillator();
    lfo.frequency.setValueAtTime(freq, t);
    var d = c.createGain();
    d.gain.setValueAtTime(depth, t);
    lfo.connect(d);
    d.connect(g.gain);
    lfo.start(t);
    if (dur) lfo.stop(t + dur + 0.1);
    E.nodes.push(lfo);
  }

  // One oscillator with a decaying envelope. o: type f0 f1 dur peak attack delay detune
  function osc(E, o) {
    var c = E.ctx;
    var t = E.t0 + (o.delay || 0);
    var f0 = o.f0 * E.pitch;
    var f1 = (o.f1 === undefined ? o.f0 : o.f1) * E.pitch;
    var s = c.createOscillator();
    s.type = o.type || 'sine';
    s.frequency.setValueAtTime(f0, t);
    if (f1 !== f0) s.frequency.exponentialRampToValueAtTime(f1, t + o.dur);
    if (o.detune) s.detune.setValueAtTime(o.detune, t);
    var g = envGain(c, E.out, t, o.peak, o.attack, o.dur);
    s.connect(g);
    s.start(t);
    s.stop(t + o.dur + 0.05);
    E.nodes.push(s);
    return s;
  }

  // Filtered noise burst. o: ftype f0 f1 q dur peak attack delay trem
  function noise(E, o) {
    if (!E.noise) return;
    var c = E.ctx;
    var t = E.t0 + (o.delay || 0);
    var s = c.createBufferSource();
    s.buffer = E.noise;
    s.loop = true;
    var f = c.createBiquadFilter();
    f.type = o.ftype || 'bandpass';
    f.frequency.setValueAtTime(o.f0 * E.pitch, t);
    if (o.f1 && o.f1 !== o.f0) f.frequency.exponentialRampToValueAtTime(o.f1 * E.pitch, t + o.dur);
    f.Q.setValueAtTime(o.q || 1, t);
    var g = envGain(c, E.out, t, o.peak, o.attack, o.dur);
    s.connect(f);
    f.connect(g);
    if (o.trem) tremolo(E, g, o.trem, o.peak * 0.4, t, o.dur);
    s.start(t, E.rand() * 0.5);
    s.stop(t + o.dur + 0.05);
    E.nodes.push(s);
  }

  // Oscillator that holds its level until E.dur (or until stopped). o: type f peak attack detune trem
  function sustainedOsc(E, o) {
    var c = E.ctx;
    var t = E.t0;
    var s = c.createOscillator();
    s.type = o.type || 'sine';
    s.frequency.setValueAtTime(o.f * E.pitch, t);
    if (o.detune) s.detune.setValueAtTime(o.detune, t);
    var g = c.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.linearRampToValueAtTime(o.peak, t + (o.attack || 0.08));
    s.connect(g);
    g.connect(E.out);
    if (o.trem) tremolo(E, g, o.trem, o.peak * 0.5, t, E.dur);
    s.start(t);
    if (E.dur) s.stop(t + E.dur + 0.1);
    E.nodes.push(s);
    return { osc: s, gain: g };
  }

  // Noise that holds its level until E.dur. o: ftype f q peak attack trem
  function sustainedNoise(E, o) {
    if (!E.noise) return;
    var c = E.ctx;
    var t = E.t0;
    var s = c.createBufferSource();
    s.buffer = E.noise;
    s.loop = true;
    var f = c.createBiquadFilter();
    f.type = o.ftype || 'bandpass';
    f.frequency.setValueAtTime(o.f * E.pitch, t);
    f.Q.setValueAtTime(o.q || 1, t);
    var g = c.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.linearRampToValueAtTime(o.peak, t + (o.attack || 0.06));
    s.connect(f);
    f.connect(g);
    g.connect(E.out);
    if (o.trem) tremolo(E, g, o.trem, o.peak * 0.5, t, E.dur);
    s.start(t, E.rand() * 0.5);
    if (E.dur) s.stop(t + E.dur + 0.1);
    E.nodes.push(s);
    return { filter: f, gain: g };
  }

  // Inharmonic partials: a struck bell.
  function bell(E, f, dur, peak, delay) {
    var ratios = [1, 2.76, 5.4, 8.93];
    var amps = [1, 0.5, 0.28, 0.12];
    for (var i = 0; i < ratios.length; i++) {
      osc(E, { type: 'sine', f0: f * ratios[i], dur: dur / (1 + i * 0.6), peak: peak * amps[i], attack: 0.004, delay: delay || 0 });
    }
  }

  // Soft pad chord: detuned triangles with a slow attack (the "choir" bed).
  function pad(E, notes) {
    for (var i = 0; i < notes.length; i++) {
      osc(E, { type: 'triangle', f0: midi(notes[i]), dur: 4.5, peak: 0.09, attack: 1.2, detune: -6 });
      osc(E, { type: 'triangle', f0: midi(notes[i]), dur: 4.5, peak: 0.07, attack: 1.4, detune: 6 });
    }
  }

  // ---------------------------------------------------------------------
  // effect recipes: function (E) -> duration in seconds, or { dur, update }.
  // All numbers are first guesses, unverified by ear.

  var R = {};

  R.click = function (E) {
    osc(E, { type: 'triangle', f0: 1900, f1: 1300, dur: 0.07, peak: 0.5 });
    noise(E, { ftype: 'highpass', f0: 4000, dur: 0.025, peak: 0.2 });
    return 0.1;
  };
  R.hover = function (E) {
    osc(E, { type: 'sine', f0: 2400, f1: 2600, dur: 0.06, peak: 0.3, attack: 0.008 });
    return 0.08;
  };
  R.tick = function (E) {
    osc(E, { type: 'triangle', f0: 2200, f1: 1600, dur: 0.05, peak: 0.5 });
    noise(E, { ftype: 'bandpass', f0: 3000, q: 2, dur: 0.03, peak: 0.25 });
    return 0.12;
  };
  R.bell_strike = function (E) {
    bell(E, midi(50), 2.3, 0.6);
    bell(E, midi(62), 1.6, 0.22);
    return 2.4;
  };
  R.bell_fall = function (E) {
    bell(E, midi(62), 1.2, 0.4);
    bell(E, midi(57), 1.3, 0.4, 0.3);
    bell(E, midi(50), 1.3, 0.45, 0.7);
    return 2.0;
  };
  // Anime-style rising energy-gathering charge swell: sweeps pitch, shimmer
  // beating and resonant aura noise live with opts.power (0..1).
  R.hum = function (E) {
    var sub = sustainedOsc(E, { type: 'sine', f: 68, peak: 0.28, attack: 0.1 });
    var core = sustainedOsc(E, { type: 'sawtooth', f: 136, peak: 0.14, attack: 0.08, trem: 11 });
    var whineA = sustainedOsc(E, { type: 'triangle', f: 272, peak: 0.18, attack: 0.08 });
    var whineB = sustainedOsc(E, { type: 'sine', f: 279, peak: 0.14, attack: 0.08 });
    var aura = sustainedNoise(E, { ftype: 'bandpass', f: 420, q: 3.5, peak: 0.14, attack: 0.12, trem: 9 });
    function setPower(o) {
      var p = clamp(o && isNum(o.power) ? o.power : 0, 0, 1);
      var mult = Math.pow(2, 1.95 * p);
      var subMult = Math.pow(2, 1.4 * p);
      var now = E.ctx.currentTime;
      sub.osc.frequency.setTargetAtTime(68 * E.pitch * subMult, now, 0.04);
      core.osc.frequency.setTargetAtTime(136 * E.pitch * mult, now, 0.04);
      whineA.osc.frequency.setTargetAtTime(272 * E.pitch * mult, now, 0.04);
      whineB.osc.frequency.setTargetAtTime((279 + 14 * p) * E.pitch * mult, now, 0.04);
      if (aura && aura.filter) {
        aura.filter.frequency.setTargetAtTime((420 + 1950 * p * p) * E.pitch, now, 0.05);
      }
    }
    setPower(E.opts);
    return { dur: E.dur, update: setPower };
  };
  R.whoosh_spear = function (E) {
    noise(E, { ftype: 'bandpass', f0: 500, f1: 3200, q: 1.2, dur: 0.5, peak: 0.7, attack: 0.12 });
    osc(E, { type: 'sine', f0: 900, f1: 1700, dur: 0.45, peak: 0.06, attack: 0.1 });
    return 0.55;
  };
  R.whirr = function (E) {
    noise(E, { ftype: 'bandpass', f0: 2600, f1: 4800, q: 3, dur: 0.45, peak: 0.55, attack: 0.05, trem: 30 });
    osc(E, { type: 'triangle', f0: 1400, f1: 2600, dur: 0.4, peak: 0.08 });
    return 0.5;
  };
  R.boom_cannon = function (E) {
    osc(E, { type: 'sine', f0: 120, f1: 36, dur: 0.7, peak: 0.9, attack: 0.004 });
    noise(E, { ftype: 'lowpass', f0: 2200, f1: 180, q: 0.7, dur: 0.5, peak: 0.75, attack: 0.003 });
    osc(E, { type: 'sine', f0: 62, f1: 34, dur: 0.4, peak: 0.6, delay: 0.14, attack: 0.01 });   // recoil thump
    noise(E, { ftype: 'lowpass', f0: 140, dur: 1.1, peak: 0.22, delay: 0.05, attack: 0.1 });    // rumble tail
    return 1.25;
  };
  R.spin_shield = function (E) {
    noise(E, { ftype: 'bandpass', f0: 900, f1: 1500, q: 2, dur: 0.55, peak: 0.5, attack: 0.08, trem: 16 });
    osc(E, { type: 'triangle', f0: 1300, f1: 1000, dur: 0.5, peak: 0.08, attack: 0.05 });
    return 0.6;
  };
  R.air_whistle = function (E) {
    sustainedNoise(E, { ftype: 'bandpass', f: 2300, q: 9, peak: 0.35 });
    return E.dur;
  };
  R.air_buzz = function (E) {
    sustainedNoise(E, { ftype: 'bandpass', f: 4200, q: 4, peak: 0.3, trem: 38 });
    return E.dur;
  };
  R.air_rumble = function (E) {
    sustainedNoise(E, { ftype: 'lowpass', f: 170, q: 0.7, peak: 0.6 });
    return E.dur;
  };
  R.air_spin = function (E) {
    sustainedNoise(E, { ftype: 'bandpass', f: 1000, q: 2.5, peak: 0.35, trem: 11 });
    return E.dur;
  };
  R.thud_unit = function (E) {
    osc(E, { type: 'sine', f0: 150, f1: 55, dur: 0.28, peak: 0.8, attack: 0.003 });
    noise(E, { ftype: 'lowpass', f0: 1000, f1: 200, dur: 0.2, peak: 0.5, attack: 0.002 });
    osc(E, { type: 'triangle', f0: 300, f1: 100, dur: 0.1, peak: 0.25, attack: 0.002 });
    return 0.4;
  };
  R.thud_heavy = function (E) {
    osc(E, { type: 'sine', f0: 95, f1: 30, dur: 0.8, peak: 1, attack: 0.004 });
    noise(E, { ftype: 'lowpass', f0: 1500, f1: 90, q: 0.7, dur: 0.6, peak: 0.8, attack: 0.003 });
    osc(E, { type: 'sine', f0: 48, dur: 0.6, peak: 0.5, delay: 0.06, attack: 0.01 });
    noise(E, { ftype: 'highpass', f0: 2500, dur: 0.3, peak: 0.15, delay: 0.02 });
    return 1.0;
  };
  R.knock_wood = function (E) {
    osc(E, { type: 'sine', f0: 340, f1: 210, dur: 0.14, peak: 0.6, attack: 0.002 });
    osc(E, { type: 'triangle', f0: 560, f1: 380, dur: 0.09, peak: 0.3, attack: 0.002 });
    noise(E, { ftype: 'bandpass', f0: 1800, q: 1.5, dur: 0.05, peak: 0.4, attack: 0.002 });
    return 0.3;
  };
  R.splinter = function (E) {
    noise(E, { ftype: 'lowpass', f0: 1200, f1: 120, dur: 0.5, peak: 0.6, attack: 0.003 });
    osc(E, { type: 'sine', f0: 100, f1: 40, dur: 0.5, peak: 0.7, attack: 0.004 });
    for (var i = 0; i < 7; i++) {
      noise(E, { ftype: 'bandpass', f0: 1500 + E.rand() * 3000, q: 3, dur: 0.04, delay: 0.05 + i * 0.07 + E.rand() * 0.02, peak: 0.35 * (1 - i / 10), attack: 0.002 });
    }
    return 1.0;
  };
  R.thump_soft = function (E) {
    osc(E, { type: 'sine', f0: 110, f1: 48, dur: 0.3, peak: 0.7, attack: 0.004 });
    noise(E, { ftype: 'lowpass', f0: 500, dur: 0.12, peak: 0.3, attack: 0.003 });
    return 0.35;
  };
  R.thump_heavy = function (E) {
    osc(E, { type: 'sine', f0: 75, f1: 32, dur: 0.7, peak: 0.9, attack: 0.005 });
    noise(E, { ftype: 'lowpass', f0: 800, f1: 90, dur: 0.5, peak: 0.6, attack: 0.004 });
    noise(E, { ftype: 'bandpass', f0: 1600, q: 0.8, dur: 0.3, delay: 0.12, peak: 0.12 });
    return 0.8;
  };
  // Metal clang: inharmonic partials.
  R.clang = function (E) {
    var ratios = [1, 1.59, 2.14, 2.65, 3.32];
    var amps = [0.6, 0.45, 0.35, 0.25, 0.15];
    for (var i = 0; i < ratios.length; i++) {
      osc(E, { type: 'sine', f0: 620 * ratios[i], dur: 0.9 / (1 + i * 0.5), peak: amps[i] * 0.7, attack: 0.002 });
    }
    noise(E, { ftype: 'highpass', f0: 3000, dur: 0.04, peak: 0.4, attack: 0.001 });
    return 0.9;
  };
  // Ghost shimmer: detuned high sines (sparkle layer).
  R.shimmer = function (E) {
    var f = [2093, 2099, 2637, 3136, 3142];
    for (var i = 0; i < f.length; i++) {
      osc(E, { type: 'sine', f0: f[i], dur: 0.7 + E.rand() * 0.3, peak: 0.06, attack: 0.03, delay: E.rand() * 0.05 });
    }
    return 1.05;
  };
  R.spell_rise = function (E) {
    osc(E, { type: 'sine', f0: 400, f1: 1600, dur: 0.8, peak: 0.3, attack: 0.1 });
    osc(E, { type: 'sine', f0: 404, f1: 1616, dur: 0.8, peak: 0.22, attack: 0.1 });
    noise(E, { ftype: 'bandpass', f0: 1500, f1: 5000, q: 2, dur: 0.8, peak: 0.12, attack: 0.3 });
    return 1.0;
  };
  R.dice_rattle = function (E) {
    for (var i = 0; i < 9; i++) {
      var d = i * 0.07 + E.rand() * 0.03;
      var p = 0.55 * (1 - i * 0.07);
      noise(E, { ftype: 'bandpass', f0: 1500 + E.rand() * 2500, q: 3, dur: 0.035, delay: d, peak: p, attack: 0.002 });
      osc(E, { type: 'triangle', f0: 800 + E.rand() * 900, dur: 0.04, delay: d, peak: p * 0.5, attack: 0.002 });
    }
    return 0.85;
  };
  R.step = function (E) {
    osc(E, { type: 'sine', f0: 125, f1: 70, dur: 0.13, peak: 0.6, attack: 0.003 });
    noise(E, { ftype: 'lowpass', f0: 500, dur: 0.07, peak: 0.3, attack: 0.002 });
    return 0.2;
  };
  R.ko = function (E) {
    osc(E, { type: 'sine', f0: 680, f1: 170, dur: 1.4, peak: 0.5, attack: 0.05 });
    osc(E, { type: 'triangle', f0: 700, f1: 175, dur: 1.4, peak: 0.3, attack: 0.05 });
    noise(E, { ftype: 'bandpass', f0: 1400, f1: 300, q: 1.5, dur: 1.4, peak: 0.25, attack: 0.2 });
    return 1.5;
  };
  R.bubble = function (E) {
    osc(E, { type: 'sine', f0: 300, f1: 900, dur: 0.09, peak: 0.4, attack: 0.005 });
    osc(E, { type: 'sine', f0: 420, f1: 1100, dur: 0.08, delay: 0.13, peak: 0.3, attack: 0.005 });
    return 0.25;
  };
  R.arpeggio_up = function (E) {
    var notes = [74, 77, 81, 86];
    for (var i = 0; i < notes.length; i++) bell(E, midi(notes[i]), 1.0, 0.3, i * 0.1);
    return 1.4;
  };
  R.chime_two = function (E) {
    osc(E, { type: 'sine', f0: 880, dur: 0.6, peak: 0.4, attack: 0.005 });
    osc(E, { type: 'sine', f0: 1318, dur: 0.7, delay: 0.12, peak: 0.35, attack: 0.005 });
    return 0.85;
  };
  R.pickup = function (E) {
    osc(E, { type: 'sine', f0: 700, f1: 1400, dur: 0.12, peak: 0.4, attack: 0.005 });
    osc(E, { type: 'sine', f0: 1400, dur: 0.2, delay: 0.08, peak: 0.3, attack: 0.005 });
    return 0.3;
  };
  // Status cues (owner 2026-11-22: stun, slow, shock and weak had no sound): all four are synthesized, no recording, no licence.
  R.status_stun = function (E) {   // a dull bonk, then three small star dings
    osc(E, { type: 'sine', f0: 230, f1: 85, dur: 0.2, peak: 0.85, attack: 0.003 });
    noise(E, { ftype: 'lowpass', f0: 900, f1: 220, dur: 0.14, peak: 0.45, attack: 0.002 });
    osc(E, { type: 'sine', f0: 1568, dur: 0.38, delay: 0.14, peak: 0.26, attack: 0.004 });
    osc(E, { type: 'sine', f0: 1976, dur: 0.38, delay: 0.26, peak: 0.24, attack: 0.004 });
    osc(E, { type: 'sine', f0: 2349, dur: 0.38, delay: 0.38, peak: 0.22, attack: 0.004 });
    return 0.9;
  };
  R.status_slow = function (E) {   // a shackle closing: a few short metal clinks and a dragging scrape
    var d = [0, 0.07, 0.15, 0.22, 0.34], f = [3300, 3900, 3000, 4300, 3500], i;
    for (i = 0; i < d.length; i++) {
      noise(E, { ftype: 'bandpass', f0: f[i], q: 7, dur: 0.035, delay: d[i], peak: 0.55, attack: 0.001 });
      osc(E, { type: 'triangle', f0: f[i] * 0.42, f1: f[i] * 0.3, dur: 0.06, delay: d[i], peak: 0.28, attack: 0.001 });
    }
    noise(E, { ftype: 'lowpass', f0: 520, f1: 260, dur: 0.5, delay: 0.04, peak: 0.2, attack: 0.02 });
    return 0.7;
  };
  R.status_shock = function (E) {   // a crackle of short noise bursts under a falling zap
    var d = [0, 0.03, 0.075, 0.13, 0.2, 0.29, 0.38], i;
    for (i = 0; i < d.length; i++) noise(E, { ftype: 'highpass', f0: 2600 + (i % 3) * 700, dur: 0.02 + (i % 2) * 0.015, delay: d[i], peak: 0.5 - i * 0.04, attack: 0.001 });
    osc(E, { type: 'sawtooth', f0: 2600, f1: 280, dur: 0.2, peak: 0.34, attack: 0.002 });
    osc(E, { type: 'square', f0: 120, f1: 90, dur: 0.45, delay: 0.05, peak: 0.12, attack: 0.01 });
    return 0.6;
  };
  R.status_frost = function (E) {   // glass: three high partials ringing out over a short icy shimmer
    osc(E, { type: 'sine', f0: 2093, dur: 0.95, peak: 0.26, attack: 0.003 });
    osc(E, { type: 'sine', f0: 2637, dur: 0.85, delay: 0.06, peak: 0.24, attack: 0.003 });
    osc(E, { type: 'sine', f0: 3136, dur: 0.75, delay: 0.12, peak: 0.2, attack: 0.003 });
    noise(E, { ftype: 'highpass', f0: 6200, dur: 0.2, peak: 0.2, attack: 0.002 });
    osc(E, { type: 'triangle', f0: 1100, f1: 2400, dur: 0.25, peak: 0.14, attack: 0.01 });
    return 1.1;
  };
  // Status cues for bleed, poison and burn (gap N9, owner 2026-11-23: wire the missing sounds). All synthesized, no recording, no licence.
  R.status_bleed = function (E) {   // a quick wet slash, a low thud and two slow drips
    noise(E, { ftype: 'bandpass', f0: 3800, f1: 900, q: 2, dur: 0.16, peak: 0.5, attack: 0.002 });
    osc(E, { type: 'sine', f0: 150, f1: 70, dur: 0.18, peak: 0.5, attack: 0.003 });
    osc(E, { type: 'sine', f0: 900, f1: 420, dur: 0.08, delay: 0.26, peak: 0.22, attack: 0.002 });
    osc(E, { type: 'sine', f0: 780, f1: 380, dur: 0.08, delay: 0.4, peak: 0.18, attack: 0.002 });
    return 0.55;
  };
  R.status_poison = function (E) {   // a thin hiss with three rising bubbles over a low murk
    noise(E, { ftype: 'highpass', f0: 5200, dur: 0.45, peak: 0.22, attack: 0.03 });
    osc(E, { type: 'sine', f0: 260, f1: 520, dur: 0.12, delay: 0.1, peak: 0.3, attack: 0.004 });
    osc(E, { type: 'sine', f0: 340, f1: 640, dur: 0.12, delay: 0.26, peak: 0.26, attack: 0.004 });
    osc(E, { type: 'sine', f0: 200, f1: 420, dur: 0.12, delay: 0.4, peak: 0.24, attack: 0.004 });
    osc(E, { type: 'triangle', f0: 110, f1: 90, dur: 0.5, peak: 0.12, attack: 0.02 });
    return 0.75;
  };
  R.status_burn = function (E) {   // an ignition whoomp that opens up, then five small crackles
    var d = [0.12, 0.2, 0.29, 0.41, 0.5], i;
    noise(E, { ftype: 'lowpass', f0: 400, f1: 2200, dur: 0.22, peak: 0.5, attack: 0.01 });
    for (i = 0; i < d.length; i++) noise(E, { ftype: 'highpass', f0: 3000 + (i % 2) * 900, dur: 0.02 + (i % 3) * 0.008, delay: d[i], peak: 0.3, attack: 0.001 });
    osc(E, { type: 'sawtooth', f0: 90, f1: 160, dur: 0.35, peak: 0.15, attack: 0.01 });
    return 0.85;
  };
  R.bleed_tick = function (E) {   // one drip at a round start
    osc(E, { type: 'sine', f0: 700, f1: 300, dur: 0.09, peak: 0.35, attack: 0.002 });
    noise(E, { ftype: 'lowpass', f0: 1200, dur: 0.06, peak: 0.2, attack: 0.002 });
    return 0.2;
  };
  R.burn_tick = function (E) {   // three crackles at a round start
    var d = [0, 0.05, 0.11], i;
    for (i = 0; i < d.length; i++) noise(E, { ftype: 'highpass', f0: 3500, dur: 0.02, delay: d[i], peak: 0.4, attack: 0.001 });
    noise(E, { ftype: 'lowpass', f0: 600, dur: 0.15, peak: 0.2, attack: 0.005 });
    return 0.3;
  };
  // Heartbeat: lub-dub every 0.9 s, scheduled for the whole loop length.
  R.heartbeat = function (E) {
    var n = Math.max(1, Math.floor(E.dur / 0.9));
    for (var i = 0; i < n; i++) {
      osc(E, { type: 'sine', f0: 62, f1: 40, dur: 0.14, delay: i * 0.9, peak: 0.8, attack: 0.01 });
      osc(E, { type: 'sine', f0: 56, f1: 38, dur: 0.12, delay: i * 0.9 + 0.22, peak: 0.55, attack: 0.01 });
    }
    return E.dur;
  };

  var RECIPE_NAMES = Object.keys(R);

  // ---------------------------------------------------------------------
  // synthesized music layers (D minor, 80 BPM, 64 eighth-note steps = 24 s).
  // start(E, L): persistent sources. step(E, s): notes for eighth-note step s.

  var BELL_SCALE = [62, 65, 69, 72, 74, 77]; // D F A C D F
  var M = {};

  M.bed = {
    start: function (E) {
      sustainedOsc(E, { type: 'sine', f: midi(38), peak: 0.35, attack: 1.5 });
      sustainedOsc(E, { type: 'triangle', f: midi(45), peak: 0.12, attack: 2, detune: 4 });
    },
    step: function (E, s) {
      if (s % 32 === 0) pad(E, [50, 53, 57]);
      if (s % 4 === 2 && E.rand() < 0.4) {
        var n = BELL_SCALE[Math.floor(E.rand() * BELL_SCALE.length)] + 12;
        bell(E, midi(n), 2.6, 0.07);
      }
    }
  };
  M.rhythm = {
    step: function (E, s) {
      var k = s % 8;
      if (k === 0 || k === 4) {
        osc(E, { type: 'sine', f0: 70, f1: 42, dur: 0.28, peak: k === 0 ? 0.5 : 0.35, attack: 0.004 });
      } else if (s % 2 === 1) {
        noise(E, { ftype: 'highpass', f0: 6000, dur: 0.04, peak: 0.05, attack: 0.002 });
      }
    }
  };
  M.tension = {
    start: function (E) {
      sustainedOsc(E, { type: 'sine', f: midi(68), peak: 0.1, attack: 1.5, trem: 5.5 });
      sustainedOsc(E, { type: 'sine', f: midi(62), peak: 0.06, attack: 1.5 });
    },
    step: function (E, s) {
      if (s % 16 === 8) bell(E, midi(80), 1.6, 0.05);
    }
  };
  M.victory = {
    step: function (E, s) {
      var arp = [62, 66, 69, 74];
      if (s % 32 === 0) pad(E, [50, 54, 57]);
      if (s % 2 === 0) bell(E, midi(arp[(s / 2) % 4] + 12), 1.5, 0.08);
    }
  };
  M.defeat = {
    start: function (E) {
      sustainedOsc(E, { type: 'sine', f: midi(38), peak: 0.3, attack: 1.5 });
      sustainedOsc(E, { type: 'sine', f: midi(39), peak: 0.1, attack: 2 });
    },
    step: function (E, s) {
      var line = [74, 72, 69, 65, 62, 60];
      if (s % 8 === 0) bell(E, midi(line[(s / 8) % 6]), 3, 0.08);
    }
  };

  // ---------------------------------------------------------------------
  // event map sanitising

  function sanitizeEntry(e) {
    if (!e || typeof e !== 'object') return null;
    if (typeof e.synth !== 'string' || !has(R, e.synth)) return null;
    var p = Array.isArray(e.pitch) && isNum(e.pitch[0]) && isNum(e.pitch[1]) ? e.pitch : [1, 1];
    var lo = clamp(Math.min(p[0], p[1]), 1 - PITCH_LIMIT, 1 + PITCH_LIMIT);
    var hi = clamp(Math.max(p[0], p[1]), 1 - PITCH_LIMIT, 1 + PITCH_LIMIT);
    return {
      sound: typeof e.sound === 'string' ? e.sound : '',
      file: typeof e.file === 'string' && e.file ? e.file : null,
      synth: e.synth,
      sparkle: typeof e.sparkle === 'string' && has(R, e.sparkle) ? e.sparkle : null,
      volume: clamp(isNum(e.volume) ? e.volume : 1, 0, 1),
      pitch: [lo, hi],
      priority: clamp(Math.round(isNum(e.priority) ? e.priority : 1), 1, 5),
      band: BANDS.indexOf(e.band) >= 0 ? e.band : 'mid',
      duration: clamp(isNum(e.duration) ? e.duration : 1, 0.05, 60),
      loop: !!e.loop,
      duck: !!e.duck,
      cooldownMs: clamp(isNum(e.cooldownMs) ? e.cooldownMs : 0, 0, 5000),
      extras: sanitizeExtras(e.extras)
    };
  }

  var EXTRA_ROLES = ['replace', 'variant', 'layer'];
  function sanitizeExtras(list) {
    if (!Array.isArray(list)) return [];
    var out = [];
    list.slice(0, 2).forEach(function (x) {
      if (!x || typeof x.file !== 'string' || !x.file || EXTRA_ROLES.indexOf(x.role) < 0) return;
      var p = Array.isArray(x.pitch) && isNum(x.pitch[0]) && isNum(x.pitch[1]) ? x.pitch : [1, 1];
      out.push({
        file: x.file, role: x.role,
        volume: clamp(isNum(x.volume) ? x.volume : 0.5, 0, 1),
        pitch: [clamp(Math.min(p[0], p[1]), 1 - PITCH_LIMIT, 1 + PITCH_LIMIT), clamp(Math.max(p[0], p[1]), 1 - PITCH_LIMIT, 1 + PITCH_LIMIT)],
        delayMs: clamp(isNum(x.delayMs) ? x.delayMs : 0, 0, 2000),
        maxSeconds: clamp(isNum(x.maxSeconds) ? x.maxSeconds : 5, 0.05, 10),
        fadeOutMs: clamp(isNum(x.fadeOutMs) ? x.fadeOutMs : 100, 0, 2000),
        chance: clamp(isNum(x.chance) ? x.chance : 1, 0, 1),
        replaceSparkle: !!x.replaceSparkle
      });
    });
    return out;
  }

  function sanitizeMap(raw) {
    var src = raw && typeof raw === 'object' ? raw : DEFAULT_EVENT_MAP;
    var events = {};
    var evSrc = src.events && typeof src.events === 'object' ? src.events : {};
    Object.keys(evSrc).forEach(function (k) {
      var e = sanitizeEntry(evSrc[k]);
      if (e) events[k] = e;
    });
    var m = src.music && typeof src.music === 'object' ? src.music : DEFAULT_EVENT_MAP.music;
    var moods = m.moods && typeof m.moods === 'object' ? m.moods : DEFAULT_EVENT_MAP.music.moods;
    var layers = m.layers && typeof m.layers === 'object' ? m.layers : DEFAULT_EVENT_MAP.music.layers;
    return {
      events: events,
      music: {
        bpm: clamp(isNum(m.bpm) ? m.bpm : 80, 40, 200),
        crossfadeSeconds: clamp(isNum(m.crossfadeSeconds) ? m.crossfadeSeconds : 1.5, 0.05, 10),
        tensionRampSeconds: clamp(isNum(m.tensionRampSeconds) ? m.tensionRampSeconds : 0.8, 0.05, 10),
        layers: layers,
        moods: moods
      }
    };
  }

  // ---------------------------------------------------------------------
  // the audio engine

  function createAudio(options) {
    var cfg = options && typeof options === 'object' ? options : {};
    var rand = typeof cfg.random === 'function' ? cfg.random : mulberry32(1);
    var logFn = typeof cfg.log === 'function' ? cfg.log
      : (typeof console !== 'undefined' && console.warn ? function (m) { console.warn(m); } : function () {});
    var map = sanitizeMap(cfg.eventMap);

    var ctx = null;
    var built = false;
    var unlocked = false;
    var muted = false;
    var volumes = { master: DEFAULT_VOLUMES.master, music: DEFAULT_VOLUMES.music, sfx: DEFAULT_VOLUMES.sfx };
    var nodes = { master: null, sfx: null, music: null, duck: null };
    var noiseBuf = null;
    var voices = [];
    var loops = {};
    var lastPlay = {};
    var nextVoiceId = 1;
    var cache = {};
    var readyPromise = null;
    var errors = 0;
    var logged = {};
    var duck = { timer: 0, level: 1 };
    var layers = {};
    var musicState = { mood: null, tension: 0 };
    var seq = { step: 0, nextTime: null };

    // ---- errors

    function warnOnce(key, msg) {
      if (logged[key]) return;
      logged[key] = true;
      try { logFn('[audio] ' + msg); } catch (e) { /* ignore */ }
    }

    function fail(label, e) {
      errors++;
      warnOnce(label + ':' + (e && e.message ? e.message : String(e)), label + ' failed: ' + (e && e.message ? e.message : String(e)));
    }

    // ---- graph

    function getCtx() {
      if (ctx) return ctx;
      var c = cfg.ctx;
      if (typeof c === 'function') c = c();
      ctx = c && typeof c === 'object' ? c : null;
      return ctx;
    }

    function makeNoise() {
      var rate = isNum(ctx.sampleRate) && ctx.sampleRate > 0 ? ctx.sampleRate : 44100;
      var len = Math.floor(rate * 2);
      var buf = ctx.createBuffer(1, len, rate);
      var data = buf.getChannelData(0);
      for (var i = 0; i < len; i++) data[i] = rand() * 2 - 1;
      return buf;
    }

    function buildGraph() {
      var c = ctx;
      nodes.master = c.createGain();
      nodes.sfx = c.createGain();
      nodes.music = c.createGain();
      nodes.duck = c.createGain();
      nodes.sfx.connect(nodes.master);
      nodes.music.connect(nodes.duck);
      nodes.duck.connect(nodes.master);
      if (typeof c.createDynamicsCompressor === 'function') {
        var comp = c.createDynamicsCompressor();
        try {
          comp.threshold.value = -10;
          comp.ratio.value = 4;
          comp.attack.value = 0.005;
          comp.release.value = 0.2;
        } catch (e) { /* defaults are fine */ }
        nodes.master.connect(comp);
        comp.connect(c.destination);
      } else {
        nodes.master.connect(c.destination);
      }
      nodes.duck.gain.value = 1;
      try { noiseBuf = makeNoise(); } catch (e) { fail('noise buffer', e); noiseBuf = null; }
      LAYER_NAMES.forEach(function (name) {
        var g = c.createGain();
        g.gain.value = 0;
        g.connect(nodes.music);
        layers[name] = { gain: g, active: false, mode: null, nodes: [], stopAt: null, target: 0 };
      });
      built = true;
      applyVolumes(true);
    }

    function applyVolumes(immediate) {
      if (!built) return;
      var now = ctx.currentTime;
      var vals = [
        [nodes.master.gain, muted ? 0 : volumes.master],
        [nodes.sfx.gain, volumes.sfx],
        [nodes.music.gain, volumes.music * MUSIC_TRIM]
      ];
      vals.forEach(function (pair) {
        if (immediate) pair[0].value = pair[1];
        else pair[0].setTargetAtTime(pair[1], now, 0.02);
      });
    }

    function rampParam(param, v, secs, now) {
      param.cancelScheduledValues(now);
      param.setValueAtTime(param.value, now);
      param.linearRampToValueAtTime(v, now + secs);
    }

    // ---- file loading

    function usableBuffer(file) {
      return file && cache[file] ? cache[file] : null;
    }

    function preload() {
      if (readyPromise) return readyPromise;
      var loader = cfg.loader;
      var fn = typeof loader === 'function' ? loader
        : (loader && typeof loader.load === 'function' ? function (f) { return loader.load(f); } : null);
      var files = [];
      function addFile(f) { if (f && files.indexOf(f) < 0) files.push(f); }
      Object.keys(map.events).forEach(function (k) { addFile(map.events[k].file); map.events[k].extras.forEach(function (x) { addFile(x.file); }); });
      Object.keys(map.music.layers).forEach(function (k) { addFile(map.music.layers[k] && map.music.layers[k].file); });
      if (!fn || !files.length) {
        readyPromise = Promise.resolve();
        return readyPromise;
      }
      var missing = 0;
      var jobs = files.map(function (f) {
        var p;
        try { p = fn(f); } catch (e) { p = Promise.reject(e); }
        return Promise.resolve(p).then(function (b) {
          if (b && typeof b === 'object' && isNum(b.duration) && b.duration > 0) {
            cache[f] = b;
          } else {
            cache[f] = null;
            missing++;
          }
        }, function () {
          cache[f] = null;
          missing++;
        });
      });
      readyPromise = Promise.all(jobs).then(function () {
        if (missing) warnOnce('missing-files', missing + ' of ' + files.length + ' audio files not loaded, using synthesized sounds');
        upgradeLayers();
      });
      return readyPromise;
    }

    // ---- voices

    function stopNodes(list, when) {
      list.forEach(function (n) {
        try { n.stop(when); } catch (e) { /* already stopped */ }
      });
    }

    function removeVoice(v) {
      var i = voices.indexOf(v);
      if (i >= 0) voices.splice(i, 1);
      if (loops[v.event] === v) delete loops[v.event];
    }

    function stopVoice(v, fade) {
      var now = ctx.currentTime;
      var f = isNum(fade) ? fade : 0.05;
      try {
        v.gain.gain.cancelScheduledValues(now);
        v.gain.gain.setValueAtTime(v.gain.gain.value, now);
        v.gain.gain.linearRampToValueAtTime(0, now + f);
      } catch (e) { /* ignore */ }
      stopNodes(v.nodes, now + f + 0.01);
      removeVoice(v);
    }

    function prune(now) {
      for (var i = voices.length - 1; i >= 0; i--) {
        if (voices[i].endsAt <= now) removeVoice(voices[i]);
      }
    }

    // Lowest priority first, oldest first among equals.
    function weakest(list) {
      var best = null;
      list.forEach(function (v) {
        if (!best || v.priority < best.priority || (v.priority === best.priority && v.start < best.start)) best = v;
      });
      return best;
    }

    // Make room under the band cap and the voice limit. False = drop the new sound.
    function makeRoom(entry, now) {
      var inBand = voices.filter(function (v) { return v.band === entry.band && now - v.start <= BAND_WINDOW; });
      if (inBand.length >= BAND_CAP) {
        var vb = weakest(inBand);
        if (vb.priority > entry.priority) return false;
        stopVoice(vb, 0.03);
      }
      if (voices.length >= MAX_VOICES) {
        var va = weakest(voices);
        if (va.priority > entry.priority) return false;
        stopVoice(va, 0.03);
      }
      return true;
    }

    function pickPitch(entry) {
      var lo = entry.pitch[0];
      var hi = entry.pitch[1];
      return clamp(lo + rand() * (hi - lo), 1 - PITCH_LIMIT, 1 + PITCH_LIMIT);
    }

    function playBuffer(E, buf, entry) {
      var s = ctx.createBufferSource();
      s.buffer = buf;
      s.playbackRate.value = E.pitch;
      s.loop = entry.loop;
      s.connect(E.out);
      s.start(E.t0);
      if (entry.loop) s.stop(E.t0 + entry.duration + 0.1);
      E.nodes.push(s);
      return entry.loop ? entry.duration : buf.duration / E.pitch;
    }

    // Extra file layers (docs/sound_mapping.md): 'replace' and 'variant' take the place of the main sound, 'layer' adds to it.
    function playExtra(E, x, buf, entryDur) {
      var s = ctx.createBufferSource();
      var g = ctx.createGain();
      var pitch = clamp(x.pitch[0] + rand() * (x.pitch[1] - x.pitch[0]), 1 - PITCH_LIMIT, 1 + PITCH_LIMIT);
      var t = E.t0 + x.delayMs / 1000;
      var len = Math.min(x.maxSeconds, buf.duration / pitch);
      var fade = Math.min(x.fadeOutMs / 1000, len);
      s.buffer = buf;
      s.playbackRate.value = pitch;
      g.gain.setValueAtTime(x.volume, t);
      g.gain.setValueAtTime(x.volume, t + len - fade);
      g.gain.linearRampToValueAtTime(0.0001, t + len);
      s.connect(g);
      g.connect(nodes.sfx);
      s.start(t);
      s.stop(t + len + 0.02);
      E.nodes.push(s);
      return x.delayMs / 1000 + len;
    }

    function triggerDuck() {
      duck.timer = DUCK_HOLD;
      duck.level = DUCK_GAIN;
      nodes.duck.gain.setTargetAtTime(duck.level, ctx.currentTime, 0.015);
    }

    function playInner(name, opts) {
      if (!unlocked || muted) return null;
      var o = opts && typeof opts === 'object' ? opts : {};
      var entry = typeof name === 'string' && has(map.events, name) ? map.events[name] : null;
      if (!entry) {
        warnOnce('unknown:' + String(name), 'unknown event ' + String(name));
        return null;
      }
      var now = ctx.currentTime;
      prune(now);

      if (entry.loop && loops[name]) {   // already running: only update parameters
        var cur = loops[name];
        if (cur.update) cur.update(o);
        return { id: cur.id, event: name, sound: entry.sound, synth: cur.synth, pitch: cur.pitch, duration: entry.duration, refreshed: true };
      }
      if (entry.cooldownMs > 0 && lastPlay[name] !== undefined && now - lastPlay[name] < entry.cooldownMs / 1000) return null;
      if (!makeRoom(entry, now)) return null;
      lastPlay[name] = now;

      var pitch = pickPitch(entry);
      var vol = clamp(entry.volume * (isNum(o.volume) ? clamp(o.volume, 0, 1) : 1), 0, 1);
      var g = ctx.createGain();
      g.gain.setValueAtTime(vol, now);
      g.connect(nodes.sfx);
      var E = { ctx: ctx, out: g, t0: now + 0.005, pitch: pitch, rand: rand, noise: noiseBuf, nodes: [], dur: entry.duration, opts: o };

      var usedFile = false;
      var end = 0;
      var update = null;
      var buf = usableBuffer(entry.file);
      var layerEnd = 0;
      var sparkleReplaced = false;
      var replaced = false;
      entry.extras.forEach(function (x) {
        var xb = usableBuffer(x.file);
        if (!xb) return;
        try {
          if (x.role === 'layer') {
            layerEnd = Math.max(layerEnd, playExtra(E, x, xb));
            if (x.replaceSparkle) sparkleReplaced = true;
          } else if (!replaced && (x.role === 'replace' || rand() < x.chance)) {
            layerEnd = Math.max(layerEnd, playExtra(E, x, xb));
            replaced = true;
            if (x.replaceSparkle) sparkleReplaced = true;
          }
        } catch (err) {
          fail('extra ' + name, err);
        }
      });
      if (replaced) { buf = null; usedFile = true; end = 0; }
      if (buf) {
        try {
          end = playBuffer(E, buf, entry);
          usedFile = true;
        } catch (e) {
          fail('file ' + name, e);
          stopNodes(E.nodes, now);
          E.nodes = [];
        }
      }
      if (!usedFile) {
        var r = R[entry.synth](E);
        if (typeof r === 'number') r = { dur: r };
        end = r.dur;
        update = r.update || null;
      }
      if (entry.sparkle && !sparkleReplaced) end = Math.max(end, R[entry.sparkle](E));
      end = Math.max(end, layerEnd);

      var voice = {
        id: nextVoiceId++, event: name, priority: entry.priority, band: entry.band, start: now,
        endsAt: now + (entry.loop ? entry.duration : Math.max(end, 0.05)) + 0.02,
        gain: g, nodes: E.nodes, update: update, pitch: pitch, synth: !usedFile, loop: entry.loop
      };
      voices.push(voice);
      if (entry.loop) loops[name] = voice;
      if (entry.duck) triggerDuck();
      return { id: voice.id, event: name, sound: entry.sound, synth: voice.synth, pitch: pitch, duration: end };
    }

    // ---- ducking

    function updateDuck(dt) {
      var left = dt;
      if (duck.timer > 0) {
        var used = Math.min(duck.timer, left);
        duck.timer -= used;
        left -= used;
      }
      if (duck.timer <= 0 && left > 0 && duck.level < 1) {
        duck.level = Math.min(1, duck.level + (left / DUCK_RELEASE) * (1 - DUCK_GAIN));
        nodes.duck.gain.setTargetAtTime(duck.level, ctx.currentTime, 0.015);
      }
    }

    // ---- music

    function musicEnv(L, t, keep) {
      return { ctx: ctx, out: L.gain, t0: t, pitch: 1, rand: rand, noise: noiseBuf, nodes: keep ? L.nodes : [], dur: 0, opts: {} };
    }

    function activateLayer(name, now) {
      var L = layers[name];
      var def = map.music.layers[name] || {};
      L.active = true;
      L.stopAt = null;
      var buf = usableBuffer(def.file);
      if (buf) {
        var s = ctx.createBufferSource();
        s.buffer = buf;
        s.loop = true;
        s.connect(L.gain);
        s.start(now);
        L.nodes = [s];
        L.mode = 'file';
      } else {
        L.mode = 'synth';
        L.nodes = [];
        if (M[name] && M[name].start) M[name].start(musicEnv(L, now + 0.02, true), L);
      }
    }

    function upgradeLayers() {   // a long track may still be decoding when its mood starts: swap the stand-in synth for the file as soon as it is there
      if (!built || !unlocked) return;
      var swapped = false;
      LAYER_NAMES.forEach(function (name) {
        var L = layers[name], def = map.music.layers[name] || {};
        if (L.active && L.mode === 'synth' && usableBuffer(def.file)) { deactivateLayer(L); swapped = true; }
      });
      if (swapped) applyMusic(map.music.crossfadeSeconds);
    }

    function deactivateLayer(L) {
      stopNodes(L.nodes, ctx.currentTime);
      L.nodes = [];
      L.active = false;
      L.mode = null;
      L.stopAt = null;
    }

    function applyMusic(ramp) {
      if (!unlocked || !musicState.mood) return;
      var now = ctx.currentTime;
      var mood = map.music.moods[musicState.mood];
      var t = musicState.tension;
      LAYER_NAMES.forEach(function (name) {
        var L = layers[name];
        var target = isNum(mood[name]) ? mood[name] : 0;
        if (mood.battle) {
          if (name === 'tension') target = Math.max(target, t * 0.9);
          if (name === 'rhythm') target = Math.max(target, 0.6 + 0.4 * t);
        }
        target = clamp(target, 0, 1);
        L.target = target;
        if (target > 0.001) {
          if (!L.active) activateLayer(name, now);
          L.stopAt = null;
        } else if (L.active) {
          L.stopAt = now + ramp + 0.1;
        }
        rampParam(L.gain.gain, target, ramp, now);
      });
    }

    function updateMusic(now) {
      var anySynth = false;
      LAYER_NAMES.forEach(function (name) {
        var L = layers[name];
        if (L.active && L.stopAt !== null && now >= L.stopAt) deactivateLayer(L);
        if (L.active && L.mode === 'synth' && M[name] && M[name].step) anySynth = true;
      });
      if (!anySynth) {
        seq.nextTime = null;
        return;
      }
      var eighth = 60 / map.music.bpm / 2;
      if (seq.nextTime === null || seq.nextTime < now - 1) seq.nextTime = now + 0.05;
      var guard = 0;
      while (seq.nextTime < now + LOOKAHEAD && guard++ < 16) {
        for (var i = 0; i < LAYER_NAMES.length; i++) {
          var name = LAYER_NAMES[i];
          var L = layers[name];
          if (L.active && L.mode === 'synth' && M[name] && M[name].step) {
            M[name].step(musicEnv(L, seq.nextTime, false), seq.step);
          }
        }
        seq.step = (seq.step + 1) % 64;
        seq.nextTime += eighth;
      }
    }

    // ---- public API

    function unlock() {
      try {
        if (unlocked) return Promise.resolve(true);
        if (!getCtx()) {
          warnOnce('no-ctx', 'no AudioContext available, audio disabled');
          return Promise.resolve(false);
        }
        if (!built) buildGraph();
        unlocked = true;
        applyVolumes(false);
        preload();
        applyMusic(map.music.crossfadeSeconds);
        var p = typeof ctx.resume === 'function' ? ctx.resume() : null;
        return Promise.resolve(p).then(function () { return true; }, function (e) {
          fail('resume', e);
          unlocked = false;
          return false;
        });
      } catch (e) {
        fail('unlock', e);
        return Promise.resolve(false);
      }
    }

    function play(name, opts) {
      try {
        return playInner(name, opts);
      } catch (e) {
        fail('play ' + String(name), e);
        return null;
      }
    }

    function stop(name, fade) {
      try {
        if (!unlocked) return 0;
        var list = voices.filter(function (v) { return v.event === name; });
        list.forEach(function (v) { stopVoice(v, fade); });
        return list.length;
      } catch (e) {
        fail('stop', e);
        return 0;
      }
    }

    function playMusic(mood) {
      try {
        if (typeof mood !== 'string' || !has(map.music.moods, mood)) {
          warnOnce('mood:' + String(mood), 'unknown mood ' + String(mood));
          return false;
        }
        musicState.mood = mood;
        applyMusic(map.music.crossfadeSeconds);
        return true;
      } catch (e) {
        fail('playMusic', e);
        return false;
      }
    }

    function setTension(x) {
      try {
        if (!isNum(x)) return musicState.tension;
        var t = clamp(x, 0, 1);
        if (t === musicState.tension) return t;   // calling every frame must not restart the ramp
        musicState.tension = t;
        applyMusic(map.music.tensionRampSeconds);
        return musicState.tension;
      } catch (e) {
        fail('setTension', e);
        return musicState.tension;
      }
    }

    function setVolumes(v) {
      try {
        if (v && typeof v === 'object') {
          ['master', 'music', 'sfx'].forEach(function (k) {
            if (isNum(v[k])) volumes[k] = clamp(v[k], 0, 1);
          });
        }
        applyVolumes(false);
      } catch (e) {
        fail('setVolumes', e);
      }
      return { master: volumes.master, music: volumes.music, sfx: volumes.sfx };
    }

    function mute(b) {
      try {
        muted = !!b;
        applyVolumes(false);
      } catch (e) {
        fail('mute', e);
      }
      return muted;
    }

    function update(dt) {
      try {
        if (!unlocked) return;
        var d = isNum(dt) && dt > 0 ? Math.min(dt, 1) : 0;
        var now = ctx.currentTime;
        prune(now);
        updateDuck(d);
        updateMusic(now);
      } catch (e) {
        fail('update', e);
      }
    }

    function ready() {
      return readyPromise || Promise.resolve();
    }

    function getState() {
      return {
        unlocked: unlocked,
        muted: muted,
        volumes: { master: volumes.master, music: volumes.music, sfx: volumes.sfx },
        mood: musicState.mood,
        tension: musicState.tension,
        duck: duck.level,
        errors: errors,
        voiceCount: voices.length,
        voices: voices.map(function (v) {
          return { id: v.id, event: v.event, priority: v.priority, band: v.band, pitch: v.pitch, synth: v.synth };
        }),
        layers: LAYER_NAMES.map(function (n) {
          var L = layers[n];
          return L ? { name: n, active: L.active, mode: L.mode, target: L.target } : { name: n, active: false, mode: null, target: 0 };
        }),
        gains: built ? {
          master: nodes.master.gain.value,
          sfx: nodes.sfx.gain.value,
          music: nodes.music.gain.value,
          duck: nodes.duck.gain.value
        } : null
      };
    }

    return {
      unlock: unlock,
      play: play,
      stop: stop,
      playMusic: playMusic,
      setTension: setTension,
      setVolumes: setVolumes,
      mute: mute,
      update: update,
      preload: preload,
      ready: ready,
      getState: getState,
      eventNames: function () { return Object.keys(map.events); }
    };
  }

  return {
    createAudio: createAudio,
    DEFAULT_EVENT_MAP: DEFAULT_EVENT_MAP,
    RECIPE_NAMES: RECIPE_NAMES,
    LAYER_NAMES: LAYER_NAMES,
    BANDS: BANDS,
    MAX_VOICES: MAX_VOICES,
    BAND_CAP: BAND_CAP,
    PITCH_LIMIT: PITCH_LIMIT,
    MUSIC_TRIM: MUSIC_TRIM,
    DUCK_GAIN: DUCK_GAIN,
    DUCK_HOLD: DUCK_HOLD,
    DUCK_RELEASE: DUCK_RELEASE
  };
});
