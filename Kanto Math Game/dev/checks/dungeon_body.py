# Route dungeons (src/dungeon, src/states/overworld/dungeon.py): Route 1, Route 2 and Viridian Forest walked on a map.
import random as _rnd
from src.states.overworld import PlayState, AreaTransitionState
from src.states.overworld.dungeon import DungeonState
from src.dungeon import core
from src.pokemon import catching, tms
from src.states.battle import WildBattleState

fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


def talk(p, n=60):
    """Read the text box to the end."""
    for _ in range(n):
        if not p.dialogue_box.visible:
            return
        p.dialogue_box.advance()


def frames(p, n=1):
    for _ in range(n):
        g.current_state.update()
        g.current_state.draw()


def kanto(area, came="PALLET_TOWN"):
    story.current_area_key = area
    story.last_area_key = came
    story.player_team = [mk(4)]
    story.player_team[0].level = 12
    story.balls_left = 20
    p = PlayState(g)
    g.states["play"] = p
    g.change_state(p)
    return p


def beside(p, kind):
    """Put a mover of this kind right beside you (east), on a walkable tile."""
    f = p.run.floor
    m = next(x for x in f.movers if x.kind == kind)
    px, py = p.run.player
    for dx, dy in core.DIRS:
        t = (px + dx, py + dy)
        if f.walkable(*t) and not f.occupied(*t):
            m.x, m.y = t
            return m, (dx, dy)
    raise RuntimeError("no room")


# ---- headless default: the old route screen (the other suites keep working)
story.current_area_key = "KANTO_ROUTE_1"
check(type(PlayState(g)) is PlayState, "headless: PlayState stays the route menu unless dungeon_routes is on")
g.dungeon_routes = True

# ---- Route 1
p = kanto("KANTO_ROUTE_1")
check(isinstance(p, DungeonState), f"Route 1 is a dungeon ({type(p).__name__})")
f = p.run.floor
targets = sorted(f.exits.values())
check(targets == ["PALLET_TOWN", "VIRIDIAN_CITY"], f"Route 1 exits {targets}")
entry = [xy for xy, t in f.exits.items() if t == "PALLET_TOWN"][0]
check(abs(entry[0] - p.run.player[0]) + abs(entry[1] - p.run.player[1]) <= 12, "you start beside the way you came in")
check(sum(m.kind == "wild" for m in f.movers) >= 4, "wild Pokemon wander the floor")
check(sum(m.kind == "trainer" for m in f.movers) == 2, "Route 1's two trainers stand on the map")
check(p.uses_keyboard, "the map takes the arrow keys")
for _ in range(40):
    frames(p)
    p.step(*_rnd.choice(core.DIRS))
    for _ in range(core.Run.SIGHT):
        frames(p)
    if p.mode != "MAP":
        break
check(True, f"walked about (mode {p.mode}, turn {p.run.turn})")

# quick catch: MATH, right answer
p = kanto("KANTO_ROUTE_1")
m, d = beside(p, "wild")
p.step(*d)
check(p.mode == "CHOICE" and p.encounter is m, "bumping a wild Pokemon brings up MATH / BATTLE")
frames(p)
orig = catching.window_throw
catching.window_throw = lambda *a, **k: (True, 3, False)
balls = story.balls_left
party = len(story.player_team)
p._pick(0)
check(p.mode == "MATH" and len(p.options) == 3, f"MATH: {p.problem_str} {p.options}")
frames(p)
p._answer(p.options.index(p.correct_ans))
check(p.mode == "THROW" and story.balls_left == balls - 1, "a right answer throws a ball")
for _ in range(80):
    frames(p)
    if p.mode != "THROW":
        break
check(len(story.player_team) == party + 1, f"caught {m.payload.display_name} (party {len(story.player_team)})")
check(m not in p.run.floor.movers, "the caught Pokemon is gone from the map")
talk(p)
frames(p, 3)
check(g.current_state is p and p.mode == "MAP", f"back on the map ({type(g.current_state).__name__})")
catching.window_throw = orig

# quick catch: wrong answer -> it runs away
m, d = beside(p, "wild")
p.step(*d)
p._pick(0)
wrong = next(i for i, o in enumerate(p.options) if o != p.correct_ans)
party = len(story.player_team)
p._answer(wrong)
for _ in range(80):
    frames(p)
    if p.mode != "THROW":
        break
check(len(story.player_team) == party and m not in p.run.floor.movers, "a wrong answer: it runs away")
talk(p)

# BATTLE: the full battle, then back to the same walk
m, d = beside(p, "wild")
p.step(*d)
p._pick(1)
b = g.current_state
check(isinstance(b, WildBattleState), f"BATTLE opens the battle screen ({type(b).__name__})")
check(b.play_state_data.get("dungeon"), "the battle knows to come back to the map")
b.on_flee_complete()
check(g.current_state is p and p.mode == "MAP", f"fled: back to the same walk ({type(g.current_state).__name__})")
check(m not in p.run.floor.movers, "the wild Pokemon from the battle is gone")
frames(p, 3)

# trainers: bump -> trainer battle; beaten -> gone
t, d = beside(p, "trainer")
p.step(*d)
check(type(g.current_state).__name__ in ("TrainerIntroState", "TrainerBattleState", "BattleTransitionState"),
      f"bumping a trainer starts a trainer battle ({type(g.current_state).__name__})")
story.mark_trainer_defeated("KANTO_ROUTE_1", t.payload[0])
back = PlayState(g, restore_data={"rounds_completed": 1})
check(back is p and t not in p.run.floor.movers, "a beaten trainer is gone when you come back")
g.change_state(p)
# line of sight
t = next(x for x in p.run.floor.movers if x.kind == "trainer")
t.facing = (1, 0)
f = p.run.floor
spot = None
for y in range(f.h):
    for x in range(f.w - 3):
        if all(f.walkable(x + k, y) and not f.occupied(x + k, y) for k in range(4)):
            spot = (x, y)
            break
    if spot:
        break
t.x, t.y = spot
p.run.player = (spot[0] + 3, spot[1])
ev = p.run.others_act()
check(any(e[0] == "spotted" for e in ev), "walking into a trainer's line of sight: spotted")

# items and Honey
p = kanto("KANTO_ROUTE_1")
f = p.run.floor
f.movers.clear()  # (no wild Pokemon jumping in)
px, py = p.run.player
d = next(dd for dd in core.DIRS if f.walkable(px + dd[0], py + dd[1]) and not f.occupied(px + dd[0], py + dd[1]))
f.items[(px + d[0], py + d[1])] = "POTION"
had = story.inventory.get("POTION", 0)
p.step(*d)
check(story.inventory.get("POTION", 0) == had + 1, "walking over an item picks it up")
frames(p, 10)  # (the step's walk animation)
story.inventory["HONEY"] = 1
check(p._scent_source() == "HONEY" and not any(b[1] in ("HONEY", "SWEET SCENT") for b in p._buttons())
      and {"WAIT"} <= {b[1] for b in p._buttons()} and len(p._buttons()) >= 3, "HONEY in the Bag; the map's buttons: POKeMON, POKeDEX, WAIT")
from src.states.systems import BagState as _Bag
_bag = _Bag(g, p)
_bag._use_field_item("HONEY")  # used from the Bag: back to the map, and it draws them in
check(g.current_state is p, "HONEY from the Bag: back on the map")
talk(p)
frames(p, 3)
check(p.mode == "CATCH" and sum(x is not None for x in p.p_data) == 3,
      f"HONEY draws three wild Pokemon to catch ({[getattr(x, 'name', None) for x in p.p_data]})")
check(story.inventory.get("HONEY") == 0 and not p.uses_keyboard, "the Honey is used up; the catch screen takes the keys")
p.action_flee()
for _ in range(200):
    frames(p)
    talk(p, 2)
    if p.mode == "MAP":
        break
check(p.mode == "MAP" and g.current_state is p, "after the catch screen: back on the map")
p.scent_floor = -1
story.player_team[0].moves = ["SCRATCH", "SWEET-SCENT"]
check(p._scent_source() == "SWEET SCENT", "a Pokemon that knows Sweet Scent: once a floor")
p.scent_floor = p.run.index
check(p._scent_source() is None, "Sweet Scent used on this floor (and no Honey): nothing")

# leaving
p = kanto("KANTO_ROUTE_1")
f = p.run.floor
goal = [xy for xy, t in f.exits.items() if t == "VIRIDIAN_CITY"][0]
f.movers.clear()
for _ in range(400):
    if not isinstance(g.current_state, DungeonState):
        break
    f.movers.clear()  # (no wild Pokemon wandering in on the way)
    s = p.run.walk_toward(goal)
    p.anim = 0
    p.step(*s)
check(isinstance(g.current_state, AreaTransitionState), f"the far sign leads on ({type(g.current_state).__name__})")
for _ in range(400):
    g.current_state.update()
    if not isinstance(g.current_state, AreaTransitionState):
        break
    if getattr(g.current_state, "dialogue_box", None) and g.current_state.dialogue_box.visible:
        g.current_state.dialogue_box.is_finished = True
check(story.current_area_key == "VIRIDIAN_CITY" and story.last_area_key == "KANTO_ROUTE_1",
      f"now in {story.current_area_key}, came from {getattr(story, 'last_area_key', None)}")

# Route 2: entered from Viridian City, a TM spot
p = kanto("KANTO_ROUTE_2", came="VIRIDIAN_CITY")
check(isinstance(p, DungeonState), "Route 2 is a dungeon")
f = p.run.floor
check(len(f.tm_spots) == 1, f"Route 2 has its TM spot {list(f.tm_spots.values())}")
spot = list(f.tm_spots.values())[0]
f.tm_spots.clear()
px, py = p.run.player
d = next(dd for dd in core.DIRS if f.walkable(px + dd[0], py + dd[1]) and not f.occupied(px + dd[0], py + dd[1]))
f.tm_spots[(px + d[0], py + d[1])] = spot
owned = set(tms.owned(story))
p.step(*d)
got = story.story_flags.get(f"dungeon_tm_{spot}")
check(tms.is_tm(got) and got in tms.owned(story) and got not in owned, f"the TM spot gave {got}")
talk(p)
again = core.pick_tm(story.story_flags["dungeon_seed"], spot, tms.table(g), owned, 0)
check(again == got, "the same save picks the same TM there (no rerolls)")
p2 = kanto("KANTO_ROUTE_2", came="VIRIDIAN_CITY")
check(not p2.run.floor.tm_spots, "a taken TM spot stays taken")

# Viridian Forest: two floors
p = kanto("VIRIDIAN_FOREST", came="KANTO_ROUTE_2")
check(p.run.n_floors == 2 and core.STAIRS in p.run.floor.exits.values(), "Viridian Forest: stairs on the first floor")
p._descend()
check(p.run.index == 1 and "VIRIDIAN_CITY" in p.run.floor.exits.values(), "the second floor leads to Viridian City")
for mode in ("MAP", "CHOICE", "MATH", "THROW", "SPOTTED"):
    m = next((x for x in p.run.floor.movers if x.kind == ("trainer" if mode == "SPOTTED" else "wild")), None)
    p.encounter, p.mode = m, mode
    p.problem_str, p.correct_ans, p.options = p.generate_math_set(0, num_options=3)
    p.throw_result, p.throw_timer = "caught", 30
    try:
        p.draw()
        ok = True
    except Exception as e:
        ok = False
        print(e)
    check(ok, f"draws in {mode}")
p.mode = "MAP"

# the map replaces the route menu everywhere (Jordan, 11-05): no CLASSIC button
check(not any(b[1] == "CLASSIC" for b in p._buttons()), "no CLASSIC button: the map is the way")
story.current_area_key = "KANTO_ROUTE_1"
check(isinstance(PlayState(g), DungeonState) and type(PlayState(g, classic=True)) is PlayState,
      "PlayState(game) is the map; classic=True is the route menu underneath")

# ---- every Kanto area (Jordan, 11-05): routes, caves, the sea, the Safari Zone, the buildings
from src.states.overworld import dungeon as _dg
_prog = g.loader.area_data["STORY_PROGRESSION"]
_kanto = [k for k in _dg.recipes(g) if k in _prog and _prog[k].get("area_type") != "town"
          and k not in ("DEFAULT",) and not k.startswith("_")]
_bad = []
for _a in _kanto:
    try:
        _p = kanto(_a, came=next(iter([i.get("target") or i.get("target_area") for i in _prog[_a].get("route_menu", [])
                                       if i.get("action") in ("EXIT", "TRAVEL")] or [None])))
        if not isinstance(_p, DungeonState):
            _bad.append((_a, "not a map"))
            continue
        for _i in range(_p.run.n_floors):
            _f = _p.run.floor
            _reach = core.distances(_f, _p.run.player)
            _things = list(_f.exits) + list(_f.items) + list(_f.tm_spots) + ([] if _dg.recipe_for(g, _a).get("layout") else [(m.x, m.y) for m in _f.movers])
            if any(t not in _reach for t in _things):
                _bad.append((_a, _i, "something out of reach"))
            _p.draw()
            if _i < _p.run.n_floors - 1:
                _p._descend()
        for _i in range(_p.run.n_floors - 1):
            _p._ascend()
        if _p.run.index != 0:
            _bad.append((_a, "stairs back up"))
    except Exception as _e:
        import traceback
        traceback.print_exc()
        _bad.append((_a, repr(_e)))
check(not _bad, f"all {len(_kanto)} areas with their own recipe: a map, every floor crossable and drawn, stairs both ways {_bad[:4]}")
check({"MT_MOON", "ROCK_TUNNEL", "SEAFOAM_ISLANDS", "KANTO_POKEMON_TOWER", "POWER_PLANT", "KANTO_ROUTE_20",
       "SAFARI_ZONE", "KANTO_SS_ANNE", "CERULEAN_CAVE", "VICTORY_ROAD"} <= set(_kanto), "caves, the sea, the buildings too")

# every region's areas (the map replaces the route menu everywhere): each opens and draws, every way out,
# figure and item on its first floor can be reached
_all = [k for k, a in _prog.items() if isinstance(a, dict) and a.get("area_type") != "town"]
_bad = []
for _a in _all:
    try:
        story.badges.setdefault(str(_prog[_a].get("region") or "KANTO").upper(), [])
        _p = kanto(_a, came=None)
        if not isinstance(_p, DungeonState):
            _bad.append((_a, "not a map"))
            continue
        _f = _p.run.floor
        _reach = core.distances(_f, _p.run.player)
        _drawn = bool(_dg.recipe_for(g, _a).get("layout"))  # (a drawn place's clerk stands behind its counter)
        if any(t not in _reach for t in list(_f.exits) + ([] if _drawn else [(m.x, m.y) for m in _f.movers])):
            _bad.append((_a, "out of reach"))
        _p.draw()
    except Exception as _e:
        _bad.append((_a, repr(_e)[:80]))
check(not _bad, f"every region: all {len(_all)} areas that aren't towns are maps {_bad[:5]}")
_styles = {_dg.recipe_for(g, k).get("style") for k in _all}
check({"field", "forest", "cave", "building", "sea", "snow", "desert"} <= _styles, f"their looks from their battle types {sorted(_styles)}")

# zones: a floor each, the zone you're on is the one whose Pokemon you meet
_p = kanto("SEAFOAM_ISLANDS", came="KANTO_ROUTE_20")
check(_p.run.n_floors == 5 and story.story_flags.get("zone_SEAFOAM_ISLANDS") == "1f", "Seafoam: 1F to B4F, you start on 1F")
_p._descend()
check(story.story_flags.get("zone_SEAFOAM_ISLANDS") == "b1f" and _p._floor_name(1) == "B1F", "down the stairs: B1F's Pokemon")
_tower = kanto("KANTO_POKEMON_TOWER", came="LAVENDER_TOWN")
check(_tower.run.n_floors == 4 and "LAVENDER_TOWN" in _tower.run.floor.exits.values(), "the Pokemon Tower: four floors, the way out on 1F")

# figures: a legendary doesn't wait for the trainers; story people; the rival on arrival
for _k in ("POWER_PLANT_boss_defeated",):
    story.story_flags.pop(_k, None)
_pp = kanto("POWER_PLANT", came="KANTO_ROUTE_10")
_pp_trainers = [i for i in range(len(_prog["POWER_PLANT"].get("trainer_pool", []))) if not story.is_trainer_defeated("POWER_PLANT", i)]
_zap = [m for f in _pp.run.floors for m in f.movers if m.kind == "figure" and m.payload.get("action") == "BOSS"]
check(_zap and _pp_trainers, "Power Plant: Zapdos is on the map before its trainers are beaten")
check(_pp._figure_img(_zap[0].payload) is not None, "...drawn with its Journeys overworld sprite")
story.story_flags.pop("mt_moon_nerd_defeated", None)
_mm = kanto("MT_MOON", came="PEWTER_CITY")
_last = _mm.run.n_floors - 1
while _mm.run.index < _last:
    _mm._descend()
_nerd = [m for m in _mm.run.floor.movers if m.kind == "figure" and m.payload.get("text") == "SUPER NERD"]
check(_nerd, "Mt. Moon: the Super Nerd stands on the last floor")
_called = []
_mm._get_route_callback = lambda item: (lambda: _called.append(item.get("text")))
_nm, _d = beside(_mm, "figure") if _nerd else (None, None)
if _nm:
    _mm.mode, _mm.anim = "MAP", 0
    _mm.dialogue_box.visible = False
    _mm.step(*_d)
check(_called and _called[0] in ("SUPER NERD", "TAKE DOME FOSSIL", "TAKE HELIX FOSSIL"), "walking into a figure does its button's action")
story.story_flags["received_pokedex_kanto"] = True
_badges = story.badges.get("KANTO", [])
story.badges["KANTO"] = []
for _ev in (_prog["KANTO_ROUTE_22"].get("on_enter_event") or []):
    story.story_flags.pop(_ev.get("flag_check") or "", None)
_r22 = kanto("KANTO_ROUTE_22", came="VIRIDIAN_CITY")
check(any(m.kind == "figure" and m.payload.get("action") == "ARRIVAL" for f in _r22.run.floors for m in f.movers),
      "Route 22: the rival waits on the map")
story.badges["KANTO"] = _badges

# fishing beside a pond, Headbutt beside a tree
story.inventory["OLD_ROD"] = 1
_fish = kanto("KANTO_ROUTE_12", came="LAVENDER_TOWN")
_f = _fish.run.floor
_pond = next(((x, y) for y in range(_f.h) for x in range(_f.w) if _f.tiles[y][x] == core.WATER
              and any(_f.walkable(x + dx, y + dy) and not _f.occupied(x + dx, y + dy) for dx, dy in core.DIRS)), None)
check(_pond is not None, "Route 12 (fishing): ponds on the map")
if _pond:
    _spot = next((_pond[0] + dx, _pond[1] + dy) for dx, dy in core.DIRS
                 if _f.walkable(_pond[0] + dx, _pond[1] + dy) and not _f.occupied(_pond[0] + dx, _pond[1] + dy))
    _fish.run.player = _spot
    _act = _fish._act_here()
    check(_act and _act[0] == "FISH" and any(b[1] == "FISH" for b in _fish._buttons()), "beside the water: a FISH button")
    _fish.mode, _fish.anim = "MAP", 0
    _fish.dialogue_box.visible = False
    _fish.fish_here()
    check(isinstance(g.current_state, WildBattleState) or _fish.dialogue_box.visible, "FISH: a bite (the route's own fishing)")
_sea = kanto("KANTO_ROUTE_20", came="FUCHSIA_CITY")
check(_sea.run.floor.style == "sea" and _sea._beside("water") is not None, "at sea: you can fish anywhere")

# the buildings (Jordan, 11-05): Silph Co., the Rocket Hideout, the Pokemon Mansion
for _k in ("silph_co_cleared", "hideout_giovanni_defeated", "game_corner_cleared", "got_secret_key"):
    story.story_flags.pop(_k, None)
story.defeated_trainers.pop("SILPH_CITY", None)
_sil = kanto("SILPH_CITY", came="SAFFRON_CITY")
check(_sil.run.n_floors == 5 and _sil._floor_name(4) == "5F" and "SAFFRON_CITY" in _sil.run.floor.exits.values(),
      "Silph Co.: 1F (the way out) up to 5F")
check(any(m.kind == "figure" and m.payload.get("text") == "NURSE" for m in _sil.run.floor.movers), "a nurse on 1F")
while _sil.run.index < 4:
    _sil._descend()
check(any(m.kind == "trainer" and m.payload[1].get("name") == "Giovanni" for m in _sil.run.floor.movers),
      "Giovanni waits on 5F")
_hid = kanto("ROCKET_HIDEOUT", came="CELADON_CITY")
while _hid.run.index < 3:
    _hid._descend()
check(_hid._floor_name(3) == "B4F" and any(m.kind == "figure" and m.payload.get("text") == "GIOVANNI"
                                          for m in _hid.run.floor.movers), "the Rocket Hideout: Giovanni on B4F")
story.story_flags["hideout_giovanni_defeated"] = True
_hid._sync_figures()
check(any(m.payload.get("text") == "SILPH SCOPE" for m in _hid.run.floor.movers if m.kind == "figure")
      and not any(m.payload.get("text") == "GIOVANNI" for m in _hid.run.floor.movers if m.kind == "figure"),
      "...beaten: the Silph Scope lies there")
story.story_flags.pop("hideout_giovanni_defeated", None)
from src.states.systems.town_services import GameCornerState as _GC
story.current_area_key = "CELADON_CITY"
_gc = _GC(g, None)
_gc.start_rocket_gauntlet()
check(type(g.current_state).__name__ == "AreaTransitionState" and g.current_state.next_area_key == "ROCKET_HIDEOUT",
      "the Game Corner's stairs lead down into the hideout")
_man = kanto("POKEMON_MANSION", came="CINNABAR_ISLAND")
while _man.run.index < _man.run.n_floors - 1:
    _man._descend()
check(any(m.kind == "figure" and m.payload.get("text") == "BURGLAR SIMON" for m in _man.run.floor.movers)
      and any(m.kind == "wild" for f in _man.run.floors for m in f.movers), "the Pokemon Mansion: wild Pokemon, the Burglar with the Secret Key")
check(any(o.get("target_area") == "POKEMON_MANSION" for o in _prog["CINNABAR_ISLAND"]["explore_options"]),
      "Cinnabar's Pokemon Mansion button leads in")

# buildings are fixed and have no fog; the Game Corner is drawn (Jordan, 11-05)
_a1 = kanto("SILPH_CITY", came="SAFFRON_CITY")
_t1 = [row[:] for row in _a1.run.floor.tiles]
_a2 = kanto("SILPH_CITY", came="SAFFRON_CITY")
check(_a2.run.floor.tiles == _t1, "Silph Co.: the same floor on every visit")
check(len(_a2.run.floor.seen) == _a2.run.floor.w * _a2.run.floor.h and _a2.run.visible(1, 1), "...and no fog: the whole floor shows")
_r1 = kanto("KANTO_ROUTE_1", came="PALLET_TOWN")
check(_r1.run.fog and len(_r1.run.floor.seen) < _r1.run.floor.w * _r1.run.floor.h, "a route keeps its fog")
story.inventory["COIN_CASE"] = 1
_gc = kanto("CELADON_GAME_CORNER", came="CELADON_CITY")
_f = _gc.run.floor
check(_f.decor and sum(1 for v in _f.decor.values() if v == "slot") >= 12 and "ROCKET_HIDEOUT" in _f.exits.values()
      and "CELADON_CITY" in _f.exits.values(), "the Game Corner: drawn, slot machines, the door and the poster")
_clerk = [m for m in _f.movers if m.kind == "figure" and m.payload.get("text") == "CLERK"]
check(_clerk and _f.tile(_clerk[0].x, _clerk[0].y + 1) == core.WALL and _f.decor.get((_clerk[0].x, _clerk[0].y + 1)) == "counter",
      "the clerk stands behind the counter")
_counter = next(t for t, v in _f.decor.items() if v == "counter" and _f.walkable(t[0], t[1] + 1))
_gc.run.player = (_counter[0], _counter[1] + 1)
_gc.mode, _gc.anim = "MAP", 0
_gc.dialogue_box.visible = False
check(_gc._act_here() and _gc._act_here()[0] == "TALK", "at the counter: TALK")
_gc._act_here()[1]()
from src.states.systems import GameCornerState as _GCS
check(isinstance(g.current_state, _GCS) and g.current_state.previous_state is _gc, "the clerk: the Game Corner's games, coins and prizes")
g.current_state.go_back()
check(g.current_state is _gc, "LEAVE: back on the Game Corner's floor")
_slot = next(t for t, v in _f.decor.items() if v == "slot" and any(_f.walkable(t[0] + dx, t[1] + dy) for dx, dy in core.DIRS))
_gc.run.player = next((_slot[0] + dx, _slot[1] + dy) for dx, dy in core.DIRS if _f.walkable(_slot[0] + dx, _slot[1] + dy))
check(_gc._act_here() and _gc._act_here()[0] == "PLAY SLOTS", "at a machine: PLAY SLOTS")
_gc.draw()

# Sevii (Jordan, 11-05: each region's maps checked against its games)
_sty = {k: _dg.recipe_for(g, k).get("style") for k in ("KINDLE_ROAD", "RUIN_VALLEY", "TANOBY_RUINS", "TREASURE_BEACH",
                                                       "DOTTED_HOLE", "LOST_CAVE", "BIRTH_ISLAND")}
check(_sty == {"KINDLE_ROAD": "field", "RUIN_VALLEY": "mountain", "TANOBY_RUINS": "sea", "TREASURE_BEACH": "desert",
               "DOTTED_HOLE": "cave", "LOST_CAVE": "cave", "BIRTH_ISLAND": "field"}, f"Sevii's places look like the games' {_sty}")
story.story_flags["beat_champion"] = True
for _k in ("navel_rock_lugia", "navel_rock_ho_oh"):
    story.story_flags.pop(_k, None)
_nr = kanto("NAVEL_ROCK", came="ONE_ISLAND")
_where = {m.payload.get("text"): i for i, f in enumerate(_nr.run.floors) for m in f.movers if m.kind == "figure"}
while _nr.run.index < _nr.run.n_floors - 1:
    _nr._descend()
_where.update({m.payload.get("text"): _nr.run.index for m in _nr.run.floor.movers if m.kind == "figure"})
check(_nr.run.n_floors == 2 and _where.get("SEEK LUGIA") == 0 and _where.get("SEEK HO-OH") == 1,
      f"Navel Rock: Lugia below, Ho-Oh at the top {_where}")
_me = kanto("MT_EMBER", came="KINDLE_ROAD")
check(_me.run.n_floors == 3, "Mt. Ember: the base, Ruby Path, the summit")

# every region (Jordan, 11-05: each region's maps checked against its games)
_want = {"HAINA_DESERT": "desert", "DESERT_RESORT": "desert", "ASADO_DESERT": "desert", "GLASEADO_MOUNTAIN": "snow",
         "HOENN_TRACKLESS_FOREST": "forest", "PLEDGE_GROVE": "forest", "SPROUT_TOWER": "building", "MOUNT_LANAKILA": "snow"}
_got = {k: _dg.recipe_for(g, k).get("style") for k in _want}
check(_got == _want, f"each region's places look like its game's {[(k, v) for k, v in _got.items() if _want[k] != v]}")
_fl = {k: _dg.recipe_for(g, k).get("floors") for k in ("UNION_CAVE", "BELL_TOWER", "HOENN_SKY_PILLAR", "MT_CORONET_BASE", "CHARGESTONE_CAVE", "REFLECTION_CAVE")}
check(all((v or 1) > 1 for v in _fl.values()), f"the big dungeons have their floors {_fl}")
_bt = kanto("BELL_TOWER", came="ECRUTEAK_CITY")
check(_bt._figure_floor({"text": "TALK TO SAGE LI", "action": "NPC"}, 4) == 0 and _bt._figure_floor({"text": "CHALLENGE HO-OH", "action": "BOSS"}, 4) == 3,
      "Bell Tower: the sage at the entrance, Ho-Oh at the top")

# the Johto Safari Zone: three areas side by side on each of 4 wide floors (Jordan, 11-05)
_jz = _prog["JOHTO_SAFARI_ZONE"]
_js = kanto("JOHTO_SAFARI_ZONE", came=next((i.get("target") or i.get("target_area") for i in _jz.get("route_menu", []) if i.get("action") in ("EXIT", "TRAVEL")), None))
_keys = [z["key"] for z in _jz["zones"]]
check(_js.run.n_floors == 4 and _js.run.floor.w == 3 * 36, f"12 areas on 4 floors, each 3x as wide ({_js.run.n_floors}, {_js.run.floor.w})")
_flag = "zone_JOHTO_SAFARI_ZONE"
_seen57 = []
for _x in (5, 50, 100):
    _js.run.player = (_x, _js.run.player[1])
    _js._note_area()
    _seen57.append(story.story_flags.get(_flag))
check(_seen57 == _keys[:3], f"crossing the gate lines: each part is its area {_seen57}")
check(_js.toast.startswith("You entered"), "...and it says which area you entered")
_js.draw()
_js._descend()
check(_js._floor_name(1) == " / ".join(_js._zone_name(i) for i in (3, 4, 5)), "the next floor: the next three areas")

# the Bug-Catching Contest (Jordan, 11-05): National Park, its own map
check(_dg.CONTEST_DAYS == tuple(range(7)), "the contest is open any day (once a day)")
story.story_flags.pop("bug_contest_day", None)
_np = kanto("NATIONAL_PARK", came="JOHTO_ROUTE_35")
_off = [m for m in _np.run.floor.movers if m.kind == "figure" and m.payload.get("action") == "BUG_CONTEST"]
check(_off, "National Park: the contest officer stands on the map")
_dg.contest_entry(_np)
talk(_np)
for _ in range(400):
    g.current_state.update()
    if isinstance(g.current_state, DungeonState):
        break
_bc = g.current_state
check(isinstance(_bc, DungeonState) and _bc.area_key == "BUG_CONTEST" and _bc.contest and _bc.contest["balls"] == 20,
      "the officer: the contest's map, 20 Sport Balls")
_bugs = {int(k) for k in g.loader.area_data["JOHTO_BUG_CONTEST_PERCENTAGES"]}
_wild = [m for m in _bc.run.floor.movers if m.kind == "wild"]
check(_wild and all(m.payload.id in _bugs or str(m.payload.id).startswith(tuple(str(b) for b in _bugs)) for m in _wild),
      f"only Bug Pokemon roam it ({sorted({m.payload.id for m in _wild})})")
_bc.draw()
_m = _wild[0]
_bc._meet_wild(_m)
_bc._pick(1)
check(_bc.mode == "CHOICE", "no BATTLE in the contest (MATH only)")
_bc._start_math()
_bc._answer(_bc.options.index(_bc.correct_ans))
check(_bc.contest["balls"] == 19, "a throw uses a Sport Ball (not your own)")
_bc.throw_result = "caught"
_bc._resolve_throw()
talk(_bc)
check(_bc.contest["best"] is _m.payload, "the catch is your contest Pokemon")
_team = len(story.player_team) + len([x for x in story.pc_pokemon if x])
_bc.mode, _bc.anim = "MAP", 0
_bc.contest["turns"] = 0
_bc._contest_check()
_lines = list(_bc.dialogue_box.text_lines)
check(any("scored" in l for l in _lines) and any("yours to keep" in l for l in _lines), f"time's up: the judging {_lines[:3]}")
check(len(story.player_team) + len([x for x in story.pc_pokemon if x]) == _team + 1, "you keep your bug")
talk(_bc)
for _ in range(400):
    g.current_state.update()
    if isinstance(g.current_state, DungeonState) and g.current_state is not _bc:
        break
check(story.current_area_key == "NATIONAL_PARK", "...and you're back in National Park")
_np2 = kanto("NATIONAL_PARK", came="JOHTO_ROUTE_35")
_dg.contest_entry(_np2)
check(any("already" in l for l in _np2.dialogue_box.text_lines), "once a day")
for _k, _n, _w in (("SAFARI_ZONE", 1, 4), ("HOENN_SAFARI_ZONE", 1, 4), ("GREAT_MARSH", 2, 3)):
    _sz = kanto(_k, came=next((i.get("target") or i.get("target_area") for i in _prog[_k].get("route_menu", []) if i.get("action") in ("EXIT", "TRAVEL")), None))
    check(_sz.run.n_floors == _n and _sz.run.floor.w == _w * 36, f"{_k}: like Johto's, {_n} floor(s) of {_w} areas side by side")
    _sz.draw()

# free movement (Jordan, 11-05): no "two route actions" before a way out; only the story locks one
_r3 = kanto("KANTO_ROUTE_3", came="PEWTER_CITY")
check(_r3.rounds_completed == 0 and _r3._exit_block(_r3.exit_items["MT_MOON_CITY"], True) == "route", "Route 3, nothing done yet")
_r3._try_exit("MT_MOON_CITY")
check(type(g.current_state).__name__ == "AreaTransitionState", "...and you can walk straight on to Mt. Moon")
_kb = story.badges.get("KANTO", [])
story.badges["KANTO"] = []
_r22b = kanto("KANTO_ROUTE_22", came="VIRIDIAN_CITY")
_r22b._try_exit("KANTO_ROUTE_23")
check(g.current_state is _r22b and _r22b.dialogue_box.visible, "a story lock still holds (Route 23 needs the eight badges)")
story.badges["KANTO"] = _kb

print(f"##### {fails} failures")
