# Design — Layered Character Rig

## Overview

`(not published)` is a pure function library that turns a JSON rig document plus a
`(state, t)` pair into a list of drawable layers. It carries no rendering code:
the browser renderer reads the layer list and draws images / procedural limbs
itself. This keeps the motion data testable under Node.

## Coordinate system

- Art box is 1024px square. All positions are **art fractions** (0..1) of that box.
- **Forward = -x** (the art faces left; the renderer mirrors per facing).
- Rotations are in **degrees**.
- `t` is **normalized 0..1** within a state. This matches `index.html`, where
  `animProgress += dt / dur` for `throw`/`hit`, and `charge` uses `t/0.25`
  (equivalent to normalized progress over its 0.25s duration).
- Body pose offsets were authored in **pixels at a 220px box** (`poseUnitPx`).
  `evalRig` converts a forward-positive pixel shift to `x` by `-(px / 220)`
  (forward = -x), and a vertical pixel value to `y` by `px / 220`.

## Rig document schema

```
Rig := {
  name: string,
  box: number,              // art box px (1024)
  poseUnitPx: number,       // px unit the pose offsets use (220)
  anchors: { [name]: { x, y } },        // static art-fraction points
  layers: Layer[],
  states: { [name]: State } // must include idle, charge, throw, hit
}

Layer := {
  id: string,
  kind: "image" | "limb" | "weapon",
  z: number,                // draw order, ascending = back to front
  image?: string,           // image key (image/weapon layers)
  from?: string, to?: string // anchor names (limb layers)
}

State := {
  duration: number,         // seconds
  tracks: { [layerId]: Track },
  events?: { [name]: number } // normalized times, e.g. { release: 0.36 }
}

Track := {
  x?, y?, rot?, sx?, sy?, alpha?: Keyframe[], // numeric channels
  visible?: { t: number, value: boolean }[]   // step channel
}

Keyframe := { t: number, v: number, ease?: string, k?: number, w?: number, base?: number }
```

## Channels and easings

- Numeric channels are keyframe arrays. The `ease` on a keyframe governs the
  segment **ending** at that keyframe; the default is `linear`.
- `visible` is a step function: the last keyframe with `t <= query` wins.
- Easings: `linear`, `easeOutCubic`, `easeInOutCubic`, and `spring`.
- `spring(q) = exp(-k*q) * cos(w*q)`. A spring keyframe is interpreted as a
  decaying oscillation toward `base` (default 0): the sampled value is
  `base + (v - base) * spring(local)`, where `local` is the segment-local
  normalized time. This reproduces both the throw follow-through
  (`LUNGE * exp(-4.2 q) * cos(5.5 q)`) and the hit impulse
  (`exp(-5 t) * cos(9 t)` with `w=9`, and the pure decays with `w=0`).

## Why layers, not frames

Each state assigns tracks to layers independently, so the weapon can disappear
mid-swing (`visible` steps to false at the release keyframe) while the body and
arm keep moving. This is the Ragnarok-style "weapon leaves the hand" handoff,
done with data rather than a code branch. The skeleton's spear sits at `z = -10`
(behind the `body` at `z = 0`); the arm is at `z = 10` (front). The bat's dagger
rides in front (`z = 5`).

## API

- `validateRig(rig) -> { ok, errors[] }` — schema, unknown references, missing
  states, bad numbers.
- `evalRig(rig, state, t) -> { layers[], anchors{}, events{} }` — per-frame
  layer transforms (sorted by z), resolved anchors, and boolean events.
- `releaseTime(rig, state) -> number | null` — the `release` event time.
- `muzzle(rig, state, t) -> { x, y } | null` — the `projectile` anchor.

## Testing strategy

`(not published)` uses only Node's `assert`. It validates both shipped rigs,
feeds broken copies to prove validation fails, walks every state at 1/60 steps to
assert determinism and continuity, confirms weapon handoff at release, checks the
required anchors and z-order, and spot-checks that the release pose equals LUNGE
and the hit peak equals the source impulse.
