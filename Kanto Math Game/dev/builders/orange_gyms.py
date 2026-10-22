"""Valencia Island and the Orange Crew gym islands."""
from orange_lib import town, wild, event, leader, gym_trainer, trainer

# ---- Valencia Island: Professor Ivy, the GS Ball, a lost Lapras, Tracey.
town("VALENCIA_ISLAND", 50, [
    event("Professor Ivy's Lab", {
        "lines": ["Professor Ivy: Welcome to Valencia Island, Champion!",
                  "I study how Pokemon here differ from Kanto's. Some are new colors, some grow bigger!",
                  "Before you go, I have a favor. I found this strange ball, and nobody can open it.",
                  "Kurt in Azalea Town knows Poke Balls better than anyone. Would you take it to Johto?",
                  "They say a Pokemon that travels through time lives in Ilex Forest..."],
        "gift_item": {"GS_BALL": 1}, "flag": "got_gs_ball",
        "done": ["Professor Ivy: The four Orange Crew Gyms are on Mikan, Navel, Trovita and Kumquat.",
                 "Win all four badges, then challenge Drake at Pummelo Stadium!"]}),
    event("Help the Lost Lapras", {
        "lines": ["A young Lapras is stranded in the shallows, crying for its herd.",
                  "You stay with it all afternoon. It doesn't want to leave your side!"],
        "gift_pokemon": 131, "flag": "got_orange_lapras"},
        flag_condition="not got_orange_lapras"),
    event("Battle Tracey", {
        "requires": ["has_coral_eye_badge"],
        "fail": ["Tracey: I'm a Pokemon Watcher! Win a badge, then I'd love to sketch your team in battle."],
        "lines": ["Tracey: You won Cissy's badge! Let me watch your Pokemon up close. Battle me!"],
        "battle": {"name": "Tracey", "class": "POKEMON_WATCHER", "sprite": "pokefan_m.png",
                   "team": [183, 48, 123], "levels": [58, 58, 61], "rewards": {"balls": 10},
                   "dialogue": {"player_won": ["Tracey: Amazing! I'll call this sketch Champion in Action."]}},
        "flag": "defeated_tracey",
        "done": ["Tracey: My sketchbook is filling up with your Pokemon!"]}),
], local=[("Valencia Beach", "VALENCIA_BEACH", None)],
    extra_travel=[{"text": "Ship to Vermilion City", "target_area": "VERMILLION_CITY",
                   "message": "The ferry sails north, back to Vermilion City in Kanto."},
                  {"text": "Ship to Olivine City", "target_area": "OLIVINE_CITY",
                   "message": "The ferry sails north-west, back to Olivine City in Johto."}])
wild("VALENCIA_BEACH", "Valencia Beach", 50, "ocean",
     {98: 15, 90: 12, 120: 12, 72: 15, 54: 10, 79: 10, 116: 10, 118: 8, 131: 3, 170: 5},
     [("Valencia Island", "VALENCIA_ISLAND")],
     [trainer("Swimmer Coral", "SWIMMER", "swimmer_f.png", [120, 121]),
      trainer("Fisherman Hal", "FISHERMAN", "fisherman.png", [129, 118, 130]),
      trainer("Beauty Sandy", "BEAUTY", "beauty.png", [54, 79, 80])])

# ---- Mikan Island: Cissy (Coral-Eye Badge).
town("MIKAN_ISLAND", 52, [{"text": "Mikan Gym", "action": "GYM", "color": "GOLD"}],
     local=[("Mikan Reef", "MIKAN_REEF", None)],
     gym={"trainers": [
         gym_trainer("Swimmer Kai", "SWIMMER", "swimmer_m.png", [116, 90, 120], [55, 55, 57],
                     "Cissy's Gym is all about water. Hope you can swim!"),
         gym_trainer("Fisherman Wade", "FISHERMAN", "fisherman.png", [118, 119, 130], [56, 56, 58],
                     "The best catches come from Mikan's reef!")],
         "leader": leader("Cissy", "swimmer_f.png", [117, 9], [60, 62], "CORAL_EYE",
                          ["Cissy: I'm Cissy of the Orange Crew. Seadra and Blastoise, let's go!"],
                          ["Cissy: What a splash! The Coral-Eye Badge is yours."],
                          ["Cissy: Better work on that aim. Come back any time!"]),
         "requirements": {"badges": 0}})
wild("MIKAN_REEF", "Mikan Reef", 52, "ocean",
     {116: 15, 117: 6, 222: 15, 90: 12, 118: 12, 223: 12, 224: 5, 226: 8, 129: 10, 211: 5},
     [("Mikan Island", "MIKAN_ISLAND")],
     [trainer("Swimmer Lani", "SWIMMER", "swimmer_f.png", [222, 117]),
      trainer("Sailor Brock", "SAILOR", "sailor.png", [66, 67, 99])])

# ---- Navel Island: Danny (Sea Ruby Badge). A snowy volcano.
town("NAVEL_ISLAND", 55, [{"text": "Navel Gym", "action": "GYM", "color": "GOLD"}],
     local=[("Navel Summit", "NAVEL_SUMMIT", None)],
     gym={"trainers": [
         gym_trainer("Hiker Dale", "HIKER", "hiker.png", [75, 95, 76], [59, 59, 61],
                     "Danny's challenge starts at the bottom of the volcano!"),
         gym_trainer("Skier Frost", "SKIER", "skier.png", [86, 87, 124], [60, 60, 62],
                     "It's freezing at the top. Can your Pokemon take it?")],
         "leader": leader("Danny", "boarder.png", [31, 123, 101], [64, 64, 66], "SEA_RUBY",
                          ["Danny: You made it up the mountain. Now for a three-on-three battle!"],
                          ["Danny: Great battle! Take the Sea Ruby Badge."],
                          ["Danny: Not bad! Climb back up when you're ready."]),
         "requirements": {"badges": 1, "fail_text": "Danny only battles trainers with the Coral-Eye Badge."}})
wild("NAVEL_SUMMIT", "Navel Summit", 55, "mountain",
     {86: 12, 87: 6, 124: 8, 220: 14, 221: 6, 215: 10, 225: 10, 75: 14, 67: 12, 74: 8},
     [("Navel Island", "NAVEL_ISLAND")],
     [trainer("Hiker Russ", "HIKER", "hiker.png", [74, 75, 95]),
      trainer("Skier Bree", "SKIER", "skier.png", [220, 221, 225])])

# ---- Trovita Island: Rudy (Spike Shell Badge).
town("TROVITA_ISLAND", 58, [{"text": "Trovita Gym", "action": "GYM", "color": "GOLD"}],
     local=[("Trovita Shore", "TROVITA_SHORE", None)],
     gym={"trainers": [
         gym_trainer("Sailor Brine", "SAILOR", "sailor.png", [99, 73, 130], [62, 62, 64],
                     "Rudy's Gym floats on the water. Mind your footing!"),
         gym_trainer("Engineer Volt", "ENGINEER", "engineer.png", [82, 101, 125], [63, 63, 65],
                     "I keep the Gym's lights on. Let's see how you handle a jolt!")],
         "leader": leader("Rudy", "acetrainer_m.png", [125, 121, 103], [67, 67, 69], "SPIKE_SHELL",
                          ["Rudy: Welcome to Trovita! My Pokemon and I battle with style."],
                          ["Rudy: Brilliant! The Spike Shell Badge suits you."],
                          ["Rudy: Better luck next time. The ferry will bring you back!"]),
         "requirements": {"badges": 2, "fail_text": "Rudy only battles trainers with two Orange Crew badges."}})
wild("TROVITA_SHORE", "Trovita Shore", 58, "ocean",
     {102: 14, 55: 10, 120: 12, 121: 5, 114: 10, 128: 8, 73: 12, 170: 10, 171: 6, 99: 8, 125: 5},
     [("Trovita Island", "TROVITA_ISLAND")],
     [trainer("Swimmer Marlin", "SWIMMER", "swimmer_m.png", [73, 171]),
      trainer("Beauty Pearl", "BEAUTY", "beauty.png", [121, 124, 36])])

# ---- Kumquat Island: Luana (Jade Star Badge). Double battles.
town("KUMQUAT_ISLAND", 61, [{"text": "Kumquat Gym", "action": "GYM", "color": "GOLD"}],
     local=[("Kumquat Jungle", "KUMQUAT_JUNGLE", None)],
     gym={"trainers": [
         gym_trainer("Beauty Lani", "BEAUTY", "beauty.png", [36, 40, 210], [66, 66, 68],
                     "Luana's son Travis runs the hotel. I run this battle!"),
         gym_trainer("Gentleman Kale", "GENTLEMAN", "gentleman.png", [59, 128, 241], [67, 67, 69],
                     "Two Pokemon at once? That's how we battle on Kumquat.")],
         "leader": leader("Luana", "acetrainer_f.png", [65, 105], [71, 72], "JADE_STAR",
                          ["Luana: Alakazam and Marowak work as one. Can your team keep up?"],
                          ["Luana: Wonderful teamwork! You've earned the Jade Star Badge.",
                           "Now you may challenge Drake at Pummelo Stadium."],
                          ["Luana: Teamwork takes practice. Come back soon!"]),
         "requirements": {"badges": 3, "fail_text": "Luana only battles trainers with three Orange Crew badges."}})
wild("KUMQUAT_JUNGLE", "Kumquat Jungle", 61, "forest",
     {103: 10, 12: 10, 17: 12, 44: 10, 182: 5, 49: 10, 166: 8, 168: 8, 193: 8, 214: 6, 127: 6, 102: 7},
     [("Kumquat Island", "KUMQUAT_ISLAND")],
     [trainer("Bug Catcher Milo", "BUG_CATCHER", "bug_catcher.png", [12, 214, 127]),
      trainer("Picnicker Rose", "PICNICKER", "picnicker.png", [182, 44, 103])])

# ---- Pummelo Island: the Orange League. Drake and the Winner's Trophy.
town("PUMMELO_ISLAND", 63, [{"text": "Pummelo Stadium", "action": "GYM", "color": "GOLD"}],
     local=[("Pummelo Cliffs", "PUMMELO_CLIFFS", None)],
     gym={"trainers": [],
          "leader": leader("Drake", "veteran.png", [132, 95, 94, 3, 125, 149], [72, 72, 73, 74, 73, 76],
                           "WINNERS_TROPHY",
                           ["Drake: I'm Drake, Supreme Gym Leader of the Orange League.",
                            "Nobody has beaten my six Pokemon in a full battle. Show me what you've got!"],
                           ["Drake: Incredible... My Dragonite has finally met its match.",
                            "The Winner's Trophy is yours, Orange League Champion!"],
                           ["Drake: A good battle, but the trophy stays here. Train and come back!"],
                           cls="CHAMPION", victory_flag="beat_orange_champion",
                           rewards={"balls": 30, "RARE_CANDY": 5}),
          "requirements": {"badges": 4,
                           "fail_text": "Only trainers with all four Orange Crew badges may challenge Drake."}})
wild("PUMMELO_CLIFFS", "Pummelo Cliffs", 63, "mountain",
     {147: 10, 148: 4, 142: 3, 22: 14, 85: 10, 227: 10, 207: 12, 112: 8, 95: 10, 132: 10, 149: 1},
     [("Pummelo Island", "PUMMELO_ISLAND")],
     [trainer("Ace Trainer Sky", "ACE_TRAINER", "acetrainer_m.png", [148, 227, 142], balls=6),
      trainer("Dragon Tamer Ryu", "DRAGON_TAMER", "dragon_tamer.png", [147, 148, 130], balls=6)])
