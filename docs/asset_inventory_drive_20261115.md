# Asset inventory: Colab output folder on Drive vs this repository (2026-11-15)

Made by the main line (read-only listing; no file was copied, moved or deleted). The Drive folder is the owner's `PumpkinKiller/out`.

- Files in the Drive output folder: 253 (253 PNG). Newest file: 2026-11-09 20:46.
- So the Colab runs planned for the night of 2026-11-10 (wind-ghost star frames, pumpkin coin, feet chain) produced NO new files: nothing newer than 2026-11-09 evening exists.

## PNG count by first word of the file name

| prefix | files |
|---|---:|
| pose | 38 |
| ui | 38 |
| fx | 28 |
| bat | 24 |
| skeleton | 18 |
| reaper | 17 |
| knight | 16 |
| portrait | 14 |
| hunchback | 12 |
| necro2 | 8 |
| shield | 8 |
| wizard | 8 |
| necro3 | 6 |
| necro | 4 |
| drop | 3 |
| env | 3 |
| necro4 | 3 |
| bride | 2 |
| ghostc2 | 1 |
| ghostc3 | 1 |
| ghostc4 | 1 |

## Wanted but missing in the page (from `scripts/release/check_asset_refs.py`) and where they exist

| name part | files on Drive | files in `assets/` |
|---|---:|---:|
| `fx_feet_chain` | 0 | 0 |
| `bg_belltower` | 0 | 0 |
| `bg_pumpkin_field` | 0 | 0 |
| `unit_knight_unarmed` | 0 | 0 |
| `ghoststar_blow` | 0 | 0 |
| `ghoststar_blow_hard` | 0 | 0 |
| `coin` | 0 | 0 |
| `move_step` | 0 | 0 |
| `item_pickup` | 0 | 0 |

## Reading
- Anything with 0 on both sides still has to be generated (Colab/Qwen, owner) or the reference dropped in code.
- Drive holds many variants (`v1`, `v2`) and intermediate sheets; most of them are not meant to be in `assets/`. A stem that is not under `assets/` is not a gap by itself.
- Not checked: image quality, licence of each picture (see `docs/ASSET_PROVENANCE.md`).
