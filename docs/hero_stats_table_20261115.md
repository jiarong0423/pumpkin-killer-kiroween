# Hero stat table — 2026-11-15

Source: `js/class_stats.js` recommended `CLASSES`; range is full-power, 54°, no-wind landing distance, rounded to 0.1 px. Ultimate total excludes the normal triggering hit.

| id / hero | HP | defense | range px | attack | ultimate total | tune here |
|---|---:|---:|---:|---:|---:|---|
| skeleton / Skeleton Spearman | 100 | 0 | 1982.9 | 24 | 36.0 | `CLASSES.skeleton.attack` |
| wizard / Pumpkin Wizard | 85 | 0 | 2000.2 | 28 | 42.0 | `CLASSES.wizard.attack` |
| bat / Bat-cat Assassin | 90 | 0 | 1982.9 | 26 | 39.0 | `CLASSES.bat.attack` |
| knight / Pumpkin Guard | 120 | 0 | 1950.8 | 30 | 45.0 | `CLASSES.knight.attack` |
| bride / Ghost Bride | 75 | 0 | 1631.1 | 27 | 40.5 | `CLASSES.bride.attack` |
| hunchback / Bell-tower Hunchback | 130 | 0 | 1316.0 | 20 | 30.0 | `CLASSES.hunchback.attack` |
| reaper / Necromancer | 105 | 0 | 1982.9 | 23 | 45.0 (12.7 + 15.0 + 17.3) | `REAPER_FLAME_CONSTANTS.DAMAGE`, `NECRO_VOLLEY_SCALE` |
| hag / Apple Hag | — | — | — | — | — | not yet defined in `js/class_stats.js` |

Every `defense: 0` is a PROVISIONAL placeholder pending owner values. The current bride and hunchback balance values are provisional. Apple Hag has art prompts but no code-backed combat values, so this row is intentionally blank rather than invented. The Necromancer total is `23 × (1.1 + 1.3 + 1.5) × 0.5`, rounded per flame by `ultimate_fx.js`.
