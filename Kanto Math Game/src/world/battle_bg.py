"""Battle backgrounds from each region's own game, used the way that game uses them (Jordan 11-23: "use the battle
backgrounds from our source games in each region ... only use the ones in the game in the way that the game uses them";
Kanto keeps its custom Gym backgrounds; the menu regions keep theirs).

A walked region lists its game's backgrounds in assets/battle_bg/<REGION>/index.json (the pictures beside it, taken from
that region's game file on its own branch):

    {"terrain": {"grass": "grass.png", "cave": "cave.png", "water": "water.png", "inside": "inside.png", ...},
     "areas": {"ROUTE_29": "grass.png",                       # one picture for every battle there, or by kind:
               "VIOLET_CITY": {"wild": "...", "trainer": "...", "water": "...", "gym": "...", "leader": "...",
                               "elite": ["e1.png", "e2.png", ...]}}}

How a battle's background is found (pick):
  - the area's entry, by the kind of battle: on the water "water" first; a Gym trainer "gym", its Leader "leader" (else
    "gym"); the Elite Four "elite" by their place in the League (else "leader"); a trainer "trainer" (else "wild"); wild
    "wild"; a plain string for all;
  - else the region's "terrain" by how the area looks (its battle_type: grass, cave, water, sand, inside, snow...);
  - time of day as the games do: a picture "<name>_eve.png" / "<name>_night.png" beside the chosen one is used in the
    evening / at night (assets.time_of_day: eve 5-8pm, night 8pm-6am);
  - nothing found (or no index for the region): None, and the battle goes on to the old rules - so a Gym the index leaves
    out keeps its own background (Kanto's custom ones), and the menu regions are untouched.
"""
import json
import os

_INDEX = {}
TERRAIN = {"grass": "grass", "field": "grass", "forest": "grass", "route": "grass", "city": "grass", "town": "grass",
           "cave": "cave", "mountain": "cave", "dungeon": "cave", "tunnel": "cave",
           "ocean": "water", "water": "water", "sea": "water", "surf": "water",
           "beach": "sand", "sand": "sand", "desert": "sand",
           "indoor": "inside", "building": "inside", "inside": "inside", "tower": "inside",
           "snow": "snow", "ice": "snow", "swamp": "swamp", "marsh": "swamp", "volcano": "volcano"}


def folder(game, region):
    return os.path.join(getattr(game.assets, "assets_dir", None) or "assets", "battle_bg", str(region).upper())


def index(game, region):
    """The region's index (cached), or None when it has none."""
    key = str(region).upper()
    if key not in _INDEX:
        try:
            with open(os.path.join(folder(game, key), "index.json"), encoding="utf-8") as f:
                _INDEX[key] = json.load(f)
        except (OSError, ValueError):
            _INDEX[key] = None
    return _INDEX[key]


def _timed(game, region, name, now=None):
    """name, or its evening / night picture when it's then and there is one."""
    from src.core.assets import AssetManager
    tag = AssetManager.time_of_day(now) if hasattr(AssetManager, "time_of_day") else ""
    if tag:
        stem, ext = os.path.splitext(name)
        alt = f"{stem}_{tag}{ext}"
        if os.path.isfile(os.path.join(folder(game, region), alt)):
            return alt
    return name


def _on_water():
    try:
        from src.dungeon import core
        return core.CURRENT_TILE in (core.SURF, getattr(core, "WATER", None))
    except Exception:
        return False


def pick(game, area_key, *, trainer=False, gym=False, leader=False, elite_index=None, water=None, now=None):
    """The picture (a path) for a battle in area_key, from its region's own game, or None (see the module's notes)."""
    story = game.story_manager
    region = str(story.area_region(area_key) if area_key else story.get_current_region() or "").upper()
    ix = index(game, region) if region else None
    if not ix:
        return None
    water = _on_water() if water is None else water
    entry = (ix.get("areas") or {}).get(area_key)
    name = None
    if isinstance(entry, str):
        name = entry
    elif isinstance(entry, dict):
        order = []
        if water:
            order.append("water")
        if elite_index is not None:
            el = entry.get("elite")
            if isinstance(el, list) and el:
                name = el[min(max(0, int(elite_index)), len(el) - 1)]
            order += ["leader", "gym"]
        elif leader:
            order += ["leader", "gym"]
        elif gym:
            order += ["gym"]
        order += (["trainer", "wild"] if trainer else ["wild"])
        name = name or next((entry[k] for k in order if isinstance(entry.get(k), str)), None)
    if not name and not (gym or leader or elite_index is not None):   # (a Gym the index doesn't name keeps its own)
        area = (game.loader.area_data.get("STORY_PROGRESSION", {}) or {}).get(area_key) or {}
        look = "water" if water else TERRAIN.get(str(area.get("battle_type") or "").lower(), "")
        name = (ix.get("terrain") or {}).get(look) if look else None
    if not name:
        return None
    path = os.path.join(folder(game, region), _timed(game, region, name, now))
    return path if os.path.isfile(path) else None
