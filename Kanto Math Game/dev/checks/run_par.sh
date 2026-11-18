#!/usr/bin/env bash
# Like run.sh, but every suite you name runs at the same time, each with its own scratch folder (11-16: a region check).
#   bash dev/checks/run_par.sh kanto_maps frlg sevii_maps dungeon walk:kanto
# Prints "== <name>: N fails" and the FAIL / Traceback lines as each finishes; the whole output stays in
# dev/checks/out/par_<name>.log. Suites are separate processes that save nothing (the harness turns saving off).
cd "$(dirname "$0")/../.." || exit 1
C=dev/checks
O=$C/out
mkdir -p "$O"
export PYTHONIOENCODING=utf-8
HELPED=" grokfix storage dlc sevii decolore sinjoh orre "   # (these need sub_helpers_body.py: keep in step with run.sh)
names=()
for t in "$@"; do
  n=${t/:/_}
  mkdir -p "$O/par_$n"
  if [ "${t#walk:}" != "$t" ]; then
    r=${t#walk:}
    cat $C/harness_head.py $C/reach_lib.py $C/walk_$r.py > $O/check_walk_$r.py
    f=$O/check_walk_$r.py
  else
    [ -f $C/${t}_body.py ] || { echo "== $t: no such suite"; continue; }
    if [ "${HELPED#* $t }" != "$HELPED" ]; then
      cat $C/harness_head.py $C/sub_helpers_body.py $C/${t}_body.py > $O/check_$t.py
    else
      cat $C/harness_head.py $C/${t}_body.py > $O/check_$t.py
    fi
    f=$O/check_$t.py
  fi
  ( timeout 2400 python "$f" "$O/par_$n" > "$O/par_$n.log" 2>&1; echo "exit $?" >> "$O/par_$n.log" ) &
  names+=("$n")
done
wait
total=0
for n in "${names[@]}"; do
  c=$(grep -cE 'FAIL |Traceback|(Syntax|Indentation)Error' "$O/par_$n.log")
  grep -q '^exit 124$' "$O/par_$n.log" && c=$((c + 1)) && echo "   (timed out)"
  total=$((total + c))
  echo "== $n: $c fails"
  grep -E 'FAIL|Traceback|(Syntax|Indentation)Error' -B2 -A6 "$O/par_$n.log" | grep -vE '^--$|##### 0 fail|^Sync: ' | head -40
done
echo "##### $total fails in all"
[ $total = 0 ]
