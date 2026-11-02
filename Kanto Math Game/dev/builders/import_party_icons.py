"""Pokemon party icons for the Gym minigames (Jordan, 11-01): Pokemon Journeys' icon###.png, two
64 x 64 frames side by side (the games' bobbing party icon), #1 to #890. Copied as they are to
assets/sprites/icons/<dex number>.png (forms left out).
    python dev/builders/import_party_icons.py ["<Pokemon Journeys V18 folder>"]
"""
import os
import re
import shutil
import sys

JOURNEYS = os.path.join("..", "..", "Pokemon Journeys V18")
OUT = os.path.join("assets", "sprites", "icons")


def main(root):
    src = os.path.join(root, "Graphics", "Icons")
    if not os.path.isdir(src):
        sys.exit(f"Pokemon Journeys icons not found at {src}")
    os.makedirs(OUT, exist_ok=True)
    n = 0
    for f in os.listdir(src):
        m = re.fullmatch(r"icon(\d{3,4})\.png", f)
        if m and int(m.group(1)) > 0:
            shutil.copyfile(os.path.join(src, f), os.path.join(OUT, f"{int(m.group(1))}.png"))
            n += 1
    print(f"{n} icons -> {OUT}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else JOURNEYS)
