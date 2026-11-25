#!/usr/bin/env bash
# Run just the suites you name (the targeted check, Jordan 11-12: test what a change touches, the way a player meets it).
#   bash dev/checks/run.sh hoenn_maps dungeon            a suite: harness_head.py (+ sub_helpers_body.py) + <name>_body.py
#   bash dev/checks/run.sh walk:hoenn walk:sinnoh       a region's reach walk: harness_head.py + reach_lib.py + walk_<r>.py
#   bash dev/checks/run.sh region:unova                 a region's set: every suite its lane owns + its walk (no long ones)
#   bash dev/checks/run.sh quick                        the quick set: short suites that open the whole game
#   bash dev/checks/run.sh tag:battle                   every suite with a tag (dev/checks/suites.txt)
#   bash dev/checks/run.sh -v hoenn_maps                -v: the whole output, not just the failures
#   bash dev/checks/run.sh list region:unova            print what a set holds, run nothing;  run.sh lint: suites.txt vs the files
#   bash dev/checks/run.sh baseline region:unova        save each suite's checks made (its last 0-fail run) in baseline.tsv
# Prints "== <name>: N fails (S s)" and every FAIL / Traceback line. A time-out counts as a fail.
# Sets run one after another here; bash dev/checks/run_par.sh runs the same words side by side.
cd "$(dirname "$0")/../.." || exit 1
. dev/checks/suites_lib.sh
mkdir -p "$O"
VERBOSE=0
total=0
case "$1" in
  list) shift; for w in "$@"; do expand "$w"; done; exit 0 ;;
  lint) lint; r=$?; [ $r = 0 ] && echo "suites.txt matches the files"; exit $r ;;
  baseline) shift
    for w in "$@"; do while read -r t; do
      k=$(sed 's/\r$//' "$O/timings.tsv" 2>/dev/null | awk -F'\t' -v n="$t" '$2 == n && $4 == 0 && $5 != "" { k = $5 } END { print k }')
      if [ -n "$k" ]; then base_set "$t" "$k"; echo "$t: $k checks"; else echo "$t: no 0-fail run in out/timings.tsv yet"; fi
    done < <(expand "$w"); done; exit 0 ;;
esac
names=()
for w in "$@"; do
  if [ "$w" = "-v" ]; then VERBOSE=1; continue; fi
  while read -r t; do [ -n "$t" ] && [[ " ${names[*]} " != *" $t "* ]] && names+=("$t"); done < <(expand "$w")   # (once each)
done
for t in "${names[@]}"; do
  why=$(_gone "$t") && { echo "== $t: taken out ($why)"; continue; }
  exists "$t" || { echo "== $t: no such suite (dev/checks/${t}_body.py)"; total=$((total + 1)); continue; }
  f=$O/check_${t/:/_}.py
  build "$t" "$f"
  s=$SECONDS
  if [ "${t#walk:}" != "$t" ]; then timeout 900 python "$f" $O > "$O/run_${t/:/_}.log" 2>&1; else timeout 1500 python "$f" $O > "$O/run_${t/:/_}.log" 2>&1; fi
  ex=$?
  n=$(count "$t" "$O/run_${t/:/_}.log" $ex 2> "$O/note.txt")   # (its notes printed under its own line)
  total=$((total + n))
  k=$(checks "$O/run_${t/:/_}.log")
  note_time "$t" $((SECONDS - s)) "$n" "$k"
  echo "== $t: $n fails ($((SECONDS - s)) s, $k checks)"
  cat "$O/note.txt" 2>/dev/null; rm -f "$O/note.txt"; base_warn "$t" "$k"
  if [ $VERBOSE = 1 ]; then grep -v '^Sync: ' "$O/run_${t/:/_}.log"; else grep -E 'FAIL |Traceback|(Syntax|Indentation)Error' -B3 -A3 "$O/run_${t/:/_}.log" | grep -vE '^--$|##### 0 fail' | head -40; fi
done
echo "##### $total fails in all"
[ $total = 0 ]
