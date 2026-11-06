"""The Pokedex's look and facts (Jordan, 11-05), from Pokemon Journeys V18 (an Essentials v18 game):

- its Pokedex pictures (Graphics/Pictures/Pokedex: the list, the INFO / AREA / FORMS pages, the search
  screens, the type labels, the seen / owned marks) -> assets/pokedex/;
- its footprints (Graphics/Icons/Footprints, #1-649) -> assets/pokedex/footprints/;
- each species' kind ("Seed"), height (m), weight (kg), colour, body shape (1-14, Essentials' order)
  and habitat, from its PBS pokemon.txt (#1-890), else PokeAPI's CSV tables (pokemon_species,
  pokemon_species_names, pokemon, pokemon_colors' ids) -> assets/dex_info.json {"25": {...}}.
Not its Pokedex descriptions (the games' own text): the INFO page says where the Pokemon lives instead.

    python dev/builders/import_pokedex.py [<Pokemon Journeys V18 folder>] [<PokeAPI CSV folder>]
"""
import csv
import json
import os
import shutil
import sys

JOURNEYS = sys.argv[1] if len(sys.argv) > 1 else os.path.join("..", "..", "Pokemon Journeys V18")
CSV = sys.argv[2] if len(sys.argv) > 2 else os.path.join("dev", "builders", "out", "pokeapi_csv")
OUT = os.path.join("assets", "pokedex")
COLORS = {1: "Black", 2: "Blue", 3: "Brown", 4: "Gray", 5: "Green", 6: "Pink", 7: "Purple", 8: "Red",
          9: "White", 10: "Yellow"}  # (PokeAPI's pokemon_colors ids; its shapes are in Essentials' order)
HABITATS = {1: "Cave", 2: "Forest", 3: "Grassland", 4: "Mountain", 5: "Rare", 6: "RoughTerrain", 7: "Sea",
            8: "Urban", 9: "WatersEdge"}


def pbs_species(path):
    out, cur = {}, None
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                cur = out.setdefault(int(line[1:-1]), {})
            elif cur is not None and "=" in line:
                k, v = (s.strip() for s in line.split("=", 1))
                cur[k] = v
    return out


def rows(name):
    with open(os.path.join(CSV, name + ".csv"), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    os.makedirs(os.path.join(OUT, "footprints"), exist_ok=True)
    pics = os.path.join(JOURNEYS, "Graphics", "Pictures", "Pokedex")
    for f in os.listdir(pics):
        shutil.copyfile(os.path.join(pics, f), os.path.join(OUT, f.lower()))
    feet = os.path.join(JOURNEYS, "Graphics", "Icons", "Footprints")
    for f in os.listdir(feet):
        if f.lower().endswith(".png"):
            shutil.copyfile(os.path.join(feet, f), os.path.join(OUT, "footprints", f.lower()))

    info = {}
    for n, d in pbs_species(os.path.join(JOURNEYS, "PBS", "pokemon.txt")).items():
        num = lambda v: float(str(v or 0).replace(",", "."))  # (a few are written "1,6")
        info[str(n)] = {"kind": d.get("Kind", ""), "height": num(d.get("Height")),
                        "weight": num(d.get("Weight")), "color": d.get("Color", ""),
                        "shape": int(d.get("Shape", 0) or 0), "habitat": d.get("Habitat", "")}
    species = {int(r["id"]): r for r in rows("pokemon_species")}
    kinds = {int(r["pokemon_species_id"]): r["genus"] for r in rows("pokemon_species_names")
             if r["local_language_id"] == "9"}
    body = {int(r["species_id"]): r for r in rows("pokemon") if r["is_default"] == "1"}
    for n in range(1, 1026):
        if str(n) in info or n not in species:
            continue
        s, b = species[n], body.get(n, {})
        info[str(n)] = {"kind": kinds.get(n, "").replace(" Pokémon", "").replace(" Pokemon", ""),
                        "height": int(b.get("height") or 0) / 10, "weight": int(b.get("weight") or 0) / 10,
                        "color": COLORS.get(int(s["color_id"] or 0), ""), "shape": int(s["shape_id"] or 0),
                        "habitat": HABITATS.get(int(s["habitat_id"] or 0), "") if s["habitat_id"] else ""}
    with open(os.path.join("assets", "dex_info.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, separators=(",", ":"), ensure_ascii=False)
    print(len(info), "species;", len(os.listdir(OUT)), "pictures")


if __name__ == "__main__":
    main()
