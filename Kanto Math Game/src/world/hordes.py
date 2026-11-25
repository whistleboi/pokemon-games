"""Horde encounters (Jordan 11-23, Hoenn H3 DECISIONS #16: ORAS's hordes as real battles): five wild Pokemon at once,
your one Pokemon against all of them (src/states/battle_horde.py plays it).

A region lists its own hordes in its area data, per area:
    "horde_pool_percentages": "<POOL NAME>"   a pool in the area data, {"<species id>": percent, ...}; a key may name a
                                              mixed horde as "41+41+41+42+42" (the five, in order), else all five are
                                              that species
    "horde_rate": 0.15                        the share of this area's wild encounters that are hordes (0..1)
    "horde_levels": [lo, hi]                  optional: the hordes' levels (ORAS's hordes run lower than the singles);
                                              else each is levelled as any wild Pokemon here
"""
import random

HORDE_SIZE = 5


def rate(game, area_data):
    """This area's horde rate (0: none), only when its horde pool exists."""
    a = area_data or {}
    pool = a.get("horde_pool_percentages")
    if not pool or not (game.loader.area_data.get(pool) if isinstance(pool, str) else pool):
        return 0.0
    try:
        return max(0.0, min(1.0, float(a.get("horde_rate", 0.0))))
    except (TypeError, ValueError):
        return 0.0


def roll(game, area_data, rng=None):
    """True when this encounter is a horde."""
    r = rate(game, area_data)
    return r > 0 and (rng or random).random() < r


def pick(game, area_data, rng=None):
    """The horde's five species ids, from the area's horde pool."""
    rng = rng or random
    a = area_data or {}
    pool = a.get("horde_pool_percentages")
    table = game.loader.area_data.get(pool) if isinstance(pool, str) else pool
    keys = [k for k in (table or {}) if str(k).replace("+", "").isdigit()]
    if not keys:
        return []
    weights = [max(0.0, float(table[k] or 0)) for k in keys]
    key = rng.choices(keys, weights=weights)[0] if sum(weights) > 0 else rng.choice(keys)
    ids = [int(x) for x in str(key).split("+") if x]
    return [ids[i % len(ids)] for i in range(HORDE_SIZE)]


def make(game, area_key, area_data, rng=None):
    """Five wild Pokemon for a horde here, levelled as the area says ("horde_levels") or as its wild Pokemon are."""
    from src.pokemon.data import Pokemon
    from src.world import levels
    rng = rng or random
    a = area_data or {}
    out = []
    lv = a.get("horde_levels")
    for pid in pick(game, a, rng):
        raw = game.loader._fetch_raw(id_pool=[pid], area_data=a)
        if not raw or raw.get("id", 0) == 0:
            continue
        p = Pokemon(raw, game.assets, size_mult=3.125)
        if isinstance(lv, (list, tuple)) and len(lv) == 2:
            p.level = rng.randint(int(min(lv)), int(max(lv)))
            p.current_hp = p.get_max_hp()
        else:
            levels.set_wild(game, p, area_key)
        out.append(p)
    return out if len(out) == HORDE_SIZE else []


def one(game, area_key, area_data, rng=None):
    """One Pokemon out of a horde, for a place with no battles: the Safari Game (Hoenn's Safari Zone, Jordan 11-24 Q16 -
    ORAS's hordes on there: Doduo, Oddish, Psyduck at Lv 15, Oddish only that way). It walks the map as a single wild
    Pokemon and is caught with Safari Balls; None when the area has no horde pool."""
    from src.pokemon.data import Pokemon
    from src.world import levels
    rng = rng or random
    a = area_data or {}
    ids = pick(game, a, rng)
    if not ids:
        return None
    raw = game.loader._fetch_raw(id_pool=[ids[0]], area_data=a)
    if not raw or raw.get("id", 0) == 0:
        return None
    p = Pokemon(raw, game.assets, size_mult=3.125)
    lv = a.get("horde_levels")
    if isinstance(lv, (list, tuple)) and len(lv) == 2:
        p.level = rng.randint(int(min(lv)), int(max(lv)))
        p.current_hp = p.get_max_hp()
    else:
        levels.set_wild(game, p, area_key)
    return p
