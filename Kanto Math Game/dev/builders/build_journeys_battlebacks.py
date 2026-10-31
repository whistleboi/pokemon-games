"""Battle backgrounds from Pokemon Journeys V18 (Jordan, 10-30): Graphics/Battlebacks has each scene as a
sky (<name>_bg.png, 512x288) and two ground discs (<name>_base0.png yours, <name>_base1.png the foe's),
some with evening and night versions. Each is put together here, its discs where our own battle
backgrounds have theirs (the foe's right of centre, yours along the bottom left), and saved to
assets/backgrounds/battle/journeys/battle_<our type>_j<...>.png, so the game picks them with its own
backgrounds of that type. Names ending _eve / _night are used at those times of day (src/core/assets.py).

    python dev/builders/build_journeys_battlebacks.py ["<Pokemon Journeys V18 folder>"]
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

JOURNEYS = sys.argv[1] if len(sys.argv) > 1 else os.path.join("..", "..", "Pokemon Journeys V18")
SRC = os.path.join(JOURNEYS, "Graphics", "Battlebacks")
OUT = os.path.join("assets", "backgrounds", "battle", "journeys")
K = 2                     # drawn at twice the size (1024x576), crisp
FOE = (0.75, 0.626)       # the foe's disc: its centre, as a share of the picture (as in battle_field1.png)
MINE = (0.22, 0.86)       # yours: its centre across, its top down

# our battle type -> (Journeys sky, Journeys discs); one picture per entry
SCENES = {
    "field": [("field", "field")],
    "grass": [("field", "grass")],
    "forest": [("forest", "forest")],
    "cave": [("cave1", "cave1"), ("cave2", "cave2"), ("cave3", "cave3")],
    "indoor": [("indoor1", "indoor1"), ("indoor2", "indoor2"), ("indoor3", "indoor3")],
    "mountain": [("rocky", "rocky")],
    "ocean": [("water", "water")],
    "snow": [("snow", "snow")],
    "sand": [("rocky", "sand")],
    "desert": [("rocky", "sand")],
    "elite": [(f"elite{i}", f"elite{i}") for i in range(1, 9)],
    "champion": [("champion1", "champion1"), ("champion2", "champion2")],
    "distortion": [("distortion", "distortion")],
    "underwater": [("underwater", "underwater")],
    "city": [("city", "city")],
}


def load(name):
    path = os.path.join(SRC, name + ".png")
    return pygame.image.load(path).convert_alpha() if os.path.isfile(path) else None


def compose(sky, discs, time=""):
    """One background, or None if this time of day has no sky for it."""
    t = f"_{time}" if time else ""
    bg = load(f"{sky}{t}_bg") or (load(f"{sky}_bg") if not time else None)
    if bg is None:
        return None
    base0 = load(f"{discs}{t}_base0") or load(f"{discs}_base0")
    base1 = load(f"{discs}{t}_base1") or load(f"{discs}_base1")
    W, H = bg.get_width() * K, bg.get_height() * K
    out = pygame.transform.scale(bg, (W, H)).convert()
    if base1:
        b = pygame.transform.scale(base1, (base1.get_width() * K, base1.get_height() * K))
        out.blit(b, b.get_rect(center=(int(W * FOE[0]), int(H * FOE[1]))))
    if base0:
        b = pygame.transform.scale(base0, (base0.get_width() * K, base0.get_height() * K))
        ink = b.get_bounding_rect()
        out.blit(b, (int(W * MINE[0]) - ink.centerx, int(H * MINE[1]) - ink.top))
    return out


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    os.makedirs(OUT, exist_ok=True)
    made = 0
    for kind, scenes in SCENES.items():
        for i, (sky, discs) in enumerate(scenes, 1):
            n = str(i) if len(scenes) > 1 else ""
            for time in ("", "eve", "night"):
                img = compose(sky, discs, time)
                if img is None:
                    continue
                name = f"battle_{kind}_j{n}" + (f"_{time}" if time else "") + ".png"
                pygame.image.save(img, os.path.join(OUT, name))
                made += 1
    print(f"{made} battle backgrounds in {OUT}")


if __name__ == "__main__":
    main()
