"""Render a Pokemon Journeys V18 map for laying out one of our maps exactly (Jordan, 11-07). See
dev/builders/town_maps/MAPPING_GUIDE.md.

    python dev/tools/journeys_render.py "ROUTE 1" OUT_PREFIX        (a map's name, or its number)

Writes OUT_PREFIX_full.png (the map at 32 px a tile, one tile = one of our tiles), OUT_PREFIX_c<k>.png
(labelled crops, "x,y" every 4 tiles, at 0.6x: read positions from these) and prints its size. Then sort its
tiles with dev/tools/tile_classify.py and read the rest (buildings, doors, signs, people) from the crops."""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "builders"))
import pygame  # noqa: E402


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    pygame.init()
    pygame.display.set_mode((1, 1))
    import render_journeys_backgrounds as R
    import rxdata
    name, out = argv[0], argv[1]
    game = R.Journeys(R.JOURNEYS)
    mid = int(name) if name.isdigit() else game.map_id(name)
    if mid is None:
        sys.exit(f"no Journeys map named {name!r}")
    img = next(x for x in game.render(mid) if isinstance(x, pygame.Surface)).convert()
    T = 32
    xs, ys = img.get_width() // T, img.get_height() // T
    pygame.image.save(img, out + "_full.png")
    g = img.copy()
    f = pygame.font.SysFont("arial", 15, bold=True)
    for i in range(xs + 1):
        pygame.draw.line(g, (255, 0, 0) if i % 4 == 0 else (255, 150, 150), (i * T, 0), (i * T, ys * T), 2 if i % 4 == 0 else 1)
    for j in range(ys + 1):
        pygame.draw.line(g, (255, 0, 0) if j % 4 == 0 else (255, 150, 150), (0, j * T), (xs * T, j * T), 2 if j % 4 == 0 else 1)
    for i in range(0, xs, 4):
        for j in range(0, ys, 4):
            g.blit(f.render(f"{i},{j}", True, (255, 255, 0), (0, 0, 0)), (i * T + 2, j * T + 2))
    k = 0
    for y0 in range(0, ys, 26):
        for x0 in range(0, xs, 40):
            part = g.subsurface((x0 * T, y0 * T, min(40, xs - x0) * T, min(26, ys - y0) * T))
            pygame.image.save(pygame.transform.smoothscale(part, (part.get_width() * 6 // 10, part.get_height() * 6 // 10)),
                              f"{out}_c{k}.png")
            k += 1
    print(f"Map{mid:03d} {rxdata.text(game.info[mid].attrs['name']).strip()}: {xs} x {ys} tiles; {k} crops -> {out}_*")


if __name__ == "__main__":
    main(sys.argv[1:])
