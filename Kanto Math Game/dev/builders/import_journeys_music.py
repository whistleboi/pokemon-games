"""Kanto's soundtrack from Pokemon Journeys V18 (Jordan's fan-game find): its 48 REG0 tracks
(towns, routes, dungeons, battles, jingles) copied to assets/music/kanto/ under plain names
(REG0_22_PalletTown.mp3 -> pallet_town.mp3), which src/core/music.py plays by area in Kanto.
Run from the game folder:
    python dev/builders/import_journeys_music.py ["<Pokemon Journeys V18 folder>"]
"""
import os
import re
import shutil
import sys

JOURNEYS = os.path.join("..", "..", "Pokemon Journeys V18")
OUT = os.path.join("assets", "music", "kanto")
RENAME = {"HallofFame": "hall_of_fame", "SSAnne": "ss_anne", "MtMoon": "mt_moon", "OakLab": "oak_lab",
          "MaleTrainAppear": "male_trainer_appears", "FemaleTrainAppear": "female_trainer_appears",
          "EvilTrainAppear": "team_rocket_appears", "JessieJamesTheme": "jessie_james"}


def plain(stem):
    """'REG0_22_PalletTown' -> 'pallet_town', 'Reg0_42_Route19' -> 'route_19'."""
    words = stem.split("_", 2)[-1]
    if words in RENAME:
        return RENAME[words]
    return re.sub(r"(?<=[a-z])(?=[A-Z0-9])|(?<=[0-9])(?=[A-Z])", "_", words).lower()


def main(argv):
    root = argv[0] if argv else JOURNEYS
    bgm = os.path.join(root, "Audio", "BGM")
    if not os.path.isdir(bgm):
        sys.exit(f"Pokemon Journeys V18 not found at {root}")
    os.makedirs(OUT, exist_ok=True)
    n = 0
    for name in sorted(os.listdir(bgm)):
        stem, ext = os.path.splitext(name)
        if not stem.upper().startswith("REG0_") or ext.lower() != ".mp3":
            continue
        dest = os.path.join(OUT, plain(stem) + ".mp3")
        shutil.copy2(os.path.join(bgm, name), dest)
        n += 1
        print(f"  {dest}")
    print(f"{n} tracks")


if __name__ == "__main__":
    main(sys.argv[1:])
