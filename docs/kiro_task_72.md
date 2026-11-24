# Kiro task 72 — one overview diagram as SVG (documentation, NOT game art)

Owner 2026-11-10: turn the current assets and the progress table into a MODULAR overview picture, with each module marked by status like "done".

Read docs/asset_inventory.json (modules with status, folders with file counts, open art list). Use only that data; invent nothing.

Create ONLY: (not published) (one self-contained SVG, no external fonts or images, 1600x1000 viewBox, readable at 800 px wide, Traditional Chinese labels, dark background to match the game).
- One box per entry of "modules", grouped in 4 columns by theme (play rules, characters, screen UI, art and tools).
- Colour by status: done = green, built_unseen = amber, in_progress = blue, not_started = grey; a legend in a corner.
- Under the modules a strip "待出圖" listing the "open_art" items with their status.
- Header: project name, generated date from the JSON, the totals (folders, files).
- No decoration that looks like game art; plain boxes, lines and text only.
Then write (not published) (max 10 lines: what the SVG shows, what you could not verify). Do not edit any other file.
