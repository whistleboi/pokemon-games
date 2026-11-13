# Hoenn's maps from the Emerald file (11-12): every rebuilt map opened in the game the way a player meets it, its ways
# out and doors, its people, and the story scenes played through. Glue after harness_head.py:
#   cat dev/checks/harness_head.py dev/checks/hoenn_maps_body.py > dev/checks/out/check_hoenn_maps.py
#   python dev/checks/out/check_hoenn_maps.py <scratch folder>
import json
from collections import deque
from src.states.overworld import PlayState, CityState
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.states.overworld.dungeon import DungeonState
from src.states.menus import StarterSelectionState as _SSS

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True
story.story_flags["hoenn_version"] = "OMEGA_RUBY"
_tm = json.load(open("assets/town_maps.json", encoding="utf-8"))
_area = g.loader.area_data["STORY_PROGRESSION"]
import importlib.util as _u
_spec = _u.spec_from_file_location("emerald", "dev/builders/town_maps/emerald.py")
_em = _u.module_from_spec(_spec); _spec.loader.exec_module(_em)
BUILT = list(_em.HOENN)


def tap(st, n=600):
    for _ in range(n):
        if getattr(st, "npc_active", False):
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif getattr(st, "dialogue_box", None) is not None and st.dialogue_box.visible:
            st.dialogue_box.advance()
        else:
            return
        st.update(); st.draw()


def frames(n):
    for _ in range(n):
        g.current_state.update(); g.current_state.draw()


def open_map(key, came):
    story.current_area_key, story.last_area_key = key, came
    g.walk_town_pos = None
    st = CityState(g) if _area[key].get("area_type") == "town" else None
    if st is None or not isinstance(st, _WTS):
        st = PlayState(g); g.states["play"] = st
    g.change_state(st)
    frames(2)
    tap(g.current_state)
    return g.current_state


# ---- every rebuilt map: opens on its own map, from each way in, and everything on it can be reached
story.story_flags.update({"received_pokedex_hoenn": True, "helped_wally": True, "hoenn_birch_thanked": True, "hoenn_rival_103": True})
for key in BUILT:
    m = _tm[key]
    a = _area.get(key, {})
    _parts = m["floors"] if m.get("floors") else [m]
    targets = set(v for f in _parts for v in f.get("exits", {}).values())
    known = {o.get("target_area") or o.get("target") for o in a.get("travel_options", []) + a.get("route_menu", []) + a.get("explore_options", [])}
    check(targets <= known, f"{key}: every way out on the map is a way out in the story data {sorted(targets - known)}")
    came = sorted(targets)[0] if targets else key
    st = open_map(key, came)
    is_town = isinstance(st, _WTS)
    w, h = (st.w, st.h) if is_town else (st.run.floor.w, st.run.floor.h)
    _here = _parts[st.run.index] if (not is_town and m.get("floors")) else m
    check((w, h) == (len(_here["art"][0]), len(_here["art"])) and (is_town or isinstance(st, DungeonState)),
          f"{key}: opens on its Emerald map ({w} x {h}, {'town' if is_town else 'route'}), in from {came}")
    grid = _here["art"]
    if m.get("floors"):  # (a place of floors: every passage leads to a tile on a floor that exists)
        _bad = [(i, k, to) for i, f in enumerate(m["floors"]) for k, to in (f.get("links") or {}).items()
                if not (0 <= to[0] < len(m["floors"]) and 0 <= to[2] < len(m["floors"][to[0]]["art"]) and 0 <= to[1] < len(m["floors"][to[0]]["art"][0]))]
        check(not _bad and all(f["art"][int(k.split(",")[1])][int(k.split(",")[0])] == "1" for f in m["floors"] for k in (f.get("links") or {})),
              f"{key}: {len(m['floors'])} floors joined by Emerald's own ladders and passages {_bad[:3]}")
    elif not m.get("parts"):
        walk = set(".=\"NX!ow$[]{}%_()D<>^vnwu20b:|;,'")   # (' round stones: crossed on the Bicycle)
        starts = [(x, y) for y, r in enumerate(grid) for x, c in enumerate(r) if c in "<>^vnwu"]
        _back = [(x, y - 1) for x, y in map(tuple, m.get("back_doors", []))]   # (a yard reached by a back door: Lavaridge's hot springs)
        seen, todo = set(starts[:1] + _back), deque(starts[:1] + _back)
        while todo:
            x, y = todo.popleft()
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                t = (x + dx, y + dy)
                if 0 <= t[0] < w and 0 <= t[1] < h and t not in seen and grid[t[1]][t[0]] in walk:
                    seen.add(t); todo.append(t)
        cut = [(x, y, c) for y, r in enumerate(grid) for x, c in enumerate(r) if c in "<>^vnwuDNX" and (x, y) not in seen]
        check(not cut, f"{key}: every way out, door, person and trainer is reachable from the first way out {cut[:4]}")
    texts = [p.get("text") if isinstance(p, dict) else p for f in _parts for p in f.get("people", []) if isinstance(p, (dict, str))]
    check(len(texts) == len(set(texts)), f"{key}: each person has a name of their own")

# ---- ways between places (11-12, rewritten from the dungeon suite's old Hoenn checks): in from each way, you stand beside
# it; and where two places are joined several separate ways (Route 116 and Rusturf Tunnel, Route 112 and the Fiery Path,
# Routes 111 and 112, the Woods' three doors), out by one you come in by its own, and back by it you're where you left
from src.dungeon import core as _core


def _exits(st):
    return dict(st.exits) if isinstance(st, _WTS) else dict(st.run.floor.exits)


def _pos(st):
    return tuple(st.player) if isinstance(st, _WTS) else tuple(st.run.player)


def arrive(key, came, idx=None, cnt=None, tile=None):
    """Open key as if you'd left came by its idx-th tile (of cnt) leading here: tile, that one (its edge partner, if it has one)."""
    if idx is not None:
        g.walk_town_exit = (came, idx, cnt)
        _core.ENTRANCE_INDEX, _core.ENTRANCE_COUNT = idx, cnt
    _to = (_tm[came].get("edge_to") or {}).get("%d,%d" % tuple(tile)) if tile is not None and came in _tm else None
    g.arrive_edge = (came, key, tuple(_to)) if _to else None
    st = open_map(key, came)
    g.walk_town_exit = None
    _core.ENTRANCE_INDEX = _core.ENTRANCE_COUNT = 0
    return st


def _near(p, tiles, d=2):
    return any(abs(p[0] - t[0]) + abs(p[1] - t[1]) <= d for t in tiles)


def _groups(tiles):
    """Separate mouths: tiles touching each other, in the order the game counts them."""
    out = []
    for t in tiles:
        grp = next((q for q in out if any(abs(t[0] - u[0]) + abs(t[1] - u[1]) == 1 for u in q)), None)
        if grp is not None:
            grp.append(t)
        else:
            out.append([t])
    return out


_far, _pairs = [], []
for key in BUILT:
    _parts = _tm[key]["floors"] if _tm[key].get("floors") else [_tm[key]]
    for came in sorted({v for f in _parts for v in f.get("exits", {}).values()} & set(BUILT)):
        st = arrive(key, came)
        own = [t for t, v in _exits(st).items() if v == came]
        if own and not _near(_pos(st), own):
            _far.append((key, came, _pos(st)))
        if key < came:
            _pairs.append((key, came))
check(not _far, f"every rebuilt map: in from each way, you stand beside that way {_far[:4]}")
_bad, _multi = [], 0
for a, b in _pairs:
    for x, y in ((a, b), (b, a)):
        if _tm[x].get("floors") or _tm[y].get("floors"):  # (a map of floors: its own section below)
            continue
        st = arrive(x, y)
        ta = [t for t, v in _exits(st).items() if v == y]
        mouths = _groups(ta)
        if len(mouths) < 2:
            continue
        _multi += 1
        for m in mouths:
            i = ta.index(m[len(m) // 2])
            sb = arrive(y, x, i, len(ta), tile=ta[i])
            tb = [t for t, v in _exits(sb).items() if v == x]
            j = min(range(len(tb)), key=lambda k: abs(tb[k][0] - _pos(sb)[0]) + abs(tb[k][1] - _pos(sb)[1])) if tb else 0
            back = arrive(x, y, j, len(tb), tile=tb[j] if tb else None)
            if not _near(_pos(back), m):
                _bad.append((x, y, m[0], _pos(sb), _pos(back)))
check(_multi >= 4 and not _bad, f"places joined several ways ({_multi} sides): out by each mouth and straight back, you're at that mouth again {_bad[:3]}")

# every door in a rebuilt town opens something (a house is just a house; the Center and Mart: the shared rooms), but the
# places not built yet (HANDOFF_HOENN_MAPS.md's gaps: Rustboro's Trainer's School, Slateport's Fan Club and its harbor's ferry)
NOT_YET = {("RUSTBORO_CITY", "school"), ("SLATEPORT_CITY", "fanclub"), ("SLATEPORT_CITY", "harbor")}   # (Slateport's ferry: once the sub is taken)
_shut = []
for key in BUILT:
    if _area[key].get("area_type") != "town":
        continue
    st = arrive(key, sorted(_tm[key]["exits"].values())[0])
    for t, kind in st.doors.items():
        if kind not in ("house", "center", "mart") and not st._door_options(kind) and (key, kind) not in NOT_YET:
            _shut.append((key, kind))
check(not _shut, f"every door in a rebuilt town opens something {sorted(set(_shut))[:6]}")
import os as _os
_pics = [(k, o.get("f")) for k in BUILT for f in (_tm[k]["floors"] if _tm[k].get("floors") else [_tm[k]])
         for o in (f.get("overheads") or []) + [f.get("roofs", {}).get("_picture") or {}] if isinstance(o, dict) and o.get("f")]
_gone = [(k, f) for k, f in _pics if not _os.path.exists(_os.path.join("assets", "tiles", f))]
check(len(_pics) >= len(BUILT) and not _gone, f"every rebuilt map's picture and the layer drawn over you are there ({len(_pics)}) {_gone[:3]}")
_mv_maps = [k for k in BUILT if not _tm[k].get("floors") and _tm[k].get("moves") and _area[k].get("area_type") != "town"]
st = arrive(_mv_maps[0], sorted(_tm[_mv_maps[0]]["exits"].values())[0])
_moving = sum(1 for m in st.run.floor.movers if getattr(m, "motion", None) is not None or st._motion(m) is not None)
check(_moving > 0, f"people move as Emerald moves them ({len(_mv_maps)} routes with moving people; {_mv_maps[0]}: {_moving})")


def _reach(st):
    """The ground you can walk from where you stand (floor and grass), hopping ledges only their own way, as you walk them."""
    f = st.run.floor
    ok = lambda t: 0 <= t[0] < f.w and 0 <= t[1] < f.h and f.tiles[t[1]][t[0]] in (_core.FLOOR, _core.GRASS)
    seen, todo = {tuple(st.run.player)}, [tuple(st.run.player)]
    while todo:
        x, y = todo.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if str(f.decor.get(n, "")) == f"ledge:{dx},{dy}":  # (a ledge from its high side: over it)
                n = (n[0] + dx, n[1] + dy)
            if n not in seen and ok(n):
                seen.add(n); todo.append(n)
    return seen


def _by(seen, st, who):
    ways = [t for t, v in st.run.floor.exits.items() if v == who]
    return any(_near(n, ways, 1) for n in seen)


# Rusturf Tunnel: the cracked rock before Verdanturf
_rs = story.inventory.pop("HM_ROCK_SMASH", None)
st = arrive("HOENN_RUSTURF_TUNNEL", "HOENN_ROUTE_116")
_g1 = st._gate("VERDANTURF_TOWN")
story.inventory["HM_ROCK_SMASH"] = 1
_g2 = st._gate("VERDANTURF_TOWN")
check(_g1 and tuple(_g1[:3]) == ("rock", "ROCK SMASH", False) and _g2[2], f"Rusturf Tunnel: a cracked rock before Verdanturf until Rock Smash ({_g1})")
if _rs is None:
    story.inventory.pop("HM_ROCK_SMASH", None)
# Granite Cave: fallen rocks bar the short way to Steven's side till you've met him
_ms = story.story_flags.pop("met_steven", None)
st = arrive("HOENN_GRANITE_CAVE", "HOENN_ROUTE_106")
_rub = []
for _i in range(st.run.n_floors):
    st.run.made(_i)
    st.run.index = _i
    st._clear_boulders()
    _rub += [(_i, t) for t, v in st.run.floor.decor.items() if str(v).startswith("rubble:")]
story.story_flags["met_steven"] = True
_open = []
for _i, t in _rub:
    st.run.index = _i
    st._clear_boulders()
    _open.append(st.run.floor.walkable(*t))
check(_rub and all(_open), f"Granite Cave: fallen rocks bar the short way {_rub} till you've met Steven, then they're gone")
if _ms is None:
    story.story_flags.pop("met_steven", None)
# (by here in the story you carry Cut and Rock Smash: the small trees and cracked rocks are out of the way)
_hm_had = {k: story.inventory.get(k) for k in ("HM_CUT", "HM_ROCK_SMASH")}
story.inventory.update({"HM_CUT": 1, "HM_ROCK_SMASH": 1})
# Route 110: the Cycling Road a deck of its own, its gates barred without a Bicycle; underneath, Slateport to Mauville on foot
_bk = story.inventory.pop("BICYCLE", None)
st = arrive("HOENN_ROUTE_110", "SLATEPORT_CITY")
st._clear_boulders()
_bars = [t for t, b in st._bars.items() if b.get("item") == "BICYCLE"]
_shut110 = [str(st.run.floor.decor.get(t, "")) for t in _bars]
_walk110 = _by(_reach(st), st, "MAUVILLE_CITY")
story.inventory["BICYCLE"] = 1
st._clear_boulders()
check(st.run.n_floors == 2 and _bars and all(v.startswith("barrier:") for v in _shut110) and all(st.run.floor.walkable(*t) for t in _bars) and _walk110,
      f"Route 110: the Cycling Road is a deck of its own; its gates {_bars} barred without a Bicycle ({_shut110}), open with one; underneath you walk from Slateport to Mauville ({_walk110})")
if _bk is None:
    story.inventory.pop("BICYCLE", None)
# Route 111: the sandstorm bars the way north without the Go-Goggles; the junction to Route 112 stays open
_gg = story.inventory.pop("GO_GOGGLES", None)
st = arrive("HOENN_ROUTE_111", "MAUVILLE_CITY")
st._clear_boulders()
_dry = _reach(st)
_dry113, _dry112 = _by(_dry, st, "HOENN_ROUTE_113"), _by(_dry, st, "HOENN_ROUTE_112")
story.inventory["GO_GOGGLES"] = 1
st._clear_boulders()
_wet113 = _by(_reach(st), st, "HOENN_ROUTE_113")
check(not _dry113 and _dry112 and _wet113,
      f"Route 111: the sandstorm bars the way to Route 113 without the Go-Goggles ({_dry113}), not the junction to Route 112 ({_dry112}); with them you cross ({_wet113})")
if _gg is None:
    story.inventory.pop("GO_GOGGLES", None)
# Route 112: in from Route 111 at the south: the ledges hop east only; the Fiery Path and the cable car yes; Lavaridge, the Jagged Pass, the north hill no
_r111 = arrive("HOENN_ROUTE_111", "HOENN_ROUTE_112")
_w111 = [t for t, v in _r111.run.floor.exits.items() if v == "HOENN_ROUTE_112"]
st = arrive("HOENN_ROUTE_112", "HOENN_ROUTE_111", len(_w111) - 1, len(_w111))   # (by Route 111's southmost tile)
_s112 = _reach(st)
_hill = [t for t, v in st.run.floor.exits.items() if v == "HOENN_ROUTE_111" and t[1] < 20]
check(_pos(st)[1] > 40 and _by(_s112, st, "HOENN_FIERY_PATH") and not _by(_s112, st, "LAVARIDGE_TOWN") and not _by(_s112, st, "HOENN_JAGGED_PASS")
      and not any(_near(n, _hill, 1) for n in _s112) and "door:cablecar" in st.run.floor.decor.values() and any(str(v).startswith("ledge:1,") for v in st.run.floor.decor.values()),
      f"Route 112: in from Route 111 at {_pos(st)}: the Fiery Path and the cable car, not Lavaridge or the Jagged Pass past the east-hopping ledges, nor the north hill")

for _k, _v in _hm_had.items():
    if _v is None:
        story.inventory.pop(_k, None)
    else:
        story.inventory[_k] = _v
# a trainer who sees you walks up for a battle (Emerald's own sight lines, the trainers' "range")
_spot = None
for _key in ("HOENN_ROUTE_102", "HOENN_ROUTE_104", "HOENN_ROUTE_116", "HOENN_ROUTE_117", "HOENN_ROUTE_110"):
    st = arrive(_key, sorted(_tm[_key]["exits"].values())[0])
    f = st.run.floor
    for m in f.movers:
        if m.kind != "trainer" or not getattr(m, "facing", None):
            continue
        dx, dy = m.facing
        line = [(m.x + dx * k, m.y + dy * k) for k in (1, 2, 3)]
        if all(f.walkable(*t) and f.mover_at(*t) is None for t in line):
            _spot = (st, m, line)
            break
    if _spot:
        break
_fought = None
if _spot:
    st, m, line = _spot
    st.run.player, st.anim = line[2], 0
    st.facing = (-m.facing[0], -m.facing[1])
    st.step(-m.facing[0], -m.facing[1])   # (one step into its sight)
    for _ in range(400):
        if g.current_state is not st:
            break
        if st.dialogue_box.visible:
            st.dialogue_box.advance()
        st.update(); st.draw()
    _fought = type(g.current_state).__name__
check(_spot is not None and _fought and "Trainer" in _fought,
      f"a trainer who sees you walks up and battles ({_spot and _spot[0].area_key}, {_spot and (_spot[1].x, _spot[1].y)}: {_fought})")

# the towns' own doors (Emerald's buildings; the games' places in them)
_want_doors = {"LITTLEROOT_TOWN": {"home", "rival", "lab"}, "RUSTBORO_CITY": {"devon", "gym", "center", "mart"},
               "SLATEPORT_CITY": {"museum", "shipyard", "contest"}, "MAUVILLE_CITY": {"bike", "game corner", "gym"},
               "VERDANTURF_TOWN": {"contest", "wally"}, "FALLARBOR_TOWN": {"cozmo", "contest"}}
for key, want in _want_doors.items():
    st = arrive(key, sorted(_tm[key]["exits"].values())[0])
    have = set(st.doors.values())
    check(want <= have and all(st._door_options(k) for k in want), f"{key}: its own doors {sorted(want)}, each opening something (has {sorted(have)})")

# ---- story scenes, played as a player meets them
def walk_into(st, way, n=1):
    for _ in range(n):
        st.anim = 0
        st.step(*way)
        frames(STEP_WAIT)


STEP_WAIT = 12
_saved = dict(story.story_flags)

# Route 101: Birch chased by a Poochyena; after the battle he walks up and you go to the lab
for k in ("received_starter_hoenn", "hoenn_birch_rescued", "hoenn_birch_walked_up", "hoenn_birch_thanked"):
    story.story_flags.pop(k, None)
_team = list(story.player_team); story.player_team = []
story.current_area_key, story.last_area_key = "HOENN_ROUTE_101", "LITTLEROOT_TOWN"
p = PlayState(g); g.states["play"] = p; g.change_state(p); frames(2)   # (not tapped through: the opening's lines are still up)
_bars = {t: b.get("look") for t, b in getattr(p, "_bars", {}).items()}
check(_bars.get((9, 13)) == "sheet:em_64.png" and _bars.get((10, 13)) == "mon:261" and _bars.get((7, 14)) == "ow:em:bag",
      f"Route 101: Birch, the Poochyena and his bag stand where Emerald has them {_bars}")


def adv(n, stop):
    for _ in range(n):
        s = g.current_state
        if stop(s):
            return True
        if getattr(s, "dialogue_box", None) is not None and s.dialogue_box.visible:
            s.dialogue_box.advance()
        s.update(); s.draw()
    return False


_s1 = adv(400, lambda s: isinstance(s, _SSS))
if _s1:
    g.current_state.load_starters(); g.current_state.selected_idx = 0; g.current_state.complete_selection()
_s2 = adv(400, lambda s: "Battle" in type(s).__name__)
if _s2:
    g.current_state.player_won = True; g.current_state.exit_battle()
_walk = [False]
def _seen_walker(s):
    _walk[0] = _walk[0] or bool(getattr(s, "_walker", None))
    return story.current_area_key == "LITTLEROOT_TOWN"
_s3 = adv(600, _seen_walker)
check(_s1 and _s2 and _walk[0] and _s3 and story.story_flags.get("hoenn_birch_walked_up"),
      f"Route 101: pick a starter, beat the Poochyena, Birch walks up and you head to Littleroot ({_s1}, {_s2}, {_walk[0]}, {_s3})")
story.story_flags.clear(); story.story_flags.update(_saved); story.player_team = _team or [mk(258)]
story.story_flags["hoenn_version"] = "OMEGA_RUBY"

# Oldale: no Pokedex, west exit: the footprint man walks up, talks, steps you back
story.story_flags.pop("received_pokedex_hoenn", None)
t = open_map("OLDALE_TOWN", "HOENN_ROUTE_101")
home = next(h for h, o in t.people.items() if o.get("text") == "Path to Route 102")
t.player = (2, 10); walk_into(t, (-1, 0))
for _ in range(400):
    if t.npc_active: break
    frames(1)
_talked = t.npc_active
tap(t); frames(150)
check(_talked and t.player == (2, 10) and t.motions[home].pos == home, f"Oldale: the footprint man stops you at the west exit and walks back ({t.player}, {t.motions[home].pos})")
story.story_flags["received_pokedex_hoenn"] = True

# (Oldale's Mart clerk: ORAS's version, below: he runs up as you arrive)

# Route 103: the rival walks up to battle
story.story_flags.pop("hoenn_rival_103", None)
p = open_map("HOENN_ROUTE_103", "OLDALE_TOWN")
rv = next((m for m in p.run.floor.movers if m.kind == "figure" and m.payload.get("action") == "ARRIVAL"), None)
_at = rv and (rv.x, rv.y)
if rv:
    p.run.player = (10, 8)
    adv(300, lambda s: s is not p)
check(_at == (10, 3) and rv and abs(rv.x - 10) + abs(rv.y - 8) == 1 and "Trainer" in type(g.current_state).__name__,
      f"Route 103: the rival waits at Emerald's spot {_at} and walks up to battle")
story.story_flags["hoenn_rival_103"] = True

# Petalburg Woods and Rusturf Tunnel: the Grunt walks up near the Devon researcher / over Peeko
for key, came, near, flag in (("HOENN_PETALBURG_WOODS", "HOENN_ROUTE_104", (23, 18), "petalburg_woods_grunt"),
                             ("HOENN_RUSTURF_TUNNEL", "HOENN_ROUTE_116", (10, 7), "rusturf_grunt_met")):
    story.story_flags.pop(flag, None)
    story.defeated_trainers.pop(key, None)
    p = open_map(key, came)
    p.run.player = near
    _said = []
    for _ in range(600):
        s = g.current_state
        if s is not p: break
        if p.dialogue_box.visible:
            _said.append(" ".join(p.dialogue_box.text_lines)); p.dialogue_box.advance()
        s.update(); s.draw()
    check(any("Grunt" in x for x in _said) and "Trainer" in type(g.current_state).__name__, f"{key}: the Grunt notices you, walks up and battles ({_said[:1]})")

# Petalburg: the guide walks a newcomer to the Pokemon Center
story.story_flags.pop("petalburg_center_tour", None)
t = open_map("PETALBURG_CITY", "HOENN_ROUTE_102")
home = next(h for h, o in t.people.items() if o.get("text") == "Guide")
t.player = (home[0] + 1, home[1]); t.anim = 0; t._talk(home)
_stops = []
for _ in range(1500):
    if t.npc_active:
        _stops.append(t.motions[home].pos)
        t.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
    frames(1)
    if story.story_flags.get("petalburg_center_tour") and not t.scenes.busy(): break
check((20, 17) in _stops, f"Petalburg: the guide takes you to the Pokemon Center ({_stops[:1]})")

# Dewford: Mr. Briney at the pier runs the boats
t = open_map("DEWFORD_TOWN", "HOENN_ROUTE_106")
_br = t._people().get((12, 9))
check(_br is not None and "Boat" in str(_br.get("text")) and (12, 8) in t.barred, f"Dewford: Mr. Briney stands by his boat at the pier and sails you ({_br and _br.get('text')})")

# Granite Cave: Steven in the deepest room where Emerald stands him; down the ladders floor by floor
_gc = _tm["HOENN_GRANITE_CAVE"]["floors"]
check(_gc[0]["art"][8][7] == "N" and "TALK TO STEVEN" in _gc[0]["people"], "Granite Cave: Steven stands in the deepest room at Emerald's spot")
story.current_area_key, story.last_area_key = "HOENN_GRANITE_CAVE", "HOENN_ROUTE_106"
p = PlayState(g); g.states["play"] = p; g.change_state(p); frames(2)
_lad = (35, 3)   # 1F's ladder down (Emerald) -> B1F
p._warp(1, 37, 11); p.run.player = (_lad[0], _lad[1] + 1); p.anim = 0
p.step(0, -1); frames(10); tap(p)
check(p.run.index == 2, f"Granite Cave: 1F's ladder at {_lad} takes you down to B1F (floor {p.run.index})")

# Route 110: through a gatehouse with the Bicycle, up the ramp onto the Cycling Road
_r110 = _tm["HOENN_ROUTE_110"]["floors"]
_gate = {k: v for k, v in _r110[0].get("links", {}).items() if v[0] == 0}
_ramps = {k: v for k, v in _r110[0].get("links", {}).items() if v[0] == 1}
check(len(_gate) == 4 and len(_ramps) >= 2 and any(b.get("item") == "BICYCLE" for b in _r110[0].get("barred", [])),
      f"Route 110: two gatehouses walked through ({len(_gate)} doors), {len(_ramps)} ramps up to the Cycling Road, the Bicycle checked at the gates")

# ---- ORAS story events on the maps (the walkthrough's, 11-12): each played as a player meets it
g.rival_character = g.rival_character or "brendan"


def _play(st, frames=1500):
    said = []
    for i in range(frames):
        s = g.current_state
        if s is not st:
            said.append("<" + type(s).__name__ + ">"); break
        sc = st.scenes if isinstance(st, _WTS) else st._scenes()
        talking = getattr(st, "npc_active", False) or (getattr(st, "dialogue_box", None) is not None and st.dialogue_box.visible)
        if talking:
            box = st.npc_dialogue if getattr(st, "npc_active", False) else st.dialogue_box
            t = " ".join(box.text_lines or [])
            if not said or said[-1] != t:
                said.append(t)
            if getattr(st, "npc_active", False):
                st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
            else:
                st.dialogue_box.advance()
        st.update(); st.draw()
        if i > 60 and not sc.busy() and not talking and len(said) > 1:
            break
    return said


def _calm(st):
    """No wild Pokemon on the floor (they stand anywhere at random, sometimes on the very tile a check steps into)."""
    if hasattr(st, "run"):
        st.run.floor.movers = [m for m in st.run.floor.movers if m.kind != "wild"]


def _scene(key, came, flags_on=(), flags_off=(), at=None, step=None):
    for k in flags_on:
        story.story_flags[k] = True
    for k in flags_off:
        story.story_flags.pop(k, None)
    st = open_map(key, came)
    if at is not None:
        if isinstance(st, _WTS):
            st.player = at
            st.scenes.entered = True
        else:
            st.run.player = at
        st.anim = 0
    if step:
        _calm(st)
        st.step(*step)
    return st, _play(st)


_saved2 = dict(story.story_flags)
st, said = _scene("LITTLEROOT_TOWN", "HOENN_ROUTE_101", ["received_pokedex_hoenn"], ["hoenn_mom_sendoff"], at=(10, 4), step=(0, -1))
check(story.story_flags.get("hoenn_mom_sendoff") and any("Mom:" in x for x in said), f"Littleroot: Mom walks out to see you off once you have the Pokedex ({said[-1:]})")
_nav = story.inventory.pop("POKE_NAV", None)
st, said = _scene("HOENN_ROUTE_101", "LITTLEROOT_TOWN", ["received_pokedex_hoenn", "hoenn_birch_walked_up", "hoenn_birch_rescued", "hoenn_birch_thanked"], ["hoenn_rival_101_tips", "got_dexnav_hoenn"])
check(story.story_flags.get("hoenn_rival_101_tips") and story.inventory.get("POKE_NAV", 0) > 0,
      f"Route 101: your rival catches up with a tip about hidden Pokemon, and hands over the DexNav ({said[:1]})")
_pot = story.inventory.get("POTION", 0)
st, said = _scene("OLDALE_TOWN", "HOENN_ROUTE_101", ["received_pokedex_hoenn"], ["oldale_free_potions"])
check(story.inventory.get("POTION", 0) > _pot, f"Oldale: the Mart clerk runs up as you arrive and hands over Potions ({said[-1:]})")
st, said = _scene("HOENN_ROUTE_102", "OLDALE_TOWN", ["received_pokedex_hoenn"], ["hoenn_rival_102_beautifly"], at=(6, 8))
check(story.story_flags.get("hoenn_rival_102_beautifly"), f"Route 102: your rival catches up to watch the Beautifly")
st, said = _scene("HOENN_PETALBURG_WOODS", "HOENN_ROUTE_104", ["woods_boss_defeated"], ["woods_researcher_left"], at=(24, 18))
check(story.story_flags.get("woods_researcher_left"), "Petalburg Woods: after the battle the researcher heals your team and hurries off")
st, said = _scene("HOENN_ROUTE_104", "HOENN_PETALBURG_WOODS", ["woods_boss_defeated"], ["route104_grunt_report"], at=(10, 28))
check(story.story_flags.get("route104_grunt_report") and any("Grunt" in x for x in said), "Route 104: out of the woods, a Grunt reports to her boss")
st, said = _scene("RUSTBORO_CITY", "HOENN_ROUTE_104", [], ["rustboro_rival_mart", "has_stone_badge"], at=(15, 50))
check(story.story_flags.get("rustboro_rival_mart"), "Rustboro: your rival steps out of the Mart and dashes off to the Gym")
_gb = story.inventory.get("GREAT_BALL", 0)
st, said = _scene("RUSTBORO_CITY", "HOENN_ROUTE_104", ["rusturf_rescued"], ["met_mr_stone", "rustboro_researcher_thanks"], at=(11, 20))
check(story.inventory.get("GREAT_BALL", 0) > _gb, "Rustboro: the researcher waits outside Devon with a Great Ball")
st, said = _scene("HOENN_RUSTURF_TUNNEL", "HOENN_ROUTE_116", ["rusturf_rescued", "rusturf_grunt_met"], ["rusturf_briney_thanks"], at=(13, 5))
check(story.story_flags.get("rusturf_briney_thanks") and any("Peeko" in x for x in said), "Rusturf Tunnel: Mr. Briney runs in to Peeko")
_tm2 = json.load(open("assets/town_maps.json", encoding="utf-8"))
_dew = next(p for p in _tm2["DEWFORD_TOWN"]["people"] if isinstance(p, dict) and p.get("text") == "Fisherman")
_hik = next(p for p in _tm2["HOENN_GRANITE_CAVE"]["floors"][1]["people"] if isinstance(p, dict) and p.get("text") == "Hiker")
check((_dew["event"].get("gift_item") or {}).get("OLD_ROD") and (_hik["event"].get("gift_item") or {}).get("HM_FLASH"),
      "Dewford's fisherman gives the Old Rod; Granite Cave's hiker gives Flash")
_q = [b for b in _tm2["SLATEPORT_CITY"].get("barred", []) if b.get("look") == "sheet:@grunt"]
check(len(_q) == 9, f"Slateport: the villain team's Grunts queue outside the Museum ({len(_q)})")
_inv = {k: story.inventory.pop(k, None) for k in ("CONTEST_PASS", "POKEBLOCK_CASE")}
st, said = _scene("SLATEPORT_CITY", "HOENN_ROUTE_109", ["oceanic_museum_cleared", "slateport_saw_dock"], ["contest_pass_received", "slateport_lisia_met"], at=(17, 6))
check(story.inventory.get("CONTEST_PASS", 0) > 0 and any("Lisia" in x for x in said), f"Slateport: after the Museum, Lisia walks out of the Contest Hall with a Contest Pass ({said[:1]})")
for _k, _v in _inv.items():
    if _v is not None and not story.inventory.get(_k):
        story.inventory[_k] = _v
st, said = _scene("HOENN_ROUTE_110", "SLATEPORT_CITY", ["oceanic_museum_cleared"], ["defeated_rival_110"], at=(34, 58))
check("<TrainerIntroState>" in said, f"Route 110: your rival walks up for a battle ({said[:1]})")
# ---- batch 5: Mauville, Route 117, Verdanturf, Route 111
st, said = _scene("MAUVILLE_CITY", "HOENN_ROUTE_110", ["helped_wally"], ["defeated_wally_mauville"])
check(any("Trainer" in x for x in said if x.startswith("<")),   # (his lines open the battle: the battle's own intro shows them)
      f"Mauville: Wally steps up from the Gym door to battle you, his uncle beside him ({said[:1]})")
story.story_flags["defeated_wally_mauville"] = True
_mv = _tm2["MAUVILLE_CITY"]
check("HOENN_NEW_MAUVILLE" in _mv["exits"].values() and "HOENN_ROUTE_111" in _mv["exits"].values(),
      "Mauville: the east house leads into New Mauville; Route 111 north")
_r111 = _tm2["HOENN_ROUTE_111"]
_dr = [(x, y) for y, r in enumerate(_r111["art"]) for x, c in enumerate(r) if c == "N"]
check((29, 88) in _dr and "HOENN_MIRAGE_TOWER" in _r111["exits"].values() and any(b.get("look") == "storm" for b in _r111.get("barred", [])),
      "Route 111: the Desert Ruins at their door, Mirage Tower in the desert, the sandstorm until the Go-Goggles")
check("daycare" in _tm2["HOENN_ROUTE_117"]["buildings"].values() and len(_tm2["HOENN_ROUTE_117"].get("barred", [])) == 4,
      "Route 117: the Day Care, its Pokemon playing in the yard")
check({"contest", "wally", "center", "mart"} <= set(_tm2["VERDANTURF_TOWN"]["buildings"].values()), "Verdanturf: the Contest Hall, Wally's uncle's house, the Center and Mart")


def _press(st, at, face):
    """Stand at a spot facing a person or sign and press A (towns)."""
    st.player, st.facing, st.anim = at, face, 0
    st.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode="", scancode=0)])
    return _play(st)


# Verdanturf (ORAS): the little girl's lost Shroomish is behind the town sign; she gives the Intriguing Stone, which Mr. Stone trades for the Pidgeotite
for _k in ("verdanturf_shroomish_asked", "verdanturf_shroomish_found", "got_intriguing_stone"):
    story.story_flags.pop(_k, None)
_stone = story.inventory.get("INTRIGUING_STONE", 0)
st = open_map("VERDANTURF_TOWN", "HOENN_ROUTE_117")
st.scenes.entered = True
_press(st, (14, 7), (0, -1))
check(not story.story_flags.get("verdanturf_shroomish_found"), "Verdanturf: the town sign is just a sign until the girl asks for help")
said = _press(st, (14, 16), (0, -1))
check(story.story_flags.get("verdanturf_shroomish_asked") and any("Shroomish" in x for x in said), f"Verdanturf: the little girl has lost her Shroomish near the sign ({said[:1]})")
said = _press(st, (14, 7), (0, -1))
check(story.story_flags.get("verdanturf_shroomish_found") and (13, 15) in st.barred, f"Verdanturf: reading the sign, the Shroomish pops out and hops back beside her ({said[:1]})")
said = _press(st, (14, 16), (0, -1))
check(story.inventory.get("INTRIGUING_STONE", 0) > _stone, f"Verdanturf: she thanks you with the Intriguing Stone ({said[-1:]})")
import json as _json
def _find(d, key):
    if isinstance(d, dict):
        if key in d:
            return d[key]
        for v in d.values():
            r = _find(v, key)
            if r is not None:
                return r
_ms = next(o for o in _find(_json.load(open("assets/hoenn_area_data.json", encoding="utf-8")), "RUSTBORO_CITY")["explore_options"] if o.get("text") == "Mr. Stone")
check(_ms.get("condition") == "has_item:INTRIGUING_STONE" and _ms["event"].get("take_item") == {"INTRIGUING_STONE": 1},
      "Rustboro: Mr. Stone trades the Pidgeotite for the Intriguing Stone")
story.inventory["INTRIGUING_STONE"] = _stone

# Route 111 (ORAS): the Winstrates, four battles in a row out of their door; Victoria gives the Macho Brace
for _k in ("winstrate_asked", "winstrate_victor", "winstrate_victoria", "winstrate_vivi", "winstrate_vicky", "winstrate_brace"):
    story.story_flags.pop(_k, None)
st, said = _scene("HOENN_ROUTE_111", "MAUVILLE_CITY", at=(14, 116), step=(0, -1))
check("<TrainerIntroState>" in said and any("Victor:" in x for x in said), f"Route 111: Victor challenges you to the Winstrate family ({said[:1]})")
for _fl, _who in (("winstrate_victor", "Victoria"), ("winstrate_victoria", "Vivi"), ("winstrate_vivi", "Vicky")):
    st, said = _scene("HOENN_ROUTE_111", "MAUVILLE_CITY", [_fl], at=(13, 116))
    check("<TrainerIntroState>" in said and any(_who + ":" in x for x in said), f"Route 111: {_who} walks out of the house to battle next ({said[:1]})")
_mb = story.inventory.get("MACHO_BRACE", 0)
st, said = _scene("HOENN_ROUTE_111", "MAUVILLE_CITY", ["winstrate_vicky"], at=(13, 116))
check(story.inventory.get("MACHO_BRACE", 0) > _mb, f"Route 111: beat all four and Victoria gives you the Macho Brace ({said[-1:]})")
# ---- batch 6: Route 112, Fiery Path, Route 113, Fallarbor
import src.dungeon.core as _core
_had_str = story.inventory.pop("HM_STRENGTH", None)
st, said = _scene("HOENN_ROUTE_112", "HOENN_ROUTE_111", [], ["got_strength_hoenn"], at=(37, 50))
check(story.inventory.get("HM_STRENGTH", 0) > 0 and any("Mt. Chimney" in x for x in said), f"Route 112: your rival walks up, heals your team and gives you Strength ({said[:1]})")
_r112 = _tm2["HOENN_ROUTE_112"]
check(_r112["art"][30][26] == "N" and _r112["art"][30][27] == "N" and "cablecar" in _r112["buildings"].values(),
      "Route 112: two Grunts stand in the only way up to the cable car (until Meteor Falls)")
for _a, _b in (("HOENN_FIERY_PATH", "HOENN_ROUTE_112"), ("HOENN_ROUTE_112", "HOENN_FIERY_PATH")):
    _st = open_map(_a, _b)
    _mouths = [t for t, v in _st.run.floor.exits.items() if v == _b]
    _land = []
    for _m in _mouths:
        _core.ENTRANCE_INDEX, _core.ENTRANCE_COUNT = _mouths.index(_m), len(_mouths)
        _land.append(tuple(open_map(_b, _a).run.player))
    check(len(_mouths) == 2 and _land[0][1] < _land[1][1], f"{_a}: out of the north mouth you come out north, the south one south ({_mouths} -> {_land})")
st, said = _scene("HOENN_ROUTE_113", "HOENN_ROUTE_111", [], ["heard_cozmo", "route113_rival_rest", "meteor_falls_cleared"])
check(story.story_flags.get("route113_rival_rest") and any("Cozmo" in x for x in said), f"Route 113: your rival, resting, heals your team and tells you of Professor Cozmo ({said[:1]})")
st, said = _scene("FALLARBOR_TOWN", "HOENN_ROUTE_113", [], ["heard_cozmo", "fallarbor_cozmo_taken", "meteor_falls_cleared"], at=(12, 10), step=(-1, 0))
check(story.story_flags.get("heard_cozmo") and any("Meteor Falls" in x for x in said), f"Fallarbor: your rival runs out of Cozmo's house: he's been taken to Meteor Falls ({said[-1:]})")
if _had_str is not None:
    story.inventory["HM_STRENGTH"] = _had_str

# ---- batch 7: Route 114, Meteor Falls, Route 115, Mt. Chimney (ORAS, parts 8-9)
_rep = getattr(story, "repel_routes", 0)
story.repel_routes = 9   # (no wild Pokemon in the way of the scenes)
for _k in ("meteor_falls_cleared", "route114_rival_race", "got_tm_dig_114", "route114_berry_day", "meteor_falls_rival_joins",
           "meteor_falls_other_leader", "mt_chimney_boss_defeated", "mt_chimney_other_leader", "cozmo_thanked"):
    story.story_flags.pop(_k, None)
story.story_flags["heard_cozmo"] = True
_tm15 = story.inventory.pop("TM15", None)
st = open_map("HOENN_ROUTE_114", "FALLARBOR_TOWN")
st.run.player, st.facing = (29, 6), (0, -1)
st._read_sign(); tap(st)
check(story.inventory.get("TM15", 0) > 0, "Route 114: the Fossil Maniac's little brother gives you TM15 (Dig)")
st.run.player, st.facing = (27, 37), (0, -1)
st._read_sign()
check(st.dialogue_box.visible and "Lanette" in " ".join(st.dialogue_box.text_lines), f"Route 114: Lanette at home ({st.dialogue_box.text_lines[:1]})")
tap(st)
_bb = next(m for m in st.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict) and m.payload.get("text") == "Berry boy")
st._use_figure(_bb)
check(story.story_flags.get("route114_berry_day") and "Berry" in " ".join(st.dialogue_box.text_lines), "Route 114: the rich boy gives a Berry a day")
tap(st)
st, said = _scene("HOENN_ROUTE_114", "FALLARBOR_TOWN", at=(25, 43), step=(0, 1))
check(story.story_flags.get("route114_rival_race") and any("Meteor Falls" in x for x in said), f"Route 114: your rival saw them take the Professor into Meteor Falls ({said[:1]})")
st, said = _scene("HOENN_METEOR_FALLS", "HOENN_ROUTE_114", at=(19, 18), step=(-1, 0))
_f0 = _tm["HOENN_METEOR_FALLS"]["floors"][0]
check(story.story_flags.get("meteor_falls_rival_joins") and {"Admin Tabitha", "Team Magma Grunt"} <= set(_f0.get("trainer_spots", [])),
      f"Meteor Falls: by the falls the Admin and her Grunts hold Professor Cozmo; your rival catches up and heals you ({said[:1]})")
st, said = _scene("HOENN_METEOR_FALLS", "HOENN_ROUTE_114", ["meteor_falls_cleared"])
check(story.story_flags.get("meteor_falls_other_leader") and any("Mt. Chimney" in x for x in said) and not any("{" in x for x in said),
      f"Meteor Falls: after the Admin, the other team's leader turns up, and your rival takes Cozmo home ({said[:1]})")
st, said = _scene("HOENN_MT_CHIMNEY", "HOENN_ROUTE_112", ["mt_chimney_boss_defeated"])
check(story.story_flags.get("mt_chimney_other_leader") and any("orbs" in x for x in said) and set(_tm["HOENN_MT_CHIMNEY"].get("trainer_spots", [])) >= {"Team Leader", "Team Admin"},
      f"Mt. Chimney: the Admin and the leader on the summit; after him, the other team's leader worries about the orbs ({said[:1]})")
_mf = _tm["HOENN_METEOR_FALLS"]
check(len(_mf["floors"]) == 4 and _mf["floors"][0].get("parts") and _mf.get("figure_floors", {}).get("THE MILLENNIUM COMET") == 3,
      "Meteor Falls: four floors from Emerald (no Steven's room); 1F's pockets reached from B1F; the comet's Jirachi in the deepest room")
story.repel_routes = _rep
if _tm15 is None:
    story.inventory.pop("TM15", None)

# after Meteor Falls (ORAS): Cozmo's thanks (TM100 Smack Down: a story gift, never sold), your rival's offer to go
# back to Mauville together; Mt. Chimney's Lava Cookies
from src.pokemon import tms as _tms, items as _items
for _k in ("cozmo_thanked", "rival_mauville_ride"):
    story.story_flags.pop(_k, None)
story.story_flags["meteor_falls_cleared"] = True
_t100 = story.inventory.pop("TM100", None)
st = open_map("FALLARBOR_TOWN", "HOENN_ROUTE_114")
_cz = next(o for o in st._door_options("cozmo") if o.get("target") == "professor_cozmo")
st._get_callback_for_option(_cz)(); tap(st)
check(story.inventory.get("TM100", 0) > 0 and _tms.move_of(g, "TM100") == "SMACK-DOWN" and "TM100" not in _tms.mart_stock(g, 8),
      "Fallarbor: Professor Cozmo thanks you with TM100 Smack Down (a story gift: not in any Mart)")
st = open_map("FALLARBOR_TOWN", "HOENN_ROUTE_114")
_rr = st._door_options("rivalride")
_shown_rival = any((o.get("any") or [o])[0].get("door") == "rivalride" for o in st._people().values() if isinstance(o, dict))
st._get_callback_for_option(_rr[0])()
frames(3)
check(_shown_rival and len(_rr) == 2 and type(g.current_state).__name__ == "AreaTransitionState" and getattr(g.current_state, "next_area_key", None) == "MAUVILLE_CITY",
      f"Fallarbor: your rival waits outside Cozmo's house and takes you back to Mauville if you like ({[o.get('text') for o in _rr]})")
st = open_map("HOENN_MT_CHIMNEY", "HOENN_ROUTE_112")
_lady = next(m for m in st.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict) and m.payload.get("text") == "Lava Cookie lady")
st._use_figure(_lady)
check(type(g.current_state).__name__ == "PokeMartState" and getattr(g.current_state, "stock", None) == ["LAVA_COOKIE"] and _items.price("LAVA_COOKIE") == 200
      and _items.MEDICINE["LAVA_COOKIE"].get("cure") == "all", "Mt. Chimney: the Lava Cookie lady sells Lava Cookies (200; they cure any status)")
g.change_state(st)
if _t100 is None:
    story.inventory.pop("TM100", None)

# ---- batch 8: Jagged Pass, Lavaridge Town, Route 118, Route 105 (ORAS, parts 9-10)
for _k in ("got_tm_swords_dance", "got_lavaridge_egg", "got_charcoal", "got_good_rod_hoenn"):
    story.story_flags.pop(_k, None)
_inv8 = dict(story.inventory)
_team8 = list(story.player_team)
st = open_map("LAVARIDGE_TOWN", "HOENN_ROUTE_112")
st.scenes.entered = True


def _talk8(st, at, face):
    st.player, st.facing, st.anim = at, face, 0
    st.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode="", scancode=0)])
    return _play(st)


_talk8(st, (16, 8), (0, -1))
check(story.inventory.get("TM101", 0) > 0, "Lavaridge: the dancing Black Belt gives TM101 Swords Dance (ORAS's TM75)")
story.player_team = _team8[:5]
_n8 = len(story.player_team)
_talk8(st, (4, 8), (0, -1))
check(len(story.player_team) == _n8 + 1 and getattr(story.player_team[-1], "is_egg", False), "Lavaridge: the old woman by the sand baths gives you an Egg (with room in your party)")
story.player_team = _team8
_herb, _ctr = st._door_options("herb"), st._door_options("center")
check({"Herb Shop", "Old man's Charcoal"} <= {o.get("text") for o in _herb} and {"Moomoo Milk", "Hot Springs"} <= {o.get("text") for o in _ctr},
      f"Lavaridge: the Herb Shop (herbs, the old man's Charcoal); the Center's Moomoo Milk and hot springs")
st._get_callback_for_option(next(o for o in _ctr if o.get("text") == "Hot Springs"))(); tap(st)
_at_springs = st.player
st.player, st.anim = (9, 1), 0
st.step(0, 1); frames(20)
check(_at_springs == (9, 1) and st.player == (9, 7), f"Lavaridge: the hot springs out back of the Center, and its back door out front again ({_at_springs}, {st.player})")
st = open_map("HOENN_ROUTE_118", "MAUVILLE_CITY")
_fish = next(m for m in st.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict) and m.payload.get("text") == "Good Rod fisherman")
st._use_figure(_fish); tap(st)
check(story.inventory.get("GOOD_ROD", 0) > 0, "Route 118: the fisherman on the east bank gives the Good Rod")
check("MEET STEVEN" in _tm["HOENN_ROUTE_118"].get("people", []) and any(s.get("who") == "MEET STEVEN" for s in _tm["HOENN_ROUTE_118"].get("scenes", [])),
      "Route 118: Steven stands where Emerald has him and walks up to take you to Southern Island")
check({"ISLAND CAVE", "AWAKEN REGIGIGAS"} <= set(_tm["HOENN_ROUTE_105"].get("people", [])), "Route 105: Island Cave's legends at its door")
_jp = _tm["HOENN_JAGGED_PASS"]
check(any(b.get("item") == "MAGMA_EMBLEM" for b in _jp.get("barred", [])) and "HOENN_MAGMA_HIDEOUT" in _jp["exits"].values(),
      "Jagged Pass: the Magma Hideout's hidden door is plain rock until the Magma Emblem")
story.inventory.clear(); story.inventory.update(_inv8)

# Gabby and Ty's battles (Routes 111 and 118: the pair as one trainer, Emerald's Interviewer picture); the Jagged Pass's
# round stones (in the way on foot, hopped on the Bicycle) and its TMs (TM102 Flame Charge, TM103 Rock Polish)
for _k in ("gabby_ty_111", "gabby_ty_118", "got_tm102_jagged"):
    story.story_flags.pop(_k, None)
_rep8 = getattr(story, "repel_routes", 0)
story.repel_routes = 9
for _key, _came, _flag in (("HOENN_ROUTE_111", "MAUVILLE_CITY", "gabby_ty_111"), ("HOENN_ROUTE_118", "MAUVILLE_CITY", "gabby_ty_118")):
    st = open_map(_key, _came)
    _gb = next(m for m in st.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict) and m.payload.get("text") == "Gabby")
    st._use_figure(_gb)
    frames(5)
    _b = (_gb.payload.get("event") or {}).get("battle") or {}
    check("Trainer" in type(g.current_state).__name__ and _b.get("sprite") == "interviewers.png" and len(_b.get("team", [])) == 2,
          f"{_key}: Gabby and Ty challenge you ({_b.get('team')} Lv. {_b.get('levels')}), then interview you")
_bk8 = story.inventory.pop("BICYCLE", None)
st = open_map("HOENN_JAGGED_PASS", "HOENN_MT_CHIMNEY")
st.run.player, st.anim = (21, 9), 0
st.dialogue_box.visible = False
st.step(0, 1)
_foot = (tuple(st.run.player), " ".join(st.dialogue_box.text_lines))
story.inventory["BICYCLE"] = 1
st = open_map("HOENN_JAGGED_PASS", "HOENN_MT_CHIMNEY")
st.run.player, st.anim = (21, 9), 0
st.dialogue_box.visible = False
st.step(0, 1)
_hop = st.hop
frames(20); st.anim = 0
st.step(0, 1); frames(20)
_pc8 = g.player_character
g.player_character = "may"
st.run.player, st.anim = (21, 10), 0
_wheelie = st._on_stones() and st._acro_sheet() == "em_acro_may.png" and st._player_img() is not None
g.player_character = _pc8
check(_foot[0] == (21, 9) and "Bicycle" in _foot[1] and _hop and _wheelie,
      f"Jagged Pass: round stones stop you on foot ({_foot}); on the Bicycle you ride onto them, a wheelie on each and a hop between (Emerald's Acro Bike frames)")
_tmf = next(m for m in st.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict) and m.payload.get("text") == "TM102 FLAME CHARGE")
st._use_figure(_tmf); tap(st)
check(story.inventory.get("TM102", 0) > 0 and "TM103 ROCK POLISH" in _tm["HOENN_JAGGED_PASS"].get("people", []),
      "Jagged Pass: TM102 Flame Charge across the stones, TM103 Rock Polish on the west hill (story-gift TMs)")
if _bk8 is None:
    story.inventory.pop("BICYCLE", None)
story.repel_routes = _rep8

# ---- Berries (11-12): soft soil from Emerald's own Berry trees; pick, plant, water, grow on the clock
from src.world import berries as _berries
import time as _time
_soil = {k: v.get("berry_soil") for k, v in _tm2.items() if v.get("berry_soil")}
check(len(_soil) >= 7 and [24, 2, "ORAN_BERRY"] in _soil.get("HOENN_ROUTE_102", []), f"Berries: soft soil on {len(_soil)} Hoenn maps, Emerald's starting Berries (Route 102's Oran and Pecha)")
_saved_bp = story.story_flags.pop("berry_patches", None)
_inv0 = dict(story.inventory)
for _k in ("ORAN_BERRY", "WAILMER_PAIL"):
    story.inventory.pop(_k, None)
st = open_map("HOENN_ROUTE_102", "OLDALE_TOWN")
_f = st.run.floor
check(str(_f.decor.get((24, 2), "")).startswith("soil:"), f"Route 102: the soil patch stands on the map ({_f.decor.get((24, 2))})")
st.run.player, st.facing = (24, 3), (0, -1)
st._read_sign()
check(story.inventory.get("ORAN_BERRY", 0) >= 2, f"Route 102: walking up to the ripe tree picks its Oran Berries ({story.inventory.get('ORAN_BERRY')})")
st.dialogue_box.visible = False
st._read_sign()
_cb = st.dialogue_box.callback   # ("Plant a Berry here?": past the words, the Berry screen)
if _cb:
    st.dialogue_box.callback = None
    _cb()
check(type(g.current_state).__name__ == "PlantBerryState", f"Route 102: empty soil asks which Berry to plant ({type(g.current_state).__name__})")
if type(g.current_state).__name__ == "PlantBerryState":
    g.current_state.chose("ORAN_BERRY")
_rec = _berries.record(story, "HOENN_ROUTE_102", (24, 2), None)
check(_rec.get("berry") == "ORAN_BERRY" and _berries.stage(_rec) == 0, f"Route 102: an Oran Berry planted ({_rec})")
story.inventory["WAILMER_PAIL"] = 1
_t0 = _rec["t"]
for _h in (0.1, 4.1, 8.1, 12.1):
    _berries.clock = lambda _h=_h: _t0 + _h * 3600
    st.dialogue_box.visible = False
    st._read_sign()
_berries.clock = lambda: _t0 + 16.1 * 3600
_n0 = story.inventory.get("ORAN_BERRY", 0)
st.dialogue_box.visible = False
st._read_sign()
_berries.clock = _time.time
check(story.inventory.get("ORAN_BERRY", 0) - _n0 == 5, f"Route 102: watered at all four stages, it bears the most Berries ({story.inventory.get('ORAN_BERRY', 0) - _n0})")
g.change_state(st)
# Route 104's Pretty Petal: the Wailmer Pail; Route 113's Glass Workshop: its flutes; Lisia's Pokeblock Kit
_r104 = next(o for o in _find(_json.load(open("assets/hoenn_area_data.json", encoding="utf-8")), "HOENN_ROUTE_104")["route_menu"] if o.get("door") == "flower")
_r113 = next(o for o in _find(_json.load(open("assets/hoenn_area_data.json", encoding="utf-8")), "HOENN_ROUTE_113")["route_menu"] if o.get("door") == "glass")
check("flower" in _tm2["HOENN_ROUTE_104"]["buildings"].values() and _r104.get("target") == "pretty_petal",
      "Route 104: the Pretty Petal Flower Shop's door (the Wailmer Pail, a Berry a day)")
check("glass" in _tm2["HOENN_ROUTE_113"]["buildings"].values() and len(_r113.get("stock", [])) == 5, "Route 113: the Glass Workshop sells the five flutes")
from src.states.berry_patch import blocks_from as _blocks
check(_blocks(["SPELON_BERRY", "PECHA_BERRY"]) == {"RED_POKEBLOCK": 2, "PINK_POKEBLOCK": 1}, "Pokeblock Kit: a Spelon makes two red Pokeblocks, a Pecha one pink")
story.inventory.clear(); story.inventory.update(_inv0)
if _saved_bp is not None:
    story.story_flags["berry_patches"] = _saved_bp
story.story_flags.clear(); story.story_flags.update(_saved2)

# ---- batch 9: Route 119 and the Weather Institute, Fortree City (two storeys), Route 120 (ORAS, parts 10-11)
_saved9, _inv9, _team9 = dict(story.story_flags), dict(story.inventory), list(story.player_team)
_rep9 = getattr(story, "repel_routes", 0)
story.repel_routes = 9
_mv = lambda st: {(m.x, m.y): (m.payload.get("text") if isinstance(m.payload, dict) else m.kind) for m in st.run.floor.movers}
for _k in ("weather_institute_cleared", "got_rocky_helmet", "hoenn_rival_119", "hoenn_rival_119_met", "got_starter_mega_stone", "route120_kecleon"):
    story.story_flags.pop(_k, None)
story.story_flags["got_mega_bracelet"] = True
for _k in ("ROCKY_HELMET", "ICY_ROCK", "DEVON_SCOPE"):
    story.inventory.pop(_k, None)
st = open_map("HOENN_ROUTE_119", "FORTREE_CITY")
check({_mv(st).get((13, 33)), _mv(st).get((13, 34))} == {"Lookout grunt", "Bored grunt"}, "Route 119: two Grunts keep lookout by the Weather Institute while the team holds it")
st = open_map("HOENN_WEATHER_INSTITUTE", "HOENN_ROUTE_119")
_wi0 = _mv(st)
st.run.enter_floor(1); frames(2)
_wi1 = _mv(st)
check(_wi0.get((15, 3)) == "trainer" and _wi1.get((10, 8)) == "trainer" and _wi1.get((19, 6)) == "trainer",
      "Weather Institute: a Grunt in the lobby; upstairs a Grunt and the Admin by the Professor")
st.run.enter_floor(0); frames(2)
st._use_figure(next(m for m in st.run.floor.movers if isinstance(m.payload, dict) and m.payload.get("text") == "Grateful scientist")); tap(st)
check(not story.inventory.get("ROCKY_HELMET"), "Weather Institute: no Rocky Helmet while the team is upstairs")
story.story_flags["weather_institute_cleared"] = True
st = open_map("HOENN_WEATHER_INSTITUTE", "HOENN_ROUTE_119")
for _who in ("Grateful scientist", "Receptionist", "Receptionist"):
    st.dialogue_box.visible = False
    st._use_figure(next(m for m in st.run.floor.movers if isinstance(m.payload, dict) and m.payload.get("text") == _who)); tap(st)
check(story.inventory.get("ROCKY_HELMET") == 1 and story.inventory.get("ICY_ROCK") == 1 and not story.inventory.get("SMOOTH_ROCK"),
      "Weather Institute: once it's freed, the scientist's Rocky Helmet and the receptionist's weather rock (one a day)")
st = open_map("HOENN_ROUTE_119", "FORTREE_CITY")
check((13, 33) not in _mv(st), "Route 119: the lookouts gone once the Institute is freed")
st.run.player, st.anim = (27, 26), 0
st.dialogue_box.visible = False
_calm(st); st.step(0, 1)
said = _play(st)
check("<TrainerIntroState>" in said, f"Route 119: your rival catches up over the bridge for a battle (Fly when you win) ({said[:1]})")
story.story_flags["hoenn_rival_119"] = True
st = open_map("HOENN_ROUTE_119", "FORTREE_CITY")
_tk = next(m for m in st.run.floor.movers if (m.x, m.y) == (17, 128))
st.run.floor.movers = [m for m in st.run.floor.movers if m is _tk or m.kind not in ("trainer", "wild")]   # (no one else walking up mid-test)
st._motion(_tk).sight = 0
st.run.player, st.anim = (12, 128), 0
_seen9 = []
for _d in ((0, 1), (0, -1)):
    st.step(*_d); frames(20)
    _seen9.append((_tk.x, _tk.y))
check(_seen9 == [(18, 128), (17, 128)], f"Route 119: the Ninja Boy in the grass copies your steps, turned a quarter (Emerald's copy movement) ({_seen9})")
_hp = story.player_team[0].current_hp = 1
st.run.player, st.anim = (33, 110), 0
st.dialogue_box.visible = False
_calm(st); st.step(0, -1); tap(st)
check(story.player_team[0].current_hp == story.player_team[0].max_hp, "Route 119: the rest stop's cabin heals your team")
# Fortree: two storeys from one Emerald map, joined by ladders; Emerald's invisible Kecleon by the Gym
st = open_map("FORTREE_CITY", "HOENN_ROUTE_119")
_lads = sorted(t for t, k in st.exits.items() if k == "FORTREE_CITY_UPPER")
st.player, st.anim = (_lads[0][0], _lads[0][1] + 1), 0
_calm(st); st.step(0, -1)
for _ in range(400):
    if isinstance(g.current_state, _WTS) and g.current_state is not st:
        break
    frames(1)
_up = g.current_state
frames(3)
check(len(_lads) == 5 and story.current_area_key == "FORTREE_CITY_UPPER" and _up.exits.get(_lads[0]) == "FORTREE_CITY"
      and tuple(_up.player) == (_lads[0][0], _lads[0][1] - 1),
      f"Fortree: up a ladder onto the treetops, beside the same ladder going down ({_lads[:1]} -> {_up.player})")
check({"hiddenpower", "spinda", "guild", "wingull"} <= set(_up.doors.values()) and "Aarune" in [o.get("text") for o in _up._door_options("guild")],
      "Fortree treetops: the treehouses' doors (the coin game, the Spinda trade, Aarune of the Flying guild)")
_up._get_callback_for_option(next(o for o in _up._door_options("hiddenpower") if o.get("text") == "The coin game"))()
check(type(g.current_state).__name__ == "GymPuzzleState" and g.current_state.kind == "coins", "Fortree: the old woman's coin game (three right for TM104 Hidden Power)")
story.player_team = _team9[:5] + [Pokemon(g.loader.fetch_specific(327), g.assets)]
_up = open_map("FORTREE_CITY_UPPER", "FORTREE_CITY")
_up._get_callback_for_option(_up._door_options("spinda")[0])(); frames(300)
check(story.player_team[-1].id == 300 and getattr(story.player_team[-1], "held_item", None) == "MAGOST_BERRY", "Fortree: the little girl trades her Skitty (with a Magost Berry) for a Spinda")
story.player_team = list(_team9)
st = open_map("FORTREE_CITY", "HOENN_ROUTE_119")
check(st.barred.get((25, 8), {}).get("look") == "unseen", "Fortree: something unseeable stands in the way to the Gym")
story.inventory["DEVON_SCOPE"] = 1
st = open_map("FORTREE_CITY", "HOENN_ROUTE_119")
st.player, st.anim = (25, 9), 0
_calm(st); st.step(0, -1); tap(st)
st = open_map("FORTREE_CITY", "HOENN_ROUTE_119")
check((25, 8) not in st.barred, "Fortree: with the Devon Scope the Kecleon shows, and runs off when you walk into it")
# Route 120: Steven on the bridge lends the Devon Scope and gives your starter's Mega Stone; the Kecleon beside him battles
story.inventory.pop("DEVON_SCOPE", None)
st = open_map("HOENN_ROUTE_120", "FORTREE_CITY")
check(st._bars.get((12, 16), {}).get("look") == "unseen", "Route 120: an invisible Kecleon on the bridge beside Steven")
st.run.player, st.anim = (5, 15), 0
st.dialogue_box.visible = False
_calm(st); st.step(1, 0)
said = _play(st, 2000)
check(story.inventory.get("DEVON_SCOPE") and story.story_flags.get("got_starter_mega_stone"), f"Route 120: Steven walks up, lends the Devon Scope and gives your starter's Mega Stone ({said[:1]})")
st = open_map("HOENN_ROUTE_120", "FORTREE_CITY")
st.run.player, st.anim = (12, 17), 0
st.dialogue_box.visible = False
_calm(st); st.step(0, -1)
said = _play(st, 400)
check("<WildBattleState>" in said, f"Route 120: with the Scope, walking into the Kecleon starts a battle ({said[-1:]})")
g.change_state(st)
story.repel_routes = _rep9
story.player_team = _team9
story.inventory.clear(); story.inventory.update(_inv9)
story.story_flags.clear(); story.story_flags.update(_saved9)

# ---- batch 10: Route 121, Route 122, Mt. Pyre (mountainside, summit, 1F-6F), Route 123 (ORAS, part 12)
_saved10, _inv10, _team10 = dict(story.story_flags), dict(story.inventory), list(story.player_team)
_badges10 = {k: list(v) for k, v in story.badges.items()}
_rep10 = getattr(story, "repel_routes", 0)
story.repel_routes = 9
story.badges["HOENN"] = list(dict.fromkeys(list(story.badges.get("HOENN", [])) + ["STONE", "KNUCKLE", "DYNAMO", "HEAT", "BALANCE", "FEATHER"]))
for _k in ("mt_pyre_cleared", "route121_grunts_ran", "mt_pyre_leader_left", "got_cleanse_tag", "got_eviolite_123", "got_tm28_123", "berry_master_123"):
    story.story_flags.pop(_k, None)
for _k in ("CLEANSE_TAG", "EVIOLITE", "TM28"):
    story.inventory.pop(_k, None)
_fig10 = lambda st, name: next(m for m in st.run.floor.movers if isinstance(m.payload, dict) and m.payload.get("text") == name)
st = open_map("HOENN_ROUTE_121", "HOENN_ROUTE_120")
check({_mv(st).get((30, 7)), _mv(st).get((31, 7))} == {"Hurried grunt", "Grunt"}, "Route 121: the team's Grunts gather before heading for Mt. Pyre")
_y121 = next(y for y in range(5, 14) if st._npc_free((19, y)) and st._npc_free((20, y)))
st.run.player, st.anim = (19, _y121), 0
st.dialogue_box.visible = False
_calm(st); st.step(1, 0)
said = _play(st)
_ran = story.story_flags.get("route121_grunts_ran")
st = open_map("HOENN_ROUTE_121", "HOENN_ROUTE_120")
check(_ran and (30, 7) not in _mv(st), f"Route 121: they hurry off south as you come near (ORAS's sighting) ({_ran}, {_mv(st).get((30, 7))}, {said[:1]})")
st = open_map("HOENN_MT_PYRE", "HOENN_ROUTE_122")
check(st.run.index == 2 and st._floor_name(2) == "1F", f"Mt. Pyre: in from Route 122 on the shrine's 1F ({st.run.index})")
st._use_figure(_fig10(st, "Old woman")); tap(st)
check(story.inventory.get("CLEANSE_TAG") == 1, "Mt. Pyre 1F: the old woman gives a Cleanse Tag")
_ct = story.player_team[0].held_item if hasattr(story.player_team[0], "held_item") else None
story.player_team[0].held_item = "CLEANSE_TAG"
st = open_map("HOENN_MT_PYRE", "HOENN_ROUTE_122")
_w, _w0 = st.run.recipe.get("wild") or [4, 6], st.recipe.get("wild") or [4, 6]
story.player_team[0].held_item = _ct
check(_w[1] < _w0[1], f"Mt. Pyre: a Cleanse Tag on your lead means fewer wild Pokemon about ({_w0} -> {_w})")
while len(st.run.floors) <= 3:
    st.run.enter_floor(len(st.run.floors))
st.run.enter_floor(3); frames(2)
st.run.player, st.anim = (11, 8), 0
st.dialogue_box.visible = False
_calm(st); st.step(0, 1)
said = _play(st, 300)
check(st.run.index == 2 and abs(st.run.player[0] - 20) + abs(st.run.player[1] - 9) <= 1 and any("hole" in x for x in said),   # (beside it, if a wild one sits there)
      f"Mt. Pyre 2F: the hole in the floor drops you onto 1F, where Emerald lands you ({st.run.index}, {st.run.player})")
st.run.player, st.anim = (19, 9), 0
_calm(st); st.step(1, 0); frames(20)
check(st.run.index == 2, "Mt. Pyre 1F: the landing spot is plain floor (no way back up through it)")
st.run.enter_floor(1); frames(2)
_sm = {(m.x, m.y) for m in st.run.floor.movers if m.kind == "trainer"}
check({(21, 15), (25, 18), (21, 11), (25, 6)} <= _sm, f"Mt. Pyre summit: three Grunts up the path, the Admin by the altar (each on its own spot) ({sorted(_sm)})")
st.run.player, st.anim = (23, 13), 0
st.dialogue_box.visible = False
_calm(st); st.step(0, -1)
said = _play(st, 2500)
check(story.story_flags.get("mt_pyre_leader_left") and any("Orb" in x for x in said), f"Mt. Pyre summit: the leader takes the Orb and leaves his Admin to battle you ({said[:1]})")
story.story_flags["mt_pyre_cleared"] = True
st = open_map("HOENN_MT_PYRE", "HOENN_ROUTE_122")
st.run.enter_floor(1); frames(2)
check(_mv(st).get((22, 5)) == "TALK TO THE ELDERS", "Mt. Pyre summit: after the Admin, the elders by the altar")
_tmp = json.load(open("assets/town_maps.json", encoding="utf-8"))["HOENN_MT_PYRE"]
check(_tmp["figure_floors"].get("TM105 SHADOW BALL") == 7 and _tmp["figure_floors"].get("SEA INCENSE") == 4 and _tmp["floors"][2].get("landings") == [[20, 9]], "Mt. Pyre: TM105 Shadow Ball on 6F, the Sea Incense on 3F; 1F's landing spot under 2F's hole")
st = open_map("HOENN_ROUTE_123", "HOENN_ROUTE_118")
st._use_figure(_fig10(st, "Magikarp fan")); tap(st)
check(story.inventory.get("EVIOLITE") == 1, "Route 123: the Magikarp fan by the pond gives an Eviolite")
story.player_team = [p for p in _team10 if "GRASS" not in [str(t).upper() for t in (p.types or [])]] or [Pokemon(g.loader.fetch_specific(258), g.assets)]
_gl = next(m for m in st.run.floor.movers if (m.x, m.y) == (108, 13))
st._use_figure(_gl); tap(st)
_no = story.inventory.get("TM28")
story.player_team = story.player_team + [Pokemon(g.loader.fetch_specific(252), g.assets)]
st.dialogue_box.visible = False
st._use_figure(_gl); tap(st)
check(not _no and story.inventory.get("TM28") == 1, "Route 123: the Grass lover gives TM28 Giga Drain only to a Trainer with a Grass type")
_b0 = sum(v for k, v in story.inventory.items() if k.endswith("_BERRY"))
st.run.player, st.anim = (22, 7), 0
st.dialogue_box.visible = False
_calm(st); st.step(0, -1); tap(st)
check(sum(v for k, v in story.inventory.items() if k.endswith("_BERRY")) - _b0 == 2, "Route 123: the Berry Master gives two Berries a day")
g.change_state(st)
story.repel_routes = _rep10
story.badges.clear(); story.badges.update(_badges10)
story.player_team = _team10
story.inventory.clear(); story.inventory.update(_inv10)
story.story_flags.clear(); story.story_flags.update(_saved10)

# ---- batch 11: Slateport's stolen submarine, Lilycove City, the team's hideout (ORAS, parts 13-14)
_saved11, _inv11, _team11 = dict(story.story_flags), dict(story.inventory), list(story.player_team)
_rep11 = getattr(story, "repel_routes", 0)
story.repel_routes = 9
for _k in ("slateport_sub_stolen", "hoenn_rival_lilycove", "lilycove_rival_met", "aqua_hideout_cleared", "got_altarianite",
           "lilycove_berry_day", "got_master_ball_hideout", "hideout_electrode_1"):
    story.story_flags.pop(_k, None)
for _k in ("ALTARIANITE", "MASTER_BALL"):
    story.inventory.pop(_k, None)
story.story_flags.update({"got_mt_pyre_orb": True, "mt_pyre_cleared": True, "slateport_grunt_defeated": True,
                          "oceanic_museum_cleared": True, "contest_pass_received": True})
st = open_map("SLATEPORT_CITY", "HOENN_ROUTE_110")
st.scenes.entered = True
st.player, st.anim = (23, 15), 0
_calm(st); st.step(1, 0)
said = _play(st, 2500)
check("<TrainerIntroState>" in said and any("submarine" in x for x in said),
      f"Slateport: after Mt. Pyre, the leader takes Captain Stern's submarine and a Grunt keeps you busy ({said[:1]})")
story.story_flags["slateport_sub_stolen"] = True
st = open_map("SLATEPORT_CITY", "HOENN_ROUTE_110")
_fs = [o.get("text") for o in st._door_options("harbor") if st._shown(o)]
st = open_map("LILYCOVE_CITY", "HOENN_ROUTE_121")
_fl = [o.get("text") for o in st._door_options("harbor")]
check("Ferry to Lilycove" in _fs and "Ferry to Slateport" in _fl, f"Slateport and Lilycove: the ferry between their harbours, once the sub is taken ({_fs}, {_fl})")
check((70, 5) in st.barred and sum(1 for t in st.barred if t[0] == 79) == 8,
      "Lilycove: a Grunt guards the cave in the cove; the team's Wailmer block the sea way to Route 124")
st.scenes.entered = True
st.player, st.anim = (31, 17), 0
st.step(0, -1)
said = _play(st, 2500)
check("<TrainerIntroState>" in said, f"Lilycove: by the north stairs your rival walks up for a battle ({said[:1]})")
story.story_flags["hoenn_rival_lilycove"] = True
st = open_map("LILYCOVE_CITY", "HOENN_ROUTE_121")
check((70, 5) not in st.barred and st.exits.get((70, 5)) == "HOENN_TEAM_HIDEOUT", "Lilycove: after your rival, the cave is open (Surf across the cove)")
_col = next(o for o in st.people.values() if isinstance(o, dict) and o.get("text") == "The Collector")
story.player_team = [p for p in _team11 if p.id != 334] or [Pokemon(g.loader.fetch_specific(258), g.assets)]
st._get_callback_for_option(_col)(); tap(st)
_no = story.inventory.get("ALTARIANITE")
story.player_team = story.player_team + [Pokemon(g.loader.fetch_specific(334), g.assets)]
st._get_callback_for_option(_col)(); tap(st)
check(not _no and story.inventory.get("ALTARIANITE") == 1, "Lilycove: the Fan Club man gives the Altarianite once you show him an Altaria")
# Lilycove's buildings walked inside (Emerald's own rooms): the store's floors by its stairs, a clerk across the counter
def _stairs(st, target):
    """Step onto the room's way out that leads to target, from the open tile beside it (as a player walks up the stairs)."""
    t = next(t for t, v in st.exits.items() if v == target)
    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        b = (t[0] + dx, t[1] + dy)
        if st._open(b) and b not in st.exits and b not in st._people():
            st.player, st.anim = b, 0
            st.step(-dx, -dy); frames(2)
            return st.room
    return None


st = open_map("LILYCOVE_CITY", "HOENN_ROUTE_121")
st.scenes.entered = True
st.player, st.anim = (27, 7), 0
st.step(0, -1); frames(2)
_floors = [st.room]
for _r in ("dept_2", "dept_3", "dept_4", "dept_5", "dept_roof"):
    _floors.append(_stairs(st, "ROOM:" + _r))
check(_floors == ["dept", "dept_2", "dept_3", "dept_4", "dept_5", "dept_roof"],
      f"Lilycove: in at the Department Store's door, and up its stairs floor by floor to the rooftop ({_floors})")
_down = [_stairs(st, "ROOM:dept_5"), _stairs(st, "ROOM:dept_4"), _stairs(st, "ROOM:dept_3"), _stairs(st, "ROOM:dept_2"), _stairs(st, "ROOM:dept")]
_out = next(v for v in st.exits.values() if str(v).startswith("OUT:"))
_stairs(st, _out)
check(_down[-1] == "dept" and st.room is None and st.player == (27, 7), f"Lilycove: down again and out of the store's door ({_down}, {st.player})")
st._go("dept_2", "ROOM:dept_3"); frames(2)
st.player, st.facing, st.anim = (10, 4), (0, 1), 0
st.step(0, 1); frames(2)
_cs = g.current_state
check(type(_cs).__name__ == "PokeMartState" and "GREAT_BALL" in (_cs.stock or []) and "TM08" not in (_cs.stock or []),
      f"Lilycove: 2F's clerk across the counter sells his own shelf (Poke Balls, medicine) ({type(_cs).__name__})")
g.change_state(st)
_shelves = {o.get("text"): o.get("stock") for r in _tm2["LILYCOVE_CITY"]["rooms"].values() for o in r.get("people", []) if isinstance(o, dict) and o.get("stock")}
check(_shelves.get("Attack TM clerk") == ["TM08", "TM03", "TM05", "TM04"] and "X_ATTACK" in _shelves.get("Battle clerk", [])
      and "LEMONADE" in _shelves.get("Rooftop stand", []) and "RED_POKEBLOCK" in _shelves.get("Contest clerk", []),
      f"Lilycove: each counter of the store sells its own kind of thing (2F travel and Trainer goods, 3F X items, 4F TMs, 5F Pokeblocks, rooftop drinks)")
check("Department Store" in _tm2["LILYCOVE_CITY"]["rooms"]["dept_3"]["people"], "Lilycove: 3F keeps the store's old shelf (its evolution stones)")
st._go("dept", "ROOM:dept_2"); frames(2)
_loto = next(o for o in st.people.values() if isinstance(o, dict) and o.get("text") == "Loto clerk")
_before = sum(story.inventory.get(k, 0) for k in ("MOOMOO_MILK", "RARE_CANDY", "MASTER_BALL"))
story.story_flags.pop("lilycove_loto_day", None)
st._get_callback_for_option(_loto)(); tap(st)
_one = sum(story.inventory.get(k, 0) for k in ("MOOMOO_MILK", "RARE_CANDY", "MASTER_BALL"))
st._get_callback_for_option(_loto)(); tap(st)
check(_one == _before + 1 and sum(story.inventory.get(k, 0) for k in ("MOOMOO_MILK", "RARE_CANDY", "MASTER_BALL")) == _one,
      "Lilycove: 1F's Lottery Corner, one Loto prize a day")
# the Museum: the curator keeps the stairs till a Master Rank win; upstairs, a portrait of each champion
_rib = [list(getattr(p, "ribbons", []) or []) for p in story.player_team]
for p in story.player_team:
    p.ribbons = []
story.pc_pokemon = [None] * 300
st._go(None, "OUT:27,6"); frames(2)
st.player, st.anim = (12, 6), 0
st.step(0, -1); frames(2)
_shut = st.room == "museum" and (16, 2) in st.barred
story.player_team[0].ribbons = ["BEAUTY_MASTER"]
st._go("museum", "OUT:12,5"); frames(2)
_open = (16, 2) not in st.barred
_up = _stairs(st, "ROOM:museum_2")
_por = sorted(t for t, b in st.barred.items() if str(b.get("look")).startswith("ribbon:"))
st.player, st.facing, st.anim = (10, 7), (0, -1), 0
st.step(0, -1)
said = _play(st, 200)
_nm = story.player_team[0].display_name
check(_shut and _open and _up == "museum_2" and _por == [(10, 6)] and any(_nm in x and "Beauty" in x for x in said),
      f"Lilycove Museum: the curator lets you upstairs after a Master Rank win; your Beauty champion's portrait hangs there ({_por}, {said[:1]})")
_cur = next(o for o in st.people.values() if isinstance(o, dict) and o.get("text") == "Curator")
story.inventory.pop("GLASS_ORNAMENT", None)
st._get_callback_for_option(_cur)(); tap(st)
_none = story.inventory.get("GLASS_ORNAMENT")
story.player_team[0].ribbons = [c + "_MASTER" for c in ("COOL", "BEAUTY", "CUTE", "SMART", "TOUGH")]
st._go("museum_2", "ROOM:museum"); frames(2)
_all = sorted(t for t, b in st.barred.items() if str(b.get("look")).startswith("ribbon:"))
st._get_callback_for_option(_cur)(); tap(st)
check(not _none and story.inventory.get("GLASS_ORNAMENT") == 1 and len(_all) == 5,
      "Lilycove Museum: all five portraits up, and the curator's thank-you gift")
for p, r in zip(story.player_team, _rib):
    p.ribbons = r
# the motel (Game Freak upstairs: the Diploma for a full Hoenn Pokedex) and the Pokeblock Master's house
st._go("motel_2", "ROOM:motel"); frames(2)
_gd = next(o for o in st.people.values() if isinstance(o, dict) and o.get("text") == "Game designer")
story.story_flags.pop("hoenn_catch_143", None); story.story_flags.pop("hoenn_diploma", None); story.inventory.pop("DIPLOMA", None)
st._get_callback_for_option(_gd)(); tap(st)
_no = story.inventory.get("DIPLOMA")
story.story_flags["hoenn_catch_143"] = True
st._get_callback_for_option(_gd)(); tap(st)
check(not _no and story.inventory.get("DIPLOMA") == 1, "Cove Lily Motel: Game Freak's designer gives a Diploma for a full Hoenn Pokedex")
st._go(None, "OUT:11,22"); frames(2)
st.player, st.anim = (11, 23), 0
st.step(0, -1); frames(2)
_pm = next((o for o in st.people.values() if isinstance(o, dict) and o.get("text") == "Pokéblock Master"), None)
story.story_flags.pop("got_pokeblock_master_gift", None)
_rb = story.inventory.get("RED_POKEBLOCK", 0)
if _pm:
    st._get_callback_for_option(_pm)(); tap(st)
check(st.room == "pokeblock_house" and story.inventory.get("RED_POKEBLOCK", 0) == _rb + 1,
      f"Lilycove: the Pokeblock Master's house, north of the harbour: her tips and a Pokeblock of each colour ({st.room})")
st._go(None, "OUT:11,22"); frames(2)
_mg = next(o for o in st.people.values() if isinstance(o, dict) and o.get("text") == "Memory Girl")
st._get_callback_for_option(_mg)()
said = _play(st, 200)
check(any("memories" in x for x in said) and any(story.player_team[0].display_name in x for x in said),
      f"Lilycove: the Memory Girl outside the Center reads your first Pokemon's memories ({said[:2]})")
_lin = _tm2["LILYCOVE_CITY"].get("inside", {})
_nod = sorted("%d,%d" % t for t in st.doors if "%d,%d" % t not in _lin)
_inroom = {q.get("text") if isinstance(q, dict) else q for r in _tm2["LILYCOVE_CITY"]["rooms"].values() for q in r.get("people", [])}
_kept = all(o.get("text") in _inroom or "door:" + k in _inroom for t, k in st.doors.items() if "%d,%d" % t in _lin for o in st._door_options(k))
check(not _nod and _kept, f"Lilycove: every door leads inside, and whoever ran its menu is in there (nurse, Contest counter, harbour sailor) ({_nod})")
st.player, st.anim = (36, 7), 0
st.step(0, -1); frames(2)
_md = next(o for o in st.people.values() if isinstance(o, dict) and o.get("text") == "Move Deleter")
st._get_callback_for_option(_md)()
said = _play(st, 200)
check(st.room == "move_deleter" and any("forgot how" in x for x in said), f"Lilycove: the Move Deleter has forgotten how to delete moves ({said[-1:]})")
st._go("house_sleepy", "OUT:55,15"); frames(2)
story.story_flags.pop("got_tm21_lilycove", None); story.inventory.pop("TM21", None)
st._get_callback_for_option(next(o for o in st.people.values() if isinstance(o, dict) and o.get("text") == "Sleepy man"))(); tap(st)
check(story.inventory.get("TM21") == 1, "Lilycove: the sleepy man in the house by the Berry gentleman gives TM21 Rest")
st._go("center", "OUT:24,14"); frames(2)
_hp = story.player_team[0]; _hp.current_hp = 1
st.player, st.facing, st.anim = (7, 4), (0, -1), 0
st.step(0, -1); frames(2); tap(st)
check(_hp.current_hp == _hp.get_max_hp(), "Lilycove: the Pokemon Center's nurse heals you across her counter")
st._go("contest_lobby", "OUT:23,24"); frames(2)
_up = _stairs(st, "ROOM:contest_hall")
check("Contest Hall" in _tm2["LILYCOVE_CITY"]["rooms"]["contest_lobby"]["people"] and _up == "contest_hall",
      "Lilycove: the Contest lobby's counter enters you in Contests; through to the hall's stages")
st._go(None, "OUT:24,14"); frames(2)
st = open_map("HOENN_TEAM_HIDEOUT", "LILYCOVE_CITY")
check(st._floor_name(0) == "1F" and "Magma" in g.loader.area_data["STORY_PROGRESSION"]["HOENN_TEAM_HIDEOUT"]["route_name"],
      "The hideout: the version's team's (Team Magma Hideout in Omega Ruby)")
# the whole way through: the stairs and Emerald's warp panels lead from the cave mouth to the Admin in the sub room
_hf = json.load(open("assets/town_maps.json", encoding="utf-8"))["HOENN_TEAM_HIDEOUT"]["floors"]
_ok = set(".=\"NX1w$o")   # (o: 1F's water, crossed with Surf)
_todo = [(0, x, y) for y, r in enumerate(_hf[0]["art"]) for x, c in enumerate(r) if c not in _ok and c in _hf[0].get("exits", {})]
_seen = set(_todo)
while _todo:
    _f, _x, _y = _todo.pop()
    _ln = (_hf[_f].get("links") or {}).get(f"{_x},{_y}")
    _nxt = [(_ln[0], _ln[1], _ln[2])] if _ln else []
    _nxt += [(_f, _x + dx, _y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))]
    for _n in _nxt:
        _a = _hf[_n[0]]["art"]
        if _n not in _seen and 0 <= _n[2] < len(_a) and 0 <= _n[1] < len(_a[0]) and _a[_n[2]][_n[1]] in _ok:
            _seen.add(_n); _todo.append(_n)
_near = lambda f, x, y: any((f, x + dx, y + dy) in _seen for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)))
check(_near(2, 23, 10) and _near(1, 15, 9), "The hideout: from the cave mouth, down the stairs and through the warp panels to the leader's room and the Admin")
st.run.enter_floor(1); frames(2)
_calm(st)
_mb = next(m for m in st.run.floor.movers if isinstance(m.payload, dict) and m.payload.get("text") == "MASTER BALL")
st._use_figure(_mb); tap(st)
_el = next(m for m in st.run.floor.movers if isinstance(m.payload, dict) and m.payload.get("text") == "POKE BALL")
st.dialogue_box.visible = False
st._use_figure(_el)
said = _play(st, 300)
check(story.inventory.get("MASTER_BALL") == 1 and "<WildBattleState>" in said,
      "The hideout: the leader's room's Poke Balls: the Master Ball, and an Electrode in disguise")
g.change_state(st)
# the sub room: five Grunts rush you (ORAS's horde battle), one battle with their five Poochyena
st = open_map("HOENN_TEAM_HIDEOUT", "LILYCOVE_CITY")
st.run.enter_floor(1); frames(2)
st.run.enter_floor(2); frames(2)
_calm(st)
story.story_flags.pop("hideout_horde_beaten", None)
st.run.player, st.anim = (20, 12), 0
st.step(-1, 0)
said = _play(st, 3000)
from src.states.overworld.common import _start_event_battle
_hz = next(s for s in _hf[2]["scenes"] if s["flag"] == "hideout_horde_beaten")
_hb = _start_event_battle(g, "HOENN_TEAM_HIDEOUT", _hz["cast"][-1]["event"]["battle"], "hideout_horde_beaten")
_hbt = getattr(_hb, "battle", None) or getattr(_hb, "next_state", None)
_ht = [p.id for p in getattr(_hbt, "opponent_team", None) or []]
check("<TrainerIntroState>" in said and any("Five of us" in x for x in said) and len(_hz["cast"]) == 5,
      f"The hideout: in the sub room five Grunts run up together and battle you ({said[:1]})")
check(_ht == [261] * 5 and "Magma Grunts" in str(getattr(_hbt, "trainer_name", "")),
      f"The hideout: the five Grunts' battle is their five Poochyena, in this version's team ({getattr(_hbt, 'trainer_name', '')}, {_ht})")
g.change_state(st)
story.repel_routes = _rep11
story.player_team = _team11
story.inventory.clear(); story.inventory.update(_inv11)
story.story_flags.clear(); story.story_flags.update(_saved11)

# ---- batch 12: the Safari Zone (Emerald's six areas stitched into one map) and the Safari Game
_saved12, _inv12 = dict(story.story_flags), dict(story.inventory)
_sz = _tm2["HOENN_SAFARI_ZONE"] if "HOENN_SAFARI_ZONE" in _tm2 else json.load(open("assets/town_maps.json", encoding="utf-8"))["HOENN_SAFARI_ZONE"]
_sa = g.loader.area_data["STORY_PROGRESSION"]["HOENN_SAFARI_ZONE"]
check(len(_sz["zone_rects"]) == 6 and len(_sa["zones"]) == 6 and all(g.loader.area_data.get(v) for v in _sa["zone_pools"].values()),
      "Safari Zone: one map of Emerald's six areas, each its own zone with its own Pokemon (5 and 6: Emerald's Johto ones)")
check(any(o.get("door") == "safari" and o.get("target_area") == "HOENN_SAFARI_ZONE" for o in g.loader.area_data["STORY_PROGRESSION"]["HOENN_ROUTE_121"]["route_menu"])
      and "HOENN_ROUTE_121" in _sz["floors"][0]["exits"].values() if _sz.get("floors") else "HOENN_ROUTE_121" in _sz["exits"].values(),
      "Safari Zone: in by Route 121's Safari Zone door, out by the entrance building again")
story.story_flags.pop("beat_hoenn_champion", None)
st = open_map("HOENN_SAFARI_ZONE", "HOENN_ROUTE_121")
_calm(st)
said = _play(st, 300)
_sf = dict(st.safari or {})
check(_sf.get("balls") == 30 and _sf.get("steps") == 500 and "hello" not in _sf,
      f"Safari Game: each visit, 30 Safari Balls and 500 steps ({_sf}, {said[:1]})")
def _try_east(st):
    st.run.player, st.anim = (75, 56), 0
    st.step(1, 0); frames(12)
    _play(st, 200)
    return st.run.player


_shut12 = _try_east(st)
check(_shut12 == (75, 56), f"Safari Zone: workers close Emerald's new eastern areas until you're Champion ({_shut12})")
st.run.player, st.anim = (66, 69), 0
_x, _y = st.run.player
_mv = next(((dx, dy) for dx, dy in ((0, -1), (1, 0), (-1, 0), (0, 1)) if st.run.floor.walkable(_x + dx, _y + dy)), (0, -1)) if hasattr(st.run.floor, "walkable") else (0, -1)
st.anim = 0
st.step(*_mv); frames(12)
check(st.safari and st.safari["steps"] == 499, f"Safari Game: each step counts down ({st.safari})")
st.encounter = None
st._pick(1)
check(st.mode != "BATTLE" and "battling" in str(getattr(st, "toast", "")).lower(), f"Safari Game: no battling wild Pokemon, only catching ({st.toast})")
st.safari["steps"] = 0
said = _play(st, 600)
frames(90)
check(any("Time's up" in x for x in said) and story.current_area_key == "HOENN_ROUTE_121",
      f"Safari Game: out of steps, the visit ends and you're back on Route 121 ({said[:1]}, {story.current_area_key})")
story.story_flags["beat_hoenn_champion"] = True
st = open_map("HOENN_SAFARI_ZONE", "HOENN_ROUTE_121")
_play(st, 300)
_calm(st)
check(_try_east(st) == (76, 56), "Safari Zone: once you're Champion the new areas are open")
check("rest_house" in (_sz.get("rooms") or {}) or any(n == "Rest House" for n in (_sz.get("floor_names") or [])),
      "Safari Zone: the rest house walked inside")
story.inventory.clear(); story.inventory.update(_inv12)
story.story_flags.clear(); story.story_flags.update(_saved12)

# ---- batch 13: Route 124 (Dive), Mossdeep City, the Space Center, Route 125
_saved13, _inv13, _team13 = dict(story.story_flags), dict(story.inventory), list(story.player_team)
_tm13 = json.load(open("assets/town_maps.json", encoding="utf-8"))
st = open_map("HOENN_ROUTE_124", "LILYCOVE_CITY")
_calm(st)
_deep = [(x, y) for y, r in enumerate(_tm13["HOENN_ROUTE_124"]["floors"][0]["art"]) for x, c in enumerate(r) if c == ":"]
_below = st.run.made(1)
_spot = next(t for t in _deep if _below.walkable(*t) and 20 <= t[1] <= 70)
story.inventory["HM_DIVE"] = 1
st.run.player, st.anim = _spot, 0
st.dive_here(); frames(4)
_dove = st.run.index
st.surface_here(); frames(4)
check(_dove == 1 and st.run.index == 0 and tuple(st.run.player) == _spot,
      f"Route 124: Dive on the deep, dark sea to the seabed, and come back up ({_spot}, {_dove})")
_north = [t for t in _deep if t[1] < 14 and _below.walkable(*t)]
check(len(_north) >= 4, f"Route 124: the rocky northern waters are reached from the seabed, coming up through their deep patches ({len(_north)})")
_shards = {o["text"] for o in g.loader.area_data["STORY_PROGRESSION"]["HOENN_ROUTE_124"]["route_menu"] if "SHARD" in o["text"]}
check(_shards == {"RED SHARD", "BLUE SHARD", "YELLOW SHARD", "GREEN SHARD"}, f"Route 124: four Shards to find, one on the seabed ({_shards})")
_th = next(o for o in _tm13["HOENN_ROUTE_124"]["rooms"]["treasure_hunter"]["people"] if isinstance(o, dict))
story.inventory.update({"RED_SHARD": 2}); story.inventory.pop("FIRE_STONE", None)
from src.states.overworld.common import _run_story_event
_said13 = []
_run_story_event(st, _th["event"], lambda c: True, lambda l, **k: _said13.extend(l))
tap(st)
check(story.inventory.get("FIRE_STONE") == 1 and story.inventory.get("RED_SHARD") == 1,
      "Route 124: the Treasure Hunter trades an evolution stone for a Shard (red: a Fire Stone)")
# Mossdeep: every door leads inside; the earthquake after the Mind Badge; the townsfolk's gifts
st = open_map("MOSSDEEP_CITY", "HOENN_ROUTE_124")
st.scenes.entered = True
_m = _tm13["MOSSDEEP_CITY"]
_inroom = {q.get("text") if isinstance(q, dict) else q for r in _m["rooms"].values() for q in r.get("people", [])}
_nod = sorted(k for k, v in st.doors.items() if "%d,%d" % k not in (_m.get("inside") or {}) and v != "gym")
check(not _nod and {"Heal", "Shop", "Steven's House"} <= _inroom,
      f"Mossdeep: every door but the Gym's leads inside; the nurse, the clerk and Steven's note are in there ({_nod})")
for _k in ("mossdeep_steven_dive", "badge_mind_earned"):
    story.story_flags.pop(_k, None)
story.badges.setdefault("HOENN", [])
story.story_flags["badge_mind_earned"] = True
st, said = _scene("MOSSDEEP_CITY", "HOENN_ROUTE_124", ["badge_mind_earned"], ["mossdeep_steven_dive"], at=(38, 10), step=(0, 1))
check(story.story_flags.get("mossdeep_steven_dive") and any("Seafloor Cavern" in x for x in said),
      f"Mossdeep: after the Mind Badge, the earthquake, and Steven sends you diving for the Seafloor Cavern ({said[:1]})")
def _talk13(room, name):
    st._go(room, "")
    frames(2)
    o = next(o for o in st.people.values() if isinstance(o, dict) and o.get("text") == name)
    st._get_callback_for_option(o)()
    return _play(st, 300)
story.inventory.pop("SUPER_ROD", None)
_talk13("rod_house", "Super Rod fisherman")
_rod = story.inventory.get("SUPER_ROD", 0)
_talk13("rod_house", "Super Rod fisherman")
check(_rod == 1 and story.inventory.get("SUPER_ROD") == 1, "Mossdeep: the fisherman by the launchpad gives the Super Rod, once")
_cap = []
st._create_hover_menu = lambda opts, _b: _cap.append(opts)
story.badges["HOENN"] = ["STONE", "KNUCKLE", "DYNAMO"]
story.story_flags.pop("badge_trivia_day", None)
_inv_b = dict(story.inventory)
said = _talk13("hex_house", "Badge reader")
_q = [x for x in said if "?" in x]
_right = next((o for o in (_cap[0] if _cap else []) if o["event"].get("gift_item")), None)
if _right:
    st._get_callback_for_option(_right)(); tap(st)
_won = sum(story.inventory.values()) > sum(_inv_b.values())
_three = bool(_cap) and len({o["text"] for o in _cap[0]}) == 3
_cap.clear()
said2 = _talk13("hex_house", "Badge reader")
check(_q and _three and len(_cap) == 0 and _right and _won and any("tomorrow" in x for x in said2),
      f"Mossdeep: the Hex Maniac's daily question about one of your badges; a right answer wins a prize; once a day ({_q[-1:]}, {_right and _right['text']})")
del st._create_hover_menu
story.story_flags.pop("mossdeep_wingull_letter", None); story.story_flags.pop("got_mental_herb_fortree", None); story.inventory.pop("MENTAL_HERB", None)
_talk13("wingull_house", "Wingull")
_ft = next(o for o in g.loader.area_data["STORY_PROGRESSION"]["FORTREE_CITY_UPPER"]["explore_options"] if o.get("door") == "wingull") if "FORTREE_CITY_UPPER" in g.loader.area_data["STORY_PROGRESSION"] else next(o for a in g.loader.area_data["STORY_PROGRESSION"].values() if isinstance(a, dict) for o in a.get("explore_options", []) if o.get("door") == "wingull")
_run_story_event(st, _ft["event"], lambda c: st._check_menu_condition(c) if hasattr(st, "_check_menu_condition") else True, lambda l, **k: None)
tap(st)
check(story.story_flags.get("mossdeep_wingull_letter") and story.inventory.get("MENTAL_HERB") == 1,
      "Mossdeep's Wingull flies a letter to Fortree; its trainer there gives you a Mental Herb")
said = _talk13("block_house", "Block taster")
check(any("Pokéblocks" in x for x in said), f"Mossdeep: the man who can tell which Pokeblocks your Pokemon likes ({said[-1:]})")
st._go(None, "OUT:23,13"); frames(2)
story.story_flags.pop("got_kings_rock_mossdeep", None); story.inventory.pop("KINGS_ROCK", None)
st._get_callback_for_option(next(o for o in st.people.values() if isinstance(o, dict) and o.get("text") == "Rock boy"))(); tap(st)
check(story.inventory.get("KINGS_ROCK") == 1, "Mossdeep: the boy by Steven's house gives you the King's Rock")
story.story_flags["beat_hoenn_champion"] = True
story.story_flags.pop("got_beldum_steven", None)
story.player_team = _team13[:5]
_n13 = len(story.player_team)
_talk13("steven", "Beldum's Poké Ball")
check(len(story.player_team) == _n13 + 1 and story.player_team[-1].id == 374, "Mossdeep: once you're Champion, Steven leaves you a Beldum")
story.player_team = _team13
# the Space Center: quiet before the Mind Badge, stormed after it
story.story_flags.pop("badge_mind_earned", None)
st = open_map("HOENN_SPACE_CENTER", "MOSSDEEP_CITY")
_quiet = not any(m.kind == "trainer" for f in st.run.floors for m in f.movers)
story.story_flags["badge_mind_earned"] = True
st = open_map("HOENN_SPACE_CENTER", "MOSSDEEP_CITY")
st.run.enter_floor(1); frames(2)
_all13 = [(m.payload[1] if isinstance(m.payload, tuple) else m.payload).get("name") for f in st.run.floors for m in f.movers if m.kind == "trainer"]
check(_quiet and len(_all13) == 3, f"Space Center: Emerald's two floors; the team storms it only after the Mind Badge ({_all13})")
_r125 = _tm13["HOENN_ROUTE_125"]
check(not _r125.get("floors") and "HOENN_SHOAL_CAVE" in _r125["exits"].values() and len(_r125.get("trainer_spots", [])) == 3,
      "Route 125: Emerald's map, its three Trainers, and Shoal Cave's mouth")
story.player_team = _team13
story.inventory.clear(); story.inventory.update(_inv13)
story.story_flags.clear(); story.story_flags.update(_saved13)

# ---- batch 14: Shoal Cave and its tides
_saved14, _inv14 = dict(story.story_flags), dict(story.inventory)
from src.states.overworld import dungeon as _dg14
_ht = _dg14.high_tide
story.inventory["HM_SURF"] = 1
_dg14.high_tide = lambda now=None: False
st = open_map("HOENN_SHOAL_CAVE", "HOENN_ROUTE_125")
_low = st.run.index
_dg14.high_tide = lambda now=None: True
st = open_map("HOENN_SHOAL_CAVE", "HOENN_ROUTE_125")
_high = st.run.index
_dg14.high_tide = _ht
check(_low == 0 and _high == 5 and "Route 125" not in st._floor_name(5) and "high" in st._floor_name(5),
      f"Shoal Cave: walking in at low tide you find the dry entrance; at high tide, the flooded one ({_low}, {_high})")
check(_dg14.high_tide(__import__("datetime").datetime(2026, 1, 1, 4)) and not _dg14.high_tide(__import__("datetime").datetime(2026, 1, 1, 10)),
      "Shoal Cave: high tide from 3:00 to 9:00 and 15:00 to 21:00 (real time)")
_sc = json.load(open("assets/town_maps.json", encoding="utf-8"))["HOENN_SHOAL_CAVE"]["floors"]
check(all(v[0] in (5, 6) for v in _sc[6].get("links", {}).values()) and any(v[0] in (2, 3) for v in _sc[1].get("links", {}).values()),
      "Shoal Cave: the ladders down to its lower rooms are only above water at low tide")
st.run.enter_floor(0); frames(2)
_mk = next(m.payload for f in st.run.floors for m in f.movers if isinstance(m.payload, dict) and m.payload.get("text") == "Shell Bell maker ")
from src.states.overworld.common import _run_story_event
story.inventory.update({"SHOAL_SALT": 4, "SHOAL_SHELL": 3}); story.inventory.pop("SHELL_BELL", None)
_run_story_event(st, _mk["event"], lambda c: True, lambda l, **k: None); tap(st)
_none14 = story.inventory.get("SHELL_BELL")
story.inventory["SHOAL_SHELL"] = 4
_run_story_event(st, _mk["event"], lambda c: True, lambda l, **k: None); tap(st)
check(not _none14 and story.inventory.get("SHELL_BELL") == 1 and not story.inventory.get("SHOAL_SALT"),
      "Shoal Cave: the old man makes a Shell Bell from four Shoal Salt and four Shoal Shells")
_salt = next(o for o in json.load(open("assets/town_maps.json", encoding="utf-8"))["HOENN_SHOAL_CAVE"]["floors"][2]["people"] if isinstance(o, dict) and o.get("text") == "SHOAL SALT")
story.story_flags.pop("shoal_salt_1", None)
_run_story_event(st, _salt["event"], lambda c: True, lambda l, **k: None); tap(st)
_one = story.inventory.get("SHOAL_SALT", 0)
_run_story_event(st, _salt["event"], lambda c: True, lambda l, **k: None); tap(st)
check(_one == 2 and story.inventory.get("SHOAL_SALT") == 2, "Shoal Cave: Shoal Salt to pick up again each day")
story.inventory.clear(); story.inventory.update(_inv14)
story.story_flags.clear(); story.story_flags.update(_saved14)

story.story_flags.clear(); story.story_flags.update(_saved)
print(f"##### {len(fails)} failures")
