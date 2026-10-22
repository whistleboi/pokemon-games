"""The Sinjoh Ruins (reached from Johto's Ruins of Alph with Arceus and every Unown): the Border Cabin,
the Ruined Pathways and the Mystri Stage. Phione lives here.
Run from the game folder: python build_sinjoh.py <scratchpad>"""
import re
import sys

sys.path.insert(0, sys.argv[1])
from sublib import Sub, event, trainer, battle, boss  # noqa: E402
from textjson import TextJSON  # noqa: E402

S = Sub("JOHTO", "SINJOH", "SINJOH", {})
CHOSEN = ["sinjoh_dialga", "sinjoh_palkia", "sinjoh_giratina"]

# ---- 1. The Border Cabin: the arrival outpost.
S.town("SINJOH_CABIN", "Sinjoh Border Cabin", 65, [
    event("The Snowbound Cabin", {
        "lines": ["A quiet guide sits by the fire with an Abra on her lap.",
                  "Guide: Few find their way here. You can't fly in or out of these ruins.",
                  "When you want to go home, my Abra will Teleport you back to the Ruins of Alph."]}),
    event("Talk to Cynthia", {
        "lines": ["Cynthia: So the Unown brought you too. Look at these ruins...",
                  "Johto carvings and Sinnoh carvings, side by side. The two regions' ancient people met here.",
                  "Something powerful is stirring at the mountain's heart, the Mystri Stage.",
                  "Be careful on the pathways. The Pokemon there are restless."],
        "flag": "met_sinjoh_cynthia",
        "done": ["Cynthia: The Mystri Stage is at the end of the Ruined Pathways."]},
        flag_condition="not sinjoh_rite_done"),
    event("Battle Cynthia", {
        "requires": [{"any": [f"{c}" for c in CHOSEN]}],
        "lines": ["Cynthia: You met one of the gods of creation... Let's see what that does to a trainer!"],
        "battle": battle("Cynthia", "CHAMPION", "cynthia.png", [442, 407, 445, 350, 448, 468],
                         [70, 70, 72, 70, 71, 70], ["Cynthia: Incredible. The ruins chose well."], balls=20),
        "flag": "defeated_sinjoh_cynthia", "done": ["Cynthia: Any time you want a rematch, I'm here."]},
        condition={"any": CHOSEN}, flag_condition="not defeated_sinjoh_cynthia"),
], local=[("Sinjoh Snowfields", "SINJOH_SNOWFIELDS", None),
          ("Ruined Pathways", "SINJOH_PATHWAYS", "met_sinjoh_cynthia"),
          ("Mystri Stage", "MYSTRI_STAGE", "phione_freed")],
    extra_travel=[{"text": "Abra's Teleport (Ruins of Alph)", "target_area": "RUINS_OF_ALPH",
                   "message": "The guide's Abra glows... and you're back in the Ruins of Alph."}],
    shop=False, ships=False)
S.areas["SINJOH_CABIN"]["explore_options"][0]["text"] = "Hiker's Rest"

S.wild("SINJOH_SNOWFIELDS", "Sinjoh Snowfields", 65, "snow",
       {361: 18, 362: 6, 459: 18, 460: 6, 225: 15, 478: 3, 220: 12, 215: 12, 124: 10},
       [("Border Cabin", "SINJOH_CABIN")],
       [trainer("Hiker Bram", "HIKER", "hiker.png", [460, 362, 473]),
        trainer("Researcher Lin", "SCIENTIST", "scientist.png", [436, 437, 344]),
        trainer("Mystic Sela", "MYSTIC", "sage.png", [478, 429, 203])])

# ---- 2. The Ruined Pathways: restless Pokemon and a Phione frozen in a spring.
S.wild("SINJOH_PATHWAYS", "Ruined Pathways", 67, "snow",
       {200: 14, 198: 14, 215: 14, 220: 12, 221: 10, 429: 3, 430: 3, 461: 3, 473: 2, 201: 10, 436: 10, 437: 5},
       [("Border Cabin", "SINJOH_CABIN")],
       [trainer("Ruin Maniac Oz", "RUIN_MANIAC", "ruinmaniac.png", [437, 344, 476]),
        trainer("Psychic Rhea", "PSYCHIC", "psychic.png", [282, 475, 196]),
        trainer("Black Belt Goro", "BLACK_BELT", "blackbelt.png", [448, 297, 68])],
       extra=[event("STRANGE ROARS", {
                  "lines": ["A wild Piloswine stops in the snow and lets out a huge roar.",
                            "Every Pokemon on the path is shaking, staring toward the mountain's heart..."]}),
              event("THE FROZEN SPRING", {
                  "requires": ["met_sinjoh_cynthia"],
                  "puzzle": "carvings",
                  "lines": ["Inside the melted spring is a small blue Pokemon: a Phione!",
                            "It must have been swept through the rift all the way from Sinnoh's Sea Temple.",
                            "It hums a soft song, and the restless Pokemon around you calm down.",
                            "Phione floats after you. It wants to go to the Mystri Stage too."],
                  "puzzle_fail": ["The ice seals hold. The Phione inside taps on the ice, waiting."],
                  "flag": "phione_freed"},
                  flag_condition="not phione_freed")])

# ---- 3. The Mystri Stage: the rite of creation.
S.wild("MYSTRI_STAGE", "Mystri Stage", 70, "indoor", {},
       [("Border Cabin", "SINJOH_CABIN")],
       extra=[event("STEP ONTO THE STAGE", {
                  "requires": ["phione_freed", "party_has:493"],
                  "fail": ["The triangular stage is silent. It seems to wait for a legendary partner... Arceus."],
                  "lines": ["You and Arceus step onto the triangular stage. Unown swirl around you!",
                            "The rift tears open above the altar. Three shapes flicker inside: time, space and antimatter.",
                            "Phione sings. Its song steadies the rift long enough for you to call ONE of them."],
                  "flag": "sinjoh_rite_ready"},
                  flag_condition="not sinjoh_rite_ready"),
              boss("CALL DIALGA (TIME)", 483, "Dialga", 70, "sinjoh_dialga",
                   ["Dialga steps out of the rift, holding the Adamant Orb!"],
                   ["Dialga leaves the Adamant Orb on the altar and returns to its time."],
                   ["sinjoh_rite_ready", "not:sinjoh_palkia", "not:sinjoh_giratina"],
                   rewards={"ADAMANT_ORB": 1}, no_catch=False, color="BLUE"),
              boss("CALL PALKIA (SPACE)", 484, "Palkia", 70, "sinjoh_palkia",
                   ["Palkia bursts out of the rift, holding the Lustrous Orb!"],
                   ["Palkia leaves the Lustrous Orb on the altar and returns to its space."],
                   ["sinjoh_rite_ready", "not:sinjoh_dialga", "not:sinjoh_giratina"],
                   rewards={"LUSTROUS_ORB": 1}, no_catch=False, color="PURPLE"),
              boss("CALL GIRATINA (ANTIMATTER)", 487, "Giratina", 70, "sinjoh_giratina",
                   ["Giratina rises from the rift's shadow, holding the Griseous Orb!"],
                   ["Giratina leaves the Griseous Orb on the altar and sinks back into the shadows."],
                   ["sinjoh_rite_ready", "not:sinjoh_dialga", "not:sinjoh_palkia"],
                   rewards={"GRISEOUS_ORB": 1}, no_catch=False, color="RED"),
              {"text": "PHIONE'S FAREWELL", "action": "BOSS", "color": "GOLD",
               "condition": [{"any": CHOSEN}, "boss_not_defeated"]}],
       area_boss={"id": 489, "name": "Phione", "victory_flag": "sinjoh_phione_caught"})

S.mission("sinjoh_m1", "SIDE", "The Sinjoh Ruins",
          "With Arceus and every Unown, follow the Unown out of the Ruins of Alph. Cynthia is waiting.",
          {"flag_not": "visited_SINJOH_CABIN", "visited": "RUINS_OF_ALPH"}, "A new place")
S.mission("sinjoh_m2", "SIDE", "The Frozen Spring",
          "Something is trapped in a frozen spring on the Ruined Pathways.",
          {"flag": "met_sinjoh_cynthia", "flag_not": "phione_freed"}, "Phione")
S.mission("sinjoh_m3", "SIDE", "The Rite of Creation",
          "Bring Arceus and Phione to the Mystri Stage and call one of the three gods of creation.",
          {"flag": "phione_freed", "flag_not": "sinjoh_phione_caught"}, "Dialga, Palkia or Giratina, and Phione")
S.save("assets/sinjoh_area_data.json")

# ---- Ruins of Alph: the way in. Once you've been, you can always go back.
J = TextJSON("assets/johto_area_data.json")
if not any("Sinjoh" in o.get("text", "") for o in J.data()["STORY_PROGRESSION"]["RUINS_OF_ALPH"]["travel_options"]):
    J.append("RUINS_OF_ALPH", "travel_options", {
        "text": "Follow the Unown (Sinjoh Ruins)", "target_area": "SINJOH_CABIN",
        "condition": {"any": ["visited_SINJOH_CABIN", ["party_has:493", "all_unown_registered"]]},
        "message": "Every Unown in the ruins swirls around Arceus... The world goes white. You're somewhere cold."})
    J.save()

# ---- Phione now lives only at the Sinjoh Ruins (it was a 5% wild Pokemon on Sinnoh's Route 223).
p = "assets/sinnoh_area_data.json"
s = open(p, encoding="utf-8").read()
s2 = re.sub(r'(\"SINNOH_ROUTE_223_PERCENTAGES\": \{[^}]*?), \"489\": 5', r"\1", s)
if s2 != s:
    open(p, "w", encoding="utf-8", newline="").write(s2)

K = TextJSON("assets/pokemon_area_data.json")
new = ["ADAMANT_ORB", "LUSTROUS_ORB", "GRISEOUS_ORB"]
missing = [k for k in new if k not in K.data()["GAME_CONFIG"]["KEY_ITEMS"]]
if missing:
    K.s = K.s.replace('    "KEY_ITEMS": [\n', '    "KEY_ITEMS": [\n      ' + ", ".join(f'"{k}"' for k in missing) + ",\n", 1)
    K.save()
g = open("src/core/game.py", encoding="utf-8").read()
if "sinjoh_area_data.json" not in g:
    g = g.replace('            "decolore": "decolore_area_data.json",\n',
                  '            "decolore": "decolore_area_data.json",\n            "sinjoh": "sinjoh_area_data.json",\n')
    open("src/core/game.py", "w", encoding="utf-8", newline="").write(g)
print("ok")
