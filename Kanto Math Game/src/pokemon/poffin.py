# [REF-0072: Berries and Poffins]
"""
Berries and Poffin cooking (Diamond/Pearl/Platinum).

Each berry has flavors (values from Gen 4). Cooking adds the berries' flavors
together and scales them by how well the batter was stirred; each flavor then
raises one contest condition when the Poffin is eaten:
  Spicy -> Cool, Dry -> Beauty, Sweet -> Cute, Bitter -> Smart, Sour -> Tough.
Smoother Poffins (better cooking) add less Sheen, so a Pokémon can eat more.
"""
from src.pokemon.contest import MAX_CONDITION, MAX_SHEEN

FLAVORS = ("SPICY", "DRY", "SWEET", "BITTER", "SOUR")
FLAVOR_CONDITION = {"SPICY": "COOL", "DRY": "BEAUTY", "SWEET": "CUTE", "BITTER": "SMART", "SOUR": "TOUGH"}
FLAVOR_COLOR = {"SPICY": (220, 60, 50), "DRY": (60, 110, 230), "SWEET": (240, 120, 180),
                "BITTER": (60, 170, 80), "SOUR": (230, 190, 40)}

BERRIES = {
    # One flavor
    "CHERI_BERRY": {"SPICY": 10}, "CHESTO_BERRY": {"DRY": 10}, "PECHA_BERRY": {"SWEET": 10},
    "RAWST_BERRY": {"BITTER": 10}, "ASPEAR_BERRY": {"SOUR": 10},
    # Two flavors
    "RAZZ_BERRY": {"SPICY": 10, "DRY": 10}, "BLUK_BERRY": {"DRY": 10, "SWEET": 10},
    "NANAB_BERRY": {"SWEET": 10, "BITTER": 10}, "WEPEAR_BERRY": {"BITTER": 10, "SOUR": 10},
    "PINAP_BERRY": {"SPICY": 10, "SOUR": 10},
    # Strong and rare
    "SPELON_BERRY": {"SPICY": 30, "DRY": 10}, "PAMTRE_BERRY": {"DRY": 30, "SWEET": 10},
    "WATMEL_BERRY": {"SWEET": 30, "BITTER": 10}, "DURIN_BERRY": {"BITTER": 30, "SOUR": 10},
    "BELUE_BERRY": {"SPICY": 10, "SOUR": 30},
}
BASIC_BERRIES = ["CHERI_BERRY", "CHESTO_BERRY", "PECHA_BERRY", "RAWST_BERRY", "ASPEAR_BERRY"]
BERRY_PRICE = 200
MAX_BERRIES_PER_POFFIN = 3
MAX_POFFINS = 100

# Cooking: three stirring stages, two stirs each, with less time as the batter thickens.
COOK_STAGES = (("The batter is runny. Stir gently!", 10000),
               ("The batter is thickening. Stir faster!", 8000),
               ("Almost done! Stir as fast as you can!", 6000))
STIRS_PER_STAGE = 2
MILD_LEVEL = 50


def berry_name(item):
    return item.replace("_BERRY", "").title() + " Berry"


def berry_label(item):
    flavors = BERRIES[item]
    return "/".join(f.title() for f in sorted(flavors, key=lambda f: -flavors[f]))


def cook(berries, good, quick, mistakes):
    """
    berries: berry item keys used. good: stirs answered right in time.
    quick: of those, how many were fast. mistakes: spills (wrong) + burns (too slow).
    Returns a poffin dict {name, flavors, smooth, level}.
    """
    if len(set(berries)) < len(berries):
        return _foul()  # the same berry twice spoils the batter, as in the games
    total = {f: 0 for f in FLAVORS}
    for b in berries:
        for f, v in BERRIES[b].items():
            total[f] += v
    mult = (0.6 + 0.1 * good + 0.05 * quick) * (1 + 0.1 * (len(berries) - 1))
    flavors = {}
    for f, v in total.items():
        if v:
            value = int(v * mult + 0.5) - 2 * mistakes
            if value > 0:
                flavors[f] = value
    if not flavors:
        return _foul()
    smooth = max(5, 25 - 2 * good - quick)
    return {"name": _poffin_name(flavors), "flavors": flavors, "smooth": smooth, "level": max(flavors.values())}


def _foul():
    return {"name": "Foul Poffin", "flavors": {"SPICY": 2, "DRY": 2, "SOUR": 2}, "smooth": 25, "level": 2}


def _poffin_name(flavors):
    level = max(flavors.values())
    if level >= MILD_LEVEL:
        return "Mild Poffin"
    ranked = sorted(flavors, key=lambda f: -flavors[f])
    if len(ranked) == 1:
        return f"{ranked[0].title()} Poffin"
    if len(ranked) == 2:
        return f"{ranked[0].title()}-{ranked[1].title()} Poffin"
    if len(ranked) == 3:
        return "Rich Poffin"
    return "Overripe Poffin"


def poffin_label(poffin):
    return f"{poffin['name'].replace(' Poffin', '')} Lv{poffin['level']}"


def poffin_color(poffin):
    flavors = poffin["flavors"]
    if poffin["name"] in ("Foul Poffin",):
        return (110, 100, 90)
    if len(flavors) >= 3:
        return (170, 120, 200)
    return FLAVOR_COLOR[max(flavors, key=flavors.get)]


def feed_poffin(pokemon, poffin):
    """Feed one Poffin. Returns (ate, messages)."""
    name = pokemon.display_name.upper()
    if pokemon.sheen >= MAX_SHEEN:
        return False, [f"{name} is full and won't eat any more."]
    lines = [f"{name} ate the {poffin['name']}!"]
    for flavor, value in poffin["flavors"].items():
        stat = FLAVOR_CONDITION[flavor]
        before = pokemon.condition[stat]
        pokemon.condition[stat] = min(MAX_CONDITION, before + value)
        if pokemon.condition[stat] > before:
            lines.append(f"{stat.title()} rose to {pokemon.condition[stat]}!")
    pokemon.sheen = min(MAX_SHEEN, pokemon.sheen + poffin["smooth"])
    if pokemon.sheen >= MAX_SHEEN:
        lines.append(f"{name} looks completely satisfied. It won't want any more.")
    return True, lines
