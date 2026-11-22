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
| New-region maps | `kanto_maps`, `frlg`, `sevii_maps`, `johto_canon`, `hoenn_maps`, `sinnoh`, `sinnohfolk` (Sinnoh townspeople), `orre_maps`, `orre_pilot` (Orre's pilot, 11-20: snagging in trainer battles, the Heart Gauge, Hyper Mode, CALL, Shadow evolution keeping the gauge, then a new Orre game played from Colosseum's opening to leaving Phenac), `orre_b1` (Orre batch 1: Pyrite played - the duel square's Shadows, Cail, the Construction Lot's Gear, the windmill, the jail, the tournament's gate, the bridge, Cipher's hideout to Pyrite Cave), `orre_b2` (Orre batch 2: Pyrite Cave and Miror B., Plusle back to Duking, Fateen, Agate's Eagun, the Relic Cave and Skrub, the Relic Stone), `orre_b3` (Orre batch 3: Mt. Battle - Cipher's takeover and Dakim, the F-Disk, Vander's Time Flute, XD's 100 with their gates, rest points and reception, starting over, Battlus and the Master), `orre_b4` (Orre batch 4: Pyrite's jail and lift, The Under's Kids Grid, Silva, Venus, the built subway and its train, the windmill's Time Flute, the Shadow Pokemon Lab to Ein and the Data ROM), `orre_b5a` (Orre batch 5a: XD's opening act with Wes - Krane carried off, Gateon and the Machine Part, Kaminko's, the Cipher Lab and Lovrina, a Battle CD played), `orre_b5b` (Orre batch 5b: ONBS, Duking's Poke Spots and trades, Miror B. and his radar's missed-Shadow loop, the ONBS raid, Kaminko's crane and the scooter, the S.S. Libra, Pyrite's XD square), `orre_b6` (Orre batch 6: the Pre Gym's Colosseum era, Cipher's Phenac and Snattle, the townsfolk freed, Phenac Stadium's gate, the Outskirt Stand's Miror B., Hordel's Shadow Togepi and Willie, XD's Snagem Hideout), `orre_b7a` (Orre batch 7a: the Orre Colosseum's tournament - XD's challengers, Justy the final - and XD's Cipher Key Lair: Zook and Snagem's Biden at the door, the maze, the Box Rooms' crates pushed to the stairs and onto the moon door's switch, the reset panel, the System Lever and the voltage panel, Smarton, Gorigan, Greevil's screen), `orre_b7b` (Orre batch 7b: Colosseum's Realgam Tower - the lobby's trainers, the old man in the yard, the Admins' four keys with a missed Shadow's second chance, the giant door and healing machine, the Tower Halls' peons, Silva, the lifts and Gonzap, the roof lift, the rooftop run with no healing between - Nascour, Evice - and the Hall of Fame in Realgam's look), `orre_b8a` (Orre batch 8a: Krane's Master Ball and Citadark Isle in seven floors - the dock, the Fortress with Lovrina and its crate wing, the Volcano's moving platforms, the Hook Hall's hooks, lift and glowing drop tiles, outside the Dome, Dome 1F's glass wall and Eldes, XD001 and Greevil; XD001 refused at the Relic Stone), `orre_b8b` (Orre batch 8b: XD after Greevil - Eagun, the Orre Colosseum's seven rounds of four with no healing and a lost round, the Relic Stone's purify leaving no Shadow behind, walking opening Shadow hearts, the Purify Chamber's nine sets, tempo and steps, XD001's best circle and its screen, Miror B.'s last Shadow Dragonite and the radar, Greevil's rematch, the Lucky Egg quest), `dungeon` (shared map engine), `soaring`, `soaring3d`, `giant_volcano`, `canon_species` (every species the source games give in one playthrough: fishing on walked routes, Johto swarms, Orre stones/Plusle, Orange Linking Cord/Tauros, Hoenn Safari water, Lavaridge's Togepi Egg), `kanto_events` (Kanto and Sevii events played on their maps: the Body Slam and Swords Dance tutors, the Lemonade-for-Facade man, the Togepi Egg, the Heracross fan, the Lucky Punch, Dario and Rodette, Lady Selphy's battle and villa, Mt. Ember's password, fishing from a town, FireRed's nine trades; 11-19: the VS Seeker's pose and bubbles, the Hall of Fame and its record, every region's opening talk) |
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
