"""Swarms (Jordan 11-19, the Sinnoh re-audit: "build swarms"), Platinum's way: once you have the National Pokedex, each
day one place has a swarm - its two commonest grass slots (40%) are that place's swarm Pokemon all day (the same pick for
the whole day, by the real date). The little sibling at the Professor's assistant's house in Sandgem saw it on the TV
news and tells you (common.py's event "swarm_news").

SWARMS: Platinum's own table (each zone's swarm species in the game's encounter data, pl_enc_data: the 22 places where
it differs from the usual grass; kanto_handoff/sinnoh_map_tools/out/canon). A region gets swarms by adding its table.
An entry is a species (in the grass) or (kind, species): "surf", "good_rod", "super_rod" - SoulSilver's swarms are in
the water too (11-19: Johto's, from the game file's swarm slots where they differ from the place's usual Pokemon;
announced on the radio's Pokemon Talk)."""
import datetime
import random

SWARMS = {
    "SINNOH": {"SINNOH_ROUTE_201": 84, "SINNOH_ROUTE_202": 263, "SINNOH_ROUTE_203": 104, "SINNOH_ROUTE_206": 246,
               "SINNOH_ROUTE_207": 231, "SINNOH_ROUTE_208": 206, "SINNOH_ROUTE_209": 209, "SINNOH_ROUTE_214": 325,
               "SINNOH_ROUTE_215": 96, "SINNOH_ROUTE_217": 225, "SINNOH_ROUTE_218": 100, "SINNOH_ROUTE_221": 83,
               "SINNOH_ROUTE_222": 300, "SINNOH_ROUTE_224": 177, "SINNOH_ROUTE_225": 296, "SINNOH_ROUTE_226": 98,
               "SINNOH_ROUTE_227": 327, "SINNOH_ROUTE_228": 374, "SINNOH_ROUTE_229": 127, "SINNOH_ROUTE_230": 222,
               "VALLEY_WINDWORKS": 309, "ETERNA_FOREST": 287},
    # Johto (11-22: SoulSilver's whole Johto list, from Bulbapedia's area pages; sources/johto): "fish" = on any rod, HGSS's way
    "JOHTO": {"DARK_CAVE": 206, "JOHTO_ROUTE_32": ("fish", 211), "JOHTO_ROUTE_34": 280, "JOHTO_ROUTE_35": 193, "JOHTO_ROUTE_38": 209,
              "JOHTO_ROUTE_44": ("fish", 223), "JOHTO_ROUTE_45": 333, "JOHTO_ROUTE_47": 132, "MT_MORTAR": 183,
              "KANTO_ROUTE_27": ("surf", 370), "VIOLET_CITY": ("fish", 340)},
    # Kanto (11-23, Jordan: SoulSilver's 9 Kanto swarms, "from the start"): read from the SoulSilver file's swarm slots
    # (johto_map_tools jcanon_rom.wild: R01 R03 R09 R12 R13 W19 R25 D46 = Viridian Forest, T06 = Vermilion). The Gen 1
    # lock still holds: a swarm of a region not played yet doesn't come out (adjust).
    "KANTO": {"KANTO_ROUTE_1": 261, "KANTO_ROUTE_3": 316, "KANTO_ROUTE_9": 303, "KANTO_ROUTE_12": ("fish", 369),
              "KANTO_ROUTE_13": 113, "KANTO_ROUTE_19": ("surf", 366), "KANTO_ROUTE_25": 427, "VIRIDIAN_FOREST": 401,
              "VERMILLION_CITY": ("surf", 278)},
    # Hoenn (11-24, main M6): Emerald's own mass outbreaks, told on TV (Bulbapedia "Mass outbreak", Gen III: Emerald's
    # Seedot / Nuzleaf / Skitty; the Surskit rows are Ruby and Sapphire's). After the Hall of Fame, as in Emerald
    # (Hoenn's National Pokedex comes then too); half the grass encounters are the outbreak's (Emerald's 50%).
    "HOENN": {"HOENN_ROUTE_102": 273, "HOENN_ROUTE_114": 274, "HOENN_ROUTE_116": 300, "HOENN_ROUTE_117": 273,
              "HOENN_ROUTE_120": 273},
}
FROM_START = {"KANTO"}   # (regions whose swarms don't wait for the National Pokedex: Jordan 11-23 for Kanto)
PLACE = {"VALLEY_WINDWORKS": "the Valley Windworks", "ETERNA_FOREST": "Eterna Forest"}
SHARE = 0.4   # (Platinum: the swarm takes the grass table's two 20% slots)
SHARE_BY = {"HOENN": 0.5}   # (Emerald: half the encounters while an outbreak is on)


def place_name(area):
    if area in PLACE:
        return PLACE[area]
    if "_ROUTE_" in area:
        return "Route " + area.rsplit("_", 1)[1]
    return area.replace("_", " ").title()


def today(story, region, day=None):
    """(area, species) of today's swarm in this region, or None (no table, or no National Pokedex yet)."""
    table = SWARMS.get(str(region or "").upper())
    if not table or (str(region or "").upper() not in FROM_START and not story.story_flags.get("unlocked_national_dex")):
        return None
    day = day or datetime.date.today().isoformat()
    area = random.Random(f"swarm@{str(region).upper()}@{day}").choice(sorted(table))
    return area, _entry(table[area])[1]


def _entry(e):
    return tuple(e) if isinstance(e, (list, tuple)) else ("grass", e)


def kind_today(story, region, day=None):
    """How today's swarm is met: "grass", "surf", "fish" (any rod), "good_rod" or "super_rod" (None: no swarm)."""
    sw = today(story, region, day)
    return _entry(SWARMS[str(region).upper()][sw[0]])[0] if sw else None


def adjust(game, pool, area_key, kind="grass"):
    """The pool (grass, surf or a rod's) with today's swarm in it (40% of encounters), when this area has it that way."""
    story = game.story_manager
    region = story.area_region(area_key) if hasattr(story, "area_region") else story.get_current_region()
    sw = today(story, region)
    k = kind_today(story, region)
    if not sw or sw[0] != area_key or not pool or not (k == kind or (k == "fish" and str(kind).endswith("_rod"))):
        return pool
    from src.world import regional_forms
    if not regional_forms.species_allowed(game, int(sw[1])):   # (Kanto's lock: no Pokemon of a region not played yet, swarm or not)
        return pool
    pool = dict(pool)
    sp = str(sw[1])
    rest = sum(v for k, v in pool.items() if k != sp)
    share = SHARE_BY.get(str(region or "").upper(), SHARE)
    pool[sp] = max(1, round(rest * share / (1 - share)))
    return pool


def news(game, region="SINNOH"):
    """What the TV news said today, or None."""
    story = game.story_manager
    sw = today(story, region)
    if not sw:
        return None
    name = str((game.loader.fetch_specific(int(sw[1])) or {}).get("name", "")).replace("-", " ").title()
    return [f"The TV news said there's a huge swarm of {name} at {place_name(sw[0])} today!",
            "Hurry, before it's over! It'd be great for your Pokedex!"]
