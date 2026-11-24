# Design — asset candidate sheet

## Shape

A single Markdown file, `docs/asset_candidates.md`, with four sections:

1. Candidates table.
2. "What the game needs" table (class x item).
3. "How to verify a license before use" (5 steps).
4. "What the write-up may say" (3 sentences).

Evidence for verified licenses lives in `(not published)`, one file per
asset, holding the URL, the date, and the license text or a screenshot.

## Rules for editing the sheet

- `verified` has two states: "NO - snippet only" and "YES - YYYY-MM-DD,
  `(not published)`". Nothing in between.
- Risk is LOW, MEDIUM or HIGH with a one-line reason. A doubt raised by a third
  party (a comment, a mismatched tag) is at least MEDIUM.
- Copyleft (GPL and similar) and non-commercial licenses are HIGH and "do not
  use".
- Pixel-art candidates carry a style-clash note, because the target look is
  `(not published)`.
- The needs table only names a candidate if the candidate's description lists
  that item. Otherwise the cell is "none".

## Why a document and not code

The decision is a human judgment about licenses. A check script cannot read a
license for us, so the control is the verification procedure plus an evidence
file per adopted asset.
