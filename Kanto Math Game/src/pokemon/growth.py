"""Real XP: each species' growth curve (from the games, via PokeAPI) and the Gen 7 battle XP
formula. Leveling is sped up by one constant, XP_BOOST, so kids level up easily while the
curves and the formula stay true to the games."""
import json
import os

XP_BOOST = 3  # every XP gain is multiplied by this (the games' own numbers are 1x)

_data = None


def _load():
    global _data
    if _data is None:
        path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "growth_rates.json")
        try:
            with open(path, encoding="utf-8") as f:
                _data = json.load(f)
        except (OSError, ValueError):
            _data = {"rates": {}, "species": {}}
    return _data


def rate(species_id):
    return _load()["species"].get(str(int(species_id)), "medium")


def total_xp(species_id, level):
    """Total XP a species has at the start of `level` (1-100)."""
    table = _load()["rates"].get(rate(species_id))
    level = max(1, min(100, int(level)))
    if not table:
        return level ** 3  # medium-fast, if the data is missing
    return table[level - 1]


def level_cost(species_id, level):
    """XP needed to go from `level` to the next one (0 at Lv 100)."""
    if level >= 100:
        return 0
    return max(1, total_xp(species_id, level + 1) - total_xp(species_id, level))


def battle_xp(base_yield, foe_level, my_level, trainer=False):
    """XP for knocking out a foe, Gen 7 formula (scaled by the level gap), times XP_BOOST:
        (a x b x L / 5) x ((2L + 10) / (L + Lp + 10)) ^ 2.5 + 1,  a = 1.5 against trainers."""
    a = 1.5 if trainer else 1.0
    L, Lp = max(1, foe_level), max(1, my_level)
    xp = (a * max(1, base_yield) * L / 5) * ((2 * L + 10) / (L + Lp + 10)) ** 2.5 + 1
    return max(1, int(xp * XP_BOOST))
