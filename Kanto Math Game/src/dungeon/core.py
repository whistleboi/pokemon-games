"""The rules of a route dungeon, with no pygame (so they can be tested, and reused by a standalone game).

A Run is one walk through an area: its floors (made as you reach them), you, the wild Pokemon and
trainers on each floor, the items lying around and the way out. The game's screen asks the Run to
take a step and gets back what happened (a bump into a wild Pokemon, an item picked up, an exit...);
what a wild Pokemon or an item *is* stays the screen's business (the "payload").

Tiles: WALL (trees or rock, by the area's style), FLOOR (a path), GRASS (tall grass: walkable,
and where wild Pokemon like to sit) and WATER (a pond: not walkable; you fish in it).

Floors are kept once made: STAIRS go on to the next floor, STAIRS_UP back to the one before (the same
layout, as you left it). Figures stand still: the area's story people and Pokemon (a boss, an event).

A fixed place (recipe "fixed": a building) is the same every visit: its floors are made from a seed of its
own ("seed"), and its trainers stand in the same spots. A drawn place (recipe "layout": the Game Corner)
isn't made at all: each floor is drawn in text ('#' wall, '.' floor, ',' grass, '~' water, '@' the start;
"legend" says what its other letters are: {"exit": area}, {"figure": a figure's text}, {"decor": name}, a
wall with something on it, a slot machine). "fog": false shows the whole floor (no fog of war).

An open place (recipe "open": a Safari Zone, a Wild Area) has no stairs: the way to the next area is an
opening in the floor's east edge, and the way back one in its west edge (you come in beside it).
"""
import inspect
import random
from collections import deque

CURRENT_FLOOR = 0  # the floor being made or walked right now (a floor's own wild pool: the seabed's)
ENTRANCE_COUNT = 0  # how many tiles the way out you left by had (0: unknown): a wide edge maps place for place
ENTRANCE_SPREAD = False  # the count is of buildings, not door tiles (out of one of Route 2's two gatehouses into Viridian Forest, whose gates are three tiles wide): the same way along
ENTRANCE_INDEX = 0  # which of several ways in from the same place you came by (Route 41's four Whirl Islands caves)
WALL, FLOOR, GRASS, WATER, SURF = 0, 1, 2, 3, 4  # (SURF: open sea, crossed with HM Surf)
DIRS = ((0, -1), (1, 0), (0, 1), (-1, 0))
STAIRS = "STAIRS"
STAIRS_UP = "STAIRS_UP"

STYLES = {
    # room size (share of its cell), corridor width, how much of a room is tall grass, rooms skipped
    "field": {"room": (0.62, 0.92), "corridor": 2, "grass": 0.35, "skip": 0.0},
    "forest": {"room": (0.45, 0.75), "corridor": 1, "grass": 0.6, "skip": 0.2},
    "cave": {"room": (0.45, 0.8), "corridor": 1, "grass": 0.0, "skip": 0.25},
    # indoors: big rooms, straight halls, no grass (Silph Co., the Pokemon Tower, the S.S. Anne...)
    "building": {"room": (0.7, 0.95), "corridor": 2, "grass": 0.0, "skip": 0.0},
    # the open sea: you surf (the floor is water you can cross), rocks and islets between
    "sea": {"room": (0.7, 0.95), "corridor": 3, "grass": 0.25, "skip": 0.0},
}


class Room:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h

    @property
    def center(self):
        return self.x + self.w // 2, self.y + self.h // 2

    def contains(self, x, y):
        return self.x <= x < self.x + self.w and self.y <= y < self.y + self.h

    def tiles(self):
        return [(x, y) for y in range(self.y, self.y + self.h) for x in range(self.x, self.x + self.w)]


class Floor:
    def __init__(self, w, h, style="field"):
        self.w, self.h, self.style = w, h, style
        self.tiles = [[WALL] * w for _ in range(h)]
        self.rooms = []
        self.start = (1, 1)
        self.exits = {}      # (x, y) -> an area key, or STAIRS
        self.items = {}      # (x, y) -> item key
        self.tm_spots = {}   # (x, y) -> TM spot id (fixed spots; the TM inside is picked per save)
        self.movers = []     # wild Pokemon and trainers
        self.seen = set()    # tiles the player has seen (the mini-map and the fog)
        self.decor = {}      # (x, y) -> what stands on that wall tile (a drawn place's slot machines)
        self.spots = {}      # figure text -> (x, y): where a drawn place's figures stand
        self.ice = set()     # sheet ice: step on it and you slide till something stops you (the Ice Path)
        self.current = {}    # (x, y) -> (dx, dy): a sea current carries you that way (Routes 132-134)
        self.deep = set()    # deep sea: Dive here to the seabed floor
        self.bridge = {}     # (x, y) -> (dx, dy): a log bridge and the line it runs along (Victory Road)

    def inside(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def tile(self, x, y):
        return self.tiles[y][x] if self.inside(x, y) else WALL

    def walkable(self, x, y):
        return self.tile(x, y) not in (WALL, WATER)

    def room_at(self, x, y):
        for r in self.rooms:
            if r.contains(x, y):
                return r
        return None

    def mover_at(self, x, y):
        for m in self.movers:  # (a jumbo one, size 2: a Max Raid's Pokemon, takes up 2 x 2 tiles)
            k = getattr(m, "size", 1)
            if m.x <= x < m.x + k and m.y <= y < m.y + k:
                return m
        return None

    def occupied(self, x, y):
        return ((x, y) in self.exits or (x, y) in self.items or (x, y) in self.tm_spots
                or self.mover_at(x, y) is not None)


class Mover:
    """A wild Pokemon ("wild"), a trainer ("trainer") or a story figure ("figure": stands still) on the map."""

    def __init__(self, kind, x, y, payload=None, facing=(0, 1)):
        self.kind, self.x, self.y, self.payload, self.facing = kind, x, y, payload, facing
        self.alert = False  # a wild one that has noticed you (it chases)


# ---------------------------------------------------------------- making a floor
def _carve(floor, x, y, kind=FLOOR):
    if 0 < x < floor.w - 1 and 0 < y < floor.h - 1 and floor.tiles[y][x] == WALL:
        floor.tiles[y][x] = kind


def _corridor(floor, a, b, width, rng):
    """An L-shaped path from a to b (horizontal first or vertical first, at random)."""
    (x1, y1), (x2, y2) = a, b
    legs = [((x1, y1), (x2, y1)), ((x2, y1), (x2, y2))]
    if rng.random() < 0.5:
        legs = [((x1, y1), (x1, y2)), ((x1, y2), (x2, y2))]
    for (sx, sy), (ex, ey) in legs:
        for x in range(min(sx, ex), max(sx, ex) + 1):
            for y in range(min(sy, ey), max(sy, ey) + 1):
                for k in range(width):
                    _carve(floor, x + (k if sx == ex else 0), y + (k if sy == ey else 0))


def arena(rng, w=56, h=34, style="field"):
    """One big open floor with nothing in the way of the view (Hyperspace Lumiose, Jordan 11-06): walls only
    round the edge, patches of tall grass, a few lone pillars. Its "rooms" are its four quarters (no walls
    between them), so the start and the way on still go far apart."""
    floor = Floor(w, h, style)
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            floor.tiles[y][x] = FLOOR
    for _ in range(max(3, w * h // 220)):  # tall grass patches
        cx, cy, rx, ry = rng.randint(3, w - 4), rng.randint(3, h - 4), rng.randint(2, 4), rng.randint(1, 3)
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                if 1 <= x < w - 1 and 1 <= y < h - 1 and ((x - cx) / (rx + .5)) ** 2 + ((y - cy) / (ry + .5)) ** 2 <= 1:
                    floor.tiles[y][x] = GRASS
    for _ in range(max(2, w * h // 400)):  # lone pillars (one tile: they never cut a way off)
        x, y = rng.randint(3, w - 4), rng.randint(3, h - 4)
        if all(floor.tiles[y + dy][x + dx] != WALL for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            floor.tiles[y][x] = WALL
    hw, hh = (w - 2) // 2, (h - 2) // 2
    floor.rooms = [Room(1 + i * hw, 1 + j * hh, hw, hh) for j in range(2) for i in range(2)]
    return floor


def generate(rng, w=44, h=30, style="field", ponds=0):
    """A floor: rooms in a grid of cells, joined by paths (every room reachable). ponds: how many rooms get
    a pond (kept off the room's middle row and column, where the paths cross, so it never cuts a way)."""
    st = STYLES.get(style, STYLES["field"])
    floor = Floor(w, h, style)
    cols, rows = max(2, w // 12), max(2, h // 10)
    cw, ch = (w - 2) // cols, (h - 2) // rows
    points = {}
    for cy in range(rows):
        for cx in range(cols):
            x0, y0 = 1 + cx * cw, 1 + cy * ch
            if rng.random() < st["skip"] and len(points) > 0:
                # no room here: a single bend in the path keeps the grid connected
                points[(cx, cy)] = (x0 + rng.randint(2, cw - 3), y0 + rng.randint(2, ch - 3))
                continue
            k = rng.uniform(*st["room"])
            rw, rh = max(4, int((cw - 2) * k)), max(4, int((ch - 2) * k))
            rx = x0 + 1 + rng.randint(0, max(0, cw - 2 - rw))
            ry = y0 + 1 + rng.randint(0, max(0, ch - 2 - rh))
            room = Room(rx, ry, rw, rh)
            floor.rooms.append(room)
            for (tx, ty) in room.tiles():
                _carve(floor, tx, ty)
            points[(cx, cy)] = room.center
    # a random spanning tree over the cells, plus a few extra links (loops make chases fun)
    cells = list(points)
    start = rng.choice(cells)
    done, edges, stack = {start}, [], [start]
    while stack:
        cur = stack[-1]
        nxt = [(cur[0] + dx, cur[1] + dy) for dx, dy in DIRS if (cur[0] + dx, cur[1] + dy) in points
               and (cur[0] + dx, cur[1] + dy) not in done]
        if not nxt:
            stack.pop()
            continue
        n = rng.choice(nxt)
        edges.append((cur, n))
        done.add(n)
        stack.append(n)
    for c in cells:
        for dx, dy in ((1, 0), (0, 1)):
            n = (c[0] + dx, c[1] + dy)
            if n in points and (c, n) not in edges and (n, c) not in edges and rng.random() < 0.25:
                edges.append((c, n))
    for a, b in edges:
        _corridor(floor, points[a], points[b], st["corridor"], rng)
    # tall grass in the rooms
    for room in floor.rooms:
        for _ in range(rng.randint(1, 3) if st["grass"] else 0):
            gw = max(2, int(room.w * rng.uniform(0.3, 0.3 + st["grass"])))
            gh = max(2, int(room.h * rng.uniform(0.3, 0.3 + st["grass"])))
            gx = room.x + rng.randint(0, max(0, room.w - gw))
            gy = room.y + rng.randint(0, max(0, room.h - gh))
            for y in range(gy, gy + gh):
                for x in range(gx, gx + gw):
                    if floor.tiles[y][x] == FLOOR:
                        floor.tiles[y][x] = GRASS
    for room in rng.sample(floor.rooms, min(ponds, len(floor.rooms))):
        _pond(floor, room, rng)
    return floor


def _pond(floor, room, rng):
    """Water in one corner of a room, clear of its middle (where the paths cross) and its edge."""
    cx, cy = room.center
    xs = [x for x in range(room.x + 1, room.x + room.w - 1) if abs(x - cx) > 1]
    ys = [y for y in range(room.y + 1, room.y + room.h - 1) if abs(y - cy) > 1]
    left, top = rng.random() < 0.5, rng.random() < 0.5
    xs = [x for x in xs if (x < cx) == left]
    ys = [y for y in ys if (y < cy) == top]
    for y in ys:
        for x in xs:
            if floor.tiles[y][x] in (FLOOR, GRASS):
                floor.tiles[y][x] = WATER


def distances(floor, start):
    """Steps from start to every walkable tile."""
    dist = {start: 0}
    q = deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in DIRS:
            n = (x + dx, y + dy)
            if n not in dist and floor.walkable(*n):
                dist[n] = dist[(x, y)] + 1
                q.append(n)
    return dist


def on_foot(floor, start):
    """The tiles you can walk to from start without Surf (from out on the sea: the sea too)."""
    wet = floor.tile(*start) in (SURF, WATER)
    seen, q = {start}, deque([start])
    while q:
        x, y = q.popleft()
        for dx, dy in DIRS:
            n = (x + dx, y + dy)
            if n not in seen and floor.walkable(*n) and (wet or floor.tile(*n) not in (SURF, WATER)):
                seen.add(n)
                q.append(n)
    return seen


def path(floor, start, goal, blocked=()):
    """The steps from start to goal (start left out), or [] if there's no way. blocked: tiles to go
    around (the goal itself may be one: you walk up to it and bump it)."""
    if start == goal or not floor.walkable(*goal):
        return []
    blocked = set(blocked) - {goal}
    prev = {start: None}
    q = deque([start])
    while q:
        cur = q.popleft()
        if cur == goal:
            break
        for dx, dy in DIRS:
            n = (cur[0] + dx, cur[1] + dy)
            if n not in prev and floor.walkable(*n) and n not in blocked:
                prev[n] = cur
                q.append(n)
    if goal not in prev:
        return []
    steps, cur = [], goal
    while cur != start:
        steps.append(cur)
        cur = prev[cur]
    return steps[::-1]


def _free_tile(floor, rng, room=None, avoid=(), prefer_grass=False, far_from=None, min_dist=0):
    tiles = room.tiles() if room else [(x, y) for y in range(floor.h) for x in range(floor.w)]
    ok = [t for t in tiles if floor.walkable(*t) and not floor.occupied(*t) and t not in avoid
          and t != floor.start]
    if far_from is not None:
        ok = [t for t in ok if abs(t[0] - far_from[0]) + abs(t[1] - far_from[1]) >= min_dist]
    if prefer_grass:
        grass = [t for t in ok if floor.tile(*t) == GRASS]
        if grass and rng.random() < 0.75:
            ok = grass
    return rng.choice(ok) if ok else None


def drawn_floor(recipe, index, entrance=None, figures=()):
    """A floor drawn in text (recipe "layout": [{"map": [rows], "legend": {...}}, ...])."""
    plan = recipe["layout"][index]
    rows = plan["map"]
    legend = dict(recipe.get("legend") or {}, **(plan.get("legend") or {}))
    h, w = len(rows), max(len(r) for r in rows)
    floor = Floor(w, h, recipe.get("style", "building"))
    floor.rooms = [Room(1, 1, max(1, w - 2), max(1, h - 2))]
    exits = {}
    for y, row in enumerate(rows):
        for x, c in enumerate(row.ljust(w, "#")):
            what = legend.get(c) or {}
            floor.tiles[y][x] = {"#": WALL, ",": GRASS, "~": WATER, "o": SURF}.get(
                c, WALL if what.get("decor") else SURF if what.get("surf") else FLOOR)
            if c == "@":
                floor.start = (x, y)
            if c == "%":
                floor.ice.add((x, y))
            if what.get("current"):
                floor.current[(x, y)] = tuple(what["current"])
            if what.get("deep"):
                floor.deep.add((x, y))
            if what.get("bridge"):
                floor.bridge[(x, y)] = tuple(what["bridge"])
            if what.get("exit"):
                exits[(x, y)] = what["exit"]
            if what.get("decor"):
                floor.decor[(x, y)] = what["decor"]
            if what.get("figure"):
                floor.spots[what["figure"]] = (x, y)
    for t in map(tuple, plan.get("exit_order") or ()):  # (several mouths to one place that pair up out of reading order: these come last, in this order: Mt. Mortar's four)
        if t in exits:
            exits[t] = exits.pop(t)
    floor.exits.update(exits)
    if entrance:  # you come in beside the way you came
        doors = [t for t, target in exits.items() if target == entrance]  # (several the same way: the matching one)
        global ENTRANCE_INDEX, ENTRANCE_COUNT
        at = ENTRANCE_INDEX
        global ENTRANCE_SPREAD
        spread, ENTRANCE_SPREAD = ENTRANCE_SPREAD, False
        if (ENTRANCE_COUNT > 2 and len(doors) > 2 and ENTRANCE_COUNT != len(doors)) or (spread and ENTRANCE_COUNT > 1 and len(doors) > ENTRANCE_COUNT):
            # (two long edges of different lengths, rocks taken out of each: the same way along, not the same count in)
            at = round(ENTRANCE_INDEX * (len(doors) - 1) / (ENTRANCE_COUNT - 1))
        door = doors[min(at, len(doors) - 1)] if doors else None
        ENTRANCE_INDEX = ENTRANCE_COUNT = 0

        def inward(d):  # (a way in on the map's edge: the tile straight in from it, if you can stand there)
            step = (1, 0) if d[0] == 0 else (-1, 0) if d[0] == w - 1 else (0, 1) if d[1] == 0 else (0, -1) if d[1] == h - 1 else None
            t = (d[0] + step[0], d[1] + step[1]) if step else None
            return t if t and floor.walkable(*t) and t not in exits else None

        def beside(d):
            return next(((d[0] + dx, d[1] + dy) for dx, dy in DIRS if floor.walkable(d[0] + dx, d[1] + dy)
                         and (d[0] + dx, d[1] + dy) not in exits), None)
        if door:
            on_edge = door[0] in (0, w - 1) or door[1] in (0, h - 1)
            if on_edge and len(doors) > 1 and not inward(door):
                # (that tile of the edge has rock straight in from it: come in by the nearest tile that's open,
                # never sideways into a pocket walled off by the edge itself: Route 124 from Lilycove)
                door = min((d for d in doors if inward(d)), key=lambda d: abs(d[0] - door[0]) + abs(d[1] - door[1]), default=door)
            if not (inward(door) or beside(door)):
                door = min((d for d in doors if beside(d)), key=lambda d: abs(d[0] - door[0]) + abs(d[1] - door[1]), default=door)
            floor.start = inward(door) or beside(door) or floor.start
    if floor.start == (1, 1) and not floor.walkable(1, 1):  # (no "@": a real map's middle, on open ground)
        cx, cy = w // 2, h // 2
        floor.start = min(((x, y) for y in range(h) for x in range(w)
                           if floor.walkable(x, y) and (x, y) not in exits),
                          key=lambda t: abs(t[0] - cx) + abs(t[1] - cy), default=(1, 1))
    for payload in figures:
        spot = floor.spots.get(payload.get("text") if isinstance(payload, dict) else payload)
        if spot is None and (recipe.get("image") or recipe.get("art")):  # (the route's people: on open ground)
            name = payload.get("text") if isinstance(payload, dict) else str(payload)
            spot = _free_tile(floor, random.Random(f"{recipe.get('seed')}:{name}"), far_from=floor.start, min_dist=4)
        if spot:
            floor.movers.append(Mover("figure", spot[0], spot[1], payload))
    floor.seen = set()
    return floor


def _edge_gate(floor, side):
    """An opening in the floor's east or west edge, a path to it from the nearest room: its tile."""
    room = (max if side == "east" else min)(floor.rooms, key=lambda r: r.center[0])
    cx, cy = room.center
    xs = range(cx, floor.w) if side == "east" else range(cx, -1, -1)
    for x in xs:
        if floor.tiles[cy][x] == WALL or floor.tiles[cy][x] == WATER:
            floor.tiles[cy][x] = FLOOR
    return (floor.w - 1, cy) if side == "east" else (0, cy)


def build_floor(rng, recipe, index, entrance=None, forwards=(), last=True, figures=(), here=None):
    """One floor of an area. entrance: the area you came from (its exit is beside you). forwards: the
    other ways out (in the rooms farthest from you); a floor before the last has STAIRS there too, and
    a floor after the first STAIRS_UP beside you. here: (entrance, forwards) for this floor alone, where
    the area's ways out are on different floors (a building's floors). figures: payloads of the story
    figures standing on this floor (in the far rooms, after the ways out)."""
    w, h = recipe.get("size", (44, 30))
    style = recipe.get("style", "field")
    ponds = int(recipe.get("ponds", 0) or 0)
    floor = arena(rng, w, h, style) if recipe.get("arena") else generate(rng, w, h, style, ponds)
    for _ in range(20 if not recipe.get("arena") else 0):  # at least two rooms: a start and somewhere to head for
        if len(floor.rooms) >= 2:
            break
        floor = generate(rng, w, h, style, ponds)
    start_room = rng.choice(floor.rooms)
    floor.start = start_room.center
    dist = distances(floor, floor.start)
    if here is not None:
        entrance, forwards = here
    elif index:
        entrance = None
    open_ = bool(recipe.get("open"))
    if open_ and index > 0:  # the way back: an opening in the west edge (you come in beside it)
        gate = _edge_gate(floor, "west")
        floor.exits[gate] = STAIRS_UP
        floor.start = (gate[0] + 1, gate[1])
    beside = [STAIRS_UP] if index > 0 and not open_ else []
    if entrance:
        beside.append(entrance)
    for target in beside:
        spot = _free_tile(floor, rng, start_room, far_from=floor.start, min_dist=1)
        floor.exits[spot or floor.start] = target
    # the rooms farthest from the start hold the way on, then the figures
    rooms = sorted((r for r in floor.rooms if r is not start_room),
                   key=lambda r: -dist.get(r.center, 0)) or [start_room]
    targets = ([] if not last and here is None else list(forwards)) + ([] if last or open_ else [STAIRS])
    if open_ and not last:  # the way on: an opening in the east edge
        floor.exits[_edge_gate(floor, "east")] = STAIRS
    for i, target in enumerate(targets):
        spot = _free_tile(floor, rng, rooms[i % len(rooms)])
        if spot:
            floor.exits[spot] = target
    for j, payload in enumerate(figures):
        spot = _free_tile(floor, rng, rooms[(len(targets) + j) % len(rooms)])
        if spot is None:
            spot = _free_tile(floor, rng, far_from=floor.start, min_dist=4)
        if spot:
            floor.movers.append(Mover("figure", spot[0], spot[1], payload))
    floor.seen = set()
    return floor


# ---------------------------------------------------------------- loot and TMs
def weighted(rng, table):
    keys = [k for k, wt in table.items() if wt > 0]
    return rng.choices(keys, weights=[table[k] for k in keys])[0] if keys else None


def roll_loot(rng, loot):
    """The loose items on one floor: loot = {"per_floor": [lo, hi], "items": {item: weight}}."""
    lo, hi = (loot.get("per_floor") or [2, 4])[:2]
    table = loot.get("items") or {}
    if not table:
        return []
    return [weighted(rng, table) for _ in range(rng.randint(lo, hi))]


def pick_tm(seed, spot_id, tm_table, owned, badges):
    """The TM at a fixed spot: picked from this save's seed (so reloading can't change it), among the
    TMs not owned yet, up to one tier above the region's badges. None if every TM is owned."""
    rng = random.Random(f"{seed}:{spot_id}")
    cap = min(8, badges + 1)
    pool = sorted(k for k, d in tm_table.items() if k not in owned and d.get("tier", 8) <= cap and not d.get("gift"))
    if not pool:
        pool = sorted(k for k, d in tm_table.items() if k not in owned and not d.get("gift"))  # (story gifts: only ever given)
    return rng.choice(pool) if pool else None


# ---------------------------------------------------------------- a walk through an area
class Run:
    """You walking through one area. make_wild(rng) -> a payload for a new wild Pokemon (the
    screen's own object); trainers: [(index, payload)] still to beat; spots: TM spot ids not taken."""

    SIGHT = 6           # how far a wild Pokemon notices you
    TRAINER_SIGHT = 4   # how far a trainer looks ahead
    RESPAWN_TURNS = 12  # a new wild Pokemon wanders in this often, up to the floor's usual number
    RESPAWN_FAR = 14    # tiles: never near you (or a friend, in co-op: "others")
    others = ()

    def __init__(self, recipe, rng=None, entrance=None, forwards=(), make_wild=None, trainers=(),
                 loot_for=None, tm_spots=(), figures=(), floor_of=None, exits_by_floor=None, start_floor=0):
        """figures: [(floor, payload)] story figures; floor_of(trainer payload) -> its floor (or None: the
        trainers are spread over the floors); exits_by_floor {floor: (entrance, [forwards])} where the ways
        out are on different floors; start_floor: the floor you arrive on."""
        self.recipe = recipe
        self.rng = rng or random.Random()
        self.n_floors = max(1, int(recipe.get("floors", 1)))
        self.entrance, self.forwards = entrance, list(forwards)
        self.make_wild = make_wild or (lambda rng: None)
        try:  # make_wild(rng, spot): it's told where the Pokemon will stand (which area of a wide floor)
            self._wild_at = len(inspect.signature(self.make_wild).parameters) >= 2
        except (TypeError, ValueError):
            self._wild_at = False
        self.loot_for = loot_for or (lambda rng: [])
        self.trainers = list(trainers)
        self.tm_spots = list(tm_spots)
        self.figures = list(figures)
        self.floor_of = floor_of or (lambda payload: None)
        self.exits_by_floor = exits_by_floor
        self.floors = []
        self.index = -1
        self.turn = 0
        self.player = (0, 0)
        self.fog = recipe.get("fog", True)
        while len(self.floors) <= start_floor:  # (the floors below the one you start on are made first)
            self.enter_floor(len(self.floors))

    @property
    def floor(self):
        return self.floors[self.index]

    @staticmethod
    def _ladder(floor, kind, nth=0):
        """The nth STAIRS (or STAIRS_UP) tile of a floor in reading order (else the first): ladders pair up
        between floors in order (Jordan, 11-07: Cerulean Cave's 1F ladders each lead to their own part of 2F)."""
        tiles = sorted((t for t, target in floor.exits.items() if target == kind), key=lambda t: (t[1], t[0]))
        return (tiles[nth] if nth < len(tiles) else tiles[0]) if tiles else None

    def _nth_here(self, kind):
        """Which of this floor's STAIRS (or STAIRS_UP) you're standing on, in reading order (0 if none)."""
        tiles = sorted((t for t, target in self.floor.exits.items() if target == kind), key=lambda t: (t[1], t[0]))
        return tiles.index(self.player) if self.player in tiles else 0

    def enter_floor(self, index, arrive=None, nth=0):
        """Go to a floor: one made before is as you left it (arrive: beside its STAIRS or STAIRS_UP, the nth)."""
        global CURRENT_FLOOR
        CURRENT_FLOOR = index
        self.deck = True
        if index < len(self.floors):
            self.index = index
            floor = self.floors[index]
            spot = self._ladder(floor, arrive, nth) if arrive else None
            self.player = self._beside(floor, spot) if spot else floor.start
            self.reveal()
            return
        last = index == self.n_floors - 1
        here = None
        if self.exits_by_floor is not None:
            here = self.exits_by_floor.get(index, (None, []))
        figures = [p for i, p in self.figures if i == index]
        # a fixed place: its floors (and where its trainers stand) from its own seed, the same every visit
        fixed = random.Random(f"{self.recipe.get('seed', '')}:{index}") if self.recipe.get("fixed") else None
        if self.recipe.get("layout"):  # (the way you came in may be on any of its floors: Mt. Moon's last)
            floor = drawn_floor(self.recipe, index, self.entrance, figures)
        else:
            floor = build_floor(fixed or self.rng, self.recipe, index, self.entrance, self.forwards, last, figures, here)
        self.floors.append(floor)
        self.index = index
        self.player = floor.start
        if arrive and self.recipe.get("layout"):  # (down a ladder: beside the one back up, the nth)
            spot = self._ladder(floor, arrive, nth)
            if spot:
                self.player = floor.start = self._beside(floor, spot)
        start_room = floor.room_at(*floor.start)
        # trainers on their floor (each keeps its index in the area's trainer list), else spread over them
        spread = [t for t in self.trainers if self.floor_of(t[1]) is None]
        mine = [t for t in self.trainers if self.floor_of(t[1]) == index] + \
            [t for i, t in enumerate(spread) if i % self.n_floors == index]
        place = fixed or self.rng
        for idx, payload in mine:
            own = (floor.spots.get(f"trainer:{payload.get('spot_name')}") or floor.spots.get(f"trainer:{payload.get('name')}"))                 if isinstance(payload, dict) else None  # (spot_name first: a villain renamed for the version keeps its own spot, even with others now named alike)
            spot = own
            if not own:  # (anywhere, but somewhere you can walk to from the way in: never across water you can't cross yet)
                afoot = on_foot(floor, floor.start) if self.recipe.get("layout") else None
                for _try in range(24 if afoot else 1):
                    spot = _free_tile(floor, place, avoid=start_room.tiles() if start_room and not self.recipe.get("layout") else (),
                                      far_from=floor.start, min_dist=8 if not self.recipe.get("layout") else 3)
                    if not afoot or spot in afoot:
                        break
            if spot and own:  # (its own spot: it looks across the way, a bridge's other lane: the Nugget Bridge)
                facing = next((d for d in ((1, 0), (-1, 0)) if floor.walkable(spot[0] + d[0], spot[1] + d[1])
                               and not floor.walkable(spot[0] - d[0], spot[1] - d[1])), (0, 1))
            elif spot:
                facing = place.choice([d for d in DIRS if floor.walkable(spot[0] + d[0], spot[1] + d[1])]
                                      or [(0, 1)])
            if spot:
                floor.movers.append(Mover("trainer", spot[0], spot[1], (idx, payload), facing))
        lo, hi = (self.recipe.get("wild") or [4, 6])[:2]
        indoors = self._indoors(index)  # (a room on a route map: nothing wild, nothing lying about. The Safari Zone's rest houses)
        if indoors:
            lo = hi = 0
        for _ in range(self.rng.randint(lo, hi)):  # (a drawn map is one room: away from you is enough)
            self._spawn_wild(floor, None if self.recipe.get("layout") else start_room)
        reach = distances(floor, floor.start)  # (loot lands where you can walk to it from here: never out on the water)
        for item in ([] if indoors else self.loot_for(self.rng)):
            spot = next((s for s in (_free_tile(floor, self.rng) for _ in range(24)) if s in reach), None)
            if spot and item:
                floor.items[spot] = item
        for spot_id in [s for i, s in enumerate(self.tm_spots) if i % self.n_floors == index]:
            spot = _free_tile(floor, self.rng, far_from=floor.start, min_dist=6)
            if spot:
                floor.tm_spots[spot] = spot_id
        self.reveal()

    def _indoors(self, index):
        """A drawn floor marked "indoors": a room (a house on a route, the Safari Zone's rest houses)."""
        lay = self.recipe.get("layout") or []
        return bool(index < len(lay) and isinstance(lay[index], dict) and lay[index].get("indoors"))

    def _spawn_wild(self, floor, avoid_room=None, far=False):
        spot = _free_tile(floor, self.rng, avoid=avoid_room.tiles() if avoid_room else (), prefer_grass=True,
                          far_from=self.player if far else floor.start, min_dist=self.RESPAWN_FAR if far else 5)
        if spot is None:
            return None
        payload = self.make_wild(self.rng, spot) if self._wild_at else self.make_wild(self.rng)
        if payload is None:
            return None
        m = Mover("wild", spot[0], spot[1], payload)
        floor.movers.append(m)
        return m

    # ---- what you can see
    explore = False    # (a first visit: the map clears as you walk it; set by the map screen)
    EXPLORE_RADIUS = 7

    def reveal(self, radius=2):
        f, (px, py) = self.floor, self.player
        if self.explore:
            r = self.EXPLORE_RADIUS
            f.seen.update((x, y) for y in range(py - r, py + r + 1) for x in range(px - r, px + r + 1)
                          if f.inside(x, y) and (x - px) ** 2 + (y - py) ** 2 <= r * r + 1)
            return
        if not self.fog:  # the whole floor, at once
            if len(f.seen) < f.w * f.h:
                f.seen = {(x, y) for y in range(f.h) for x in range(f.w)}
            return
        for y in range(py - radius, py + radius + 1):
            for x in range(px - radius, px + radius + 1):
                if f.inside(x, y):
                    f.seen.add((x, y))
        room = f.room_at(px, py)
        if room:  # a room lights up whole, with its edge
            for y in range(room.y - 1, room.y + room.h + 1):
                for x in range(room.x - 1, room.x + room.w + 1):
                    if f.inside(x, y):
                        f.seen.add((x, y))

    def reveal_at(self, px, py):
        """A friend's view clears the fog too."""
        f, r = self.floor, self.EXPLORE_RADIUS
        f.seen.update((x, y) for y in range(py - r, py + r + 1) for x in range(px - r, px + r + 1)
                      if f.inside(x, y) and (x - px) ** 2 + (y - py) ** 2 <= r * r + 1)

    def visible(self, x, y):
        """Can you see this tile right now (same room, or close by; anywhere, without fog)?"""
        if self.explore:
            return (x, y) in self.floor.seen
        if not self.fog:
            return True
        px, py = self.player
        room = self.floor.room_at(px, py)
        if room and room.x - 1 <= x <= room.x + room.w and room.y - 1 <= y <= room.y + room.h:
            return True
        return abs(x - px) <= 2 and abs(y - py) <= 2

    deck = True  # on a log bridge: up on its deck (True), or passing underneath it (False)

    def made(self, index):
        """A floor, made if it wasn't yet, without going there (what lies under a Dive spot)."""
        global CURRENT_FLOOR
        at = (self.index, self.player, CURRENT_FLOOR, self.deck)
        while len(self.floors) <= index:
            self.enter_floor(len(self.floors))
        self.index, self.player, CURRENT_FLOOR, self.deck = at
        return self.floors[index]

    def jump_floor(self, index, spot):
        """Straight to a tile of another floor (Dive, and back up to the surface)."""
        global CURRENT_FLOOR
        self.made(index)
        self.index, self.player, CURRENT_FLOOR, self.deck = index, spot, index, True
        self.reveal()

    def _bridge_bars(self, here, to, dx, dy):
        """A log bridge has two levels: its deck, crossed along its length, and the floor under it, crossed
        along its width. You're on the one you stepped onto it by, and can't swap in the middle."""
        b = self.floor.bridge
        if here in b and to not in b:
            along = (abs(dx), abs(dy)) == b[here]
            return along != self.deck
        return False

    # ---- a turn
    def step(self, dx, dy):
        """You try to step (dx, dy). Returns a list of events, in order:
        ("blocked",), ("bump", mover), ("moved",), ("item", key), ("tm", spot_id), ("exit", target),
        ("stairs",), ("stairs_up",), ("ambush", mover) (a wild Pokemon reached you), ("spotted", trainer)."""
        f = self.floor
        x, y = self.player[0] + dx, self.player[1] + dy
        if not f.walkable(x, y) or self._bridge_bars(self.player, (x, y), dx, dy):
            return [("blocked",)]
        m = f.mover_at(x, y)
        if m is not None:
            return [("bump", m)]
        if (x, y) in f.bridge and self.player not in f.bridge:
            self.deck = (abs(dx), abs(dy)) == f.bridge[(x, y)]
        elif (x, y) not in f.bridge:
            self.deck = True
        self.player = (x, y)
        self.turn += 1
        self.reveal()
        events = [("moved",)]
        if (x, y) in f.items:
            events.append(("item", f.items.pop((x, y))))
        if (x, y) in f.tm_spots:
            events.append(("tm", f.tm_spots.pop((x, y))))
        if (x, y) in f.exits:
            target = f.exits[(x, y)]
            events.append(("stairs",) if target == STAIRS else ("stairs_up",) if target == STAIRS_UP
                          else ("warp", target) if str(target).startswith("WARP:") else ("exit", target))
            return events  # nothing else moves while you leave
        events += self.others_act()
        return events

    def wait(self):
        """Stay put for a turn (the others still move)."""
        self.turn += 1
        return self.others_act()

    def _beside(self, floor, spot):
        for dx, dy in DIRS:
            t = (spot[0] + dx, spot[1] + dy)
            if floor.walkable(*t) and not floor.occupied(*t):
                return t
        return floor.start

    def warp(self, index, x, y, land=False):
        """Through a passage to any floor (a map's "links": Mt. Coronet's branching rooms): beside its far end; land:
        onto that very spot, when it's plain floor (falling through a hole: Mt. Pyre's)."""
        index = max(0, min(self.n_floors - 1, index))
        while len(self.floors) <= index:  # (floors are made in order: the ones on the way too)
            self.enter_floor(len(self.floors))
        self.enter_floor(index)
        floor = self.floors[index]
        land = land and (x, y) not in floor.exits and floor.walkable(x, y) and not floor.occupied(x, y)   # (a plain spot, not a passage: a hole's landing)
        self.player = (x, y) if land else self._beside(floor, (x, y))
        self.reveal()

    def _ladders(self, index):
        """A floor's own ladder order, if its map gives one ("ladders": its STAIRS in reading order, each the
        number of the next floor's STAIRS_UP it leads to: Rock Tunnel's, whose ladders don't pair in order)."""
        floors = (self.recipe.get("art") or {}).get("floors") or []
        return floors[index].get("ladders") if 0 <= index < len(floors) else None

    def descend(self):
        """On to the next floor (STAIRS): beside its matching STAIRS_UP (the same place in reading order)."""
        nth, order = self._nth_here(STAIRS), self._ladders(self.index)
        self.enter_floor(self.index + 1, arrive=STAIRS_UP, nth=order[nth] if order and nth < len(order) else nth)

    def ascend(self):
        """Back to the floor before (STAIRS_UP): beside its matching STAIRS."""
        nth, order = self._nth_here(STAIRS_UP), self._ladders(self.index - 1)
        if order and nth in order:
            nth = order.index(nth)
        self.enter_floor(max(0, self.index - 1), arrive=STAIRS, nth=nth)

    def add_figure(self, index, payload):
        """A story figure that turns up later (a boss once its story step is done), on its floor."""
        if (index, payload) in self.figures:
            return
        self.figures.append((index, payload))
        if index < len(self.floors):
            f = self.floors[index]
            spot = f.spots.get(payload.get("text") if isinstance(payload, dict) else payload)
            if spot is None or f.occupied(*spot):
                spot = _free_tile(f, self.rng, far_from=f.start, min_dist=6) or _free_tile(f, self.rng)
            if spot:
                f.movers.append(Mover("figure", spot[0], spot[1], payload))

    def drop_figure(self, payload):
        """A figure whose story step is done (a beaten boss, a fossil taken) leaves every floor."""
        self.figures = [(i, p) for i, p in self.figures if p is not payload]
        for f in self.floors:
            f.movers = [m for m in f.movers if not (m.kind == "figure" and m.payload is payload)]

    def remove(self, mover):
        if mover in self.floor.movers:
            self.floor.movers.remove(mover)

    def others_act(self):
        f, events = self.floor, []
        px, py = self.player
        for m in list(f.movers):
            if m.kind == "figure":
                continue
            if m.kind == "trainer":
                if self._sees(m):
                    events.append(("spotted", m))
                    return events
                continue
            d = abs(m.x - px) + abs(m.y - py)
            if d == 1:  # beside you: it notices you and jumps in
                m.alert = True
            elif d <= self.SIGHT and (self.visible(m.x, m.y) or m.alert):
                m.alert = True
                blocked = {(o.x, o.y) for o in f.movers if o is not m} | set(f.exits)
                steps = path(f, (m.x, m.y), (px, py), blocked)
                if steps and steps[0] != (px, py):
                    m.x, m.y = steps[0]
            elif self.rng.random() < 0.5:
                dx, dy = self.rng.choice(DIRS)
                nx, ny = m.x + dx, m.y + dy
                if f.walkable(nx, ny) and not f.occupied(nx, ny) and (nx, ny) != (px, py):
                    m.x, m.y = nx, ny
            if m.alert and abs(m.x - px) + abs(m.y - py) == 1 and not any(e[0] == "ambush" for e in events):
                events.append(("ambush", m))
        if self.recipe.get("respawn", True) and self.turn % self.RESPAWN_TURNS == 0 and not self._indoors(self.index):  # (Hyperspace: none)
            most = (self.recipe.get("wild") or [4, 6])[-1]
            if sum(1 for m in f.movers if m.kind == "wild") < most:
                count = len(f.movers)
                self._spawn_wild(f, far=True)
                if len(f.movers) > count and any(abs(f.movers[-1].x - x) + abs(f.movers[-1].y - y) < self.RESPAWN_FAR for x, y in self.others):
                    f.movers.pop()
        return events

    def _sees(self, trainer):
        dx, dy = trainer.facing
        x, y = trainer.x, trainer.y
        for _ in range(self.TRAINER_SIGHT):
            x, y = x + dx, y + dy
            if not self.floor.walkable(x, y):
                return False
            if (x, y) == self.player:
                return True
            if self.floor.mover_at(x, y):
                return False
        return False

    def walk_toward(self, goal):
        """The next step (dx, dy) on the way to a tapped tile, or None."""
        f = self.floor
        # (around the other ways out: a walk to a far tile mustn't leave by a sign on the way)
        blocked = {(m.x, m.y) for m in f.movers} | set(f.exits)
        steps = path(f, self.player, goal, blocked)
        if not steps:
            return None
        nx, ny = steps[0]
        return nx - self.player[0], ny - self.player[1]
