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
    if not _menu_targets(area):   # (a place with no menu buttons at all: its walked map's own ways out - Orre's Pyrite Building
        out += [t for t in _walk_exits(area, gated=True) if t not in out]   # lift to The Under, 11-23. Where a place still has menu buttons,
    out += [t for t in _rides(area, st) if t not in out]   # those carry its story gates; its map's barred ways aren't read here)
    return out


def _cond_ok(st, cond):
    """A walked map's condition: a flag, "not:flag", a list of them, or a menu condition the game itself checks."""
    if not cond:
        return True
    if isinstance(cond, list):
        return all(_cond_ok(st, c) for c in cond)
    if isinstance(cond, str) and cond.startswith("not:"):
        return not story.story_flags.get(cond[4:])
    if isinstance(cond, str) and cond in story.story_flags:
        return bool(story.story_flags.get(cond))
    for f in ("_check_menu_condition", "_check_route_condition"):
        fn = getattr(st, f, None)
        if fn is not None:
            try:
                return bool(fn(cond) if f == "_check_menu_condition" else fn(cond, False, {}))
            except Exception:
                pass
    return bool(story.story_flags.get(cond)) if isinstance(cond, str) else False


def _rides(area, st):
    """The places a walked map's people take you (Unova's cleanup, 11-23): a person whose event has "travel" (ships, ferries,
    trains: Pop Roxie, the Liberty Garden sailor) or "travel_choices" (each with its own "requires"), shown now. Scenes
    (one-off story rides) and "@ferry" sailors (a ship's own two ports, already its exits) aren't counted."""
    _walk_exits(area)   # (loads the maps)
    m = _WALK["maps"].get(area) or {}
    out = []
    for part in [m] + list(m.get("floors") or []) + list((m.get("rooms") or {}).values()):
        people = []
        for pp in (part or {}).get("people") or [] if isinstance(part, dict) else []:
            if isinstance(pp, list):   # (one spot, several people by flag: a list of them, or {"any": [...]})
                people += [x for x in pp if isinstance(x, dict)]
            else:
                people += (pp.get("any") or []) if isinstance(pp, dict) and "any" in pp else [pp]
        for pp in people:
            if not isinstance(pp, dict) or "trigger" in pp or not _cond_ok(st, pp.get("condition")):
                continue
            ev = pp.get("event") or {}
            if not isinstance(ev, dict):
                continue
            to = ev.get("travel")
            if isinstance(to, str) and not to.startswith("@") and to in PROG:
                out.append(to)
            for ch in ev.get("travel_choices") or []:
                if ch.get("to") in PROG and _cond_ok(st, ch.get("requires")):
                    out.append(ch["to"])
    return out


def _menu_targets(area):
    a = PROG.get(area) or {}
    return [o for o in (a.get("travel_options") or []) + (a.get("explore_options") or []) + (a.get("route_menu") or [])
            if o.get("target_area") or (o.get("target") and o.get("action") in ("TRAVEL", "EXIT"))]


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


_WALK = {}


def _walk_exits(area, gated=False):
    """The areas a walkable map's exits name (its own and its rooms'; "ROOM:" and "OUT:" stay inside): a place rebuilt
    walkable has no menu buttons left, so its ways out live only in assets/town_maps.json (Unova's cleanup, 11-23).
    gated: leave out a way out the map marks shut till its flags are set - "gated_exits": {target: [flag, "not:flag"...]}
    (a scene turns you back there till then: Unova's Route 16 Bridge Gate lift, till the Hall of Fame; 11-23)."""
    if "maps" not in _WALK:
        try:
            import json as _json
            _d = _json.load(open("assets/town_maps.json", encoding="utf-8"))
            _WALK["maps"] = _d.get("maps", _d)
        except (OSError, ValueError):
            _WALK["maps"] = {}
    m = _WALK["maps"].get(area) or {}
    out = []
    for part in [m] + list(m.get("floors") or []) + list((m.get("rooms") or {}).values()):
        ex = (part or {}).get("exits") if isinstance(part, dict) else None
        for t in (ex.values() if isinstance(ex, dict) else ex or []):
            t = t if isinstance(t, str) else (t.get("target") if isinstance(t, dict) else None)
            if t and not t.startswith(("ROOM:", "OUT:")) and t in PROG:
                out.append(t)
    if gated:
        gates = m.get("gated_exits") or {}
        ok = lambda f: (not story.story_flags.get(f[4:])) if str(f).startswith("not:") else bool(story.story_flags.get(f))
        out = [t for t in out if all(ok(f) for f in gates.get(t, []))]
    return out


def _raw_targets(area):
    a = PROG.get(area) or {}
    out = []
    for o in (a.get("travel_options") or []) + (a.get("route_menu") or []):
        t = o.get("target_area") or (o.get("target") if o.get("action") in ("TRAVEL", "EXIT") else None)
        if t:
            out.append(t)
    return list(dict.fromkeys(out + _walk_exits(area)))


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
