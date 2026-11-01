"""League Redo (Jordan, 11-01): once the player is Champion of a second region, the first region
they won calls them back. Its professor says the League wants a rematch; every Gym Leader there
battles again with a full team of six at level 100, in any order, and each win gives that badge
again with a star in the Badge Case. With all eight stars, the Elite Four and the Champion take
them on the same way.

All of it lives in story flags (no save-file changes):
    league_redo_told_<REGION>        the professor's call has been made
    redo_badge_<REGION>_<BADGE>      that Leader beaten again (the starred badge)
    redo_champion_<REGION>           the Champion beaten again
"""
from src.pokemon.balance import is_legendary
from src.world.hms import _norm

LEVEL = 100
TEAM_SIZE = 6
PROFESSORS = {"KANTO": "Professor Oak", "JOHTO": "Professor Elm"}
# The newest Pokemon each region's game has (its own generation, or the remake's: HGSS, ORAS, BDSP),
# so Kanto's Magmar stays a Magmar.
GEN_CAP = {"KANTO": 151, "ORANGE": 251, "JOHTO": 493, "ORRE": 386, "HOENN": 721, "SINNOH": 493,
           "UNOVA": 649, "KALOS": 721, "ALOLA": 809, "GALAR": 905, "PALDEA": 1025}
# Paradox Pokemon: not for a Leader's team (the legendary-like ones as much as the rest).
PARADOX = set(range(984, 996)) | {1005, 1006, 1009, 1010, 1020, 1021, 1022, 1023}


def first_region(story):
    """The first region the player won: where they started (the move to a new region comes after
    a title), once its Champion is beaten."""
    region = str(story.starting_region or "").upper()
    return region if region and story.is_region_champion(region) else None


def redo_region(story):
    """The region with a League Redo open, or None until a second region's title is won."""
    first = first_region(story)
    if not first:
        return None
    others = [r for r, _cfg in story.get_region_starts() if r != first and story.is_region_champion(r)]
    return first if others else None


def active_here(story, region=None):
    region = str(region or story.get_current_region()).upper()
    return bool(region) and redo_region(story) == region


def badge_flag(region, badge):
    return f"redo_badge_{str(region).upper()}_{_norm(badge)}"


def champion_flag(region):
    return f"redo_champion_{str(region).upper()}"


def has_badge(story, region, badge):
    return bool(story.story_flags.get(badge_flag(region, badge)))


def gyms(story, region):
    """([(area key, badge)] for the region's Gyms in story order, the League's area key or None).
    (Kanto's areas have no "region": story.area_region counts them as Kanto.)"""
    from src.states.overworld import is_league
    found, league = [], None
    for key, area in story.game.loader.area_data.get("STORY_PROGRESSION", {}).items():
        gym = (area or {}).get("gym")
        if not gym or story.area_region(key) != region:
            continue
        badge = (gym.get("leader") or {}).get("badge_reward")
        if is_league(gym):
            league = league or key
        elif badge:
            found.append((key, badge))
    return found, league


def badges_won(story, region):
    return [b for _k, b in gyms(story, region)[0] if has_badge(story, region, b)]


def league_open(story, region=None):
    """All eight badges won again: the Elite Four and the Champion are next (until beaten)."""
    region = str(region or story.get_current_region()).upper()
    badges = gyms(story, region)[0]
    return (active_here(story, region) and bool(badges) and len(badges_won(story, region)) == len(badges)
            and not story.story_flags.get(champion_flag(region)))


def professor_name(story, region):
    return story.get_region_start(region).get("professor") or PROFESSORS.get(region, "the Professor")


def call_lines(story, region):
    """The professor's call when the player comes back."""
    prof = professor_name(story, region)
    name = region.title()
    return [f"*Ring ring!* It's {prof}!",
            f"{prof}: Welcome back to {name}, Champion! I have news from the {name} League.",
            f"{prof}: The Gym Leaders want to battle you again. They've had a long time to train,"
            " and this time they won't hold back!",
            f"{prof}: Win all {len(gyms(story, region)[0]) or 8} badges again, in any order you like."
            f" Every Leader has a full team of six at level {LEVEL}.",
            f"{prof}: Win them all, and the Elite Four and the Champion will face you at full strength too!"]


def take_call(story, region=None):
    """The call's lines the first time the player is back in the redo region, else []."""
    region = str(region or story.get_current_region()).upper()
    flag = f"league_redo_told_{region}"
    if not active_here(story, region) or story.story_flags.get(flag):
        return []
    story.story_flags[flag] = True
    return call_lines(story, region)


def intro_lines(name, league=False):
    if league:
        return [f"{name}: So, the Champion returns. We've trained for this day.",
                "No holding back. Show us everything you have!"]
    return [f"{name}: You're back! I've trained every day since our last battle.",
            "This time it's my full team, at full strength. No holding back!"]


def won_lines(name, badge=None):
    if badge:
        return [f"{name}: Amazing... You really are a Champion.",
                f"You've won the {badge.replace('_', ' ').title()} Badge all over again!"]
    return [f"{name}: Incredible. You're stronger than ever!"]


# ---- the teams

def _species(game):
    """{species name: id} and {id: data} for the base species (no forms)."""
    cache = getattr(game, "_redo_species", None)
    if cache is None:
        data = {int(k): v for k, v in (game.assets.movesets or {}).items() if str(k).isdigit() and int(k) < 2000}
        cache = ({str(v.get("name", "")).upper(): k for k, v in data.items()}, data)
        game._redo_species = cache
    return cache


def _next_stages(game, pid, dex=None):
    """The species pid evolves into (only those in dex, when given)."""
    by_name, data = _species(game)
    evolutions = getattr(game.loader, "evolution_map", None) or {}
    nxt = [by_name.get(str(n).upper()) for n in evolutions.get(str(data[pid].get("name", "")).upper(), [])]
    return [n for n in nxt if n and (dex is None or n in dex)]


def fully_evolved(game, pid, dex=None):
    """The last stage of pid's line inside dex (Kanto's Magmar stays Magmar), the first branch
    where it splits; pid itself if it's last."""
    _by_name, data = _species(game)
    pid = int(pid)
    if pid not in data:
        return pid  # a regional form etc.: keep it as it is
    seen = {pid}
    while True:
        nxt = [n for n in _next_stages(game, pid, dex) if n not in seen]
        if not nxt:
            return pid
        pid = nxt[0]
        seen.add(pid)


def _region_dex(story, region):
    cfg = story.get_region_start(region)
    lo, hi = (cfg.get("dex_range") or [1, 151])[:2]
    return list(range(int(lo), int(hi) + 1)) + [int(p) for p in cfg.get("dex_extra", [])]


def _main_type(data, team):
    """The type most of the team shares (on a tie, not Normal: Falkner's Pidgey are Flying)."""
    count = {}
    for pid in team:
        for t in (data.get(int(pid), {}).get("types") or []):
            count[t] = count.get(t, 0) + 1
    return max(count, key=lambda t: (count[t], t != "NORMAL", -list(count).index(t))) if count else None


def redo_team(game, region, team_ids):
    """Six Pokemon for a League Redo: the trainer's own team, fully evolved, then the strongest
    fully evolved Pokemon of their type from the region's Pokedex (no legendaries)."""
    _by_name, data = _species(game)
    cap = GEN_CAP.get(region, 1025)
    ok = lambda p: p <= cap and p not in PARADOX
    allowed = {p for p in data if ok(p)}  # evolving: anything of the region's generation
    dex = {p for p in _region_dex(game.story_manager, region) if ok(p)}  # added: the region's own
    team = []
    for pid in team_ids:
        final = fully_evolved(game, pid, allowed | {int(pid)})
        if final not in team:
            team.append(final)
    kind = _main_type(data, team_ids)
    bst = lambda p: sum((data[p].get("stats") or {}).values())

    def fill(typed):
        picks = [p for p in sorted(dex) if p in data and p not in team and not is_legendary(p)
                 and not _next_stages(game, p, allowed)
                 and (not typed or kind is None or kind in (data[p].get("types") or []))]
        for p in sorted(picks, key=lambda p: (-bst(p), p)):
            if len(team) >= TEAM_SIZE:
                return
            team.append(p)

    fill(True)
    if len(team) < TEAM_SIZE:  # a type the region has few of: its strongest of any type
        fill(False)
    return team[:TEAM_SIZE]


def mission(story):
    """The Journal's League Redo mission (a MAIN one, so the guide points at it), or None."""
    region = redo_region(story)
    if not region or not story.story_flags.get(f"league_redo_told_{region}"):
        return None
    found, league = gyms(story, region)
    left = [(k, b) for k, b in found if not has_badge(story, region, b)]
    won = len(found) - len(left)
    if left:
        target = left[0][0]
        desc = (f"The {region.title()} Gym Leaders want a rematch at full strength: six Pokemon at level {LEVEL}."
                f" Win their badges again, in any order. {won} of {len(found)} won so far.")
    else:
        target = league
        desc = f"All {len(found)} badges won again! The Elite Four and the Champion are waiting, at full strength."
    return {"id": f"league_redo_{region.lower()}", "type": "MAIN", "title": "League Redo", "description": desc,
            "condition": {"required_region": region, "flag": f"league_redo_told_{region}"},
            "completed_flag": champion_flag(region), "target": target, "reward": "A starred Badge Case"}
