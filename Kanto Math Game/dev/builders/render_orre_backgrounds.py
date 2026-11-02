"""Orre town and route backgrounds rendered from the fan game Pokemon Orre 2.1.1 (Jordan's find, 11-01:
an RPG Maker XP / Essentials project with Orre's towns and places), drawn the same way as the Pokemon
Journeys backgrounds (render_journeys_backgrounds.py), so Orre gets the same look as the other regions.

Its map names don't follow ours, so each area is matched by hand (MAPS, checked by eye). Left out:
Pyrite Cave and Under Colosseum (no map for them: its "Cave" is a legendary's room, its "Pre Gym" a
Phenac stadium lobby), and
the places it doesn't have (Cave Poke Spot, Shadow Pokemon Lab, Cipher Lab, S.S. Libra, Prestige
Precept Center, Deep Colosseum); those keep their pictures.

Saved to assets/backgrounds/orre/towns|routes/<area key>.png, which the town and route screens use first.
Also Orre's one Pokemon Center and one Mart (BUILDINGS: Phenac's), for every Orre town: the room cropped
from its black surroundings, scaled up (crisp) to fill the height above the text box, on black.
    python dev/builders/render_orre_backgrounds.py ["<Pokemon Orre folder>"] [AREA_KEY ...]
"""
import json
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rxdata  # noqa: E402
from render_journeys_backgrounds import Journeys, map_path, mostly_void  # noqa: E402

ORRE_GAME = os.path.join(os.path.expanduser("~"), "Downloads", "Pokemon_Orre_2.1.1", "Pokemon_Orre_2.1.1_reupload")
# our area -> the fan game's map number (Data/MapNNN.rxdata)
MAPS = {
    "OUTSKIRT_STAND": 32, "ORRE_DESERT": 16, "PHENAC_CITY": 42, "ORRE_POKE_SPOTS": 47, "PYRITE_TOWN": 82,
    "PYRITE_BUILDING": 101, "OASIS_POKE_SPOT": 50, "AGATE_VILLAGE": 77, "RELIC_CAVE": 112, "RELIC_FOREST": 113,
    "MT_BATTLE": 89, "THE_UNDER": 121, "GATEON_PORT": 80, "XD_ONBS": 130, "SNAGEM_HIDEOUT": 131,
    "ORRE_COLOSSEUM": 196, "XD_CIPHER_KEY_LAIR": 157, "REALGAM_TOWER": 160, "CIPHER_COMMAND": 163,
    "XD_CITADARK_ISLE": 146,
}


# Maps with black all around (indoor maps, and a few outdoor ones built that way): shown whole, cropped
# to what's drawn, at the screen's height, with a blurred, darkened copy of it filling the sides.
WHOLE = {"PYRITE_BUILDING", "RELIC_CAVE", "MT_BATTLE", "THE_UNDER", "XD_ONBS", "SNAGEM_HIDEOUT", "XD_CIPHER_KEY_LAIR",
         "CIPHER_COMMAND"}


def content(game, mid):
    """A map drawn, cropped to its non-black part."""
    img = game.render(mid)
    img = img[0] if isinstance(img, tuple) else img
    mask = pygame.mask.from_threshold(img, (0, 0, 0, 255), (12, 12, 12, 255))
    mask.invert()
    rects = mask.get_bounding_rects()
    return img.subsurface(rects[0].unionall(rects[1:]) if rects else img.get_rect())


def whole_picture(game, mid, size=(1280, 540)):
    """All of a map in the frame: fitted to its height (or width), a blurred copy behind."""
    room = content(game, mid)
    w, h = size
    k = min(w / room.get_width(), h / room.get_height())
    main = pygame.transform.smoothscale(room, (int(room.get_width() * k), int(room.get_height() * k)))
    out = pygame.Surface(size)
    blur = pygame.transform.smoothscale(room, (24, max(1, 24 * h // w)))
    out.blit(pygame.transform.smoothscale(blur, size), (0, 0))
    dark = pygame.Surface(size, pygame.SRCALPHA)
    dark.fill((0, 0, 0, 120))
    out.blit(dark, (0, 0))
    out.blit(main, main.get_rect(center=(w // 2, h // 2)))
    return out


# Orre's shared Pokemon Center and Mart (src/core/assets.py REGION_BUILDINGS): the fan game's Phenac ones
BUILDINGS = {"orre_center.png": 22, "orre_mart.png": 43}

# Places the fan game has no map for, from other pictures (Jordan's finds), shown whole the same way:
# Pyrite Cave from a fan's GBA-style Orre maps (Reddit, "Made some GBA Orre region maps as a fun art
# project"), kept in dev/builders/sources/orre.
PICTURES = {"PYRITE_CAVE": os.path.join("dev", "builders", "sources", "orre", "pyrite_cave_gba.webp")}


def render_pictures(only=()):
    """The PICTURES places, each as a whole picture with the blurred sides (no fan game needed)."""
    from import_swsh_maps import whole_picture as whole_image
    with open(os.path.join("assets", "orre_area_data.json"), encoding="utf-8") as f:
        areas = json.load(f)["STORY_PROGRESSION"]
    for key, src in PICTURES.items():
        if only and key not in only:
            continue
        img = pygame.image.load(src).convert_alpha()
        out = map_path("towns" if areas[key].get("area_type") == "town" else "routes", key)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        pygame.image.save(whole_image(img), out)
        print(f"  {out}  <- {src}")


def room_picture(game, mid):
    """An indoor map as a 1280 x 540 picture: the room (its non-black part), scaled up crisp, on black."""
    room = content(game, mid)
    k = min(1280 / room.get_width(), 540 / room.get_height())
    big = pygame.transform.scale(room, (int(room.get_width() * k), int(room.get_height() * k)))
    out = pygame.Surface((1280, 540))
    out.blit(big, big.get_rect(center=(640, 270)))
    return out


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    root = args[0] if args and os.path.isdir(args[0]) else ORRE_GAME
    only = {a.upper() for a in args if not os.path.isdir(a)}
    pygame.init()
    pygame.display.set_mode((1, 1))
    render_pictures(only)
    if only and only <= set(PICTURES):
        return
    if not os.path.isdir(os.path.join(root, "Data")):
        sys.exit(f"Pokemon Orre not found at {root}")
    game = Journeys(root)
    with open(os.path.join("assets", "orre_area_data.json"), encoding="utf-8") as f:
        areas = json.load(f)["STORY_PROGRESSION"]
    done = skipped = 0
    for key, mid in MAPS.items():
        if only and key not in only:
            continue
        town = areas[key].get("area_type") == "town"
        out = map_path("towns" if town else "routes", key)
        if key in WHOLE:
            img = whole_picture(game, mid)
        else:
            img = game.town_background(mid) if town else game.route_background(mid)
        if img is None or (key not in WHOLE and mostly_void(img)):  # an indoor map: the area keeps its own picture
            skipped += 1
            print(f"  skipped {key}: Map{mid:03d} is mostly black")
            continue
        os.makedirs(os.path.dirname(out), exist_ok=True)
        pygame.image.save(img, out)
        done += 1
        print(f"  {out}  <- Map{mid:03d} {rxdata.text(game.info[mid].attrs['name']).strip()}")
    if not only:
        for name, mid in BUILDINGS.items():
            out = os.path.join("assets", "backgrounds", "orre", name)
            pygame.image.save(room_picture(game, mid), out)
            print(f"  {out}  <- Map{mid:03d} {rxdata.text(game.info[mid].attrs['name']).strip()}")
    print(f"{done} backgrounds, {skipped} skipped")


if __name__ == "__main__":
    main(sys.argv[1:])
