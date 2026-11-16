"""Map maker (Jordan, 11-14): draw a walkable map on a grid, in the game's own map format, and see it as the game draws it.

Made first for the regions that only exist in 3D (Kalos, Alola, Galar, Paldea): you lay a reference picture of the
3D area underneath (its top-down render, height map, door and people markers) and design the 2D map over it. It edits
any map, though: open one of the game's own maps by its key (PALLET_TOWN), or a layout someone made for you.

    python dev/tools/map_maker.py                          a new 40 x 30 map
    python dev/tools/map_maker.py PALLET_TOWN              one of the game's maps (assets/town_maps.json)
    python dev/tools/map_maker.py ALOLA_IKI_TOWN           a map you saved here before (dev/builders/town_maps/made/)
    python dev/tools/map_maker.py layout.json --ref=top.png   a layout handed to you, with a picture underneath
    python dev/tools/map_maker.py --size=60x45                 a new map of that size

What it saves: dev/builders/town_maps/made/<KEY>.json, the map's entry exactly as the game reads it (its rows, buildings
and their kinds, roof colours, ways out, people, signs), plus the map maker's own notes (height levels, the reference
picture, building names) under "_maker". dev/builders/build_town_maps.py takes every made map into assets/town_maps.json
and checks it like any other (rectangles, doors, everything reachable). A made map with the same key as one in a region's
file replaces it when built.

Mouse: left paints with the tool; right picks up what's under it; the wheel zooms; middle-drag (or Space + drag) pans.
Keys: Ctrl+Z / Ctrl+Y undo / redo, Ctrl+S save, G game look, L levels, R reference, Delete removes the chosen building,
arrows move the chosen building a tile, P the park builder.

The park builder (its button, or P): the panel becomes pictures of everything, in tabs (buildings, scenery, ground,
height, ways out). Click a picture, or drag it onto the map: a see-through copy follows the mouse, green where it fits,
red where it doesn't; click to drop it (again for another; right-click or Esc empties your hand). Drag anything placed to
move it; right-click it to take it away. Ground and height are brushes (1, 3 or 5 tiles); raising or lowering the ground
rebuilds the cliffs when you let go. A source picture (a map to follow) goes with the map: Load..., or drop the picture
file on the window; Fit map sizes the map to it; Move / size frames it against the map (drag it; the wheel sizes it,
Ctrl only wider, Shift only taller; arrows nudge; Keep shape, Reset); its mode button cycles On top (the picture see-through over the map),
Underneath (the map see-through over it) and Tracing layer (the picture, with only what you've put down drawn over it:
plain lawn stays clear); Strength fades it.
"""
import copy
import json
import os
import sys

GAME = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, GAME)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(GAME)
import pygame  # noqa: E402
import cliff_tiers  # noqa: E402

MADE = os.path.join("dev", "builders", "town_maps", "made")
GAME_TILE = 32                      # the game look is drawn at this size, then scaled (art.py needs room to draw)
PANEL_W = 420
BG = (34, 38, 52)
PANEL = (46, 52, 70)
PANEL_LINE = (80, 90, 120)
TEXT = (232, 236, 246)
DIM = (150, 160, 184)
ACCENT = (110, 170, 255)

# ---------------------------------------------------------------- the assets: every map character, by kind
PALETTE = [
    ("Ground", [(".", "grass"), ("d", "pale grass path"), ("=", "sand path"), ("s", "beach"), ('"', "tall grass (wild)"),
                ("f", "flowers"), ("a", "city road"), ("p", "sidewalk"), ("e", "pale stone pavement"), (",", "plank walkway"),
                ("8", "deep snow"), ("9", "marsh mud"), ("%", "sheet ice")]),
    ("Nature", [("T", "tree"), ("2", "small tree (Cut)"), ("r", "rock"), ("0", "cracked rock (Rock Smash)"),
                ("b", "boulder (Strength)"), ("@", "gravestone")]),
    ("Water", [("~", "water (no crossing)"), ("o", "sea (Surf)"), (":", "deep sea (Dive)"), ("q", "rock in the sea"),
               ("$", "waterfall"), ("[", "current west"), ("]", "current east"), ("{", "current north"), ("}", "current south")]),
    ("Cliffs & ledges", [("c", "cliff"), ("_", "ledge (hop south)"), ("(", "ledge (hop west)"), (")", "ledge (hop east)"),
                         ("/", "climbing wall (Rock Climb)"), ("7", "muddy slope (Bicycle)"), ("'", "round stones")]),
    ("Fences & walls", [("#", "wooden fence"), ("k", "white picket fence"), ("i", "iron railing"), ("g", "stone gate wall"),
                        ("j", "stone post")]),
    ("Props", [("!", "sign"), ("l", "lamp post"), ("h", "fire hydrant"), ("m", "machine / counter"), ("y", "sofa"),
               ("z", "potted plant"), ("*", "lava")]),
    ("Bridges", [("|", "log bridge (north-south)"), (";", "log bridge (east-west)")]),
    ("Ways out", [("^", "way out north"), ("v", "way out south"), ("<", "way out west"), (">", "way out east"),
                  ("w", "water way out"), ("+", "ladder down"), ("-", "ladder up")]),
    ("People", [("N", "someone standing"), ("X", "a trainer's spot")]),
]
NAME = {c: n for _cat, items in PALETTE for c, n in items}

# Pre-made buildings: (name, kind, width, height with the door row), sizes as the game's own maps most often have them
BUILDINGS = [("Pokemon Center", "center", 5, 5), ("Poke Mart", "mart", 4, 4), ("House (small)", "house", 4, 4),
             ("House (tall)", "house", 4, 5), ("House (wide)", "house", 6, 4), ("Your home", "home", 5, 5),
             ("Rival's home", "rival", 5, 5), ("Gym", "gym", 7, 5), ("Lab", "lab", 7, 5), ("Gatehouse", "gate", 6, 7),
             ("Harbor", "harbor", 7, 6), ("Day Care", "daycare", 5, 5), ("Museum", "museum", 11, 6),
             ("Game Corner", "game corner", 7, 6), ("Contest Hall", "contest", 7, 6), ("Pokemon League", "league", 11, 6),
             ("School", "school", 7, 5), ("Fountain", "fountain", 4, 5), ("Cave mouth", "cave", 3, 3)]
KINDS = sorted({b[1] for b in BUILDINGS} | {"bike", "tunnel", "heap", "hedge", "cycle", "guru", "fisher", "gent",
                                            "oldman", "aide", "bill", "fanclub", "timber"})
ROOF_PRESETS = [(232, 92, 64), (72, 122, 214), (96, 170, 108), (80, 152, 166), (214, 72, 64), (222, 128, 150),
                (222, 150, 70), (150, 162, 184), (150, 116, 84), (120, 170, 220), (196, 170, 90), (140, 100, 170)]

# the park builder's groups, tab by tab (a piece's index.json may name its own "group"; else it's guessed from its name)
GROUPS = {"Buildings": ["Centers & Marts", "Houses", "Shops & towers", "Landmarks"],
          "Scenery": ["Stairs", "Paths & ground", "Trees & plants", "Rocks", "Mounds", "Statues", "Signs & lamps", "Furniture", "Vehicles", "Fences & walls", "Props"],
          "Ground": ["Paths", "Grass", "Water", "Ledges"], "Ways out": ["Ways out", "People"], "Height": []}
SOURCES = {"alola": "KingTapir", "biome": "Kyle-Dove", "lotus": "LotusKing", "hgss": "Akizakura16", "gen5": "UltimoSpriter",
           "hoenn_sv": "SailorVicious", "kaliser": "Kaliser", "bp": "Banished Platinum"}
_WORDS = [("Stairs", "stair steps"), ("Trees & plants", "tree palm pine jungle tropic sprout bush grove flower hedge plant"),
          ("Rocks", "boulder rock stump ice crystal stone_block"),
          ("Signs & lamps", "sign board map lamp lantern light"),
          ("Statues", "totem tiki statue monument arch pedestal tablet post orb fountain"),
          ("Vehicles", "truck van yacht boat car ship bike"),
          ("Fences & walls", "fence wall gate rail"),
          ("Furniture", "bench table umbrella chair stand")]


THEMES = ["Town", "Tropical", "Forest", "Desert", "Snow", "Water", "Cave", "Ruins", "Mountain", "Swamp", "Volcano"]
_THEME_WORDS = [("Tropical", "palm tropic beach umbrella surf hula tiki totem aloha alola"),
                ("Snow", "snow ice frost winter"), ("Desert", "cactus desert sand dune"), ("Swamp", "swamp marsh bog"),
                ("Volcano", "lava volcano magma"), ("Cave", "cave mine crystal"), ("Ruins", "ruin temple shrine"),
                ("Water", "dock pier boat yacht ship sea"), ("Mountain", "boulder rock cliff mountain"),
                ("Forest", "tree pine stump log bush jungle grove mushroom")]
# the sheet's own categories (Pokemon Ultimate Tileset Collection) -> our themes
CATEGORY_THEMES = {"beaches": "Tropical", "beachers": "Tropical", "trees": "Forest", "forests": "Forest", "plants": "Forest",
                   "snow": "Snow", "desert": "Desert", "water": "Water", "caves": "Cave", "ruins": "Ruins",
                   "mountains": "Mountain", "cliffs": "Mountain", "rocks": "Mountain", "swamp": "Swamp", "volcano": "Volcano",
                   "lava": "Volcano", "city": "Town", "buildings": "Town", "poi": "Town", "paths": "Town", "routes": "Forest"}


def guess_theme(name, label, kind):
    words = f"{name} {label}".lower()
    for theme, ws in _THEME_WORDS:
        if any(w in words for w in ws.split()):
            return theme
    return "Town" if kind not in ("tree", "prop") else None


def guess_group(name, label, kind):
    """Which group a piece goes in, from its kind and name."""
    words = f"{name} {label}".lower()
    if kind in ("center", "mart"):
        return "Centers & Marts"
    if kind not in ("tree", "prop"):
        if any(w in words for w in ("shop", "store", "tower", "building", "apartment", "market", "mall", "office")):
            return "Shops & towers"
        if any(w in words for w in ("hut", "house", "home", "cottage", "cabin")):
            return "Houses"
        return "Landmarks"
    for group, ws in _WORDS:
        if any(w in words for w in ws.split()):
            return group
    return "Trees & plants" if kind == "tree" else "Props"


def library():
    """The ready-made pieces (dev/tools/piece_library.py): every assets/tiles/<set>/index.json entry with a footprint."""
    out = []
    base = os.path.join("assets", "tiles")
    for folder in sorted(os.listdir(base)) if os.path.isdir(base) else []:
        idx = os.path.join(base, folder, "index.json")
        if not os.path.isfile(idx):
            continue
        try:
            with open(idx, encoding="utf-8") as f:
                index = json.load(f)
        except (OSError, ValueError):
            continue
        for name, meta in index.items():
            if isinstance(meta, dict) and meta.get("foot"):
                kind = meta.get("kind", "house")
                out.append({"key": f"{folder}:{name}", "label": meta.get("label", name), "kind": kind,
                            "w": meta["foot"][0], "h": meta["foot"][1], "doors": meta.get("doors", []),
                            "prop": kind in ("tree", "prop"),
                            "group": meta.get("group") or guess_group(name, meta.get("label", name), kind),
                            "source": meta.get("artist") or SOURCES.get(folder, folder),
                            "walk": bool(meta.get("walk")),       # (stairs: walked on, not in the way)
                            "theme": meta.get("theme") or guess_theme(name, meta.get("label", name), kind),
                            "gen": meta.get("gen") or ""})
    return out


LIBRARY = library()
# pre-made buildings and the library's pieces: (name, kind, w, h, library piece or None)
PRESETS = [b + (None,) for b in BUILDINGS] + [(f"{p['label']}  [{p['key']}]", p["kind"], p["w"], p["h"], p) for p in LIBRARY]

# flat colours for the quick view (the game look draws the real thing)
FLAT = {".": (124, 200, 120), "d": (196, 236, 204), "=": (226, 204, 148), "s": (240, 226, 178), '"': (72, 158, 82),
        "f": (236, 150, 190), "a": (128, 128, 138), "p": (222, 190, 124), "e": (226, 222, 210), ",": (176, 124, 72),
        "8": (238, 244, 250), "9": (104, 186, 150), "%": (200, 230, 250), "T": (40, 110, 56), "2": (70, 140, 70),
        "r": (150, 140, 128), "0": (170, 150, 130), "b": (130, 120, 110), "@": (170, 170, 176), "~": (76, 140, 222),
        "o": (76, 140, 222), ":": (40, 80, 170), "q": (110, 110, 130), "$": (180, 220, 250), "[": (90, 150, 230),
        "]": (90, 150, 230), "{": (90, 150, 230), "}": (90, 150, 230), "c": (200, 160, 116), "_": (170, 200, 110),
        "(": (170, 200, 110), ")": (170, 200, 110), "/": (160, 130, 100), "7": (150, 120, 80), "'": (180, 170, 160),
        "#": (176, 124, 76), "k": (246, 246, 240), "i": (90, 120, 200), "g": (180, 176, 168), "j": (236, 236, 236),
        "!": (196, 150, 96), "l": (240, 220, 120), "h": (220, 60, 60), "m": (120, 130, 150), "y": (200, 70, 70),
        "z": (60, 140, 80), "*": (240, 90, 40), "|": (176, 124, 72), ";": (176, 124, 72), "^": (255, 255, 255),
        "v": (255, 255, 255), "<": (255, 255, 255), ">": (255, 255, 255), "w": (200, 230, 255), "+": (90, 70, 50),
        "-": (90, 70, 50), "N": (255, 210, 60), "X": (255, 120, 60), "D": (70, 40, 24), "`": (110, 170, 100)}
EXIT_CHARS = "^v<>wu+-"
SPRITE_HOUSES = ("house", "home", "rival", "assistant", "elder")   # (drawn off the tile sheet: a custom roof tints it)


def roof_rgb(v):
    """A roof entry's colour: [r, g, b], or {"roof": [r, g, b], ...}; None if it has none."""
    if isinstance(v, dict):
        v = v.get("roof")
    return list(v) if isinstance(v, (list, tuple)) else None


# ---------------------------------------------------------------- the map being made
class MapDoc:
    def __init__(self, w=40, h=30, key="NEW_MAP"):
        self.key = key
        self.w, self.h = w, h
        self.art = [["."] * w for _ in range(h)]
        self.levels = [[0] * w for _ in range(h)]
        self.buildings, self.roofs, self.names = {}, {}, {}
        self.exits, self.people, self.signs = {}, {}, {}
        self.theme = None
        self.ref = None              # {"path": ..., "alpha": 0-255}
        self.objects = []            # ready-made pieces standing on the map: {"k": "alola:palm", "at": [x, y]} (on ` tiles)
        self.paint = {}              # painted ground: {(x, y): surface} (assets/tiles/autotiles; roofs "_paint" in the map)
        self.extra = {}              # the entry's other keys (kept as they were: rooms, scenes, ...)

    # ---- reading and writing the game's format
    @classmethod
    def from_entry(cls, key, m, maker=None):
        rows = m["art"]
        d = cls(len(rows[0]), len(rows), key)
        d.art = [list(r) for r in rows]
        d.buildings = dict(m.get("buildings") or {})
        d.roofs = {k: v for k, v in (m.get("roofs") or {}).items() if len(k) == 1 and not k.startswith("_")}
        d.exits = dict(m.get("exits") or {})
        d.theme = m.get("theme")
        cells = lambda ch: [(x, y) for y in range(d.h) for x in range(d.w) if d.art[y][x] == ch]
        d.people = {c: p for c, p in zip(cells("N"), m.get("people") or [])}
        d.signs = {c: s for c, s in zip(cells("!"), m.get("signs") or [])}
        d.extra = {k: v for k, v in m.items() if k not in ("art", "buildings", "roofs", "exits", "people", "signs", "theme", "_maker")}
        extras = {k: v for k, v in (m.get("roofs") or {}).items() if k not in d.roofs}
        sets = {p["key"].split(":")[0] for p in LIBRARY}
        objs = extras.pop("_objects", []) or []
        pt = extras.pop("_paint", None) or {}
        for y, row in enumerate((pt.get("rows") or [])[:d.h]):
            for x, code in enumerate(row[:d.w]):
                if code in (pt.get("key") or {}):
                    d.paint[(x, y)] = pt["key"][code]
        d.objects = [o for o in objs if isinstance(o.get("k"), str) and o["k"].split(":")[0] in sets and "at" in o]
        if len(d.objects) < len(objs):
            extras["_objects"] = [o for o in objs if o not in d.objects]
        d.extra["_roof_extras"] = extras
        maker = maker or m.get("_maker") or {}
        if maker.get("levels") and len(maker["levels"]) == d.h:
            d.levels = [list(r) for r in maker["levels"]]
        d.names = dict(maker.get("names") or {})
        d.ref = maker.get("ref")
        return d

    def to_entry(self):
        order = lambda dct: [dct[c] for c in sorted(dct, key=lambda t: (t[1], t[0]))]
        rows = ["".join(r) for r in self.art]
        used = {c for r in rows for c in r}
        m = {k: v for k, v in self.extra.items() if k != "_roof_extras"}
        roofs = dict(self.extra.get("_roof_extras") or {})
        roofs.update({k: v for k, v in self.roofs.items() if k in used})
        if self.objects:
            roofs["_objects"] = list(roofs.get("_objects") or []) + self.objects
        if self.paint_spec():
            roofs["_paint"] = self.paint_spec()
        m.update({"art": rows, "buildings": {k: v for k, v in self.buildings.items() if k in used}, "roofs": roofs,
                  "exits": {k: v for k, v in self.exits.items() if k in used},
                  "people": [p for p in order({c: p for c, p in self.people.items() if self.cell(*c) == "N"})],
                  "signs": [s for s in order({c: s for c, s in self.signs.items() if self.cell(*c) == "!"})]})
        if self.theme:
            m["theme"] = self.theme
        m["_maker"] = {"levels": self.levels, "names": {k: v for k, v in self.names.items() if k in used}, "ref": self.ref}
        return m

    def snapshot(self):
        return copy.deepcopy((self.w, self.h, self.art, self.levels, self.buildings, self.roofs, self.names,
                              self.exits, self.people, self.signs, self.theme, self.ref, self.objects, self.extra, self.paint))

    def restore(self, s):
        (self.w, self.h, self.art, self.levels, self.buildings, self.roofs, self.names, self.exits, self.people,
         self.signs, self.theme, self.ref, self.objects, self.extra, self.paint) = copy.deepcopy(s)

    def paint_spec(self):
        """The painted ground as the map holds it: {"key": {code: surface}, "rows": [...]} ("." unpainted), or None."""
        live = {xy: n for xy, n in self.paint.items() if n in AUTOTILES and self.cell(*xy) in (AUTOTILES[n].get("char"), "`")}
        if not live:
            return None
        codes = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        names = sorted(set(live.values()))
        code = dict(zip(names, codes))
        rows = [["."] * self.w for _ in range(self.h)]
        for (x, y), n in live.items():
            rows[y][x] = code[n]
        return {"key": {c: n for n, c in code.items()}, "rows": ["".join(r) for r in rows]}

    def paint_cell(self, x, y, name):
        """Paint a tile with a surface (its walking character goes in the map; "" rubs it back to grass). Never over a
        building, a placed piece or cliff rock. True if it changed."""
        if not (0 <= x < self.w and 0 <= y < self.h) or self.owner(x, y) or self.cell(x, y) in ("`", "c"):
            return False
        ch = AUTOTILES[name]["char"] if name else "."
        if self.cell(x, y) == ch and self.paint.get((x, y), "") == name:
            return False
        self.set(x, y, ch)
        if name:
            self.paint[(x, y)] = name
        return True

    # ---- cells
    def cell(self, x, y):
        return self.art[y][x] if 0 <= x < self.w and 0 <= y < self.h else None

    def is_building(self, ch):
        return ch is not None and ch.isupper() and ch not in "TDNX"

    def owner(self, x, y):
        """The building letter at (x, y) (its door too), or None."""
        ch = self.cell(x, y)
        if self.is_building(ch):
            return ch
        if ch == "D":
            for dx, dy in ((0, -1), (-1, 0), (1, 0)):
                if self.is_building(self.cell(x + dx, y + dy)):
                    return self.cell(x + dx, y + dy)
        return None

    def rect_of(self, L):
        """(x, y, w, h) of building L, its door row included."""
        cells = [(x, y) for y in range(self.h) for x in range(self.w) if self.art[y][x] == L]
        if not cells:
            return None
        xs, ys = [c[0] for c in cells], [c[1] for c in cells]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        if any(self.cell(x, y1 + 1) == "D" for x in range(x0, x1 + 1)) and not any(self.cell(x, y1) == "D" for x in range(x0, x1 + 1)):
            y1 += 1
        return x0, y0, x1 - x0 + 1, y1 - y0 + 1

    def door_of(self, L):
        r = self.rect_of(L)
        if not r:
            return None
        x, y, w, h = r
        for dx in range(w):
            if self.cell(x + dx, y + h - 1) == "D":
                return dx
        return None

    def set(self, x, y, ch):
        if not (0 <= x < self.w and 0 <= y < self.h):
            return
        self.paint.pop((x, y), None)
        if self.owner(x, y) and not self.is_building(ch) and ch != "D":
            L = self.owner(x, y)
            self.remove_building(L)
        if self.art[y][x] == "`" and ch != "`":
            self.remove_object_at(x, y)
        self.art[y][x] = ch

    def object_at(self, x, y):
        for o in self.objects:
            p = next((q for q in LIBRARY if q["key"] == o["k"]), None)
            w, h = (p["w"], p["h"]) if p else (1, 1)
            if o["at"][0] <= x < o["at"][0] + w and o["at"][1] <= y < o["at"][1] + h:
                return o
        return None

    def painted_char(self, x, y):
        """The walking character of a tile's painted ground (sand: =), or "." where it isn't painted."""
        n = self.paint.get((x, y))
        return AUTOTILES[n]["char"] if n in AUTOTILES else "."

    def remove_object_at(self, x, y):
        o = self.object_at(x, y)
        if o:
            self.objects.remove(o)
            p = next((q for q in LIBRARY if q["key"] == o["k"]), None)
            for yy in range(o["at"][1], o["at"][1] + (p["h"] if p else 1)):
                for xx in range(o["at"][0], o["at"][0] + (p["w"] if p else 1)):
                    if self.cell(xx, yy) == "`":
                        self.art[yy][xx] = self.painted_char(xx, yy)

    def place_object(self, x, y, piece):
        """A ready-made prop (a palm, a totem): its footprint in the way (`), the piece drawn over it. Stairs (a "walk"
        piece) are walked on: their footprint becomes open ground (.), even across a cliff."""
        if not (0 <= x and x + piece["w"] <= self.w and 0 <= y and y + piece["h"] <= self.h):
            return False
        for yy in range(y, y + piece["h"]):
            for xx in range(x, x + piece["w"]):
                if self.owner(xx, yy):
                    self.remove_building(self.owner(xx, yy))
                if self.cell(xx, yy) == "`" or self.object_at(xx, yy):
                    self.remove_object_at(xx, yy)
                self.art[yy][xx] = self.painted_char(xx, yy) if piece.get("walk") else "`"   # (painted ground runs on under it)
        self.objects.append({"k": piece["key"], "at": [x, y]})
        return True

    def free_letter(self):
        used = {c for r in self.art for c in r} | set(self.buildings)
        for c in "ABCEFGHIJKLMOPQRSUVWYZ" + "".join(chr(c) for c in range(0x391, 0x3AA)) + "".join(chr(c) for c in range(0x410, 0x430)):
            if c not in used and c.isupper():
                return c
        return None

    def place_building(self, x, y, w, h, kind, roof=None, name=None, door_dx=None, doors=None):
        L = self.free_letter()
        if not L:
            return None
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if 0 <= xx < self.w and 0 <= yy < self.h:
                    if self.owner(xx, yy):
                        self.remove_building(self.owner(xx, yy))
                    self.art[yy][xx] = L
        for dx in ([w // 2 if door_dx is None else max(0, min(w - 1, door_dx))] if doors is None else doors):
            if 0 <= y + h - 1 < self.h and 0 <= x + dx < self.w:
                self.art[y + h - 1][x + dx] = "D"
        self.buildings[L] = kind
        if roof:
            self.roofs[L] = list(roof)
        if name:
            self.names[L] = name
        return L

    def remove_building(self, L, fill="."):
        r = self.rect_of(L)
        if r:
            x, y, w, h = r
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    if self.art[yy][xx] in (L, "D") and (self.art[yy][xx] == L or self.owner(xx, yy) in (L, None)):
                        self.art[yy][xx] = fill
        for d in (self.buildings, self.roofs, self.names):
            d.pop(L, None)

    def reshape_building(self, L, x, y, w, h, door_dx=None):
        """Move / resize building L (keeps its kind, roof, name)."""
        kind, roof, name = self.buildings.get(L, "house"), self.roofs.get(L), self.names.get(L)
        if door_dx is None:
            door_dx = self.door_of(L)
        w, h = max(1, w), max(2, h)
        x, y = max(0, min(self.w - w, x)), max(0, min(self.h - h, y))
        self.remove_building(L)
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                other = self.owner(xx, yy)
                if other:
                    self.remove_building(other)
                self.art[yy][xx] = L
        dx = w // 2 if door_dx is None else max(0, min(w - 1, door_dx))
        self.art[y + h - 1][x + dx] = "D"
        self.buildings[L] = kind
        if roof:
            self.roofs[L] = roof
        if name:
            self.names[L] = name

    def flood(self, x, y, ch):
        old = self.cell(x, y)
        if old is None or old == ch or self.owner(x, y):
            return
        todo, seen = [(x, y)], set()
        while todo:
            a, b = todo.pop()
            if (a, b) in seen or self.cell(a, b) != old:
                continue
            seen.add((a, b))
            self.art[b][a] = ch
            self.paint.pop((a, b), None)
            todo += [(a + 1, b), (a - 1, b), (a, b + 1), (a, b - 1)]

    def resize(self, w, h, fill="."):
        self.art = [[self.art[y][x] if y < self.h and x < self.w else fill for x in range(w)] for y in range(h)]
        self.levels = [[self.levels[y][x] if y < self.h and x < self.w else 0 for x in range(w)] for y in range(h)]
        cl = (self.extra.get("_roof_extras") or {}).get("_cliffs")
        if cl:   # (the cliffs' tiles keep their places)
            for k in ("rock", "steps"):
                cl[k] = [((cl[k][y] if y < len(cl[k]) else "") + "." * w)[:w] for y in range(h)]
        self.w, self.h = w, h
        self.paint = {(x, y): n for (x, y), n in self.paint.items() if x < w and y < h}
        for L in list(self.buildings):
            if not any(L in r for r in self.art):
                self.buildings.pop(L, None)

    def cliffs_from_levels(self, rows=3, set_name="rock_bp"):
        """Cliffs where the levels step down (dev/tools/cliff_tiers.py): a higher level's south edge shows its face
        (rows tall, lip included), its sides a column of rock, its north edge the lip; tiers stand on one another, inside
        corners turn, paths crossing a cliff become stairs (still open). Rock tiles become c; the tiles to draw go in the
        map's roofs "_cliffs" (a tile set: rock_bp, Banished Platinum's). Run it again after changing levels: the last
        cliffs are cleared first. Returns how many cliff tiles there are."""
        extras = self.extra.setdefault("_roof_extras", {})
        art, cliffs = cliff_tiers.lay(self.art, self.levels, set_name, rows, extras.get("_cliffs"))
        self.art = [list(r) for r in art]
        if cliffs:
            extras["_cliffs"] = cliffs
        else:
            extras.pop("_cliffs", None)
        return sum(c != "." for r in (cliffs or {}).get("rock", ()) for c in r)


# ---------------------------------------------------------------- little widgets
class Button:
    def __init__(self, rect, text, fn, toggle=None):
        self.rect, self.text, self.fn, self.toggle = pygame.Rect(rect), text, fn, toggle

    def draw(self, s, font, mouse):
        on = self.toggle() if self.toggle else False
        col = ACCENT if on else ((86, 98, 132) if self.rect.collidepoint(mouse) else (66, 76, 104))
        pygame.draw.rect(s, col, self.rect, border_radius=6)
        pygame.draw.rect(s, PANEL_LINE, self.rect, 1, border_radius=6)
        t = font.render(self.text, True, TEXT)
        s.blit(t, t.get_rect(center=self.rect.center))

    def click(self, pos):
        if self.rect.collidepoint(pos):
            self.fn()
            return True
        return False


class Dropdown:
    def __init__(self, rect, items, on_pick, rows=14):
        self.rect, self.items, self.on_pick, self.rows = pygame.Rect(rect), items, on_pick, rows
        self.index, self.open, self.scroll = 0, False, 0

    def label(self):
        return self.items[self.index][1] if self.items else ""

    def draw(self, s, font, mouse):
        pygame.draw.rect(s, (30, 34, 48), self.rect, border_radius=6)
        pygame.draw.rect(s, ACCENT if self.open else PANEL_LINE, self.rect, 1, border_radius=6)
        t = font.render(self.label()[:40], True, TEXT)
        s.blit(t, (self.rect.x + 8, self.rect.centery - t.get_height() // 2))
        pygame.draw.polygon(s, DIM, [(self.rect.right - 18, self.rect.centery - 3), (self.rect.right - 8, self.rect.centery - 3),
                                     (self.rect.right - 13, self.rect.centery + 4)])

    def draw_list(self, s, font, mouse):
        if not self.open:
            return
        h = self.rect.h
        vis = self.items[self.scroll:self.scroll + self.rows]
        box = pygame.Rect(self.rect.x, self.rect.bottom + 2, self.rect.w, h * len(vis))
        pygame.draw.rect(s, (24, 28, 40), box)
        pygame.draw.rect(s, ACCENT, box, 1)
        for i, (_v, text) in enumerate(vis):
            r = pygame.Rect(box.x, box.y + i * h, box.w, h)
            if r.collidepoint(mouse) or self.scroll + i == self.index:
                pygame.draw.rect(s, (60, 80, 130), r)
            t = font.render(text[:44], True, TEXT)
            s.blit(t, (r.x + 8, r.centery - t.get_height() // 2))

    def event(self, e):
        """True if it took the event."""
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            if self.rect.collidepoint(e.pos):
                self.open = not self.open
                self.scroll = max(0, min(self.index - self.rows // 2, len(self.items) - self.rows))
                return True
            if self.open:
                h = self.rect.h
                i = (e.pos[1] - self.rect.bottom - 2) // h
                if self.rect.x <= e.pos[0] < self.rect.right and 0 <= i < min(self.rows, len(self.items) - self.scroll):
                    self.index = self.scroll + i
                    self.on_pick(self.items[self.index][0])
                self.open = False
                return True
        if e.type == pygame.MOUSEWHEEL and self.open:
            self.scroll = max(0, min(len(self.items) - self.rows, self.scroll - e.y * 3))
            return True
        return False

    def set_items(self, items, index=0):
        self.items, self.index = items, max(0, min(index, len(items) - 1))


class TextBox:
    def __init__(self, rect, text="", hint=""):
        self.rect, self.text, self.hint, self.focus = pygame.Rect(rect), text, hint, False

    def draw(self, s, font, mouse):
        pygame.draw.rect(s, (24, 28, 40), self.rect, border_radius=5)
        pygame.draw.rect(s, ACCENT if self.focus else PANEL_LINE, self.rect, 1, border_radius=5)
        t = font.render(self.text or self.hint, True, TEXT if self.text else DIM)
        s.blit(t, (self.rect.x + 6, self.rect.centery - t.get_height() // 2), (max(0, t.get_width() - self.rect.w + 12), 0, self.rect.w - 12, t.get_height()))
        if self.focus and (pygame.time.get_ticks() // 500) % 2:
            x = self.rect.x + 6 + min(t.get_width() if self.text else 0, self.rect.w - 12)
            pygame.draw.line(s, TEXT, (x, self.rect.y + 5), (x, self.rect.bottom - 5))

    def event(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.focus = self.rect.collidepoint(e.pos)
            return self.focus
        if self.focus and e.type == pygame.KEYDOWN:
            if e.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_ESCAPE, pygame.K_TAB):
                self.focus = False
            return True
        if self.focus and e.type == pygame.TEXTINPUT:
            self.text += e.text
            return True
        return False


class Slider:
    def __init__(self, rect, lo, hi, get, set_, label):
        self.rect, self.lo, self.hi, self.get, self.set, self.label, self.drag = pygame.Rect(rect), lo, hi, get, set_, label, False

    def draw(self, s, font, mouse):
        v = self.get()
        t = font.render(f"{self.label} {int(v)}", True, DIM)
        s.blit(t, (self.rect.x, self.rect.y - 2))
        bar = pygame.Rect(self.rect.x + 90, self.rect.centery - 3, self.rect.w - 90, 6)
        pygame.draw.rect(s, (24, 28, 40), bar, border_radius=3)
        k = (v - self.lo) / (self.hi - self.lo)
        pygame.draw.circle(s, ACCENT, (bar.x + int(k * bar.w), bar.centery), 8)

    def event(self, e):
        bar = pygame.Rect(self.rect.x + 90, self.rect.y, self.rect.w - 90, self.rect.h)
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and bar.collidepoint(e.pos):
            self.drag = True
        if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            was, self.drag = self.drag, False
            return was
        if self.drag and e.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
            k = max(0.0, min(1.0, (e.pos[0] - bar.x) / bar.w))
            self.set(self.lo + k * (self.hi - self.lo))
            return True
        return False


# ---------------------------------------------------------------- the park builder (Jordan, 11-15: "like Roller Coaster Tycoon")
# A second panel (the "Park builder" button, or P): every building, piece, prop and ground as a picture. Click one (or drag
# it onto the map) and a see-through copy follows the mouse, green where it fits, red where it doesn't; click to drop it,
# again and again. Drag anything placed to move it; right-click it to take it away. The ground brushes paint 1, 3 or 5
# tiles at a time (the game draws the edges); the height brush raises or lowers the ground and the cliffs rebuild when
# you let go (dev/tools/cliff_tiers.py).
BUILDER_TABS = ["Buildings", "Scenery", "Ground", "Height", "Ways out"]


def autotiles():
    """The ground you paint (assets/tiles/autotiles, kanto_handoff/tileset_catalog/autotiles.py): {name: meta}. Each one
    draws its own edges and corners from its neighbours (art.py _paint)."""
    try:
        with open(os.path.join("assets", "tiles", "autotiles", "index.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


AUTOTILES = autotiles()
# (Jordan, 11-15: the park builder offers only pictures from the games and tile artists, not the map maker's own drawn
#  buildings, scenery and ground; those stay in the classic panel's lists, and the game still draws maps with them)
HIDDEN = os.path.join("dev", "builders", "pieces", "hidden.json")
OURS = "Our own art"                 # (the map characters and buildings art.py draws itself)
GAME_SOURCES = ("FireRed / LeafGreen", "HeartGold / SoulSilver", "Diamond / Pearl / Platinum", "Black 2 / White 2")   # (read from
                                     # the games' own files: kanto_handoff/tileset_catalog/game_sets.py; listed first)     # (pictures hidden from the palette: right-click one)
THUMB = 88
CARRY_OVER = set('.=sd"f8T2,ape@r')   # (what a building or piece may be dropped on: its tiles are cleared)


def builder_items():
    """{tab: [item]}: an item is {"preset": PRESETS entry} (placed whole), {"char": c} (a brush), or {"height": op}."""
    pal = dict(PALETTE)
    out = {t: [] for t in BUILDER_TABS}
    game_groups = {"center": "Centers & Marts", "mart": "Centers & Marts", "house": "Houses", "home": "Houses", "rival": "Houses"}
    for p in PRESETS:
        if p[4]:
            out["Scenery" if p[4]["prop"] else "Buildings"].append({"preset": p, "label": p[4]["label"], "group": p[4]["group"],
                                                                     "source": p[4]["source"], "theme": p[4]["theme"],
                                                                     "gen": p[4]["gen"]})
        # (the map maker's own drawn buildings: the classic panel only)
    char_groups = {"T": "Trees & plants", "2": "Trees & plants", "r": "Rocks", "0": "Rocks", "b": "Rocks", "@": "Statues",
                   "!": "Signs & lamps", "l": "Signs & lamps"}
    for cat, tab in (("Ways out", "Ways out"), ("People", "Ways out")):      # (markers, not drawings: kept)
        for c, n in pal[cat]:
            group = cat if tab in ("Ground", "Ways out") else char_groups.get(c, "Fences & walls" if cat == "Fences & walls" else "Props")
            theme = {"8": "Snow", "%": "Snow", "9": "Swamp", "*": "Volcano", "s": "Tropical", "o": "Water", "~": "Water",
                     ":": "Water", "q": "Water", "$": "Water", "T": "Forest", "2": "Forest", "r": "Mountain", "b": "Mountain",
                     "0": "Mountain", "/": "Mountain", "@": "Ruins"}.get(c)
            out[tab].append({"char": c, "label": n, "group": group, "source": OURS, "theme": theme, "gen": "Ours"})
    for name, meta in AUTOTILES.items():     # (painted ground: its edges draw themselves)
        out["Ground"].append({"surface": name, "label": meta["label"], "group": meta.get("group", "Paths"),
                              "theme": meta.get("theme"), "source": meta.get("credit", "").split(" (")[0] or OURS})
    out["Ground"].append({"surface": "", "label": "Plain grass (rubs painted ground out)", "group": "Paths", "source": OURS})
    out["Ground"].append({"ledge": True, "label": "Ledge (drag along it)", "group": "Ledges", "source": OURS})
    out["Height"] = [{"height": "raise", "label": "Raise the ground"}, {"height": "lower", "label": "Lower the ground"}] + \
                    [{"height": i, "label": f"Level {i}"} for i in range(4)]
    return out


class ParkBuilder:
    """The park builder's panel and mouse handling (mixed into MapMaker)."""

    def _build_builder(self):
        x0 = self.screen.get_width() - PANEL_W + 14
        w = PANEL_W - 28
        self.b_items = builder_items()
        self.b_tab = getattr(self, "b_tab", "Buildings")
        self.b_scroll = {t: 0 for t in BUILDER_TABS}
        self.b_brush = getattr(self, "b_brush", 1)
        self.b_pick = None             # the chosen item (a brush or a thing to place)
        self.carry = None              # a thing following the mouse: {"preset" | "move", "w", "h", "ghost", "up", "grab"}
        self.b_stroke = None           # a brush stroke going on: the tiles it has touched
        self._thumbs = {}
        tw = (w - 4 * (len(BUILDER_TABS) - 1)) // len(BUILDER_TABS)
        self.b_tab_btns = [Button((x0 + i * (tw + 4), 76, tw, 28), t, lambda t=t: self.builder_tab(t), toggle=lambda t=t: self.b_tab == t)
                           for i, t in enumerate(BUILDER_TABS)]
        self.b_brush_btns = [Button((x0 + 96 + i * 52, 112, 46, 26), f"{n}x{n}" if isinstance(n, int) else n.title(),
                                    lambda n=n: setattr(self, "b_brush", n), toggle=lambda n=n: self.b_brush == n)
                             for i, n in enumerate((1, 3, 5, "box", "fill"))]
        self.b_box_from = None         # a box being dragged out (Ground: box): its first corner
        self.b_ledge = None            # a ledge being drawn: its tiles in the order dragged; then the last one drawn
        H = self.screen.get_height()
        self.b_search = getattr(self, "b_search", None) or TextBox((0, 0, 10, 10), "", "search: palm, house, Ekat99...")
        filt = lambda _v: self.pick_chip("b_source", self.b_source)     # (a list changed: back to the top of the pictures)
        self.b_set_dd = getattr(self, "b_set_dd", None) or Dropdown((0, 0, 10, 10), [], filt, rows=16)
        self.b_theme_dd = getattr(self, "b_theme_dd", None) or Dropdown((0, 0, 10, 10), [], filt, rows=14)
        self.b_gen_dd = getattr(self, "b_gen_dd", None) or Dropdown((0, 0, 10, 10), [], filt, rows=12)
        try:
            with open(HIDDEN, encoding="utf-8") as f:
                self.b_hidden = set(json.load(f))
        except (OSError, ValueError):
            self.b_hidden = set()
        self.b_show_hidden = getattr(self, "b_show_hidden", False)
        self.b_hidden_btn = Button((0, 0, 10, 10), f"Hidden ({len(self.b_hidden)})", self.toggle_show_hidden,
                                   toggle=lambda: self.b_show_hidden)
        self.b_group = getattr(self, "b_group", "All")
        self.b_source = getattr(self, "b_source", "All sets")
        self.b_grid = pygame.Rect(x0, 146, w, H - 146 - 322)
        self.b_grid_bottom = self.b_grid.bottom
        self.layout_chips()
        # the lower part of the panel: laid out by layout_bottom (the roof colours only for a chosen building, the
        # source picture's controls only while "Picture" is open), so the pictures get the rest
        z = (0, 0, 10, 10)
        self.b_roof_rects = [pygame.Rect(z) for _ in ROOF_PRESETS]
        self.b_detail_rect = pygame.Rect(x0, 0, w, 26)
        self.b_pic_open = getattr(self, "b_pic_open", bool(self.doc.ref))
        self.b_view_btns = [Button(z, "Game look", self.toggle_game, toggle=lambda: self.game_look),
                            Button(z, "Grid", lambda: setattr(self, "show_grid", not self.show_grid), toggle=lambda: self.show_grid),
                            Button(z, "Levels", lambda: setattr(self, "show_levels", not self.show_levels), toggle=lambda: self.show_levels),
                            Button(z, "Picture", lambda: setattr(self, "b_pic_open", not self.b_pic_open), toggle=lambda: self.b_pic_open),
                            Button(z, "Undo", self.undo)]
        self.b_src_btns = [Button(z, "Load...", self.browse_ref), Button(z, "Fit map", self.fit_to_ref),
                           Button(z, "Show", lambda: setattr(self, "show_ref", not self.show_ref), toggle=lambda: self.show_ref),
                           Button(z, "On top", self.toggle_ref_under, toggle=self.ref_under)]
        self.b_ref_alpha = Slider(z, 0, 255, lambda: (self.doc.ref or {}).get("alpha", 140), self._set_ref_alpha, "Strength")
        self.b_frame_btns = [Button(z, "Move / size", self.toggle_ref_adjust, toggle=lambda: getattr(self, "ref_adjust", False)),
                             Button(z, "Keep shape", self.ref_keep_shape), Button(z, "Size", self.ref_size_cycle),
                             Button(z, "Remove", self.remove_ref)]
        self._bottom_key = None
        self.layout_bottom()

    def layout_bottom(self):
        """Lay out the panel's lower part from the bottom up; the pictures fill what's left above it."""
        key = (self.screen.get_size(), bool(self.selected), bool(self.detail), self.b_pic_open)
        if key == self._bottom_key:
            return
        self._bottom_key = key
        x0 = self.screen.get_width() - PANEL_W + 14
        w = PANEL_W - 28
        y = self.screen.get_height() - 22
        self.b_hint_y = y
        y -= 34
        widths = [92, 52, 62, 68]
        x = x0
        for b, bw in zip(self.b_view_btns, widths + [w - sum(widths) - 4 * 6]):
            b.rect = pygame.Rect(x, y, bw, 28)
            x += bw + 6
        if self.b_pic_open:
            y -= 34
            for b, (dx, bw) in zip(self.b_frame_btns, ((0, 104), (110, 98), (214, 100), (320, w - 320))):
                b.rect = pygame.Rect(x0 + dx, y, bw, 28)
            y -= 26
            self.b_ref_alpha.rect = pygame.Rect(x0, y, w, 18)
            y -= 34
            for b, (dx, bw) in zip(self.b_src_btns, ((0, 96), (102, 74), (182, 64), (252, w - 252))):
                b.rect = pygame.Rect(x0 + dx, y, bw, 28)
            y -= 22
            self.b_src_y = y
        if self.detail:
            y -= 34
            self.b_detail_rect.y = y
            self.detail_box.rect = pygame.Rect(self.b_detail_rect)
            y -= 18
        if self.selected:
            y -= 28
            for i, r in enumerate(self.b_roof_rects):
                r.update(x0 + i * 32, y, 28, 22)
            y -= 22
            self.b_roof_y = y
        self.b_grid_bottom = y - 24
        if hasattr(self, "b_chips"):
            self.layout_chips()

    def toggle_builder(self):
        self.builder = not self.builder
        self.carry, self.b_pick, self.b_stroke = None, None, None
        self.detail_box.rect = pygame.Rect(self.b_detail_rect if self.builder else self.detail_rect_classic)
        self.set_detail(None)
        self.status = ("Park builder: pick a picture on the right, then click the map (or drag it there)" if self.builder
                       else "Classic panel")

    def layout_chips(self):
        """The group and source chips for this tab (wrapping onto more rows), the pictures below them."""
        x0 = self.screen.get_width() - PANEL_W + 14
        w = PANEL_W - 28
        items = self.b_items[self.b_tab]
        groups = ["All"] + [g for g in GROUPS.get(self.b_tab, []) if any(i.get("group") == g for i in items)]
        self.b_chips = []
        y = 112
        for row, values, cur, attr in ((0, groups, self.b_group, "b_group"),):
            if len(values) <= 2:
                continue
            x = x0
            for v in values:
                tw = self.small.size(v)[0] + 14
                if x + tw > x0 + w:
                    x, y = x0, y + 26
                self.b_chips.append(Button((x, y, tw, 22), v, lambda v=v, a=attr: self.pick_chip(a, v),
                                           toggle=lambda v=v, a=attr: getattr(self, a) == v))
                x += tw + 4
            y += 28
        # the search box, the hidden pieces' button, and the set / theme / generation lists
        self.b_search.rect = pygame.Rect(x0, y, w - 120, 26)
        self.b_hidden_btn.rect = pygame.Rect(x0 + w - 114, y, 114, 26)
        y += 32
        sets = sorted({i.get("source", OURS) for i in items}, key=lambda v: (v != OURS, v not in GAME_SOURCES, v.lower()))
        themes = [t for t in THEMES if any(i.get("theme") == t for i in items)]
        gens = sorted({i.get("gen") for i in items if i.get("gen")}, key=lambda g: (g == "Ours", g))
        dw = (w - 8) // 3
        for k, (dd, label, values) in enumerate(((self.b_set_dd, "Any tile set", sets), (self.b_theme_dd, "Any theme", themes),
                                                 (self.b_gen_dd, "Any generation", gens))):
            dd.rect = pygame.Rect(x0 + k * (dw + 4), y, dw, 26)
            cur = dd.items[dd.index][0] if dd.items else None
            dd.set_items([(None, label)] + [(v, v) for v in values])
            dd.index = next((n for n, (v, _t) in enumerate(dd.items) if v == cur), 0)
        y += 32
        self.b_brush_y = y
        for i, b in enumerate(self.b_brush_btns):
            b.rect.y = y
        if self.b_tab in ("Ground", "Height", "Ways out"):
            y += 32
        self.b_grid = pygame.Rect(x0, y + 4, w, self.b_grid_bottom - y - 4)

    def pick_chip(self, attr, v):
        setattr(self, attr, v)
        self.b_scroll[self.b_tab] = 0

    def items_view(self):
        """This tab's pictures, filtered by the group chip, the set / theme / generation lists, the search words and
        the hidden list (a hidden picture shows only while "Hidden" is on)."""
        pick = lambda dd: dd.items[dd.index][0] if dd.items else None
        st, th, gn = pick(self.b_set_dd), pick(self.b_theme_dd), pick(self.b_gen_dd)
        words = self.b_search.text.lower().split()
        out = []
        for i in self.b_items[self.b_tab]:
            hidden = self.item_key(i) in self.b_hidden
            if hidden != self.b_show_hidden:
                continue
            if self.b_group != "All" and i.get("group") != self.b_group:
                continue
            if (st and i.get("source", OURS) != st) or (th and i.get("theme") != th) or (gn and i.get("gen") != gn):
                continue
            text = f"{i['label']} {i.get('source', '')} {i.get('theme') or ''} {i.get('group', '')}".lower()
            if any(wd not in text for wd in words):
                continue
            out.append(i)
        return out

    @staticmethod
    def item_key(i):
        if "surface" in i:
            return "surface:" + i["surface"]
        if "ledge" in i:
            return "ledge"
        return i["preset"][4]["key"] if "preset" in i and i["preset"][4] else (
            "game:" + i["preset"][0] if "preset" in i else "char:" + i["char"] if "char" in i else f"height:{i['height']}")

    def toggle_hidden_item(self, item):
        """Right-click a picture: hide it from the palette (or, while "Hidden" is on, bring it back)."""
        k = self.item_key(item)
        if k in self.b_hidden:
            self.b_hidden.discard(k)
            self.status = f"{item['label']}: back in the palette"
        else:
            self.b_hidden.add(k)
            self.status = f"{item['label']}: hidden (the Hidden button shows hidden pieces; right-click one to bring it back)"
        try:
            with open(HIDDEN, "w", encoding="utf-8", newline="\n") as f:
                json.dump(sorted(self.b_hidden), f, indent=1)
                f.write("\n")
        except OSError:
            pass
        self.b_hidden_btn.text = f"Hidden ({len(self.b_hidden)})"

    def toggle_show_hidden(self):
        self.b_show_hidden = not self.b_show_hidden
        self.b_scroll[self.b_tab] = 0

    def builder_tab(self, t):
        self.b_tab = t
        if t != "Ground" and not isinstance(self.b_brush, int):
            self.b_brush = 1
        self.b_group, self.b_source = "All", "All sets"
        for dd in (self.b_set_dd, self.b_theme_dd, self.b_gen_dd):
            dd.index, dd.open = 0, False
        self.b_scroll[t] = 0
        self.layout_chips()
        self.carry, self.b_pick = None, None
        self.show_levels = t == "Height"

    # ---- pictures
    def thumb(self, item):
        key = json.dumps({k: (v[0] if k == "preset" else v) for k, v in item.items() if k != "label"}, default=str)
        if key not in self._thumbs:
            if "preset" in item:
                img, _fx, _fy, _up = self.preset_picture(item["preset"])
            elif "char" in item:
                img = self.preview(("a", item["char"]), self.asset_rows(item["char"]))
            elif "ledge" in item:
                img = self.preview(("a", "_"), self.asset_rows("_"))
            elif "surface" in item:
                name = item["surface"]
                ch = AUTOTILES[name]["char"] if name else "."
                rows = [".....", "." + ch * 3 + ".", ch * 4 + ".", "." + ch * 3 + ".", "....."]
                paint = {"key": {"a": name}, "rows": ["".join("a" if c == ch else "." for c in r) for r in rows]} if name else None
                img = self.preview(("surface", name), rows, None, {"_paint": paint} if paint else {})
            else:
                img = pygame.Surface((96, 96))
                op = item["height"]
                img.fill((90, 150, 90) if op in ("raise", "lower") else [(60, 70, 140), (70, 140, 70), (200, 160, 40), (200, 70, 60)][op])
                if op in ("raise", "lower"):
                    pts = [(48, 18), (80, 60), (16, 60)] if op == "raise" else [(48, 78), (80, 36), (16, 36)]
                    pygame.draw.polygon(img, (250, 250, 250), pts)
                else:
                    t = self.big.render(f"L{op}", True, (255, 255, 255))
                    img.blit(t, t.get_rect(center=(48, 48)))
            sc = min(THUMB / img.get_width(), THUMB / img.get_height())
            self._thumbs[key] = pygame.transform.smoothscale(img, (max(1, int(img.get_width() * sc)), max(1, int(img.get_height() * sc))))
        return self._thumbs[key]

    def preset_picture(self, preset):
        """A preset as the game draws it: (picture, footprint x, footprint y, tiles of picture above the footprint)."""
        name, kind, w, h, piece = preset
        if piece:
            rows = ["." * (w + 2)] * 3 + ["." + ("`" if piece["prop"] else "A") * w + "." for _ in range(h)] + ["." * (w + 2)]
            if not piece["prop"]:
                last = list(rows[-2])
                for d in piece["doors"]:
                    last[1 + d] = "D"
                rows[-2] = "".join(last)
            roofs = {"_objects": [{"k": piece["key"], "at": [1, 3]}]} if piece["prop"] else {"A": {"model": piece["key"]}}
            return self.preview(("lib", piece["key"]), rows, {"A": kind}, roofs), 1, 3, 3
        rows = ["." * (w + 2)] + ["." + "A" * w + "." for _ in range(h - 1)] + ["." + "A" * (w // 2) + "D" + "A" * (w - w // 2 - 1) + "."] + ["." * (w + 2)]
        return self.preview(("bld", name), rows, {"A": kind}), 1, 1, 1

    @staticmethod
    def ghost_of(img, fx, fy, w, h, up):
        """The see-through copy that follows the mouse: the footprint's columns, from the picture's top to the footprint's foot."""
        T = GAME_TILE
        g = img.subsurface((fx * T, (fy - up) * T, w * T, (h + up) * T)).copy()
        g.set_alpha(185)
        return g

    # ---- placing
    def fits(self, x, y, w, h):
        if not (0 <= x and 0 <= y and x + w <= self.doc.w and y + h <= self.doc.h):
            return False
        c = self.carry or {}
        piece = c["preset"][4] if c.get("preset") else (c.get("move") or {}).get("piece")
        ok = CARRY_OVER | ({"c"} if piece and piece.get("walk") else set())      # (stairs may cut through a cliff)
        return all(self.doc.cell(xx, yy) in ok and not self.doc.owner(xx, yy)
                   for yy in range(y, y + h) for xx in range(x, x + w))

    def carry_spot(self, pos):
        tx, ty = self.to_tile(pos)
        gx, gy = self.carry["grab"]
        return tx - gx, ty - gy

    def b_pick_item(self, item):
        self.b_pick = item
        self.carry = None
        self.set_detail(None)
        if "preset" in item:
            name, kind, w, h, piece = item["preset"]
            img, fx, fy, up = self.preset_picture(item["preset"])
            self.carry = {"preset": item["preset"], "w": w, "h": h, "up": up, "ghost": self.ghost_of(img, fx, fy, w, h, up),
                          "grab": (w // 2, h // 2)}
            self.status = f"{item['label']}: click the map to place it (right-click or Esc: put it down)"
        elif "char" in item:
            self.status = f"Brush: {item['label']} ({self.brush_n()}x{self.brush_n()}) - click or drag on the map"
        elif "ledge" in item:
            self.status = ("Ledge: drag along it. Across the map it hops south; up or down it hops toward the lower ground, "
                           "else dragged down hops east, dragged up hops west (F flips it)")
        elif "surface" in item:
            how = {"box": "drag out a box", "fill": "click to fill the whole stretch"}.get(self.b_brush, "click or drag to paint")
            self.status = f"{item['label']}: {how}; the edges and corners draw themselves"
        else:
            op = item["height"]
            self.show_levels = True
            self.status = ("Drag to raise the ground a level" if op == "raise" else "Drag to lower the ground a level" if op == "lower"
                           else f"Drag to set the ground to level {op}") + "; the cliffs rebuild when you let go"

    def drop(self, x, y):
        """Put the carried thing down at (x, y): True if it went down."""
        c = self.carry
        if not self.fits(x, y, c["w"], c["h"]):
            return False
        prop = ("move" in c and c["move"]["type"] == "object") or ("preset" in c and bool(c["preset"][4]) and c["preset"][4]["prop"])
        for yy in range(y, y + c["h"]):          # (trees and props under it go; a placed piece keeps painted ground under it)
            for xx in range(x, x + c["w"]):
                if prop and (xx, yy) in self.doc.paint and self.doc.cell(xx, yy) == self.doc.painted_char(xx, yy):
                    continue
                if self.doc.cell(xx, yy) != ".":
                    self.doc.set(xx, yy, ".")
        if "move" in c:
            m = c["move"]
            if m["type"] == "object":
                self.doc.place_object(x, y, m["piece"])
            else:
                L = self.doc.place_building(x, y, c["w"], c["h"], m["kind"], name=m["name"], doors=m["doors"])
                if L and m["roof"] is not None:
                    self.doc.roofs[L] = m["roof"]
                self.select(L)
        else:
            name, kind, w, h, piece = c["preset"]
            if piece and piece["prop"]:
                self.doc.place_object(x, y, piece)
            elif piece:
                L = self.doc.place_building(x, y, w, h, kind, name=piece["label"], doors=piece["doors"])
                if L:
                    self.doc.roofs[L] = {"model": piece["key"]}
                    self.select(L)
            else:
                L = self.doc.place_building(x, y, w, h, kind)
                if L:
                    self.select(L)
        self.changed()
        return True

    def piece_tile(self, pos):
        """The tile under the mouse, or, when the mouse is on the visible part of a ready-made piece's picture that
        stands above its footprint (a tall tower, a tree's crown), a tile of that piece's footprint: the frontmost
        piece whose picture is solid there. So a piece is picked, moved or taken away by clicking any of it."""
        tx, ty = self.to_tile(pos)
        if self.doc.owner(tx, ty) or self.doc.object_at(tx, ty):
            return tx, ty
        mx, my = (pos[0] - self.ox) * 32 / self.zoom, (pos[1] - self.oy) * 32 / self.zoom
        best = None

        def hit(key, fx, fy, front, tile):
            nonlocal best
            m = self.art._model(key)
            if not m:
                return
            pic, ox, oy = m
            px, py = int(mx - (fx * 32 - ox)), int(my - (fy * 32 - oy))
            if 0 <= px < pic.get_width() and 0 <= py < pic.get_height() and pic.get_at((px, py)).a > 40:
                if best is None or front > best[0]:
                    best = (front, tile)
        for L in self.doc.buildings:
            roof = self.doc.roofs.get(L)
            r = self.doc.rect_of(L)
            if r and isinstance(roof, dict) and roof.get("model"):
                hit(roof["model"], r[0], r[1], r[1] + r[3], (r[0], r[1]))
        for o in self.doc.objects:
            p = next((q for q in LIBRARY if q["key"] == o["k"]), None)
            hit(o["k"], o["at"][0], o["at"][1], o["at"][1] + (p["h"] if p else 1), tuple(o["at"]))
        return best[1] if best else (tx, ty)

    def pick_up(self, tx, ty):
        """Lift the building or piece at (tx, ty) off the map to carry it (the map keeps a copy to put back)."""
        surf = self.game_surface() and self._game[1]
        L = self.doc.owner(tx, ty)
        o = None if L else self.doc.object_at(tx, ty)
        if not L and not o:
            return False
        self.push()
        if L:
            x, y, w, h = self.doc.rect_of(L)
            doors = [dx for dx in range(w) if self.doc.cell(x + dx, y + h - 1) == "D"]
            move = {"type": "building", "kind": self.doc.buildings.get(L, "house"), "name": self.doc.names.get(L),
                    "roof": copy.deepcopy(self.doc.roofs.get(L)), "doors": doors, "from": (x, y)}
        else:
            p = next((q for q in LIBRARY if q["key"] == o["k"]), None)
            if not p:
                self.undo_stack.pop()
                return False
            x, y = o["at"]
            w, h = p["w"], p["h"]
            move = {"type": "object", "piece": p, "from": (x, y)}
        up = min(3, y)
        ghost = None
        if surf is not None:
            ghost = surf.subsurface((x * GAME_TILE, (y - up) * GAME_TILE, w * GAME_TILE, (h + up) * GAME_TILE)).copy()
            ghost.set_alpha(185)
        if L:
            self.doc.remove_building(L)
            self.selected = None
        else:
            self.doc.remove_object_at(x, y)
        self.carry = {"move": move, "w": w, "h": h, "up": up, "ghost": ghost, "grab": (tx - x, ty - y)}
        self.changed()
        self.status = "Moving it: let go where it should stand"
        return True

    def take_away(self, tx, ty):
        L = self.doc.owner(tx, ty)
        if L:
            self.push()
            self.doc.remove_building(L)
            self.selected = None if self.selected == L else self.selected
        elif self.doc.object_at(tx, ty):
            self.push()
            self.doc.remove_object_at(tx, ty)
        elif self.doc.cell(tx, ty) not in (".", None):
            self.push()
            self.doc.set(tx, ty, ".")
        else:
            return
        self.changed()
        self.status = "Taken away (Ctrl+Z puts it back)"

    def brush_at(self, tx, ty):
        item = self.b_pick
        if "surface" in item or "ledge" in item:
            return self.ground_at(tx, ty)
        r = self.brush_n() // 2
        for yy in range(ty - r, ty + r + 1):
            for xx in range(tx - r, tx + r + 1):
                if not (0 <= xx < self.doc.w and 0 <= yy < self.doc.h) or (xx, yy) in self.b_stroke:
                    continue
                self.b_stroke.add((xx, yy))
                if "height" in item:
                    op, lv = item["height"], self.doc.levels[yy][xx]
                    self.doc.levels[yy][xx] = max(0, min(3, lv + 1 if op == "raise" else lv - 1 if op == "lower" else op))
                else:
                    c = item["char"]
                    if self.doc.owner(xx, yy) or self.doc.cell(xx, yy) == "`":
                        continue            # (a brush paints round buildings and pieces, never over them)
                    self.doc.set(xx, yy, c)
                    if c == "N":
                        self.doc.people.setdefault((xx, yy), "someone")
                    if c == "!":
                        self.doc.signs.setdefault((xx, yy), ["A sign."])
        if "char" in item:
            self.changed()

    def brush_n(self):
        """The brush's width in tiles (a box or a fill: one tile at a time where they don't apply)."""
        return self.b_brush if isinstance(self.b_brush, int) else 1

    def brush_buttons(self):
        return self.b_brush_btns if self.b_tab == "Ground" else self.b_brush_btns[:3]

    def ground_at(self, tx, ty):
        """The Ground tab's brush: paint a surface (its edges draw themselves), or lay a ledge tile."""
        item = self.b_pick
        if "ledge" in item:
            if (tx, ty) not in self.b_stroke and 0 <= tx < self.doc.w and 0 <= ty < self.doc.h and not self.doc.owner(tx, ty) \
                    and self.doc.cell(tx, ty) not in ("`", "c"):
                self.b_stroke.add((tx, ty))
                self.b_ledge["cells"].append((tx, ty))
                self.doc.set(tx, ty, "_")
                self.changed()
            return
        if self.b_brush == "box":
            return                      # (a box is laid when the mouse comes up)
        if self.b_brush == "fill":
            self.fill_ground(tx, ty, item["surface"])
            return
        r = self.brush_n() // 2
        for yy in range(ty - r, ty + r + 1):
            for xx in range(tx - r, tx + r + 1):
                if (xx, yy) not in self.b_stroke:
                    self.b_stroke.add((xx, yy))
                    self.doc.paint_cell(xx, yy, item["surface"])
        self.changed()

    def fill_ground(self, tx, ty, name):
        """Paint the whole stretch of like ground round (tx, ty): every tile joined to it (not corner to corner) with the
        same character and paint, up to buildings, pieces and anything different."""
        d = self.doc
        if not (0 <= tx < d.w and 0 <= ty < d.h):
            return 0
        like = (d.cell(tx, ty), d.paint.get((tx, ty), ""))
        todo, seen = [(tx, ty)], set()
        while todo:
            x, y = todo.pop()
            if (x, y) in seen or not (0 <= x < d.w and 0 <= y < d.h) or (d.cell(x, y), d.paint.get((x, y), "")) != like \
                    or d.owner(x, y):
                continue
            seen.add((x, y))
            todo += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
        n = sum(d.paint_cell(x, y, name) for x, y in seen)
        self.changed()
        self.status = f"Filled {n} tiles" + (" (the edges draw themselves)" if name else " with plain grass")
        return n

    def box_ground(self, a, b, name):
        (x0, y0), (x1, y1) = a, b
        n = sum(self.doc.paint_cell(x, y, name) for y in range(min(y0, y1), max(y0, y1) + 1) for x in range(min(x0, x1), max(x0, x1) + 1))
        self.changed()
        self.status = f"Painted a box of {n} tiles"

    def finish_ledge(self):
        """Which way the ledge just drawn faces: a run across the map hops south; a run up or down it hops toward the
        lower ground (by the levels), else the way the drag went: dragged down, it hops east; dragged up, west (F flips
        it). Each tile is the part of the run it's on, so an L-shaped ledge turns its corner."""
        cells = self.b_ledge["cells"]
        if not cells:
            return
        on = set(cells)
        lv = lambda x, y: self.doc.levels[y][x] if 0 <= x < self.doc.w and 0 <= y < self.doc.h else None
        west = sum((lv(x - 1, y) or 0) for x, y in cells)
        east = sum((lv(x + 1, y) or 0) for x, y in cells)
        down = cells[-1][1] >= cells[0][1]
        side = ")" if east < west else "(" if west < east else (")" if down else "(")
        for x, y in cells:
            across = (x - 1, y) in on or (x + 1, y) in on or not ((x, y - 1) in on or (x, y + 1) in on)
            self.doc.art[y][x] = "_" if across else side
        self.b_ledge = {"cells": [], "last": cells}
        self.changed()
        kinds = {self.doc.art[y][x] for x, y in cells}
        self.status = ("Ledge laid: " + ", ".join({"_": "hop south", "(": "hop west", ")": "hop east"}[k] for k in sorted(kinds))
                       + ("  (F flips the side ones)" if kinds - {"_"} else ""))

    def flip_ledge(self):
        last = (self.b_ledge or {}).get("last") or []
        side = [(x, y) for x, y in last if self.doc.cell(x, y) in ("(", ")")]
        if not side:
            return False
        self.push()
        for x, y in side:
            self.doc.art[y][x] = "(" if self.doc.art[y][x] == ")" else ")"
        self.changed()
        self.status = "Ledge flipped: it hops " + ("west" if self.doc.cell(*side[0]) == "(" else "east")
        return True

    def end_stroke(self):
        if self.b_stroke is None:
            return
        item = self.b_pick
        if item and "ledge" in item:
            self.finish_ledge()
        elif item and "surface" in item and self.b_brush == "box" and self.b_box_from:
            self.box_ground(self.b_box_from, self.b_box_to, item["surface"])
        self.b_box_from = None
        if item and "height" in item:
            n = self.doc.cliffs_from_levels()
            self.changed()
            self.status = f"Ground reshaped; {n} cliff tiles" if n else "Ground reshaped (all one level: no cliffs)"
        elif item and item.get("char") and item["char"] in EXIT_CHARS + "N!":
            x, y = next(iter(self.b_stroke))
            c = item["char"]
            self.set_detail(("exit", c) if c in EXIT_CHARS else ("person", (x, y)) if c == "N" else ("sign", (x, y)))
            self.status = "Fill in the box below the pictures (where it leads / who / what it says)"
        self.b_stroke = None

    # ---- events
    def builder_event(self, e):
        """True if the park builder took the event (else the map maker's own handling goes on: zoom, pan, keys)."""
        self.layout_bottom()
        panel = pygame.Rect(self.screen.get_width() - PANEL_W, 0, PANEL_W, self.screen.get_height())
        canvas = self.canvas_rect()
        for dd in (self.b_set_dd, self.b_theme_dd, self.b_gen_dd):
            if dd.open and dd.event(e):
                self.b_scroll[self.b_tab] = 0
                return True
        if e.type == pygame.MOUSEBUTTONDOWN and getattr(e, "button", 0) == 1:
            for dd in (self.b_set_dd, self.b_theme_dd, self.b_gen_dd):
                if dd.rect.collidepoint(e.pos):
                    for o in (self.b_set_dd, self.b_theme_dd, self.b_gen_dd):
                        o.open = False
                    dd.event(e)
                    return True
        if self.b_search.focus and e.type in (pygame.KEYDOWN, pygame.TEXTINPUT):
            self.b_search.event(e)
            self.b_scroll[self.b_tab] = 0
            return True
        typing = self.key_box.focus or self.detail_box.focus or self.b_search.focus
        if getattr(self, "ref_adjust", False) and self.doc.ref and not typing and self.ref_frame_event(e):
            return True
        if e.type == pygame.KEYDOWN or e.type == pygame.TEXTINPUT:
            for b in (self.key_box, self.detail_box):
                if b.focus and b.event(e):
                    if b is self.detail_box:
                        self.detail_changed()
                    return True
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.put_down()
                return True
            if e.type == pygame.KEYDOWN and e.key == pygame.K_f and not typing and self.flip_ledge():
                return True
            return False
        if e.type == pygame.MOUSEWHEEL and panel.collidepoint(pygame.mouse.get_pos()):
            n = len(self.items_view())
            cols = max(1, self.b_grid.w // (THUMB + 8))
            rows_fit = max(1, self.b_grid.h // (THUMB + 26))
            self.b_scroll[self.b_tab] = max(0, min(max(0, (n + cols - 1) // cols - rows_fit), self.b_scroll[self.b_tab] - e.y))
            return True
        pos = getattr(e, "pos", None)
        if self.b_ref_alpha.drag and e.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP):
            self.b_ref_alpha.event(e)
            return True
        if e.type == pygame.MOUSEBUTTONDOWN and pos and panel.collidepoint(pos):
            if e.button == 3:
                item = self.item_at(pos)
                if item:
                    self.toggle_hidden_item(item)
                return True
            if e.button != 1:
                return True
            for b in (self.key_box, self.detail_box, self.b_search):
                b.event(e)
            if self.b_pic_open and self.b_ref_alpha.event(e):
                return True
            pic = self.b_src_btns + self.b_frame_btns if self.b_pic_open else []
            for b in [self.btn_save, self.btn_builder, self.b_hidden_btn] + self.b_tab_btns + self.b_chips + self.brush_buttons() + self.b_view_btns + pic:
                if b.click(pos):
                    return True
            for i, r in enumerate(self.b_roof_rects):
                if r.collidepoint(pos) and self.selected:
                    self.push()
                    self.put_roof(self.selected, ROOF_PRESETS[i])
                    return True
            item = self.item_at(pos)
            if item:
                self.b_pick_item(item)
                self.drag_from_panel = "preset" in item
            return True
        if not pos:
            return False
        if e.type == pygame.MOUSEBUTTONDOWN and canvas.collidepoint(pos):
            if e.button == 2 or (e.button == 1 and pygame.key.get_pressed()[pygame.K_SPACE]):
                return False                   # (panning: the map maker's own)
            tx, ty = self.to_tile(pos)
            if e.button == 3:
                if self.carry:
                    self.put_down()
                elif 0 <= tx < self.doc.w and 0 <= ty < self.doc.h:
                    self.take_away(*self.piece_tile(pos))
                return True
            if e.button != 1 or not (0 <= tx < self.doc.w and 0 <= ty < self.doc.h):
                return True
            if self.carry and "preset" in self.carry:
                x, y = self.carry_spot(pos)
                self.push()
                if self.drop(x, y):
                    self.status = f"Placed. Click again for another, right-click to put it down"
                else:
                    self.undo_stack.pop()
                    self.status = "It doesn't fit there (red): something's in the way, or it's off the map"
                return True
            if self.b_pick and any(k in self.b_pick for k in ("char", "height", "surface", "ledge")):
                self.push()
                self.b_stroke = set()
                if "ledge" in self.b_pick:
                    self.b_ledge = {"cells": [], "last": (self.b_ledge or {}).get("last")}
                if "surface" in self.b_pick and self.b_brush == "box":
                    self.b_box_from = self.b_box_to = (tx, ty)
                self.brush_at(tx, ty)
                return True
            if not self.pick_up(*self.piece_tile(pos)):
                self.select(None)
            return True
        if e.type == pygame.MOUSEMOTION:
            if self.b_stroke is not None and canvas.collidepoint(pos):
                tx, ty = self.to_tile(pos)
                if self.b_box_from:
                    self.b_box_to = (max(0, min(self.doc.w - 1, tx)), max(0, min(self.doc.h - 1, ty)))
                elif not (self.b_pick and "surface" in self.b_pick and self.b_brush == "fill"):
                    self.brush_at(tx, ty)
                return True
            return False
        if e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            if self.b_stroke is not None:
                self.end_stroke()
                return True
            if self.carry and "move" in self.carry:
                x, y = self.carry_spot(pos) if canvas.collidepoint(pos) else (-99, -99)
                if not self.drop(x, y):
                    self.drop(*self.carry["move"]["from"])
                    self.status = "It doesn't fit there: put back where it was"
                else:
                    self.status = "Moved"
                self.carry = None
                return True
            if self.carry and "preset" in self.carry and getattr(self, "drag_from_panel", False) and canvas.collidepoint(pos):
                x, y = self.carry_spot(pos)       # (dragged from a picture straight onto the map)
                self.push()
                if self.drop(x, y):
                    self.status = "Placed. Click again for another, right-click to put it down"
                else:
                    self.undo_stack.pop()
            self.drag_from_panel = False
            return panel.collidepoint(pos)
        return False

    def put_down(self):
        if self.carry and "move" in self.carry:
            self.drop(*self.carry["move"]["from"])
        self.carry, self.b_pick = None, None
        self.status = "Nothing in hand"

    def item_at(self, pos):
        g = self.b_grid
        if not g.collidepoint(pos):
            return None
        cols = max(1, g.w // (THUMB + 8))
        c, r = (pos[0] - g.x) // (THUMB + 8), (pos[1] - g.y) // (THUMB + 26)
        if c >= cols:
            return None
        i = (r + self.b_scroll[self.b_tab]) * cols + c
        items = self.items_view()
        return items[i] if 0 <= i < len(items) else None

    # ---- drawing
    def draw_builder_panel(self, mouse):
        self.layout_bottom()
        s = self.screen
        px = s.get_width() - PANEL_W
        pygame.draw.rect(s, PANEL, (px, 0, PANEL_W, s.get_height()))
        pygame.draw.line(s, PANEL_LINE, (px, 0), (px, s.get_height()))
        x0 = px + 14
        s.blit(self.big.render("Map key", True, TEXT), (x0, 12))
        for w in [self.key_box, self.btn_save, self.btn_builder] + self.b_tab_btns:
            w.draw(s, self.font, mouse)
        for b in self.b_chips:
            b.draw(s, self.small, mouse)
        self.b_search.draw(s, self.font, mouse)
        self.b_hidden_btn.draw(s, self.small, mouse)
        for dd in (self.b_set_dd, self.b_theme_dd, self.b_gen_dd):
            dd.draw(s, self.small, mouse)
        if self.b_tab in ("Ground", "Height", "Ways out"):
            s.blit(self.font.render("Brush size", True, DIM), (x0, self.b_brush_y + 4))
            for b in self.brush_buttons():
                b.draw(s, self.font, mouse)
        elif not self.b_chips:
            s.blit(self.small.render("Click a picture, then the map. Drag placed things to move them.", True, DIM), (x0, 118))
        g = self.b_grid
        pygame.draw.rect(s, (36, 40, 56), g, border_radius=6)
        s.set_clip(g)
        cols = max(1, g.w // (THUMB + 8))
        items = self.items_view()
        start = self.b_scroll[self.b_tab] * cols
        for n, item in enumerate(items[start:]):
            c, r = n % cols, n // cols
            cell = pygame.Rect(g.x + c * (THUMB + 8) + 2, g.y + r * (THUMB + 26) + 4, THUMB + 4, THUMB + 22)
            if cell.y > g.bottom:
                break
            chosen = item is self.b_pick
            pygame.draw.rect(s, (70, 96, 150) if chosen else (60, 70, 96) if cell.collidepoint(mouse) else (48, 54, 74), cell, border_radius=6)
            if chosen:
                pygame.draw.rect(s, ACCENT, cell, 2, border_radius=6)
            im = self.thumb(item)
            s.blit(im, (cell.centerx - im.get_width() // 2, cell.y + 2 + (THUMB - im.get_height()) // 2))
            t = self.small.render(item["label"][:15], True, TEXT)
            s.blit(t, (cell.centerx - t.get_width() // 2, cell.bottom - 18))
        s.set_clip(None)
        if self.selected:
            s.blit(self.font.render("Roof colour of the chosen building", True, DIM), (x0, self.b_roof_y))
            for i, r in enumerate(self.b_roof_rects):
                pygame.draw.rect(s, ROOF_PRESETS[i], r, border_radius=4)
                pygame.draw.rect(s, (255, 255, 255) if list(ROOF_PRESETS[i]) == list(self._roof()) else PANEL_LINE, r, 2, border_radius=4)
        if self.detail:
            label = {"exit": "Leads to:", "person": "This person:", "sign": "This sign says:"}[self.detail[0]]
            s.blit(self.small.render(label, True, TEXT), (self.detail_box.rect.x, self.detail_box.rect.y - 18))
            self.detail_box.draw(s, self.font, mouse)
        for b in self.b_view_btns:
            b.draw(s, self.font, mouse)
        if self.b_pic_open:
            name = os.path.basename(self.doc.ref["path"]) if self.doc.ref else "none (Load..., or drop one on the map)"
            s.blit(self.font.render(f"Source picture: {name}"[:54], True, DIM), (x0, self.b_src_y))
            self.b_src_btns[3].text = self.REF_MODES[self.ref_mode()]
            for b in self.b_src_btns:
                b.draw(s, self.font, mouse)
            self.b_ref_alpha.draw(s, self.small, mouse)
            for b in self.b_frame_btns:
                b.draw(s, self.font, mouse)
        s.blit(self.small.render("Right-click: take away / put down   Esc: empty hand   wheel: zoom", True, DIM), (x0, self.b_hint_y))
        n = len(self.items_view())
        s.blit(self.small.render(f"{n} picture{'s' if n != 1 else ''}" + ("  (hidden ones: right-click to bring back)" if self.b_show_hidden else
                                 "  (right-click one to hide it)"), True, DIM), (x0, self.b_grid.bottom + 4))
        for dd in (self.b_set_dd, self.b_theme_dd, self.b_gen_dd):
            dd.draw_list(s, self.small, mouse)

    def draw_carry(self, mouse):
        """The carried thing under the mouse, green where it fits, red where it doesn't."""
        c = self.carry
        if not c or not self.canvas_rect().collidepoint(mouse):
            return
        Z = self.zoom
        x, y = self.carry_spot(mouse)
        if c.get("ghost") is not None:
            g = pygame.transform.smoothscale(c["ghost"], (c["w"] * Z, (c["h"] + c["up"]) * Z))
            g.set_alpha(185)
            self.screen.blit(g, (self.ox + x * Z, self.oy + (y - c["up"]) * Z))
        ok = self.fits(x, y, c["w"], c["h"])
        lay = pygame.Surface((c["w"] * Z, c["h"] * Z), pygame.SRCALPHA)
        lay.fill((60, 220, 90, 70) if ok else (230, 50, 50, 90))
        self.screen.blit(lay, (self.ox + x * Z, self.oy + y * Z))
        pygame.draw.rect(self.screen, (60, 220, 90) if ok else (230, 50, 50), (self.ox + x * Z, self.oy + y * Z, c["w"] * Z, c["h"] * Z), 2)

    def draw_brush(self, mouse):
        if not self.b_pick or "preset" in self.b_pick or not self.canvas_rect().collidepoint(mouse):
            return
        tx, ty = self.to_tile(mouse)
        Z = self.zoom
        if self.b_box_from:            # (a box being dragged out)
            (x0, y0), (x1, y1) = self.b_box_from, self.b_box_to
            x0, x1, y0, y1 = min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1)
            pygame.draw.rect(self.screen, (255, 255, 255), (self.ox + x0 * Z, self.oy + y0 * Z, (x1 - x0 + 1) * Z, (y1 - y0 + 1) * Z), 2)
            return
        n = 1 if ("ledge" in self.b_pick or "surface" in self.b_pick) and not isinstance(self.b_brush, int) else self.brush_n()
        r = n // 2
        pygame.draw.rect(self.screen, (255, 255, 255), (self.ox + (tx - r) * Z, self.oy + (ty - r) * Z, n * Z, n * Z), 2)


# ---------------------------------------------------------------- the map maker
class MapMaker(ParkBuilder):
    TOOLS = [("paint", "Paint"), ("rect", "Box"), ("fill", "Fill"), ("building", "Building"), ("select", "Pick bldg"),
             ("level", "Levels")]

    def __init__(self, doc, size=(1600, 940), headless=False):
        pygame.init()
        flags = 0 if headless else pygame.RESIZABLE
        self.screen = pygame.display.set_mode(size, flags)
        pygame.display.set_caption("Map maker")
        pygame.key.set_repeat(300, 40)
        self.font = pygame.font.SysFont("segoeui,arial", 15)
        self.small = pygame.font.SysFont("segoeui,arial", 13)
        self.big = pygame.font.SysFont("segoeui,arial", 18, bold=True)
        from src.dungeon import art
        self.art = art
        self.doc = doc
        self.undo_stack, self.redo_stack = [], []
        self.zoom = 24
        self.ox, self.oy = 16, 16
        self.tool = "paint"
        self.char = "."
        self.level_brush = 1
        self.game_look = True
        self.show_grid = True
        self.show_levels = False
        self.show_ref = True
        self.selected = None          # a building letter
        self.preset = PRESETS[2]
        self.drag_start = None
        self.panning = None
        self.painting = False
        self.status = "New map" if not doc.extra else f"Opened {doc.key}"
        self._game = None             # (rows, surface) of the last game-look drawing
        self._scaled = None
        self._ref_img = None
        self._previews = {}
        self.dirty_at = 0
        self.builder = False          # the park builder's panel (P) instead of the classic one
        self.drag_from_panel = False
        self._build_panel()
        self.center_view()

    # ---- panel
    def _build_panel(self):
        x0 = self.screen.get_width() - PANEL_W + 14
        w = PANEL_W - 28
        y = 12
        self.widgets = []
        self.detail_box = TextBox((0, 0, 10, 10), "", "")
        self.detail = None            # what the box edits: ("exit", char), ("person", (x, y)), ("sign", (x, y))
        self.key_box = TextBox((x0, y + 22, w - 232, 28), getattr(getattr(self, "key_box", None), "text", self.doc.key), "MAP_KEY")
        self.btn_builder = Button((x0 + w - 224, y + 22, 112, 28), "Park builder", self.toggle_builder, toggle=lambda: self.builder)
        self.btn_save = Button((x0 + w - 106, y + 22, 106, 28), "Save", self.save)
        y += 58
        self.w_box = TextBox((x0, y + 20, 56, 28), str(self.doc.w), "w")
        self.h_box = TextBox((x0 + 64, y + 20, 56, 28), str(self.doc.h), "h")
        self.btn_new = Button((x0 + 128, y + 20, 82, 28), "New", self.new_map)
        self.btn_resize = Button((x0 + 216, y + 20, 92, 28), "Resize", self.resize_map)
        y += 52
        self.open_box = TextBox((x0, y + 20, w - 92, 28), "", "key or layout file")
        self.btn_open = Button((x0 + w - 84, y + 20, 84, 28), "Open", self.browse_open)
        y += 54
        self.tool_btns = []
        bw = (w - 10) // 3
        for i, (t, label) in enumerate(self.TOOLS):
            r = (x0 + (i % 3) * (bw + 5), y + (i // 3) * 34, bw, 28)
            self.tool_btns.append(Button(r, label, lambda t=t: self.set_tool(t), toggle=lambda t=t: self.tool == t))
        y += 72
        self.cat_dd = Dropdown((x0, y + 20, w, 28), [(i, c) for i, (c, _items) in enumerate(PALETTE)], self.pick_category)
        self.item_dd = Dropdown((x0, y + 54, w, 28), [], self.pick_item)
        self.pick_category(0)
        self.preview_rect = pygame.Rect(x0, y + 90, 150, 110)
        self.detail_box.rect = pygame.Rect(x0 + 160, y + 160, w - 160, 26)
        y += 210
        self.bld_dd = Dropdown((x0, y + 20, w, 28), [(i, f"{b[0]}  ({b[2]}x{b[3]})") for i, b in enumerate(PRESETS)],
                               self.pick_preset, rows=18)
        self.bld_dd.index = 2
        self.bld_preview_rect = pygame.Rect(x0, y + 56, 150, 130)
        # the chosen building's editor, beside its preview
        ex = x0 + 160
        self.sel_kind_dd = Dropdown((ex, y + 74, w - 160, 26), [(k, k) for k in KINDS], self.set_kind, rows=12)
        self.sel_name = TextBox((ex, y + 106, w - 160, 26), "", "name over the door")
        self.sel_btns = [Button((ex, y + 138, 34, 26), "W-", lambda: self.grow(-1, 0)), Button((ex + 38, y + 138, 34, 26), "W+", lambda: self.grow(1, 0)),
                         Button((ex + 76, y + 138, 34, 26), "H-", lambda: self.grow(0, -1)), Button((ex + 114, y + 138, 34, 26), "H+", lambda: self.grow(0, 1)),
                         Button((ex, y + 168, 52, 26), "door<", lambda: self.move_door(-1)), Button((ex + 56, y + 168, 52, 26), "door>", lambda: self.move_door(1)),
                         Button((ex + 112, y + 168, 60, 26), "Delete", self.delete_selected)]
        y += 200
        self.roof_rects = [pygame.Rect(x0 + i * 32, y + 20, 28, 22) for i in range(len(ROOF_PRESETS))]
        self.rgb = [Slider((x0, y + 50 + i * 22, w, 18), 0, 255, lambda i=i: self._roof()[i], lambda v, i=i: self._set_roof(i, v),
                           ("Red", "Green", "Blue")[i]) for i in range(3)]
        y += 122
        self.view_btns = [Button((x0, y + 20, 92, 28), "Game look", self.toggle_game, toggle=lambda: self.game_look),
                          Button((x0 + 98, y + 20, 60, 28), "Grid", lambda: setattr(self, "show_grid", not self.show_grid), toggle=lambda: self.show_grid),
                          Button((x0 + 164, y + 20, 72, 28), "Levels", lambda: setattr(self, "show_levels", not self.show_levels), toggle=lambda: self.show_levels),
                          Button((x0 + 242, y + 20, 92, 28), "Reference", lambda: setattr(self, "show_ref", not self.show_ref), toggle=lambda: self.show_ref)]
        self.ref_box = TextBox((x0, y + 56, w - 302, 28), (self.doc.ref or {}).get("path", ""), "reference picture (png)")
        self.btn_ref_size = Button((x0 + w - 296, y + 56, 150, 28), "Size", self.ref_size_cycle)
        self.btn_ref_remove = Button((x0 + w - 140, y + 56, 70, 28), "Remove", self.remove_ref)
        self.btn_ref = Button((x0 + w - 64, y + 56, 64, 28), "Load", self.browse_ref)
        self.ref_alpha = Slider((x0, y + 92, w, 18), 0, 255, lambda: (self.doc.ref or {}).get("alpha", 140), self._set_ref_alpha, "Picture")
        self.level_btns = [Button((x0 + i * 46, y + 118, 40, 26), f"L{i}", lambda i=i: self.set_level(i), toggle=lambda i=i: self.level_brush == i and self.tool == "level") for i in range(4)]
        self.btn_cliffs = Button((x0 + 190, y + 118, w - 190, 26), "Cliffs from levels", self.cliffs)
        self.boxes = [self.key_box, self.w_box, self.h_box, self.open_box, self.sel_name, self.ref_box, self.detail_box]
        self.dropdowns = [self.cat_dd, self.item_dd, self.bld_dd, self.sel_kind_dd]
        self.detail_rect_classic = pygame.Rect(self.detail_box.rect)
        self._build_builder()
        if self.builder:
            self.detail_box.rect = pygame.Rect(self.b_detail_rect)
        self.buttons = [self.btn_save, self.btn_builder, self.btn_new, self.btn_resize, self.btn_open, self.btn_ref, self.btn_ref_size, self.btn_ref_remove, self.btn_cliffs] + self.tool_btns + self.sel_btns + self.view_btns + self.level_btns
        self.sliders = self.rgb + [self.ref_alpha]
        self.labels = [(x0, 12, "Map key"), (x0, 70, "Size (tiles)"), (x0, 122, "Open a map"), (x0, 176, "Tools"),
                       (x0, 248, "Assets"), (x0, 458, "Buildings"), (x0, 658, "Roof colour"), (x0, 780, "View")]

    # ---- actions
    def push(self):
        self.undo_stack.append(self.doc.snapshot())
        self.undo_stack = self.undo_stack[-200:]
        self.redo_stack = []

    def changed(self):
        self._game = None
        self._scaled = None

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.doc.snapshot())
            self.doc.restore(self.undo_stack.pop())
            self.changed()
            self.status = "Undone"

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.doc.snapshot())
            self.doc.restore(self.redo_stack.pop())
            self.changed()
            self.status = "Redone"

    def set_tool(self, t):
        self.tool = t
        if t != "select":
            self.selected = self.selected if t == "building" else None

    def set_level(self, i):
        self.level_brush = i
        self.tool = "level"
        self.show_levels = True

    def pick_category(self, i):
        self.item_dd.set_items([(c, f"{n}   [{c}]") for c, n in PALETTE[i][1]])
        self.pick_item(PALETTE[i][1][0][0])

    def pick_item(self, c):
        self.char = c
        self.set_detail(("exit", c) if c in EXIT_CHARS else None)
        if self.tool not in ("paint", "rect", "fill"):
            self.tool = "paint"
        self.status = f"Painting: {NAME.get(c, c)}"

    def pick_preset(self, i):
        self.preset = PRESETS[i]
        self.tool = "building"
        self.status = f"Click the map to place: {self.preset[0]}"

    def set_detail(self, what):
        """Point the detail box at a way out's destination, a person's option or a sign's words."""
        self.detail = what
        box = self.detail_box
        box.focus = False
        if not what:
            box.text, box.hint = "", ""
        elif what[0] == "exit":
            box.text, box.hint = self.doc.exits.get(what[1], ""), f"where {what[1]} leads (AREA_KEY)"
        elif what[0] == "person":
            p = self.doc.people.get(what[1], "")
            box.text, box.hint = p if isinstance(p, str) else json.dumps(p), "who: a town option's name"
        elif what[0] == "sign":
            box.text, box.hint = " | ".join(self.doc.signs.get(what[1], [])), "sign lines, split with |"

    def detail_changed(self):
        what, text = self.detail, self.detail_box.text
        if not what:
            return
        if what[0] == "exit":
            if text.strip():
                self.doc.exits[what[1]] = text.strip().upper()
            else:
                self.doc.exits.pop(what[1], None)
        elif what[0] == "person":
            try:
                self.doc.people[what[1]] = json.loads(text) if text.strip().startswith("{") else text
            except ValueError:
                self.doc.people[what[1]] = text
        elif what[0] == "sign":
            self.doc.signs[what[1]] = [line.strip() for line in text.split("|") if line.strip()]

    def toggle_game(self):
        self.game_look = not self.game_look

    def new_map(self):
        try:
            w, h = int(self.w_box.text), int(self.h_box.text)
        except ValueError:
            self.status = "Size: two whole numbers"
            return
        if not (4 <= w <= 300 and 4 <= h <= 300):
            self.status = "Size: 4 to 300 tiles each way"
            return
        self.push()
        key = self.key_box.text.strip() or "NEW_MAP"
        self.doc = MapDoc(w, h, key)
        self.selected = None
        self.changed()
        self.center_view()
        self.status = f"New {w} x {h} map"

    def resize_map(self):
        try:
            w, h = int(self.w_box.text), int(self.h_box.text)
        except ValueError:
            self.status = "Size: two whole numbers"
            return
        self.push()
        self.doc.resize(max(4, w), max(4, h))
        self.changed()
        self.status = f"Resized to {self.doc.w} x {self.doc.h}"

    def open_from_box(self):
        what = self.open_box.text.strip()
        if not what:
            self.status = "Type a map key (PALLET_TOWN) or a layout file"
            return
        doc = load(what)
        if doc is None:
            self.status = f"Couldn't open {what}"
            return
        self.push()
        self.doc = doc
        self.key_box.text = doc.key
        self.w_box.text, self.h_box.text = str(doc.w), str(doc.h)
        self.ref_box.text = (doc.ref or {}).get("path", "")
        self.selected = None
        self._ref_img = None
        self.changed()
        self.center_view()
        self.status = f"Opened {doc.key} ({doc.w} x {doc.h})"

    def save(self):
        key = (self.key_box.text.strip() or self.doc.key).upper().replace(" ", "_")
        self.doc.key = key
        self.key_box.text = key
        entry = self.doc.to_entry()
        problems = check(entry)
        os.makedirs(MADE, exist_ok=True)
        path = os.path.join(MADE, f"{key}.json")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"key": key, "map": entry}, f, ensure_ascii=False, indent=1)
            f.write("\n")
        self.status = f"Saved {path}" + (f"  (to fix: {problems[0]})" if problems else "")
        return path, problems

    def load_ref(self):
        self.set_ref(self.ref_box.text)

    def set_ref(self, path):
        """Lay a source picture with the map (a map from the real game, a sketch): stretched to the map's size."""
        path = (path or "").strip().strip('"')
        try:
            pygame.image.load(path)
        except (pygame.error, FileNotFoundError, OSError):
            self.status = f"Couldn't open a picture at {path}" if path else "No picture chosen"
            return
        self.push()
        old = self.doc.ref or {}
        self.doc.ref = {"path": path, "alpha": old.get("alpha", 140), "mode": self.ref_mode() if old else "top"}
        self._ref_src = None
        img = self.ref_source()
        if img is not None:              # (at its actual size, a tile per 32 px, the way the pieces are drawn: not stretched)
            self.doc.ref["rect"] = [0.0, 0.0, round(img.get_width() / 32, 3), round(img.get_height() / 32, 3)]
        self.ref_box.text = path
        self._ref_img = None
        self.show_ref = True
        self.b_pic_open = True
        self.status = f"Source picture: {os.path.basename(path)} at its actual size, 32 px a tile (the Size button: 16 px, or stretched to the map)"

    def ask_file(self, title, filetypes):
        """A file window (opening where the map maker saves its maps), or None if cancelled or there is none."""
        try:
            import tkinter
            from tkinter import filedialog
            root = tkinter.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            os.makedirs(MADE, exist_ok=True)
            path = filedialog.askopenfilename(title=title, initialdir=os.path.abspath(MADE), filetypes=filetypes, parent=root)
            root.destroy()
        except Exception as e:     # (no file window here: type the key or path in the box, or drop the file on the map)
            self.status = f"No file window ({type(e).__name__}): type it in the box, or drop the file onto the map"
            return None
        return path or None

    def browse_ref(self):
        """Pick the source picture in a file window."""
        path = self.ask_file("Source picture for this map", [("Pictures", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All files", "*.*")])
        if path:
            self.set_ref(path)

    def browse_open(self):
        """Open a map from a file window (the saved maps); a key typed in the box opens with Enter."""
        path = self.ask_file("Open a map", [("Maps", "*.json"), ("All files", "*.*")])
        if path:
            self.open_box.text = path
            self.open_from_box()

    def fit_to_ref(self):
        """Size the map to the source picture, a tile per 16 px (a Gen 3/4 screenshot) or per 32 px (a fan-game map)."""
        if not self.doc.ref:
            self.status = "Load a source picture first"
            return
        try:
            w, h = pygame.image.load(self.doc.ref["path"]).get_size()
        except (pygame.error, FileNotFoundError, OSError):
            self.status = "Couldn't open the source picture"
            return
        t = 32 if w % 32 == 0 and h % 32 == 0 and min(w, h) // 32 >= 12 else 16
        last = getattr(self, "_fit", None)
        if last and last[0] == self.doc.ref["path"] and last[1] == (self.doc.w, self.doc.h):
            t = 48 - last[2]                 # (pressed again on the same picture: the other tile size, 16 <-> 32)
        self._fit = None
        self.push()
        self.doc.resize(max(4, min(300, w // t)), max(4, min(300, h // t)))
        self.w_box.text, self.h_box.text = str(self.doc.w), str(self.doc.h)
        self.doc.ref.pop("rect", None)
        self._ref_img = None
        self.changed()
        self.center_view()
        self._fit = (self.doc.ref["path"], (self.doc.w, self.doc.h), t)
        self.status = f"Map sized to the picture: {self.doc.w} x {self.doc.h} tiles ({t} px a tile; Fit map again for {48 - t} px)"

    REF_MODES = {"top": "On top", "under": "Underneath", "trace": "Tracing layer"}

    def ref_mode(self):
        """How the source picture lies with the map: "top" (see-through over it), "under" (the whole map see-through
        over it), "trace" (a tracing layer: the picture, and over it only what you've put down; plain lawn is clear)."""
        if not self.doc.ref:
            return "top"
        return self.doc.ref.get("mode") or ("under" if self.doc.ref.get("under") else "top")

    def ref_under(self):
        return self.ref_mode() != "top"

    def toggle_ref_under(self):
        if not self.doc.ref:
            self.status = "Load a source picture first"
            return
        order = list(self.REF_MODES)
        m = order[(order.index(self.ref_mode()) + 1) % len(order)]
        self.doc.ref["mode"] = m
        self.doc.ref.pop("under", None)
        self.status = {"top": "Source picture on top of the map, see-through",
                       "under": "Source picture underneath: the whole map see-through over it",
                       "trace": "Tracing layer: the picture, with only what you put down drawn over it (plain lawn is clear)"}[m]

    def trace_surface(self):
        """The map as a tracing layer, at the zoom: only what's been put down (buildings, pieces, paths, trees, water,
        cliffs...), plain lawn left clear."""
        if self.game_surface() is None or self._game[1] is None:
            return None
        full, key = self._game[1], self._game[0]
        if getattr(self, "_trace", None) is None or self._trace[0] != key:
            T = GAME_TILE
            lay = pygame.Surface(full.get_size(), pygame.SRCALPHA)
            models = []
            for L in self.doc.buildings:
                r = self.doc.rect_of(L)
                if not r:
                    continue
                roof = self.doc.roofs.get(L)
                if isinstance(roof, dict) and roof.get("model") and self.art._model(roof["model"]):
                    models.append((r[1] + r[3], roof["model"], r[0], r[1]))
                else:
                    lay.blit(full, (r[0] * T, r[1] * T), (r[0] * T, r[1] * T, r[2] * T, r[3] * T))
            for y in range(self.doc.h):
                for x in range(self.doc.w):
                    if self.doc.art[y][x] in ".`" or self.doc.owner(x, y):
                        continue
                    lay.blit(full, (x * T, y * T), (x * T, y * T, T, T))
            for o in self.doc.objects:
                p = next((q for q in LIBRARY if q["key"] == o["k"]), None)
                models.append((o["at"][1] + (p["h"] if p else 1), o["k"], o["at"][0], o["at"][1]))
            for _foot, k, x, y in sorted(models):      # (the ready-made pieces whole, back to front)
                m = self.art._model(k)
                if m:
                    lay.blit(m[0], (x * T - m[1], y * T - m[2]))
            self._trace = (key, lay, None)
        if self._trace[2] is None or self._trace[2][0] != self.zoom:
            w, h = self.doc.w * self.zoom, self.doc.h * self.zoom
            sc = pygame.transform.smoothscale(self._trace[1], (w, h)) if self.zoom < GAME_TILE else pygame.transform.scale(self._trace[1], (w, h))
            self._trace = (self._trace[0], self._trace[1], (self.zoom, sc))
        return self._trace[2][1]

    def _set_ref_alpha(self, v):
        if self.doc.ref:
            self.doc.ref["alpha"] = int(v)
            if self._ref_img and self._ref_img[1] is not None:
                self._ref_img[1].set_alpha(int(v))

    def cliffs(self):
        self.push()
        n = self.doc.cliffs_from_levels()
        self.changed()
        self.status = (f"Cliffs laid where the levels step down: {n} tiles, paths across them made stairs" if n else
                       "No cliffs: paint higher levels first (L1-L3), then lay the cliffs")

    # ---- the chosen building
    def _roof(self, L=None):
        L = L or self.selected
        got = roof_rgb(self.doc.roofs.get(L)) if L else None
        if got:
            return got
        kind = self.doc.buildings.get(L, "house")
        if kind in SPRITE_HOUSES:
            return [110, 196, 110]                # (the tile sheet house's own green)
        return list(self.art.ROOFS.get(kind, self.art.ROOFS["house"])[0])

    def put_roof(self, L, rgb):
        """A building's roof colour; a tile-sheet house gets its picture tinted (art.py), anything else its colour."""
        rgb = [int(v) for v in rgb]
        self.doc.roofs[L] = {"roof": rgb, "tint": True} if self.doc.buildings.get(L) in SPRITE_HOUSES else rgb
        self.changed()

    def _set_roof(self, i, v):
        L = self.selected
        if not L:
            return
        roof = list(self._roof())
        roof[i] = int(v)
        self.put_roof(L, roof)

    def set_kind(self, k):
        if self.selected:
            self.push()
            self.doc.buildings[self.selected] = k
            self.changed()

    def grow(self, dw, dh):
        L = self.selected
        r = self.doc.rect_of(L) if L else None
        if r:
            self.push()
            x, y, w, h = r
            self.doc.reshape_building(L, x, y, w + dw, h + dh)
            self.changed()

    def move_door(self, d):
        L = self.selected
        r = self.doc.rect_of(L) if L else None
        if r:
            self.push()
            x, y, w, h = r
            self.doc.reshape_building(L, x, y, w, h, (self.doc.door_of(L) or 0) + d)
            self.changed()

    def move_selected(self, dx, dy):
        L = self.selected
        r = self.doc.rect_of(L) if L else None
        if r:
            self.push()
            x, y, w, h = r
            self.doc.reshape_building(L, x + dx, y + dy, w, h)
            self.changed()

    def delete_selected(self):
        if self.selected:
            self.push()
            self.doc.remove_building(self.selected)
            self.selected = None
            self.changed()

    def select(self, L):
        self.selected = L
        if L:
            kind = self.doc.buildings.get(L, "house")
            items = [(k, k) for k in sorted(set(KINDS) | {kind})]
            self.sel_kind_dd.set_items(items, [k for k, _ in items].index(kind))
            self.sel_name.text = self.doc.names.get(L, "")
            r = self.doc.rect_of(L)
            self.status = f"Building {L}: {kind}, {r[2]} x {r[3]} at ({r[0]}, {r[1]})"

    # ---- view
    def canvas_rect(self):
        return pygame.Rect(0, 0, self.screen.get_width() - PANEL_W, self.screen.get_height() - 30)

    def center_view(self):
        c = self.canvas_rect()
        self.zoom = max(6, min(48, min((c.w - 40) // max(1, self.doc.w), (c.h - 40) // max(1, self.doc.h))))
        self.ox = (c.w - self.doc.w * self.zoom) // 2
        self.oy = (c.h - self.doc.h * self.zoom) // 2

    def to_tile(self, pos):
        return (pos[0] - self.ox) // self.zoom, (pos[1] - self.oy) // self.zoom

    def game_surface(self):
        rows = (tuple("".join(r) for r in self.doc.art), json.dumps(self.doc.objects), json.dumps(self.draw_roofs(), sort_keys=True, default=str))
        if self._game is None or self._game[0] != rows:
            try:
                surf = self.art.surface(list(rows[0]), dict(self.doc.buildings), GAME_TILE,
                                        self.draw_roofs(), self.doc.theme)
            except Exception as e:  # (a map the game can't draw yet: a lone ledge with nothing to hop to...)
                self.status = f"Game look can't draw this yet ({type(e).__name__}); flat colours shown"
                surf = None
            self._game = (rows, surf)
            self._scaled = None
        if self._game[1] is None:
            return None
        if self._scaled is None or self._scaled[0] != self.zoom:
            self._scaled = (self.zoom, pygame.transform.smoothscale(self._game[1], (self.doc.w * self.zoom, self.doc.h * self.zoom))
                            if self.zoom < GAME_TILE else pygame.transform.scale(self._game[1], (self.doc.w * self.zoom, self.doc.h * self.zoom)))
        return self._scaled[1]

    def ref_source(self):
        """The source picture as loaded (cached), or None."""
        if not self.doc.ref:
            return None
        path = self.doc.ref["path"]
        if getattr(self, "_ref_src", None) is None or self._ref_src[0] != path:
            try:
                self._ref_src = (path, pygame.image.load(path).convert())
            except (pygame.error, FileNotFoundError, OSError):
                self._ref_src = (path, None)
        return self._ref_src[1]

    def ref_rect(self):
        """Where the source picture lies, in map tiles: [x, y, w, h] (stretched over the whole map until it's framed)."""
        r = (self.doc.ref or {}).get("rect")
        return list(r) if r else [0.0, 0.0, float(self.doc.w), float(self.doc.h)]

    def ref_picture(self, mw=None, mh=None):
        """The part of the source picture on screen, at this zoom and placing: (surface, top-left) or None."""
        img = self.ref_source()
        if img is None:
            return None
        Z = self.zoom
        x, y, w, h = self.ref_rect()
        D = pygame.Rect(round(self.ox + x * Z), round(self.oy + y * Z), max(1, round(w * Z)), max(1, round(h * Z)))
        V = D.clip(self.canvas_rect())
        if V.w <= 0 or V.h <= 0:
            return None
        key = (self.doc.ref["path"], tuple(D), tuple(V))
        if self._ref_img is None or self._ref_img[0] != key:
            iw, ih = img.get_size()
            sx, sy = (V.x - D.x) * iw / D.w, (V.y - D.y) * ih / D.h
            sw, sh = max(1, min(iw - int(sx), int(V.w * iw / D.w + 1))), max(1, min(ih - int(sy), int(V.h * ih / D.h + 1)))
            part = img.subsurface((int(sx), int(sy), sw, sh))
            self._ref_img = (key, pygame.transform.smoothscale(part, V.size))
        return self._ref_img[1], V.topleft

    def frame_ref(self, rect, push=True):
        if push and not getattr(self, "_framing", False):
            self.push()
            self._framing = True       # (one undo for a whole drag or run of wheel turns)
        self.doc.ref["rect"] = [round(v, 3) for v in rect]
        self._ref_img = None

    def toggle_ref_adjust(self):
        if not self.doc.ref:
            self.status = "Load a source picture first"
            return
        self.ref_adjust = not getattr(self, "ref_adjust", False)
        self.carry, self.b_pick, self._framing = None, None, False
        self.status = ("Framing the picture: drag it to move; wheel to size it (Ctrl: only wider, Shift: only taller); "
                       "arrows nudge (Shift: a whole tile); +/- size; Esc when done") if self.ref_adjust else "Picture framed"

    def ref_keep_shape(self):
        img = self.ref_source()
        if img is None:
            return
        x, y, w, h = self.ref_rect()
        iw, ih = img.get_size()
        self._framing = False
        self.frame_ref([x, y, w, w * ih / iw])
        self.status = "The picture keeps its own shape (as wide as it was; its height to match)"

    def remove_ref(self):
        """Take the source picture off the map altogether (Ctrl+Z puts it back); saving then leaves it out."""
        if not self.doc.ref:
            self.status = "No source picture to remove"
            return
        self.push()
        name = os.path.basename(self.doc.ref.get("path", ""))
        self.doc.ref = None
        self.ref_box.text = ""
        self._ref_img = self._ref_src = None
        self.ref_adjust = False
        self.status = f"Source picture {name} removed (Ctrl+Z puts it back)"

    def ref_size_state(self):
        """How the picture is sized: "32", "16" (actual size at that many px a tile), "stretch" or "framed"."""
        if not self.doc.ref:
            return None
        r = self.doc.ref.get("rect")
        if not r:
            return "stretch"
        img = self.ref_source()
        if img is not None:
            for t in ("32", "16"):
                if abs(r[2] - img.get_width() / int(t)) < 0.01 and abs(r[3] - img.get_height() / int(t)) < 0.01:
                    return t
        return "framed"

    SIZE_LABELS = {"32": "Size: 32 px a tile", "16": "Size: 16 px a tile", "stretch": "Size: stretched", "framed": "Size: framed",
                   None: "Size"}

    def ref_size_cycle(self):
        """Actual size at 32 px a tile (fan maps, RPG Maker), at 16 px (GBA screenshots), or stretched over the map."""
        img = self.ref_source()
        if not self.doc.ref or img is None:
            self.status = "Load a source picture first"
            return
        state = self.ref_size_state()
        nxt = {"32": "16", "16": "stretch"}.get(state, "32")
        self.push()
        x, y = (self.doc.ref.get("rect") or [0.0, 0.0])[:2]
        if nxt == "stretch":
            self.doc.ref.pop("rect", None)
            self.status = "Picture stretched over the whole map (its own shape lost)"
        else:
            t = int(nxt)
            self.doc.ref["rect"] = [x, y, round(img.get_width() / t, 3), round(img.get_height() / t, 3)]
            self.status = (f"Picture at its actual size, {t} px a tile: {img.get_width() / t:.0f} x {img.get_height() / t:.0f} tiles "
                           f"({'fan maps, RPG Maker sheets' if t == 32 else 'GBA screenshots'}); Move / size frames it by hand")
        self._ref_img = None

    def ref_reset(self):
        if self.doc.ref and self.doc.ref.get("rect"):
            self.push()
            self.doc.ref.pop("rect", None)
            self._ref_img = None
        self.status = "Picture stretched over the whole map again"

    def ref_scale(self, k, about=None, wide=True, tall=True):
        x, y, w, h = self.ref_rect()
        ax, ay = about if about else (x + w / 2, y + h / 2)
        nw, nh = (w * k if wide else w), (h * k if tall else h)
        if min(nw, nh) < 1 or max(nw, nh) > 2000:
            return
        self.frame_ref([ax - (ax - x) * nw / w, ay - (ay - y) * nh / h, nw, nh])

    def ref_frame_event(self, e):
        """Mouse and keys while framing the picture: True if taken."""
        canvas = self.canvas_rect()
        Z = self.zoom
        if e.type == pygame.KEYDOWN:
            shift = e.mod & pygame.KMOD_SHIFT
            step = 1.0 if shift else 0.25
            moves = {pygame.K_LEFT: (-step, 0), pygame.K_RIGHT: (step, 0), pygame.K_UP: (0, -step), pygame.K_DOWN: (0, step)}
            if e.key in moves:
                x, y, w, h = self.ref_rect()
                self.frame_ref([x + moves[e.key][0], y + moves[e.key][1], w, h])
                return True
            if e.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_MINUS, pygame.K_KP_MINUS):
                self.ref_scale(1.02 if e.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS) else 1 / 1.02)
                return True
            if e.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                self.toggle_ref_adjust()
                return True
            return False
        if e.type == pygame.MOUSEWHEEL and canvas.collidepoint(pygame.mouse.get_pos()):
            mx, my = pygame.mouse.get_pos()
            mods = pygame.key.get_mods()
            self.ref_scale(1.04 ** e.y, ((mx - self.ox) / Z, (my - self.oy) / Z),
                           wide=not mods & pygame.KMOD_SHIFT, tall=not mods & pygame.KMOD_CTRL)
            return True
        pos = getattr(e, "pos", None)
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and pos and canvas.collidepoint(pos) \
                and not pygame.key.get_pressed()[pygame.K_SPACE]:
            self._framing = False
            self._ref_drag = (pos, self.ref_rect())
            return True
        if e.type == pygame.MOUSEMOTION and getattr(self, "_ref_drag", None):
            (sx, sy), (x, y, w, h) = self._ref_drag
            self.frame_ref([x + (pos[0] - sx) / Z, y + (pos[1] - sy) / Z, w, h])
            return True
        if e.type == pygame.MOUSEBUTTONUP and e.button == 1 and getattr(self, "_ref_drag", None):
            self._ref_drag = None
            return True
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 3 and pos and canvas.collidepoint(pos):
            self.toggle_ref_adjust()
            return True
        return False

    def draw_roofs(self):
        """The roofs the game look draws with: the map's own, its other entries, its placed pieces."""
        roofs = dict(self.doc.roofs, **(self.doc.extra.get("_roof_extras") or {}))
        if self.doc.objects:
            roofs["_objects"] = list(roofs.get("_objects") or []) + list(self.doc.objects)
        if self.doc.paint_spec():
            roofs["_paint"] = self.doc.paint_spec()
        return roofs

    def preview(self, key, rows, kinds=None, roofs=None):
        if key not in self._previews:
            try:
                surf = self.art.surface(rows, kinds or {}, GAME_TILE, roofs or {}, None)
            except Exception:
                surf = pygame.Surface((len(rows[0]) * GAME_TILE, len(rows) * GAME_TILE))
                for y, r in enumerate(rows):
                    for x, c in enumerate(r):
                        surf.fill(FLAT.get(c, (200, 70, 60)), (x * GAME_TILE, y * GAME_TILE, GAME_TILE, GAME_TILE))
            self._previews[key] = surf
        return self._previews[key]

    def asset_rows(self, c):
        if c in EXIT_CHARS or c in "NX!lhjz":
            return [".....", ".....", ".." + c + "..", ".....", "....."]
        if c in "~o:q$[]{}":
            base = "o" if c not in "~" else "~"
            return [base * 5] * 2 + [base * 2 + c + base * 2] + [base * 5] * 2 if c in "q$" else [c * 5] * 5
        if c in "_()":
            return [".....", ".....", c * 5, ".....", "....."] if c == "_" else ["." * 5] * 5
        return [".....", "." + c * 3 + ".", "." + c * 3 + ".", "." + c * 3 + ".", "....."]

    # ---- drawing
    def draw(self):
        label = self.SIZE_LABELS[self.ref_size_state()]
        self.btn_ref_size.text = label
        if hasattr(self, "b_frame_btns"):
            self.b_frame_btns[2].text = label.replace("Size: ", "").replace(" a tile", "/tile") if self.doc.ref else "Size"
        s = self.screen
        s.fill(BG)
        mouse = pygame.mouse.get_pos()
        canvas = self.canvas_rect()
        s.set_clip(canvas)
        Z = self.zoom
        mw, mh = self.doc.w * Z, self.doc.h * Z
        pygame.draw.rect(s, (20, 22, 30), (self.ox - 2, self.oy - 2, mw + 4, mh + 4))
        g = self.game_surface() if self.game_look else None
        rp = self.ref_picture() if self.show_ref else None
        ref, rpos = rp if rp else (None, None)
        framing = bool(getattr(self, "ref_adjust", False) and self.doc.ref)
        on_map = canvas.clip(pygame.Rect(self.ox, self.oy, mw, mh))
        mode = self.ref_mode() if ref is not None else "top"
        under = mode == "under"
        if mode == "trace":                 # (a tracing layer: the picture, faded by Strength, and over it what's been put down)
            ref.set_alpha(self.doc.ref.get("alpha", 140))
            s.set_clip(canvas if framing else on_map)
            s.blit(ref, rpos)
            s.set_clip(canvas)
            tr = self.trace_surface() if g is not None else None
            if tr is not None:
                s.blit(tr, (self.ox, self.oy))
            else:
                for y in range(self.doc.h):
                    for x in range(self.doc.w):
                        c = self.doc.art[y][x]
                        if c != ".":
                            s.fill(FLAT.get(c) or tuple(self._roof(c)), (self.ox + x * Z, self.oy + y * Z, Z, Z))
        elif under:
            ref.set_alpha(255)
            s.set_clip(canvas if framing else on_map)
            s.blit(ref, rpos)
            s.set_clip(canvas)
        if mode == "trace":
            pass
        elif g is not None:
            g.set_alpha(255 - self.doc.ref.get("alpha", 140) if under else 255)
            s.blit(g, (self.ox, self.oy))
            g.set_alpha(255)
        elif under:
            lay = pygame.Surface((mw, mh), pygame.SRCALPHA)
            for y in range(self.doc.h):
                for x in range(self.doc.w):
                    col = FLAT.get(self.doc.art[y][x]) or tuple(self._roof(self.doc.art[y][x]))
                    lay.fill(tuple(col) + (255 - self.doc.ref.get("alpha", 140),), (x * Z, y * Z, Z, Z))
            s.blit(lay, (self.ox, self.oy))
        else:
            for y in range(self.doc.h):
                for x in range(self.doc.w):
                    c = self.doc.art[y][x]
                    col = FLAT.get(c) or tuple(self._roof(c))
                    s.fill(col, (self.ox + x * Z, self.oy + y * Z, Z, Z))
                    if c in EXIT_CHARS + "NX!":
                        t = self.small.render(c, True, (0, 0, 0))
                        s.blit(t, t.get_rect(center=(self.ox + x * Z + Z // 2, self.oy + y * Z + Z // 2)))
        if g is not None and Z >= 10:   # (what the game puts there when you walk it: people, trainers, ways out)
            for y in range(self.doc.h):
                for x in range(self.doc.w):
                    c = self.doc.art[y][x]
                    if c in "NX" or c in EXIT_CHARS:
                        cx, cy = self.ox + x * Z + Z // 2, self.oy + y * Z + Z // 2
                        col = (255, 210, 60) if c == "N" else (255, 120, 60) if c == "X" else (255, 255, 255)
                        pygame.draw.circle(s, (0, 0, 0), (cx, cy), Z // 3 + 1)
                        pygame.draw.circle(s, col, (cx, cy), Z // 3)
                        t = self.small.render(c, True, (0, 0, 0))
                        s.blit(t, t.get_rect(center=(cx, cy)))
        if ref is not None and mode == "top":
            ref.set_alpha(self.doc.ref.get("alpha", 140))
            s.set_clip(canvas if framing else on_map)
            s.blit(ref, rpos)
            s.set_clip(canvas)
        if framing:     # (the picture's outline and corners while it's being framed)
            x, y, w, h = self.ref_rect()
            R = pygame.Rect(round(self.ox + x * Z), round(self.oy + y * Z), round(w * Z), round(h * Z))
            pygame.draw.rect(s, (255, 220, 40), R, 3)
            for c in (R.topleft, R.topright, R.bottomleft, R.bottomright):
                pygame.draw.circle(s, (255, 220, 40), c, 6)
            pygame.draw.rect(s, (255, 255, 255), (self.ox, self.oy, mw, mh), 1)
        if self.show_levels:
            tint = [(0, 0, 120, 70), (0, 120, 0, 50), (200, 160, 0, 70), (200, 40, 40, 80)]
            lay = pygame.Surface((mw, mh), pygame.SRCALPHA)
            for y in range(self.doc.h):
                for x in range(self.doc.w):
                    lay.fill(tint[min(3, self.doc.levels[y][x])], (x * Z, y * Z, Z, Z))
            s.blit(lay, (self.ox, self.oy))
            if Z >= 14:
                for y in range(self.doc.h):
                    for x in range(self.doc.w):
                        t = self.small.render(str(self.doc.levels[y][x]), True, (255, 255, 255))
                        s.blit(t, (self.ox + x * Z + 2, self.oy + y * Z))
        if self.show_grid and Z >= 8:
            for x in range(self.doc.w + 1):
                pygame.draw.line(s, (0, 0, 0), (self.ox + x * Z, self.oy), (self.ox + x * Z, self.oy + mh))
            for y in range(self.doc.h + 1):
                pygame.draw.line(s, (0, 0, 0), (self.ox, self.oy + y * Z), (self.ox + mw, self.oy + y * Z))
        # building names and the chosen one
        for L in list(self.doc.buildings):
            r = self.doc.rect_of(L)
            if not r:
                continue
            rr = pygame.Rect(self.ox + r[0] * Z, self.oy + r[1] * Z, r[2] * Z, r[3] * Z)
            name = self.doc.names.get(L) or self.doc.buildings.get(L)
            if Z >= 12 and name:
                t = self.small.render(name, True, (255, 255, 255))
                bg = t.get_rect(midtop=(rr.centerx, rr.y + 2)).inflate(6, 0)
                pygame.draw.rect(s, (0, 0, 0), bg)
                s.blit(t, t.get_rect(center=bg.center))
            if L == self.selected:
                pygame.draw.rect(s, (255, 255, 0), rr, 3)
        # what the tool would do
        tx, ty = self.to_tile(mouse)
        if self.builder:
            self.draw_brush(mouse)
            self.draw_carry(mouse)
        elif canvas.collidepoint(mouse) and 0 <= tx < self.doc.w and 0 <= ty < self.doc.h:
            if self.tool == "building":
                _n, _k, bw, bh, _p = self.preset
                pygame.draw.rect(s, (255, 255, 255), (self.ox + tx * Z, self.oy + ty * Z, bw * Z, bh * Z), 2)
            elif self.tool == "rect" and self.drag_start:
                x0, y0 = self.drag_start
                pygame.draw.rect(s, (255, 255, 255), (self.ox + min(x0, tx) * Z, self.oy + min(y0, ty) * Z,
                                                      (abs(tx - x0) + 1) * Z, (abs(ty - y0) + 1) * Z), 2)
            else:
                pygame.draw.rect(s, (255, 255, 255), (self.ox + tx * Z, self.oy + ty * Z, Z, Z), 2)
        s.set_clip(None)
        if self.builder:
            self.draw_builder_panel(mouse)
        else:
            self.draw_panel(mouse)
        bar = pygame.Rect(0, s.get_height() - 30, s.get_width() - PANEL_W, 30)
        pygame.draw.rect(s, (24, 26, 36), bar)
        here = f"({tx}, {ty}) {NAME.get(self.doc.cell(tx, ty) or '', self.doc.cell(tx, ty) or '')}" if 0 <= tx < self.doc.w and 0 <= ty < self.doc.h else ""
        t = self.font.render(f"{self.doc.key}  {self.doc.w} x {self.doc.h}   {here}    {self.status}", True, DIM)
        s.blit(t, (10, bar.y + 6))

    def draw_panel(self, mouse):
        s = self.screen
        px = s.get_width() - PANEL_W
        pygame.draw.rect(s, PANEL, (px, 0, PANEL_W, s.get_height()))
        pygame.draw.line(s, PANEL_LINE, (px, 0), (px, s.get_height()))
        for x, y, text in self.labels:
            s.blit(self.big.render(text, True, TEXT), (x, y))
        for w in self.boxes + self.buttons:
            if w is not self.detail_box or self.detail:
                w.draw(s, self.font, mouse)
        for w in self.sliders:
            w.draw(s, self.small, mouse)
        # the asset's picture, as the game draws it
        pr = self.preview_rect
        img = self.preview(("a", self.char), self.asset_rows(self.char))
        s.blit(pygame.transform.smoothscale(img, (pr.w, int(pr.w * img.get_height() / img.get_width()))), pr.topleft)
        pygame.draw.rect(s, PANEL_LINE, (pr.x, pr.y, pr.w, int(pr.w * img.get_height() / img.get_width())), 1)
        t = self.small.render(NAME.get(self.char, self.char), True, DIM)
        s.blit(t, (pr.right + 10, pr.y + 4))
        if self.detail:
            label = {"exit": "Leads to:", "person": "This person:", "sign": "This sign says:"}[self.detail[0]]
            s.blit(self.small.render(label, True, TEXT), (self.detail_box.rect.x, self.detail_box.rect.y - 18))
        walk = "walkable" if (self.char in self.art.OPEN) else "in the way"
        s.blit(self.small.render(f"key: {self.char}   ({walk})", True, DIM), (pr.right + 10, pr.y + 22))
        # the building's picture (the chosen one if any, else the preset)
        br = self.bld_preview_rect
        if self.selected and self.doc.rect_of(self.selected):
            L = self.selected
            x, y, w, h = self.doc.rect_of(L)
            rows = ["." * (w + 2)] + ["." + "".join(self.doc.art[yy][xx] for xx in range(x, x + w)) + "." for yy in range(y, y + h)] + ["." * (w + 2)]
            img = self.preview(("sel", tuple(rows), self.doc.buildings.get(L), str(self.doc.roofs.get(L))), rows,
                               {L: self.doc.buildings.get(L, "house")}, {L: self.doc.roofs[L]} if L in self.doc.roofs else {})
            title = f"Chosen: {self.doc.names.get(L) or self.doc.buildings.get(L)}"
        else:
            name, kind, w, h, piece = self.preset
            if piece:
                rows = ["." * (w + 2)] * 3 + ["." + ("`" if piece["prop"] else "A") * w + "." for _ in range(h)] + ["." * (w + 2)]
                if not piece["prop"]:
                    last = list(rows[-2])
                    for d in piece["doors"]:
                        last[1 + d] = "D"
                    rows[-2] = "".join(last)
                roofs = {"_objects": [{"k": piece["key"], "at": [1, 3]}]} if piece["prop"] else {"A": {"model": piece["key"]}}
                img = self.preview(("lib", piece["key"]), rows, {"A": kind}, roofs)
                title = piece["label"]
            else:
                rows = ["." * (w + 2)] + ["." + "A" * w + "." for _ in range(h - 1)] + ["." + "A" * (w // 2) + "D" + "A" * (w - w // 2 - 1) + "."] + ["." * (w + 2)]
                img = self.preview(("bld", name), rows, {"A": kind})
                title = name
        sc = min(br.w / img.get_width(), br.h / img.get_height())
        im = pygame.transform.smoothscale(img, (int(img.get_width() * sc), int(img.get_height() * sc)))
        s.blit(im, br.topleft)
        pygame.draw.rect(s, PANEL_LINE, (br.x, br.y, im.get_width(), im.get_height()), 1)
        s.blit(self.small.render(title[:30], True, TEXT), (br.x + 160, br.y))
        s.blit(self.small.render("Pick bldg, then edit:" if not self.selected else "kind / name / size / door", True, DIM), (br.x + 160, br.y + 16))
        for i, r in enumerate(self.roof_rects):
            pygame.draw.rect(s, ROOF_PRESETS[i], r, border_radius=4)
            pygame.draw.rect(s, (255, 255, 255) if self.selected and list(ROOF_PRESETS[i]) == list(self._roof()) else PANEL_LINE, r, 2, border_radius=4)
        for d in self.dropdowns:
            if d is not self.sel_kind_dd or self.selected:
                d.draw(s, self.font, mouse)
        for d in self.dropdowns:   # (an open list on top of everything)
            d.draw_list(s, self.font, mouse)

    # ---- input
    def handle(self, e):
        if e.type == pygame.VIDEORESIZE:
            self.screen = pygame.display.set_mode((max(1200, e.w), max(800, e.h)), pygame.RESIZABLE)
            self._build_panel()
            return
        if e.type == pygame.DROPFILE:
            if e.file.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif")):
                self.set_ref(e.file)
            elif e.file.lower().endswith(".json"):
                self.open_box.text = e.file
                self.open_from_box()
            return
        if self.builder and self.builder_event(e):
            return
        for d in self.dropdowns:
            if d.open and d.event(e):
                return
        for d in self.dropdowns:
            if (d is not self.sel_kind_dd or self.selected) and d.event(e):
                for o in self.dropdowns:
                    if o is not d:
                        o.open = False
                return
        name_before = self.sel_name.text
        for b in self.boxes:
            if b.event(e):
                if b is self.sel_name and self.selected and self.sel_name.text != name_before:
                    self.doc.names[self.selected] = self.sel_name.text
                if b is self.detail_box:
                    self.detail_changed()
                if b is self.open_box and e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.open_from_box()
                return
        for sl in self.sliders:
            if sl.event(e):
                if sl in self.rgb and e.type == pygame.MOUSEBUTTONDOWN:
                    self.push()
                return
        typing = any(b.focus for b in self.boxes)
        if e.type == pygame.KEYDOWN and not typing:
            ctrl = e.mod & pygame.KMOD_CTRL
            if ctrl and e.key == pygame.K_z:
                self.undo()
            elif ctrl and e.key == pygame.K_y:
                self.redo()
            elif ctrl and e.key == pygame.K_s:
                self.save()
            elif e.key == pygame.K_g:
                self.toggle_game()
            elif e.key == pygame.K_p:
                self.toggle_builder()
            elif e.key == pygame.K_l:
                self.show_levels = not self.show_levels
            elif e.key == pygame.K_r:
                self.show_ref = not self.show_ref
            elif e.key == pygame.K_DELETE:
                self.delete_selected()
            elif e.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN) and self.selected:
                self.move_selected({pygame.K_LEFT: -1, pygame.K_RIGHT: 1}.get(e.key, 0), {pygame.K_UP: -1, pygame.K_DOWN: 1}.get(e.key, 0))
            return
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for b in self.buttons:
                if b.click(e.pos):
                    return
            for i, r in enumerate(self.roof_rects):
                if r.collidepoint(e.pos) and self.selected:
                    self.push()
                    self.put_roof(self.selected, ROOF_PRESETS[i])
                    return
        canvas = self.canvas_rect()
        if e.type == pygame.MOUSEWHEEL and canvas.collidepoint(pygame.mouse.get_pos()):
            mx, my = pygame.mouse.get_pos()
            tx, ty = (mx - self.ox) / self.zoom, (my - self.oy) / self.zoom
            self.zoom = max(6, min(64, self.zoom + (2 if e.y > 0 else -2)))
            self.ox, self.oy = int(mx - tx * self.zoom), int(my - ty * self.zoom)
            return
        if e.type == pygame.MOUSEBUTTONDOWN and canvas.collidepoint(e.pos):
            if e.button == 2 or (e.button == 1 and pygame.key.get_pressed()[pygame.K_SPACE]):
                self.panning = (e.pos, self.ox, self.oy)
                return
            tx, ty = self.to_tile(e.pos)
            if not (0 <= tx < self.doc.w and 0 <= ty < self.doc.h):
                return
            if e.button == 3:   # pick up what's here
                L = self.doc.owner(*self.piece_tile(e.pos))
                if L:
                    self.select(L)
                    self.tool = "select"
                else:
                    self.char = self.doc.cell(tx, ty)
                    self.tool = "paint"
                    self.status = f"Picked up: {NAME.get(self.char, self.char)}"
                    kind = {"N": "person", "!": "sign"}.get(self.char)
                    self.set_detail((kind, (tx, ty)) if kind else ("exit", self.char) if self.char in EXIT_CHARS else None)
                    if kind:
                        self.status = f"Editing this {kind}: type in the box under the picture"
                return
            if e.button == 1:
                self.click_tool(*(self.piece_tile(e.pos) if self.tool == "select" else (tx, ty)))
        if e.type == pygame.MOUSEMOTION:
            if self.panning:
                (sx, sy), ox, oy = self.panning
                self.ox, self.oy = ox + e.pos[0] - sx, oy + e.pos[1] - sy
            elif self.painting:
                tx, ty = self.to_tile(e.pos)
                self.paint_at(tx, ty)
        if e.type == pygame.MOUSEBUTTONUP:
            if self.panning:
                self.panning = None
            if e.button == 1 and self.tool == "rect" and self.drag_start:
                tx, ty = self.to_tile(e.pos)
                x0, y0 = self.drag_start
                for y in range(min(y0, ty), max(y0, ty) + 1):
                    for x in range(min(x0, tx), max(x0, tx) + 1):
                        self.doc.set(x, y, self.char)
                self.drag_start = None
                self.changed()
            self.painting = False

    def click_tool(self, tx, ty):
        t = self.tool
        if t == "select":
            self.select(self.doc.owner(tx, ty))
            return
        self.push()
        if t == "paint":
            self.painting = True
            self.paint_at(tx, ty)
        elif t == "level":
            self.painting = True
            self.paint_at(tx, ty)
        elif t == "rect":
            self.drag_start = (tx, ty)
        elif t == "fill":
            self.doc.flood(tx, ty, self.char)
            self.changed()
        elif t == "building":
            name, kind, w, h, piece = self.preset
            if piece and piece["prop"]:
                if self.doc.place_object(tx, ty, piece):
                    self.status = f"Placed {piece['label']}"
                    self.changed()
                return
            if piece:
                L = self.doc.place_building(tx, ty, w, h, kind, name=piece["label"], doors=piece["doors"])
                if L:
                    self.doc.roofs[L] = {"model": piece["key"]}
            else:
                L = self.doc.place_building(tx, ty, w, h, kind)
            if L:
                self.select(L)
                self.status = f"Placed {name} ({L}). Edit it on the right; arrows move it."
            else:
                self.status = "No letters left for another building"
            self.changed()

    def paint_at(self, tx, ty):
        if not (0 <= tx < self.doc.w and 0 <= ty < self.doc.h):
            return
        if self.tool == "level":
            self.doc.levels[ty][tx] = self.level_brush
            return
        if self.tool == "paint" and self.doc.cell(tx, ty) != self.char:
            self.doc.set(tx, ty, self.char)
            if self.char == "N":
                self.doc.people.setdefault((tx, ty), "someone")
            if self.char == "!":
                self.doc.signs.setdefault((tx, ty), ["A sign."])
            self.changed()

    def run(self):
        clock = pygame.time.Clock()
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    return
                self.handle(e)
            self.draw()
            pygame.display.flip()
            clock.tick(60)


# ---------------------------------------------------------------- opening and checking
def load(what):
    """A MapDoc from a map key (a saved made map first, then the game's), or a layout file (.json)."""
    what = what.strip().strip('"')
    if what.lower().endswith(".json") and os.path.isfile(what):
        with open(what, encoding="utf-8") as f:
            d = json.load(f)
        if "map" in d and "art" in d["map"]:        # a made map
            return MapDoc.from_entry(d.get("key", "NEW_MAP"), d["map"])
        if "art" in d:                              # a single map entry
            return MapDoc.from_entry(os.path.splitext(os.path.basename(what))[0].upper(), d)
        return from_layout(d, os.path.splitext(os.path.basename(what))[0].upper())
    key = what.upper()
    path = os.path.join(MADE, f"{key}.json")
    if os.path.isfile(path):
        return load(path)
    with open(os.path.join("assets", "town_maps.json"), encoding="utf-8") as f:
        maps = json.load(f)
    if key in maps and "art" in maps[key]:
        return MapDoc.from_entry(key, maps[key])
    return None


# a layout from the 3D-region tools (kanto_handoff/alola_rom_tools): grid rows in their own letters -> map characters
LAYOUT_CHARS = {"T": "T", ".": ".", "=": "=", "P": "=", "G": '"', "C": "c", "S": "=", "W": "~", "s": "s"}


def from_layout(d, key):
    if "grid" in d and d["grid"] and isinstance(d["grid"][0], str):         # (a redesign: rows of letters)
        rows = d["grid"]
        doc = MapDoc(len(rows[0]), len(rows), key)
        doc.art = [[LAYOUT_CHARS.get(c, ".") for c in r] for r in rows]
        if d.get("level"):
            doc.levels = [list(r) for r in d["level"]]
        for b in d.get("buildings") or []:
            name = b.get("name", "house")
            doc.place_building(b["x"], b["y"], b["w"], b["h"], "house", name=name)   # (kind: change it in the editor)
        doc.extra = {"_roof_extras": {}}
        return doc
    if "grid" in d:                                                         # (a literal trace: rows of numbers)
        kinds = {0: ".", 1: "=", 2: "T", 3: "c", 4: "c", 5: "~", 6: "s"}
        rows = d["grid"]
        doc = MapDoc(len(rows[0]), len(rows), key)
        doc.art = [[kinds.get(v, ".") for v in r] for r in rows]
        doc.extra = {"_roof_extras": {}}
        return doc
    return None


def check(m):
    """The builder's own checks that a map maker can make without the rest of the game: problems, in words."""
    out = []
    art = m["art"]
    letters = {c for r in art for c in r if c.isupper() and c not in "TDNX"}
    for L in letters:
        cells = [(x, y) for y, r in enumerate(art) for x, c in enumerate(r) if c == L]
        xs, ys = [c[0] for c in cells], [c[1] for c in cells]
        if any(art[y][x] not in (L, "D") for y in range(min(ys), max(ys) + 1) for x in range(min(xs), max(xs) + 1)):
            out.append(f"building {L} isn't a rectangle")
        if L not in m.get("buildings", {}):
            out.append(f"building {L} has no kind")
    if not any(c in "^v<>wu" for r in art for c in r) and not any(k.isupper() for k in m.get("exits", {})):
        out.append("no way out yet (^ v < >)")
    for c in sorted({c for r in art for c in r if c in "^v<>wu"}):
        if c not in m.get("exits", {}):
            out.append(f"way out {c} doesn't say where it leads (pick it, fill in 'Leads to')")
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    doc = load(args[0]) if args else None
    if args and doc is None:
        print(f"Couldn't open {args[0]}: starting a new map")
    doc = doc or MapDoc(40, 30)
    for a in sys.argv[1:]:
        if a.startswith("--size="):
            w, h = (int(v) for v in a.split("=", 1)[1].lower().split("x"))
            doc = MapDoc(w, h, doc.key)
        if a.startswith("--ref="):
            doc.ref = {"path": a.split("=", 1)[1], "alpha": 140}
    MapMaker(doc).run()


if __name__ == "__main__":
    main()
