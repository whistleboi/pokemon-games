"""Game Corner pictures (Jordan, 11-01): the Slot Machine and Voltorb Flip graphics from Pokemon Orre
2.1.1 (Pokemon Essentials' set, the HeartGold/SoulSilver look; Orre's copy has the clean cabinet top
and board without key hints), and its Tile Puzzle (the Ruins of Alph panels and wall, used by the
Ruins and the Gym challenge). Copied as they are to assets/sprites/game_corner/{slots,voltorb,tiles}/.
    python dev/builders/import_game_corner.py ["<Pokemon Orre folder>"]
"""
import os
import shutil
import sys

ORRE_GAME = os.path.join(os.path.expanduser("~"), "Downloads", "Pokemon_Orre_2.1.1", "Pokemon_Orre_2.1.1_reupload")
OUT = os.path.join("assets", "sprites", "game_corner")
SETS = {
    "slots": ("Slot Machine", {"bg.png": "bg.png", "images.png": "images.png", "numbers.png": "numbers.png",
                               "button.png": "button.png", "lights.png": "lights.png", "insert.png": "insert.png",
                               "press.png": "press.png", "stop.png": "stop.png", "win.png": "win.png",
                               "lose.png": "lose.png", "bonus.png": "bonus.png", "line1.png": "line1.png",
                               "line2.png": "line2.png", "line3a.png": "line3a.png", "line3b.png": "line3b.png",
                               "ReelOverlay.png": "reel_overlay.png"}),
    "voltorb": ("Voltorb Flip", {"Voltorb Flip bg.png": "board.png", "tiles.png": "tiles.png",
                                 "numbersSmall.png": "numbers_small.png", "numbersScore.png": "numbers_score.png",
                                 "explosion.png": "explosion.png", "flipAnimation.png": "sparkle.png",
                                 "cursor.png": "cursor.png", "memo.png": "memo.png"}),
    "tiles": ("Tile Puzzle", {"bg.png": "bg.png", "bgOmanyte.png": "bg_omanyte.png", "bgAerodactyl.png": "bg_aerodactyl.png",
                              "bgHooh.png": "bg_hooh.png", "tilesKabuto.png": "kabuto.png", "tilesOmanyte.png": "omanyte.png",
                              "tilesAerodactyl.png": "aerodactyl.png", "tilesHooh.png": "hooh.png"}),
}


def main(root):
    ui = os.path.join(root, "Graphics", "UI")
    if not os.path.isdir(ui):
        sys.exit(f"Pokemon Orre not found at {root}")
    for kind, (folder, files) in SETS.items():
        os.makedirs(os.path.join(OUT, kind), exist_ok=True)
        for src, dst in files.items():
            shutil.copyfile(os.path.join(ui, folder, src), os.path.join(OUT, kind, dst))
        print(f"{len(files)} {kind} pictures -> {os.path.join(OUT, kind)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ORRE_GAME)
