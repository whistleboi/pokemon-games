"""Town and route backgrounds rendered from Pokemon Journeys V18's maps (Jordan's fan-game find, an
RPG Maker XP / Essentials v18 project with hand-built Kanto, Johto, Hoenn, Sinnoh, Sevii and
Orange Islands maps), so every town and route of those regions shares one look.

Each map is drawn tile by tile (tileset, autotiles, then its signs and objects) and framed to the
screen above the text box (1280 x 540):
- a town shows the whole town: shrunk (never below its original Game Boy pixels) until it fits,
  the frame's spare room filled by the land or sea at its edges, not stretched;
- a route or cave shows the stretch of the map with the most tall grass (where the wild Pokemon
  stand on the route screen), at full size.

Saved to assets/journeys/towns/<area key>.png and assets/journeys/routes/<area key>.png, which
the town and route screens use before any other background. Unova and Orre are left out: Journeys
built only a handful of their maps, and a region should look the same throughout.
Run from the game folder:
    python dev/builders/render_journeys_backgrounds.py ["<Pokemon Journeys V18 folder>"] [AREA_KEY ...]
"""
import json
import os
import re
import struct
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rxdata  # noqa: E402

JOURNEYS = os.path.join("..", "..", "Pokemon Journeys V18")
OUT = os.path.join("assets", "journeys")
W, H = 1280, 540  # the screen above the text box
MIN_SCALE = 0.5   # never shrink a map below its original Game Boy pixel size
GRASS_TAGS = {2, 10}  # Essentials v18 terrain tags: Grass, TallGrass

# Our area files -> the Journeys region folders their maps are in (Kanto's Routes 26-28 and
# Mt. Silver are in Journeys' Johto folder).
REGIONS = {
    "pokemon_area_data.json": ["Kanto Region", "Johto Region"],
    "johto_area_data.json": ["Johto Region", "Kanto Region"],
    "hoenn_area_data.json": ["Hoenn Region"],
    "sinnoh_area_data.json": ["Sinnoh Region"],
    "sevii_area_data.json": ["Inter-Region"],
    "orange_area_data.json": ["Orange Islands"],
}
# Our name -> Journeys' map name, where they differ.
ALIASES = {
    "VERMILLION_CITY": "VERMILION CITY", "DIGLETT_CAVE": "DIGGLET'S CAVE", "CLIFF_CAVE": "CLIFF CAVES",
    "CLIFF_EDGE_GATE": "CLIFFEDGE GATE", "DRAGONS_DEN": "DRAGON DEN", "SOOTOPOLIS_CITY": "SOOTOPOLIS CITY NC",
    "MT_PYRE": "MT. PYRE EXTERIOR", "SHOAL_CAVE": "SHOAL CAVE NC", "ROUTE_211": "Route 211 West",
    "MT_CORONET": "Mt Coronet Wilds", "FUEGO_IRONWORKS": "Fuego Ironworks EXT",
    "MEMORIAL_PILLAR": "MEMORIAL PILLAR NC", "SIX_ISLAND": "SIX ISLANDS", "MT_EMBER": "MT EMBER",
}
# Our "towns" that are really a cave or a building (Journeys has them only as indoor maps).
SKIP = {"MT_MOON_CITY", "MT_SILVER_CITY", "ROCK_TUNNEL_CITY", "SILPH_CITY", "OLIVINE_LIGHTHOUSE",
        "PINKAN_ISLAND"}  # (Journeys' Pinkan Island is an empty placeholder)
# Towns tucked into a corner of a big map of cliffs or forest, framed by hand: (scale, x, y) of
# the frame's top-left tile.
FOCUS = {"LAVARIDGE_TOWN": (1.0, 20, 43), "VERDANTURF_TOWN": (1.0, 60, 0)}
# Towns whose edge fill needs a hand-picked map tile: {area key: {side: (x, y)}}.
SIDES = {"ONE_ISLAND": {"right": (23, 0)}}  # the sea, not One Island's cliff wall

# RMXP autotiles: the four 16 x 16 quarters (cells of the 96 x 128 sheet, 1-based) of each of
# the 48 patterns.
AUTO = [
    [27, 28, 33, 34], [5, 28, 33, 34], [27, 6, 33, 34], [5, 6, 33, 34], [27, 28, 33, 12], [5, 28, 33, 12],
    [27, 6, 33, 12], [5, 6, 33, 12], [27, 28, 11, 34], [5, 28, 11, 34], [27, 6, 11, 34], [5, 6, 11, 34],
    [27, 28, 11, 12], [5, 28, 11, 12], [27, 6, 11, 12], [5, 6, 11, 12], [25, 26, 31, 32], [25, 6, 31, 32],
    [25, 26, 31, 12], [25, 6, 31, 12], [15, 16, 21, 22], [15, 16, 21, 12], [15, 16, 11, 22], [15, 16, 11, 12],
    [29, 30, 35, 36], [29, 30, 11, 36], [5, 30, 35, 36], [5, 30, 11, 36], [39, 40, 45, 46], [5, 40, 45, 46],
    [39, 6, 45, 46], [5, 6, 45, 46], [25, 30, 31, 36], [15, 16, 45, 46], [13, 14, 19, 20], [13, 14, 19, 12],
    [17, 18, 23, 24], [17, 18, 11, 24], [41, 42, 47, 48], [5, 42, 47, 48], [37, 38, 43, 44], [37, 6, 43, 44],
    [13, 18, 19, 24], [13, 14, 43, 44], [37, 42, 43, 48], [17, 18, 47, 48], [13, 18, 43, 48], [1, 2, 7, 8],
]


def norm(name):
    return re.sub(r"[^A-Z0-9]+", "_", str(name).upper()).strip("_")


class Journeys:
    def __init__(self, root):
        self.root = root
        data = os.path.join(root, "Data")
        self.info = rxdata.load(os.path.join(data, "MapInfos.rxdata"))
        self.tilesets = rxdata.load(os.path.join(data, "Tilesets.rxdata"))
        self._imgs = {}

    def map_id(self, name):
        for k, v in sorted(self.info.items()):
            if rxdata.text(v.attrs["name"]).strip().upper() == name.upper():
                return k
        return None

    def image(self, sub, name):
        key = (sub, name)
        if key not in self._imgs:
            self._imgs[key] = None
            for ext in ("", ".png", ".PNG"):
                p = os.path.join(self.root, "Graphics", sub, name + ext)
                if name and os.path.isfile(p):
                    self._imgs[key] = pygame.image.load(p)
                    break
        return self._imgs[key]

    @staticmethod
    def autotile(img, pattern):
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        if img.get_height() == 32:  # a one-tile autotile
            surf.blit(img, (0, 0), (0, 0, 32, 32))
            return surf
        for q, n in enumerate(AUTO[pattern]):
            n -= 1
            surf.blit(img, ((q % 2) * 16, (q // 2) * 16), ((n % 6) * 16, (n // 6) * 16, 16, 16))
        return surf

    def render(self, map_id, pad_x=0, pad_y=0, sides=None, people=True):
        """The map at 32 px a tile, with pad_x / pad_y extra tiles on each side that repeat the
        nearest edge tile (so the sea or cliffs carry on)."""
        mp = rxdata.load(os.path.join(self.root, "Data", f"Map{map_id:03d}.rxdata"))
        ts = self.tilesets[mp.attrs["tileset_id"]].attrs
        sheet = self.image("Tilesets", rxdata.text(ts["tileset_name"]))
        autos = [self.image("Autotiles", rxdata.text(n)) for n in ts["autotile_names"]]
        raw = mp.attrs["data"].data
        _dim, xs, ys, zs, _n = struct.unpack("<5i", raw[:20])
        vals = struct.unpack(f"<{xs * ys * zs}h", raw[20:20 + 2 * xs * ys * zs])
        out = pygame.Surface(((xs + 2 * pad_x) * 32, (ys + 2 * pad_y) * 32), pygame.SRCALPHA)
        out.fill((0, 0, 0, 255))
        # Past the border each side repeats its most common 2 x 2 block (all layers), so the sea,
        # a forest or a rock face carries on (trees are 2 x 2 tiles; one tile would streak).
        stack = lambda x, y: tuple(vals[x + y * xs + z * xs * ys] for z in range(zs))
        block = lambda x, y: tuple(stack(min(x + dx, xs - 1), min(y + dy, ys - 1)) for dy in (0, 1) for dx in (0, 1))
        def common(cells):
            """The most common block; a plain one (sea, rock, grass) wins if it's nearly as common,
            since a cliff's edge or a wall repeated sideways shows as stripes."""
            top = max(set(cells), key=cells.count)
            plain = [c for c in cells if len(set(c)) == 1]
            if plain:
                best = max(set(plain), key=plain.count)
                if plain.count(best) * 2 >= cells.count(top):
                    return best
            return top
        band = range(0, 4, 2)  # the outer 4 tiles of each side
        fill = {"top": common([block(x, d) for x in range(0, xs, 2) for d in band]),
                "bottom": common([block(x, ys - 2 - ys % 2 - d) for x in range(0, xs, 2) for d in band]),
                "left": common([block(d, y) for y in range(0, ys, 2) for d in band]),
                "right": common([block(xs - 2 - xs % 2 - d, y) for y in range(0, ys, 2) for d in band])}
        fill.update({side: (stack(*cell),) * 4 for side, cell in (sides or {}).items()})
        cache = {}
        for z in range(zs):
            for ty in range(-pad_y, ys + pad_y):
                for tx in range(-pad_x, xs + pad_x):
                    if 0 <= tx < xs and 0 <= ty < ys:
                        t = vals[tx + ty * xs + z * xs * ys]
                    else:
                        side = "left" if tx < 0 else "right" if tx >= xs else "top" if ty < 0 else "bottom"
                        t = fill[side][(ty % 2) * 2 + tx % 2][z]
                    pos = ((tx + pad_x) * 32, (ty + pad_y) * 32)
                    if t >= 384 and sheet:
                        i = t - 384
                        out.blit(sheet, pos, ((i % 8) * 32, (i // 8) * 32, 32, 32))
                    elif t >= 48:
                        a = t // 48 - 1
                        img = autos[a] if a < len(autos) else None
                        if img:
                            if (a, t % 48) not in cache:
                                cache[(a, t % 48)] = self.autotile(img, t % 48)
                            out.blit(cache[(a, t % 48)], pos)
        for e in mp.attrs["events"].values():  # signs, objects and townsfolk as first placed
            g = e.attrs["pages"][0].attrs["graphic"].attrs
            ex, ey = (e.attrs["x"] + pad_x) * 32, (e.attrs["y"] + pad_y) * 32
            name = rxdata.text(g["character_name"])
            if name and not people and not name.lower().startswith(("object", "berrytree")):
                continue  # a route's townsfolk would look like trainers waiting to battle
            if name:
                img = self.image("Characters", name)
                if img:
                    fw, fh = img.get_width() // 4, img.get_height() // 4
                    row = {2: 0, 4: 1, 6: 2, 8: 3}.get(g["direction"], 0)
                    out.blit(img, (ex + 16 - fw // 2, ey + 32 - fh), (g["pattern"] * fw, row * fh, fw, fh))
            elif g["tile_id"] >= 384 and sheet:
                i = g["tile_id"] - 384
                out.blit(sheet, (ex, ey), ((i % 8) * 32, (i // 8) * 32, 32, 32))
        tags_raw = ts["terrain_tags"].data
        tags = struct.unpack(f"<{(len(tags_raw) - 20) // 2}h", tags_raw[20:])
        grass = [[any(tags[vals[x + y * xs + z * xs * ys]] in GRASS_TAGS
                      for z in range(zs) if 0 <= vals[x + y * xs + z * xs * ys] < len(tags))
                  for x in range(xs)] for y in range(ys)]
        stacks = [[stack(x, y) for x in range(xs)] for y in range(ys)]
        events = {(e.attrs["x"], e.attrs["y"]) for e in mp.attrs["events"].values()}
        counts = {}
        for row in stacks:
            for st in row:
                counts[st] = counts.get(st, 0) + 1
        filler, covered = set(), 0  # the commonest tiles, three quarters of the map: trees, grass, sea, rock
        for st in sorted(counts, key=counts.get, reverse=True):
            if covered >= 0.75 * xs * ys:
                break
            filler.add(st)
            covered += counts[st]
        self.last_map = {"xs": xs, "ys": ys, "grass": grass, "stacks": stacks,
                         "empty": [[not any(stacks[y][x]) for x in range(xs)] for y in range(ys)],
                         # what makes a town: buildings, signs, fences... (tileset tiles, not the
                         # filler; shores and paths are autotiles) and events
                         "detail": [[(x, y) in events or (stacks[y][x] not in filler
                                                          and any(t >= 384 for t in stacks[y][x]))
                                     for x in range(xs)] for y in range(ys)]}
        return out, xs, ys

    def maps_in(self, regions):
        """{normalized name: map id} of the built maps in these Journeys region folders (an
        empty placeholder map is about 1 KB)."""
        data = os.path.join(self.root, "Data")
        parent = {k: v.attrs["parent_id"] for k, v in self.info.items()}

        def top(k):
            while parent.get(k, 0):
                k = parent[k]
            return rxdata.text(self.info[k].attrs["name"])

        found = {}
        for region in regions:
            for k in sorted(self.info):
                path = os.path.join(data, f"Map{k:03d}.rxdata")
                if top(k) == region and os.path.isfile(path) and os.path.getsize(path) > 2000:
                    found.setdefault(norm(rxdata.text(self.info[k].attrs["name"])), k)
        return found

    MAX_VOID = 0.15  # a frame more than this much empty map (black) isn't used

    def _best_window(self, wt, ht, kind):
        """Top-left tile of the best wt x ht window (it may run past the map's edge, where the
        padding is): a route's has the most tall grass (doubly in its lower two thirds, where the
        Pokemon stand), a town's the most buildings, signs and variety; either avoids empty map.
        Returns (x0, y0, share of the window that is empty map, share of the map's events in it)."""
        m = self.last_map
        xs, ys = m["xs"], m["ys"]

        def prefix(grid):
            pre = [[0] * (xs + 1) for _ in range(ys + 1)]
            for y in range(ys):
                row = 0
                for x in range(xs):
                    row += grid[y][x]
                    pre[y + 1][x + 1] = pre[y][x + 1] + row
            return pre

        def box(pre, x0, y0, x1, y1):
            x0, x1, y0, y1 = max(0, x0), min(xs, x1), max(0, y0), min(ys, y1)
            if x0 >= x1 or y0 >= y1:
                return 0
            return pre[y1][x1] - pre[y0][x1] - pre[y1][x0] + pre[y0][x0]

        grass, empty, detail = prefix(m["grass"]), prefix(m["empty"]), prefix(m["detail"])
        stacks = m["stacks"]
        # A map narrower (or shorter) than the window stays centred that way; a bigger one slides.
        xr = range(0, xs - wt + 1, 2) if xs >= wt else [(xs - wt) // 2]
        yr = range(0, ys - ht + 1, 2) if ys >= ht else [(ys - ht) // 2]
        best, best_score = (xr[0], yr[0], 1.0), None
        for y0 in yr:
            for x0 in xr:
                x1, y1 = x0 + wt, y0 + ht
                void = box(empty, x0, y0, x1, y1)
                variety = len({stacks[y][x] for y in range(max(0, y0), min(ys, y1), 3)
                               for x in range(max(0, x0), min(xs, x1), 3)})
                if kind == "route":
                    score = box(grass, x0, y0, x1, y1) + box(grass, x0, y0 + ht // 3, x1, y1) + variety * 0.5
                else:
                    score = variety + box(detail, x0, y0, x1, y1)
                score -= 3 * void
                if best_score is None or score > best_score:
                    best, best_score = (x0, y0, void / (wt * ht),
                                        box(detail, x0, y0, x1, y1) / max(1, detail[ys][xs])), score
        return best

    def town_background(self, map_id, sides=None, focus=None):
        """The town framed to W x H around its busiest stretch, as close up as still shows most
        of it (80% of its buildings, paths and signs; else as far out as MIN_SCALE), any spare room
        filled by the land or sea at its edges. None if the frame would show empty map."""
        _img, xs, ys = self.render(map_id)
        for scale in ((focus[0],) if focus else (1.0, 0.75, MIN_SCALE)):
            need_w, need_h = W / scale, H / scale  # frame size in map pixels
            wt, ht = -(-int(need_w) // 32), -(-int(need_h) // 32)
            x0, y0, void, shown = self._best_window(wt, ht, "town")
            if focus:
                x0, y0 = focus[1], focus[2]
            elif shown >= 0.8:
                break
        if void > self.MAX_VOID:
            return None
        pad_x = max(0, -x0, x0 + wt - xs) + 1
        pad_y = max(0, -y0, y0 + ht - ys) + 1
        img, _, _ = self.render(map_id, pad_x, pad_y, sides)
        center = ((x0 + pad_x) * 32 + int(need_w) // 2, (y0 + pad_y) * 32 + int(need_h) // 2)
        return self._frame(img, center, need_w, need_h, scale)

    def route_background(self, map_id):
        """W x H of the route or cave at full size around its grassiest stretch. None if the
        frame would show empty map (an indoor map's black)."""
        img, xs, ys = self.render(map_id, people=False)
        if xs * 32 < W or ys * 32 < H:
            return self.town_background(map_id)
        x0, y0, void, _ = self._best_window(-(-W // 32), -(-H // 32), "route")
        if void > self.MAX_VOID:
            return None
        return self._frame(img, (x0 * 32 + W // 2, y0 * 32 + H // 2), W, H, 1.0)

    @staticmethod
    def _frame(img, center, need_w, need_h, scale):
        crop = pygame.Rect(0, 0, int(need_w), int(need_h))
        crop.center = center
        crop.clamp_ip(img.get_rect())
        part = img.subsurface(crop.clip(img.get_rect())).copy()
        if scale == 1.0 and part.get_size() == (W, H):
            return part
        if scale == 0.5:
            return pygame.transform.scale(part, (W, H))  # tiles are drawn at 2x: halving is exact
        return pygame.transform.smoothscale(part, (W, H))


def mostly_void(img, limit=0.15):
    """True when more than `limit` of the picture is black (an indoor map's surroundings; some
    maps paint them with a black tile, so the tiles alone don't tell)."""
    w, h = img.get_size()
    pts = [(x, y) for x in range(4, w, 16) for y in range(4, h, 16)]
    return sum(1 for p in pts if sum(img.get_at(p)[:3]) < 40) > limit * len(pts)


def areas():
    """(area key, area data, Journeys region folders) for every area of the covered regions."""
    for fname, regions in REGIONS.items():
        with open(os.path.join("assets", fname), encoding="utf-8") as f:
            for key, data in json.load(f).get("STORY_PROGRESSION", {}).items():
                if data.get("area_type") in ("town", "wild_route", "dungeon"):
                    yield key, data, regions


def match(key, data, found):
    names = [ALIASES.get(key), ALIASES.get(norm(data.get("route_name", ""))), data.get("route_name", ""), key,
             re.sub(r"^(KANTO|JOHTO|HOENN|SINNOH|SEVII)_", "", key)]
    for n in names:
        if n and norm(n) in found:
            return found[norm(n)]
    return None


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    root = args[0] if args and os.path.isdir(args[0]) else JOURNEYS
    only = {a.upper() for a in args if not os.path.isdir(a)}
    if not os.path.isdir(os.path.join(root, "Data")):
        sys.exit(f"Pokemon Journeys V18 not found at {root}")
    pygame.init()
    pygame.display.set_mode((1, 1))
    game = Journeys(root)
    pools = {}
    done = missing = 0
    for key, data, regions in areas():
        if (only and key not in only) or key in SKIP:
            continue
        found = pools.setdefault(tuple(regions), game.maps_in(regions))
        mid = match(key, data, found)
        if mid is None:
            missing += 1
            continue
        town = data.get("area_type") == "town"
        out = os.path.join(OUT, "towns" if town else "routes", f"{key.lower()}.png")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        img = game.town_background(mid, SIDES.get(key), FOCUS.get(key)) if town else game.route_background(mid)
        if img is None or mostly_void(img):  # mostly empty map (an indoor map, a placeholder)
            missing += 1
            if os.path.exists(out):
                os.remove(out)
            continue
        pygame.image.save(img, out)
        done += 1
        print(f"  {out}  <- Map{mid:03d} {rxdata.text(game.info[mid].attrs['name']).strip()}")
    print(f"{done} backgrounds, {missing} areas without a Journeys map")


if __name__ == "__main__":
    main(sys.argv[1:])
