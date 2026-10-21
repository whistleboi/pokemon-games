# [REF-0079: Opponent levels]
"""
Levels for everything the player fights.

- Gyms: each region's gyms in their canonical order, with ace levels close to the games.
  The rest of a leader's team sits a few levels below the ace.
- Elite Four and Champion: per-region ladders.
- Wild Pokemon and route trainers: the area's level from assets/area_levels.json (real
  encounter levels from the games; an area's own `"level"` key overrides it).
- Legendaries use fixed levels; Max Raid bosses take their level from the star rank.
"""
import random

from src.pokemon.balance import is_legendary

GYM_ORDER = {
    "KANTO": ["PEWTER_CITY", "CERULEAN_CITY", "VERMILLION_CITY", "CELADON_CITY", "FUCHSIA_CITY",
              "SAFFRON_CITY", "CINNABAR_ISLAND", "VIRIDIAN_CITY"],
    "JOHTO": ["VIOLET_CITY", "AZALEA_TOWN", "GOLDENROD_CITY", "ECRUTEAK_CITY", "CIANWOOD_CITY",
              "OLIVINE_CITY", "MAHOGANY_TOWN", "BLACKTHORN_CITY"],
    "HOENN": ["RUSTBORO_CITY", "DEWFORD_TOWN", "MAUVILLE_CITY", "LAVARIDGE_TOWN", "PETALBURG_CITY",
              "FORTREE_CITY", "MOSSDEEP_CITY", "SOOTOPOLIS_CITY"],
    "SINNOH": ["OREBURGH_CITY", "ETERNA_CITY", "VEILSTONE_CITY", "PASTORIA_CITY", "HEARTHOME_CITY",
               "CANALAVE_CITY", "SNOWPOINT_CITY", "SUNYSHORE_CITY"],
    "UNOVA": ["STRIATON_CITY", "NACRENE_CITY", "CASTELIA_CITY", "NIMBASA_CITY", "DRIFTVEIL_CITY",
              "MISTRALTON_CITY", "ICIRRUS_CITY", "OPELUCID_CITY"],
    "KALOS": ["SANTALUNE_CITY", "CYLLAGE_CITY", "SHALOUR_CITY", "COUMARINE_CITY", "LUMIOSE_CITY",
              "LAVERRE_CITY", "ANISTAR_CITY", "SNOWBELLE_CITY"],
    "ALOLA": ["HAUOLI_CITY", "HEAHEA_CITY", "MALIE_CITY", "SEAFOLK_VILLAGE"],
    "GALAR": ["TURFFIELD", "HULBURY", "MOTOSTOKE", "STOW_ON_SIDE", "BALLONLEA", "CIRCHESTER",
              "SPIKEMUTH", "HAMMERLOCKE"],
    "PALDEA": ["CORTONDO", "ARTAZON", "LEVINCIA", "CASCARRAFA", "MEDALI", "MONTENEVERA",
               "ALFORNADA", "GLASEADO"],
    # The Orange Islands (the anime's Orange League): post-game, after the Kanto and Johto titles.
    "ORANGE": ["MIKAN_ISLAND", "NAVEL_ISLAND", "TROVITA_ISLAND", "KUMQUAT_ISLAND"],
}
# Ace level of each gym, then (Elite Four first, last) and the Champion's ace.
# Johto is HeartGold/SoulSilver x1.26 (JOHTO_SCALE), so Lance's ace matches Kanto's Champion (63).
JOHTO_SCALE = 63 / 50
GYM_ACE = {
    "KANTO": [14, 21, 24, 29, 37, 43, 47, 50], "JOHTO": [16, 21, 24, 32, 39, 44, 43, 52],
    "HOENN": [14, 16, 21, 28, 30, 35, 45, 46], "SINNOH": [14, 22, 30, 32, 36, 39, 44, 50],
    "UNOVA": [14, 20, 23, 27, 31, 35, 39, 43], "KALOS": [12, 25, 32, 34, 37, 42, 48, 54],
    "ALOLA": [12, 27, 39, 48], "GALAR": [20, 24, 25, 36, 38, 42, 46, 48],
    "PALDEA": [15, 17, 24, 30, 36, 42, 45, 48],
    "ORANGE": [62, 66, 69, 72],
}
ELITE_FOUR = {"KANTO": (54, 60), "JOHTO": (53, 59), "HOENN": (50, 53), "SINNOH": (53, 59),
              "UNOVA": (48, 50), "KALOS": (58, 62), "ALOLA": (54, 57), "GALAR": (52, 58),
              "PALDEA": (57, 60)}
CHAMPION_ACE = {"KANTO": 63, "JOHTO": 63, "HOENN": 59, "SINNOH": 62, "UNOVA": 54, "KALOS": 66,
                "ALOLA": 60, "GALAR": 65, "PALDEA": 62,
                "ORANGE": 76}
START_LEVEL = 3

# Legendaries: the box legends and their peers are Lv 70, mythicals and the rest Lv 50.
BOX_LEGENDS = {150, 249, 250, 382, 383, 384, 483, 484, 487, 643, 644, 646, 716, 717, 718, 791, 792, 800,
               888, 889, 890, 898, 1007, 1008, 1024}
MYTHICAL_HIGH = {386: 80, 493: 80, 151: 60, 251: 60, 385: 60}
RAID_LEVELS = {1: 15, 2: 25, 3: 35, 4: 50, 5: 65}

_AREA_LEVELS = {}


def _area_levels(game):
    """assets/area_levels.json: wild levels from the real games (PokeAPI encounter data),
    hand-set where there was none (Paldea, story-only areas), towns from their neighbours."""
    key = id(game.loader)
    if key not in _AREA_LEVELS:
        import json
        import os
        path = os.path.join(game.assets.assets_dir, "area_levels.json")
        try:
            with open(path, encoding="utf-8") as f:
                _AREA_LEVELS[key] = json.load(f)
        except OSError:
            _AREA_LEVELS[key] = {}
    return _AREA_LEVELS[key]


def gym_aces(region):
    return GYM_ACE.get(region, [12, 18, 24, 30, 36, 42, 46, 50])


def area_level(game, area_key):
    """An area's wild level (an area's own "level" key wins)."""
    area = game.loader.area_data.get("STORY_PROGRESSION", {}).get(area_key, {})
    if area.get("level"):
        return int(area["level"])
    return int(_area_levels(game).get(area_key, START_LEVEL + 2))


def wild_level(game, area_key):
    return max(2, area_level(game, area_key) + random.randint(-2, 1))


def trainer_level(game, area_key, boss=False):
    return area_level(game, area_key) + (4 if boss else random.randint(1, 3))


def legendary_level(pid):
    pid = int(pid)
    if pid in MYTHICAL_HIGH:
        return MYTHICAL_HIGH[pid]
    return 70 if pid in BOX_LEGENDS else 50


def boss_level(game, area_key, pid):
    """Area bosses: legendaries at their fixed level, others a little above the area."""
    if is_legendary(pid):
        return legendary_level(pid)
    return area_level(game, area_key) + 5


def gym_team_levels(region, area_key, size, role):
    """Levels for a gym/league team, ending on the ace. role: leader, trainer, elite, champion."""
    order = GYM_ORDER.get(region, [])
    if role == "champion":
        ace = CHAMPION_ACE.get(region, 60)
    elif role == "elite":
        ace = ELITE_FOUR.get(region, (50, 55))[0]
    elif area_key in order:
        ace = gym_aces(region)[order.index(area_key)]
        if role == "trainer":
            ace -= 4
    else:
        ace = 30
    return [max(2, ace - (size - 1 - i) * 2) for i in range(size)]


LEVEL_CAP_MODES = ("STORY", "OBEDIENCE", "NONE")
LEVEL_CAP_TEXT = {
    "STORY": ("STORY", "Can't level past the next Gym Leader's ace"),
    "OBEDIENCE": ("OBEDIENCE", "High-level Pokemon may ignore you until you earn badges"),
    "NONE": ("OFF", "Level freely, like the original games"),
}


def cap_mode(story):
    return getattr(story, "level_cap_mode", "STORY")


def story_level_cap(story):
    """STORY mode: the next Gym Leader's ace in this region (Champion's after 8, none after)."""
    region = story.get_current_region()
    if story.is_region_champion(region) or story.get_region_start(region).get("no_badges"):
        return 100  # Orre has no Gyms to cap levels by
    badges = len(story.badges.get(region, []))
    aces = gym_aces(region)
    if badges < len(aces):
        return aces[badges]
    return CHAMPION_ACE.get(region, 60)


def xp_cap(story):
    """Highest level XP can take a Pokemon to right now (100 when uncapped)."""
    return story_level_cap(story) if cap_mode(story) == "STORY" else 100


def obey_level(story):
    """Highest level that always obeys: Lv 20, +10 per badge from the current region, all at 8."""
    if cap_mode(story) != "OBEDIENCE":
        return 100
    if story.get_region_start(story.get_current_region()).get("travel_only"):
        return 100  # post-game trips (Orange Islands, Orre): your team already obeys you
    badges = len(story.badges.get(story.get_current_region(), []))
    return 100 if badges >= 8 else 20 + 10 * badges


def set_wild(game, pokemon, area_key):
    """A wild Pokemon's level: legendaries keep their fixed level, the rest suit the area."""
    if pokemon and not is_legendary(pokemon.id):
        pokemon.level = wild_level(game, area_key)
        pokemon.current_hp = pokemon.get_max_hp()
    return pokemon


def set_team(team, team_levels, exact=False):
    """exact: a trainer's team with levels from the data, legendaries included (Kieran's Ogerpon);
    otherwise legendaries keep their fixed level."""
    for p, lv in zip(team, team_levels):
        if p and (exact or not is_legendary(p.id)):
            p.level = int(lv)
            p.current_hp = p.get_max_hp()
    return team


def trainer_team_levels(game, area_key, size, boss=False):
    """Route trainers: around the area level, building to the last Pokemon."""
    top = trainer_level(game, area_key, boss)
    return [max(2, top - (size - 1 - i)) for i in range(size)]


def elite_levels(region, index, size):
    """The Elite Four get a little tougher one after another (index 0-3)."""
    lo, hi = ELITE_FOUR.get(region, (50, 55))
    ace = lo + round((hi - lo) * min(index, 3) / 3)
    return [max(2, ace - (size - 1 - i) * 2) for i in range(size)]


def gym_role(trainer_class, is_leader):
    if trainer_class == "CHAMPION":
        return "champion"
    if trainer_class == "ELITE_FOUR":
        return "elite"
    return "leader" if is_leader else "trainer"
