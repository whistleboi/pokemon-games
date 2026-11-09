"""Regional forms' and female Pokemon's overworld sprites (Jordan, 11-08), from the Gen 7, Gen 8 and Hisuian sheets and the
gender-variant sheet. Each block (32 px frames: 2 across, a facing each row, on its own background colour) becomes a 4 x 4
walking sheet, each pixel doubled, like the rest of assets/dungeon/followers:
    a form the game has its own id for: <id>.png (2001 = Alolan Rattata), shiny/<id>.png
    a female: <dex>_female.png, shiny/<dex>_female.png
Only the forms and variants the game has are taken; every species already has its own sheet.

    python dev/builders/import_form_followers.py [folder holding the sheets]
"""
import json
import glob
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

UNIT_W, UNIT_H = 64, 128
OUT = os.path.join("assets", "dungeon", "followers")
JPEG_TOLERANCE = 46  # (a .jpg's background isn't one exact colour)

ALOLAN = {2001: (11, 0), 2002: (11, 1), 2003: (11, 2), 2004: (11, 3), 2005: (11, 4), 2006: (11, 5), 2007: (11, 6), 2008: (11, 7), 2009: (11, 8),
          2010: (12, 0), 2011: (12, 1), 2012: (12, 2), 2013: (12, 3), 2014: (12, 4), 2015: (12, 5), 2016: (12, 6), 2018: (10, 8)}
ALOLAN_BIG = {2017: (12, 7)}  # (Exeggutor: 64 px frames)
GALARIAN = {2019: (11, 1), 2020: (11, 3), 2021: (11, 4), 2024: (11, 5), 2025: (11, 7), 2026: (11, 8), 2031: (12, 1), 2032: (12, 3), 2033: (12, 4),
            2034: (12, 6), 2035: (12, 7), 2036: (12, 8), 2037: (13, 0), 2038: (13, 2), 2022: (13, 3), 2023: (13, 4), 2030: (13, 5),
            2027: (13, 6), 2028: (13, 7), 2029: (13, 8)}
HISUIAN = {2054: (0, 0), 2043: (0, 1), 2046: (0, 2), 2044: (0, 5), 2047: (0, 7), 2051: (1, 1), 2052: (1, 2), 2039: (1, 6), 2040: (1, 7),
           2041: (2, 0), 2042: (2, 1), 2045: (2, 2), 2053: (2, 4), 2048: (2, 5), 2049: (2, 6), 2050: (2, 7)}
FEMALE_ORDER = [3, 12, 19, 20, 25, 26, 41, 42, 44, 45,
                64, 65, 84, 85, 97, 111, 112, 118, 119, 123,
                129, 130, 133, 154, 165, 166, 178, 185, 186, 190,
                194, 195, 198, 202, 203, 207, 208, 212, 214, 215,
                217, 221, 224, 229, 232, 255, 256, 257, 267, 269,
                272, 274, 275, 307, 308, 315, 316, 317, 322, 323,
                332, 350, 369, 396, 397, 398, 399, 400, 401, 402,
                403, 404, 405, 407, 415, 417, 418, 419, 424, 443,
                444, 445, 449, 450, 453, 454, 456, 457, 459, 460,
                461, 464, 465, 473]


def block(sheet, r, c, frame, tolerance=0):
    """A block's 4 x 4 walking sheet, its background see-through."""
    x0, y0 = c * UNIT_W, r * UNIT_H
    bg = tuple(sheet.get_at((x0 + 1, y0 + 1)))[:3]
    out = pygame.Surface((4 * frame, 4 * frame), pygame.SRCALPHA)
    for row in range(4):
        for k in range(4):
            out.blit(sheet, (k * frame, row * frame), (x0 + (k % 2) * frame, y0 + row * frame, frame, frame))
    for y in range(out.get_height()):
        for x in range(out.get_width()):
            if all(abs(a - b) <= tolerance for a, b in zip(tuple(out.get_at((x, y)))[:3], bg)):
                out.set_at((x, y), (0, 0, 0, 0))
    return pygame.transform.scale(out, (out.get_width() * 2, out.get_height() * 2))


def block_on_white(sheet, r, c):
    """A block on plain white: only the white reaching in from each frame's edge goes (Indeedee's face is white too)."""
    out = block(sheet, r, c, 32, -1)  # (nothing keyed out yet)
    cell = out.get_width() // 4
    for fy in range(4):
        for fx in range(4):
            x0, y0 = fx * cell, fy * cell
            for x in range(cell):  # (the neighbouring block's pale colour, a line along the edge)
                for y in range(cell):
                    if (x < 2 or y < 2 or x >= cell - 2 or y >= cell - 2) and min(tuple(out.get_at((x0 + x, y0 + y)))[:3]) >= 170:
                        out.set_at((x0 + x, y0 + y), (0, 0, 0, 0))
            todo = [(x0 + x, y0 + y) for x in range(cell) for y in (0, cell - 1)] + [(x0 + x, y0 + y) for y in range(cell) for x in (0, cell - 1)]
            seen = set()
            while todo:
                x, y = todo.pop()
                if (x, y) in seen or not (x0 <= x < x0 + cell and y0 <= y < y0 + cell):
                    continue
                seen.add((x, y))
                if out.get_at((x, y)).a and min(tuple(out.get_at((x, y)))[:3]) < 250:
                    continue
                out.set_at((x, y), (0, 0, 0, 0))
                todo += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return out


def save(img, name, shiny):
    folder = os.path.join(OUT, "shiny") if shiny else OUT
    pygame.image.save(img, os.path.join(folder, f"{name}.png"))


def forms_by_id():
    out = {}
    for path in glob.glob(os.path.join("assets", "*.json")):
        try:
            data = json.load(open(path, encoding="utf-8-sig"))
        except ValueError:
            continue
        if isinstance(data, dict):
            out.update(data.get("FORM_MAP", {}))
    return out


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Downloads")
    pygame.init()
    pygame.display.set_mode((8, 8))
    load = lambda n: pygame.image.load(os.path.join(src, n)).convert()
    made = 0
    for normal, shiny, table, frame in (("alolan overworld sprites.png", "alolan shiny overworld sprites.png", ALOLAN, 32),
                                        ("alolan overworld sprites.png", "alolan shiny overworld sprites.png", ALOLAN_BIG, 64),
                                        ("galarian overworld sprites.png", "galarian shiny overworld sprites.png", GALARIAN, 32)):
        for name, is_shiny in ((normal, False), (shiny, True)):
            sheet = load(name)
            for fid, (r, c) in table.items():
                save(block(sheet, r, c, frame), fid, is_shiny)
                made += 1
    for name, is_shiny in (("hisuian overworld sprites.png", False), ("hisuian shiny overworld sprites.png", True)):  # (the originals: dev/reference/followers)
        sheet = pygame.image.load(os.path.join("dev", "reference", "followers", name)).convert()
        for fid, (r, c) in HISUIAN.items():
            save(block(sheet, r, c, 32), fid, is_shiny)
            made += 1
    female = load("gender variant overworld sprites.png")
    for i, dex in enumerate(FEMALE_ORDER):
        r, c = divmod(i, 10)
        save(block(female, r, c, 32), f"{dex}_female", False)
        save(block(female, r, c + 10, 32), f"{dex}_female", True)
        made += 2
    for dex, c in ((521, 4), (876, 9)):  # (Unfezant, Indeedee: the last row, on white, no shinies on the sheet)
        save(block_on_white(female, 9, c), f"{dex}_female", False)
        made += 1
    cast = load("castform sprites.jpg")
    weather = {v["form"]: int(k) for k, v in forms_by_id().items() if v.get("id") == 351}
    for c, form in enumerate(("sun", "rain", "hail")):  # (the top row, then its shinies)
        if form in weather:
            save(block(cast, 0, c, 32, JPEG_TOLERANCE), weather[form], False)
            save(block(cast, 1, c, 32, JPEG_TOLERANCE), weather[form], True)
            made += 2
    print(made, "sheets")


if __name__ == "__main__":
    main()
