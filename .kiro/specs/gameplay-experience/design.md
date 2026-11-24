# Gameplay experience: design

Reasoning, tables and open questions: `docs/experience_design.md`. This file is the build plan.
Nothing here edits `index.html`, `assets/`, `scripts/` or `js/` yet. The main line decides the order after the owner approves.

## Modules

| Module | Role | I/O |
|---|---|---|
| `(not published)` (new) | The budget numbers from R1 and R2 as one frozen object `FX_BUDGET`. | none |
| `(not published)` (new) | `createDirector({seed, reducedEffects, canvasWidth, hudRects})` returns `plan(event, state)` and `tick(dtMs, liveCount)`. Pure and DOM-free, same Node/browser wrapper as `particles.js`. | none |
| `js/particles.js` (extend) | New presets only (list below). Existing presets stay unchanged. | none |
| `(not published)` (new) | Applies a plan's reactions: hit-stop timer, shake offset, flash alpha, slow motion factor. Pure state machine, `step(dtMs)` returns `{timeScale, shakeX, shakeY, flashAlpha}`. | none |
| `(not published)` (new) | Keeps the last 4 landings and builds the "short N / long N" tag from public history rows. | none |
| `(not published)` (new) | State machine for the 3 hints (R7). | none |
| `index.html` (later, main line) | Wiring only: call the director on game events, draw plans, draw plates and pillars, play sounds. | DOM, canvas, audio |

The director only ever receives events the MCP history or the game loop already exposes, so it cannot read hidden state.

## Event shape

```js
// event
{ type: 'charge'|'release'|'flight'|'hit'|'block'|'ground'|'fence'|'ko'|
        'poison_applied'|'poison_tick'|'shield_placed'|'shield_expired'|
        'ultimate_ready'|'ultimate_used'|'pip'|'round_start'|'round_end'|'game_over',
  team: 'player'|'agent', cls: 'skeleton'|'bat'|'wizard'|'knight',
  x: number, y: number, dirX: -1|1, power?: number, damage?: number }
```

## Plan shape

```js
{ calls: [{ preset, x, y, opts, delayMs }],
  screen: { hitStopMs, shakePx, shakeMs, flashAlpha, flashMs, slowMo },
  texts: [{ text, x, y, color }],
  pillar?: { x, y, team } }
```

`plan` also returns the particle total, so tests can sum it (R1.5).

## Budget enforcement

1. `plan` computes the planned total. If `liveCount + total` is over the soft budget (300, or 450 while an ultimate is flagged), it halves `scale` on the lowest-priority calls first, then drops them in the R4.4 order.
2. `tick` tracks one-shot starts in a rolling 1000 ms window (R1.4). Over the limit, the lowest priority one-shot is dropped.
3. Reduced effects: counts are halved with `Math.ceil`, screen reactions are zeroed.
4. Emit points are clipped against `hudRects`. A point inside a rectangle moves to the nearest edge outside it. `pip_pop` is exempt.

Priority (high to low): impact core, damage number, KO wisps, block flash, hit sparks, ricochet sparks, landing ring, shock rings, smoke and dust, trail stardust, wind motes, ambient.

## New presets in `js/particles.js`

| Preset | Look | Count at scale 1.25 | Notes |
|---|---|---|---|
| `weapon_trail_shuriken` | cyan-violet motes plus small spinning squares | 1-2 per call | replaces `weapon_trail_dart` for the cat |
| `shock_ring` | one expanding ring, `opts.color` | 1 | also used for KO and block |
| `landing_pillar` | 6 rising ghost-fire motes at emit. The pillar line itself is drawn by the UI from `landing_memory`. | 6 | |
| `ash_fall` | grey-violet flakes drifting down | 10 | KO |
| `shield_dissolve` | the bar breaks into rising cyan motes | 8 | |
| `ultimate_ready_pulse` | gold-violet column pulse at the feet | 6 | called every 1500 ms |
| `pip_pop` | one small ring and 3 sparks | 4 | |
| `wind_motes` | faint dust and sparks drifting with `opts.wind` | 1 per call | called every 250 ms |
| `turn_marker_wisp` | small cyan flame circling the active unit's feet | 1 per call | called every 300 ms |
| `banner_embers` | embers rising off the round banner | 10 | |

All of them follow the existing preset contract: any `opts` (missing, null, non-finite) emits at least one particle, no `Math.random`, no I/O.

## Weapon effects vs micro-motions

Weapon effects go through the director and count toward the budget. Face and body micro-motions (breathing bob, cape sway, hit nudge, white hit tint, poison tint) are sprite transforms in the renderer. They cost no particles and are not in the director, except `face_glow_*` which stay ambient.

## Testing

- `(not published)`: property tests with at least 200 seeded cases: totals, determinism, order of dropping, HUD clipping, reduced effects.
- `(not published)`: hit-stop, shake, flash, slow-mo limits.
- `(not published)`: last 4 landings, alpha table, short/long tag.
- `(not published)`: hint order and the local flag.
- Stress scenario: a scripted 60 s match with all events at their maximum rate. Record the peak live count and assert R1.1 and R1.2 without the hard cap ever being hit.
- Everything visual or audible is checked by a human with the checklist in `tasks.md` (marked unverified until then).
