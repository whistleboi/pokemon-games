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


_HITS = {}


def _text_hits(game, text):
    """The place names in a mission's text, longest first. Kept per text: every region's names are more
    patterns than re's own cache holds, and a town's guide asks this for each person and door
    (Lilycove, 11-13: a second's freeze every second)."""
    key = (id(game.loader), text)
    if key not in _HITS:
        if len(_HITS) > 256:
            _HITS.clear()
        _HITS[key] = [(name, k) for name, k in _name_index(game) if re.search(r"\b" + re.escape(name) + r"\b", text)]
    return _HITS[key]


def mission_target(game, mission):
    """The area a mission is about: the first of its "targets" ([area, done-when condition]) not done
    yet (the Silph Scope's hideout before the Tower), else its "target", else the longest place name in
    its text (an area of the current region wins over a same-named one elsewhere)."""
    story = game.story_manager
    for area, done in mission.get("targets") or []:
        if not _ok(story, done):
            return area
    step = current_step(game, mission)
    if step and step.get("area"):  # (its next way-point is in a place of its own: Mr. Fuji's house after the Tower)
        return step["area"]
    if mission.get("target"):
        return mission["target"]
    text = " ".join(str(mission.get(k) or "") for k in ("title", "text", "description", "desc")).lower()
    region = story.get_current_region()
    hits = _text_hits(game, text)
    if not hits:
        return None
    longest = len(hits[0][0])
    best = [k for name, k in hits if len(name) == longest]
    return next((k for k in best if story.area_region(k) == region), best[0])


def current_step(game, mission):
    """A mission's next way-point: the first of its "steps" ({"area", "room" / "floor", "at", "label", "done", "when"})
    not done yet and, if it has a "when", whose time has come. None: no steps, or all done. (11-17: towns and their
    rooms read these too, and a step's "area" is where the Journal leads while it is the next one.)"""
    story = game.story_manager
    for s in (mission or {}).get("steps") or []:
        if s.get("done") and _ok(story, s["done"]):
            continue
        if s.get("when") and not _ok(story, s["when"]):
            continue
        return s
    return None


WALKED_REGIONS = {"KANTO", "ORANGE", "JOHTO", "HOENN"}  # (Orange: 11-17, its walked maps from 5.7, batch by batch; Johto: 11-22, after its playthrough passed, Jordan: "Yes, add Johto"; Hoenn: 11-24, its playthrough Littleroot to Steven passed with 0 stuck points - Dev Map M6) (regions whose Journal is led over the walked maps' own ways out, not the old menus' jumps: each joins after its own scripted playthrough)
_WAYS = {}


def map_ways(game, area_key):
    """The areas a walked map leads to by its own ways out (its rooms' and floors' too), or None: no walked map here,
    or its region still goes by the menus' links."""
    try:
        from src.states.overworld.walk_town import story_map, available
    except Exception:
        return None
    if not available(game, area_key) or game.story_manager.area_region(area_key) not in WALKED_REGIONS:
        return None
    m = story_map(game, area_key)   # (the map the story walks it on now: Shamouti in the storm, 11-18)
    if not isinstance(m, dict):
        return None
    key = (id(m), area_key)
    if key not in _WAYS:
        out = set()

        def take(part):
            for tg in (part.get("exits") or {}).values():
                if isinstance(tg, str) and not tg.startswith(("OUT:", "ROOM:")):
                    out.add(tg)
            for room in (part.get("rooms") or {}).values():
                if isinstance(room, dict):
                    take(room)
            for f in part.get("floors") or []:
                if isinstance(f, dict):
                    take(f)
        take(m)
        _WAYS[key] = out
    return _WAYS[key]


_PARTS = {}


def map_parts(game, area_key):
    """A walked place made of rooms that don't all join up (the Underground Path: one tunnel north-south, another
    east-west): [the areas each joined-up group of its rooms leads to, ...]. None: one group, or no walked map."""
    if map_ways(game, area_key) is None:
        return None
    from src.states.overworld.walk_town import story_map
    m = story_map(game, area_key)
    key = (id(m), area_key)
    if key not in _PARTS:
        rooms = m.get("rooms") or {}
        group = {None: None}
        group.update({n: n for n in rooms})

        def find(a):
            while group[a] != a:
                a = group[a]
            return a

        def join(a, b):
            if a in group and b in group:
                group[find(a)] = find(b)
        out = None
        if rooms and not m.get("floors"):
            for door, room in (m.get("inside") or {}).items():
                join(None, room)
            for name, part in [(None, m)] + list(rooms.items()):
                for tg in list((part.get("exits") or {}).values()) + [v[0] for v in (part.get("links") or {}).values() if isinstance(v, list) and v and isinstance(v[0], str)]:
                    tg = str(tg)
                    if tg.startswith("OUT:"):
                        join(name, None)
                    elif tg.startswith("ROOM:"):
                        join(name, None if tg[5:] == "MAIN" else tg[5:])
                    elif tg in rooms:
                        join(name, tg)
            sets = {}
            for name, part in [(None, m)] + list(rooms.items()):
                for tg in (part.get("exits") or {}).values():
                    if isinstance(tg, str) and not tg.startswith(("OUT:", "ROOM:")):
                        sets.setdefault(find(name), set()).add(tg)
            if len(sets) > 1:
                out = list(sets.values())
        _PARTS[key] = out
    return _PARTS[key]


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


def advances_goal(game, area_key, item, mission=None):
    """True when using this menu button is what the tracked Journal mission needs (Jordan, 11-01): a
    trainer here whose win sets its flag, a story event or legendary that sets it, or the Gym of a
    badge mission. The button is then shown in gold. (mission: the tracked one, when the caller has it.)"""
    mission = mission or tracked_mission(game)
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
    if action == "LEAGUE":  # (an Elite Four member in their own room: the next one to battle, while the mission is the League's)
        i = int(item.get("index", 0))
        won = lambda n: bool(story.story_flags.get(f"league_won_{area_key}_{n}"))
        return mission_target(game, mission) == area_key and not won(i + 1) and all(won(n) for n in range(1, i + 1))
    if action in ("NPC", "EVENT") and item.get("target"):   # (11-24, Hoenn: someone whose talk waits on a step not done yet is
        from src.world import story_events               # not the next step, though the mission names them: Mr. Stone
        _ev = story_events.get(item.get("target")) or {}   # before the Devon Parts are back; unless what the talk sets
        req = _ev.get("requires") or []                    # when it can't go on is what the mission waits for)
        if any(not story.story_flags.get(f) for f in (req if isinstance(req, list) else [req])) \
                and not (need and _ev.get("fail_flag") and _needs(need, _ev["fail_flag"])):
            return False
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


def _ok(story, cond, area=None):
    """A rough menu-condition check without a town/route screen: flags, items and badges.
    Things only a screen can judge (rounds played, balls left) count as open. (area: the place whose button it is, for
    the conditions that mean "this route's": its Pokemon in the way, its trainers.)"""
    if not cond:
        return True
    if isinstance(cond, (list, tuple)):
        return all(_ok(story, c, area) for c in cond)
    if isinstance(cond, dict):
        return any(_ok(story, c, area) for c in cond.get("any", [])) if "any" in cond else True
    c = str(cond)
    if c.startswith("not:"):
        return not _ok(story, c[4:], area)
    if c in ("can_exit", "can_battle", "has_balls", "has_trainers", "can_fish"):
        return True
    if c == "boss_defeated" and area:  # (the route's own Pokemon asleep across the way: Route 12's Snorlax)
        return bool(story.story_flags.get(f"{area}_boss_defeated"))
    if c == "no_trainers" and area:  # (every trainer of the route beaten: Nugget Bridge)
        pool = (story.game.loader.area_data.get("STORY_PROGRESSION", {}).get(area) or {}).get("trainer_pool") or []
        return len(story.defeated_trainers.get(area, ())) >= len(pool)
    if c.startswith("has_item:"):
        return story.inventory.get(c[9:], 0) > 0
    if c.startswith("has_") and c.endswith("_badge"):
        return story.has_badge(c[4:-6])
    if c.startswith("has_") and story.inventory.get(c[4:].upper(), 0) > 0:
        return True
    return bool(story.story_flags.get(c, False))


def _flag_ok(story, fc):
    """An option's "flag_condition" ("flag" or "not flag"), as the town screens read it."""
    parts = str(fc or "").split()
    if len(parts) == 2 and parts[0] == "not":
        return not story.story_flags.get(parts[1])
    return not parts or bool(story.story_flags.get(parts[0]))


def leads_to(game, area_key, opt):
    """The area a town or route button takes you to, or None: a way out, or a building that is an area
    of its own (Celadon's Game Corner, with the Rocket Hideout under it)."""
    if opt.get("action") in ("TRAVEL", "EXIT") or (opt.get("target_area") and not opt.get("action")):
        return opt.get("target_area") or opt.get("target")
    if opt.get("leads_to"):   # (someone at a door who takes you in after a battle: the Radio Tower's guard in the takeover, 11-22)
        return opt["leads_to"]
    if opt.get("action") == "GAMECORNER":
        key = area_key.replace("_CITY", "").replace("_TOWN", "") + "_GAME_CORNER"
        return key if key in game.loader.area_data.get("STORY_PROGRESSION", {}) else None
    return None


def neighbours(game, area_key, open_only=True, came=None):
    """Areas you can go to from area_key (town travel / explore travel / route exits). (came: the area you came in
    from, when the place is rooms that don't all join up: only where that part of it leads.)"""
    parts = map_parts(game, area_key) if came else None
    if parts:
        mine = [p for p in parts if came in p]
        if len(mine) == 1:
            return [n for n in neighbours(game, area_key, open_only) if n in mine[0]]
    story = game.story_manager
    area = game.loader.area_data.get("STORY_PROGRESSION", {}).get(area_key, {})
    ways = map_ways(game, area_key)  # (a walked map: only where its own ways out and doors lead, not the menu's jumps)
    out = []
    for opt in (area.get("travel_options") or []):
        if opt.get("target_area") and (ways is None or opt["target_area"] in ways or opt.get("door")) \
                and (not open_only or (_ok(story, opt.get("condition"), area_key) and _flag_ok(story, opt.get("flag_condition"))
                                       and (ways is None or not opt.get("item_condition") or story.inventory.get(opt["item_condition"], 0) > 0))):
            out.append(opt["target_area"])
    for opt in (area.get("explore_options") or []) + (area.get("route_menu") or []):
        target = leads_to(game, area_key, opt)
        if target and (ways is None or target in ways or opt.get("door") or opt.get("action") == "GAMECORNER") \
                and (not open_only or (_ok(story, opt.get("condition"), area_key) and _flag_ok(story, opt.get("flag_condition")))):
            out.append(target)
    return out


def _avoided(game, mission=None):
    """Areas the tracked mission's way must not pass through (its "avoid": [area, ...] or [[area, till-condition], ...]):
    a road the map blocks though its links look open (Route 12's Snorlax before the Poke Flute)."""
    mission = mission or tracked_mission(game)
    out = set()
    for a in (mission or {}).get("avoid") or []:
        if isinstance(a, (list, tuple)):
            if not _ok(game.story_manager, a[1]):
                out.add(a[0])
        else:
            out.add(a)
    return out


def path_to(game, start, goal, avoid=None):
    """Shortest list of areas from start to goal (both included), or None. (avoid: areas not to pass through, the
    tracked mission's own by default; ignored if there is no other way.)"""
    avoid = _avoided(game) if avoid is None else set(avoid)
    avoid -= {start, goal}
    for skip in ((avoid, set()) if avoid else (set(),)):
        for open_only in (True, False):  # the way you can take now, else any way
            first = (start, None)   # (an area, and the one you came into it from)
            prev, q = {first: None}, deque([first])
            while q:
                cur = q.popleft()
                if cur[0] == goal:
                    path = []
                    while cur is not None:
                        path.append(cur[0])
                        cur = prev[cur]
                    return path[::-1]
                for n in neighbours(game, cur[0], open_only, cur[1]):
                    state = (n, cur[0] if map_parts(game, n) else None)
                    if state not in prev and n not in skip:
                        prev[state] = cur
                        q.append(state)
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
           pygame.time.get_ticks() // 2000, len(game.story_manager.story_flags))   # (and at once when a flag is set: a mission's last step done mid-cave, 11-22)
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
    story = game.story_manager
    key = ("map_hop", here, goal, frozenset(targets), len(story.story_flags), sum(1 for v in story.inventory.values() if v),
           sum(len(b) for b in story.badges.values()), (tracked_mission(game) or {}).get("id"))
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
