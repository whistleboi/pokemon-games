"""Hoenn re-audit batch H4 (11-23): canon fixes laid over the Emerald maps, after oras_fill and oras_extras.

Found by kanto_handoff/hoenn_rom_tools/hcanon.py (kanto_handoff/hoenn_check/CANON.md); Jordan's answers in
kanto_handoff/hoenn_check/DECISIONS.md. Kept here, one place, instead of hand edits in emerald.py (which hdrift.py would
have to carry): each entry names the area, the floor (or a town's room) and the tile.

- PEOPLE: someone (an area option, by its text; or a whole person dict) set on an open tile, as oras_fill does.
- HIDDEN: an item hidden on a tile (dungeon.py "hidden": stepped on / faced, the Itemfinder beeps).
- LISTS: a person who already stands there gets more to say, first come first: [new options..., what they had]. With two
  showing at once the player picks from a small menu (walk_town: a person that is a list).
The options themselves (texts, conditions, lines) are the area data's (hoenn_area_data.json / hoenn_oras.json).
- H4 items (11-23): the missing ORAS / Emerald item balls (PEOPLE, made by _ball: a "found" item stepped into once) and
  hidden items (HIDDEN), each on the tile its walkthrough line or Emerald's map gives. Routes 107, 129 and 130 have no
  seabed floor yet, so their seabed Plates, Orbs and shards wait for one.
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
# Mauville (Jordan 11-23, #18): ORAS's Ultimate Move Studio and Pledge Move Dojo, in Mauville Hills (Emerald's Mauville has
# no mall); as every tutor now, they sell their moves as TMs (src/pokemon/tutors.py), at the TM's price as Johto's
PEOPLE += [
    ("MAUVILLE_CITY", None, "hills", 10, 5,
     {"text": "Ultimate Move tutor", "action": "EVENT",
      "event": {"lines": ["Tutor: The ultimate moves! Only a fully evolved first partner who loves its Trainer can learn one."],
                "tutor": {"choices": ["FRENZY-PLANT", "BLAST-BURN", "HYDRO-CANNON"], "min_friend": 220, "price": "tm"}}}),
    ("MAUVILLE_CITY", None, "hills", 12, 5,
     {"text": "Pledge tutor", "action": "EVENT",
      "event": {"lines": ["Tutor: Pledge moves! Fire, Water and Grass, each stronger together. Want to learn one?"],
                "tutor": {"choices": ["GRASS-PLEDGE", "FIRE-PLEDGE", "WATER-PLEDGE"], "price": "tm"}}}),
]
HIDDEN = [
    ("HOENN_GRANITE_CAVE", 1, 36, 11, "STEELIXITE"),   # (1F, the south side east of the big rock: hidden, as ORAS)
]


def _ball(item, text, flag, name):
    """An item ball: a "found" item you step into, once (the area data's found items, worded the same)."""
    return {"text": text, "action": "EVENT", "color": "GOLD", "found": True, "flag_condition": f"not {flag}",
            "event": {"lines": [f"You found {name}!"], "gift_item": {item: 1}, "flag": flag}}


# H4 items (11-23): the ORAS / Emerald item balls and hidden items hcanon.py found missing (CANON.md "item ball",
# "hidden item"). Each sits where ORAS's walkthrough says, or on Emerald's own tile when the check gives one.
PEOPLE += [
    # Magma Hideout (Emerald's tiles; the PP Max's own tile holds the Cameruptite, so it lies one step east)
    ("HOENN_MAGMA_HIDEOUT", 2, None, 21, 7, _ball("MAX_ELIXIR", "MAX ELIXIR far side", "got_h4_magma_max_elixir", "a Max Elixir")),
    ("HOENN_MAGMA_HIDEOUT", 4, None, 6, 9, _ball("PP_MAX", "PP MAX side room", "got_h4_magma_pp_max", "a PP Max")),
    # Route 107: on the beach by Dewford
    ("HOENN_ROUTE_107", None, None, 2, 12, _ball("SUPER_REPEL", "SUPER REPEL beach", "got_h4_r107_super_repel", "a Super Repel")),
    # Route 111: north-east of the south entrance
    ("HOENN_ROUTE_111", None, None, 23, 135, _ball("STARDUST", "STARDUST south", "got_h4_r111_stardust", "some Stardust")),
    # Route 123: south-west of Ace Trainer Julie
    ("HOENN_ROUTE_123", None, None, 133, 15, _ball("PP_UP", "PP UP east", "got_h4_r123_pp_up", "a PP Up")),
    # Route 134: the islet in the south-west
    ("HOENN_ROUTE_134", 0, None, 26, 29, _ball("HEART_SCALE", "HEART SCALE islet", "got_h4_r134_heart_scale", "a Heart Scale")),
    # Granite Cave: B2F's north side (Emerald's Repel and Rare Candy tiles), its south side (the TM by the big rock),
    # and the second Escape Rope east of Hiker Davian
    ("HOENN_GRANITE_CAVE", 3, None, 4, 4, _ball("REPEL", "REPEL north side", "got_h4_granite_repel", "a Repel")),
    ("HOENN_GRANITE_CAVE", 3, None, 29, 4, _ball("RARE_CANDY", "RARE CANDY north side", "got_h4_granite_rare_candy", "a Rare Candy")),
    ("HOENN_GRANITE_CAVE", 3, None, 14, 11, _ball("TM061", "TM061 SHADOW CLAW", "got_h4_granite_tm_shadow_claw", "TM Shadow Claw")),
    ("HOENN_GRANITE_CAVE", 0, None, 10, 7, _ball("ESCAPE_ROPE", "ESCAPE ROPE by the Hiker", "got_h4_granite_escape_rope", "an Escape Rope")),
    # Jagged Pass: south of Hiker Eric, on the middle slope
    ("HOENN_JAGGED_PASS", None, None, 19, 12, _ball("FULL_HEAL", "FULL HEAL slope", "got_h4_jagged_full_heal", "a Full Heal")),
]
HIDDEN += [
    # Pacifidlog: east of the south-east house's door
    ("PACIFIDLOG_TOWN", None, 14, 24, "HEART_SCALE"),
    # Route 106: the water's edge north-east of Fisherman Elliot
    ("HOENN_ROUTE_106", None, 59, 12, "POKE_BALLS"),
    # Route 109: north-west of Sailor Huey (the blue umbrella); the island south of the beach
    ("HOENN_ROUTE_109", None, 15, 11, "HEART_SCALE"),
    ("HOENN_ROUTE_109", None, 31, 30, "HEART_SCALE"),
    # Route 111: east of Picnicker Becky
    ("HOENN_ROUTE_111", None, 28, 132, "STARDUST"),
    # Route 116: the closed-off part by Rusturf Tunnel's east end
    ("HOENN_ROUTE_116", None, 72, 7, "BLACK_GLASSES"),
    # Route 123: north of Psychic Cameron
    ("HOENN_ROUTE_123", None, 30, 13, "PP_UP"),
    # Route 126, the seabed: bare spots in the seaweed
    ("HOENN_ROUTE_126", 1, 11, 4, "HEART_SCALE"),     # (northern area)
    ("HOENN_ROUTE_126", 1, 28, 4, "ULTRA_BALL"),      # (south-east of the north-west dive spot)
    ("HOENN_ROUTE_126", 1, 19, 16, "MIND_PLATE"),     # (the dead end north, then west, of the crater)
    ("HOENN_ROUTE_126", 1, 38, 12, "BIG_PEARL"),      # (north-north-west of the crater)
    ("HOENN_ROUTE_126", 1, 11, 34, "BLUE_SHARD"),     # (north of the western dive spot)
    ("HOENN_ROUTE_126", 1, 22, 60, "PEARL"),          # (the crater's south-west side)
    ("HOENN_ROUTE_126", 1, 37, 67, "STARDUST"),       # (just west of the way into Sootopolis)
    ("HOENN_ROUTE_126", 1, 64, 60, "YELLOW_SHARD"),   # (east-south-east of the crater)
    # Route 128: the sand ring's south side, the sandbar east of it, the south-central island; the Adamant Orb inside
    # the rocky ring by its north wall
    ("HOENN_ROUTE_128", 0, 59, 22, "HEART_SCALE"),
    ("HOENN_ROUTE_128", 0, 68, 26, "HEART_SCALE"),
    ("HOENN_ROUTE_128", 0, 47, 39, "HEART_SCALE"),
    ("HOENN_ROUTE_128", 0, 75, 13, "ADAMANT_ORB"),
    # Route 134: the largest island, east of the Carbos
    ("HOENN_ROUTE_134", 0, 52, 17, "HEART_SCALE"),
    ("HOENN_ROUTE_134", 0, 55, 14, "HEART_SCALE"),
    # Petalburg Woods: a break in the trees up north; the south-east corner below the ledge
    ("HOENN_PETALBURG_WOODS", None, 26, 6, "TINY_MUSHROOM"),
    ("HOENN_PETALBURG_WOODS", None, 44, 22, "TINY_MUSHROOM"),
    # Granite Cave: B1F's dead-end tunnel in the south and its east corner; B2F by the middle ladder, and the Everstone
    # inside the big rock (Emerald's own tile: walk into the rock)
    ("HOENN_GRANITE_CAVE", 2, 15, 22, "PARALYZE_HEAL"),
    ("HOENN_GRANITE_CAVE", 2, 29, 12, "X_DEFENSE"),
    ("HOENN_GRANITE_CAVE", 3, 13, 3, "SUPER_POTION"),
    ("HOENN_GRANITE_CAVE", 3, 15, 11, "EVERSTONE"),
    # Jagged Pass: between Expert Shelby and Hiker Eric
    ("HOENN_JAGGED_PASS", None, 15, 8, "FULL_HEAL"),
    # Shoal Cave: the Ice room's north-west corner (off the ice)
    ("HOENN_SHOAL_CAVE", 4, 4, 7, "ICE_HEAL"),
    # Cave of Origin: 1F north-east of the way down; B1F by the north stairs
    ("HOENN_CAVE_OF_ORIGIN", 1, 14, 16, "X_ATTACK"),
    ("HOENN_CAVE_OF_ORIGIN", 2, 11, 6, "REVIVE"),
]
PATCH = [   # (someone already on the map gets more to their event)
    # Petalburg Woods: ORAS's Devon researcher gives the Exp. Share; ours retired it, so a Lucky Egg (as Kanto; #22)
    ("HOENN_PETALBURG_WOODS", None, None, "Devon researcher",
     {"lines": ["I came looking for Shroomish, and that thug came after my papers! Thank you for stepping in.",
                "Here, take this. A Pokemon holding it learns faster from every battle."],
      "gift_item": {"LUCKY_EGG": 1}, "flag": "got_lucky_egg_hoenn",
      "done": ["Devon researcher: Thanks again! I'll get these papers back to the company safe and sound."]}),
]
DOUBLES = [   # (a pair's person-event battles, written into emerald.py: real doubles, as every ORAS pair; #5)
    ("HOENN_ROUTE_111", "Interviewers Gabby & Ty"),
    ("HOENN_ROUTE_118", "Interviewers Gabby & Ty"),
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
    for key, floor, room, text, ev in PATCH:
        m = maps.get(key)
        if not m:
            continue
        p = _part(m, floor, room)
        who = next((q for q in p.get("people") or [] if isinstance(q, dict) and q.get("text") == text), None)
        if who is None:
            print(ascii(f"  hoenn_canon: no {text} on {key}: left out"))
            continue
        who["event"] = dict(who.get("event") or {}, **ev)
    for key, name in DOUBLES:
        m = maps.get(key)
        for p in ((m.get("floors") or [m]) if m else []):
            for q in p.get("people") or []:
                b = (q.get("event") or {}).get("battle") if isinstance(q, dict) else None
                if isinstance(b, dict) and b.get("name") == name:
                    b["double"] = True
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
