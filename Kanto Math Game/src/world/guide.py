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
                if (a.get("area_type") == "town" and name.lower().endswith((" city", " town"))
                        and len(name) - 5 >= 4):  # "Saffron" for Saffron City (missions say it that way)
                    out.append((name[:-5].lower(), k))
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


def _event_flags(event):
    """Every flag a story event (src/world/story_events.py, or an EVENT button's own) can set."""
    if not isinstance(event, dict):
        return set()
    out = {event.get("flag"), (event.get("battle") or {}).get("victory_flag")}
    for stage in event.get("stages") or []:
        out |= _event_flags(stage)
    return out - {None}


def _plain(text):
    return str(text or "").lower().replace("é", "e").replace("{", "").replace("}", "")


def _named_in_mission(game, mission, area_key, item):
    """A town's building or person the mission names (Jordan, 11-02: "guide them directly to the
    building"): a button in the mission's own area whose words are in its title or text ("Fighting
    Dojo", "Copycat", "Bill's House"). Gyms, healing and shops go by their own rules."""
    if item.get("action") in ("GYM", "HEAL", "SHOP", "EXIT", "ZONE", "CATCH", "BATTLE", "FISH"):
        return False
    label = _plain(item.get("text"))
    for word in ("visit ", "talk to ", "go to ", "enter "):
        label = label[len(word):] if label.startswith(word) else label
    if len(label) < 4 or mission_target(game, mission) != area_key:
        return False
    text = _plain(" ".join(str(mission.get(k) or "") for k in ("title", "text", "description", "desc")))
    return bool(re.search(r"\b" + re.escape(label) + r"\b", text))


def advances_goal(game, area_key, item):
    """True when using this menu button is what the tracked Journal mission needs (Jordan, 11-01): a
    trainer here whose win sets its flag, a story event or legendary that sets it, or the Gym of a
    badge mission. The button is then shown in gold."""
    mission = tracked_mission(game)
    if not mission:
        return False
    story = game.story_manager
    flags = story.mission_flags(mission)
    left = [f for f in flags if not story.story_flags.get(f)]  # (a list: the ones not done yet)
    need = left[0] if len(left) == 1 else (set(left) or None)
    action = item.get("action")
    area = game.loader.area_data.get("STORY_PROGRESSION", {}).get(area_key, {})
    if action == "GYM":
        return bool(mission.get("completed_badge") or str(need or "").startswith("badge_"))             and mission_target(game, mission) == area_key
    if _named_in_mission(game, mission, area_key, item):
        return True  # the building or person the mission names, in its town (the Fighting Dojo)
    if not need:
        return False
    if action == "TRAINER":
        done = story.defeated_trainers.get(area_key, set())
        return any(_needs(need, t.get("victory_flag")) for i, t in enumerate(area.get("trainer_pool") or [])
                   if i not in done)
    if action == "BOSS":
        boss = item.get("boss") or area.get("area_boss") or {}
        return _needs(need, boss.get("victory_flag", f"{area_key}_boss_defeated"))
    if action in ("NPC", "EVENT"):
        from src.world import story_events
        got = _event_flags(item.get("event")) | _event_flags(story_events.get(item.get("target")))
        return bool(got & need) if isinstance(need, set) else need in got
    return False


def _needs(need, flag):
    """Is flag what the mission needs (need: a flag, or the set of a mission's flags not done yet)?"""
    return flag in need if isinstance(need, set) else flag == need


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


def map_hop(game, targets):
    """Of the ways out a walked map has (their area keys), the one to take toward the goal: the
    next hop if it's one of them, else the one with the shortest trip from there (a town's menu can
    jump further than its map: Pallet's TRAVEL goes to Viridian, its map only to Route 1)."""
    targets = set(t for t in targets if t)
    hop = cached(game, "hop")
    if not hop or hop in targets:
        return hop
    goal = goal_area(game)
    here = game.story_manager.current_area_key
    key = ("map_hop", here, goal, frozenset(targets))
    if key not in _CACHE:
        best = None
        for t in sorted(targets):
            path = [t] if t == goal else path_to(game, t, goal)
            if path and here not in path and (best is None or len(path) < best[0]):
                best = (len(path), t)
        _CACHE[key] = best and best[1]
    return _CACHE[key]


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
