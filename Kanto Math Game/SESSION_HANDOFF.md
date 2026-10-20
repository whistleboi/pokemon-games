# Kanto Math Game: session handoff (as of 2026-10-19)

**Repo:** `C:\Users\Dad\Games\Python Games\pokemon-games\Kanto Math Game\Kanto Math Game` (git, branch `main`). All work is committed locally and nothing has been pushed. The latest commits are listed newest first:

- `f439bc7` Sinnoh Poffins: berries, berry trees, Poffin House cooking and Poffin Case
- `30fb4b8` Pokémon Contests: halls, Pokéblocks, math-powered appeals and ribbons
- `2c86b6b` Leave Speed out of the battle stat modifier
- `1ece894` Real HP stats, percentage damage, and stat modifiers
- `537c235` Pick each attack's move by power × effectiveness × weather
- `889c2eb` Battle weather with modern 5-turn rules and weather rocks
- `0b4ae09` Day/night encounter tables for Johto, Sinnoh, Alola, Paldea
- `16148eb` Johto-start players unlock Kanto the reverse way
- `257c49a` Post-champion move: Mom buys a new home in a region you choose
- `17f24c7` Regional fossils as gym rewards with fossil labs, plus reward and badge crash fixes
- `6d462c9` Kanto/Johto audit: every Gen 1–2 species obtainable, plus badge-check fixes
- Earlier commits cover the region audits (Sinnoh `b8eed60`, Unova `bdd167f`, Kalos `5dc9fc9`, Alola `be53309`, Galar `6e83129`, Paldea `1105710`).

## What the game is

It's a Pygame Pokémon game where battles are won by answering math problems. It covers all nine regions, Kanto through Paldea.

The data lives in JSON region files under `assets/`, named `pokemon_area_data.json` (Kanto), `johto_area_data.json`, `hoenn_…`, `sinnoh_…`, `unova_…`, `kalos_…`, `alola_…`, `galar_…` and `paldea_…`. They are merged in that order in `src/core/game.py`. `STORY_PROGRESSION` is merged as a dict, and other top-level keys use `update`.

**Main code files:**

- `src/states/battle.py`: battles
- `src/states/overworld.py`: towns, routes, NPCs
- `src/states/menus.py`: region, rival and starter selection
- `src/states/systems.py`: Bag, Mart, Pokédex, badge case, fossils
- `src/world/story.py`: StoryManager, saves, flags
- `src/pokemon/data.py`: Pokemon class, XP and HP
- `src/pokemon/contest.py`: contest rules (categories, ranks, Pokéblocks, Feebas Beauty check)
- `src/states/contest.py`: Contest Hall lobby, contest screen, Lilycove Museum text
- `src/pokemon/poffin.py`: berries, Poffin cooking formula, Poffin feeding
- `src/states/poffin.py`: Poffin House, cooking screen, Poffin Case
- `src/pokemon/loader.py`, `src/core/assets.py`, `src/vfx/renderer.py`, `src/ui/panels.py`

## Data schema (keep new content in this shape)

- **Towns:** `travel_options` and `explore_options`, each entry with `text` and `action`. Actions are NPC, RANDOM_NPC, HEAL, SHOP, GYM or TRAVEL. Conditions can be lists, which are ANDed.
- **Routes and dungeons:** a `route_menu` with actions CATCH, BATTLE, TRAINER, BOSS, EXIT, FISH, HEADBUTT, MAX_RAID, NPC or GALACTIC_GAUNTLET.
- **Gyms:** `gym.leader` is a dict containing `badge_reward`, `rewards` (written as `{ITEM: qty}`), `dialogue` and `victory_flag`.
- **Optional area keys:**
  - `region` and `area_type` (town, wild_route or dungeon)
  - `battle_type`
  - `wild_pool_percentages`, `day_pool_percentages`, `night_pool_percentages`
  - `max_raid_den`, `department_store`, `weather`
- **`REGION_START` per region:** order, subtitle, start_area, starters, intro_text, starter_text, newgame_text, mom_home_text, mom_newstart_text, dex_range, dex_extra, badge_images.
- **Formatting:** Kanto and Johto JSON files are hand-formatted, so edit them by text insertion only. The other region files are machine-formatted with `dumps()` from the scratchpad's `link_regions.py`.

## Systems built (all working)

- **New game in any region:**
  - The start screen shows all nine regions in a 3×3 grid.
  - Kanto and Johto keep their original lab rival flow.
  - Hoenn onward hand off to the start town, where an `on_enter_event` rival battle runs.
  - Starter rival battles use only Normal moves (`STARTER_MOVES` in battle.py), and losing proceeds instead of looping.
- **Champion and moving regions:**
  - Becoming Champion triggers a one-time phone call from Mom, who offers to move. The player can also ask Mom at home.
  - The move uses `RegionSelectionState(mode="move")` and has a STAY HERE option.
  - Entering any area calls `story.enter_region`, which immediately unlocks that region's badge page and Pokédex section.
  - Helpers: `champion_flag(region)` (Kanto's is `beat_champion`, others are `beat_<r>_champion`), `is_region_champion`, `move_to_region` and `has_badge`.
- **Johto start, then Kanto:** a Johto Champion visiting Oak gets the National Dex, the Kanto badge case and a Kanto starter choice. Elm won't give a second Johto starter.
- **Dex coverage:** every species from Gen 1–9 is obtainable in its own region. Non-generation species may appear anywhere. A few later-generation evolution exceptions get spaces in the regional dex. The Paldean form sprites are IDs 2055–2058 (`.png`).
- **Johto starters:** they stay as rare wild encounters (the user decided this): Chikorita in the Johto Safari Zone, Cyndaquil in Burned Tower, Totodile at the Whirl Islands.
- **Real levels (replaced stages, sub-stages, wins and badge stage caps):**
  - Each Pokemon stores `level` (1-100), `xp` (into the level), `friendship` and `counters` (battle feats). Saves store all four; old saves convert stage + XP to a level (`Pokemon.legacy_level`).
  - Fast XP: a level costs 10 XP below Lv 20, then 15/20/30/40 per band of 20 (2,250 XP from Lv 5 to 100). A win is 10 XP, +-25% per 4 levels of gap, -25% for a stat-weak foe, x1.5 from trainers (`Pokemon.battle_xp`). Level-ups show "grew to Lv N!" and newly learned same-type moves. Rare Candy = +1 level.
  - Data: `assets/pokemon_levels.json` (built from PokeAPI): `pairs` "fromId>toId" -> evolution rule, `min_level` per species (default level for gifts/starters/fossils), `learnsets` per species id. `assets/area_levels.json`: wild level per area (real encounter levels for 270 areas, hand-set for Paldea and story areas, towns from neighbours). Builders: scratchpad `build_levels.py`, `build_area_levels.py`, `finish_area_levels.py`.
  - Opponents (`src/world/levels.py`): wild = area level -2..+1; route trainers area +1..3 (+4 for bosses/rivals/villain leaders); gyms by canonical order and ace levels (`GYM_ORDER`, `GYM_ACE`), Elite Four ladder, Champion ace; legendaries fixed (box legends 70, others 50, Deoxys/Arceus 80); Max Raids by star 15/25/35/50/65 with double HP.
  - Evolution (`src/pokemon/evolution.py`): real levels; items from the Bag (Kanto stand-ins kept; plain trades use a LINKING_CORD; new items join EVOLUTION_ITEMS so marts stock them); friendship = catch 5 Pokemon with it in the party (or Soothe Bell); time of day; known move by level; party species/type; rain; Feebas beauty; battle feats (3 crits in a battle, 49+ damage in a won battle, 20 attacks, 10 wins, 3 Bisharp, 20 catches for Meltan); $9,999 for Gimmighoul; Nincada leaves a Shedinja. Regional-only evolutions stay with regional forms. The catch-5 evolution was removed. The summary page shows how each Pokemon evolves.
  - Damage (`src/pokemon/balance.py`): the main-series formula step by step with the games' rounding: base = floor(floor(floor(2Lv/5+2) x Power x A/D)/50)+2, then weather, crit (1/24, x1.5), random 85-100%, STAB x1.5, type. Stats at level = 2xBasexLv/100+5. Sandstorm raises Rock Sp. Def x1.5 (special moves) and snow raises Ice Defense x1.5 (physical). No caps, no stat-tier modifiers, no Mega bonus (the user removed them); Dynamax raid bosses keep double HP.
  - Moves are level-gated by the learnset (TM/tutor moves from Lv 40); the strongest same-type move is still picked by power x type x weather.
  - Level cap option (Options screen button, `story.level_cap_mode`, saved): STORY (default) = XP and Rare Candy stop at the next Gym Leader's ace level in the region (Champion's ace after 8 badges, none after becoming Champion); OBEDIENCE = no XP cap, but Pokemon above Lv 20 + 10 per region badge ignore you with chance (L-cap)/(L+cap); NONE = uncapped. Test: `check_levelcap.py`.
  - Battle HUD shows "Lv N" for both sides; the XP bar fills per level (gold at Lv 100). Party shows levels.
  - Tests: `check_levels.py` (replaces the retired `check_realhp.py` and `check_xp_silph.py`, which tested the stage system).
- **Weather (modern rules):**
  - A battle in a weather area starts with that weather for 5 turns, or 8 if the player owns the matching rock.
  - Rain: Water ×1.5, Fire ×0.5. Sun is the reverse.
  - Sand: 1/16 chip per turn to anything not Rock, Ground or Steel. The chip never knocks out (it stops at 1 HP). Rock-types take ×⅔ damage.
  - Snow: Ice-types take ×⅔ damage, no chip.
  - The battlefield gets a tint and particles, and a turn counter shows at the top center.
  - Galar's Wild Area (`weather: "RANDOM"`) gets different weather each day.
  - **Weather rocks** (Damp, Heat, Smooth, Icy, $2000 each) are sold in marts. Each region stocks only the rocks for weather found there. A rock can be used from the battle Bag once per battle to summon 8 turns of its weather. Sprites are in `assets/sprites/items/`.
  - **Weather areas:**

    | Region | Areas |
    |---|---|
    | Hoenn | Routes 119 and 120, Seafloor Cavern (rain); Route 111 (sand); Cave of Origin (sun) |
    | Sinnoh | Routes 216 and 217, Lake Acuity (snow); Routes 212 and 215 (rain) |
    | Unova | Route 4, Desert Resort (sand) |
    | Kalos | Route 17 (snow) |
    | Alola | Route 17, Po Town (rain); Mount Lanakila (snow) |
    | Galar | Routes 8–10 (snow); Wild Area (random daily) |
    | Paldea | Glaseado Mountain, North Province Area 3 (snow); Asado Desert (sand) |

    Kanto and Johto have none.
- **Seasons (`src/world/seasons.py`):**
  - Unova rules: the season changes every month. Jan/May/Sep Spring, Feb/Jun/Oct Summer, Mar/Jul/Nov Autumn, Apr/Aug/Dec Winter.
  - A region is seasonal if its REGION_START has a `climate`: `{SEASON: {WEATHER: % chance}}`. All seven weather regions (Hoenn–Paldea) have one; Kanto and Johto don't. Alola never snows; Sinnoh winter is 55% snow; Paldea summer is 50% sun.
  - `seasons.area_weather(game, area_key)` is the single source of today's weather. Order: area `season_weather` override (Unova Route 7 snows every winter), then fixed `weather`, then `RANDOM` (Wild Area, now nudged by the climate), then a daily roll from the climate. The daily roll applies to `wild_route` areas only (towns and caves stay clear). It is seeded by date + area, so a route keeps its weather all day.
  - **Battles:** `_init_area_weather` uses it, so seasonal rain/sun/sand/snow get the full 5-turn rules.
  - **Encounters:** `adjust_pool` reweights wild, headbutt, fishing and dive pools by type. Season: Spring Grass/Bug/Fairy ×1.5; Summer Fire/Bug ×1.5, Water ×1.25; Autumn Ghost/Dark ×1.5, Grass ×1.25; Winter Ice ×2, Bug ×0.5, Grass ×0.75. Weather: Rain Water ×2, Electric ×1.5, Fire ×0.5; Sun Fire ×2, Grass ×1.5, Ice ×0.5; Sand Rock/Ground ×2, Steel ×1.5; Snow Ice ×2, Fire ×0.5. Never below ×0.25.
  - **Marts:** weather rocks are stocked for weather possible in the region *this season* (fixed areas + climate).
  - **Berry trees:** Spring/Autumn +1 berry, Winter −1, rain +1, harsh sun −1 (minimum 1), with lines explaining why.
  - **HUD:** "Winter  -  Snow" under the ball count in towns and routes of seasonal regions.
  - **Notice:** the first town visit in a new season shows "It's Winter in Unova!" (flag `last_season`).
  - **Deerling/Sawsbuck:** the summary shows "Coat: Winter Form" for the current season. There are no separate form sprites.
  - Test: `check_seasons.py <scratchpad>` (fakes the date via `seasons._today`).
- **Weather Dial (`src/states/weather.py`):**
  - Gate: the "WEATHER DIRECTOR" option at the Weather Institute appears after `cave_of_origin_cleared` (Primal Groudon/Kyogre calmed). The Director gives `WEATHER_DIAL` + one of each weather rock (`got_weather_dial`, side mission `hoenn_s8`).
  - Once per real day (`story_flags["weather_dial_used"]`): a rock is used up to set an outdoor route's weather until midnight, or CLEAR SKIES for free. Seasons can never be changed manually.
  - Test: `check_weather_dial.py`.
- **Mega Evolution & Primal Reversion (`src/pokemon/forms.py`, `assets/mega_forms.json`):**
  - 48 classic Megas + Primal Groudon/Kyogre: stats/types from PokeAPI, sprites in `sprites/pokemon/mega/` (`back/`, `shiny/`, `back/shiny/`), named `<id>_<form>.png`. Item icons in `sprites/items/`.
  - Player: a MEGA (or PRIMAL) button appears left of MATH/BAG/PKMN/RUN when the active Pokemon can transform: Key Stone (`MEGA_BRACELET` or Kalos `MEGA_RING`) + the species' stone (Rayquaza needs no stone), or Groudon + `RED_ORB` / Kyogre + `BLUE_ORB`. Pressing it transforms without using the turn. Only ONE Mega or Primal per side per battle (`mega_used`); the button then disappears.
  - Foes transform automatically on entry, also one per battle: a trainer's `"mega": <species id>` (applied by `forms.mark_trainer_team` at all four team-building sites); a boss with `"primal": true`.
  - Extreme weather while that Pokemon is out (no countdown, rocks can't override it, ends when it leaves): `HARSH_SUN` (Fire x1.5, Water fizzles for 0), `HEAVY_RAIN` (Water x1.5, Fire fizzles), `STRONG_WINDS` (Electric/Ice/Rock vs Flying halved). Move choice skips moves that would fizzle.
  - Forms revert after battle (`revert_transform` also calls `forms.revert_form`; `exit_battle` and catches revert too).
  - Test: `check_forms.py`.
- **Hoenn follows Omega Ruby / Alpha Sapphire (`src/world/hoenn.py`, `src/states/hoenn.py`):**
  - First arrival in a Hoenn town shows "CHOOSE YOUR STORY" (flag `hoenn_version` = `OMEGA_RUBY` / `ALPHA_SAPPHIRE`).
  - Hoenn data is written once with tokens (`{team}`, `{leader}`, `{legend}`, `{orb}`, `{other_orb}`, `{other_legend}`, `{eon}`, `{goal}`, `{team_short}`) and villain roles (`"villain": grunt/admin_a/admin_b/leader`). `hoenn.apply_version` rewrites the in-memory data from a pristine copy (called at PlayState/CityState init): team names, sprites (Showdown art: maxie, archie, tabitha, courtney, matt, shelly, magma_grunt, aqua_grunt, zinnia), Numel/Camerupt vs Carvanha/Sharpedo, leader Mega Camerupt/Sharpedo. Areas where both teams appear (Route 112, Meteor Falls, Mt. Chimney, New Mauville) keep both teams' grunts.
  - ORAS gym order enforced with gym `requirements`: Roxanne, Brawly, Wattson, Flannery, Norman (5th), Winona, Tate & Liza, Wallace (8th, also needs `cave_of_origin_cleared`). Leaders set `badge_<x>_earned`. Champion is Steven (Mega Metagross); Wally has Mega Gallade.
  - Story events (route action `HOENN_EVENT`): Mt. Pyre elders give the other orb; the Seafloor Cavern leader awakens the legend, starting the Primal crisis (the version's sun/rain over every outdoor Hoenn area until the Cave of Origin); Cave of Origin Primal boss; the leader then gives the stolen orb; Steven on Route 118 (after the Balance Badge) takes you to Southern Island: Latios (OR) / Latias (AS) + its stone + Mega Bracelet; Steven on Route 120 gives the starter Mega Stone; the Route 114 stone collector sells 22 Hoenn Mega Stones ($5000) after the crisis.
  - Delta Episode (post-champion): Sky Pillar travel opens, Zinnia battle, Rayquaza boss, "RIDE RAYQUAZA INTO SPACE" for Deoxys (`delta_episode_cleared`), then the other legend in the Cave of Origin (`counterpart_legend_caught`). Deoxys removed from the Sky Pillar wild pool. Route 118 Southern Island (Eon Ticket) now fights the other Eon dragon; Route 120 Desert Ruins fights Regirock (both buttons did nothing before).
  - Route/town conditions accept `not:<flag>` and lists; route `BOSS` buttons can carry their own `"boss"` dict (`primal`, `background`).
  - Journal: Hoenn missions rewritten in ORAS order with `required_region` + new `region_badges_min/less`; the journal now prefers the current region's main mission.
  - Test: `check_oras.py`.
- **Hisui (Legends: Arceus) sub-region of Sinnoh:**
  - "Space-Time Rift (Hisui)" in Jubilife City (needs the Coal Badge) leads to JUBILIFE_VILLAGE (Professor Laventon, heal, Galaxy Team shop). Areas have `"region": "SINNOH", "subregion": "HISUI"`, so Sinnoh badges, team and weather all apply.
  - Five areas gated by Sinnoh badges: Obsidian Fieldlands (Lv 12, free), Crimson Mirelands (Lv 24, Forest Badge), Cobalt Coastlands (Lv 32, Fen), Coronet Highlands (Lv 40, Mine), Alabaster Icelands (Lv 50, Beacon; snow). Each has a PLA-style pool, two trainers and a Noble boss (Kleavor 18, Hisuian Lilligant 32, Hisuian Arcanine 36, Hisuian Electrode 46, Hisuian Avalugg 56). Enamorus in Crimson Mirelands after the Sinnoh championship. Builder: scratchpad `build_hisui.py`.
  - Hisuian forms (FORM_MAP 2039-2054) were removed from every other pool (Kanto Routes 5-8/10, Power Plant, Cinnabar Volcano, Hoenn New Mauville/Safari). Evolving inside Hisui gives the Hisuian form (Quilava -> Hisuian Typhlosion etc.), and Stantler/Scyther/Ursaring/Basculin can become Wyrdeer/Kleavor/Ursaluna/Basculegion there.
  - Regional forms everywhere (`src/world/regional_forms.py`): once every Alolan, Galarian, Hisuian or Paldean form is caught (flag `forms_complete_<form>`), that region's forms join any pool (wild, headbutt, fishing, dive) containing their counterpart at about 1%. Side mission `sinnoh_hisui`. Test: `check_hisui.py`.
- **Day/night:**
  - Applies to Johto, Sinnoh, Alola and Paldea. Night is before 6:00 or from 20:00.
  - Encounter weights shift rather than lock: a species in its own time of day gets ×2 weight, and one out of its time gets ×0.25 (never 0).
  - An option to make it strict (night-only species) was offered but not requested.
- **Galar Max Raids:**
  - Star odds depend on badge count. Each den has slots weighted 35/35/15/10/5, with the rare 5% slot holding the G-Max species.
  - A caught raid boss becomes a normal-size Pokémon with `gmax_factor`.
  - The Pokédex shows a G-Max tag and "Gigantamax Factor: YES" on the summary page. Gigantamax does not work in battle (offered, not requested).
- **Fossils:**
  - Each region's fossils are gym badge rewards.
  - Fossil labs are handled by `visit_stoneman` for the targets stoneman, fossil_lab, nacrene_museum and ambrette_fossil_lab.
  - Galar fossils are combined from two halves (`FOSSIL_COMBOS`).
  - When reviving, unowned species are preferred.
- **Pokémon Contests (Hoenn; Sinnoh's Hearthome hall also works):**
  - **Halls:** Slateport, Verdanturf, Fallarbor and Lilycove have a "Contest Hall" option (NPC target `contest_hall`), which opens `ContestHallState`. The lobby offers ENTER CONTEST, POKéBLOCKS (a stand that reuses `PokeMartState(stock=...)`), RIBBONS and LEAVE.
  - **First visit:** in Hoenn, Lisia gives the Contest Pass, a Pokéblock Case and 3 of each Pokéblock (flag `contest_pass_received`). Other regions get a plain receptionist instead.
  - **Ranks:** Normal, Super, Hyper and Master need 0, 2, 4 and 6 badges from the hall's region, plus a win at the rank below in that category (`contest_won_<CAT>_<RANK>` flags).
  - **Categories:** Cool, Beauty, Cute, Smart and Tough. Each move's category comes from its type (`TYPE_CATEGORY`).
  - **Contest flow:**
    1. Condition judging: hearts = condition ÷ 16.
    2. Five appeal turns. The player picks one of four moves (up to two fit the category), then answers a math problem.
       - A right answer earns 2 hearts.
       - +1 if the move fits the contest, which also fills the shared crowd meter.
       - +1 for answering within 6 seconds.
       - −1 for repeating the previous move.
       - Whoever fills the 5-pip crowd meter gets Spectacular Talent, +4.
       - A wrong answer earns nothing.
    3. Three rivals scale with rank: Normal uses unevolved Pokémon, Super stage 1–2, Hyper and Master evolved ones. Legendaries are never used.
  - **Prizes:** the winner gets a ribbon (e.g. `BEAUTY_NORMAL`) plus $500, $1,000, $2,000 or $4,000 by rank. The first Master win anywhere earns 3 Rare Candies from Lisia.
  - **Lilycove Museum** (target `contest_museum`): one painting per Master category won. All five set `contest_master`, which completes mission `hoenn_s7`, and give 5 Rare Candies, 5 of each Pokéblock and $10,000.
  - **Pokéblocks:**
    - Five items: RED, BLUE, PINK, GREEN and YELLOW, one per condition.
    - Each gives +20 condition (max 255) and +12 Sheen (max 255, about 21 blocks).
    - Fed from the Bag's first page (items tab). Sold for $300 at the hall stand or at marts in towns with a hall.
  - **Feebas:** it only evolves with Beauty ≥ 170 (`feebas_ready`). Feeding can trigger the evolution immediately if it already has 15 wins.
  - **Per-Pokémon data:** `condition`, `sheen` and `ribbons` are saved, shown as bars on the summary page, and kept through evolution. Evolution now also keeps `gmax_factor` and `caught_region`.
  - **Text and art:** the pixel font can't render ♥ or é, so contest text avoids both and hearts are drawn as shapes. The contest stage is drawn in code; Lisia uses beauty.png and the curator gentleman.png.
- **Sinnoh Poffins:**
  - **Berries:** 15 Gen 4 berries with their real flavors (`BERRIES`):
    - Basic one-flavor: Cheri, Chesto, Pecha, Rawst, Aspear.
    - Two-flavor: Razz, Bluk, Nanab, Wepear, Pinap.
    - Strong rare: Spelon, Pamtre, Watmel, Durin, Belue.
  - **Flavor → condition:** Spicy → Cool, Dry → Beauty, Sweet → Cute, Bitter → Smart, Sour → Tough.
  - **Getting berries:**
    - Floaroma's "Flower Shop" (NPC target `berry_shop`) gives the Berry Pouch and 3 of each basic berry (flag `has_berry_pouch`), then sells berries for $200. Two-flavor berries are added once you have 3 Sinnoh badges.
    - The town's regular mart moved to a separate "Shop" option.
    - 16 Sinnoh routes have `berry_trees` and a "PICK BERRIES" route action (`BERRY`, shown with `has_berry_pouch`). Each route can be picked once per day and gives 2–4 berries. Basic berries grow early, two-flavor ones mid-game, rare ones on Routes 213, 214, 215, 218 and 222.
  - **Poffin House** (Hearthome, target `poffin_house`):
    - The first visit gives the Poffin Case (plus a Berry Pouch and berries if missing).
    - Menu: COOK POFFINS, POFFIN CASE, LEAVE.
  - **Cooking (`PoffinCookState`):**
    - Pick up to 3 different berries.
    - Then come 3 stages × 2 stirs. Each stir is a math problem with a 10, 8 or 6 second limit by stage.
    - A right answer is a stir; within half the time it's a "perfect" stir. A wrong answer is a spill and a timeout is a burn.
    - Formula (`cook()`): flavors sum × (0.6 + 0.1 × stirs + 0.05 × perfect) × (1 + 0.1 per extra berry), minus 2 per spill or burn.
    - Smoothness (Sheen added) = max(5, 25 − 2 × stirs − perfect).
    - A duplicate berry, or every flavor dropping to 0, makes a Foul Poffin.
    - Naming: one or two flavors use their names ("Spicy-Dry Poffin"), three is Rich, four or more is Overripe, and level 50+ is Mild.
    - Examples: three basic berries cooked perfectly give a Rich Lv18; three rare berries cooked perfectly give a Mild Lv72.
  - **Poffin Case:** `story.poffins` is a saved list of dicts, max 100. Poffins are fed from the Poffin Case (a usable Bag key item, or from the Poffin House) and raise every flavor's condition plus Sheen. The Berry Pouch key item lists your berries.
  - **Mission:** `sinnoh_s9` "Master Poffin Chef" is completed by cooking a Mild Poffin (flag `made_mild_poffin`).
  - **Contests:** Poffins feed into Hearthome's Contest Hall, which already works and is gated by Sinnoh badges.
- **Kanto (2026-10-20):** the 'Crazy Guy' town NPCs and the ninja ambush were removed (code and data). The Champion is always your rival with the FireRed/LeafGreen team and exact levels (Pidgeot 59, Alakazam 57, Rhydon 59, then Gyarados/Arcanine, Exeggutor/Gyarados or Arcanine/Exeggutor, and Venusaur/Charizard/Blastoise 63, by the rival's starter); the old title-defense challengers are gone. Gym/league trainers can carry an exact `levels` list.
- **Other content:**
  - Silph Co. is a Rocket dungeon. Clearing it unlocks a Porygon and a Master Ball from the president. Giovanni was removed from it because he must stay hidden until the 8th gym.
  - Oceanic Museum, Space Center and Team Hideout areas were built.
  - Fuchsia is now spelled consistently everywhere, and saves migrate the old FUSCHIA key.
  - Victory Road and Mt. Moon 3F are linked. Mt. Silver being reachable only by Fly is intentional.
  - Department stores sell evolution items, and the `EVOLUTION_ITEMS` map resolves item-based evolutions.

## Testing

Tests run headless. Each script sets `SDL_VIDEODRIVER=dummy`, stubs out `DataManager.save` and `wipe_data`, and must run with `PYTHONIOENCODING=utf-8` from the game directory.

The scripts live in the session scratchpad, which is temporary and may be gone next time: `C:\Users\Dad\AppData\Local\Temp\claude\c--Users-Dad-Games-Python-Games-pokemon-games-Kanto-Math-Game\cd3f7f95-b504-44ab-8b17-371cd71d2a5a\scratchpad`.

- `smoke_regions.py <gamedir>` is the full regression and should end with `##### 0 failures`.
- Feature checks: `check_poffin.py`, `check_contest.py`, `check_realhp.py`, `check_weather.py`, `check_movepick.py`, `check_starter_battles.py`, `check_move.py`, `check_reverse.py`, `check_fossils.py`, `check_galar.py`, `check_xp_silph.py`.

## Assets

- `ASSETS_NEEDED.md` (repo root) is the per-region, story-ordered list of missing backgrounds, trainer sprites, Pokemon sprites, item icons and badges, with exact file names, folders, sizes, a style guide and AI prompt template. Regenerate with scratchpad `asset_audit.py` + `write_asset_list.py`.
- Background names are forgiving: if the exact file is missing, `get_background` tries town/city/island swaps, dropped words (rock_tunnel_city -> rock_city), no-underscore forms (evergrande) and close spellings with the same start (fallabor). Town-specific Center/Mart art wins over the generic pokecenter.png/pokemart.png names.
- Backgrounds in any region folder (`backgrounds/hoenn/`, `backgrounds/sinnoh/`, ...) are now found by `get_background` (Hoenn's 23 existing interiors were previously never loaded). Kalos (badges 43-50) and Galar (51-60) badge images are mapped; Alola and Paldea badges still needed.
- Test Sinnoh art drawn in code (scratchpad `sinnoh_art.py`): `backgrounds/sinnoh/twinleaf_town.png`, `backgrounds/sinnoh/oreburgh_center.png`, `backgrounds/battle/sinnoh/gym/battle_gym_oreburgh.png`.

- **Battle moves and story events (2026-10-20):** see `CHANGELOG.md`.
  - Moves: `src/pokemon/moves.py`, `assets/moves.json`.
  - IVs and status are on `Pokemon`.
  - Story NPC buttons: `src/world/story_events.py`, run by `_run_story_event` in overworld.py.
  - `ClassicDialogueBox` callbacks are one-shot.

## Not started / ideas

- **Next (from the 2026-10-20 play-test):**
  - Badge progression gates that hide off-story destinations.
  - Whiting out sends you to the last Pokémon Center used, with the nurse's message.
  - Journal filtered by region, with the Hisui mission waiting for the Coal Badge.
  - Options: Quit button and an autosave toggle.
  - Shiny back sprites.
  - UI overhaul for the PC, Pokédex, Bag, badges and battles.

- Fog weather (not implemented; asked about on 2026-10-19).
- BDSP mechanics for Sinnoh (requested 2026-10-19, not started yet): Grand Underground (Explorer Kit, Hideaways, digging), Ramanas Park slates, Honey Trees.
- ORAS extras not done: Soaring/Eon Flute, Mirage Spots, DexNav, Secret Bases.
- Side missions from other regions (e.g. Galar's 'The Wild Area') have no `required_region`, so they show in every region.

### From the original feature list

- Sinnoh Underground
- Kalos Amie and Inverse Battles
- Alola SOS battles, Ride Pokémon and Rotom hints
- Galar Camping
- Paldea's three story paths

## User preferences

- Confirm each region before moving to the next during audits.
- "Save all files" means commit.
- Commits end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
