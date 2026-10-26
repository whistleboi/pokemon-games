"""The Black Fog (from The Electric Tale of Pikachu manga): an ancient, giant Haunter that can't be
caught. It haunts one place in every region (and two sub-regions) as an optional boss.
Run from the game folder: python dev/builders/build_black_fog.py dev/builders   (safe to re-run)"""
import json
import sys

sys.path.insert(0, sys.argv[1])
from textjson import TextJSON  # noqa: E402

BLACK_FOG = 10501  # assets/sprites/pokemon/10501.png
HAUNTS = {  # file -> haunted areas
    "pokemon_area_data.json": ["KANTO_POKEMON_TOWER"],
    "johto_area_data.json": ["BURNED_TOWER"],
    "hoenn_area_data.json": ["HOENN_MT_PYRE"],
    "sinnoh_area_data.json": ["OLD_CHATEAU"],
    "unova_area_data.json": ["CELESTIAL_TOWER"],
    "kalos_area_data.json": ["LOST_HOTEL"],
    "alola_area_data.json": ["THRIFTY_MEGAMART"],
    "galar_area_data.json": ["CROWN_OLD_CEMETERY"],
    "paldea_area_data.json": ["DALIZAPA_PASSAGE"],
    "sevii_area_data.json": ["LOST_CAVE"],
    "decolore_area_data.json": ["SPECTRALA_WOODS"],
}
LEVEL_UP = 8  # above the area: a scary, optional fight
area_levels = json.load(open("assets/area_levels.json", encoding="utf-8"))


def option(area_key, area):
    level = int(area.get("level") or area_levels.get(area_key, 20)) + LEVEL_UP
    flag = f"black_fog_banished_{area_key.lower()}"
    return {"text": "THE BLACK FOG", "action": "BOSS", "color": "PURPLE", "flag_condition": f"not {flag}",
            "boss": {"id": BLACK_FOG, "name": "Black Fog", "level": level, "no_catch": True, "victory_flag": flag,
                     "lines": ["The air turns ice-cold. A black fog pours across the floor...",
                               "Two huge eyes open in the dark. A giant Haunter rises: the Black Fog!",
                               "Long ago people worshipped it as a god. It feeds on dreams. Don't let it get yours!"],
                     "won": ["The Black Fog is too proud to ever be caught.",
                             "It Self-Destructs in a burst of black mist... and is gone.",
                             "But a cold whisper lingers: it will rise again in another haunted place."],
                     "rewards": {"balls": 10, "RARE_CANDY": 3}}}


for fname, areas in HAUNTS.items():
    t = TextJSON(f"assets/{fname}")
    sp = t.data()["STORY_PROGRESSION"]
    changed = False
    for key in areas:
        menu = list(sp[key].get("route_menu") or [])
        if any(o.get("text") == "THE BLACK FOG" for o in menu):
            continue
        at = next((i for i, o in enumerate(menu) if o.get("action") == "EXIT"), len(menu))
        menu.insert(at, option(key, sp[key]))
        t.set(key, "route_menu", menu)
        changed = True
    if changed:
        t.save()
        print("added:", fname, areas)

# The form: Haunter's stats and moves, its own name, art and types.
K = TextJSON("assets/pokemon_area_data.json")
if str(BLACK_FOG) not in K.data().get("FORM_MAP", {}):
    old = '    "3025": { "id": 201, "form": "normal", "name": "Nown", "types": ["PSYCHIC"] }\n'
    assert K.s.count(old) == 1, "FORM_MAP layout changed"
    K.s = K.s.replace(old, old.rstrip("\n") + ',\n    "' + str(BLACK_FOG) + '": { "id": 93, "form": "black_fog",'
                      ' "name": "Black Fog", "types": ["GHOST", "POISON"] }\n')
    K.save()
    print("FORM_MAP: Black Fog added")
print("ok")
