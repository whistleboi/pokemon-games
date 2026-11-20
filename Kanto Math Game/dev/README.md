# dev: everything that isn't the game itself

Nothing here is loaded by the game. Rules for map work and which checks to run: `pokemon-games/kanto_handoff/SWEEP_RULES.md`
(outside the repo). Paths here are used by many tools and notes: **don't rename or move files**; add new ones beside them.

## builders/ — scripts that make the game's data and pictures
- `build_town_maps.py`: draws and checks every walkable map, writes `assets/town_maps.json` (`--only=<region>`).
  Its previews go to `out/maps/` (rebuilt every run).
- `town_maps/<region>.py`: the walkable maps themselves (written by each region's tool in `kanto_handoff`; edit
  those, never the JSON). `town_maps/made/` = maps exported from the Pokemath Map Maker. `MAPPING_GUIDE.md` = the
  older hand-mapping method.
- `build_*.py`, `import_*.py`, `make_*.py`, `render_*.py`, `fetch_*.py`: one builder per data set or picture set
  (learnsets, TMs, EV yields, followers, music, region maps...). Some are one-offs whose output was hand-edited
  since: read one before re-running it.
- Old (menu) region builders: `build_orange.py`, `orange_*.py`, `build_orre.py`, `orre_shadows.py`,
  `build_decolore.py`, `build_sinjoh.py`, `build_dlc.py`, `kalos_*.py`, `make_kalos_*`, `make_unova_buildings.py`.
- `data/`, `sources/`, `art/`: inputs the builders read. `rxdata.py`, `gba_maps.py`, `textjson.py`, `sublib.py`: helpers.
- Not in git: `out/` (generated; `out/pokeapi_csv` and `out/swsh_maps` are builder inputs, keep them),
  `bulbapedia_cache/` (saved character pages).

## checks/ — the check suites
Each suite is `harness_head.py` + `<name>_body.py` (a few also `sub_helpers_body.py`), run headless.
`bash dev/checks/run.sh <suite> ... walk:<region>` runs some; `run_all.sh` runs everything (about 40 minutes).

| Kind | Suites |
|---|---|
| New-region maps | `kanto_maps`, `frlg`, `sevii_maps`, `johto_canon`, `hoenn_maps`, `sinnoh`, `sinnohfolk` (Sinnoh townspeople), `orre_maps`, `dungeon` (shared map engine), `soaring`, `soaring3d`, `giant_volcano`, `canon_species` (every species the source games give in one playthrough: fishing on walked routes, Johto swarms, Orre stones/Plusle, Orange Linking Cord/Tauros, Hoenn Safari water, Lavaridge's Togepi Egg), `kanto_events` (Kanto and Sevii events played on their maps: the Body Slam and Swords Dance tutors, the Lemonade-for-Facade man, the Togepi Egg, the Heracross fan, the Lucky Punch, Dario and Rodette, Lady Selphy's battle and villa, Mt. Ember's password, fishing from a town, FireRed's nine trades; 11-19: the VS Seeker's pose and bubbles, the Hall of Fame and its record, every region's opening talk) |
| Region starts | `kantostart`, `hoennstart`, `sinnohstart`, `smoke_regions.py` (every region starts) |
| Reach walks | `walk_<region>.py` with `reach_lib.py` (`walk:<region>` in run.sh) |
| Engine | `battle2`, `doubles`, `catch`, `items`, `items_pp`, `moveeffects`, `selfko`, `tmshop`, `savename`, `faces`, `townsea`, `aiswitch`, `flyrule`, `vsseeker`, `partners`, `movepool`, `scaling`, `storage`, `slots`, `menus`, `ui`, `events`, `features`, `loops` |
| Old (menu) regions' data | `orange`, `orangeforms`, `decolore`, `sinjoh`, `dlc`, `lumiose`, `eterna`, `orre`, `shadows`, `sevii` (older Sevii story) |
| Older fix batches | `batch3`-`batch6`, `fixes`, `bugs2`, `grokfix`, `recheck*`, `answers1023`, `canon1029`, `rivals`, `blockers`, `blackfog` |

`out/` (not in git) holds the joined suites and their scratch files.

## tools/ — one-off tools
`dex_audit_body.py` (every region's dex obtainable; join with `checks/harness_head.py`), `map_grid.py`,
`map_compare.py`, `tile_classify.py`, `journeys_layout.py`, `journeys_render.py` (older map-making helpers),
`export_map_audit.py` (writes `dev/map_audit/`, every map beside its source; not in git), `make_android_copy.py`,
`make_all_champions_save.py`, `make_orre_test_save.py`, `generate_names.py`, `fix_png_crc.py`.

## reference/ — pictures kept for reference
Region and world maps, a few source town pictures (`maps/`), Hisuian overworld sheets (`followers/`). See its README.
