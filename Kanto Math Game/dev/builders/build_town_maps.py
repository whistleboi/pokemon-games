"""Custom walkable maps (Jordan, 11-06): towns and routes drawn in our own route-map style, laid out after
the Pokemon Journeys V18 maps (used only as a guide: they're hand-built and Jordan confirmed each layout).
Wide open, no fog, no ledges (a ledge is a fence with gaps).

Each map is a grid of characters (ART below); src/dungeon/art.py draws it and says what you can walk on:
  T tree   r rock   ~ sea   # fence          (in the way)
  . ground  = sand path  s beach  " tall grass  f flowers   (walkable; wild Pokemon live in the tall grass)
  a capital letter: a building (each its own rectangle), D its door
  < > ^ v  a way out (EXITS says where to)   N someone standing (PEOPLE: which town option, in order)
BUILDINGS: a building letter's kind (center, mart, lab, home: yours, house: locked, gate, or a town option's
"door" name). Writes assets/town_maps.json.
    python dev/builders/build_town_maps.py
    python dev/builders/build_town_maps.py --only=sinnoh        (one region alone, or several: --only=kanto,sevii)
--only checks and rebuilds just those regions' maps and keeps every other region's as it was last written, so a map
someone else is in the middle of changing can't stop your build. A map deleted from a region's file stays in the JSON
until a full build.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))  # (the game folder: src.dungeon.art, for whose door is whose)

# One file a region (dev/builders/town_maps/<region>.py), in story order.
REGIONS = ["kanto", "johto", "hoenn", "sinnoh", "sevii", "orre"]


ONLY = next((a.split("=", 1)[1].split(",") for a in sys.argv[1:] if a.startswith("--only=")), None)
CHECKED = None  # (with --only: the keys of the maps being rebuilt; the rest are kept as last written)


def all_maps():
    import importlib
    global CHECKED
    out = {}
    if ONLY:
        assert all(r in REGIONS for r in ONLY), f"--only: one of {REGIONS}"
        with open(os.path.join("assets", "town_maps.json"), encoding="utf-8") as f:
            out = json.load(f)
        CHECKED = set()
    for region in ONLY or REGIONS:
        maps = importlib.import_module(f"town_maps.{region}").MAPS
        out.update(maps)
        if ONLY:
            CHECKED |= set(maps)
    return out


MAPS = all_maps()


def check(key, m):
    art = m["art"]
    w = len(art[0])
    bad = [(i, len(r)) for i, r in enumerate(art) if len(r) != w]
    assert not bad, f"{key}: rows not {w} wide: {bad}"
    for ch in set("".join(art)) - set("Tr~#.=s\"f<>^vNDw!lkc+-Xoqbuapihmgjeyzdtx%&$/n*_(),@[]{}:|;0123456789?'"):  # (? a crate: Orre's S.S. Libra; ' round stones: the Jagged Pass)
        from src.dungeon import art as _a
        cells = [(x, y) for y, r in enumerate(art) for x, c in enumerate(r) if c == ch or
                 (c == "D" and (_a.door_owner(art, x, y) == ch or (_a.door_owner(art, x, y) is None and 0 <= y - 1 and art[y - 1][x] == ch)))]
        xs = [x for x, _y in cells]
        ys = [y for _x, y in cells]
        box = [(x, y) for y in range(min(ys), max(ys) + 1) for x in range(min(xs), max(xs) + 1)]
        assert all(art[y][x] in (ch, "D") for x, y in box), f"{key}: building {ch} isn't a rectangle"
        assert ch in m.get("buildings", {}), f"{key}: building {ch} has no kind"
    assert sum(r.count("N") for r in art) == len(m.get("people", [])), f"{key}: N count vs people"
    assert sum(r.count("!") for r in art) == len(m.get("signs", [])), f"{key}: sign count vs signs"
    assert sum(r.count("X") for r in art) == len(m.get("trainer_spots", [])), f"{key}: X count vs trainer_spots"


OPEN = set('.=s"f<>^vNw+-Xobuapedx%$/n,[]{}:|;1345689')  # (o: the sea you Surf; b: a boulder, pushed aside with Strength)


def reachable(key, m):
    """Every way out, door, sign and person can be got to from the first way out (nothing walled off)."""
    if m.get("dive") is not None or m.get("surface") is not None:  # (a sea and its seabed: Dive joins them anywhere, pools ringed by rocks and all)
        return
    art = m["art"]
    h, w = len(art), len(art[0])
    cells = lambda ch: [(x, y) for y in range(h) for x in range(w) if art[y][x] in ch]
    exits = [t for t in cells("".join(c for c in m.get("exits", {}) if not c.isupper()) + "+-1")]
    lead = {c for c in m.get("exits", {}) if c.isupper()}
    lead_doors = [(x, y) for x, y in cells("D") if any(art[y + b][x + a] in lead for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= y + b < h and 0 <= x + a < w)]
    if not exits or m.get("parts"):  # (every way out a building's door: Ilex Forest's two gates; or a map in parts, one reached only by a cave mouth: Ever Grande's League side) start from those doors too
        exits = exits + lead_doors
    if not exits:  # (the only way out a parked motorbike, kind "cycle": Orre's towns, left by riding)
        bikes = {k for k, v in m.get("buildings", {}).items() if v == "cycle"}
        exits = [(x, y) for x, y in cells("D") if any(art[y + b][x + a] in bikes for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= y + b < h and 0 <= x + a < w)]
    assert exits, f"{key}: no way out"
    starts = exits if m.get("parts") else exits[:1]  # (a floor in separate parts, each reached by its own ladder)
    starts = starts + [(x, y - 1) for x, y in map(tuple, m.get("back_doors", []))]  # (a yard reached only through a house's back door: Fuchsia's pond)
    seen, todo = set(starts), list(starts)
    while todo:
        x, y = todo.pop()
        pad = (m.get("links") or {}).get(f"{x},{y}")  # (a warp pad on this same map: on to its far pad)
        if pad and (pad[1], pad[2]) not in seen and not m.get("floors"):
            seen.add((pad[1], pad[2]))
            todo.append((pad[1], pad[2]))
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            far = (m.get("links") or {}).get(f"{n[0]},{n[1]}") if 0 <= n[0] < w and 0 <= n[1] < h and art[n[1]][n[0]] == "D" and not m.get("floors") else None
            if far and (far[1], far[2]) not in seen:  # (a gatehouse walked through: in by this door, out by its other one)
                seen.add((far[1], far[2]))
                todo.append((far[1], far[2]))
            room = (m.get("inside") or {}).get(f"{n[0]},{n[1]}") if 0 <= n[0] < w and 0 <= n[1] < h and art[n[1]][n[0]] == "D" else None
            for d, r in ((m.get("inside") or {}).items() if room else ()):  # (a building with a room and several doors: in by one, out by any other. Kanto's gatehouses)
                t = tuple(int(v) for v in d.split(","))
                if r == room and t not in seen:
                    seen.add(t)
                    todo.append(t)
            if 0 <= n[0] < w and 0 <= n[1] < h and n not in seen and (art[n[1]][n[0]] in OPEN or art[n[1]][n[0]] in "_()$027?'"):  # (a ledge: crossed one way, near enough here; a waterfall: climbed with Waterfall; a crate: pushed aside)
                seen.add(n)
                todo.append(n)
    near = lambda t: any((t[0] + dx, t[1] + dy) in seen for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    cut = [("exit", t) for t in exits if t not in seen and not near(t)]
    # (in a room, someone behind a counter is talked to across it)
    over = lambda t: m.get("theme") == "room" and any(0 <= t[1] + dy < h and 0 <= t[0] + dx < w and art[t[1] + dy][t[0] + dx] == "m"
                                                      and (t[0] + 2 * dx, t[1] + 2 * dy) in seen for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    at = lambda x, y: art[y][x] if 0 <= y < h and 0 <= x < w else "c"
    over2 = lambda t: m.get("theme") == "room" and any(at(t[0] + dx, t[1] + dy) == "m" and at(t[0] + 2 * dx, t[1] + 2 * dy) == "m" and (t[0] + 3 * dx, t[1] + 3 * dy) in seen
                                                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))  # (a counter two tiles deep)
    cut += [(what, t) for what, ch in (("door", "D"), ("sign", "!"), ("person", "N")) for t in cells(ch) if not near(t) and not (ch == "N" and (over(t) or over2(t)))]
    assert not cut, f"{key}: out of reach {cut[:6]}"


def preview(key, m):
    """dev/builders/out/maps/<key>.png: the map as the game draws it, at half size (for a look)."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame
    sys.path.insert(0, os.getcwd())
    from src.dungeon import art
    if not pygame.display.get_init():
        pygame.display.init()
        pygame.display.set_mode((1, 1))
    surf = art.surface(m["art"], m.get("buildings", {}), 56, m.get("roofs"), m.get("theme"))
    art.draw_overheads(surf, m, 56)
    surf = pygame.transform.smoothscale(surf, (surf.get_width() // 2, surf.get_height() // 2))
    out = os.path.join("dev", "builders", "out", "maps")
    os.makedirs(out, exist_ok=True)
    pygame.image.save(surf, os.path.join(out, f"{key}.png"))


def main():
    for key, m in MAPS.items():
        if CHECKED is not None and key not in CHECKED:
            continue
        parts = [(f"{key}_{i + 1}", dict(m, floors=None, **f)) for i, f in enumerate(m["floors"])] if m.get("floors")             else [(key, m)]
        parts += [(f"{key}__{r}", room) for r, room in (m.get("rooms") or {}).items()]  # (the rooms inside a town's buildings: each a map of its own)
        for d, r in (m.get("inside") or {}).items():
            x, y = (int(v) for v in d.split(","))
            assert m["art"][y][x] == "D" and r in m["rooms"], f"{key}: inside {d} -> {r}: no door there, or no such room"
        for name, part in parts:  # (a map of floors: each floor its own)
            check(name, part)
            reachable(name, part)
            preview(name, part)
            print(f"  {name}: {len(part['art'][0])} x {len(part['art'])}")
    with open(os.path.join("assets", "town_maps.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(MAPS, f, ensure_ascii=False, indent=1)
        f.write("\n")


if __name__ == "__main__":
    main()
