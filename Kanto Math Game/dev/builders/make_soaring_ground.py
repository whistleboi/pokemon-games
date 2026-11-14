"""Hoenn seen from high above, for Soaring in the Sky (Jordan, 11-14): the ground that scrolls under Latios / Latias.

Made from the game's own Hoenn map picture (assets/region_maps/hoenn.png, 480 x 320): each pixel is sorted into sea,
shallows, grass, forest, mountain or sand; the route lines and town markers drawn over it are filled in from what is
around them; then it is drawn again in our style, four times the size (smooth pixel edges: pygame's scale2x twice),
with surf along the coasts, darker deep water, tree clumps and ridges. A band of open sea is added above and below so
the flight can loop north without a seam.
    python dev/builders/make_soaring_ground.py      (from the game folder; writes assets/soaring/hoenn_ground.png)
"""
import os
import random

import pygame

SRC = os.path.join("assets", "region_maps", "hoenn.png")
OUT = os.path.join("assets", "soaring", "hoenn_ground.png")
PAD = 40            # rows of open sea added above and below (map pixels)
SEA, SHALLOW, GRASS, FOREST, MOUNT, SAND, UNKNOWN, WET = range(8)   # WET: a sea route's line (water under it)
LOOK = {SEA: (40, 112, 200), SHALLOW: (72, 168, 224), GRASS: (112, 192, 80), FOREST: (64, 148, 64),
        MOUNT: (176, 144, 96), SAND: (232, 212, 136)}
KEY = {v: k for k, v in LOOK.items()}


def kind(c):
    r, g, b = c[:3]
    if r > 195 and 130 <= g <= 206 and b < 150 and r - g > 28:   # the orange route lines (and their soft edges):
        return WET if b >= 85 else UNKNOWN                        #  over the sea they're a bluer orange
    if r > 200 and g < 140:                               # red town markers
        return UNKNOWN
    if b > 200 and r < 140 and g < 170:                   # blue markers
        return UNKNOWN
    if r > 215 and g > 215 and b > 215:                   # markers' white rims
        return UNKNOWN
    if b > r + 40 and b >= g - 25:
        return SHALLOW if g > 182 else SEA
    if r > 215 and g > 195 and b < 120:
        return SAND                                       # the desert's yellow
    if r > 170 and g > 150 and b < 110 and 0 <= r - g <= 28:
        return MOUNT                                      # tan mountain land
    if g >= r and g >= b:
        return FOREST if g < 175 else GRASS
    return UNKNOWN


def classify(img):
    w, h = img.get_size()
    grid = [[kind(img.get_at((x, y))) for x in range(w)] for y in range(h)]
    for y in range(h):                                    # a "sea" line with mostly land around it is a land line
        for x in range(w):
            if grid[y][x] == WET:
                wet = dry = 0
                for dy in range(-5, 6):
                    for dx in range(-5, 6):
                        if 0 <= x + dx < w and 0 <= y + dy < h:
                            k = grid[y + dy][x + dx]
                            wet += k in (SEA, SHALLOW)
                            dry += k in (GRASS, FOREST, MOUNT, SAND)
                if dry > wet * 2:
                    grid[y][x] = UNKNOWN
    for _ in range(40):                                   # fill the lines and markers from their neighbours
        todo = [(x, y) for y in range(h) for x in range(w) if grid[y][x] in (UNKNOWN, WET)]
        if not todo:
            break
        new = []
        for x, y in todo:
            seen = {}
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    nx, ny = x + dx, y + dy
                    k = grid[ny][nx] if 0 <= nx < w and 0 <= ny < h else UNKNOWN
                    if k not in (UNKNOWN, WET) and (grid[y][x] != WET or k in (SEA, SHALLOW)):
                        seen[k] = seen.get(k, 0) + 1
            if seen:
                new.append((x, y, max(seen, key=seen.get)))
        for x, y, k in new:
            grid[y][x] = k
    for row in grid:
        for x, k in enumerate(row):
            if k in (UNKNOWN, WET):
                row[x] = SEA
    return grid


def smooth(grid, rounds=2):
    """Lone specks (left from the markers) take their neighbours' kind."""
    h, w = len(grid), len(grid[0])
    for _ in range(rounds):
        out = [row[:] for row in grid]
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                seen = {}
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if dx or dy:
                            k = grid[y + dy][x + dx]
                            seen[k] = seen.get(k, 0) + 1
                best = max(seen, key=seen.get)
                if seen.get(grid[y][x], 0) <= 1 and seen[best] >= 5:
                    out[y][x] = best
        grid = out
    return grid


def no_puddles(grid, least=40):
    """Water patches smaller than `least` map pixels inside the land (left from route lines) become land."""
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    for y0 in range(h):
        for x0 in range(w):
            if seen[y0][x0] or grid[y0][x0] not in (SEA, SHALLOW):
                continue
            part, stack, edge, around = [], [(x0, y0)], False, {}
            seen[y0][x0] = True
            while stack:
                x, y = stack.pop()
                part.append((x, y))
                edge = edge or x in (0, w - 1) or y in (0, h - 1)
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < w and 0 <= ny < h:
                        k = grid[ny][nx]
                        if k in (SEA, SHALLOW):
                            if not seen[ny][nx]:
                                seen[ny][nx] = True
                                stack.append((nx, ny))
                        else:
                            around[k] = around.get(k, 0) + 1
            if len(part) < least and not edge and around:
                land = max(around, key=around.get)
                for x, y in part:
                    grid[y][x] = land
    return grid


def pad(grid):
    """Open sea above and below; land touching the picture's top or bottom edge is worn into a coast."""
    rng = random.Random(7)
    w = len(grid[0])
    edge = [[SEA] * w for _ in range(PAD)]
    grid = [row[:] for row in grid]
    for x in range(w):                                    # a ragged coast instead of a cut
        bite = 3 + int(2.5 * (1 + __import__("math").sin(x / 9.0))) + rng.randint(0, 2)
        for y in range(bite):
            if grid[y][x] != SEA:
                grid[y][x] = SHALLOW if y == bite - 1 else SEA
        for y in range(len(grid) - 1, len(grid) - 1 - bite // 2, -1):
            if grid[y][x] != SEA:
                grid[y][x] = SEA
    return edge + grid + [row[:] for row in edge]


def paint(grid):
    h, w = len(grid), len(grid[0])
    small = pygame.Surface((w, h))
    for y, row in enumerate(grid):
        for x, k in enumerate(row):
            small.set_at((x, y), LOOK[k])
    big = pygame.transform.scale2x(pygame.transform.scale2x(small))
    W, H = big.get_size()
    rng = random.Random(11)
    out = big.copy()
    at = big.get_at
    land = (GRASS, FOREST, MOUNT, SAND)

    def k_of(x, y):
        return KEY.get(tuple(at((max(0, min(W - 1, x)), max(0, min(H - 1, y))))[:3]), SEA)

    for y in range(H):
        for x in range(W):
            k = k_of(x, y)
            if k in (SEA, SHALLOW):
                near = 0                                   # how close the nearest land is (surf, then shallows)
                for r in (2, 4, 7):
                    if any(k_of(x + dx, y + dy) in land for dx, dy in ((r, 0), (-r, 0), (0, r), (0, -r))):
                        near = r
                        break
                if near == 2:
                    out.set_at((x, y), (236, 244, 248))
                elif near == 4:
                    out.set_at((x, y), (120, 200, 236))
                elif k == SEA:
                    far = not any(k_of(x + dx, y + dy) in land or k_of(x + dx, y + dy) == SHALLOW
                                  for dx, dy in ((24, 0), (-24, 0), (0, 24), (0, -24)))
                    base = (30, 96, 184) if far else LOOK[SEA]
                    if (x * 7 + y * 13) % 97 == 0:          # glints on the waves
                        base = (96, 160, 232)
                    out.set_at((x, y), base)
            elif k == FOREST and rng.random() < 0.22:
                out.set_at((x, y), (40, 112, 48))
            elif k == GRASS and rng.random() < 0.05:
                out.set_at((x, y), (136, 208, 96))
            elif k == MOUNT:
                if any(k_of(x + dx, y + dy) != MOUNT for dx, dy in ((0, 1), (1, 0))):
                    out.set_at((x, y), (136, 104, 64))     # ridge shading on the slopes' south and east
                elif rng.random() < 0.08:
                    out.set_at((x, y), (200, 172, 120))
            elif k == SAND and rng.random() < 0.07:
                out.set_at((x, y), (214, 188, 112))
    return out


def main():
    pygame.init()
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    img = pygame.image.load(SRC)
    img = img.subsurface((0, 0, img.get_width() - 3, img.get_height())).copy()   # (its right edge is a grey frame)
    grid = pad(smooth(no_puddles(classify(img))))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    pygame.image.save(paint(grid), OUT)
    print("wrote", OUT, "pad", PAD * 4, "px above and below")


if __name__ == "__main__":
    main()
