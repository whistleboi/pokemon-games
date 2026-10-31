"""Top-down pixel-art Kalos Pokémon Center -> assets/backgrounds/kalos/kalos_center.png

The one Pokemon Center (with its shop) every Kalos town uses (Jordan, 10-30), laid out from X/Y's
Center and aveontrainer's pixel take on it: the blue cylinder healing machine with Nurse Joy inside a
red horseshoe counter and the red PC beside it; the shop raised at the back right (clerks behind a
curved blue counter, goods on the wall); the cream back wall with the TV, a painting, books and the red
door to the back room; diamond tiles at the back, mint tiles at the front with the Poke Ball emblem;
the black corner sofa and a glass table (left), red cafe tables and stools, a shelf of goods and a
drinks fridge (right). Drawn here, not copied: dark outlines, three-tone shading, soft drop shadows.

Drawn at 426x180 and scaled 3x (crisp) onto the 1280x540 area above the dialogue box.
Nurse Joy is the front-facing frame of dev/builders/art/nurse_joy_overworld.png. The PC,
glass case, shop shelves, bookshelves, glass table, plants, cushions and drinks fridge come
from DonLawride's HGSS Mart/Center tileset (dev/builders/art/mart_center_tileset_hgss.png).

    python dev/builders/make_kalos_center.py
"""
import colorsys
import math
import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "assets", "backgrounds", "kalos", "kalos_center.png")
NURSE_SHEET = os.path.join(HERE, "art", "nurse_joy_overworld.png")
TILESET = os.path.join(HERE, "art", "mart_center_tileset_hgss.png")
# Pieces of the tileset (drawn at 2x there): name -> rect on the sheet.
TILES = {
    "pc": (254, 148, 30, 52), "glass_case": (130, 116, 96, 44), "bookshelf": (258, 252, 62, 58),
    "table": (322, 258, 60, 60), "plant": (66, 292, 28, 60), "shelf": (2, 276, 60, 64),
    "cushion": (450, 166, 30, 26), "fridge": (162, 172, 60, 68),
}
W, H, SCALE = 426, 180, 3
OUT_W, OUT_H = 1280, 540

INK = (40, 34, 46)
WHITE, WHITE_S, WHITE_D = (250, 250, 252), (226, 226, 234), (190, 190, 204)
FLOOR_TOP, FLOOR_BOT, GRID = (232, 233, 240), (246, 246, 250), (220, 221, 230)
RED, RED_L, RED_D, RED_DD = (222, 52, 52), (246, 100, 96), (172, 34, 42), (120, 24, 34)
CYAN, CYAN_D, CYAN_L = (88, 208, 240), (32, 128, 192), (204, 246, 255)
DARK, DARK_M, DARK_L = (44, 44, 56), (70, 70, 88), (104, 104, 124)
WOOD, WOOD_L, WOOD_D = (150, 98, 60), (186, 132, 86), (104, 66, 40)

CLERK_COLORS = {
    "k": INK, "h": (124, 76, 50), "H": (84, 50, 34), "L": (168, 112, 70), "s": (248, 210, 172),
    "S": (220, 164, 124), "e": (44, 44, 70), "w": (250, 250, 250), "c": (96, 200, 232),
    "b": (52, 124, 204), "B": (32, 82, 148),
}
CLERK = [
    "......kkkkkk......",
    "....kkhhhhhhkk....",
    "...khLLhhhhhhhk...",
    "..khLhhhhhhhhhhk..",
    "..khhhhhhhhhhhHk..",
    ".khHhhhhhhhhhhHHk.",
    ".khHkkkkkkkkkkHHk.",
    ".kHksssssssssskHk.",
    ".kHksswsssswsskHk.",
    ".kHksseksskesskHk.",
    "..kkSsksssskSskk..",
    "...kkSskkkksSkk...",
    "....kkwwccwwkk....",
    "..kkbbwwccwwbbkk..",
    ".kbbbbbwccwbbbbbk.",
    "kbbbbbbbwwbbbbbbbk",
    "kBbbbbbbwwbbbbbbBk",
    "kBsBbbbbbbbbbbBsBk",
]


def lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def box(s, color, rect, outline=INK):
    pygame.draw.rect(s, color, rect)
    if outline:
        pygame.draw.rect(s, outline, rect, 1)


def shadow(s, rect, alpha=46):
    sh = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    pygame.draw.ellipse(sh, (30, 30, 60, alpha), sh.get_rect())
    s.blit(sh, rect[:2])


def vgrad(s, rect, top, bottom):
    x, y, w, h = rect
    for i in range(h):
        pygame.draw.line(s, lerp(top, bottom, i / max(1, h - 1)), (x, y + i), (x + w - 1, y + i))


def pixmap(s, rows, colors, x, y, max_rows=None):
    for j, row in enumerate(rows[:max_rows]):
        for i, ch in enumerate(row):
            if ch in colors:
                s.set_at((x + i, y + j), colors[ch])


def load_tiles():
    sheet = pygame.image.load(TILESET)
    tiles = {}
    for name, (x, y, w, h) in TILES.items():
        piece = pygame.Surface((w, h), pygame.SRCALPHA)
        piece.blit(sheet, (0, 0), (x, y, w, h))
        tiles[name] = pygame.transform.scale(piece, (w // 2, h // 2))  # back to 1x pixels
    tiles["red_cushion"] = recolor(tiles["cushion"], 0)
    return tiles


def recolor(surf, hue):
    """Same shading, new hue, for the colored pixels (outlines and whites stay)."""
    out = surf.copy()
    for y in range(out.get_height()):
        for x in range(out.get_width()):
            r, g, b, a = out.get_at((x, y))
            h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
            if a and s > 0.35 and 0.2 < l < 0.9:
                r, g, b = colorsys.hls_to_rgb(hue / 360, l * 0.9, s)
                out.set_at((x, y), (round(r * 255), round(g * 255), round(b * 255), a))
    return out


def place(s, tile, x, y, shade=True):
    """Blit a tileset piece with its feet at (x, y + height), with a soft shadow under it."""
    w, h = tile.get_size()
    if shade:
        shadow(s, (x - 2, y + h - 4, w + 4, 7), 44)
    s.blit(tile, (x, y))


def nurse_sprite():
    sheet = pygame.image.load(NURSE_SHEET)
    frame = pygame.Surface((68, 72), pygame.SRCALPHA)
    frame.blit(sheet, (0, 0), (0, 0, 68, 72))               # top-left frame: facing down
    frame = pygame.transform.scale(frame, (34, 36))          # the sheet is drawn at 2x
    return frame.subsurface(frame.get_bounding_rect()).copy()


CREAM, CREAM_D, CREAM_L = (240, 222, 172), (214, 190, 140), (250, 238, 200)
MINT, MINT_G = (190, 226, 216), (172, 214, 204)
DIAMOND, DIAMOND_D = (226, 228, 236), (196, 198, 212)
BLUE, BLUE_D, BLUE_L, BLUE_DD = (64, 150, 222), (36, 98, 176), (140, 206, 250), (22, 58, 120)
TAN, TAN_D = (222, 196, 150), (180, 150, 104)


def diamonds(s, rect):
    """A floor of grey diamond tiles (the back of the room and the raised shop)."""
    x, y, w, h = rect
    tile = pygame.Surface((w, h))
    tile.fill(DIAMOND)
    for i in range(-h, w + h, 10):
        pygame.draw.line(tile, DIAMOND_D, (i, 0), (i + h, h))
        pygame.draw.line(tile, DIAMOND_D, (i, h), (i + h, 0))
    s.blit(tile, (x, y))


def floor(s):
    room = [(4, 2), (422, 2), (422, 168), (412, 178), (14, 178), (4, 168)]
    pygame.draw.polygon(s, MINT, room)                              # the mint tiles at the front
    for x in range(4, 422, 16):
        pygame.draw.line(s, MINT_G, (x, 96), (x, 177))
    for y in range(96, 178, 16):
        pygame.draw.line(s, MINT_G, (4, y), (421, y))
    diamonds(s, (4, 46, 418, 50))                                   # the diamond tiles at the back
    box(s, DIAMOND_D, (4, 95, 418, 2), None)
    return room


def back_wall(s):
    vgrad(s, (4, 2, 418, 6), DARK_L, DARK_M)                        # the grey trim along the top
    vgrad(s, (4, 8, 418, 32), CREAM_L, CREAM)                       # the cream wall
    for x in range(30, 420, 36):
        pygame.draw.line(s, CREAM_D, (x, 9), (x, 39))
    vgrad(s, (4, 40, 418, 5), DARK_L, DARK_M)                       # the baseboard
    box(s, INK, (4, 45, 418, 1), None)
    box(s, DARK, (16, 13, 46, 24))                                  # the TV
    vgrad(s, (19, 16, 40, 18), CYAN_L, CYAN_D)
    pygame.draw.line(s, WHITE, (21, 18), (32, 18))
    box(s, WOOD_D, (74, 9, 40, 16))                                 # a landscape painting
    vgrad(s, (76, 11, 36, 6), (250, 170, 120), (250, 214, 160))
    vgrad(s, (76, 17, 36, 6), (110, 180, 90), (70, 140, 70))
    box(s, DARK_L, (74, 32, 40, 4), INK)                            # books on a ledge
    for i, c in enumerate(((210, 60, 60), (60, 110, 200), (240, 190, 60), (110, 70, 160), (60, 160, 100))):
        box(s, c, (77 + i * 7, 26, 5, 6), INK)
    box(s, DARK_M, (136, 12, 34, 33))                               # the red door to the back room
    box(s, RED_D, (139, 16, 28, 29), INK)
    pygame.draw.line(s, INK, (153, 16), (153, 44))
    for x in (141, 155):
        box(s, RED, (x, 19, 10, 22), None)


def floor_marks(s):
    for x in (178, 248):                                            # the walkway to the door
        pygame.draw.line(s, DARK, (x, 100), (x, 176), 2)
    shadow(s, (186, 150, 54, 12), 36)
    pygame.draw.circle(s, DARK, (213, 140), 20)                     # the Poke Ball emblem
    pygame.draw.circle(s, MINT, (213, 140), 16)
    box(s, DARK, (195, 138, 37, 5), None)
    pygame.draw.circle(s, DARK, (213, 140), 8)
    pygame.draw.circle(s, MINT, (213, 140), 4)
    box(s, DARK, (196, 173, 34, 5), INK)                            # the door mat


def lounge(s, t):
    # A long black sofa round the corner of the left wall, a glass table before it, plants.
    shadow(s, (8, 112, 84, 66), 40)
    box(s, DARK, (6, 100, 16, 70))                                  # along the wall
    box(s, DARK, (6, 158, 84, 14))                                  # along the front
    box(s, DARK_M, (22, 104, 8, 54), INK)
    box(s, DARK_M, (22, 150, 66, 8), INK)
    pygame.draw.line(s, DARK_L, (9, 103), (9, 167))
    pygame.draw.line(s, DARK_L, (9, 161), (86, 161))
    box(s, WHITE_D, (48, 108, 16, 34), INK)                         # the glass table
    vgrad(s, (50, 110, 12, 30), (236, 244, 250), (200, 214, 230))
    pygame.draw.line(s, WHITE, (52, 112), (58, 118))
    place(s, t["plant"], 6, 66)
    place(s, t["plant"], 94, 146)


def shop(s, t):
    # The shop, raised at the back right: goods on the wall, clerks behind a curved blue counter.
    diamonds(s, (262, 2, 160, 56))
    pygame.draw.line(s, WHITE, (262, 2), (421, 2), 2)               # its glass rail
    for x in (300, 330, 360, 390):
        place(s, t["shelf"], x, 2, shade=False)
    for x in (318, 364):
        pixmap(s, CLERK, CLERK_COLORS, x, 26)
    shadow(s, (262, 60, 160, 10), 40)
    pts = [(270, 44), (421, 44), (421, 58), (276, 58), (266, 52)]
    pygame.draw.polygon(s, BLUE, pts)
    pygame.draw.polygon(s, BLUE_L, [(270, 44), (421, 44), (421, 48), (268, 48)])
    pygame.draw.line(s, BLUE_D, (276, 56), (421, 56), 2)
    pygame.draw.polygon(s, INK, pts, 1)
    box(s, WHITE, (398, 36, 14, 10), INK)                           # the till
    box(s, DARK_M, (400, 38, 10, 4), None)


def cafe(s, t):
    # Goods on a shelf and a drinks fridge on the right wall; red cafe tables with red stools.
    place(s, t["shelf"], 340, 58)
    place(s, t["fridge"], 392, 92)
    place(s, t["plant"], 396, 146)
    for tx, ty in ((330, 124), (330, 158)):
        shadow(s, (tx - 18, ty + 6, 36, 9), 44)
        box(s, WHITE_S, (tx - 2, ty + 2, 4, 8), INK)
        box(s, RED_D, (tx - 13, ty - 8, 26, 12), INK)               # the table
        box(s, (248, 190, 190), (tx - 10, ty - 6, 20, 7), None)
        for dx, dy in ((-28, -6), (16, -6)):                        # round red stools
            box(s, WHITE_S, (tx + dx + 5, ty + dy + 6, 2, 7), None)
            pygame.draw.ellipse(s, INK, (tx + dx - 1, ty + dy - 1, 14, 9))
            pygame.draw.ellipse(s, RED, (tx + dx, ty + dy, 12, 7))
            pygame.draw.line(s, RED_L, (tx + dx + 3, ty + dy + 2), (tx + dx + 8, ty + dy + 2))


def tower(s, nurse):
    # The healing machine: a tall blue cylinder, dotted with light, banded in navy, a tan disc on top.
    pygame.draw.ellipse(s, DARK_M, (158, 58, 110, 46))
    pygame.draw.ellipse(s, DARK, (166, 62, 94, 36))
    x0, w = 184, 58
    for i in range(w):
        t = abs(i - w / 2) / (w / 2)
        pygame.draw.line(s, lerp(BLUE, BLUE_DD, t ** 2), (x0 + i, 6), (x0 + i, 74))
    for y in range(12, 70, 5):                                      # specks of light
        for i in range(3 + (y // 5) % 2 * 3, w - 3, 6):
            t = abs(i - w / 2) / (w / 2)
            s.set_at((x0 + i, y), lerp(BLUE_L, BLUE, t))
    for y0 in (40, 58):                                             # navy bands with diamond lights
        box(s, BLUE_DD, (x0, y0, w, 7), None)
        for x in range(x0 + 6, x0 + w - 4, 10):
            pygame.draw.polygon(s, CYAN, [(x, y0 + 1), (x + 3, y0 + 3), (x, y0 + 5), (x - 3, y0 + 3)])
    pygame.draw.ellipse(s, TAN_D, (x0 - 3, 0, w + 6, 12))
    pygame.draw.ellipse(s, TAN, (x0 - 1, 0, w + 2, 9))
    pygame.draw.line(s, INK, (x0 - 1, 6), (x0 - 1, 74))
    pygame.draw.line(s, INK, (x0 + w, 6), (x0 + w, 74))
    s.blit(nurse, (213 - nurse.get_width() // 2, 81 - nurse.get_height()))


def counter(s, t):
    # Red horseshoe counter: dark front face, lit top, opening toward the tower.
    layer = pygame.Surface((W, H), pygame.SRCALPHA)
    cx, cy, rx, ry = 213, 72, 58, 22
    pygame.draw.ellipse(layer, RED_DD, (cx - rx - 1, cy - ry + 7, 2 * rx + 2, 2 * ry + 2))
    pygame.draw.ellipse(layer, RED_D, (cx - rx, cy - ry + 7, 2 * rx, 2 * ry))
    pygame.draw.ellipse(layer, INK, (cx - rx - 1, cy - ry - 1, 2 * rx + 2, 2 * ry + 2))
    pygame.draw.ellipse(layer, RED, (cx - rx, cy - ry, 2 * rx, 2 * ry))
    pygame.draw.ellipse(layer, RED_L, (cx - rx + 3, cy - ry + 2, 2 * rx - 6, 2 * ry - 8), 2)
    pygame.draw.ellipse(layer, INK, (cx - rx + 11, cy - ry + 3, 2 * (rx - 11), 2 * (ry - 10)))
    pygame.draw.ellipse(layer, (0, 0, 0, 0), (cx - rx + 12, cy - ry + 4, 2 * (rx - 12), 2 * (ry - 10) - 2))
    clip = pygame.Surface((W, H), pygame.SRCALPHA)
    clip.blit(layer, (0, cy - 2), (0, cy - 2, W, H))               # front half only
    s.blit(clip, (0, 0))
    box(s, CYAN_L, (205, 94, 16, 3), CYAN_D)                       # glass top at the front
    place(s, recolor(t["pc"], 0), 278, 60)                          # the red PC beside the counter


def draw():
    s = pygame.Surface((W, H))
    s.fill((0, 0, 0))
    room = floor(s)
    back_wall(s)
    floor_marks(s)
    tiles = load_tiles()
    lounge(s, tiles)
    shop(s, tiles)
    cafe(s, tiles)
    tower(s, nurse_sprite())
    counter(s, tiles)
    pygame.draw.polygon(s, INK, room, 1)
    big = pygame.transform.scale_by(s, SCALE)
    out = pygame.Surface((OUT_W, OUT_H))
    out.fill((0, 0, 0))
    out.blit(big, ((OUT_W - big.get_width()) // 2, 0))
    return out


if __name__ == "__main__":
    pygame.init()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    pygame.image.save(draw(), OUT)
    print("wrote", OUT)
