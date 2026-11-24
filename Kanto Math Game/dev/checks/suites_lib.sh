# Shared by run.sh, run_par.sh and run_all.sh (Checks branch, 11-24). Sourced from the game folder.
# The list of suites, who owns each and its tags: dev/checks/suites.txt. Add a line there for every new suite.
C=dev/checks
O=$C/out
LIST=$C/suites.txt
export PYTHONIOENCODING=utf-8

_rows() { sed 's/\r$//; s/#.*//' "$LIST" | awk 'NF >= 2 && $1 != "alias" && $1 != "gone"'; }
_gone() { sed 's/\r$//' "$LIST" | awk -v n="$1" '$1 == "gone" && $2 == n { $1 = $2 = ""; sub(/^ +/, ""); print; f = 1 } END { exit !f }'; }
_has_tag() { _rows | awk -v n="$1" -v t="$2" '$1 == n { if (("," $3 ",") ~ ("," t ",")) f = 1 } END { exit !f }'; }
_alias() { sed 's/\r$//; s/#.*//' "$LIST" | awk -v n="$1" '$1 == "alias" && $2 == n { $1 = $2 = ""; print; f = 1 } END { exit !f }'; }

# expand <word>: the suite names (or walk:<r>) a word on the command line stands for, one per line.
#   region:<lane>  every suite that lane owns + walk:<lane> (no long ones: those are listed, name them to run)
#   quick          the quick set: a few short suites that open the whole game (about 2-3 minutes side by side)
#   tag:<t>        every suite with that tag      owner:<o>  the same as region:<o> without the walk
#   all            every suite but the long ones   an old name kept by an alias line: its new name(s)
expand() {
  local w=$1 r
  case "$w" in
    region:sevii) expand region:kanto ;;
    region:*|owner:*)
      r=${w#*:}
      _rows | awk -v r="$r" '$2 == r && ("," $3 ",") !~ /,long,/ { print $1 }'
      [ "${w%%:*}" = region ] && [ -f "$C/walk_$r.py" ] && echo "walk:$r"
      local skipped; skipped=$(_rows | awk -v r="$r" '$2 == r && ("," $3 ",") ~ /,long,/ { printf "%s ", $1 }')
      [ -n "$skipped" ] && echo "   (left out of $w as long: ${skipped}- name them to run)" >&2 ;;
    quick) _rows | awk '("," $3 ",") ~ /,quick,/ { print $1 }' ;;
    tag:*) _rows | awk -v t="${w#tag:}" '("," $3 ",") ~ ("," t ",") { print $1 }' ;;
    all) _rows | awk '("," $3 ",") !~ /,long,/ { print $1 }' ;;
    *) _alias "$w" | tr ' ' '\n' | grep . || echo "$w" ;;
  esac
}

# build <name|walk:r> <file>: join the suite into one script (harness_head.py + helpers + body).
build() {
  local t=$1 f=$2
  if [ "${t#walk:}" != "$t" ]; then
    cat $C/harness_head.py $C/reach_lib.py $C/walk_${t#walk:}.py > "$f"
  elif _has_tag "$t" helpers; then
    cat $C/harness_head.py $C/sub_helpers_body.py $C/${t}_body.py > "$f"
  else
    cat $C/harness_head.py $C/${t}_body.py > "$f"
  fi
}

exists() { if [ "${1#walk:}" != "$1" ]; then [ -f "$C/walk_${1#walk:}.py" ]; else [ -f "$C/${1}_body.py" ]; fi; }

# count <name> <log> <exit code>: the failures in a finished suite's output.
# FAIL lines + Tracebacks + a suite that can't start (SyntaxError); a time-out or a crash with no Traceback counts 1.
count() {
  local t=$1 log=$2 ex=$3 n
  if [ "${t#walk:}" != "$t" ]; then
    n=$(grep -ciE 'FAIL|Traceback' "$log")
  else
    n=$(grep -cE 'FAIL |Traceback|(Syntax|Indentation)Error' "$log")
    # (C2, 11-24) every suite ends "##### N failures": no such line = it stopped early; more failures there than FAIL
    # lines = some were counted without a FAIL line, so the bigger number counts
    local end; end=$(grep -E '^##### [0-9]+ failures' "$log" | tail -1 | sed -E 's/^##### ([0-9]+).*/\1/')
    if [ -z "$end" ]; then n=$((n + 1)); echo "   (no '##### N failures' end line: it stopped early)" >&2
    elif [ "$end" -gt "$n" ]; then n=$end; fi
  fi
  if [ "$ex" = 124 ]; then n=$((n + 1)); echo "   (timed out)" >&2
  elif [ "$n" = 0 ] && [ "$ex" != 0 ]; then n=1; echo "   (stopped with exit $ex and no FAIL line)" >&2; fi
  echo "$n"
}

# lint: bodies missing from suites.txt and lines with no body (run_all.sh prints it; run.sh lint).
lint() {
  local b n bad=0
  for b in $C/*_body.py; do
    n=$(basename "$b" _body.py); [ "$n" = sub_helpers ] && continue
    _rows | awk -v n="$n" '$1 == n { f = 1 } END { exit !f }' || { echo "   not in suites.txt: $n (add a line: name owner tags)"; bad=$((bad + 1)); }
  done
  for n in $(_rows | awk '{ print $1 }'); do [ -f "$C/${n}_body.py" ] || { echo "   in suites.txt but no ${n}_body.py"; bad=$((bad + 1)); }; done
  return $bad
}

# timing: every finished suite's seconds go to out/timings.tsv (date, name, seconds, fails, checks made), for ROADMAP_CHECKS.md.
note_time() { printf "%s\t%s\t%s\t%s\t%s\n" "$(date +%F)" "$1" "$2" "$3" "$4" >> "$O/timings.tsv"; }

# checks <log>: how many checks a suite made (its "ok" / "FAIL" lines): compare before and after moving or merging tests.
checks() { grep -cE '^ *(ok|OK|FAIL)( |$)' "$1"; }

# baseline.tsv (C2, 11-24): name, checks made, date - how many checks each suite made when last counted. A run that
# makes fewer says so (not a fail: a map's door count can change); moving or merging tests must not lower the total.
# bash dev/checks/run.sh baseline <suite>...  writes the numbers from those suites' last run (out/timings.tsv).
BASE=$C/baseline.tsv
base_of() { [ -f "$BASE" ] && sed 's/\r$//' "$BASE" | awk -F'\t' -v n="$1" '$1 == n { print $2 }'; }
base_warn() { local b; b=$(base_of "$1"); [ -n "$b" ] && [ -n "$2" ] && [ "$2" -lt "$b" ] && echo "   (made $2 checks, fewer than its baseline $b: dev/checks/baseline.tsv)"; return 0; }
base_set() {   # base_set <name> <checks>
  touch "$BASE"
  { sed 's/\r$//' "$BASE" | awk -F'\t' -v n="$1" '$1 != n'; printf "%s\t%s\t%s\n" "$1" "$2" "$(date +%F)"; } | sort > "$BASE.new" && mv "$BASE.new" "$BASE"
}
