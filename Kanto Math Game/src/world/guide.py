# [REF-0081: Route guide]
"""Route guidance (Jordan): the Journal mission you track (or, if you haven't picked one, your
first active story mission) has a goal town or route, and the game points the way there:

- goal_area: the mission's own "target" area, else the place named in its title / description
  ("Defeat Roxanne at the Rustboro City Gym" -> RUSTBORO_CITY);
- next_hop: the next area on the shortest way from where you are (a search over the town travel
  options and route exits; ways you can't take yet are avoided when another way exists).

Towns and routes highlight that exit in gold, the HUD shows GOAL / NEXT, and the Town Map marks
the goal."""
import re
from collections import deque

_NAMES = {}


def _name_index(game):
    """(lowercase place name, area key) for every area, longest names first."""
    key = id(game.loader)
    if key not in _NAMES:
        out = []
        for k, a in game.loader.area_data.get("STORY_PROGRESSION", {}).items():
            name = str(a.get("route_name") or "").strip()
            if len(name) >= 4:
                out.append((name.lower(), k))
        _NAMES[key] = sorted(out, key=lambda x: -len(x[0]))
    return _NAMES[key]


def mission_target(game, mission):
    """The area a mission is about: its "target", else the longest place name in its text (an
    area of the current region wins over a same-named one elsewhere)."""
    if mission.get("target"):
        return mission["target"]
    story = game.story_manager
    text = " ".join(str(mission.get(k) or "") for k in ("title", "text", "description", "desc")).lower()
    region = story.get_current_region()
    hits = [(name, k) for name, k in _name_index(game) if re.search(r"\b" + re.escape(name) + r"\b", text)]
    if not hits:
        return None
    longest = len(hits[0][0])
    best = [k for name, k in hits if len(name) == longest]
    return next((k for k in best if story.area_region(k) == region), best[0])


def tracked_mission(game):
    """The Journal mission being guided to: the one the player picked, else the first active
    story mission (None when there's nothing to do)."""
    story = game.story_manager
    try:
        active = [m for m in story.get_all_journal_entries() if m.get("status") == "ACTIVE"]
    except Exception:
        return None
    picked = getattr(story, "tracked_mission", None)
    if picked == "off":
        return None
    for m in active:
        if m.get("id") == picked:
            return m
    main = [m for m in active if str(m.get("type", "")).upper() == "MAIN"]
    return (main or [None])[0]


def goal_area(game):
    m = tracked_mission(game)
    return mission_target(game, m) if m else None


def _ok(story, cond):
    """A rough menu-condition check without a town/route screen: flags, items and badges.
    Things only a screen can judge (rounds played, balls left) count as open."""
    if not cond:
        return True
    if isinstance(cond, (list, tuple)):
        return all(_ok(story, c) for c in cond)
    if isinstance(cond, dict):
        return any(_ok(story, c) for c in cond.get("any", [])) if "any" in cond else True
    c = str(cond)
    if c.startswith("not:"):
        return not _ok(story, c[4:])
    if c in ("can_exit", "can_battle", "has_balls", "has_trainers", "can_fish"):
        return True
    if c.startswith("has_item:"):
        return story.inventory.get(c[9:], 0) > 0
    if c.startswith("has_") and c.endswith("_badge"):
        return story.has_badge(c[4:-6])
    if c.startswith("has_") and story.inventory.get(c[4:].upper(), 0) > 0:
        return True
    return bool(story.story_flags.get(c, False))


def neighbours(game, area_key, open_only=True):
    """Areas you can go to from area_key (town travel / explore travel / route exits)."""
    story = game.story_manager
    area = game.loader.area_data.get("STORY_PROGRESSION", {}).get(area_key, {})
    out = []
    for opt in (area.get("travel_options") or []):
        if opt.get("target_area") and (not open_only or _ok(story, opt.get("condition"))):
            out.append(opt["target_area"])
    for opt in (area.get("explore_options") or []) + (area.get("route_menu") or []):
        if opt.get("action") in ("TRAVEL", "EXIT"):
            target = opt.get("target_area") or opt.get("target")
            if target and (not open_only or _ok(story, opt.get("condition"))):
                out.append(target)
    return out


def path_to(game, start, goal):
    """Shortest list of areas from start to goal (both included), or None."""
    for open_only in (True, False):  # the way you can take now, else any way
        prev, seen, q = {}, {start}, deque([start])
        while q:
            cur = q.popleft()
            if cur == goal:
                path = [cur]
                while path[-1] != start:
                    path.append(prev[path[-1]])
                return path[::-1]
            for n in neighbours(game, cur, open_only):
                if n not in seen:
                    seen.add(n)
                    prev[n] = cur
                    q.append(n)
    return None


def next_hop(game, here=None):
    """The next area toward the goal from here, or None (no goal, already there, no way)."""
    here = here or game.story_manager.current_area_key
    goal = goal_area(game)
    if not goal or goal == here:
        return None
    path = path_to(game, here, goal)
    return path[1] if path and len(path) > 1 else None


_CACHE = {}


def cached(game, what):
    """hud_lines / next_hop, worked out at most every 2 s (screens draw every frame)."""
    import pygame
    key = (game.story_manager.current_area_key, getattr(game.story_manager, "tracked_mission", None),
           pygame.time.get_ticks() // 2000)
    hit = _CACHE.get(what)
    if not hit or hit[0] != key:
        hit = _CACHE[what] = (key, hud_lines(game) if what == "hud" else next_hop(game))
    return hit[1]


def hud_lines(game):
    """'GOAL: Rustboro City' and 'NEXT: Route 104' for the town / route HUD (empty if none)."""
    goal = goal_area(game)
    if not goal:
        return []
    prog = game.loader.area_data.get("STORY_PROGRESSION", {})
    name = lambda k: prog.get(k, {}).get("route_name") or k.replace("_", " ").title()
    if goal == game.story_manager.current_area_key:
        return [f"GOAL: {name(goal)} (you're here!)"]
    hop = next_hop(game)
    return [f"GOAL: {name(goal)}"] + ([f"NEXT: {name(hop)}"] if hop else [])
