"""Soaring in the Sky, 3D (Jordan, 11-14: the "baked 2.5D, phone-safe" try): what the flight needs to know.

The ground is the 2D version's map of Hoenn, or Omega Ruby's own sky map baked from Jordan's game file
(kanto_handoff/oras_rom_tools/bake_soaring3d.py -> assets/soaring3d): GROUND below. Places are in world units,
x east, z south (Omega Ruby's: Hoenn is about 48 000 x 36 000). The screen: src/states/overworld/soaring3d.py.

What's out there comes from the HOENN_SOARING_IN_THE_SKY area's own menu (assets/hoenn_area_data.json):
- each EXIT to a Mirage place is a spot below to land on;
- the six SEEK legends (the Journal's "Soaring in the Sky", hoenn_s30) wait in the sky, as in ORAS: a Dimensional
  Rift south of Dewford Town (Dialga, Palkia, then Giratina) and a storm cloud north of Fortree City (Tornadus,
  Thundurus, then Landorus). One legend each time you fly in, in that order; ORAS's party conditions are left out.
"""
import math

AREA = "HOENN_SOARING_IN_THE_SKY"
FLUTE = "EON_FLUTE"
FLUTE_TEXT = "Play it outside and your Eon friend comes to fly you high over the regions you know."


# ---------------------------------------------------------------- the Eon Flute (ORAS: Steven gives it at Southern Island)
def give_flute(story):
    """The Eon Flute comes with the Eon at Southern Island; a save that met its Eon before the flute was in the game
    gets it now. True if it was added."""
    if story.inventory.get(FLUTE, 0) > 0 or not story.story_flags.get("got_mega_bracelet"):
        return False
    mine = story.store_regions() if hasattr(story, "store_regions") else None
    if mine is not None and "HOENN" not in mine:
        return False
    story.inventory[FLUTE] = 1
    return True


def flute_block(story):
    """Why the Eon Flute can't be played here (a line to show), or None. It plays in any region (Jordan, 11-18: whoever
    has their Mega Latias / Latios in another region is a Champion of two, so may soar there and land there too);
    the flight's area is a border area (assets/hoenn_area_data.json "border"), so going up keeps the region you're in."""
    area = story.get_current_area_data() or {}
    if area.get("indoors") or area.get("battle_type") in ("indoor", "cave"):
        return "There's no open sky here. Try it outside!"
    if story.current_area_key == AREA:
        return "You're already soaring!"
    return None

# Which ground you fly over (Jordan, 11-14: "use that map instead of the blurry one"; 11-18: one big world):
#   "world" - Hoenn, Johto, Kanto, the Sevii and Orange Islands as one ground, placed as Jordan's world map has them
#             (assets/soaring3d/world, dev/builders/make_soaring_world.py); only where you've been is clear, the rest
#             is under clouds (cover_open below). Hoenn is the same size and in the same place as on the "map" ground;
#   "map"   - the 2D version's ground: the game's own Hoenn map picture redrawn in our pixel style
#             (assets/soaring3d/map_ground.png, from hoenn-soaring-2d's dev/builders/make_soaring_ground.py);
#   "oras"  - Omega Ruby's own sky map, baked (ground.jpg, ground_far.jpg).
# A missing world falls back to "map".
GROUND = "world"
# Which world: "world", placed as the game's own world map (Pokemon Journeys', assets/world_map 2.png): Jordan's pick
# (11-18) over duskl1ghtness's map ("world_dusk": make_soaring_world.py --layout=dusk builds it, not kept in assets).
WORLD = "world"
# Who carries you (Jordan, 11-14: "the 2D sprite but still your 3D coordinating"):
#   "sprite" - Jordan's Mega Latias / Latios from behind, the 2D version's (assets/soaring3d/mega_lati*_back.png);
#   "model"  - Omega Ruby's own models, baked at 5 banks x 3 pitches (eon_<id>_<bank>_<pitch>.png).
EON_LOOK = "sprite"

# The map picture (assets/region_maps/hoenn.png, 480 x 320, map_points.json's frame) in world units: one scale and
# offset, fitted to the towns on both grounds so heights and speeds feel the same over either. The ground picture
# is that map four times the size with 40 map rows of sea added above (make_soaring_ground.py).
MAP_SCALE, MAP_X0, MAP_Z0 = 88.4, -13391.0, -12234.0
MAP_GROUND_SCALE, MAP_GROUND_PAD = 4, 40


def map_xy(px):
    """A point on the map picture (map_points.json's pixels) in world units."""
    return px[0] * MAP_SCALE + MAP_X0, px[1] * MAP_SCALE + MAP_Z0


def map_ground_rect(w, h):
    """The map ground picture's world rect (x0, z0, x1, z1), from its size in pixels."""
    k = MAP_SCALE / MAP_GROUND_SCALE
    x0, z0 = MAP_X0, MAP_Z0 - MAP_GROUND_PAD * MAP_SCALE
    return x0, z0, x0 + w * k, z0 + h * k


# Towns on Omega Ruby's sky map, read off the bake (world units). On the map ground they come from map_points.json.
ORAS_TOWNS = {
    "LITTLEROOT_TOWN": (-3800, 7600), "OLDALE_TOWN": (-3700, 5200), "PETALBURG_CITY": (-6700, 4300),
    "RUSTBORO_CITY": (-9400, -3100), "DEWFORD_TOWN": (-7700, 11200), "SLATEPORT_CITY": (1500, 8500),
    "MAUVILLE_CITY": (1200, 900), "VERDANTURF_TOWN": (-4300, 1500), "FALLARBOR_TOWN": (-5400, -6200),
    "LAVARIDGE_TOWN": (-1500, -3100), "FORTREE_CITY": (6800, -5900), "LILYCOVE_CITY": (14300, -2900),
    "MOSSDEEP_CITY": (22000, -1400), "SOOTOPOLIS_CITY": (18200, 2300), "PACIFIDLOG_TOWN": (12600, 7400),
    "EVER_GRANDE_CITY": (25000, 4000),
}

# Mirage places (the area's EXITs), near where ORAS has them: (look, on the sky map, on the map picture)
SPOT_PLACES = {
    "HOENN_MIRAGE_ISLANDS": ("island", (-10000, 12000), (52, 276)),   # (ORAS's Mirage Island: the Gen 1-3 legends)
    "HOENN_MIRAGE_FOREST": ("forest", (1000, 11500), (172, 266)),
    "HOENN_MIRAGE_CAVE": ("cave", (24200, 9400), (424, 232)),
    "HOENN_MIRAGE_MOUNTAIN": ("mountain", (15500, -5700), (322, 80)),
    "HOENN_CRESCENT_ISLE": ("crescent", (25900, 15700), (446, 296)),
    "HOENN_PATHLESS_PLAIN": ("plain", (13300, 12100), (306, 266)),
    "HOENN_NAMELESS_CAVERN": ("cave", (20500, 600), (374, 148)),
    "HOENN_FABLED_CAVE": ("cave", (4300, 4000), (204, 186)),
    "HOENN_GNARLED_DEN": ("den", (-3100, -6800), (118, 84)),
    "HOENN_TRACKLESS_FOREST": ("forest", (-7900, 1400), (70, 166)),
}

# The legends in the sky: where (sky map / map picture), height, the SEEK bosses' victory flags in the order they come
SKY_PLACES = [
    {"key": "rift", "look": "rift", "oras": (-7200, 14400), "px": (84, 300), "alt": 2200, "name": "a huge gap in the sky",
     "flags": ["soaring_dialga", "soaring_palkia", "soaring_giratina"]},
    {"key": "storm", "look": "storm", "oras": (5400, -9700), "px": (204, 46), "alt": 2600, "name": "a black storm cloud",
     "flags": ["soaring_tornadus", "soaring_thundurus", "soaring_landorus"]},
]

# The wild Pokemon flying over each region (Jordan, 11-18: "a generation's birds would only be over that area of the
# map"; normal flyers in flocks of at least three, the stronger ones now and then alone). Each region's own generation,
# from the birds its own wild tables have (Orange's: 5.7's Kanto birds). {region: (flocks, solos)}, {species: weight}.
SKY_BIRDS = {
    "KANTO": ({16: 40, 21: 35, 17: 15, 83: 10}, {18: 45, 22: 45, 142: 7, 149: 3}),
    "SEVII": ({21: 40, 16: 25, 177: 20, 198: 15}, {22: 45, 178: 30, 227: 25}),
    "JOHTO": ({163: 35, 165: 25, 177: 20, 198: 20}, {164: 40, 178: 25, 227: 25, 166: 10}),
    "HOENN": ({278: 35, 276: 35, 333: 30}, {279: 30, 277: 30, 334: 25, 357: 12, 373: 3}),
    "ORANGE": ({16: 40, 21: 35, 17: 15, 83: 10}, {18: 50, 22: 45, 149: 5}),
}
SOLO = 0.12            # how often what comes is one strong flyer on its own, not a flock
FLOCK = (3, 5)         # how many fly together
REGION_NAMES = {"HOENN": "Hoenn", "JOHTO": "Johto", "KANTO": "Kanto", "SEVII": "Sevii Islands",
                "ORANGE": "Orange Islands"}


def sky_wild(region, rng, fallback=None):
    """(species, how many) for the next flyers over this region: a flock of FLOCK, or now and then (SOLO) one strong
    flyer alone. fallback: the area's own pool, for a sky with no birds of its own."""
    flocks, solos = SKY_BIRDS.get(region, (fallback or {}, {}))
    if not flocks and not solos:
        return None, 0
    if solos and (rng.random() < SOLO or not flocks):
        pool, n = solos, 1
    else:
        pool, n = flocks, rng.randint(*FLOCK)
    keys = list(pool)
    return int(rng.choices(keys, [pool[k] for k in keys])[0]), n


# The places on the ground in use (use_ground sets them): towns, Mirage places (look, at), the sky's legends.
# LAND_TOWNS: the towns LAND can set you down in (on the world: every region's, Jordan 11-18; the flight lets you land
# where Fly would: a town you've been to with a Pokemon Center, or a region's home town: fly_map.fly_ok).
TOWNS, LAND_SPOTS, SKY_SPOTS, LAND_TOWNS = {}, {}, [], set()


# ---------------------------------------------------------------- the world ground (GROUND = "world")
def world_meta(assets_dir):
    """assets/soaring3d/world/world.json (make_soaring_world.py), or None if the world isn't built."""
    import json
    import os
    try:
        with open(os.path.join(assets_dir, "soaring3d", WORLD, "world.json"), encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def world_point(meta, sx, sy):
    """A point on the world's town-map-sized picture (world.json's map_px frame) in world units."""
    ox, oz = meta["origin"]
    u = meta["unit_per_map_px"]
    return ox + sx * u, oz + sy * u


def world_rect(meta):
    """The world ground's rect in world units (x0, z0, x1, z1)."""
    ox, oz = meta["origin"]
    u = meta["unit_per_map_px"]
    w, h = meta["map_px"]
    return ox, oz, ox + w * u, oz + h * u


def cover_open(meta, flags):
    """Which towns' patches of the world are clear (Jordan, 11-18: "soaring should only allow to reach the areas the
    player has been to"): the numbers (world.json's seeds) of the towns you've been to."""
    towns = {i for i, (key, _region, _x, _y) in enumerate(meta["seeds"]) if flags.get(f"visited_{key}")}
    # open sea far from any town goes with its nearest region: clear once you've been anywhere in that region
    regions = meta.get("regions") or []
    known = {meta["seeds"][i][1] for i in towns}
    return towns | {meta.get("sea_of", 200) + n for n, r in enumerate(regions) if r in known}


def use_ground(ground, town_px=None, meta=None):
    """Put every place on this ground ("world", "map" or "oras"); town_px: map_points.json's Hoenn points; meta: the
    world's world.json."""
    global TOWNS, LAND_SPOTS, SKY_SPOTS, LAND_TOWNS
    if ground == "world" and meta:
        TOWNS = {key: world_point(meta, x, y) for key, _region, x, y in meta["seeds"]}
        LAND_TOWNS = {key for key, _region, _x, _y in meta["seeds"]}   # (any region's: the flight keeps Fly's rule)
        LAND_SPOTS = {k: (look, map_xy(px)) for k, (look, _at, px) in SPOT_PLACES.items()}
        SKY_SPOTS = [dict(s, at=map_xy(s["px"])) for s in SKY_PLACES]
        return
    LAND_TOWNS = set(ORAS_TOWNS)
    if ground == "map":
        TOWNS = {k: map_xy(p) for k, p in (town_px or {}).items() if k in ORAS_TOWNS} or dict(ORAS_TOWNS)
        LAND_SPOTS = {k: (look, map_xy(px)) for k, (look, _at, px) in SPOT_PLACES.items()}
        SKY_SPOTS = [dict(s, at=map_xy(s["px"])) for s in SKY_PLACES]
    else:
        TOWNS = dict(ORAS_TOWNS)
        LAND_SPOTS = {k: (look, at) for k, (look, at, _px) in SPOT_PLACES.items()}
        SKY_SPOTS = [dict(s, at=s["oras"]) for s in SKY_PLACES]


use_ground("oras")


def _flag_ok(flags, item):
    fc = item.get("flag_condition")
    if fc:
        parts = fc.split()
        if parts[0] == "not" and len(parts) == 2:
            if flags.get(parts[1]):
                return False
        elif not flags.get(parts[0]):
            return False
    cond = item.get("condition")
    if isinstance(cond, list):
        for c in cond:
            c = str(c)
            if c.startswith("not:"):
                if flags.get(c[4:]):
                    return False
            elif not flags.get(c):
                return False
    return True


def bosses(area_data, flags):
    """The area's SEEK legends you can meet now: {victory flag: boss dict}. A legend that got away comes back
    (legend_rematch_<flag>, as on the route menu)."""
    out = {}
    for item in area_data.get("route_menu") or []:
        if item.get("action") != "BOSS" or not item.get("boss"):
            continue
        flag = item["boss"].get("victory_flag")
        from src.states.battle import legend_back
        if legend_back(flags, flag) or _flag_ok(flags, item):   # (one that got away: back the next day)
            out[flag] = item["boss"]
    return out


def sky_spots(area_data, flags):
    """The rift and the cloud while a legend in them is still out: each with "next", the boss that comes out."""
    have = bosses(area_data, flags)
    out = []
    for s in SKY_SPOTS:
        nxt = next((have[f] for f in s["flags"] if f in have), None)
        if nxt:
            out.append(dict(s, next=nxt))
    return out


def land_spots(area_data, flags, names=None):
    """The Mirage places to land on: the area's EXITs that have a spot here. Each: key, look, at, area, name,
    beacon (a legend there still to catch: its area has a BOSS whose flag isn't set)."""
    out = []
    names = names or {}
    for item in area_data.get("route_menu") or []:
        if item.get("action") != "EXIT":
            continue
        target = item.get("target_area") or item.get("target")
        if target not in LAND_SPOTS:
            continue
        look, at = LAND_SPOTS[target]
        out.append({"key": target, "look": look, "at": at, "area": target,
                    "name": names.get(target) or item.get("text", target).title(), "beacon": False})
    return out


def mark_beacons(spots, story_data, flags):
    """A red beacon over a Mirage place while one of its legends is still to catch (ORAS)."""
    for s in spots:
        area = story_data.get(s["area"]) or {}
        s["beacon"] = any(it.get("action") == "BOSS" and it.get("boss") and not flags.get(it["boss"].get("victory_flag"))
                          for it in area.get("route_menu") or [])
    return spots


def nearest_town(x, z, visited=None):
    """(key, distance) of the nearest town, among the visited ones if any are."""
    keys = [k for k in TOWNS if not visited or k in visited] or list(TOWNS)
    k = min(keys, key=lambda t: (TOWNS[t][0] - x) ** 2 + (TOWNS[t][1] - z) ** 2)
    return k, math.hypot(TOWNS[k][0] - x, TOWNS[k][1] - z)


def town_name(key):
    return key.replace("_", " ").title()
