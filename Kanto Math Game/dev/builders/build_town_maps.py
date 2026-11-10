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
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# One file a region (dev/builders/town_maps/<region>.py), in story order.
REGIONS = ["kanto", "johto", "hoenn"]


def all_maps():
    import importlib
    out = {}
    for region in REGIONS:
        out.update(importlib.import_module(f"town_maps.{region}").MAPS)
    return out


MAPS = all_maps()


def check(key, m):
    art = m["art"]
    w = len(art[0])
    bad = [(i, len(r)) for i, r in enumerate(art) if len(r) != w]
    assert not bad, f"{key}: rows not {w} wide: {bad}"
    for ch in set("".join(art)) - set("Tr~#.=s\"f<>^vNDw!lkc+-Xoqbuapihmgjeyzdtx%&$/n"):
        cells = [(x, y) for y, r in enumerate(art) for x, c in enumerate(r) if c == ch or
                 (c == "D" and any(0 <= y - 1 and art[y - 1][x] == ch for _ in [0]))]
        xs = [x for x, _y in cells]
        ys = [y for _x, y in cells]
        box = [(x, y) for y in range(min(ys), max(ys) + 1) for x in range(min(xs), max(xs) + 1)]
        assert all(art[y][x] in (ch, "D") for x, y in box), f"{key}: building {ch} isn't a rectangle"
        assert ch in m.get("buildings", {}), f"{key}: building {ch} has no kind"
    assert sum(r.count("N") for r in art) == len(m.get("people", [])), f"{key}: N count vs people"
    assert sum(r.count("!") for r in art) == len(m.get("signs", [])), f"{key}: sign count vs signs"
    assert sum(r.count("X") for r in art) == len(m.get("trainer_spots", [])), f"{key}: X count vs trainer_spots"


OPEN = set('.=s"f<>^vNw+-Xobuapedx%$/n')  # (o: the sea you Surf; b: a boulder, pushed aside with Strength)


def reachable(key, m):
    """Every way out, door, sign and person can be got to from the first way out (nothing walled off)."""
    art = m["art"]
    h, w = len(art), len(art[0])
    cells = lambda ch: [(x, y) for y in range(h) for x in range(w) if art[y][x] in ch]
    exits = [t for t in cells("".join(c for c in m.get("exits", {}) if not c.isupper()) + "+-")]
    if not exits:  # (every way out a building's door: Ilex Forest's two gates) start from those doors
        lead = {c for c in m.get("exits", {}) if c.isupper()}
        exits = [(x, y) for x, y in cells("D") if any(art[y + b][x + a] in lead for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= y + b < h and 0 <= x + a < w)]
    assert exits, f"{key}: no way out"
    starts = exits if m.get("parts") else exits[:1]  # (a floor in separate parts, each reached by its own ladder)
    seen, todo = set(starts), list(starts)
    while todo:
        x, y = todo.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if 0 <= n[0] < w and 0 <= n[1] < h and n not in seen and art[n[1]][n[0]] in OPEN:
                seen.add(n)
                todo.append(n)
    near = lambda t: any((t[0] + dx, t[1] + dy) in seen for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    cut = [("exit", t) for t in exits if t not in seen and not near(t)]
    cut += [(what, t) for what, ch in (("door", "D"), ("sign", "!"), ("person", "N")) for t in cells(ch) if not near(t)]
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
        parts = [(f"{key}_{i + 1}", dict(m, floors=None, **f)) for i, f in enumerate(m["floors"])] if m.get("floors")             else [(key, m)]
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
