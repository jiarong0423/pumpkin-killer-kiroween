#!/bin/bash
# Stage the combined 2026-11-15 art queue and its reference pictures into the Drive inputs folder as NEW files (never overwrites).
# Run it in the user's own terminal: the sandbox cannot write to Google Drive.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DST="${PK_DRIVE_INPUTS_DIR:-}"   # the Drive "PumpkinKiller/inputs" folder; set it in your own shell
[ -n "$DST" ] && [ -d "$DST" ] || { echo "ERROR Drive folder not found: $DST" >&2; exit 1; }
rc=0
for rel in assets/env/bg_graveyard.png assets/units/unit_knight.png assets/units/unit_skeleton.png assets/units/unit_wizard.png docs/ref/concept_mockup.png; do
  [ -f "$ROOT/$rel" ] || { echo "ERROR missing $ROOT/$rel" >&2; rc=1; continue; }
  mkdir -p "$DST/$(dirname "$rel")" || { rc=1; continue; }
  if [ -f "$DST/$rel" ]; then echo "SKIP exists $rel"; else cp "$ROOT/$rel" "$DST/$rel" && echo "OK $rel"; fi
done
SRC="${PK_QUEUE_FILE:-$ROOT/colab/jobs_queue_all_20261115.json}"
cp "$SRC" "$DST/${PK_QUEUE_NAME:-jobs_queue_all.json}" || { echo "ERROR copy queue failed" >&2; exit 1; }
[ "$(shasum -a 256 < "$SRC")" = "$(shasum -a 256 < "$DST/${PK_QUEUE_NAME:-jobs_queue_all.json}")" ] && echo "OK jobs_queue_all.json checksum matches" || { echo "ERROR checksum differs" >&2; rc=1; }
exit $rc
