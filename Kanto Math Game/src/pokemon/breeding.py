# [REF-0093: Genders, the Day Care and Eggs]
"""Genders, the Pokemon Day Care and Eggs (Jordan, 11-03).

- Gender: from the species' ratio (assets/species_data.json "gender": female eighths 0-8, -1 genderless),
  set when the Pokemon is made and kept (Pokemon.gender "M" / "F" / None).
- The Day Care (one in each region where the games have one; Orre's in Agate Village and Paldea's in
  Mesagoza are this game's own): leave two Pokemon; if they can breed, an Egg is ready after
  EGG_TRAVELS trips (a "trip" = travelling to another area). Compatible: one male and one female that
  share an Egg Group, or any breedable Pokemon with Ditto; never two Ditto, a Pokemon from the
  Undiscovered group, or an Egg.
- The Egg: the bottom of the mother's line (or the non-Ditto parent's), in her regional form; 3 IVs
  passed down from the parents; her hidden ability 60% of the time if she has it. It hatches after
  HATCH_TRAVELS trips in the party; Flame Body, Magma Armor or Steam Engine in the party makes each trip
  count twice (as in the games, they halve the time). An Egg can't battle (it always has 0 HP).
"""
import random

from src.pokemon import abilities as ablib

EGG_TRAVELS = 20
HATCH_TRAVELS = 30
HATCH_HELPERS = {"FLAMEBODY", "MAGMAARMOR", "STEAMENGINE"}
DITTO = 132
# Evolutions only a regional form has: their Eggs hatch in that form (Sirfetch'd: Galarian Farfetch'd).
REGIONAL_ONLY = {862: "galarian", 863: "galarian", 864: "galarian", 865: "galarian", 866: "galarian",
                 867: "galarian", 903: "hisuian", 904: "hisuian", 980: "paldean"}


# ---------------------------------------------------------------- gender
def roll_gender(game, pid, rng=random):
    rate = ablib.species(game, pid).get("gender", 4)
    if rate is None or rate < 0:
        return None
    return "F" if rng.random() < rate / 8 else "M"


def gender_of(game, mon):
    """'M', 'F' or None (genderless); set on first look for Pokemon from older saves."""
    if mon is None:
        return None
    if not hasattr(mon, "gender") or mon.gender == "?":
        mon.gender = roll_gender(game, mon.id)
    return mon.gender


SYMBOL = {"M": ("♂", (64, 132, 232)), "F": ("♀", (232, 84, 120))}


# ---------------------------------------------------------------- compatibility
def species_id(game, mon):
    entry = ablib.species(game, mon.id)
    return int(entry.get("form_of") or mon.id)


def egg_groups(game, mon):
    return set(ablib.species(game, mon.id).get("egg_groups") or ["UNDISCOVERED"])


def compatible(game, a, b):
    """(can breed, why not) for two Day Care Pokemon."""
    if not a or not b:
        return False, "It needs a second Pokemon."
    if getattr(a, "is_egg", False) or getattr(b, "is_egg", False):
        return False, "An Egg can't be left at the Day Care."
    ga, gb = egg_groups(game, a), egg_groups(game, b)
    if "UNDISCOVERED" in ga or "UNDISCOVERED" in gb:
        return False, "One of them can't have Eggs."
    a_ditto, b_ditto = "DITTO" in ga, "DITTO" in gb
    if a_ditto and b_ditto:
        return False, "Two Ditto can't have an Egg."
    if a_ditto or b_ditto:
        return True, ""
    sa, sb = gender_of(game, a), gender_of(game, b)
    if sa is None or sb is None:
        return False, "A Pokemon with no gender can only have an Egg with Ditto."
    if sa == sb:
        return False, "They're both " + ("male." if sa == "M" else "female.")
    if not ga & gb:
        return False, "They don't share an Egg Group."
    return True, ""


def mother_of(game, a, b):
    """The parent whose species the Egg is: the female, or the one that isn't Ditto."""
    if "DITTO" in egg_groups(game, a):
        return b
    if "DITTO" in egg_groups(game, b):
        return a
    return a if gender_of(game, a) == "F" else b


# ---------------------------------------------------------------- the Egg
def egg_species(game, mother):
    """Our id for what hatches: the bottom of the mother's line, in her regional form if it has one."""
    base = species_id(game, mother)
    root = int(ablib.species(game, base).get("egg") or base)
    form = str(getattr(mother, "form", "normal") or "normal").lower()
    if base in REGIONAL_ONLY:
        form = REGIONAL_ONLY[base]
    if form not in ("normal", "") and getattr(game, "loader", None):
        for fid, m in game.loader.area_data.get("FORM_MAP", {}).items():
            if int(m.get("id", 0)) == root and str(m.get("form")).lower() == form:
                return int(fid)
    return root


def make_egg(game, a, b, rng=random):
    """The Egg two Day Care Pokemon leave: a Pokemon that hasn't hatched yet."""
    from src.pokemon.data import Pokemon
    mother = mother_of(game, a, b)
    pid = egg_species(game, mother)
    egg = Pokemon(game.loader.fetch_specific(pid), game.assets, size_mult=2.5)
    egg.level = 1
    egg.xp = 0
    # three IVs from the parents
    for stat in rng.sample(list(Pokemon.IV_KEYS), 3):
        egg.ivs[stat] = rng.choice((a, b)).ivs.get(stat, egg.ivs[stat])
    egg.floor_ivs()
    if ablib.is_hidden(game, mother) and rng.random() < 0.6:
        egg.ability_slot = ablib.HIDDEN_SLOT
    elif egg.ability_slot == ablib.HIDDEN_SLOT:
        egg.ability_slot = rng.randint(0, 1)
    egg.gender = roll_gender(game, pid, rng)
    egg.caught_region = game.story_manager.get_current_region()
    egg.moves, egg.move_pool = [], []
    make_unhatched(game, egg)
    return egg


def make_unhatched(game, egg, steps=0):
    """Dress a Pokemon as an Egg (the egg sprite, the name EGG, no HP)."""
    egg.is_egg = True
    egg.egg_steps = steps
    egg.hatch_name = egg.display_name
    egg.display_name = "Egg"
    sprite = egg_sprite(game)
    if sprite is not None:
        egg.image = sprite
        egg.sidebar_image = sprite


def egg_sprite(game):
    import os
    import pygame
    cache = game.__dict__.setdefault("_egg_sprite", {})
    if "img" not in cache:
        cache["img"] = None
        path = os.path.join(game.assets.pokemon_sprites_dir, "egg.png")
        try:
            cache["img"] = pygame.image.load(path).convert_alpha()
        except (pygame.error, FileNotFoundError):
            pass
    return cache["img"]


def hatch_hint(egg):
    """What the Summary says about an Egg, by how close it is to hatching."""
    left = HATCH_TRAVELS - getattr(egg, "egg_steps", 0)
    if left > 20:
        return "It looks like this Egg will take a long time to hatch."
    if left > 10:
        return "What will hatch from this? It doesn't seem close to hatching."
    if left > 4:
        return "It moves around inside sometimes. It must be close to hatching."
    return "Sounds can be heard coming from inside! It will hatch soon!"


# ---------------------------------------------------------------- the Day Care
def daycare(story):
    """This region's Day Care: {"mons": [up to 2 Pokemon], "steps": trips so far, "egg": ready?}."""
    return story._store().setdefault("daycare", {"mons": [], "steps": 0, "egg": False})


def on_travel(game, rng=random):
    """A trip to another area: the Day Care counts towards an Egg, Eggs in the party towards
    hatching. Returns (party index of an Egg ready to hatch or None, lines to show)."""
    story = game.story_manager
    lines = []
    dc = daycare(story)
    mons = dc["mons"]
    if len(mons) == 2 and not dc["egg"] and compatible(game, *mons)[0]:
        dc["steps"] += 1
        if dc["steps"] >= EGG_TRAVELS:
            dc["egg"], dc["steps"] = True, 0
            lines.append("The Day Care couple found an Egg! Go and collect it at the Day Care.")
    team = story.player_team
    helpers = any(p and not getattr(p, "is_egg", False) and ablib.ability(game, p) in HATCH_HELPERS for p in team)
    ready = None
    for i, p in enumerate(team):
        if p is not None and getattr(p, "is_egg", False):
            p.egg_steps = getattr(p, "egg_steps", 0) + (2 if helpers else 1)
            if p.egg_steps >= HATCH_TRAVELS and ready is None:
                ready = i
    return ready, lines
