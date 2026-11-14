# [REF-0092: TMs]
"""TMs (Jordan, 11-03): Sword/Shield's 100 (TM00-TM99) in every region, reusable (Gen 5 on).
Data: assets/tms.json and assets/tm_learners.json (dev/builders/build_tms.py).

How you get them, so a region's 100 can all be had by its League (each region's Bag is its own):
- the Poke Mart sells a TM once the region has its tier's badges (tiers 0-8, weak to strong), cheaply;
- every Gym Leader, Elite Four member and Champion gives one (its type when there's one left);
- route trainers often give one too (TRAINER_CHANCE).
Hoenn (Jordan, 11-14) has its own: Omega Ruby / Alpha Sapphire's numbering TM01-TM100 and Emerald's own after TM100
(assets/tms_hoenn.json, dev/builders/build_hoenn_tms.py). Their items are HTM01... (shown "TM01 ..."), keys of their own so
a Bag shared between regions can hold both; Hoenn's Marts sell Hoenn's, the other regions' Marts their own.
Unlocking (Jordan, 11-04): a TM in the Bag puts its move in the move pool of every Pokemon that can learn
it (src/pokemon/moves.py move_pool), to pick in the Summary's MOVES. Using it from the Bag also sets the
move while the Pokemon knows fewer than four.
"""
import json
import os
import random

TRAINER_CHANCE = 0.35
# Regions whose maps carry their games' own TMs (on the ground, from people) and whose Leaders give their own (Jordan,
# 11-13: Hoenn, from Emerald / ORAS): no random TMs from battles there.
REAL_TM_REGIONS = {"HOENN"}
LEADER_CLASSES = ("GYM_LEADER", "ELITE_FOUR", "CHAMPION")


def _load(game, name):
    cache = game.__dict__.setdefault("_tm_data", {})
    if name not in cache:
        try:
            with open(os.path.join(game.assets.assets_dir, name), encoding="utf-8") as f:
                cache[name] = json.load(f)
        except (OSError, ValueError, TypeError):
            cache[name] = {}
    return cache[name]


HOENN = "HOENN"


def table(game):
    """Every TM: Sword/Shield's (TM00-TM99, story gifts TM100 on) and Hoenn's own (HTM01-...)."""
    cache = game.__dict__.setdefault("_tm_data", {})
    if "_all" not in cache:
        cache["_all"] = dict(_load(game, "tms.json"), **_load(game, "tms_hoenn.json"))
    return cache["_all"]


def is_tm(item):
    if not isinstance(item, str):
        return False
    if item.startswith("HTM"):   # (Hoenn's own)
        return len(item) >= 5 and item[3:].isdigit()
    return len(item) >= 4 and item.startswith("TM") and item[2:].isdigit()  # (TM00-TM99; story gifts TM100 on)


def is_hoenn(item):
    return isinstance(item, str) and item.startswith("HTM")


def hoenn_key(game, move):
    """Hoenn's TM for a move (its HTM key), or None."""
    return next((k for k, d in _load(game, "tms_hoenn.json").items() if d.get("move") == move), None)


def _here(game):
    """The TMs this region's Marts deal in: Hoenn's own in Hoenn, Sword/Shield's elsewhere."""
    hoenn = str(game.story_manager.get_current_region() or "").upper() == HOENN
    return {k: d for k, d in table(game).items() if is_hoenn(k) == hoenn}


def info(game, item):
    return table(game).get(item) or {}


def move_of(game, item):
    return info(game, item).get("move")


def label(game, item):
    """'TM24 Snore' (Hoenn's HTM34 too: 'TM34 Shock Wave')."""
    move = move_of(game, item)
    shown = item[1:] if is_hoenn(item) else item
    return f"{shown} {move.replace('-', ' ').title()}" if move else shown


def price(game, item):
    return info(game, item).get("price", 3000)


def _species(game, mon):
    pid = int(mon.id)
    if pid > 1025:
        form = game.loader.area_data.get("FORM_MAP", {}).get(str(pid)) or {}
        pid = int(form.get("id", pid))
    return pid


def can_learn(game, mon, item):
    move = move_of(game, item)
    return bool(move) and _species(game, mon) in set(_load(game, "tm_learners.json").get(move, ()))


def knows(mon, move):
    return move in (getattr(mon, "moves", None) or [])


def works_on(game, mon, item):
    """ABLE in the party list: it can learn the move and hasn't set it yet."""
    return can_learn(game, mon, item) and not knows(mon, move_of(game, item))


def teach(game, mon, item):
    """Teach the TM's move. Returns the lines to show."""
    from src.pokemon import moves as movelib
    move = move_of(game, item)
    name, label_ = mon.display_name, move.replace("-", " ").title()
    if not can_learn(game, mon, item):
        return [f"{name} can't learn {label_}."]
    if knows(mon, move):
        return [f"{name} already knows {label_}."]
    movelib.ensure_moves(game, mon)
    pool = movelib.move_pool(game, mon)  # (the TM's move is in it already: it unlocks it)
    if move not in pool:
        pool.append(move)
    if len(mon.moves) < movelib.MAX_MOVES:
        mon.moves.append(move)
        return [f"{name} learned {label_}!"]
    return [f"{name} can use {label_}!", "It's in its move pool: pick its four moves in its Summary (MOVES)."]


def owned(story):
    return {k for k, q in story.inventory.items() if q and is_tm(k)}


def mart_stock(game, badges):
    """The TMs the Mart sells with this many badges (the ones you don't have yet)."""
    have = owned(game.story_manager)
    have |= {hoenn_key(game, move_of(game, k)) or k for k in have}   # (one you have under the other numbering: no need to buy it)
    return [k for k, d in _here(game).items() if d.get("tier", 8) <= badges and k not in have and not d.get("gift")
            and not d.get("shop_only")]   # (shop_only: sold only where a shop lists it, Lilycove's TM Corner)


def reward(game, badges, trainer_class, team_types=(), rng=random):
    """A TM a battle win gives (None if none): every Leader / Elite Four / Champion gives one (of
    its type when there's one left), route trainers TRAINER_CHANCE of the time."""
    if trainer_class in (None, "WILD"):
        return None
    if game.story_manager.get_current_region() in REAL_TM_REGIONS:
        return None
    leader = trainer_class in LEADER_CLASSES
    if not leader and rng.random() >= TRAINER_CHANCE:
        return None
    have = owned(game.story_manager)
    cap = min(8, badges + (2 if leader else 1))
    pool = [k for k, d in _here(game).items() if k not in have and d.get("tier", 8) <= cap and not d.get("gift") and not d.get("shop_only")]
    if not pool:
        pool = [k for k, d in _here(game).items() if k not in have and not d.get("gift") and not d.get("shop_only")]  # (story gifts are only given)
    if not pool:
        return None
    if leader:
        typed = [k for k in pool if info(game, k).get("type") in set(team_types)]
        if typed:  # the Leader's own type, the strongest one on offer
            return max(typed, key=lambda k: (info(game, k).get("tier", 0), k))
    return rng.choice(sorted(pool))
