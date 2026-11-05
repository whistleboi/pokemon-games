"""Town and route backgrounds from GBA ROM hacks' maps (Jordan, 11-04), read with gba_maps.py.

So far: Unova from Pokemon Black & White Advanced (a FireRed hack, the "d2" demo: Nuvema Town to
Driftveil City; its other maps are FireRed's own Kanto and Sevii, left out), and Orange Islands places
the Pokemon Journeys maps lack from Pokemon Orange Generation (pokeant's FireRed hack), and Kanto and
Sevii places they lack from Pokemon Ultra Violet (LocksmithArmy's FireRed hack), and Hoenn caves and
places they lack from Pokemon Mega Emerald X and Y (jovefreak1993's Emerald hack, set in Hoenn).
Also Wyndon from Sword and Shield Ultimate v3.1.5 (the other Galar places come from its wiki).

Each area's map is matched by hand (ROMS[..]["maps"], group.map numbers, checked by eye), drawn at 2x
(32 px a metatile, like the Pokemon Journeys backgrounds) and framed to the screen above the text box:
- a town shows the whole town, fitted, with a blurred, darkened copy filling the sides (as Orre's);
- a route or cave shows its grassiest stretch at full size (the whole map, fitted, if it's smaller).
Saved to assets/backgrounds/<region>/towns|routes/<area key>.png (its sub-region's folder, like Sevii's,
where there is one), which the town and route screens use before any other background.
    python dev/builders/import_gba_maps.py [AREA_KEY ...]
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gba_maps import Rom, MapReader  # noqa: E402
from render_orre_backgrounds import whole_picture  # noqa: E402
from render_journeys_backgrounds import map_path  # noqa: E402

DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")
W, H = 1280, 540  # the screen above the text box
SCALE = 2         # 16 px metatiles drawn at 32 px, the Journeys backgrounds' size
MAX_VOID = 0.15   # a route's frame may show this much empty (black) map

ROMS = {
    "Pokemon Black & White Advanced": {
        "path": os.path.join(DOWNLOADS, "Pokemon Black & White Advanced", "black-advanced-d2.gba"),
        # our area -> (map group, map number), with the hack's name for it
        "maps": {
            "NUVEMA_TOWN": (3, 0), "ACCUMULA_TOWN": (3, 1), "STRIATON_CITY": (3, 2),
            "NACRENE_CITY": (3, 3), "CASTELIA_CITY": (3, 4), "DRIFTVEIL_CITY": (3, 6),
            "UNOVA_ROUTE_1": (3, 19), "UNOVA_ROUTE_2": (3, 20), "UNOVA_ROUTE_3": (3, 22),
            "UNOVA_ROUTE_4": (3, 23),  # "Route 4-Desert"
            "UNOVA_ROUTE_5": (3, 24),
            "PINWHEEL_FOREST": (1, 114), "DREAMYARD": (39, 0), "WELLSPRING_CAVE": (1, 122),
        },
    },
    # Orange Islands places the Pokemon Journeys maps don't have (its own Orange maps; the rest of the
    # ROM is FireRed's Kanto and Sevii). Left out: its "Mikan Cave" (not clearly our Crystal Cave) and
    # its unnamed "Route 3" / "Route 4".
    "Pokemon Orange Generation": {
        "path": os.path.join(DOWNLOADS, "Pokemon Orange Generation", "Pokemon Orange Generation.gba"),
        "maps": {
            "ORANGE_ROUTE_52": (3, 20), "ORANGE_ROUTE_53": (3, 29), "ORANGE_ROUTE_54": (3, 24),
            "MURCOTT_ISLAND": (1, 0),
        },
    },
    # Kanto and Sevii places the Pokemon Journeys maps don't cover (a FireRed hack with its own game
    # code, so the engine is named). It has no Johto. Left out: the S.S. Anne (its dock map shows only
    # sea; the ship is a sprite), Bill's house, the Underground Path (a narrow corridor), the League gate.
    "Pokemon Ultra Violet": {
        "path": os.path.join(DOWNLOADS, "Pokemon Ultra Violet v1.22", "Pokemon Ultra Violet v1.22.gba"),
        "engine": "BPRE",
        "maps": {
            "VIRIDIAN_CITY": (3, 1), "MT_MOON_CITY": (1, 1), "ROCK_TUNNEL_CITY": (1, 81),
            "SILPH_CITY": (1, 51), "KANTO_POKEMON_TOWER": (1, 94),
            "THREE_ISLE_PORT": (3, 49), "NAVEL_ROCK": (2, 0), "BIRTH_ISLAND": (2, 56),
            "ROCKET_WAREHOUSE": (1, 114),
        },
    },
    # Despite its name, a Hoenn game (Emerald with X/Y Pokemon and Mega Evolution): no Kalos maps.
    # Hoenn's caves and places the Pokemon Journeys maps don't cover. Left out (no map there): Seafloor
    # Cavern, the Weather Institute, Oceanic Museum, Space Center, S.S. Tidal, Mirage Island, Sea Mauville.
    "Pokemon Mega Emerald X and Y": {
        "path": os.path.join(DOWNLOADS, "Pokemon X and Y GBA", "mega-emerald-x-y.gba"),
        "maps": {
            "HOENN_ARTISAN_CAVE": (24, 99), "HOENN_SEALED_CHAMBER": (24, 72), "HOENN_SCORCHED_SLAB": (24, 73),
            "HOENN_ALTERING_CAVE": (24, 106), "HOENN_MIRAGE_TOWER": (24, 96), "HOENN_MAGMA_HIDEOUT": (24, 91),
            "HOENN_MT_CHIMNEY": (24, 12), "HOENN_NEW_MAUVILLE": (24, 53), "HOENN_ABANDONED_SHIP": (24, 54),
            "HOENN_SAFARI_ZONE": (26, 13), "HOENN_SHOAL_CAVE": (24, 51), "HOENN_CAVE_OF_ORIGIN": (24, 39),
            "HOENN_SKY_PILLAR": (24, 85), "HOENN_VICTORY_ROAD": (24, 43), "HOENN_TEAM_HIDEOUT": (24, 75),
            "HOENN_SOUTHERN_ISLAND": (26, 9), "HOENN_MARINE_CAVE": (24, 103), "HOENN_TERRA_CAVE": (24, 105),
        },
    },
    # Galar places the wiki pictures (import_swsh_maps.py) don't have. Left out: Spikemuth and its Isle of
    # Armor town (their colours come out magenta: the hack loads those palettes while it runs), its "Rose
    # Tower" and "Crown Tundra" (an office room; FireRed's Ember Spa renamed).
    # (Pokemon Sun and Moon GBA and Pokemon Scarlet+Violet were checked too: both keep FireRed's Kanto
    # and Sevii maps, so they have nothing for Alola or Paldea.)
    "Pokemon Sword and Shield Ultimate": {
        "path": os.path.join(DOWNLOADS, "Pokemon Sword and Shield Ultimate GBA v3.1.5 English",
                             "Pokemon Sword and Shield Ultimate GBA v3.1.5 English.gba"),
        "maps": {"WYNDON": (3, 9)},
    },
}


class _Shown:
    """whole_picture's view of a map: render(mid) gives the drawn map."""

    def __init__(self, img):
        self.img = img

    def render(self, _mid):
        return self.img


def route_frame(img, grass):
    """W x H of the map at full size around its grassiest stretch (the lower two thirds count
    twice: the wild Pokemon stand there) that shows the least empty (black) map. A narrow (or flat)
    route shows its full width (or height) that way, a blurred copy at the sides; one smaller than
    the screen both ways is shown whole, fitted."""
    if img.get_width() < W and img.get_height() < H:
        return whole_picture(_Shown(img), None, (W, H))
    cell = 16 * SCALE
    ww, hh = min(W, img.get_width()), min(H, img.get_height())
    wt, ht = -(-ww // cell), -(-hh // cell)
    ys, xs = len(grass), len(grass[0])
    black = [[all(sum(img.get_at((x * cell + dx, y * cell + dy))[:3]) < 40
                  for dx, dy in ((2, 2), (cell // 2, cell // 2), (cell - 3, cell - 3)))
              for x in range(xs)] for y in range(ys)]

    def prefix(grid):
        pre = [[0] * (xs + 1) for _ in range(ys + 1)]
        for y in range(ys):
            row = 0
            for x in range(xs):
                row += grid[y][x]
                pre[y + 1][x + 1] = pre[y][x + 1] + row
        return pre

    pre, void = prefix(grass), prefix(black)

    def box(x0, y0, x1, y1, grid=None):
        g = grid or pre
        return g[y1][x1] - g[y0][x1] - g[y1][x0] + g[y0][x0]

    best, best_score = (0, 0), None
    for y0 in range(0, max(1, ys - ht + 1)):
        for x0 in range(0, max(1, xs - wt + 1)):
            x1, y1 = min(xs, x0 + wt), min(ys, y0 + ht)
            score = box(x0, y0, x1, y1) + box(x0, y0 + ht // 3, x1, y1) - 3 * box(x0, y0, x1, y1, void)
            if best_score is None or score > best_score:
                best, best_score = (x0, y0), score
    x0, y0 = best
    if box(x0, y0, min(xs, x0 + wt), min(ys, y0 + ht), void) > MAX_VOID * wt * ht:
        return whole_picture(_Shown(img), None, (W, H))  # a cave with empty map all round: all of it
    crop = pygame.Rect(x0 * cell, y0 * cell, ww, hh).clamp(img.get_rect())
    part = img.subsurface(crop).copy()
    if (ww, hh) == (W, H):
        return part
    out = pygame.transform.smoothscale(pygame.transform.smoothscale(part, (24, max(1, 24 * H // W))), (W, H))
    dark = pygame.Surface((W, H), pygame.SRCALPHA)
    dark.fill((0, 0, 0, 120))
    out.blit(dark, (0, 0))
    out.blit(part, part.get_rect(center=(W // 2, H // 2)))
    return out


def area_kinds():
    """{area key: "towns" or "routes"} from every region's area data."""
    import json
    out = {}
    for fname in os.listdir("assets"):
        if fname.endswith("_area_data.json"):
            with open(os.path.join("assets", fname), encoding="utf-8") as f:
                for key, area in (json.load(f).get("STORY_PROGRESSION") or {}).items():
                    if isinstance(area, dict):
                        out[key] = "towns" if area.get("area_type") == "town" else "routes"
    return out


def main(argv):
    only = {a.upper() for a in argv}
    pygame.init()
    pygame.display.set_mode((1, 1))
    kinds = area_kinds()
    done = 0
    for title, cfg in ROMS.items():
        if not os.path.isfile(cfg["path"]):
            print(f"{title}: not found at {cfg['path']}")
            continue
        reader = MapReader(Rom(cfg["path"], cfg.get("engine")))
        groups = reader.groups()
        for key, (gi, mi) in cfg["maps"].items():
            if only and key not in only:
                continue
            header = groups[gi][mi]
            img = reader.render(header, SCALE)
            kind = kinds.get(key, "routes")
            out = (whole_picture(_Shown(img), None, (W, H)) if kind == "towns"
                   else route_frame(img, reader.grass(header)))
            path = map_path(kind, key)  # its region's (or sub-region's) folder
            os.makedirs(os.path.dirname(path), exist_ok=True)
            pygame.image.save(out, path)
            done += 1
            print(f"  {path}  <- {title} {gi}.{mi} {reader.name(reader.layout(header)['section'])}")
    print(f"{done} backgrounds")


if __name__ == "__main__":
    main(sys.argv[1:])
