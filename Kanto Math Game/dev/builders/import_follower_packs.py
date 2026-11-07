"""Following-Pokemon packs Jordan added (11-06), from ~/Downloads (Essentials naming: NAME.png, NAME_<form>.png,
NAME_gmax.png; shiny ones in their own folders): Mega and Primal forms, Legends: Z-A's Megas, Gigantamax,
and the Teal Mask / Indigo Disk Pokemon. Each goes to assets/dungeon/followers/<dex>[_<form>].png (and shiny/),
replacing what was there (run after import_followers.py, import_paldea_followers.py, import_extra_followers.py).
Forms by the game's own names: mega, mega_x / mega_y (Charizard, Mewtwo), primal (Groudon, Kyogre), gmax,
and Ogerpon's water_mask / fire_mask / rock_mask.

    python dev/builders/import_follower_packs.py [<Downloads folder>]
"""
import glob
import json
import os
import re
import shutil
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Downloads")
OUT = os.path.join("assets", "dungeon", "followers")
TYPOS = {"BANNETTE": "BANETTE", "CORVINIGHT": "CORVIKNIGHT", "HOUDOOM": "HOUNDOOM",
         "PIDGEOTTO": "PIDGEOT"}  # (the pack's own misspellings: Pidgeotto has no Mega, Mega Pidgeot is filed so)
SKIP = {"LUCARIO_2", "RAICHU_3", "RAICHU_4", "PECHARUNT_1", "URSHIFU_2_gmax"}
TWO_MEGAS = {"CHARIZARD", "MEWTWO"}
PRIMAL = {"GROUDON", "KYOGRE"}
OGERPON = {"1": "water_mask", "2": "fire_mask", "3": "rock_mask"}  # (4-7: its Terastal looks, not used)
BIG_FIRST = ("Megas 512x", "Shiny Megas 512x")  # (the huge ones: their bigger sheets win)


def norm(name):
    return re.sub(r"[^A-Z0-9]", "", name.upper())


def dex_of(names, species):
    species = TYPOS.get(species, species)
    hit = [int(d) for d, n in names.items() if int(d) <= 1025 and norm(n) == norm(species)]
    if hit:
        return hit[0]
    for dex, n in names.items():
        if int(dex) <= 1025 and (norm(n) == norm(species) or norm(n.split("-")[0]) == norm(species)):
            return int(dex)
    return None


def target(names, stem):
    """(dex, form or None) for a file's name, or None to leave it out."""
    if stem in SKIP:
        return None
    if stem.endswith("_gmax"):
        base = stem[:-5].split("_")[0]
        dex = dex_of(names, base)
        return (dex, "gmax") if dex else None
    parts = stem.split("_")
    base, form = parts[0], parts[1] if len(parts) > 1 else None
    dex = dex_of(names, base)
    if not dex:
        return None
    if form is None:
        return dex, None
    if base in PRIMAL:
        return dex, "primal"
    if base == "OGERPON":
        return (dex, OGERPON[form]) if form in OGERPON else None
    if base == "URSALUNA":
        return dex, "bloodmoon"
    if base in TWO_MEGAS:
        return dex, {"1": "mega_x", "2": "mega_y"}.get(form)
    return dex, "mega" if form == "1" else None


def main():
    names = json.load(open(os.path.join("assets", "pokemon_names.json"), encoding="utf-8"))
    files = sorted(glob.glob(os.path.join(SRC, "*", "**", "*.png"), recursive=True))
    files = [f for f in files if any(k in f for k in ("MEGA sprites", "ZA Megas", "GMAX Sprites", "Indigo Disk"))]
    # the 512x sheets of a Pokemon win over its 256x one: copied last
    files.sort(key=lambda f: any(b in f for b in BIG_FIRST))
    done, left = 0, []
    for f in files:
        stem = os.path.splitext(os.path.basename(f))[0]
        hit = target(names, stem)
        if not hit or hit[0] is None or (len(hit) > 1 and hit[1] is None and "_" in stem):
            left.append(stem)
            continue
        dex, form = hit
        shiny = "shiny" in f.lower()
        name = f"{dex}_{form}.png" if form else f"{dex}.png"
        out = os.path.join(OUT, "shiny" if shiny else "", name)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        shutil.copyfile(f, out)
        done += 1
    print(done, "sheets; left out:", sorted(set(left)))


if __name__ == "__main__":
    main()
