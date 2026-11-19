"""The giant Soaring world (Jordan, 11-18): Hoenn, Johto, Kanto, the Sevii Islands and the Orange Islands as one ground to
fly over, placed as Jordan's world map has them (assets/world_map 2.png; "the islands can be made larger ... but the
relative position should be the same as the world map"; "the sizing can remain or change if needed").

How it's made:
1. The world map is cut to the five regions (CROP) and blown up to the regions' own town-map size (K = 1 / 0.46875:
   Hoenn's picture sits in the world map at 0.469 of its size), so Hoenn keeps today's size and places.
2. Each region's own town map (assets/region_maps/<region>.png, much finer than the world map) is pasted where it was
   found in the world map (PLACES: matched picture against picture, 11-18). Island regions first wipe the world map's
   own drawing of them, so nothing shows twice. The land between and around them is the world map's.
3. Then the same drawing as Hoenn's old ground (make_soaring_ground.py: sea / shallows / grass / forest / mountain / sand,
   route lines and markers painted out, 4x, surf and ridges), done with numpy here because the world is 14 Hoenns big.
4. Cut for the phone (Jordan's game runs in Pydroid): the full picture and its half in 512-pixel tiles, read only near
   you; its quarter and eighth whole.
5. Who can see what: every town on the five maps is a "seed"; each patch of ground belongs to its nearest town (within
   REACH, else it's no town's: open sea far from everyone). The flight covers a patch in clouds until you've been to its
   town (src/world/soaring3d.py). Saved as cells.png (the town's number per pixel, 255 = no town's).

    python dev/builders/make_soaring_world.py                  (from the game folder; needs numpy; ~20 seconds)
    python dev/builders/make_soaring_world.py --layout=dusk    (the second world, from duskl1ghtness's map)
    (add --compose to write just the pasted-together picture, _compose.png, to check the places)
Writes assets/soaring3d/world/ (or world_dusk/): t0_<col>_<row>.png, t1_<col>_<row>.png, w2.png, w3.png, cells.png,
world.json. Which one the flight uses: src/world/soaring3d.py WORLD.
"""
import json
import os
import sys

import numpy as np
import pygame

sys.path.insert(0, os.path.dirname(__file__))
import make_soaring_ground as G   # noqa: E402  (its colour sorting and clean-ups)

# The worlds to build (Jordan, 11-18: his world map, and a second one from duskl1ghtness's map to compare). Each:
#   src   - the world map picture; crop - the part kept (its pixels); k - its pixels -> town-map pixels (so that
#           Hoenn's town map is its own size: Hoenn's place's scale x k = 1);
#   places - where each region's town map goes: (region, x, y, sx, sy): its picture's pixel (0, 0) at (x, y) on the
#           world map, sx / sy of the world map's pixels per picture pixel. Pasted in this order;
#   wipe  - the world map's own drawing of a region, wiped to sea first (its pixels: x0, y0, x1, y1);
#   land_only - regions whose own map goes on without its sea (islands near another region's coast);
#   cut   - region: keep only this many pixels of its picture's width (Johto's shows Kanto's west edge too);
#   base  - "dusk": the world map is drawn in other colours (sorted into ours first, dusk_colours).
LAYOUTS = {
    # Pokemon Journeys' world map (the game's own, assets/world_map 2.png): places matched picture against picture
    "journeys": dict(
        src=os.path.join("assets", "world_map 2.png"), out="world", crop=(540, 790, 1300, 1280), k=480 / 225,
        places=[("HOENN", 595, 876, 225 / 480, 225 / 480), ("JOHTO", 811, 885, 220 / 480, 220 / 480),
                ("KANTO", 1011, 870, 216 / 480, 216 / 480), ("ORANGE", 795, 1059, 273 / 480, 273 / 480),
                ("SEVII", 1014, 1037, 240 / 480, 240 / 480)],
        wipe={"ORANGE": (790, 1012, 1012, 1270), "SEVII": (1012, 1030, 1262, 1205)},
        land_only=set(), cut={}, base=None),
    # duskl1ghtness's "Pokemon World Map" (DeviantArt, 2025; its regions after Niknaks93's maps), the 1280 x 831 view:
    # places fitted to its towns (Hoenn: Rustboro, Mossdeep, Fortree, Dewford; Johto with Kanto as one, from Cianwood to
    # Lavender, Journeys' own Johto-Kanto join; Orange to its islands' spread; Sevii: One, Five, Six, Seven Island)
    "dusk": dict(
        src=os.path.join("..", "..", "sources", "world_maps", "duskl1ghtness",
                         "pokemon_world_map_by_duskl1ghtness_fullview.jpg"),
        out="world_dusk", crop=(150, 340, 960, 725), k=1 / 0.354,
        places=[("HOENN", 162.3, 602.9, 0.354, 0.354), ("JOHTO", 453.0, 368.0, 0.277, 0.277),
                ("KANTO", 453.0 + 448 * 0.277, 368.0 + 7 * 0.277, 0.277, 0.277),
                ("ORANGE", 444.4, 489.4, 0.48, 0.48), ("SEVII", 600.4, 426.5, 0.95, 0.75)],
        wipe={"ORANGE": (474, 486, 628, 652), "SEVII": (695, 436, 948, 642)},
        land_only={"ORANGE", "SEVII"}, cut={"JOHTO": 448}, base="dusk",
        # Hoenn's town map shows the south edge of Orre (the Journeys world joins them) above the channel north of
        # Fortree and Lilycove: on this map Hoenn is an island, so that strip is sea
        sea_over={"HOENN": [(155, 0), (155, 36), (240, 36), (280, 41), (320, 49), (360, 61), (400, 79), (440, 79),
                            (480, 89), (480, 0)]}),
}
LAYOUT = LAYOUTS["journeys"]
REGIONS = ["HOENN", "JOHTO", "KANTO", "ORANGE", "SEVII"]
FRAME = 3                                # the town maps' grey frame on the right edge
TILE = 512
REACH = 150                              # town-map pixels: farther than this from every town is no town's
CELL = 2                                 # cells.png: one pixel per 2 x 2 town-map pixels
SCALE = 88.4                             # world units per town-map pixel (soaring3d.MAP_SCALE: Hoenn's)
HOENN_X0, HOENN_Z0 = -13391.0, -12234.0  # Hoenn's town-map pixel (0, 0) in world units (soaring3d.MAP_X0 / MAP_Z0)
# make_soaring_ground's colours for each kind (what its classify() reads back): dusk_colours paints the world map in them
CANON = {G.SEA: (40, 112, 200), G.SHALLOW: (72, 190, 224), G.GRASS: (112, 192, 80), G.FOREST: (64, 148, 64),
         G.MOUNT: (180, 160, 100), G.SAND: (232, 212, 110), G.UNKNOWN: (255, 0, 255)}


def dusk_colours(img):
    """duskl1ghtness's map sorted into our kinds, in the colours classify() reads: its sea blue, two greens, the orange
    and brown mountain tiers, the desert's yellow; white routes, snow, markers and writing are left to be filled in."""
    a = pygame.surfarray.array3d(img).astype(np.int16)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    out = np.zeros(a.shape, np.uint8)
    out[:] = CANON[G.UNKNOWN]
    water = (b > r + 50) & (b >= g - 10)
    green = (g > r + 30) & (g >= b) & ~water
    sand = (r > 190) & (g > 165) & (b < 110)
    mount = (r > g + 25) & (r > 130) & ~sand
    out[water] = CANON[G.SEA]
    out[green & (g >= 182)] = CANON[G.GRASS]
    out[green & (g < 182)] = CANON[G.FOREST]
    out[mount] = CANON[G.MOUNT]
    out[sand] = CANON[G.SAND]
    s = pygame.Surface(img.get_size())
    pygame.surfarray.blit_array(s, out)
    return s


def no_water(pic):
    """The picture's land only: its sea and shallows see-through (an island region pasted near another's coast)."""
    pic = pic.convert_alpha()
    a = pygame.surfarray.array3d(pic).astype(np.int16)
    water = (a[:, :, 2] > a[:, :, 0] + 40) & (a[:, :, 2] >= a[:, :, 1] - 25)
    alpha = pygame.surfarray.pixels_alpha(pic)
    alpha[water] = 0
    del alpha
    return pic


def compose():
    """The world in town-map pixels: the world map blown up, each region's own map on its spot. Returns the picture
    and each region's (left, top, sx, sy) on it."""
    L = LAYOUT
    K = L["k"]
    world = pygame.image.load(L["src"]).convert()
    if L["base"] == "dusk":
        world = dusk_colours(world)
    cx0, cy0, cx1, cy1 = L["crop"]
    sea = world.get_at((cx0 + 20, cy1 - 20))
    w, h = int(round((cx1 - cx0) * K)), int(round((cy1 - cy0) * K))
    canvas = pygame.transform.scale(world.subsurface((cx0, cy0, cx1 - cx0, cy1 - cy0)), (w, h))
    for a, b, c, d in L["wipe"].values():
        canvas.fill(sea, (int((a - cx0) * K), int((b - cy0) * K), int((c - a) * K), int((d - b) * K)))
    places = {}
    for region, x, y, sx, sy in L["places"]:
        pic = pygame.image.load(os.path.join("assets", "region_maps", region.lower() + ".png"))
        pw = min(pic.get_width() - FRAME, L["cut"].get(region, 10 ** 6))
        pic = pic.subsurface((0, 0, pw, pic.get_height())).copy()
        if region in L.get("sea_over", {}):
            pygame.draw.polygon(pic, (39, 168, 194), L["sea_over"][region])
        fx, fy = sx * K, sy * K
        if abs(fx - 1) < 0.01 and abs(fy - 1) < 0.01:
            fx = fy = 1.0                       # (Hoenn: exactly its own size, so its places stay where they are)
        else:
            pic = pygame.transform.scale(pic, (int(round(pic.get_width() * fx)), int(round(pic.get_height() * fy))))
        if region in L["land_only"]:
            pic = no_water(pic)
        left, top = int(round((x - cx0) * K)), int(round((y - cy0) * K))
        canvas.blit(pic, (left, top))
        places[region] = (left, top, fx, fy)
    return canvas, places


def no_routes(canvas):
    """Route lines and town markers painted out before sorting: each of their pixels takes the colour of the nearest
    pixel that isn't one (spreading in from both sides), so a wide route block in Orre's desert becomes desert and a
    route across the sea becomes sea (Jordan, 11-18: make_soaring_ground's rule turned Orre's route blocks to water)."""
    a = pygame.surfarray.array3d(canvas).astype(np.int16)
    r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    route = (r > 195) & (g >= 130) & (g <= 206) & (b < 150) & (r - g > 28)
    marker = ((r > 200) & (g < 140)) | ((b > 200) & (r < 140) & (g < 170)) | ((r > 215) & (g > 215) & (b > 215))
    todo = route | marker
    for _ in range(2):                                  # (and the blended pixels round each line: never copied from)
        grown = todo.copy()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            grown |= shift(todo, dx, dy, False)
        todo = grown
    for _ in range(400):
        if not todo.any():
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            src_ok = shift(~todo, dx, dy, False)
            take = todo & src_ok
            if take.any():
                moved = np.stack([shift(a[:, :, c], dx, dy, 0) for c in range(3)], axis=2)
                a[take] = moved[take]
                todo &= ~take
    pygame.surfarray.blit_array(canvas, a.astype(np.uint8))
    return canvas


def classes(canvas, places):
    grid = G.smooth(G.no_puddles(G.classify(no_routes(canvas))))
    # Sevii's town map has a big pale oval of decoration: open water there is sea, not shallows
    left, top, fx, fy = places["SEVII"]
    w, h = int(477 * fx), int(320 * fy)
    land = (G.GRASS, G.FOREST, G.MOUNT, G.SAND)
    arr = np.array(grid, dtype=np.uint8)
    near = np.zeros_like(arr, dtype=bool)
    isl = np.isin(arr, land)
    for dy in range(-6, 7):
        for dx in range(-6, 7):
            near |= np.roll(np.roll(isl, dy, 0), dx, 1)
    box = np.zeros_like(near)
    box[top:top + h, left:left + w] = True
    arr[box & (arr == G.SHALLOW) & ~near] = G.SEA
    return no_slivers(arr)


def opening(m, axis, n):
    """m with every run along `axis` (0 = down, 1 = across) shorter than n taken out."""
    er = m.copy()
    for i in range(n):
        er &= shift(m, i if axis == 1 else 0, i if axis == 0 else 0, False)
    out = er.copy()
    for i in range(n):
        out |= shift(er, -i if axis == 1 else 0, -i if axis == 0 else 0, False)
    return out


def no_slivers(arr, keep=30):
    """The sea routes' lines leave one-pixel strips of land beside where they ran (both edges of the line): land not
    inside any 3 x 3 block of land becomes sea. Small islands (under `keep` pixels) are left whole."""
    land = np.isin(arr, (G.GRASS, G.FOREST, G.MOUNT, G.SAND))
    er = land.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            er &= shift(land, dx, dy, False)
    opened = er.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            opened |= shift(er, dx, dy, False)
    gone = land & ~opened
    h, w = arr.shape
    small = np.zeros_like(land)
    seen = np.zeros_like(land)
    for y0, x0 in zip(*np.nonzero(land & ~er)):        # (small islands have no 3 x 3 inside, or hardly any)
        if seen[y0, x0]:
            continue
        part, stack = [], [(y0, x0)]
        seen[y0, x0] = True
        while stack and len(part) <= keep:
            y, x = stack.pop()
            part.append((y, x))
            for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= ny < h and 0 <= nx < w and land[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        if len(part) <= keep and not stack:
            for y, x in part:
                small[y, x] = True
    out = arr.copy()
    out[gone & ~small] = G.SEA
    # straight strips a few pixels thick and long (a wider route line's edges): sea too
    land = np.isin(out, (G.GRASS, G.FOREST, G.MOUNT, G.SAND))
    for thick_ax, long_ax in ((0, 1), (1, 0)):
        thin = land & ~opening(land, thick_ax, 6)
        strip = thin & opening(thin, long_ax, 12)
        out[strip] = G.SEA
    # (and the lines' pale insides: shallows not inside any 3 x 3 block of shallows)
    sh = out == G.SHALLOW
    er = sh.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            er &= shift(sh, dx, dy, False)
    opened = er.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            opened |= shift(er, dx, dy, False)
    out[sh & ~opened] = G.SEA
    return out


def shift(a, dx, dy, fill):
    """a moved by (dx, dy): out[y, x] = a[y + dy, x + dx], the edge filled with `fill`."""
    out = np.full_like(a, fill)
    h, w = a.shape
    ys, yd = (slice(dy, h), slice(0, h - dy)) if dy >= 0 else (slice(0, h + dy), slice(-dy, h))
    xs, xd = (slice(dx, w), slice(0, w - dx)) if dx >= 0 else (slice(0, w + dx), slice(-dx, w))
    out[yd, xd] = a[ys, xs]
    return out


def paint(arr):
    """make_soaring_ground.paint's look, with numpy: 4x (scale2x twice), surf, shallows, deep water, glints, tree clumps,
    ridges. Returns an (H, W, 3) uint8 array."""
    h, w = arr.shape
    small = pygame.Surface((w, h))
    pal = np.zeros((8, 3), np.uint8)
    for k, c in G.LOOK.items():
        pal[k] = c
    pygame.surfarray.blit_array(small, pal[arr].transpose(1, 0, 2))
    big = pygame.transform.scale2x(pygame.transform.scale2x(small))
    rgb = pygame.surfarray.array3d(big).transpose(1, 0, 2)
    H, W = rgb.shape[:2]
    k = np.full((H, W), G.SEA, np.uint8)
    for kind, c in G.LOOK.items():
        k[(rgb[:, :, 0] == c[0]) & (rgb[:, :, 1] == c[1]) & (rgb[:, :, 2] == c[2])] = kind
    land = np.isin(k, (G.GRASS, G.FOREST, G.MOUNT, G.SAND))
    water = ~land
    out = rgb.copy()

    def any_dir(m, r):
        return shift(m, r, 0, False) | shift(m, -r, 0, False) | shift(m, 0, r, False) | shift(m, 0, -r, False)

    n2, n4, n7 = any_dir(land, 2), any_dir(land, 4), any_dir(land, 7)
    sea = water & (k == G.SEA)
    far = sea & ~n7 & ~any_dir(land | (k == G.SHALLOW), 24)
    out[sea & ~n7 & ~far] = G.LOOK[G.SEA]
    out[far] = (30, 96, 184)
    yy, xx = np.mgrid[0:H, 0:W]
    out[sea & ~n4 & ((xx * 7 + yy * 13) % 97 == 0)] = (96, 160, 232)
    out[water & n4 & ~n2] = (120, 200, 236)
    out[water & n2] = (236, 244, 248)
    rng = np.random.default_rng(11)
    r = rng.random((H, W))
    out[(k == G.FOREST) & (r < 0.22)] = (40, 112, 48)
    out[(k == G.GRASS) & (r < 0.05)] = (136, 208, 96)
    mount = k == G.MOUNT
    ridge = mount & ((shift(k, 0, 1, G.MOUNT) != G.MOUNT) | (shift(k, 1, 0, G.MOUNT) != G.MOUNT))
    out[mount & ~ridge & (r < 0.08)] = (200, 172, 120)
    out[ridge] = (136, 104, 64)
    out[(k == G.SAND) & (r < 0.07)] = (214, 188, 112)
    return out


def surface(a):
    s = pygame.Surface((a.shape[1], a.shape[0]))
    pygame.surfarray.blit_array(s, a.transpose(1, 0, 2))
    return s


def seeds(places):
    with open(os.path.join("assets", "map_points.json"), encoding="utf-8") as f:
        pts = json.load(f)["region_maps"]
    out = []
    for region, (left, top, fx, fy) in places.items():
        for key, (px, py) in (pts.get(region) or {}).get("points", {}).items():
            if region in LAYOUT["cut"] and px >= LAYOUT["cut"][region]:
                continue                        # (Johto's picture's Kanto edge: those points are Kanto's)
            out.append([key, region, round(left + px * fx, 1), round(top + py * fy, 1)])
    return out


SEA_OF = 200   # cells.png: 200 + n = open sea nearest the n-th region (REGIONS), far from its towns


def cells(seed_list, arr):
    """Each cell's town (its seed's number), if within REACH of it. Farther: open sea goes with the nearest town's region
    (SEA_OF + its number: clear once you've been anywhere in that region, so you can fly from one region you know to
    the next across the sea); far land (other continents) is no one's (255: always under cloud)."""
    h, w = arr.shape
    cw, ch = (w + CELL - 1) // CELL, (h + CELL - 1) // CELL
    yy, xx = np.mgrid[0:ch, 0:cw]
    xx, yy = xx * CELL + CELL / 2, yy * CELL + CELL / 2
    best = np.full((ch, cw), 1e12)
    idx = np.full((ch, cw), 255, np.uint8)
    for i, (_k, _r, sx, sy) in enumerate(seed_list):
        d = (xx - sx) ** 2 + (yy - sy) ** 2
        m = d < best
        best[m] = d[m]
        idx[m] = i
    far = best > REACH ** 2
    region_of = np.array([REGIONS.index(r) for _k, r, _x, _y in seed_list], np.uint8)
    water = np.isin(arr[::CELL, ::CELL][:ch, :cw], (G.SEA, G.SHALLOW))
    idx[far & water] = SEA_OF + region_of[idx[far & water]]
    idx[far & ~water] = 255
    s = pygame.Surface((cw, ch), depth=8)
    s.set_palette([(i, i, i) for i in range(256)])
    pygame.surfarray.blit_array(s, idx.T)
    return s


def main():
    global LAYOUT
    name = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--layout=")), "journeys")
    LAYOUT = LAYOUTS[name]
    OUT = os.path.join("assets", "soaring3d", LAYOUT["out"])
    pygame.init()
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    os.makedirs(OUT, exist_ok=True)
    canvas, places = compose()
    if "--compose" in sys.argv:              # (just the pasted-together picture, to check the places)
        pygame.image.save(canvas, os.path.join(OUT, "_compose.png"))
        print("wrote _compose.png", canvas.get_size(), places)
        return
    arr = classes(canvas, places)
    full = surface(paint(arr))
    W, H = full.get_size()
    half = pygame.transform.scale(full, (W // 2, H // 2))
    quarter = pygame.transform.scale(half, (W // 4, H // 4))
    eighth = pygame.transform.smoothscale(quarter, (W // 8, H // 8))
    for name in os.listdir(OUT):
        if name.startswith(("t0_", "t1_")):
            os.remove(os.path.join(OUT, name))
    for lvl, img in (("t0", full), ("t1", half)):
        for ty in range(0, img.get_height(), TILE):
            for tx in range(0, img.get_width(), TILE):
                r = pygame.Rect(tx, ty, TILE, TILE).clip(img.get_rect())
                pygame.image.save(img.subsurface(r), os.path.join(OUT, f"{lvl}_{tx // TILE}_{ty // TILE}.png"))
    pygame.image.save(quarter, os.path.join(OUT, "w2.png"))
    pygame.image.save(eighth, os.path.join(OUT, "w3.png"))
    seed_list = seeds(places)
    pygame.image.save(cells(seed_list, arr), os.path.join(OUT, "cells.png"))
    hx, hy, _fx, _fy = places["HOENN"]
    meta = {
        "layout": name,
        "source": "%s cut to %s, x%.4f; region maps pasted on (dev/builders/make_soaring_world.py --layout=%s)"
                  % (LAYOUT["src"].replace(os.sep, "/"), list(LAYOUT["crop"]), LAYOUT["k"], name),
        "map_px": [arr.shape[1], arr.shape[0]],           # the world in town-map pixels
        "ground_px": [W, H], "tile": TILE, "per_map_px": 4,
        "unit_per_map_px": SCALE,
        "origin": [HOENN_X0 - hx * SCALE, HOENN_Z0 - hy * SCALE],   # world units of town-map pixel (0, 0)
        "places": {r: list(v) for r, v in places.items()},
        "cell": CELL, "reach": REACH, "regions": REGIONS, "sea_of": SEA_OF,
        "seeds": seed_list,
    }
    with open(os.path.join(OUT, "world.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)
    print("wrote", OUT, "ground", (W, H), "seeds", len(seed_list))


if __name__ == "__main__":
    main()
