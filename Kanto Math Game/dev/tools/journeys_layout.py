"""A Pokemon Journeys V18 map, read tile for tile into our map characters: a first draft for one of our maps
(Jordan, 11-07: maps exact to their originals). See dev/builders/town_maps/MAPPING_GUIDE.md.

    python dev/tools/journeys_layout.py MAP_ID_OR_NAME [OUT_DIR]

From the map's own data (not its picture): what blocks (RPG Maker's passages), the tileset's terrain tags
(tall grass, water, ledges, sand), the events (doors and where they lead, signs, people, items); blocked tiles
are told apart by the rendered tile's colour (green: a tree; else rock or wall). Writes OUT_DIR/layout.txt
(the rows, with a ruler), OUT_DIR/events.txt (each event: x, y, what), OUT_DIR/map.png (the map at 1x, 32 px
a tile, with a grid every 4 tiles). Ledges come out as "#" (our fences with gaps: open the gaps by hand where
the original's path crosses them); buildings come out as "c" blocks to replace with building letters."""
import os
import struct
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "builders"))
import pygame  # noqa: E402

import rxdata  # noqa: E402
import render_journeys_backgrounds as R  # noqa: E402

GRASS_TAGS = {2, 10}      # (Essentials: Grass, TallGrass)
WATER_TAGS = {5, 6, 7}    # (DeepWater, StillWater, Water)
LEDGE_TAGS = {1}
SAND_TAGS = {3}


def table(t):
    """An RPG Maker Table: a 20-byte header, then 16-bit values."""
    raw = t.data
    return struct.unpack(f"<{(len(raw) - 20) // 2}h", raw[20:])


def read(game, mid):
    mp = rxdata.load(os.path.join(game.root, "Data", f"Map{mid:03d}.rxdata"))
    ts = game.tilesets[mp.attrs["tileset_id"]].attrs
    passages, priorities = table(ts["passages"]), table(ts["priorities"])
    tags = table(ts["terrain_tags"]) if "terrain_tags" in ts else [0] * len(passages)
    raw = mp.attrs["data"].data
    _dim, xs, ys, zs, _n = struct.unpack("<5i", raw[:20])
    vals = struct.unpack(f"<{xs * ys * zs}h", raw[20:20 + 2 * xs * ys * zs])

    def stack(x, y):
        return [vals[x + y * xs + z * xs * ys] for z in range(zs)]

    def passable(x, y):
        for t in reversed(stack(x, y)):
            if t <= 0 or t >= len(passages):
                continue
            if passages[t] & 0x0F == 0x0F:
                return False
            if priorities[t] == 0:
                return True
        return True

    def tag(x, y):
        for t in reversed(stack(x, y)):
            if 0 < t < len(tags) and tags[t]:
                return tags[t]
        return 0
    return mp, xs, ys, passable, tag


def main(argv):
    if not argv:
        sys.exit(__doc__)
    pygame.init()
    pygame.display.set_mode((1, 1))
    game = R.Journeys(R.JOURNEYS)
    key = argv[0]
    mid = int(key) if key.isdigit() else game.map_id(key)
    if mid is None:
        sys.exit(f"no Journeys map named {key!r}")
    out = argv[1] if len(argv) > 1 else os.path.join("dev", "builders", "out", "journeys", str(mid))
    os.makedirs(out, exist_ok=True)
    mp, xs, ys, passable, tag = read(game, mid)
    img = next(x for x in game.render(mid) if isinstance(x, pygame.Surface))
    T = img.get_width() // xs

    def colour(x, y):
        r = g = b = n = 0
        for py in range(y * T + 4, y * T + T - 4, 3):
            for px in range(x * T + 4, x * T + T - 4, 3):
                c = img.get_at((px, py)); r += c[0]; g += c[1]; b += c[2]; n += 1
        return r / n, g / n, b / n

    rows = []
    for y in range(ys):
        row = ""
        for x in range(xs):
            t = tag(x, y)
            if t in WATER_TAGS:
                ch = "o"
            elif t in LEDGE_TAGS:
                ch = "#"
            elif not passable(x, y):
                r, g, b = colour(x, y)
                ch = "T" if g > r + 12 and g > b + 12 else "c"
            elif t in GRASS_TAGS:
                ch = '"'
            elif t in SAND_TAGS:
                ch = "s"
            else:
                ch = "."
            row += ch
        rows.append(row)
    events = []
    for e in mp.attrs["events"].values():
        x, y = e.attrs["x"], e.attrs["y"]
        page = e.attrs["pages"][0].attrs
        g = page["graphic"].attrs
        what = rxdata.text(e.attrs.get("name", "")) or "event"
        for cmd in page["list"]:
            c = cmd.attrs
            if c["code"] == 201 and c["parameters"] and c["parameters"][0] == 0 and c["parameters"][1] in game.info:
                what = "DOOR to " + rxdata.text(game.info[c["parameters"][1]].attrs["name"]).strip()
                if 0 <= x < xs and 0 <= y < ys:
                    rows[y] = rows[y][:x] + "D" + rows[y][x + 1:]
                break
        else:
            sprite = rxdata.text(g["character_name"])
            if sprite:
                what += f" ({sprite})"
        events.append((y, x, what))
    with open(os.path.join(out, "layout.txt"), "w", encoding="utf-8") as f:
        f.write("    " + "".join(str((i // 10) % 10) for i in range(xs)) + "\n")
        f.write("    " + "".join(str(i % 10) for i in range(xs)) + "\n")
        for j, r in enumerate(rows):
            f.write(f"{j:3d} {r}\n")
    with open(os.path.join(out, "events.txt"), "w", encoding="utf-8") as f:
        for y, x, what in sorted(events):
            f.write(f"{x:3d},{y:3d}  {what}\n")
    grid = img.copy()
    for i in range(0, xs + 1, 4):
        pygame.draw.line(grid, (255, 0, 0), (i * T, 0), (i * T, ys * T), 1)
    for j in range(0, ys + 1, 4):
        pygame.draw.line(grid, (255, 0, 0), (0, j * T), (xs * T, j * T), 1)
    pygame.image.save(grid, os.path.join(out, "map.png"))
    print(f"Map{mid:03d} {rxdata.text(game.info[mid].attrs['name']).strip()}: {xs} x {ys} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
