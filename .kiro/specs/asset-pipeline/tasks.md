# Asset pipeline: tasks

## Implementation

- [x] 1. Record always-on art acceptance and disclosure rules in `.kiro/steering/art_pipeline.md`.
- [x] 2. Specify required hero images, file acceptance, literal asset references, manifest, and hook behavior.
- [x] 3. Implement `scripts/check_asset_pipeline.py` with human, JSON, hero, path, manifest, and manifest-check modes.
- [x] 4. Add temporary-Pillow fixture tests for accepted, rejected, and stale-manifest cases.
- [x] 5. Generate `docs/ASSET_MANIFEST.json` from the repository state.
- [x] 6. Add the managed-PNG PostFileSave hook.

## Validation

- [ ] 7. Run the repository checker and record every error in `docs/kiro_180_result.md`.
- [ ] 8. Run `python3 -B scripts/test_asset_pipeline.py`.
- [ ] 9. Run `python3 -B scripts/test_check_asset_refs.py`.
- [ ] 10. Run `node scripts/test_audio.js`.
- [ ] 11. Main line reruns the checks and records its independent result in `docs/kiro_verified.json`.

## Visual acceptance owned by the main line and owner

- [ ] 12. Review every newly generated avatar for complete head margin, identity lock, and the required face and skin-colour rules before installing it.
- [ ] 13. Confirm the owner has recorded the Qwen-Image-Edit and Lightning LoRA licence terms in `docs/ASSET_PROVENANCE.md`.
