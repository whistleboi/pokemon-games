#!/usr/bin/env bash
# Run just the suites you name (the targeted check, Jordan 11-12: test what a change touches, the way a player meets it).
#   bash dev/checks/run.sh hoenn_maps dungeon            a suite: harness_head.py (+ sub_helpers_body.py) + <name>_body.py
#   bash dev/checks/run.sh walk:hoenn walk:sinnoh       a region's reach walk: harness_head.py + reach_lib.py + walk_<r>.py
#   bash dev/checks/run.sh -v hoenn_maps                -v: the whole output, not just the failures
# Prints "== <name>: N fails" and every FAIL / Traceback line. bash dev/checks/run_all.sh runs everything (before a commit).
cd "$(dirname "$0")/../.." || exit 1
C=dev/checks
O=$C/out
mkdir -p "$O"
export PYTHONIOENCODING=utf-8
HELPED=" grokfix storage dlc sevii decolore sinjoh orre "   # (these need sub_helpers_body.py: keep in step with run_all.sh)
VERBOSE=0
total=0
for t in "$@"; do
  if [ "$t" = "-v" ]; then VERBOSE=1; continue; fi
  if [ "${t#walk:}" != "$t" ]; then
    r=${t#walk:}
    cat $C/harness_head.py $C/reach_lib.py $C/walk_$r.py > $O/check_walk_$r.py
    out=$(timeout 900 python $O/check_walk_$r.py $O 2>&1)
    n=$(echo "$out" | grep -ciE 'FAIL|Traceback')
  else
    [ -f $C/${t}_body.py ] || { echo "== $t: no such suite (dev/checks/${t}_body.py)"; total=$((total + 1)); continue; }
    if [ "${HELPED#* $t }" != "$HELPED" ]; then
      cat $C/harness_head.py $C/sub_helpers_body.py $C/${t}_body.py > $O/check_$t.py
    else
      cat $C/harness_head.py $C/${t}_body.py > $O/check_$t.py
    fi
    out=$(timeout 1500 python $O/check_$t.py $O 2>&1)
    n=$(echo "$out" | grep -cE 'FAIL |Traceback')
    [ "$t" = batch5 ] && n=$((n - $(echo "$out" | grep -c '^ValueError: test$')))   # (its crash-handler test raises on purpose)
  fi
  total=$((total + n))
  echo "== $t: $n fails"
  if [ $VERBOSE = 1 ]; then echo "$out" | grep -v '^Sync: '; else echo "$out" | grep -E 'FAIL|Traceback' -A3 | grep -vE '^--$|##### 0 fail' | head -40; fi
done
echo "##### $total fails in all"
[ $total = 0 ]
