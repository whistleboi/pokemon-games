"""Safari Zones in areas (Jordan, 11-02): each Safari Zone is split into its games' areas, each with
its own picture and its own wild Pokemon (zone_pools), like the Wild Areas' zones.

- Kanto: FireRed/LeafGreen's Center Area and Areas 1-3 (East, North, West).
- Johto: HeartGold/SoulSilver's twelve areas (their default Pokemon; no blocks).
- Hoenn: Omega Ruby/Alpha Sapphire's Areas 1-4 (Emerald's 5 and 6 aren't in ORAS).
- Sinnoh: the Great Marsh's Areas 1-6 (Brilliant Diamond/Shining Pearl), the Pokemon that change
  daily in every area at a low rate.
- The Seafoam Islands too (Jordan, 11-02): FireRed/LeafGreen's floors 1F-B4F, down the stairs like the
  Pokemon Tower (zones_linear), Articuno on B4F and the way out on 1F.

Encounter tables: Bulbapedia's area tables (land only: Surfing and fishing keep the area's own
pools). Pictures: Bulbapedia's area pictures (FRLG, HGSS), or crops of the whole map (Emerald's
Safari Zone, Platinum's Great Marsh), scaled up by whole pixels and framed to 1280 x 540.
The Pokemon each area had before stay, each placed in the area that suits it (EXTRAS).

Run from the game folder:  python dev/builders/build_safari_zones.py [--pictures]
"""
import io
import json
import math
import os
import re
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame  # noqa: E402

sys.path.insert(0, os.path.dirname(__file__))
from fetch_town_backgrounds import api, download  # noqa: E402

CACHE = os.path.join("dev", "builders", "out", "safari_maps")
W, H = 1280, 540

# region file, area key, Bulbapedia page, the game's section, picture folder
SAFARIS = {
    "KANTO": ("pokemon_area_data", "SAFARI_ZONE", "Kanto Safari Zone", "Generation III", "kanto"),
    "JOHTO": ("johto_area_data", "JOHTO_SAFARI_ZONE", "Johto Safari Zone", None, "johto"),
    "HOENN": ("hoenn_area_data", "HOENN_SAFARI_ZONE", "Hoenn Safari Zone", "Generation VI", "hoenn"),
    "SINNOH": ("sinnoh_area_data", "GREAT_MARSH", "Great Marsh", "Generation VIII", "sinnoh"),
    "SEAFOAM": ("pokemon_area_data", "SEAFOAM_ISLANDS", "Seafoam Islands", "Generation III", "kanto"),
}
# Floors (UP / DOWN the stairs) rather than areas side by side; the menu items kept to one floor.
LINEAR = {"SEAFOAM": {"CHALLENGE ARTICUNO": "b4f", "EXIT CAVE": "1f"}}
MOODS = {"SEAFOAM": {"1f": "Cold sea air blows in from the entrance.",
                     "b1f": "The floor is slick with ice.",
                     "b2f": "Boulders sit by the frozen pools.",
                     "b3f": "Fast currents rush through the dark water.",
                     "b4f": "It's freezing down here. Something is watching..."}}
# zone key, name, the page's section heading(s), picture
ZONES = {
    "KANTO": [("center", "Center Area", ["Center Area"], "Safari Zone entrance FRLG.png"),
              ("east", "Area 1 (East)", ["Area 1 - East"], "Safari Zone area 1 FRLG.png"),
              ("north", "Area 2 (North)", ["Area 2 - North"], "Safari Zone area 2 FRLG.png"),
              ("west", "Area 3 (West)", ["Area 3 - West"], "Safari Zone area 3 FRLG.png")],
    "JOHTO": [(a.lower().replace(" ", "_"), a, [a], f"Johto Safari Zone {a} HGSS.png")
              for a in ("Plains", "Meadow", "Savannah", "Peak", "Rocky Beach", "Wetland", "Forest", "Swamp",
                        "Marshland", "Wasteland", "Mountain", "Desert")],
    "HOENN": [(f"area_{n}", f"Area {n}", [f"Area {n}"], "Hoenn Safari Zone E.png") for n in (1, 2, 3, 4)],
    "SINNOH": [(f"area_{n}", f"Area {n}", [s], "Great Marsh Pt.png")
               for n, s in ((1, "Areas 1 and 2"), (2, "Areas 1 and 2"), (3, "Areas 3 and 4"),
                            (4, "Areas 3 and 4"), (5, "Area 5"), (6, "Area 6"))],
    "SEAFOAM": [(f.lower(), f, [f], f"Seafoam Islands {f} FRLG.png") for f in ("1F", "B1F", "B2F", "B3F", "B4F")],
}
# Crops of a whole-map picture: (x, y, w, h) of each area in it (Emerald's map is 1920 x 1280 in
# a 3 x 2 grid, Areas 1-4 here; Platinum's Great Marsh is 1088 x 1200, split by its center path).
CROPS = {
    ("HOENN", "area_1"): (642, 708, 589, 572), ("HOENN", "area_2"): (0, 708, 642, 572),
    ("HOENN", "area_3"): (0, 0, 642, 708), ("HOENN", "area_4"): (642, 0, 589, 708),
    ("SINNOH", "area_1"): (0, 0, 576, 440), ("SINNOH", "area_2"): (576, 0, 512, 440),
    ("SINNOH", "area_3"): (0, 440, 576, 330), ("SINNOH", "area_4"): (576, 440, 512, 270),
    ("SINNOH", "area_5"): (0, 770, 576, 430), ("SINNOH", "area_6"): (576, 710, 512, 490),
}
# The Pokemon each Safari Zone had before (not in its games' tables), and the area each goes to.
EXTRAS = {
    "KANTO": {"1": "west", "2": "west", "108": "north", "112": "north", "133": "center", "2017": "east",
              "2055": "east", "2056": "east", "2057": "east", "2058": "west"},
    "JOHTO": {"214": "forest", "212": "forest", "231": "savannah", "232": "savannah", "227": "mountain",
              "241": "plains", "246": "wasteland", "247": "wasteland", "215": "mountain", "207": "desert",
              "213": "rocky_beach", "216": "forest", "152": "meadow"},
    "HOENN": {"214": "area_4", "212": "area_4", "231": "area_2", "232": "area_2", "227": "area_3",
              "241": "area_1", "246": "area_3", "247": "area_3", "215": "area_4", "207": "area_3",
              "213": "area_2", "216": "area_1"},
    "SINNOH": {"46": "area_1", "118": "area_6", "271": "area_3", "114": "area_5"},
    "SEAFOAM": {"7": "1f", "8": "b1f", "90": "b3f", "91": "b3f", "98": "b4f", "99": "b4f", "124": "b4f",
                "131": "b4f", "134": "b2f", "2022": "b1f", "2023": "b2f", "2006": "b3f", "2007": "b3f"},
}
# The Great Marsh's daily Pokemon (in a different area each day in the games): a little of each everywhere.
DAILY_RATE = 1  # (one of them at a time, about 10%, in the games)


def wikitext(page):
    path = os.path.join(CACHE, page.replace(" ", "_") + ".txt")
    if not os.path.isfile(path):
        os.makedirs(CACHE, exist_ok=True)
        text = api(action="parse", page=page, prop="wikitext", redirects=1)["parse"]["wikitext"]["*"]
        open(path, "w", encoding="utf-8").write(text)
    return open(path, encoding="utf-8").read()


def section(text, game, heading):
    """The lines under a heading (inside the game's section, when given), up to the next heading."""
    pokemon = re.search(r"^==+\s*Pokémon\s*==+\s*$", text, re.M)  # (the tables are under Pokémon)
    text = text[pokemon.end():] if pokemon else text
    if game:
        start = re.search(r"^(=+)\s*%s\s*=+\s*$" % re.escape(game), text, re.M)
        text = text[start.end():]
        end = re.search(r"^={1,%d}[^=]" % len(start.group(1)), text, re.M)  # the next heading as high
        text = text[:end.start()] if end else text
    m = re.search(r"^=+\s*%s\s*=+\s*$" % re.escape(heading), text, re.M)
    if not m:
        raise KeyError(heading)
    rest = text[m.end():]
    end = re.search(r"^=+[^=]", rest, re.M)
    return rest[:end.start()] if end else rest


LAND = ("grass", "tall grass", "horde encounter", "walking", "cave")


def rate(value):
    value = value.strip().replace("all=", "")
    if "/" in value:
        a, b = value.rstrip("%").split("/")
        return 100.0 * float(a) / float(b)
    try:
        return float(value.rstrip("%"))
    except ValueError:
        return 5.0  # "??%"


def land_rates(block, stop_at_block_list=True):
    """{species id: weight} of the land encounters in a table (both versions, every time of day)."""
    out = {}
    for line in block.splitlines():
        low = line.lower()
        if low.startswith("{{catch/div"):
            if "hidden" in low or "water" in low or "rock smash" in low or "national" in low:
                break
            continue
        if stop_at_block_list and "the following are block-based" in low:  # (Johto's blocks: not here)
            break
        m = re.match(r"\{\{[Cc]atch/entry\w*\|(\d+)\|[^|]*\|(yes|no)\|(yes|no)\|([^|]*)\|[^|]*\|(.*)\}\}", line)
        if not m or m.group(4).strip().lower() not in LAND:
            continue
        pid, v1, v2, _, tail = m.groups()
        rates = [rate(x) for x in tail.split("|") if x.strip() and "=" not in x.replace("all=", "")]
        share = ((v1 == "yes") + (v2 == "yes")) / 2
        key = str(int(pid))
        out[key] = out.get(key, 0) + share * (sum(rates) / len(rates) if rates else 0)
    return {k: v for k, v in out.items() if v > 0}


def daily(text):
    """The Great Marsh's daily Pokemon (Brilliant Diamond / Shining Pearl, the National Dex ones too)."""
    block = section(text, "Generation VIII", "Changing Pokémon")
    ids = re.findall(r"\{\{catch/entry\w*\|(\d+)\|", block, re.I)
    return list(dict.fromkeys(str(int(i)) for i in ids))


def percentages(weights):
    total = sum(weights.values())
    pct = {k: max(1, round(100 * v / total)) for k, v in sorted(weights.items(), key=lambda kv: -kv[1])}
    return pct


def pools(region):
    _file, _area, page, game, _folder = SAFARIS[region]
    text = wikitext(page)
    out = {}
    for key, _name, heads, _pic in ZONES[region]:
        weights = {}
        for head in heads:
            for k, v in land_rates(section(text, game, head)).items():
                weights[k] = weights.get(k, 0) + v
        pct = percentages(weights)
        if region == "SINNOH":
            for pid in daily(text):
                pct[pid] = pct.get(pid, 0) + DAILY_RATE
        out[key] = pct
    return out


def picture(region, key, pic):
    path = os.path.join(CACHE, pic.replace(" ", "_"))
    if not os.path.isfile(path):
        data = download("File:" + pic)
        open(path, "wb").write(data)
    img = pygame.image.load(path)
    crop = CROPS.get((region, key))
    if crop:
        img = img.subsurface(pygame.Rect(crop).clip(img.get_rect())).copy()
    w, h = img.get_size()
    k = max(math.ceil(W / w), math.ceil(H / h))  # whole pixels keep the pixel art sharp
    img = pygame.transform.scale(img, (w * k, h * k))
    frame = pygame.Rect(0, 0, W, H)
    frame.center = img.get_rect().center
    return img.subsurface(frame).copy()


def main(argv):
    pictures = "--pictures" in argv
    for region, (fname, area, _page, _game, folder) in SAFARIS.items():
        path = os.path.join("assets", fname + ".json")
        s = open(path, encoding="utf-8", newline="").read()
        data = json.loads(s)
        block = data["STORY_PROGRESSION"][area]
        old_key = block["wild_pool_percentages"]
        old = data[old_key]
        zp = pools(region)
        extras = EXTRAS[region]
        for pid, weight in old.items():
            zone = extras.get(pid)
            if any(pid in p for p in zp.values()):
                continue
            if not zone:
                raise SystemExit(f"{region}: {pid} was in the Safari Zone but has no area (EXTRAS)")
            zp[zone][pid] = zp[zone].get(pid, 0) + weight
        new = {}
        for key, _name, _heads, _pic in ZONES[region]:
            pool_key = f"{old_key[:-len('_PERCENTAGES')]}_{key.upper()}_PERCENTAGES"
            new[pool_key] = zp[key]
        union = {}
        for p in zp.values():
            for pid, w in p.items():
                union[pid] = max(union.get(pid, 0), w)
        print(f"== {region}: {len(union)} species ({len(old)} before)")
        for key, name, _h, _p in ZONES[region]:
            print(f"   {name}: {zp[key]}")
        if pictures:
            for key, _name, _heads, pic in ZONES[region]:
                out = os.path.join("assets", "backgrounds", folder, "routes", f"{area.lower()}_{key}.png")
                os.makedirs(os.path.dirname(out), exist_ok=True)
                pygame.image.save(picture(region, key, pic), out)
        yield region, path, s, data, area, old_key, union, new


def write(path, s, area, old_key, union, new, zones, region=None):
    """Into the hand-formatted file: the area's zones (EXPLORE buttons) and zone pools, a ZONE menu
    item before its first way out, its old pool turned into all the areas' Pokemon, and the area pools."""
    nl = "\r\n" if "\r\n" in s else "\n"
    start = s.index(f'"{area}": {{')
    head_end = s.index(nl, start) + len(nl)
    if '"zone_pools"' not in s[start:s.index("route_menu", start)]:
        ind = re.match(r"[ ]*", s[head_end:]).group(0)
        zone_list = ", ".join(json.dumps({"key": k, "name": n}) for k, n, _h, _p in zones)
        pools_map = json.dumps({k: pk for (k, *_), pk in zip(zones, new)})
        how = (f'{ind}"zones_linear": true,{nl}{ind}"zones_descend": true,{nl}'  # (down into the cave)
               f'{ind}"zone_moods": {json.dumps(MOODS.get(region, {}))},{nl}'
               if region in LINEAR else f'{ind}"zones_explore": true,{nl}')
        s = s[:head_end] + (f'{ind}"zones": [{zone_list}],{nl}' + how +
                            f'{ind}"zone_pools": {pools_map},{nl}') + s[head_end:]
        for text, zone in LINEAR.get(region, {}).items():  # Articuno at the bottom, the way out at the top
            item = s.index(f'"text": "{text}"', start)
            close = s.index("}", item)
            s = s[:close].rstrip() + f', "zone": "{zone}" ' + s[close:]
    menu = s.index('"route_menu": [', start)
    first_exit = s.index('"action": "EXIT"', menu)
    line = s.rindex(nl, 0, first_exit) + len(nl)
    if '"action": "ZONE"' not in s[menu:first_exit]:
        ind = re.match(r"[ ]*", s[line:]).group(0)
        s = s[:line] + f'{ind}{{ "text": "ZONE", "action": "ZONE", "color": "CYAN" }},{nl}' + s[line:]
    m = re.search(r'^([ ]*)"%s": \{[^\n]*\},?\r?$' % re.escape(old_key), s, re.M)
    ind = m.group(1)
    lines = [f'{ind}"{old_key}": {json.dumps(union)},']
    lines += [f'{ind}"{k}": {json.dumps(v)},' for k, v in new.items() if f'"{k}":' not in s]
    s = s[:m.start()] + nl.join(lines) + s[m.end():] if m.group(0).rstrip().endswith(",") else None
    json.loads(s)
    open(path, "w", encoding="utf-8", newline="").write(s)


if __name__ == "__main__":
    for region, path, s, _data, area, old_key, union, new in main(sys.argv[1:]):
        if "--write" in sys.argv:
            write(path, s, area, old_key, union, new, ZONES[region], region)
            print("   written:", path)
