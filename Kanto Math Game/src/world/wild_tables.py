"""A place's own wild Pokemon, slot by slot, as its game has them (11-20: Black 2 / White 2's, read from the game file by
kanto_handoff/unova_map_tools/uwild.py into the area's "wild_tables").

    "wild_tables": {season or "ALL": {kind: [[species, form, chance, lo, hi], ...]}}

kinds: "grass" (tall grass), "dark" (dark grass: stronger), "rustle" (rustling grass, a phenomenon), "surf", "ripple"
(rippling water, a phenomenon), "fish", "fish_ripple" (fishing in rippling water). Seasons follow src/world/seasons.py
(Unova's month-by-month calendar). Each slot keeps its own level range, as the games do; the chances are Gen 5's.
Forms the game has no data for (Blue-Striped Basculin) come as the usual form. Both versions' Pokemon are in one table
whichever version you play (Jordan 11-20: the version changes the story only): dev/builders/unova_wild.py merged()."""
import random

from src.world import seasons

KINDS = ("grass", "dark", "rustle", "surf", "ripple", "fish", "fish_ripple")


def tables(area):
    return (area or {}).get("wild_tables") or {}


def season_table(area, season=None):
    """This season's tables (the "ALL" set when the place never changes)."""
    t = tables(area)
    if not t:
        return {}
    return t.get(season or seasons.current_season()) or t.get("ALL") or {}


def has(area, kind):
    return bool(season_table(area).get(kind))


def slots(area, kind):
    return season_table(area).get(kind) or []


def pick(area, kind, rng=None):
    """(species, level) from the slot the dice land on, else None."""
    sl = slots(area, kind)
    if not sl:
        return None
    rng = rng or random
    roll = rng.uniform(0, sum(s[2] for s in sl))
    for sp, _form, chance, lo, hi in sl:
        roll -= chance
        if roll <= 0:
            return int(sp), rng.randint(int(lo), int(max(lo, hi)))
    sp, _form, _c, lo, hi = sl[-1]
    return int(sp), rng.randint(int(lo), int(max(lo, hi)))


def pool(area, kind, season=None):
    """{species: chance} for one kind this season (the Pokedex's area list, the Habitat List, the species audit)."""
    out = {}
    for sp, _form, chance, _lo, _hi in (season_table(area, season).get(kind) or []):
        out[str(sp)] = out.get(str(sp), 0) + chance
    return out
