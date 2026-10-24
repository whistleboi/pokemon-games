"""Download every Kalos location-area's X/Y encounters from PokeAPI into kalos_xy_encounters.json:
{location: {pokemon_id: {"methods": [...], "chance": max_chance}}}."""
import json
import os
import re
import sys
import time
import urllib.request

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "kalos_xy_encounters.json")


def get(url):
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "kanto-math-game-builder"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            time.sleep(1 + attempt)
            err = e
    raise err


region = get("https://pokeapi.co/api/v2/region/kalos/")
result = {}
for loc in region["locations"]:
    ld = get(loc["url"])
    entry = {}
    for area in ld.get("areas", []):
        ad = get(area["url"])
        for pe in ad.get("pokemon_encounters", []):
            pid = int(re.search(r"/(\d+)/$", pe["pokemon"]["url"]).group(1))
            for vd in pe.get("version_details", []):
                if vd["version"]["name"] not in ("x", "y"):
                    continue
                e = entry.setdefault(str(pid), {"methods": [], "chance": 0})
                e["chance"] = max(e["chance"], vd.get("max_chance", 0))
                for det in vd.get("encounter_details", []):
                    m = det["method"]["name"]
                    if m not in e["methods"]:
                        e["methods"].append(m)
    if entry:
        result[loc["name"]] = entry
    print(loc["name"], len(entry), flush=True)
json.dump(result, open(OUT, "w"), indent=1)
print("locations with encounters:", len(result))
