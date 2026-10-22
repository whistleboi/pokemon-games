"""Build assets/orange_area_data.json and hook the Orange Islands into Kanto and Johto.
Run from the game folder: python build_orange.py <scratchpad>"""
import json
import sys

sys.path.insert(0, sys.argv[1])
from orange_lib import AREAS, POOLS  # noqa: E402
import orange_gyms  # noqa: E402,F401
from orange_special import PINKAN, CRYSTAL_ONIX  # noqa: E402
from textjson import TextJSON  # noqa: E402

names = json.load(open("assets/pokemon_names.json", encoding="utf-8"))
form_map = {str(sid): {"id": base, "form": "pinkan", "name": f"Pinkan {names[str(base)]}"}
            for sid, base in PINKAN.items()}
form_map[str(CRYSTAL_ONIX)] = {"id": 95, "form": "crystal", "name": "Crystal Onix", "types": ["ROCK", "ICE"]}

missions = [
    {"id": "orange_m1", "type": "MAIN", "title": "Welcome to the Orange Islands",
     "description": "Meet Professor Ivy on Valencia Island, then sail to Mikan Island for your first Orange Crew badge.",
     "condition": {"required_region": "ORANGE", "region_badges_less": 1}, "reward": "GS Ball"},
    {"id": "orange_m2", "type": "MAIN", "title": "The Orange Crew",
     "description": "Win the Coral-Eye, Sea Ruby, Spike Shell and Jade Star Badges from Cissy, Danny, Rudy and Luana.",
     "condition": {"required_region": "ORANGE", "region_badges_min": 1, "region_badges_less": 4},
     "reward": "Four Orange Crew badges"},
    {"id": "orange_m3", "type": "MAIN", "title": "The Orange League",
     "description": "Beat Drake's full six-Pokemon team at Pummelo Stadium to win the Winner's Trophy.",
     "condition": {"required_region": "ORANGE", "region_badges_min": 4, "flag_not": "beat_orange_champion"},
     "reward": "Winner's Trophy"},
    {"id": "orange_s1", "type": "SIDE", "title": "Pink Pokemon",
     "description": "Stop Team Rocket on Pinkan Island and earn Officer Jenny's permit to catch Pinkan Pokemon.",
     "condition": {"required_region": "ORANGE", "visited": "PINKAN_ISLAND", "flag_not": "got_pinkan_permit"},
     "reward": "Pinkan Permit"},
    {"id": "orange_s2", "type": "SIDE", "title": "The Crystal Onix",
     "description": "Mateo on Sunburst Island says a glass-clear Onix lives in the Crystal Cave.",
     "condition": {"required_region": "ORANGE", "flag": "met_mateo", "flag_not": "got_mateo_gift"},
     "reward": "Crystal Onix + Amulet Coin"},
    {"id": "orange_s3", "type": "SIDE", "title": "The Chosen One",
     "description": "Gather the treasures of Fire, Ice and Lightning Islands and bring them to the Shamouti Shrine.",
     "condition": {"required_region": "ORANGE", "flag": "heard_shamouti_legend", "flag_not": "shamouti_lugia_defeated"},
     "reward": "Lugia"},
]

data = {
    "REGION_START": {"ORANGE": {
        "order": 2.5, "travel_only": True, "storage_region": "KANTO", "subtitle": "ANIME / ORANGE ISLANDS",
        "start_area": "VALENCIA_ISLAND", "dex_range": [0, -1], "dex_extra": [],
        "badge_images": ["orange_1", "orange_2", "orange_3", "orange_4", "orange_5"]}},
    "FORM_MAP": form_map,
    "JOURNAL_MISSIONS": missions,
    "STORY_PROGRESSION": AREAS,
}
data.update(POOLS)
with open("assets/orange_area_data.json", "w", encoding="utf-8", newline="\n") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
print("areas:", len(AREAS), "pools:", len(POOLS) // 2, "forms:", len(form_map))

# ---- Kanto and Johto: the ferry to the Orange Islands, after both titles.
BOTH = ["beat_champion", "beat_johto_champion"]
INFO = {"text": "Orange Islands Ferry", "action": "EVENT", "color": "GOLD",
        "condition": {"any": ["not:beat_champion", "not:beat_johto_champion"]},
        "event": {"lines": ["Sailor: This ferry sails south to the Orange Islands.",
                            "It only takes the Champion of both Kanto and Johto. Come back when you've won both!"]}}
for path, area in (("assets/pokemon_area_data.json", "VERMILLION_CITY"), ("assets/johto_area_data.json", "OLIVINE_CITY")):
    t = TextJSON(path)
    sp = t.data()["STORY_PROGRESSION"][area]
    if not any("Orange Islands" in o.get("text", "") for o in sp.get("travel_options", [])):
        t.append(area, "travel_options", {
            "text": "Ship to the Orange Islands", "target_area": "VALENCIA_ISLAND", "condition": BOTH,
            "message": "The ferry sails south for days over warm seas... Land ho! It's Valencia Island!"})
        t.append(area, "explore_options", INFO)
    if path.endswith("pokemon_area_data.json"):
        new = ["PINKAN_PERMIT", "FIRE_TREASURE", "ICE_TREASURE", "LIGHTNING_TREASURE"]
        keys = t.data()["GAME_CONFIG"]["KEY_ITEMS"]
        missing = [k for k in new if k not in keys]
        if missing:
            t.s = t.s.replace('    "KEY_ITEMS": [\n', '    "KEY_ITEMS": [\n      '
                              + ", ".join(f'"{k}"' for k in missing) + ",\n", 1)
    t.save()
print("ok")
