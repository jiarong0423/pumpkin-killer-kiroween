# UI settings design

A single `#settings-sheet` dialog is opened by `#settings-btn`. It sits in the upper-left safe area while the match is active, leaving the centre countdown board and bottom dock visible. A transparent `#settings-backdrop` receives outside taps. Escape closes the sheet.

`settingsState` uses guarded `readSettings()` and `saveSettings()` helpers. Defaults are effects on at volume 1, music volume 0.7, reduced motion off, and the existing normal AI level. The page persists only preferences, never match state.

The sound toggle remains a quick effects-mute control. The sheet exposes effects mute and volume, music volume, reduced motion, language, and the built-in AI level. `applySettings()` updates GameAudio and AmbientSfx when they exist. Existing no-hover touch rules provide 44 px targets. The sheet uses the established deep blue-violet, pumpkin-orange, ghost-cyan, and gold palette.

`reduceMotionEnabled()` gates shake, hit-flash drawing, and particle emission. It also asks `WeatherFx` for low quality. Effects retain small feedback bursts and never alter collision, timing, damage, or input.
