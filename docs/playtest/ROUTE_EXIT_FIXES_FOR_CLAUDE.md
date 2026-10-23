# Route exit fixes (playtest tree) - handoff

Patch: `route_exit_fixes_playtest.patch` (ASCII, CRLF). Apply it from the outer "Kanto Math Game" folder with `git apply --ignore-whitespace route_exit_fixes_playtest.patch`.
Base: 0746892 + 23 playtest patches + c_01_save_slots_100_playtest.patch.
It touches JSON only: assets/{alola,galar,hoenn,johto,kalos,pokemon,unova}_area_data.json and assets/area_levels.json.

## Sources
- Bulbapedia, List of routes: https://bulbapedia.bulbagarden.net/wiki/List_of_routes (the termini table).
- Bulbapedia per-route pages: Kanto Route 28, Johto Route 46, Johto Route 29, Hoenn Route 123, Galar Route 7/8/9, Alola Route 7/8, and Aether Base.
- Serebii-derived connection data in the local game_reference JSONs (used as a cross-check).
- Bulbapedia blocks direct page fetches from the box, so its content was read through search-result extracts of those same pages.

## Changes
| Region | Change | Gate | Source |
|---|---|---|---|
| Johto | Route 46 next_area set to Route 29 | none | BP Johto Route 46 ("connecting Route 45 and Route 29") |
| Johto | Mt. Silver exit now goes to Kanto Route 28 | unchanged | BP Kanto Route 28 |
| Kanto/Johto | NEW area KANTO_ROUTE_28 (wild, can_fish, Lv 53): Mt. Silver <-> Route 28 <-> Reception Gate. The Reception Gate's "Mt. Silver" entry now reads "Route 28" | beat_johto_champion + has_8_johto_badges (same as the old gate) | BP List of routes: Rt 28, W Mt. Silver / E Reception Gate. The Route 26 side is reached through the gate |
| Johto | Ruins of Alph <-> Union Cave | has_zephyr_badge on the Ruins side | BP List: Route 32 lists both. Canon tunnel from the Ruins to Union Cave |
| Hoenn | Removed 113<->114. Route 113 next_area set to Fallarbor | - | BP List: 113 = Mauville/Fallarbor side, 114 = Fallarbor/Meteor Falls |
| Hoenn | Removed 123<->124. Route 123 goes to Route 122 (one-way side), 121<->122 added, 122->123 added | HM_SURF where water is needed | BP Hoenn Route 123 ("connecting Route 122 and Route 118"); List: 122 = 121/123 |
| Hoenn | Added 128<->129 | existing surf gating | BP List: 128 = 127/129 |
| Unova | Added Route 6 <-> Mistralton Cave | visited_MISTRALTON_CITY | BP List (Route 6 row) |
| Unova | 14<->15: NOT changed (see below). Added 15<->16 (Marvelous Bridge) | visited_UNOVA_ROUTE_15 on the 16 side | BP List (rows 14/15/16) |
| Kalos | Added Route 6 <-> Route 7 | visited_PARFUM_PALACE | BP List (Route 6/7 rows) |
| Kalos | Added 15<->16 | none | BP List |
| Galar | Order is now Hammerlocke - Rt 7 - Rt 8 - Circhester - Rt 9 - Spikemuth. The Route 9 Tunnel links Rt 7 and Rt 9. Hammerlocke<->Route 6 added; the Ballonlea->Rt 7 and Hammerlocke->Rt 9 links were removed | has_dark_badge (tunnel), has_rock_badge (Circhester->Rt 9), has_fairy_badge (Rt 6->Hammerlocke) | BP Galar Route 7/8/9 |
| Alola | Route 8 now connects Route 5 and Route 7; the Konikoni and Aether Paradise exits were removed | - | BP Alola Route 8 ("connecting Route 7 and Route 5"). Aether *Base* is on Route 8; Aether Paradise is not |
| Alola | Konikoni<->Malie removed. The ferry is now Heahea <-> Malie. Heahea <-> Diglett's Tunnel (to Konikoni) added. Konikoni next_area set to Diglett's Tunnel | has_rockium_z_badge (ferry, same as the old gate) | BP Alola Route 8 / Diglett's Tunnel; game_reference |

## Kalos 6<->7 finding
The link was truly missing. No direct Route 6<->Route 7 exit existed under any name. Related links already in the game were Camphrier->Route 7, Parfum Palace->Route 6 and Connecting Cave->Route 7. The link was added in both directions.

## Requested but deliberately not changed
- **Kanto 26<->22:** canon. Both routes connect through the Pokemon League Reception Gate, and that link already exists. The audit flag came from the checker, which did not follow the gate.
- **Kanto 3<->4:** the canon link already exists through Mt. Moon (the MT_MOON_CITY hub / west Route 4). A direct link to the east part of KANTO_ROUTE_4 would let players skip Mt. Moon.
- **Unova 14<->15:** in canon, Route 15 connects only through Black City/White Forest, and neither exists in this game. Removing the link would strand Route 15, so it was kept.
- **Galar Wild Area<->Hammerlocke:** not added, because it would bypass badge gates. Route 6<->Hammerlocke was added instead (canon).

## Non-canon links noticed but not requested (left as-is)
- Fortree<->Route 123
- Ever Grande<->Route 129
- Kalos Route 16->Dendemille
- Konikoni<->Alola Route 7
- MT_SILVER_CITY->Mt. Silver
- Hoenn Route 114 has no Meteor Falls exit

## Verification
- A link checker compared base vs patched exits. Every changed link has its reverse link, every target and next_area exists, and it found 0 problems.
- py_compile passed. Python 3.13.5 was used; 3.14 is not available on the box.
- dev/checks/run_all.sh passed: 24/24, SIM 535 turns with 0 errors, smoke 0 failures, and all 7 region reachability walks had 0 problems.
- battle2 "the Geodude attacked" fails sometimes (2 of 17 runs on the patched tree, 0 of 16 on the base). The cause is the timing-based "lightning-fast answer" flinch, which stops the Geodude from moving. The test runs on HOENN_ROUTE_119, which this patch does not touch, so this is a flaky test, not a regression.
- `git apply --ignore-whitespace --check` passed on a clean playtest copy from both the root and the "Kanto Math Game" folder (-p2). The applied JSON is semantically identical to the fixed tree.

## Black City and White Forest (Unova, added 2026-10-23)

### What was added (all in assets/unova_area_data.json plus area_levels.json)
- BLACK_CITY (town): Pokemon Center (HEAL), Shop, travel to Route 14, Route 15, Black Tower (Areas 1-5) and, once those are cleared, Black Tower Areas 6-10. It is the default city: it is always there after the Unova champion. The Pokemon Center stands in for the Black Tower Doctor. You can leave mid-tower to heal, and beaten trainers stay beaten.
- BLACK_TOWER and BLACK_TOWER_UPPER (indoor dungeons, gauntlet).
- WHITE_FOREST (forest wild route with trainers) and WHITE_TREEHOLLOW (gauntlet), both locked behind the Black Tower.
- Pools: WHITE_FOREST / WHITE_FOREST_PERCENTAGES.
- area_levels: BLACK_CITY 60, BLACK_TOWER 60, BLACK_TOWER_UPPER 68, WHITE_FOREST 60, WHITE_TREEHOLLOW 64.

### Connections (canon: both sit between Route 14 to the north and Route 15 to the west)
- Route 14: the "ROUTE 15" shortcut is removed. It is replaced by Black City (needs can_exit + beat_unova_champion) and White Forest (needs can_exit + black_tower_cleared).
- Route 15: "Route 14" is replaced by Black City and White Forest (black_tower_cleared). Its next_area is now BLACK_CITY.
- Every link has its reverse. There is no direct Black City <-> White Forest link, because canonically they occupy the same spot.
- Story gating: Route 14/15/Undella only open after the Unova champion (the walk shows this), so the champion gate adds no new lock. It matches canon, where Black City's gate opens after the Hall of Fame. Route 15 is not used by any story script, and Route 16 -> 15 is unchanged.

### Gauntlet design (no new code)
- The gauntlet reuses the existing GALACTIC_GAUNTLET action, the same one Team Galactic HQ uses. Trainers fight in trainer_pool order, defeats persist, and you can stop and heal at any time.
- Each "Area" is one gate Trainer followed by one Boss Trainer (ACE_TRAINER, is_boss_battle, 3 Pokemon).
- The Area 5 boss (Ellas) has victory_flag black_tower_cleared. The gauntlet's own completion also sets the flag when the pool is empty.
- Black Tower Areas 6-10 (flag black_tower_upper_cleared) and the White Treehollow (Areas 1-10, flag white_treehollow_cleared) are optional post-unlock gauntlets. Their last boss is Benga, as in canon.

### Unlock condition
- Clear Black Tower Areas 1-5. That is 10 battles, ending with Boss Trainer Ellas, and it sets story flag black_tower_cleared.
- That flag opens White Forest from Route 14 and Route 15, plus Black Tower Areas 6-10.

### Trainer sources
- Boss Trainers: the B2W2 Black Tower / White Treehollow boss names and boss teams by Area, from Serebii (serebii.net/blackwhite2/ Black Tower and White Treehollow pages, saved in /workspace/game_reference/unova/blackcity.json and whiteforest.json). Bulbapedia's Black City, White Forest and Black Tower pages were used through search extracts; Bulbapedia blocks direct fetching.
- Gate Trainers: B2W2's Black Tower gate Trainers draw random Pokemon from EV-focused pools, which are not modelled. Instead, each gate uses a canon Black City / White Forest resident from Black/White 1 (names and species from the same Serebii pages), with a class in the B2W2 gate-Trainer style.
  - Some class/sprite substitutions were needed because those sprites don't exist here: Rich Boy -> GENTLEMAN class with the richboy sprite; Socialite/Lady -> BEAUTY; Backpacker -> PICNIKER/CAMPER; Nursery Aide -> PICNIKER.
  - Two Treehollow gates (Lass Lena with Gardevoir/Gallade, Youngster Shane with Rhyperior) are filler trainers, not canon residents. They were added so that every area has a gate.
- White Forest wild pool: the Black/White 1 White Forest species at 10% each (Pidgey, Nidoran F, Nidoran M, Oddish, Abra, Machop, Magnemite, Gastly, Ralts, Bagon). B2W2's White Forest has no wild grass, so this is the B/W1 list.
  - White Forest trainers: W1 Nursery Aide Briana and School Kid Shaye.

### Scaling
- Canon levels are NOT used. Levels follow the game's existing logic in src/world/levels.py:
  - Trainers get area level +1..3 and bosses +4.
  - After the Unova champion, postgame_area_level makes everything follow the player (the check shows a boss at 70-72 in the test save).
  - Legendaries in teams (Ira's Articuno/Entei, Harmony's Victini, Benga's/Iria's legendaries etc.) use the game's fixed LEGEND_LEVEL.

### Skipped
- The EV feature (as asked).
- The Doctor heal (replaced by the Pokemon Center).
- The B2W2 random-pool gate teams.
- Janna/Jariel (rematch-only bosses).
- Hint/shortcut mechanics.
- Tower-only items/rewards (rewards are Poke Balls, like other trainers).

### Tests
- dev/checks/walk_unova.py has a "Black City / White Forest" block. It checks:
  - the post-champion unlock and the pre-champion lock;
  - that the 14<->15 shortcut is gone;
  - the gate/boss order and the Ellas flag;
  - that the gauntlet button shows;
  - level scaling;
  - that clearing the tower sets black_tower_cleared;
  - that White Forest, the Treehollow and Areas 6-10 open;
  - all four reverse links.
