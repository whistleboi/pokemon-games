"""Real catch rates (Jordan: Poke Balls work like the games). assets/pokemon_movesets.json had 45 for
every species; this fills in each species' catch rate from PokeAPI's pokemon_species.csv
(github.com/PokeAPI/pokeapi, data/v2/csv). Forms above #1025 keep their species' rate in game
(src/pokemon/catching.py). Run from the game folder:
  python dev/builders/build_capture_rates.py <folder with pokemon_species.csv>
"""
import csv
import json
import os
import sys

with open(os.path.join(sys.argv[1], "pokemon_species.csv"), encoding="utf-8") as f:
    rates = {r["id"]: int(r["capture_rate"]) for r in csv.DictReader(f)}
P = "assets/pokemon_movesets.json"
data = json.load(open(P, encoding="utf-8"))
changed = 0
for pid, entry in data.items():
    if pid in rates and entry.get("capture_rate") != rates[pid]:
        entry["capture_rate"] = rates[pid]
        changed += 1
json.dump(data, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"{changed} catch rates set")
