#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PORT=${PK_PORT:-8000}

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.10 or later is required: https://www.python.org/downloads/" >&2
  exit 1
fi
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' || {
  echo "Python 3.10 or later is required: https://www.python.org/downloads/" >&2
  exit 1
}

python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$ROOT" &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT INT TERM
URL="http://127.0.0.1:${PORT}/"
if command -v open >/dev/null 2>&1; then
  open "$URL"
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$URL" >/dev/null 2>&1 || true
else
  echo "Open $URL in a browser."
fi
wait "$SERVER_PID"
