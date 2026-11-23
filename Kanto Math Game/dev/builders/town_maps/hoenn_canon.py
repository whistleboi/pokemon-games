"""Hoenn re-audit batch H4 (11-23): canon fixes laid over the Emerald maps, after oras_fill and oras_extras.

Found by kanto_handoff/hoenn_rom_tools/hcanon.py (kanto_handoff/hoenn_check/CANON.md); Jordan's answers in
kanto_handoff/hoenn_check/DECISIONS.md. Kept here, one place, instead of hand edits in emerald.py (which hdrift.py would
have to carry): each entry names the area, the floor (or a town's room) and the tile.

- PEOPLE: someone (an area option, by its text; or a whole person dict) set on an open tile, as oras_fill does.
- HIDDEN: an item hidden on a tile (dungeon.py "hidden": stepped on / faced, the Itemfinder beeps).
- LISTS: a person who already stands there gets more to say, first come first: [new options..., what they had]. With two
  showing at once the player picks from a small menu (walk_town: a person that is a list).
The options themselves (texts, conditions, lines) are the area data's (hoenn_area_data.json / hoenn_oras.json).
"""
from . import oras_fill as _F

# Every ORAS Mega Stone obtainable (Jordan 11-23, DECISIONS #20): the stones that were area options with no spot.
# The post-Primal ones (ORAS: "after capturing or defeating Groudon / Kyogre") wait for cave_of_origin_cleared in the data.
PEOPLE = [
    ("LITTLEROOT_TOWN", None, None, 4, 18, "A Glinting Stone: Mewtwonite X"),   # (south-west of Birch's Lab)
    ("LAVARIDGE_TOWN", None, None, 6, 10, "A Glinting Stone: Houndoominite"),   # (by the sand baths)
    ("HOENN_ROUTE_110", 0, None, 29, 15, "MANECTITE"),                           # (east of the Cycling Road's north gate)
    ("HOENN_ROUTE_119", 0, None, 24, 131, "VENUSAURITE"),                        # (the southernmost long grass)
    ("HOENN_ROUTE_123", None, None, 6, 9, "ABOMASITE"),                          # (the Berry fields, west)
    ("HOENN_ROUTE_124", 0, None, 15, 75, "PINSIRITE"),                           # (the lone sandbar in the south-west)
    ("HOENN_PETALBURG_WOODS", None, None, 20, 10, "SCIZORITE"),                  # (past the Cut trees)
    ("HOENN_JAGGED_PASS", None, None, 21, 31, "TYRANITARITE"),                   # (by the southernmost grass)
    # ORAS: the Team grunt in the Oceanic Museum gives TM Thief (oras_fill had put him in Slateport's street as
    # "Team MagmaOR/AquaAS Grunt"; his option is taken out of hoenn_oras.json and stands here instead)
    ("HOENN_OCEANIC_MUSEUM", 0, None, 16, 3,
     {"text": "Bored grunt", "action": "EVENT", "flag_condition": "not oras_slateport_city_6",
      "event": {"lines": ["Grunt: Ugh, guarding a museum. Here, take this TM off my hands. I never use it anyway."],
                "gift_item": {"TM018": 1}, "flag": "oras_slateport_city_6"}}),
]
TRAINERS = [   # (trainers in the area data with no spot on the map: set on open water near the route's others)
    ("HOENN_ROUTE_129", 0, 55, 25, "Scuba Diver Colten"),
    ("HOENN_ROUTE_129", 0, 70, 33, "Free Diver Coral"),
]
HIDDEN = [
    ("HOENN_GRANITE_CAVE", 1, 36, 11, "STEELIXITE"),   # (1F, the south side east of the big rock: hidden, as ORAS)
]
LISTS = [
    # Rusturf Tunnel: Wanda's boyfriend digs out the Aggronite once the tunnel is cleared (ORAS)
    ("HOENN_RUSTURF_TUNNEL", None, None, 23, 5, ["AGGRONITE"]),
    # Littleroot: after the Delta Episode Mom has your version's Lati stone (ORAS: Latiasite in Omega Ruby, Latiosite in
    # Alpha Sapphire; the options' hoenn_version conditions pick)
    ("LITTLEROOT_TOWN", None, "home", 2, 6, ["Mom", "Mom's Second Stone"]),
]


def _part(m, floor, room):
    if room:
        return m["rooms"][room]
    if floor is not None and m.get("floors"):
        return m["floors"][floor]
    return m


def _at(part, x, y):
    """The index in the part's people list of the person on (x, y) (people go to the N tiles in reading order)."""
    spots = [(cx, cy) for cy, r in enumerate(part["art"]) for cx, c in enumerate(r) if c == "N"]
    return spots.index((x, y)) if (x, y) in spots else None


def apply(maps):
    for key, floor, room, x, y, who in PEOPLE:
        m = maps.get(key)
        if m:
            _F._put(_part(m, floor, room), "N", "people", [[x, y, who]])
    for key, floor, x, y, name in TRAINERS:
        m = maps.get(key)
        if m:
            _F._put(_part(m, floor, None), "X", "trainer_spots", [[x, y, name]])
    for key, floor, x, y, item in HIDDEN:
        m = maps.get(key)
        if m:
            p = _part(m, floor, None)
            p.setdefault("hidden", {})[f"{x},{y}"] = item
    for key, floor, room, x, y, more in LISTS:
        m = maps.get(key)
        if not m:
            continue
        p = _part(m, floor, room)
        i = _at(p, x, y)
        if i is None:
            print(ascii(f"  hoenn_canon: nobody stands on {key} {room or floor} {x},{y}: {more} left out"))
            continue
        had = p["people"][i]
        p["people"][i] = list(more) + (had if isinstance(had, list) else [had])
