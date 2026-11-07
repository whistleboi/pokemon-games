"""Overworld Pokemon for the walked maps (Jordan, 11-06): the "Following Pokemon" sheets of the fan game
Pokemon Everlasting X and Devastating Y (Beta v1.5, Graphics/Characters/Followers and Followers shiny),
4 x 4 walking frames each (rows down, left, right, up), Gen 1-8 -> assets/dungeon/followers/<dex>.png
and assets/dungeon/followers/shiny/<dex>.png. Paldea's (Gen 9) aren't in it: those keep their party icon.

    python dev/builders/import_followers.py [<Everlasting X folder>]
"""
import json
import os
import re
import shutil
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser(
    "~/Downloads/(Beta v1.5) Pokemon Everlasting X Devastating Y/(Beta v1.5) Pokemon Everlasting X Devastating Y")
OUT = os.path.join("assets", "dungeon", "followers")
SPECIAL = {29: "NIDORANfE", 32: "NIDORANmA"}


def norm(name):
    return re.sub(r"[^A-Z0-9]", "", name.upper())


def main():
    names = json.load(open(os.path.join("assets", "pokemon_names.json"), encoding="utf-8"))
    done = 0
    for sub, out in (("Followers", OUT), ("Followers shiny", os.path.join(OUT, "shiny"))):
        folder = os.path.join(SRC, "Graphics", "Characters", sub)
        have = {f[:-4] for f in os.listdir(folder) if f.endswith(".png")}
        os.makedirs(out, exist_ok=True)
        for dex, name in names.items():
            dex = int(dex)
            if dex > 1025:
                continue
            for key in (SPECIAL.get(dex), norm(name), norm(name.split("-")[0])):
                if key and key in have:
                    shutil.copyfile(os.path.join(folder, key + ".png"), os.path.join(out, f"{dex}.png"))
                    done += 1
                    break
    print(done, "sheets")


if __name__ == "__main__":
    main()
