# [REF-0095: Z-Moves and Terastal]
"""Z-Moves and Terastal (Jordan, 11-03), used like Mega Evolution: once you have the key item, the
battle's Z-MOVE / TERA button works in every region, once per battle.

Z-Moves: the Z-Ring comes with your first Alola trial (a Z-Crystal as its prize). A Pokemon holding a
Z-Crystal (given from the Bag, which keeps it, as in Sun / Moon; won from the Kahunas and Captains, or
bought in Alola's Poke Marts as you clear trials) can turn a damaging move of the crystal's type into its
Z-Move: the games' names, power from the move's (the games' table), it never misses, and no added
effects. Alola's Leaders use theirs too.

Terastal: the Tera Orb comes when you reach Paldea, and works there only (for now, Jordan 11-03).
Every Pokemon has a Tera Type (one of its own types, until changed): Terastallizing makes it that type
for the rest of the battle; its moves of its
old types keep their bonus, and a Tera Type it already had gets twice the bonus. 10 Tera Shards of a
type change a Pokemon's Tera Type (the games use 50); Paldea's Marts sell them. Paldea's Leaders
Terastallize their last Pokemon into their Gym's type.
"""
import random

TYPES = ("NORMAL", "FIRE", "WATER", "ELECTRIC", "GRASS", "ICE", "FIGHTING", "POISON", "GROUND", "FLYING",
         "PSYCHIC", "BUG", "ROCK", "GHOST", "DRAGON", "DARK", "STEEL", "FAIRY")
CRYSTAL = {"NORMAL": "NORMALIUM_Z", "FIRE": "FIRIUM_Z", "WATER": "WATERIUM_Z", "ELECTRIC": "ELECTRIUM_Z",
           "GRASS": "GRASSIUM_Z", "ICE": "ICIUM_Z", "FIGHTING": "FIGHTINIUM_Z", "POISON": "POISONIUM_Z",
           "GROUND": "GROUNDIUM_Z", "FLYING": "FLYINIUM_Z", "PSYCHIC": "PSYCHIUM_Z", "BUG": "BUGINIUM_Z",
           "ROCK": "ROCKIUM_Z", "GHOST": "GHOSTIUM_Z", "DRAGON": "DRAGONIUM_Z", "DARK": "DARKINIUM_Z",
           "STEEL": "STEELIUM_Z", "FAIRY": "FAIRIUM_Z"}
Z_MOVE = {"NORMAL": "Breakneck Blitz", "FIRE": "Inferno Overdrive", "WATER": "Hydro Vortex",
          "ELECTRIC": "Gigavolt Havoc", "GRASS": "Bloom Doom", "ICE": "Subzero Slammer",
          "FIGHTING": "All-Out Pummeling", "POISON": "Acid Downpour", "GROUND": "Tectonic Rage",
          "FLYING": "Supersonic Skystrike", "PSYCHIC": "Shattered Psyche", "BUG": "Savage Spin-Out",
          "ROCK": "Continental Crush", "GHOST": "Never-Ending Nightmare", "DRAGON": "Devastating Drake",
          "DARK": "Black Hole Eclipse", "STEEL": "Corkscrew Crash", "FAIRY": "Twinkle Tackle"}
Z_RING, TERA_ORB = "Z_RING", "TERA_ORB"
SHARDS_TO_CHANGE = 10
SHARD_PRICE = 300
# Crystals Alola's Marts sell, by the region's badges (the trials the games give them at).
CRYSTAL_SHOP = {1: ("WATERIUM_Z", "FIRIUM_Z", "GRASSIUM_Z"), 2: ("ELECTRIUM_Z", "GHOSTIUM_Z", "FAIRIUM_Z"),
                3: ("FLYINIUM_Z", "PSYCHIUM_Z", "BUGINIUM_Z"), 4: ("ICIUM_Z", "POISONIUM_Z", "STEELIUM_Z",
                                                                  "DRAGONIUM_Z")}
ITEM_TEXT = {Z_RING: "A ring that lets your Pokemon use Z-Moves (the Z-MOVE button in battle, once a battle).",
             TERA_ORB: "An orb that lets a Pokemon Terastallize into its Tera Type (the TERA button, once a battle)."}
for _t, _c in CRYSTAL.items():
    ITEM_TEXT[_c] = (f"A Z-Crystal: with the Z-Ring, it turns a {_t.title()}-type move into the Z-Move "
                     f"{Z_MOVE[_t]}.")
    ITEM_TEXT[f"{_t}_TERA_SHARD"] = (f"Use {SHARDS_TO_CHANGE} on a Pokemon to change its Tera Type to "
                                     f"{_t.title()}.")
KEY_ITEMS = {Z_RING, TERA_ORB} | set(CRYSTAL.values())


def shard_type(item):
    return item[:-len("_TERA_SHARD")] if str(item).endswith("_TERA_SHARD") else None


def z_power(power):
    """The games' Z-Move power from the move's power."""
    p = power or 0
    for limit, z in ((55, 100), (65, 120), (75, 140), (85, 160), (95, 175), (100, 180), (110, 185), (125, 190),
                     (130, 195)):
        if p <= limit:
            return z
    return 200


def crystals(story):
    """The Z-Crystals you have: in the Bag, or won as an Alola trial's prize (its 'badge')."""
    have = {k for k, q in story.inventory.items() if q and k in CRYSTAL.values()}
    have |= {b for blist in story.badges.values() for b in blist if b in CRYSTAL.values()}
    return have


CRYSTAL_TYPE = {c: t for t, c in CRYSTAL.items()}


def held_crystal_type(mon):
    """The type of the Z-Crystal this Pokemon holds, or None."""
    return CRYSTAL_TYPE.get(getattr(mon, "held_item", None))


def tera_type(mon):
    """The Pokemon's Tera Type (set when first needed: one of its own types)."""
    t = getattr(mon, "tera_type", None)
    if not t:
        own = [x for x in (getattr(mon, "types", None) or []) if x in TYPES]
        t = mon.tera_type = random.choice(own) if own else "NORMAL"
    return t


def give_key_items(story):
    """The Z-Ring with your first Alola trial, the Tera Orb in Paldea. Returns the lines to show."""
    lines = []
    inv = story.inventory
    for b in story.badges.get("ALOLA", []):  # a trial's crystal goes in the Bag, to give to a Pokemon
        if b in CRYSTAL_TYPE and not inv.get(b):
            inv[b] = 1
    if not inv.get(Z_RING) and (story.badges.get("ALOLA") or crystals(story)):
        inv[Z_RING] = 1
        lines += ["You received a Z-RING!", "With a Z-Crystal, your Pokemon can unleash a Z-Move once per battle!"]
    if not inv.get(TERA_ORB) and story.get_current_region() == "PALDEA":
        inv[TERA_ORB] = 1
        lines += ["You received the TERA ORB!", "Your Pokemon can Terastallize into their Tera Type once per battle!"]
    return lines


def mart_stock(story):
    """Alola's Marts: the Z-Crystals for its badges. Paldea's: Tera Shards."""
    region = story.get_current_region()
    if region == "ALOLA":
        badges = len(story.badges.get("ALOLA", []))
        have = crystals(story)
        return [c for n, cs in CRYSTAL_SHOP.items() if badges >= n for c in cs if c not in have]
    if region == "PALDEA":
        return [f"{t}_TERA_SHARD" for t in TYPES]
    return []
