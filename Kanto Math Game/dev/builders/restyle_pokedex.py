"""The Pokedex's pictures in the 11-21 dark look (the UI restyle after Solar Eclipse).

The Pokedex (src/states/systems/pokedex.py) is laid out on Pokemon Journeys' 512 x 384 Essentials
pictures in assets/pokedex. This recolours them into assets/pokedex/dark (same names, same layout):
the white pages and grid turn charcoal, the light bevels dark, the black frames stay; the colours
(the red / teal / green / purple bands) stay as they are. The game loads a dark copy when there is one.

    python dev/builders/restyle_pokedex.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "..", "assets", "pokedex")
OUT = os.path.join(SRC, "dark")
NAMES = [f for f in os.listdir(SRC) if f.endswith(".png") and f.startswith(("bg_", "overlay_", "icon_slider",
                                                                              "icon_searchslider", "icon_hw"))]


def dark(c):
    r, g, b, a = c
    if a == 0:
        return c
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    if max(r, g, b) - min(r, g, b) >= 40 and not (lum > 150 and max(r, g, b) - min(r, g, b) < 60):
        return c  # a colour: kept
    if lum >= 240:
        out = (46, 46, 52)       # the pages
    elif lum >= 215:
        out = (58, 58, 66)       # the grid lines, the Poke Ball watermark
    elif lum >= 185:
        out = (72, 72, 82)       # light bevels, buttons' faces
    elif lum >= 150:
        out = (26, 26, 30)       # shadows
    elif lum >= 100:
        out = (34, 34, 40)
    else:
        out = (12, 12, 16)       # the frames
    return (*out, a)


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    os.makedirs(OUT, exist_ok=True)
    for name in sorted(NAMES):
        im = pygame.image.load(os.path.join(SRC, name)).convert_alpha()
        w, h = im.get_size()
        cache = {}
        im.lock()
        for y in range(h):
            for x in range(w):
                c = tuple(im.get_at((x, y)))
                d = cache.get(c)
                if d is None:
                    d = cache[c] = dark(c)
                if d != c:
                    im.set_at((x, y), d)
        im.unlock()
        pygame.image.save(im, os.path.join(OUT, name))
        print("dark", name)


if __name__ == "__main__":
    sys.exit(main())
