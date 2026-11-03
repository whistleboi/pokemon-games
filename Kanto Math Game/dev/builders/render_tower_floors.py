"""The Pokemon Tower's floors (Jordan, 11-02): assets/backgrounds/kanto/pokemon_tower_1-4.png, one
for each of the tower's four zones (1F-4F; "zones" in pokemon_area_data.json), shown whole like the
other maps: fitted to the height above the text box, crisp, with a blurred copy filling the sides
(import_swsh_maps.whole_picture).

Saved to assets/backgrounds/kanto/routes/kanto_pokemon_tower_floor_<n>.png (the zone's picture).
    python dev/builders/render_tower_floors.py
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from import_swsh_maps import whole_picture  # noqa: E402

SRC = os.path.join("assets", "backgrounds", "kanto", "pokemon_tower_{n}.png")
OUT = os.path.join("assets", "backgrounds", "kanto", "routes", "kanto_pokemon_tower_floor_{n}.png")


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    for n in range(1, 5):
        img = pygame.image.load(SRC.format(n=n)).convert_alpha()
        pygame.image.save(whole_picture(img), OUT.format(n=n))
        print(f"  {OUT.format(n=n)}")


if __name__ == "__main__":
    main()
