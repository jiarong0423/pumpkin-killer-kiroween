# UI settings requirements

Scope: settings UI, preference persistence, `index.html`, the two language dictionaries, and layout evidence. The current game controls and rules are out of scope.

- **US-01 Settings entry:** When a player taps the gear button, the page shall open one settings sheet; when the player taps outside that sheet or presses Escape, the page shall close it.
- **US-02 Placement:** While a match is running, the page shall position the settings sheet so it does not cover the countdown board or bottom dock.
- **US-03 Phone targets:** When the input device has no hover capability, each settings control shall provide a target at least 44 by 44 CSS pixels; the sheet shall fit a 392 px-high landscape viewport.
- **US-04 Effects sound:** When the player changes effects sound on/off or volume, the page shall update the effects-audio gain without changing game rules.
- **US-05 Music:** When the player changes music volume, the page shall update music gain without changing effects-audio gain.
- **US-06 Reduced motion:** When the player enables reduced motion, the page shall suppress screen shake and hit flashes, and shall limit emitted particles to small bursts while preserving playable input and turn resolution.
- **US-07 Language:** When the player selects a language, the page shall apply that language to the page and rebuild dynamic start-screen controls.
- **US-08 AI level:** Before a match starts, when the player selects a built-in AI level, the page shall use the existing level multiplier and show the selected level.
- **US-09 Persistence:** When browser storage is available, the page shall restore effects sound, effects volume, music volume, reduced motion, language, and AI level after reload; when storage is blocked or throws, the page shall continue with defaults.
- **US-10 Translations:** The page shall obtain every new visible string and accessibility label from literal keys present in both language dictionaries; English values shall contain no CJK except the existing language-switch keys.
- **US-11 Evidence:** For 200 seeded landscape viewports from 560–1000 px wide, 320–480 px high, and DPR 1.5–3, the measured stage shall fit the viewport, HUD rectangles shall not intersect, and the settings sheet shall fit.
