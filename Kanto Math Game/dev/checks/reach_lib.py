"""Reachability through a region using the game's own condition checks (appended after harness_head).
reach(start) -> (set of reachable areas, {area: gym_open_bool})"""
from src.states import overworld as ow
from src.world import hms

g.data.save = lambda *a, **k: None
PROG = g.loader.area_data["STORY_PROGRESSION"]
_cache = {}


def _state(area):
    story.current_area_key = area
    a = PROG.get(area, {})
    if a.get("area_type") == "town":
        st = ow.CityState(g)
    else:
        st = ow.PlayState(g)
        st.rounds_completed = 99
    return st


def _flag_ok(fc):
    if not fc:
        return True
    parts = fc.split()
    if len(parts) == 2 and parts[0] == "not":
        return not story.story_flags.get(parts[1], False)
    return bool(story.story_flags.get(parts[0], False))


def links(area):
    a = PROG.get(area, {})
    st = _state(area)
    out = []
    if a.get("area_type") == "town":
        for o in (a.get("travel_options") or []) + (a.get("explore_options") or []):
            tgt = o.get("target_area") or (o.get("target") if o.get("action") in ("TRAVEL", "EXIT") else None)
            if not tgt or (o.get("action") not in (None, "TRAVEL", "EXIT") and "target_area" not in o):
                continue
            if not _flag_ok(o.get("flag_condition")):
                continue
            if o.get("item_condition") and story.inventory.get(o["item_condition"], 0) <= 0:
                continue
            cond = o.get("condition")
            if cond and not st._check_menu_condition(cond):
                continue
            out.append(tgt)
    else:
        for o in a.get("route_menu") or []:
            if o.get("action") not in ("EXIT", "TRAVEL"):
                continue
            tgt = o.get("target") or o.get("target_area")
            if not _flag_ok(o.get("flag_condition")):
                continue
            cond = o.get("condition")
            if cond and not st._check_route_condition(cond, False, o):
                continue
            out.append(tgt)
    return out


def gym_open(area):
    req = ((PROG.get(area) or {}).get("gym") or {}).get("requirements") or {}
    if not req:
        return True
    if req.get("flag") and not story.story_flags.get(req["flag"]):
        return False
    if any(not story.story_flags.get(f) for f in req.get("flags", [])):
        return False
    if req.get("defeated_area"):
        pool = (PROG.get(req["defeated_area"]) or {}).get("trainer_pool", [])
        if not all(story.is_trainer_defeated(req["defeated_area"], i) for i in range(len(pool))):
            return False
    region = str((PROG.get(area) or {}).get("region", "KANTO")).upper()
    have = story.badges.get(region, [])
    if req.get("badges") and len(have) < int(req["badges"]):
        return False
    for b in req.get("badge_names") or []:
        if b not in have:
            return False
    return True


def reach(start):
    seen, todo = {start}, [start]
    while todo:
        a = todo.pop()
        for t in links(a):
            if t in PROG and t not in seen:
                seen.add(t)
                todo.append(t)
    gyms = {a: gym_open(a) for a in seen if (PROG.get(a) or {}).get("gym", {}).get("leader")}
    return seen, gyms


def badge(region, name):
    story.badges.setdefault(region, [])
    if name not in story.badges[region]:
        story.badges[region].append(name)
    hms.give_for_badges(story)


def clear_area(area):
    for i in range(len((PROG.get(area) or {}).get("trainer_pool", []))):
        story.mark_trainer_defeated(area, i)


def report(title, start, prev):
    seen, gyms = reach(start)
    new = sorted(seen - prev)
    print(f"--- {title}")
    print("    new areas:", new)
    print("    gyms open:", sorted(a for a, ok in gyms.items() if ok),
          "| locked:", sorted(a for a, ok in gyms.items() if not ok))
    return seen


def _raw_targets(area):
    a = PROG.get(area) or {}
    out = []
    for o in (a.get("travel_options") or []) + (a.get("route_menu") or []):
        t = o.get("target_area") or (o.get("target") if o.get("action") in ("TRAVEL", "EXIT") else None)
        if t:
            out.append(t)
    return out


def expansion_check(tag, keys, start):
    """Added-area check: every key exists, is reachable from start with the current story state,
    has no dangling exits and every exit has a way back."""
    seen, _ = reach(start)
    bad = 0
    for k in keys:
        if k not in PROG:
            print(f"   FAIL {tag}: {k} missing"); bad += 1; continue
        if k not in seen:
            print(f"   FAIL {tag}: {k} unreachable from {start}"); bad += 1
        for t in _raw_targets(k):
            if t not in PROG:
                print(f"   FAIL {tag}: {k} -> {t} dangling"); bad += 1
            elif k not in _raw_targets(t):
                print(f"   FAIL {tag}: {k} -> {t} has no way back"); bad += 1
        a = PROG.get(k) or {}
        try:  # the area opens in the game's own state
            st = _state(k)
            if a.get("area_type") != "town":
                st.show_progression_menu()
        except Exception as e:  # noqa: BLE001
            print(f"   FAIL {tag}: {k} does not open: {e!r}"); bad += 1
        pk = a.get("wild_pool_percentages")
        if pk and not g.loader.area_data.get(pk):
            print(f"   FAIL {tag}: {k} pool {pk} missing"); bad += 1
        if any(m.get("action") == "GALACTIC_GAUNTLET" for m in a.get("route_menu") or []):
            fl = a["trainer_pool"][-1].get("victory_flag")
            clear_area(k)
            _state(k).show_progression_menu()
            if not fl or not story.story_flags.get(fl):
                print(f"   FAIL {tag}: gauntlet {k} does not set {fl}"); bad += 1
    print(f"--- {tag}: {len(keys)} added areas checked, {bad} problems")
    return seen


def gate_check(tag, keys, start, flag):
    """keys must NOT be reachable while story flag `flag` is unset."""
    old = story.story_flags.get(flag)
    story.story_flags[flag] = False
    seen, _ = reach(start)
    for k in keys:
        if k in seen:
            print(f"   FAIL {tag}: {k} reachable without {flag}")
    story.story_flags[flag] = old
