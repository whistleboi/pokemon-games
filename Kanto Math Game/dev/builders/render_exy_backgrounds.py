"""Kalos route and cave backgrounds rendered from the fan game Pokemon Everlasting X and Devastating Y
(Beta v1.5; Jordan's find, 11-04: an RPG Maker XP / Essentials remake of X and Y, built from Vaniville Town
to Cyllage City), drawn the same way as the Pokemon Journeys backgrounds (render_journeys_backgrounds.py).

Its map names follow X and Y's, but the game also keeps Essentials' sample maps (its own "Route 1" to
"Route 8", Lappet Town, Cedolan City...), so each area is matched by hand (MAPS, checked by eye). Kalos's
towns keep the pictures they have. Left out: Route 1 (Vaniville Pathway; it has no map for it) and the
Parfum Palace rooms (scattered rooms on black; its grounds are used instead).

Saved to assets/backgrounds/kalos/routes/<area key>.png, which the route screen uses first.
    python dev/builders/render_exy_backgrounds.py ["<Everlasting X folder>"] [AREA_KEY ...]
"""
import json
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rxdata  # noqa: E402
from render_journeys_backgrounds import Journeys, map_path, mostly_void  # noqa: E402
from render_orre_backgrounds import whole_picture  # noqa: E402

_NAME = "(Beta v1.5) Pokemon Everlasting X Devastating Y"
EXY_GAME = os.path.join(os.path.expanduser("~"), "Downloads", _NAME, _NAME)
# our area -> the fan game's map number (Data/MapNNN.rxdata)
MAPS = {
    "KALOS_ROUTE_2": 78, "SANTALUNE_FOREST": 79, "KALOS_ROUTE_3": 80, "KALOS_ROUTE_22": 95,
    "KALOS_ROUTE_4": 96, "KALOS_ROUTE_5": 102, "KALOS_ROUTE_6": 108, "PARFUM_PALACE": 109,
    "KALOS_ROUTE_7": 32, "GLITTERING_CAVE": 111, "CONNECTING_CAVE": 113,
}
# Caves: no tall grass to frame on, so shown whole, with a blurred copy at the sides.
WHOLE = {"GLITTERING_CAVE", "CONNECTING_CAVE"}
# Routes framed by hand, (x, y) of the frame's top-left tile, drawn with their people: Route 7's grassiest
# stretch is forest, so its Day Care, crossroads and the Snorlax asleep on the bridge instead.
FOCUS = {"KALOS_ROUTE_7": (98, 17)}


def focused(game, mid, x, y):
    """The W x H stretch of a map at full size whose top-left tile is (x, y), with its people."""
    img = game.render(mid)[0]
    w, h = 1280, 540
    return game._frame(img, (x * 32 + w // 2, y * 32 + h // 2), w, h, 1.0)


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    root = args[0] if args and os.path.isdir(args[0]) else EXY_GAME
    only = {a.upper() for a in args if not os.path.isdir(a)}
    if not os.path.isdir(os.path.join(root, "Data")):
        sys.exit(f"Pokemon Everlasting X not found at {root}")
    pygame.init()
    pygame.display.set_mode((1, 1))
    game = Journeys(root)
    with open(os.path.join("assets", "kalos_area_data.json"), encoding="utf-8") as f:
        areas = json.load(f)["STORY_PROGRESSION"]
    done = skipped = 0
    for key, mid in MAPS.items():
        if only and key not in only:
            continue
        town = areas[key].get("area_type") == "town"
        out = map_path("towns" if town else "routes", key)
        if key in WHOLE:
            img = whole_picture(game, mid)
        elif key in FOCUS:
            img = focused(game, mid, *FOCUS[key])
        else:
            img = game.town_background(mid) if town else game.route_background(mid)
        if img is None or (key not in WHOLE and mostly_void(img)):
            skipped += 1
            print(f"  skipped {key}: Map{mid:03d} is mostly black")
            continue
        os.makedirs(os.path.dirname(out), exist_ok=True)
        pygame.image.save(img, out)
        done += 1
        print(f"  {out}  <- Map{mid:03d} {rxdata.text(game.info[mid].attrs['name']).strip()}")
    print(f"{done} backgrounds, {skipped} skipped")


if __name__ == "__main__":
    main(sys.argv[1:])
