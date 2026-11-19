"""Collection cases (Jordan, 11-18): a family of collectibles kept in one Bag slot, opened to browse them. Every family
with five or more kinds gets one, plus the region collectibles Jordan named (Plates, Memories, Drives, Wings, Fossils,
Ogerpon's masks), Mega Stones, Z-Crystals, Mints, Exp. Candies and Tera Shards.

A case isn't an item you're handed: it's there as soon as you own one thing that goes in it, and the Bag tells you so
the first time you open it after (story_flags "case:<KEY>"). Linked regions share one Bag, so their cases are shared too.
The Bag shows the case as one card in the pocket its contents belong in; tapping it lists what's inside, used as usual
(src/states/systems/bag.py)."""
import re

STONES = ("FIRE_STONE", "WATER_STONE", "THUNDER_STONE", "LEAF_STONE", "MOON_STONE", "SUN_STONE", "SHINY_STONE",
          "DUSK_STONE", "DAWN_STONE", "ICE_STONE")
GLASS_FLUTES = ("BLUE_FLUTE", "YELLOW_FLUTE", "RED_FLUTE", "BLACK_FLUTE", "WHITE_FLUTE")
CONTEST_SCARVES = ("RED_SCARF", "BLUE_SCARF", "PINK_SCARF", "GREEN_SCARF", "YELLOW_SCARF")
EV_WINGS = ("HEALTH", "MUSCLE", "RESIST", "GENIUS", "CLEVER", "SWIFT", "PRETTY")   # (Unova's: the Silver and Rainbow Wings are key items)
OGERPON_MASKS = ("WELLSPRING_MASK", "HEARTHFLAME_MASK", "CORNERSTONE_MASK")
_TM = re.compile(r"^(TM\d{3}|TM_\w+|HM_\w+)$")


def _mega_stones():
    """Every Mega Stone the game knows (the item of each non-Primal form), made once."""
    global _MEGA
    if _MEGA is None:
        from src.ui import theme
        if theme.GAME is None:   # (not loaded yet: ask again later)
            return set()
        try:
            from src.pokemon import forms
            allf = forms.all_forms(theme.GAME.assets)
            _MEGA = {f.get("item") for fl in allf.values() for f in fl if f.get("form") != "primal" and f.get("item")}
        except Exception:
            _MEGA = set()
    return _MEGA


_MEGA = None


def _z(key):
    from src.pokemon import zpower
    return key in zpower.CRYSTAL_TYPE


def _pokeblock(key):
    try:
        from src.pokemon.contest import POKEBLOCKS
    except Exception:
        return key.endswith("_POKEBLOCK")
    return key in POKEBLOCKS


# (case key, its name, what goes in it, the pocket it sits in), in the order they're listed
CASES = [
    ("TM_CASE", "TM Case", lambda k: bool(_TM.match(k)), "KEY ITEMS"),
    ("Z_CRYSTAL_CASE", "Z-Crystal Case", _z, "KEY ITEMS"),
    ("MEGA_STONE_CASE", "Mega Stone Case", lambda k: k in _mega_stones() or k.endswith(("ITE_X", "ITE_Y")), "ITEMS"),
    ("STONE_CASE", "Evolution Stone Case", lambda k: k in STONES, "ITEMS"),
    ("PLATE_CASE", "Plate Case", lambda k: k.endswith("_PLATE"), "ITEMS"),
    ("MEMORY_CASE", "Memory Case", lambda k: k.endswith("_MEMORY"), "ITEMS"),
    ("DRIVE_CASE", "Drive Case", lambda k: k.endswith("_DRIVE"), "ITEMS"),
    ("WING_CASE", "Wing Case", lambda k: k.endswith(("_WING", "_FEATHER")) and k.split("_")[0] in EV_WINGS, "ITEMS"),
    ("FOSSIL_CASE", "Fossil Case", lambda k: k.endswith("_FOSSIL") or k == "OLD_AMBER", "ITEMS"),
    ("MASK_CASE", "Mask Case", lambda k: k in OGERPON_MASKS, "ITEMS"),
    ("MINT_CASE", "Mint Case", lambda k: k.endswith("_MINT"), "ITEMS"),
    ("CANDY_CASE", "Exp. Candy Case", lambda k: k.startswith("EXP_CANDY"), "ITEMS"),
    ("SHARD_CASE", "Tera Shard Case", lambda k: k.endswith("_TERA_SHARD"), "ITEMS"),
    ("GEM_CASE", "Gem Case", lambda k: k.endswith("_GEM"), "ITEMS"),
    ("INCENSE_CASE", "Incense Case", lambda k: k.endswith("_INCENSE"), "ITEMS"),
    ("APRICORN_BOX", "Apricorn Box", lambda k: k.endswith("_APRICORN"), "ITEMS"),
    ("POKEBLOCK_CASE", "Pokeblock Case", _pokeblock, "ITEMS"),
    ("SCARF_CASE", "Contest Scarf Case", lambda k: k in CONTEST_SCARVES, "ITEMS"),
    ("FLUTE_CASE", "Glass Flute Case", lambda k: k in GLASS_FLUTES, "ITEMS"),
]
BY_KEY = {c[0]: c for c in CASES}
WHAT = {"TM_CASE": "TMs and HMs", "Z_CRYSTAL_CASE": "Z-Crystals", "MEGA_STONE_CASE": "Mega Stones",
        "STONE_CASE": "evolution stones", "PLATE_CASE": "Plates", "MEMORY_CASE": "Memories", "DRIVE_CASE": "Drives",
        "WING_CASE": "Wings", "FOSSIL_CASE": "Fossils", "MASK_CASE": "masks", "MINT_CASE": "Mints",
        "CANDY_CASE": "Exp. Candies", "SHARD_CASE": "Tera Shards", "GEM_CASE": "Gems", "INCENSE_CASE": "Incenses",
        "APRICORN_BOX": "Apricorns", "POKEBLOCK_CASE": "Pokeblocks", "SCARF_CASE": "Contest scarves",
        "FLUTE_CASE": "glass flutes"}


def case_of(key):
    """The case an item goes in, or None."""
    if not isinstance(key, str) or key in BY_KEY:
        return None
    for ck, _n, test, _p in CASES:
        try:
            if test(key):
                return ck
        except Exception:
            continue
    return None


def is_case(key):
    return key in BY_KEY


def name(case):
    return BY_KEY[case][1]


def pocket(case):
    return BY_KEY[case][3]


def describe(case, inventory):
    n = len(contents(case, inventory))
    return f"Holds your {WHAT.get(case, 'items')}: {n} kind{'s' if n != 1 else ''} inside. Tap to open it."


def contents(case, inventory):
    """[(item, qty)] in a case, in name order."""
    return sorted(((k, q) for k, q in (inventory or {}).items() if q and q > 0 and case_of(k) == case), key=lambda kq: kq[0])


def owned(inventory):
    """The cases with anything in them, in list order."""
    have = {case_of(k) for k, q in (inventory or {}).items() if q and q > 0}
    return [c[0] for c in CASES if c[0] in have]


def new_cases(story):
    """Cases you have now that you haven't been told about; marks them told. [(case, name)]."""
    flags = story.story_flags
    out = []
    for c in owned(story.inventory):
        if not flags.get("case:" + c):
            flags["case:" + c] = True
            out.append(c)
    return out
