"""The Decolore Islands (Unova, after the Unova title): five islands, a ferry with trainers, and
Team Plasma's Genesect. Run from the game folder: python build_decolore.py <scratchpad>"""
import sys

sys.path.insert(0, sys.argv[1])
from sublib import Sub, event, trainer, battle  # noqa: E402
from textjson import TextJSON  # noqa: E402

S = Sub("UNOVA", "DECOLORE", "DECOLORE", {})
FERRY = ("Board the Ferry", "DECOLORE_FERRY", None)


def island(key, name, level, explore, local):
    S.town(key, name, level, explore, local=[FERRY] + local, ships=False)


# ---- The ferry: trainers on deck, no wild Pokemon. Each island opens with the story.
S.wild("DECOLORE_FERRY", "Decolore Ferry", 57, "ocean", {},
       [("Honey Island", "HONEY_ISLAND"),
        ("Scalchop Island", "SCALCHOP_ISLAND", "got_burn_drive"),
        ("Grand Spectrala Island", "GRAND_SPECTRALA_ISLAND", "got_douse_drive"),
        ("Torom Island", "TOROM_ISLAND", "got_chill_drive"),
        ("Paladin Island", "PALADIN_ISLAND", "decolore_lab_cleared"),
        ("Castelia City", "CASTELIA_CITY")],
       [trainer("Sailor Moby", "SAILOR", "sailor.png", [130, 91, 594]),
        trainer("Gentleman Percy", "GENTLEMAN", "gentleman.png", [508, 128, 59]),
        trainer("Rich Boy Lance", "RICH_BOY", "richboy.png", [534, 521, 587], balls=8),
        trainer("Tourist Mae", "TOURIST", "pokefan_f.png", [573, 25, 133]),
        trainer("Swimmer Coral", "SWIMMER", "swimmer_f.png", [321, 593, 171])],
       extra=[event("WATCH THE WAVES", {
           "lines": ["Wingull and Ducklett glide alongside the ferry.",
                     "The captain says the islands' colors change with the seasons. That's why they're called Decolore!"]})])

# ---- 1. Honey Island: scorched hives and the Burn Drive.
island("HONEY_ISLAND", "Honey Island", 56, [
    event("The Beekeepers' Hives", {
        "lines": ["Beekeeper: Something burned our hives last night! A purple, metal bug with a cannon on its back!",
                  "It flew off toward the other islands. Team Plasma's boats were seen right after..."],
        "flag": "decolore_heard_genesect",
        "done": ["Beekeeper: The Combee are rebuilding. Thank you for looking into it!"]}),
    event("Search the Scorched Hives", {
        "requires": ["decolore_heard_genesect"],
        "lines": ["In the ashes you find a red cartridge, still warm. It's labeled BURN DRIVE.",
                  "A Plasma logo is stamped on the back... Maybe Scalchop Island has more clues."],
        "gift_item": {"BURN_DRIVE": 1}, "flag": "got_burn_drive"},
        condition="decolore_heard_genesect", flag_condition="not got_burn_drive"),
    event("Taste the Honey", {
        "lines": ["Beekeeper: Try some! Our Combee make the sweetest honey in Unova.",
                  "Here, take a jar for the road. Wild Pokemon love the smell!"],
        "gift_item": {"balls": 5, "RARE_CANDY": 1}, "flag": "tasted_decolore_honey",
        "done": ["Beekeeper: Sweet, isn't it?"]}),
], [("Honey Meadow", "HONEY_MEADOW", None)])
S.wild("HONEY_MEADOW", "Honey Meadow", 56, "grass",
       {415: 26, 416: 7, 15: 8, 12: 8, 267: 6, 420: 10, 546: 10, 548: 16, 541: 9}  # Gen 5 or earlier only (Jordan),
       [("Honey Island", "HONEY_ISLAND")],
       [trainer("Beekeeper Hal", "BEEKEEPER", "bug_catcher.png", [415, 416, 15]),
        trainer("Bug Catcher Wes", "BUG_CATCHER", "bug_catcher.png", [542, 545, 637]),
        trainer("Picnicker Lily", "PICNICKER", "picnicker.png", [549, 547, 548])])

# ---- 2. Scalchop Island: Oshawott's island, Team Plasma at the shrine, the Douse Drive.
island("SCALCHOP_ISLAND", "Scalchop Island", 58, [
    event("Scalchop Festival", {
        "lines": ["Every Oshawott on the island is polishing its scalchop for the festival!",
                  "The best scalchop wins. Yours is judged... the shiniest one there!"],
        "gift_item": {"balls": 5}, "flag": "scalchop_festival",
        "done": ["The Oshawott are still showing off their scalchops."]}),
    event("Plasma at the Shrine", {
        "requires": ["got_burn_drive"],
        "lines": ["Plasma Grunts are loading crates onto a boat at the island shrine!",
                  "Grunt: The professor needs these Drives for his Genesect! Get lost!"],
        "battle": battle("Plasma Grunts", "PLASMA_GRUNT", "plasma_grunt.png", [510, 552, 625, 530],
                         [56, 57, 57, 58], ["Grunt: The professor won't like this... Retreat!"]),
        "flag": "decolore_shrine_plasma"},
        flag_condition="not decolore_shrine_plasma"),
    event("Search the Crates", {
        "requires": ["decolore_shrine_plasma"],
        "lines": ["One crate was left behind. Inside is a blue cartridge: the DOUSE DRIVE.",
                  "The shipping label says: Grand Spectrala Island."],
        "gift_item": {"DOUSE_DRIVE": 1}, "flag": "got_douse_drive"},
        condition="decolore_shrine_plasma", flag_condition="not got_douse_drive"),
], [("Scalchop Coast", "SCALCHOP_COAST", None)])
S.wild("SCALCHOP_COAST", "Scalchop Coast", 58, "ocean",
       {501: 6, 502: 3, 98: 12, 99: 6, 320: 12, 321: 3, 550: 12, 594: 8, 592: 10, 72: 10, 222: 8, 535: 10},
       [("Scalchop Island", "SCALCHOP_ISLAND")],
       [trainer("Fisherman Ray", "FISHERMAN", "fisherman.png", [550, 99, 130]),
        trainer("Swimmer Nell", "SWIMMER", "swimmer_f.png", [594, 593, 321]),
        trainer("Black Belt Taro", "BLACK_BELT", "blackbelt.png", [538, 539, 534])])

# ---- 3. Grand Spectrala Island: Zoroark's illusions and the Chill Drive.
island("GRAND_SPECTRALA_ISLAND", "Grand Spectrala Island", 60, [
    event("The Illusion Woods", {
        "requires": ["got_douse_drive"],
        "fail": ["Mist hangs over the woods. Something seems to be playing tricks on visitors..."],
        "puzzle": "illusion",
        "lines": ["Behind the last illusion is a hidden Plasma camp, already abandoned.",
                  "A Zoroark was guarding a white cartridge: the CHILL DRIVE. It lets you take it.",
                  "A map on the table shows a laboratory on Torom Island..."],
        "puzzle_fail": ["The woods fold back on themselves. You're back where you started."],
        "gift_item": {"CHILL_DRIVE": 1}, "flag": "got_chill_drive"},
        flag_condition="not got_chill_drive"),
    event("Ghost Stories", {
        "lines": ["Old Man: On foggy nights, the ghosts of Spectrala dance in the old mansion.",
                  "Don't worry. They only play tricks. Mostly."]}),
], [("Spectrala Woods", "SPECTRALA_WOODS", None)])
S.wild("SPECTRALA_WOODS", "Spectrala Woods", 60, "forest",
       {570: 10, 571: 4, 200: 10, 429: 3, 92: 10, 93: 6, 94: 2, 607: 10, 608: 4, 562: 10, 574: 8, 517: 10, 518: 3},
       [("Grand Spectrala Island", "GRAND_SPECTRALA_ISLAND")],
       [trainer("Ranger Elle", "POKEMON_RANGER", "ranger_m.png", [571, 518, 609], balls=6),
        trainer("Hiker Boulder", "HIKER", "hiker.png", [525, 526, 76]),
        trainer("Illusionist Ivo", "ILLUSIONIST", "medium.png", [570, 571, 429])])

# ---- 4. Torom Island: the Plasma lab, the Shock Drive, and Genesect.
island("TOROM_ISLAND", "Torom Island", 62, [
    event("The Plasma Laboratory", {
        "requires": ["got_chill_drive"],
        "fail": ["A locked lab sits on the cliffs, humming with electricity."],
        "lines": ["Plasma Scientist: So you're the one collecting my Drives.",
                  "Genesect is perfection: an ancient Pokemon, rebuilt with a cannon! With all four Drives, it obeys only me.",
                  "Let's see if your Pokemon can match my research!"],
        "battle": battle("Plasma Scientist", "PLASMA_SAGE", "scientist.png", [82, 375, 606, 601, 462],
                         [61, 61, 62, 62, 64], ["Scientist: Fascinating... You've earned the right to see what happens next."],
                         balls=15),
        "flag": "decolore_lab_cleared"},
        flag_condition="not decolore_lab_cleared"),
    event("Shut Down the Lab", {
        "requires": ["decolore_lab_cleared"],
        "lines": ["You flip the lab's main switch. The capsules hiss open!",
                  "Genesect blasts through the roof and flies to the island's peak.",
                  "On the console is the last cartridge: the SHOCK DRIVE.",
                  "Without its Drives, Genesect is just a Pokemon that wants to be free..."],
        "gift_item": {"SHOCK_DRIVE": 1}, "flag": "got_shock_drive"},
        condition="decolore_lab_cleared", flag_condition="not got_shock_drive"),
], [("Torom Peak", "TOROM_PEAK", None)])
S.wild("TOROM_PEAK", "Torom Peak", 62, "mountain",
       {479: 6, 81: 10, 82: 6, 462: 2, 125: 8, 466: 2, 100: 10, 101: 5, 599: 10, 600: 4, 602: 8, 587: 10, 595: 10, 596: 4},
       [("Torom Island", "TOROM_ISLAND")],
       [trainer("Scientist Volta", "SCIENTIST", "scientist.png", [600, 82, 479]),
        trainer("Poke Fan Rita", "POKEFAN", "pokefan_f.png", [587, 25, 523]),
        trainer("Engineer Ohm", "ENGINEER", "engineer.png", [603, 101, 125])],
       extra=[{"text": "CHALLENGE GENESECT", "action": "BOSS", "color": "GOLD",
               "condition": ["got_shock_drive", "boss_not_defeated", "not:P2_LABORATORY_boss_defeated"]}],
       area_boss={"id": 649, "name": "Genesect", "victory_flag": "decolore_genesect_defeated"})

# ---- 5. Paladin Island: the Paladin Tournament of Gym Leaders.
island("PALADIN_ISLAND", "Paladin Island", 64, [
    {"text": "Paladin Tournament", "action": "GYM", "color": "GOLD"},
], [("Paladin Fields", "PALADIN_FIELDS", None)])
S.areas["PALADIN_ISLAND"]["gym"] = {
    "trainers": [
        {"name": "Lenora", "class": "GYM_LEADER", "sprite": "lenora.png", "team": [508, 505, 573], "levels": [62, 62, 63],
         "rewards": {"balls": 5}, "dialogue": {"intro": ["Lenora: Round one! Let's research how strong you are!"]}},
        {"name": "Burgh", "class": "GYM_LEADER", "sprite": "burgh.png", "team": [542, 589, 617], "levels": [63, 63, 64],
         "rewards": {"balls": 5}, "dialogue": {"intro": ["Burgh: Round two! My Bug Pokemon are a work of art!"]}},
        {"name": "Elesa", "class": "GYM_LEADER", "sprite": "elesa.png", "team": [523, 587, 604], "levels": [64, 64, 65],
         "rewards": {"balls": 5}, "dialogue": {"intro": ["Elesa: The semifinal! Let's make it dazzling!"]}}],
    "leader": {"name": "Alder", "class": "TOURNAMENT_CHAMPION", "sprite": "alder.png", "is_boss_battle": True,
               "team": [617, 626, 621, 584, 589, 637], "levels": [66, 66, 66, 66, 66, 68],
               "rewards": {"balls": 25, "RARE_CANDY": 5}, "victory_flag": "paladin_tournament_won",
               "dialogue": {"intro": ["Alder: The final! The Paladin Tournament crowns the strongest trainer in Unova!"],
                            "player_won": ["Alder: Ha ha! What a battle! You're the Paladin Tournament champion!"],
                            "player_lost": ["Alder: Good fight! The tournament runs every day. Come back!"]}},
    "requirements": {"badges": 0}}
S.wild("PALADIN_FIELDS", "Paladin Fields", 64, "grass",
       {25: 8, 515: 10, 511: 10, 513: 10, 133: 6, 506: 10, 509: 10, 519: 10, 427: 8, 39: 8, 573: 5, 587: 5},
       [("Paladin Island", "PALADIN_ISLAND")],
       [trainer("Ace Trainer Rex", "ACE_TRAINER", "acetrainer_m.png", [609, 612, 635], balls=6),
        trainer("Tourist Joy", "TOURIST", "pokefan_m.png", [516, 512, 514])])

S.mission("decolore_m1", "SIDE", "The Decolore Islands",
          "A ferry from Castelia City sails to the Decolore Islands. The beekeepers on Honey Island need help.",
          {"flag": "beat_unova_champion", "flag_not": "got_burn_drive"}, "Burn Drive")
S.mission("decolore_m2", "SIDE", "The Drives",
          "Team Plasma is gathering Drives for a Genesect. Follow the trail from Scalchop to Grand Spectrala to Torom Island.",
          {"flag": "got_burn_drive", "flag_not": "decolore_lab_cleared"}, "Douse and Chill Drives")
S.mission("decolore_m3", "SIDE", "Genesect",
          "Genesect flew to Torom Peak. Without its Drives, it's free... and waiting for a worthy trainer.",
          {"flag": "got_shock_drive", "flag_not": "decolore_genesect_defeated"}, "Genesect")
S.mission("decolore_m4", "SIDE", "The Paladin Tournament",
          "Gym Leaders from all over Unova battle in the Paladin Tournament. Can you beat Alder in the final?",
          {"flag": "decolore_lab_cleared", "flag_not": "paladin_tournament_won"}, "Rare Candy")
S.save("assets/decolore_area_data.json")

# ---- Hook into Unova: a ferry from Castelia; P2 Laboratory's Genesect moves to Torom Island.
U = TextJSON("assets/unova_area_data.json")
sp = U.data()["STORY_PROGRESSION"]
if not any("Decolore" in o.get("text", "") for o in sp["CASTELIA_CITY"]["travel_options"]):
    U.append("CASTELIA_CITY", "travel_options",
             {"text": "Ferry to the Decolore Islands", "target_area": "DECOLORE_FERRY", "condition": "beat_unova_champion",
              "message": "The ferry leaves Castelia's pier for the colorful Decolore Islands."})
if sp["P2_LABORATORY"].get("area_boss"):
    U.drop_where("P2_LABORATORY", "route_menu", lambda o: o.get("action") == "BOSS")
    U.remove("P2_LABORATORY", "area_boss")
    U.append("P2_LABORATORY", "route_menu", {
        "text": "READ THE LAB NOTES", "action": "EVENT", "color": "GOLD",
        "event": {"lines": ["The lab is empty. A note on the desk reads:",
                            "\"Genesect capsules moved to Torom Island, Decolore. Drives to follow.\"",
                            "The Decolore ferry leaves from Castelia City."]}})
U.save()
K = TextJSON("assets/pokemon_area_data.json")
new = ["BURN_DRIVE", "DOUSE_DRIVE", "CHILL_DRIVE", "SHOCK_DRIVE"]
missing = [k for k in new if k not in K.data()["GAME_CONFIG"]["KEY_ITEMS"]]
if missing:
    K.s = K.s.replace('    "KEY_ITEMS": [\n', '    "KEY_ITEMS": [\n      ' + ", ".join(f'"{k}"' for k in missing) + ",\n", 1)
    K.save()
g = open("src/core/game.py", encoding="utf-8").read()
if "decolore_area_data.json" not in g:
    g = g.replace('            "sevii": "sevii_area_data.json",\n',
                  '            "sevii": "sevii_area_data.json",\n            "decolore": "decolore_area_data.json",\n')
    open("src/core/game.py", "w", encoding="utf-8", newline="").write(g)
print("ok")
