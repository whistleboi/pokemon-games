"""Paldea's overworld Pokemon (Jordan, 11-06): the "Gen 9 (Paldea) Pokemon Overworlds" sheets by Darkus_Shadow,
Princess-Phoenix, shaderr31, Wolfang62, CarmaNekko and EduarPokeN (free to use with credit; DeviantArt,
darkusshadow's gallery), normal and shiny. On the sheet each Pokemon has a block on its own background
colour: a small one 64 x 128 (2 frames across, 4 facings down: down, left, right, up, 32 px frames), a big one
256 x 128 (64 px frames: down, down, left, left / right, right, up, up). Each becomes a 4 x 4 walking sheet
(its background see-through) -> assets/dungeon/followers/<dex>.png and shiny/<dex>.png, like Everlasting X's
(dev/builders/import_followers.py), each pixel doubled to match them. Forms the game has its own id for (Paldean Tauros, Paldean Wooper) go
under that id.

    python dev/builders/import_paldea_followers.py <normal sheet.png> <shiny sheet.png>
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

UW, UH = 64, 128
# the sheet's blocks in reading order -> the Pokemon (None: a pose or a form the game doesn't have)
ORDER = [906, 907, 908, 909, 910, 911, 912, 913, 914, 915, 916, None, 917, 918, 919, 920, 921, 922, 923, 924, 925,
         None, 926, 927, 928, 929, 930, 931, None, None, None, 932, 933, 934, 935, 936, 937, 938, 939, 940, 941, 942,
         943, 944, 945, 946, 947, 948, 949, 950, 951, 952, 953, 954, 955, 956, 957, 958, 959, 960, 961, 962, 963,
         964, None, 965, 966, 967, None, 968, 969, 970, 971, 972, 973, 974, 975, 976, 977, 978, None, None, 979, 980,
         981, 982, None, 983, 984, 985, 986, 987, 988, 989, 990, 991, 992, 993, 994, 995, 996, 997, 998, None, 999,
         None, 1000, 1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010, 1011, 1012, 1013, 1014, 1015, 1016,
         1017, None, None, None, None, None, None, None, None, None, None, None, None, 1018, 1019, 1020, 1021, 1022,
         1023, 1024, None, None, None, 1025, 2057, 2056, 2055, 2058]


def blocks(sheet):
    """[(x, y, w, h, colour)] in units: each Pokemon's block (same-coloured units joined)."""
    cols, rows = sheet.get_width() // UW, sheet.get_height() // UH
    col = {(c, r): tuple(sheet.get_at((c * UW + 1, r * UH + 1)))[:3] for r in range(rows) for c in range(cols)}
    seen, out = set(), []
    for r in range(rows):
        for c in range(cols):
            if (c, r) in seen:
                continue
            k = col[(c, r)]
            w = 1
            while col.get((c + w, r)) == k and (c + w, r) not in seen:
                w += 1
            h = 1
            while all(col.get((c + i, r + h)) == k and (c + i, r + h) not in seen for i in range(w)):
                h += 1
            seen |= {(c + i, r + j) for i in range(w) for j in range(h)}
            out.append((c, r, w, h, k))
    return out


def walking_sheet(sheet, c, r, w, h, colour):
    big = w > 1
    f = 64 if big else 32
    x0, y0 = c * UW, r * UH
    if big:  # (down, down, left, left / right, right, up, up)
        cells = {0: [(0, 0), (1, 0)], 1: [(2, 0), (3, 0)], 2: [(0, 1), (1, 1)], 3: [(2, 1), (3, 1)]}
    else:  # (2 frames across, a facing each row)
        cells = {row: [(0, row), (1, row)] for row in range(4)}
    out = pygame.Surface((4 * f, 4 * f), pygame.SRCALPHA)
    for row, frames in cells.items():
        for k in range(4):
            fx, fy = frames[k % 2]
            out.blit(sheet, (k * f, row * f), (x0 + fx * f, y0 + fy * f, f, f))
    for y in range(out.get_height()):  # the block's background colour: see-through
        for x in range(out.get_width()):
            if tuple(out.get_at((x, y)))[:3] == colour:
                out.set_at((x, y), (0, 0, 0, 0))
    # (drawn at 1x; Everlasting X's are 2x, each pixel doubled: doubled here too, so they all match)
    return pygame.transform.scale(out, (out.get_width() * 2, out.get_height() * 2))


def main():
    normal, shiny = sys.argv[1], sys.argv[2]
    pygame.init()
    pygame.display.set_mode((8, 8))
    base = os.path.join("assets", "dungeon", "followers")
    made = 0
    for path, out_dir in ((normal, base), (shiny, os.path.join(base, "shiny"))):
        sheet = pygame.image.load(path).convert()
        found = blocks(sheet)
        for (c, r, w, h, colour), dex in zip(found, ORDER):
            if dex is None:
                continue
            os.makedirs(out_dir, exist_ok=True)
            pygame.image.save(walking_sheet(sheet, c, r, w, h, colour), os.path.join(out_dir, f"{dex}.png"))
            made += 1
    print(made, "sheets")


if __name__ == "__main__":
    main()
