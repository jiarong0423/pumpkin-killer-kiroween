#!/usr/bin/env bash
# Run all local sheet checks. Usage: scripts/run_ingest_pipeline.sh INPUT_FOLDER [--grid ROWSxCOLS] [--force]
set +e

if [ "$#" -lt 1 ]; then
  echo "ERROR usage: scripts/run_ingest_pipeline.sh INPUT_FOLDER [--grid ROWSxCOLS] [--force]" >&2
  exit 1
fi

input_dir=$1
shift
continuity_json="docs/audition/sheet_continuity.json"
preview_dir="docs/audition/strip_previews"
thumb_dir="docs/audition/review"
pipeline_log="docs/audition/ingest_pipeline.log"
if ! mkdir -p "docs/audition" "$preview_dir" "$thumb_dir"; then
  echo "ERROR could not create pipeline output folders" >&2
  exit 1
fi

note() {
  printf '%s\n' "$*" | tee -a "$pipeline_log" >&2
}

failed=0
run_step() {
  local label=$1
  shift
  "$@" 2>&1 | tee -a "$pipeline_log" >&2
  local code=${PIPESTATUS[0]}
  note "$label exit code: $code"
  [ "$code" -eq 0 ] || failed=1
}

run_step "ingest_sheets" python3 -B scripts/ingest_sheets.py "$input_dir" "$@"
run_step "check_pose_set" python3 -B scripts/check_pose_set.py
run_step "check_continuity" python3 -B scripts/check_continuity.py --json "$continuity_json"
run_step "make_strip_gif (including review-compatible thumbnails)" python3 -B scripts/make_strip_gif.py --continuity-json "$continuity_json" --output-dir "$preview_dir" --thumbnail-dir "$thumb_dir"

note "SUMMARY input=$input_dir continuity=$continuity_json previews=$preview_dir thumbnails=$thumb_dir overall=$([ "$failed" -eq 0 ] && echo OK || echo ERROR)"
exit "$failed"
