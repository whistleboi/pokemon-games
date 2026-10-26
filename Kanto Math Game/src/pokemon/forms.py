# [REF-0075: Mega Evolution and Primal Reversion]
"""
Battle-only form changes, Omega Ruby / Alpha Sapphire rules.

- Mega Evolution: the trainer needs a Key Stone (Mega Bracelet or Mega Ring) and the
  Pokemon's Mega Stone. Rayquaza needs no stone (it knows Dragon Ascent).
- Primal Reversion: Groudon with the Red Orb or Kyogre with the Blue Orb.
- The player chooses when with the MEGA / PRIMAL battle button. Only one Pokemon per
  side can Mega Evolve or Primal Revert in a battle.
- Mega Rayquaza, Primal Groudon and Primal Kyogre bring their own extreme weather.

Forms come from assets/mega_forms.json (stats, types, item, sprite name); sprites live
in sprites/pokemon/mega (back/, shiny/, back/shiny/). Everything reverts after battle.
"""
import json
import os

import pygame

KEY_STONES = ("MEGA_BRACELET", "MEGA_RING")
RAYQUAZA = 384
# Pokemon that bring extreme weather in their battle form.
FORM_WEATHER = {(383, "primal"): "HARSH_SUN", (382, "primal"): "HEAVY_RAIN", (384, "mega"): "STRONG_WINDS"}

_FORMS = None


def all_forms(assets):
    global _FORMS
    if _FORMS is None:
        path = os.path.join(assets.assets_dir, "mega_forms.json")
        try:
            with open(path, encoding="utf-8") as f:
                _FORMS = json.load(f)
        except OSError:
            _FORMS = {}
    return _FORMS


def forms_for(assets, species_id):
    return all_forms(assets).get(str(species_id), [])


def mega_stones(assets):
    """Every Mega Stone item name (orbs excluded)."""
    return sorted({f["item"] for fs in all_forms(assets).values() for f in fs
                   if f.get("item") and f["form"] != "primal"})


def stone_for(assets, species_id):
    return [f["item"] for f in forms_for(assets, species_id) if f["form"] != "primal" and f.get("item")]


def item_label(item):
    return item.replace("_", " ").title()


def has_key_stone(inventory):
    return any(inventory.get(k, 0) > 0 for k in KEY_STONES)


def player_form(assets, pokemon, inventory, form_used):
    """The form the player's Pokemon can change into right now (MEGA/PRIMAL button), or None."""
    if form_used or is_changed(pokemon) or pokemon.form != "normal":
        return None
    for f in forms_for(assets, pokemon.id):
        if f["form"] == "primal":
            if inventory.get(f["item"], 0) > 0:
                return f
            continue
        if not has_key_stone(inventory):
            continue
        if pokemon.id == RAYQUAZA or inventory.get(f["item"], 0) > 0:
            return f
    return None


def opponent_form(assets, pokemon, form_used):
    """Foes change form on entering battle, only when flagged (a trainer's Mega Pokemon or a Primal boss)."""
    if form_used or is_changed(pokemon) or pokemon.form != "normal":
        return None
    for f in forms_for(assets, pokemon.id):
        if f["form"] == "primal" and getattr(pokemon, "primal_ready", False):
            return f
        if f["form"] != "primal" and getattr(pokemon, "mega_ready", False):
            return f
    return None


def is_changed(pokemon):
    return hasattr(pokemon, "_form_state")


def _load(assets, sub, fname, shiny):
    base = os.path.join(assets.mega_sprites_dir, sub) if sub else assets.mega_sprites_dir
    for folder in ([os.path.join(base, "shiny")] if shiny else []) + [base]:
        path = os.path.join(folder, fname)
        if os.path.exists(path):
            return pygame.image.load(path).convert_alpha()
    return None


def apply_form(assets, pokemon, form):
    """Change into a Mega/Primal form for this battle. Returns the announcement lines."""
    pokemon._form_state = {k: getattr(pokemon, k) for k in
                           ("types", "base_stats", "display_name", "form", "image", "back_image", "sidebar_image")}
    old_name = pokemon.display_name.upper()
    pokemon.types = list(form["types"])
    pokemon.base_stats = dict(form["stats"])
    pokemon.display_name = form["name"]
    pokemon.form = form["form"]
    for attr, sub in (("image", ""), ("back_image", "back"), ("sidebar_image", "")):
        current = getattr(pokemon, attr)
        img = _load(assets, sub, form["sprite"], pokemon.is_shiny)
        if current is not None and img is not None:
            setattr(pokemon, attr, pygame.transform.scale(img, current.get_size()))
    if form["form"] == "primal":
        return [f"{old_name}'s Primal Reversion!", f"It reverted to its primal form: {form['name']}!"]
    if pokemon.id == RAYQUAZA:
        return [f"{old_name} is reacting to the Key Stone's power!",
                f"{old_name} has Mega Evolved into {form['name']}!"]
    return [f"{old_name} is reacting to the Key Stone!", f"{old_name} has Mega Evolved into {form['name']}!"]


def revert_form(pokemon):
    state = getattr(pokemon, "_form_state", None)
    if state is None:
        return
    for k, v in state.items():
        setattr(pokemon, k, v)
    del pokemon._form_state
    # HP went up to stage 3 levels while transformed: keep the same share of HP afterwards.
    scale = getattr(pokemon, "_form_hp", None)
    if scale:
        before, during = scale
        if pokemon.current_hp > 0 and during:
            pokemon.current_hp = max(1, min(before, round(pokemon.current_hp * before / during)))
        del pokemon._form_hp


# Dynamax raid bosses have double HP, as in the games.
DYNAMAX_HP_MULT = 2


def is_dynamax(pokemon):
    return bool(getattr(pokemon, "raid_stage", None))


def is_powered(pokemon):
    """Mega Evolved, Primal Reverted, or a Dynamax/Gigantamax raid boss."""
    return bool(pokemon) and (is_changed(pokemon) or is_dynamax(pokemon))


def form_weather(pokemon):
    return FORM_WEATHER.get((pokemon.id, pokemon.form)) if pokemon else None


def mark_trainer_team(team, trainer_info):
    """A trainer's `mega` (species id, or a list when the team depends on the player's starter)
    Mega Evolves when it comes out. `movesets` gives canon moves by species id ({"25": ["THUNDERBOLT",
    ...]}); moves.ensure_moves turns them into the real set."""
    mega = (trainer_info or {}).get("mega")
    megas = {int(m) for m in (mega if isinstance(mega, list) else [mega] if mega else [])}
    for p in team:
        if p and p.id in megas:
            p.mega_ready = True
            break
    sets = (trainer_info or {}).get("movesets") or {}
    for p in team:
        if p and str(p.id) in sets:
            p.preset_moves = list(sets[str(p.id)])
            p.moves = []
    return team
