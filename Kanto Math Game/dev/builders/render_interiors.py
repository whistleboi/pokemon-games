"""Building interiors (Gyms, labs, the hero's home, Pokemon Centers and Marts) rendered from the fan games'
indoor maps (Jordan, 11-04), for the towns whose buildings still use a stand-in picture.

Sources: the Pokemon Essentials games Pokemon Everlasting X and Devastating Y (Kalos) and Pokemon Journeys
V18 (Kanto, Johto, Hoenn, Sinnoh, Sevii, Orange), drawn by render_journeys_backgrounds.Journeys; and the GBA
ROM hacks Mega Emerald X and Y (Hoenn) and Black & White Advanced (Unova), read by gba_maps.py (map numbers
"group.map", rects in metatiles; no people on these).
Each room is matched by hand (ROOMS, checked by eye), drawn with its people (Nurse Joy, the leader, Mom),
cropped to the room (or to a hand-picked stretch of a big map: (x, y, w, h) in tiles), scaled up crisp to
fill the screen above the text box, on black, like Orre's Center and Mart. Also each region's shared Center
and Mart (SHARED) for its towns without their own. A Gym can have several rooms
in order (a list): the lobby shows the one for the next battle, the Leader's last (gym_lobby.py).

Saved in the region's background folder under the name the town's data gives it ("backgrounds": "gym",
"lab", "mom_home"...), or <area key>_gym / _center / _mart.png, the name the screens look for otherwise.
A Gym's rooms take the names in its data's list, which has to be there first.
Needs the fan games and ROMs where import_gba_maps.py and render_exy_backgrounds.py look for them.
    python dev/builders/render_interiors.py [AREA_KEY ...]
"""
import json
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rxdata  # noqa: E402
from render_journeys_backgrounds import JOURNEYS, Journeys, map_path  # noqa: E402
from render_exy_backgrounds import EXY_GAME  # noqa: E402
from gba_maps import Rom, MapReader  # noqa: E402
from import_gba_maps import ROMS  # noqa: E402

W, H = 1280, 540  # the screen above the text box
SOURCES = {"exy": EXY_GAME, "journeys": JOURNEYS,
           "emerald": "Pokemon Mega Emerald X and Y", "bwa": "Pokemon Black & White Advanced"}  # (ROMS' names)
# The town data's background key for each kind of room, and the suffix of the name the screens fall back on.
KINDS = {"gym": ("gym", "gym"), "center": ("pokecenter", "center"), "mart": ("pokemart", "mart"),
         "lab": ("lab", "lab"), "mom": ("mom", "mom")}
# (area key, kind) -> (source, map number[, (x, y, w, h) tiles]), or a list of them (a Gym's rooms)
ROOMS = {
    # Kalos (its shared Center keeps its X/Y picture). Left out: the gyms past Cyllage (not built yet).
    # Its Gyms have no trainers: the first room is for the Gym challenge, the last the Leader's.
    ("SANTALUNE_CITY", "gym"): [("exy", 92, (0, 15, 10, 10)),    # a forest room
                                ("exy", 92, (0, 0, 10, 9))],     # Viola's
    ("CYLLAGE_CITY", "gym"): [("exy", 121, (18, 30, 33, 17)),    # the climbing hall
                              ("exy", 121, (39, 14, 12, 10))],   # Grant's ledge
    ("LUMIOSE_CITY", "lab"): ("exy", 101),                       # Sycamore's Lab, upstairs
    ("VANIVILLE_TOWN", "mom"): ("exy", 48),                      # the hero's house
    # From Pokemon Journeys' Kanto labs and Pallet homes (Sinnoh's in Journeys are empty).
    ("PALLET_TOWN", "mom"): ("journeys", 176, (4, 25, 14, 12)),
    ("TWINLEAF_TOWN", "mom"): ("journeys", 176, (4, 56, 15, 11)),
    ("SANDGEM_TOWN", "lab"): ("journeys", 175, (6, 5, 15, 15)),
    # Hoenn, from Mega Emerald X and Y (Emerald's maps). A Gym's trainers share the rooms before the Leader's.
    ("LITTLEROOT_TOWN", "mom"): ("emerald", "1.0"),
    ("LITTLEROOT_TOWN", "lab"): ("emerald", "1.4"),
    ("PETALBURG_CITY", "gym"): [("emerald", "8.1", (0, 103, 9, 9)),   # the lobby
                                ("emerald", "8.1", (0, 90, 9, 12)),   # a training room
                                ("emerald", "8.1", (0, 0, 9, 8))],    # Norman's
    ("RUSTBORO_CITY", "gym"): ("emerald", "11.3"),
    ("DEWFORD_TOWN", "gym"): ("emerald", "3.3"),
    ("MAUVILLE_CITY", "gym"): ("emerald", "10.0"),
    ("LAVARIDGE_TOWN", "gym"): [("emerald", "4.2"), ("emerald", "4.1")],  # the basement, then Flannery's floor
    ("FORTREE_CITY", "gym"): ("emerald", "12.1"),
    ("MOSSDEEP_CITY", "gym"): [("emerald", "14.0", (0, 25, 10, 11)),  # the lobby
                               ("emerald", "14.0", (19, 3, 8, 9))],   # Tate and Liza's
    ("SOOTOPOLIS_CITY", "gym"): ("emerald", "15.0"),
    ("EVER_GRANDE_CITY", "gym"): [("emerald", f"16.{i}") for i in range(5)],  # the Elite Four's rooms, Steven's
    # Unova, from Black & White Advanced (as far as it goes: Nuvema to Driftveil; Castelia's colours are wrong).
    ("NUVEMA_TOWN", "mom"): ("bwa", "4.0"),
    ("NUVEMA_TOWN", "lab"): ("bwa", "4.3"),
    ("STRIATON_CITY", "gym"): ("bwa", "6.2"),
    ("NACRENE_CITY", "gym"): [("bwa", "7.5", (0, 0, 22, 40)),          # the library
                              ("bwa", "7.5", (36, 0, 14, 40))],        # Lenora's
}
# The regions' shared Center and Mart, for the towns without their own (assets.REGION_DEFAULT_BUILDINGS):
# background folder/file -> (source, map number, (x, y, w, h) tiles). Journeys' Indigo and Hoenn rooms.
SHARED = {
    "kanto/kanto_center.png": ("journeys", 182, (0, 27, 20, 13)),
    "kanto/kanto_mart.png": ("journeys", 181, (2, 10, 14, 12)),
    "hoenn/hoenn_center.png": ("journeys", 501, (8, 26, 18, 14)),
    "hoenn/hoenn_mart.png": ("journeys", 503, (3, 6, 16, 12)),
}


def out_name(area, kind):
    """(The name the town's data gives a room, or None; the data's key for it.)"""
    data_key, suffix = KINDS[kind]
    bgs = area.get("backgrounds") or {}
    keys = [data_key] + (["mom_home", "mom_house"] if kind == "mom" else ["prof_oak_lab"] if kind == "lab" else [])
    for k in keys:
        name = bgs.get(k)
        if isinstance(name, list):
            name = name[0] if name else None
        if name and name not in ("pokecenter.png", "pokemart.png"):
            return name, k
    return None, data_key


def out_names(area, key, kind, count):
    """The files a room (or a Gym's rooms) is saved as."""
    names = (area.get("backgrounds") or {}).get(KINDS[kind][0])
    if count > 1:
        if not (isinstance(names, list) and len(names) == count):
            sys.exit(f"{key}: list its {count} {kind} pictures in its data's backgrounds first")
        return names
    name = out_name(area, kind)[0]
    return [name or f"{key.lower()}_{KINDS[kind][1]}.png"]


_drawn = {}


def drawn(game, mid, people):
    if (id(game), mid, people) not in _drawn:
        _drawn[(id(game), mid, people)] = game.render(mid, people=people)[0]
    return _drawn[(id(game), mid, people)]


class GbaRooms:
    """A GBA ROM hack's maps, drawn like an Essentials game's (32 px a metatile); map ids are "group.map"."""

    def __init__(self, title):
        cfg = ROMS[title]
        self.reader = MapReader(Rom(cfg["path"], cfg.get("engine")))
        self.headers = self.reader.groups()
        self.title = title

    def header(self, mid):
        gi, mi = map(int, mid.split("."))
        return self.headers[gi][mi]

    def render(self, mid, people=True):
        return (self.reader.render(self.header(mid), 2),)

    def label(self, mid):
        return f"{self.title} {mid} {self.reader.name(self.reader.layout(self.header(mid))['section'])}"


def room(game, mid, rect=None):
    """A room as a W x H picture: its drawn part (within rect, in tiles, on a map of many rooms) with its
    people, scaled up crisp, on black."""
    full, tiles = drawn(game, mid, True), drawn(game, mid, False)
    area = (pygame.Rect(rect[0] * 32, rect[1] * 32, rect[2] * 32, rect[3] * 32).clip(full.get_rect()) if rect
            else full.get_rect())
    # the room's tiles only, so a person standing off in the dark doesn't widen it
    mask = pygame.mask.from_threshold(tiles.subsurface(area), (0, 0, 0, 255), (12, 12, 12, 255))
    mask.invert()
    rects = mask.get_bounding_rects()
    box = rects[0].unionall(rects[1:]).move(area.topleft) if rects else area
    part = full.subsurface(box)
    k = min(W / part.get_width(), H / part.get_height())
    big = pygame.transform.scale(part, (int(part.get_width() * k), int(part.get_height() * k)))
    out = pygame.Surface((W, H))
    out.blit(big, big.get_rect(center=(W // 2, H // 2)))
    return out


def all_areas():
    out = {}
    for fname in os.listdir("assets"):
        if fname.endswith("_area_data.json"):
            with open(os.path.join("assets", fname), encoding="utf-8") as f:
                out.update((k, v) for k, v in (json.load(f).get("STORY_PROGRESSION") or {}).items()
                           if isinstance(v, dict))
    return out


def main(argv):
    only = {a.upper() for a in argv}
    pygame.init()
    pygame.display.set_mode((1, 1))
    areas = all_areas()
    games = {}

    def save(path, src, mid, rect):
        if src not in games:
            root = SOURCES[src]
            if root in ROMS:
                games[src] = GbaRooms(root) if os.path.isfile(ROMS[root]["path"]) else None
            else:
                games[src] = Journeys(root) if os.path.isdir(os.path.join(root, "Data")) else None
            if games[src] is None:
                print(f"{src}: not found ({root})")
        game = games[src]
        if game is None:
            return 0
        pygame.image.save(room(game, mid, rect), path)
        label = game.label(mid) if isinstance(game, GbaRooms) else             f"{src} Map{mid:03d} {rxdata.text(game.info[mid].attrs['name']).strip()}"
        print(f"  {path}  <- {label}")
        return 1

    done = 0
    for (key, kind), specs in ROOMS.items():
        if only and key not in only:
            continue
        specs = specs if isinstance(specs, list) else [specs]
        folder = os.path.dirname(os.path.dirname(map_path("towns", key)))  # the region's background folder
        for name, (src, mid, *rect) in zip(out_names(areas[key], key, kind, len(specs)), specs):
            done += save(os.path.join(folder, name), src, mid, rect[0] if rect else None)
    if not only:
        for rel, (src, mid, rect) in SHARED.items():
            done += save(os.path.join("assets", "backgrounds", *rel.split("/")), src, mid, rect)
    print(f"{done} rooms")


if __name__ == "__main__":
    main(sys.argv[1:])
