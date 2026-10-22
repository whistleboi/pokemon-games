"""Sevii Islands 1-3 (Tri-Pass, from Blaine)."""
from sublib import Sub, event, trainer, battle, boss

TRI, RAINBOW = "has_item:TRI_PASS", "has_item:RAINBOW_PASS"
S = Sub("KANTO", "SEVII", "SEVII", {
    "ONE_ISLAND": ("One Island", TRI), "TWO_ISLAND": ("Two Island", TRI), "THREE_ISLAND": ("Three Island", TRI),
    "FOUR_ISLAND": ("Four Island", RAINBOW), "FIVE_ISLAND": ("Five Island", RAINBOW),
    "SIX_ISLAND": ("Six Island", RAINBOW), "SEVEN_ISLAND": ("Seven Island", RAINBOW),
    "FARAWAY_ISLAND": ("Faraway Island", "has_item:OLD_SEA_MAP"),
}, ship_word="Seagallop", ship_line="The Seagallop Ferry speeds across the waves.")
HOME = [{"text": "Seagallop to Vermilion City", "target_area": "VERMILLION_CITY",
         "message": "The Seagallop Ferry speeds back to Vermilion City."}]

# ---- One Island: Celio's Network Machine, Treasure Beach, Kindle Road, Mt. Ember (Moltres).
S.town("ONE_ISLAND", "One Island", 40, [
    event("Celio's Network Machine", {
        "lines": ["Celio: Hi! I'm Celio, Bill's friend. I'm building the Network Machine.",
                  "It will link Kanto's PCs with faraway regions, so trainers can trade with Johto!",
                  "But it needs two special gems, a Ruby and a Sapphire, to power it.",
                  "People say Team Rocket has been sneaking around these islands looking for gems...",
                  "If you find out anything, please come back and tell me!"],
        "flag": "met_celio",
        "done": ["Celio: Still no Ruby or Sapphire... I heard Team Rocket was seen on Mt. Ember."]},
        flag_condition="not network_machine_fixed"),
    event("Celio's Rainbow Pass", {
        "requires": ["beat_champion", "unlocked_national_dex"],
        "fail": ["Celio: The farther islands are only open to Champions with a National Pokedex."],
        "lines": ["Celio: You're the Champion, and you have the National Pokedex!",
                  "Take this Rainbow Pass. The Seagallop Ferry will take you to Islands 4 through 7.",
                  "Maybe out there you'll find where Team Rocket hid the gems!"],
        "gift_item": {"RAINBOW_PASS": 1}, "flag": "got_rainbow_pass"},
        condition="beat_champion", flag_condition="not got_rainbow_pass"),
    event("Give Celio the Gems", {
        "requires": ["has_item:RUBY", "has_item:SAPPHIRE"],
        "lines": ["Celio: The Ruby AND the Sapphire! You got them back from Team Rocket!",
                  "With these, the Network Machine works! Kanto is linked to the world.",
                  "Oh, and the warehouse files mentioned this old sea chart...",
                  "It shows an island that isn't on any map. Sailors see a pink Pokemon there!"],
        "take_item": {"RUBY": 1, "SAPPHIRE": 1}, "gift_item": {"OLD_SEA_MAP": 1}, "flag": "network_machine_fixed"},
        condition="has_item:SAPPHIRE", flag_condition="not network_machine_fixed"),
], local=[("Treasure Beach", "TREASURE_BEACH", None), ("Kindle Road", "KINDLE_ROAD", None)], extra_travel=HOME)

S.wild("TREASURE_BEACH", "Treasure Beach", 38, "ocean",
       {72: 18, 73: 6, 116: 12, 98: 14, 90: 12, 120: 10, 118: 10, 129: 8, 222: 5, 223: 5},
       [("One Island", "ONE_ISLAND")],
       [trainer("Swimmer Mara", "SWIMMER", "swimmer_f.png", [120, 116]),
        trainer("Fisherman Ned", "FISHERMAN", "fisherman.png", [129, 118, 223])],
       extra=[event("DIG IN THE SAND", {
           "lines": ["You dig around the washed-up driftwood...", "Something shiny was buried in the sand!"],
           "gift_item": {"RARE_CANDY": 2}, "flag": "treasure_beach_dug"},
           flag_condition="not treasure_beach_dug")])

S.wild("KINDLE_ROAD", "Kindle Road", 40, "mountain",
       {77: 15, 21: 15, 22: 6, 74: 15, 75: 8, 66: 10, 126: 4, 218: 10, 129: 7, 54: 10},
       [("One Island", "ONE_ISLAND"), ("Mt. Ember", "MT_EMBER")],
       [trainer("Hiker Bert", "HIKER", "hiker.png", [74, 75, 95]),
        trainer("Biker Rex", "BIKER", "biker.png", [109, 88]),
        trainer("Ruin Maniac Ezra", "RUIN_MANIAC", "ruinmaniac.png", [27, 104]),
        trainer("Super Nerd Blaze", "SUPER_NERD", "supernerd.png", [58, 37, 126])])

S.wild("MT_EMBER", "Mt. Ember", 43, "cave",
       {74: 14, 75: 12, 77: 10, 78: 5, 126: 8, 218: 14, 219: 6, 66: 12, 67: 6, 95: 8, 21: 5},
       [("Kindle Road", "KINDLE_ROAD")],
       [trainer("Hiker Gus", "HIKER", "hiker.png", [75, 95, 76])],
       extra=[event("TALK TO THE RESEARCHERS", {
                  "lines": ["Researcher: We're studying the volcano's heat... but two men in black chased us off!",
                            "They were digging near the summit, talking about a gem called the Ruby."],
                  "flag": "met_ember_researchers"},
                  flag_condition="not met_ember_researchers"),
              event("CHASE OFF TEAM ROCKET", {
                  "requires": ["met_ember_researchers"],
                  "lines": ["Rocket Grunt: The boss is gone, but we've got our own plans now!",
                            "Gems, stronger Pokemon, forced evolution... Scram, kid!"],
                  "battle": battle("Rocket Grunts", "ROCKET_GRUNT", "rocket_grunt_m.png", [109, 41, 110, 24],
                                   [42, 42, 44, 44], ["Grunt: Fine, keep the mountain! We'll find the gems elsewhere."]),
                  "flag": "sevii_ember_rocket"},
                  condition="met_ember_researchers", flag_condition="not sevii_ember_rocket"),
              {"text": "CHALLENGE MOLTRES", "action": "BOSS", "color": "GOLD",
               "condition": ["boss_not_defeated", "not:CINNABAR_VOLCANO_boss_defeated"]}],
       area_boss={"id": 146, "name": "Moltres", "victory_flag": "MT_EMBER_boss_defeated"})

# ---- Two Island: the Joyful Game Corner, Cape Brink's move tutor, and the lost Lostelle.
ULTIMATE = {3: "FRENZY-PLANT", 154: "FRENZY-PLANT", 254: "FRENZY-PLANT", 389: "FRENZY-PLANT",
            497: "FRENZY-PLANT", 652: "FRENZY-PLANT", 724: "FRENZY-PLANT", 812: "FRENZY-PLANT", 908: "FRENZY-PLANT",
            6: "BLAST-BURN", 157: "BLAST-BURN", 257: "BLAST-BURN", 392: "BLAST-BURN", 500: "BLAST-BURN",
            655: "BLAST-BURN", 727: "BLAST-BURN", 815: "BLAST-BURN", 911: "BLAST-BURN",
            9: "HYDRO-CANNON", 160: "HYDRO-CANNON", 260: "HYDRO-CANNON", 395: "HYDRO-CANNON", 503: "HYDRO-CANNON",
            658: "HYDRO-CANNON", 730: "HYDRO-CANNON", 818: "HYDRO-CANNON", 914: "HYDRO-CANNON"}
S.town("TWO_ISLAND", "Two Island", 42, [
    {"text": "Joyful Game Corner", "action": "GAMECORNER"},
    event("Lostelle's Dad", {
        "lines": ["Man: My daughter Lostelle went to pick berries on Three Island and never came home!",
                  "Bikers have taken over the bridge there... Please, help me find her!"],
        "flag": "heard_lostelle",
        "done": ["Man: Lostelle went to the Berry Forest past Bond Bridge on Three Island!"]},
        flag_condition="not rescued_lostelle"),
    event("Lostelle's Thanks", {
        "requires": ["rescued_lostelle"],
        "lines": ["Lostelle: Thank you for saving me from that Hypno!",
                  "Dad: How can we ever repay you? Please, take these."],
        "gift_item": {"RARE_CANDY": 3, "balls": 10}, "flag": "lostelle_thanked"},
        condition="rescued_lostelle", flag_condition="not lostelle_thanked"),
], local=[("Cape Brink", "CAPE_BRINK", None)], extra_travel=HOME)

S.wild("CAPE_BRINK", "Cape Brink", 42, "grass",
       {43: 14, 44: 6, 69: 14, 70: 6, 54: 12, 55: 6, 187: 10, 188: 4, 191: 10, 161: 10, 162: 4, 16: 4},
       [("Two Island", "TWO_ISLAND")],
       [trainer("Lass Tia", "LASS", "lass.png", [35, 39, 187]),
        trainer("Youngster Joey", "YOUNGSTER", "youngster.png", [19, 20, 161]),
        trainer("School Kid Ana", "SCHOOL_KID", "school_kid_f.png", [43, 69, 191])],
       extra=[event("VISIT THE MOVE TUTOR", {
           "lines": ["Old Woman: I teach the ultimate moves of the starter Pokemon.",
                     "Show me a fully evolved starter you've raised with love, and I'll teach it!"],
           "teach": {str(k): v for k, v in ULTIMATE.items()}})])

# ---- Three Island: the biker gang, Bond Bridge and the Berry Forest.
S.town("THREE_ISLAND", "Three Island", 44, [
    event("Stop the Biker Gang", {
        "lines": ["Biker: This island's ours now! Nobody crosses Bond Bridge without beating our leader!"],
        "battle": battle("Biker Paxton", "BIKER", "biker.png", [109, 89, 110, 89], [43, 44, 45, 46],
                         ["Paxton: Okay, okay! We're leaving! Take your bridge back!"]),
        "flag": "beat_three_island_bikers",
        "done": ["Townsfolk: The bikers are gone! You can cross Bond Bridge now."]}),
], local=[("Bond Bridge", "BOND_BRIDGE", "beat_three_island_bikers")], extra_travel=HOME)

S.wild("BOND_BRIDGE", "Bond Bridge", 44, "grass",
       {16: 12, 17: 8, 29: 10, 32: 10, 206: 10, 52: 8, 48: 10, 72: 10, 165: 8, 167: 8, 84: 6},
       [("Three Island", "THREE_ISLAND"), ("Berry Forest", "BERRY_FOREST")],
       [trainer("Biker Dan", "BIKER", "biker.png", [88, 109]),
        trainer("Cue Ball Ike", "CUE_BALL", "cueball.png", [56, 66, 57]),
        trainer("Bug Catcher Sam", "BUG_CATCHER", "bug_catcher.png", [48, 165, 167])])

S.wild("BERRY_FOREST", "Berry Forest", 46, "forest",
       {96: 12, 97: 6, 43: 10, 17: 10, 54: 10, 49: 8, 204: 12, 205: 5, 206: 10, 102: 10, 191: 7},
       [("Bond Bridge", "BOND_BRIDGE")],
       extra=[boss("FIND LOSTELLE", 97, "Hypno", 48, "rescued_lostelle",
                   ["Deep in the misty forest, a Hypno is swinging its pendulum at a crying girl!"],
                   ["The Hypno runs off into the mist.", "Lostelle: You saved me! I want to go home to Two Island!"],
                   "heard_lostelle")])
