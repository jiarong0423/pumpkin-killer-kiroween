# UI polish: design

Approach: the canvas keeps its 1920 x 1080 coordinate space. A single helper `uiScale()` returns `max(1, 0.55 / displayScale)` for text and bars (R1.1, R1.2); every `ctx.font` size for UI text goes through `fs(px)`. Plates become a function `drawPlate(side)` that draws the avatar (cached `Image`), name, HP number, bar and status chips; the old plate drawing code is removed, not left beside it.

Selection screen: the card template already builds avatar, role, bars and chips in `buildStartScreen()`; this spec adds the compact layout (card height at most 200 px, blurb hidden, tooltip), the `off` state for a failed avatar, and the responsive grid (4 columns, 2 columns under 600 px).

Wind arrow: drawn beside `images.wind_ghost` with `effWind()`; the sign is shown from the left side's view (positive blows toward the right side = tailwind for the left).

Preload: the start button waits on `heroImagesReady(picked)`, `sceneReady(picked)`, `uiReady()`; `loadRestInBackground()` loads the remaining pose sets with `requestIdleCallback` or a 1 s timer.

Out of scope: seat assignment and symmetric skills (spec `seats-and-items`), new art.
