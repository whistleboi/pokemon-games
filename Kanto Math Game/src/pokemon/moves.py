# [REF-0082: Moves]
"""
Each Pokemon knows up to four moves, chosen from its level-up learnset
(assets/pokemon_levels.json) using real move data (assets/moves.json, from PokeAPI).

Only moves that work in this game are learned:
  - damaging moves (power > 0, not one-hit KOs or self-KO moves),
  - weather moves (Rain Dance, Sunny Day, Sandstorm, Hail/Snowscape),
  - status moves that inflict burn, paralysis, poison, sleep or freeze.

A new Pokemon knows the last four of those it learned by its level, like the games.
On level-up it learns new ones; with four already it forgets its weakest move.
"""
import json
import os

WEATHER_MOVES = {"RAIN-DANCE": "RAIN", "SUNNY-DAY": "SUN", "SANDSTORM": "SAND", "HAIL": "SNOW", "SNOWSCAPE": "SNOW"}
STATUSES = ("burn", "paralysis", "poison", "sleep", "freeze")
STATUS_LABEL = {"burn": "BRN", "paralysis": "PAR", "poison": "PSN", "sleep": "SLP", "freeze": "FRZ"}
SELF_KO = {"EXPLOSION", "SELF-DESTRUCT", "MISTY-EXPLOSION", "MEMENTO", "FINAL-GAMBIT", "HEALING-WISH"}
FALLBACK = "TACKLE"
MAX_MOVES = 4


def table(game):
    cache = getattr(game, "_move_table", None)
    if cache is None:
        path = os.path.join(game.assets.assets_dir, "moves.json")
        try:
            with open(path, encoding="utf-8") as f:
                cache = json.load(f)
        except OSError:
            cache = {}
        game._move_table = cache
    return cache


def info(game, name):
    """Move data with its name (TACKLE stand-in if unknown)."""
    d = table(game).get(name) or table(game).get(FALLBACK) or {"type": "NORMAL", "power": 40, "accuracy": 100,
                                                                "category": "PHYSICAL", "priority": 0}
    return dict(d, name=name)


def usable(d):
    """Can this game use the move?"""
    if d.get("name") in SELF_KO or d.get("category_meta") == "ohko":
        return False
    if (d.get("power") or 0) > 0:
        return True
    if d.get("name") in WEATHER_MOVES:
        return True
    return d.get("category") == "STATUS" and d.get("ailment") in STATUSES and d.get("category_meta") == "ailment"


def _species(poke):
    from src.pokemon.evolution import base_id
    return base_id(poke)


def learnable(game, poke, up_to=None, after=0):
    """Usable level-up moves learned in (after, up_to], oldest first."""
    from src.pokemon.evolution import learnset
    lv = poke.level if up_to is None else up_to
    out = []
    for learn_level, name in sorted(learnset(game, _species(poke)), key=lambda x: x[0]):
        if after < max(1, learn_level) <= lv and name not in out and usable(info(game, name)):
            out.append(name)
    return out


def default_moves(game, poke):
    """The last four usable moves learned by its level (Tackle if none)."""
    moves = learnable(game, poke)
    return moves[-MAX_MOVES:] or [FALLBACK]


def ensure_moves(game, poke):
    if not getattr(poke, "moves", None):
        poke.moves = default_moves(game, poke)
    return poke.moves


def move_value(game, poke, name):
    """How useful a move is to keep: STAB damage, then status, then weather."""
    d = info(game, name)
    power = d.get("power") or 0
    if power:
        return power * (1.5 if d["type"] in (poke.types or []) else 1.0) * ((d.get("accuracy") or 100) / 100)
    return 35 if name not in WEATHER_MOVES else 30


def learn_new_moves(game, poke, old_level):
    """Learn moves reached between old_level and its level. Returns message lines."""
    ensure_moves(game, poke)
    lines = []
    for name in learnable(game, poke, after=old_level):
        if name in poke.moves:
            continue
        label = name.replace("-", " ")
        if len(poke.moves) < MAX_MOVES:
            poke.moves.append(name)
            lines.append(f"{poke.display_name.upper()} learned {label}!")
            continue
        weakest = min(poke.moves, key=lambda m: move_value(game, poke, m))
        if move_value(game, poke, name) <= move_value(game, poke, weakest):
            continue  # not worth replacing anything
        poke.moves[poke.moves.index(weakest)] = name
        lines.append(f"{poke.display_name.upper()} forgot {weakest.replace('-', ' ')} and learned {label}!")
    return lines
