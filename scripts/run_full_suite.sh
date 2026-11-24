#!/bin/zsh
# Full socket-free suite: every scripts/test_*.js with node, every socket-free scripts/test_*.py with python3, then the team simulator.
# Writes logs_local/full_suite.log (one line per test: PASS/FAIL + last output line). Exit code 1 if anything failed.
ROOT="${0:A:h:h}"
cd "$ROOT" || exit 2
mkdir -p logs_local
LOG=logs_local/full_suite.log
: > "$LOG"
FAILED=0
SOCKET_TESTS=(test_relay_reconnect_block.py test_relay_late_join.py test_fill_room_selftest.py test_relay_reconnect.py test_relay_seat_grace.py test_phone_room_check.py e2e_local.py test_mcp_stdio.py)
for f in scripts/test_*.js; do
  if [[ " ${PK_SKIP:-} " == *" ${f:t} "* ]]; then echo "SKIP $f | PK_SKIP (owner 2026-11-18: no rendering runs)" >> "$LOG"; continue; fi
  out=$(node "$f" 2>&1); rc=$?
  last=$(print -r -- "$out" | tail -1 | cut -c1-160)
  if [ $rc -eq 0 ]; then echo "PASS $f | $last" >> "$LOG"; else echo "FAIL $f | $last" >> "$LOG"; FAILED=1; fi
done
for f in scripts/test_*.py; do
  base=${f:t}
  if (( ${SOCKET_TESTS[(Ie)$base]} )); then echo "SKIP $f | needs sockets" >> "$LOG"; continue; fi
  out=$(cd scripts && timeout 300 python3 -B "$base" 2>&1); rc=$?
  last=$(print -r -- "$out" | tail -1 | cut -c1-160)
  if [ $rc -eq 0 ]; then echo "PASS $f | $last" >> "$LOG"; else echo "FAIL $f | $last" >> "$LOG"; FAILED=1; fi
done
out=$(python3 -B scripts/sim_team_headless.py 2>&1); rc=$?
last=$(print -r -- "$out" | tail -1 | cut -c1-160)
if [ $rc -eq 0 ]; then echo "PASS scripts/sim_team_headless.py | $last" >> "$LOG"; else echo "FAIL scripts/sim_team_headless.py | $last" >> "$LOG"; FAILED=1; fi
echo "DONE failed=$FAILED" >> "$LOG"
exit $FAILED
