# Colab run order for `colab/ui_jobs_kiro.json` (Kiro task 26)

39 jobs, tier `U2`. Time uses 2 minutes per image and 2 variants per job (`VARIANTS = 2`), so 78 images and 156 minutes (2 h 36 min) for everything. Model load time and reruns are not counted. A 20 percent rerun allowance adds about 30 minutes.
Run one phase, look at the results with `docs/art_prompt_guide.md` section d, fix prompts, then run the next phase. Set `ONLY` to the ids of the phase.

| Phase | Why this order | Job ids | Jobs | Images (2 variants) | Minutes |
|---|---|---|---|---|---|
| 1. First look | Biggest change on screen: dock frame and button plates, top team plates, lock button, fence, lead portrait. Gate: if these look wrong, change the style string before spending more time. | `ui_dock_frame`, `ui_plate_normal`, `ui_plate_active`, `env_fence_intact`, `ui_top_plate_left`, `ui_top_plate_right`, `ui_lock_plate`, `portrait_wizard` | 8 | 16 | 32 |
| 2. Finish the dock | Completes the button states, icons and hero chips so the dock can switch from CSS to art in one go. | `ui_plate_hover`, `ui_plate_disabled`, `ui_icon_normal`, `ui_icon_double`, `ui_icon_heavy`, `ui_icon_heal`, `ui_hero_chip_normal`, `ui_hero_chip_active` | 8 | 16 | 32 |
| 3. Finish the top HUD and fence | Rest of the top bar and the two fence damage states. | `ui_top_center_plate`, `ui_hp_frame`, `ui_hp_fill`, `ui_wind_frame`, `ui_wind_arrow`, `env_fence_damaged`, `env_fence_broken` | 7 | 14 | 28 |
| 4. Portraits and cut-ins | Throw drama in the dock. Wizard cut-ins first, then the other three classes. | `portrait_cutin_wizard_charge`, `portrait_cutin_wizard_shout`, `portrait_cutin_wizard_hit`, `portrait_skeleton`, `portrait_bat`, `portrait_knight` | 6 | 12 | 24 |
| 5. Atmosphere and small parts | Small on screen, so they matter least. | `ui_ghostfire_cyan`, `ui_ghostfire_violet`, `ui_candle`, `ui_power_unlit`, `ui_power_orange`, `ui_power_hot`, `ui_socket_ammo`, `ui_socket_special` | 8 | 16 | 32 |
| 6. Round buttons | Last, 44 px each on screen. | `ui_btn_sound`, `ui_btn_reset` | 2 | 4 | 8 |
| Total | | | 39 | 78 | 156 |

## If only 8 images

Run these 8 jobs with `VARIANTS = 1`: 8 images, about 16 minutes. With 2 variants it is 16 images and 32 minutes (this is phase 1).

1. `ui_dock_frame`
2. `ui_plate_normal`
3. `ui_plate_active`
4. `env_fence_intact`
5. `ui_top_plate_left`
6. `ui_top_plate_right`
7. `ui_lock_plate`
8. `portrait_wizard`

Why these: the dock frame and the two plates give most of the "premium" look (as noted in `dock_asset_requests.md`). The icons stay as emoji until phase 2. The fence is the owner's explicit request and is on screen all the time. The two team plates and the lock plate are the largest top and bottom objects after the dock frame.

## Changes the Colab cell needs (not made here, `colab/pumpkin_assets_job.py` was not touched)

1. Upload `ui_jobs_kiro.json` to `MyDrive/PumpkinKiller/inputs/` and load it instead of `jobs.json` (the script reads `{IN_DIR}/jobs.json`).
2. Set `TIERS = ["U2"]`, or use `ONLY = [...]` with the ids of a phase.
3. Use a new `TAG` (or delete the old U1 outputs). The U1 jobs have the same ids, and the script skips any output file that already exists.
4. Optional: pass `negative_prompt=j.get("negative", " ")` instead of `" "`. Every job has a `negative` string. Whether it improves results is untested.
5. After generating, crop each result to the object (the canvas is always 1024 x 1024) and chroma-key `#FF00FF`.

## Riskiest prompts

| Job | Risk |
|---|---|
| `env_fence_intact`, `_damaged`, `_broken` | Tall narrow object from a wide reference. May come out wide, may lose the "black", and the damage states may not keep the same footprint. Fallback in the guide (section e). |
| `ui_icon_normal`, `ui_icon_double`, `ui_icon_heavy` | Wizard reference can leak the character or hat into an icon. |
| `ui_top_plate_left`, `ui_top_plate_right`, `ui_hp_frame`, `ui_wind_frame` | Counts (ten runes, seven ticks, three rivets per cap) and a truly empty centre. |
| `ui_socket_special` | Twelve dashed runes in a ring, no gold, violet must not turn pink. |
| `ui_ghostfire_cyan`, `ui_ghostfire_violet` | Opaque flames with matching end heights for tiling. Models like soft translucent haze, which breaks the key. |
| `portrait_*` and wizard cut-ins | Reference faces left, prompt asks for right. Expression changes may alter the hat or face design. |
| `ui_btn_sound`, `ui_btn_reset` | Small carved icons: the speaker or arrow shape may be wrong, and the model may add text or notes. |
