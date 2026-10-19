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
- **XP:**
  - Each Pokémon stores `xp`, with `wins = xp // 10`. Constants: `TIER_XP = 150`, sub-stage costs (20, 30, 40, 60), and sub-stages that give slight stat, HP and damage boosts.
  - Battle XP is relative to stage. A stronger foe gives +25%, and a weaker foe or one with a stat disadvantage gives −25%. The steps add together and the total is clamped to 0.5–1.75.
  - The XP bar shows sub-stage segments.
- **Real HP:**
  - Max HP uses the games' formula: floor(2 × base HP × level / 100) + level + 10.
  - The level comes from the stage via `LEVEL_BY_STAGE = (15, 15, 35, 55)` in `src/pokemon/data.py`. Sub-stages move it part of the way toward the next stage.
  - Examples: Charmander 36, Charizard 150, Chansey 220, Snorlax 241.
  - The old 20/60/90 scale still exists as `battle_hp_scale()`.
  - Saves store `"hp_real": True`. Older saves convert stored HP to the same share of the new maximum.
- **Damage (still a share of HP):**
  - Each hit is rolled on the old 20/60/90 scale from tables by stage: normal (0, 7, 20, 30), super effective (0, 10, 28, 42), not very effective (0, 4, 12, 18).
  - Sub-stages interpolate between those values. Then come the stat modifier, a random spread of ±2, a 10% chance of a ×1.5 critical hit, and the weather factor.
  - The result, as a share of the defender's old-scale HP, is applied to its real HP, so a 50% hit is always 50%.
  - The opponent attacks every turn.
- **Stat modifier (`_stat_mod`, −2 to +2):**
  - The attacker's offense stat (Attack or Sp. Atk, matching the move's physical or special category) adds +1 if strong and −1 if weak.
  - The defender's matching Defense or Sp. Def does the reverse.
  - A base stat of 100 or more counts as strong, below 50 counts as weak (`Pokemon.stat_tier`).
  - Speed is deliberately excluded (the user's decision: Speed already decides who strikes first).
  - The XP "easy foe" penalty applies when the foe's modifier against you is negative.
- **Move choice (`_pick_move` / `_ready_attacks`):**
  - Runs before every attack.
  - Picks the attacker's strongest same-type damaging move, scored as power × type effectiveness × rain/sun factor.
  - Self-KO and one-hit KO moves are skipped, and exact ties are broken at random.
  - The chosen move's type sets `adv_opp`/`adv_player` and the weather boost. Its category (physical or special) picks the stats for the stat modifier.
  - If no move qualifies, the attacker uses Tackle, typed as its best type.
  - The type chart stores immunities as 0.5. That looks intentional and was left alone.
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
  - Gate: the "WEATHER DIRECTOR" option in the Weather Institute (`HOENN_WEATHER_INSTITUTE` route_menu, action `WEATHER_DIRECTOR`) appears only after `rayquaza_awakened` (Sky Pillar). The Director gives the `WEATHER_DIAL` key item plus one of each weather rock, sets `got_weather_dial`, and completes side mission `hoenn_s8` "Master of the Skies".
  - Use: from the Bag's key items, on an outdoor route or fixed-weather area in a seasonal region (`seasons.can_change_weather`). Towns, caves, Kanto and Johto are refused.
  - Picking a rock uses it up and sets that area's weather until midnight (`story_flags["weather_override"]`, date-stamped; older days are pruned). CLEAR SKIES is free. The override beats every other rule, so battles, encounters, berries and the HUD all follow it.
  - Seasons can never be changed manually.
  - Test: `check_weather_dial.py <scratchpad>`.
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

## Not started (from the original feature list)

- Sinnoh Underground
- Kalos Amie and Inverse Battles
- Alola SOS battles, Ride Pokémon and Rotom hints
- Galar Camping
- Paldea's three story paths

## User preferences

- Confirm each region before moving to the next during audits.
- "Save all files" means commit.
- Commits end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
