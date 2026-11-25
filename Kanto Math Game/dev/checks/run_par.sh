#!/usr/bin/env bash
# Like run.sh, but the suites run side by side, each with its own scratch folder (11-16: a region check).
#   bash dev/checks/run_par.sh kanto_maps frlg sevii_maps dungeon walk:kanto
#   bash dev/checks/run_par.sh region:unova      the same words as run.sh (region:<lane>, quick, tag:<t>, all)
#   JOBS=6 bash dev/checks/run_par.sh all        at most JOBS at once (default 8)
# Prints "== <name>: N fails (S s)" and the FAIL / Traceback lines once all are done; the whole output stays in
# dev/checks/out/par_<name>.log. Suites are separate processes that save nothing (the harness turns saving off).
cd "$(dirname "$0")/../.." || exit 1
. dev/checks/suites_lib.sh
mkdir -p "$O"
JOBS=${JOBS:-8}
names=()
for w in "$@"; do
  while read -r t; do [ -n "$t" ] && [[ " ${names[*]} " != *" $t "* ]] && names+=("$t"); done < <(expand "$w")   # (once each)
done
one() {   # one <name>: run it into its log, its time and exit code on the last two lines
  local t=$1 n=${1/:/_} s=$SECONDS lim=2400
  mkdir -p "$O/par_$n"
  build "$t" "$O/check_$n.py"
  timeout $lim python "$O/check_$n.py" "$O/par_$n" > "$O/par_$n.log" 2>&1
  echo "exit $?" >> "$O/par_$n.log"; echo "secs $((SECONDS - s))" >> "$O/par_$n.log"
}
ran=()
for t in "${names[@]}"; do
  why=$(_gone "$t") && { echo "== $t: taken out ($why)"; continue; }
  exists "$t" || { echo "== $t: no such suite"; continue; }
  while [ "$(jobs -rp | wc -l)" -ge "$JOBS" ]; do wait -n; done
  one "$t" &
  ran+=("$t")
done
wait
total=0
for t in "${ran[@]}"; do
  n=${t/:/_}; log=$O/par_$n.log
  ex=$(grep '^exit ' "$log" | tail -1 | cut -d' ' -f2); secs=$(grep '^secs ' "$log" | tail -1 | cut -d' ' -f2)
  c=$(count "$t" "$log" "$ex")
  total=$((total + c))
  k=$(checks "$log")
  note_time "$t" "$secs" "$c" "$k"
  echo "== $n: $c fails ($secs s, $k checks)"
  base_warn "$t" "$k"
  grep -E 'FAIL |Traceback|(Syntax|Indentation)Error' -B2 -A6 "$log" | grep -vE '^--$|##### 0 fail|^Sync: |^(exit|secs) ' | head -40
done
echo "##### $total fails in all"
[ $total = 0 ]
