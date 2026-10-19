# [REF-0070: Pokémon Contest Rules]
"""
Contest rules shared by the hall, the contest itself, the Bag and saves.

Conditions (Cool / Beauty / Cute / Smart / Tough) run 0-255 and are raised by
feeding Pokeblocks. Each Pokeblock also adds Sheen; once Sheen is full the
Pokémon won't eat any more, so a Pokémon can only be polished so far.
"""

CATEGORIES = ("COOL", "BEAUTY", "CUTE", "SMART", "TOUGH")
RANKS = ("NORMAL", "SUPER", "HYPER", "MASTER")

# Gym badges (in the hall's region) needed to enter each rank, as well as a
# win at the rank below in the same category.
RANK_BADGES = {"NORMAL": 0, "SUPER": 2, "HYPER": 4, "MASTER": 6}
RANK_PRIZE = {"NORMAL": 500, "SUPER": 1000, "HYPER": 2000, "MASTER": 4000}

# A move's contest category comes from its type.
TYPE_CATEGORY = {
    "FIRE": "COOL", "DRAGON": "COOL", "FLYING": "COOL", "ELECTRIC": "COOL",
    "WATER": "BEAUTY", "ICE": "BEAUTY", "FAIRY": "BEAUTY",
    "NORMAL": "CUTE", "GRASS": "CUTE", "BUG": "CUTE",
    "PSYCHIC": "SMART", "GHOST": "SMART", "DARK": "SMART",
    "ROCK": "TOUGH", "GROUND": "TOUGH", "FIGHTING": "TOUGH", "POISON": "TOUGH", "STEEL": "TOUGH",
}

CATEGORY_COLOR = {
    "COOL": (220, 60, 50), "BEAUTY": (60, 110, 230), "CUTE": (240, 120, 180),
    "SMART": (60, 170, 80), "TOUGH": (230, 190, 40),
}

POKEBLOCKS = {
    "RED_POKEBLOCK": "COOL", "BLUE_POKEBLOCK": "BEAUTY", "PINK_POKEBLOCK": "CUTE",
    "GREEN_POKEBLOCK": "SMART", "YELLOW_POKEBLOCK": "TOUGH",
}
POKEBLOCK_PRICE = 300
POKEBLOCK_GAIN = 20
POKEBLOCK_SHEEN = 12
MAX_CONDITION = 255
MAX_SHEEN = 255

# Feebas only evolves once its Beauty is this high (as in Ruby/Sapphire/Emerald).
FEEBAS_BEAUTY = 170

RIBBON_NAMES = {r: f"{r.title()} Rank" for r in RANKS}


def move_category(move_type):
    return TYPE_CATEGORY.get(str(move_type or "").upper(), "CUTE")


def new_condition():
    return {c: 0 for c in CATEGORIES}


def ribbon_id(category, rank):
    return f"{category}_{rank}"


def ribbon_label(ribbon):
    category, rank = ribbon.split("_", 1)
    return f"{category.title()} {rank.title()} Rank Ribbon"


def feed_pokeblock(pokemon, block):
    """Feed one Pokeblock. Returns (ate, messages)."""
    stat = POKEBLOCKS[block]
    name = pokemon.display_name.upper()
    if pokemon.sheen >= MAX_SHEEN:
        return False, [f"{name} is full of Pokeblocks and won't eat any more."]
    if pokemon.condition[stat] >= MAX_CONDITION:
        return False, [f"{name}'s {stat.title()} can't go any higher."]
    pokemon.condition[stat] = min(MAX_CONDITION, pokemon.condition[stat] + POKEBLOCK_GAIN)
    pokemon.sheen = min(MAX_SHEEN, pokemon.sheen + POKEBLOCK_SHEEN)
    lines = [f"{name} ate the Pokeblock!", f"{name}'s {stat.title()} rose to {pokemon.condition[stat]}!"]
    if pokemon.sheen >= MAX_SHEEN:
        lines.append(f"{name} looks completely satisfied. It won't want any more.")
    return True, lines


def feebas_ready(pokemon):
    """Feebas needs high Beauty to evolve; everything else is unaffected."""
    if pokemon.name.upper() != "FEEBAS":
        return True
    return pokemon.condition.get("BEAUTY", 0) >= FEEBAS_BEAUTY
