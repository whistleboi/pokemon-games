# SAVE SLOTS 5 -> 100 (patch c_01)

Patch: c_01_save_slots_100.patch (git diff --binary, against the playtest state =
23 PC patches + Android port). Apply from the outer "Kanto Math Game" folder:

    git apply --ignore-whitespace --check c_01_save_slots_100.patch
    git apply --ignore-whitespace c_01_save_slots_100.patch

## What changed
- src/core/save_slots.py (new): SAVE_SLOTS = 100, the only place the count lives.
  slot_path(), slot_index(), used_slots() (one os.listdir), first_empty(), any_saves(),
  summary() cached by (mtime, size) of the file and its .bak, forget().
- src/ui/slot_list.py (new): paged list, 8 rows per page, 13 pages.
  Touch: tap a row, PREV / NEXT buttons, swipe up/down. Keyboard (optional): Up/Down,
  PgUp/PgDn, Left/Right, Home/End, Enter. Empty slots are drawn without opening any file;
  only used slots on the visible page are read, once, then cached.
  Font: assets/pokemon_gsc_rebuilt.ttf (rebuilt GSC font with a proper e-acute), 24 px and
  16 px, antialias=False. Row: gold No.001, white name, saved date on the right,
  grey "Region - Area - N badges". Anything long is cut with "..." so it fits the row.
  (The save files have no play time, so none is shown.)
- src/states/menus.py:
  - Main menu: LOAD is enabled if any slot 0-99 exists (was range(5)).
  - NEW GAME now opens the file picker (LoadState mode="new"). It starts on the first empty
    slot. An empty slot starts at once. A used slot asks YES/NO first. The picked slot becomes
    data.save_file.
  - LoadState: the 5 fixed buttons are replaced by the paged list, plus BACK and Esc.
    The save_slots / get_slot_text API is kept.
  - SaveState: a "No.NNN ... - CHANGE" button opens the same paged picker. The default
    slot is the current file, or the first empty slot when playing from game_data.json
    (before, it fell back to slot 0). The old filename parsing is replaced by save_slots.slot_index().
- assets/pokemon_gsc_rebuilt.ttf (new, binary).
- dev/checks/slots_body.py (new) + run_all.sh: saves to slots 0, 57 and 99 with the
  real DataManager.save in a temp folder, then lists and loads each. Also checks the .bak,
  the read count per page (cache), the keys, a .bak-only slot 4, the main menu LOAD and the
  new game picker. 26 checks.
- dev/checks/touch_smoke.py: NEW GAME now taps through the picker (NEXT, PREV, row).
  The save screen opens the picker, swipes and taps a row. Two KEYDOWN sites were added
  to the allow-list.

Not changed: the region-select screen, delete and copy. There is no slot code in them.
The game has no delete or copy for save files. File names are the same (game_data_N.json +
.bak), so saves 0-4 load unchanged.

## Tests (SDL_VIDEODRIVER=dummy, py3.11 venv)
bash dev/checks/run_all.sh: all 21 suites have 0 fails (slots is new), all 7 walks have 0 problems,
test_kanto_fixes 24/24 passed, SIM 0 errors, smoke_regions 0 failures, touch_smoke RESULT: 0 fails.
(touch_smoke prints "info HoennVersionState: opened but crashed headless". This was there before the patch.)

## Screenshots (screenshots/)
before_page1.png (old 5 buttons), after_page1.png, after_last.png (page 13/13),
after_save.png, after_save_picker.png

## Which patch targets which base

- c_01_save_slots_100_playtest.patch  -> USE THIS ON THE PC PLAYTEST COPY.
  Base: commit 0746892 + the 23 patches a_01..a_11, b_01..b_12
  (NO android_port.diff). Touches 6 files only: src/core/save_slots.py (new,
  with folder() helper -> assets.base_dir since this base has no save_dir),
  src/ui/slot_list.py (new), src/states/menus.py, assets/pokemon_gsc_rebuilt.ttf
  (new), dev/checks/slots_body.py (new), dev/checks/run_all.sh.
  No touch_smoke.py edits. Name entry stays keyboard typing as in that base.
  Tests: run_all.sh headless (SDL dummy, Python 3.13) -> all 9 suites 0 fails,
  incl. slots 0 fails. git apply --ignore-whitespace --check passes from the
  outer folder; applying it reproduces the tested tree exactly.
- c_01_save_slots_100.patch -> base = playtest base + android_port.diff
  (Android tree, 959ba5c). Includes touch_smoke.py edits and TextField/SAVE
  button handling. Keep for later, after android_port.diff is applied.
