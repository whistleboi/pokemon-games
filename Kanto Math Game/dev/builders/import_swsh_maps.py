"""Galar town and route backgrounds from Sword and Shield Ultimate Plus (Jordan, 11-01): a FireRed ROM
hack by Pclg and Jeanstars, translated by Phantonomy, tiles by KingTapir. Its wiki
(github.com/Ddaretrogamer/sword-and-shield-ultimate-plus-wiki) has a screenshot of each map: whole,
top-down, no labels; the same look as the other regions' fan-game maps.

Each map is shown whole, fitted to the height above the text box (or the width), with a blurred,
darkened copy filling the sides, like Orre's (render_orre_backgrounds.whole_picture).

Matched by hand (MAPS, checked by eye). Left out: Spikemuth, Wyndon, Rose Tower, the Meetup Spot, the
Weald Altar and the Space-Time Distortion (the hack has no map for them), and Snowslide Slope and the
Split-Decision Ruins (no clear match); those keep their pictures.

Downloads to dev/builders/out/swsh_maps (kept between runs), saves to
assets/backgrounds/galar/towns|routes/<area key>.png, which the town and route screens use first.
    python dev/builders/import_swsh_maps.py [AREA_KEY ...]
"""
import json
import os
import sys
import urllib.parse
import urllib.request

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

WIKI = "https://raw.githubusercontent.com/Ddaretrogamer/sword-and-shield-ultimate-plus-wiki/HEAD/docs/img/routes/"
CACHE = os.path.join("dev", "builders", "out", "swsh_maps")
OUT = os.path.join("assets", "backgrounds", "galar")
SIZE = (1280, 540)

# our area -> the wiki's map picture
MAPS = {
    "POSTWICK": "Postwick", "WEDGEHURST": "Wedgehurst", "MOTOSTOKE": "Motostoke", "TURFFIELD": "Turffield",
    "HULBURY": "Hulbury", "STOW_ON_SIDE": "Stow-On-Side", "BALLONLEA": "Ballonlea", "CIRCHESTER": "Circhester",
    "HAMMERLOCKE": "Hammerlocke",
    "GALAR_ROUTE_1": "Route 1", "GALAR_ROUTE_2": "Route 2", "GALAR_ROUTE_3": "Route 3", "GALAR_ROUTE_4": "Route 4",
    "GALAR_ROUTE_5": "Route 5", "GALAR_ROUTE_6": "Route 6", "GALAR_ROUTE_7": "Route 7", "GALAR_ROUTE_8": "Route 8",
    "GALAR_ROUTE_9": "Route 9", "GALAR_ROUTE_10": "Route 10",
    "MOTOSTOKE_OUTSKIRTS": "Motostoke East", "SLUMBERING_WEALD": "Slumbering Weald",
    "GALAR_MINE": "Galar Mine 1", "GALAR_MINE_NO_2": "Galar Mine 2", "GLIMWOOD_TANGLE": "Glimwood Tangle",
    # the Wild Areas in two zones each ("zones" in galar_area_data.json): <area>_<zone key>
    "WILD_AREA_ROLLING_FIELDS": "Wild Area 1 South", "WILD_AREA_LAKE_MILOCH": "Wild Area 1 North",
    "WILD_AREA_NORTH_BRIDGE_FIELD": "Wild Area 1 Northeast", "WILD_AREA_NORTH_HAMMERLOCKE_HILLS": "Wild Area 4 West",
    # the Isle of Armor and the Crown Tundra in zones too
    "ISLE_OF_ARMOR_FIELDS_OF_HONOR": "Isle Of Armor 1", "ISLE_OF_ARMOR_SOOTHING_WETLANDS": "Isle Of Armor 4",
    "ISLE_OF_ARMOR_FOREST_OF_FOCUS": "Isle Of Armor 5", "ISLE_OF_ARMOR_CHALLENGE_ROAD": "Isle Of Armor 8",
    "ISLE_OF_ARMOR_POTBOTTOM_DESERT": "Isle Of Armor Desert",
    "CROWN_TUNDRA_FREEZINGTON": "Freezington (Crown Tundra)", "CROWN_TUNDRA_FROSTPOINT_FIELD": "Crown Tundra Snowy East",
    "CROWN_TUNDRA_GIANTS_BED": "Crown Tundra Grassy East", "CROWN_TUNDRA_BALLIMERE_LAKE": "Tree Base (Crown Tundra)",
    "DYNA_TREE_HILL": "Big Tree (Crown Tundra)", "CROWN_OLD_CEMETERY": "Crown Tundra Graveyard",
    "MAX_LAIR": "Dynamax Adventure (Crown Tundra)",
}


def fetch(name):
    """The wiki's picture, downloaded once."""
    path = os.path.join(CACHE, name + ".png")
    if not os.path.exists(path):
        os.makedirs(CACHE, exist_ok=True)
        urllib.request.urlretrieve(WIKI + urllib.parse.quote(name + ".png"), path)
    return path


def whole_picture(img, size=SIZE):
    """All of a map in the frame: fitted, crisp when it's made bigger, a blurred copy behind."""
    w, h = size
    k = min(w / img.get_width(), h / img.get_height())
    dims = (int(img.get_width() * k), int(img.get_height() * k))
    main = pygame.transform.scale(img, dims) if k >= 1 else pygame.transform.smoothscale(img, dims)
    out = pygame.Surface(size)
    solid = pygame.Surface(img.get_size())  # see-through corners take the map's own colour, not black
    solid.fill(pygame.transform.average_color(img, pygame.Rect(0, 0, img.get_width() // 2, img.get_height() // 2))[:3])
    solid.blit(img, (0, 0))
    blur = pygame.transform.smoothscale(solid, (24, max(1, 24 * h // w)))
    out.blit(pygame.transform.smoothscale(blur, size), (0, 0))
    dark = pygame.Surface(size, pygame.SRCALPHA)
    dark.fill((0, 0, 0, 120))
    out.blit(dark, (0, 0))
    out.blit(main, main.get_rect(center=(w // 2, h // 2)))
    return out


def main(argv):
    only = {a.upper() for a in argv}
    pygame.init()
    pygame.display.set_mode((1, 1))
    with open(os.path.join("assets", "galar_area_data.json"), encoding="utf-8") as f:
        areas = json.load(f)["STORY_PROGRESSION"]
    done = 0
    for key, name in MAPS.items():
        if only and key not in only:
            continue
        kind = "towns" if (areas.get(key) or {}).get("area_type") == "town" else "routes"  # (a zone: routes)
        img = pygame.image.load(fetch(name)).convert_alpha()  # (Freezington has see-through corners)
        out = os.path.join(OUT, kind, key.lower() + ".png")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        pygame.image.save(whole_picture(img), out)
        done += 1
        print(f"  {out}  <- {name}")
    print(f"{done} backgrounds")


if __name__ == "__main__":
    main(sys.argv[1:])
