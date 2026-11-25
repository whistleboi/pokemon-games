#!/usr/bin/env bash
# Run every check headless from the game folder:  bash dev/checks/run_all.sh   (only when Jordan asks: lean checks, 11-24)
# Every suite in dev/checks/suites.txt but the long ones (the playthroughs: LONG=1 adds them), every region's reach walk,
# and the smoke test,
# side by side (JOBS at once, default 8; run_par.sh), then the 3.11 compile and tests/.
cd "$(dirname "$0")/../.." || exit 1
. dev/checks/suites_lib.sh
lint   # (a suite missing from suites.txt would be left out of every set: add its line)
sets="all"
[ "${LONG:-0}" = 1 ] && sets="$sets tag:long"
for r in johto hoenn sinnoh unova kalos alola galar paldea kanto orange orre; do sets="$sets walk:$r"; done
sets="$sets smoke"   # (smoke_regions.py: every region starts; Checks C9)
bash $C/run_par.sh $sets
# Android (Pydroid 3) runs Python 3.11: the game must compile there too (Jordan, 11-04)
if py -3.11 -c "" 2>/dev/null; then
  echo "python 3.11 compile: $(py -3.11 -c "import compileall, sys; print('OK' if compileall.compile_dir('src', quiet=1, force=True) and compileall.compile_file('main.py', quiet=1, force=True) else 'FAIL')" 2>&1 | tail -3)"
fi
python tests/test_kanto_fixes.py 2>&1 | grep -E "FAIL|passed"
python tests/test_dungeon_core.py 2>&1 | grep -E "FAIL|passed"
python tests/test_coop_net.py 2>&1 | grep -E "FAIL|passed"
timeout 300 python tests/sim_battles.py 2>&1 | tail -1
