# Shared helpers for suites that play a walked region's town or route on its map, as a player would (legacy menu clear,
# Step 5, 11-24: the menu-era suites moved onto the maps). A suite reads it with
#   exec(open("dev/checks/walk_lib.py", encoding="utf-8").read())
# It turns g.walk_towns / g.dungeon_routes on: a walked place opens its map, a menu region's place still opens its menu.
# From kanto_events' helpers: walk_town / walk_route open a place, walk_meet walks into whoever it is, walk_door goes
# through a door, walk_out steps off the map by an exit, walk_play taps through what's said and fights the battles.
import pygame as _wl_pg
from src.states.overworld import PlayState as _WL_PS, CityState as _WL_CS
from src.states.overworld.walk_town import WalkTownState as _WL_WTS
from src.dungeon import core as _wl_core

g.walk_towns = True
g.dungeon_routes = True
story.story_flags.setdefault("hoenn_version", "OMEGA_RUBY")   # (past each region's version pick, as doors does)
story.story_flags.setdefault("unova_version", "BLACK_2")
walk_said = []
_wl_last = None


def walk_frames(n=1):
    for _ in range(n):
        g.current_state.update()
        g.current_state.draw()


def _wl_note(st):
    box = getattr(st, "npc_dialogue", None) if getattr(st, "npc_active", False) else getattr(st, "dialogue_box", None)
    global _wl_last
    if box is not None and getattr(box, "visible", True):
        lines = list(getattr(box, "text_lines", []) or [])
        if (id(box), lines) == _wl_last:
            return
        _wl_last = (id(box), lines)
        for line in lines:
            if not walk_said or walk_said[-1] != line:
                walk_said.append(line)


def walk_play(picks=(), n=3000, until=None, fight=True, off_map=False):
    """Run the game as a player: tap through what's said, answer each pick list with the next of picks (by value, or True
    for the first), fight battles with the right answers (fight=False: stop at a battle). Stops when nothing is left to do
    (or until() is true)."""
    picks = list(picks)
    quiet = 0
    for _ in range(n):
        if until and until():
            return True
        st = g.current_state
        name = type(st).__name__
        if off_map and not walked(st):   # (stop at whatever screen the map handed over to: a battle, the starter pick)
            return True
        if name == "RegionSelectionState" and getattr(st, "return_state", None) is not None:   # (Mom's move offer after a
            g.change_state(st.return_state)   # title: stay put - a suite moves regions itself)
            quiet = 0
            continue
        if name == "PickListState":
            v = picks.pop(0) if picks else None
            if v is None:
                st.done(None) if hasattr(st, "done") else None
            elif v is True:
                c0 = (getattr(st, "choices", None) or [None])[0]
                st.pick(c0[1] if isinstance(c0, (tuple, list)) else c0)
            else:
                st.pick(v) if hasattr(st, "pick") else st.done(v)
            quiet = 0
        elif hasattr(st, "math_ui") and hasattr(st, "phase"):
            if not fight:
                return True
            walk_fight(st)
            quiet = 0
        elif getattr(st, "npc_active", False):
            _wl_note(st)
            st.handle_events([_wl_pg.event.Event(_wl_pg.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
            quiet = 0
        elif getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
            _wl_note(st)
            st.dialogue_box.advance()
            quiet = 0
        elif getattr(st, "_scene_lock", False) or (getattr(st, "scenes", None) is not None and st.scenes.busy()):
            quiet = 0   # (a scene playing: let it run)
        else:
            quiet += 1
            if quiet > 40 and until is None:
                return True
        st.update(); st.draw()
    return until() if until else True


def walk_fight(b, n=8000):
    for _k in range(n):
        if g.current_state is not b:
            return
        if b.phase == "SWITCH_PROMPT" and b.btn_no.visible and b.btn_no.callback:
            b.btn_no.callback()
        elif b.phase == "MENU" and not b.dialogue_box.visible:
            b.open_move_menu()
            b.choose_move(b.move_buttons[0].text.replace(" ", "-"))
            b.math_ui.on_click(b.options.index(b.correct_ans))
        elif b.dialogue_box.visible:
            _wl_note(b)
            b.dialogue_box.is_finished = True
            if b.phase in ("OUTRO", "VICTORY_TEXT", "REWARD_TEXT"):
                b.handle_events([_wl_pg.event.Event(_wl_pg.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
            elif b.dialogue_box.callback:
                cb = b.dialogue_box.callback; b.dialogue_box.callback = None; cb()
        b.feedback_timer = 0
        b.update(); b.draw()


def walk_town(area, came=None, room=None, play=True):
    """A town's walking map, come in from came (a menu region's town: its menu screen)."""
    g.walk_town_pos = g.walk_town_exit = g.walk_town_room = None
    story.current_area_key, story.last_area_key = area, came
    t = _WL_CS(g); g.change_state(t); walk_frames(2)
    if play:
        walk_play()
        if isinstance(g.current_state, _WL_CS) and g.current_state is not t:   # (the town made anew: back from Mom's offer)
            t = g.current_state
    if room:
        t._go(room, ""); walk_frames(2)
    return t


def walk_route(area, came=None, floor=0, play=True):
    """A route's walking map (a dungeon), come in from came."""
    _wl_core.ENTRANCE_INDEX, _wl_core.ENTRANCE_COUNT = 0, 0
    story.current_area_key, story.last_area_key = area, came
    p = _WL_PS(g)
    g.states["play"] = p
    g.change_state(p)
    walk_frames(3)
    if play:
        walk_play()
    p = g.current_state if isinstance(g.current_state, _WL_PS) else p
    if floor:
        p.run.enter_floor(floor); walk_frames(2)
    return p


def walk_place(area, came=None):
    """Open an area the way the game does: a town's walking map, or a route's."""
    a = g.loader.area_data["STORY_PROGRESSION"].get(area, {})
    return walk_town(area, came) if a.get("area_type") == "town" else walk_route(area, came)


def walked(st):
    """True if st is a walked map (a town's or a route's), not a menu screen."""
    return isinstance(st, _WL_WTS) or hasattr(st, "run")


def _wl_town_spot(st, test):
    hit = next((s for s, o in st._people().items() if test(o)), None)
    if hit is None:   # (in one of the town's rooms: go in)
        for room in [None] + list(st.town_map.get("rooms") or {}):
            if room == getattr(st, "room", None):
                continue
            st._go(room, ""); walk_frames(2); walk_play()
            hit = next((s for s, o in st._people().items() if test(o)), None)
            if hit is not None:
                break
    return hit


def _wl_bump(st, spot, avoid=()):
    """Stand on an open tile beside spot and walk into it (in a town's room, across a counter: the nurse, the clerk)."""
    cands = [(dx, dy, 1) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))]
    if isinstance(st, _WL_WTS) and getattr(st, "room", None):
        cands += [(dx, dy, k) for k in (2, 3) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))
                  if all(0 <= spot[1] + dy * j < st.h and 0 <= spot[0] + dx * j < st.w and st.grid[spot[1] + dy * j][spot[0] + dx * j] == "m" for j in range(1, k))]
    for dx, dy, k in cands:
        b = (spot[0] + dx * k, spot[1] + dy * k)
        if isinstance(st, _WL_WTS):
            ok = st._open(b) and b not in st.exits and b not in avoid
        else:
            f = st.run.floor
            ok = f.walkable(*b) and f.mover_at(*b) is None and b not in f.exits and b not in avoid
        if ok:
            if isinstance(st, _WL_WTS):
                st.player = st.anim_from = b; st.anim = 0; st.walk_goal = None
            else:
                st.run.player = b; st.anim = 0
            st.step(-dx, -dy)
            return True
    return False


def walk_who(st, text):
    """Where whoever is called text stands on this map (a town: going into its rooms to look), or None."""
    test = text if callable(text) else (lambda o: o.get("text") == text)
    if isinstance(st, _WL_WTS):
        return _wl_town_spot(st, test)
    hit = lambda fl: next((m for m in fl.movers if m.kind in ("figure", "trainer") and isinstance(m.payload, dict) and test(m.payload)), None)
    if hit(st.run.floor) is None:
        for i in range(st.run.n_floors):
            if hit(st.run.made(i)) is not None:
                st.run.enter_floor(i); walk_frames(2)
                break
    m = hit(st.run.floor)
    return (m.x, m.y) if m else None


def walk_meet(st, text, picks=(), n=3000, play=True, fight=True, choose=None):
    """Walk into whoever is called text (or for whom text(option) is true) and play out what follows. Someone with
    several things to do opens the hover list: choose is the button to tap (default: the first). Returns what was said,
    or None if they aren't on the map."""
    walk_said.clear()
    spot = walk_who(st, text)
    if spot is None:
        return None
    if not isinstance(st, _WL_WTS):
        st.run.floor.movers = [m for m in st.run.floor.movers if m.kind != "wild"]
    if not _wl_bump(st, spot):
        return None
    walk_frames(2)
    if g.current_state is st and getattr(st, "hover_buttons", None):
        if not walk_pick(st, choose) if choose else not (st.hover_buttons[0].callback() or True):
            return None
    if play:
        walk_play(picks, n, fight=fight)
    return list(walk_said)


def walk_door(st, kind, picks=(), play=True):
    """Walk through a door of kind (center, mart, gym, house, a named building...) on this town's map. Returns the hover
    list's labels if the door holds several things, else what was said; None if there's no such door, or none you can
    walk to from where you stand."""
    walk_said.clear()
    doors = [t for t, k in sorted(st.doors.items()) if k == kind]
    if not doors:
        return None
    door = next((d for d in doors if st._path(d)), None)   # (one you can walk to from where you stand: a Cut tree can bar it)
    if door is None:
        return None
    if not _wl_bump(st, door):
        return None
    walk_frames(30)
    if getattr(st, "hover_buttons", None) and g.current_state is st:
        return [b.text for b in st.hover_buttons]
    if play:
        walk_play(picks)
    return list(walk_said)


def walk_pick(st, label):
    """Tap a button of the hover list a person or door opened (by its words, ignoring the guide's "> ")."""
    b = next((b for b in getattr(st, "hover_buttons", []) if b.text.lstrip("> ") == label), None)
    if b is None:
        return False
    b.callback()
    return True


def walk_exits(st):
    """The places this map's ways out lead to (a town: its streets; a route: every floor's)."""
    if isinstance(st, _WL_WTS):
        return set(st.exits.values())
    return {t for i in range(st.run.n_floors) for t in st.run.made(i).exits.values()}   # (every floor's: a gate's too)


def walk_out(st, target, n=200):
    """Walk off the map by its way out to target. Returns the state you end in (the same map, with its message, if the
    way is shut)."""
    if not isinstance(st, _WL_WTS) and target not in st.run.floor.exits.values():   # (on another floor: a gate's, a cave's)
        for i in range(st.run.n_floors):
            if target in st.run.made(i).exits.values():
                st.run.enter_floor(i); walk_frames(2)
                break
    ex = st.exits if isinstance(st, _WL_WTS) else st.run.floor.exits
    tiles = sorted(t for t, v in ex.items() if v == target)
    for t in tiles:
        if _wl_bump(st, t, avoid=set(ex)):
            break
    else:
        return None
    for _ in range(n):
        if g.current_state is not st and not type(g.current_state).__name__.endswith("TransitionState"):
            break
        walk_frames()
    walk_play()
    return g.current_state


def walk_fish(p, frames_=60):
    """On a route's map: stand on dry ground beside water and cast (fish_here, as the FISH key does). Returns the state the
    cast leads to (a battle on a bite), or None if this floor has no water to stand beside."""
    f = p.run.floor
    for y in range(f.h):
        for x in range(f.w):
            if not f.walkable(x, y) or f.mover_at(x, y) is not None or (x, y) in f.exits or f.tile(x, y) in (_wl_core.WATER, _wl_core.SURF):
                continue
            if any(f.tile(x + dx, y + dy) in (_wl_core.WATER, _wl_core.SURF) for dx, dy in _wl_core.DIRS):
                p.run.player = (x, y); p.anim = 0; p.mode = "MAP"
                p.fish_here()
                for _ in range(frames_):
                    if g.current_state is not p:
                        break
                    if p.dialogue_box.visible:
                        p.dialogue_box.advance()
                    walk_frames()
                return g.current_state
    return None


def npc(target):
    """A test for walk_meet / walk_who: the person whose option visits target (an NPC option's "target":
    "professor_oak", "mom"...)."""
    return lambda o: o.get("target") == target or any(x.get("target") == target for x in o.get("any") or [])


def walk_ways(st):
    """The ways on from this walked map that would open now, as the map gates them: a town's exits (walk_town._leave:
    its matching travel option, shown), its doors' and people's TRAVEL options (a harbour's boats, the bike list); a
    route's exits on every floor (dungeon._try_exit: no story block). A set of the target areas and the options' words."""
    out = set()
    if isinstance(st, _WL_WTS):
        for t in set(st.exits.values()):
            if str(t).startswith(("OUT:", "ROOM:")):
                continue
            o = st._travel_option(t)
            if o is not None and st._shown(o):
                out |= {t, o.get("text")}
        for kind in set(st.doors.values()):
            for o in st._door_options(kind):
                if str(o.get("action") or "").upper() == "TRAVEL" and st._shown(o):
                    out |= {o.get("target_area") or o.get("target"), o.get("text")}
        for room in [None] + list((st.town_map.get("rooms") or {})):
            if room != getattr(st, "room", None):
                st._go(room, "")
            for o in st._people().values():
                if str(o.get("action") or "").upper() == "TRAVEL":
                    out |= {o.get("target_area"), o.get("text")}
        if getattr(st, "room", None):
            st._go(None, "")
    else:
        story_ = g.story_manager
        pool = st.area_data.get("trainer_pool", [])
        left = any(not story_.is_trainer_defeated(st.area_key, i) for i in range(len(pool)))
        for i in range(st.run.n_floors):
            for t in set(st.run.made(i).exits.values()):
                item = st.exit_items.get(t)
                if item is None or st._exit_block(item, left) not in ("story", "hidden"):
                    out.add(t)
                    if item is not None:
                        out.add(item.get("text"))
    out.discard(None)
    return out


def walk_travel(area, came=None):
    """sub_helpers' travel(area), walked: where this place's map lets you go on now (targets and option words)."""
    return walk_ways(walk_place(area, came))


def walk_state_for(area, came=None):
    """sub_helpers' state_for(area), walked: the place's map."""
    return walk_place(area, came)


def walk_run(area, text, solve=True, came=None, picks=()):
    """sub_helpers' run(area, text), walked: open the place's map, walk up to whoever (or whatever) is called text and
    play out what they say; a battle is left at its start (as run() leaves it). Returns [what was said] (run()'s shape),
    or [] if they aren't on the map now."""
    from src.states import gym_puzzles as _gp
    st = walk_place(area, came)
    said = walk_meet(st, text, picks=picks, fight=False)
    if said is None:
        print(f"   (walk_run: {text!r} isn't on {area}'s map now)")
        return []
    pz = g.current_state
    if isinstance(pz, _gp.GymPuzzleState):
        if not solve:
            pz.answer(next(i for i, o in enumerate(pz.options) if not o[1]))
            pz.leave()
        else:
            while not pz.finished:
                pz.answer(next(i for i, o in enumerate(pz.options) if o[1]))
            pz.on_done(pz.solved)
        walk_play(fight=False)
    return [said]


_WL_MAPS = {}


def walk_map_exits(area):
    """The places a walked town's map (and its rooms) lead to, read from assets/town_maps.json without opening it; None
    if the place has no walked map of its own (a route: its exits are its route_menu's EXITs; a menu region's town)."""
    import json as _json
    if "maps" not in _WL_MAPS:
        _d = _json.load(open("assets/town_maps.json", encoding="utf-8"))
        _WL_MAPS["maps"] = _d.get("maps", _d)
    m = _WL_MAPS["maps"].get(area)
    if not isinstance(m, dict):
        return None
    out = set()
    for part in [m] + list(m.get("floors") or []) + list((m.get("rooms") or {}).values()):
        ex = (part or {}).get("exits") if isinstance(part, dict) else None
        for t in (ex.values() if isinstance(ex, dict) else ex or []):
            t = t if isinstance(t, str) else (t.get("target") if isinstance(t, dict) else None)
            if t and not t.startswith(("ROOM:", "OUT:")):
                out.add(t)
    import re as _re   # (and the rides its people give: Nimbasa's train to Anville - an event's "travel")
    out |= set(_re.findall(r'"travel": "([A-Z0-9_]+)"', _json.dumps(m)))
    a = g.loader.area_data["STORY_PROGRESSION"].get(area) or {}
    out |= {o.get("target_area") for o in (a.get("travel_options") or []) + (a.get("explore_options") or [])
            if o.get("door") and o.get("target_area")}   # (through a door: a harbour's boats, the bike list)
    return out


def walk_sign(st, text, play=False):
    """Walk up to the sign (or panel, or slab) whose event is called text, in this town or one of its rooms, and read it.
    Returns True if there was one to read."""
    for room in [getattr(st, "room", None), None] + list((st.town_map.get("rooms") or {})):
        part = (st.town_map.get("rooms") or {}).get(room) if room else st.town_map
        hit = next((k for k, e in ((part or {}).get("sign_events") or {}).items() if e.get("text") == text), None)
        if hit is None:
            continue
        if room != getattr(st, "room", None):
            st._go(room, ""); walk_frames(2)
        x, y = (int(v) for v in hit.split(","))
        if not _wl_bump(st, (x, y)):
            return False
        walk_frames(2)
        if play:
            walk_play()
        return True
    return False
