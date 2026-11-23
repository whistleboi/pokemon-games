"""Johto's one Pokemon Center and one Poke Mart picture -> assets/backgrounds/johto/johto_center.png, johto_mart.png

The screens behind the Center's and Mart's menus (heal, shop) for every Johto town (Jordan, 11-22: "use the in-game designs for
the centers and marts ... cookie-cutter"). Cut from the same SoulSilver rooms every Johto town walks in (assets/tiles/ss_ground/
T21PC0101.png and T21FS0101.png, made by kanto_handoff/johto_map_tools/j_center_mart.py), not drawn: the old per-town pictures
(cherrygrove_city_center.png and the rest) were an early version's look and are gone.

Each room is cut at its own size (no scaling: crisp) and laid in the middle of the 1280x540 area above the dialogue box, on the
dark of the room pictures' own surround. Run from the game folder: python dev/builders/make_johto_buildings.py"""
import os
import pygame

W, H = 1280, 540
DARK = (17, 17, 27)
# picture, the part of it that is the room (px): the Center's ground floor from its back wall down past the nurse's counter and the
# Poke Ball mat; the Mart whole, from its back shelves to the door
CUTS = {"johto_center.png": ("T21PC0101.png", (32, 70, 512, 610)),
        "johto_mart.png": ("T21FS0101.png", (32, 146, 416, 500)),
        # (the one shop with its own look: Goldenrod's Dept. Store, its ground floor)
        "goldenrod_dept_store.png": ("T25R1001.png", (32, 140, 768, 500))}


def main():
    pygame.init()
    src = os.path.join("assets", "tiles", "ss_ground")
    out = os.path.join("assets", "backgrounds", "johto")
    for name, (pic, (x0, y0, x1, y1)) in CUTS.items():
        img = pygame.image.load(os.path.join(src, pic))
        room = img.subsurface((x0, y0, x1 - x0, y1 - y0))
        canvas = pygame.Surface((W, H))
        canvas.fill(DARK)
        canvas.blit(room, ((W - room.get_width()) // 2, (H - room.get_height()) // 2))
        pygame.image.save(canvas, os.path.join(out, name))
        print(name, room.get_size())


if __name__ == "__main__":
    main()
