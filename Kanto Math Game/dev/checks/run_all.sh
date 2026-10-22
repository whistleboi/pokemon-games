#!/usr/bin/env bash
# Run every check headless from the game folder:  bash dev/checks/run_all.sh
# Each suite is harness_head.py (+ sub_helpers_body.py) + <name>_body.py, built into dev/checks/out/.
# A line "FAIL" is a failed check; batch5 raises ValueError("test") on purpose (its crash-handler test).
cd "$(dirname "$0")/../.." || exit 1
C=dev/checks
O=$C/out
mkdir -p "$O"
export PYTHONIOENCODING=utf-8
HELPED="grokfix storage dlc sevii decolore sinjoh orre"
PLAIN="orange batch6 batch5 ui batch4 batch3 fixes battle2 events features loops eterna catch"
for t in $HELPED; do cat $C/harness_head.py $C/sub_helpers_body.py $C/${t}_body.py > $O/check_$t.py; done
for t in $PLAIN; do cat $C/harness_head.py $C/${t}_body.py > $O/check_$t.py; done
for t in $HELPED $PLAIN; do
  r=$(timeout 600 python $O/check_$t.py $O 2>&1)
  echo "== $t: $(echo "$r" | grep -cE 'FAIL ') fails"; echo "$r" | grep -E "FAIL " | head -5
done
for r in johto hoenn sinnoh unova kalos alola galar; do
  cat $C/harness_head.py $C/reach_lib.py $C/walk_$r.py > $O/check_walk_$r.py
  echo "walk $r: $(timeout 600 python $O/check_walk_$r.py $O 2>&1 | grep -ciE 'FAIL|Traceback') problems"
done
python tests/test_kanto_fixes.py 2>&1 | grep -E "FAIL|passed"
timeout 300 python tests/sim_battles.py 2>&1 | tail -1
timeout 590 python $C/smoke_regions.py "$(pwd)" 2>&1 | grep -E "^#####|Traceback"
