"""Maps made with the map maker (its own project, Pokemath Map Maker, beside this one: its Export puts them here): one file each in made/<KEY>.json, {"key", "map"}.
The map maker's own notes ("_maker": height levels, the reference picture, building names) stay out of the game's file.
A made map with the same key as a region's own map replaces it (this file is built last)."""
import json
import os

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "made")
MAPS = {}
for name in sorted(os.listdir(HERE)) if os.path.isdir(HERE) else []:
    if name.endswith(".json"):
        with open(os.path.join(HERE, name), encoding="utf-8") as f:
            d = json.load(f)
        MAPS[d["key"]] = {k: v for k, v in d["map"].items() if k != "_maker"}
