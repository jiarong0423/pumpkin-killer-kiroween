# Apple Hag Colab run sheet — 2026-11-15

1. Copy `colab/jobs_apple_hag_20261115.json` to the Drive inputs folder as a new queue; do not overwrite `jobs.json`.
2. Stage its existing references: `assets/units/unit_wizard.png`, `assets/weapons/dart.png`, `assets/fx/sprites/fx_poison_bubbles.png`, and `assets/fx/sprites/fx_heal_rain_drop.png`.
3. Run Stage 1 first with `TIERS = ["Q3"]` and `VARIANTS = 1`: `hag_idle1` and `hag_front`.
4. The owner picks the best `hag_idle1` output, stages it as `hag_idle1_v1_hag1.png`, and uses it as the `out:` identity reference.
5. Run Stage 2 next: `hag_idle2`, `hag_charge1`, `hag_charge2`, `hag_charge3`, `hag_release`, `hag_empty`, and `hag_hit`.
6. Run Stage 3 after that: `proj_poison_apple`, both apple-rain sheets, `fx_black_smoke`, and `ui_bitten_apple`.
7. Expect 14 pictures at about 7 minutes each, roughly 98 minutes before owner selection and review.
8. Reject any image that resembles a known cartoon witch. The hag must remain an original black-witch-hatted, purple-edged, pumpkin-basket character.
9. For every pose, check the same face, scale, full-body proportion, LEFT action direction, throwing hand, and feet baseline against selected idle1.
10. Check every sprite has a clean #FF00FF background, no text, no extra limbs or characters, no red/carved/jack-o'-lantern apple, no blue cloak, and no white hair.
11. Check poison effects use plain green apples with black smoke. Check the healing sheet has soft light-green glow and no smoke.
12. After review, download approved outputs and key them with the appropriate existing asset-ingest process; do not hand-edit generated art.
13. Ask the main line to add reviewed destination mappings before installing any new queue IDs, then run its chosen asset and pose checks.
14. Record each actual Colab run and verdict in `docs/PROMPT_LOG.md`.

(2026-11-15 owner: only the HOOD is replaced by a pointed witch hat; hunched, underhand scooping lob, broken-down hand. Stage 1 jobs are now hag_idle1_r2 and hag_front_r2.)
