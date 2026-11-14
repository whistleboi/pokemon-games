"""Soaring in the Sky, 3D (Jordan, 11-14: the "baked 2.5D, phone-safe" try): what the flight needs to know.

The ground is Omega Ruby's own sky map of Hoenn, baked from Jordan's game file to top-down pictures
(kanto_handoff/oras_rom_tools/bake_soaring3d.py -> assets/soaring3d). Places here are in that map's world units:
x east, z south (about 48 000 x 36 000 across the main picture). The screen: src/states/overworld/soaring3d.py.

What's out there comes from the HOENN_SOARING_IN_THE_SKY area's own menu (assets/hoenn_area_data.json):
- each EXIT to a Mirage place is a spot below to land on;
- the six SEEK legends (the Journal's "Soaring in the Sky", hoenn_s30) wait in the sky, as in ORAS: a Dimensional
  Rift south of Dewford Town (Dialga, Palkia, then Giratina) and a storm cloud north of Fortree City (Tornadus,
  Thundurus, then Landorus). One legend each time you fly in, in that order; ORAS's party conditions are left out.
"""
import math

AREA = "HOENN_SOARING_IN_THE_SKY"
FLUTE = "EON_FLUTE"
FLUTE_TEXT = "Play it outside in Hoenn and your Eon friend comes to fly you high over the region."


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
    """Why the Eon Flute can't be played here (a line to show), or None."""
    if str(story.get_current_region() or "").upper() != "HOENN":
        return "Your Eon friend can't hear the flute this far from Hoenn."
    area = story.get_current_area_data() or {}
    if area.get("indoors") or area.get("battle_type") in ("indoor", "cave"):
        return "There's no open sky here. Try it outside!"
    if story.current_area_key == AREA:
        return "You're already soaring!"
    return None

# Towns, read off the baked map (world units). Landing picks the nearest you've visited.
TOWNS = {
    "LITTLEROOT_TOWN": (-3800, 7600), "OLDALE_TOWN": (-3700, 5200), "PETALBURG_CITY": (-6700, 4300),
    "RUSTBORO_CITY": (-9400, -3100), "DEWFORD_TOWN": (-7700, 11200), "SLATEPORT_CITY": (1500, 8500),
    "MAUVILLE_CITY": (1200, 900), "VERDANTURF_TOWN": (-4300, 1500), "FALLARBOR_TOWN": (-5400, -6200),
    "LAVARIDGE_TOWN": (-1500, -3100), "FORTREE_CITY": (6800, -5900), "LILYCOVE_CITY": (14300, -2900),
    "MOSSDEEP_CITY": (22000, -1400), "SOOTOPOLIS_CITY": (18200, 2300), "PACIFIDLOG_TOWN": (12600, 7400),
    "EVER_GRANDE_CITY": (25000, 4000),
}

# Mirage places (the area's EXITs), out at sea or tucked in the hills, near where ORAS has them.
LAND_SPOTS = {
    "HOENN_MIRAGE_ISLAND": ("island", (-10000, 12000)),
    "HOENN_MIRAGE_FOREST": ("forest", (1000, 11500)),
    "HOENN_MIRAGE_CAVE": ("cave", (24200, 9400)),
    "HOENN_MIRAGE_MOUNTAIN": ("mountain", (15500, -5700)),
    "HOENN_CRESCENT_ISLE": ("crescent", (25900, 15700)),
    "HOENN_PATHLESS_PLAIN": ("plain", (13300, 12100)),
    "HOENN_NAMELESS_CAVERN": ("cave", (20500, 600)),
    "HOENN_FABLED_CAVE": ("cave", (4300, 4000)),
    "HOENN_GNARLED_DEN": ("den", (-3100, -6800)),
    "HOENN_TRACKLESS_FOREST": ("forest", (-7900, 1400)),
}

# The legends in the sky: (look, where, height, the SEEK bosses' victory flags in the order they come out)
SKY_SPOTS = [
    {"key": "rift", "look": "rift", "at": (-7200, 14400), "alt": 2200, "name": "a huge gap in the sky",
     "flags": ["soaring_dialga", "soaring_palkia", "soaring_giratina"]},
    {"key": "storm", "look": "storm", "at": (5400, -9700), "alt": 2600, "name": "a black storm cloud",
     "flags": ["soaring_tornadus", "soaring_thundurus", "soaring_landorus"]},
]


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
        if flags.get(f"legend_rematch_{flag}") or _flag_ok(flags, item):
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
