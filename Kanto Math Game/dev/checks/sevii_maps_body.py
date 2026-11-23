# The Sevii Islands' maps laid out from FireRed's map data (dev/builders/town_maps/frlg.py SEVII), entered the way a player would:
# into each town and route by each of its ways in, through its doors, across to each other way out.
#   cat dev/checks/harness_head.py dev/checks/sevii_maps_body.py > dev/checks/out/check_sevii_maps.py
#   python dev/checks/out/check_sevii_maps.py <scratch dir>
import json
from src.states.overworld import PlayState, CityState as _CS
from src.states.overworld.dungeon import DungeonState
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.dungeon import core

fails = 0
g.dungeon_routes = True
g.walk_towns = True
MAPS = json.load(open("assets/town_maps.json", encoding="utf-8"))
DATA = json.load(open("assets/sevii_area_data.json", encoding="utf-8"))["STORY_PROGRESSION"]


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


def frames(p, n=1):
    for _ in range(n):
        g.current_state.update()
        g.current_state.draw()


def _tap_through(st, n=400):
    for _ in range(n):
        if not getattr(st, "npc_active", False):
            return
        st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        frames(st)


def town(area, came):
    g.walk_town_pos = None
    g.walk_town_exit = None
    g.walk_town_room = None
    story.current_area_key, story.last_area_key = area, came
    st = _CS(g); g.change_state(st); _tap_through(st)
    return st


def route(area, came, index=0, count=0):
    core.ENTRANCE_INDEX, core.ENTRANCE_COUNT = index, count
    story.current_area_key, story.last_area_key = area, came
    story.player_team = [mk(4)]
    story.player_team[0].level = 60
    story.balls_left = 20
    p = PlayState(g)
    g.states["play"] = p
    g.change_state(p)
    frames(p, 3)
    return p


def enter(t, door):
    t.player = t.anim_from = (door[0], door[1] + 1); t.anim = 0; t.walk_goal = None
    t.step(0, -1); t.anim = 0


def reach_town(t, start):
    seen, todo = {start}, [start]
    while todo:
        x, y = todo.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in seen and 0 <= n[0] < t.w and 0 <= n[1] < t.h and t._open(n):
                seen.add(n); todo.append(n)
    return seen


def reach(f, start):
    """Every tile a player with every HM gets to from start on this floor (ledges and things in the way counted as passed)."""
    ok = lambda t: f.walkable(*t) or t in f.exits or str(f.decor.get(t, "")).split(":")[0] in ("ledge", "crack", "cut", "boulder", "falls")
    seen, todo = {start}, [start]
    while todo:
        x, y = todo.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in seen and f.inside(*n) and ok(n):
                seen.add(n); todo.append(n)
    return seen


_inv = dict(story.inventory)
_flags = dict(story.story_flags)
for _k in ("HM_SURF", "HM_CUT", "HM_STRENGTH", "HM_ROCK_SMASH", "HM_WATERFALL", "TRI_PASS", "RAINBOW_PASS"):
    story.inventory[_k] = 1
for _k in ("beat_three_island_bikers", "heard_lostelle", "sapphire_stolen", "met_lorelei_sevii"):
    story.story_flags[_k] = True

# ---- the towns: (area, size, {way out: somewhere it must lead}, {door kind that must open something})
TOWNS = [
    ("TWO_ISLAND", (48, 20), {"CAPE_BRINK"}, {"center", "harbor", "gamecorner"}),
    ("THREE_ISLAND", (48, 60), {"BOND_BRIDGE", "THREE_ISLE_PORT"}, {"center", "mart", "harbor"}),
    ("FOUR_ISLAND", (48, 40), {"ICEFALL_CAVE"}, {"center", "mart", "harbor", "daycare", "lorelei", "house"}),
    ("FIVE_ISLAND", (24, 20), {"FIVE_ISLE_MEADOW", "WATER_LABYRINTH"}, {"center", "harbor"}),
    ("SIX_ISLAND", (24, 30), {"WATER_PATH"}, {"center", "mart", "harbor", "notes"}),
    ("SEVEN_ISLAND", (120, 60), {"CANYON_ENTRANCE"}, {"center", "mart", "harbor", "gym"}),
]
for _a, _size, _outs, _kinds in TOWNS:
    for _came in sorted(_outs):
        t = town(_a, _came)
        _near = min((abs(x - t.player[0]) + abs(y - t.player[1]) for (x, y), v in t.exits.items() if v == _came), default=99) if isinstance(t, _WTS) else 99
        check(isinstance(t, _WTS) and (t.w, t.h) == _size and set(t.exits.values()) == _outs and _near <= 2,
              f"{_a}: FireRed's {_size[0]} x {_size[1]}; in from {_came} you stand by that way out {getattr(t, 'player', None)}; ways out {sorted(set(getattr(t, 'exits', {}).values()))}")
    _open = {k for k in set(t.doors.values()) if t._door_options(k) or any(t._room_for(d) for d, kk in t.doors.items() if kk == k)}
    check(_kinds <= _open, f"...its doors open onto something: {sorted(_kinds)} (open: {sorted(_open)})")
    for _d, _k in sorted(t.doors.items()):
        if t._room_for(_d):
            enter(t, _d)
            _in = t.room
            _who = [o for o in t.people.values()]
            t.draw()
            t._go(None, "OUT:%d,%d" % _d)
            g.walk_town_room = None
            check(_in and _who and t.room is None, f"...through the {_k}'s door {_d} you stand in its room ({_in}, {len(_who)} to talk to) and come back out")
    t.draw()

t = town("TWO_ISLAND", "CAPE_BRINK")
check(t.doors.get((10, 8)) == "harbor" and len(t._door_options("harbor")) >= 7 and any(o.get("action") == "SHOP" for o in t.people.values()),
      f"Two Island: the harbour's door is the mat at the pier's end, with the ferry's stops behind it ({len(t._door_options('harbor'))}); the market stall's keeper sells")
t = town("THREE_ISLAND", "BOND_BRIDGE")
check(t.doors.get((12, 53)) == "harbor" and len(t._door_options("harbor")) >= 7 and t.rows[45][38] == "#",
      f"Three Island: Three Isle Port is the south of the same map, its harbour at the pier's end; the grass pocket's own mouth is shut from this side ({t.doors.get((12, 53))}, {len(t._door_options('harbor'))}, {t.rows[45][38]})")

# ---- the routes: (area, size of the floor you come in on per way in, ways out, FireRed's trainers)
ROUTES = [
    ("KINDLE_ROAD", {"ONE_ISLAND": (24, 140), "MT_EMBER": (24, 140)}, {"ONE_ISLAND", "MT_EMBER"}, 12),
    ("CAPE_BRINK", {"TWO_ISLAND": (24, 40)}, {"TWO_ISLAND"}, 0),
    ("BOND_BRIDGE", {"THREE_ISLAND": (96, 20), "BERRY_FOREST": (96, 20)}, {"THREE_ISLAND", "BERRY_FOREST"}, 6),
    ("THREE_ISLE_PORT", {"THREE_ISLAND": (30, 7)}, {"THREE_ISLAND"}, 0),
    ("MT_EMBER", {"KINDLE_ROAD": (57, 54)}, {"KINDLE_ROAD"}, 3),
    ("BERRY_FOREST", {"BOND_BRIDGE": (57, 47)}, {"BOND_BRIDGE"}, 0),
    ("ICEFALL_CAVE", {"FOUR_ISLAND": (30, 36)}, {"FOUR_ISLAND"}, 0),
    ("FIVE_ISLE_MEADOW", {"FIVE_ISLAND": (24, 40), "MEMORIAL_PILLAR": (24, 40), "ROCKET_WAREHOUSE": (24, 40)}, {"FIVE_ISLAND", "MEMORIAL_PILLAR", "ROCKET_WAREHOUSE"}, 3),
    ("ROCKET_WAREHOUSE", {"FIVE_ISLE_MEADOW": (29, 27)}, {"FIVE_ISLE_MEADOW"}, 5),   # (11-17: FireRed's second Admin added)
    ("MEMORIAL_PILLAR", {"FIVE_ISLE_MEADOW": (24, 60)}, {"FIVE_ISLE_MEADOW"}, 3),
    ("WATER_LABYRINTH", {"FIVE_ISLAND": (72, 20), "RESORT_GORGEOUS": (72, 20)}, {"FIVE_ISLAND", "RESORT_GORGEOUS"}, 1),
    ("RESORT_GORGEOUS", {"WATER_LABYRINTH": (72, 20), "LOST_CAVE": (72, 20)}, {"WATER_LABYRINTH", "LOST_CAVE"}, 7),
    ("WATER_PATH", {"SIX_ISLAND": (24, 100), "GREEN_PATH": (24, 100), "RUIN_VALLEY": (24, 100)}, {"SIX_ISLAND", "GREEN_PATH", "RUIN_VALLEY"}, 6),
    ("PATTERN_BUSH", {"GREEN_PATH": (60, 32)}, {"GREEN_PATH"}, 12),
    ("OUTCAST_ISLAND", {"GREEN_PATH": (24, 80), "SEVII_ALTERING_CAVE": (24, 80)}, {"GREEN_PATH", "SEVII_ALTERING_CAVE"}, 5),
    ("SEVII_ALTERING_CAVE", {"OUTCAST_ISLAND": (32, 24)}, {"OUTCAST_ISLAND"}, 0),
    ("RUIN_VALLEY", {"WATER_PATH": (48, 40), "DOTTED_HOLE": (48, 40)}, {"WATER_PATH", "DOTTED_HOLE"}, 5),
    ("DOTTED_HOLE", {"RUIN_VALLEY": (16, 11)}, {"RUIN_VALLEY"}, 0),
    ("CANYON_ENTRANCE", {"SEVEN_ISLAND": (24, 40), "SEVAULT_CANYON": (24, 40)}, {"SEVEN_ISLAND", "SEVAULT_CANYON"}, 5),
    ("SEVAULT_CANYON", {"CANYON_ENTRANCE": (24, 80), "TANOBY_RUINS": (24, 80)}, {"CANYON_ENTRANCE", "TANOBY_RUINS"}, 7),
    ("TANOBY_RUINS", {"SEVAULT_CANYON": (144, 20)}, {"SEVAULT_CANYON"}, 4),
    ("LOST_CAVE", {"RESORT_GORGEOUS": (11, 11)}, {"RESORT_GORGEOUS"}, 2),
    ("NAVEL_ROCK", {"ONE_ISLAND": (17, 13)}, {"ONE_ISLAND"}, 0),   # (11-23, K2: you land in FireRed's harbour room, 2.59, and walk out onto the rock)
    ("BIRTH_ISLAND", {"ONE_ISLAND": (17, 13)}, {"ONE_ISLAND"}, 0),   # (11-17: you land in FireRed's harbour room, 2.58, and walk out onto the island)
    ("FARAWAY_ISLAND", {"ONE_ISLAND": (34, 46)}, {"ONE_ISLAND"}, 0),
]
for _a, _ins, _outs, _n in ROUTES:
    _pool = [t for t in DATA[_a].get("trainer_pool", []) if not t.get("is_boss_battle")]
    for _came, _size in _ins.items():
        p = route(_a, _came)
        f = p.run.floor
        _all = set()
        for _i in range(p.run.n_floors):
            _all |= {v for v in p.run.made(_i).exits.values() if isinstance(v, str) and not v.startswith("WARP")}
        _got = reach(f, tuple(p.run.player))
        _far = {v for t, v in f.exits.items() if t in _got and isinstance(v, str) and not v.startswith("WARP")}
        _mine = min((abs(x - p.run.player[0]) + abs(y - p.run.player[1]) for (x, y), v in f.exits.items() if v == _came), default=99)
        _there = _far >= {v for v in f.exits.values() if isinstance(v, str) and not v.startswith("WARP")}
        check(isinstance(p, DungeonState) and (f.w, f.h) == _size and _all == _outs and _mine <= 2 and f.walkable(*p.run.player) and _there,
              f"{_a} from {_came}: FireRed's {_size[0]} x {_size[1]}; you stand by that way in {p.run.player}; every way out of this floor can be walked to {sorted(_far)}; ways out {sorted(_all)}")
    _spots = sum(len(fl.get("trainer_spots", [])) for fl in (MAPS[_a].get("floors") or [MAPS[_a]]))
    check(len(_pool) == _n == _spots, f"...FireRed's {_n} trainers, each with a spot of their own on the map (pool {len(_pool)}, spots {_spots})")

# Kindle Road: the Ember Spa's mouth gives Rock Smash; the cracked rocks stand in the way without it
story.inventory.pop("HM_ROCK_SMASH", None)
story.story_flags.pop("got_rock_smash_sevii", None)
p = route("KINDLE_ROAD", "ONE_ISLAND")
f = p.run.floor
_cr = sorted(t for t, v in f.decor.items() if str(v).startswith("crack:"))
_spa = [t for t, v in f.exits.items() if str(v).startswith("WARP:") and t == (15, 58)]
check(len(_cr) == 13 and len(_spa) == 1 and not f.walkable(*_cr[0]),
      f"Kindle Road: 13 cracked rocks in the way (FireRed's own), the Ember Spa's mouth at {_spa} leads inside")
_opt = next(o for o in DATA["KINDLE_ROAD"]["route_menu"] if o.get("door") == "spa")
check(_opt["event"]["gift_item"] == {"HM_ROCK_SMASH": 1}, "...the Ember Spa's old man hands over HM Rock Smash (as in FireRed)")
# buildings on routes (the engine's rooms-on-routes): in at the door you stand in the room, its person is there to talk to,
# no wild Pokemon indoors, out by the mat you stand below the door
for _a, _came, _door, _who in (("KINDLE_ROAD", "ONE_ISLAND", (15, 58), "EMBER SPA"), ("CAPE_BRINK", "TWO_ISLAND", (12, 16), "VISIT THE MOVE TUTOR"),
                               ("RESORT_GORGEOUS", "WATER_LABYRINTH", (39, 8), "SELPHY'S VILLA"), ("SEVAULT_CANYON", "CANYON_ENTRANCE", (7, 17), "OPEN THE CHAMBERS")):
    for _k in ("got_rock_smash_sevii", "visited_resort_gorgeous", "tanoby_chambers_open"):
        story.story_flags.pop(_k, None)
    story.story_flags["rescued_selphy"] = story.story_flags["selphy_home"] = True   # (11-17: Lady Selphy is in her villa once she's home from the Lost Cave, FireRed)
    p = route(_a, _came)
    f = p.run.floor
    _v = str(f.exits.get(_door, ""))
    _j, _x, _y = (int(v) for v in _v.split(":")[1:]) if _v.startswith("WARP:") else (0, 0, 0)
    _room = p.run.made(_j) if _j else f
    _back = str(_room.exits.get((_x, _y), ""))
    _fig = [m for m in _room.movers if m.kind == "figure" and (m.payload or {}).get("text") == _who]
    _wild = [m for m in _room.movers if m.kind == "wild"]
    _out = [m for m in f.movers if m.kind == "figure" and (m.payload or {}).get("text") == _who]
    _near = _fig and any(_room.walkable(_fig[0].x + dx, _fig[0].y + dy) and (_fig[0].x + dx, _fig[0].y + dy) in reach(_room, (_x, _y)) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    check(_j >= 1 and _back == "WARP:0:%d:%d" % (_door[0], _door[1] + 1) and f.walkable(_door[0], _door[1] + 1) and len(_fig) == 1 and _near and not _wild and not _out
          and _door in reach(f, tuple(p.run.player)),
          f"{_a}: through the door at {_door} you stand in its room (floor {_j}); {_who} is there to walk up to, no wild Pokemon indoors ({len(_wild)}); its mat leads back out below the door ({_back})")
    p.run.jump_floor(_j, (_x, _y)); p.draw(); p.run.jump_floor(0, (_door[0], _door[1] + 1))
# the harbours: inside, the sailor on the pier offers the boats the door used to
for _a, _d in (("ONE_ISLAND", (12, 18)), ("TWO_ISLAND", (10, 8)), ("THREE_ISLAND", (12, 53)), ("FOUR_ISLAND", (10, 28)), ("FIVE_ISLAND", (12, 14)), ("SIX_ISLAND", (11, 23)), ("SEVEN_ISLAND", (64, 53))):
    t = town(_a, "NOWHERE")
    enter(t, _d)
    _s = t.people.get((8, 6)) or {}
    _boats = [o for o in _s.get("any", []) if t._shown(o)]
    t.draw()
    _in = t.room
    t._go(None, "OUT:%d,%d" % _d)
    g.walk_town_room = None
    check(_in == "harbor" and len(_boats) >= 6 and all(o.get("action") == "TRAVEL" for o in _boats) and t.room is None,
          f"{_a}: in the harbour the sailor on the pier offers the boats ({len(_boats)} now)")

# Three Isle Path: through the tunnel to the grass pocket
p = route("THREE_ISLE_PORT", "THREE_ISLAND")
f0, f1 = p.run.made(0), p.run.made(1)
_w0 = [t for t, v in f0.exits.items() if str(v).startswith("WARP")]
_w1 = [t for t, v in f1.exits.items() if str(v).startswith("WARP")]
check(p.run.n_floors == 2 and len(_w0) == 1 and len(_w1) == 1 and _w0[0] in reach(f0, tuple(p.run.player)) and (f1.w, f1.h) == (18, 9),
      f"Three Isle Path: the dug tunnel leads from the pier yard's mouth to its far mouth {_w0}, out into the grass pocket {_w1}")

# every floor of the caves: each passage leads to an open tile on the floor FireRed joins it to, and every floor can be got to
CAVES = {"MT_EMBER": "KINDLE_ROAD", "ICEFALL_CAVE": "FOUR_ISLAND", "DOTTED_HOLE": "RUIN_VALLEY", "TANOBY_RUINS": "SEVAULT_CANYON",
         "LOST_CAVE": "RESORT_GORGEOUS", "NAVEL_ROCK": "ONE_ISLAND", "FARAWAY_ISLAND": "ONE_ISLAND"}
for _a in CAVES:
    p = route(_a, CAVES[_a])
    _seen, _todo, _bad = {0}, [0], []
    while _todo:
        _i = _todo.pop()
        _f = p.run.made(_i)
        for _t, _v in _f.exits.items():
            if str(_v).startswith("WARP:"):
                _j, _x, _y = (int(v) for v in _v.split(":")[1:4])   # (a fall "WARP:j:x:y:fall": the Dotted Hole's holes)
                _g = p.run.made(_j)
                if not (_g.walkable(_x, _y) or (_x, _y) in _g.exits): _bad.append((_i, _t, _v))
                if _j not in _seen: _seen.add(_j); _todo.append(_j)
    check(len(_seen) == p.run.n_floors and not _bad, f"{_a}: all {p.run.n_floors} floors joined by their passages, each landing on open ground ({sorted(_seen)}; bad {_bad[:3]})")
story.inventory.pop("HM_WATERFALL", None)                # (with the HM in the Bag the falls are no longer in the way)
p = route("ICEFALL_CAVE", "FOUR_ISLAND")
story.inventory["HM_WATERFALL"] = 1
_f1, _f2 = p.run.made(1), p.run.made(2)
_drops = [t for t, v in _f1.exits.items() if str(v) == "WARP:2:%d:%d" % t]
_ti = MAPS["ICEFALL_CAVE"]["floors"][1].get("thin_ice") or {}
_tit = [tuple(int(v) for v in k.split(",")) for k in _ti.get("tiles", [])]
check(len(_drops) == 3 and _ti.get("to") == 2 and len(_tit) == 9 and all(_f1.walkable(*t) and _f2.walkable(*t) for t in _tit)
      and len(_f2.ice) >= 50 and any(str(v).startswith("falls:") for v in p.run.made(0).decor.values()),
      f"Icefall Cave: 1F's 3 ladders take you to the same spot on B1F ({len(_drops)}); its 9 thin-ice tiles stand over open B1F floor ({len(_tit)}); B1F's sheet ice ({len(_f2.ice)} tiles); the entrance's waterfall")
p._warp(1, 9, 9, land=True); frames(p, 30)
_first = p._thin_ice((9, 9)); _was = p.run.index
_second = p._thin_ice((9, 9))
_land = None
for _ in range(400):   # (the box tapped on; where you stand read the moment you land, before a tap could walk you on)
    if p.dialogue_box.visible:
        p.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
    frames(p)
    if p.run.index == 2:
        _land = tuple(p.run.player); break
check(not _first and _was == 1 and _second and p.run.index == 2 and _land == (9, 9),
      f"...FireRed's thin ice: the first step cracks it, the second drops you to B1F on the same spot (floor {p.run.index}, landed on {_land})")
from src.dungeon import core as _core   # (11-18: a wild Pokemon standing on the landing spot made this land a tile off now and then)
_f2 = p.run.made(2)
_f2.movers = [m for m in _f2.movers if (m.x, m.y) != (9, 9)]
_wm = _core.Mover("wild", 9, 9, None)
_f2.movers.append(_wm)
p.run.warp(2, 9, 9, land=True)
check(tuple(p.run.player) == (9, 9) and (_wm.x, _wm.y) != (9, 9), f"...a wild Pokemon on the landing spot steps aside: you land on it ({p.run.player}, it's at {(_wm.x, _wm.y)})")

# Green Path is two halves joined only through Pattern Bush (as in FireRed): each of the Bush's mouths brings you out on its own side
for _i, _side in ((0, "west"), (5, "east")):
    p = route("GREEN_PATH", "PATTERN_BUSH", index=_i, count=6)
    _got = {v for t, v in p.run.floor.exits.items() if t in reach(p.run.floor, tuple(p.run.player))}
    check(_got == ({"PATTERN_BUSH", "OUTCAST_ISLAND"} if _side == "west" else {"PATTERN_BUSH", "WATER_PATH"}) and (p.run.player[0] < 55) == (_side == "west"),
          f"Green Path out of Pattern Bush's {_side} mouth: you stand on the {_side} half {p.run.player}, which leads to {sorted(_got)}")
p = route("GREEN_PATH", "WATER_PATH")
check(p.run.player[0] >= 60, f"Green Path from Water Path: on the east lane {p.run.player}")

# Faraway Island (Emerald's: its own walls, its look from the pictures): from the boat up the cliff steps, through the grove to the forest's way in, to Mew
p = route("FARAWAY_ISLAND", "ONE_ISLAND")
f0, f1 = p.run.made(0), p.run.made(1)
_got0 = reach(f0, tuple(p.run.player))
_got1 = reach(f1, (12, 19))
_mew = [t for k, t in f1.spots.items() if "MEW" in k.upper() or "PINK" in k.upper()]
check((22, 7) in _got0 and (23, 7) in _got0 and (3, 33) in _got0 and (f1.w, f1.h) == (29, 26) and len(_mew) >= 1
      and all(any((t[0] + dx, t[1] + dy) in _got1 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) for t in _mew),
      f"Faraway Island: from the pier {p.run.player} you can walk up to the forest's way in (22-23, 7) and round to the sign; inside, to Mew at {_mew}")
_land, _todo = {tuple(p.run.player)}, [tuple(p.run.player)]
while _todo:  # (the same walk without Surf: the ponds are in the way)
    _x, _y = _todo.pop()
    for _dx, _dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        _n = (_x + _dx, _y + _dy)
        if _n not in _land and f0.inside(*_n) and f0.walkable(*_n) and f0.tile(*_n) != core.SURF:
            _land.add(_n); _todo.append(_n)
check((9, 16) in _land and (22, 9) not in _land and not f0.walkable(18, 13) and f0.tile(18, 10) == core.SURF,
      "...as Emerald's own walls have it: on foot you reach the grove but not the forest's way in; the way crosses the ponds (Surf); the three trees across the lane stand")

# Tanoby Ruins: the Unown are in the chambers, not out on the sea; each of the seven ruins leads into its own chamber
p = route("TANOBY_RUINS", "SEVAULT_CANYON")
_out = [m for m in p.run.floor.movers if m.kind == "wild"]
_doors = sorted(int(str(v).split(":")[1]) for v in p.run.floor.exits.values() if str(v).startswith("WARP:"))
check(not _out and _doors == [1, 2, 3, 4, 5, 6, 7], f"Tanoby Ruins: no wild Pokemon outside ({len(_out)}); the seven ruins' doors lead to chambers {_doors}")
story.badges["KANTO"] = ["BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL", "MARSH", "VOLCANO", "EARTH"]   # (11-17: Kanto's HMs want FireRed's badges; the road north crosses water)
t = town("SEVEN_ISLAND", "CANYON_ENTRANCE")
check(t.doors.get((58, 7)) == "gym" and t._door_options("gym") and (58, 8) in reach_town(t, tuple(t.player)),
      f"Seven Island: the Trainer Tower's door on the same map, north up the road from town; you can walk to it from the south way in {t.player}")
# every option that needs a place to stand has one: no figure option left without a spot on its map
for _a in sorted(DATA):
    if _a not in MAPS or DATA[_a].get("area_type") == "town": continue
    _m = MAPS[_a]
    _fl = (_m.get("floors") or [_m]) + [f for sm in (_m.get("story_maps") or []) for f in (sm.get("map") or {}).get("floors") or []]   # (11-23: a map's other versions too: the Trainer Tower's climbs)
    _who = lambda x: [x] if isinstance(x, str) else [y.get("text") if isinstance(y, dict) else y for y in x] if isinstance(x, list) else [x.get("text")] if isinstance(x, dict) else []   # (a rebuilt map's people: names, lists, whole options; 11-14)
    _have = {y for f in _fl + list((_m.get("rooms") or {}).values()) for x in f.get("people", []) for y in _who(x)} | ({"BOSS"} if any(f.get("boss_spot") for f in _fl) else set())
    _kinds = set((_m.get("buildings") or {}).values()) | {k for f in _fl for k in (f.get("buildings") or {}).values()}
    _lost = [o["text"] for o in DATA[_a].get("route_menu", []) if o.get("action") in ("EVENT", "BOSS", "NPC") and not o.get("not_on_map")
             and o["text"] not in _have and o.get("door") not in _kinds and not (o.get("action") == "BOSS" and "BOSS" in _have)]
    check(not _lost, f"{_a}: every event and boss has someone to walk up to or a door to go through (missing: {_lost})")

# ---- the Sevii canon pass (11-17, k_batch29-32): each redrawn area on FireRed's own pictures (every floor, every room), and
# FireRed's people, item balls and story people on FireRed's tiles
REDRAWN = {"FOUR_ISLAND": ["3_15", "35_0", "35_1", "35_2", "35_3", "35_4", "35_5", "35_6", "35_7"], "ICEFALL_CAVE": ["1_110", "1_111", "1_112", "1_113"],
           "FIVE_ISLAND": ["3_16", "36_0", "36_1", "36_2", "36_3", "36_4"], "FIVE_ISLE_MEADOW": ["3_56"], "ROCKET_WAREHOUSE": ["1_114"],
           "MEMORIAL_PILLAR": ["3_57"], "WATER_LABYRINTH": ["3_55"], "RESORT_GORGEOUS": ["3_54", "39_0"],
           "LOST_CAVE": [f"2_{n}" for n in range(12, 27)],
           "SIX_ISLAND": ["3_18", "37_0", "37_1", "37_2", "37_3", "37_4"], "WATER_PATH": ["3_60", "41_0", "41_1"], "RUIN_VALLEY": ["3_61"],
           "DOTTED_HOLE": [f"1_{n}" for n in range(115, 121)], "GREEN_PATH": ["3_59"], "PATTERN_BUSH": ["1_121"], "OUTCAST_ISLAND": ["3_58"],
           "SEVII_ALTERING_CAVE": ["1_122"], "SEVEN_ISLAND": ["k_seven", "31_0", "31_1", "31_2", "31_3", "31_4", "31_6"],
           "CANYON_ENTRANCE": ["3_63"], "SEVAULT_CANYON": ["3_64", "2_35", "42_0"], "TANOBY_RUINS": ["3_65"] + [f"2_{n}" for n in range(27, 34)],
           "NAVEL_ROCK": ["2_0", "2_36", "2_37", "2_38", "2_55", "2_59"], "BIRTH_ISLAND": ["2_56", "2_58"]}
for _a, _pics in REDRAWN.items():
    _s = json.dumps(MAPS[_a])
    check(all(f"fr_ground/{_p}.png" in _s for _p in _pics), f"{_a}: drawn on FireRed's own pictures, every floor and room ({_pics})")


def _town_people(t, room=None):
    if room:
        t._go(room, ""); frames(t, 2)
    return {o.get("text"): p for p, o in t._people().items()}


def _route_figures(p, i):
    _f = p.run.made(i)
    return {(m.payload or {}).get("text"): (m.x, m.y) for m in _f.movers if m.kind == "figure" and isinstance(m.payload, dict)}


t = town("FOUR_ISLAND", "ICEFALL_CAVE")
_pp = _town_people(t)
check(_pp.get("STAR PIECE") == (5, 6) and _pp.get("STARDUST") == (32, 19) and _pp.get("Day-Care Man") == (16, 13) and t._room_for((25, 14)) == "bodyslam"
      and "hall" not in t.doors.values() and not any("Contest" in str(o.get("text")) for o in DATA["FOUR_ISLAND"]["explore_options"]),
      f"Four Island: FireRed's two item balls and the Day-Care Man on their tiles; no Contest Hall (Jordan, 11-17): (25, 14) is FireRed's Body Slam house ({_pp.get('STAR PIECE')}, {_pp.get('STARDUST')})")
check(t.town_map.get("hidden", {}) == {"22,34": "PEARL", "6,21": "ULTRA_BALL"}, f"...FireRed's two hidden items ({t.town_map.get('hidden')})")
_pp = _town_people(t, "lorelei")
check(_pp.get("Lorelei's House") == (7, 4) or _pp.get("Battle Lorelei") == (7, 4), f"...Lorelei at home where FireRed has her ({_pp})")
t._go(None, "OUT:33,23"); g.walk_town_room = None
_pp = _town_people(t, "house")
check(_pp.get("Sticker girl") == (4, 4) and "Body Slam Tutor" not in _pp, f"...the sticker house: FireRed's sticker girl alone ({_pp})")
t._go(None, "OUT:33,23"); g.walk_town_room = None
_pp = _town_people(t, "bodyslam")
check(_pp.get("Body Slam Tutor") == (8, 3) and _pp.get("Bouncing boy") == (9, 3), f"...FireRed's Body Slam house: the tutor and his friend ({_pp})")
t._go(None, "OUT:25,15"); g.walk_town_room = None
_tu = next(o for o in DATA["FOUR_ISLAND"]["explore_options"] if o["text"] == "Body Slam Tutor")
check(_tu["event"]["stages"][0]["tutor"]["move"] == "BODY-SLAM", "...Body Slam is taught once, then again for money (FireRed's tutor)")
p = route("ICEFALL_CAVE", "FOUR_ISLAND")
_f1, _f2, _f3 = _route_figures(p, 1), _route_figures(p, 2), _route_figures(p, 3)
check(_f1.get("TAKE THE HM") == (12, 16) and _f1.get("ULTRA BALL") == (11, 7) and _f2.get("FULL RESTORE") == (10, 14) and _f2.get("NEVERMELTICE") == (21, 7),
      f"Icefall Cave: HM07 Waterfall is FireRed's item ball on 1F (12,16); its three other balls on their floors ({_f1}, {_f2})")
check(_f3.get("STOP TEAM ROCKET") == (11, 14) and _f3.get("Lorelei") == (12, 16) and "Grunt" in _f3,
      f"...the back cavern: the Rockets on FireRed's Grunts' tiles, Lorelei facing them ({_f3})")
_tm0, _rp = story.tracked_mission, story.inventory.get("RAINBOW_PASS")
_lf = {k: story.story_flags.pop(k, None) for k in ("met_lorelei_sevii", "sevii_icefall_cleared", "got_sevii_gems")}
story.inventory["RAINBOW_PASS"] = 1; story.tracked_mission = "sevii_m5"
t = town("FOUR_ISLAND", "NOWHERE"); t._go("lorelei", ""); frames(t, 2)
_g1 = t._guide_spot()
story.story_flags["met_lorelei_sevii"] = story.story_flags["got_waterfall_sevii"] = True   # (11-17: HM07 is the step before the back cavern)
p = route("ICEFALL_CAVE", "FOUR_ISLAND")
p.run.enter_floor(3); frames(p, 2); p._guide_key = p._step_key = None
_g2 = p._guide_spot()
check(_g1 and _g1[0] == (7, 4) and _g2 and _g2[0] == (11, 14),
      f"Journal (The Ruby and the Sapphire): the marker is on Lorelei in her house, then on the Rockets in Icefall's back cavern ({_g1}, {_g2})")
for _k, _v in _lf.items():
    story.story_flags.pop(_k, None)
    if _v is not None: story.story_flags[_k] = _v
story.tracked_mission = _tm0
g.walk_town_room = None

t = town("FIVE_ISLAND", "FIVE_ISLE_MEADOW")
_pp = _town_people(t)
check(_pp.get("Fisherman") == (8, 5) and _pp.get("Little girl") == (16, 10) and set(t.doors.values()) >= {"center", "harbor", "house"},
      f"Five Island: FireRed's townspeople on their tiles; its Center, harbour and houses ({sorted(set(t.doors.values()))})")
_pp = _town_people(t, "house_e")
check(_pp.get("Meadow owner") == (2, 3), f"...the Meadow's owner at home ({_pp})")
t._go(None, "OUT:22,9"); g.walk_town_room = None
_ss = story.story_flags.pop("sapphire_stolen", None)
p = route("FIVE_ISLE_MEADOW", "FIVE_ISLAND")
_f = p.run.floor
_wh = [t for t, v in _f.exits.items() if v == "ROCKET_WAREHOUSE"]
_fig = _route_figures(p, 0)
check(_wh == [(12, 21)] and not _f.walkable(12, 21) and _fig.get("MAX POTION") == (12, 11) and _fig.get("PP UP") == (3, 22)
      and sum(r.count("2") for r in MAPS["FIVE_ISLE_MEADOW"]["art"]) == 2 and str(_f.decor.get((12, 21))).startswith("barrier:"),
      f"Five Isle Meadow: the Warehouse door shut till the Sapphire is stolen; FireRed's two item balls and two Cut trees ({_wh}, {_fig}, {_f.decor.get((12, 21))})")
story.story_flags["sapphire_stolen"] = story.story_flags["warehouse_door_open"] = True   # (11-17: the two passwords keyed in)
p = route("FIVE_ISLE_MEADOW", "FIVE_ISLAND")
check(p.run.floor.walkable(12, 21) or (12, 21) in p.run.floor.exits and not any(str(v).startswith("barrier:") for t, v in p.run.floor.decor.items() if t == (12, 21)),
      "...once it's stolen, the door lets you in")
story.story_flags.pop("sapphire_stolen", None); story.story_flags.pop("warehouse_door_open", None)
if _ss is not None: story.story_flags["sapphire_stolen"] = _ss
p = route("ROCKET_WAREHOUSE", "FIVE_ISLE_MEADOW")
_fig = _route_figures(p, 0)
_tr = {(m.x, m.y): DATA["ROCKET_WAREHOUSE"]["trainer_pool"][m.payload[0]]["name"] for m in p.run.floor.movers if m.kind == "trainer"}
_ad = next(o for o in DATA["ROCKET_WAREHOUSE"]["route_menu"] if o["text"] == "CONFRONT THE ADMIN")["event"]["battle"]
_wm = MAPS["ROCKET_WAREHOUSE"]
_wp = dict(zip([(x, y) for y, r in enumerate(_wm["art"]) for x, c in enumerate(r) if c == "N"], _wm["people"]))
check(_wp.get((25, 11)) == "CONFRONT THE ADMIN" and _tr.get((27, 16)) == "Admin" and _tr.get((27, 4)) == "Gideon"
      and _ad["team"] == [42, 110, 229] and _ad["levels"] == [53, 54, 55],
      f"Rocket Warehouse: FireRed's two Admins (the one by the way in, and the last on FireRed's tile with his team), Gideon by his machine ({_tr}, {_wp.get((25, 11))})")
check(_fig.get("TM208") == (17, 3) and _fig.get("PEARL") == (1, 16) and _fig.get("BIG PEARL") == (8, 25) and "UP-GRADE" not in _fig
      and len(_wm.get("stops", [])) >= 15,
      f"...FireRed's items (TM36 Sludge Bomb = TM141; no Up-Grade in Kanto) and its spin maze's stop tiles ({len(_wm.get('stops', []))})")
p = route("MEMORIAL_PILLAR", "FIVE_ISLE_MEADOW")
_fig = _route_figures(p, 0)
check(_fig.get("Memorial man") == (8, 44) and _fig.get("METAL COAT") == (4, 47), f"Memorial Pillar: the man by the grave, FireRed's Metal Coat ({_fig})")
_mm = next(o for o in DATA["MEMORIAL_PILLAR"]["route_menu"] if o["text"] == "Memorial man")["event"]["stages"][0]
check(_mm["take_item"] == {"LEMONADE": 1} and _mm["gift_item"] == {"TM025": 1}, "...a Lemonade left for Tectonix: TM39 Facade (FireRed's TM42)")
p = route("WATER_LABYRINTH", "FIVE_ISLAND")
_fig = _route_figures(p, 0)
_eg = next(o for o in DATA["WATER_LABYRINTH"]["route_menu"] if o["text"] == "THE OLD MAN'S EGG")["event"]["stages"][0]
check(_fig.get("THE OLD MAN'S EGG") == (14, 11) and _eg["gift_egg"] == 175 and _eg["requires"] == ["lead_friend:255"],
      f"Water Labyrinth: the old man on FireRed's tile; his Togepi Egg for a Trainer whose lead Pokemon loves them ({_fig})")
_lead = story.player_team[0]
_f0 = getattr(_lead, "friendship", 0)
_lead.friendship = 70
_lo = story.special_condition("lead_friend:255")
_lead.friendship = 255
check(not _lo and story.special_condition("lead_friend:255"), "...the fondness test (FireRed: maximum, 255): not at 70, yes at 255")
_lead.friendship = _f0
_sf = {k: story.story_flags.pop(k, None) for k in ("rescued_selphy", "selphy_home")}
p = route("RESORT_GORGEOUS", "WATER_LABYRINTH")
_fig0 = _route_figures(p, 0)
story.story_flags["rescued_selphy"] = True
p = route("RESORT_GORGEOUS", "WATER_LABYRINTH")
_fig1 = _route_figures(p, 0)
check("Lady Selphy" not in _fig0 and _fig1.get("Lady Selphy") == (39, 9) and len(p.run.floor.spots if hasattr(p.run.floor, "spots") else []) >= 0,
      f"Resort Gorgeous: Lady Selphy waits at her door once she's back from the Lost Cave ({_fig1.get('Lady Selphy')})")
_vo = next(o for o in DATA["RESORT_GORGEOUS"]["route_menu"] if o["text"] == "SELPHY'S VILLA")
check(_vo["event"]["show_request"]["rewards"] == ["NUGGET", "PEARL", "BIG_PEARL", "STARDUST", "STAR_PIECE", "RARE_CANDY"] and _vo["condition"] == "selphy_home",
      "...inside, she wishes to see one of your Pokemon and gives one of FireRed's rewards (Nugget, Pearl, Big Pearl, Stardust, Star Piece, Rare Candy)")
from src.states.overworld import common as _common
_dex = g.data.data.setdefault("pokedex", {})
_had = dict(_dex)
_dex["sevii_test_25"] = {"id": 25}
story.story_flags["selphy_wish"] = 25
_t0 = list(story.player_team)
story.player_team = [p for p in _t0 if p and int(p.id) != 25]
_ask = _common._show_request(g, _vo["event"]["show_request"])
story.player_team = _t0 + [mk(25)]
_bag = sum(story.inventory.get(k, 0) for k in _vo["event"]["show_request"]["rewards"])
_thx = _common._show_request(g, _vo["event"]["show_request"])
_bag2 = sum(story.inventory.get(k, 0) for k in _vo["event"]["show_request"]["rewards"])
story.player_team = _t0
_dex.clear(); _dex.update(_had)
check("Pikachu" in _ask[0] and "Pikachu" in _thx[0] and _bag2 == _bag + 1, f"...played: she asks for a Pikachu; shown one, a reward ({_ask[0]} / {_thx[-1]})")
for _k, _v in _sf.items():
    story.story_flags.pop(_k, None)
    if _v is not None: story.story_flags[_k] = _v
_rs = story.story_flags.pop("rescued_selphy", None)
p = route("LOST_CAVE", "RESORT_GORGEOUS")
if _rs is not None: story.story_flags["rescued_selphy"] = _rs
_lc = {i: _route_figures(p, i) for i in (10, 11, 12, 13, 14)}
_tr = MAPS["LOST_CAVE"].get("figure_floors", {})
_sel = next(o for o in DATA["LOST_CAVE"]["route_menu"] if o["text"] == "LADY SELPHY")["event"]["battle"]
check(_lc[10].get("LADY SELPHY") == (5, 5) and _sel["team"] == [53, 53] and _sel["levels"] == [49, 49] and _tr.get("Lawson") == 1 and _tr.get("Laura") == 4,
      f"Lost Cave: Lady Selphy in FireRed's room (her two Persian, Lv 49); FireRed's two trainers in their rooms ({_lc[10]})")
check(_lc[10].get("SILK SCARF") == (5, 2) and _lc[11].get("LAX INCENSE") == (5, 5) and _lc[12].get("SEA INCENSE") == (5, 5)
      and _lc[13].get("MAX REVIVE") == (5, 5) and _lc[14].get("SEARCH THE DARK") == (5, 5) and _lc[12].get("THE BLACK FOG") == (5, 4),
      f"...FireRed's five item balls in the item rooms (the Rare Candy too); the Black Fog (ours) in its side room ({_lc[12]})")

# ---- k_batch32: the canon pass on the nine areas redrawn in batches 27-28
t = town("ONE_ISLAND", "KINDLE_ROAD")
_bc = story.story_flags.pop("beat_champion", None)
_pp = _town_people(t, "center")
check(_pp.get("Bill") == (14, 6) and any(p == (15, 6) for n, p in _pp.items() if n and n.startswith("Celio")),
      f"One Island: Celio on FireRed's tile by his machine, Bill beside him ({_pp.get('Bill')})")
t._go(None, "OUT:14,12"); g.walk_town_room = None
if _bc is not None: story.story_flags["beat_champion"] = _bc
p = route("KINDLE_ROAD", "ONE_ISLAND")
check(_route_figures(p, 0).get("CARBOS") == (18, 114), "Kindle Road: the Carbos on FireRed's tile (18,114)")
_mf = {k: story.story_flags.pop(k, None) for k in ("met_ember_researchers", "ember_grunt_a", "ember_grunt_b", "sevii_ember_rocket", "met_celio", "beat_champion")}   # (11-17: one MAIN mission shows at a time: the post-League ones wait)
story.story_flags["met_ember_researchers"] = story.story_flags["met_celio"] = story.story_flags["got_tri_pass"] = True
p = route("MT_EMBER", "KINDLE_ROAD")
_fig = _route_figures(p, 0)
check(_fig.get("ROCKET GRUNT") == (41, 40) and _fig.get("CHASE OFF TEAM ROCKET") == (42, 40),
      f"Mt. Ember: FireRed's two diggers at the Ruby Path's door (41,40 and 42,40) ({_fig.get('ROCKET GRUNT')}, {_fig.get('CHASE OFF TEAM ROCKET')})")
_tm0, _rp2 = story.tracked_mission, story.inventory.pop("RAINBOW_PASS", None)   # (the post-League mission would show instead)
story.tracked_mission = "sevii_m2"
p._guide_key = p._step_key = None
_g = p._guide_spot()
story.tracked_mission = _tm0
if _rp2: story.inventory["RAINBOW_PASS"] = _rp2
check(_g and _g[0] == (41, 40), f"...Journal (Team Rocket on Mt. Ember): the marker on the first digger ({_g})")
for _k, _v in _mf.items():
    story.story_flags.pop(_k, None)
    if _v is not None: story.story_flags[_k] = _v
_lf = {k: story.story_flags.pop(k, None) for k in ("rescued_lostelle", "heard_lostelle", "two_island_biker_scene", "lostelle_thanked")}
t = town("TWO_ISLAND", "CAPE_BRINK")
t._go("gamecorner", ""); frames(t, 3)
_sc = [sc for sc in (t.room_map() if hasattr(t, "room_map") else {}).get("scenes", [])] if False else MAPS["TWO_ISLAND"]["rooms"]["gamecorner"].get("scenes", [])
_tap_through(t, 600)
for _i in range(120):
    frames(t)
    _tap_through(t, 50)
check(_sc and _sc[0]["cast"][0]["sheet"] == "fr_53.png" and story.story_flags.get("two_island_biker_scene") and not getattr(t, "npc_active", False),
      f"Two Island: the first time in the Game Corner, FireRed's biker walks in, sneers and leaves ({story.story_flags.get('two_island_biker_scene')})")
story.story_flags["rescued_lostelle"] = True
t = town("TWO_ISLAND", "CAPE_BRINK")
_pp = _town_people(t, "gamecorner")
_ty = next(o for o in DATA["TWO_ISLAND"]["explore_options"] if o["text"] == "Lostelle's Thanks")["event"]
check(_pp.get("Lostelle") == (6, 5) and _ty["gift_item"] == {"MOON_STONE": 1}, f"...once she's home, Lostelle beside her dad, who gives a Moon Stone (FireRed) ({_pp.get('Lostelle')})")
t._go(None, "OUT:39,9"); g.walk_town_room = None
for _k, _v in _lf.items():
    story.story_flags.pop(_k, None)
    if _v is not None: story.story_flags[_k] = _v
_bk = story.story_flags.pop("beat_three_island_bikers", None)
t = town("THREE_ISLAND", "BOND_BRIDGE")
_pp = _town_people(t)
_bg = next(o for o in DATA["THREE_ISLAND"]["explore_options"] if o["text"] == "Stop the Biker Gang")["event"]["stages"]
check(_pp.get("Islander") == (7, 24) and _pp.get("Islander ") == (8, 23) and _pp.get("Biker") == (15, 31)
      and [st["battle"]["team"] for st in _bg] == [[109, 88], [109], [88], [110, 89]] and _bg[-1]["battle"]["name"] == "Cue Ball Paxton",
      f"Three Island: FireRed's islanders stand up to the gang; its biker on the road south; three Goons, then Cue Ball Paxton ({[st['battle']['team'] for st in _bg]})")
_fr = next(o for o in t.people.values() if o.get("text") == "Islander")["event"]["stages"][0]
check(_fr["gift_item"] == {"FULL_RESTORE": 1} and _fr["requires"] == ["beat_three_island_bikers"], "...the islander's Full Restore once the bikers are gone (FireRed)")
_pp = _town_people(t, "center")
check(_pp.get("Sailor") == (11, 5), f"...the Center's sailor (FireRed's 11,5) ({_pp.get('Sailor')})")
t._go(None, "OUT:23,16") if False else None; g.walk_town_room = None
if _bk is not None: story.story_flags["beat_three_island_bikers"] = _bk
_lf = {k: story.story_flags.pop(k, None) for k in ("rescued_lostelle", "beat_champion")}
story.story_flags["heard_lostelle"] = True
p = route("BERRY_FOREST", "BOND_BRIDGE")
_hy = next(o for o in DATA["BERRY_FOREST"]["route_menu"] if o["text"] == "FIND LOSTELLE")["boss"]
check(_route_figures(p, 0).get("FIND LOSTELLE") == (4, 8) and _hy["level"] == 30, f"Berry Forest: Lostelle at FireRed's 4,8; the Hypno that scares her at Lv 30 (FireRed)")
_tm0, _rp3 = story.tracked_mission, story.inventory.pop("RAINBOW_PASS", None); story.tracked_mission = "sevii_m3"; story.story_flags["beat_three_island_bikers"] = story.story_flags["celio_has_ruby"] = True
p._guide_key = p._step_key = None
_g = p._guide_spot()
story.tracked_mission = _tm0
if _rp3: story.inventory["RAINBOW_PASS"] = _rp3
check(_g and _g[0] == (4, 8), f"...Journal (Lost Lostelle): the marker on Lostelle ({_g})")
for _k, _v in _lf.items():
    story.story_flags.pop(_k, None)
    if _v is not None: story.story_flags[_k] = _v
if _bk is None: story.story_flags.pop("beat_three_island_bikers", None)

# ---- 11-17, Jordan's answers and batches 33-36
_ef = {k: story.story_flags.pop(k, None) for k in ("ember_grunt_a", "ember_grunt_b", "sevii_ember_rocket", "met_ember_researchers")}
story.story_flags.update({"ember_grunt_a": True, "ember_grunt_b": True, "met_ember_researchers": True})
p = route("MT_EMBER", "KINDLE_ROAD")
_f0, _f12 = _route_figures(p, 0), _route_figures(p, 12)
check(_f0.get("JESSIE AND JAMES") == (40, 41) and "CHASE OFF TEAM ROCKET" not in _f0 and _f12.get("RUBY") == (7, 7)
      and (MAPS["MT_EMBER"]["floors"][0].get("scenes") or [{}])[0].get("flag") == "ember_password",
      f"Mt. Ember: Jessie & James once both diggers are beaten; the diggers' password overheard; the Ruby at the Ruby Path's bottom ({_f0.get('JESSIE AND JAMES')}, {_f12.get('RUBY')})")
for _k, _v in _ef.items():
    story.story_flags.pop(_k, None)
    if _v is not None: story.story_flags[_k] = _v
_ice = next(o for o in DATA["ICEFALL_CAVE"]["route_menu"] if o["text"] == "STOP TEAM ROCKET")["event"]["battle"]
check(_ice["name"] == "Jessie and James" and _ice["levels"] == [38, 38, 38], "Icefall Cave: Jessie & James in place of FireRed's Grunt (Lv 38)")
_door = MAPS["FIVE_ISLE_MEADOW"]["barred"][0]
check(_door["open_with"]["flag"] == "warehouse_door_open" and "sapphire_stolen" in _door["open_with"]["condition"],
      "Five Isle Meadow: the Warehouse door opens with FireRed's two passwords (Mt. Ember's diggers, Gideon's)")
_jm = {m["id"]: m for m in json.load(open("assets/sevii_area_data.json", encoding="utf-8"))["JOURNAL_MISSIONS"]}
check(all(_jm[i]["type"] == "MAIN" and _jm[i].get("steps") for i in ("sevii_m1", "sevii_m2", "sevii_m2b", "sevii_m2c", "sevii_m3", "sevii_m4a", "sevii_m4", "sevii_m5", "sevii_m5b")),
      "Sevii's story is MAIN in the Journal, every mission with its steps (Jordan 11-17)")
_cases = [("WATER_PATH", "SIX_ISLAND", {"ELIXIR": (17, 19), "DRAGON SCALE": (17, 87)}), ("RUIN_VALLEY", "WATER_PATH", {"HP UP": (5, 33), "FULL RESTORE": (19, 11), "SUN STONE": (43, 32)}),
          ("OUTCAST_ISLAND", "GREEN_PATH", {"PP UP": (11, 16)}), ("SEVAULT_CANYON", "CANYON_ENTRANCE", {"KING'S ROCK": (18, 45), "MAX ELIXIR": (7, 38), "NUGGET": (17, 23)})]
for _a, _came, _want in _cases:
    p = route(_a, _came)
    _fig = _route_figures(p, 0)
    check(all(_fig.get(k) == v for k, v in _want.items()), f"{_a}: FireRed's item balls on FireRed's tiles ({ {k: _fig.get(k) for k in _want} })")
t = town("SEVEN_ISLAND", "CANYON_ENTRANCE")
_pp = _town_people(t)
check(_pp.get("Psychic Dario") == (56, 26) and _pp.get("Psychic Rodette") == (56, 29) and _pp.get("Swords Dance Tutor") == (55, 58),
      f"Seven Island: FireRed's Psychics Dario and Rodette on the Tower's grounds; the Swords Dance tutor ({_pp.get('Swords Dance Tutor')})")
from src.states.overworld import walk_town as _wt
_tags = {k: _wt.important_person(o) for k, o in t._people().items() if isinstance(o, dict) and o.get("text") in ("Psychic Dario", "Psychic Rodette", "Swords Dance Tutor")}
check(sorted(_tags.values()) == [False, False, True], f"...no name tags over trainers: Dario and Rodette get none, the tutor keeps his (Jordan, 11-17) ({_tags})")
t = town("SIX_ISLAND", "WATER_PATH")
_pp = _town_people(t, "notes")
check(_pp.get("Ruin Maniac's Notes") == (7, 5), f"Six Island: the old man's house keeps the Unown Report ({_pp})")
g.walk_town_room = None
p = route("DOTTED_HOLE", "RUIN_VALLEY")
check(p.run.n_floors == 6 and all(len(p.run.made(i).signs if hasattr(p.run.made(i), "signs") else [1]) >= 0 for i in range(6))
      and [len((MAPS["DOTTED_HOLE"]["floors"][i].get("signs") or [])) for i in range(1, 5)] == [1, 1, 1, 1],
      "Dotted Hole: six rooms; the braille in each of the four middle rooms says which way on")
check(not any(o.get("text") == "READ THE BRAILLE" for o in DATA["DOTTED_HOLE"].get("route_menu", [])), "...no braille to read inside: it is read at the door (FireRed)")
# Ruin Valley: FireRed's door - read the braille outside; it opens with Cut (HM01 and the Cascade Badge), not before
story.story_flags.pop("dotted_hole_open", None); story.story_flags.pop("sapphire_stolen", None)
_hm, _bd = story.inventory.pop("HM_CUT", None), {k: list(v) for k, v in story.badges.items()}
story.badges["KANTO"] = [b for b in story.badges.get("KANTO", []) if "CASCADE" not in str(b).upper()]
p = route("RUIN_VALLEY", "WATER_PATH")
_shut = str(p.run.floor.decor.get((24, 24), "")).startswith("barrier:")
p.run.player, p.anim = (24, 25), 0
p.step(0, -1); frames(p, 60)
_still = not story.story_flags.get("dotted_hole_open")
for _ in range(200):
    if p.dialogue_box.visible: p.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
    frames(p)
story.inventory["HM_CUT"] = 1
story.badges.setdefault("KANTO", []).append("CASCADE")
p.run.player, p.anim = (24, 25), 0
p.step(0, -1); frames(p, 60)
check(_shut and _still and story.story_flags.get("dotted_hole_open") and not str(p.run.floor.decor.get((24, 24), "")).startswith("barrier:"),
      f"Ruin Valley: the braille door stays shut without Cut; with HM01 and the Cascade Badge it opens (FireRed) ({_shut}, {_still}, {story.story_flags.get('dotted_hole_open')})")
story.badges.clear(); story.badges.update(_bd)

# ---- the Trainer Tower, FireRed's (11-23, Kanto K2): Seven Island's door, the desk, a climb's floors, its battles, the roof
from src.world import trainer_tower as _tt
from src.ui import challenge_clock as _ck
def _ttap(st, n=400):
    for _ in range(n):
        cs = g.current_state
        if getattr(cs, "dialogue_box", None) is not None and getattr(cs.dialogue_box, "visible", False):
            cs.dialogue_box.advance()
        frames(cs)
        if getattr(cs, "_ready", None) and cs._ready() and not getattr(cs.dialogue_box, "visible", False):
            return
for _k in [k for k in story.story_flags if k.startswith("tt_")] + ["challenge_clock"]:
    story.story_flags.pop(_k, None)
_opt = next(o for o in DATA["SEVEN_ISLAND"]["explore_options"] if o.get("text") == "Trainer Tower")
check(_opt.get("action") == "TRAVEL" and _opt.get("target_area") == "TRAINER_TOWER" and not DATA["SEVEN_ISLAND"].get("gym"),
      "Trainer Tower: Seven Island's door goes into the tower (no menu, no Rolf/Koji/Vera/Tower Master)")
p = route("TRAINER_TOWER", "SEVEN_ISLAND")
check(p.run.index == 0 and (p.run.floor.w, p.run.floor.h) == (19, 17) and p.run.n_floors == 11, f"...in at FireRed's lobby, 19 x 17; lobby, 1F-8F, roof and the lift ({p.run.player}, {p.run.n_floors})")
_lob = {(m.payload or {}).get("text"): (m.x, m.y) for m in p.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict)}
check(_lob.get("NURSE") == (4, 9) and _lob.get("CLERK") == (14, 9) and _lob.get("RECEPTIONIST") == (11, 7), f"...the nurse, the clerk and the receptionist on FireRed's spots ({_lob})")
p.run.floor.movers = [m for m in p.run.floor.movers if m.kind == "figure"]
p.run.player, p.anim = (9, 3), 0
p.step(0, -1); _ttap(p)
check(p.run.index == 0, f"...the stairs up wait till you sign up ({p.run.index})")
_said = []
_tt.event(p, {"tt": "desk"}, [], lambda l: _said.extend(l))
for _ in range(300):
    if type(g.current_state).__name__ == "PickListState":
        break
    st = g.current_state
    if getattr(st, "dialogue_box", None) is not None and st.dialogue_box.visible:
        st.dialogue_box.advance()
    frames(st)
_pk = g.current_state if type(g.current_state).__name__ == "PickListState" else None
_rows = [c[0] for c in _pk.choices] if _pk else []
story.player_team = [mk(4), mk(9)]
story.player_team[0].level, story.player_team[1].level = 60, 55
if _pk:
    _pk.pick("SINGLE")
for _ in range(900):
    if type(g.current_state).__name__ in ("PlayState", "DungeonState") and getattr(g.current_state, "run", None) is not None and g.current_state._ready():
        break
    _st = g.current_state
    if getattr(_st, "dialogue_box", None) is not None and getattr(_st.dialogue_box, "visible", False):
        _st.dialogue_box.advance()
    frames(_st)
p = g.current_state
check(_rows[:4] == ["Single Battle", "Double Battle", "Knockout", "Mixed"] and story.story_flags.get("tt_on") and _ck.running(story)
      and p.run.index == 0 and tuple(p.run.player) == (9, 7),
      f"...the receptionist: four climbs; signed up, the clock runs and you stand before the counter ({_rows}, {getattr(p.run, 'player', None)})")
p.run.floor.movers = [m for m in p.run.floor.movers if m.kind == "figure"]
p.run.player, p.anim = (9, 3), 0
p.step(0, -1); _ttap(p)
_one = {(m.payload or {}).get("text"): (m.x, m.y) for m in p.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict)}
check(p.run.index == 1 and _one.get("Alberto") == (15, 13), f"...up to 1F: the Single climb's first trainer, Alberto, on FireRed's spot ({p.run.index}, {_one})")
# (FireRed's trigger tile: step onto (10,13) and Alberto walks up and battles you - Jordan 11-23)
p.run.player, p.anim = (10, 14), 0
p.step(0, -1)
for _ in range(400):
    if type(g.current_state).__name__ == "TrainerIntroState":
        break
    _st = g.current_state
    if getattr(_st, "dialogue_box", None) is not None and getattr(_st.dialogue_box, "visible", False):
        _st.dialogue_box.advance()
    frames(_st)
_trig = g.current_state
check(type(_trig).__name__ == "TrainerIntroState" and getattr(getattr(_trig, "next_state", None), "trainer_name", None) == "Alberto",
      f"...step onto FireRed's trigger tile (10,13): Alberto walks up and the battle starts ({type(_trig).__name__})")
g.change_state(p); frames(p, 2)
# Knockout: a win and the next comes straight at you, in FireRed's order (bottom, top, right)
_was = {k: story.story_flags.get(k) for k in ("tt_climb_SINGLE_on", "tt_climb_KNOCKOUT")}
story.story_flags.pop("tt_climb_SINGLE_on", None); story.story_flags["tt_climb_KNOCKOUT"] = True
_kf = _tt.floor_data(story, 1)
_nx = _tt.after_battle(g, {"floor": 1, "kind": "KNOCKOUT", "k": 0}, True)
if callable(_nx):
    _nx()
_ko = g.current_state
check(callable(_nx) and type(_ko).__name__ == "TrainerIntroState" and getattr(_ko.next_state, "trainer_name", None) == _kf["trainers"][1]["name"]
      and len([q for q in _ko.next_state.opponent_team if q]) == 1,
      f"...Knockout: beat the first and the second comes straight at you, one Pokemon each ({getattr(getattr(_ko, 'next_state', None), 'trainer_name', None)})")
for _k, _v in _was.items():
    story.story_flags.pop(_k, None)
    if _v: story.story_flags[_k] = _v
story.story_flags.pop("tt_ko_1_0", None)
g.change_state(p); frames(p, 2)
_b = _tt._battle(g, 1, _tt.floor_data(story, 1), 0)
_bb = getattr(_b, "battle_state", None) or getattr(_b, "next_state", None) or getattr(_b, "battle", None)
_team = [(q.id, q.level, getattr(q, "held_item", None)) for q in getattr(_bb, "opponent_team", [])]
check([t[:2] for t in _team] == [(160, 60), (115, 60)],
      f"...his two (FireRed's pick for 1F: Feraligatr, Kangaskhan) at your highest level, Lv 60 ({_team})")
_after = _tt.after_battle(g, {"floor": 1, "kind": "SINGLE", "k": 0}, True)
p.run.floor.movers = [m for m in p.run.floor.movers if m.kind == "figure"]
p.run.player, p.anim = (15, 7), 0
p.step(0, -1); _ttap(p)
check(story.story_flags.get("tt_floor_1") and p.run.index == 2, f"...beaten, 1F's stairs up open: 2F ({p.run.index}, {_after})")
_lose = _tt.after_battle(g, {"floor": 2, "kind": "SINGLE", "k": 0}, False)
if callable(_lose):
    _lose()
for _ in range(900):
    if type(g.current_state).__name__ in ("PlayState", "DungeonState") and getattr(g.current_state, "run", None) is not None and g.current_state is not p and g.current_state._ready():
        break
    _st = g.current_state
    if getattr(_st, "dialogue_box", None) is not None and getattr(_st.dialogue_box, "visible", False):
        _st.dialogue_box.advance()
    frames(_st)
p = g.current_state
check(not story.story_flags.get("tt_on") and not story.story_flags.get("tt_floor_1") and not _ck.running(story) and p.run.index == 0,
      f"...lose a battle: the climb is over, back in the lobby ({p.run.index}, {p.run.player})")
# the Double climb: its own floors (FireRed's Double layouts) and pairs
story.story_flags["tt_on"] = True; story.story_flags["tt_climb_DOUBLE"] = True
for _nm in _tt.on_climb("DOUBLE"):
    story.story_flags["tt_here_" + _nm.strip().replace(" ", "_")] = True
p = route("TRAINER_TOWER", "SEVEN_ISLAND")
while len(p.run.floors) <= 1:
    p.run.enter_floor(len(p.run.floors))
p.run.enter_floor(1); frames(p, 2)
_two = {(m.payload or {}).get("text"): (m.x, m.y) for m in p.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict)}
_d = _tt._battle(g, 1, _tt.floor_data(story, 1), 0)
check(_two.get("Jen") == (10, 12) and _two.get("Kira") == (10, 13) and "2_151" in json.dumps(MAPS["TRAINER_TOWER"]["story_maps"][0]["map"])
      and (getattr(getattr(_d, "next_state", None), "battle_options", None) or {}).get("double"),
      f"...the Double climb: FireRed's Double floors; Jen & Kira side by side, a double battle ({_two})")
# the roof: the owner, the time, the prize once, the record
for _n in range(1, 9):
    story.story_flags[f"tt_floor_{_n}"] = True
story.story_flags.pop("tt_climb_DOUBLE", None); story.story_flags["tt_climb_SINGLE_on"] = True
_ck.start(story, "TRAINER TOWER")
story.story_flags.pop("tt_prize_SINGLE", None); story.inventory.pop("UPGRADE", None)
_ndx = story.story_flags.pop("unlocked_national_dex", None)
_nd_regions = None
p = route("TRAINER_TOWER", "SEVEN_ISLAND")
while len(p.run.floors) <= 9:
    p.run.enter_floor(len(p.run.floors))
p.run.enter_floor(9); frames(p, 2)
_said = []
from src.states.systems import has_national_dex as _hnd
_tt.event(p, {"tt": "owner"}, [], lambda l: _said.extend(l))
check(_hnd(story) or (not story.inventory.get("UPGRADE") and not story.story_flags.get("tt_prize_SINGLE") and any("National Pokedex" in x for x in _said)),
      f"...without the National Pokedex the owner keeps the Up-Grade for later (Jordan 11-23: none in Kanto before it) ({_said[2:4]})")
story.story_flags["unlocked_national_dex"] = True
story.story_flags["tt_on"] = True; story.story_flags["tt_climb_SINGLE_on"] = True; story.story_flags["tt_floor_8"] = True; _ck.start(story, "TRAINER TOWER")
_said = []
_tt.event(p, {"tt": "owner"}, [], lambda l: _said.extend(l))
check(story.inventory.get("UPGRADE") == 1 and story.story_flags.get("tt_best_SINGLE") is not None and not _ck.running(story) and any("record" in x for x in _said),
      f"...the roof: the owner stops the clock, gives the Single climb's prize (FireRed: the Up-Grade) and keeps the record ({_said[:3]})")
_said = []
story.story_flags["tt_on"] = True; story.story_flags["tt_climb_SINGLE_on"] = True; story.story_flags["tt_floor_8"] = True; _ck.start(story, "TRAINER TOWER")
_tt.event(p, {"tt": "owner"}, [], lambda l: _said.extend(l))
check(story.inventory.get("UPGRADE") == 1, f"...the prize once only ({story.inventory.get('UPGRADE')})")
if _ndx is None: story.story_flags.pop("unlocked_national_dex", None)
for _k in [k for k in story.story_flags if k.startswith("tt_")] + ["challenge_clock"]:
    story.story_flags.pop(_k, None)

story.inventory.clear(); story.inventory.update(_inv)
story.story_flags.clear(); story.story_flags.update(_flags)
g.walk_towns = False
print(f"##### {fails} failures")
