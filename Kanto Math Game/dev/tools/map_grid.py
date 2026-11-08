"""Measure a source map picture tile by tile, for laying out one of our maps exactly (Jordan, 11-07).

    python dev/tools/map_grid.py PICTURE OUT_DIR [--tile 16] [--phase X,Y] [--zoom 2] [--sample NAME=I,J ...]

Writes into OUT_DIR:
  grid_full.png     the picture with its tile grid drawn on (every 4th line bold), at 1x: the whole layout
  grid_q<k>.png     zoomed crops of it (2x), with "i,j" tile labels every 4 tiles: read positions from these
  mask.txt          one character a tile: for each --sample NAME=I,J, the tiles whose colour matches that
                    sample tile's are marked with NAME's first letter ("." elsewhere): e.g. road=11,30
  info.txt          the picture's size, the tile size and grid phase used, the map size in tiles

The tile is the source's own (16 px for FireRed/LeafGreen and HeartGold/SoulSilver pictures at 1x); the
phase (where the first grid line falls) is found from the picture's edges unless given. Tile (i, j) covers
pixels x = PHASE_X - TILE + TILE * i ... , y likewise: so tile 0 may be partly off the picture.
See dev/builders/town_maps/MAPPING_GUIDE.md for the whole method."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402


def find_phase(img, tile):
    """(x, y) of the strongest grid lines: where colour changes most, column by column (and row by row)."""
    w, h = img.get_size()
    lum = lambda c: c[0] + c[1] + c[2]
    cols, rows = [0] * tile, [0] * tile
    for x in range(1, w):
        for y in range(0, h, 3):
            cols[x % tile] += abs(lum(img.get_at((x, y))) - lum(img.get_at((x - 1, y))))
    for y in range(1, h):
        for x in range(0, w, 3):
            rows[y % tile] += abs(lum(img.get_at((x, y))) - lum(img.get_at((x, y - 1))))
    return max(range(tile), key=lambda k: cols[k]), max(range(tile), key=lambda k: rows[k])


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    opts = {}
    samples = {}
    it = iter(argv)
    for a in it:
        if a == "--sample":
            name, at = next(it).split("=")
            samples[name] = tuple(int(v) for v in at.split(","))
        elif a.startswith("--"):
            opts[a[2:]] = next(it)
    args = [a for a in args if "=" not in a]
    if len(args) < 2:
        sys.exit(__doc__)
    src, out = args[0], args[1]
    os.makedirs(out, exist_ok=True)
    pygame.init()
    pygame.display.set_mode((1, 1))
    img = pygame.image.load(src).convert()
    tile = int(opts.get("tile", 16))
    zoom = int(opts.get("zoom", 2))
    px, py = (tuple(int(v) for v in opts["phase"].split(",")) if "phase" in opts else find_phase(img, tile))
    ox, oy = px - tile, py - tile
    w, h = img.get_size()
    cols, rows = (w - ox + tile - 1) // tile, (h - oy + tile - 1) // tile

    def tile_px(i, j):
        for y in range(oy + tile * j + 2, oy + tile * j + tile - 2):
            for x in range(ox + tile * i + 2, ox + tile * i + tile - 2):
                if 0 <= x < w and 0 <= y < h:
                    yield img.get_at((x, y))[:3]

    def mean(i, j):
        ps = list(tile_px(i, j))
        return tuple(sum(p[k] for p in ps) // max(1, len(ps)) for k in range(3))

    # the grid, at 1x and zoomed
    font = pygame.font.SysFont("arial", 12, bold=True)
    for name, z in (("full", 1), ("zoom", zoom)):
        big = pygame.transform.scale(img, (w * z, h * z)) if z > 1 else img.copy()
        for i in range(cols + 1):
            x = (ox + tile * i) * z
            pygame.draw.line(big, (255, 0, 0) if i % 4 == 0 else (255, 140, 140), (x, 0), (x, h * z), 2 if i % 4 == 0 else 1)
        for j in range(rows + 1):
            y = (oy + tile * j) * z
            pygame.draw.line(big, (255, 0, 0) if j % 4 == 0 else (255, 140, 140), (0, y), (w * z, y), 2 if j % 4 == 0 else 1)
        if name == "full":
            pygame.image.save(big, os.path.join(out, "grid_full.png"))
            continue
        for i in range(0, cols, 4):
            for j in range(0, rows, 4):
                t = font.render(f"{i},{j}", True, (255, 255, 0), (0, 0, 0))
                big.blit(t, ((ox + tile * i) * z + 2, (oy + tile * j) * z + 2))
        cw, ch = 760, 860  # (crops a viewer can read at full size)
        k = 0
        for cy in sorted({0, max(0, h * z - ch)} | set(range(0, max(1, h * z - ch), ch))):
            for cx in sorted({0, max(0, w * z - cw)} | set(range(0, max(1, w * z - cw), cw))):
                r = pygame.Rect(cx, cy, min(cw, w * z - cx), min(ch, h * z - cy))
                pygame.image.save(big.subsurface(r), os.path.join(out, f"grid_q{k}.png"))
                k += 1
    # the colour mask
    lines = []
    if samples:
        refs = {n: mean(*at) for n, at in samples.items()}
        for j in range(rows):
            row = ""
            for i in range(cols):
                ps = list(tile_px(i, j))
                best = "."
                for n, ref in refs.items():
                    hit = sum(1 for p in ps if sum(abs(a - b) for a, b in zip(p, ref)) < 60) / max(1, len(ps))
                    if hit > 0.5:
                        best = n[0]
                        break
                row += best
            lines.append(f"{j:3d} {row}")
        with open(os.path.join(out, "mask.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    with open(os.path.join(out, "info.txt"), "w", encoding="utf-8") as f:
        f.write(f"picture {w} x {h}\ntile {tile}\nphase {px},{py} (grid origin {ox},{oy})\n"
                f"map {cols} x {rows} tiles\nsamples {samples}\n")
    print(f"{cols} x {rows} tiles (tile {tile}, phase {px},{py}) -> {out}")


if __name__ == "__main__":
    main(sys.argv[1:])
