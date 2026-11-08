"""Put a source picture and our built map's preview side by side at the same scale, for checking a layout
(Jordan, 11-07: maps exact to their originals).

    python dev/tools/map_compare.py PICTURE MAP_KEY OUT.png [--tile 16] [--phase X,Y]

The preview (dev/builders/out/maps/<MAP_KEY>.png, 28 px a tile) is scaled to the picture's tile size and
lined up with its grid (the phase: where the picture's first full tile starts)."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402


def main(argv):
    opts, args, it = {}, [], iter(argv)
    for a in it:
        if a.startswith("--"):
            opts[a[2:]] = next(it)
        else:
            args.append(a)
    src, key, out = args
    tile = int(opts.get("tile", 16))
    px, py = (int(v) for v in opts.get("phase", "0,0").split(","))
    pygame.init()
    pygame.display.set_mode((1, 1))
    a = pygame.image.load(src).convert()
    b = pygame.image.load(os.path.join("dev", "builders", "out", "maps", f"{key}.png")).convert()
    b = pygame.transform.smoothscale(b, (b.get_width() * tile // 28, b.get_height() * tile // 28))
    gap = 12
    o = pygame.Surface((a.get_width() * 2 + gap, max(a.get_height(), b.get_height())))
    o.fill((0, 0, 0))
    o.blit(a, (0, 0))
    o.blit(b, (a.get_width() + gap + px - tile, py - tile))
    pygame.image.save(o, out)
    print(out)


if __name__ == "__main__":
    main(sys.argv[1:])
