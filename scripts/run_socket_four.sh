#!/bin/zsh
# Runs the four socket suites one after another (one process at a time) in a normal terminal, outside the Claude sandbox.
# Writes redteam/evidence/socket_four_<HEAD>_<date>.txt (one line per suite plus the last lines of any failure). Exit 1 if any suite failed.
ROOT="${0:A:h:h}"
cd "$ROOT/scripts" || exit 2
HEADSHA=$(git -C "$ROOT" rev-parse --short HEAD)
OUT="$ROOT/redteam/evidence/socket_four_${HEADSHA}_$(date +%Y%m%d).txt"
TMPLOG="$(mktemp -d)"
FAILED=0
{
  echo "socket four, HEAD $HEADSHA, $(date '+%Y-%m-%d %H:%M:%S'), load $(uptime | sed 's/.*load averages*: //')"
} > "$OUT"
for t in test_mcp_stdio.py test_relay_reconnect.py test_relay_seat_grace.py test_phone_room_check.py; do
  start=$(date +%s)
  timeout 400 python3 -B "$t" > "$TMPLOG/$t.log" 2>&1
  rc=$?
  secs=$(( $(date +%s) - start ))
  summary=$(grep -E "^(Ran [0-9]+ tests|OK|FAILED|OK \(skipped)" "$TMPLOG/$t.log" | tr '\n' ' ' | cut -c1-160)
  skipped=$(grep -c "skipped" "$TMPLOG/$t.log")
  if [ $rc -eq 0 ]; then echo "PASS $t | ${secs}s | $summary | skipped-mentions=$skipped" >> "$OUT"; else echo "FAIL $t | rc=$rc | ${secs}s | $summary" >> "$OUT"; tail -n 8 "$TMPLOG/$t.log" | sed 's/^/    ERROR /' >> "$OUT"; FAILED=1; fi
done
echo "DONE failed=$FAILED RESOURCE_RELEASED" >> "$OUT"
cat "$OUT"
exit $FAILED
