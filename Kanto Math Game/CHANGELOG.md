# Changelog

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
- Badge-based progression gates that hide off-story destinations.
- Whiting out sends you to the last Pokémon Center used, with the nurse's message.
- Journal shows only the current region's missions, and the Hisui mission waits for the Coal Badge.
- Options: Quit button and an autosave toggle (save on area travel).
- Shiny back sprites.
- A larger UI pass over the PC, Pokédex, Bag, badge case and battle screens.
