# AREAS EXPANSION - handoff for Claude
Generated Fri Oct 23 2026, 12:08 PM PDT. Scope: every Tier 1-3 area from routing_audit/missing_areas.md, plus the region-tag case cleanup.

## Apply order
Apply these on top of route_exit_fixes_playtest.patch, in order. Each one is ASCII with CRLF line endings, and passes
`git apply --ignore-whitespace --check` against the previous step:

1. areas_01_sinnoh.patch
2. areas_02_kalos.patch
3. areas_03_paldea.patch
4. areas_04_alola.patch
5. areas_05_unova.patch
6. areas_06_hoenn.patch
7. areas_07_johto.patch
8. areas_08_kanto.patch
9. areas_09_sevii.patch
10. areas_10_kitakami.patch
11. areas_11_terarium.patch
12. areas_12_galar.patch
13. areas_13_region_case.patch

Command: `git apply --ignore-whitespace areas_NN_*.patch`

## Verification (after each patch, and on the full stack)
- py_compile on every changed .py file.
- dev/checks/run_all.sh: "##### 0 failures". On the full stack, the walks for johto, hoenn, sinnoh, unova, kalos, alola, galar, paldea
  and kanto all report 0 problems, and the simulator reports 0 errors.
- The walks check that each added area is reachable with the right story state, that no exit is dangling, that every link goes both ways,
  and that each gate stays locked until its badge, item or flag.

## Global rules and assumptions
- Content is canon: canon links (bidirectional, with canon gates), canon wild pools, canon trainers with this game's level scaling, and area_levels.json entries.
- Gym leaders, Elite Four and Champions use their canon teams. Legendaries are cap+3 before the 8th badge and L70 after it.
- Battle facilities and team hideouts are GALACTIC_GAUNTLET gauntlets. There are no EV features.
- The reference library (/workspace/game_reference) is the primary source. Serebii Pokearth was used where the library had no wild data:
  Hoenn ORAS areas, Unova B2W2 areas, Paldea, Kitakami and the Terarium. Those Serebii pools have no rates, so they use equal weights.
- Trainer classes with no matching sprite use class fallbacks. These are PLACEHOLDERS and are listed per region below.
- Nothing was committed or pushed to the real repo. All work was done in a local scratch repo.

## Per-region adds, sources, assumptions, placeholders and uncertain items

## areas_01_sinnoh.patch - Sinnoh (30 areas)
Sources: Serebii pages in game_reference/sinnoh (Platinum tables preferred, BDSP for Grand Underground/Maniac Tunnel); Bulbapedia List of routes for connections.
Added: Routes 219, 220, 221; Battle Zone: Fight Area, Survival Area, Resort Area, Routes 224-230 (Route 224 from Victory Road, also to Flower Paradise in place of Seabreak Path); Battle Frontier (gauntlet); Distortion World (gauntlet vs Cyrus); Wayward Cave, Lost Tower, Floaroma Meadow, Fuego Ironworks, Ravaged Path, Maniac Tunnel, Trophy Garden, Acuity/Valor/Verity Lakefronts, Sendoff Spring, Oreburgh Gate, Galactic Eterna Building (gauntlet), Galactic Warehouse (gauntlet), Grand Underground.
Gates: Battle Zone ferry from Snowpoint City, Route 224, Trophy Garden, Sendoff Spring (and Turnback Cave -> Sendoff Spring): beat_sinnoh_champion. Distortion World from Spear Pillar: spear_pillar_resolved. Route 220/230 and Fuego Ironworks from Route 205: HM Surf. Ravaged Path: Coal Badge (Rock Smash). Eterna Building: Forest Badge; Warehouse: Cobble Badge.
Stark Mountain: the non-canon Sunyshore ferry link was removed both ways; Stark Mountain is now reached by canon Route 227 (still post-champion).
Skipped: Ramanas Park (every canon encounter is a legendary already hosted elsewhere, so it would be an empty area), Battle Park (BDSP duplicate of the Battle Frontier role), Spring Path / Seabreak Path (connector corridors folded into links), Pal Park (not requested).
Placeholders / uncertain:
- Battle Frontier gauntlet: the reference only lists 3 Frontier Brains (Palmer, Dahlia, Darach) - Argenta and Thorton are not in the data, so they are not included. Brains use master.png (no brain sprites). Palmer is last (boss).
- Galactic Eterna Building / Warehouse use their own clear flags (eterna_galactic_building_cleared, galactic_warehouse_cleared); they do NOT set galactic_eterna_cleared or give the Galactic Key, so the existing story path is unchanged.
- Distortion World has no Giratina boss (Giratina stays at Turnback Cave to avoid a second copy).
- Floaroma Meadow (honey trees only) and Verity Lakefront (no canon wild table) have no wild pool; Verity Lakefront is a pure connector.
- Wayward Cave entry ungated (canon Strength/Flash requirement not modelled).
- area_levels: canon Serebii median levels except early-access areas pinned to neighbours (Fuego 18, Floaroma Meadow 14, Grand Underground 15 - BDSP scales GU by badges), Battle Frontier 60.
Level fix: Ravaged Path is area level 8, the same as Route 204. It is still gated by the Coal Badge (Rock Smash). The patch already had 8; only this note was missing it.

## areas_02_kalos.patch (Kalos, 10 areas)
Adds: KALOS_ROUTE_20, KALOS_ROUTE_21, KALOS_ROUTE_22, KILOUDE_CITY, BATTLE_MAISON_KALOS, AZURE_BAY, SEA_SPIRITS_DEN, BATTLE_CHATEAU, LYSANDRE_LABS, KALOS_POWER_PLANT.
Sources: game_reference/kalos (Serebii X/Y). Connections were checked against Bulbapedia (via search): Route 21 is Snowbelle to the Victory Road gate; Route 22 is Santalune to the Victory Road gate; Kiloude is reached by train from Lumiose.
Gates:
- Route 22: Santalune and Lumiose, ungated. Its Victory Road exit needs Iceberg Badge + HM Waterfall + HM Strength (same as the existing link).
- Route 21: Snowbelle to Victory Road, same gate.
- Route 20: Snowbelle to Pokemon Village, which still needs beat_kalos_champion.
- Kiloude City and the Battle Maison: beat_kalos_champion (train from Lumiose).
- Azure Bay: HM Surf from Route 12. Sea Spirit's Den (Articuno boss, L70 as a legendary): beat_kalos_champion.
- Battle Chateau: from Route 7, ungated.
- Lysandre Labs: Psychic Badge, from Lumiose. Grunts, then Lysandre.
- Kalos Power Plant: Plant Badge, from Route 13. Grunts, then Aliana.
Assumptions and placeholders:
- UNCERTAIN: Route 22 to Lumiose follows Jordan's note. In canon, Route 22's other end is the Victory Road gate, not Lumiose.
- Route 22 is set to area level 6, not Serebii's 25 median. It is reachable from Santalune right away, and the Serebii median mixes in high-level encounters.
- Kept the existing direct "Route 20 / Pokemon Village" link from Snowbelle. Removing it would need a non-ASCII hunk (the e-acute). It is champion-gated like Route 20.
- Sea Spirit's Den: canon has all three birds at L70. Only one area_boss is supported, so it is Articuno.
- Battle Chateau: the reference has no Grand Duke. The gauntlet is the 10 nobility ranks (Baron to Duchess) and the last one is the boss.
- Battle Maison: 4 Battle Chatelaines (Nita, Evelyn, Dana, Morgan), and the last one is the boss.
- Skipped: Xerosic, Essentia and the Lumiose Gang (post-game Looker quest). Lysandre Labs' Xerosic battle is not included.
- Lib change: sid() now maps form names such as "Aegislash"/"Meowstic" to the base species ("aegislash-shield", "meowstic-male").
Tests: walk_kalos expansion 0 problems; Kiloude/Sea Spirit/Village gate ok; Route 22 early/Victory Road gate ok; run_all 0 failures (24/24, SIM 513 turns 0 errors).

## areas_03_paldea.patch (Paldea)
Adds 17 areas and 16 bidirectional link pairs.
- Team Star base gauntlets use GALACTIC_GAUNTLET, with the boss last. Each sets its existing flag and needs met_team_star:
  - SEGIN (via West Province Area 1): Giacomo, level 20.
  - SCHEDAR (via East Province Area 1): Mela, level 26.
  - NAVI (via Tagtree Thicket): Atticus, level 31.
  - RUCHBAH (via North Province Area 3): Ortega, level 50.
  - CAPH (via North Province Area 2): Eri, level 54.
- Routes, towns and sea areas:
  - SOCARRAT_TRAIL (via Casseroya Lake), level 40.
  - DALIZAPA_PASSAGE (via Glaseado Mountain), level 37.
  - SOUTH_PROVINCE_AREA_4 (connects to SPA1, SPA2, WPA1, SPA6, Inlet Grotto and the South Sea), level 8.
  - SOUTH_PROVINCE_AREA_6 (connects to SPA4, Alfornada and Alfornada Cavern), level 18.
  - INLET_GROTTO (connects to Route 1, standing in for Poco Path, and SPA4), level 5.
  - PORTO_MARINADA town (connects to WPA2 and the West Sea), level 22.
  - The four seas, levels 8/22/12/40.
- GREAT_CRATER_OF_PALDEA (via Area Zero) is champion-gated, level 60.

Sources:
- Bulbapedia for the area parents and connections.
- Serebii Pokearth "Standard Pokemon" species lists (/workspace/areas/serebii_paldea.json) for the wild pools. These lists have no rates, so the weights are equal. Levels are estimated from neighbouring areas and the level cap.

Placeholders:
- Team Star grunts and the Courier, Poke Maniac, Model and Office Lady trainers use existing class sprites.
- Gym Trainer Hugo was skipped.
- The original Team Star EVENT nodes are kept, so each squad flag can now be set two ways.

Uncertain:
- North Paldean Sea is linked to Casseroya.
- Inlet Grotto's link to Route 1 stands in for Poco Path.

## areas_04_alola.patch (Alola, SM/USUM)
Adds 46 areas and 35 link pairs. Connections come from game_reference/alola/*.json `connections`. Wild pools and trainers come from the same references, preferring USUM. Captains, kahunas, Hau, Gladion, Guzma and Lillie are left out of the route trainer pools.

Melemele (after Verdant Cavern):
- Route 3, linked to Routes 1 and 2 and Melemele Meadow.
- Melemele Meadow, Seaward Cave and Kala'e Bay.
- Hau'oli Cemetery, linked to Route 2.
- Big Wave Beach (a town node with no pool), linked to Route 2 and Sandy Cave.

Akala:
- Paniola Town (town with a center), Paniola Ranch and Route 6.
- Royal Avenue: trainers only.
- Hano Grand Resort (town), linked to Heahea City and Hano Beach.
- Heahea Beach, linked to Heahea City.
- Route 9, linked to Konikoni City, Memorial Hill and Diglett's Tunnel.
- Akala Outskirts, linked to Memorial Hill and to Ruins of Life (champion-gated).
- Dividing Peak Tunnel, linked to Routes 7 and 8.

Ula'ula:
- Malie Garden.
- Route 12, linked to Route 11, Secluded Shore, Ula'ula Beach, Route 13 and Blush Mountain.
- Route 13, linked to Haina Desert and Tapu Village.
- Hokulani Observatory (town), linked to Mount Hokulani.
- Aether House, linked to Route 15.
- Ula'ula Meadow, linked to Routes 16 and 17.

Mantine Surf beach chain:
- Big Wave Beach to Heahea Beach needs Rockium Z.
- Heahea Beach to Ula'ula Beach needs Rockium Z.
- Ula'ula Beach to Poni Wilds needs Darkinium Z.

Poni:
- Exeggutor Island, linked to Seafolk Village.
- Poni Wilds, Ancient Poni Path (also linked to Vast Poni Canyon) and Poni Breaker Coast.
- Post-champion, entered from Ancient Poni Path: Poni Grove, Plains, Meadow, Coast and Gauntlet.
- Resolution Cave has a Zygarde boss (718) at level 70.
- Battle Tree is a GALACTIC_GAUNTLET of Red then Blue (USUM teams), flag battle_tree_cleared.

Team Rocket's Castle:
- Entered from Aether Paradise, champion-gated.
- Gauntlet of 3 Rainbow Rocket Grunts, then Archie, Maxie, Cyrus, Lysandre, Ghetsis and Giovanni (boss). Flag rocket_castle_cleared.

Ultra worlds (from Ultra Space, champion-gated): each is a boss-only dungeon at level 70.
- Ultra Deep Sea: Nihilego.
- Ultra Jungle: Buzzwole.
- Ultra Desert: Pheromosa.
- Ultra Plant: Xurkitree.
- Ultra Crater: Celesteela.
- Ultra Forest: Kartana.
- Ultra Ruin: Guzzlord.
- UB assignments are from Serebii.

Levels follow the canon trainer median where one exists (most areas match within a few levels). The exceptions:
- Heahea Beach is set to 20; the canon median of 35 comes from Mantine Surf.
- Aether House is set to 33; the canon median is 42.
- Resolution Cave and the Ultra worlds are set to 70, the post-8th-badge legendary rule.

Data unavailable (no pool, flagged rather than invented):
- The references have no wild data for Route 9, Route 13, Heahea Beach or Resolution Cave, so those areas have no wild pool.
- The Ultra worlds also have no wild data.

Skipped:
- Megalo Tower and Ultra Megalopolis: Ultra Necrozma would duplicate the existing ULTRA_SPACE Necrozma boss, and Poipole is a gift.
- Ultra Space Wilds: legendary interactions only.
- Plains Grotto, the Lakes of Sunne/Moone and the Ruins of Abundance/Hope: no host area exists. The links Haina Desert to Ruins of Abundance, Breaker Coast to Ruins of Hope, and Ula'ula Meadow to the Lakes are therefore omitted.
- Battle Tree's Battle Legends and the Kartenvoy trainer.

Placeholders:
- Several USUM trainer classes (Actor, Sightseer, Police Officer, Bellhop, Pro Wrestler, Ultra Recon Squad, "X User", Rainbow Rocket Grunt, Ghetsis) use existing class sprites.
- Veteran Leon was forced to veteran.png, because the name matched the Galar champion sprite.
- Giovanni uses leader_giovanni.png.

Observed, not changed: in the base, Route 16 links to Seafolk Village ungated, so Poni is already reachable with Rockium Z.

Checks:
- dev/checks/walk_alola.py has the expansion and gate checks appended: 0 problems.
- run_all: 0 failures, 24/24.
- One run showed a flaky battle2 "the Geodude attacked" failure (a Kanto battle check, unrelated). Two reruns were clean.

## areas_05_unova.patch (Unova, BW/B2W2)
Adds 21 areas and 18 link pairs. Trainers come from game_reference/unova, preferring B2W2. Wild species come from Serebii Pokearth (scraped into serebii_unova.json; standard grass/surf/fish species only, no encounter rates). Rival, Cheren, Alder, gym leaders, Colress, Zinzolin, Julius, Hugh and Bianca are left out of the route trainer pools. Swimmers use swimmer sprites.

Early B2W2 (ungated side branch):
- Virbank City (town, off Castelia), Virbank Complex, Route 20, Floccesy Ranch, Floccesy Town, Route 19 and Aspertia City. Levels 5-13.
- Relic Passage: Castelia Sewers <-> Relic Castle. The Relic Castle exit needs the Bolt Badge. L22.
- Tubeline Bridge: Route 8 <-> Opelucid. The Opelucid exit needs the Freeze Badge. L33.
- Lentimas Town (entry from Mistralton needs the Jet Badge), Reversal Mountain (exit to Undella needs the champion flag) and Strange House. L30-32.

Post-champion (beat_unova_champion):
- Humilau City, linked to Routes 21 and 22, to Undella (standing in for the Marine Tube), to the Plasma Frigate and to the Nature Preserve.
- Undella Bay and Seaside Cave.
- PLASMA_FRIGATE gauntlet: 3 grunts, then Shadow, Zinzolin and Colress (boss). Sets plasma_frigate_cleared.
- Nature Preserve (L65), Marvelous Bridge (Route 16 <-> 15, L60), Village Bridge (Route 11 <-> 12), Challenger's Cave (off Victory Road) and Clay Tunnel (off Driftveil, L60). East side L52-55.

Assumptions and uncertain items:
- No B2W2 gyms were added, because the badge set is fixed to BW1.
- Left out: PWT, Pokestar Studios, Cave of Being and Abyssal Ruins.
- The Marine Tube is collapsed into a direct Humilau <-> Undella link.

## areas_06_hoenn.patch (Hoenn, ORAS with Emerald fallbacks)
Adds 16 areas and 11 link pairs. Trainers come from game_reference/hoenn, preferring the ORAS pages and falling back to the Gen 3 (.3rd) pages. Wild species come from Serebii Pokearth (serebii_hoenn.json; static/"interact" encounters are excluded; no rates). The lib change is that Region.order lets ORAS pages win over .3rd. lib also gains `ship()`, a ship template (a cabin gauntlet docked at each port), which S.S. Tidal uses now and S.S. Aqua/S.S. Anne will reuse. Build specs can also carry `events` (EVENT menu items).

Story-side:
- Magma Hideout: a gauntlet off Jagged Pass that needs the Feather Badge. 3 grunts, then Tabitha, then Maxie (boss), using the Emerald team because the ORAS page has no Maxie/Tabitha. Sets magma_hideout_cleared. L33.
- Mirage Tower: off Route 111, needs the Heat Badge (Go-Goggles stand-in). L24.
- Altering Cave (Route 103), Sea Mauville (Route 108) and Scorched Slab (Route 120). Each needs HM Surf. L16, L30 and L28.
- S.S. Tidal: Slateport <-> Lilycove, boarding needs the Balance Badge. A 6-trainer cabin gauntlet that sets ss_tidal_cleared. L30.

Post-champion (beat_hoenn_champion):
- Sealed Chamber: off Route 134, also needs Surf. It has a READ THE BRAILLE event that sets regi_trio_awakened. The base data's Desert Ruins, Island Cave and Ancient Tomb Regi BOSS options needed that flag, but nothing ever set it, so before this patch they could not be reached.
- Desert Underpass: off Route 114.
- Battle Frontier: from the S.S. Tidal. A GALACTIC_GAUNTLET of the Frontier Brains' first listed (Silver) teams: Anabel, Tucker, Spenser, Greta, Lucy, then Brandon as the boss. Sets hoenn_battle_frontier_cleared. L65.
- Artisan Cave: off the Battle Frontier.
- Battle Resort: off Ever Grande City. L60.
- Soaring in the Sky: off Mossdeep (Space Center). From it you reach Mirage Cave, Mirage Forest, Mirage Mountain and Mirage Island (L55).

Assumptions and uncertain items:
- Battle Resort's real sea route is not modelled; Ever Grande is a stand-in host.
- Factory Head Noland is left out because he uses rental teams and has no fixed party.
- I assumed which reference entries are the Silver teams.
- The Frontier Brain sprites are generic ace trainers. Bug Maniac uses bug_catcher.png.
- Left out:
  - Southern Island and the Regi chambers, which already exist as BOSS options;
  - legendary-only spots: Nameless Cavern, Pathless Plain, Trackless Forest, Gnarled Den, Fabled Cave, Crescent Isle, Terra Cave and Marine Cave;
  - Battle Maison (no named trainers) and Trainer Hill (no reference data);
  - event islands: Birth Island, Navel Rock and Faraway Island;
  - Secret Base spots.

## areas_07_johto.patch (Johto, HGSS)
Adds 6 areas and 5 link pairs. Connections, wild pools and trainers come from game_reference/johto (the HGSS pages).

- Route 47: links Cliff Edge Gate <-> Route 48 and leads to Cliff Cave. L40, 4 trainers. Camper Grant's sprite is forced to camper.png because "grant.png" is the Kalos leader.
- Route 48: links Route 47 <-> the existing Johto Safari Zone. L40. The base's direct Cliff Edge Gate -> Safari Zone link is kept.
- Cliff Cave: L40. Its exit to Embedded Tower is champion-gated.
- Embedded Tower: Groudon (383) BOSS, L70 (post-8th-badge rule). This is the HeartGold choice; SoulSilver would be Kyogre, and the game has no HG/SS version flag.
- S.S. Aqua: built with lib.ship(), the shared ship template. It is a 6-trainer cabin gauntlet docked at Olivine City and Vermilion (key VERMILLION_CITY), and boarding needs has_item:SS_TICKET. Sets ss_aqua_cleared. L40. The existing long_ride ferry options are untouched.
- Battle Frontier: a champion-gated gauntlet off Route 40, with Frontier Access collapsed into it. It has Tower Tycoon Palmer, Arcade Star Dahlia and Castle Valet Darach (boss). Sets johto_battle_frontier_cleared. L65.

Assumptions and uncertain items:
- The Johto Battle Frontier page lists no teams, so I used the Platinum teams from game_reference/sinnoh/battlefrontier.json.
- Factory Head Thorton and Hall Matron Argenta are missing because they are not in any reference.
- The Frontier is champion-gated as a level-curve choice.

## areas_08_kanto.patch (Kanto, FRLG)
- KANTO_SS_ANNE: S.S. Anne, built with lib.ship(). It is a cabin gauntlet docked at Vermilion (VERMILLION_CITY), and boarding needs has_item:SS_TICKET. It has 5 FRLG cabin trainers, then Rival Blue as the boss (the first of the three starter-dependent teams). Sets ss_anne_cleared. L18.
- New dev/checks/walk_kanto.py checks the ticket gate, the gauntlet flag and that Vermilion <-> S.S. Anne links both ways. It is wired into run_all.sh's walk loop.

## areas_09_sevii.patch (Sevii, FRLG)
Region tag is KANTO and subregion is SEVII. Level 55 is the post-game level.

Added areas:
- Canyon Entrance (Two Island)
- Green Path and Outcast Island (Three Island)
- Altering Cave (Six Island)
- Water Path
- Memorial Pillar (Five Island)
- Resort Gorgeous (Six Island)

Each area has FRLG wild pools and trainers, scaled. There are 8 links, all bidirectional, and the water links are gated by Surf.

Skipped:
- Trainer Tower: it already exists as the Seven Island GYM action.

Sprite overrides:
- Bird Keeper (the default milo.png collided with the Galar gym leader)
- Swimmer F
- Psychic

Checks: sevii_body expects 31 areas (was 24) and now checks the new links and that no new area is a dead end.

## areas_10_kitakami.patch (Kitakami, The Teal Mask)
- Adds 12 areas to paldea_area_data.json (region "paldea"):
  - Mossui Town (town). Joins the existing KITAKAMI hub.
  - Kitakami Hall (town, no center).
  - Apple Hills, Mossfell Confluence, Oni Mountain, Infernal Pass, Fellhorn Gorge, Oni's Maw, Chilling Waterhead, Wistful Fields.
  - Crystal Pool and Dreaded Den (gated, see below).
- Links: links from new areas to existing Reveler's Road, Paradise Barrens and Timeless Woods go both ways.
- Gates: Crystal Pool (from Oni Mountain) and Dreaded Den (from Timeless Woods) both need all three Loyal Three boss flags. This matches the existing Masked Ogre/Pecharunt gating.
- Levels are 62-68, matching the existing Kitakami areas (62-66).
- Wild pools: species are from the reference library (kitakami.md), ordered so that the species Serebii Pokearth lists for the area come first. Only the first 14 are used. There are no rates, so all weights are equal (ASSUMPTION).
- Trainers: from reference kitakami/*.json, deduplicated (each trainer appears twice: story version and post-game version). PLACEHOLDER sprites: Festival Boy/Girl, Glitterati, Ogre Clan and Ruffian use the acetrainer/hiker class fallbacks.
- UNCERTAIN: the exact map adjacency is approximate (Mossfell Confluence is treated as the central river hub). Serebii lists no connections for these areas.
- Mossui Town has no trainers: its reference trainers are the Carmine/Kieran story battles, which already exist in KITAKAMI.
- Checks: walk_paldea.py has new Kitakami expansion and gate checks. run_all: 0 failures.

## areas_11_terarium.patch (Terarium biomes, The Indigo Disk)
- Decision: the biomes are separate areas, and the existing TERARIUM area is kept as the entry dome.
- Adds 7 areas to dlc_area_data.json:
  - Central Plaza (town, with a center). It links both ways with TERARIUM and with each of the four biomes.
  - Savanna, Coastal, Canyon and Polar Biome. Coastal and Polar can be fished.
  - Torchlit Labyrinth (off Canyon) and Chargestone Cavern (off Polar). UNCERTAIN which biome each cave hangs off.
- Levels are 72-75. The reference canon level is 74-75; the existing Terarium is 70.
- Gating is inherited from TERARIUM/BLUEBERRY_ACADEMY (beat_paldea_champion plus KITAKAMI_boss_defeated). No new gates.
- Wild pools: the blueberry.md species lists, with Serebii-listed species first; the top 14, equal weights (ASSUMPTION).
- Trainers: the League Club members from the reference, up to 6 per biome. The BB Elite Four are excluded because they already exist in BLUEBERRY_ACADEMY. Each biome has one League Club trainer pool. PLACEHOLDER sprites: acetrainer_m/f.
- Checks: walk_paldea.py has a Terarium expansion check and a hub link check. run_all: 0 failures.

## areas_12_galar.patch (Galar small spots, Sword/Shield)
- Motostoke Outskirts: Sword/Shield wild pool and trainers (Madame Caroline, Police Officer Raymond). Links both ways with MOTOSTOKE. Entering from Motostoke needs has_grass_badge (canon: you reach Hulbury after Turffield).
- Galar Mine No. 2 (dungeon, can fish): Sword/Shield pool. Trainers are Bede, the workers, Team Yell Grunts and Rail Staff Vincent. Links Outskirts <-> HULBURY both ways.
  - Hop is OMITTED because his teams are starter-dependent. UNCERTAIN: a Hop battle may be wanted here later.
- Meetup Spot: a Wild Area station town linked with WILD_AREA, with a center and shop. The Let's Go Pikachu/Eevee gift is not modelled because it depends on a Let's Go save (not applicable).
- Levels follow this game's scaling (15/16/12) rather than canon (24), so they fit between MOTOSTOKE (12) and HULBURY (15).
- Placeholder sprites: Team Yell Grunt, Rail Staff and Police Officer use the class fallbacks.
- Checks: walk_galar.py has a badge gate check, an expansion check and a Hulbury link check. run_all: 0 failures.

## areas_13_region_case.patch (cleanup only, no content changes)
- Patches 01-12 wrote area "region" tags in lowercase (for example "alola"). The base data is all uppercase.
- This patch uppercases all 169 of those values, in 10 asset files. No other lines change.
- It is safe: the base data had 0 lowercase region tags, so every changed value came from this expansion. All readers already call .upper(). run_all passes with 0 failures and every walk reports 0 problems.
- The generator (lib.py) now writes uppercase directly, so future regions need no cleanup.
