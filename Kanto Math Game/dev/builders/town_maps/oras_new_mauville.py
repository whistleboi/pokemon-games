"""New Mauville as Omega Ruby / Alpha Sapphire lays it out (Jordan, 11-14: "for new mauville do make that with emerald
interiors the best you can to match the layout as well"). Mauville City itself stays Emerald's (Jordan, 11-14: "I liked
the old mauville better... use old mauville and work the oras story into that geography": hoenn_oras.py).

The layout is Omega Ruby's own: where you can walk, its generators and machines, its way in and where its people stand,
read from Jordan's game file by kanto_handoff/oras_map_tools (orasmap.export -> dev/builders/data/mauville_oras.json,
"new_mauville"). One tile there is one tile here. It is drawn with Emerald's own New Mauville tiles (24_53.png), stamped
into one picture (assets/tiles/em_ground/oras_new_mauville.png). Its way in and out is the door in Mauville, as before.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))   # (dev/builders/town_maps -> the game folder)
DATA = json.load(open(os.path.join(GAME, "dev", "builders", "data", "mauville_oras.json"), encoding="utf-8"))["new_mauville"]
PICS = os.path.join(GAME, "assets", "tiles", "em_ground")
TILES = {"floor": (16, 10), "wall_lo": (18, 4), "wall_hi": (18, 3), "counter": (5, 6), "plant": (12, 1), "mat": (16, 10)}
VOID = (16, 14, 20)


def _walk(v):
    return int(v, 16) & 0xFF in (0x20, 0x01, 0x24)


def _near_floor(rows, x, y):
    """Furniture worth drawing: next to somewhere you can walk (else it is just wall)."""
    return any(0 <= y + dy < len(rows) and 0 <= x + dx < len(rows[0]) and _walk(rows[y + dy][x + dx])
               for dx in (-1, 0, 1) for dy in (-1, 0, 1))


def picture(art):
    """Stamp the picture from Emerald's New Mauville tiles: floor, walls (two tiles tall over the floor), machines."""
    import pygame as pg
    if not pg.get_init():
        pg.init()
    sheet = pg.image.load(os.path.join(PICS, "24_53.png"))
    tile = {k: sheet.subsurface((x * 16, y * 16, 16, 16)) for k, (x, y) in TILES.items()}
    h, w = len(art), len(art[0])
    s = pg.Surface((w * 16, h * 16))
    s.fill(VOID)
    walk = lambda x, y: 0 <= y < h and 0 <= x < w and art[y][x] not in "cm"
    for y in range(h):
        for x in range(w):
            c, at = art[y][x], (x * 16, y * 16)
            if c == "c":
                if walk(x, y + 1) or (y + 1 < h and art[y + 1][x] == "m"):
                    s.blit(tile["wall_lo"], at)
                elif walk(x, y + 2):
                    s.blit(tile["wall_hi"], at)
                continue
            s.blit(tile["floor"], at)
            if c == "m":
                lone = not any(0 <= x + dx < w and 0 <= y + dy < h and art[y + dy][x + dx] == "m"
                               for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                s.blit(tile["plant" if lone else "counter"], at)
            elif c == "v":
                s.blit(tile["mat"], at)
    pg.image.save(s, os.path.join(PICS, "oras_new_mauville.png"))
    return "em_ground/oras_new_mauville.png"


def new_mauville(maps):
    """HOENN_NEW_MAUVILLE: ORAS's layout; the security computer where ORAS has its back-room person, the Ampharosite;
    out the way in, back to Mauville City."""
    rows = DATA["rows"]
    grid = [["." if _walk(v) else "c" for v in row] for row in rows]
    for fx, fy, fw, fh, _ in DATA["furniture"]:
        for i in range(fw):
            for j in range(fh):
                if 0 <= fy + j < len(grid) and 0 <= fx + i < len(grid[0]):
                    grid[fy + j][fx + i] = "m" if _near_floor(rows, fx + i, fy + j) else "c"
    w = DATA["warps"][0]
    for i in range(max(1, w["w"])):
        grid[w["y"]][w["x"] + i] = "v"
    spots = sorted((p["y"], p["x"]) for p in DATA["people"])
    first = spots[0]   # (the security computer: ORAS's top-room person, at its back wall)
    amph = next(s for s in spots if s[0] > 10)
    grid[first[0]][first[1]] = "N"
    grid[amph[0]][amph[1]] = "N"
    art = ["".join(r) for r in grid]
    maps["HOENN_NEW_MAUVILLE"] = {"art": art, "exits": {"v": "MAUVILLE_CITY"}, "buildings": {},
                                  "people": ["Security computer", "AMPHAROSITE"] if first < amph else ["AMPHAROSITE", "Security computer"],
                                  "trainer_spots": [], "theme": "room",
                                  "roofs": {"_picture": {"f": picture(art), "at": [0, 0]}, "_signs_in_picture": True,
                                            "_buildings_in_picture": True}}
