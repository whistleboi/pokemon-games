# Changelog

## Unreleased: Kanto fixes (Grok audit) and bug fixes

- **Grok "kanto-fixes" batch merged.** It includes:
  - real type immunities, plus Struggle when nothing can hit;
  - status cures (Full Heal, Pokémon Centers, whiteouts) and sleep lasting 1–3 turns;
  - Thunder Wave and powder immunities, and Toxic;
  - multi-hit, drain, recoil and high-crit moves; two-turn and recharge moves; fixed-damage moves; flinch; Fly, Dig and Dive dodging;
  - Ned's Super Rod and a Vermilion Old Rod;
  - Koffing in the wild;
  - a Kanto Pokédex of exactly #1–151;
  - the path to Indigo, and the Champion win now being recorded;
  - the fossil revival loop and the Bill crash fixed;
  - per-town Kanto marts and higher late-game levels;
  - math puzzles in Surge's, Koga's and Sabrina's gyms, and Blaine's quiz;
  - one rival per region;
  - FireRed/LeafGreen rematch teams.
  - Tests are in `tests/`.
- **Kanto stays Kanto.** Pokémon and regional forms from regions you haven't played don't appear wild in Kanto. Evolutions into later-region species, such as Crobat and Porygon2, also wait until you've been to that region. Other regions keep their own listed exceptions, like Hoenn's Gallade.
- **Up-Grade** is never sold. It's a gift from a Silph Co. employee once Silph Co. is freed and you've visited Johto.
- **Recoil, burn, poison and sandstorm can knock Pokémon out**, as in the games.
- **Canon Kanto gates:**
  - Route 3 opens after Brock.
  - Nugget Bridge must be cleared before reaching Bill.
  - Route 9 needs Cut (the Cascade Badge and a visit to Vermilion).
  - Cut trees block Surge's and Erika's gyms.
  - Saffron's guards want Tea from the Celadon Mansion.
  - Team Rocket blocks Sabrina's gym until Silph Co. is freed.
  - Snorlax blocks Lavender → Route 12.
  - Cycling Road needs a Bicycle.
  - Blaine's gym needs the Secret Key from the Pokémon Mansion.
  - Cerulean Cave opens after becoming Champion.
- **Saves:**
  - Saves are written safely (temp file plus a `.bak` backup), and a damaged save loads from its backup.
  - Damaged slots say "DAMAGED" instead of "EMPTY".
  - A stale whiteout flag that broke every battle is cleared.
  - The Poké Ball count is now right when you save from a menu.
- **Pokémon never vanish:** every PC deposit uses a free slot, the PC keeps anything stored past slot 300, and the region filter never deletes a Pokémon.
- **Healing:**
  - The overworld whiteout check works.
  - Evolving keeps damage.
  - Levelling up adds the HP gained.
  - A party with no Pokémon able to fight goes straight to a whiteout.
- **Text and taps:**
  - Long text pages inside its box.
  - Finished boxes no longer swallow taps, and overlay messages close themselves.
  - Each tap is handled on its own, and taps right after a screen change are ignored.
  - Bag messages ("already at full health", level-ups, learned moves) now show.
- **Whiting out** takes you to the last Pokémon Center you used in this region. The nurse says "We've healed your Pokémon after that tough battle." If you haven't used a center in the region yet, you go home and Mom heals your team.
- **Journal:**
  - It shows only the missions of the region you're in. Kanto's 40 missions now appear; before, they never loaded.
  - A region's missions count that region's badges.
  - The Hisui mission waits for the Coal Badge.
- **Johto's routes and dungeons** are now tagged as Johto. Before, they counted as Kanto for the AUTO math level, badge counts and missions.
- **Options:**
  - New QUIT button: Save & Quit to Title, Quit to Title without saving, or Cancel.
  - New AUTOSAVE toggle, on by default, which saves each time you travel to a new area.
  - The title screen has its own QUIT button that closes the game.
- **Battle soft-lock fixed (Eterna rival).** When a Pokémon fainted, the turn's other queued move wasn't cleared and could leak into the next turn. A KO now ends the queue. The rival battle was replayed 27 ways (every starter, solo, a fainted lead, two Pokémon, switching or not, right or wrong answers), and every run finishes.
- **"Change Pokémon?"** is only asked when you have another Pokémon able to battle.
- After a whiteout, a town's arrival battle (like Barry in Eterna) waits until your next visit instead of ambushing you as you leave the Pokémon Center.
- **Bag pages.** A full pocket splits into pages with UP/DOWN buttons and a page count, so every item can be reached.
- **Shiny Pokémon make their sound again.** The game now finds `Shiny.mp3`.
- **Shiny back sprites:** 1,084 downloaded, including regional forms and the three Paldean Tauros breeds. "Galarian Psyduck" isn't a real form, so it keeps the normal back.
- **Stand-in art** for anything without its own picture yet, in `assets/backgrounds/generic/`:
  - The cute Pokémon Center and Mart pictures for every Center and Mart.
  - New pixel-art gym, lab, Mom's house, town, and generic building (museums, lighthouses and so on).
  - Battle backdrops for gyms, Elite Four rooms, indoor areas and deserts.
  - A gym without its own battle art no longer borrows another town's gym.
  - Nurse Joy appears in Pokémon Centers that have their own art.
- **Saffron's "Confront Team Rocket"** takes you into Silph Co. (it pointed at the removed Crazy Guy). It shows after the Pokémon Tower and disappears once Silph Co. is freed.
- **Game Corner Team Rocket** grunts have levels that fit together (around Lv 17–21), getting a little tougher each fight.
- **Fishing:**
  - Better rods reach bigger fish: Old Rod Lv 5+, Good Rod Lv 10+, Super Rod Lv 15+.
  - Nothing bites below the level it evolves at; a low-level Dragonair comes up as a Dratini instead.
  - The Good Rod now counts as a rod.
- **Erika** uses her FireRed/LeafGreen team: Victreebel, Tangela, and Vileplume as her ace.
- **"Loreli" is now "Lorelei".**
- **Mr. Fuji** gives you the Poké Flute himself, with the story of the Marowak in the tower. The game no longer hands it over in the background.
- **Evolution after gym and town battles:** a Pokémon that reaches its level while winning a badge evolves right away. The same goes for town battles, like the rival in Eterna.
- **Several evolutions at once:** when more than one Pokémon is ready, they evolve one after another, as in the games. Saying NO to one moves on to the next without asking again.
- **Summary screen:** Amie hearts, plus a new STATS & MOVES page with every stat, IV bars, status, XP to the next level, and the four moves with type, category, power and accuracy. Hearts also show on the party screen once a Pokémon has any.
- **Music by situation:** towns, routes, wild battles, trainer battles and gym/Elite/Champion battles each have their own music, and a victory jingle plays after a win.
  - New original chiptune tracks: `music_town`, `music_route`, `music_gym`, `music_victory`.
  - The existing `kanto_wild`, `kanto_trainer` and `kanto_battle` tracks are used for their battles.
  - Drop in a file like `johto_town1.ogg` and that region uses it automatically.
- **Mart:**
  - New layout: BUY and SELL tabs, item cards with price and how many you have, and a money panel.
  - A quantity picker that shows the math (3 x $500 = $1,500, money before and after).
  - Selling pays half price. Key items, gifts and Mega Stones can't be sold.
  - You can hold up to 999 of each item.
  - New **Everstone** ($3,000): give it to a Pokémon from the Bag to stop it evolving, and use it again to take it back.
- **Keyboard:** arrow keys move a gold highlight between buttons, Enter or Space presses (or moves the text on), and Esc goes back or cancels. It works on every screen; name entry and the pickers keep their own keys.
- **Paldea:**
  - Orthworm moved to its real home, the new East Province Area 3.
  - The Quaking Earth Titan is Great Tusk or Iron Treads.
  - Casseroya Lake battles use the lake backdrop.
- **Story:**
  - The Route 22 rival battle now happens.
  - Knocking Snorlax out clears the road.
  - The early Viridian Team Rocket fight uses fair levels.

## Unreleased: Pokémon-Amie, Galar camping, Paldea's three paths

- **Pokémon-Amie (Kalos).** Pokémon-Amie button in every Kalos town with a Pokémon Center.
  - PET a party Pokémon, or PLAY a timed 3-question math game, to raise its affection (0–5 hearts, up to 100 affection per Pokémon per day).
  - Affection is saved and kept through evolution. Its battle perks work in every region:
    - 2 hearts: 1.2× XP
    - 3+ hearts: may hang on with 1 HP after a knockout blow
    - 4+ hearts: may dodge an attack and shake off a status
    - 5 hearts: double crit rate
- **Galar camping.** SET UP CAMP on 20 Galar routes and Wild Area spots.
  - REST fully heals and cures the team, once per day per spot.
  - COOK CURRY: add up to 3 berries, then do three timed math stirs.
  - The curry class (Koffing up to Charizard) heals the team and, for the better classes, also gives XP and affection.
- **Paldea's three paths.**
  - **Path of Legends:** the five Titans are boss fights that can't be caught. Each drops Herba Mystica.

    | Titan | Level | Where |
    |---|---|---|
    | Klawf | 16 | South Province Area 3 |
    | Bombirdier | 20 | West Province Area 1 |
    | Orthworm | 29 | East Province Area 3 (new area, off Levincia) |
    | Great Tusk or Iron Treads | 45 | Asado Desert (each save gets one, like Scarlet or Violet) |
    | Dondozo | 56 | Casseroya Lake (new area) |

  - **Starfall Street:** five Team Star bases, each boss ending on the Starmobile (Revavroom).

    | Boss | Level | Where |
    |---|---|---|
    | Giacomo | 21 | West Province Area 1 |
    | Mela | 27 | East Province Area 1 |
    | Atticus | 33 | Tagtree Thicket |
    | Ortega | 51 | North Province Area 3 |
    | Eri | 56 | North Province Area 1 |

  - **Finales:** Arven's battle in Mesagoza after all five Titans, and Penny (Cassiopeia) at Naranja Academy after all five bases.
  - **Area Zero** now opens only after all three paths are done: Victory Road, Path of Legends and Starfall Street.
  - Path buttons stay hidden until you meet Arven or Team Star in Mesagoza.
  - Area menus can now hold a full story event inline (action `EVENT`).
  - Trainer sprites added for Giacomo, Mela, Atticus, Ortega, Eri, Penny and Arven.

## 2026-10-20: since the last push (`ac5e891`)

This covers everything since "any-region starts, playable Gen 3–9 regions". That is 29 earlier local commits plus today's battle and story fixes.

### Battles
- **Moves.** You now press FIGHT, choose one of up to four moves, then answer the math question.
  - Moves come from real level-up learnsets, and only damaging, weather and status moves are used.
  - Move data covers 765 moves in `assets/moves.json`.
  - New moves are learned on level-up. When a Pokémon already knows four, the weakest one is replaced.
- **Fixed: wrong type effectiveness.** Moves had been taking the attacker's best type, which is why Tackle showed as super effective. Each move now has its real type.
- **Fixed: foe never attacking.** A message callback was firing again on later text. That ended turns early, so the foe never attacked and the same math question repeated, most visibly in rain.
- **Damage.** Damage now uses the real Gen 6+ formula: 85–100% random roll, 1/24 crit chance, STAB, type matchups and weather. The old stat modifiers and damage caps are gone.
- **IVs.** Every Pokémon has random IVs (0–31), saved with it and counted in its stats. A Lv 14 Geodude's Bulldoze does 36–44 to a Lv 14 Cranidos, matching Showdown.
- **Turn order.** Move priority goes first, then Speed. Paralysis halves Speed, and ties are random.
- **Status conditions.** Burn, paralysis, poison, sleep and freeze work, with type immunities. Burn and poison do chip damage, and status lasts after battle.
- **AI.** The foe picks moves by damage × effectiveness × STAB × weather × accuracy. It uses weather and status moves when they help, and adds a little randomness.
- **Weather.**
  - Weather lasts 5 turns (8 with the matching rock) from the start of battle.
  - It keeps counting down on turns that end in a knockout. It no longer looks reset when a trainer's next Pokémon comes out.
  - Only moves and items can set it again.
- **Party.** A fainted lead no longer starts the battle.
- **XP.** XP now scales with the level gap, so beating a stronger Pokémon gives more. For example, a Lv 2 beating a Lv 7 gets several levels' worth.
- **Mega Evolution and Primal Reversion.** These use a MEGA/PRIMAL button and are never automatic. Each side gets one per battle.

### Levels and progression
- Real levels, real evolution levels and faster XP. Level costs scale per band of 20 levels.
- Creative stand-ins replace friendship, trade and other non-level evolutions.
- Level cap option with three modes: Story (default), Obedience or None. Pokémon over the obedience cap can disobey.
- Trainer, gym, Elite Four, Champion and legendary levels follow the real games.

### Regions and story
- **Hoenn** follows Omega Ruby / Alpha Sapphire, including Team Magma/Aqua, the orbs, Primal Groudon/Kyogre and Mega Evolution.
- **Seasons** in every weather region. The **Weather Dial** unlocks late in Hoenn, uses up weather rocks and works once per in-game day.
- **Hisui**, a sub-region reachable only from Sinnoh, has 5 areas.
  - Hisuian forms are locked there.
  - Once every form from a region is caught, those forms show up at a low rate wherever their counterparts live. This applies to every region.
- **Sinnoh** follows Brilliant Diamond / Shining Pearl (no Underground yet). Also added: Pokémon Contests, Pokéblocks, Poffins and berry trees.
- **Kanto**: the Crazy Guy NPCs and the ninja ambush are removed. The Champion is the rival with the canon FireRed/LeafGreen team.
- **Story buttons (new `src/world/story_events.py`).** 62 story buttons across all regions did nothing when clicked; all of them now work.
  - **Sinnoh:** Find Roark in Oreburgh Mine, which now opens the Oreburgh Gym. Also the Galactic battles at Jubilife, Floaroma, Eterna and the three lakes, Cyrus at Spear Pillar (which unlocks Sunyshore), Riley's Riolu, and Barry at Victory Road.
  - **Unova:** N, Bianca, Cheren and the Team Plasma events.
  - **Johto:** Giovanni at Tohjo Falls, Sage Li, the Radio Director and the Dragon Shrine.
  - **Hoenn, Kalos, Alola and Galar:** their town NPCs.
  - Each event has its dialogue, a canon team (picked by your starter where it matters), gifts and the story flag the next step needs.
- Route buttons now hide once their story step is done. Clearing every trainer in the Galactic HQ or Valley Windworks sets the area's cleared flag.
- Every Gen 1–9 species is obtainable in its home region. Also new: regional fossils, day/night encounters, Max Raids, Silph Co. as a Rocket dungeon, and the post-Champion move to a new region.

### Menus and quality of life
- Fixed: opening a side menu (Bag, PC, Badges, Journal, Options) in the middle of the three-Pokémon catch sequence no longer rerolls the three Pokémon.
- Background art is found under alternate file names and in region subfolders, for example `cinnabar_cty`.
- Missing trainer sprites, back sprites and item icons were downloaded. `ASSETS_NEEDED.md` lists the art still needed per region.

### Still to do (from the latest play-test)
- A larger UI pass over the PC, Pokédex, Bag, badge case and battle screens.
