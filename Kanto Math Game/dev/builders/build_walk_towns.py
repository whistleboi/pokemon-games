"""Walkable towns (Jordan, 11-06): each town's Pokemon Journeys V18 map as a place you walk around, like the
route maps but open (no fog, no narrow halls): the map's own picture, which tiles you can walk on (the
tileset's passages and priorities, as RPG Maker XP decides; signs, objects and fences block), its doors (the
map's transfer events, named by the room they lead to: the Pokemon Center, the Mart, the Gym, a house...) and
its edges (PBS/connections.txt: which route each side joins).

Writes assets/walk_towns/<AREA_KEY>.png (the map, 32 px a tile, without its townsfolk) and
assets/walk_towns.json: {area key: {"map": id, "w", "h", "rows": ["#" blocked, "." walkable, "D" a door],
"doors": [{"x", "y", "name"}], "edges": {"north": area key, ...}}}. src/states/overworld/walk_town.py
walks it. Kanto first (the pilot); other regions: add their area files to REGIONS_DONE.
    python dev/builders/build_walk_towns.py [AREA_KEY ...]
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
from render_journeys_backgrounds import JOURNEYS, REGIONS, SKIP, Journeys, match  # noqa: E402

REGIONS_DONE = ["pokemon_area_data.json"]  # (the pilot: Kanto)
OUT = os.path.join("assets", "walk_towns")
SIDE = {"N": "north", "S": "south", "E": "east", "W": "west"}
# Which route each side of a town leads to. Journeys' own connections.txt gets several wrong (Route 9 by
# Saffron, Vermilion and Lavender), so the sides are Kanto's, by hand.
EDGES = {
    "PALLET_TOWN": {"north": "KANTO_ROUTE_1", "south": "KANTO_ROUTE_21"},
    "VIRIDIAN_CITY": {"south": "KANTO_ROUTE_1", "west": "KANTO_ROUTE_22", "north": "KANTO_ROUTE_2"},
    "PEWTER_CITY": {"south": "KANTO_ROUTE_2", "east": "KANTO_ROUTE_3"},
    "CERULEAN_CITY": {"west": "KANTO_ROUTE_4", "north": "KANTO_ROUTE_24", "east": "KANTO_ROUTE_9", "south": "KANTO_ROUTE_5"},
    "VERMILLION_CITY": {"north": "KANTO_ROUTE_6", "east": "KANTO_ROUTE_11"},
    "LAVENDER_TOWN": {"north": "KANTO_ROUTE_10", "west": "KANTO_ROUTE_8", "south": "KANTO_ROUTE_12"},
    "CELADON_CITY": {"east": "KANTO_ROUTE_7", "west": "KANTO_ROUTE_16"},
    "SAFFRON_CITY": {"north": "KANTO_ROUTE_5", "south": "KANTO_ROUTE_6", "west": "KANTO_ROUTE_7", "east": "KANTO_ROUTE_8"},
    "FUCHSIA_CITY": {"west": "KANTO_ROUTE_18", "east": "KANTO_ROUTE_15", "south": "KANTO_ROUTE_19"},
    "CINNABAR_ISLAND": {"north": "KANTO_ROUTE_21", "east": "KANTO_ROUTE_20"},
    "INDIGO_PLATEAU": {"south": "KANTO_ROUTE_23"},
}
# A door's kind, from the name of the room it leads to (Journeys keeps many rooms on shared maps with odd
# names: those are houses).
KINDS = [("center", ("pokecenter", "poke center", "pokemon center")), ("mart", ("mart", "dept")),
         ("gym", ("gym",)), ("lab", ("lab",)), ("home", ("homes", "home")), ("game corner", ("casino",)),
         ("tower", ("pokemon tower",)), ("mansion", ("mansion",)), ("silph", ("silph",))]


# Routes walked on their real map (Jordan, 11-06: "could the real Route 1 map be placed in?"): each side's
# area. They go to assets/walk_routes.json as a route map recipe (src/states/overworld/dungeon.py).
ROUTE_EDGES = {
    "KANTO_ROUTE_1": {"south": "PALLET_TOWN", "north": "VIRIDIAN_CITY"},
}
EXIT_CHARS = {"north": "N", "south": "S", "east": "E", "west": "W"}


def door_kind(name):
    n = name.lower()
    return next((k for k, words in KINDS if any(w in n for w in words)), "house")


def openings(rows, side):
    """The walkable tiles along one edge of the map."""
    h, w = len(rows), len(rows[0])
    cells = {"north": [(x, 0) for x in range(w)], "south": [(x, h - 1) for x in range(w)],
             "west": [(0, y) for y in range(h)], "east": [(w - 1, y) for y in range(h)]}[side]
    return [c for c in cells if rows[c[1]][c[0]] == "."]


def table(t):
    raw = t.data
    return struct.unpack(f"<{(len(raw) - 20) // 2}h", raw[20:])


def connections(root):
    """{map id: {side: neighbour map id}} from PBS/connections.txt (the side-by-side lines)."""
    out = {}
    path = os.path.join(root, "PBS", "connections.txt")
    for line in open(path, encoding="utf-8-sig"):
        parts = [p.strip() for p in line.split("#")[0].split(",")]
        if len(parts) != 6 or not parts[1][:1].upper() in SIDE or not parts[4][:1].upper() in SIDE:
            continue
        try:
            a, b = int(parts[0]), int(parts[3])
        except ValueError:
            continue
        out.setdefault(a, {})[SIDE[parts[1][0].upper()]] = b
        out.setdefault(b, {})[SIDE[parts[4][0].upper()]] = a
    return out


def walk_grid(game, mid):
    """(rows, doors) of map mid: what you can walk on, and its doors [(x, y, room name)]."""
    mp = rxdata.load(os.path.join(game.root, "Data", f"Map{mid:03d}.rxdata"))
    ts = game.tilesets[mp.attrs["tileset_id"]].attrs
    passages, priorities = table(ts["passages"]), table(ts["priorities"])
    raw = mp.attrs["data"].data
    _dim, xs, ys, zs, _n = struct.unpack("<5i", raw[:20])
    vals = struct.unpack(f"<{xs * ys * zs}h", raw[20:20 + 2 * xs * ys * zs])

    def passable(x, y):  # (RPG Maker XP: the top tile first; one that blocks blocks, a ground tile lets you)
        for z in range(zs - 1, -1, -1):
            t = vals[x + y * xs + z * xs * ys]
            if t <= 0 or t >= len(passages):
                continue
            if passages[t] & 0x0F == 0x0F:
                return False
            if priorities[t] == 0:
                return True
        return True

    rows = [["." if passable(x, y) else "#" for x in range(xs)] for y in range(ys)]
    doors = []
    for e in mp.attrs["events"].values():
        x, y = e.attrs["x"], e.attrs["y"]
        page = e.attrs["pages"][0].attrs
        dest = None
        for cmd in page["list"]:
            c = cmd.attrs
            if c["code"] == 201 and c["parameters"] and c["parameters"][0] == 0:  # transfer to a set map
                dest = c["parameters"][1]
                break
        g = page["graphic"].attrs
        if dest and dest in game.info:
            name = rxdata.text(game.info[dest].attrs["name"]).strip()
            doors.append((x, y, name, dest))
            if 0 <= x < xs and 0 <= y < ys:
                rows[y][x] = "D"
        elif (rxdata.text(g["character_name"]) or g["tile_id"]) and not page.get("through") and 0 <= x < xs and 0 <= y < ys:
            rows[y][x] = "#"  # (a sign, a rock, a berry tree: it stands in the way)
    return ["".join(r) for r in rows], doors


def main(argv):
    only = {a.upper() for a in argv}
    pygame.init()
    pygame.display.set_mode((1, 1))
    game = Journeys(JOURNEYS)
    links = connections(JOURNEYS)
    out_path = os.path.join("assets", "walk_towns.json")
    data = json.load(open(out_path, encoding="utf-8")) if os.path.exists(out_path) else {}
    os.makedirs(OUT, exist_ok=True)
    for fname in REGIONS_DONE:
        regions = REGIONS[fname]
        found = game.maps_in(regions)
        prog = json.load(open(os.path.join("assets", fname), encoding="utf-8"))["STORY_PROGRESSION"]
        area_of = {}  # Journeys map id -> our area key
        for key, a in prog.items():
            mid = match(key, a, found)
            if mid is not None:
                area_of.setdefault(mid, key)
        for key, a in prog.items():
            if a.get("area_type") != "town" or key in SKIP or (only and key not in only):
                continue
            mid = match(key, a, found)
            if mid is None:
                print(f"  {key}: no Journeys map")
                continue
            img, xs, ys = game.render(mid, people=False)
            rows, doors = walk_grid(game, mid)
            edges = EDGES.get(key) or {side: area_of[n] for side, n in links.get(mid, {}).items() if n in area_of}
            pygame.image.save(img, os.path.join(OUT, f"{key}.png"))
            data[key] = {"map": mid, "w": xs, "h": ys, "rows": rows,
                         "doors": [{"x": x, "y": y, "name": n, "kind": door_kind(n), "to": area_of.get(d)}
                                   for x, y, n, d in doors],
                         "edges": edges}
            print(f"  {key}: Map{mid:03d} {xs}x{ys}, doors {[(door_kind(n), x, y) for x, y, n, _d in doors]}")
            print(f"      edges: {[(s_, t, len(openings(rows, s_))) for s_, t in edges.items()]}")
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    routes(game, only)


def routes(game, only):
    """The routes in ROUTE_EDGES: their map (tall grass ","), the ways out (a letter a side) and picture."""
    out_path = os.path.join("assets", "walk_routes.json")
    data = json.load(open(out_path, encoding="utf-8")) if os.path.exists(out_path) else {}
    os.makedirs(os.path.join("assets", "walk_routes"), exist_ok=True)
    for fname, regions in REGIONS.items():
        found = game.maps_in(regions)
        prog = json.load(open(os.path.join("assets", fname), encoding="utf-8"))["STORY_PROGRESSION"]
        for key, edges in ROUTE_EDGES.items():
            if key not in prog or (only and key not in only):
                continue
            mid = match(key, prog[key], found)
            if mid is None:
                print(f"  {key}: no Journeys map")
                continue
            img, xs, ys = game.render(mid, people=False)
            grass = game.last_map["grass"]
            rows, doors = walk_grid(game, mid)
            grid = [[("," if c == "." and grass[y][x] else c) for x, c in enumerate(r)] for y, r in enumerate(rows)]
            for x, y, _n, _d in doors:  # (an edge warp is a way out; another door isn't walked into here)
                side = "north" if y == 0 else "south" if y == ys - 1 else "west" if x == 0 else "east" if x == xs - 1 else None
                grid[y][x] = EXIT_CHARS[side] if side in edges else "#"
            for side in edges:
                flat = ["".join(r).replace(",", ".") for r in grid]
                for (x, y) in openings(flat, side):
                    grid[y][x] = EXIT_CHARS[side]
            pygame.image.save(img, os.path.join("assets", "walk_routes", f"{key}.png"))
            data[key] = {"map": mid, "w": xs, "h": ys, "rows": ["".join(r) for r in grid],
                         "legend": {EXIT_CHARS[s_]: {"exit": t} for s_, t in edges.items()}}
            n = {s_: sum(r.count(EXIT_CHARS[s_]) for r in data[key]["rows"]) for s_ in edges}
            print(f"  route {key}: Map{mid:03d} {xs}x{ys}, grass {sum(r.count(',') for r in data[key]['rows'])}, exits {n}")
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")


if __name__ == "__main__":
    main(sys.argv[1:])
