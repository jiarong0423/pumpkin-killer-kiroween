#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
SEAT=${1:-}
if [ -z "$SEAT" ]; then
  echo "Usage: $0 <red|white|spectator|referee> [relay-url invitation-code]" >&2
  exit 2
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.10 or later is required: https://www.python.org/downloads/" >&2
  exit 1
fi
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' || {
  echo "Python 3.10 or later is required: https://www.python.org/downloads/" >&2
  exit 1
}
if [ "$#" -ne 1 ] && [ "$#" -ne 3 ]; then
  echo "Usage: $0 <red|white|spectator|referee> [relay-url invitation-code]" >&2
  exit 2
fi
if [ "$#" -eq 3 ]; then
  exec python3 -B "$ROOT/scripts/mcp_stdio_server.py" --seat "$SEAT" --connect "$2" --code "$3"
fi
exec python3 -B "$ROOT/scripts/mcp_stdio_server.py" --seat "$SEAT"
