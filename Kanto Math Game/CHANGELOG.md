# Changelog

## Unreleased: no repeated regions, local rivals, Mew's count

- **No repeating regions.** The goal is to work through all nine regions once. After a title, Mom's move picker now offers only regions you haven't played.
  - Kanto and Johto still connect by ship, train and road.
  - When every region has been played, Mom says there's nowhere new to move.
- **Sub-region rivals are their own characters.** None of the sub-regions borrow a region's rival. Kitakami's Carmine and Kieran are now ordinary local trainers, so nothing treats them as Paldea's rival.
- **Mew's hint counts Kanto Pokémon only.** On Faraway Island the hint now shows your progress, e.g. "Your Pokédex: 100 of the 150 Kanto Pokémon. 50 still to catch!". It counts species #1–150 only, so Pokémon from other regions don't help.

## Unreleased: fixes from Grok's handoff (sub-regions and travel)

- **Battle freeze fixed (Paldea and more).**
  - 60 Gen 6–9 species (the Paldea starters, Ogerpon and others) had no back sprite. When one fainted on your side, the faint animation never started and the battle froze. The animation now always runs.
  - All 60 now have their real back and shiny back sprites from PokeAPI.
- **Catching a story boss uses up the ball.** It used to be refunded (fixed with the single ball count).
  - The Crystal Onix and Orre's Shadow Pokémon now work like legendaries: beating one without catching it leaves it there to try again, instead of losing it for good.
- **Ho-Oh is reachable.** Sage Li checked the Pokédex in a way that could never match, so the Rainbow Wing was never given.
  - The same mistake hid the Poké Ball icon on wild Pokémon you'd already caught, and let the Unown researcher hand out Nown repeatedly.
- **Red and Mt. Silver open after the Johto title.** They no longer need 8 Kanto badges.
- **New region, fresh start, explained.** When you start another region, its professor says your old Pokémon are safe at home in that region's PC and your challenge starts over.
  - Johto now has a Professor Elm introduction on the starter screen.
- **The right rival in each intro.** Moving to a new region could name the previous region's rival ("Your neighbor BLUE...").
- **Sinnoh:** Rowan's "Choose wisely: Turtwig, Chimchar or Piplup" now comes before you choose.
- **No Poké Balls after beating a legendary:** it now says so and that the Pokémon got away, instead of the battle just ending.
- **Bill gives his Eevee** in Goldenrod after you meet him in Ecruteak, as in HeartGold/SoulSilver.
- **Shamouti treasures can't be lost.** If you calmed a bird but don't have its treasure, you can search that island's shrine again until the song is played.

## Unreleased: fixes from Grok's Johto playthrough

- **Crash at the Red Gyarados fixed.** The shiny boss asked for its back sprite in an unsupported way, which stopped the story at 6 badges. Shiny bosses now load their shiny art through the normal loader.
- **The team no longer gets boxed on the way to the League.**
  - A leftover rule sent Pokémon caught in another region to the PC at the start of every battle. Routes 26 and 27 counted as Kanto, so a Johto team lost everyone but its starter right before Silver's 6-Pokémon fight.
  - The rule is gone; regional storage now does that job properly.
  - Routes 26 and 27 are Johto routes again.
  - The League Reception Gate is a border that keeps the region you arrive with.
- **No more softlocks:**
  - **Radio Tower:** clearing it over two visits left no exit. Any area with no wild battles on its menu and no trainers left now lets you leave.
  - **Silver League Plateau:** now has exits back to Mt. Silver City and the Reception Gate.
  - **No Poké Balls:** the catch screen no longer opens. It says "You have no Poké Balls left!" and goes back to the menu.
- **Poké Balls you buy stay bought.** Each route kept its own copy of your ball count, and an old copy coming back (a revisited route, an event battle from town) erased the balls you'd bought. There's now one ball count for the whole game.
- **League prize money uses the games' formula:** the opponent's top level × 100, or × 200 for the Champion. A flat 25,000 per Elite Four win, doubled by the Amulet Coin, let a lost League run be farmed for 200k+.
- **Roaming Raikou and Entei:**
  - They now suit the route (Lv 40 at most, as in HeartGold/SoulSilver) instead of a Lv 50 that knocked out a team at 4 badges in one hit.
  - Beating one and choosing YES now catches it. The battle was catching into an older route screen.
  - They show up a little more often (10% per route entry). This also makes Ho-Oh reachable, since it needs all three beasts.
- **Johto levels:**
  - Union Cave and Slowpoke Well are now Lv 13 and 15; they're required before Bugsy.
  - Mt. Mortar, the Whirl Islands, Route 44, the Ice Path, Route 45 and the Dragon's Den now rise in steps toward the late Gyms.
  - The road to the League after the 8th badge is the training ground: Route 27 Lv 45, Tohjo Falls 48, Route 26 50. Before, there was nowhere to earn XP between Lv 58 and the Lv 63 Champion.
  - The level cap never goes down: Pryce's ace is lower than Jasmine's, so the cap now keeps the highest ace so far.
  - First-route trainers sit only 0–1 levels above the area, so Youngster Joey's Rattata isn't a wall for a fresh starter.
- **Johto details:**
  - The League's journal missions now check the Johto title.
  - A man in Goldenrod gives a Coin Case, so a Johto-first game can use the Game Corner.
  - Morty's Gym note hints that you can battle your rival again at the Burned Tower.
  - Fixed the "MAHOGNAY TOWN" typo at the Lake of Rage.
- **After any region's title, you go home** to celebrate, where Mom's call and the next-region story run. Before, every region except Kanto went back to the League lobby, which was already in rematch mode (Grok saw a rematch Will).

## Unreleased: separate regional PCs, Bags and Pokédexes

- **Each region has its own party, PC and Bag.**
  - Going to a new region for the first time, whether by Mom's move, a ship, a train or a road, leaves your Pokémon and items behind in the region they're from. You collect new key items there.
  - With no partner from that region yet, you're taken to its professor, and the starter choice opens as you arrive.
  - Going back to a region brings back its own party, PC and Bag.
- **Linking.** When you become Champion of a second region, the professor calls: your regional PCs are now linked, and your Bags are combined.
  - Every region you're Champion of shares one party, PC and Bag from then on, and each new title joins in.
  - Your current party stays as your party; the other region's party goes to the PC.
  - Items add up, and key items aren't doubled.
- **What's shared and where:**
  - Money and Poké Balls are shared everywhere, so you can always catch.
  - The S.S. Ticket goes with you, so you can always sail home.
  - Sub-regions use their region's storage (Sevii is Kanto's, Sinjoh is Johto's). The Orange Islands use Kanto's, and Orre uses Hoenn's.
  - Key items and HMs are only given into the Bag of the region that earned them.
- **Old saves:** everything in an existing save stays together. Every region already visited counts as linked, so nothing goes missing.
- **Regional Pokédexes, as in the games.**
  - A region's Pokédex now arrives with its starter, not just when you set foot there.
  - The Pokédex opens on the dex for the region you're in. A button at the top switches between each regional dex ("Kanto Dex", "Johto Dex"...) and the National Dex.
  - The caught count shows that dex's progress (e.g. 98 / 151).

## Unreleased: Galar and Paldea DLC accuracy

The DLC areas existed but had some things wrong. Fixed:

- **Isle of Armor:**
  - Zarude wasn't in that DLC (it's from a movie); it moved to Glimwood Tangle after the Galar title.
  - Kubfu is no longer a wild Pokémon. At Mustard's Master Dojo, beat his students Klara and Avery and Mustard gives you Kubfu. Climb the Tower of Darkness or the Tower of Waters to evolve it into Single Strike or Rapid Strike Urshifu.
- **Crown Tundra:** Peony's expedition now opens **Dyna Tree Hill**, with catchable Galarian Articuno, Zapdos and Moltres (Lv 70) and Crown Tundra wild Pokémon.
- **Enamorus and the Space-Time Distortion** came from Legends: Arceus, not Galar. They moved to Hisui and are now reached from the Obsidian Fieldlands instead of the Slumbering Weald.
- **The Teal Mask:**
  - Carmine and Kieran meet you in Kitakami. Battle Carmine, then Kieran once you've found the Loyal Three.
  - Ogerpon now appears only after the Loyal Three, as in the game.
- **The Indigo Disk** was missing, so I added it.
  - After Kitakami, an exchange from Mesagoza goes to **Blueberry Academy**.
  - The BB League: Crispin, Amarys, Lacey and Drayton, then Champion Kieran (Lv 70–77).
  - **The Terarium** has Pokémon from its four biomes.
  - **Terapagos** now waits until you've won the BB League and joined Briar's expedition.
- Three journal entries.
- **Fix:** trainers' legendary Pokémon ignored the levels in the data and stayed at their wild level (Kieran's Ogerpon at Lv 50 in a Lv 67 team). Exact team levels now apply to every Pokémon on the team.

## Unreleased: Orre

- **A desert region from Pokémon Colosseum.** After the Hoenn title, an air transit from Lilycove City flies to Phenac City.
  - Orre has no wild Pokémon, no Gyms and no badges, so it gets no badge-case page. It never appears in the new-game or move pickers.
  - The Desert Trail is a motorbike ride.
- **Cipher and Shadow Pokémon:**
  - **Phenac City:** stop the Cipher Peons at the fountain. Rui then gives you the **Snag Machine**.
  - **Snagging:** Cipher trainers send out 12 Shadow Pokémon (dark, purple-tinged art) across Orre: Makuhita, Teddiursa, Houndour, the Johto starters' middle forms, Ledian, Hitmontop, Ursaring, Skarmory, Snorlax and Tyranitar. Weaken one and throw a ball to snag it. If it faints, you can find it again and try another snag.
  - **Agate Village:** the **Relic Stone** opens their hearts. Every Shadow Pokémon in your party and PC becomes the normal species, keeping its level, IVs, moves and shininess, and gains friendship.
  - **Pyrite Town:** the Colosseum, with Miror B. and his Ludicolo, and Cipher's hideout in **The Under**, run by Admin Venus.
  - **Realgam Tower:** Admins Dakim and Ein, then Cipher Head Evice. After that, the last Shadow Pokémon wait in the Command Center.
  - **Phenac Stadium:** a tournament.
- **Jirachi moved here.** It was a 2% wild Pokémon in Hoenn's Sky Pillar. Once Cipher falls, a wishing star lands at the Relic Stone and Jirachi wakes up.
- Four journal entries guide the story.
- **Fix:** the level rules use the current region's badges. That meant Story mode capped levels at 12 in Orre, and in Obedience mode a strong team ignored you in Orre and the Orange Islands. Neither happens now.

## Unreleased: the Sinjoh Ruins

- **A hidden place from HeartGold/SoulSilver.** With Arceus in your party and all 28 Unown registered (A to Z, ! and ?), the Ruins of Alph offer "Follow the Unown". Once you've been, you can go back without Arceus.
- **No flying in or out.** The guide's Abra at the Border Cabin Teleports you back to the Ruins of Alph.
- **The Border Cabin:** a Hiker's Rest to heal (no shop) and the Sinjoh Snowfields (Snorunt, Snover, Delibird...). Cynthia studies the mixed Johto and Sinnoh carvings and warns you about the Mystri Stage.
- **The Ruined Pathways:** restless Pokémon (Misdreavus, Murkrow, Sneasel, Swinub, Piloswine) let out strange roars.
  - A **Phione** swept through the rift from Sinnoh's Sea Temple is frozen in a spring. Melt three ice seals by touching the carving with the bigger number, and it follows you.
- **The Mystri Stage:** with Arceus in your party, Phione's song steadies the rift long enough to call **one** of Dialga, Palkia or Giratina. Each comes holding its orb and can be caught; the other two stay away.
  - Afterwards, Phione says goodbye and can be caught too.
  - Cynthia then battles you at the cabin with a full Lv 70–72 team.
- **Phione moved here.** It was a 5% wild Pokémon on Sinnoh's Route 223.
- Three journal entries. Two new menu conditions: `party_has:<id>` and `all_unown_registered`.

## Unreleased: the Decolore Islands

- **A Unova sub-region from the anime.** After the Unova title, a ferry from Castelia City sails to the Decolore Islands.
  - The ferry deck is its own stop, with no wild Pokémon and five trainers to battle: sailors, a gentleman, a rich boy, a tourist and a swimmer.
  - Each island opens from the ferry as the story moves on.
- **Genesect and Team Plasma.** Genesect moved here from P2 Laboratory, where a lab note now points to the islands. Team Plasma is collecting Drives for a rebuilt Genesect:
  - **Honey Island:** scorched beehives and the Burn Drive.
  - **Scalchop Island:** Plasma Grunts at the shrine, then the Douse Drive in their abandoned crates.
  - **Grand Spectrala Island:** Zoroark's illusion woods, a math puzzle (pick the door whose sign is true), then the Chill Drive.
  - **Torom Island:** beat the Plasma Scientist and shut down the lab for the Shock Drive. Genesect breaks free to Torom Peak, where you can catch it. It won't appear twice if an old save already beat it at P2 Laboratory.
- **Paladin Island:** the Paladin Tournament. Lenora, Burgh and Elesa, then Alder in the final.
- **Wild Pokémon on each island,** from your list: Combee, Vespiquen and Comfey on Honey Island; Oshawott, Krabby and Wailmer at Scalchop; Zorua, Zoroark and Misdreavus on Spectrala; Rotom and Magnemite on Torom; Pikachu and the Elemental Monkeys on Paladin. Trainer classes follow the to-do (Beekeepers, Illusionists, Rangers, Scientists, Engineers, Tourists...).
- Four journal entries guide the story.
- **Fix (sub-region builder):** areas with no wild Pokémon (the ferry, Dotted Hole, the Rocket Warehouse, Faraway Island) asked for two rounds of battles before you could leave, so you could get stuck. You can now leave them right away.

## Unreleased: the Sevii Islands

- **A Kanto sub-region from FireRed/LeafGreen.** Blaine now gives a **Tri-Pass** with the Volcano Badge (saves that already have it get one), along with a tip about Moltres. The Seagallop Ferry in Vermilion goes to Islands One to Three.
  - After the Hall of Fame, with the National Pokédex, Celio gives a **Rainbow Pass** for Islands Four to Seven.
  - Ferries link every island you have a pass for, and each island has a ferry home.
- **Johto Pokémon early.** The Sevii Islands are the one place in Kanto with Johto Pokémon before you've been to Johto (Hoppip, Slugma, Wooper, Murkrow, Larvitar...). The mainland still keeps them out.
- **The story:** a Team Rocket cell left over after Giovanni's defeat is hunting the Ruby and Sapphire that Celio's Network Machine needs.
  - **One Island:** chase them off Mt. Ember. **Moltres moved there** from Cinnabar Volcano, at the summit; if you already beat it in the volcano, it won't appear twice.
  - **Four Island:** stop them netting Lapras in Icefall Cave. Lorelei, at home on Four Island, then battles you.
  - **Six Island:** solve the braille puzzle in the Dotted Hole by counting the raised dots. The scientist Gideon then snatches the Sapphire.
  - **Five Island:** crack the Rocket Warehouse door codes (adding three numbers), beat Admin Archer and recover both gems.
  - **Back on One Island:** Celio fixes the machine and gives you the **Old Sea Map**.
- **Mew moved to Faraway Island,** reached with the Old Sea Map. As before, it only appears once you've caught the other 150 Kanto Pokémon. Professor Oak's tip now points to the Sevii Islands instead of Mt. Moon.
- **Each island has its own extras:**
  - **One:** Treasure Beach (dig in the sand) and Kindle Road.
  - **Two:** the Joyful Game Corner. At Cape Brink, a tutor teaches the ultimate move (Frenzy Plant, Blast Burn or Hydro Cannon) to any generation's fully evolved starter.
  - **Three:** the biker gang blocks Bond Bridge. Beyond it, rescue the lost girl Lostelle from a Hypno in the Berry Forest; her family thanks you on Two Island.
  - **Four:** a Day Care.
  - **Five:** Resort Gorgeous, the Water Labyrinth (a Togepi from an old man) and the dark Lost Cave.
  - **Six:** Pattern Bush and Ruin Valley.
  - **Seven:** Sevault Canyon, the **Trainer Tower** (three floors, then the Tower Master) and the **Tanoby Ruins**. Solve seven number-pattern doors there and Unown pour out to be caught.
- Six journal entries guide the Sevii story.
- **New for story events:** an event can run a math puzzle, which also works from wild areas, and a move tutor can teach a move.

## Unreleased: the Orange Islands

- **A new post-game region from the anime.** Once you're Champion of both Kanto and Johto, Professor Ivy invites you, and a ferry sails from Vermilion and Olivine to Valencia Island. Before then, a sailor at either port explains the rule.
- **Ships between every island.** Each island's travel menu lists a ship to every other island, and more open as you earn badges. Long menus now wrap into columns so they fit on screen.

  | Islands | Open after |
  |---|---|
  | Valencia, Mikan | arrival |
  | Navel, Pinkan | Coral-Eye Badge |
  | Trovita, Sunburst | Sea Ruby Badge |
  | Kumquat, Shamouti | Spike Shell Badge |
  | Pummelo | Jade Star Badge |

- **The Orange Crew.** Each Gym opens with its leader's challenge from the show as a math minigame, then two Gym trainers, then the leader. Badges have their own art.

  | Island | Leader | Challenge | Team | Badge |
  |---|---|---|---|---|
  | Mikan | Cissy | Water Gun targets (addition) | Seadra 60, Blastoise 62 | Coral-Eye |
  | Navel | Danny | Climb the volcano (subtraction; a miss slides you down) | Nidoqueen 64, Scyther 64, Electrode 66 | Sea Ruby |
  | Trovita | Rudy | Find the Spike Shell pile (counting) | Electabuzz 67, Starmie 67, Exeggutor 69 | Spike Shell |
  | Kumquat | Luana | Doubles (4 + 4...) | Alakazam 71, Marowak 72 | Jade Star |

- **The Orange League.** Drake at Pummelo Stadium fields a full six: Ditto, Onix, Gengar, Venusaur, Electabuzz and Dragonite (Lv 76). Winning earns the Winner's Trophy and the title. There's no house move, since the islands are a trip. Drake can be rematched 10 levels higher.
- **Three special islands:**
  - **Pinkan Island:** a reserve of pink Pokémon (16 Pinkan forms, with their own pink art). Stop Jessie and James poaching, and Officer Jenny gives you a permit to catch them.
  - **Sunburst Island:** Mateo the glassblower sends you to the Crystal Cave for the catchable Crystal Onix (Rock/Ice, glass-clear art). Show him and he makes you an Amulet Coin.
  - **Shamouti Island:** at the festival you're named the Chosen One. Calm Moltres, Articuno and Zapdos on Fire, Ice and Lightning Islands for their treasures. Then place them at the Shrine and Lugia rises from the sea.
- **Valencia Island:** Professor Ivy gives you the GS Ball (Celebi in Ilex Forest), a lost Lapras joins you, and Tracey battles you after your first badge.
- **Every island has a wild area** with Gen 1–2 Pokémon and island trainers: swimmers, fishermen, sailors, hikers, skiers and dragon tamers. Pummelo's cliffs have Dratini and even Drake's Ditto. Levels run from 50 on Valencia to 64 at the Shrine.
- The Orange Islands follow the "Kanto stays Kanto" rules, get their own badge case page and journal missions, and never appear in the new-game or move pickers.
- **Fix:** wild Pokémon with their own form art (Alolan forms in Kanto pools, Pinkan forms) showed the ordinary sprite. They now show their form's art.

## Unreleased: Johto teams, Silver and Red, League rematches

- **Johto teams match HeartGold/SoulSilver.** Every Gym Leader, Elite Four member and Lance has their HGSS team. Levels are scaled so Lance's ace is Lv 63, the same as Kanto's Champion. Johto's wild areas are scaled to match.
- **Silver follows the games.**
  - The first battle is in Cherrygrove after Mr. Pokémon, not an ambush in New Bark.
  - He battles again at Azalea, the Burned Tower, the Goldenrod Underground and Victory Road (Mt. Silver city).
  - His team always has the starter that beats yours.
  - The made-up Tyranitar fight on Mt. Silver is gone.
- **Red is on Mt. Silver.** "Challenge Red" is now a trainer battle with his HGSS team: Pikachu 88, Lapras 80, Snorlax 82, Venusaur 84, Charizard 84, Blastoise 84.
- **Every region's League works like Indigo.**
  - A loss starts the League over from the first Elite Four member.
  - After the title, the League becomes a rematch.
  - Johto uses the HGSS rematch teams, and Kanto keeps its FireRed/LeafGreen ones. Other regions add 10 levels.
- **Marts are the same everywhere.**
  - Every mart sells Poké Balls, Potions and Full Heals.
  - The Everstone comes after 2 badges and Revive after 3.
  - Rare Candy is sold only at League towns and department stores.
  - Evolution items follow the region rules, so Johto stays Johto: no Dawn Stones or later-generation items until their regions are played.
- **Kanto and Johto are linked by travel.**
  - After either title, a message says the road to the other region is open, and you get the S.S. Ticket.
  - The S.S. Aqua sails between Vermilion and Olivine.
  - Picking Kanto or Johto in Mom's region picker now says to travel there instead of moving house.
- **Story items from the games:**
  - **The Magnet Train:** talk to the Power Plant manager, find the Machine Part in the Cerulean Gym's pool, then return Copycat's Clefairy doll (from the Fan Club) for her Pass. The train runs between Saffron and Goldenrod.
  - **The Red Scale:** pick it up at the Lake of Rage, and Mr. Pokémon trades it for an Exp. Share.
  - **Celebi:** it now needs the GS Ball, which will come from Professor Ivy in the Orange Islands.
  - **The Shiny Charm:** show Professor Oak all 251 Kanto and Johto Pokémon. It triples shiny odds.
- **National Park** no longer shows Gym, Catch and Battle buttons that did nothing.

## Unreleased: HMs, story gates and real growth curves

- **Real growth curves, fast leveling.** Every species now levels on its real curve (Fast, Medium, Slow, Erratic...). XP uses the real Gen 7 formula: the foe's base XP yield, the level gap, ×1.5 from trainers and ×1.2 with strong affection. All XP is then ×3 (`XP_BOOST` in `src/pokemon/growth.py`) so leveling stays quick. An even fight is worth about a level, and early fights about two.
- **HMs (Johto through Kalos).** Each Gym gives the HM its badge unlocks in the games, announced with the badge ("You received HM Surf!"). Saves that already have badges get their HMs automatically. HMs are key items, so they can't be sold.

  | Region | Badge → HM |
  |---|---|
  | Johto | Zephyr Flash, Hive Cut, Plain Strength, Fog Surf, Storm Fly, Glacier Whirlpool, Rising Waterfall |
  | Hoenn | Stone Cut, Knuckle Flash, Dynamo Rock Smash, Heat Strength, Balance Surf, Feather Fly, Mind Dive, Rain Waterfall |
  | Sinnoh | Coal Rock Smash, Forest Cut, Cobble Fly, Fen Defog, Relic Surf, Mine Strength, Icicle Rock Climb, Beacon Waterfall |
  | Unova | Trio Cut, Basic Strength, Bolt Surf, Quake Fly, Freeze Waterfall, Legend Dive |
  | Kalos | Bug Cut, Cliff Strength, Rumble Surf, Plant Fly, Fairy Waterfall |

- **Story gates in every region after Kanto,** so each region plays in its games' order. A test walks each region from the start, badge by badge, and checks that only the next steps open.
  - **Johto:**
    - Route 32 opens after Falkner.
    - Cut opens Ilex Forest, Flash opens Dark Cave, and Surf opens the routes to Cianwood and Mahogany.
    - Morty waits for the Burned Tower rival battle, Jasmine for Amphy's medicine, and Pryce for the Rocket Hideout.
    - The Red Gyarados now comes before the Hideout.
    - Route 44 opens after the Radio Tower.
    - Whirlpool opens the Whirl Islands, and Waterfall opens the road from Tohjo Falls to the League.
    - Kanto opens after the Johto title, and Mt. Silver after 16 badges.
  - **Hoenn:**
    - Mr. Briney's boat (Rustboro → Dewford → Slateport) is added.
    - Rock Smash, Strength, Surf, Dive and Waterfall gate their places.
    - The League needs 8 badges.
  - **Sinnoh:**
    - The road to Floaroma opens after Roark, and the bridge after the Windworks.
    - The Bicycle (from the Galactic building) opens Cycling Road and Mt. Coronet.
    - Celestic needs the Fen Badge and Defog, and Canalave needs Surf.
    - Snowpoint needs Strength, and Spear Pillar needs Rock Climb and the Galactic HQ.
    - Sunyshore opens after Spear Pillar.
  - **Unova:** each city's road opens after its Gym, Victory Road after the Legend Badge, and Lacunosa and Undella after the title.
  - **Kalos:**
    - The Snorlax on Route 7 needs a visit to Parfum Palace (for the Poké Flute).
    - Each city's road opens after its Gym, with Surf to Azure Bay and Waterfall and Strength for Victory Road.
    - Pokémon Village opens after the title.
  - **Alola:** the ferries follow the island challenge, and each kahuna waits for that island's trials.
  - **Galar:** each town's road opens after its Gym.
  - **Paldea** stays open-world, as in the games.
- **Fixes found along the way:**
  - The Silver League couldn't be reached at all.
  - Blackthorn hid all of its exits.
  - Lugia could never be challenged.
  - Olivia needed a badge that comes after her, so she could never be fought.
  - Team Flare's Geosenge showdown never appeared, so Kalos couldn't be finished.
  - Bugsy's "clear the Slowpoke Well first" rule wasn't checked.
  - Hoenn's "KNuckle" badge didn't count.
  - Badges from other regions with the same name (Grass, Fairy…) unlocked gates in the wrong region.
  - The Galactic HQ key check never worked.

## Unreleased: math rules, voices and playthrough fixes

- **Wrong answers don't waste the turn anymore.** Your move still happens, in normal Speed order, but with a weak damage roll (75–85% instead of the usual 85–100%). A line explains it: "The answer was off, so the attack was weaker."
- **Quick answers earn a bonus.** A right answer in under 2 seconds (a hidden timer) gives one random bonus:
  - a max-power damage roll;
  - a higher critical-hit chance;
  - a chance to make the foe flinch, if you move first.
  A line explains it whenever the bonus makes a difference ("Your speedy answer powered up CHARMANDER's attack: max power!").
- **XP follows the real formula only:** the level-gap scaling, 1.5x from trainers and 1.2x with strong affection. The "Tough foe bonus!" and "(easy foe)" notes and the extra cap on big level gaps are gone.
- **Character voices with the built-in speech:** lines that start with a name ("Professor Oak: ...", "Mom: ...") are read out automatically. Each character has their own voice, with male or female, pitch and speed (a deep, slow Oak; quick rivals). The speaker button reads any line.
- **Mew** can only be found after catching all 150 other Kanto Pokémon. Other regions' Pokémon and alternate forms no longer count toward Oak's sighting.
- **Fixes from Grok's 151/151 playthrough:**
  - Struggle no longer crashes the move menu.
  - A wild Ditto's Transform no longer soft-locks the battle. A second crash right after the Transform is also fixed.
  - The Game Corner menu comes back after Cash In or Slots.
  - If something unexpected goes wrong, the game writes `crash.log` and returns you to the current town or route ("Your progress is safe") instead of closing.
- **No more "ghost" exits:** route buttons ignore taps for half a second after they appear, so a quick tap left over from a catch can't send you down a route you didn't choose.

## Unreleased: presentation pass (from Grok's UI comparison)

- **One fixed 1280×720 canvas.** The game scales to any window or screen, with black bars if the shape differs. Every screen now looks the same on every monitor and tablet, and the window can be resized freely. This fixes text that grew with screen width while spacing didn't, like the clipped CANCEL and overlapping labels.
- **Buttons** have a raised look (a darker lip underneath and a light top edge), glow under the mouse, and play soft click and back sounds.
- **Text boxes** show a bobbing arrow when they're waiting for a tap, and line breaks are kept (the town panel reads "Welcome to / Viridian City!").
- **Screens crossfade** in about a quarter of a second.
- **Move buttons:**
  - The move name, a type pill with the full type name, and the power.
  - A badge you can read without words: green **!!** for super effective, orange **▼** for not very, grey **✕** for no effect, plus the word.
  - Moves that match the Pokémon's own type have a gold border.
- **Answer feedback:**
  - A right answer flashes green with a star burst, a cheer ("Great job!", "Awesome!"...) and a chime.
  - A wrong answer gently shows the right one ("Nice try! It was 18.") before the foe moves.
- **HP bars** slide to their new value, show the HP just lost as a light-red chunk that drains away, and have bigger "HP 40/46" numbers. The level moved up to the name line.
- **MENU button:** the column of small buttons (PC, Bag, Badges, Save, Load, Journal, Fly, Map, Options) is now one big MENU button. It opens a grid of large tiles with icons. Tapping outside the grid, CLOSE, or Esc goes back.
- **Read-aloud (Windows):** a speaker button on the battle question, the catch question and every text box reads it out. Math reads naturally ("7 + 3 = ?" becomes "7 plus 3 equals what?").
- The party CANCEL button fits its label, and the "USEABLE ITEMS" pocket is now "ITEMS".

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
- A larger UI pass over the PC, Pokédex and badge case screens.

### Long-term add-ins
- An Options page: music and sound volume, text speed, big text.
- The Sinnoh Underground.
