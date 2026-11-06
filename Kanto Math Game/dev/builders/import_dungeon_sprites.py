"""Overworld sprites for the route dungeons (Jordan, 11-05), from Pokemon Journeys V18's Graphics/Characters:
the trainers' walking sheets (trchar###, numbered by its PBS trainertypes.txt: 38 Youngster, 24 a Rocket
grunt...), the townsfolk (NPC ##), the overworld Pokemon (Pokemon ##: a column a Pokemon, a row a way it
faces) and objects (a Poke Ball, a boulder).

Copied to assets/dungeon/characters/; which sheet is whose is in assets/dungeon_sprites.json (kept by hand:
trainers by their battle sprite's name, the story figures by area and button, Pokemon by species).
    python dev/builders/import_dungeon_sprites.py ["<Pokemon Journeys V18 folder>"]
"""
import os
import shutil
import sys

JOURNEYS = os.path.join("..", "..", "Pokemon Journeys V18")
OUT = os.path.join("assets", "dungeon", "characters")
WANT = ("trchar", "NPC ", "Pokemon ", "Object ")  # (the players: trchar000_1 Red, 001 Leaf)


def main(argv):
    root = argv[0] if argv and os.path.isdir(argv[0]) else JOURNEYS
    src = os.path.join(root, "Graphics", "Characters")
    if not os.path.isdir(src):
        sys.exit(f"Pokemon Journeys V18 not found at {root}")
    os.makedirs(OUT, exist_ok=True)
    n = 0
    for f in sorted(os.listdir(src)):
        if f.startswith(WANT) and f.lower().endswith(".png"):
            shutil.copyfile(os.path.join(src, f), os.path.join(OUT, f))
            n += 1
    print(f"{n} sheets -> {OUT}")


if __name__ == "__main__":
    main(sys.argv[1:])
