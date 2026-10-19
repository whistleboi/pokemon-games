"""
Seasons and the weather they bring (Unova rules: the season changes every month).

Jan/May/Sep = Spring, Feb/Jun/Oct = Summer, Mar/Jul/Nov = Autumn, Apr/Aug/Dec = Winter.

Every region that has a `climate` in its REGION_START config is seasonal. Its outdoor
routes roll their weather once a day from the climate's chances for the season, so the
same route keeps the same weather all day. Areas with a fixed `weather` keep it, and an
area's `season_weather` ({"WINTER": "SNOW"}) forces weather for that season.

Late in the Hoenn story the Weather Institute hands over the WEATHER_DIAL. Once a day the
player can burn a weather rock to set one route's weather until midnight (or clear the
skies for free). Nothing can change the season itself.

During Hoenn's Primal crisis (Seafloor Cavern cleared, Cave of Origin not yet) the box
legend's harsh sun or heavy rain covers every outdoor Hoenn area.

This module is the one place that answers "what's the weather here today?", so battles,
wild encounters, marts and berry trees all agree.
"""
import datetime
import random

SEASONS = ("SPRING", "SUMMER", "AUTUMN", "WINTER")
WEATHERS = ("RAIN", "SUN", "SAND", "SNOW")

SEASON_NAMES = {"SPRING": "Spring", "SUMMER": "Summer", "AUTUMN": "Autumn", "WINTER": "Winter"}
WEATHER_NAMES = {"RAIN": "Rain", "SUN": "Harsh Sun", "SAND": "Sandstorm", "SNOW": "Snow", None: "Clear"}
SEASON_COLORS = {"SPRING": (255, 160, 200), "SUMMER": (120, 220, 90),
                 "AUTUMN": (240, 150, 60), "WINTER": (170, 210, 255)}

# Wild Pokémon that like the season or the weather show up more (never less than a quarter as often).
SEASON_TYPE_MULT = {
    "SPRING": {"GRASS": 1.5, "BUG": 1.5, "FAIRY": 1.5},
    "SUMMER": {"FIRE": 1.5, "BUG": 1.5, "WATER": 1.25},
    "AUTUMN": {"GHOST": 1.5, "DARK": 1.5, "GRASS": 1.25},
    "WINTER": {"ICE": 2.0, "BUG": 0.5, "GRASS": 0.75},
}
WEATHER_TYPE_MULT = {
    "RAIN": {"WATER": 2.0, "ELECTRIC": 1.5, "FIRE": 0.5},
    "SUN": {"FIRE": 2.0, "GRASS": 1.5, "ICE": 0.5},
    "SAND": {"ROCK": 2.0, "GROUND": 2.0, "STEEL": 1.5},
    "SNOW": {"ICE": 2.0, "FIRE": 0.5},
}

# Berry trees: rain waters them, spring and autumn are growing and harvest time, winter is lean.
SEASON_BERRY_BONUS = {"SPRING": 1, "SUMMER": 0, "AUTUMN": 1, "WINTER": -1}

# Deerling and Sawsbuck change their coats with the season.
SEASONAL_FORM_IDS = {585, 586}

# Galar's Wild Area ("RANDOM") rolls from every weather, nudged by the season.
RANDOM_BASE_WEIGHTS = {"CLEAR": 3, "RAIN": 1, "SUN": 1, "SAND": 1, "SNOW": 1}

_today = datetime.date.today  # tests can swap this out


def today():
    return _today()


def current_season(date=None):
    date = date or today()
    return SEASONS[(date.month - 1) % 4]


def season_name(season=None):
    return SEASON_NAMES[season or current_season()]


def weather_name(weather):
    return WEATHER_NAMES.get(weather, "Clear")


def _areas(game):
    return game.loader.area_data.get("STORY_PROGRESSION", {})


def area_region(game, area_key):
    area = _areas(game).get(area_key, {})
    if area.get("region"):
        return str(area["region"]).upper()
    prefix = area_key.split("_")[0] if area_key else ""
    return prefix if prefix in game.loader.area_data.get("REGION_START", {}) else "KANTO"


def region_climate(game, region):
    return game.loader.area_data.get("REGION_START", {}).get(region or "", {}).get("climate")


def is_seasonal(game, region):
    return bool(region_climate(game, region))


def _day_rng(area_key, date):
    return random.Random(f"{date.toordinal()}:{area_key}")


def area_weather(game, area_key, date=None):
    """Today's weather in an area: RAIN, SUN, SAND, SNOW or None (clear)."""
    date = date or today()
    override = _override(game, area_key, date)
    if override:
        return override["weather"]
    area = _areas(game).get(area_key, {})
    crisis = _hoenn_crisis(game, area_key, area)
    if crisis:
        return crisis
    region = area_region(game, area_key)
    climate = region_climate(game, region) or {}
    season = current_season(date)

    forced = (area.get("season_weather") or {}).get(season)
    if forced:
        forced = str(forced).upper()
        return forced if forced in WEATHERS else None

    fixed = str(area.get("weather") or "").upper()
    if fixed == "RANDOM":
        weights = dict(RANDOM_BASE_WEIGHTS)
        for w, chance in climate.get(season, {}).items():
            weights[w] = weights.get(w, 0) + chance / 10
        rng = _day_rng(area_key, date)
        pick = rng.choices(list(weights), weights=list(weights.values()))[0]
        return pick if pick in WEATHERS else None
    if fixed in WEATHERS:
        return fixed

    # Seasonal weather only falls on outdoor routes; towns and caves stay clear.
    if not climate or area.get("area_type") != "wild_route":
        return None
    roll = _day_rng(area_key, date).random() * 100
    for w, chance in climate.get(season, {}).items():
        if roll < chance:
            return w if w in WEATHERS else None
        roll -= chance
    return None


# ---- Weather Dial: the player's own weather for the rest of the day ----
WEATHER_DIAL = "WEATHER_DIAL"
DIAL_UNLOCK_FLAG = "cave_of_origin_cleared"  # once Primal Groudon/Kyogre is calmed
ROCK_WEATHER = {"DAMP_ROCK": "RAIN", "HEAT_ROCK": "SUN", "SMOOTH_ROCK": "SAND", "ICY_ROCK": "SNOW"}


def _override(game, area_key, date):
    story = getattr(game, "story_manager", None)
    flags = getattr(story, "story_flags", None) or {}
    entry = (flags.get("weather_override") or {}).get(area_key)
    return entry if entry and entry.get("date") == date.isoformat() else None


def _hoenn_crisis(game, area_key, area):
    from src.world import hoenn
    story = getattr(game, "story_manager", None)
    if story is None or area_region(game, area_key) != "HOENN" or not hoenn.primal_crisis(story):
        return None
    v = hoenn.info(story)
    if not v or area.get("area_type") == "dungeon" and not area.get("weather"):
        return None
    return v["crisis_weather"]


def dial_used_today(game, date=None):
    return game.story_manager.story_flags.get("weather_dial_used") == (date or today()).isoformat()


def can_change_weather(game, area_key):
    """Outdoor routes and weather areas in seasonal regions; towns and caves can't be changed."""
    area = _areas(game).get(area_key, {})
    if not is_seasonal(game, area_region(game, area_key)):
        return False
    return area.get("area_type") == "wild_route" or bool(area.get("weather"))


def set_weather(game, area_key, weather, date=None):
    """Set an area's weather (RAIN/SUN/SAND/SNOW, or None for clear skies) until midnight."""
    date = date or today()
    flags = game.story_manager.story_flags
    overrides = {k: v for k, v in (flags.get("weather_override") or {}).items()
                 if v.get("date") == date.isoformat()}  # yesterday's settings are spent
    overrides[area_key] = {"date": date.isoformat(), "weather": weather}
    flags["weather_override"] = overrides
    flags["weather_dial_used"] = date.isoformat()  # the dial works once per day


def region_weathers(game, region, date=None):
    """Every kind of weather that can turn up in a region this season (for mart weather rocks)."""
    season = current_season(date)
    found = set()
    for key, area in _areas(game).items():
        if area_region(game, key) != region:
            continue
        fixed = str(area.get("weather") or "").upper()
        if fixed == "RANDOM":
            found.update(WEATHERS)
        elif fixed in WEATHERS:
            found.add(fixed)
        forced = str((area.get("season_weather") or {}).get(season) or "").upper()
        if forced in WEATHERS:
            found.add(forced)
    climate = region_climate(game, region) or {}
    found.update(w for w, chance in climate.get(season, {}).items() if chance > 0 and w in WEATHERS)
    return found


def species_types(game, pid):
    pid = str(pid)
    mapping = game.loader.area_data.get("FORM_MAP", {}).get(pid) or {}
    if mapping.get("types"):
        return [str(t).upper() for t in mapping["types"]]
    moves = game.assets.movesets.get(pid) or game.assets.movesets.get(str(mapping.get("id", pid)), {})
    return [str(t).upper() for t in moves.get("types", [])]


def encounter_mult(types, season=None, weather=None):
    mult = 1.0
    for table in (SEASON_TYPE_MULT.get(season, {}), WEATHER_TYPE_MULT.get(weather, {})):
        boosts = [table[t] for t in types if t in table]
        if boosts:
            # A dual type uses its best boost, or its gentlest penalty.
            mult *= max(boosts) if max(boosts) > 1 else min(boosts)
    return max(0.25, mult)


def adjust_pool(game, pool, area_key, date=None):
    """Re-weight a wild pool ({id: pct}) for the season and today's weather in this area."""
    if not pool or not is_seasonal(game, area_region(game, area_key)):
        return pool
    season, weather = current_season(date), area_weather(game, area_key, date)
    return {pid: pct * encounter_mult(species_types(game, pid), season, weather)
            for pid, pct in pool.items()}


def berry_bonus(game, area_key, date=None):
    """Extra berries (may be negative) and the lines explaining them."""
    region = area_region(game, area_key)
    if not is_seasonal(game, region):
        return 0, []
    season = current_season(date)
    bonus, lines = SEASON_BERRY_BONUS[season], []
    if season == "WINTER":
        lines.append("The cold winter left few berries on the trees.")
    elif bonus > 0:
        lines.append(f"The trees are full in {season_name(season).lower()}!")
    weather = area_weather(game, area_key, date)
    if weather == "RAIN":
        bonus += 1
        lines.append("The rain watered the trees. They grew extra berries!")
    elif weather == "SUN":
        bonus -= 1
        lines.append("The harsh sun has dried out some of the berries.")
    return bonus, lines


def form_name(pid, season=None):
    """Deerling and Sawsbuck wear the current season's coat."""
    if int(pid) in SEASONAL_FORM_IDS:
        return f"{season_name(season)} Form"
    return None


def hud_label(game, area_key, date=None):
    """'Winter - Snow' for the overworld HUD, or None outside seasonal regions."""
    region = area_region(game, area_key)
    if not is_seasonal(game, region):
        return None
    season = current_season(date)
    return f"{season_name(season)}  -  {weather_name(area_weather(game, area_key, date))}", SEASON_COLORS[season]


def season_change_notice(game, story, region, date=None):
    """Lines announcing a new season the first time the player sees it, else None."""
    if not is_seasonal(game, region):
        return None
    season = current_season(date)
    last = story.story_flags.get("last_season")
    story.story_flags["last_season"] = season
    if last == season:
        return None
    lines = {
        "SPRING": "Flowers are blooming and Grass and Bug Pokemon are out in force.",
        "SUMMER": "The sun beats down and Fire Pokemon are more common.",
        "AUTUMN": "Leaves are falling and Ghost and Dark Pokemon come out to play.",
        "WINTER": "Snow is in the air and Ice Pokemon are easier to find.",
    }
    return [f"It's {season_name(season)} in {region.title()}!", lines[season]]
