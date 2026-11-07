"""Overworld sheets Jordan added (11-06) for Pokemon and forms the other sets don't have, from ~/Downloads:
single 4 x 4 walking sheets (Archaludon, Ogerpon's Teal and Wellspring Masks, Terapagos's Terastal and
Stellar forms, Mega Malamar, Mega Victreebel), and "gigantamax overworld.png": six Gigantamax Pokemon in a
3 x 2 grid, each block 4 frames across (2 normal, 2 shiny) and 4 facings down.
-> assets/dungeon/followers/<dex>.png, <dex>_<form>.png (the form's name as the game has it: water_mask,
terra, mega, gmax...), and shiny/<dex>_gmax.png.

    python dev/builders/import_extra_followers.py [<folder>]   (after import_paldea_followers.py: its Ogerpon and
                                                                Archaludon are replaced by these)
"""
import os
import shutil
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Downloads")
OUT = os.path.join("assets", "dungeon", "followers")
SINGLE = {"archaludon.png": "1018.png", "Ogerpon Teal Mask.png": "1017.png",
          "Ogerpon Wellspring Mask.png": "1017_water_mask.png", "Terapagos Terastal Form.png": "1024_terra.png",
          "Terapagos Stellar Form.png": "1024_stellar.png", "mega malamar.png": "687_mega.png",
          "mega victreebell.png": "71_mega.png"}
GMAX = [[68, 94, 25], [99, 131, 809]]  # Machamp, Gengar, Pikachu / Kingler, Lapras, Melmetal


def main():
    pygame.init()
    pygame.display.set_mode((8, 8))
    os.makedirs(os.path.join(OUT, "shiny"), exist_ok=True)
    for src, dst in SINGLE.items():
        path = os.path.join(SRC, src)
        if os.path.exists(path):
            shutil.copyfile(path, os.path.join(OUT, dst))
    path = os.path.join(SRC, "gigantamax overworld.png")
    if os.path.exists(path):
        sheet = pygame.image.load(path).convert_alpha()
        bw, bh = sheet.get_width() / 3, sheet.get_height() / 2
        f = int(round(bw / 4))
        for r, row in enumerate(GMAX):
            for c, pid in enumerate(row):
                for shiny, first in ((False, 0), (True, 2)):
                    out = pygame.Surface((4 * f, 4 * f), pygame.SRCALPHA)
                    for facing in range(4):
                        for k in range(4):
                            col = first + k % 2
                            x = int(round(c * bw + col * bw / 4))
                            y = int(round(r * bh + facing * bh / 4))
                            out.blit(sheet, (k * f, facing * f), (x, y, f, f))
                    out = pygame.transform.scale(out, (out.get_width() * 2, out.get_height() * 2))  # (1x art: 2x like the rest)
                    pygame.image.save(out, os.path.join(OUT, "shiny" if shiny else "", f"{pid}_gmax.png"))
    print("ok")


if __name__ == "__main__":
    main()
