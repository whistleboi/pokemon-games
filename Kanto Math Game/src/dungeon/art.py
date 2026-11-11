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
A map's "theme" "cave" (or a turbine's t: in the way) draws the ground as a cave floor and c as its rock walls; "ice" the same, icy."""
import random

import pygame

BLOCK = set("Tr~#!lkcqihmgjyztx&$/*_()")
LEDGES = {"_": (0, 1), "(": (-1, 0), ")": (1, 0)}  # a ledge, and the one way you hop over it
CLIFF = (200, 160, 116)
CLIFF_DARK = (150, 112, 78)
CLIFF_LIGHT = (222, 188, 146)
OPEN = set('.=s"f<>^vNw+-Xouaped%n,')
EXIT_CHARS = set("<>^vwu+-n")  # (n: a fifth way out, a cave mouth: Mt. Silver 1F's)
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
                for k, r in out.items():
                    if r.left <= x < r.right and r.top <= y <= r.bottom:
                        out[k] = r.union(pygame.Rect(x, y, 1, 1))
    return out


def doors(art):
    """{(x, y): building letter} for every D."""
    rects = buildings(art)
    found = {}
    for y, row in enumerate(art):
        for x, c in enumerate(row):
            if c == "D":
                found[(x, y)] = next((k for k, r in rects.items() if r.collidepoint(x, y)), None)
    return found


def walkable(art, x, y):
    return cell(art, x, y) in OPEN


def signs(art):
    """The signs' tiles, in reading order (the map's "signs" lines go to them in this order)."""
    return [(x, y) for y, row in enumerate(art) for x, c in enumerate(row) if c == "!"]


def surface(art, kinds, tile, roofs=None, theme=None):
    """The whole map drawn, tile px a tile (roofs: {building letter: roof colour}, the map's own; theme
    "cave": a cave's floor and walls)."""
    global _THEME
    _THEME = theme
    h, w = len(art), len(art[0])
    surf = pygame.Surface((w * tile, h * tile))
    rng = random.Random(f"{w}x{h}:{''.join(art[0])}")
    # the ground first, everywhere (under the trees and buildings too)
    for y in range(h):
        for x in range(w):
            _ground(surf, art, x, y, tile, rng)
    for y in range(h):
        for x in range(w):
            c = art[y][x]
            r = pygame.Rect(x * tile, y * tile, tile, tile)
            if c == "#":
                _fence(surf, art, x, y, r)
            elif c == "k":
                _fence(surf, art, x, y, r, "k", PICKET, PICKET_DARK)
            elif c == "r" and _THEME != "tower":
                _rock(surf, r)
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
            elif c == "m":  # a machine: a console panel with its lights
                _machine(surf, art, x, y, r)
            elif c == "h":  # a fire hydrant
                pygame.draw.ellipse(surf, (90, 60, 40), (r.centerx - 10, r.bottom - 12, 20, 8))
                pygame.draw.rect(surf, (200, 56, 44), (r.centerx - 8, r.y + 18, 16, r.h - 26), border_radius=4)
                pygame.draw.rect(surf, (230, 90, 70), (r.centerx - 10, r.y + 12, 20, 9), border_radius=4)
                pygame.draw.rect(surf, (150, 40, 32), (r.centerx - 13, r.y + 26, 26, 6), border_radius=3)
            elif c == "q":  # a rock in the sea (the lanes' edges)
                _rock(surf, r)
                pygame.draw.arc(surf, FOAM, r.inflate(-4, -10).move(0, 8), 3.4, 6.0, 3)
            elif c == "x" and cell(art, x - 1, y) != "x" and cell(art, x, y - 1) != "x":  # a whirlpool (2 x 2 tiles)
                _whirlpool(surf, r)
            elif c == "!":
                _sign(surf, r)
            elif c == "l":
                _lamp(surf, r)
            elif c in "+-":
                _ladder(surf, r, c == "+")
    for k, rect in sorted(buildings(art).items(), key=lambda kv: kv[1].bottom):
        _building(surf, art, rect, kinds.get(k, "house"), tile, (roofs or {}).get(k))
    for y in range(h):  # trees last, top to bottom: a lower one stands in front
        for x in range(w):
            if art[y][x] == "T":
                _tree(surf, pygame.Rect(x * tile, y * tile, tile, tile), rng)
    for y in range(h):  # (a turbine stands taller than its tile, so it goes over the trees behind it)
        for x in range(w):
            if art[y][x] == "t":
                _turbine(surf, pygame.Rect(x * tile, y * tile, tile, tile))
    return surf


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


def _ground(surf, art, x, y, tile, rng, as_c=None):
    c = as_c or art[y][x]
    r = pygame.Rect(x * tile, y * tile, tile, tile)
    if as_c is None and c in LEDGES:  # (drawn on the ground you hop from)
        way = LEDGES[c]
        behind = cell(art, x - way[0], y - way[1])
        _ground(surf, art, x, y, tile, rng, as_c=behind if behind in '.=e"ds' else ".")
        _ledge(surf, art, x, y, r, way)
        return
    if c == ",":  # a plank walkway up among the trees: boards, a rope rail along each open side (Fortree's bridges)
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
    if c in "~wuoqx":
        pygame.draw.rect(surf, SEA, r)
        for _ in range(2):
            ax, ay = r.x + rng.randint(4, tile - 26), r.y + rng.randint(6, tile - 14)
            pygame.draw.arc(surf, SEA_DARK, (ax, ay, 22, 10), 0.3, 2.8, 2)
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):  # foam where it meets the land
            n = cell(art, x + dx, y + dy)
            if n not in "~wuoqxTr#c":
                edge = {(0, -1): (r.x, r.y, tile, 5), (0, 1): (r.x, r.bottom - 5, tile, 5),
                        (-1, 0): (r.x, r.y, 5, tile), (1, 0): (r.right - 5, r.y, 5, tile)}[(dx, dy)]
                pygame.draw.rect(surf, FOAM, edge)
        return
    if _THEME == "tower":  # the Pokemon Tower: dim purple floors, stone walls, graves (its r)
        if c == "c":
            pygame.draw.rect(surf, (70, 58, 84), r)
            if cell(art, x, y + 1) != "c":
                pygame.draw.rect(surf, (48, 40, 60), (r.x, r.bottom - 10, tile, 10))
            return
        pygame.draw.rect(surf, (128, 112, 140), r)
        pygame.draw.rect(surf, (116, 100, 128), r, 1)
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
    if _THEME == "tunnel":  # the Underground Path: concrete, painted lines, stair rails
        if c == "c":
            pygame.draw.rect(surf, (70, 72, 80), r)
            if cell(art, x, y + 1) != "c":
                pygame.draw.rect(surf, (52, 54, 60), (r.x, r.bottom - 8, tile, 8))
            return
        pygame.draw.rect(surf, (176, 176, 168), r)
        pygame.draw.rect(surf, (156, 156, 150), r, 1)
        if c in "<>^v":
            for i in range(4):
                pygame.draw.line(surf, (120, 120, 116), (r.x + 6, r.y + 8 + i * 11), (r.right - 6, r.y + 8 + i * 11), 3)
        return
    cave = _THEME in ("cave", "ice")
    ice = _THEME == "ice"  # (Seafoam Islands: pale blue ice)
    wall, wall_dark, wall_light = ((156, 196, 226), (104, 148, 190), (214, 236, 250)) if ice else         (CAVE_WALL, CAVE_WALL_DARK, CAVE_WALL_LIGHT)
    floor, floor_dark = ((206, 228, 242), (176, 206, 228)) if ice else (CAVE_FLOOR, CAVE_FLOOR_DARK)
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
    if cave and c not in "~ws=f":  # a cave's floor, under everything (its grass: rougher ground, the wild ones')
        pygame.draw.rect(surf, floor, r)
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


def overhead(o, tile):
    """What passes over your head: (image, (x px, y px)). o: {"kind": "rail", "rect": [x, y, w, h]} in tiles; you walk
    underneath it (Goldenrod's Magnet Train line over the main road). The image takes in the shadow it casts below."""
    x, y, w, h = o["rect"]
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


def _rock(surf, r):
    body = r.inflate(-8, -10).move(0, 2)
    pygame.draw.ellipse(surf, ROCK_DARK, body)
    pygame.draw.ellipse(surf, ROCK, body.inflate(-6, -8).move(-2, -3))
    pygame.draw.ellipse(surf, (196, 188, 176), (body.x + 8, body.y + 6, 12, 7))


_THEME = None


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
    roof, shade, wall = ROOFS.get(kind, ROOFS["house"])
    if roof_colour:
        roof, shade = tuple(roof_colour), theme_shade(roof_colour, 0.74)
    box = pygame.Rect(rect.x * tile, rect.y * tile, rect.w * tile, rect.h * tile)
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
