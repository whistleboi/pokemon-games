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


# The Orange Islands' colour-only forms (Pinkan, Valencia) Mega Evolve like their species (Jordan 11-23), in their
# own colours: sprites/pokemon/mega/<dex>_<variant>_mega.png (dev/builders/recolor_form_followers.py), else the Mega's.
COLOUR_VARIANTS = ("pinkan", "valencia", "shadow")   # (Orre's Shadow forms Mega Evolve too, Jordan 11-24 - their stats swapped)


def _species(pokemon):
    """The species whose Megas a Pokemon has: a colour variant's (Pinkan Beedrill 9106 -> 15), else its own id."""
    if getattr(pokemon, "form", "normal") in COLOUR_VARIANTS:
        try:
            return int(getattr(pokemon, "meta_id", None) or pokemon.id)
        except (TypeError, ValueError):
            pass
    return pokemon.id






def item_label(item):
    return item.replace("_", " ").title()


def has_key_stone(inventory):
    return any(inventory.get(k, 0) > 0 for k in KEY_STONES)


def player_form(assets, pokemon, inventory, form_used):
    """The form the player's Pokemon can change into right now (MEGA/PRIMAL button), or None."""
    if form_used or is_changed(pokemon) or pokemon.form not in ("normal",) + COLOUR_VARIANTS:
        return None
    for f in forms_for(assets, _species(pokemon)):
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
    if form_used or is_changed(pokemon) or pokemon.form not in ("normal",) + COLOUR_VARIANTS:
        return None
    for f in forms_for(assets, _species(pokemon)):
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
    variant = pokemon.form if pokemon.form in COLOUR_VARIANTS else None
    species = _species(pokemon)
    pokemon.types = list(form["types"])
    pokemon.base_stats = dict(form["stats"])
    if variant == "shadow":   # (a Shadow keeps its reverse stats as a Mega: Attack <-> Defense, Sp. Atk <-> Sp. Def - Jordan 11-24)
        st = pokemon.base_stats
        st["ATTACK"], st["DEFENSE"] = st["DEFENSE"], st["ATTACK"]
        st["SPECIAL-ATTACK"], st["SPECIAL-DEFENSE"] = st["SPECIAL-DEFENSE"], st["SPECIAL-ATTACK"]
    pokemon.display_name = form["name"]
    if variant and form["name"].upper().startswith("MEGA "):   # (MEGA PINKAN BEEDRILL)
        pokemon.display_name = f"MEGA {variant.upper()} {form['name'][5:]}"
    pokemon.form = form["form"]
    for attr, sub in (("image", ""), ("back_image", "back"), ("sidebar_image", "")):
        current = getattr(pokemon, attr)
        img = None
        if variant:   # (its own colours; none drawn -> keep its current picture rather than the species' colours)
            img = _load(assets, sub, f"{species}_{variant}_{form['form']}.png", pokemon.is_shiny)
            img = img if img is not None else current
        img = img if img is not None else _load(assets, sub, form["sprite"], pokemon.is_shiny)
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




def form_weather(pokemon):
    return FORM_WEATHER.get((pokemon.id, pokemon.form)) if pokemon else None


# Rotom's appliance forms (Platinum, Black 2): Electric plus the appliance's type, each with its own move (assets/
# pokemon_movesets.json "479_<form>"; sprites in altform/). Unova 11-24: the PWT's sets and the Shopping Mall's stockroom.
ROTOM = 479
ROTOM_FORMS = {"heat": "OVERHEAT", "wash": "HYDRO-PUMP", "frost": "BLIZZARD", "fan": "AIR-SLASH", "mow": "LEAF-STORM"}


def rotom_change(game, slot_index, form):
    """Change the Rotom in your party's slot to form ("heat", "wash", "frost", "fan", "mow", or "normal"): its types,
    stats and picture change, the old form's own move goes and the new form's own move comes in (in its place, else the
    last slot; back to normal, Thunder Shock if it would know nothing). Returns lines, or None if that's no Rotom."""
    story = game.story_manager
    party = story.player_team
    p = party[slot_index] if 0 <= slot_index < len(party) else None
    if p is None or int(getattr(p, "id", 0) or 0) != ROTOM:
        return None
    form = form if form in ROTOM_FORMS else "normal"
    old = list(getattr(p, "moves", None) or [])
    at = next((i for i, m in enumerate(old) if m in ROTOM_FORMS.values()), None)
    moves = [m for m in old if m not in ROTOM_FORMS.values()]
    new_move = ROTOM_FORMS.get(form)
    if new_move:
        if at is not None:
            moves.insert(min(at, len(moves)), new_move)
        elif len(moves) < 4:
            moves.append(new_move)
        else:
            moves[-1] = new_move
    if not moves:
        moves = ["THUNDER-SHOCK"]
    rec = story._pokemon_record(p)
    rec["form"] = form
    rec["moves"] = moves
    party[slot_index] = story._load_pokemon(rec, game.loader)
    party[slot_index].moves = list(moves)
    lines = [f"{p.display_name} changed its form!"]
    if new_move:
        lines.append(f"It learned {new_move.replace('-', ' ').title()}!")
    return lines


# Kyurem's fused forms (Black 2 / White 2): Black Kyurem (Teravolt, Fusion Bolt / Freeze Shock) and White Kyurem (Turboblaze,
# Fusion Flare / Ice Burn); data "646_black" / "646_white", sprites in altform/. Unova 11-24: the Giant Chasm's boss; later the
# DNA Splicers. form_extras gives any Pokemon built in such a form its form's own ability and moves.
KYUREM = 646
KYUREM_FORMS = {"black": ("TERAVOLT", ["FUSION-BOLT", "FREEZE-SHOCK", "DRAGON-CLAW", "SCARY-FACE"]),
                "white": ("TURBOBLAZE", ["FUSION-FLARE", "ICE-BURN", "DRAGON-PULSE", "SCARY-FACE"])}


def form_extras(p, form):
    """What a form brings beyond its data: Kyurem's fused ability and signature moves, Rotom's appliance move."""
    if p is None or not form or form == "normal":
        return p
    pid = int(getattr(p, "id", 0) or 0)
    if pid == KYUREM and form in KYUREM_FORMS:
        ab, moves = KYUREM_FORMS[form]
        p.ability_override = ab
        if not getattr(p, "preset_moves", None):
            p.preset_moves = list(moves)
            p.moves = []
    elif pid == ROTOM and form in ROTOM_FORMS and not getattr(p, "preset_moves", None):
        p.preset_moves = [ROTOM_FORMS[form]]
    p.form = form
    return p


def _apply_forms(team, forms_list):
    """A trainer team's forms by slot ("forms": ["heat", None, ...]): each Pokemon rebuilt in that form (the PWT's Rotom)."""
    from src.ui import theme
    game = theme.GAME
    if game is None:
        return
    from src.pokemon.data import Pokemon
    for i, f in enumerate(forms_list or []):
        if i < len(team) and team[i] is not None and f and f != "normal":
            p = team[i]
            raw = game.loader.fetch_specific(int(p.id), f)
            if not raw:
                continue
            new = Pokemon(raw, game.assets, size_mult=getattr(p, "size_mult", 3.125))
            new.level = p.level
            new.current_hp = new.get_max_hp()
            if getattr(p, "preset_moves", None):
                new.preset_moves = list(p.preset_moves)
            team[i] = form_extras(new, f)   # (its form's own ability and moves: Rotom's appliance move, Kyurem's fusion)


def mark_trainer_team(team, trainer_info):
    """A trainer's `mega` (species id, or a list when the team depends on the player's starter)
    Mega Evolves when it comes out. `movesets` gives canon moves by species id ({"25": ["THUNDERBOLT",
    ...]}); moves.ensure_moves turns them into the real set."""
    _apply_forms(team, (trainer_info or {}).get("forms"))   # (forms by slot, first: everything below marks the rebuilt ones)
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
    # Moves by team slot ("team_moves": one list per Pokemon, in team order), for a team with the
    # same species twice and different moves (Norman's two Slaking, ORAS).
    for p, moves in zip(team, (trainer_info or {}).get("team_moves") or []):
        if p and moves:
            p.preset_moves = list(moves)
            p.moves = []
    # Held items by team slot: "team_items" (Orre's discs, 11-20) and "held" (the Frontier Brains', Orange 5.7's
    # trainers' Berries; 11-22: the data had them, nothing gave them out)
    for p, item in [pi for key in ("team_items", "held") for pi in zip(team, (trainer_info or {}).get(key) or [])]:
        if p and item:
            p.held_item = item
    return team
