"""Sort a source picture's tiles into our map characters by colour (Jordan, 11-07: maps exact to their
originals). See dev/builders/town_maps/MAPPING_GUIDE.md.

    python dev/tools/tile_classify.py PICTURE --tile 32 --origin 0,0 [--area x0,y0,x1,y1] \\
        --colour .=112,200,160 --colour '"'=55,144,47+112,200,160 --colour T=132,211,98+189,251,140 \\
        --colour ==208,192,128 [--dark #] [--out FILE]

Each --colour CHAR=R,G,B[+R,G,B...] names the exact colours of a kind of tile (sample them first: the most
common colours of a few tiles you know). A tile is the character whose colours cover most of it; one listed
with several colours (tall grass: dark blades + lawn) counts them all. --dark CH marks tiles with many pixels
redder than green (ledges, cliff edges) as CH. Tiles nothing covers well print "?": read those by eye.
--origin is where tile (0,0) starts in the picture (pixels; Journeys renders: 0,0; town pictures: the grid
phase from dev/tools/map_grid.py minus the tile). Prints the rows with a ruler, and writes them to --out.

The lesson from Viridian Forest: average colours mislead (a tree's shadow averages like tall grass); the
share of each kind's exact colours doesn't."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402


def main(argv):
    opts, colours, rest = {}, [], []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--colour":
            spec = argv[i + 1]
            ch, cols = spec[0], spec[2:]  # (CHAR=..., the char may itself be "=")
            colours.append((ch, [tuple(int(v) for v in c.split(",")) for c in cols.split("+")]))
            i += 2
        elif a.startswith("--"):
            opts[a[2:]] = argv[i + 1]
            i += 2
        else:
            rest.append(a)
            i += 1
    if not rest or not colours:
        sys.exit(__doc__)
    pygame.init()
    img = pygame.image.load(rest[0])
    w, h = img.get_size()
    T = int(opts.get("tile", 32))
    ox, oy = (int(v) for v in opts.get("origin", "0,0").split(","))
    cols, rows = (w - ox) // T, (h - oy) // T
    x0, y0, x1, y1 = (int(v) for v in opts["area"].split(",")) if "area" in opts else (0, 0, cols, rows)
    dark = opts.get("dark")
    near = lambda p, q: sum(abs(a - b) for a, b in zip(p, q)) < 30
    out = []
    for y in range(y0, y1):
        row = ""
        for x in range(x0, x1):
            ps = [img.get_at((px, py))[:3] for py in range(oy + y * T, oy + y * T + T, 2)
                  for px in range(ox + x * T, ox + x * T + T, 2) if 0 <= px < w and 0 <= py < h]
            if not ps:
                row += " "
                continue
            n = len(ps)
            if dark and sum(1 for p in ps if p[0] > p[1] + 20 and p[0] < 200) / n > 0.12:
                row += dark
                continue
            best, share = "?", 0.0
            for ch, refs in colours:
                s = sum(1 for p in ps if any(near(p, r) for r in refs)) / n
                if s > share:
                    best, share = ch, s
            row += best if share > 0.35 else "?"
        out.append(row)
    text = ["    " + "".join(str((i // 10) % 10) for i in range(x0, x1)),
            "    " + "".join(str(i % 10) for i in range(x0, x1))]
    text += [f"{y:3d} {r}" for y, r in zip(range(y0, y1), out)]
    print("\n".join(text))
    if "out" in opts:
        with open(opts["out"], "w", encoding="utf-8") as f:
            f.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
