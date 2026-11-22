# The live 3D camera (Jordan 11-20, Castelia: "the camera does not tilt" -> "Live 3D camera"; "follow the curve"):
# Black 2's models drawn every frame from its own camera for each place, following you; on the avenue the camera
# circles the city's middle and your keys follow the road's bend. Needs moderngl and an OpenGL 3.3 card: without them
# this suite says so and stops (the game then keeps its baked pictures).
#   bash dev/checks/run.sh live3d
import json
from src.states.overworld import CityState
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.dungeon import live3d

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.live3d_headless = True
story.story_flags["unova_version"] = "BLACK_2"
story.starting_region = "UNOVA"
for _a in ("CASTELIA_CITY",):
    story.story_flags["visited_" + _a] = True


def settle(n=60):
    for _ in range(n):
        st = g.current_state
        if getattr(st, "npc_active", False):
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
            st.dialogue_box.advance()
        st.update(); st.draw()


def town(room=None, at=None):
    g.story_manager.current_area_key = "CASTELIA_CITY"
    g.walk_town_pos = ("CASTELIA_CITY", at, (0, 1)) if at else None
    g.walk_town_room = ("CASTELIA_CITY", room) if room else None
    g.change_state(CityState(g)); settle()
    t = g.current_state
    if room and getattr(t, "room", None) != room:
        t._go(room, None); settle()
    if at:
        t.player = t.anim_from = t.partner = t.partner_from = at; t._remember(); t._live_yaw = None; settle(5)
    return g.current_state


def walk(dx, dy, n):
    out = []
    for _ in range(n):
        settle(1); g.current_state.step(dx, dy, by_key=True); settle(16)
        out.append(tuple(g.current_state.player))
    return out


print("1) the scenes: Black 2's models and cameras, exported")
if not live3d.available(g):
    print("   (no moderngl / OpenGL 3.3 card here: the live camera is off, the baked pictures stay)")
    print(f"##### {len(fails)} failures")
    raise SystemExit
for z in (28, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40):
    check(live3d.has_scene(g, z), f"zone {z}: its 3D scene is in assets/b2_3d")
sc = live3d.scene(g, 31)
check(sc is not None and len(sc.parts) > 20 and sc.cam is not None and abs(float(sc.cam[0]) - 38.0) < 0.5,
      f"Gym Street: its models and Black 2's camera 8 (38 degrees) ({None if sc is None else [round(float(v), 1) for v in sc.cam]})")

import numpy as np
sc = live3d.scene(g, 30)   # (the plaza: what the export left out, put back, 11-21)
kinds = [k for k, _t, _v in sc.parts]
check(kinds.count(3) >= 5, f"the plaza's lamp glows are light sheets, drawn faint ({kinds.count(3)})")
_c = [float(v) for v in sc.cam]
_img = sc.render((480, 360), live3d.follow(21.5, -0.3, 30.5, _c[0], _c[1], 0, _c[2]))
_px = pygame.surfarray.array3d(_img).reshape(-1, 3)
check(not np.all(_px == live3d.KEY, axis=1).any(), "no atlas key colour (magenta) on screen")
_cream = (_px[:, 0] > 245) & (_px[:, 1] > 236) & (_px[:, 2] > 185) & (_px[:, 2] < 210)
check(_cream.mean() < 0.01, f"no solid cream wedges where the lamps' glows are ({_cream.mean():.3f} of the picture)")

print("2) a street: drawn live, the camera following you")
t = town("gym_street", (21, 50))
check(isinstance(t, _WTS) and t._live() is not None, "Gym Street is drawn live")
c1 = t._live_cam()
walk(0, 1, 4)
c2 = g.current_state._live_cam()
check(abs(c2["eye"][2] - c1["eye"][2] - 4) < 0.6 and abs(c2["eye"][0] - c1["eye"][0]) < 0.01,
      f"walking south, the camera moves south with you ({c1['eye']} -> {c2['eye']})")
pygame.image.save(pygame.display.get_surface(), f"{S}/live3d_01_street.png")
v = t._view()
tile = t._tile_at((v.centerx, v.centery + 120))
check(abs(tile[0] - t.player[0]) <= 3 and tile[1] > t.player[1], f"a tap below you picks a tile below you ({tile}, you at {t.player})")

print("2b) ground under every walkable tile (Jordan 11-21: dropped under the avenue's middle); a scene with holes stays flat")
# (11-21 re-export: the avenue's holes were road pieces the skyline filter took out; Route 4's street was 12 rows out of
#  line with its grid (the importer's crop); Narrow Street's mouth onto the plaza is filled from its own ground)
for room, at_ in ((None, (64, 67)), ("route4_street", None), ("narrow_street", None), ("gym_street", (21, 50)),
                  ("castelia_street", None), ("prime_pier", None)):
    t = town(room, at_)
    check(t._live() is not None, f"{room or 'the avenue'}: whole, drawn live ({t._live() is not None})")
_sc = live3d.scene(g, 31)
check(not _sc.covers([(500, 500)]), "a tile with nothing under it counts as a hole (such a place would stay flat)")

print("3) the avenue: the camera circles the city's middle; your keys follow the road's bend")
t = town(None, (64, 67))
y1 = (settle(40), g.current_state._live_yaw)[1]
path = walk(-1, 0, 32)   # (32: still on the avenue; further on, the road runs into a street now that its mouths are ways in)
y2 = (settle(60), g.current_state._live_yaw)[1]
check(path[-1][0] <= 33 and path[-1][1] < 74 and any(p[1] == 74 for p in path),
      f"holding left from the Pokemon Center: round the south bend and up the west side ({path[0]} .. {path[-1]})")
check(y1 is not None and y2 is not None and y1 > 20 and y2 < -25, f"the camera swung round with you (from the south-east bend to the south-west) ({y1:.0f} -> {y2:.0f} degrees)")
pygame.image.save(pygame.display.get_surface(), f"{S}/live3d_02_avenue.png")
up = walk(0, -1, 2)
check(up[0][0] > path[-1][0] or up[0][1] < path[-1][1], f"up: in toward the city ({path[-1]} -> {up})")

print("3b) on the bend: you face the key you press; others turn with the camera; taps aren't turned (Jordan 11-21)")
t = town(None, (34, 74)); settle(60)   # (on the bend, clear of doors: "up" by a doorway now walks in, 11-21)
yaw = t._live_yaw
for key in ((-1, 0), (0, -1), (1, 0), (0, 1)):
    settle(20); t = g.current_state; t.step(*key, by_key=True); settle(4)
    check(t._live_me_face() == key, f"key {key} at the west bend (camera {yaw:.0f} degrees): drawn facing {t._live_me_face()}, the map's facing {tuple(t.facing)}")
settle(20)
check(t._live_face((0, -1)) == (0, -1) or abs(yaw) < 45, "the map's north, turned by under 45 degrees, still looks up")
t = town(None, (34, 74)); settle(60)   # (on the bend, clear of doors: "up" by a doorway now walks in, 11-21)
start = tuple(t.player)
_open = [(start[0] + dx, start[1] + dy) for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)) if t._open((start[0] + dx, start[1] + dy))]
goal = _open[0]
t.walk_goal = goal; settle(30)
check(tuple(g.current_state.player) == goal, f"a tapped tile next to you, on the bend: you step straight onto it ({start} -> {goal}: at {tuple(g.current_state.player)})")
t = town(None, (34, 74)); settle(60)   # (on the bend, clear of doors: "up" by a doorway now walks in, 11-21)
far = (30, 65)
t.walk_goal = far; settle(400)
check(tuple(g.current_state.player) == far, f"a tapped tile up the west side: you walk there ({far}: at {tuple(g.current_state.player)})")

live3d.ALLOW_HOLES = False

print("3c) out of the Center, the Battle Company, Passerby Analytics: back at their door (Jordan 11-21: sent to the entry stairs)")
for door, room in (((64, 66), "center"), ((39, 69), "battle_co"), ((26, 45), "passerby")):
    t = town(None, (door[0], door[1] + 1))
    t._go(room, "OUT:%d,%d" % door); settle(5); t = g.current_state
    way = next(xy for xy, v in t.exits.items() if v == "ROOM:MAIN")
    t._leave("ROOM:MAIN"); settle(5); t = g.current_state
    check(t.room is None and abs(t.player[0] - door[0]) + abs(t.player[1] - door[1]) <= 2,
          f"out of {room}: by its door {door} ({tuple(t.player)})")

print("4) a scene's zoom, shadows, the Options switch, no numpy (11-21)")
t = town("gym_street", (21, 50))
d0 = abs(t._live_cam()["eye"][1] - t._live_cam()["target"][1])
t.npc_zoom(1.25); settle(120)
d1 = abs(t._live_cam()["eye"][1] - t._live_cam()["target"][1])
check(d1 < d0 * 0.9, f"a scene's zoom moves the live camera in ({d0:.1f} -> {d1:.1f} tiles up)")
t.npc_zoom(None); settle(120)
check(getattr(t, "shadows", False), "an oval under everyone's feet, in the scene too")
from src.core import settings
settings.put(g, "live3d", False); settle(3)
check(t._live() is None, "Options, 3D camera: Flat draws the baked pictures")
settings.put(g, "live3d", True)
from src.states.systems.options import OptionsState
o = OptionsState(g, t, lambda: None)
o.tab = o.tabs.index("SCREEN & SOUND")
check(any(r[0] == "3D camera" for r in o.rows()), "Options, SCREEN & SOUND: a 3D camera row")
_np, live3d.np = live3d.np, None   # (a Python without numpy: flat, never a crash)
t = town("plaza", (21, 30))
check(t.room == "plaza" and t._live() is None, "no numpy: the plaza loads and draws flat")
live3d.np = _np
t = town("prime_pier", (16, 20)); settle(5)
pygame.image.save(pygame.display.get_surface(), f"{S}/live3d_03_pier.png")
t = town("plaza", (21, 30)); settle(5)
pygame.image.save(pygame.display.get_surface(), f"{S}/live3d_04_plaza.png")

print("5) off: the baked picture")
g.live3d = False
t = town("gym_street", (21, 50))
check(t._live() is None, "with the live camera off, the baked picture is drawn")
g.live3d = True
print("5) the avenue's street mouths (Jordan 11-21: fell under the road there, couldn't get into the streets)")
live3d.ALLOW_HOLES = False
t = town(None, (64, 67))
_m = t.town_map
_ex = {}
for _y, _r in enumerate(_m["art"]):
    for _x, _c in enumerate(_r):
        if _c in _m["exits"]:
            _ex.setdefault(_m["exits"][_c], []).append((_x, _y))
_sc = t._live()[0]
_lift, _lk = t._live()[1].get("lift") or [], float(t._live()[1].get("lift_k") or 1.0) or 1.0
_near = lambda x, y: float(_lift[y][x]) / _lk + float(t._live()[1].get("base") or 0.0) if 0 <= y < len(_lift) and 0 <= x < len(_lift[y]) else None
# (the street surface nearest the place's own heights, not an awning or ledge over it: 11-21)
_low = [(x, y) for y, r in enumerate(_m["art"]) for x, c in enumerate(r)
        if c == "." and _sc.surfaces(x, y) and min(abs(t._live_height(x, y) - v) for v in _sc.surfaces(x, y)) > 0.05]
_land = lambda ys: min([v for v in ys if v > -1.0] or [99.0])   # (the lowest surface that isn't the sea)
_awning = [(x, y) for y, r in enumerate(_m["art"]) for x, c in enumerate(r)
           if c == "." and _sc._top(x, y, "_kind0", _land) is not None and abs(_near(x, y) or 0) < 1.0
           and t._live_height(x, y) - _sc._top(x, y, "_kind0", _land) > 1.5]   # (on top of something, the street right under it)
check(not _awning, f"nobody stands on an awning or ledge over the avenue: {_awning[:6]}")
check(not _low, f"you stand on the 3D road on every avenue tile (the steps down to the docks too: {_low[:6]})")
for _room in ("ROOM:mode_street", "ROOM:castelia_street", "ROOM:narrow_street", "ROOM:gym_street"):
    t = town(None, (64, 67))   # (back on the avenue each time)
    _tiles = sorted(_ex.get(_room, []))
    _in = None
    for _t in _tiles:
        for _dx, _dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            _s = (_t[0] - _dx, _t[1] - _dy)
            if _in or not t._open(_s) or _s in t.exits:
                continue
            for _key in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                t = town(None, _s)
                settle(1)
                try:
                    t.step(*_key, by_key=True)
                except TypeError:
                    t.step(*_key)
                settle(20)
                if getattr(g.current_state, "room", None) == _room[5:]:
                    _in = (_s, _key)
                    break
    check(_in is not None, f"into {_room[5:]} from the avenue with an arrow key ({_in})")

# 11-21: walking a side street keeps you on its road: no awning, planter or roof underfoot, no hop between tiles
for _room in ("mode_street", "castelia_street", "narrow_street", "gym_street", "route4_street"):
    t = town(_room)
    if not t._live():
        continue
    _H = {(x, y): t._live_height(x, y) for y in range(t.h) for x in range(t.w) if t.rows[y][x] != "#"}
    _hop = [(p, q) for p in _H for q in ((p[0] + 1, p[1]), (p[0], p[1] + 1)) if q in _H and abs(_H[p] - _H[q]) > 0.7]
    check(not _hop, f"{_room}: no sudden step between neighbouring tiles ({_hop[:4]})")
    for _p, _who in t.people.items():
        if "cone" in str(_who).lower():
            check(_H.get(_p, t._live_height(*_p)) < 1.0, f"the Casteliacone seller stands in the street, not on her awning ({round(t._live_height(*_p), 2)})")

# 11-21 (Jordan: "camera angles inside of buildings"): every Castelia room drawn from Black 2's own interior camera
import json as _json
_cm = _json.load(open("assets/town_maps.json", encoding="utf-8"))["CASTELIA_CITY"]["rooms"]
_flat = []
for _room, _r in _cm.items():
    if not str(((_r.get("roofs") or {}).get("_picture") or {}).get("f") or "").startswith("b2_ground/"):
        continue
    t = town(_room)
    if not t._live():
        _flat.append(_room)
check(not _flat, f"every Castelia room in the live 3D view (not the flat picture): {_flat}")
t = town("studio")
check(t._live() and t._live()[0].indoor and not live3d.scene(g, 28).indoor, "a room is drawn on black, the streets under the sky")
for _room, _lv in (("gym", 0.0), ("gym_10", 10.0), ("gym_20", 20.0)):
    t = town(_room)
    _op = [(x, y) for y in range(t.h) for x in range(t.w) if t._open((x, y))]
    _off = [p for p in _op if abs(t._live_height(*p) - _lv) > 0.6]
    check(t._live() and not _off, f"the Gym's {_room}: you stand on its own floor ({_lv}) everywhere ({_off[:4]})")

# 11-21 (Jordan: "entering the castelia pokemon center, It entered me behind the counter of the pokemart and I am now stuck")
t = town(None, (64, 67))
_door = next(d for d, k in t.doors.items() if k == "center")
t._enter(_door); settle(5)
t = g.current_state
check(getattr(t, "room", None) == "center" and t._reaches_out(tuple(t.player)) and t.player[1] >= 17,
      f"in by the Center's door: just inside it, free to walk out ({getattr(t, 'room', None)}, {t.player})")
g.walk_town_pos, g.walk_town_room = ("CASTELIA_CITY", (12, 17), (0, 1)), ("CASTELIA_CITY", "center")
g.change_state(CityState(g)); settle()
t = g.current_state
check(t.room == "center" and t._reaches_out(tuple(t.player)), f"a spot saved shut in behind the Mart counter: back at the Center's door ({t.player})")

# 11-21 (Jordan: "Do the three live 3D todos for the earlier Unova places"): every Unova place built before Castelia
import os as _os
import numpy as _np


def place(area, room=None, at=None):
    story.current_area_key = area
    story.story_flags["visited_" + area] = True
    g.walk_town_pos = None
    g.walk_town_room = (area, room) if room else None
    g.change_state(CityState(g)); settle(4)
    t = g.current_state
    if room and getattr(t, "room", None) != room:
        t._go(room, None); settle(3)
        t = g.current_state
    if at:
        t.player = t.anim_from = t.partner = t.partner_from = at; t._remember(); t._live_yaw = None; settle(12)
    return g.current_state


_all = _json.load(open("assets/town_maps.json", encoding="utf-8"))
_flatp, _holed, _skyp = [], [], []
for _area, _m in _all.items():
    if not isinstance(_m, dict):
        continue
    for _rn, _r in [(None, _m)] + list((_m.get("rooms") or {}).items()):
        _f = str(((_r.get("roofs") or {}).get("_picture") or {}).get("f") or "") if isinstance(_r, dict) else ""
        if not _f.startswith("b2_ground/") or int(_os.path.splitext(_os.path.basename(_f))[0]) < 427:
            continue
        t = place(_area, _rn)
        _name = _area + ("/" + _rn if _rn else "")
        if not t._live():
            _flatp.append(_name)
            continue
        _sc = t._live()[0]
        _op = [(x, y) for y in range(t.h) for x in range(t.w) if t._open((x, y))]
        if not _sc.covers(_op):
            _holed.append(_name)
        if not _sc.indoor and _rn is None:   # (outdoors: from each corner, the land round it, not the sky)
            for _c in (min(_op, key=lambda p: p[0] + p[1]), max(_op, key=lambda p: p[0] + p[1]),
                       min(_op, key=lambda p: p[0] - p[1]), max(_op, key=lambda p: p[0] - p[1])):
                t.player = t.anim_from = t.partner = t.partner_from = _c; t._remember(); t._live_yaw = None; settle(6)
                t.draw()
                _px = pygame.surfarray.array3d(pygame.display.get_surface().subsurface((298, 86, 826, 624))).astype(int)
                _sky = float((_np.abs(_px - _np.array([150, 190, 235])).sum(2) < 12).mean())
                if _sky > 0.2:
                    _skyp.append((_name, _c, round(_sky, 2)))
check(not _flatp, f"every Unova place built before Castelia opens in the live 3D view ({_flatp})")
check(not _holed, f"...with ground under every tile you walk on ({_holed})")
check(not _skyp, f"...and from an outdoor place's corners, the land round it, not the sky (its world-map neighbours) ({_skyp[:4]})")
for _area in ("ASPERTIA_CITY", "FLOCCESY_TOWN", "VIRBANK_CITY", "CASTELIA_CITY"):
    t = place(_area, "center")
    check(not any(t._open(p) for p in ((5, 8), (9, 8), (6, 10), (12, 17))),
          f"{_area}'s Center: no stepping off the upper floor behind the counter, nor into the pocket behind the Mart's")
t = place("UNOVA_ROUTE_20")
_op = [(x, y) for y in range(t.h) for x in range(t.w) if t._open((x, y))]
_H = {p: t._live_height(*p) for p in _op}
_cl = [(p, q) for p in _H for q in ((p[0] + 1, p[1]), (p[0], p[1] + 1)) if q in _H and abs(_H[p] - _H[q]) > 1.5]
check(len(_cl) <= 15, f"Route 20: you walk its terraces, not halfway up their cliffs (a cliff's face isn't ground): {len(_cl)} big steps")
t = place("VIRBANK_CITY", "nursery")
_op = [(x, y) for y in range(t.h) for x in range(t.w) if t._open((x, y))]
check(t._live() and all(t._live()[0].surfaces(*p) for p in _op), "Virbank's nursery: its model lined up with its walk grid (it sat 10 tiles off)")

# 11-21 (Jordan: "Run the remaining castelia checks for the 45 earlier places, and remember those going forward")
_high, _slow = [], []
import time as _time
for _area, _m in _all.items():
    if not isinstance(_m, dict):
        continue
    for _rn, _r in [(None, _m)] + list((_m.get("rooms") or {}).items()):
        _f = str(((_r.get("roofs") or {}).get("_picture") or {}).get("f") or "") if isinstance(_r, dict) else ""
        if not _f.startswith("b2_ground/"):
            continue
        t = place(_area, _rn)
        if not t._live():
            continue
        for _p in t.people:   # (nobody up on an awning, a roof or a counter: level with the ground beside them)
            _nb = [t._live_height(*q) for q in ((_p[0] + 1, _p[1]), (_p[0] - 1, _p[1]), (_p[0], _p[1] + 1), (_p[0], _p[1] - 1)) if t._open(q)]
            if _nb and t._live_height(*_p) - max(_nb) > 1.5:
                _high.append((_area, _rn, _p, round(t._live_height(*_p), 1)))
        _t0 = _time.time()
        for _ in range(10):
            t.draw()
        if (_time.time() - _t0) / 10 > 0.04:
            _slow.append((_area, _rn))
check(not _high, f"nobody in Unova stands up on an awning, a roof or a counter ({_high[:4]})")
check(not _slow, f"every live place draws a frame in under 40 ms ({_slow[:4]})")
t = place("ASPERTIA_CITY", None, (3, 8))
check(abs(t._live_height(3, 8) - 9.0) < 0.5 and t._cam_zone(3, 8),
      f"Aspertia's Outlook: up its stairs, on its deck ({round(t._live_height(3, 8), 1)}), the camera sliding north over the edge")

# 11-21 (Jordan: "Yes, block them"): no stepping off one level onto another (both the 3D ground and Black 2's heights
# say it's a drop), and nothing you need cut off by it
t = place("VIRBANK_CITY", None, (15, 19))
t.step(-1, 0); settle(20)
check(tuple(g.current_state.player) == (15, 19), f"Virbank: no stepping off the street down onto the canal walkway, 3.5 below ({g.current_state.player})")
t = g.current_state
_pp = t._path((14, 19))
check(t._level_edge((15, 19), (14, 19)) and (not _pp or _pp[0] != (14, 19)),
      f"...and a tapped path won't drop straight off either (it goes the long way round, under the bridge: {len(_pp)} steps)")
_lost = []
for _area, _m in _all.items():
    if not isinstance(_m, dict):
        continue
    for _rn, _r in [(None, _m)] + list((_m.get("rooms") or {}).items()):
        _f = str(((_r.get("roofs") or {}).get("_picture") or {}).get("f") or "") if isinstance(_r, dict) else ""
        if not _f.startswith("b2_ground/"):
            continue
        t = place(_area, _rn)
        if not t._live():
            continue
        _N = ((0, 1), (0, -1), (1, 0), (-1, 0))

        def _reach(block):
            seen, todo = set(), []
            for e in list(t.exits) + list(t.doors):
                for dx, dy in _N:
                    q = (e[0] + dx, e[1] + dy)
                    if t._open(q) and q not in t.exits:
                        seen.add(q); todo.append(q)
            while todo:
                x, y = todo.pop()
                for dx, dy in _N:
                    q = (x + dx, y + dy)
                    if q in seen or not t._open(q) or q in t.exits or q in t.doors or (block and t._level_edge((x, y), q)):
                        continue
                    seen.add(q); todo.append(q)
            return seen
        _b, _a = _reach(False), _reach(True)
        _near = lambda T, S: any((T[0] + dx, T[1] + dy) in S for dx, dy in _N)
        _lost += [(_area, _rn, k, e) for k, es in (("exit", t.exits), ("door", t.doors), ("person", t.people)) for e in es if _near(e, _b) and not _near(e, _a)]
check(not _lost, f"blocking the drops cuts nobody and no way out off ({_lost[:4]})")
t = place("ASPERTIA_CITY", None, (3, 8))
check(any(t._open(q) for q in ((4, 6),)) and not t._level_edge((10, 21), (11, 21)), "Aspertia: the way up to the Outlook (and Bianca) stays open")

# 11-21 (Jordan: "Bring live 3D to the route walker first"): the route-type places, walked by the route walker
# (dungeon.DungeonState + dungeon_live.RouteLive) as the game itself hands them out, not opened as towns
from src.states.overworld import PlayState as _PS
_rflat, _rcut, _rsky, _rslow = [], [], [], []
_N4 = ((0, 1), (0, -1), (1, 0), (-1, 0))
for _area in ("UNOVA_ROUTE_19", "UNOVA_ROUTE_20", "PLEDGE_GROVE", "FLOCCESY_RANCH", "FLOCCESY_RANCH_OUTSIDE", "CASTELIA_SEWERS",
              "VIRBANK_COMPLEX", "VIRBANK_COMPLEX_OUTSIDE", "CASTELIA_EMPTY_LOT", "LIBERTY_GARDEN", "ROYAL_UNOVA"):
    story.current_area_key = _area
    story.story_flags["visited_" + _area] = True
    g.walk_town_pos = g.walk_town_room = None
    g.change_state(_PS(g)); settle(6)
    t = g.current_state
    if type(t).__name__ != "DungeonState" or not t._dl_live():
        _rflat.append((_area, type(t).__name__))
        continue
    _f = t.run.floor
    _W = {(x, y) for y in range(_f.h) for x in range(_f.w) if _f.walkable(x, y)}

    def _rreach(block):
        seen, todo = set(), []
        for e in _f.exits:
            for dx, dy in _N4:
                q = (e[0] + dx, e[1] + dy)
                if q in _W:
                    seen.add(q); todo.append(q)
        while todo:
            x, y = todo.pop()
            for dx, dy in _N4:
                q = (x + dx, y + dy)
                if q in seen or q not in _W or (block and t._level_edge((x, y), q)):
                    continue
                seen.add(q); todo.append(q)
        return seen
    _b0, _b1 = _rreach(False), _rreach(True)
    _nr = lambda T, S: T in S or any((T[0] + dx, T[1] + dy) in S for dx, dy in _N4)
    _rcut += [(_area, m.kind, (m.x, m.y)) for m in _f.movers if _nr((m.x, m.y), _b0) and not _nr((m.x, m.y), _b1)]
    _rcut += [(_area, "exit", e) for e in _f.exits if _nr(e, _b0) and not _nr(e, _b1)]
    _op = sorted(_W)
    for _c in (min(_op, key=lambda p: p[0] + p[1]), max(_op, key=lambda p: p[0] + p[1]),
               min(_op, key=lambda p: p[0] - p[1]), max(_op, key=lambda p: p[0] - p[1])):
        t.run.player = t.anim_from = t.partner = t.partner_from = _c; t.anim = 0
        t.draw()
        _px = pygame.surfarray.array3d(pygame.display.get_surface().subsurface(t._view())).astype(int)
        _sky = float((_np.abs(_px - _np.array([150, 190, 235])).sum(2) < 12).mean())
        if _sky > 0.2:
            _rskyp = (_area, _c, round(_sky, 2)); _rsky.append(_rskyp)
    _t0 = _time.time()
    for _ in range(10):
        t.draw()
    if (_time.time() - _t0) / 10 > 0.04:
        _rslow.append(_area)
check(not _rflat, f"every Unova route-type place is walked in the live 3D view by the route walker, as in play ({_rflat})")
check(not _rcut, f"...no drop blocked there cuts off a person or a way out ({_rcut[:4]})")
check(not _rsky, f"...no sky from their corners (Floccesy Ranch, its own small map, gets its ground laid past its edges) ({_rsky[:4]})")
check(not _rslow, f"...each under 40 ms a frame ({_rslow})")
story.current_area_key = "CASTELIA_SEWERS"; g.walk_town_pos = g.walk_town_room = None
g.change_state(_PS(g)); settle(6)
t = g.current_state
check(t._dl_live() and abs(t._dl_height(46, 19) - 4.5) < 0.3 and abs(t._dl_height(50, 19) - 0.5) < 0.3,
      f"the Sewers' stairs up to the Empty Lot: you climb them, not walk under them ({round(t._dl_height(46, 19), 1)})")

print(f"##### {len(fails)} failures")
