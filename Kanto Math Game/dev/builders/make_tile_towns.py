"""Tile-built town backgrounds (Jordan, 10-30): Kalos towns drawn from Pokemon Journeys' Gen 5 tiles
(UnovaSummer + autotiles), each laid out from its XY map (assets/backgrounds/kalos/<town>.png) and
Jordan's notes on it. Every layout is confirmed with Jordan before it's built.
Ground is a letter grid (autotiles get proper edges, RPG Maker style); objects are stamps from the
tileset, and a few are made here (BUILT).

Superseded (Jordan, 10-30): Kalos towns now use the X/Y maps with their labels taken out
(dev/builders/clean_kalos_maps.py). Running this would overwrite those backgrounds in
assets/backgrounds/kalos/towns/<key>.png (1280 x 540); its full maps go to dev/builders/out/.

    python dev/builders/make_tile_towns.py [town ...]      (default: every town here)
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

pygame.init()
J = os.path.join("..", "..", "Pokemon Journeys V18", "Graphics") + "/"
SHEET = pygame.image.load(J + "Tilesets/UnovaSummer.png")
T = 32
# ground letters -> autotiles, drawn in this order (grass under everything)
AUTO = {"g": "Light grass", "p": "Brick path", "b": "Brick path", "c": "Brick path", "s": "Brick path", "w": "Lake"}


def full_colour(img):
    """A 32-bit copy (the sheets are palette images: a new colour would snap back to the palette)."""
    out = pygame.Surface(img.get_size(), pygame.SRCALPHA)
    out.blit(img, (0, 0))
    return out


AUTO_IMG = {k: full_colour(pygame.image.load(J + f"Autotiles/{v}.png").subsurface(pygame.Rect(0, 0, 96, 128)))
            for k, v in AUTO.items()}


def ramp(img, dark, light):
    """Recolour by brightness onto a ramp (keeps the pattern, changes the stone)."""
    for x in range(img.get_width()):
        for y in range(img.get_height()):
            c = img.get_at((x, y))
            if c.a:
                k = (0.299 * c.r + 0.587 * c.g + 0.114 * c.b) / 255
                img.set_at((x, y), tuple(int(dark[i] + (light[i] - dark[i]) * k) for i in range(3)) + (c.a,))
    return img


ramp(AUTO_IMG["p"], (110, 72, 48), (250, 222, 186))   # warm sandstone (Aquacorde)
ramp(AUTO_IMG["b"], (92, 40, 34), (214, 128, 104))    # red brick (Vaniville's garden paths)
ramp(AUTO_IMG["c"], (92, 96, 108), (236, 238, 242))   # grey cobbles (Vaniville's street)
ramp(AUTO_IMG["s"], (112, 76, 60), (232, 196, 164))   # rosy brick (Santalune's streets)
LUSH = ramp(full_colour(AUTO_IMG["g"]), (34, 92, 40), (150, 206, 104))  # a deeper, grassier green
# small things to scatter on grass: (x, y, w, h) in sheet pixels
TUFTS = [(0, 184, 32, 16), (32, 200, 32, 20), (64, 194, 32, 20), (112, 196, 32, 20)]
PLANTS = [(32, 224, 32, 32), (0, 256, 32, 32)]

# stamps: (col, row, w, h) on the sheet, in tiles
STAMP = {
    "tree": (2, 227, 2, 4),
    "house": (0, 326, 6, 7),
    "fountain": (0, 943, 5, 6),
    "cafe": (3, 976, 3, 4),
    "lamp": (0, 901, 1, 4),
    "bridge": (3, 868, 5, 8),
    "flowers": (0, 958, 4, 2),
    "bench": (0, 965, 3, 2),
    "tall_shop": (0, 466, 5, 7),     # navy roof, taller than wide
    "long_house": (0, 278, 7, 6),    # hip roof: widened and repainted navy for Aquacorde
    "orange_house": (0, 512, 6, 7),  # orange roof with dormers (Vaniville's row)
    "hedge_ring": (5, 961, 3, 4),
    "tall_hedge": (7, 983, 1, 3),
    "cliff": (0, 195, 4, 5),
    "pokemon_center": (0, 241, 7, 9),
}
GREEN_ROOF = ((30, 70, 40), (120, 190, 110))
BUILT = {}  # stamps made here: name -> Surface


def stamp_img(name):
    if name in BUILT:
        return BUILT[name]
    c, r, w, h = STAMP[name]
    return SHEET.subsurface(pygame.Rect(c * T, r * T, w * T, h * T))


def stamp_size(name):
    """(w, h) in tiles."""
    if name in BUILT:
        return BUILT[name].get_width() // T, BUILT[name].get_height() // T
    return STAMP[name][2], STAMP[name][3]


def widened(name, extra, mid):
    """A stamp made wider by repeating its column `mid` `extra` more times."""
    src = stamp_img(name)
    w, h = src.get_size()
    out = pygame.Surface((w + extra * T, h), pygame.SRCALPHA)
    out.blit(src, (0, 0), pygame.Rect(0, 0, (mid + 1) * T, h))
    for i in range(extra):
        out.blit(src, ((mid + 1 + i) * T, 0), pygame.Rect(mid * T, 0, T, h))
    out.blit(src, ((mid + 1 + extra) * T, 0), pygame.Rect((mid + 1) * T, 0, w - (mid + 1) * T, h))
    return out


def repaint_roof(img, roof_h, dark, light):
    """Orange roof tiles (the top roof_h pixels) onto another colour ramp; walls are left alone."""
    for x in range(img.get_width()):
        for y in range(min(roof_h, img.get_height())):
            c = img.get_at((x, y))
            if c.a and c.r > 120 and c.r - c.b > 90 and c.r > c.g + 30:
                k = (0.299 * c.r + 0.587 * c.g + 0.114 * c.b) / 255
                img.set_at((x, y), tuple(int(dark[i] + (light[i] - dark[i]) * k) for i in range(3)) + (c.a,))
    return img


def awning(img, y, x0=None, x1=None):
    """A red-and-white striped awning across a building's front at height y (pixels in the stamp)."""
    x0 = 6 if x0 is None else x0
    x1 = img.get_width() - T - 2 if x1 is None else x1
    for i, x in enumerate(range(x0, x1, 8)):
        colour = (204, 40, 46) if i % 2 == 0 else (246, 236, 230)
        pygame.draw.rect(img, colour, (x, y, min(8, x1 - x), 16))
        pygame.draw.circle(img, colour, (x + 4, y + 16), 4)   # the scalloped edge
    pygame.draw.line(img, (120, 24, 30), (x0, y), (x1 - 1, y), 2)
    return img


def bug_emblem():
    """The Kalos Bug Gym's sign: a half Poke Ball (its red dome) with a green triangle over it, on a plinth."""
    out = pygame.Surface((3 * T, 3 * T), pygame.SRCALPHA)
    cx, base = out.get_width() // 2, 3 * T - 14
    pygame.draw.rect(out, (120, 122, 132), (10, base, 3 * T - 20, 12), border_radius=3)
    pygame.draw.rect(out, (70, 72, 82), (10, base, 3 * T - 20, 12), 2, border_radius=3)
    dome = pygame.Rect(cx - 30, base - 30, 60, 60)
    pygame.draw.ellipse(out, (40, 40, 48), dome.inflate(6, 6))
    pygame.draw.ellipse(out, (214, 46, 52), dome)
    pygame.draw.rect(out, (0, 0, 0, 0), (0, base, out.get_width(), 40))           # only its top half
    pygame.draw.rect(out, (120, 122, 132), (10, base, 3 * T - 20, 12), border_radius=3)
    pygame.draw.rect(out, (70, 72, 82), (10, base, 3 * T - 20, 12), 2, border_radius=3)
    pygame.draw.line(out, (40, 40, 48), (cx - 33, base - 1), (cx + 33, base - 1), 5)
    pygame.draw.circle(out, (246, 246, 246), (cx, base - 4), 9)
    pygame.draw.circle(out, (40, 40, 48), (cx, base - 4), 9, 3)
    tri = [(cx, 6), (cx - 26, base - 34), (cx + 26, base - 34)]
    pygame.draw.polygon(out, (88, 176, 64), tri)
    pygame.draw.polygon(out, (34, 80, 34), tri, 4)
    return out


def draw_autotile(surf, img, x, y, same):
    """RPG Maker XP autotile: each 16px quarter picked from the 96x128 sheet by its neighbours.
    same(dx, dy) -> True if that neighbour is the same ground."""
    h = T // 2
    for qx, qy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        sx = -1 if qx == 0 else 1
        sy = -1 if qy == 0 else 1
        hor, ver, dia = same(sx, 0), same(0, sy), same(sx, sy)
        if hor and ver and dia:      # inside: the centre tile
            tx, ty = 1, 2
        elif hor and ver:            # inside corner
            src = pygame.Rect(64 + qx * h, qy * h, h, h)
            surf.blit(img, (x + qx * h, y + qy * h), src)
            continue
        elif not hor and not ver:    # outside corner
            tx, ty = (0 if qx == 0 else 2), (1 if qy == 0 else 3)
        elif ver:                    # a left/right edge
            tx, ty = (0 if qx == 0 else 2), 2
        else:                        # a top/bottom edge
            tx, ty = 1, (1 if qy == 0 else 3)
        src = pygame.Rect(tx * T + qx * h, ty * T + qy * h, h, h)
        surf.blit(img, (x + qx * h, y + qy * h), src)


LIP, FACE, SHADE = (246, 222, 188), (176, 124, 88), (120, 82, 58)


def wall(surf, points, raised=None):
    """A low sandstone wall through points (map pixels): a darker face under a light top, and a
    rounded joint at each bend, so a run can hook. raised: a rect (pixels) lightened as the upper level."""
    if raised:
        lift = pygame.Surface(raised.size, pygame.SRCALPHA)
        lift.fill((255, 246, 230, 46))
        surf.blit(lift, raised.topleft)
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        pygame.draw.line(surf, SHADE, (x0, y0 + 14), (x1, y1 + 14), 16)
        pygame.draw.line(surf, FACE, (x0, y0 + 8), (x1, y1 + 8), 14)
    for x, y in points:
        pygame.draw.circle(surf, SHADE, (x, y + 14), 8)
        pygame.draw.circle(surf, FACE, (x, y + 8), 7)
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        pygame.draw.line(surf, LIP, (x0, y0), (x1, y1), 10)
    for x, y in points:
        pygame.draw.circle(surf, LIP, (x, y), 5)


def stairs(surf, c0, c1, r0, r1):
    """Steps up to the raised half: light treads, dark risers."""
    for r in range(r0 * T, r1 * T, 8):
        pygame.draw.rect(surf, LIP, (c0 * T, r, (c1 - c0) * T, 5))
        pygame.draw.rect(surf, FACE, (c0 * T, r + 5, (c1 - c0) * T, 3))
    for c in (c0, c1):
        pygame.draw.rect(surf, SHADE, (c * T - 3, r0 * T, 6, (r1 - r0) * T))


def flower_bed(surf, points):
    """A flower bed in a wooden border, any shape (points in map pixels), planted with the two flower
    autotiles in turn."""
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    box = pygame.Rect(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
    bed = pygame.Surface(box.size, pygame.SRCALPHA)
    kinds = [pygame.image.load(J + f"Autotiles/Flowers{n}.png").subsurface((0, 0, T, T)) for n in (1, 2)]
    for y in range(0, box.h, T):
        for x in range(0, box.w, T):
            bed.blit(kinds[(x // T + y // T) % 2], (x, y))
    mask = pygame.Surface(box.size, pygame.SRCALPHA)
    local = [(x - box.x, y - box.y) for x, y in points]
    pygame.draw.polygon(mask, (255, 255, 255, 255), local)
    bed.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    pygame.draw.polygon(surf, (86, 58, 36), points)
    surf.blit(bed, box.topleft)
    pygame.draw.polygon(surf, (70, 44, 28), points, 6)
    pygame.draw.polygon(surf, (150, 104, 66), points, 2)


def stone_statue(sprite_path, size=2):
    """A Pokemon as a grey stone statue on a plinth (size tiles wide), from its battle sprite."""
    img = pygame.image.load(sprite_path).convert_alpha() if pygame.display.get_surface() else \
        full_colour(pygame.image.load(sprite_path))
    img = img.subsurface(img.get_bounding_rect()).copy()
    w = size * T
    h = int(img.get_height() * w / img.get_width())
    img = ramp(full_colour(pygame.transform.scale(img, (w, h))), (70, 72, 82), (214, 216, 222))
    plinth_h = 18
    rows = -(-(h + plinth_h) // T)
    out = pygame.Surface((w, rows * T), pygame.SRCALPHA)
    top = rows * T - plinth_h
    out.blit(img, (0, top - h + 6))
    pygame.draw.rect(out, (120, 122, 132), (2, top, w - 4, plinth_h), border_radius=3)
    pygame.draw.rect(out, (176, 178, 188), (2, top, w - 4, 6), border_radius=3)
    pygame.draw.rect(out, (70, 72, 82), (2, top, w - 4, plinth_h), 2, border_radius=3)
    return out


def scatter(surf, ground, seed, tufts=0.22, plants=0.04):
    """Grass tufts and a few flowering plants over the open grass (a fixed seed: the same each build)."""
    import random
    rnd = random.Random(seed)
    for r, row in enumerate(ground):
        for c, ch in enumerate(row):
            if ch != "g":
                continue
            x, y = c * T + rnd.randrange(-6, 7), r * T + rnd.randrange(-6, 7)
            roll = rnd.random()
            if roll < plants:
                surf.blit(SHEET, (x, y), pygame.Rect(rnd.choice(PLANTS)))
            elif roll < plants + tufts:
                surf.blit(SHEET, (x, y + 8), pygame.Rect(rnd.choice(TUFTS)))


def render(ground, objects, extra=None, grass=None):
    """grass: another grass autotile under everything (LUSH), else the light grass."""
    rows, cols = len(ground), len(ground[0])
    surf = pygame.Surface((cols * T, rows * T), pygame.SRCALPHA)
    for layer in AUTO:
        for r in range(rows):
            for c in range(cols):
                ch = ground[r][c]
                if layer == "g" or ch == layer:
                    def same(dx, dy, ch=layer):
                        rr, cc = r + dy, c + dx
                        if not (0 <= rr < rows and 0 <= cc < cols):
                            return True
                        return ch == "g" or ground[rr][cc] == ch
                    img = grass if layer == "g" and grass is not None else AUTO_IMG[layer]
                    draw_autotile(surf, img, c * T, r * T, same)
    if extra:
        extra(surf)
    for name, c, r in sorted(objects, key=lambda o: o[2] + stamp_size(o[0])[1]):
        surf.blit(stamp_img(name), (c * T, r * T))
    return surf


def save(img, key):
    """The full map for checking, and the town background the game uses (assets/backgrounds/kalos/towns, picked
    first): 1280 x 540, filling the width (a little of the top and bottom trimmed)."""
    os.makedirs("dev/builders/out", exist_ok=True)
    pygame.image.save(img, f"dev/builders/out/{key}_tiles_raw.png")
    k = 1280 / img.get_width()
    sm = pygame.transform.smoothscale(img, (1280, round(img.get_height() * k)))
    framed = pygame.Surface((1280, 540))
    framed.blit(sm, (0, (540 - sm.get_height()) // 2))
    out = f"assets/backgrounds/kalos/towns/{key}.png"
    pygame.image.save(framed, out)
    print("ok", key, img.get_size(), round(k, 3), out)


# ---------------------------------------------------------------------------------------------------
def aquacorde():
    """Aquacorde Town: the forest, the river and its wide bridge, then a walled plaza. The north half:
    two tall shops either side of the fountain and its grass beds. A wall crosses the middle, hooking up
    toward the centre where stairs climb to the raised south half: café tables and two long buildings
    either side of the path out."""
    BUILT["long_shop"] = repaint_roof(widened("long_house", 3, 3), 3 * T, (24, 32, 70), (96, 118, 180))
    W, H = 68, 30
    P0, P1 = 17, 51            # the plaza's columns
    g = [["g"] * W for _ in range(H)]
    for r in range(3, 8):
        for c in range(W):
            g[r][c] = "w"
    for r in range(9, H - 1):
        for c in range(P0, P1):
            g[r][c] = "p"
    for r in list(range(0, 3)) + [8, H - 1]:
        for c in range(32, 36):
            g[r][c] = "p"
    for r in range(10, 15):    # the grass beds by the fountain
        for c in (28, 29, 38, 39):
            g[r][c] = "g"
    objs = [("bridge", 31, 1)]
    for c in range(0, W, 2):   # the forest: north of the river, and both sides of the plaza
        if not 29 <= c <= 37:
            objs.append(("tree", c, -2))
    for r in range(7, H, 3):
        for c in list(range(0, P0 - 1, 2)) + list(range(P1 + 1, W, 2)):
            objs.append(("tree", c, r))
    objs += [("tall_shop", 20, 9), ("tall_shop", 43, 9), ("fountain", 31, 9),
             ("lamp", 30, 5), ("lamp", 36, 5), ("lamp", 26, 10), ("lamp", 41, 10),
             ("cafe", 19, 19), ("cafe", 23, 19), ("cafe", 41, 19), ("cafe", 45, 19),
             ("lamp", 31, 19), ("lamp", 36, 19),
             ("long_shop", 18, 22), ("long_shop", 39, 22),
             ("flowers", 26, 8), ("flowers", 38, 8)]

    def walls(surf):
        """The wall across the plaza: straight from each side, then hooking up and round toward the stairs."""
        y = 17 * T + 8
        left = [(P0 * T, y), (28 * T, y), (29 * T + 8, y - 12), (29 * T + 16, 15 * T + 16), (30 * T, 14 * T + 20),
                (31 * T, 14 * T + 16), (31 * T + 16, 15 * T + 8)]
        right = [(P1 * T - (x - P0 * T), yy) for x, yy in left]
        wall(surf, left, pygame.Rect(P0 * T, y + 20, (P1 - P0) * T, (H - 1) * T - y - 20))
        wall(surf, right)
        stairs(surf, 32, 36, 17, 19)

    save(render(g, objs, walls), "aquacorde_town")


def vaniville():
    """Vaniville Town: a row of three orange-roofed homes across the top, joined by an archway in the
    middle that leads north to Route 1 (the only way out): one wide home left of it, yours and then the
    rival's right of it. The whole block stands on cobbles; each home has a walled front garden (planted
    beds, a brick path to the street), and a Rhyhorn statue stands before the tall tree in yours. Below,
    one wide cobbled street that widens into a V to the south, with two triangular flower beds either side
    of the middle and street lamps; big trees in rings of hedge in the lower corners. Cliffs close the
    town in along the top and sides, over deep grass."""
    W, H = 68, 30
    LEFT, YOURS, RIVAL = 20, 37, 42         # left edges of the homes (the left one is 10 wide)
    HOMES = {LEFT: 10, YOURS: 5, RIVAL: 5}
    DOOR = 2                                # the door's column in each home
    house = stamp_img("orange_house")      # the wide home: two roof sections, one front door
    wide = pygame.Surface((house.get_width() + 5 * T, house.get_height()), pygame.SRCALPHA)
    wide.blit(house, (5 * T, 0))
    wide.blit(house, (0, 0), pygame.Rect(0, 0, 5 * T, house.get_height()))
    wall_h = house.get_height() - 5 * T    # the second door bricked up, a window in its place
    wide.blit(house, ((5 + DOOR) * T, 5 * T), pygame.Rect(0, 5 * T, T, wall_h))
    BUILT["wide_home"] = wide
    arch = widened("orange_house", 2, 2)    # the archway: a gate cut through a stretched home
    gate = pygame.Rect(3 * T - 8, 4 * T + 6, 2 * T + 16, 3 * T - 6)
    pygame.draw.rect(arch, (64, 58, 66), gate, border_top_left_radius=30, border_top_right_radius=30)
    pygame.draw.rect(arch, (150, 120, 92), gate, 5, border_top_left_radius=30, border_top_right_radius=30)
    BUILT["archway"] = arch
    BUILT["rhyhorn"] = stone_statue("assets/sprites/pokemon/111.png")
    ring = stamp_img("hedge_ring")          # a big tree standing in a ring of hedge
    ringed = pygame.Surface((ring.get_width(), ring.get_height() + 2 * T), pygame.SRCALPHA)
    ringed.blit(ring, (0, 2 * T))
    ringed.blit(stamp_img("tree"), ((ring.get_width() - 2 * T) // 2, T + 8))
    BUILT["ringed_tree"] = ringed

    g = [["g"] * W for _ in range(H)]
    for r in range(0, 16):                  # the way north, through the archway
        for c in range(32, 36):
            g[r][c] = "c"
    for r in range(3, 16):                  # the cobbled block under the homes and gardens
        for c in range(LEFT - 1, RIVAL + 6):
            g[r][c] = "c"
    for r in range(15, 20):                 # the street
        for c in range(10, 58):
            g[r][c] = "c"
    for r in range(20, 28):                 # widening into a V to the south
        k = (r - 19) * 2.6
        for c in range(int(10 + k), int(58 - k)):
            g[r][c] = "c"
    beds = []                               # each garden's planted beds, either side of its path
    for c, w in HOMES.items():
        for r in range(9, 14):
            g[r][c + DOOR] = "b"
        beds += [(c + 0, c + DOOR), (c + DOOR + 1, c + w)]
    for c0, c1 in beds:
        for r in range(10, 14):
            for c in range(c0 + (c0 == min(HOMES)) * 0, c1):
                g[r][c] = "g"

    # left to right, each covering its neighbour's shadow so the row reads as one block
    objs = [("wide_home", LEFT, 2), ("archway", 30, 2), ("orange_house", YOURS, 2), ("orange_house", RIVAL, 2)]
    objs += [("tree", LEFT, 9), ("tall_hedge", LEFT + 3, 10), ("tree", LEFT + 4, 9), ("tall_hedge", LEFT + 6, 10),
             ("tree", LEFT + 7, 9)]
    objs += [("tall_hedge", YOURS, 10), ("tall_hedge", YOURS + 1, 10), ("tree", YOURS + 3, 8),
             ("rhyhorn", YOURS + 3, 11)]
    objs += [("tree", RIVAL, 9), ("tall_hedge", RIVAL + 3, 10), ("tall_hedge", RIVAL + 4, 10)]
    objs += [("lamp", 12, 15), ("lamp", 55, 15), ("lamp", 20, 18), ("lamp", 47, 18),
             ("lamp", 29, 24), ("lamp", 38, 24)]
    for c, r in ((3, 20), (12, 23), (63, 20), (54, 23)):
        objs.append(("ringed_tree", c, r))
    # the cliffs closing the town in: along the top (behind the homes) and down both sides
    for c in range(0, W, 4):
        if not 28 <= c <= 36:
            objs.append(("cliff", c, -2))
    for r, cols in ((2, (0, 4, 8, 12, 16)), (6, (0, 4, 8, 12)), (10, (0, 4)), (14, (0,)), (18, (-2,))):
        for c in cols:
            objs += [("cliff", c, r), ("cliff", W - 4 - c, r)]
    objs += [("tree", 9, 11), ("tree", 13, 10), ("tree", 5, 15), ("tree", 57, 11), ("tree", 53, 10), ("tree", 61, 15),
             ("tree", 16, 23), ("tree", 50, 23), ("tree", 7, 26), ("tree", 59, 26)]

    def extra(surf):
        scatter(surf, g, seed=7)
        for c, w in HOMES.items():          # each garden's low wall, open where its path meets the street
            x0, x1, y0, y1 = c * T + 6, (c + w) * T - 6, 9 * T, 14 * T + 10
            wall(surf, [(x0, y0), (x0, y1), ((c + DOOR) * T - 6, y1)])
            wall(surf, [((c + DOOR + 1) * T + 6, y1), (x1, y1), (x1, y0)])
        mid = 34 * T
        flower_bed(surf, [(mid - 9 * T, 17 * T), (mid - T, 17 * T), (mid - T, 22 * T)])
        flower_bed(surf, [(mid + T, 17 * T), (mid + 9 * T, 17 * T), (mid + T, 22 * T)])

    save(render(g, objs, extra, grass=LUSH), "vaniville_town")


def santalune():
    """Santalune City: a round fountain plaza in the middle, rosy brick streets out from it in a grid.
    The Trainers' School (red-brown roof) just above the fountain, facing south onto it; the Gym in the
    top-right corner (green roof) with the Bug Gym's emblem in front; top left a large green-roofed
    building with a red awning along its south wall. Shops with green roofs and red awnings in pairs both
    sides of the plaza; the Pokemon Center lower right of the fountain beside another shop. Flower fields
    across the top, a long flower bed and a wall along the bottom, trees outside. The only ways out: north
    between the two flower fields, east by the Gym, south below the Pokemon Center."""
    W, H = 76, 36
    BUILT["shop"] = awning(repaint_roof(full_colour(stamp_img("orange_house")), 7 * T, *GREEN_ROOF), 4 * T + 26)
    BUILT["school"] = widened("long_house", 3, 3)
    BUILT["gym"] = repaint_roof(full_colour(widened("long_house", 4, 3)), 3 * T, *GREEN_ROOF)
    BUILT["hall"] = awning(repaint_roof(full_colour(widened("orange_house", 2, 3)), 7 * T, *GREEN_ROOF),
                           4 * T + 26)
    BUILT["bug_emblem"] = pygame.transform.scale(bug_emblem(), (4 * T, 4 * T))

    g = [["g"] * W for _ in range(H)]

    def street(c0, c1, r0, r1):
        for r in range(r0, r1):
            for c in range(c0, c1):
                g[r][c] = "s"

    street(24, 28, 0, 11)        # north, between the flower fields
    street(14, W, 9, 11)         # the top street, out east by the Gym
    street(20, 23, 9, 30)        # the west street
    street(44, 48, 9, 30)        # the middle street, through the fountain plaza
    street(69, 72, 9, 20)        # the east street
    street(20, 72, 18, 20)       # across the middle
    street(20, 70, 28, 30)       # along the bottom
    street(57, 61, 28, H)        # south, below the Pokemon Center
    street(40, 52, 11, 15)       # the school's forecourt
    street(5, 15, 11, 17)        # the yard before the top-left hall

    objs = [("hall", 4, 4), ("cafe", 5, 12), ("cafe", 10, 12),
            ("school", 39, 4), ("gym", 62, 2), ("bug_emblem", 56, 5),
            ("shop", 25, 11), ("shop", 30, 11), ("shop", 60, 11), ("shop", 65, 11),
            ("shop", 25, 21), ("shop", 30, 21), ("pokemon_center", 55, 19), ("shop", 64, 21),
            ("fountain", 43, 16),
            ("lamp", 52, 25), ("lamp", 62, 25), ("lamp", 41, 8), ("lamp", 52, 8)]
    for c in list(range(0, 18, 3)) + list(range(73, W, 3)):     # trees outside the walls
        for r in range(17, H, 4):
            objs.append(("tree", c, r))
    for c in range(18, 72, 3):
        if not 55 <= c <= 61:
            objs.append(("tree", c, 32))
    for c in (0, 3, 50, 53, 56):
        objs.append(("tree", c, -1))

    def extra(surf):
        scatter(surf, g, seed=11)
        cx, cy = 46 * T, 19 * T + 8                                 # the round plaza
        pygame.draw.circle(surf, (150, 120, 104), (cx, cy), 4 * T + 12)
        pygame.draw.circle(surf, (226, 200, 176), (cx, cy), 4 * T + 2)
        pygame.draw.circle(surf, (196, 166, 144), (cx, cy), 3 * T, 6)
        for x0 in (8 * T, 30 * T):                                  # the flower fields
            flower_bed(surf, [(x0, 0), (x0 + 13 * T, 0), (x0 + 13 * T, 6 * T), (x0, 6 * T)])
        flower_bed(surf, [(21 * T, 30 * T + 8), (56 * T, 30 * T + 8), (56 * T, 31 * T + 20), (21 * T, 31 * T + 20)])
        flower_bed(surf, [(62 * T, 30 * T + 8), (71 * T, 30 * T + 8), (71 * T, 31 * T + 20), (62 * T, 31 * T + 20)])
        wall(surf, [(19 * T, 12 * T), (19 * T, 32 * T), (57 * T, 32 * T)])   # the town wall, open to the south
        wall(surf, [(61 * T, 32 * T), (73 * T, 32 * T), (73 * T, 12 * T)])

    save(render(g, objs, extra, grass=LUSH), "santalune_city")


TOWNS = {"aquacorde": aquacorde, "vaniville": vaniville, "santalune": santalune}

if __name__ == "__main__":
    for name in sys.argv[1:] or list(TOWNS):
        TOWNS[name]()
