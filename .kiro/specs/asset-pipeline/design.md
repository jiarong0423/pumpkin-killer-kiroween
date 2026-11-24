# Asset pipeline: design

## Inputs and outputs

`shared/heroes.json` is the canonical hero list. `index.html` contains both `imgList`, which resolves named images to files, and `POSE_SETS`, which maps a unit key to animation image keys. The checker parses both structures without importing page code. It scans literal `assets/` paths in the page, JavaScript, CSS, and service worker.

The checker produces three forms of output:

- Human output has one actionable `ERROR <path> <rule>` line per problem and a final summary.
- `--json` returns the same result as structured data for scripts.
- `--manifest` serializes per-hero required image records and every managed picture record into `docs/ASSET_MANIFEST.json`. `--manifest --check` compares generated content without writing it and exits 3 when it is stale.

Every command appends a short result line to `(not published)`. The normal command returns 1 if acceptance errors exist. A stale manifest returns 3 in check mode, provided the asset checks themselves have no errors.

## Requirement resolution

For a hero id, the required paths are:

| Role | Resolution |
|---|---|
| Avatar | `(not published)` |
| Front portrait | `DOCK_PORTRAIT.<hero>` |
| Unit | `imgList.unit_<hero>` |
| Windup, release, hit | `POSE_SETS.unit_<hero>` then the matching `imgList` entry |

This allows the current page to keep its intentional legacy aliases, such as the Bat's dock portrait at `assets/ui/portrait_bat.png`, the Necromancer's `unit_reaper` art, or the Skeleton's `skel_*` pose keys. Missing map entries and unresolved paths are blocking errors rather than guessed filenames.

## Image checks

The scanner examines raster files in the managed picture folders. Pillow verifies that each opens and both dimensions are at least 128 pixels. All checked pictures must use RGBA except scene backgrounds named `assets/env/bg_*.png` and raw unit sources named `assets/units/*_raw.png`, which may remain RGB source images. For opaque pixels only, it counts RGB values within Euclidean distance 60 of `#FF00FF`; a percentage above 10 is rejected. Avatar checks add the 256-square and transparent-corner constraints.

Filename validation is category-specific. Current filenames allowed by the page's legacy aliases pass the compatibility rule, while a new name outside the documented family is rejected. The manifest includes `legacy_name: true` where compatibility was used, making cleanup measurable rather than silently accepted.

## Invocation modes

`--path` resolves a supplied repository-relative or absolute PNG and runs only direct file checks. This keeps the save hook fast and prevents a save from restating unrelated backlog errors. `--hero` runs one complete hero requirement set plus its direct pictures. No selector runs all required hero checks, reference checks, and managed image checks.

The image-save hook uses Kiro's `"$KIRO_FILE"` variable. Its matcher limits it to managed PNG files; the command falls back to the whole repository check if that variable is unavailable.

## Limits

Pixel inspection cannot prove a character has one head, two arms, a complete composition, or a particular identity. Those are generation-prompt and visual-review acceptance rules. The checker proves file-level constraints only. It also cannot infer whether an existing avatar was generated or cropped; provenance remains in `docs/ASSET_PROVENANCE.md`.
