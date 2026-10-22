"""Build assets/sevii_area_data.json and hook the Sevii Islands into Kanto.
Run from the game folder: python build_sevii.py <scratchpad>"""
import sys

sys.path.insert(0, sys.argv[1])
from sevii_b import S  # noqa: E402
from textjson import TextJSON  # noqa: E402

S.save("assets/sevii_area_data.json")

K = TextJSON("assets/pokemon_area_data.json")
sp = K.data()["STORY_PROGRESSION"]

# Blaine: the Tri-Pass, and a tip about Moltres.
old = '"rewards": { "balls": 10, "RARE_CANDY": 1, "VOLCANO_PASS": 1 }'
if "TRI_PASS" not in K.s:
    assert K.s.count(old) == 1
    K.s = K.s.replace(old, '"rewards": { "balls": 10, "RARE_CANDY": 1, "VOLCANO_PASS": 1, "TRI_PASS": 1 }')
    tip = '"Take this Volcano Badge."'
    assert K.s.count(tip) == 1
    K.s = K.s.replace(tip, tip + ', "Here, take this Tri-Pass too. The Seagallop Ferry in Vermilion goes to the Sevii Islands.",'
                      ' "They say a legendary bird of fire nests at the top of Mt. Ember on One Island!"')

# Vermilion Harbor: the Seagallop Ferries.
if not any("Seagallop" in o.get("text", "") for o in sp["VERMILLION_CITY"]["travel_options"]):
    K.append("VERMILLION_CITY", "travel_options",
             {"text": "Seagallop to One Island", "target_area": "ONE_ISLAND", "condition": "has_item:TRI_PASS",
              "message": "The Seagallop Ferry speeds south to the Sevii Islands. Next stop: One Island!"})
    K.append("VERMILLION_CITY", "travel_options",
             {"text": "Seagallop to Four Island", "target_area": "FOUR_ISLAND", "condition": "has_item:RAINBOW_PASS",
              "message": "The Seagallop Ferry speeds far to the south. Next stop: Four Island!"})

# Mew moves to Faraway Island, Moltres to Mt. Ember.
K.drop_where("MT_MOON", "route_menu", lambda o: "MEW" in o.get("text", "").upper() and "MEWTWO" not in o.get("text", "").upper())
K.remove("MT_MOON", "area_boss")
K.drop_where("CINNABAR_VOLCANO", "route_menu", lambda o: "MOLTRES" in o.get("text", "").upper())
K.remove("CINNABAR_VOLCANO", "area_boss")

new = ["TRI_PASS", "RAINBOW_PASS", "RUBY", "SAPPHIRE", "OLD_SEA_MAP"]
missing = [k for k in new if k not in K.data()["GAME_CONFIG"]["KEY_ITEMS"]]
if missing:
    K.s = K.s.replace('    "KEY_ITEMS": [\n', '    "KEY_ITEMS": [\n      ' + ", ".join(f'"{k}"' for k in missing) + ",\n", 1)
K.save()

g = open("src/core/game.py", encoding="utf-8").read()
if "sevii_area_data.json" not in g:
    g = g.replace('            "orange": "orange_area_data.json",\n',
                  '            "orange": "orange_area_data.json",\n            "sevii": "sevii_area_data.json",\n')
    open("src/core/game.py", "w", encoding="utf-8", newline="").write(g)
print("ok")
