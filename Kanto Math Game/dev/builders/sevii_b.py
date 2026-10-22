"""Sevii Islands 4-7 and Faraway Island (Rainbow Pass, after the Hall of Fame)."""
from sevii_a import S, HOME
from sublib import event, trainer, battle

# ---- Four Island: Lorelei's home, the Day Care, Icefall Cave.
S.town("FOUR_ISLAND", "Four Island", 52, [
    {"text": "Pokemon Day Care", "action": "NPC", "target": "day_care"},
    event("Lorelei's House", {
        "lines": ["Lorelei: This is my home island. I came back to rest after the League...",
                  "But Team Rocket is in Icefall Cave, catching Lapras to sell! Please stop them."],
        "flag": "met_lorelei_sevii",
        "done": ["Lorelei: Thank you for saving the Icefall Cave Pokemon."]},
        flag_condition="not sevii_icefall_cleared"),
    event("Battle Lorelei", {
        "requires": ["sevii_icefall_cleared"],
        "lines": ["Lorelei: You saved the Lapras. Now, a battle, just for fun. Don't hold back!"],
        "battle": battle("Lorelei", "ELITE_FOUR", "loreli.png", [87, 91, 80, 124, 131], [56, 57, 56, 58, 60],
                         ["Lorelei: Still as strong as ever. Come back any time."], balls=15),
        "flag": "defeated_lorelei_sevii", "done": ["Lorelei: That was a wonderful battle."]},
        condition="sevii_icefall_cleared"),
], local=[("Icefall Cave", "ICEFALL_CAVE", None)], extra_travel=HOME)

S.wild("ICEFALL_CAVE", "Icefall Cave", 52, "cave",
       {220: 14, 221: 6, 225: 12, 215: 12, 42: 12, 86: 12, 87: 6, 124: 6, 131: 3, 90: 9, 91: 3, 238: 5},
       [("Four Island", "FOUR_ISLAND")],
       [trainer("Ace Trainer Nia", "ACE_TRAINER", "acetrainer_f.png", [87, 221, 124], balls=6),
        trainer("Fisherman Lou", "FISHERMAN", "fisherman.png", [130, 119, 91])],
       extra=[event("STOP TEAM ROCKET", {
           "requires": ["met_lorelei_sevii"],
           "fail": ["Voices echo from deep in the ice... Someone in town might know what's going on."],
           "lines": ["Rocket Grunts have trapped a pod of Lapras in nets!",
                     "Grunt: These Lapras will make us a fortune! And there's word of a gem on Six Island..."],
           "battle": battle("Rocket Grunts", "ROCKET_GRUNT", "rocket_grunt_f.png", [24, 42, 110, 20],
                            [50, 51, 52, 52], ["Grunt: Ugh! Let the Lapras go! Retreat to the warehouse!"]),
           "flag": "sevii_icefall_cleared"},
           condition="met_lorelei_sevii", flag_condition="not sevii_icefall_cleared")])

# ---- Five Island: Resort Gorgeous, the Water Labyrinth, Lost Cave, the Rocket Warehouse.
S.town("FIVE_ISLAND", "Five Island", 54, [
    event("Resort Gorgeous", {
        "lines": ["Selphy: Welcome to my villa! Oh, a real Champion!",
                  "Please, take a little something from our resort shop."],
        "gift_item": {"balls": 10, "RARE_CANDY": 2}, "flag": "visited_resort_gorgeous",
        "done": ["Selphy: Do come again!"]}),
], local=[("Five Isle Meadow", "FIVE_ISLE_MEADOW", None), ("Water Labyrinth", "WATER_LABYRINTH", None),
          ("Lost Cave", "LOST_CAVE", None), ("Rocket Warehouse", "ROCKET_WAREHOUSE", "sapphire_stolen")],
    extra_travel=HOME)

S.wild("FIVE_ISLE_MEADOW", "Five Isle Meadow", 54, "grass",
       {198: 14, 228: 12, 229: 4, 161: 10, 162: 6, 17: 10, 52: 10, 53: 5, 194: 10, 183: 10, 184: 5, 203: 4},
       [("Five Island", "FIVE_ISLAND")],
       [trainer("Rich Boy Theo", "RICH_BOY", "richboy.png", [52, 53, 203], balls=8),
        trainer("Rocket Grunt", "ROCKET_GRUNT", "rocket_grunt_m.png", [198, 228, 229])])
S.wild("WATER_LABYRINTH", "Water Labyrinth", 54, "ocean",
       {194: 15, 195: 8, 183: 15, 184: 6, 72: 12, 73: 6, 60: 10, 61: 6, 186: 2, 118: 10, 119: 5, 170: 5},
       [("Five Island", "FIVE_ISLAND")],
       [trainer("Swimmer Gil", "SWIMMER", "swimmer_m.png", [61, 184, 73])],
       extra=[event("THE OLD MAN'S EGG", {
           "lines": ["Old Man: I raise Pokemon by the water... This Egg hatched while I wasn't looking!",
                     "Togepi needs a trainer who travels. Will you take it?"],
           "gift_pokemon": 175, "flag": "got_sevii_togepi"},
           flag_condition="not got_sevii_togepi")])
S.wild("LOST_CAVE", "Lost Cave", 55, "cave",
       {92: 14, 93: 10, 94: 3, 200: 10, 41: 12, 42: 10, 198: 10, 228: 10, 177: 8, 178: 4},
       [("Five Island", "FIVE_ISLAND")],
       [trainer("Channeler Ivy", "CHANNELER", "channeler.png", [93, 200, 94])],
       extra=[event("SEARCH THE DARK", {
           "lines": ["You feel your way through the pitch-black cave...",
                     "Someone dropped a pouch here long ago. You found it!"],
           "gift_item": {"RARE_CANDY": 3}, "flag": "lost_cave_searched"},
           flag_condition="not lost_cave_searched")])
S.wild("ROCKET_WAREHOUSE", "Rocket Warehouse", 57, "indoor", {},
       [("Five Island", "FIVE_ISLAND")],
       [trainer("Rocket Grunt", "ROCKET_GRUNT", "rocket_grunt_m.png", [110, 42, 24]),
        trainer("Rocket Grunt", "ROCKET_GRUNT", "rocket_grunt_f.png", [89, 20, 53]),
        trainer("Scientist Gideon", "SCIENTIST", "scientist.png", [82, 101, 137])],
       extra=[event("UNLOCK THE DOORS", {
                  "puzzle": "security", "lines": ["The doors open, one by one. The Admin's office is ahead!"],
                  "puzzle_fail": ["The door pads reset. Try the codes again!"],
                  "flag": "warehouse_doors_open"},
                  flag_condition="not warehouse_doors_open"),
              event("CONFRONT THE ADMIN", {
                  "requires": ["warehouse_doors_open"],
                  "lines": ["Admin: So you're the one ruining our plans on every island.",
                            "With the Ruby and Sapphire we'd force any Pokemon to evolve! Prepare yourself!"],
                  "battle": battle("Rocket Admin Archer", "ROCKET_ADMIN", "archer.png", [229, 110, 42, 24, 112],
                                   [56, 57, 56, 57, 59], ["Archer: Impossible... Take your precious gems, then!"],
                                   balls=15),
                  "flag": "sevii_warehouse_cleared"},
                  condition="warehouse_doors_open", flag_condition="not sevii_warehouse_cleared"),
              event("RECOVER THE GEMS", {
                  "requires": ["sevii_warehouse_cleared"],
                  "lines": ["On the Admin's desk sit two glowing gems: the Ruby and the Sapphire!",
                            "Team Rocket's Sevii hideout is shut down for good. Take them to Celio!"],
                  "gift_item": {"RUBY": 1, "SAPPHIRE": 1}, "flag": "got_sevii_gems"},
                  condition="sevii_warehouse_cleared", flag_condition="not got_sevii_gems")])

# ---- Six Island: Pattern Bush, Ruin Valley, the Dotted Hole (Sapphire).
S.town("SIX_ISLAND", "Six Island", 56, [
    event("Ruin Maniac's Notes", {
        "lines": ["Ruin Maniac: There's a sealed cave in Ruin Valley called the Dotted Hole.",
                  "Its walls are covered in raised dots. Count them right and the door opens!"]}),
], local=[("Pattern Bush", "PATTERN_BUSH", None), ("Ruin Valley", "RUIN_VALLEY", None)], extra_travel=HOME)

S.wild("PATTERN_BUSH", "Pattern Bush", 56, "forest",
       {214: 10, 165: 8, 166: 8, 167: 8, 168: 8, 177: 12, 178: 6, 204: 10, 193: 10, 127: 6, 48: 8, 13: 6},
       [("Six Island", "SIX_ISLAND")],
       [trainer("Bug Catcher Ray", "BUG_CATCHER", "bug_catcher.png", [214, 166, 168]),
        trainer("Psychic Mira", "PSYCHIC", "psychic.png", [178, 64, 196])])
S.wild("RUIN_VALLEY", "Ruin Valley", 57, "mountain",
       {177: 12, 178: 8, 194: 10, 195: 6, 193: 10, 202: 6, 203: 8, 231: 10, 232: 4, 74: 14, 207: 12},
       [("Six Island", "SIX_ISLAND"), ("Dotted Hole", "DOTTED_HOLE")],
       [trainer("Ruin Maniac Hal", "RUIN_MANIAC", "ruinmaniac.png", [232, 76, 112]),
        trainer("Psychic Dex", "PSYCHIC", "psychic_m.png", [202, 203, 97])])
S.wild("DOTTED_HOLE", "Dotted Hole", 58, "indoor", {},
       [("Ruin Valley", "RUIN_VALLEY")],
       extra=[event("READ THE BRAILLE", {
                  "puzzle": "braille", "lines": ["A hidden passage opens into the ruins below!"],
                  "puzzle_fail": ["The dots stay silent. Maybe count again?"],
                  "flag": "dotted_hole_open"},
                  flag_condition="not dotted_hole_open"),
              event("TAKE THE SAPPHIRE", {
                  "requires": ["dotted_hole_open"],
                  "lines": ["Deep underground, a blue gem glows on a stone pedestal: the Sapphire!",
                            "As you reach for it, a man in a lab coat shoves past and grabs it!",
                            "Gideon: Thanks for opening the door! Team Rocket will pay well for this.",
                            "He runs off toward the docks... toward Five Island's Rocket Warehouse!"],
                  "flag": "sapphire_stolen"},
                  condition="dotted_hole_open", flag_condition="not sapphire_stolen")])

# ---- Seven Island: the Trainer Tower, Sevault Canyon, the Tanoby Ruins (Unown).
S.town("SEVEN_ISLAND", "Seven Island", 58, [
    {"text": "Trainer Tower", "action": "GYM", "color": "GOLD"},
], local=[("Sevault Canyon", "SEVAULT_CANYON", None), ("Tanoby Ruins", "TANOBY_RUINS", None)],
    extra_travel=HOME,
    gym={"trainers": [
        {"name": "Expert Rolf", "class": "EXPERT", "sprite": "veteran.png", "team": [57, 68, 107], "levels": [57, 58, 59],
         "rewards": {"balls": 5}, "dialogue": {"intro": ["Floor 1! Can you climb the whole Tower?"]}},
        {"name": "Black Belt Koji", "class": "BLACK_BELT", "sprite": "blackbelt.png", "team": [106, 237, 214],
         "levels": [58, 59, 60], "rewards": {"balls": 5}, "dialogue": {"intro": ["Floor 2! My fists are ready!"]}},
        {"name": "Ace Trainer Vera", "class": "ACE_TRAINER", "sprite": "acetrainer_f.png", "team": [36, 199, 230],
         "levels": [59, 60, 61], "rewards": {"balls": 5}, "dialogue": {"intro": ["Floor 3! Almost at the top!"]}}],
        "leader": {"name": "Tower Master", "class": "TOWER_MASTER", "sprite": "master.png", "is_boss_battle": True,
                   "team": [248, 227, 232, 197, 229, 149], "levels": [62, 61, 61, 61, 61, 63],
                   "rewards": {"balls": 20, "RARE_CANDY": 5}, "victory_flag": "trainer_tower_cleared",
                   "dialogue": {"intro": ["The top floor! I am the Tower Master. Show me your best!"],
                                "player_won": ["You've conquered the Trainer Tower! Climb again any time."],
                                "player_lost": ["The Tower stands. Come back and try again!"]}},
        "requirements": {"badges": 0}})

S.wild("SEVAULT_CANYON", "Sevault Canyon", 58, "mountain",
       {246: 6, 231: 12, 232: 6, 227: 10, 74: 12, 75: 8, 104: 12, 105: 6, 207: 12, 111: 10, 66: 6},
       [("Seven Island", "SEVEN_ISLAND")],
       [trainer("Black Belt Ken", "BLACK_BELT", "blackbelt.png", [107, 106, 237]),
        trainer("Ace Trainer Gale", "ACE_TRAINER", "acetrainer_m.png", [227, 232, 247], balls=6)])
S.wild("TANOBY_RUINS", "Tanoby Ruins", 58, "cave", {201: 100},
       [("Seven Island", "SEVEN_ISLAND")],
       extra=[event("OPEN THE CHAMBERS", {
           "puzzle": "tanoby", "lines": ["Unown of every shape swirl out of the seven chambers!"],
           "puzzle_fail": ["The chamber doors stay sealed."], "flag": "tanoby_chambers_open"},
           flag_condition="not tanoby_chambers_open")],
       catch_cond=["has_balls", "tanoby_chambers_open"])

# ---- Faraway Island: Mew, after the Sevii story (and all 150 Kanto Pokemon, as before).
S.wild("FARAWAY_ISLAND", "Faraway Island", 60, "forest", {},
       [("Seagallop to One Island", "ONE_ISLAND")],
       extra=[event("FOLLOW THE PINK SHADOW", {
                  "lines": ["Tall grass sways on the uncharted island. Something pink giggles and darts away...",
                            "It only shows itself to a trainer who has caught all 150 other Kanto Pokemon.",
                            "Your Pokedex: {kanto_caught} of the 150 Kanto Pokemon. {kanto_missing} still to catch!"]},
                  condition="not:caught_range:1-150"),
              {"text": "CHALLENGE MEW", "action": "BOSS", "color": "GOLD",
               "condition": ["boss_not_defeated", "caught_range:1-150"]}],
       area_boss={"id": 151, "name": "Mew", "victory_flag": "caught_mew"})

S.mission("sevii_m1", "SIDE", "The Sevii Islands",
          "Blaine's Tri-Pass opens the Seagallop Ferry from Vermilion. Meet Celio on One Island.",
          {"item": "TRI_PASS", "flag_not": "met_celio"}, "Network Machine")
S.mission("sevii_m2", "SIDE", "Team Rocket on Mt. Ember",
          "Researchers on Mt. Ember saw Team Rocket digging for a gem. Chase them off, and look for Moltres at the summit.",
          {"flag": "met_celio", "flag_not": "sevii_ember_rocket"}, "Moltres")
S.mission("sevii_m3", "SIDE", "Lost Lostelle",
          "Lostelle never came home from Three Island. Beat the bikers on Bond Bridge and search the Berry Forest.",
          {"flag": "heard_lostelle", "flag_not": "rescued_lostelle"}, "Rare Candy")
S.mission("sevii_m4", "SIDE", "The Rainbow Pass",
          "As Champion with the National Pokedex, ask Celio for the Rainbow Pass to Islands 4-7.",
          {"flag": ["met_celio", "beat_champion"], "flag_not": "got_rainbow_pass"}, "Rainbow Pass")
S.mission("sevii_m5", "SIDE", "The Ruby and the Sapphire",
          "Stop Team Rocket in Icefall Cave, open the Dotted Hole on Six Island, then raid the Rocket Warehouse on Five Island.",
          {"item": "RAINBOW_PASS", "flag_not": "network_machine_fixed"}, "Old Sea Map")
S.mission("sevii_m6", "SIDE", "The Faraway Island",
          "Celio's old sea map shows an uncharted island. A pink Pokemon lives there...",
          {"item": "OLD_SEA_MAP", "flag_not": "caught_mew"}, "Mew")
