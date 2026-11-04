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
PLAIN="canon1029 menus items moveeffects rivals hoennstart kantostart sinnohstart recheck recheck_uk recheck_agh recheck_pkt recheck_orre lumiose scaling movepool blackfog blockers bugs2 shadows orangeforms answers1023 slots orange batch6 batch5 ui batch4 batch3 fixes battle2 events features loops eterna catch"
for t in $HELPED; do cat $C/harness_head.py $C/sub_helpers_body.py $C/${t}_body.py > $O/check_$t.py; done
for t in $PLAIN; do cat $C/harness_head.py $C/${t}_body.py > $O/check_$t.py; done
for t in $HELPED $PLAIN; do
  r=$(timeout 600 python $O/check_$t.py $O 2>&1)
  n=$(echo "$r" | grep -cE 'FAIL |Traceback')
  [ "$t" = batch5 ] && n=$((n - $(echo "$r" | grep -c '^ValueError: test$')))  # its crash-handler test raises on purpose
  echo "== $t: $n fails"; echo "$r" | grep -E "FAIL |Error" | head -5
done
for r in johto hoenn sinnoh unova kalos alola galar paldea kanto orange orre; do
  cat $C/harness_head.py $C/reach_lib.py $C/walk_$r.py > $O/check_walk_$r.py
  echo "walk $r: $(timeout 600 python $O/check_walk_$r.py $O 2>&1 | grep -ciE 'FAIL|Traceback') problems"
done
# Android (Pydroid 3) runs Python 3.11: the game must compile there too (Jordan, 11-04)
if py -3.11 -c "" 2>/dev/null; then
  echo "python 3.11 compile: $(py -3.11 -c "import compileall, sys; print('OK' if compileall.compile_dir('src', quiet=1, force=True) and compileall.compile_file('main.py', quiet=1, force=True) else 'FAIL')" 2>&1 | tail -3)"
fi
python tests/test_kanto_fixes.py 2>&1 | grep -E "FAIL|passed"
timeout 300 python tests/sim_battles.py 2>&1 | tail -1
timeout 590 python $C/smoke_regions.py "$(pwd)" 2>&1 | grep -E "^#####|Traceback"
