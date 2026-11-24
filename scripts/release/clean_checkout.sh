#!/usr/bin/env bash
# Verify a source tree from an isolated local copy. This script never contacts a remote.
set -u

usage() {
  printf 'Usage: bash scripts/release/clean_checkout.sh --src <dir> --log <file> [--worktree] [--keep]\n' >&2
}

SRC=''
LOG=''
KEEP=0
WORKTREE=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --src)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      SRC=$2
      shift 2
      ;;
    --log)
      [ "$#" -ge 2 ] || { usage; exit 2; }
      LOG=$2
      shift 2
      ;;
    --worktree)
      WORKTREE=1
      shift
      ;;
    --keep)
      KEEP=1
      shift
      ;;
    *)
      usage
      exit 2
      ;;
  esac
done

[ -n "$SRC" ] && [ -n "$LOG" ] || { usage; exit 2; }
[ -d "$SRC" ] || { printf 'Source directory does not exist: %s\n' "$SRC" >&2; exit 2; }

START_DIR=$(pwd -P)
case "$SRC" in
  /*) SRC=$(cd "$SRC" && pwd -P) ;;
  *) SRC=$(cd "$SRC" && pwd -P) ;;
esac
case "$LOG" in
  /*) ;;
  *) LOG=$START_DIR/$LOG ;;
esac

LOG_DIR=$(dirname "$LOG")
[ -d "$LOG_DIR" ] || { printf 'Log directory does not exist: %s\n' "$LOG_DIR" >&2; exit 2; }
: > "$LOG" || { printf 'Cannot write log: %s\n' "$LOG" >&2; exit 2; }

TEMP_ROOT=$(mktemp -d) || exit 2
COPY=$TEMP_ROOT/project
SERVER_PID=''
PORT=''
SERVER_STOPPED=yes

log() {
  printf '%s\n' "$*" >> "$LOG"
}

copy_worktree() {
  mkdir -p "$COPY"
  for entry in "$SRC"/.[!.]* "$SRC"/..?* "$SRC"/*; do
    [ -e "$entry" ] || continue
    name=$(basename "$entry")
    case "$name" in
      .git|node_modules)
        continue
        ;;
      docs)
        mkdir -p "$COPY/docs"
        for doc_entry in "$SRC/docs"/.[!.]* "$SRC/docs"/..?* "$SRC/docs"/*; do
          [ -e "$doc_entry" ] || continue
          [ "$(basename "$doc_entry")" = audition ] && continue
          cp -R "$doc_entry" "$COPY/docs/"
        done
        ;;
      *)
        cp -R "$entry" "$COPY/"
        ;;
    esac
  done
}

stop_server() {
  if [ -z "$SERVER_PID" ]; then
    return
  fi
  log "Stopping server PID $SERVER_PID on port $PORT"
  kill "$SERVER_PID" >> "$LOG" 2>&1 || true
  wait "$SERVER_PID" >> "$LOG" 2>&1 || true
  if command -v lsof >/dev/null 2>&1; then
    if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >> "$LOG" 2>&1; then
      SERVER_STOPPED=no
      log "Listener remains on port $PORT"
    else
      log "No listener remains on port $PORT"
    fi
  else
    SERVER_STOPPED=no
    log "lsof is unavailable; could not verify port $PORT"
  fi
  SERVER_PID=''
}

cleanup() {
  status=$?
  stop_server
  if [ "$KEEP" -eq 0 ]; then
    rm -rf "$TEMP_ROOT"
  else
    log "Keeping temporary copy: $TEMP_ROOT"
  fi
  exit "$status"
}
trap cleanup EXIT INT TERM

fetch_status() {
  python3 - "$1" <<'PY'
import sys
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

try:
    with urlopen(sys.argv[1], timeout=2) as response:
        print(response.status)
except HTTPError as error:
    print(error.code)
except (URLError, OSError):
    print('000')
PY
}

log "Clean checkout source: $SRC"
log "Known optional-package failures are left unchanged: scripts/test_fonts.py (fontTools), scripts/test_ingest_missing.py (Pillow), scripts/test_ingest_sheets.py (numpy and Pillow), scripts/test_ingest_wind_sheets.py (Pillow), scripts/test_postprocess_audio.py (numpy). scripts/test_i18n.js is expected to pass after its page wiring."
if [ "$WORKTREE" -eq 1 ]; then
  COPY_MODE='worktree'
  log "Copy method: cp -R worktree exclusions (.git, docs/audition, node_modules)"
  copy_worktree >> "$LOG" 2>&1
  COPY_STATUS=$?
elif [ -d "$SRC/.git" ]; then
  COPY_MODE='git clone'
  log "Copy method: git clone --no-hardlinks"
  git clone --no-hardlinks "$SRC" "$COPY" >> "$LOG" 2>&1
  COPY_STATUS=$?
else
  COPY_MODE='worktree (source has no .git)'
  log "Copy method: cp -R worktree exclusions (.git, docs/audition, node_modules)"
  copy_worktree >> "$LOG" 2>&1
  COPY_STATUS=$?
fi
if [ "$COPY_STATUS" -ne 0 ] || [ ! -d "$COPY" ]; then
  log "Copy failed with exit code $COPY_STATUS"
  {
    printf 'copy mode: %s\n' "$COPY_MODE"
    printf 'server 200: no\n'
    printf '404 count: 0\n'
    printf 'missing references: 0\n'
    printf 'missing reference paths: none\n'
    printf 'tests passed: 0\n'
    printf 'tests failed: copy\n'
    printf 'overall result: FAIL\n'
  } | tee -a "$LOG"
  exit 1
fi

PORT=$(python3 - <<'PY'
import socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind(('127.0.0.1', 0))
    print(sock.getsockname()[1])
PY
)
log "Starting static server on port $PORT"
(
  cd "$COPY" || exit 1
  exec python3 -m http.server "$PORT" --bind 127.0.0.1
) >> "$LOG" 2>&1 &
SERVER_PID=$!

INDEX_STATUS=000
attempt=1
while [ "$attempt" -le 50 ]; do
  INDEX_STATUS=$(fetch_status "http://127.0.0.1:$PORT/index.html")
  [ "$INDEX_STATUS" = 200 ] && break
  sleep 0.1
  attempt=$((attempt + 1))
done
log "GET /index.html: $INDEX_STATUS"

REFS_FILE=$TEMP_ROOT/asset_refs.txt
(
  cd "$COPY" || exit 1
  python3 -B scripts/release/check_asset_refs.py --root "$COPY"
) > "$REFS_FILE" 2>&1
REFS_STATUS=$?
cat "$REFS_FILE" >> "$LOG"
log "Asset-reference scanner exit code: $REFS_STATUS"

NOT_FOUND=0
MISSING_REFS=()
while IFS= read -r line; do
  case "$line" in
    'REF '*)
      asset=${line#REF }
      status=$(fetch_status "http://127.0.0.1:$PORT/$asset")
      log "GET /$asset: $status"
      if [ "$status" = 404 ]; then
        NOT_FOUND=$((NOT_FOUND + 1))
      fi
      ;;
    'MISSING '*)
      MISSING_REFS+=("${line#MISSING }")
      ;;
    'CASE '*)
      MISSING_REFS+=("${line#CASE }")
      ;;
  esac
done < "$REFS_FILE"
MISSING_COUNT=${#MISSING_REFS[@]}
if [ "$MISSING_COUNT" -eq 0 ]; then
  MISSING_PATHS=none
else
  MISSING_PATHS=''
  for asset in "${MISSING_REFS[@]:0:5}"; do
    MISSING_PATHS=${MISSING_PATHS:+$MISSING_PATHS,}$asset
  done
fi

stop_server

PASSED=0
FAILED=''
for test_file in "$COPY"/scripts/test_*.js; do
  [ -f "$test_file" ] || continue
  test_name=${test_file#"$COPY"/}
  log "Running: node $test_name"
  (
    cd "$COPY" || exit 1
    node "$test_name"
  ) >> "$LOG" 2>&1
  code=$?
  if [ "$code" -eq 0 ]; then
    PASSED=$((PASSED + 1))
    log "PASS $test_name (exit 0)"
  else
    FAILED=${FAILED:+$FAILED,}$test_name
    log "FAIL $test_name (exit $code)"
  fi
done
for test_file in "$COPY"/scripts/test_*.py; do
  [ -f "$test_file" ] || continue
  test_name=${test_file#"$COPY"/}
  log "Running: python3 -B $test_name"
  (
    cd "$COPY" || exit 1
    python3 -B "$test_name"
  ) >> "$LOG" 2>&1
  code=$?
  if [ "$code" -eq 0 ]; then
    PASSED=$((PASSED + 1))
    log "PASS $test_name (exit 0)"
  else
    FAILED=${FAILED:+$FAILED,}$test_name
    log "FAIL $test_name (exit $code)"
  fi
done

if [ -z "$FAILED" ]; then
  FAILED=none
fi
if [ "$INDEX_STATUS" = 200 ] && [ "$NOT_FOUND" -eq 0 ] && [ "$MISSING_COUNT" -eq 0 ] && [ "$FAILED" = none ] && [ "$SERVER_STOPPED" = yes ]; then
  RESULT=PASS
  EXIT_CODE=0
else
  RESULT=FAIL
  EXIT_CODE=1
fi

{
  printf 'copy mode: %s\n' "$COPY_MODE"
  printf 'server 200: %s\n' "$( [ "$INDEX_STATUS" = 200 ] && printf yes || printf no )"
  printf '404 count: %s\n' "$NOT_FOUND"
  printf 'missing references: %s\n' "$MISSING_COUNT"
  printf 'missing reference paths: %s\n' "$MISSING_PATHS"
  printf 'tests passed: %s\n' "$PASSED"
  printf 'tests failed: %s\n' "$FAILED"
  printf 'overall result: %s\n' "$RESULT"
} | tee -a "$LOG"

exit "$EXIT_CODE"
