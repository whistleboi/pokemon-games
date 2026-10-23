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
    # Orange League in line with Kanto's League (Jordan): Gyms like the Elite Four (54-60), Drake like
    # Kanto's Champion (63); his rematch (+10) is 69-73, close to Kanto's FRLG rematch (72-75).
    "ORANGE": [54, 56, 58, 60],
}
ELITE_FOUR = {"KANTO": (54, 60), "JOHTO": (53, 59), "HOENN": (50, 53), "SINNOH": (53, 59),
              "UNOVA": (48, 50), "KALOS": (58, 62), "ALOLA": (54, 57), "GALAR": (52, 58),
              "PALDEA": (57, 60)}
CHAMPION_ACE = {"KANTO": 63, "JOHTO": 63, "HOENN": 59, "SINNOH": 62, "UNOVA": 54, "KALOS": 66,
                "ALOLA": 60, "GALAR": 65, "PALDEA": 62,
                "ORANGE": 63}
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
    """An area's wild level (an area's own "level" key wins). Post-game (the area's region, or
    its parent, has been won) every area follows the player instead: postgame_cap - POSTGAME_UNDER,
    so wild Pokemon are a few levels under the cap and trainers at about the cap (see
    postgame_area_level). The League never uses area levels, so it is not affected."""
    scaled = postgame_area_level(game, area_key)
    if scaled is not None:
        return scaled
    area = game.loader.area_data.get("STORY_PROGRESSION", {}).get(area_key, {})
    if area.get("level"):
        return int(area["level"])
    return int(_area_levels(game).get(area_key, START_LEVEL + 2))


def wild_level(game, area_key):
    return max(2, area_level(game, area_key) + random.randint(-2, 1))


def trainer_level(game, area_key, boss=False):
    """Route trainers sit a little above the area; on the first routes (a fresh Lv 5 starter)
    only by 0-1, so Youngster Joey's Rattata isn't a wall."""
    base = area_level(game, area_key)
    if boss:
        return base + 4
    return base + (random.randint(0, 1) if base < 8 else random.randint(1, 3))


# Jordan's legendary rule:
# - before the region's last Gym badge: the story level cap + LEGEND_OVER_CAP (Hoenn patch 09);
# - from the last Gym badge on (Victory Road, the League) and the whole post-game, including the
#   post-game sub-regions and DLC areas: a flat LEGEND_LEVEL (70). Legendaries are never part of
#   the player-led post-game scaling. This replaces 09's "Champion's ace stands in for the cap".
LEGEND_OVER_CAP = 3
LEGEND_LEVEL = 70


def legendary_level(pid):
    """A legendary or mythical made outside an encounter (trainer teams without levels, a fresh
    Pokemon from the loader): LEGEND_LEVEL. Replaces the old 70/50/80/60 split."""
    return LEGEND_LEVEL


def legendary_encounter_level(game, area_key=None):
    """Level of a legendary met in the wild, as a boss (data levels included), a roamer or a
    gift: cap + 3 before the last Gym badge, LEGEND_LEVEL (70) from then on and post-game."""
    story = game.story_manager
    region = story.get_current_region()
    if is_postgame(story, region) or len(story.badges.get(region, [])) >= len(gym_aces(region)):
        return LEGEND_LEVEL
    return max(5, min(100, int(story_level_cap(story)) + LEGEND_OVER_CAP))


def boss_level(game, area_key, pid):
    """Area bosses: legendaries per legendary_encounter_level, others a little above the area."""
    if is_legendary(pid):
        return legendary_encounter_level(game, area_key)
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


# Jordan's post-game rule: once a region's Champion is beaten, the cap is player-controlled.
# It is the team's highest level, but never below the lowest level met in that region's League
# rematch. Lowest rematch level per region, as GymLobbyState.challenge_gym builds the rematch
# teams (the games' rematch teams, else the League's levels + 10). The League itself is NOT
# scaled by this cap: rematch levels stay as they are. Only Elite Four and Champion teams count
# (LEAGUE_CLASSES): Galar's Marnie/Hop and Paldea's Nemona are post-game rematches on the cap
# rules, so Galar's floor is Leon's lowest (65) and Paldea's is Rika's (59).
LEAGUE_REMATCH_FLOOR = {"KANTO": 63, "JOHTO": 58, "HOENN": 56, "SINNOH": 55, "UNOVA": 52,
                        "KALOS": 62, "ALOLA": 58, "GALAR": 65, "PALDEA": 59}
# Post-game spreads around the cap (Jordan): wild Pokemon a few levels under it (area level =
# cap - 3, wild = area -2..+1 -> cap-5..cap-2), route/story trainers about at it (area +1..+3 ->
# cap-2..cap, bosses cap+1), non-legendary area bosses cap+2. Post-game legendaries stay at 70 (LEGEND_LEVEL).
POSTGAME_UNDER = 3
# League rosters: only these classes keep the League's own (rematch) levels. Anyone else in a
# League lobby (Galar's Marnie/Hop, Paldea's Nemona) is a post-game rematch on the cap rules.
LEAGUE_CLASSES = ("ELITE_FOUR", "CHAMPION")


def parent_region(story, region=None):
    """The main region a region or sub-region belongs to. Sub-region areas already carry their
    parent's "region" (Sevii: KANTO, Decolore: UNOVA, Sinjoh and Hisui: SINNOH, the DLC areas:
    GALAR/PALDEA); the Orange Islands and Orre are trips from KANTO and HOENN ("storage_region")."""
    region = str(region or story.get_current_region()).upper()
    return str(story.get_region_start(region).get("storage_region") or region).upper()


def is_postgame(story, region=None):
    """After this region's title or its parent region's (a sub-region or trip such as Sevii,
    Orange, Decolore, Sinjoh, Hisui, Orre and the DLC areas follows its parent), and anywhere
    without Gyms (Orre)."""
    region = str(region or story.get_current_region()).upper()
    return bool(story.is_region_champion(region) or story.is_region_champion(parent_region(story, region))
                or story.get_region_start(region).get("no_badges"))


def postgame_area_level(game, area_key):
    """The post-game level an area's wild Pokemon and trainers are built around, or None before
    the title (then the area's own level is used)."""
    story = getattr(game, "story_manager", None)
    if story is None or not hasattr(story, "is_region_champion"):
        return None
    region = story.area_region(area_key) if area_key and hasattr(story, "area_region") else None
    if region is None or not is_postgame(story, region):
        return None
    return max(2, postgame_cap(story, region) - POSTGAME_UNDER)


def postgame_trainers(game, area_key=None):
    """True when trainers here follow the post-game cap (data levels from the games are ignored)."""
    story = game.story_manager
    return postgame_area_level(game, area_key or story.current_area_key) is not None


def postgame_cap(story, region=None):
    """The player-controlled post-game cap: the party's highest level, floored at the parent
    region's League rematch floor. It moves up with the team (see xp_cap), so a team that
    over-levels meets stronger wild Pokemon and trainers (not legendaries: always 70); the League
    keeps its own."""
    top = max((int(p.level) for p in getattr(story, "player_team", []) if p), default=0)
    floor = LEAGUE_REMATCH_FLOOR.get(parent_region(story, region), 50)
    return max(5, min(100, max(top, floor)))


# Jordan: after the last Gym badge and before the title (Victory Road / the League) the cap is 70
# in every region (sub-regions follow their parent's rule). Legendaries are a flat 70 from then on.
# The League's own levels are not raised: the Elite Four and Champions (aces 48-66) sit below it.
PRE_LEAGUE_CAP = 70


def story_level_cap(story):
    """STORY mode: the next Gym Leader's ace in this region (PRE_LEAGUE_CAP after the last). After the title
    (and in Orre, which has no Gyms) the player-controlled post-game cap (postgame_cap)."""
    region = story.get_current_region()
    if is_postgame(story, region):
        return postgame_cap(story, region)
    badges = len(story.badges.get(region, []))
    aces = gym_aces(region)
    if badges < len(aces):
        return max(aces[:badges + 1])  # never lower than an earlier Gym's (Pryce's ace is below Jasmine's)
    return PRE_LEAGUE_CAP  # every Gym badge, no title yet (Victory Road / the League): Lv 70 everywhere


def xp_cap(story):
    """Highest level XP can take a Pokemon to right now (100 when uncapped). Post-game the cap
    is the team's own highest level, so XP is not blocked: the player controls the level and the
    cap follows the team."""
    if cap_mode(story) != "STORY" or is_postgame(story):
        return 100
    return story_level_cap(story)


def obey_level(story):
    """Highest level that always obeys: Lv 20, +10 per badge from the current region, all at 8."""
    if cap_mode(story) != "OBEDIENCE":
        return 100
    if story.get_region_start(story.get_current_region()).get("travel_only"):
        return 100  # post-game trips (Orange Islands, Orre): your team already obeys you
    badges = len(story.badges.get(story.get_current_region(), []))
    return 100 if badges >= 8 else 20 + 10 * badges


def set_wild(game, pokemon, area_key):
    """A wild Pokemon's level: legendaries per legendary_encounter_level, the rest suit the area."""
    if pokemon and is_legendary(pokemon.id):
        pokemon.level = legendary_encounter_level(game, area_key)
        pokemon.current_hp = pokemon.get_max_hp()
    elif pokemon:
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
