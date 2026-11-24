# Requirements — asset candidate sheet

## Introduction

`docs/asset_candidates.md` is the single honest list of third-party art that
could serve as placeholder or style reference for Pumpkin Killer, with what
each license really allows. Final art comes from the owner's Colab generation.
This spec says how the sheet is kept current. The sheet is the deliverable.

## Requirements

### Requirement 1 — One sheet, honest licenses

**User story:** As the owner, I want one table of candidates and their
licenses, so the Devpost write-up never claims more than we have rights to.

**Acceptance criteria**

1. THE SYSTEM SHALL provide `docs/asset_candidates.md` with a candidate table
   (name, URL, contents, license as stated, verified, risk, allowed use).
2. THE SYSTEM SHALL set `verified` to "NO - snippet only" for any entry whose
   license has not been read on the asset's own page.
3. IF a license is not known, THEN THE SYSTEM SHALL write "unknown" and SHALL
   NOT invent license text.
4. IF a license cannot be shown, THEN THE SYSTEM SHALL set the allowed use to
   "do not use".

### Requirement 2 — Needs mapping

**User story:** As the owner, I want to see which needs a candidate could
cover, so I know what must come from Colab.

**Acceptance criteria**

1. THE SYSTEM SHALL provide a table of the four classes (skeleton, bat,
   knight/guard, pumpkin wizard) against body, thrown item, hit pose, portrait
   and projectile.
2. WHERE no candidate covers a cell, THE SYSTEM SHALL write "none".
3. WHERE a candidate is pixel art, THE SYSTEM SHALL note that it clashes with
   the mockup style.

### Requirement 3 — Verification before use

**Acceptance criteria**

1. THE SYSTEM SHALL describe a 5-step license check ending with a record in
   `(not published)`.
2. WHEN a candidate is verified, THE SYSTEM SHALL update its `verified` cell
   with the date and the record file name.
3. THE SYSTEM SHALL NOT allow GPL or other copyleft material into the repo.

### Requirement 4 — Write-up wording

**Acceptance criteria**

1. THE SYSTEM SHALL provide three plain write-up sentences that remain true if
   no candidate is used.
2. WHEN a candidate is adopted, THE SYSTEM SHALL list it with source and
   license in the write-up.

### Requirement 5 — Scope limits

**Acceptance criteria**

1. THE SYSTEM SHALL NOT create, download or copy any image.
2. THE SYSTEM SHALL NOT edit `index.html`, `assets/`, `scripts/` or `js/`.
3. THE SYSTEM SHALL NOT run git commands.
