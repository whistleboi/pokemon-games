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
    ("FOUR_ISLAND", (48, 40), {"ICEFALL_CAVE"}, {"center", "mart", "harbor", "daycare", "lorelei", "hall"}),
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
    ("ROCKET_WAREHOUSE", {"FIVE_ISLE_MEADOW": (29, 27)}, {"FIVE_ISLE_MEADOW"}, 4),
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
    ("NAVEL_ROCK", {"ONE_ISLAND": (20, 23)}, {"ONE_ISLAND"}, 0),
    ("BIRTH_ISLAND", {"ONE_ISLAND": (30, 30)}, {"ONE_ISLAND"}, 0),
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
                _j, _x, _y = (int(v) for v in _v.split(":")[1:])
                _g = p.run.made(_j)
                if not (_g.walkable(_x, _y) or (_x, _y) in _g.exits): _bad.append((_i, _t, _v))
                if _j not in _seen: _seen.add(_j); _todo.append(_j)
    check(len(_seen) == p.run.n_floors and not _bad, f"{_a}: all {p.run.n_floors} floors joined by their passages, each landing on open ground ({sorted(_seen)}; bad {_bad[:3]})")
story.inventory.pop("HM_WATERFALL", None)                # (with the HM in the Bag the falls are no longer in the way)
p = route("ICEFALL_CAVE", "FOUR_ISLAND")
story.inventory["HM_WATERFALL"] = 1
_f1, _f2 = p.run.made(1), p.run.made(2)
_drops = [t for t, v in _f1.exits.items() if str(v) == "WARP:2:%d:%d" % t]
check(len(_drops) == 12 and len(_f2.ice) >= 50 and any(str(v).startswith("falls:") for v in p.run.made(0).decor.values()),
      f"Icefall Cave: 1F's thin ice and ladders ({len(_drops)} tiles: 9 of ice, 3 ladders) take you to the same spot on B1F; B1F's sheet ice ({len(_f2.ice)} tiles); the entrance's waterfall")

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
t = town("SEVEN_ISLAND", "CANYON_ENTRANCE")
check(t.doors.get((58, 7)) == "gym" and t._door_options("gym") and (58, 8) in reach_town(t, tuple(t.player)),
      f"Seven Island: the Trainer Tower's door on the same map, north up the road from town; you can walk to it from the south way in {t.player}")
# every option that needs a place to stand has one: no figure option left without a spot on its map
for _a in sorted(DATA):
    if _a not in MAPS or DATA[_a].get("area_type") == "town": continue
    _m = MAPS[_a]
    _fl = _m.get("floors") or [_m]
    _have = {x for f in _fl for x in f.get("people", [])} | ({"BOSS"} if any(f.get("boss_spot") for f in _fl) else set())
    _kinds = set((_m.get("buildings") or {}).values()) | {k for f in _fl for k in (f.get("buildings") or {}).values()}
    _lost = [o["text"] for o in DATA[_a].get("route_menu", []) if o.get("action") in ("EVENT", "BOSS", "NPC")
             and o["text"] not in _have and o.get("door") not in _kinds and not (o.get("action") == "BOSS" and "BOSS" in _have)]
    check(not _lost, f"{_a}: every event and boss has someone to walk up to or a door to go through (missing: {_lost})")

story.inventory.clear(); story.inventory.update(_inv)
story.story_flags.clear(); story.story_flags.update(_flags)
g.walk_towns = False
print(f"##### {fails} failures")
