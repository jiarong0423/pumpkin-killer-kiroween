# Asset pipeline: requirements

Scope: generated and installed picture acceptance. Files: `.kiro/steering/art_pipeline.md`, this specification, `scripts/check_asset_pipeline.py`, its test, the generated manifest, and the image-save hook. The game page, styles, and translations are out of scope.

Terms: a **hero** is a key in `shared/heroes.json`. A **required pose** is that hero's `windup`, `release`, or `hit` entry in `POSE_SETS` in `index.html`. A **magenta-like pixel** is an opaque pixel whose RGB Euclidean distance from `#FF00FF` is at most 60.

## R1 Required hero picture set

1. Each hero shall have `(not published)`.
2. Each avatar shall be a 256 x 256 RGBA PNG, and each of its four corner pixels shall be transparent.
3. Each hero shall have a front portrait resolved from its `DOCK_PORTRAIT` entry in `index.html`.
4. Each hero shall have a unit image and the `windup`, `release`, and `hit` pose images resolved from its `POSE_SETS` entry in `index.html`.
5. A missing required hero image shall be reported as a blocking error. The output shall identify the hero, path, and missing role.

## R2 Picture acceptance

1. Every checked picture under `assets/avatars`, `assets/portraits`, `assets/poses`, `assets/units`, `assets/ui`, `assets/fx`, `assets/env`, and `assets/weapons` shall open through Pillow and be at least 128 pixels in both dimensions. It shall use RGBA mode except scene backgrounds named `assets/env/bg_*.png`, which may be RGB, and raw unit sources named `assets/units/*_raw.png`, which may be RGB.
2. A checked picture shall contain no more than 10 percent magenta-like opaque pixels.
3. Names shall follow the applicable rule in `art_pipeline.md`: avatars use `avatar_<hero>.png`; portraits use `<hero>_front.png`; unit pictures use `unit_<hero>[_<variant>].png`; pose images use a `pose_` prefix or a hero action name; effects use `fx_*.png`; and backgrounds use `bg_<scene>.png`.
4. Legacy picture names used by the current page shall remain accepted until replaced. Their use must be recorded in the generated manifest.

## R3 Referenced files

1. Every `assets/` path literally referenced by `index.html`, any file in `js/` or `css/`, or `sw.js` shall exist.
2. The checker shall inspect `POSE_SETS` using its image-key references rather than inferring filenames from hero names.
3. The checker shall read hero ids from `shared/heroes.json`.

## R4 Command interface and output

1. `python3 -B scripts/check_asset_pipeline.py` shall check the repository. `--hero <id>` shall check one hero requirement set and `--path <file>` shall check one picture for save hooks.
2. `--json` shall emit the complete machine-readable check result. `--manifest` shall write `docs/ASSET_MANIFEST.json`; `--manifest --check` shall return status 3 and report `ERROR docs/ASSET_MANIFEST.json manifest-stale` when the manifest differs from current required or managed picture data.
3. Human-readable checks shall print one `ERROR <path> <rule>` line for each problem, a summary, and exit 1 if any error was found.
4. Every invocation shall append a concise result to `(not published)`.

## R5 Manifest and hook

1. The generated manifest shall list each hero's resolved required files, dimensions, SHA-256 values, and per-hero check status. It shall also list every managed picture that was checked, so additions, removals, and changed file metadata make the manifest stale.
2. The manifest check shall fail when the checked data differs from the committed generated file.
3. A `PostFileSave` hook shall invoke the one-file check for saved PNG files in the managed image folders. If the hook cannot receive the saved filename, it shall run the repository check instead.

## R6 Verification

1. `scripts/test_asset_pipeline.py` shall construct accepted and rejected temporary fixtures with Pillow and assert the specific reported rules.
2. The task validation also runs `scripts/test_check_asset_refs.py` and `scripts/test_audio.js`.
