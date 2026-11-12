"""Our own walkable maps' look and ground (Jordan, 11-06): a map is a grid of characters (assets/town_maps.json,
dev/builders/build_town_maps.py) drawn here in the route maps' style, tile by tile, and read for where you
can walk. The town screen (src/states/overworld/walk_town.py) and the route maps (dungeon.py) both use it.

  T tree   r rock   ~ sea   # fence                       (in the way)
  . ground  = sand path  s beach  " tall grass  f flowers  (open ground)
  ! a sign (read it)  l a lamp post  k a white picket fence  c cliff rock   (in the way)
  a capital letter: a building (a rectangle), D its door; < > ^ v a way out; w water that's a way out
  (Surf); N someone standing; X a trainer's own spot (the map's "trainer_spots", by name: the Nugget
  Bridge); + a ladder down, - a ladder up (a map of floors: Mt. Moon)
  o open sea you Surf across (route maps: Routes 19-21)   q a rock in the sea (in the way)
  u a second water way out (Cinnabar: w north to Route 21, u east to Route 20)
  a a city road (gray)   p a sidewalk (brick, a curb where it meets the road): Saffron's streets
  i an iron railing (blue arches)   h a fire hydrant   m a machine (a console: desks, lockers, generators)
  g a stone gate wall (pillars: Route 23's badge gates)   j a white stone post   e pale stone pavement
  y a sofa (red cushions)   z a potted plant   (indoors; in the way)
  d a walking path of pale grass (FireRed / LeafGreen's towns: Pallet's paths), lawn "." around it
    (in the way)
  b a boulder: Strength and the slide puzzle push it aside (route maps: Seafoam)
  % sheet ice: you slide across it till something stops you   & a hole in the floor (the Ice Path)
  $ a waterfall (Waterfall climbs it)   / a rock wall with footholds (Rock Climb scales it)  (Mt. Silver)
  * lava (in the way: Mt. Chimney's crater)
  , a plank walkway (open ground: Fortree's bridges, on its upper layer)
  _ ( ) a ledge you hop over one way only: down (south), west, east (the Jagged Pass)
  @ a gravestone out in the open (in the way: Mt. Pyre)
  0 a cracked rock: in the way till you have Rock Smash (Ravaged Path, Oreburgh Gate)
  2 a small tree: in the way till you have Cut   7 a steep muddy slope: in the way till you have the Bicycle
  3 4 5 6 a spin tile: the floor carries you west, east, north, south till something stops you (Fuego Ironworks)
  8 deep snow   9 marsh mud   (open ground you wade through: each step takes twice as long)
  1 a passage to any other floor, or across this one (a map's "links" {"x,y": [floor, x, y]}: Mt. Coronet)
  [ ] { } a sea current: it carries you west, east, north, south till something stops you (Routes 132-134)
  : deep, dark sea: Surf across it, and Dive there to the map's seabed floor
  | ; a log bridge running north-south / east-west: cross it along its length, or walk under it across
    its width, never from one to the other (Victory Road's two levels)
A map's "theme" "distortion" draws the Distortion World: red rock slabs in a blue void (its c), stepping stones (its ,).
A map's "theme" "seabed" draws a floor under the sea: dark blue sand, rock walls, seaweed for its tall grass.
A way out (< > ^ v) with the sea on every side is surfed onto, like w and u (Route 124's sides).
A map's "theme" "cave" (or a turbine's t: in the way) draws the ground as a cave floor and c as its rock walls; "ice" the same, icy."""
import random

import pygame

BLOCK = set("Tr~#!lkcqihmgjyztx&$/*_()@027")
LEDGES = {"_": (0, 1), "(": (-1, 0), ")": (1, 0)}  # a ledge, and the one way you hop over it
CLIFF = (200, 160, 116)
CLIFF_DARK = (150, 112, 78)
CLIFF_LIGHT = (222, 188, 146)
OPEN = set('.=s"f<>^vNw+-Xouaped%n,[]{}:|;1345689')
CURRENTS = {"[": (-1, 0), "]": (1, 0), "{": (0, -1), "}": (0, 1)}  # a sea current, and the way it carries you
BRIDGES = {"|": (0, 1), ";": (1, 0)}  # a log bridge, and the line it runs along
SEA_CHARS = "o[]{}:"  # open sea you Surf across
BRIDGE_LOOK = None
ROOM_LOOK = (None, None)  # a room's own floor and wall colours (the map's roofs "_floor", "_wall"; theme "room")
ROOM_STAIRS = {}  # a room's staircase, tile by tile (the map's roofs "_stairs" {"x,y": "foot" | "flight"}): drawn as steps whatever stands there
ROOM_STOPS = set()  # a room's stop tiles ("_stops" ["x,y", ...]): where a spin tile's slide ends, a small steel stud
WET_TREES = set()  # trees standing in water (the map's roofs "_wet" [[x0, x1, y], ...]: the Lake of Rage's flooded wood): the lake carries on under them
LOOK = {}  # a floor's own colours, from its source (the map's or floor's roofs "_look" {"floor", "top", "wall"}): a cave's, tower's or building's
ROOM_GLASS = set()  # a room's invisible walls ("_glass" ["x,y", ...]: Fuchsia Gym's): in the way, drawn as the floor with a faint glint
ROOM_KINDS = {}  # what each piece of furniture is (the map's roofs "_kinds" {"x,y": "crate" | "bed" | "table" | ...}): drawn as that, in its _things colour
ROOM_THINGS = {}  # a room's furniture colours, tile by tile (the map's roofs "_things" {"x,y": colour}: its m tiles, coloured after the original)
BRIDGE_LOOKS = {None: ((168, 124, 140), (112, 78, 96), (204, 164, 176), (96, 64, 80)),
                "wood": ((176, 124, 72), (124, 84, 50), (206, 160, 104), (112, 76, 46)),
                "steel": ((150, 156, 168), (104, 110, 124), (196, 202, 212), (84, 90, 104)),
                "solar": ((70, 110, 176), (40, 70, 128), (130, 170, 226), (150, 158, 170))}
EXIT_CHARS = set("<>^vwu+-n1")  # (n: a fifth way out, a cave mouth: Mt. Silver 1F's)
CAVE_FLOOR = (150, 132, 112)
CAVE_FLOOR_DARK = (128, 112, 94)
CAVE_WALL = (112, 92, 78)
CAVE_WALL_DARK = (78, 62, 52)
CAVE_WALL_LIGHT = (140, 118, 100)
SIGN = (196, 150, 96)
SIGN_DARK = (120, 84, 48)
PICKET = (246, 246, 240)
PICKET_DARK = (170, 170, 176)

GROUND = (124, 200, 120)
GROUND_DARK = (104, 178, 104)
PATH = (226, 204, 148)
PATH_EDGE = (198, 174, 118)
BEACH = (240, 226, 178)
PALE_PATH = (196, 236, 204)
PALE_PATH_DARK = (172, 218, 186)
PALE_PATH_EDGE = (150, 204, 160)
ROAD = (128, 128, 138)
ROAD_DARK = (110, 110, 120)
SIDEWALK = (222, 190, 124)
SIDEWALK_LINE = (196, 162, 100)
CURB = (150, 120, 80)
SEA = (76, 140, 222)
SEA_DARK = (58, 116, 196)
FOAM = (220, 238, 252)
GRASS = (72, 158, 82)
GRASS_DARK = (44, 116, 58)
TRUNK = (110, 76, 46)
LEAF = (52, 132, 72)
LEAF_DARK = (34, 98, 56)
LEAF_LIGHT = (96, 178, 98)
FENCE = (176, 124, 76)
FENCE_DARK = (118, 80, 46)
ROCK = (150, 140, 128)
ROCK_DARK = (104, 96, 88)

_SNOW = {"GROUND": (238, 244, 250), "GROUND_DARK": (216, 226, 238), "GRASS": (196, 216, 232), "GRASS_DARK": (150, 180, 208),
         "LEAF": (128, 172, 160), "LEAF_DARK": (76, 122, 116), "LEAF_LIGHT": (240, 246, 252), "PATH": (222, 228, 238), "PATH_EDGE": (196, 206, 222)}

_MARSH = {"GROUND": (104, 186, 150), "GROUND_DARK": (84, 164, 132), "GRASS": (58, 112, 108), "GRASS_DARK": (36, 80, 84),
          "LEAF": (48, 128, 70), "LEAF_DARK": (30, 94, 54), "LEAF_LIGHT": (90, 172, 96), "PATH": (150, 176, 140), "PATH_EDGE": (120, 150, 118)}
_SWAPS = {"snow": _SNOW, "marsh": _MARSH}

# (roof, roof shade, wall) for each kind of building
ROOFS = {"center": ((232, 92, 64), (184, 60, 44), (248, 236, 216)),
         "mart": ((72, 122, 214), (48, 88, 168), (240, 240, 232)),
         "lab": ((150, 162, 184), (112, 122, 146), (232, 232, 236)),
         "home": ((96, 170, 108), (62, 128, 76), (238, 226, 200)),
         "gate": ((70, 168, 170), (44, 124, 128), (220, 214, 196)),
         "house": ((80, 152, 166), (52, 112, 126), (236, 222, 196)),
         "gent": ((222, 128, 150), (176, 90, 112), (240, 226, 200)),
         "fisher": ((222, 128, 150), (176, 90, 112), (240, 226, 200)),
         "rival": ((214, 72, 64), (164, 46, 42), (240, 228, 206)),
         "school": ((84, 160, 92), (52, 116, 62), (238, 226, 200)),
         "oldman": ((96, 170, 108), (62, 128, 76), (232, 220, 196)),
         "museum": ((214, 120, 160), (168, 84, 120), (236, 228, 220)),
         "aide": ((72, 122, 214), (48, 88, 168), (236, 226, 200)),
         "cave": ((150, 116, 84), (108, 80, 56), (70, 52, 40)),
         "daycare": ((222, 150, 70), (176, 110, 48), (240, 228, 206)),
         "bill": ((120, 170, 220), (80, 130, 180), (240, 236, 226)),
         "harbor": ((214, 84, 64), (164, 56, 42), (226, 220, 210)),
         "guru": ((232, 150, 60), (186, 110, 40), (240, 228, 206)),
         "fanclub": ((96, 170, 108), (62, 128, 76), (232, 226, 210)),
         "tunnel": ((150, 150, 160), (110, 110, 120), (210, 210, 214))}


def cell(art, x, y):
    return art[y][x] if 0 <= y < len(art) and 0 <= x < len(art[0]) else "T"


def at_sea(art, x, y):
    """Is this way out (< > ^ v) out on open water: sea on every side but the map's edge and its own kind? Then you Surf onto it."""
    c = art[y][x]
    near = [cell(art, x + dx, y + dy) for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)) if 0 <= x + dx < len(art[0]) and 0 <= y + dy < len(art)]
    return c in "<>^v" and (any(n in SEA_CHARS for n in near) or c in near) and all(n in "o~qcT[]{}:" or n == c for n in near)


def buildings(art):
    """{letter: pygame.Rect in tiles} (a building takes in its doors)."""
    out = {}
    for y, row in enumerate(art):
        for x, c in enumerate(row):
            if c.isupper() and c not in "TDNX":
                out[c] = out[c].union(pygame.Rect(x, y, 1, 1)) if c in out else pygame.Rect(x, y, 1, 1)
    for y, row in enumerate(art):  # (a door in its bottom row)
        for x, c in enumerate(row):
            if c == "D":
                own = door_owner(art, x, y)
                if own in out:  # (a door on a porch: the porch's own building, not the one behind it)
                    out[own] = out[own].union(pygame.Rect(x, y, 1, 1))
                    continue
                for k, r in out.items():
                    if r.left <= x < r.right and r.top <= y <= r.bottom:
                        out[k] = r.union(pygame.Rect(x, y, 1, 1))
    return out


def door_owner(art, x, y):
    """The building letter a door on a porch belongs to: the letter beside it in its own row, when the building
    above it doesn't reach down into that row (a porch standing out in front: Jubilife's Trainers' School).
    None: an ordinary door, in its building's bottom row."""
    is_b = lambda c: c.isupper() and c not in "TDNX"
    above = cell(art, x, y - 1)
    beside = [c for c in (cell(art, x - 1, y), cell(art, x + 1, y)) if is_b(c)]
    if not beside or above in beside or (is_b(above) and above in art[y]):
        return None
    return beside[0]


def doors(art):
    """{(x, y): building letter} for every D."""
    rects = buildings(art)
    found = {}
    for y, row in enumerate(art):
        for x, c in enumerate(row):
            if c == "D":
                found[(x, y)] = next((k for k, r in rects.items() if r.collidepoint(x, y)), None)
                if found[(x, y)] is None and cell(art, x, y + 1) in rects:  # (a door mat at the end of a pier, its building just below it: One Island's harbour)
                    found[(x, y)] = cell(art, x, y + 1)
    return found


def walkable(art, x, y):
    return cell(art, x, y) in OPEN


def signs(art):
    """The signs' tiles, in reading order (the map's "signs" lines go to them in this order)."""
    return [(x, y) for y, row in enumerate(art) for x, c in enumerate(row) if c == "!"]


def surface(art, kinds, tile, roofs=None, theme=None):
    """The whole map drawn, tile px a tile (roofs: {building letter: roof colour}, the map's own; theme
    "cave": a cave's floor and walls)."""
    if theme in _SWAPS:  # snow country (Sinnoh's north): the same map under snow: white ground, frosted grass and trees; a marsh: wet teal ground, reeds
        _SNOW = _SWAPS[theme]
        old = {k: globals()[k] for k in _SNOW}
        globals().update(_SNOW)
        try:
            return surface(art, kinds, tile, roofs, None)
        finally:
            globals().update(old)
    global _THEME, BRIDGE_LOOK
    _THEME = theme
    big_rocks = _big_rocks(art) if (roofs or {}).get("_rocks") == "big" else {}  # (FireRed's sea rocks: one rock to four tiles)
    global ROOM_LOOK, ROOM_THINGS, ROOM_STAIRS
    ROOM_STAIRS = (roofs or {}).get("_stairs") or {}
    global ROOM_STOPS
    ROOM_STOPS = set((roofs or {}).get("_stops") or [])
    ROOM_THINGS = (roofs or {}).get("_things") or {}
    global LOOK, ROOM_KINDS
    ROOM_KINDS = (roofs or {}).get("_kinds") or {}
    global ROOM_GLASS
    ROOM_GLASS = set((roofs or {}).get("_glass") or [])
    LOOK = {k: tuple(v) for k, v in ((roofs or {}).get("_look") or {}).items()}
    global WET_TREES
    WET_TREES = {(x, y) for x0, x1, y in (roofs or {}).get("_wet") or () for x in range(x0, x1 + 1)}
    ROOM_LOOK = ((roofs or {}).get("_floor"), (roofs or {}).get("_wall"))
    BRIDGE_LOOK = (roofs or {}).get("_bridge")  # (the map's own bridges: "wood" planks, "steel" (a cycling road), "solar" panels; else the log bridge)
    h, w = len(art), len(art[0])
    surf = pygame.Surface((w * tile, h * tile))
    rng = random.Random(f"{w}x{h}:{''.join(art[0])}")
    # the ground first, everywhere (under the trees and buildings too)
    for y in range(h):
        for x in range(w):
            _ground(surf, art, x, y, tile, rng)
    snow = {tuple(t) for t in (roofs or {}).get("_snow", [])}  # (patches of snow lying on a green map's lawn, where the source has them: Sinnoh)
    for x, y in sorted(snow):
        if 0 <= y < h and 0 <= x < w and art[y][x] == ".":
            _snow_patch(surf, pygame.Rect(x * tile, y * tile, tile, tile), [(x + dx, y + dy) in snow for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0))])
    wet = {tuple(t) for t in (roofs or {}).get("_puddles", [])}  # (puddles on the lawn you walk through: Sinnoh's rainy routes)
    for x, y in sorted(wet):
        if 0 <= y < h and 0 <= x < w and art[y][x] == ".":
            _snow_patch(surf, pygame.Rect(x * tile, y * tile, tile, tile), [(x + dx, y + dy) in wet for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0))],
                        (150, 196, 236), (176, 216, 246))
    for y in range(h):
        for x in range(w):
            c = art[y][x]
            r = pygame.Rect(x * tile, y * tile, tile, tile)
            if LOOK and _THEME in ("tunnel", "tower") and c in "+-n<>^v":  # inside a building drawn in its source's colours: stairs between floors, a red mat at each way out
                if c in "+-":
                    _stairs_in(surf, r, c == "+")
                else:
                    mat = r.inflate(-6, -r.h // 3)
                    pygame.draw.rect(surf, (150, 40, 36), mat.move(0, 2), border_radius=5)
                    pygame.draw.rect(surf, (226, 70, 58), mat, border_radius=5)
                    pygame.draw.rect(surf, (246, 130, 110), mat.inflate(-10, -10), 2, border_radius=4)
                continue
            if c == "c" and f"{x},{y}" in ROOM_THINGS:  # something standing in a room that the map holds as wall (a long table, a bed): its floor, then the thing in its own colour
                col = tuple(ROOM_THINGS[f"{x},{y}"])
                same = lambda a, b: tuple(ROOM_THINGS.get(f"{a},{b}") or ()) == col
                pygame.draw.rect(surf, LOOK.get("floor") or tuple(ROOM_LOOK[0] or (176, 176, 168)), r)
                if f"{x},{y}" in ROOM_KINDS:
                    _furniture(surf, r, ROOM_KINDS[f"{x},{y}"], col, lambda dx, dy: ROOM_KINDS.get(f"{x + dx},{y + dy}") == ROOM_KINDS[f"{x},{y}"])
                    continue
                body = pygame.Rect(r.x + (0 if same(x - 1, y) else 3), r.y + (0 if same(x, y - 1) else 4),
                                   tile - (0 if same(x - 1, y) else 3) - (0 if same(x + 1, y) else 3), tile - (0 if same(x, y - 1) else 4) - (0 if same(x, y + 1) else 2))
                pygame.draw.rect(surf, col, body)
                if not same(x, y - 1):
                    pygame.draw.rect(surf, tuple(min(255, v + 40) for v in col), (body.x, body.y, body.w, 5))
                if not same(x, y + 1):
                    pygame.draw.rect(surf, tuple(v * 2 // 3 for v in col), (body.x, body.bottom - tile // 4, body.w, tile // 4))
                continue
            if c == "#":
                _fence(surf, art, x, y, r)
            elif c == "k":
                _fence(surf, art, x, y, r, "k", PICKET, PICKET_DARK)
            elif c in "gjr" and _THEME == "ruins":  # old ruins (the Ruins of Alph): g a broken sandstone wall, j a broken column, r rubble
                _ruin(surf, art, x, y, r, c)
            elif c == "r" and _THEME != "tower":
                _rock(surf, r)
            elif c == "2":  # a small tree (Cut): a round little bush of a tree on a thin trunk
                cx, cy = r.centerx, r.centery
                pygame.draw.ellipse(surf, LEAF_DARK, (r.x + 8, r.bottom - 11, r.w - 16, 8))
                pygame.draw.rect(surf, TRUNK, (cx - 3, cy + 2, 6, r.h // 2 - 6))
                pygame.draw.circle(surf, LEAF_DARK, (cx, cy - 1), r.w // 3)
                pygame.draw.circle(surf, LEAF_LIGHT, (cx - 2, cy - 4), r.w // 5)
                pygame.draw.line(surf, LEAF_DARK, (cx - 6, cy - 1), (cx + 6, cy - 1), 2)
            elif c == "7":  # a steep muddy slope (the Bicycle rides up it): brown ruts running down it
                pygame.draw.rect(surf, (150, 112, 78), r)
                for i in range(r.x + 4, r.right - 2, 7):
                    pygame.draw.line(surf, (104, 74, 50), (i, r.y + 2), (i - 2, r.bottom - 2), 2)
            elif c in "3456":  # a spin tile: a steel plate with an arrow the way it sends you
                plate = r.inflate(-4, -4)
                pygame.draw.rect(surf, (176, 182, 194), plate, border_radius=4)
                pygame.draw.rect(surf, (92, 98, 114), plate, 2, border_radius=4)
                dx, dy = [(-1, 0), (1, 0), (0, -1), (0, 1)]["3456".index(c)]
                cx, cy, q = r.centerx, r.centery, r.w // 4
                tip = (cx + dx * q, cy + dy * q)
                pygame.draw.polygon(surf, (222, 96, 60), [tip, (cx - dx * q + dy * q, cy - dy * q + dx * q), (cx - dx * q - dy * q, cy - dy * q - dx * q)])
            elif c == "0":  # a cracked rock (Rock Smash breaks it): a rock, split by dark cracks
                _rock(surf, r)
                cx, cy = r.centerx, r.centery
                pygame.draw.lines(surf, (40, 34, 30), False, [(cx - 2, cy - 9), (cx + 3, cy - 3), (cx - 3, cy + 2), (cx + 2, cy + 8)], 2)
                pygame.draw.line(surf, (40, 34, 30), (cx + 3, cy - 3), (cx + 9, cy - 5), 2)
                pygame.draw.line(surf, (40, 34, 30), (cx - 3, cy + 2), (cx - 9, cy + 4), 2)
            elif c == "@":  # a gravestone out in the open: a rounded grey slab on its plinth (Mt. Pyre)
                pygame.draw.ellipse(surf, (60, 110, 70), (r.x + 6, r.bottom - 12, r.w - 12, 8))
                stone = pygame.Rect(r.x + r.w // 4, r.y + 5, r.w // 2, r.h - 13)
                pygame.draw.rect(surf, (188, 190, 204), stone, border_top_left_radius=9, border_top_right_radius=9)
                pygame.draw.rect(surf, (104, 108, 128), stone, 2, border_top_left_radius=9, border_top_right_radius=9)
                pygame.draw.line(surf, (104, 108, 128), (stone.x + 4, stone.y + 9), (stone.right - 5, stone.y + 9), 2)
                pygame.draw.rect(surf, (150, 152, 168), (stone.x - 3, stone.bottom - 3, stone.w + 6, 5), border_radius=2)
            elif c == "i":  # an iron railing: blue arches (Saffron's edges)
                _railing(surf, art, x, y, r)
            elif c == "g":  # a stone gate wall: gray blocks, a pillar every few tiles
                _gate_wall(surf, art, x, y, r)
            elif c == "j":  # a white stone post: a round stump
                pygame.draw.ellipse(surf, (140, 140, 150), (r.x + 8, r.bottom - 16, r.w - 16, 12))
                body = pygame.Rect(r.x + 10, r.y + 12, r.w - 20, r.h - 20)
                pygame.draw.rect(surf, (226, 226, 232), body, border_radius=12)
                pygame.draw.ellipse(surf, (248, 248, 252), (body.x, body.y - 4, body.w, 16))
                pygame.draw.rect(surf, (160, 160, 174), body, 2, border_radius=12)
            elif c == "y":  # a sofa: red cushions on a dark frame
                pygame.draw.rect(surf, (120, 40, 36), r.inflate(-6, -10))
                pygame.draw.rect(surf, (214, 64, 52), r.inflate(-12, -18).move(0, 2), border_radius=6)
                pygame.draw.line(surf, (240, 120, 100), (r.x + 10, r.y + 16), (r.right - 10, r.y + 16), 2)
            elif c == "z":  # a potted plant
                pygame.draw.rect(surf, (176, 110, 60), (r.centerx - 10, r.bottom - 22, 20, 16), border_radius=3)
                pygame.draw.circle(surf, (40, 120, 60), (r.centerx, r.y + 22), 15)
                pygame.draw.circle(surf, (70, 160, 80), (r.centerx - 4, r.y + 18), 8)
            elif c == "m" and _THEME == "room" and f"{x},{y}" in ROOM_GLASS:  # an invisible wall (Fuchsia Gym's): the floor shows through, a faint glint at its corners
                fl = tuple(ROOM_LOOK[0] or (222, 206, 160))
                pygame.draw.rect(surf, fl, r)
                hi = tuple(min(255, v + 26) for v in fl)
                for cx, cy in ((r.x + 5, r.y + 5), (r.right - 6, r.bottom - 6)):
                    pygame.draw.line(surf, hi, (cx - 3, cy), (cx + 3, cy), 1)
                    pygame.draw.line(surf, hi, (cx, cy - 3), (cx, cy + 3), 1)
            elif c == "m" and f"{x},{y}" in ROOM_KINDS and f"{x},{y}" in ROOM_THINGS:  # a piece of furniture drawn as what it is
                _furniture(surf, r, ROOM_KINDS[f"{x},{y}"], tuple(ROOM_THINGS[f"{x},{y}"]), lambda dx, dy: ROOM_KINDS.get(f"{x + dx},{y + dy}") == ROOM_KINDS[f"{x},{y}"])
            elif c == "m" and f"{x},{y}" in ROOM_THINGS:  # a piece of furniture in its own colour (a counter, a case, a shelf, a table): a block, joined to its neighbours
                col = tuple(ROOM_THINGS[f"{x},{y}"])
                same = lambda a, b: cell(art, a, b) == "m" and tuple(ROOM_THINGS.get(f"{a},{b}") or ()) == col
                body = pygame.Rect(r.x + (0 if same(x - 1, y) else 3), r.y + (0 if same(x, y - 1) else 4),
                                   tile - (0 if same(x - 1, y) else 3) - (0 if same(x + 1, y) else 3), tile - (0 if same(x, y - 1) else 4) - (0 if same(x, y + 1) else 2))
                pygame.draw.rect(surf, col, body)
                if not same(x, y - 1):  # its lit top edge
                    pygame.draw.rect(surf, tuple(min(255, v + 40) for v in col), (body.x, body.y, body.w, 5))
                if not same(x, y + 1):  # its front, in shade
                    pygame.draw.rect(surf, tuple(v * 2 // 3 for v in col), (body.x, body.bottom - tile // 4, body.w, tile // 4))
                for side, ok in ((body.x, same(x - 1, y)), (body.right - 2, same(x + 1, y))):
                    if not ok:
                        pygame.draw.rect(surf, tuple(v // 2 for v in col), (side, body.y, 2, body.h))
            elif c == "m":  # a machine: a console panel with its lights
                _machine(surf, art, x, y, r)
            elif c == "h":  # a fire hydrant
                pygame.draw.ellipse(surf, (90, 60, 40), (r.centerx - 10, r.bottom - 12, 20, 8))
                pygame.draw.rect(surf, (200, 56, 44), (r.centerx - 8, r.y + 18, 16, r.h - 26), border_radius=4)
                pygame.draw.rect(surf, (230, 90, 70), (r.centerx - 10, r.y + 12, 20, 9), border_radius=4)
                pygame.draw.rect(surf, (150, 40, 32), (r.centerx - 13, r.y + 26, 26, 6), border_radius=3)
            elif c == "q" and (x, y) in big_rocks:  # one of the four tiles of a big sea rock: drawn once, from its top left tile
                if big_rocks[(x, y)] == (x, y):
                    big = pygame.Rect(r.x, r.y, tile * 2, tile * 2).inflate(-tile // 2, -tile // 2)
                    _rock(surf, big)
                    pygame.draw.arc(surf, FOAM, big.inflate(tile // 4, -tile // 4).move(0, tile // 3), 3.4, 6.0, 3)
            elif c == "q":  # a rock in the sea (the lanes' edges)
                _rock(surf, r)
                pygame.draw.arc(surf, FOAM, r.inflate(-4, -10).move(0, 8), 3.4, 6.0, 3)
            elif c == "x" and cell(art, x - 1, y) != "x" and cell(art, x, y - 1) != "x":  # a whirlpool (2 x 2 tiles)
                _whirlpool(surf, r)
            elif c == "!":
                _sign(surf, r)
            elif c == "l":
                _lamp(surf, r)
            elif c == "1" and _THEME in ("tunnel", "room"):  # in a building: a warp panel (Team Galactic's, Saffron Gym's): a glowing pad
                pad = r.inflate(-6, -6)
                pygame.draw.rect(surf, (40, 60, 90), pad, border_radius=6)
                pygame.draw.rect(surf, (96, 226, 220), pad.inflate(-6, -6), border_radius=5)
                pygame.draw.rect(surf, (220, 252, 250), pad.inflate(-16, -16), border_radius=4)
                pygame.draw.rect(surf, (30, 44, 70), pad, 2, border_radius=6)
            elif c == "1" and (roofs or {}).get("_passage") == "stairs":  # a staircase between decks or floors (the S.S. Anne, the Rocket Hideout): steps, a rail each side
                pygame.draw.rect(surf, (150, 156, 176), r.inflate(-4, -4), border_radius=3)
                for i in range(6, tile - 6, max(6, tile // 6)):
                    pygame.draw.line(surf, (236, 238, 244), (r.x + 7, r.y + i), (r.right - 8, r.y + i), 3)
                    pygame.draw.line(surf, (96, 100, 124), (r.x + 7, r.y + i + 3), (r.right - 8, r.y + i + 3), 1)
                for sx in (r.x + 4, r.right - 7):
                    pygame.draw.rect(surf, (84, 88, 112), (sx, r.y + 4, 3, tile - 8))
            elif c == "1":  # a passage to another floor (a map's "links"): a ladder
                _ladder(surf, r, True)
            elif c == "8":  # deep snow: drifts you sink into
                pygame.draw.rect(surf, (226, 234, 246), r)
                for i, j in ((5, 8), (17, 5), (9, 20), (21, 18)):
                    pygame.draw.arc(surf, (176, 196, 224), (r.x + i, r.y + j, 10, 8), 0.3, 2.9, 2)
                    pygame.draw.line(surf, (250, 252, 255), (r.x + i + 2, r.y + j + 7), (r.x + i + 8, r.y + j + 7), 1)
            elif c == "9":  # deep marsh mud: dark, wet, a few reeds standing in it
                pygame.draw.rect(surf, (52, 86, 92), r)
                for i, j in ((4, 6), (16, 14), (8, 22)):
                    pygame.draw.ellipse(surf, (36, 62, 70), (r.x + i, r.y + j, 12, 5))
                    pygame.draw.line(surf, (110, 150, 150), (r.x + i + 2, r.y + j + 1), (r.x + i + 7, r.y + j + 1), 1)
                for i in (7, 20):
                    pygame.draw.line(surf, (140, 170, 96), (r.x + i, r.bottom - 6), (r.x + i + 2, r.bottom - 16), 2)
            elif c in "+-":
                _ladder(surf, r, c == "+")
    for o in (roofs or {}).get("_fittings") or ():  # a room's drawn objects, over its furniture blocks (the Prize Corner's cases)
        fitting(surf, o, tile)
    if _THEME != "room":  # stop tiles on a route map's floor (the Rocket Hideout): a small steel stud
        for spot in ROOM_STOPS:
            sx, sy = (int(v) for v in spot.split(","))
            if 0 <= sy < h and 0 <= sx < w:
                c0 = (sx * tile + tile // 2, sy * tile + tile // 2)
                pygame.draw.circle(surf, (120, 126, 140), c0, tile // 5)
                pygame.draw.circle(surf, (214, 218, 226), c0, tile // 9)
    for k, rect in sorted(buildings(art).items(), key=lambda kv: kv[1].bottom):
        _building(surf, art, rect, kinds.get(k, "house"), tile, (roofs or {}).get(k))
    big = [tuple(t) for t in (roofs or {}).get("_big_trees", []) if all(0 <= t[1] + b < h and 0 <= t[0] + a < w and art[t[1] + b][t[0] + a] == "T" for a in (0, 1) for b in (0, 1))]  # (a map's big trees: two tiles by two, as the source has them: Sinnoh)
    under = {(bx + a, by + b) for bx, by in big for a in (0, 1) for b in (0, 1)}
    order = [(y, x, 1) for y in range(h) for x in range(w) if art[y][x] == "T" and (x, y) not in under] + [(by + 1, bx, 2) for bx, by in big]
    for y, x, size in sorted(order):  # trees last, top to bottom: a lower one stands in front
        if size == 2:
            _big_tree(surf, pygame.Rect(x * tile, (y - 1) * tile, tile * 2, tile * 2))
        else:
            _tree(surf, pygame.Rect(x * tile, y * tile, tile, tile), rng)
    for y in range(h):  # (a turbine stands taller than its tile, so it goes over the trees behind it)
        for x in range(w):
            if art[y][x] == "t":
                _turbine(surf, pygame.Rect(x * tile, y * tile, tile, tile))
    return surf


def _big_rocks(art):
    """{tile: its rock's top left tile} for every full 2 x 2 block of sea rock (q), taken in reading order."""
    out = {}
    for y in range(len(art) - 1):
        for x in range(len(art[0]) - 1):
            four = [(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)]
            if all(art[b][a] == "q" and (a, b) not in out for a, b in four):
                for t in four:
                    out[t] = (x, y)
    return out


def _ledge(surf, art, x, y, r, way):
    """A ledge's lip over its ground: a drop on the side you land, a round stone at each end of the run."""
    lip, dark, tile = (168, 124, 88), (104, 74, 58), r.w
    if way == (0, 1):
        band = pygame.Rect(r.x, r.centery - 2, tile, tile // 3)
    elif way == (1, 0):
        band = pygame.Rect(r.centerx - 2, r.y, tile // 3, tile)
    else:
        band = pygame.Rect(r.centerx - tile // 3 + 2, r.y, tile // 3, tile)
    pygame.draw.rect(surf, dark, band.move(way[0] * 3, way[1] * 4))  # (its shadow, on the low side)
    pygame.draw.rect(surf, lip, band)
    if way[1]:
        pygame.draw.line(surf, (214, 176, 132), band.topleft, band.topright, 2)
        ends = ((-1, 0, band.x + 7), (1, 0, band.right - 7))
        for dx, _dy, cx in ends:
            if cell(art, x + dx, y) != art[y][x]:
                pygame.draw.circle(surf, dark, (cx, band.centery + 2), 9)
                pygame.draw.circle(surf, (190, 150, 112), (cx, band.centery), 8)
                pygame.draw.circle(surf, (226, 196, 160), (cx - 2, band.centery - 3), 3)
    else:
        pygame.draw.line(surf, (214, 176, 132), band.topleft, band.bottomleft, 2)
        for dy, cy in ((-1, band.y + 7), (1, band.bottom - 7)):
            if cell(art, x, y + dy) != art[y][x]:
                pygame.draw.circle(surf, dark, (band.centerx, cy + 2), 9)
                pygame.draw.circle(surf, (190, 150, 112), (band.centerx, cy), 8)
                pygame.draw.circle(surf, (226, 196, 160), (band.centerx - 2, cy - 3), 3)


def _over_sea(art, x, y):
    """A building's tile with the sea at either end of its row of that building: it stands out over the water."""
    c = cell(art, x, y)
    if not c.isupper() or c in "TDNX":
        return False
    for dx in (-1, 1):
        i = x
        while cell(art, i, y) == c and 0 <= i < len(art[0]):
            i += dx
        if 0 <= i < len(art[0]) and art[y][i] in SEA_CHARS:
            return True
    return False


def _ground(surf, art, x, y, tile, rng, as_c=None):
    c = as_c or art[y][x]
    r = pygame.Rect(x * tile, y * tile, tile, tile)
    if as_c is None and c in "XN" and sum(cell(art, x + dx, y + dy) in SEA_CHARS or (x + dx, y + dy) in WET_TREES for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0))) >= 3:
        c = "o"  # a swimmer out at sea: the water carries on under them
    if as_c is None and c in "XN!<>^v" and _THEME is None:  # someone (or a sign, or a way out) on a pier or a sand path: the planks or sand carry on under them (Route 12)
        near = [cell(art, x + dx, y + dy) for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0))]
        for g0 in ",=":
            if sum(n == g0 for n in near) >= (1 if c in "<>^v" else 2) and not any(n in '."df' for n in near):
                return _ground(surf, art, x, y, tile, rng, as_c=g0)
    if as_c is None and c == "D" and _THEME is None and cell(art, x, y - 1) == ",":  # a door at a building's back, off a pier: the planks run in under it (Route 12's lookout)
        return _ground(surf, art, x, y, tile, rng, as_c=",")
    if as_c is None and c == "D" and _THEME is None and cell(art, x - 1, y) == cell(art, x + 1, y) == "=":  # a back door on a sand porch (Fuchsia's fishing house)
        return _ground(surf, art, x, y, tile, rng, as_c="=")
    if as_c is None and c == "T" and (x, y) in WET_TREES:
        c = "o"  # (a tree standing in the lake)
    if as_c is None and _over_sea(art, x, y):
        c = "o"  # (a building standing out over the water: the sea carries on under it: Mossdeep's launch towers)
    if as_c is None and c in "kil!j" and _THEME is None:  # a fence, rail, lamp, sign or post standing in a paved street: the paving carries on under it
        near = [cell(art, x + dx, y + dy) for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0))]
        if sum(n == "e" for n in near) >= 2 and not any(n in '."dfT' for n in near):
            return _ground(surf, art, x, y, tile, rng, as_c="e")
    if as_c is None and _THEME == "ruins" and c in "gjr":  # ruins stand on the ground around them (sand, paving or grass)
        near = [n for n in (cell(art, x + dx, y + dy) for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0), (-1, -1), (1, -1), (-1, 1), (1, 1))) if n in ".=e"]
        return _ground(surf, art, x, y, tile, rng, as_c=max(set(near), key=near.count) if near else "=")
    if as_c is None and c in LEDGES:  # (drawn on the ground you hop from)
        way = LEDGES[c]
        behind = cell(art, x - way[0], y - way[1])
        _ground(surf, art, x, y, tile, rng, as_c=behind if behind in '.=e"ds' else ".")
        _ledge(surf, art, x, y, r, way)
        return
    if c == "," and _THEME != "distortion":  # a plank walkway up among the trees: boards, a rope rail along each open side (Fortree's bridges)
        pygame.draw.rect(surf, (176, 124, 72), r)
        for sx in range(r.x, r.right, max(6, tile // 5)):
            pygame.draw.line(surf, (124, 84, 50), (sx, r.y), (sx, r.bottom), 2)
        for dy, ry in ((-1, r.y), (1, r.bottom - 4)):
            if cell(art, x, y + dy) not in ",n":
                pygame.draw.rect(surf, (224, 204, 150), (r.x, ry, tile, 4))
                pygame.draw.rect(surf, (112, 76, 46), (r.x, ry - 3 if dy < 0 else ry, 4, 7))
        return
    if c == "*":  # lava: a slow molten glow, bright veins, a dark crust at its banks (Mt. Chimney's crater)
        pygame.draw.rect(surf, (214, 62, 18), r)
        for _ in range(3):  # brighter currents
            ax, ay = r.x + rng.randint(0, tile - 18), r.y + rng.randint(2, tile - 8)
            pygame.draw.ellipse(surf, (244, 120, 28), (ax, ay, rng.randint(14, 26), rng.randint(5, 9)))
        for _ in range(2):  # white-hot threads
            ax, ay = r.x + rng.randint(4, tile - 16), r.y + rng.randint(6, tile - 8)
            pygame.draw.arc(surf, (255, 214, 96), (ax, ay, 14, 8), 3.3, 6.0, 2)
        if rng.random() < 0.45:  # a bubble about to burst
            bx, by = r.x + rng.randint(8, tile - 8), r.y + rng.randint(8, tile - 8)
            pygame.draw.circle(surf, (255, 170, 60), (bx, by), 4)
            pygame.draw.circle(surf, (150, 30, 10), (bx, by), 4, 1)
        for (dx, dy), edge in (((0, -1), (r.x, r.y, tile, 5)), ((0, 1), (r.x, r.bottom - 4, tile, 4)), ((-1, 0), (r.x, r.y, 4, tile)), ((1, 0), (r.right - 4, r.y, 4, tile))):
            if cell(art, x + dx, y + dy) != "*":  # the cooled crust where it meets the rock
                pygame.draw.rect(surf, (92, 28, 20), edge)
        return
    if c in BRIDGES:  # a log bridge: the ground it spans underneath, then its logs laid across, a rail along each side
        _ground(surf, art, x, y, tile, rng, as_c=".")
        bridge(surf, r, c)
        return
    if c in "~wuoqx[]{}:" or (c in "<>^v" and as_c is None and at_sea(art, x, y)):
        pygame.draw.rect(surf, (44, 92, 172) if c == ":" else SEA, r)
        if c in CURRENTS:  # a current: long streaks the way it runs, a white crest leading each
            dx, dy = CURRENTS[c]
            for i in range(3):
                off = 8 + i * (tile - 16) // 2 + ((x + y) % 2) * 3
                lead = (x * 7 + y * 11 + i * 13) % (tile // 2)
                if dx:
                    a, b = (r.x + lead, r.y + off), (r.x + lead + tile // 2, r.y + off)
                    tip = b if dx > 0 else a
                    wing = [(tip[0] - dx * 6, tip[1] - 4), tip, (tip[0] - dx * 6, tip[1] + 4)]
                else:
                    a, b = (r.x + off, r.y + lead), (r.x + off, r.y + lead + tile // 2)
                    tip = b if dy > 0 else a
                    wing = [(tip[0] - 4, tip[1] - dy * 6), tip, (tip[0] + 4, tip[1] - dy * 6)]
                pygame.draw.line(surf, SEA_DARK, a, b, 2)
                pygame.draw.lines(surf, FOAM, False, wing, 2)
        else:
            for _ in range(2):
                ax, ay = r.x + rng.randint(4, tile - 26), r.y + rng.randint(6, tile - 14)
                pygame.draw.arc(surf, (30, 68, 140) if c == ":" else SEA_DARK, (ax, ay, 22, 10), 0.3, 2.8, 2)
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):  # foam where it meets the land
            n = cell(art, x + dx, y + dy)
            if n not in "~wuoqxTr#c[]{}:$" and _over_sea(art, x + dx, y + dy) and not (n in "<>^v" and at_sea(art, x + dx, y + dy)) and not (
                    n in "XN" and [cell(art, x + dx + ax, y + dy + ay) for ax, ay in ((0, -1), (0, 1), (-1, 0), (1, 0))].count("o") >= 3):  # (a swimmer: no shore)
                edge = {(0, -1): (r.x, r.y, tile, 5), (0, 1): (r.x, r.bottom - 5, tile, 5),
                        (-1, 0): (r.x, r.y, 5, tile), (1, 0): (r.right - 5, r.y, 5, tile)}[(dx, dy)]
                pygame.draw.rect(surf, FOAM, edge)
        return
    if _THEME == "tower":  # the Pokemon Tower: dim purple floors, stone walls, graves (its r)
        if c == "c":
            pygame.draw.rect(surf, LOOK.get("top", (70, 58, 84)), r)
            if cell(art, x, y + 1) != "c":
                if "wall" in LOOK:  # (its own wall, seen from the front)
                    pygame.draw.rect(surf, LOOK["wall"], (r.x, r.bottom - tile // 2, tile, tile // 2))
                    pygame.draw.rect(surf, tuple(v * 2 // 3 for v in LOOK["wall"]), (r.x, r.bottom - 4, tile, 4))
                else:
                    pygame.draw.rect(surf, (48, 40, 60), (r.x, r.bottom - 10, tile, 10))
            return
        _fl = LOOK.get("floor", (128, 112, 140))
        pygame.draw.rect(surf, _fl, r)
        pygame.draw.rect(surf, tuple(max(0, v - 12) for v in _fl), r, 1)
        if c == "r":  # a grave
            stone = pygame.Rect(r.x + 12, r.y + 8, tile - 24, tile - 16)
            pygame.draw.rect(surf, (176, 176, 186), stone, border_top_left_radius=12, border_top_right_radius=12)
            pygame.draw.rect(surf, (110, 110, 124), stone, 2, border_top_left_radius=12, border_top_right_radius=12)
            pygame.draw.line(surf, (110, 110, 124), (stone.centerx, stone.y + 10), (stone.centerx, stone.y + 24), 2)
            pygame.draw.line(surf, (110, 110, 124), (stone.centerx - 6, stone.y + 15), (stone.centerx + 6, stone.y + 15), 2)
        return
    if _THEME == "ship":  # the S.S. Anne: wood decks, white walls
        if c == "c":
            pygame.draw.rect(surf, (236, 236, 240), r)
            if cell(art, x, y + 1) != "c":
                pygame.draw.rect(surf, (150, 160, 190), (r.x, r.bottom - 10, tile, 10))
            return
        if c == "~":
            pygame.draw.rect(surf, SEA, r)
            return
        if c == "=":  # a red carpet (Indigo Plateau's)
            pygame.draw.rect(surf, (168, 44, 40), r)
            if cell(art, x - 1, y) != "=":  # (its gold edges)
                pygame.draw.line(surf, (210, 170, 70), (r.x, r.y), (r.x, r.bottom), 2)
            if cell(art, x + 1, y) != "=":
                pygame.draw.line(surf, (210, 170, 70), (r.right - 2, r.y), (r.right - 2, r.bottom), 2)
            return
        pygame.draw.rect(surf, (204, 168, 112), r)
        for i in range(0, tile, 14):
            pygame.draw.line(surf, (176, 140, 90), (r.x, r.y + i), (r.right, r.y + i), 2)
        if c in "<>^v":
            pygame.draw.rect(surf, (150, 60, 50), r.inflate(-10, -10), border_radius=4)
        return
    if _THEME == "room":  # the inside of a house or shop: its own floor and wall colours, a rug (=), a door mat on each way out
        floor, wall = tuple(ROOM_LOOK[0] or (222, 206, 160)), tuple(ROOM_LOOK[1] or (236, 232, 214))
        if f"{x},{y}" in ROOM_STAIRS:  # a staircase to another floor: wooden steps running across, a white rail along each open side
            step, edge = (214, 180, 96), (140, 108, 52)
            pygame.draw.rect(surf, step, r)
            for i in range(0, tile, max(6, tile // 4)):
                pygame.draw.rect(surf, edge, (r.x + i, r.y, 3, tile))
                pygame.draw.rect(surf, (238, 212, 140), (r.x + i + 3, r.y, 3, tile))
            for dy, ry in ((-1, r.y), (1, r.bottom - 5)):
                if f"{x},{y + dy}" not in ROOM_STAIRS:
                    pygame.draw.rect(surf, (244, 244, 240), (r.x, ry, tile, 5))
                    pygame.draw.rect(surf, (150, 150, 160), (r.x, ry + (4 if dy < 0 else 0), tile, 1))
            if ROOM_STAIRS[f"{x},{y}"] == "foot":  # (where you step on: an arrow up the flight)
                way = 1 if f"{x + 1},{y}" in ROOM_STAIRS else -1
                cx, cy, q = r.centerx, r.centery, tile // 5
                pygame.draw.polygon(surf, (120, 60, 40), [(cx + way * q, cy), (cx - way * q, cy - q), (cx - way * q, cy + q)])
            return
        if c == "c":
            pygame.draw.rect(surf, wall, r)
            if cell(art, x, y + 1) != "c":  # (its skirting, where the floor begins)
                pygame.draw.rect(surf, tuple(v * 2 // 3 for v in wall), (r.x, r.bottom - 8, tile, 8))
            return
        pygame.draw.rect(surf, floor, r)
        pygame.draw.rect(surf, tuple(max(0, v - 18) for v in floor), r, 1)
        if c == "=":  # a rug
            pygame.draw.rect(surf, (112, 176, 110), r)
            for (dx, dy), edge in (((0, -1), (r.x, r.y, tile, 5)), ((0, 1), (r.x, r.bottom - 5, tile, 5)), ((-1, 0), (r.x, r.y, 5, tile)), ((1, 0), (r.right - 5, r.y, 5, tile))):
                if cell(art, x + dx, y + dy) != "=":
                    pygame.draw.rect(surf, (236, 236, 224), edge)
        elif c == "e":  # a flight of stairs
            pygame.draw.rect(surf, (196, 170, 96), r)
            for i in range(0, tile, tile // 4):
                pygame.draw.line(surf, (128, 104, 56), (r.x, r.y + i), (r.right, r.y + i), 3)
        elif f"{x},{y}" in ROOM_STOPS:  # a stop tile
            pygame.draw.circle(surf, (120, 126, 140), r.center, tile // 5)
            pygame.draw.circle(surf, (214, 218, 226), r.center, tile // 9)
        elif c in "<>^v":  # a door mat
            mat = r.inflate(-8, -12)
            pygame.draw.rect(surf, (200, 66, 56), mat, border_radius=4)
            pygame.draw.rect(surf, (244, 196, 180), mat, 3, border_radius=4)
        return
    if _THEME == "distortion":  # the Distortion World: slabs of red rock adrift in a deep blue void, small stones to step across on
        void = (22, 28, 112)
        if c in "c,":
            pygame.draw.rect(surf, void, r)
            if rng.random() < 0.06:  # a far-off slab, glowing faintly below
                gx, gy = r.x + rng.randint(4, tile - 14), r.y + rng.randint(4, tile - 12)
                pygame.draw.rect(surf, (36, 52, 150), (gx, gy, 10, 7), border_radius=2)
                pygame.draw.line(surf, (60, 110, 230), (gx + 4, gy + 7), (gx + 4, gy + 13), 2)
            if c == ",":  # a stepping stone
                st = r.inflate(-10, -12)
                pygame.draw.rect(surf, (30, 34, 70), st.move(0, 6), border_radius=6)
                pygame.draw.rect(surf, (204, 108, 118), st, border_radius=6)
                pygame.draw.rect(surf, (150, 70, 84), st, 2, border_radius=6)
            return
        if c not in "o":
            if cell(art, x, y + 1) in "c,":  # the slab's lit edge, hanging over the void
                pygame.draw.rect(surf, void, r)
                pygame.draw.rect(surf, (40, 60, 170), (r.x, r.bottom - 6, tile, 6))
                body = pygame.Rect(r.x, r.y, tile, tile - 6)
            else:
                body = r
            pygame.draw.rect(surf, (204, 108, 118), body)
            for k in range(2):  # the rock's six-sided plates
                yy = body.y + 4 + k * (tile // 2)
                pygame.draw.line(surf, (164, 78, 92), (r.x + 2, yy), (r.right - 3, yy), 1)
                pygame.draw.line(surf, (164, 78, 92), (r.x + (tile // 2 if k else 4), yy), (r.x + (tile // 2 if k else 4), min(body.bottom - 1, yy + tile // 2)), 1)
            return
    if _THEME == "tunnel":  # the Underground Path: concrete, painted lines, stair rails
        if c == "c":
            pygame.draw.rect(surf, LOOK.get("top", (70, 72, 80)), r)
            if cell(art, x, y + 1) != "c":
                if "wall" in LOOK:  # (its own wall, seen from the front)
                    pygame.draw.rect(surf, LOOK["wall"], (r.x, r.bottom - tile // 2, tile, tile // 2))
                    pygame.draw.rect(surf, tuple(v * 2 // 3 for v in LOOK["wall"]), (r.x, r.bottom - 4, tile, 4))
                else:
                    pygame.draw.rect(surf, (52, 54, 60), (r.x, r.bottom - 8, tile, 8))
            return
        _fl = LOOK.get("floor", (176, 176, 168))
        pygame.draw.rect(surf, _fl, r)
        pygame.draw.rect(surf, tuple(max(0, v - 20) for v in _fl) if "floor" in LOOK else (156, 156, 150), r, 1)
        if c in "<>^v":
            for i in range(4):
                pygame.draw.line(surf, (120, 120, 116), (r.x + 6, r.y + 8 + i * 11), (r.right - 6, r.y + 8 + i * 11), 3)
        return
    cave = _THEME in ("cave", "ice", "seabed")
    ice = _THEME == "ice"  # (Seafoam Islands: pale blue ice)
    seabed = _THEME == "seabed"  # (under the sea: Dive's floor)
    wall, wall_dark, wall_light = ((156, 196, 226), (104, 148, 190), (214, 236, 250)) if ice else         (CAVE_WALL, CAVE_WALL_DARK, CAVE_WALL_LIGHT)
    floor, floor_dark = ((206, 228, 242), (176, 206, 228)) if ice else (CAVE_FLOOR, CAVE_FLOOR_DARK)
    if seabed:
        wall, wall_dark, wall_light = (52, 66, 138), (34, 44, 102), (86, 104, 178)
        floor, floor_dark = (72, 104, 184), (58, 86, 162)
    if cave and "floor" in LOOK:  # (this cave's own rock, from its source)
        floor, floor_dark = LOOK["floor"], tuple(max(0, v - 22) for v in LOOK["floor"])
    if cave and "wall" in LOOK:
        wall, wall_dark, wall_light = LOOK["wall"], tuple(v * 2 // 3 for v in LOOK["wall"]), tuple(min(255, v + 36) for v in LOOK["wall"])
    if c == "$":  # a waterfall: white water pouring down (Waterfall climbs it)
        pygame.draw.rect(surf, (52, 120, 200), r)
        for i in range(0, tile, 8):
            pygame.draw.line(surf, (200, 230, 255), (r.x + i + (y % 2) * 4, r.y), (r.x + i + (y % 2) * 4, r.bottom), 2)
        pygame.draw.rect(surf, (236, 246, 255), (r.x, r.bottom - 6, tile, 6))
        return
    if c == "/":  # a rock wall with footholds (Rock Climb scales it)
        pygame.draw.rect(surf, wall if cave else CLIFF, r)
        for j in range(3):
            pygame.draw.ellipse(surf, (170, 170, 176), (r.x + 6 + (j % 2) * (tile // 2 - 4), r.y + 4 + j * (tile // 3), tile // 3, tile // 5))
        return
    if c == "%":  # sheet ice: slick, pale, streaked (you slide across it: the Ice Path)
        pygame.draw.rect(surf, (172, 218, 244), r)
        surf.set_clip(r)
        for i in range(-tile, tile, 18):
            pygame.draw.line(surf, (230, 246, 255), (r.x + i, r.bottom), (r.x + i + tile, r.y), 3)
        surf.set_clip(None)
        pygame.draw.rect(surf, (150, 200, 232), r, 1)
        return
    if c == "&":  # a hole in the floor: a boulder pushed in drops to the floor below
        pygame.draw.rect(surf, floor, r)
        pygame.draw.ellipse(surf, (40, 52, 70), r.inflate(-6, -12))
        pygame.draw.ellipse(surf, (16, 22, 34), r.inflate(-14, -20))
        return
    if c == "c" and cave:  # a cave's rock wall
        pygame.draw.rect(surf, wall, r)
        for _ in range(2):
            sx, sy = r.x + rng.randint(4, tile - 16), r.y + rng.randint(4, tile - 10)
            pygame.draw.line(surf, wall_dark, (sx, sy), (sx + 10, sy + 3), 2)
        if cell(art, x, y + 1) != "c":
            pygame.draw.rect(surf, wall_dark, (r.x, r.bottom - 10, tile, 10))
        if cell(art, x, y - 1) != "c":
            pygame.draw.rect(surf, wall_light, (r.x, r.y, tile, 4))
        return
    if cave and (seabed or c not in "~ws=f"):  # a cave's floor, under everything (its grass: rougher ground, the wild ones')
        pygame.draw.rect(surf, floor, r)
        if seabed and c == '"':  # seaweed: dark fronds swaying up from the sand
            for i in range(4):
                bx = r.x + 6 + i * (tile - 12) // 4 + (y % 2) * 3
                pygame.draw.lines(surf, (24, 84, 96), False, [(bx, r.bottom - 4), (bx + 4, r.bottom - 16), (bx - 2, r.bottom - 28), (bx + 3, r.y + 6)], 3)
                pygame.draw.line(surf, (56, 132, 128), (bx + 4, r.bottom - 16), (bx + 1, r.bottom - 24), 1)
            return
        if rng.random() < 0.2 or c == '"':
            for _ in range(3 if c == '"' else 1):
                pygame.draw.circle(surf, floor_dark, (r.x + rng.randint(8, tile - 8), r.y + rng.randint(8, tile - 8)), 3)
        return
    if c == "c":  # cliff rock: rough stone, a dark lip where it drops to open ground
        pygame.draw.rect(surf, CLIFF, r)
        for _ in range(3):
            sx, sy = r.x + rng.randint(4, tile - 16), r.y + rng.randint(4, tile - 10)
            pygame.draw.line(surf, CLIFF_DARK, (sx, sy), (sx + 10, sy + 3), 2)
            pygame.draw.line(surf, CLIFF_LIGHT, (sx, sy - 2), (sx + 8, sy + 1), 1)
        if cell(art, x, y + 1) not in "cT":
            pygame.draw.rect(surf, CLIFF_DARK, (r.x, r.bottom - 8, tile, 8))
        if cell(art, x, y - 1) not in "cT":
            pygame.draw.rect(surf, CLIFF_LIGHT, (r.x, r.y, tile, 4))
        return
    near4 = [cell(art, x + dx, y + dy) for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0))]
    if c == "d" or (c in "<>^vX!Nlr" and near4.count("d") >= 2):  # a pale grass path (the town's walking paths)
        pygame.draw.rect(surf, PALE_PATH, r)
        for _ in range(3):
            px, py = r.x + rng.randint(4, tile - 8), r.y + rng.randint(4, tile - 8)
            pygame.draw.line(surf, PALE_PATH_DARK, (px, py), (px + 3, py), 2)
        for (dx, dy), edge in (((0, -1), (r.x, r.y, r.w, 3)), ((0, 1), (r.x, r.bottom - 3, r.w, 3)),
                               ((-1, 0), (r.x, r.y, 3, r.h)), ((1, 0), (r.right - 3, r.y, 3, r.h))):
            if cell(art, x + dx, y + dy) == ".":  # (a soft edge where it meets the lawn)
                pygame.draw.rect(surf, PALE_PATH_EDGE, edge)
        return
    if c == "e" or (c in "<>^vX!Nljrh" and near4.count("e") >= (1 if c in "jr" else 2)):  # pale stone pavement (Route 23's plazas)
        pygame.draw.rect(surf, (210, 210, 204), r)
        half = r.w // 2
        pygame.draw.line(surf, (188, 188, 182), (r.x, r.y + half), (r.right, r.y + half), 1)
        pygame.draw.line(surf, (188, 188, 182), (r.x + (half if y % 2 else 0), r.y), (r.x + (half if y % 2 else 0), r.y + half), 1)
        pygame.draw.line(surf, (188, 188, 182), (r.x + (0 if y % 2 else half), r.y + half), (r.x + (0 if y % 2 else half), r.bottom), 1)
        pygame.draw.rect(surf, (196, 196, 190), r, 1)
        return
    if c in "ap":  # a city's road and sidewalks (Saffron)
        _street(surf, art, x, y, r, c, rng)
        return
    base = {"=": PATH, "s": BEACH}.get(c, GROUND)
    city = [cell(art, x + dx, y + dy) for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0))]
    if (c in "<>^vX!Nlih" or c.isupper()) and ("a" in city or "p" in city):  # (on a city street)
        _street(surf, art, x, y, r, "a" if "a" in city and (c in "<>^v" or "p" not in city) else "p", rng)
        return
    if c in "<>^vX!N":  # a way out, a sign, someone standing: the path carries on (or the beach, or the grass)
        near = [cell(art, x + dx, y + dy) for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0))]
        base = PATH if "=" in near and (c != "!" or near.count("=") >= 3) else BEACH if near.count("s") >= 2 or (
            "s" in near and "." not in near and '"' not in near) else GROUND if c != "!" or "." in near else base
    pygame.draw.rect(surf, base, r)
    if base == PATH:  # a soft edge where the path meets the grass
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            if cell(art, x + dx, y + dy) in '.f"N':
                edge = {(0, -1): (r.x, r.y, tile, 3), (0, 1): (r.x, r.bottom - 3, tile, 3),
                        (-1, 0): (r.x, r.y, 3, tile), (1, 0): (r.right - 3, r.y, 3, tile)}[(dx, dy)]
                pygame.draw.rect(surf, PATH_EDGE, edge)
    elif base == GROUND and rng.random() < 0.18 and c in ".N":  # a few tufts
        tx, ty = r.x + rng.randint(8, tile - 14), r.y + rng.randint(10, tile - 10)
        for i in range(3):
            pygame.draw.line(surf, GROUND_DARK, (tx + i * 3, ty), (tx + i * 3 - 1, ty - 5), 2)
    if c == '"':  # tall grass: a clump of blades
        pygame.draw.rect(surf, GRASS, r.inflate(-2, -2), border_radius=6)
        for row in range(2):
            for i in range(4):
                bx = r.x + 5 + i * 12 + (row * 6)
                by = r.y + 12 + row * 20
                pygame.draw.polygon(surf, GRASS_DARK, [(bx, by + 14), (bx + 5, by), (bx + 10, by + 14)])
    elif c == "f":  # flowers
        for _ in range(3):
            fx, fy = r.x + rng.randint(10, tile - 10), r.y + rng.randint(10, tile - 10)
            col = rng.choice([(240, 90, 110), (250, 214, 80), (246, 246, 246), (230, 130, 220)])
            for ox, oy in ((-3, 0), (3, 0), (0, -3), (0, 3)):
                pygame.draw.circle(surf, col, (fx + ox, fy + oy), 3)
            pygame.draw.circle(surf, (250, 230, 120), (fx, fy), 2)


def _turbine(surf, r):
    """A wind turbine: a stone foot, a tall white pole, three blades up in the air."""
    cx, foot, s = r.centerx, r.bottom - 8, r.w / 56
    hub = (cx, int(r.y - 22 * s))
    pygame.draw.line(surf, GROUND_DARK, (cx, foot), (cx + int(24 * s), foot + int(10 * s)), 3)
    pygame.draw.rect(surf, (96, 108, 120), (cx - int(13 * s), foot - int(10 * s), int(26 * s), int(14 * s)), border_radius=3)
    pygame.draw.rect(surf, (214, 222, 228), (cx - int(4 * s), hub[1], max(2, int(8 * s)), foot - hub[1] - int(6 * s)))
    pygame.draw.line(surf, (150, 160, 172), (cx + int(3 * s), hub[1]), (cx + int(3 * s), foot - int(6 * s)), 2)
    for tip, side in (((0, -30), (5, -12)), ((26, 16), (12, 2)), ((-26, 16), (-12, 10))):
        end = (hub[0] + int(tip[0] * s), hub[1] + int(tip[1] * s))
        mid = (hub[0] + int(side[0] * s), hub[1] + int(side[1] * s))
        pygame.draw.polygon(surf, (244, 248, 250), [hub, mid, end])
        pygame.draw.line(surf, (130, 142, 156), hub, end, 1)
    pygame.draw.circle(surf, (96, 108, 120), hub, max(3, int(5 * s)))


def _whirlpool(surf, r):
    """A whirlpool: a dark pit in the sea, ringed by white spiral arms."""
    import math
    cx, cy, R = r.right, r.bottom, r.w * 19 // 20
    pygame.draw.circle(surf, (64, 176, 244), (cx, cy), R)
    pygame.draw.circle(surf, (120, 214, 252), (cx, cy), R * 3 // 5)
    pygame.draw.circle(surf, (24, 96, 200), (cx, cy), R // 4)
    for arm in range(3):
        last = None
        for i in range(44):
            t = i / 43
            a = arm * 2.094 + t * 4.4
            d = R * (0.22 + 0.76 * t)
            p = (int(cx + math.cos(a) * d), int(cy + math.sin(a) * d))
            if last:
                pygame.draw.line(surf, (255, 255, 255), last, p, max(3, r.w // 8))
            last = p
    pygame.draw.circle(surf, (150, 206, 248), (cx, cy), R, max(2, r.w // 16))


def fitting(surf, o, tile, ox=0, oy=0):
    """A drawn object in a room, over its furniture blocks (the map's roofs "_fittings" [{"kind", "rect": [x, y, w, h] in tiles,
    fractions allowed}]; the same kinds as overheads where you walk behind their tops). Kinds: "case_top" (a prize case's
    upper shelf: three boxed prizes), "case" (its lower shelf and glass doors), "window" (a prize window in a counter top),
    "emblem" (the Game Corner's sign on the wall)."""
    x, y, w, h = o["rect"]
    r = pygame.Rect(round(x * tile) + ox, round(y * tile) + oy, round(w * tile), round(h * tile))
    line, white, shade = (72, 76, 104), (240, 244, 248), (188, 196, 212)
    u = max(2, tile // 18)
    kind = o.get("kind")
    if kind == "case_top":
        pygame.draw.rect(surf, white, r, border_radius=u * 2)
        pygame.draw.rect(surf, line, r, u, border_radius=u * 2)
        inner = r.inflate(-u * 6, -u * 4).move(0, -u)
        bw = inner.w // 3
        for i, (c, band) in enumerate((((72, 128, 208), (150, 196, 248)), ((248, 216, 96), (224, 96, 72)), ((120, 208, 144), (240, 244, 248)))):
            b = pygame.Rect(inner.x + i * bw + u, inner.y, bw - u * 2, inner.h)
            pygame.draw.rect(surf, c, b, border_radius=u)
            for k in (1, 2) if i != 1 else (1,):
                yy = b.y + b.h * k // 3
                pygame.draw.rect(surf, band, (b.x, yy - u, b.w, u * 2))
            if i == 1:
                pygame.draw.rect(surf, band, (b.centerx - u, b.y + u, u * 2, b.h - u * 2))
            pygame.draw.rect(surf, line, b, u, border_radius=u)
        pygame.draw.rect(surf, shade, (r.x + u, r.bottom - u * 3, r.w - u * 2, u * 2))
    elif kind == "case":
        pygame.draw.rect(surf, white, r, border_radius=u * 2)
        top = pygame.Rect(r.x + u * 2, r.y + u, r.w - u * 4, r.h * 2 // 5)
        pygame.draw.rect(surf, shade, top)
        for i, c in enumerate(((96, 200, 136), (88, 144, 224), (240, 152, 72))):  # the small prizes on its lower shelf
            cx = top.x + top.w * (2 * i + 1) // 6
            pygame.draw.circle(surf, c, (cx, top.centery), max(3, top.h // 3))
            pygame.draw.circle(surf, line, (cx, top.centery), max(3, top.h // 3), 1)
        glass = pygame.Rect(r.x + u * 2, top.bottom + u, r.w - u * 4, r.bottom - top.bottom - u * 4)
        half = glass.w // 2
        for i in range(2):
            g2 = pygame.Rect(glass.x + i * half + (u if i else 0), glass.y, half - u, glass.h)
            pygame.draw.rect(surf, (136, 196, 248), g2)
            pygame.draw.line(surf, (224, 240, 255), (g2.x + u * 2, g2.bottom - u), (g2.x + g2.h + u, g2.y + u), u)
            pygame.draw.rect(surf, (64, 120, 200), (g2.x, g2.bottom - u * 2, g2.w, u * 2))
        pygame.draw.rect(surf, line, r, u, border_radius=u * 2)
    elif kind == "window":
        slot = pygame.Rect(0, 0, r.w * 3 // 5, max(8, r.h // 4))
        slot.center = (r.centerx, r.y + r.h * 2 // 5)
        pygame.draw.rect(surf, (200, 192, 120), slot.inflate(u * 2, u * 2), border_radius=u * 2)
        pygame.draw.rect(surf, (252, 244, 152), slot, border_radius=u)
    elif kind == "pad":  # a Gym Leader's pad on the floor (Koga's): a gold frame round an orange square
        pygame.draw.rect(surf, (150, 130, 96), r.inflate(-u * 2, -u * 2), border_radius=u * 3)
        pygame.draw.rect(surf, (236, 204, 110), r.inflate(-u * 4, -u * 4), border_radius=u * 3)
        pygame.draw.rect(surf, (244, 160, 88), r.inflate(-u * 10, -u * 10), border_radius=u * 2)
        pygame.draw.rect(surf, (250, 198, 140), r.inflate(-u * 14, -u * 14), border_radius=u * 2)
    elif kind == "emblem":
        pygame.draw.ellipse(surf, (40, 128, 120), r.inflate(0, -r.h // 3))
        pygame.draw.ellipse(surf, (64, 168, 150), r.inflate(-u * 4, -r.h // 3 - u * 4))
        cx, cy, a, b = r.centerx, r.centery, r.w // 3, r.h // 3
        card = [(cx - a, cy - b), (cx + a // 3, cy - b - u * 2), (cx + a, cy + b // 2), (cx - a // 3, cy + b + u)]
        pygame.draw.polygon(surf, (248, 236, 184), card)
        pygame.draw.polygon(surf, line, card, u)
        pygame.draw.polygon(surf, (224, 88, 72), [(cx + a // 3, cy + b // 3), (cx + a, cy + b // 2), (cx + a // 2, cy + b + u)])
        pygame.draw.circle(surf, (64, 136, 232), (cx, cy - u), max(4, b // 2))
        pygame.draw.circle(surf, (200, 228, 255), (cx, cy - u), max(2, b // 5))


def overhead(o, tile):
    """What passes over your head: (image, (x px, y px)). o: {"kind": "rail", "rect": [x, y, w, h]} in tiles; you walk
    underneath it (Goldenrod's Magnet Train line over the main road). The image takes in the shadow it casts below."""
    x, y, w, h = o["rect"]
    if o.get("kind") in ("case_top", "case", "window", "emblem"):  # a room's fitting you walk behind (a prize case's top shelf)
        surf = pygame.Surface((round(w * tile), round(h * tile)), pygame.SRCALPHA)
        fitting(surf, dict(o, rect=[0, 0, w, h]), tile)
        return surf, (round(x * tile), round(y * tile))
    if o.get("kind") == "tops":  # what stands just below pokes up over this row of open tiles and hides your feet, as the original draws it
        # (FireRed's top layer): "of" "tree": the tips of the trees below; "roof": the top edge of the roof below, in "colour"
        surf = pygame.Surface((w * tile, tile), pygame.SRCALPHA)
        for i in range(w):
            r = pygame.Rect(i * tile, 0, tile, tile)
            if o.get("of") == "post":  # a guard rail's post leaning over the lane beside it (the Cycling Road): steel, a red cap
                pw = max(4, tile // 9)
                px = r.x if o.get("side") == "left" else r.right - pw
                pygame.draw.rect(surf, (150, 158, 176), (px, r.y + tile // 5, pw, tile * 4 // 5))
                pygame.draw.rect(surf, (96, 102, 122), (px + (pw - 2 if o.get("side") == "left" else 0), r.y + tile // 5, 2, tile * 4 // 5))
                pygame.draw.rect(surf, (214, 64, 56), (px - (0 if o.get("side") == "left" else 2), r.y + tile // 8, pw + 2, tile // 4), border_radius=3)
                pygame.draw.rect(surf, (248, 150, 130), (px - (0 if o.get("side") == "left" else 2) + 1, r.y + tile // 8 + 1, pw, 3), border_radius=2)
                continue
            if o.get("of") == "roof":
                c = tuple(o.get("colour") or ROOFS["house"][0])
                lip = pygame.Rect(r.x, r.bottom - tile * 2 // 5, tile, tile * 2 // 5)
                pygame.draw.rect(surf, c, lip)
                pygame.draw.rect(surf, tuple(min(255, v + 36) for v in c), (lip.x, lip.y, tile, max(3, tile // 12)))
                pygame.draw.line(surf, tuple(v * 3 // 4 for v in c), (lip.x, lip.bottom - 1), (lip.right, lip.bottom - 1), 2)
            else:
                cx = r.centerx
                pygame.draw.polygon(surf, LEAF_DARK, [(r.x + 3, r.bottom), (cx, r.bottom - tile * 9 // 20), (r.right - 3, r.bottom)])
                pygame.draw.polygon(surf, LEAF, [(r.x + tile // 4, r.bottom), (cx - 1, r.bottom - tile * 7 // 20), (cx + tile // 8, r.bottom)])
        return surf, (x * tile, y * tile)
    if o.get("kind") == "road":  # a raised road, any shape: "runs" [[row, first x, last x], ...] (Route 110's Cycling Road)
        tiles = {(i, r[0]) for r in o["runs"] for i in range(r[1], r[2] + 1)}
        surf = pygame.Surface((w * tile, h * tile + tile // 2), pygame.SRCALPHA)
        for i, j in tiles:  # (the shadow it casts)
            if (i, j + 1) not in tiles:
                pygame.draw.rect(surf, (20, 20, 34, 90), ((i - x) * tile, (j - y + 1) * tile, tile, tile // 2))
        rail, post = max(3, tile // 9), (98, 110, 150)
        for i, j in tiles:
            r = pygame.Rect((i - x) * tile, (j - y) * tile, tile, tile)
            pygame.draw.rect(surf, (222, 230, 238), r)
            pygame.draw.line(surf, (200, 212, 232), (r.x, r.centery), (r.right, r.centery), 1)
            for (dx, dy), edge in (((0, -1), (r.x, r.y, tile, rail)), ((0, 1), (r.x, r.bottom - rail, tile, rail)),
                                   ((-1, 0), (r.x, r.y, rail, tile)), ((1, 0), (r.right - rail, r.y, rail, tile))):
                if (i + dx, j + dy) not in tiles:
                    pygame.draw.rect(surf, (156, 180, 222), edge)
                    pygame.draw.rect(surf, post, (edge[0], edge[1], min(edge[2], rail * 2), min(edge[3], rail * 2)))
        return surf, (x * tile, y * tile)
    if o.get("kind") == "belt":  # a conveyor belt up on its steel frame, any shape: "runs" like a raised road's (Oreburgh's mine yard)
        tiles = {(i, r[0]) for r in o["runs"] for i in range(r[1], r[2] + 1)}
        surf = pygame.Surface((w * tile, h * tile + tile // 2), pygame.SRCALPHA)
        for i, j in tiles:
            if (i, j + 1) not in tiles:
                pygame.draw.rect(surf, (20, 20, 34, 90), ((i - x) * tile, (j - y + 1) * tile, tile, tile // 2))
        edge_w = max(4, tile // 6)
        for i, j in tiles:
            r = pygame.Rect((i - x) * tile, (j - y) * tile, tile, tile)
            pygame.draw.rect(surf, (58, 92, 150), r)
            across = (i - 1, j) in tiles and (i + 1, j) in tiles and not ((i, j - 1) in tiles and (i, j + 1) in tiles)
            for k in range(0, tile, tile // 3):  # the belt's slats, across the way it runs
                if across:
                    pygame.draw.line(surf, (40, 66, 116), (r.x + k, r.y), (r.x + k, r.bottom), 2)
                else:
                    pygame.draw.line(surf, (40, 66, 116), (r.x, r.y + k), (r.right, r.y + k), 2)
            for (dx, dy), edge in (((0, -1), (r.x, r.y, tile, edge_w)), ((0, 1), (r.x, r.bottom - edge_w, tile, edge_w)),
                                   ((-1, 0), (r.x, r.y, edge_w, tile)), ((1, 0), (r.right - edge_w, r.y, edge_w, tile))):
                if (i + dx, j + dy) not in tiles:
                    pygame.draw.rect(surf, (150, 158, 170), edge)
                    pygame.draw.rect(surf, (84, 90, 104), edge, 1)
        return surf, (x * tile, y * tile)
    if o.get("kind") == "rope":  # a rope bridge between tree houses, level with their decks (Fortree's): planks, a rope rail either side
        surf = pygame.Surface((w * tile, h * tile + tile // 3), pygame.SRCALPHA)
        deck = pygame.Rect(0, tile // 4, w * tile, h * tile - tile // 2)
        pygame.draw.rect(surf, (20, 30, 24, 80), deck.move(0, tile // 3))
        pygame.draw.rect(surf, (176, 124, 72), deck)
        for sx in range(0, deck.w, max(6, tile // 5)):
            pygame.draw.line(surf, (124, 84, 50), (sx, deck.y), (sx, deck.bottom), 2)
        for ry in (deck.y, deck.bottom - 3):
            pygame.draw.rect(surf, (224, 204, 150), (0, ry, deck.w, 3))
        for sx in range(0, deck.w + 1, tile):
            pygame.draw.rect(surf, (112, 76, 46), (min(sx, deck.w - 4), deck.y - 5, 4, deck.h + 8))
        return surf, (x * tile, y * tile)
    if o.get("kind") == "torii":  # a red wooden gate over the road (Ecruteak's)
        surf = pygame.Surface((w * tile, h * tile), pygame.SRCALPHA)
        roof = pygame.Rect(0, 0, w * tile, tile)
        pygame.draw.rect(surf, (96, 34, 30), roof)
        for sx in range(0, roof.w, tile // 3):
            pygame.draw.line(surf, (150, 58, 44), (sx, 0), (sx, roof.bottom), 2)
        pygame.draw.rect(surf, (60, 22, 22), (0, roof.bottom - 6, roof.w, 6))
        pygame.draw.rect(surf, (128, 44, 36), (tile // 3, roof.bottom, roof.w - tile * 2 // 3, tile // 4))
        return surf, (x * tile, y * tile)
    surf = pygame.Surface((w * tile, (h + 1) * tile), pygame.SRCALPHA)
    deck = pygame.Rect(0, 0, w * tile, h * tile)
    pygame.draw.rect(surf, (20, 20, 34, 96), (0, deck.bottom, deck.w, tile * 3 // 4))
    pygame.draw.rect(surf, (104, 108, 120), deck)
    pygame.draw.rect(surf, (196, 200, 208), (0, 0, deck.w, tile // 5))
    pygame.draw.rect(surf, (222, 224, 230), (0, deck.bottom - tile * 3 // 4, deck.w, tile * 3 // 4))
    pygame.draw.rect(surf, (140, 142, 152), (0, deck.bottom - tile // 4, deck.w, tile // 4))
    for rail in (tile * 3 // 4, tile * 2):
        for sx in range(tile // 4, deck.w, tile // 2):
            pygame.draw.rect(surf, (70, 62, 58), (sx, rail - tile // 8, tile // 5, tile * 5 // 8))
        pygame.draw.rect(surf, (214, 218, 224), (0, rail, deck.w, 5))
        pygame.draw.rect(surf, (214, 218, 224), (0, rail + tile // 3, deck.w, 5))
    for px in range(tile * 2, deck.w, tile * 8):
        pygame.draw.line(surf, (70, 72, 84), (px, 0), (px, deck.bottom), 3)
    return surf, (x * tile, y * tile)


def draw_overheads(surf, m, tile):
    """A preview's overhead parts, at the end of the drawing (the game draws them over you instead)."""
    for o in m.get("overheads", []) or []:
        img, at = overhead(o, tile)
        surf.blit(img, at)


def _tree(surf, r, rng):
    cx, cy = r.centerx, r.centery
    pygame.draw.ellipse(surf, LEAF_DARK, (r.x + 6, r.bottom - 14, r.w - 12, 12))  # its shadow
    pygame.draw.rect(surf, TRUNK, (cx - 5, cy + 4, 10, r.h // 2 - 6))
    pygame.draw.circle(surf, LEAF_DARK, (cx, cy - 2), r.w // 2 - 1)
    pygame.draw.circle(surf, LEAF, (cx - 2, cy - 6), r.w // 2 - 6)
    pygame.draw.circle(surf, LEAF_LIGHT, (cx - 9, cy - 13), r.w // 6)


def _furniture(surf, r, kind, col, same):
    """A piece of furniture on its tile, drawn as what it is in its own colour (same(dx, dy): the same kind stands on that side, so they join)."""
    t = r.w
    dark, lite = tuple(v * 2 // 3 for v in col), tuple(min(255, v + 40) for v in col)
    deep = tuple(v // 2 for v in col)
    L, R_, U, D = same(-1, 0), same(1, 0), same(0, -1), same(0, 1)
    body = pygame.Rect(r.x + (0 if L else 3), r.y + (0 if U else 4), t - (0 if L else 3) - (0 if R_ else 3), t - (0 if U else 4) - (0 if D else 2))
    cx, cy = r.centerx, r.centery
    if kind == "crate":  # a wooden crate: planks, a frame, a cross brace
        box = r.inflate(-4, -4)
        pygame.draw.rect(surf, deep, box.move(2, 3))
        pygame.draw.rect(surf, col, box)
        for i in range(1, 4):
            pygame.draw.line(surf, dark, (box.x, box.y + i * box.h // 4), (box.right - 1, box.y + i * box.h // 4), 1)
        pygame.draw.line(surf, dark, box.topleft, (box.right - 1, box.bottom - 1), 3)
        pygame.draw.line(surf, dark, (box.right - 1, box.y), (box.x, box.bottom - 1), 3)
        pygame.draw.rect(surf, lite, box, 3)
        pygame.draw.rect(surf, deep, box, 1)
    elif kind == "barrel":  # a drum: a round lid, two hoops
        box = r.inflate(-t // 4, -6)
        pygame.draw.rect(surf, dark, box, border_radius=6)
        pygame.draw.rect(surf, col, box.inflate(-4, 0), border_radius=5)
        for yy in (box.y + box.h // 2, box.bottom - 7):
            pygame.draw.line(surf, deep, (box.x, yy), (box.right - 1, yy), 2)
        pygame.draw.ellipse(surf, lite, (box.x, box.y - 2, box.w, t // 3))
        pygame.draw.ellipse(surf, deep, (box.x, box.y - 2, box.w, t // 3), 1)
    elif kind == "bed":  # a bed: a frame, a white pillow at its head, a blanket in its colour
        pygame.draw.rect(surf, (236, 236, 228), body, border_radius=4)
        if not U:
            pygame.draw.rect(surf, (255, 255, 255), (body.x + 4, body.y + 3, body.w - 8, t // 3), border_radius=5)
            pygame.draw.rect(surf, (196, 200, 210), (body.x + 4, body.y + 3, body.w - 8, t // 3), 1, border_radius=5)
        top = body.y + (t // 2 if not U else 0)
        pygame.draw.rect(surf, col, (body.x + 1, top, body.w - 2, body.bottom - top - 1), border_radius=3)
        pygame.draw.line(surf, lite, (body.x + 2, top + 2), (body.right - 3, top + 2), 2)
        pygame.draw.rect(surf, deep, body, 1, border_radius=4)
    elif kind == "table":  # a table or counter: a lit top, a shaded front edge
        pygame.draw.rect(surf, col, body)
        if not U:
            pygame.draw.rect(surf, lite, (body.x, body.y, body.w, 5))
        if not D:
            pygame.draw.rect(surf, dark, (body.x, body.bottom - t // 4, body.w, t // 4))
            pygame.draw.rect(surf, deep, (body.x, body.bottom - 2, body.w, 2))
        for side, ok in ((body.x, L), (body.right - 2, R_)):
            if not ok:
                pygame.draw.rect(surf, deep, (side, body.y, 2, body.h))
    elif kind == "shelf":  # a bookcase: its frame, two rows of spines
        pygame.draw.rect(surf, dark, body)
        spines = ((204, 72, 64), (72, 122, 204), (236, 196, 84), (96, 170, 108), (232, 232, 224), (150, 96, 170))
        for row in range(2):
            yy = body.y + 4 + row * (body.h - 6) // 2
            hh = (body.h - 6) // 2 - 4
            pygame.draw.rect(surf, deep, (body.x + 2, yy, body.w - 4, hh))
            n = max(3, body.w // 6)
            for i in range(n):
                sp = spines[(i * 5 + row * 3 + r.x // t + r.y // t) % len(spines)]
                pygame.draw.rect(surf, sp, (body.x + 3 + i * (body.w - 6) // n, yy + (i * 7 + row) % 3, (body.w - 6) // n - 1, hh - (i * 7 + row) % 3))
        pygame.draw.rect(surf, lite, (body.x, body.y, body.w, 3))
    elif kind == "tv":  # a television: a dark case, a lit screen, a stand
        case = pygame.Rect(r.x + 4, r.y + 6, t - 8, t - 16)
        pygame.draw.rect(surf, dark, (cx - t // 5, case.bottom - 2, t * 2 // 5, 8))
        pygame.draw.rect(surf, (52, 54, 62), case, border_radius=4)
        pygame.draw.rect(surf, (118, 196, 226), case.inflate(-8, -8), border_radius=3)
        pygame.draw.line(surf, (222, 244, 252), (case.x + 8, case.y + 8), (case.x + case.w // 3, case.y + 6), 2)
    elif kind == "fridge":  # a fridge: tall, pale, a door line and a handle
        box = pygame.Rect(r.x + 5, r.y + 2, t - 10, t - 4)
        pygame.draw.rect(surf, col, box, border_radius=4)
        pygame.draw.rect(surf, lite, (box.x + 2, box.y + 2, box.w - 4, 4), border_radius=2)
        pygame.draw.line(surf, dark, (box.x, box.y + box.h // 3), (box.right - 1, box.y + box.h // 3), 2)
        pygame.draw.rect(surf, deep, (box.right - 8, box.y + box.h // 3 + 5, 3, box.h // 4))
        pygame.draw.rect(surf, deep, box, 1, border_radius=4)
    elif kind == "sink":  # a sink: a counter, a basin, a tap
        pygame.draw.rect(surf, col, body)
        pygame.draw.rect(surf, lite, (body.x, body.y, body.w, 4))
        pygame.draw.ellipse(surf, (150, 170, 190), (cx - t // 4, cy - t // 6, t // 2, t // 3))
        pygame.draw.ellipse(surf, (198, 226, 244), (cx - t // 4 + 2, cy - t // 6 + 2, t // 2 - 4, t // 3 - 4))
        pygame.draw.rect(surf, (120, 124, 134), (cx - 2, body.y + 4, 4, t // 5))
        pygame.draw.rect(surf, dark, (body.x, body.bottom - t // 5, body.w, t // 5))
    elif kind == "bin":  # a bin: a small can with a lid
        box = pygame.Rect(cx - t // 5, cy - t // 6, t * 2 // 5, t // 2)
        pygame.draw.rect(surf, col, box, border_bottom_left_radius=5, border_bottom_right_radius=5)
        pygame.draw.rect(surf, deep, box, 1, border_bottom_left_radius=5, border_bottom_right_radius=5)
        pygame.draw.ellipse(surf, lite, (box.x - 2, box.y - 4, box.w + 4, 9))
        pygame.draw.ellipse(surf, deep, (box.x - 2, box.y - 4, box.w + 4, 9), 1)
    elif kind == "clock":  # a tall clock: its case, a white face with hands, a pendulum
        box = pygame.Rect(r.x + t // 4, r.y + 2, t // 2, t - 4)
        pygame.draw.rect(surf, col, box, border_top_left_radius=8, border_top_right_radius=8)
        pygame.draw.rect(surf, deep, box, 1, border_top_left_radius=8, border_top_right_radius=8)
        pygame.draw.circle(surf, (250, 248, 236), (cx, box.y + t // 4), t // 6)
        pygame.draw.line(surf, (40, 40, 48), (cx, box.y + t // 4), (cx, box.y + t // 4 - t // 9), 2)
        pygame.draw.line(surf, (40, 40, 48), (cx, box.y + t // 4), (cx + t // 10, box.y + t // 4), 2)
        pygame.draw.line(surf, (236, 196, 84), (cx, box.y + t // 2), (cx, box.bottom - 8), 2)
        pygame.draw.circle(surf, (236, 196, 84), (cx, box.bottom - 8), 3)
    elif kind == "pc":  # a computer on its desk: a monitor with a blue screen, a keyboard
        pygame.draw.rect(surf, col, (body.x, cy, body.w, body.bottom - cy))
        pygame.draw.rect(surf, dark, (body.x, body.bottom - 5, body.w, 5))
        mon = pygame.Rect(cx - t // 4, r.y + 4, t // 2, t // 2 - 2)
        pygame.draw.rect(surf, (70, 72, 84), mon, border_radius=3)
        pygame.draw.rect(surf, (96, 168, 236), mon.inflate(-6, -6), border_radius=2)
        pygame.draw.rect(surf, (226, 226, 220), (cx - t // 5, cy + 3, t * 2 // 5, 5), border_radius=2)
    else:  # a machine: a case in its colour, a dark screen, a row of lights
        pygame.draw.rect(surf, col, body, border_radius=3)
        if not U:
            pygame.draw.rect(surf, lite, (body.x, body.y, body.w, 4))
            pygame.draw.rect(surf, (36, 44, 60), (body.x + 4, body.y + 7, body.w - 8, t // 4), border_radius=2)
            pygame.draw.line(surf, (96, 226, 180), (body.x + 7, body.y + 7 + t // 8), (body.right - 8, body.y + 7 + t // 8), 1)
        for i, lamp in enumerate(((226, 70, 58), (236, 196, 84), (96, 200, 110))):
            pygame.draw.circle(surf, lamp, (body.x + 8 + i * 8, body.bottom - 9), 2)
        if not D:
            pygame.draw.rect(surf, dark, (body.x, body.bottom - 4, body.w, 4))
        pygame.draw.rect(surf, deep, body, 1, border_radius=3)


def _snow_patch(surf, r, joined, shade=(206, 222, 240), top=(246, 250, 255)):
    """A patch of snow on the lawn: white, rounded where it ends, a pale blue shade along its lower edge. joined: is there snow up, right, down, left."""
    up, right, down, left = joined
    inset = r.w // 6
    box = pygame.Rect(r.x + (0 if left else inset), r.y + (0 if up else inset), r.w - (0 if left else inset) - (0 if right else inset),
                      r.h - (0 if up else inset) - (0 if down else inset))
    rad = r.w // 3
    pygame.draw.rect(surf, shade, box.move(0, 0 if down else 3), border_top_left_radius=0 if up or left else rad, border_top_right_radius=0 if up or right else rad,
                     border_bottom_left_radius=0 if down or left else rad, border_bottom_right_radius=0 if down or right else rad)
    pygame.draw.rect(surf, top, box, border_top_left_radius=0 if up or left else rad, border_top_right_radius=0 if up or right else rad,
                     border_bottom_left_radius=0 if down or left else rad, border_bottom_right_radius=0 if down or right else rad)


def _big_tree(surf, r):
    """A big tree, two tiles by two: a broad round crown in three lights over a short trunk."""
    cx = r.centerx
    pygame.draw.ellipse(surf, LEAF_DARK, (r.x + 8, r.bottom - 18, r.w - 16, 16))  # its shadow
    pygame.draw.rect(surf, TRUNK, (cx - 7, r.centery + 10, 14, r.h // 2 - 14))
    pygame.draw.circle(surf, LEAF_DARK, (cx, r.centery - 2), r.w // 2 - 3)
    pygame.draw.circle(surf, LEAF, (cx - 3, r.centery - 7), r.w // 2 - 10)
    pygame.draw.circle(surf, LEAF_LIGHT, (cx - 11, r.centery - 16), r.w // 5)
    pygame.draw.circle(surf, LEAF, (cx + 9, r.centery + 6), r.w // 6)


def _rock(surf, r):
    body = r.inflate(-8, -10).move(0, 2)
    pygame.draw.ellipse(surf, ROCK_DARK, body)
    pygame.draw.ellipse(surf, ROCK, body.inflate(-6, -8).move(-2, -3))
    pygame.draw.ellipse(surf, (196, 188, 176), (body.x + 8, body.y + 6, 12, 7))


_THEME = None


def _stairs_in(surf, r, down):
    """A staircase inside a building: yellow steps, a red rail down one side (down: the steps darken as they go)."""
    box = r.inflate(-4, -4)
    pygame.draw.rect(surf, (120, 96, 40), box, border_radius=3)
    n = 5
    for i in range(n):
        k = (n - 1 - i) if down else i
        col = (236 - k * 14, 196 - k * 14, 84 - k * 8)
        pygame.draw.rect(surf, col, (box.x + 2 + i * (box.w - 12) // n, box.y + 2, (box.w - 12) // n - 1, box.h - 4))
    pygame.draw.rect(surf, (214, 62, 52), (box.right - 9, box.y + 1, 7, box.h - 2), border_radius=2)
    pygame.draw.rect(surf, (140, 36, 32), (box.right - 9, box.y + 1, 7, box.h - 2), 1, border_radius=2)


def _ladder(surf, r, down):
    """A ladder: down (a hole with its top rungs) or up (rungs against the wall)."""
    if down:
        pygame.draw.ellipse(surf, (30, 24, 20), r.inflate(-8, -14))
    for i in range(3):
        yy = r.y + 12 + i * 12
        pygame.draw.line(surf, (196, 150, 96), (r.x + 16, yy), (r.right - 16, yy), 4)
    pygame.draw.line(surf, (150, 110, 70), (r.x + 16, r.y + 6), (r.x + 16, r.bottom - 8), 4)
    pygame.draw.line(surf, (150, 110, 70), (r.right - 16, r.y + 6), (r.right - 16, r.bottom - 8), 4)


def _sign(surf, r):
    pygame.draw.rect(surf, SIGN_DARK, (r.centerx - 3, r.y + 26, 6, 24))
    board = pygame.Rect(r.x + 8, r.y + 8, r.w - 16, 24)
    pygame.draw.rect(surf, SIGN_DARK, board.inflate(4, 4), border_radius=4)
    pygame.draw.rect(surf, SIGN, board, border_radius=3)
    for i in range(3):
        pygame.draw.line(surf, SIGN_DARK, (board.x + 6, board.y + 7 + i * 5), (board.right - 6, board.y + 7 + i * 5), 1)


def _street(surf, art, x, y, r, c, rng):
    """A city's road (gray, a manhole now and then) or sidewalk (brick, with a curb along the road)."""
    if c == "a":
        pygame.draw.rect(surf, ROAD, r)
        if rng.random() < 0.06:
            pygame.draw.circle(surf, ROAD_DARK, r.center, r.w // 4)
            pygame.draw.circle(surf, (96, 96, 106), r.center, r.w // 4, 2)
        return
    pygame.draw.rect(surf, SIDEWALK, r)
    half = r.w // 2
    for k in (0, half):  # bricks
        pygame.draw.line(surf, SIDEWALK_LINE, (r.x, r.y + k), (r.right, r.y + k), 1)
    pygame.draw.line(surf, SIDEWALK_LINE, (r.x + (half if (y % 2) else 0), r.y), (r.x + (half if (y % 2) else 0), r.y + half), 1)
    pygame.draw.line(surf, SIDEWALK_LINE, (r.x + (0 if (y % 2) else half), r.y + half), (r.x + (0 if (y % 2) else half), r.bottom), 1)
    for (dx, dy), edge in (((0, -1), (r.x, r.y, r.w, 4)), ((0, 1), (r.x, r.bottom - 4, r.w, 4)),
                           ((-1, 0), (r.x, r.y, 4, r.h)), ((1, 0), (r.right - 4, r.y, 4, r.h))):
        if cell(art, x + dx, y + dy) == "a":  # the curb
            pygame.draw.rect(surf, CURB, edge)


RUIN = (206, 184, 138)
RUIN_DARK = (150, 126, 88)
RUIN_LIGHT = (232, 214, 172)
RUIN_PIT = (112, 96, 72)


def _ruin(surf, art, x, y, r, c):
    """A map's "theme" "ruins": what is left of old stone buildings. g: a sandstone wall, its blocks joined to the next,
    its top broken off where nothing stands behind it, and a sunken dark floor where wall is on every side (the inside of a
    roofless room); j: the stump of a column; r: a heap of fallen blocks."""
    t = r.w
    if c == "g":
        near = [cell(art, x + dx, y + dy) == "g" for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0))]
        if all(near):  # inside the walls: the old floor, in shadow
            pygame.draw.rect(surf, RUIN_PIT, r)
            pygame.draw.line(surf, (96, 82, 62), (r.x, r.y + t // 2), (r.right, r.y + t // 2), 1)
            return
        top = r.y + (0 if near[0] else (t // 5 if (x * 7 + y * 3) % 3 else t // 3))  # (a broken top edge, uneven from tile to tile)
        body = pygame.Rect(r.x, top, t, r.bottom - top)
        pygame.draw.rect(surf, RUIN, body)
        pygame.draw.rect(surf, RUIN_LIGHT, (body.x, body.y, t, max(3, t // 10)))
        for k in range(1, 3):  # courses of blocks, the joints staggered
            yy = body.y + k * body.h // 3
            pygame.draw.line(surf, RUIN_DARK, (r.x, yy), (r.right, yy), 1)
            xx = r.x + (t // 4 if k % 2 else 3 * t // 4)
            pygame.draw.line(surf, RUIN_DARK, (xx, yy - body.h // 3), (xx, yy), 1)
        if not near[1]:  # its foot, in shadow
            pygame.draw.rect(surf, RUIN_DARK, (r.x, r.bottom - max(4, t // 8), t, max(4, t // 8)))
        if not near[2]:
            pygame.draw.line(surf, RUIN_DARK, (r.x, body.y), (r.x, r.bottom), 2)
        if not near[3]:
            pygame.draw.line(surf, RUIN_DARK, (r.right - 1, body.y), (r.right - 1, r.bottom), 2)
    elif c == "j":
        pygame.draw.ellipse(surf, (120, 104, 78), (r.x + t // 6, r.bottom - t // 3, t * 2 // 3, t // 4))  # its shadow
        body = pygame.Rect(r.x + t // 4, r.y + t // 3, t // 2, t // 2)
        pygame.draw.rect(surf, RUIN, body, border_radius=4)
        pygame.draw.rect(surf, RUIN_DARK, body, 2, border_radius=4)
        pygame.draw.polygon(surf, RUIN_LIGHT, [(body.x, body.y + 3), (body.x + body.w // 3, body.y - t // 8), (body.centerx, body.y + 2), (body.right - 2, body.y - t // 12), (body.right, body.y + 4)])
        pygame.draw.line(surf, RUIN_DARK, (body.centerx - 2, body.y + 4), (body.centerx + 3, body.bottom - 4), 1)  # a crack
    else:
        pygame.draw.ellipse(surf, (120, 104, 78), (r.x + 4, r.bottom - t // 3, t - 8, t // 4))
        for k, (fx, fy, fw, fh) in enumerate(((.10, .50, .42, .34), (.46, .56, .44, .30), (.26, .30, .44, .32))):
            blk = pygame.Rect(r.x + int(fx * t), r.y + int(fy * t), int(fw * t), int(fh * t))
            pygame.draw.rect(surf, RUIN_LIGHT if k == 2 else RUIN, blk, border_radius=3)
            pygame.draw.rect(surf, RUIN_DARK, blk, 1, border_radius=3)


def _gate_wall(surf, art, x, y, r):
    """Stone gate wall: pale stone, a darker band at its foot, a pillar where it starts and every 3 tiles."""
    pygame.draw.rect(surf, (196, 198, 206), r)
    pygame.draw.rect(surf, (172, 174, 184), r, 1)
    for k in range(1, 4):
        pygame.draw.line(surf, (176, 178, 188), (r.x, r.y + k * r.h // 4), (r.right, r.y + k * r.h // 4), 1)
    if cell(art, x, y + 1) != "g":
        pygame.draw.rect(surf, (150, 120, 96), (r.x, r.bottom - 14, r.w, 14))
        pygame.draw.rect(surf, (226, 140, 60), (r.x + 4, r.bottom - 12, r.w - 8, 8), border_radius=3)
    if cell(art, x - 1, y) != "g" or cell(art, x + 1, y) != "g" or x % 3 == 0:
        pygame.draw.rect(surf, (226, 228, 234), (r.centerx - 9, r.y, 18, r.h))
        pygame.draw.rect(surf, (150, 152, 164), (r.centerx - 9, r.y, 18, r.h), 2)


def _machine(surf, art, x, y, r):
    """A console: a steel body, a screen or a row of lights on top (joined to the next one along a row)."""
    body, edge, top = (150, 160, 176), (92, 100, 116), (196, 204, 216)
    left, right = cell(art, x - 1, y) == "m", cell(art, x + 1, y) == "m"
    up, down = cell(art, x, y - 1) == "m", cell(art, x, y + 1) == "m"
    box = pygame.Rect(r.x + (0 if left else 4), r.y + (0 if up else 4), r.w - (0 if left else 4) - (0 if right else 4),
                      r.h - (0 if up else 4) - (0 if down else 2))
    pygame.draw.rect(surf, body, box)
    if not up:
        pygame.draw.rect(surf, top, (box.x, box.y, box.w, 10))
    pygame.draw.rect(surf, edge, box, 2)
    if not down:
        pygame.draw.rect(surf, edge, (box.x, box.bottom - 8, box.w, 8))
    if (x + y) % 2:
        pygame.draw.rect(surf, (40, 60, 90), (r.x + 12, r.y + 16, r.w - 24, 14), border_radius=2)
        pygame.draw.line(surf, (110, 200, 240), (r.x + 15, r.y + 22), (r.right - 15, r.y + 22), 2)
    else:
        for k, col in enumerate(((90, 220, 120), (240, 200, 70), (230, 90, 80))):
            pygame.draw.circle(surf, col, (r.x + 15 + k * 13, r.y + 24), 4)


def _railing(surf, art, x, y, r):
    """Blue iron railing: arches along a row, a post line down a column (yellow indoors: the Power Plant's)."""
    blue, dark = ((236, 206, 64), (170, 140, 30)) if _THEME in ("tunnel", "ship") else ((52, 84, 168), (30, 48, 104))
    if cell(art, x - 1, y) == "i" or cell(art, x + 1, y) == "i" or cell(art, x, y - 1) != "i":
        for k in (0, r.w // 2):
            arch = pygame.Rect(r.x + k + 2, r.y + r.h // 2 - 6, r.w // 2 - 4, 20)
            pygame.draw.arc(surf, dark, arch.move(0, 2), 0, 3.15, 5)
            pygame.draw.arc(surf, blue, arch, 0, 3.15, 5)
        pygame.draw.line(surf, dark, (r.x, r.y + r.h // 2 + 12), (r.right, r.y + r.h // 2 + 12), 3)
    else:  # (down a column: a line of posts)
        pygame.draw.rect(surf, dark, (r.centerx - 4, r.y, 8, r.h))
        pygame.draw.rect(surf, blue, (r.centerx - 3, r.y, 5, r.h))


def _lamp(surf, r):
    pygame.draw.ellipse(surf, GROUND_DARK, (r.centerx - 10, r.bottom - 10, 20, 8))
    pygame.draw.rect(surf, (70, 80, 90), (r.centerx - 3, r.y + 14, 6, r.h - 18))
    pygame.draw.rect(surf, (60, 150, 150), (r.centerx - 9, r.y + 2, 18, 14), border_radius=4)
    pygame.draw.rect(surf, (250, 240, 170), (r.centerx - 5, r.y + 6, 10, 7), border_radius=2)


def _fence(surf, art, x, y, r, ch="#", wood=None, dark=None):
    wood, dark = wood or FENCE, dark or FENCE_DARK
    left, right = cell(art, x - 1, y) == ch, cell(art, x + 1, y) == ch
    up, down = cell(art, x, y - 1) == ch, cell(art, x, y + 1) == ch
    if left or right or not (up or down):  # a row of rails
        x0 = r.x if left else r.centerx
        x1 = r.right if right else r.centerx
        for yy in (r.y + 18, r.y + 32):
            pygame.draw.rect(surf, wood, (min(x0, x1), yy, max(6, abs(x1 - x0)), 5))
    if up or down:
        y0 = r.y if up else r.centery
        y1 = r.bottom if down else r.centery
        pygame.draw.rect(surf, wood, (r.centerx - 3, y0, 6, max(6, y1 - y0)))
    pygame.draw.rect(surf, dark, (r.centerx - 5, r.y + 10, 10, 34), border_radius=3)
    pygame.draw.rect(surf, wood, (r.centerx - 3, r.y + 12, 6, 30), border_radius=2)


def _treehouse(surf, art, rect, tile, gym=False):
    """A Fortree tree house: a plank cabin on stilts with a ladder, under the tree's wide crown (the Gym: a hollow stump, a feather over its door)."""
    box = pygame.Rect(rect.x * tile, rect.y * tile, rect.w * tile, rect.h * tile)
    pygame.draw.ellipse(surf, (40, 90, 56), (box.x, box.bottom - 12, box.w, 18))  # its shadow
    cabin_h = int(tile * 1.5)
    cabin = pygame.Rect(box.x + tile // 4, box.bottom - cabin_h - tile // 3, box.w - tile // 2, cabin_h)
    for sx in (cabin.x + 4, cabin.right - 10):  # stilts
        pygame.draw.rect(surf, (104, 70, 44), (sx, cabin.bottom - 4, 6, tile // 3 + 4))
    wood, dark = ((168, 112, 64), (112, 72, 44)) if not gym else ((150, 104, 70), (96, 64, 44))
    pygame.draw.rect(surf, wood, cabin, border_radius=4)
    for yy in range(cabin.y + 8, cabin.bottom - 2, 9):
        pygame.draw.line(surf, dark, (cabin.x + 3, yy), (cabin.right - 3, yy), 2)
    pygame.draw.rect(surf, dark, cabin, 2, border_radius=4)
    pygame.draw.rect(surf, (196, 150, 96), (cabin.x - 4, cabin.bottom - 6, cabin.w + 8, 6))  # the deck
    for (dx, dy), _k in doors_in(art, rect):
        d = pygame.Rect(dx * tile + tile // 2 - 11, cabin.bottom - 34, 22, 30)
        pygame.draw.rect(surf, (60, 40, 30), d, border_radius=8)
        lx = d.centerx
        for off in ((-8, 8) if gym else ()):  # (the Gym's own steps down to the ground)
            pygame.draw.line(surf, (128, 88, 52), (lx + off, cabin.bottom - 4), (lx + off, box.bottom), 3)
        for yy in (range(cabin.bottom, box.bottom, 7) if gym else ()):
            pygame.draw.line(surf, (196, 150, 96), (lx - 8, yy), (lx + 8, yy), 2)
        if gym:  # a feather over the door
            pygame.draw.ellipse(surf, (250, 250, 250), (d.centerx - 5, d.y - 16, 10, 16))
            pygame.draw.line(surf, (120, 160, 220), (d.centerx, d.y - 16), (d.centerx, d.y), 2)
    if not gym and cell(art, rect.x + 1, rect.bottom) == "n":  # its ladder, where the map has one at its foot
        lx = box.x + tile * 3 // 2
        for off in (-8, 8):
            pygame.draw.line(surf, (128, 88, 52), (lx + off, cabin.bottom - 4), (lx + off, box.bottom + tile * 3 // 4), 3)
        for yy in range(cabin.bottom, box.bottom + tile * 3 // 4, 7):
            pygame.draw.line(surf, (196, 150, 96), (lx - 8, yy), (lx + 8, yy), 2)
    crown = pygame.Rect(box.x - tile // 4, box.y, box.w + tile // 2, box.h - cabin_h - tile // 6)  # the crown over it all
    pygame.draw.ellipse(surf, (34, 104, 58), crown.inflate(0, 10).move(0, 6))
    pygame.draw.ellipse(surf, (52, 136, 72), crown)
    for k in range(5):
        cx = crown.x + (k + 0.5) * crown.w / 5
        pygame.draw.circle(surf, (78, 164, 88), (int(cx), crown.y + crown.h // 3 + (k % 2) * 6), max(8, crown.h // 4))
    pygame.draw.ellipse(surf, (28, 84, 48), crown, 3)


def _contest_hall(surf, art, rect, tile):
    """A Hoenn Contest Hall as it stands outside (Ruby, Sapphire and Emerald): a wide pale-blue roof with cut corners
    and rows of studs, a red front hung with white pennants, blue double doors under a ribbon."""
    box = pygame.Rect(rect.x * tile, rect.y * tile, rect.w * tile, rect.h * tile)
    wall_h = int(tile * 1.35)
    walls = pygame.Rect(box.x + tile // 5, box.bottom - wall_h, box.w - tile * 2 // 5, wall_h)
    pygame.draw.ellipse(surf, (60, 110, 70), (box.x, box.bottom - 10, box.w, 16))  # its shadow
    pygame.draw.rect(surf, (216, 80, 72), walls)
    for k in (0.42, 0.62, 0.82):
        pygame.draw.line(surf, (176, 56, 56), (walls.x, walls.y + int(walls.h * k)), (walls.right, walls.y + int(walls.h * k)), 2)
    pygame.draw.rect(surf, (120, 40, 44), walls, 2)
    top = pygame.Rect(box.x, box.y + 2, box.w, box.h - wall_h + 4)
    c = tile // 3  # (the cut corners)
    shape = [(top.x + c, top.y), (top.right - c, top.y), (top.right, top.y + c), (top.right, top.bottom - c),
             (top.right - c // 2, top.bottom), (top.x + c // 2, top.bottom), (top.x, top.bottom - c), (top.x, top.y + c)]
    pygame.draw.polygon(surf, (176, 192, 224), shape)
    pygame.draw.polygon(surf, (104, 120, 160), shape, 3)
    pygame.draw.rect(surf, (136, 152, 192), (top.x + 3, top.bottom - tile // 4, top.w - 6, tile // 4 - 2))
    step = max(8, tile // 3)
    for yy in range(top.y + step, top.bottom - tile // 4 - 2, step):
        for xx in range(top.x + step, top.right - step // 2, step):
            pygame.draw.circle(surf, (120, 136, 176), (xx, yy), 2)
            pygame.draw.circle(surf, (224, 232, 248), (xx - 1, yy - 1), 1)
    door_xs = [x for (x, y), _k in doors_in(art, rect)]
    for tx in range(rect.x, rect.right):  # the pennants along the front
        if tx in door_xs:
            continue
        for k in range(2):
            px = tx * tile + tile // 4 + k * tile // 2
            pygame.draw.polygon(surf, (248, 248, 248), [(px - 5, walls.y + 5), (px + 5, walls.y + 5), (px, walls.y + 14)])
    for (dx, dy), _k in doors_in(art, rect):
        d = pygame.Rect(dx * tile + tile // 2 - 15, box.bottom - 36, 30, 34)
        pygame.draw.rect(surf, (88, 160, 224), d, border_radius=3)
        pygame.draw.rect(surf, (40, 72, 136), d, 2, border_radius=3)
        pygame.draw.line(surf, (40, 72, 136), (d.centerx, d.y), (d.centerx, d.bottom), 2)
        pygame.draw.circle(surf, (248, 248, 248), (d.centerx, d.y + 12), 6)          # the ribbon on the doors
        pygame.draw.circle(surf, (232, 80, 120), (d.centerx, d.y + 12), 3)
        pygame.draw.polygon(surf, (248, 248, 248), [(d.centerx - 4, d.y + 16), (d.centerx - 7, d.y + 25), (d.centerx - 1, d.y + 20)])
        pygame.draw.polygon(surf, (248, 248, 248), [(d.centerx + 4, d.y + 16), (d.centerx + 7, d.y + 25), (d.centerx + 1, d.y + 20)])
        pygame.draw.rect(surf, (190, 70, 60), (d.x - 4, d.bottom - 2, d.w + 8, 4))  # the mat


def _building(surf, art, rect, kind, tile, roof_colour=None):
    if kind == "timber":
        return _timber(surf, rect, tile)
    if kind == "well":
        return _well(surf, rect, tile)
    if kind == "cave":
        return _cave(surf, art, rect, tile)
    if kind in ("rocket", "gantry"):
        return _rocket(surf, rect, tile, kind == "gantry")
    if kind.startswith("cabin") or kind == "captain":  # a ship's cabin: its wall and door, no roof
        box = pygame.Rect(rect.x * tile, rect.y * tile, rect.w * tile, rect.h * tile)
        pygame.draw.rect(surf, (236, 236, 240), box)
        pygame.draw.rect(surf, (150, 160, 190), (box.x, box.bottom - 10, box.w, 10))
        for (dx, dy), _k in doors_in(art, rect):
            d = pygame.Rect(dx * tile + tile // 2 - 14, box.bottom - 46, 28, 44)
            pygame.draw.rect(surf, (110, 76, 52) if kind != "captain" else (60, 70, 120), d, border_radius=4)
            pygame.draw.rect(surf, (60, 40, 26), d, 2, border_radius=4)
            pygame.draw.circle(surf, (230, 200, 90), (d.right - 7, d.centery), 2)
        return
    if kind == "contest":
        return _contest_hall(surf, art, rect, tile)
    if kind == "treehouse" or roof_colour == "tree":  # (a roof of "tree": any building in a tree, Fortree's Gym)
        return _treehouse(surf, art, rect, tile, kind != "treehouse")
    look = roof_colour if isinstance(roof_colour, dict) else {}  # (a roof given as {"roof", "wall", "design"}: the building's own walls and shape too: Sinnoh)
    if look:
        roof_colour = look.get("roof")
    roof, shade, wall = ROOFS.get(kind, ROOFS["house"])
    if roof_colour:
        roof, shade = tuple(roof_colour), theme_shade(roof_colour, 0.74)
    if look.get("wall"):
        wall = tuple(look["wall"])
    box = pygame.Rect(rect.x * tile, rect.y * tile, rect.w * tile, rect.h * tile)
    if look.get("design") in ("block", "tower"):
        return _city_block(surf, art, rect, kind, tile, roof, shade, wall, look["design"] == "tower")
    if look.get("design") == "slab":  # more of the roof of the building in front of it (ground a tall building hides)
        pygame.draw.rect(surf, shade, box.inflate(-2, -2), border_radius=4)
        pygame.draw.rect(surf, roof, box.inflate(-8, -8), border_radius=3)
        return
    if kind == "bikes":  # bicycles parked in a rack, one to a tile (outside the Bike Shop)
        for j in range(rect.h):
            for i in range(rect.w):
                b = pygame.Rect((rect.x + i) * tile, (rect.y + j) * tile, tile, tile)
                pygame.draw.line(surf, (96, 100, 112), (b.x + 6, b.bottom - 8), (b.right - 6, b.bottom - 8), 3)       # the rack's bar
                rw = tile // 5
                for cx in (b.x + tile // 3, b.right - tile // 3):                                                   # two wheels
                    pygame.draw.circle(surf, (40, 40, 48), (cx, b.centery + 6), rw, 3)
                    pygame.draw.circle(surf, (200, 204, 212), (cx, b.centery + 6), 2)
                pygame.draw.lines(surf, (214, 70, 60), False, [(b.x + tile // 3, b.centery + 6), (b.centerx, b.centery - 6),
                                                                 (b.right - tile // 3, b.centery + 6)], 4)            # its red frame
                pygame.draw.line(surf, (214, 70, 60), (b.centerx, b.centery - 6), (b.centerx - 6, b.centery + 6), 3)
                pygame.draw.line(surf, (60, 60, 70), (b.centerx - 5, b.centery - 12), (b.centerx + 7, b.centery - 12), 3)   # saddle
                pygame.draw.line(surf, (60, 60, 70), (b.right - tile // 3 - 2, b.centery - 8), (b.right - tile // 3 + 6, b.centery - 14), 3)   # handlebar
        return
    if kind == "hedge":  # a clipped hedge: one long rounded bank of leaves, lighter on top
        box = pygame.Rect(rect.x * tile, rect.y * tile, rect.w * tile, rect.h * tile).inflate(-4, -tile // 3)
        pygame.draw.rect(surf, (40, 110, 50), box.move(0, 5), border_radius=tile // 3)
        pygame.draw.rect(surf, (112, 206, 84), box, border_radius=tile // 3)
        pygame.draw.rect(surf, (168, 236, 120), (box.x + 6, box.y + 4, box.w - 12, max(4, box.h // 4)), border_radius=tile // 6)
        pygame.draw.rect(surf, (48, 124, 56), box, 2, border_radius=tile // 3)
        return
    if kind == "fountain":  # a round stone basin, water in it and a jet in the middle
        pygame.draw.ellipse(surf, (60, 110, 70), box.move(0, 5))
        pygame.draw.ellipse(surf, (176, 180, 190), box)
        pygame.draw.ellipse(surf, (116, 120, 134), box, 3)
        pygame.draw.ellipse(surf, SEA, box.inflate(-14, -14))
        pygame.draw.ellipse(surf, (206, 232, 250), box.inflate(-box.w * 2 // 3, -box.h * 2 // 3))
        pygame.draw.circle(surf, (250, 252, 255), box.center, 5)
        return
    if kind == "heap":  # a mound of coal and broken rock (Oreburgh's mine yard)
        pygame.draw.ellipse(surf, (70, 60, 56), box.move(0, 4))
        pygame.draw.ellipse(surf, tuple(roof_colour) if roof_colour else (112, 103, 88), box)
        pygame.draw.ellipse(surf, (58, 50, 46), box, 3)
        rng = random.Random(f"heap{rect.x},{rect.y}")
        for _ in range(max(4, rect.w * rect.h * 2)):
            px = rng.randint(box.x + box.w // 5, box.right - box.w // 5); py = rng.randint(box.y + box.h // 5, box.bottom - box.h // 4)
            pygame.draw.circle(surf, rng.choice([(48, 44, 46), (86, 78, 70), (140, 130, 116)]), (px, py), rng.randint(3, 6))
        return
    if kind == "rig":  # mine machinery: a steel frame, girders crossed, a dark hopper on top
        pygame.draw.rect(surf, (60, 110, 70), (box.x, box.bottom - 8, box.w, 12))
        pygame.draw.rect(surf, (86, 96, 108), box.inflate(-6, -6))
        pygame.draw.rect(surf, tuple(roof_colour) if roof_colour else (79, 104, 95), box.inflate(-6, -6).clip(pygame.Rect(box.x, box.y, box.w, box.h // 3 + 4)))
        pygame.draw.rect(surf, (40, 46, 56), box.inflate(-6, -6), 3)
        for gx in range(box.x + 3, box.right - 3 - tile + 1, tile):
            pygame.draw.line(surf, (150, 160, 172), (gx, box.y + box.h // 3 + 4), (gx + tile, box.bottom - 6), 3)
            pygame.draw.line(surf, (150, 160, 172), (gx + tile, box.y + box.h // 3 + 4), (gx, box.bottom - 6), 3)
        return
    wall_h = int(tile * (1.25 if rect.h <= 3 else 1.6))
    walls = pygame.Rect(box.x + 4, box.bottom - wall_h, box.w - 8, wall_h)
    pygame.draw.ellipse(surf, (60, 110, 70), (box.x, box.bottom - 10, box.w, 16))  # its shadow
    pygame.draw.rect(surf, wall, walls)
    pygame.draw.rect(surf, (150, 136, 116), walls, 2)
    # the roof: eaves over the walls, stripes, a ridge
    top = pygame.Rect(box.x, box.y + 4, box.w, box.h - wall_h + 6)
    pygame.draw.rect(surf, shade, top, border_radius=8)
    pygame.draw.rect(surf, roof, top.inflate(-6, -8).move(0, -2), border_radius=6)
    for yy in range(top.y + 10, top.bottom - 6, 9):
        pygame.draw.line(surf, shade, (top.x + 6, yy), (top.right - 6, yy), 2)
    pygame.draw.rect(surf, theme_shade(roof, 1.18), (top.x + 6, top.y + 4, top.w - 12, 5), border_radius=3)
    # windows, and the door(s)
    door_xs = [x for (x, y), _k in doors_in(art, rect)]
    for tx in range(rect.x, rect.right):
        if tx in door_xs:
            continue
        wr = pygame.Rect(tx * tile + tile // 2 - 11, walls.y + 10, 22, 16)
        pygame.draw.rect(surf, (90, 160, 220), wr)
        pygame.draw.rect(surf, (70, 70, 90), wr, 2)
        pygame.draw.line(surf, (200, 230, 250), (wr.x + 4, wr.y + 4), (wr.x + 9, wr.y + 4), 2)
    for (dx, dy), _k in doors_in(art, rect):
        d = pygame.Rect(dx * tile + tile // 2 - 12, box.bottom - 34, 24, 32)
        pygame.draw.rect(surf, (96, 64, 40), d, border_radius=4)
        pygame.draw.rect(surf, (60, 40, 26), d, 2, border_radius=4)
        pygame.draw.circle(surf, (230, 200, 90), (d.right - 7, d.centery), 2)
        pygame.draw.rect(surf, (190, 70, 60), (d.x - 4, d.bottom - 2, d.w + 8, 4))  # the mat
    if kind == "center":  # a Poke Ball over the door
        cx, cy = box.centerx, top.centery
        pygame.draw.circle(surf, (250, 250, 250), (cx, cy), 13)
        pygame.draw.circle(surf, (220, 50, 50), (cx, cy), 13, draw_top_left=True, draw_top_right=True)
        pygame.draw.circle(surf, (40, 40, 40), (cx, cy), 13, 2)
        pygame.draw.line(surf, (40, 40, 40), (cx - 13, cy), (cx + 13, cy), 2)
        pygame.draw.circle(surf, (250, 250, 250), (cx, cy), 4)
        pygame.draw.circle(surf, (40, 40, 40), (cx, cy), 4, 2)
    elif kind == "mart":  # a striped sign
        s = pygame.Rect(0, 0, min(box.w - 20, 70), 18)
        s.center = (box.centerx, top.centery)
        pygame.draw.rect(surf, (250, 250, 250), s, border_radius=4)
        for i in range(0, s.w, 10):
            pygame.draw.rect(surf, (72, 122, 214), (s.x + i, s.y + 4, 5, 10))
        pygame.draw.rect(surf, (40, 60, 110), s, 2, border_radius=4)
    elif kind == "gym":  # a gold badge plaque
        cx, cy = box.centerx, top.centery
        pygame.draw.circle(surf, (250, 250, 250), (cx, cy), 13)
        pygame.draw.circle(surf, (236, 190, 60), (cx, cy), 9)
        pygame.draw.circle(surf, (120, 84, 20), (cx, cy), 13, 2)
        pygame.draw.polygon(surf, (250, 250, 250), [(cx, cy - 6), (cx + 5, cy + 4), (cx - 5, cy + 4)])


def _city_block(surf, art, rect, kind, tile, roof, shade, wall, tower=False):
    """A city building seen from above the street: a flat roof with a parapet at the back, floors of windows down
    its front (Jubilife's offices and condominiums); a tower's roof is a small cap and its front taller still."""
    box = pygame.Rect(rect.x * tile, rect.y * tile, rect.w * tile, rect.h * tile)
    roof_h = max(tile // 2, int(box.h * (0.22 if tower else 0.4)))
    walls = pygame.Rect(box.x + 3, box.y + roof_h, box.w - 6, box.h - roof_h)
    pygame.draw.ellipse(surf, (60, 110, 70), (box.x, box.bottom - 10, box.w, 16))
    top = pygame.Rect(box.x + 1, box.y + 3, box.w - 2, roof_h + 4)
    pygame.draw.rect(surf, shade, top, border_radius=5)
    pygame.draw.rect(surf, roof, top.inflate(-8, -8), border_radius=3)
    pygame.draw.rect(surf, theme_shade(roof, 1.18), (top.x + 6, top.y + 5, top.w - 12, 4), border_radius=2)
    pygame.draw.rect(surf, wall, walls)
    pygame.draw.rect(surf, theme_shade(wall, 0.72), walls, 2)
    door_cells = {(x, y) for (x, y), _k in doors_in(art, rect)}
    floors = max(1, (walls.h - 8) // 26)
    for f in range(floors):
        wy = walls.y + 7 + f * 26
        if wy + 16 > walls.bottom - 4:
            break
        last = wy + 42 > walls.bottom
        for tx in range(rect.x, rect.right):
            if last and any(dx == tx for dx, _dy in door_cells):
                continue
            wr = pygame.Rect(tx * tile + tile // 2 - 11, wy, 22, 14)
            pygame.draw.rect(surf, (96, 168, 226), wr)
            pygame.draw.rect(surf, (60, 66, 88), wr, 2)
            pygame.draw.line(surf, (206, 232, 250), (wr.x + 4, wr.y + 4), (wr.x + 9, wr.y + 4), 2)
        pygame.draw.line(surf, theme_shade(wall, 0.84), (walls.x + 2, wy + 20), (walls.right - 3, wy + 20), 1)
    for dx, dy in door_cells:
        d = pygame.Rect(dx * tile + tile // 2 - 12, box.bottom - 34, 24, 32)
        pygame.draw.rect(surf, (70, 96, 130), d, border_radius=3)
        pygame.draw.rect(surf, (36, 48, 70), d, 2, border_radius=3)
        pygame.draw.line(surf, (36, 48, 70), (d.centerx, d.y + 2), (d.centerx, d.bottom - 2), 2)
        pygame.draw.rect(surf, (120, 124, 136), (d.x - 4, d.bottom - 2, d.w + 8, 4))
    if kind == "gym":
        cx, cy = box.centerx, top.centery
        pygame.draw.circle(surf, (250, 250, 250), (cx, cy), 12)
        pygame.draw.circle(surf, (236, 190, 60), (cx, cy), 8)
        pygame.draw.circle(surf, (120, 84, 20), (cx, cy), 12, 2)


def _cave(surf, art, rect, tile):
    """A cave's way in: a rock mound with a dark mouth (its door)."""
    box = pygame.Rect(rect.x * tile, rect.y * tile, rect.w * tile, rect.h * tile)
    pygame.draw.rect(surf, ROOFS["cave"][1], box, border_radius=22)
    pygame.draw.rect(surf, ROOFS["cave"][0], box.inflate(-8, -10).move(0, -3), border_radius=18)
    for i in range(4):
        pygame.draw.line(surf, ROOFS["cave"][1], (box.x + 14 + i * 22, box.y + 18), (box.x + 24 + i * 22, box.y + 30), 3)
    for (dx, dy), _k in doors_in(art, rect):
        mouth = pygame.Rect(dx * tile + 4, box.bottom - 44, tile - 8, 44)
        pygame.draw.ellipse(surf, (24, 18, 14), mouth)
        pygame.draw.rect(surf, (24, 18, 14), (mouth.x, mouth.centery, mouth.w, mouth.h // 2))


def doors_in(art, rect):
    return [((x, y), k) for (x, y), k in doors(art).items() if rect.collidepoint(x, y)]


def theme_shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def _well(surf, rect, tile):
    """Our own simple-shape stone well and wooden supports; no source tiles/sprites."""
    b = pygame.Rect(rect.x * tile, rect.y * tile, rect.w * tile, rect.h * tile)
    cx = b.centerx
    body = pygame.Rect(cx - tile * 3 // 4, b.y + tile, tile * 3 // 2, tile * 3 // 2)
    pygame.draw.ellipse(surf, (72, 104, 80), (b.x + 4, b.bottom - 16, b.w - 8, 16))
    pygame.draw.rect(surf, (120, 128, 136), body, border_radius=10)
    pygame.draw.rect(surf, (64, 72, 80), body, 3, border_radius=10)
    rim = pygame.Rect(body.x - 5, body.y - tile // 3, body.w + 10, tile * 2 // 3)
    pygame.draw.ellipse(surf, (168, 176, 176), rim)
    pygame.draw.ellipse(surf, (40, 64, 80), rim.inflate(-14, -12))
    for px in (b.x + tile // 3, b.right - tile // 3):
        pygame.draw.rect(surf, (120, 88, 48), (px - 4, b.y + tile // 4, 8, b.h - tile // 2))
        for py in range(b.y + tile // 2, b.bottom - 8, max(4, tile // 3)):
            pygame.draw.line(surf, (200, 160, 96), (px - 7, py), (px + 7, py), 3)
    for py in range(b.bottom - tile, b.bottom - 4, max(4, tile // 5)):
        pygame.draw.line(surf, (184, 144, 88), (cx - tile // 5, py), (cx + tile // 5, py), 3)


def _timber(surf, rect, tile):
    """Own-style cut timber: a cylinder and end rings, not a source sprite."""
    for y in range(rect.y, rect.bottom):
        for x in range(rect.x, rect.right):
            b = pygame.Rect(x * tile + 4, y * tile + tile // 4, tile - 8, tile // 2)
            pygame.draw.rect(surf, (128, 88, 48), b, border_radius=6)
            pygame.draw.line(surf, (88, 56, 32), (b.x, b.bottom - 4), (b.right, b.bottom - 4), 3)
            end = pygame.Rect(b.x, b.y, max(6, b.w // 3), b.h)
            pygame.draw.ellipse(surf, (208, 168, 104), end)
            pygame.draw.ellipse(surf, (144, 104, 56), end.inflate(-6, -6), 2)


def bridge(surf, r, c):
    """One tile of a log bridge (| north-south, ; east-west) drawn into r: its shadow, its logs laid across, a rail along each side."""
    along, tile = BRIDGES[c], r.w
    body, dark, light, rail = BRIDGE_LOOKS.get(BRIDGE_LOOK, BRIDGE_LOOKS[None])
    wide = BRIDGE_LOOK is not None  # (a map's own bridge fills its tile: decks side by side make one wide road)
    deck = r if wide else (r.inflate(0, -8) if along[0] else r.inflate(-8, 0))
    if not wide:
        pygame.draw.rect(surf, (60, 40, 40), deck.move(3, 4))  # (its shadow on the floor below)
    pygame.draw.rect(surf, body, deck)
    step = max(6, tile // 6)
    for i in range(0, tile, step):  # the logs (planks, plates), side by side
        if along[0]:
            pygame.draw.line(surf, dark, (r.x + i, deck.y), (r.x + i, deck.bottom - 1), 2)
            pygame.draw.line(surf, light, (r.x + i + 3, deck.y + 2), (r.x + i + 3, deck.bottom - 3), 1)
        else:
            pygame.draw.line(surf, dark, (deck.x, r.y + i), (deck.right - 1, r.y + i), 2)
            pygame.draw.line(surf, light, (deck.x + 2, r.y + i + 3), (deck.right - 3, r.y + i + 3), 1)
    if wide:
        return
    if along[0]:
        pygame.draw.rect(surf, rail, (r.x, deck.y, tile, 3))
        pygame.draw.rect(surf, rail, (r.x, deck.bottom - 3, tile, 3))
    else:
        pygame.draw.rect(surf, rail, (deck.x, r.y, 3, tile))
        pygame.draw.rect(surf, rail, (deck.right - 3, r.y, 3, tile))


def blocker(surf, r, look):
    """Someone standing in your way till the story moves on (a map's "barred" with a look): a Psyduck holding its head,
    a Team Galactic grunt, a guard, anyone."""
    cx, by = r.centerx, r.bottom - 3
    pygame.draw.ellipse(surf, (40, 60, 50), (cx - 11, by - 5, 22, 8))
    if look == "psyduck":
        pygame.draw.ellipse(surf, (246, 208, 72), (cx - 10, by - 22, 20, 20))
        pygame.draw.ellipse(surf, (246, 208, 72), (cx - 9, by - 32, 18, 16))
        pygame.draw.ellipse(surf, (236, 224, 170), (cx - 6, by - 24, 12, 6))
        pygame.draw.circle(surf, (30, 30, 30), (cx - 4, by - 27), 2)
        pygame.draw.circle(surf, (30, 30, 30), (cx + 4, by - 27), 2)
        for dx in (-3, 0, 3):
            pygame.draw.line(surf, (40, 40, 40), (cx + dx, by - 33), (cx + dx, by - 37), 2)
        pygame.draw.line(surf, (246, 208, 72), (cx - 10, by - 18), (cx - 7, by - 29), 4)
        pygame.draw.line(surf, (246, 208, 72), (cx + 10, by - 18), (cx + 7, by - 29), 4)
        return
    body, trim, hair = {"grunt": ((226, 228, 236), (60, 70, 90), (70, 190, 190)), "guard": ((70, 96, 168), (36, 48, 96), (60, 44, 36))}.get(
        look, ((196, 112, 84), (110, 60, 44), (70, 50, 36)))
    pygame.draw.rect(surf, trim, (cx - 6, by - 9, 5, 9))
    pygame.draw.rect(surf, trim, (cx + 1, by - 9, 5, 9))
    pygame.draw.rect(surf, body, (cx - 8, by - 23, 16, 15), border_radius=4)
    pygame.draw.rect(surf, trim, (cx - 8, by - 23, 16, 15), 2, border_radius=4)
    pygame.draw.circle(surf, (246, 214, 180), (cx, by - 29), 7)
    pygame.draw.circle(surf, hair, (cx, by - 32), 7, draw_top_left=True, draw_top_right=True)
    pygame.draw.circle(surf, (30, 30, 30), (cx - 3, by - 29), 1)
    pygame.draw.circle(surf, (30, 30, 30), (cx + 3, by - 29), 1)
    if look == "grunt":
        pygame.draw.line(surf, (40, 40, 40), (cx - 4, by - 17), (cx + 4, by - 17), 2)


def _rocket(surf, rect, tile, gantry=False):
    """Mossdeep's launch pad: a white rocket standing on its fins, or one of the red lattice towers beside it."""
    box = pygame.Rect(rect.x * tile, rect.y * tile, rect.w * tile, rect.h * tile)
    if gantry:  # a red tower: two legs, cross-braces all the way up, a cabin on top
        red, dark, pale = (214, 70, 60), (140, 40, 40), (240, 150, 120)
        legs = box.inflate(-box.w // 5, 0)
        pygame.draw.rect(surf, (70, 76, 100), legs.inflate(-8, -6))
        step = max(12, tile // 2)
        for yy in range(legs.y + tile // 2, legs.bottom - 4, step):
            pygame.draw.line(surf, red, (legs.x + 3, yy), (legs.right - 3, min(legs.bottom, yy + step)), 4)
            pygame.draw.line(surf, red, (legs.right - 3, yy), (legs.x + 3, min(legs.bottom, yy + step)), 4)
            pygame.draw.line(surf, dark, (legs.x, yy), (legs.right, yy), 2)
        for lx in (legs.x, legs.right - 6):
            pygame.draw.rect(surf, red, (lx, legs.y, 6, legs.h))
            pygame.draw.rect(surf, dark, (lx, legs.y, 6, legs.h), 1)
        cab = pygame.Rect(legs.x - 3, legs.y, legs.w + 6, tile // 2)
        pygame.draw.rect(surf, pale, cab, border_radius=3)
        pygame.draw.rect(surf, dark, cab, 2, border_radius=3)
        pygame.draw.rect(surf, (60, 70, 96), cab.inflate(-14, -12))
        return
    cx = box.centerx
    w = max(tile * 2 // 3, box.w * 2 // 5)
    white, shade, line = (244, 244, 248), (196, 200, 216), (120, 124, 150)
    body = pygame.Rect(cx - w // 2, box.y + box.h // 4, w, box.h * 3 // 4 - tile // 3)
    pygame.draw.ellipse(surf, (70, 110, 80), (cx - w, box.bottom - tile // 3, w * 2, tile // 3))  # its shadow on the pad
    for side in (-1, 1):  # the fins it stands on
        fin = [(cx + side * w // 2, body.bottom - tile), (cx + side * w, box.bottom - 4), (cx + side * w // 2, box.bottom - 4)]
        pygame.draw.polygon(surf, shade, fin)
        pygame.draw.polygon(surf, line, fin, 2)
    pygame.draw.rect(surf, white, body)
    pygame.draw.rect(surf, shade, (body.right - w // 3, body.y, w // 3, body.h))
    nose = [(body.x, body.y), (cx - 3, box.y + tile // 3), (cx, box.y), (cx + 3, box.y + tile // 3), (body.right - 1, body.y)]
    pygame.draw.polygon(surf, white, nose)
    pygame.draw.polygon(surf, line, nose, 2)
    pygame.draw.rect(surf, line, body, 2)
    for k in (3, 6):  # its pale blue bands
        band = pygame.Rect(body.x, body.y + body.h * k // 8, body.w, max(5, tile // 8))
        pygame.draw.rect(surf, (150, 178, 236), band)
        pygame.draw.rect(surf, line, band, 1)
    pygame.draw.rect(surf, (70, 80, 110), (cx - 4, body.y + body.h // 5, 8, tile // 3), border_radius=2)
    pygame.draw.polygon(surf, (96, 100, 120), [(body.x + 4, body.bottom), (body.right - 4, body.bottom), (body.right + 2, box.bottom - 2), (body.x - 2, box.bottom - 2)])
