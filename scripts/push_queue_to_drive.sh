#!/bin/bash
# Copy an art queue json into the Drive inputs folder as a NEW file (never overwrites jobs.json or anything else).
# Usage: bash scripts/push_queue_to_drive.sh [source json (default colab/jobs_queue_20261109.json)] [name in Drive (default jobs_queue.json)]
# Run it in the user's own terminal: the sandbox cannot write to Google Drive.
set -u
ROOTDIR="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${1:-$ROOTDIR/colab/jobs_queue_20261109.json}"
NAME="${2:-jobs_queue.json}"
DST_DIR="${PK_DRIVE_INPUTS_DIR:-<DRIVE_DIR>}"
case "$NAME" in jobs.json|unit_*|ref_*) echo "ERROR refusing to overwrite $NAME" >&2; exit 1;; esac
if [ ! -f "$SRC" ]; then echo "ERROR missing $SRC" >&2; exit 1; fi
if [ ! -d "$DST_DIR" ]; then echo "ERROR Drive folder not found: $DST_DIR" >&2; exit 1; fi
cp "$SRC" "$DST_DIR/$NAME" || { echo "ERROR copy failed" >&2; exit 1; }
SA=$(shasum -a 256 "$SRC" | cut -d' ' -f1); SB=$(shasum -a 256 "$DST_DIR/$NAME" | cut -d' ' -f1)
if [ "$SA" = "$SB" ]; then echo "OK $NAME copied ($SA)"; else echo "ERROR checksum differs" >&2; exit 1; fi
