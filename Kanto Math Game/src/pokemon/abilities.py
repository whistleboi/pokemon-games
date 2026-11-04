# [REF-0090: Abilities]
"""Abilities (Jordan, 11-03): every Pokemon has one, as in the games, from Pokemon Journeys' PBS
data (Pokemon Essentials) and PokeAPI for the newer ones (dev/builders/import_species_data.py).

A Pokemon keeps an ability *slot* (Pokemon.ability_slot: 0 or 1 = its species' abilities, 2 = the
hidden one), so evolving or Mega Evolving gives it the new species' ability in the same slot.
Hidden abilities: about 5% of new Pokemon have theirs (HIDDEN_CHANCE); a parent passes its hidden
ability to an egg 60% of the time (the Daycare).

Data:
  assets/abilities.json     {KEY: {"name", "desc"}}
  assets/species_data.json  {id: {"abilities", "hidden", "gender", "egg_groups"}}
  assets/move_flags.json    {MOVE: ["contact", "punch", "bite", "sound", "pulse", "bomb", "powder", "dance"]}
The battle effects are in src/states/battle_abilities.py.
"""
import json
import os
import random

HIDDEN_SLOT = 2
HIDDEN_CHANCE = 0.05


def _load(game, name):
    cache = game.__dict__.setdefault("_ability_data", {})
    if name not in cache:
        try:
            with open(os.path.join(game.assets.assets_dir, name), encoding="utf-8") as f:
                cache[name] = json.load(f)
        except (OSError, ValueError, TypeError):
            cache[name] = {}
    return cache[name]


def table(game):
    return _load(game, "abilities.json")


def species_table(game):
    return _load(game, "species_data.json")


def species(game, pid):
    """The species (or form) entry: abilities, hidden, gender, egg groups ({} if unknown)."""
    data = species_table(game)
    entry = data.get(str(pid))
    if entry is None:
        form = game.loader.area_data.get("FORM_MAP", {}).get(str(pid)) if getattr(game, "loader", None) else None
        entry = data.get(str((form or {}).get("id", "")), {})
    return entry or {}


def roll_slot(rng=random):
    """A new Pokemon's slot: hidden about 1 time in 20, else either of the two."""
    return HIDDEN_SLOT if rng.random() < HIDDEN_CHANCE else rng.randint(0, 1)


def key_for(game, pid, slot):
    """The ability a Pokemon of this species/form has in this slot (the hidden slot falls back to
    a normal one when the species has no hidden ability)."""
    entry = species(game, pid)
    normal = entry.get("abilities") or []
    if slot == HIDDEN_SLOT and entry.get("hidden"):
        return entry["hidden"]
    if not normal:
        return entry.get("hidden")
    return normal[int(slot or 0) % len(normal)]


def ability(game, mon):
    """The ability this Pokemon has now (its battle form's, e.g. a Mega's)."""
    if mon is None:
        return None
    override = getattr(mon, "ability_override", None)
    if override:
        return override
    slot = getattr(mon, "ability_slot", None)
    if slot is None:
        slot = mon.ability_slot = roll_slot()
    return key_for(game, mon.id, slot)


def name(game, key):
    if not key:
        return "None"
    return (table(game).get(key) or {}).get("name") or key.title()


def desc(game, key):
    return (table(game).get(key) or {}).get("desc") or ""


def is_hidden(game, mon):
    entry = species(game, mon.id)
    return getattr(mon, "ability_slot", 0) == HIDDEN_SLOT and bool(entry.get("hidden"))


def choices(game, pid):
    """(normal abilities, hidden) of a species (the Pokedex page)."""
    entry = species(game, pid)
    return list(entry.get("abilities") or []), entry.get("hidden")


def move_flags(game, move):
    return set(_load(game, "move_flags.json").get(str(move).upper(), ()))
