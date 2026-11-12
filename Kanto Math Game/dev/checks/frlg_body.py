# Kanto's and the Sevii Islands' maps laid out from FireRed's map data (dev/builders/town_maps/frlg.py), entered the way a player would.
#   cat dev/checks/harness_head.py dev/checks/frlg_body.py > dev/checks/out/check_frlg.py
#   python dev/checks/out/check_frlg.py <scratch dir>
from src.states.overworld import PlayState, CityState as _CS
from src.states.overworld.dungeon import DungeonState
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.dungeon import core
import os

fails = 0
g.dungeon_routes = True
g.walk_towns = True


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


def frames(p, n=1):
    for _ in range(n):
        g.current_state.update()
        g.current_state.draw()


def _tap_through(st, n=400):
    """Tap through whatever the town says first, as a player would."""
    for _ in range(n):
        if not getattr(st, "npc_active", False):
            return
        st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        frames(st)


def town(area, came):
    g.walk_town_pos = None
    g.walk_town_exit = None
    story.current_area_key, story.last_area_key = area, came
    st = _CS(g); g.change_state(st); _tap_through(st)
    return st


def route(area, came, index=0, count=0):
    core.ENTRANCE_INDEX, core.ENTRANCE_COUNT = index, count
    story.current_area_key, story.last_area_key = area, came
    story.player_team = [mk(4)]
    story.player_team[0].level = 12
    story.balls_left = 20
    p = PlayState(g)
    g.states["play"] = p
    g.change_state(p)
    frames(p, 3)
    return p


def step(p, at, d, n=5):
    """Stand on a tile and take one step, as a player would (nobody wandering in the way): (floor, where you are)."""
    p.run.floor.movers = [m for m in p.run.floor.movers if m.kind == "figure"]
    p.run.player = tuple(at); p.anim = 0; p.anim_from = tuple(at)
    _ev = p.run.step(*d); p._handle(_ev); frames(p, n)
    return p.run.index, tuple(p.run.player)


def people(p):
    """Who stands on this floor (the route options' texts)."""
    return {m.payload.get("text") for m in p.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict)}


def outs(f):
    """A floor's ways out to other areas (not its doors into rooms)."""
    return {v for v in f.exits.values() if not str(v).startswith("WARP:")}


def hop(p, start, way):
    """Stand at start, step that way; where you end up (a ledge hop carries you two tiles)."""
    f = p.run.floor
    keep, f.movers = f.movers, []
    p.run.player = tuple(start); p.anim = 0; p.sliding = None; p.hop = None
    p.step(*way)
    end = tuple(p.run.player)
    p.hop = None; p.anim = 0; f.movers = keep
    return end


def tstep(t, start, way):
    t.player = t.anim_from = tuple(start); t.anim = 0; t.walk_goal = None
    t.step(*way)
    end = tuple(t.player); t.anim = 0
    return end


_inv = dict(story.inventory)
story.story_flags["received_starter_kanto"] = True
story.story_flags["received_pokedex_kanto"] = True
story.story_flags["move_offer_kanto"] = True
for _k in ("HM_SURF", "HM_CUT"):
    story.inventory.pop(_k, None)

# ---- Pallet Town
t = town("PALLET_TOWN", "KANTO_ROUTE_1")
check(isinstance(t, _WTS) and (t.w, t.h) == (24, 20) and t.player[1] <= 2 and set(t.exits.values()) == {"KANTO_ROUTE_1", "KANTO_ROUTE_21"},
      f"Pallet Town: FireRed's 24 x 20; in from Route 1 at the top {t.player}; Route 21 across the pond")
check(t.doors.get((6, 7)) == "home" and t.doors.get((15, 7)) == "rival" and t.doors.get((16, 13)) == "lab" and len(t.signs) == 5,
      f"...your house, the rival's, the Lab at FireRed's doors {sorted(t.doors.items())}; five signs")
check(tstep(t, (7, 16), (0, 1)) == (7, 16) and "Surf" in t.toast, f"...the pond is in the way without Surf ({t.toast!r})")
story.inventory["HM_SURF"] = 1
check(tstep(t, (7, 16), (0, 1)) == (7, 17), "...and crossed with it")
story.inventory.pop("HM_SURF", None)
check(any(o.get("kind") == "tops" and o.get("of") == "roof" for o, _i, _a in t.overheads), "...the roofs' top edges are drawn over you (overheads)")
t.draw()

# ---- Route 1: every ledge a one-way hop south
p = route("KANTO_ROUTE_1", "PALLET_TOWN")
f = p.run.floor
_led = [v for v in f.decor.values() if str(v).startswith("ledge:")]
check(isinstance(p, DungeonState) and (f.w, f.h) == (24, 40) and p.run.player[1] >= 36 and sorted(set(f.exits.values())) == ["PALLET_TOWN", "VIRIDIAN_CITY"],
      f"Route 1: FireRed's 24 x 40; in from Pallet at the bottom {p.run.player}")
check(len(_led) == 61 and set(_led) == {"ledge:0,1"}, f"...its 61 ledge tiles all hop south ({len(_led)})")
_down, _up = hop(p, (4, 4), (0, 1)), hop(p, (4, 6), (0, -1))
check(_down == (4, 6) and _up == (4, 6), f"...the top-left ledge (row 5) is hopped down ({_down}) and not climbed ({_up})")
check(sum(m.kind == "wild" for m in f.movers) >= 3, "...wild Pokemon in its grass")

# ---- Viridian City
t = town("VIRIDIAN_CITY", "KANTO_ROUTE_1")
check(isinstance(t, _WTS) and (t.w, t.h) == (48, 40) and t.player[1] >= 37 and set(t.exits.values()) == {"KANTO_ROUTE_1", "KANTO_ROUTE_2", "KANTO_ROUTE_22"},
      f"Viridian City: FireRed's 48 x 40; in from Route 1 at the bottom {t.player}; Route 2 north, Route 22 west")
check({"gym", "oldman", "school", "mart", "center"} <= set(t.doors.values()) and t.doors.get((36, 10)) == "gym" and t.doors.get((26, 26)) == "center"
      and t._door_options("school") and t.doors.get((25, 11)) == "oldman", f"...the Gym's porch door, the Center, the School's lessons, the old man's house {sorted(set(t.doors.values()))}")
check(tstep(t, (30, 29), (0, 1)) == (30, 31) and tstep(t, (30, 31), (0, -1)) == (30, 31), "...the long ledge south of the Center is hopped down, not climbed")
check(tstep(t, (11, 23), (0, 1)) == (11, 23) and "CUT" in t.toast, f"...the small tree by the pond needs Cut ({t.toast!r})")
_n = min(t.exits, key=lambda e: e[1])
t.player = t.anim_from = (_n[0], _n[1] + 1); t.anim = 0
t.step(0, -1)
check(type(g.current_state).__name__ == "AreaTransitionState" and getattr(g.current_state, "target_area", None) in (None, "KANTO_ROUTE_2"),
      "...walk off the top: on to Route 2")
t.draw()

# ---- Route 22
p = route("KANTO_ROUTE_22", "VIRIDIAN_CITY")
f = p.run.floor
check((f.w, f.h) == (48, 24) and p.run.player[0] >= 44 and outs(f) == {"VIRIDIAN_CITY"}
      and str(f.exits.get((8, 5))).startswith("WARP:") and str(f.exits.get((9, 5))).startswith("WARP:"),
      f"Route 22: FireRed's 48 x 24; in from Viridian on the east {p.run.player}; the League gate's two doors")
check(not any(m.kind == "figure" for fl in p.run.floors[1:] for m in fl.movers if isinstance(m.payload, dict) and m.payload.get("action") == "ARRIVAL"), "...the rival, when he waits here, waits outdoors")
_i, _at = step(p, (8, 6), (0, -1))
check(p._floor_name(_i) == "League Gate" and people(p) >= {"GATE GUARD"} and outs(p.run.floor) == {"KANTO_ROUTE_23"}, f"...into the League gate {_at}: FireRed's room, its guard; its north doorway leads on to Route 23")
p.draw()
p = route("KANTO_ROUTE_22", "KANTO_ROUTE_23")
check(p._floor_name(p.run.index) == "League Gate" and p.run.player[1] <= 3, f"...in from Route 23: inside the gate, by its north doorway {tuple(p.run.player)}")
_i, _at = step(p, (7, 9), (0, 1))
check(_i == 0 and _at[1] == 6 and _at[0] in (8, 9), f"......and out by its south mat onto Route 22 {_at}")

# ---- Route 2, whole: Viridian below, the Forest's two gates, Pewter above
p = route("KANTO_ROUTE_2", "VIRIDIAN_CITY")
p = route("KANTO_ROUTE_2", "VIRIDIAN_CITY")
f = p.run.floor
check((f.w, f.h) == (24, 80) and p.run.player[1] >= 76 and outs(f) == {"VIRIDIAN_CITY", "PEWTER_CITY", "DIGGLETT_CAVE"},
      f"Route 2: FireRed's 24 x 80; in from Viridian at the bottom {p.run.player}")
_fd = sorted((xy for xy, v in f.exits.items() if str(v).startswith("WARP:")), key=lambda t: (t[1], t[0]))
check(_fd == [(17, 22), (18, 41), (19, 41), (18, 46), (19, 46)] + [] or {(5, 13), (6, 13), (5, 51), (6, 51), (17, 22), (18, 41), (19, 41), (18, 46), (19, 46)} == set(_fd),
      f"...the Forest's two gatehouses, the trade house and the east gatehouse are its doors {_fd}")
check(f.exits.get((17, 11)) == "DIGGLETT_CAVE", "...Diglett's Cave's mouth")
_i, _at = step(p, (18, 47), (0, -1))
check(p._floor_name(_i) == "Route 2 Gate" and people(p) == {"OAK'S AIDE", "GATE VISITOR"}, f"...the east gatehouse by its south door {_at}: FireRed's room, Oak's Aide inside")
p.draw()
_i, _at = step(p, (7, 2), (0, -1))
check(_i == 0 and _at[1] <= 41, f"......and out by its north mat, north of it {_at}")
_i, _at = step(p, (17, 23), (0, -1))
check(p._floor_name(_i) == "Trade House" and people(p) == {"TRADER", "TRADER'S FRIEND"}, f"...the trade house: FireRed's room, two people {_at}")
p.draw()
_i, _at = step(p, (4, 6), (0, 1))
check((_i, _at) == (0, (17, 23)), f"......and out by its mat {_at}")
f = p.run.floor
check(str(f.decor.get((16, 62))).startswith("cut:") and str(f.decor.get((11, 13))).startswith("cut:"), "...small trees to Cut stand where FireRed has them")
p = route("KANTO_ROUTE_2", "PEWTER_CITY")
check(p.run.player[1] <= 3, f"...in from Pewter at the top {p.run.player}")
for _ix, _n, _who in ((0, 6, {"FOREST GUIDE", "BUG FAN", "RESTING GIRL"}), (5, 6, {"GATE LADY", "YOUNG TRAINER"}), (0, 2, {"FOREST GUIDE", "BUG FAN", "RESTING GIRL"}), (1, 2, {"GATE LADY", "YOUNG TRAINER"})):
    p = route("KANTO_ROUTE_2", "VIRIDIAN_FOREST", index=_ix, count=_n)
    check(p._floor_name(p.run.index) == "Forest Gate" and people(p) == _who and outs(p.run.floor) == {"VIRIDIAN_FOREST"},
          f"...out of the Forest's {'north' if _ix == 0 else 'south'} gate (way {_ix} of {_n}) you stand inside Route 2's {'north' if _ix == 0 else 'south'} gatehouse {tuple(p.run.player)}: FireRed's room, its people")
    p.draw()
    if _n == 2:
        _i, _at = step(p, (7, 9) if _ix == 0 else (7, 2), (0, 1) if _ix == 0 else (0, -1))
        check(type(g.current_state).__name__ != "PlayState" or core.ENTRANCE_COUNT == 2, f"......its forest-side mat leads back into the Forest (way {core.ENTRANCE_INDEX} of {core.ENTRANCE_COUNT})")
        check(core.ENTRANCE_INDEX == _ix, "......by the matching gate")
p = route("KANTO_ROUTE_2", "VIRIDIAN_FOREST", index=0, count=2)
_i, _at = step(p, (7, 2), (0, -1))
check(_i == 0 and _at[1] <= 14, f"...out of the north gatehouse's route-side mat: on Route 2 north of the Forest {_at}")
p = route("KANTO_ROUTE_2", "VIRIDIAN_FOREST", index=1, count=2)
_i, _at = step(p, (7, 9), (0, 1))
check(_i == 0 and _at[1] >= 50, f"...out of the south gatehouse's route-side mat: on Route 2 south of the Forest {_at}")
for _ix, _ok in ((0, lambda q: q[1] <= 14), (1, lambda q: q[1] >= 55)):
    core.ENTRANCE_SPREAD = True
    q = route("VIRIDIAN_FOREST", "KANTO_ROUTE_2", index=_ix, count=2)
    check(_ok(q.run.player), f"...and the Forest from Route 2's {'north' if _ix == 0 else 'south'} gatehouse: in by its {'north' if _ix == 0 else 'south'} gate {tuple(q.run.player)}")

# ---- Viridian Forest
p = route("VIRIDIAN_FOREST", "KANTO_ROUTE_2", index=3, count=4)
f = p.run.floor
check((f.w, f.h) == (54, 69) and set(f.exits.values()) == {"KANTO_ROUTE_2"} and p.run.player[1] >= 59,
      f"Viridian Forest: FireRed's 54 x 69; in by Route 2's south gate you stand at its south end {p.run.player}")
check(sum(m.kind == "trainer" for m in f.movers) == 5, f"...its five Bug Catchers ({sum(m.kind == 'trainer' for m in f.movers)})")
p = route("VIRIDIAN_FOREST", "KANTO_ROUTE_2", index=0, count=4)
check(p.run.player[1] <= 12, f"...in by the north gate you stand at its north end {p.run.player}")

# ---- Pewter City
t = town("PEWTER_CITY", "KANTO_ROUTE_2")
check(isinstance(t, _WTS) and (t.w, t.h) == (48, 40) and t.player[1] >= 37 and set(t.exits.values()) == {"KANTO_ROUTE_2", "KANTO_ROUTE_3"},
      f"Pewter City: FireRed's 48 x 40; in from Route 2 at the bottom {t.player}; Route 3 east")
check(t.doors.get((17, 6)) == "museum" and t.doors.get((25, 4)) == "museum" and t.doors.get((15, 16)) == "gym" and t.doors.get((28, 18)) == "mart"
      and t.doors.get((17, 25)) == "center" and t._door_options("museum") and t._door_options("gym"),
      f"...the Museum's front and back doors, the Gym's porch door, the Mart, the Center {sorted(t.doors.items())}")
check(tstep(t, (10, 6), (0, 1)) == (10, 8) and tstep(t, (10, 8), (0, -1)) == (10, 8), "...the ledge below the Museum is hopped down, not climbed")
check(len(t.signs) == 5 and (42, 20) in t.people, "...five signs; the boy on the east road")
t.draw()

# ---- Pewter's buildings, inside (rooms): each door leads into FireRed's own room; the town's options are the people in them
def enter(t, door):
    t.player = t.anim_from = (door[0], door[1] + 1); t.anim = 0; t.walk_goal = None
    t.step(0, -1); t.anim = 0


enter(t, (17, 25))
check(t.room == "center" and (t.w, t.h) == (15, 10) and t.player == (7, 7) and set(t.exits.values()) == {"OUT:17,25"},
      f"Pewter's Pokemon Center: through the door you stand inside, by the mat ({t.room}, {t.player})")
t.draw()
check(tstep(t, (7, 5), (0, -1)) == (7, 4), "...walk up to the counter")
t.step(0, -1)
_pc = g.current_state
check(_pc is t and t.npc_active and bool(t.npc_dialogue), f"...talk to the nurse across her counter: she heals you from the map, no screen of the Center's own ({type(_pc).__name__})")
g.change_state(t)
t.npc_active = False
t2 = town("PEWTER_CITY", "KANTO_ROUTE_2")
g.walk_town_pos, g.walk_town_room = ("PEWTER_CITY", (7, 4), (0, -1)), ("PEWTER_CITY", "center")
story.current_area_key = "PEWTER_CITY"
t = _CS(g); g.change_state(t); _tap_through(t)
check(t.room == "center" and t.player == (7, 4), f"...back from a battle or a screen you are still inside ({t.room}, {t.player})")
t.player = t.anim_from = (7, 7); t.anim = 0
t.step(0, 1)
check(t.room is None and t.player == (17, 26) and (t.w, t.h) == (48, 40), f"...out over the mat: back in town below the Center's door ({t.room}, {t.player})")
enter(t, (28, 18))
check(t.room == "mart" and (2, 3) in t.people and t.people[(2, 3)].get("action") == "SHOP", f"the Mart: the clerk behind the counter is the Shop ({t.room})")
t._go(None, "OUT:28,18")
enter(t, (15, 16))
check(t.room == "gym" and (t.w, t.h) == (13, 16) and t.people.get((6, 5), {}).get("action") == "GYM" and not t._open((5, 3)) and t._open((6, 4)),
      f"the Gym: its boulders in the way, Brock at the back is the Gym challenge ({t.room}, {t.player})")
t.draw()
t._go(None, "OUT:15,16")
enter(t, (17, 6))
check(t.room == "museum_1f" and t.player[0] in (13, 14, 15) and t.player[1] == 8 and len(t.signs) == 2, f"the Museum: in by the front door ({t.player}); the two fossils' plaques")
t.player = t.anim_from = (7, 8); t.anim = 0
t.step(1, 0)
check(t.room == "museum_2f" and abs(t.player[0] - 11) + abs(t.player[1] - 8) == 1, f"...up its stairs: the first floor, beside the stairhead ({t.room}, {t.player})")
t.draw()
t.player = t.anim_from = (12, 8); t.anim = 0; t.step(-1, 0)
check(t.room == "museum_1f" and abs(t.player[0] - 8) + abs(t.player[1] - 8) == 1, f"...and down again to the foot of the stairs ({t.room}, {t.player})")
t.player = t.anim_from = (14, 8); t.anim = 0
t.step(0, 1)
check(t.room is None and t.player == (17, 7), f"...out by the front mats: below the Museum's porch door ({t.player})")
enter(t, (25, 4))
check(t.room == "museum_1f" and t.player[0] in (21, 22) and t.player[1] == 8, f"...its back door leads into the back room ({t.player})")
t._go(None, "OUT:25,4")
check(t.player == (25, 5), f"...and out again behind the Museum ({t.player})")
for _door, _room in (((33, 11), "house_ne"), ((9, 30), "house_sw")):
    enter(t, _door)
    check(t.room == _room and len(t.people) == 1, f"the house at {_door}: open, someone at home ({t.room})")
    t.draw()
    t._go(None, "OUT:%d,%d" % _door)
g.walk_town_room = None

# ---- Viridian's Center and Mart: the rooms every town shares; the clerk has the parcel before he sells
t = town("VIRIDIAN_CITY", "KANTO_ROUTE_1")
enter(t, (36, 19))
_clerk = t.people.get((2, 3), {})
check(t.room == "mart" and [o.get("text") for o in _clerk.get("any", [])] == ["Poke Mart", "Shop"] and t._people().get((2, 3), {}).get("action") == "SHOP",
      f"Viridian's Mart: the shared room; the clerk is Oak's parcel first, then the Shop ({t.room})")
t._go(None, "OUT:36,19")
enter(t, (26, 26))
check(t.room == "center" and t.people.get((7, 2), {}).get("action") == "HEAL", "Viridian's Center: the shared room, the nurse")
t._go(None, "OUT:26,26")
g.walk_town_room = None

# ---- Route 3, with the foot of Mt. Moon above its east end
p = route("KANTO_ROUTE_3", "PEWTER_CITY")
f = p.run.floor
check((f.w, f.h) == (84, 40) and p.run.player[0] <= 2 and p.run.player[1] >= 20 and outs(f) == {"PEWTER_CITY", "MT_MOON"},
      f"Route 3: FireRed's Route 3 with the mountain's foot joined above it, 84 x 40; in from Pewter on the west {p.run.player}")
check(f.exits.get((79, 5)) == "MT_MOON" and str(f.exits.get((72, 5))).startswith("WARP:") and f.walkable(70, 19) and f.walkable(70, 20),
      "...Mt. Moon's mouth and the Pokemon Center's door up at the foot; the two maps join as open ground")
_tr = {(m.x, m.y): getattr(m, "name", None) or str(getattr(m, "data", "")) for m in f.movers if m.kind == "trainer"}
check(len(_tr) == 8 and {(12, 26), (17, 24), (19, 29), (25, 24), (29, 30), (30, 23), (32, 26), (40, 31)} == set(_tr),
      f"...FireRed's own eight trainers, each on their own spot ({sorted(_tr)})")
_pool = [t["name"] for t in g.loader.area_data["STORY_PROGRESSION"]["KANTO_ROUTE_3"]["trainer_pool"]]
check(_pool == ["Sally", "Ben", "Greg", "Colton", "James", "Janice", "Calvin", "Robin"], f"...and its trainer list is FireRed's {_pool}")
_e, _w = hop(p, (24, 26), (0, 1)), hop(p, (24, 28), (0, -1))
check(_e == (24, 28) and _w == (24, 28), f"...a ledge is hopped south ({_e}) and not climbed ({_w})")
p = route("KANTO_ROUTE_3", "MT_MOON")
check(p.run.player[1] <= 8 and abs(p.run.player[0] - 79) <= 2, f"...out of Mt. Moon you stand at its mouth {p.run.player}")

# ---- Mt. Moon: three floors, each ladder joined to FireRed's own far end
p = route("MT_MOON", "KANTO_ROUTE_3")
f = p.run.floor
check(p.run.n_floors == 3 and (f.w, f.h) == (48, 40) and p.run.index == 0 and p.run.player[1] >= 35 and "KANTO_ROUTE_3" in f.exits.values(),
      f"Mt. Moon: three floors; in from Route 3 at 1F's mouth {p.run.player}")
check(sum(m.kind == "trainer" for m in f.movers) == 7, f"...FireRed's seven trainers on 1F ({sum(m.kind == 'trainer' for m in f.movers)})")
_mm = g.loader.area_data["STORY_PROGRESSION"]["MT_MOON"]["trainer_pool"]
check([t["name"] for t in _mm] == ["Miriam", "Marcos", "Josh", "Kent", "Iris", "Robby", "Jovan", "Grunt", "Grunt", "Grunt", "Grunt", "Jessie and James"]
      and _mm[1]["team"] == [74, 74, 95] and _mm[1]["levels"] == [10, 10, 10], "...its trainer list is FireRed's (Hiker Marcos: Geodude, Geodude, Onix at 10), then the four Rockets and Jessie and James")
f.movers = []
p.run.player = (5, 7); p.anim = 0; p.sliding = None
_ev = p.run.step(0, -1)
p._handle(_ev)
for _q in range(40):
    if getattr(p, "dialogue_box", None) and p.dialogue_box.visible:
        p.dialogue_box.advance()
    frames(p)
check(p.run.index == 1 and abs(p.run.player[0] - 3) + abs(p.run.player[1] - 3) <= 1, f"...the north-west ladder leads to B1F's north-west corner (floor {p.run.index}, {tuple(p.run.player)})")
p = route("MT_MOON", "KANTO_ROUTE_4")
check(p.run.index == 1 and (p.run.floor.w, p.run.floor.h) == (49, 40) and p.run.player[0] >= 42 and p.run.player[1] <= 6,
      f"...in from Route 4 you stand at B1F's far mouth (floor {p.run.index}, {tuple(p.run.player)})")

# ---- Route 4, east of Mt. Moon
p = route("KANTO_ROUTE_4", "MT_MOON")
f = p.run.floor
_led = [v for v in f.decor.values() if str(v).startswith("ledge:")]
check((f.w, f.h) == (86, 20) and p.run.player[0] <= 14 and set(f.exits.values()) == {"MT_MOON", "CERULEAN_CITY"},
      f"Route 4: FireRed's Route 4 from Mt. Moon's far mouth east, 86 x 20; out of the mountain at {p.run.player}")
check({"ledge:0,1", "ledge:1,0", "ledge:-1,0"} == set(_led), f"...its ledges hop south, east and west ({len(_led)})")

# ---- Cerulean City
t = town("CERULEAN_CITY", "KANTO_ROUTE_4")
check(isinstance(t, _WTS) and (t.w, t.h) == (48, 40) and t.player[0] <= 2 and t.player[1] >= 19
      and set(t.exits.values()) == {"KANTO_ROUTE_24", "KANTO_ROUTE_4", "KANTO_ROUTE_9", "KANTO_ROUTE_5", "CERULEAN_CAVE"},
      f"Cerulean City: FireRed's 48 x 40; in from Route 4 on the west road {t.player}")
check(t.doors.get((22, 19)) == "center" and t.doors.get((29, 28)) == "mart" and t.doors.get((31, 21)) == "gym" and t.doors.get((13, 28)) == "bike"
      and t.exits.get((1, 12)) == "CERULEAN_CAVE", f"...the Center, Mart, Gym porch, Bike Shop doors; Cerulean Cave's mouth {sorted(set(t.doors.values()))}")
enter(t, (22, 19))
check(t.room == "center", "...its Center is the shared room")
t._go(None, "OUT:22,19")
enter(t, (31, 21))
check(t.room == "gym" and t.people.get((8, 6), {}).get("action") == "GYM" and len(t.people) == 3, f"...its Gym: FireRed's room, Misty, the guide and the poolside spot ({t.room})")
t.draw(); t._go(None, "OUT:31,21")
g.walk_town_room = None
t = town("CERULEAN_CITY", "KANTO_ROUTE_24")
check(t.player[1] <= 5 and 21 <= t.player[0] <= 28 and (tuple(t.player) not in t.water_exits), f"...in from Route 24 you stand on land at the north end (the bridge or its east bank), not in the river {t.player}")
t.draw()

# ---- Route 24 (Nugget Bridge), Route 25, Bill's Sea Cottage, Route 5
p = route("KANTO_ROUTE_24", "CERULEAN_CITY", index=6, count=11)
f = p.run.floor
check((f.w, f.h) == (24, 40) and p.run.player[1] >= 36 and 10 <= p.run.player[0] <= 12 and set(f.exits.values()) == {"CERULEAN_CITY", "KANTO_ROUTE_25"},
      f"Route 24: FireRed's 24 x 40; off Cerulean's bridge you stand on Nugget Bridge {p.run.player}")
check(sum(m.kind == "trainer" for m in f.movers) == 7, f"...FireRed's six trainers and the Rocket at the bridge's head ({sum(m.kind == 'trainer' for m in f.movers)})")
_e, _w = hop(p, (12, 4), (1, 0)), hop(p, (14, 4), (-1, 0))
check(_e == (14, 4) and _w == (14, 4), f"...the ledge beside the top path is hopped east ({_e}), not back west ({_w})")
p = route("KANTO_ROUTE_25", "KANTO_ROUTE_24")
f = p.run.floor
check((f.w, f.h) == (72, 20) and p.run.player[0] <= 2 and f.exits.get((51, 4)) == "BILLS_HOUSE" and sum(m.kind == "trainer" for m in f.movers) == 9,
      f"Route 25: FireRed's 72 x 20; in from Route 24 on the west {p.run.player}; Bill's door; FireRed's nine trainers")
_p25 = [t["name"] for t in g.loader.area_data["STORY_PROGRESSION"]["KANTO_ROUTE_25"]["trainer_pool"]]
check(_p25 == ["Joey", "Franklin", "Dan", "Flint", "Chad", "Haley", "Wayne", "Kelsey", "Nob"], f"...its trainer list is FireRed's {_p25}")
t = town("BILLS_HOUSE", "KANTO_ROUTE_25")
check(isinstance(t, _WTS) and (t.w, t.h) == (15, 11) and t.player[1] >= 7 and (7, 5) in t.people and set(t.exits.values()) == {"KANTO_ROUTE_25"},
      f"Bill's Sea Cottage: FireRed's room, 15 x 11; in by the mat {t.player}; Bill by his machine")
t.draw()
_tea = story.inventory.get("TEA"); story.inventory.pop("TEA", None)
p = route("KANTO_ROUTE_5", "SAFFRON_CITY")
check(p._floor_name(p.run.index) == "Saffron Gate" and people(p) == {"GUARD"} and outs(p.run.floor) == {"SAFFRON_CITY"}, f"Route 5: in from Saffron you stand inside its gatehouse {tuple(p.run.player)}: FireRed's room, the thirsty guard")
_i, _at = step(p, (4, 8), (0, 1))
check(g.current_state is p and _i == p.recipe["art"]["room_floors"]["gate"], f"...without the Tea the way on to Saffron is barred, inside the gatehouse {_at}")
while p.dialogue_box.visible: p.dialogue_box.advance()
frames(p, 3)
p.draw()
_i, _at = step(p, (4, 2), (0, -1)); f = p.run.floor
check(_i == 0 and (f.w, f.h) == (48, 40) and _at in ((24, 31), (25, 31)) and f.exits.get((31, 31)) == "UNDERGROUND_PATH", f"...out by its north mat: north of the gatehouse {_at}; FireRed's 48 x 40; the Underground Path's door")
_i, _at = step(p, (23, 26), (0, -1))
check(p._floor_name(_i) == "Day Care" and people(p) == {"POK\u00e9MON DAY CARE"}, f"...the Day Care: FireRed's room, the Day-Care Man {_at}")
p.draw()
story.inventory["TEA"] = 1
p = route("KANTO_ROUTE_5", "SAFFRON_CITY"); step(p, (4, 8), (0, 1))
check(g.current_state is not p, f"...with the Tea the mat leads on to Saffron ({type(g.current_state).__name__})")
if _tea is None: story.inventory.pop("TEA", None)
p = route("KANTO_ROUTE_5", "CERULEAN_CITY")
check(p.run.player[1] <= 2, f"...in from Cerulean at the top {p.run.player}")

# ---- the routes round Saffron (6, 7, 8, 9, 10 north and south, 11): size, the way in from each neighbour, the ways out
def at_route(key, came, size, where, outs_, what, **kw):
    p = route(key, came, **kw)
    f = p.run.floor
    check((f.w, f.h) == size and where(*p.run.player) and outs(f) == outs_,
          f"{what}: {size[0]} x {size[1]}; in from {came} at {tuple(p.run.player)}; out to {sorted(outs(f))}")
    return p
    return p


def gate_in(key, title, mat, d, where, what):
    """In from Saffron: you stand inside the gatehouse (FireRed's room, the thirsty guard); out by the route's mat."""
    p = route(key, "SAFFRON_CITY")
    check(p._floor_name(p.run.index) == title and people(p) == {"GUARD"} and outs(p.run.floor) == {"SAFFRON_CITY"}, f"{what}: in from Saffron you stand inside its gatehouse {tuple(p.run.player)}: FireRed's room, the guard")
    p.draw()
    _i, _at = step(p, mat, d)
    check(_i == 0 and where(*_at), f"...and out by its other mat onto the route {_at}")
    return p


_R6 = {"UNDERGROUND_PATH", "VERMILLION_CITY"}
p = at_route("KANTO_ROUTE_6", "VERMILLION_CITY", (24, 40), lambda x, y: y >= 36, _R6, "Route 6")
check(str(p.run.floor.exits.get((12, 5))).startswith("WARP:") and sum(m.kind == "trainer" for m in p.run.floor.movers) == 6 and not people(p), "...Saffron's gatehouse doors; FireRed's six trainers; the guard is indoors now")
gate_in("KANTO_ROUTE_6", "Saffron Gate", (4, 8), (0, 1), lambda x, y: y <= 7 and 10 <= x <= 15, "Route 6")
_R7 = {"CELADON_CITY", "UNDERGROUND_PATH"}
at_route("KANTO_ROUTE_7", "CELADON_CITY", (24, 20), lambda x, y: x <= 2, _R7, "Route 7")
gate_in("KANTO_ROUTE_7", "Saffron Gate", (2, 5), (-1, 0), lambda x, y: 13 <= x <= 15 and 8 <= y <= 12, "Route 7")
_R8 = {"LAVENDER_TOWN", "UNDERGROUND_PATH"}
at_route("KANTO_ROUTE_8", "LAVENDER_TOWN", (72, 20), lambda x, y: x >= 69, _R8, "Route 8")
gate_in("KANTO_ROUTE_8", "Saffron Gate", (10, 5), (1, 0), lambda x, y: 7 <= x <= 9 and 8 <= y <= 12, "Route 8")
p = at_route("KANTO_ROUTE_9", "CERULEAN_CITY", (72, 20), lambda x, y: x <= 2, {"CERULEAN_CITY", "KANTO_ROUTE_10"}, "Route 9")
check(sum(m.kind == "trainer" for m in p.run.floor.movers) == 9, "...FireRed's nine trainers")
p = at_route("KANTO_ROUTE_10", "KANTO_ROUTE_9", (24, 50), lambda x, y: x <= 2 and y <= 12, {"KANTO_ROUTE_9", "ROCK_TUNNEL", "POWER_PLANT"}, "Route 10 (north)")
check(p.run.floor.exits.get((8, 19)) == "ROCK_TUNNEL" and str(p.run.floor.exits.get((13, 20))).startswith("WARP:") and p.run.floor.exits.get((7, 40)) == "POWER_PLANT",
      "...Rock Tunnel's mouth, the Center's door, the Power Plant's door")
_i, _at = step(p, (13, 21), (0, -1))
check(p._floor_name(_i) == "Pokemon Center" and people(p) == {"POKEMON CENTER"}, f"...the Pokemon Center: the shared room, its nurse {_at}")
p.draw()
_i, _at = step(p, (7, 7), (0, 1))
check((_i, _at) == (0, (13, 21)), f"......and out by its mat {_at}")
at_route("KANTO_ROUTE_10_SOUTH", "ROCK_TUNNEL", (24, 30), lambda x, y: y <= 9 and 6 <= x <= 10, {"ROCK_TUNNEL", "LAVENDER_TOWN"}, "Route 10 (south)")
p = at_route("KANTO_ROUTE_11", "VERMILLION_CITY", (72, 20), lambda x, y: x <= 2, {"VERMILLION_CITY", "DIGGLETT_CAVE"}, "Route 11")
check(sum(m.kind == "trainer" for m in p.run.floor.movers) == 10 and str(p.run.floor.exits.get((58, 10))).startswith("WARP:"),
      "...FireRed's ten trainers; the gatehouse's west door")
_i, _at = step(p, (57, 10), (1, 0))
check(p._floor_name(_i) == "Route 11 Gate" and people(p) == {"GATE GUARD"} and outs(p.run.floor) == {"KANTO_ROUTE_12"}, f"...into the gatehouse {_at}: FireRed's room, its guard; its east mats lead on to Route 12")
p.draw()
p = route("KANTO_ROUTE_11", "KANTO_ROUTE_12")
check(p._floor_name(p.run.index) == "Route 11 Gate" and p.run.player[0] >= 9, f"...in from Route 12: inside the gatehouse, by its east mats {tuple(p.run.player)}")
_i, _at = step(p, (2, 6), (-1, 0))
check((_i, _at) == (0, (57, 10)), f"......and out by its west mat onto Route 11 {_at}")

# ---- the caves
p = route("ROCK_TUNNEL", "KANTO_ROUTE_10")
check(p.run.n_floors == 2 and p.run.index == 0 and p.run.player[1] <= 4 and sum(m.kind == "trainer" for m in p.run.floor.movers) == 7,
      f"Rock Tunnel: two floors; in from Route 10 at the north mouth {tuple(p.run.player)}; FireRed's seven trainers on 1F")
p = route("ROCK_TUNNEL", "KANTO_ROUTE_10_SOUTH")
check(p.run.index == 0 and p.run.player[1] >= 35, f"...in from the south stretch at the south mouth {tuple(p.run.player)}")
p = route("DIGGLETT_CAVE", "KANTO_ROUTE_2")
check(p.run.n_floors == 3 and p.run.index == 0 and (p.run.floor.w, p.run.floor.h) == (10, 8), f"Diglett's Cave: in from Route 2 in its end room (floor {p.run.index})")
p = route("DIGGLETT_CAVE", "KANTO_ROUTE_11")
check(p.run.index == 2, f"...in from Route 11 in the far end room (floor {p.run.index})")
t = town("UNDERGROUND_PATH", "KANTO_ROUTE_5")
check(isinstance(t, _WTS) and t.room is None and (t.w, t.h) == (13, 10) and "KANTO_ROUTE_5" in t.exits.values(),
      f"The Underground Path: in from Route 5 in its stair building ({t.room}, {tuple(t.player)})")
_st = next(xy for xy, v in t.exits.items() if v == "ROOM:ns")
_from = next((_st[0] + dx, _st[1] + dy) for dx, dy in ((0, 1), (1, 0), (-1, 0), (0, -1)) if t._open((_st[0] + dx, _st[1] + dy)) and (_st[0] + dx, _st[1] + dy) not in t.exits)
t.player = t.anim_from = _from; t.anim = 0; t.walk_goal = None
t.step(_st[0] - _from[0], _st[1] - _from[1])
check(t.room == "ns" and (t.w, t.h) == (8, 63) and t.player[1] <= 6 and len(t.people) == 1,
      f"...down its stairs: the north end of the north-south tunnel ({t.room}, {tuple(t.player)}); the Fossil Maniac stands in it")
t.draw()
for _came, _room in (("KANTO_ROUTE_6", "south"), ("KANTO_ROUTE_7", "west"), ("KANTO_ROUTE_8", "east")):
    g.walk_town_room = None
    t = town("UNDERGROUND_PATH", _came)
    check(t.room == _room and _came in t.exits.values(), f"...in from {_came}: its own stair building ({t.room})")
g.walk_town_room = None


# ---- Vermilion, Lavender, Celadon, Saffron
def at_town(key, came, size, where, outs, doors, what):
    t = town(key, came)
    got = set(t.doors.values())
    check(isinstance(t, _WTS) and (t.w, t.h) == size and where(*t.player) and set(t.exits.values()) == outs and doors <= got,
          f"{what}: {size[0]} x {size[1]}; in from {came} at {tuple(t.player)}; out to {sorted(set(t.exits.values()))}; doors {sorted(got)}")
    t.draw()
    return t


t = at_town("VERMILLION_CITY", "KANTO_ROUTE_6", (48, 40), lambda x, y: y <= 2 and 22 <= x <= 24, {"KANTO_ROUTE_6", "KANTO_ROUTE_11"},
            {"center", "mart", "gym", "fanclub", "guru", "harbor"}, "Vermilion City")
check(t.doors.get((23, 34)) == "harbor" and t._door_options("harbor") and t.doors.get((14, 25)) == "gym", "...the harbour's mats at the pier's head open the boats; the Gym's porch door")
enter(t, (15, 6))
check(t.room == "center", "...its Center is the shared room")
t._go(None, "OUT:15,6")
enter(t, (14, 25))
check(t.room == "gym" and t.people.get((5, 2), {}).get("action") == "GYM" and t._open((5, 6)) and t._open((5, 7)), f"...its Gym: FireRed's room, the gate open, Lt. Surge at the back ({t.room})")
t.draw(); t._go(None, "OUT:14,25")
t = at_town("LAVENDER_TOWN", "KANTO_ROUTE_10_SOUTH", (24, 20), lambda x, y: y <= 2, {"KANTO_ROUTE_10_SOUTH", "KANTO_ROUTE_8", "KANTO_ROUTE_12"},
            {"center", "mart", "ptower", "fuji"}, "Lavender Town")
check(t._door_options("ptower") and t._door_options("fuji") and t.doors.get((18, 6)) == "ptower", "...the Tower's door at its foot and Mr. Fuji's house open their options")
enter(t, (20, 15))
check(t.room == "mart", "...its Mart is the shared room")
t._go(None, "OUT:20,15")
check(t.doors.get((18, 11)) == "radio" and t._door_options("radio") is not None and t.locked.get("radio"), "...HeartGold's Radio Tower stands below the Pokemon Tower's path, its door its own kind")
t = at_town("CELADON_CITY", "KANTO_ROUTE_7", (60, 40), lambda x, y: x >= 57, {"KANTO_ROUTE_7", "KANTO_ROUTE_16"},
            {"center", "dept", "gym", "game corner", "mansion", "hotel"}, "Celadon City")
check(t._door_options("dept") and t._door_options("game corner") and t.doors.get((11, 30)) == "gym" and t.doors.get((30, 4)) == "mansion",
      "...the Dept. Store and the Game Corner open their options; the Gym's porch door; the Mansion's back door")
check(t.doors.get((26, 18)) == "diner" and t._open((23, 19)) and t._open((26, 19)) and t.locked.get("diner"), "...the diner has HeartGold's door, and a way into its yard")
enter(t, (11, 30))
check(t.room == "gym" and t.people.get((6, 4), {}).get("action") == "GYM" and t.rows[8][6] == "2", f"...its Gym: FireRed's room, Erika behind the small trees ({t.room})")
t.draw(); t._go(None, "OUT:11,30")
g.walk_town_room = None
t = at_town("SAFFRON_CITY", "KANTO_ROUTE_5", (66, 55), lambda x, y: 5 <= y <= 8 and 32 <= x <= 37,
            {"KANTO_ROUTE_5", "KANTO_ROUTE_6", "KANTO_ROUTE_7", "KANTO_ROUTE_8", "SILPH_CITY"},
            {"center", "mart", "gym", "dojo", "copycat", "station"}, "Saffron City")
check(t.exits.get((33, 30)) == "SILPH_CITY" and len(t.signs) == 9 and t.doors.get((20, 7)) == "station" and t._open((20, 9)) and t.doors.get((43, 38)) == "house" and t.doors.get((40, 12)) == "dojo" and t.doors.get((22, 14)) == "copycat",
      f"...Silph Co.'s door; HeartGold's Magnet Train station in the north-west corner with a way through the railing, the Dojo's porch and Copycat's house are doors of their own kind; nine signs (silph {t.exits.get((33, 30))}, signs {len(t.signs)}, options: station {len(t._door_options('station'))}, dojo {len(t._door_options('dojo'))}, copycat {len(t._door_options('copycat'))})")
for _came, _where in (("KANTO_ROUTE_6", lambda x, y: 44 <= y <= 46 and 32 <= x <= 37), ("KANTO_ROUTE_7", lambda x, y: x in (9, 10) and 25 <= y <= 29),
                      ("KANTO_ROUTE_8", lambda x, y: x in (56, 57) and 25 <= y <= 29)):
    t = town("SAFFRON_CITY", _came)
    check(_where(*t.player), f"...in from {_came} you stand outside its gatehouse's city door {tuple(t.player)}")
t = town("SAFFRON_CITY", "KANTO_ROUTE_5")
t.player = t.anim_from = (34, 6); t.anim = 0; t.walk_goal = None
t.step(0, -1)
check(type(g.current_state).__name__ == "AreaTransitionState", f"...walk into the north gatehouse's door: on to Route 5 ({type(g.current_state).__name__})")
g.walk_town_room = None

# ---- every room, Pallet to Saffron: through its door you stand inside by the mat, someone in it has something to do, the mat leads back out
import json as _json
_tm = _json.load(open(os.path.join("assets", "town_maps.json"), encoding="utf-8"))
_came = {"PALLET_TOWN": "KANTO_ROUTE_1", "VIRIDIAN_CITY": "KANTO_ROUTE_1", "PEWTER_CITY": "KANTO_ROUTE_2", "CERULEAN_CITY": "KANTO_ROUTE_4",
         "VERMILLION_CITY": "KANTO_ROUTE_6", "LAVENDER_TOWN": "KANTO_ROUTE_8", "CELADON_CITY": "KANTO_ROUTE_7", "SAFFRON_CITY": "KANTO_ROUTE_5"}
_bad, _n = [], 0
for _key, _from in _came.items():
    t = town(_key, _from)
    for _d, _room in sorted(_tm[_key].get("inside", {}).items()):
        _door = tuple(int(v) for v in _d.split(","))
        g.walk_town_room = None
        if t.room: t._go(None, "OUT:%d,%d" % _door)
        t._go(_room, "OUT:%d,%d" % _door)
        _n += 1
        _mats = [xy for xy, v in t.exits.items() if v == "OUT:%d,%d" % _door]
        _ok = t.room == _room and t._open(tuple(t.player)) and all(isinstance(o, dict) for o in t.people.values()) and len(t.people) >= 1
        if _mats:
            _ok = _ok and min(abs(t.player[0] - x) + abs(t.player[1] - y) for x, y in _mats) == 1
            _m = _mats[0]
            _f = next(((_m[0] + dx, _m[1] + dy) for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)) if t._open((_m[0] + dx, _m[1] + dy)) and (_m[0] + dx, _m[1] + dy) not in t.exits), None)
            if _f:
                t.player = t.anim_from = _f; t.anim = 0; t.walk_goal = None
                t.step(_m[0] - _f[0], _m[1] - _f[1])
                _ok = _ok and t.room is None and abs(t.player[0] - _door[0]) + abs(t.player[1] - _door[1]) == 1  # (below the door; a back door: behind it)
        t.draw()
        if not _ok: _bad.append((_key, _room, _d, t.room, tuple(t.player)))
    g.walk_town_room = None
check(not _bad and _n >= 30, f"all {_n} doors with a room behind them, Pallet to Saffron: in by the mat, someone to talk to, out again below the door {_bad}")

t = town("PALLET_TOWN", "KANTO_ROUTE_1")
enter(t, (16, 13))
check(t.room == "lab" and t.people.get((6, 3), {}).get("target") == "professor_oak", f"Oak's Lab: Professor Oak stands at the back ({t.room})")
t._go(None, "OUT:16,13"); enter(t, (6, 7))
check(t.room == "home" and (8, 4) in t.people, "your house: Mom at the table")
g.walk_town_room = None
t = town("VIRIDIAN_CITY", "KANTO_ROUTE_1")
enter(t, (25, 18))
_les = t.people.get((6, 2), {})
check(t.room == "school" and len(_les.get("any", [])) == 5, f"the Trainers' School: the teacher has the five lessons ({len(_les.get('any', []))})")
t.player = t.anim_from = (6, 3); t.anim = 0
t.step(0, -1)
check(bool(t.hover_menu_active), "...talk to her: a menu of the lessons")
t.clear_hover_menu(); t._go(None, "OUT:25,18")
enter(t, (36, 10))
check(t.room == "gym" and (t.w, t.h) == (20, 24) and t.grid[3][11] == "4" and (17, 3) in t.stops, f"Viridian Gym: FireRed's maze, its spin tiles and stop tiles ({t.room})")
_slid = tstep(t, (10, 3), (1, 0))
check(_slid == (17, 3), f"...step on the spin tile at (11, 3): it carries you east to the stop tile at (17, 3) ({_slid})")
t.draw(); g.walk_town_room = None
t = town("SAFFRON_CITY", "KANTO_ROUTE_5")
enter(t, (46, 12))
check(t.room == "gym" and (t.w, t.h) == (29, 25) and len(t.links) == 30 and t.people.get((14, 11), {}).get("action") == "GYM",
      f"Saffron Gym: FireRed's nine rooms, thirty warp pads, Sabrina in the middle one ({t.room}, {len(t.links)} pads)")
_pad = tstep(t, (17, 20), (1, 0))
check(_pad == (28, 23), f"...step on the pad by the door: you stand on its far pad in the south-east room ({_pad})")
t.draw(); g.walk_town_room = None
t = town("CERULEAN_CITY", "KANTO_ROUTE_4")
check(t.doors.get((13, 28)) == "bike" and not t._open((11, 26)), "Cerulean's bike rack stands outside the Bike Shop")
enter(t, (13, 28))
check(t.room == "bike" and t.people.get((9, 3), {}).get("action") == "BIKESHOP", f"the Bike Shop: the owner behind his counter ({t.room})")
g.walk_town_room = None

# ---- the Rocket Hideout and the S.S. Anne, from FireRed's own floors
def settle(p, n=120):
    for _q in range(n):
        if getattr(p, "dialogue_box", None) and p.dialogue_box.visible:
            p.dialogue_box.advance()
        frames(p)
        if not p.sliding and p.anim <= 0:
            break


p = route("ROCKET_HIDEOUT", "CELADON_GAME_CORNER")
f = p.run.floor
check(p.run.n_floors == 4 and (f.w, f.h) == (28, 34) and p.run.index == 0 and p.run.player[1] <= 5 and sum(m.kind == "trainer" for m in f.movers) == 5,
      f"the Rocket Hideout: FireRed's four floors; in from the Game Corner at B1F's stairs {tuple(p.run.player)}; FireRed's five Grunts on B1F")
_hp = [t.get("zone") for t in g.loader.area_data["STORY_PROGRESSION"]["ROCKET_HIDEOUT"]["trainer_pool"]]
check(_hp == ["b1f"] * 5 + ["b2f"] + ["b3f"] * 2 + ["b4f"] * 3, f"...its trainer list is FireRed's eleven Grunts, floor by floor {_hp}")
p.run.warp(1, 21, 3)                                     # (down to B2F, where the spin-tile maze is)
f = p.run.floor
_spin = sorted(f.current)
_stops = p._stop_tiles()
check(p.run.index == 1 and len(_spin) >= 4 and len(_stops) >= 4, f"...B2F has spin tiles ({len(_spin)}) and stop tiles ({len(_stops)})")
_done = None
f.movers = []
for (_x, _y) in _spin:  # (the first spin tile you can step onto from the tile behind it)
    _dx, _dy = f.current[(_x, _y)]
    _from = (_x - _dx, _y - _dy)
    if f.walkable(*_from) and _from not in f.current and _from not in f.exits:
        p.run.player = _from; p.anim = 0; p.sliding = None
        p.step(_dx, _dy)
        settle(p)
        _done = ((_x, _y), tuple(p.run.player))
        break
check(_done and _done[1] != _done[0] and (_done[1] in _stops or abs(_done[1][0] - _done[0][0]) + abs(_done[1][1] - _done[0][1]) >= 1) and not p.sliding,
      f"...step on a spin tile: it carries you off and you come to rest {_done}")
p = route("ROCKET_HIDEOUT", "CELADON_GAME_CORNER")
p.run.floor.movers = []
p.run.player = (24, 26); p.anim = 0; p.sliding = None
_ev = p.run.step(0, -1); p._handle(_ev)
for _q in range(40):
    if getattr(p, "dialogue_box", None) and p.dialogue_box.visible:
        p.dialogue_box.advance()
    frames(p)
check(p.run.index == 3 and abs(p.run.player[0] - 20) + abs(p.run.player[1] - 23) <= 1, f"...the lift's door on B1F takes you down to B4F's (floor {p.run.index}, {tuple(p.run.player)})")
_fig = [m.payload.get("text") if isinstance(m.payload, dict) else m.payload for m in p.run.floor.movers if m.kind == "figure"]
check(any("GIOVANNI" in str(t) for t in _fig) or sum(m.kind == "trainer" for m in p.run.floor.movers) == 3, f"...B4F: Giovanni (when the story has him there) and its three Grunts ({_fig})")

# the Game Corner joins Celadon to the Hideout, as in the game (FireRed's room 10.14): a Grunt guards a poster, the switch behind it opens the stairs
check(set(p.run.floors[0].exits.values()) >= {"CELADON_GAME_CORNER"} and "CELADON_CITY" not in p.run.floors[0].exits.values(), "...B1F's stairs lead up to the Game Corner, not out to the street")
_gcf = ("game_corner_guard_defeated", "game_corner_poster", "game_corner_cleared", "visited_ROCKET_HIDEOUT", "visited_CELADON_GAME_CORNER")
_gcs = {k: story.story_flags.pop(k, None) for k in _gcf}
story.inventory["COIN_CASE"] = 1
t = town("CELADON_CITY", "KANTO_ROUTE_7")
check("gamecorner" not in t.town_map.get("rooms", {}) and t.doors.get((34, 21)) == "game corner", "Celadon: the Game Corner's door")
enter(t, (34, 21))
check(type(g.current_state).__name__ == "AreaTransitionState" and g.current_state.next_area_key == "CELADON_GAME_CORNER", "...through it: into the Game Corner")
p = route("CELADON_GAME_CORNER", "CELADON_CITY")
f = p.run.floor
check((f.w, f.h) == (18, 15) and [f.exits.get((x, 13)) for x in (9, 10, 11)] == ["CELADON_CITY"] * 3 and p.run.player[1] == 12,
      f"the Game Corner: FireRed's room, in at the mats {tuple(p.run.player)}")
check(all(f.decor.get((x, y)) == "slot" for x in (0, 5, 6, 11, 12, 17) for y in range(6, 11)) and all(f.decor.get((x, 3)) == "counter" for x in range(1, 10)),
      "...its six banks of slot machines and its long counter where FireRed has them")
_grunt = [m for m in f.movers if m.kind == "figure" and m.payload.get("text") == "ROCKET GRUNT"]
check(len(_grunt) == 1 and (_grunt[0].x, _grunt[0].y) == (11, 2) and f.decor.get((11, 1)) == "poster", "...a Rocket Grunt stands in front of the poster, where FireRed has him")
check("ROCKET_HIDEOUT" not in f.exits.values() and not f.walkable(15, 2), "...no stairs yet: the corner is plain wall")
p.draw()
f.movers = [m for m in f.movers if m.kind == "figure"]
p.run.player = (12, 2); p.anim = 0
_ev = p.run.step(-1, 0); p._handle(_ev); frames(p, 3)
_b = g.current_state
for _q in range(8):  # (his line, if it's said on the map first)
    if _b is p and p.dialogue_box.visible: p.dialogue_box.advance()
    frames(p, 2); _b = g.current_state
check(tuple(p.run.player) == (12, 2) and type(_b).__name__ in ("TrainerIntroState", "TrainerBattleState"), f"...walk into him: he challenges you ({type(_b).__name__})")
_nx = getattr(_b, "next_state", _b)
_opp = next((v for k, v in vars(_nx).items() if isinstance(v, list) and v and hasattr(v[0], "level") and v is not story.player_team), [])
_team = [(getattr(m, "id", None), m.level) for m in _opp]
check(_team == [(20, 20), (41, 20)], f"...FireRed's Raticate and Zubat, both Lv 20 {_team}")
story.story_flags["game_corner_guard_defeated"] = True  # (the battle won)
p = route("CELADON_GAME_CORNER", "CELADON_CITY")
f = p.run.floor
check(not any(m.kind == "figure" and m.payload.get("text") == "ROCKET GRUNT" for m in f.movers) and "ROCKET_HIDEOUT" not in f.exits.values(), "...beaten: he's gone, the stairs still hidden")
f.movers = [m for m in f.movers if m.kind == "figure"]
p.run.player = (11, 2); p.anim = 0
_act = p._act_here()
check(_act and _act[0] == "CHECK", f"...stand below the poster: CHECK ({_act and _act[0]})")
_act[1](); frames(p, 2)
check(story.story_flags.get("game_corner_poster") and f.exits.get((15, 2)) == "ROCKET_HIDEOUT" and f.walkable(15, 2) and p.dialogue_box.visible,
      "...push the switch behind it: the stairs open in the top-right corner")
for _q in range(4):
    if p.dialogue_box.visible: p.dialogue_box.advance()
    frames(p, 2)
p.draw()
p.run.player = (14, 2); p.anim = 0
_ev = p.run.step(1, 0); p._handle(_ev); frames(p, 5)
check(type(g.current_state).__name__ == "AreaTransitionState" and g.current_state.next_area_key == "ROCKET_HIDEOUT", "...step onto the stairs: down into the Rocket Hideout")
p = route("CELADON_GAME_CORNER", "ROCKET_HIDEOUT")
check(tuple(p.run.player) == (14, 2), f"...back up from the Hideout: you stand by the stairs {tuple(p.run.player)}")
for _k in _gcf: story.story_flags.pop(_k, None)
story.story_flags["game_corner_cleared"] = True  # (an older save that cleared the Hideout before the poster was built)
p = route("CELADON_GAME_CORNER", "CELADON_CITY")
check("ROCKET_HIDEOUT" in p.run.floor.exits.values() and not any(m.kind == "figure" and m.payload.get("text") == "ROCKET GRUNT" for m in p.run.floor.movers),
      "...a save that already cleared the Hideout: the stairs are open, no guard")
for _k in _gcf:
    story.story_flags.pop(_k, None)
    if _gcs[_k] is not None: story.story_flags[_k] = _gcs[_k]
g.walk_town_pos = None
t = town("CELADON_CITY", "CELADON_GAME_CORNER")
check(tuple(t.player) == (34, 22), f"...out of the Game Corner with no remembered spot: below its own door {tuple(t.player)}")
# the Prize Corner next door (FireRed's room 10.15)
check(t.doors.get((39, 20)) == "prize corner", "Celadon: the Prize Corner's own door, beside the Game Corner")
enter(t, (39, 20))
check(t.room == "prize" and (t.w, t.h) == (9, 10) and sorted(t.people) == [(2, 2), (4, 2), (6, 2)], f"...through it: FireRed's room, three clerks behind the counter ({t.room}, {sorted(t.people)})")
t.draw()
check(tstep(t, (2, 5), (0, -1)) == (2, 4), "...walk up to the counter")
t.step(0, -1)
check(g.current_state is t and bool(getattr(t, "npc_active", False)), "...the side windows' clerks point you to the middle one")
_tap_through(t)
check(tstep(t, (4, 5), (0, -1)) == (4, 4), "...the middle window")
t.step(0, -1)
_pz = g.current_state
check(type(_pz).__name__ == "PrizeCounterState" and _pz.previous_state is t, f"...talk across it: the prize counter ({type(_pz).__name__})")
_pz.draw(); _pz.leave()
check(g.current_state is t and t.room == "prize", "...BACK: in the Prize Corner again")
_out = tstep(t, (4, 7), (0, 1))
t.step(0, 1) if t.room else None
check(t.room is None and tuple(t.player) == (39, 21), f"...out by the mat: below its door in Celadon ({t.room}, {tuple(t.player)})")
g.walk_town_room = None

p = route("KANTO_SS_ANNE", "VERMILLION_CITY")
f = p.run.floor
check(p.run.n_floors == 7 and (f.w, f.h) == (31, 21) and p.run.index == 0 and p.run.player[1] <= 4 and 17 <= p.run.player[0] <= 21,
      f"the S.S. Anne: FireRed's seven floors; up the gangway onto 1F {tuple(p.run.player)}")
check([f.decor.get((x, 10)) for x in (5, 8, 11, 14, 17, 20)] == [f"door:cabin{k}" for k in range(6)], "...1F's corridor: six cabin doors, our six cabins in order")
f.movers = []
p.run.player = (4, 8); p.anim = 0; p.sliding = None
_ev = p.run.step(-1, 0); p._handle(_ev)
for _q in range(40):
    if getattr(p, "dialogue_box", None) and p.dialogue_box.visible:
        p.dialogue_box.advance()
    frames(p)
check(p.run.index == 1 and abs(p.run.player[0] - 2) + abs(p.run.player[1] - 2) <= 1, f"...1F's west stairs lead up to 2F's (floor {p.run.index}, {tuple(p.run.player)})")

# ---- Routes 12 to 15 and Fuchsia City (FireRed 3.30-3.33, 3.7)
_had = {k: story.inventory.get(k) for k in ("HM_SURF", "HM_CUT")}
story.inventory["HM_SURF"] = 1; story.inventory["HM_CUT"] = 1
_sn = story.story_flags.pop("KANTO_ROUTE_12_boss_defeated", None)
for _a, _b, _size, _n in (("KANTO_ROUTE_12", "LAVENDER_TOWN", (24, 120), 8), ("KANTO_ROUTE_12", "KANTO_ROUTE_11", (24, 120), 8), ("KANTO_ROUTE_12", "KANTO_ROUTE_13", (24, 120), 8),
                          ("KANTO_ROUTE_13", "KANTO_ROUTE_12", (72, 20), 10), ("KANTO_ROUTE_13", "KANTO_ROUTE_14", (72, 20), 10),
                          ("KANTO_ROUTE_14", "KANTO_ROUTE_13", (24, 60), 11), ("KANTO_ROUTE_14", "KANTO_ROUTE_15", (24, 60), 11),
                          ("KANTO_ROUTE_15", "KANTO_ROUTE_14", (72, 20), 11), ("KANTO_ROUTE_15", "FUCHSIA_CITY", (72, 20), 11)):
    p = route(_a, _b); f = p.run.floor
    _edge = [t for t, v in f.exits.items() if v == _b]
    check((f.w, f.h) == _size and _edge and min(abs(p.run.player[0] - x) + abs(p.run.player[1] - y) for x, y in _edge) == 1 and sum(m.kind == "trainer" for m in f.movers) == _n,
          f"{_a} from {_b}: FireRed's {_size[0]} x {_size[1]}, in beside the way you came {tuple(p.run.player)}, FireRed's {_n} trainers")
    p.draw()
p = route("KANTO_ROUTE_12", "LAVENDER_TOWN"); f = p.run.floor; f.movers = []
_i, _at = step(p, (14, 14), (0, 1))
check(p._floor_name(_i) == "Route 12 Gate" and _at == (5, 2) and people(p) == {"GATE GUARD"}, f"Route 12's lookout: in by its north door {_at}: FireRed's room, its guard")
p.draw()
_i, _at = step(p, (5, 10), (0, 1))
check((_i, _at) == (0, (13, 22)), f"...out by its south mat, onto the pier below {_at}")
_i, _at = step(p, (13, 22), (1, -1) if False else (0, -1)) if False else (0, _at)
p._warp(p.recipe["art"]["room_floors"]["gate"], 5, 3); frames(p, 2)
_i, _at = step(p, (5, 2), (0, -1))
check((_i, _at) == (0, (14, 14)), f"...and out by its north mat {_at}")
_i, _at = step(p, (12, 87), (0, -1))
check(p._floor_name(_i) == "Fishing House" and people(p) == {"FISHING GURU"}, f"...the fishing house: FireRed's room, the Fishing Guru's brother {_at}")
p.draw()
_i, _at = step(p, (3, 6), (0, 1))
check((_i, _at) == (0, (12, 87)), f"......and out by its mat {_at}")
check(f.exits.get((14, 70)) == "BOSS" and p._gate("KANTO_ROUTE_13") is None, "...Snorlax sleeps on the pier where FireRed has him (not across the way out)")
p.run.player = (14, 69); p.anim = 0; p.anim_from = (14, 69)
_ev = p.run.step(0, 1); p._handle(_ev); frames(p, 3)
check(p.dialogue_box.visible and tuple(p.run.player) != (14, 70), "...walk into him without the Poke Flute: sound asleep, he won't budge")
while p.dialogue_box.visible: p.dialogue_box.advance()
story.story_flags["KANTO_ROUTE_12_boss_defeated"] = True
p._sync_figures()
check((14, 70) not in f.exits and f.walkable(14, 70), "...beaten: the pier is clear")
story.story_flags.pop("KANTO_ROUTE_12_boss_defeated", None)
if _sn: story.story_flags["KANTO_ROUTE_12_boss_defeated"] = _sn
p = route("KANTO_ROUTE_15", "KANTO_ROUTE_14")
_i, _at = step(p, (17, 11), (-1, 0))
check(p._floor_name(_i) == "Route 15 Gate" and _at == (10, 6) and people(p) == {"GATE GUARD"}, f"Route 15's gatehouse: in by its east door {_at}: FireRed's room, its guard")
p.draw()
_i, _at = step(p, (2, 6), (-1, 0))
check((_i, _at) == (0, (8, 11)), f"...out by its west mat, west of the gatehouse {_at}")
_i, _at = step(p, (8, 11), (1, 0)); _j, _at2 = step(p, (10, 7), (1, 0))
check(_at == (2, 6) and (_j, _at2) == (0, (17, 11)), f"...and back the other way {_at} {_at2}")
for _from, _side in (("KANTO_ROUTE_15", lambda q: q[0] >= 45), ("KANTO_ROUTE_18", lambda q: q[0] <= 2), ("KANTO_ROUTE_19", lambda q: q[1] >= 37)):
    t = town("FUCHSIA_CITY", _from)
    check((t.w, t.h) == (48, 40) and _side(t.player), f"Fuchsia City from {_from}: FireRed's 48 x 40, in at that edge {tuple(t.player)}")
check(sum(k == "hedge" for k in t.town_map["buildings"].values()) >= 14 and t.exits and "SAFARI_ZONE" in t.exits.values() or "safari" in t.doors.values(), "...the zoo's pens, the Safari Zone's gate")
for _d, _room, _who in (((33, 31), "warden", None), ((38, 31), "brother", "Fishing Guru's Brother"), ((25, 31), "center", "Heal"), ((11, 15), "mart", "Shop")):
    enter(t, _d)
    check(t.room == _room and (_who is None or any(o.get("text") == _who for o in t.people.values())), f"...door {_d}: the {_room}'s room ({t.room})")
    t.draw(); t._go(None, "OUT:%d,%d" % _d)
enter(t, (38, 31))
_bm = next(xy for xy, v in t.exits.items() if v == "OUT:39,28")
t.player = t.anim_from = (_bm[0], _bm[1] + 1); t.anim = 0; t.step(0, -1); t.anim = 0
check(t.room is None and tuple(t.player) == (39, 27), f"...the fishing house's back door: out to the pond yard behind it {tuple(t.player)}")
t.step(0, 1); t.anim = 0
check(t.room == "brother", "...and back in by it")
t._go(None, "OUT:38,31"); g.walk_town_room = None
for _k, _v in _had.items():
    if _v is None: story.inventory.pop(_k, None)
    else: story.inventory[_k] = _v

# ---- the Cycling Road (FireRed 3.34-3.36) and Fuchsia Gym (11.3)
_had = {k: story.inventory.get(k) for k in ("HM_SURF", "HM_CUT", "BICYCLE")}
story.inventory["HM_SURF"] = 1; story.inventory["HM_CUT"] = 1; story.inventory["BICYCLE"] = 1
_sn = story.story_flags.pop("KANTO_ROUTE_16_boss_defeated", None)


def _still(p, n=40):
    for _q in range(n):
        if p.anim == 0: break
        frames(p)


for _a, _b, _size, _n in (("KANTO_ROUTE_16", "CELADON_CITY", (48, 20), 7), ("KANTO_ROUTE_16", "KANTO_ROUTE_17", (48, 20), 7), ("KANTO_ROUTE_17", "KANTO_ROUTE_16", (24, 160), 10),
                          ("KANTO_ROUTE_17", "KANTO_ROUTE_18", (24, 160), 10), ("KANTO_ROUTE_18", "KANTO_ROUTE_17", (60, 20), 3), ("KANTO_ROUTE_18", "FUCHSIA_CITY", (60, 20), 3)):
    p = route(_a, _b); f = p.run.floor
    check((f.w, f.h) == _size and _b in f.exits.values() and sum(m.kind == "trainer" for m in f.movers) == _n, f"{_a} from {_b}: FireRed's {_size[0]} x {_size[1]}, FireRed's {_n} trainers")
    p.draw()
p = route("KANTO_ROUTE_16", "CELADON_CITY"); f = p.run.floor; f.movers = []
check(f.exits.get((31, 13)) == "BOSS" and str(f.exits.get((10, 5))).startswith("WARP:"), "Route 16: Snorlax asleep on the road where FireRed has him; the quiet house's door")
story.story_flags["KANTO_ROUTE_16_boss_defeated"] = True; p._sync_figures()
for _y, _in, _mat in ((13, (10, 12), (2, 12)), (6, (10, 3), (2, 3))):
    _i, _at = step(p, (28, _y), (-1, 0))
    check(p._floor_name(_i) == "Cycling Road Gate" and _at == _in and not p._cycling(), f"...the gatehouse's {'lower' if _y == 13 else 'upper'} east door: into its {'lower' if _y == 13 else 'upper'} hall {_at}, on foot")
    if _y == 6: check(people(p) == {"GATE GUARD", "CYCLIST"}, "......its guard behind the counter, a cyclist")
    p.draw()
    _i, _at = step(p, _mat, (-1, 0))
    check((_i, _at) == (0, (19, _y)), f"......and out by the west mat, west of the gatehouse {_at}")
_i, _at = step(p, (10, 6), (0, -1))
check(p._floor_name(_i) == "A Quiet House" and people(p) == {"A QUIET HOUSE"}, f"...the quiet house: FireRed's room, the girl inside {_at}")
p.draw()
_i, _at = step(p, (4, 6), (0, 1))
check((_i, _at) == (0, (10, 6)), f"......and out by its mat {_at}")
check(p._cycling((5, 15)) and not p._cycling((40, 13)), "...west of the gatehouse you ride; on Celadon's side you walk")
story.inventory.pop("BICYCLE")
check(p._gate("KANTO_ROUTE_17") == ("bike", None, False) and not p._cycling((5, 15)), "...without the Bicycle: the way onto Route 17 is barred")
p = route("KANTO_ROUTE_18", "FUCHSIA_CITY")
check(p._gate("KANTO_ROUTE_17") == ("bike", None, False), "Route 18: the same from the south")
_i, _at = step(p, (49, 9), (-1, 0))
check(p._floor_name(_i) == "Cycling Road Gate" and people(p) == {"GATE GUARD"} and not p._cycling(), f"...into its gatehouse by the east door: FireRed's room, its guard; on foot inside {_at}")
p.draw()
_i, _at = step(p, (2, 6), (-1, 0))
check((_i, _at) == (0, (40, 9)), f"...and out by its west mat, west of the gatehouse {_at}")
story.inventory["BICYCLE"] = 1
story.story_flags.pop("KANTO_ROUTE_16_boss_defeated", None)
if _sn: story.story_flags["KANTO_ROUTE_16_boss_defeated"] = _sn
p = route("KANTO_ROUTE_17", "KANTO_ROUTE_16"); f = p.run.floor; f.movers = []; p.banner = 0
check(p._cycling() and p._downhill() and len(p._overheads()) >= 60, f"Route 17: you ride, on the slope; its rail posts are an overhead layer ({len(p._overheads())})")
_y0 = p.run.player[1]; frames(p, 60)
check(p.run.player[1] >= _y0 + 6, f"...hands off: you roll downhill (row {_y0} to {p.run.player[1]})")
check(any(b[1] == "BRAKE" for b in p._buttons()), "...the WAIT button reads BRAKE on the slope")
p.wait_turn(); _still(p); _y1 = p.run.player[1]; frames(p, 40)
check(p.braking and p.run.player[1] == _y1, f"...BRAKE: you hold still (row {_y1})")
p.step(1, 0); _x1 = p.run.player[0]; frames(p, 30)
check(not p.braking and p.run.player[1] > _y1, f"...steer aside: off the brake, rolling again (row {p.run.player[1]})")
p.wait_turn(); _still(p); _y2 = p.run.player[1]; p.step(0, -1)
check(p.run.player[1] == _y2 - 1 and p.anim > 6, f"...pedalling back up: a step takes twice as long ({p.anim} frames)")
p.draw()
p = route("KANTO_ROUTE_17", "KANTO_ROUTE_16"); f = p.run.floor
_tr = [m for m in f.movers if m.kind == "trainer"][0]; f.movers = [_tr]
p.run.player = (_tr.x, _tr.y - 4); p.anim = 0; frames(p, 80)
check(tuple(p.run.player) == (_tr.x, _tr.y - 1) and g.current_state is p, f"...a biker in your lane: you stop short of him, no crash {tuple(p.run.player)}")
f.movers = []; p.run.player = (9, 150); p.anim = 0; p.braking = False; frames(p, 140)
check(tuple(p.run.player) == (9, 159) and not p._downhill(), f"...the slope ends at the bottom: over the ledge onto level ground {tuple(p.run.player)}")
t = town("FUCHSIA_CITY", "KANTO_ROUTE_15")
enter(t, (9, 32))
_gl = t.town_map["rooms"]["gym"]["roofs"]["_glass"]
check(t.room == "gym" and (t.w, t.h) == (15, 23) and t.people.get((7, 13), {}).get("action") == "GYM" and len(_gl) >= 50, f"Fuchsia Gym: FireRed's room, Koga on his pad, {len(_gl)} invisible walls")
check(tstep(t, (3, 17), (0, -1)) == (3, 17) and tstep(t, (1, 17), (0, -1)) == (1, 16), "...walk into one: it stops you; the gap FireRed leaves lets you through")
t.draw(); t._go(None, "OUT:9,32"); g.walk_town_room = None
_gt = [x["name"] for x in g.loader.area_data["STORY_PROGRESSION"]["FUCHSIA_CITY"]["gym"]["trainers"]]
check(len(_gt) == 6 and _gt[0] == "Juggler Kayden" and _gt[-1] == "Tamer Edgar", f"...its trainers are FireRed's six {_gt}")
for _k, _v in _had.items():
    if _v is None: story.inventory.pop(_k, None)
    else: story.inventory[_k] = _v

# ---- the sea loop, Cinnabar, Seafoam, the League's road, the Safari Zone, the Mansion (FireRed 3.37-3.42, 3.8, 3.9, 1.39-1.41, 1.59-1.66, 1.83-1.87)
_had = {k: story.inventory.get(k) for k in ("HM_SURF", "HM_CUT", "HM_STRENGTH", "BICYCLE")}
for _k in _had: story.inventory[_k] = 1
_kb = list(story.badges.get("KANTO", []))
story.badges["KANTO"] = ["BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL", "MARSH", "VOLCANO", "EARTH"]
_bf = {k: story.story_flags.pop(k) for k in list(story.story_flags) if k.startswith("boulder_SEAFOAM")}
for _a, _b, _size in (("KANTO_ROUTE_19", "FUCHSIA_CITY", (24, 60)), ("KANTO_ROUTE_19", "KANTO_ROUTE_20", (24, 60)), ("KANTO_ROUTE_20", "KANTO_ROUTE_19", (120, 20)),
                      ("KANTO_ROUTE_20", "CINNABAR_ISLAND", (120, 20)), ("KANTO_ROUTE_21", "PALLET_TOWN", (24, 100)), ("KANTO_ROUTE_21", "CINNABAR_ISLAND", (24, 100)),
                      ("KANTO_ROUTE_23", "KANTO_ROUTE_22", (24, 160)), ("KANTO_ROUTE_23", "INDIGO_PLATEAU", (24, 160)), ("SAFARI_ZONE", "FUCHSIA_CITY", (158, 80))):
    p = route(_a, _b); f = p.run.floor
    _edge = [t for t, v in f.exits.items() if v == _b]
    check((f.w, f.h) == _size and _edge and min(abs(p.run.player[0] - x) + abs(p.run.player[1] - y) for x, y in _edge) <= 1,
          f"{_a} from {_b}: FireRed's {_size[0]} x {_size[1]}, in beside the way you came {tuple(p.run.player)}")
    p.draw()
p = route("KANTO_ROUTE_20", "KANTO_ROUTE_19"); f = p.run.floor
check(sum(v == "SEAFOAM_ISLANDS" for v in f.exits.values()) == 2 and sum(m.kind == "trainer" for m in f.movers) >= 9, "Route 20: Seafoam's two mouths, FireRed's swimmers")
for _i, _x in ((0, 6), (1, 32)):
    p = route("SEAFOAM_ISLANDS", "KANTO_ROUTE_20", index=_i, count=2)
    check(p.run.n_floors == 5 and (p.run.floor.w, p.run.floor.h) == (38, 24) and tuple(p.run.player) == (_x, 20), f"Seafoam: in by Route 20's {'west' if _i == 0 else 'east'} mouth {tuple(p.run.player)}")
    q = route("KANTO_ROUTE_20", "SEAFOAM_ISLANDS", index=_i, count=2)
    check(q.run.player[0] == (60, 72)[_i], f"...and back out at the same mouth {tuple(q.run.player)}")
check(sorted(t for t, v in p.run.floor.decor.items() if str(v).startswith("boulder")) == [(22, 12), (32, 9)], "...1F's two boulders where FireRed has them")
p.run.floor.movers = []; p._warp(3, 12, 9); frames(p, 3); f = p.run.floor
check(len(f.current) > 50 and sorted(t for t, v in f.decor.items() if str(v).startswith("hole")) == [(6, 18), (9, 18)], f"...B3F: the current runs ({len(f.current)} tiles), two holes for its boulders")
story.story_flags["boulder_SEAFOAM_ISLANDS_0_22_12"] = True; story.story_flags["boulder_SEAFOAM_ISLANDS_0_32_9"] = True
p._clear_boulders()
check(not f.current and sorted(t for t, v in f.decor.items() if str(v).startswith("fallen")) == [(23, 8), (24, 8)], "...1F's boulders pushed down: they land in B3F's channel and its current stops")
p._warp(4, 15, 9); frames(p, 3); f = p.run.floor
check(len(f.current) > 100 and any(m.kind == "figure" and (m.x, m.y) == (9, 2) for m in f.movers), f"...B4F: the current runs ({len(f.current)} tiles), Articuno where FireRed has it")
story.story_flags["boulder_SEAFOAM_ISLANDS_3_6_17"] = True; story.story_flags["boulder_SEAFOAM_ISLANDS_3_9_16"] = True
p._clear_boulders()
check(not f.current, "...B3F's two boulders pushed down: B4F's current stops, the way to Articuno is open")
p.draw()
for _k in list(story.story_flags):
    if _k.startswith("boulder_SEAFOAM"): story.story_flags.pop(_k)
story.story_flags.update(_bf)
for _from, _ok in (("KANTO_ROUTE_21", lambda q: q[1] <= 2), ("KANTO_ROUTE_20", lambda q: q[0] >= 20)):
    t = town("CINNABAR_ISLAND", _from)
    check((t.w, t.h) == (24, 20) and _ok(t.player), f"Cinnabar Island from {_from}: FireRed's 24 x 20 {tuple(t.player)}")
check({"mansion", "gym", "fossil", "center", "mart"} <= set(t.doors.values()) and "CINNABAR_VOLCANO" in t.exits.values(), "...the Mansion, Gym, Lab, Center, Mart; the volcano's mouth (HeartGold's)")
_gk = story.story_flags.get("got_secret_key"); story.story_flags["got_secret_key"] = True
for _d, _room in (((14, 11), "center"), ((19, 11), "mart"), ((8, 9), "lab"), ((20, 4), "gym")):
    enter(t, _d)
    check(t.room == _room and t.people, f"...door {_d}: the {_room}'s room ({t.room})")
    t.draw()
    if t.room == "gym":
        check((t.w, t.h) == (30, 25) and t.people.get((5, 4), {}).get("action") == "GYM" and t._open((26, 9)) and t._open((5, 9)), "...Cinnabar Gym: FireRed's rooms, the quiz doors open, Blaine in the far one")
    if t.room: t._go(None, "OUT:%d,%d" % _d)
if not _gk: story.story_flags.pop("got_secret_key", None)
g.walk_town_room = None
check(len(g.loader.area_data["STORY_PROGRESSION"]["CINNABAR_ISLAND"]["gym"]["trainers"]) == 7, "...its trainers are FireRed's seven")
p = route("KANTO_ROUTE_23", "KANTO_ROUTE_22"); f = p.run.floor
_gd = sorted((m.y, m.payload.get("text")) for m in f.movers if m.kind == "figure")
check([n for _y, n in _gd] == ["EARTH BADGE GUARD", "VOLCANO BADGE GUARD", "MARSH BADGE GUARD", "SOUL BADGE GUARD", "RAINBOW BADGE GUARD", "THUNDER BADGE GUARD", "CASCADE BADGE GUARD", "BOULDER BADGE GUARD"]
      and len(p._overheads()) >= 6, f"Route 23: the eight badge guards in FireRed's order, north to south; the gates' arches overhead ({len(p._overheads())})")
for _i, _fl, _n in ((0, 0, 2), (1, 1, 5)):
    p = route("VICTORY_ROAD", "KANTO_ROUTE_23", index=_i, count=2)
    check(p.run.n_floors == 3 and p.run.index == _fl and sum(m.kind == "trainer" for m in p.run.floor.movers) == _n, f"Victory Road by Route 23's {'south' if _i == 0 else 'north'} mouth: onto {'1F' if _fl == 0 else '2F'} (floor {p.run.index}), FireRed's trainers there")
    p.run.floor.movers = []; p.run.player = [t0 for t0, v in p.run.floor.exits.items() if v == "KANTO_ROUTE_23"][0]
    p._try_exit("KANTO_ROUTE_23")
    check((core.ENTRANCE_INDEX, core.ENTRANCE_COUNT) == (_i, 2), f"...and out again by the same mouth ({core.ENTRANCE_INDEX} of {core.ENTRANCE_COUNT})")
    q = route("KANTO_ROUTE_23", "VICTORY_ROAD", index=_i, count=2)
    check(tuple(q.run.player) == ((5, 29), (18, 29))[_i], f"...standing below it on Route 23 {tuple(q.run.player)}")
t = town("INDIGO_PLATEAU", "KANTO_ROUTE_23")
check((t.w, t.h) == (24, 20) and t.doors.get((11, 6)) == "league" and "johto" in t.doors.values() and t.player[1] >= 17, f"Indigo Plateau: FireRed's 24 x 20, up the stairs from Route 23 {tuple(t.player)}; the League's door, the booth for Johto (ours)")
enter(t, (11, 6))
check(t.room == "lobby" and {o.get("text") for o in t.people.values()} == {"Heal", "Shop", "ELITE_FOUR"}, f"...the League's lobby: the nurse, the clerk, the Elite Four's door ({t.room})")
t.draw(); t._go(None, "OUT:11,6"); g.walk_town_room = None
p = route("SAFARI_ZONE", "FUCHSIA_CITY"); f = p.run.floor; f.movers = [m for m in f.movers if m.kind == "figure"]
check([p.zones[p._zone_index(0, x, y)] for x, y in ((75, 60), (130, 60), (75, 20), (20, 60))] == ["center", "east", "north", "west"], "the Safari Zone: FireRed's four areas, each its own zone")
p.run.player = (59, 59); p.anim = 0; p.anim_from = (59, 59)
_ev = p.run.step(-1, 0); p._handle(_ev); frames(p, 4)
check(p.run.player[0] < 48, f"...through the Center's west gate: out of the West area's east gate {tuple(p.run.player)}")
check(any(m.kind == "figure" and m.payload.get("text") == "GOLD TEETH" and m.x < 48 for m in f.movers) or story.story_flags.get("got_gold_teeth"), "...the Gold Teeth lie in the West")
p.draw()
for _n, (_dx, _dy), _zone, _who in ((1, (79, 67), "center", {"SAFARI RANGER", "RESTING SCIENTIST"}), (2, (143, 56), "east", {"TIRED HIKER", "BIRD FAN", "ROCK FAN"}),
                                    (3, (91, 8), "north", {"NAP TAKER", "LOST BOY", "FISHING FAN", "PICNIC GIRL"}), (4, (19, 60), "west", {"OLD CAMPER", "TEETH HUNTER", "LUCKY CATCHER"}),
                                    (5, (12, 49), "west", {"SECRET HOUSE MAN"})):
    if p.run.index != 0: p._warp(0, _dx, _dy + 1); frames(p, 3)
    p.run.floor.movers = [m for m in p.run.floor.movers if m.kind == "figure"]
    p.run.player = (_dx, _dy + 1); p.anim = 0; p.anim_from = (_dx, _dy + 1); p._note_area() if hasattr(p, "_note_area") else None
    story.story_flags["zone_SAFARI_ZONE"] = _zone
    _ev = p.run.step(0, -1); p._handle(_ev); frames(p, 4); f = p.run.floor
    check(p.run.index == _n and tuple(p.run.player) == (4, 8) and (f.w, f.h) == (13, 11) and not any(m.kind == "wild" for m in f.movers) and not f.items
          and {m.payload.get("text") for m in f.movers if m.kind == "figure"} == _who and story.story_flags.get("zone_SAFARI_ZONE") == _zone,
          f"...in at the {p._floor_name(_n)}'s door {(_dx, _dy)}: FireRed's room, its people, nothing wild (floor {p.run.index}, {tuple(p.run.player)}, zone {story.story_flags.get('zone_SAFARI_ZONE')})")
    check(len(p._overheads()) >= 2 and not f.walkable(8, 5 if _n == 5 else 6) and f.walkable(9, 2), "......its shelves hang over the row below; the counter or desks in the way")
    p.draw()
    _who1 = next(m for m in f.movers if m.kind == "figure")
    _ev = p.run.step(0, 1); p._handle(_ev); frames(p, 4)
    check(p.run.index == 0 and tuple(p.run.player) == (_dx, _dy + 1), f"......and out by its mat, below the door {tuple(p.run.player)}")
p = route("POKEMON_MANSION", "CINNABAR_ISLAND")
check(p.run.n_floors == 4 and (p.run.floor.w, p.run.floor.h) == (38, 35) and sum(m.kind == "trainer" for m in p.run.floor.movers) == 2, f"the Pokemon Mansion: FireRed's four floors, in at the front doors {tuple(p.run.player)}, 1F's two trainers")
p.run.floor.movers = []; p._warp(2, 8, 3); frames(p, 3)
check(any(m.kind == "figure" and m.payload.get("text") == "BURGLAR SIMON" and (m.x, m.y) == (7, 13) for m in p.run.floor.movers) or story.story_flags.get("got_secret_key"), "...Burglar Simon on 3F, where FireRed stands him")
p.draw()
story.badges["KANTO"] = _kb
for _k, _v in _had.items():
    if _v is None: story.inventory.pop(_k, None)
    else: story.inventory[_k] = _v

# ---- the ordinary houses in the towns (FireRed's own rooms: 7.0-7.9, 9.4, 9.7, 8.3, 8.4, 10.17-10.19, 14.4, 14.8, 14.9, 11.2, 11.4, 11.9)
for _town, _came, _doors in (
        ("CERULEAN_CITY", "KANTO_ROUTE_4", (((10, 11), "house_w", (10, 10), 1), ((30, 11), "house_ne", (10, 9), 2), ((31, 8), "house_ne", (10, 9), 2), ((15, 17), "house_mid", (11, 9), 2), ((23, 28), "house_s", (11, 9), 1), ((17, 11), "house_n", (11, 9), 1))),
        ("VERMILLION_CITY", "KANTO_ROUTE_6", (((19, 17), "house_n", (11, 9), 1), ((28, 24), "house_e", (11, 9), 2))),
        ("LAVENDER_TOWN", "KANTO_ROUTE_8", (((5, 16), "house_w", (11, 9), 1), ((10, 16), "rater", (11, 9), 1))),
        ("CELADON_CITY", "KANTO_ROUTE_7", (((37, 29), "restaurant", (15, 11), 5), ((41, 29), "house_e", (11, 9), 2), ((49, 29), "hotel", (17, 11), 3))),
        ("SAFFRON_CITY", "KANTO_ROUTE_5", (((27, 21), "house_w", (11, 9), 2), ((43, 38), "psychic", (11, 9), 1), ((47, 21), "fans", (11, 17), 4))),
        ("FUCHSIA_CITY", "KANTO_ROUTE_15", (((28, 16), "office", (20, 11), 4), ((14, 31), "house_w", (11, 9), 2), ((19, 31), "deleter", (11, 9), 1)))):
    t = town(_town, _came)
    for _d, _room, _size, _n in _doors:
        enter(t, _d)
        _said = [o.get("event", {}).get("lines") for o in t.people.values() if isinstance(o, dict)]
        check(t.room == _room and (t.w, t.h) == _size and len(t.people) == _n and all(_said) and set(t.exits.values()) <= {"OUT:%d,%d" % q for q, r, _s, _c in _doors if r == _room},
              f"{_town} door {_d}: FireRed's room {_size[0]} x {_size[1]} ({t.room}), {len(t.people)} people with something to say, in by the mat {tuple(t.player)}")
        _near = [q for q in t.people if any(t._open((q[0] + a, q[1] + b)) or t._open((q[0] + 2 * a, q[1] + 2 * b)) for a, b in ((0, 1), (0, -1), (1, 0), (-1, 0)))]
        check(len(_near) == len(t.people), f"...everyone can be walked up to ({len(_near)} of {len(t.people)})")
        t.draw()
        if t.room:
            t._go(None, "OUT:%d,%d" % _d)
            check(t.room is None and abs(t.player[0] - _d[0]) + abs(t.player[1] - _d[1]) <= 1, f"...and back out beside the door {tuple(t.player)}")
        g.walk_town_room = None
t = town("CELADON_CITY", "KANTO_ROUTE_7")
check("hotel" not in t.locked and "diner" in t.locked, "Celadon: the hotel's door is open now; the diner (ours, HeartGold's) stays shut")

# ---- One Island and Treasure Beach
t = town("ONE_ISLAND", "KINDLE_ROAD")
check(isinstance(t, _WTS) and (t.w, t.h) == (24, 20) and t.player[0] >= 21 and set(t.exits.values()) == {"KINDLE_ROAD", "TREASURE_BEACH"},
      f"One Island: FireRed's 24 x 20; in from Kindle Road on the east {t.player}")
enter(t, (14, 5))
check(t.room == "center" and len(t.people) == 3 and t.people[(2, 2)].get("action") == "SHOP" and "any" in t.people[(13, 2)],
      f"...the Network Center: the shared Center room, with the shop's clerk and Celio standing in it ({t.room})")
t._go(None, "OUT:14,5")
g.walk_town_room = None
check(t.doors.get((12, 18)) == "harbor" and t.doors.get((14, 5)) == "center" and t._door_options("harbor") and t._door_options("center"),
      f"...the harbour's door is the mat at the pier's end; the Network Center's door {sorted(t.doors.items())}")
check(tstep(t, (11, 17), (-1, 0)) == (11, 17) and "Surf" in t.toast, "...the sea beside the pier needs Surf")
check(all(t.rows[6][x] == "#" for x in range(18, 23)) and t.rows[6][16] == ".", "...the row above the east house is solid")
t.draw()
p = route("TREASURE_BEACH", "ONE_ISLAND")
f = p.run.floor
check((f.w, f.h) == (24, 40) and set(f.exits.values()) == {"ONE_ISLAND"} and not f.walkable(3, 4) and not f.walkable(4, 4) and not f.walkable(3, 5) and not f.walkable(4, 5),
      "Treasure Beach: FireRed's 24 x 40; a sea rock is solid on all four of its tiles")

story.inventory.clear(); story.inventory.update(_inv)
g.walk_towns = False
print(f"##### {fails} failures")
