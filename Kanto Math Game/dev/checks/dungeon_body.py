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
targets = sorted(set(f.exits.values()))  # (our own map, Jordan 11-07: a road's width of tiles each way)
check(targets == ["PALLET_TOWN", "VIRIDIAN_CITY"], f"Route 1 exits {targets}")
entry = [xy for xy, t in f.exits.items() if t == "PALLET_TOWN"][0]
check(abs(entry[0] - p.run.player[0]) + abs(entry[1] - p.run.player[1]) <= 12, "you start beside the way you came in")
check(sum(m.kind == "wild" for m in f.movers) >= 4, "wild Pokemon wander the floor")
check(sum(m.kind == "trainer" for m in f.movers) == 0, "Route 1: no trainers (as in the games)")
check(any(m.kind == "figure" and m.payload.get("text") == "POKE MART CLERK" for m in f.movers),
      "...the Poke Mart clerk stands there (a free Potion)")
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
m.payload.is_shiny = False  # (a shiny is caught even on a wrong answer: not what this checks)
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

# trainers: bump -> trainer battle; beaten -> gone (Route 3's: Route 1 has none)
p = kanto("KANTO_ROUTE_3", came="PEWTER_CITY")
t, d = beside(p, "trainer")
p.step(*d)
check(type(g.current_state).__name__ in ("TrainerIntroState", "TrainerBattleState", "BattleTransitionState"),
      f"bumping a trainer starts a trainer battle ({type(g.current_state).__name__})")
story.mark_trainer_defeated("KANTO_ROUTE_3", t.payload[0])
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
check(p._scent_source() == "HONEY" and {"HONEY", "WAIT"} <= {b[1] for b in p._buttons()}
      and next(b for b in p._buttons() if b[1] == "HONEY")[4] and len(p._buttons()) >= 4,
      "HONEY in the Bag; the map's buttons: POKeMON, POKeDEX, HONEY (Jordan, 11-06: back), WAIT")
check(p.HONEY_PACK in [k for f in p.run.floors for k in f.items.values()] or
      any(p.HONEY_PACK in str(v) for f in p.run.floors for v in f.items.values()) or not p._get_wild_pool(p.area_data),
      "3 HONEY lying on the floor (where wild Pokemon live)")
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

# Viridian Forest: laid out from FireRed's own map (11-11), one floor; both its gates open onto Route 2, which runs on south to Viridian
p = kanto("VIRIDIAN_FOREST", came="KANTO_ROUTE_2")
check(p.run.n_floors == 1 and {"KANTO_ROUTE_2"} == set(p.run.floor.exits.values()),
      "Viridian Forest: one open map, out to Route 2 by its north gate and its south gate")
check(sum(m.kind == "trainer" for m in p.run.floor.movers) == 5, "...its five Bug Catchers (and the school kids)")
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


def _reach_of(f, start):
    """Where you can get to from start, a boulder counting as pushed aside (Strength and the slide puzzle), a cracked rock as broken (Rock Smash), a waterfall as climbed and a rock wall as scaled (Waterfall, Rock Climb), a ledge as hopped over (one way: near enough for this)."""
    held = {t: f.tiles[t[1]][t[0]] for t, v in f.decor.items() if str(v).startswith(("boulder:", "whirl:", "ledge:", "crack:", "falls:", "climb:", "cut:", "slope:"))}
    for (x, y) in held:
        f.tiles[y][x] = core.FLOOR
    try:
        return core.distances(f, start)
    finally:
        for (x, y), v in held.items():
            f.tiles[y][x] = v


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
        while _p.run.index > 0:  # (a cave entered partway down, Cerulean Cave's 1F: from its top floor)
            _p._ascend()
        _art_floors = ((_dg.recipe_for(g, _a).get("art") or {}).get("floors") or [])
        for _i in range(_p.run.n_floors):
            _f = _p.run.floor
            _reach = _reach_of(_f, _p.run.player)
            if (_i < len(_art_floors) and _art_floors[_i].get("parts")) or (_dg.recipe_for(g, _a).get("art") or {}).get("parts"):  # (in parts: each from its own ladder)
                for _t in list(_f.exits):
                    _reach = {**_reach, **_reach_of(_f, _t)}
            _things = list(_f.exits) + list(_f.items) + list(_f.tm_spots) + ([] if _dg.recipe_for(g, _a).get("layout") else [(m.x, m.y) for m in _f.movers])
            if any(t not in _reach for t in _things):
                _bad.append((_a, _i, "something out of reach", [(t, _f.exits.get(t), _f.items.get(t)) for t in _things if t not in _reach][:6]))
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
        _reach = _reach_of(_f, _p.run.player)
        _af = ((_dg.recipe_for(g, _a).get("art") or {}).get("floors") or [])
        if (_af and _af[_p.run.index].get("parts")) or (_dg.recipe_for(g, _a).get("art") or {}).get("parts"):  # (in parts, Rock Tunnel's 1F: each from its own ladder; Route 42: each from its own way out)
            for _t in list(_f.exits):
                _reach = {**_reach, **_reach_of(_f, _t)}
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
_pond = next(((x, y) for y in range(_f.h) for x in range(_f.w) if _f.tiles[y][x] in (core.WATER, core.SURF)
              and any(_f.walkable(x + dx, y + dy) and _f.tiles[y + dy][x + dx] == core.FLOOR and not _f.occupied(x + dx, y + dy) for dx, dy in core.DIRS)), None)
check(_pond is not None, "Route 12 (fishing): the sea beside its piers (11-11: FireRed's Silence Bridge)")
if _pond:
    _spot = next((_pond[0] + dx, _pond[1] + dy) for dx, dy in core.DIRS
                 if _f.walkable(_pond[0] + dx, _pond[1] + dy) and _f.tiles[_pond[1] + dy][_pond[0] + dx] == core.FLOOR and not _f.occupied(_pond[0] + dx, _pond[1] + dy))
    _fish.run.player = _spot
    _act = _fish._act_here()
    check(_act and _act[0] == "FISH" and any(b[1] == "FISH" for b in _fish._buttons()), "beside the water: a FISH button")
    _fish.mode, _fish.anim = "MAP", 0
    _fish.dialogue_box.visible = False
    _fish.fish_here()
    check(isinstance(g.current_state, WildBattleState) or _fish.dialogue_box.visible, "FISH: a bite (the route's own fishing)")
_sea = kanto("KANTO_ROUTE_20", came="KANTO_ROUTE_19")
check(_sea._on_surf() and _sea._beside("water") is not None, "at sea (surfing Route 20): you can fish anywhere")

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
_hid = kanto("ROCKET_HIDEOUT", came="CELADON_GAME_CORNER")
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
_man._warp(2, 8, 3)  # (11-12: FireRed's four floors; he stands on 3F, where FireRed has him)
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
_r1 = kanto("GALAR_ROUTE_2", came="GALAR_ROUTE_1")  # (a made-up route map: our own ones are open; Route 48 was the example till it got its SoulSilver map)
check(_r1.run.fog and len(_r1.run.floor.seen) < _r1.run.floor.w * _r1.run.floor.h, "a route keeps its fog")
story.inventory["COIN_CASE"] = 1
story.story_flags["game_corner_poster"] = True  # (the switch behind the poster pushed: the stairs are open; the guard and the switch: frlg_body)
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
check(set(_sty.values()) == {"field"},  # (every Sevii place is our own drawn map now, laid out from FireRed's map data, 11-11: a drawn map's recipe is a "field"; its look is its theme)
      f"Sevii's places are drawn maps of their own {_sty}")
story.story_flags["beat_champion"] = True
for _k in ("navel_rock_lugia", "navel_rock_ho_oh"):
    story.story_flags.pop(_k, None)
_nr = kanto("NAVEL_ROCK", came="ONE_ISLAND")
_where = {t: i for i in range(_nr.run.n_floors) for t in _nr.run.made(i).spots}
check(_nr.run.n_floors == 21 and _where.get("SEEK LUGIA") == 20 and _where.get("SEEK HO-OH") == 8,  # (FireRed's own floors, 11-11: the island, the cave, the fork, the long stairs, 4 flights up to the summit, 11 down to the base)
      f"Navel Rock: FireRed's 21 floors; Ho-Oh on the summit, Lugia in the base {_where}")
_me = kanto("MT_EMBER", came="KINDLE_ROAD")
check(_me.run.n_floors == 13, "Mt. Ember: FireRed's 13 floors: the mountain, the Summit Path's three, the summit, the Ruby Path's eight")

# every region (Jordan, 11-05: each region's maps checked against its games)
_want = {"HAINA_DESERT": "desert", "DESERT_RESORT": "desert", "ASADO_DESERT": "desert", "GLASEADO_MOUNTAIN": "snow",
         "HOENN_TRACKLESS_FOREST": "forest", "PLEDGE_GROVE": "forest", "SPROUT_TOWER": "field", "MOUNT_LANAKILA": "snow"}  # (Sprout Tower: our own exact floors now)
_got = {k: _dg.recipe_for(g, k).get("style") for k in _want}
check(_got == _want, f"each region's places look like its game's {[(k, v) for k, v in _got.items() if _want[k] != v]}")
_fl = {k: _dg.recipe_for(g, k).get("floors") for k in ("UNION_CAVE", "BELL_TOWER", "HOENN_SKY_PILLAR", "MT_CORONET_BASE", "CHARGESTONE_CAVE", "REFLECTION_CAVE")}
check(all((v or 1) > 1 for v in _fl.values()), f"the big dungeons have their floors {_fl}")
_bt = kanto("BELL_TOWER", came="ECRUTEAK_CITY")
check(_bt.run.n_floors == 11 and _bt._figure_floor({"text": "TALK TO SAGE LI", "action": "NPC"}, 11) == 0 and _bt._figure_floor({"text": "CHALLENGE HO-OH", "action": "BOSS"}, 11) == 10,
      "Bell Tower: SoulSilver's ten floors and roof; the sage at the entrance, Ho-Oh on the roof")

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
for _k, _n, _w in (("HOENN_SAFARI_ZONE", 1, 4),):  # (the Great Marsh has its own real map now: dev/checks/sinnoh_body.py)
    _sz = kanto(_k, came=next((i.get("target") or i.get("target_area") for i in _prog[_k].get("route_menu", []) if i.get("action") in ("EXIT", "TRAVEL")), None))
    check(_sz.run.n_floors == _n and _sz.run.floor.w == _w * 36, f"{_k}: like Johto's, {_n} floor(s) of {_w} areas side by side")
    _sz.draw()

# free movement (Jordan, 11-05): no "two route actions" before a way out; only the story locks one
_r3 = kanto("KANTO_ROUTE_3", came="PEWTER_CITY")
check(_r3.rounds_completed == 0 and _r3._exit_block(_r3.exit_items["MT_MOON"], True) == "route", "Route 3, nothing done yet")
_r3._try_exit("MT_MOON")  # (straight into the cave now: its Pokemon Center is on Route 3, Jordan 11-07)
check(type(g.current_state).__name__ == "AreaTransitionState", "...and you can walk straight on to Mt. Moon")
_kb = story.badges.get("KANTO", [])
story.badges["KANTO"] = []
_r22b = kanto("KANTO_ROUTE_22", came="VIRIDIAN_CITY")
_r22b._try_exit("KANTO_ROUTE_23")
check(g.current_state is _r22b and _r22b.dialogue_box.visible, "a story lock still holds (Route 23 needs the eight badges)")
story.badges["KANTO"] = _kb

# Story gates on the map (Jordan, 11-06): what's in the way stands on the locked way out
_inv = dict(story.inventory)
story.inventory.pop("POKE_FLUTE", None)
_r12 = kanto("KANTO_ROUTE_12", came="LAVENDER_TOWN")
check(_r12._boss_spot() == (14, 70) and _r12.run.floor.exits.get((14, 70)) == "BOSS" and not any(
    m.kind == "figure" and m.payload.get("action") == "BOSS" for f in _r12.run.floors for m in f.movers),
      "Route 12: Snorlax asleep on the pier where FireRed has him, in the way south and west (11-11; not a figure somewhere else on the map)")
_r12._try_exit("BOSS")
check(_r12.dialogue_box.visible and "asleep" in " ".join(_r12.dialogue_box.text_lines), "walking into it: it's sound asleep")
frames(_r12, 2)
story.player_team = [mk(4)]
story.current_area_key = "HOENN_RUSTURF_TUNNEL"
story.inventory.pop("HM_ROCK_SMASH", None)
_rt = PlayState(g); g.change_state(_rt)
check(_rt._gate("VERDANTURF_TOWN")[:3] == ("rock", "ROCK SMASH", False), "Rusturf Tunnel: a cracked rock before Verdanturf")
_rt.draw()
story.inventory["HM_ROCK_SMASH"] = 1
check(_rt._gate("VERDANTURF_TOWN")[2], "...gone once you have HM Rock Smash")
story.inventory.clear(); story.inventory.update(_inv)

# Overworld Pokemon (Everlasting X's following Pokemon): your partner and the wild ones walk on the map
_p = kanto("KANTO_ROUTE_1")
_img = _p._follower_img(story.player_team[0], (0, 1))
check(_img is not None and _img.get_height() >= 40, "the partner's overworld sprite, at the trainer's scale")

# Hyperspace Lumiose (Jordan, 11-06): a donut opens a zone; big open floors, a clock
from src.world import donuts as _dn
_d = _dn.bake(["PECHA_BERRY"] * 3)
check(_d["recipe"] == "perfect" and _d["stars"] == 1 and _dn.zone_for(g, _d) == "HYPERSPACE_VERDANT",
      "a Perfect Sweet donut (1 star) opens the Verdant Rift")
_r = _dn.bake(["CHERI_BERRY", "PECHA_BERRY", "ASPEAR_BERRY"])
check(_r["recipe"] == "rainbow" and _r["bonus_seconds"] == 30, "a Rainbow donut: 30 more seconds a floor")
check(_dn.zone_for(g, _dn.bake(["CHESTO_BERRY"] * 3)) is None and
      _dn.zone_for(g, _dn.bake(["CHESTO_BERRY", "NANAB_BERRY", "CHESTO_BERRY"], burnt=False) | {"stars": 2}) == "HYPERSPACE_FROST",
      "the Frost Rift needs 2 stars (star berries)")
story.player_team = [mk(4)]
story.player_team[0].level = 10  # (under the level cap: the win's XP shows)
story.story_flags[_dn.FLAG] = _d
story.current_area_key = "HYPERSPACE_VERDANT"
_h = PlayState(g); g.change_state(_h)
check(type(_h).__name__ == "HyperspaceState" and _h.run.fog is False and _h.run.floor.w >= 40
      and _h._enemies() and story.story_flags.get(_dn.FLAG) is None, "into the Verdant Rift: big, open, the donut eaten")
check(_h._stairs_blocked(), "the stairs wait until the floor is clear")
_w = next(m for m in _h.run.floor.movers if m.kind == "wild")
_h._meet_wild(_w)
check(_h.mode == "CHOICE", "a wild one: the usual catch-or-battle choice (battles are turn-based, Jordan 11-07)")
_h.mode, _h.encounter = "MAP", None
_h.clock = 1
_h.update()
check(_h.dialogue_box.visible, "the clock runs out: back to the hub")


def fight(b, n=8000):
    """Play a turn-based battle as a player would: each turn the first move and the right answer; tap through
    its text. Returns how many math questions were answered."""
    asked = 0
    for _k in range(n):
        if g.current_state is not b:
            break
        if b.phase == "SWITCH_PROMPT" and b.btn_no.visible and b.btn_no.callback:
            b.btn_no.callback()  # ("Change Pokemon?" NO, as a player would)
        elif b.phase == "MENU" and not b.dialogue_box.visible:
            b.open_move_menu()
            b.choose_move(b.move_buttons[0].text.replace(" ", "-"))
            b.math_ui.on_click(b.options.index(b.correct_ans))
            asked += 1
        elif b.dialogue_box.visible:
            b.dialogue_box.is_finished = True
            if b.phase in ("OUTRO", "VICTORY_TEXT", "REWARD_TEXT"):
                b.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
            else:
                _cb = b.dialogue_box.callback
                if _cb:
                    b.dialogue_box.callback = None
                    _cb()
                else:
                    b.dialogue_box.advance()
        b.feedback_timer = 0
        if g.current_state is b:
            b.update()
            b.draw()
    return asked


# Options > BATTLE STYLE (Jordan, 11-07): CLASSIC or OVERWORLD, trainer battles only; the same turns and math
from src.states.battle import TrainerBattleState, TrainerIntroState, WildBattleState
story.battle_style = "TRADITIONAL"
_p = kanto("KANTO_ROUTE_3", came="PEWTER_CITY")
_t = next((m for f in _p.run.floors for m in f.movers if m.kind == "trainer"), None)
_p._battle_trainer(_t)
check(isinstance(g.current_state, TrainerIntroState), "CLASSIC: a trainer battle on the battle screen (its intro first)")
story.battle_style = "OVERWORLD"
_p = kanto("KANTO_ROUTE_3", came="PEWTER_CITY")
_ow = mk(6)  # (a sure win: a Lv 100 Charizard; two Lv 2s keep the team's level, which foes follow, near 51)
_ow.level = 100
_ow.moves = ["FLAMETHROWER", "AIR-SLASH"]
_ow.heal_full()
story.player_team = [_ow, mk(132), mk(128)]  # (Ditto, Tauros: their shared XP starts no evolution)
for _pp in story.player_team[1:]:
    _pp.level = 2
    _pp.heal_full()
_t = next((m for f in _p.run.floors for m in f.movers if m.kind == "trainer"), None)
_money = story.money
from src.pokemon import items as _it
from src.states.overworld.route_encounters import _story_badges
_prize = _it.trainer_prize(_story_badges(g))
_inv0, _bl = {k: story.inventory.get(k, 0) for k in _prize}, story.balls_left
_p._battle_trainer(_t)
check(_p.dialogue_box.visible and g.current_state is _p, "OVERWORLD: the trainer's lines first, in the map's text box")
while _p.dialogue_box.visible:
    _p.dialogue_box.advance()
    _p.update()
_b = g.current_state
check(isinstance(_b, TrainerBattleState) and getattr(_b, "overworld", None) is not None,
      "...then the turn-based battle, drawn on the map")
_ov = _b.overworld
check(_ov.spot != _ov.mine and _p.run.player not in (_ov.spot, _ov.mine) and (_t.x, _t.y) not in (_ov.spot, _ov.mine),
      "...the two Pokemon on their own tiles (no one standing on anyone)")
_asked = fight(_b)
check(_asked >= 1 and g.current_state is _p and story.is_trainer_defeated("KANTO_ROUTE_3", _t.payload[0])
      and story.money > _money, f"...a math question every turn ({_asked}), won: back on the map, the trainer beaten, paid")
check(all(story.inventory.get(k, 0) == _inv0[k] + n for k, n in _prize.items()) and story.balls_left == _bl,
      f"...a route trainer's prize: healing items ({_prize}), no Poke Balls")
check(_it.route_rewards(1, {"balls": 3}) == {"POTION": 2, "balls": 0}
      and _it.route_rewards(3, None) == {"POTION": 1, "SUPER_POTION": 1, "balls": 0}
      and _it.route_rewards(5, {"balls": 2, "TM_X": 1}) == {"TM_X": 1, "SUPER_POTION": 2, "REVIVE": 1, "balls": 0}
      and _it.route_rewards(8, {}) == {"HYPER_POTION": 2, "REVIVE": 1, "balls": 0}
      and not any("MAX_REVIVE" in _it.route_rewards(b, {}) for b in range(9)),
      "prizes grow with the badges: Potions, Super Potions and Revives, Hyper Potions (never a Max Revive)")
_p = kanto("KANTO_ROUTE_1")
_ww, _ = beside(_p, "wild")
_p._meet_wild(_ww)
check(_p.mode == "CHOICE", "OVERWORLD: a wild one is still the catch-or-battle choice")
_p._pick(1)
check(isinstance(g.current_state, WildBattleState) and getattr(g.current_state, "overworld", None) is not None,
      "...and its battle is on the map too")
story.battle_style = "TRADITIONAL"

# Mega Evolution on the map (Legends: Z-A): a minute of walking, into battles that way, then the Key Stone rests
from src.pokemon import mega_clock, forms as _forms
from src.states.systems import PokemonPartyMenuState
_p = kanto("KANTO_ROUTE_3", came="PEWTER_CITY")
story.player_team = [mk(3)]
_v = story.player_team[0]
_v.level = 60
_v.moves = ["PETAL-BLIZZARD", "SLUDGE-BOMB"]
_v.heal_full()
story.inventory["MEGA_BRACELET"] = story.inventory["VENUSAURITE"] = 1
_img0 = _v.image
g.rt_mega = None
_mb = _p._map_mega_button()
check(_mb is not None and _mb[4] and _mb in _p._buttons(), "on the map: MEGA (the Venusaur following you can)")
_p.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=_mb[0].center)])
check(_v.form == "mega" and mega_clock.active(g), "...tapped: it Mega Evolves right there")
_mb = _p._map_mega_button()
check(_mb is not None and not _mb[4] and "left" in _mb[5], f"...the button counts its minute down ({_mb and _mb[5]})")
_party = PokemonPartyMenuState(g, _p, context="normal")
g.change_state(_party)
_party.update(); _party.draw()
check(_v.image is not _img0 and _v.display_name.upper().startswith("MEGA"), "the party menu shows the Mega")
g.change_state(_p)
_t = next((m for f in _p.run.floors for m in f.movers if m.kind == "trainer"), None)
_p._battle_trainer(_t)  # (CLASSIC)
_intro = g.current_state
_b = _intro.next_state
check(_b.mega_used["player"], "a battle: it comes in a Mega (that's the battle's one Mega)")
g.change_state(_b)
_left = mega_clock.state(g)["left"]
for _k in range(60):
    mega_clock.tick(g)
check(mega_clock.state(g)["left"] == _left, "...its minute waits while you battle")
fight(_b)
check(g.current_state is _p and _v.form == "mega" and mega_clock.active(g), "the battle won: still a Mega on the map")
for _k in range(mega_clock.SECONDS * 25):
    mega_clock.tick(g)
check(_v.form == "normal" and mega_clock.cooling(g), "a minute on: back to normal, the Key Stone resting")
check(story._pokemon_record(_v)["form"] == "normal", "(saved as its normal form)")
for _k in range(mega_clock.COOLDOWN * 25 + 2):
    mega_clock.tick(g)
check(not mega_clock.cooling(g), "30 seconds on: MEGA is ready again")
g.rt_mega = None
story.player_team = [mk(25), _v]
check(_p._map_mega_button() is None, "a Pokemon with no Mega Stone following you: no MEGA button")
# the POKEMON list on the map: tap one to have it follow you; right-click (or its potion) heals it, strongest first
_p.qp_open = True
_pk = story.player_team[1]
_p.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=_p._qp_rects()[1].center)])
check(story.player_team[0] is _pk and _p.lead() is _pk and not _p.qp_open, "on the map: tap one, it follows you")
story.inventory.update({"POTION": 3, "HYPER_POTION": 1})
_pk.current_hp = 5
_p.qp_open = True
_p.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=3, pos=_p._qp_rects()[0].center)])
check(story.inventory.get("HYPER_POTION", 0) == 0 and story.inventory.get("POTION") == 3 and _pk.current_hp > 5,
      "right-click: healed with the strongest potion (the Hyper Potion)")
_pk.current_hp = 5
_p.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=_p._qp_heal_rect(_p._qp_rects()[0]).center)])
check(story.inventory.get("POTION") == 2 and _pk.current_hp > 5, "...or tap its potion (now a Potion)")
story.player_team[1].current_hp = 0
story.inventory["REVIVE"] = 1
_p._quick_heal(1)
check(story.player_team[1].current_hp > 0 and not story.inventory.get("REVIVE"), "a fainted one: a Revive")
_p.qp_open = False
story.inventory.pop("VENUSAURITE", None); story.inventory.pop("MEGA_BRACELET", None)
story.battle_style = "TRADITIONAL"

# playtest fixes (Jordan, 11-07): a story battle on the map brings you back where you were
story.story_flags.pop("mt_moon_nerd_defeated", None)
_mm = kanto("MT_MOON", came="KANTO_ROUTE_3")
story.player_team[0].level = 40
while _mm.run.index < _mm.run.n_floors - 1:
    _mm._descend()
_nerd = next(m for m in _mm.run.floor.movers if m.kind == "figure" and m.payload.get("text") == "SUPER NERD")
_mm.run.player = _spot = (_nerd.x, _nerd.y - 1)
_mm._get_route_callback(_nerd.payload)()
_b = g.current_state.next_state
_b.player_won = True
_b.exit_battle()
check(g.current_state is _mm and _mm.run.index == _mm.run.n_floors - 1 and _mm.run.player == _spot,
      "the Super Nerd beaten: back where you were (not Mt. Moon's entrance)")
_fos = sorted(m.payload.get("text") for m in _mm.run.floor.movers if m.kind == "figure")
check(_fos == ["TAKE DOME FOSSIL", "TAKE HELIX FOSSIL"]
      and max(abs(a.x - b.x) + abs(a.y - b.y) for a in _mm.run.floor.movers for b in _mm.run.floor.movers
              if a.kind == b.kind == "figure") <= 4, "...the two fossils side by side to pick from")
story.story_flags.pop("defeated_rival_nugget_bridge", None)
_bd = dict(story.badges)
story.badges["KANTO"] = ["BOULDER"]
_r24 = kanto("KANTO_ROUTE_24", came="CERULEAN_CITY")
_riv = next(m for f in _r24.run.floors for m in f.movers if m.kind == "figure" and m.payload.get("action") == "ARRIVAL")
_r24._use_figure(_riv)
_b = g.current_state.next_state
check(_b.background is not None, "the rival after Nugget Bridge: a battle background")
_b.player_won = True
_b.exit_battle()
check(g.current_state is _r24, "...and back on Route 24 where you were")
story.badges.clear(); story.badges.update(_bd)
_p = kanto("KANTO_ROUTE_3", came="PEWTER_CITY")
story.tracked_mission = None
check(_p._journal_rect() is not None and _p._minimap_rect().y > _p._journal_rect().bottom,
      "the Journal's mission stays on screen under MENU (the mini-map under it)")

# walkable towns (Jordan, 11-06): the town on its Pokemon Journeys map, walked like a route
from src.states.overworld import CityState as _CS
from src.states.overworld.walk_town import WalkTownState as _WTS
g.walk_towns = True
g.walk_town_pos = None
story.story_flags["received_starter_kanto"] = True
story.story_flags["move_offer_kanto"] = True  # (the suites' save is Kanto's Champion: no move offer here)
story.current_area_key, story.last_area_key = "PALLET_TOWN", "KANTO_ROUTE_1"
_wt = _CS(g); g.change_state(_wt)


def _tap_through(st, n=400):
    """Tap through whatever the town says first (a call, a milestone), as a player would."""
    for _ in range(n):
        if not st.npc_active:
            return
        st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        frames(st)


_tap_through(_wt)
check(isinstance(_wt, _WTS) and _wt.player[1] <= 2, f"Pallet Town: walked, in from Route 1 at the top ({_wt.player})")
_lab = next(t for t, k in _wt.doors.items() if k == "lab")
_wt.walk_goal = _lab
for _k in range(300):
    frames(_wt)
    if _wt.hover_menu_active or _wt.room:
        break
check(_wt.room == "lab" and any(o.get("target") == "professor_oak" for o in _wt.people.values()), f"walk into the Lab: inside it, Professor Oak there ({_wt.room})")
_wt._go(None, "OUT:16,13")
g.walk_town_room = None
_n = min(t for t, v in _wt.exits.items() if v == "KANTO_ROUTE_1")
_wt.player = _wt.anim_from = (_n[0], _n[1] + 1)
_wt.anim = 0
_wt.step(0, -1)
check(type(g.current_state).__name__ == "AreaTransitionState", "walk off the top: on to Route 1")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "VIRIDIAN_CITY", "KANTO_ROUTE_1"
_wt = _CS(g); g.change_state(_wt)
_tap_through(_wt)
_r1y = max(y for (x, y), v in _wt.exits.items() if v == "KANTO_ROUTE_1")
check(abs(_wt.player[1] - _r1y) <= 1 and set(_wt.doors.values()) >= {"center", "mart", "gym"},
      "Viridian City: in from Route 1 at its south gate; its Center, Mart and Gym have doors")
_wt.walk_goal = next(t for t, k in _wt.doors.items() if k == "center")
for _k in range(600):
    frames(_wt)
    if g.current_state is not _wt or _wt.room:
        break
check(_wt.room == "center" and g.current_state is _wt, f"walk into the Pokemon Center: inside its room ({_wt.room}, {_wt.player})")
_wt.player = _wt.anim_from = (7, 4); _wt.anim = 0; _wt.walk_goal = None
_wt.step(0, -1)
_pc = g.current_state
check(type(_pc).__name__ == "PokeCenterState" and _pc.previous_state is _wt, "...talk to the nurse across her counter: the Center's screen")
_spot = _wt.player
g.change_state(_wt)
check(_wt.player == _spot and _wt.room == "center" and _wt.action_menu not in g.ui_manager.elements, "...out of it again: where you were, no menu bar")
_wt._go(None, "OUT:26,26")
g.walk_town_room = None

# the Johto pilot (Jordan, 11-06): our own maps, laid out after Pokemon Journeys' (New Bark, Route 29, Cherrygrove)
g.walk_town_pos = None
story.story_flags["received_starter_johto"] = True
story.story_flags["move_offer_johto"] = True
story.current_area_key, story.last_area_key = "NEW_BARK_TOWN", None
_nb = _CS(g); g.change_state(_nb); _tap_through(_nb)
check(isinstance(_nb, _WTS) and {"lab", "home", "rival"} <= set(_nb.doors.values()) and not _nb._people()
      and (_nb.w, _nb.h) == (32, 32) and len(_nb.signs) == 7,
      "New Bark Town: SoulSilver's own 32 x 32 map, doors for Elm's Lab, your house and Silver's mom's, its signs (the three house signs two tiles tall), nobody outside")
_nb_rd = next(t for t, k in _nb.doors.items() if k == "rival")
_nb._enter(_nb_rd)
check(_nb.room == "rival" and len(_nb.people) == 1, f"Silver's mom's door: you walk into her house (SoulSilver's own room), the Nice Lady standing there {_nb.room, len(_nb.people)}")
_nb._talk(next(iter(_nb.people)))
check(_nb.npc_active and _nb.current_npc == "silver_mom", "...talk to her: the Nice Lady")
_tap_through(_nb)
_nb._leave("OUT:%d,%d" % _nb_rd)
check(_nb.room is None and _nb.player == (_nb_rd[0], _nb_rd[1] + 1), f"...and back out below her door {_nb.player}")
_nb._enter(next(t for t, k in _nb.doors.items() if k == "house"))
check(_nb.toast == "The door is locked.", "Elm's house: locked")
_nb_surf = story.inventory.pop("HM_SURF", None)
_nb.player = _nb.anim_from = (28, 16)
_nb.anim = 0
_nb.step(1, 0)
check(_nb.player == (28, 16) and _nb.rows[16][29] == "o" and len(getattr(_nb, "overheads", [])) >= 6,
      "New Bark's bay is Surf water (no Surf: you stay on the shore); the tree tops and roof edges are an overhead layer")
story.inventory["HM_SURF"] = 1
_nb.player = _nb.anim_from = (30, 16)
_nb.anim = 0
_held = _nb._check_menu_condition
_nb._check_menu_condition = lambda c: False if c == "has_8_johto_badges" else _held(c)
_nb.step(1, 0)
check(_nb.player == (30, 16) and "8 Johto badges" in _nb.toast and type(g.current_state).__name__ != "AreaTransitionState",
      "the east bay without 8 badges: turned back, told why")
_nb._check_menu_condition = lambda c: True if c == "has_8_johto_badges" else _held(c)
_nb.anim = 0
_nb.step(1, 0)
check(type(g.current_state).__name__ == "AreaTransitionState", "the east bay with 8 badges: on to Route 27")
_nb._check_menu_condition = _held
if _nb_surf is None:
    story.inventory.pop("HM_SURF", None)
else:
    story.inventory["HM_SURF"] = _nb_surf
g.change_state(_nb)
_nb.player = _nb.anim_from = (20, 11)
_nb.anim = 0
_nb_ld = next(t for t, k in _nb.doors.items() if k == "lab")
_nb.walk_goal = _nb_ld
for _k in range(400):
    frames(_nb)
    if _nb.npc_active or _nb.room:
        break
_nb_lab = _nb.room
if _nb.room:  # (11-11: the Lab is SoulSilver's own room now: walk in, talk to the Professor, walk out)
    _nb._talk(next(iter(_nb.people)))
check(_nb_lab == "lab" and _nb.npc_active and _nb.current_npc == "professor_elm", "walk into Elm's Lab (its own room): Professor Elm")
_tap_through(_nb)
_nb._go(None, "OUT:%d,%d" % _nb_ld); g.walk_town_room = None
_w = min(_nb.exits)
_nb.player = _nb.anim_from = (_w[0] + 1, _w[1])
_nb.anim = 0
_nb.step(-1, 0)
check(type(g.current_state).__name__ == "AreaTransitionState", "walk off the west edge: on to Route 29")
_r29 = kanto("JOHTO_ROUTE_29", came="NEW_BARK_TOWN")
_f = _r29.run.floor
check(_r29.run.recipe.get("art") and not _r29.run.fog
      and sorted({v for v in _f.exits.values() if not str(v).startswith("WARP")}) == ["CHERRYGROVE_CITY", "NEW_BARK_TOWN"] and _r29.run.recipe["exit_floors"].get("JOHTO_ROUTE_46", 0) >= 1
      and _r29.run.player[0] >= _f.w - 3, "Route 29: our map, open, in from New Bark (east); Cherrygrove; Route 46 through the gatehouse (a room of its own)")
_wl = [m for m in _f.movers if m.kind == "wild"]
check((_f.w, _f.h) == (96, 32) and str(_f.exits.get((50, 5))).startswith("WARP") and str(_f.exits.get((51, 5))).startswith("WARP")
      and _f.walkable(50, 6), f"Route 29: SoulSilver's own 96 x 32, the gatehouse's two-tile doorway (it leads inside) with open ground in front {_f.exits.get((50, 5))}")
_l29 = [v for v in _f.decor.values() if str(v).startswith("ledge:")]
check((_l29.count("ledge:0,1"), _l29.count("ledge:1,0"), _l29.count("ledge:-1,0")) == (49, 15, 8) and _f.decor.get((15, 12)) == "ledge:0,1",
      f"Route 29: SoulSilver's ledges are real one-way hops: 49 south, 15 east, 8 west ({len(_l29)})")
_m29 = _f.movers; _f.movers = []
_r29.run.player = (15, 13); _r29.anim = 0; _r29.sliding = None
_r29.step(0, -1)
_up29 = tuple(_r29.run.player)
_r29.run.player = (15, 11); _r29.anim = 0
_r29.step(0, 1)
_down29 = tuple(_r29.run.player)
_r29.hop = None; _r29.anim = 0
_r29.run.player = (28, 8); _r29.step(-1, 0)
_west29 = tuple(_r29.run.player)
_r29.run.player = (26, 8); _r29.anim = 0; _r29.step(1, 0)
_east29 = tuple(_r29.run.player)
_r29.hop = None; _r29.anim = 0; _f.movers = _m29
check(_up29 == (15, 13) and _down29 == (15, 13) and _west29 == (28, 8) and _east29 == (28, 8),
      f"Route 29: the ledge at (15, 12) is hopped down ({_down29}) and not climbed ({_up29}); the one at (27, 8) is hopped east ({_east29}), not west ({_west29})")
check(_wl and any(_f.tiles[m.y][m.x] == core.GRASS for m in _wl)
      and sum(m.kind == "trainer" for m in _f.movers) == sum(
          not story.is_trainer_defeated("JOHTO_ROUTE_29", i) for i in range(len(_r29.area_data.get("trainer_pool", [])))),
      "...wild Pokemon in its tall grass, its trainers on the map")
g.walk_town_pos = None
story.story_flags["defeated_rival_cherrygrove"] = True
story.current_area_key, story.last_area_key = "CHERRYGROVE_CITY", "JOHTO_ROUTE_29"
_cg = _CS(g); g.change_state(_cg); _tap_through(_cg)
check(_cg.player[0] >= _cg.w - 3 and {"center", "mart", "gent", "fisher"} <= set(_cg.doors.values())
      and set(_cg.exits.values()) == {"JOHTO_ROUTE_29", "JOHTO_ROUTE_30"},
      "Cherrygrove City: in from Route 29 (east); the Center, the Mart, the Guide Gent's and the fisherman's houses")
story.inventory.pop("MYSTIC_WATER", None)
story.story_flags.pop("got_mystic_water", None)
def _in_and_talk(t, kind):  # (11-11: Johto's houses are SoulSilver's own rooms now: in by the door, talk to whoever is there, out again)
    door = next(d for d, k in t.doors.items() if k == kind)
    t._enter(door)
    was = t.room
    for spot in list(t.people) if was else []:
        t._talk(spot); _tap_through(t)
    if was:
        t._go(None, "OUT:%d,%d" % door); g.walk_town_room = None
    return was


_cg_room = _in_and_talk(_cg, "fisher")
_tap_through(_cg)
check(_cg_room == "fisher" and story.inventory.get("MYSTIC_WATER") == 1, "the fisherman's house (its own room): Mystic Water")
_in_and_talk(_cg, "fisher")
_tap_through(_cg)
check(story.inventory.get("MYSTIC_WATER") == 1, "...once (after that he just talks)")
# a save loaded straight into a walked town (Jordan, 11-07: it went back to the title): nothing to come from
_had = story.__dict__.pop("last_area_key", None)
g.walk_town_pos = None
story.current_area_key = "CHERRYGROVE_CITY"
try:
    _ld = _CS(g)
    check(isinstance(_ld, _WTS) and _ld._open(_ld.player), "a loaded save in a walked town: it opens (no came-from)")
except Exception as _e:
    check(False, f"a loaded save in a walked town: {_e!r}")
story.last_area_key = _had


# Johto's exact maps, Cherrygrove through Azalea (Jordan, 11-09)
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "VIOLET_CITY", "JOHTO_ROUTE_31"
_vi = _CS(g); g.change_state(_vi); _tap_through(_vi)
check(isinstance(_vi, _WTS) and (_vi.w, _vi.h) == (64, 64) and {"sprout", "gym", "mart", "center"} <= set(_vi.doors.values())
      and set(_vi.exits.values()) == {"JOHTO_ROUTE_31", "JOHTO_ROUTE_32", "JOHTO_ROUTE_36"} and _vi.player[0] >= _vi.w - 12,
      "Violet City: exact map, in from Route 31 (east); Tower, Gym, Mart, Center doors and its three ways out")
_vi._enter(next(t for t, k in _vi.doors.items() if k == "sprout"))
check(type(g.current_state).__name__ == "AreaTransitionState", "Sprout Tower's door: in you go")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "AZALEA_TOWN", "JOHTO_ROUTE_33"
_az = _CS(g); g.change_state(_az); _tap_through(_az)
check(isinstance(_az, _WTS) and (_az.w, _az.h) == (64, 32) and {"kurt", "gym", "mart", "center"} <= set(_az.doors.values())
      and "SLOWPOKE_WELL" in _az.exits.values() and "JOHTO_ROUTE_33" in _az.exits.values() and "ILEX_FOREST" in _az.exits.values(),
      "Azalea Town: exact map; Kurt's, the Gym, Mart and Center doors; the Well, Ilex and Route 33")
_az_kd = next(t for t, k in _az.doors.items() if k == "kurt")
_az._enter(_az_kd)
_az_room = _az.room
_az._talk(next(iter(_az.people)))
check(_az_room == "kurt" and _az.npc_active and _az.current_npc == "kurt", "Kurt's door: his house (its own room), Kurt inside")
_tap_through(_az)
_az._go(None, "OUT:%d,%d" % _az_kd); g.walk_town_room = None
_had_flash = story.inventory.pop("HM_FLASH", None)
_r31 = kanto("JOHTO_ROUTE_31", came="JOHTO_ROUTE_30")
_f31 = _r31.run.floor
check((_f31.w, _f31.h) == (64, 32) and _f31.exits.get((53, 13)) == "DARK_CAVE" and _f31.exits.get((6, 13)) == "VIOLET_CITY" and _f31.exits.get((6, 14)) == "VIOLET_CITY"
      and _r31.run.player[1] >= 29, f"Route 31: SoulSilver's own 64 x 32; in from Route 30 (south) at {_r31.run.player}; the Dark Cave mouth in the east cliff, the gatehouse's two-tile doorway to Violet")
check(not _r31._try_exit("DARK_CAVE") and type(g.current_state).__name__ != "AreaTransitionState", "...and it stays shut without Flash")
if _had_flash:
    story.inventory["HM_FLASH"] = _had_flash
_r30 = kanto("JOHTO_ROUTE_30", came="CHERRYGROVE_CITY")
check((_r30.run.floor.w, _r30.run.floor.h) == (32, 96) and _r30.run.floor.exits.get((24, 6)) == "MR_POKEMONS_HOUSE" and _r30.run.player[1] >= 93
      and "JOHTO_ROUTE_31" in _r30.run.floor.exits.values() and list(_r30.run.floor.decor.values()).count("ledge:0,1") == 32,
      f"Route 30: SoulSilver's own 32 x 96; in from Cherrygrove (south) at {_r30.run.player}; Mr. Pokemon's door top right, the way north, its ledges hopped south")
_r32 = kanto("JOHTO_ROUTE_32", came="VIOLET_CITY")
check((_r32.run.floor.w, _r32.run.floor.h) == (32, 160) and _r32.run.player[1] <= 2 and _r32.run.floor.exits.get((14, 142)) == "UNION_CAVE" and {"VIOLET_CITY", "RUINS_OF_ALPH", "UNION_CAVE"} <= set(_r32.run.floor.exits.values())
      and any(o.get("door") == "center" for o in _r32.area_data["route_menu"]), "Route 32: exact map, its ways out, a working Center door")
_r33 = kanto("JOHTO_ROUTE_33", came="AZALEA_TOWN")
check({"AZALEA_TOWN", "UNION_CAVE"} == set(_r33.run.floor.exits.values()), "Route 33: Azalea and Union Cave")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "RUINS_OF_ALPH", "JOHTO_ROUTE_32"
_ra = _CS(g); g.change_state(_ra); _tap_through(_ra)
check(isinstance(_ra, _WTS) and (_ra.w, _ra.h) == (32, 64) and {"kabuto", "hooh", "omanyte", "aerodactyl", "ruins", "lab"} <= set(_ra.doors.values())
      and {"JOHTO_ROUTE_32", "UNION_CAVE"} <= set(_ra.exits.values()) and "JOHTO_ROUTE_36" in _ra.town_map["rooms"]["gate"]["exits"].values(),
      "Ruins of Alph: exact map; four chambers, the ruins, the lab, its ways out (Route 36 through the north gatehouse)")
for _k in ("kabuto", "hooh", "omanyte", "aerodactyl"):
    check(len(_ra._door_options(_k)) == 1, f"...the {_k} door opens its puzzle")
_r_un = kanto("UNION_CAVE", came="JOHTO_ROUTE_32")
_un_names = [m.payload[1].get("name") if isinstance(m.payload, tuple) else None for m in _r_un.run.floor.movers if m.kind == "trainer"]
check(_r_un.run.n_floors == 3 and _r_un.run.index == 0 and {"JOHTO_ROUTE_32", "JOHTO_ROUTE_33", "RUINS_OF_ALPH"} <= set(_r_un.run.floor.exits.values()) and len(_un_names) == 5,
      f"Union Cave: SoulSilver's three floors; in from Route 32 on 1F; five of its six trainers there (the sixth on B1F) {_r_un.run.n_floors, _r_un.run.index, sorted(set(map(str, _r_un.run.floor.exits.values()))), [(m.kind, str(m.payload)[:50]) for m in _r_un.run.floor.movers if m.kind != 'wild'][:8]}")
# Johto's caves from SoulSilver's own floors: every stair is a passage to its real far end; walk each one
import json as _json_j
_tm_j = _json_j.load(open("assets/town_maps.json", encoding="utf-8"))
_walked_j = []
for _kj, _camej in (("UNION_CAVE", "JOHTO_ROUTE_32"), ("SLOWPOKE_WELL", "AZALEA_TOWN"), ("WHIRL_ISLANDS", "JOHTO_ROUTE_41"),
                     ("BURNED_TOWER", "ECRUTEAK_CITY"), ("SPROUT_TOWER", "VIOLET_CITY"),
                     ("OLIVINE_LIGHTHOUSE_FLOORS", "OLIVINE_CITY"), ("RADIO_TOWER", "GOLDENROD_CITY"), ("GOLDENROD_UNDERGROUND", "GOLDENROD_CITY"), ("BELL_TOWER", "BELLCHIME_TRAIL"), ("MT_MORTAR", "JOHTO_ROUTE_42"),
                     ("ROCKET_HQ", "MAHOGANY_TOWN"), ("ICE_PATH", "JOHTO_ROUTE_44"), ("DRAGONS_DEN", "BLACKTHORN_CITY"), ("JOHTO_CLIFF_CAVE", "JOHTO_ROUTE_47"), ("TOHJO_FALLS", "KANTO_ROUTE_27")):
    for _i, _fj2 in enumerate(_tm_j[_kj]["floors"]):
        for _at, (_j, _x, _y) in (_fj2.get("links") or {}).items():
            _rj = kanto(_kj, came=_camej)
            _ax, _ay = (int(v) for v in _at.split(","))
            _rj.run.warp(_i, _ax, _ay)
            _px, _py = _rj.run.player
            _ev = _rj.run.step(_ax - _px, _ay - _py)
            _rj._handle(_ev)
            for _q in range(40):
                if getattr(_rj, "dialogue_box", None) and _rj.dialogue_box.visible:
                    _rj.dialogue_box.advance()
                frames(_rj)
            _okj = (any(e[0] == "warp" for e in _ev) and _rj.run.index == _j and _rj.run.floor.walkable(*_rj.run.player)
                    and (abs(_rj.run.player[0] - _x) + abs(_rj.run.player[1] - _y) <= 1 or _rj.run.player == _rj.run.floor.start))
            _walked_j.append((_kj, _i, _at, _okj))
check(len(_walked_j) == 217 and all(w[3] for w in _walked_j),
      f"Johto's caves and towers from SoulSilver (Union Cave, Slowpoke Well, Whirl Islands, Burned and Sprout Towers, Lighthouse, Radio Tower, Underground, Bell Tower, Mt. Mortar, Rocket HQ, Ice Path): stepping onto each of their {len(_walked_j)} stairs takes you beside its far end on the right floor {[w for w in _walked_j if not w[3]][:6]}")
_ilx = kanto("ILEX_FOREST", came="AZALEA_TOWN")
check((_ilx.run.floor.w, _ilx.run.floor.h) == (64, 96) and {"AZALEA_TOWN"} == {v for v in _ilx.run.floor.exits.values() if not str(v).startswith("WARP")} and _ilx.run.recipe["exit_floors"].get("JOHTO_ROUTE_34", 0) >= 1
      and _ilx.run.player[1] >= 78, f"Ilex Forest: SoulSilver's own 64 x 96, in from Azalea at the south-west gate {_ilx.run.player}, Route 34 north")
_r34 = kanto("JOHTO_ROUTE_34", came="ILEX_FOREST")
check((_r34.run.floor.w, _r34.run.floor.h) == (32, 96) and _r34.run.player[1] in (64, 65, 66) and {"ILEX_FOREST", "GOLDENROD_CITY"} == {v for v in _r34.run.floor.exits.values() if not str(v).startswith("WARP")}
      and "daycare" in (_r34.run.recipe.get("art") or {}).get("room_floors", {}) and any(o.get("door") == "daycare" for o in _r34.area_data["route_menu"]),
      "Route 34: exact map, Goldenrod and Ilex, the Day Care (a room of its own)")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "GOLDENROD_CITY", "JOHTO_ROUTE_34"
_gd = _CS(g); g.change_state(_gd); _tap_through(_gd)
check(isinstance(_gd, _WTS) and (_gd.w, _gd.h) == (96, 64) and _gd.player[1] >= 60
      and {"radio", "gym", "center", "dept", "bike", "flower", "station", "game corner"} <= set(_gd.doors.values())
      and {"JOHTO_ROUTE_34", "GOLDENROD_UNDERGROUND"} == set(_gd.exits.values()) and "JOHTO_ROUTE_35" in _gd.town_map["rooms"]["gate"]["exits"].values(),
      "Goldenrod City: exact map, in from Route 34 (south); every shop's door, both Underground stairs, the gate north")
_gd.player = _gd.anim_from = (70, 23); _gd.anim = 0
for _k in range(5):
    _gd.step(0, 1)
    _gd.anim = 0
check(_gd.player == (70, 28) and any(o[0].get("kind") == "rail" for o in _gd.overheads), "...you walk under the Magnet Train line")
_gd.draw()
for _k in ("radio", "dept", "bike", "flower", "center", "game corner"):
    check(_gd._door_options(_k), f"...the {_k} door has something behind it")
_r35 = kanto("JOHTO_ROUTE_35", came="GOLDENROD_CITY")
check((_r35.run.floor.w, _r35.run.floor.h) == (32, 64) and {"JOHTO_ROUTE_36", "GOLDENROD_CITY"} == {v for v in _r35.run.floor.exits.values() if not str(v).startswith("WARP")}
      and _r35.run.player[1] >= 58 and core.distances(_r35.run.floor, _r35.run.player).get((10, 11)) is not None
      and _r35.run.floor.exits.get((26, 0)) == "JOHTO_ROUTE_36" and str(_r35.run.floor.exits.get((10, 10))).startswith("WARP") and _r35.run.recipe["exit_floors"].get("NATIONAL_PARK", 0) >= 1,
      f"Route 35: SoulSilver's own 32 x 64, in from Goldenrod's gatehouse (south) at {_r35.run.player}; on foot to the National Park gate's door; the east lane north to Route 36")
_np = kanto("NATIONAL_PARK", came="JOHTO_ROUTE_36")
check((_np.run.floor.w, _np.run.floor.h) == (96, 96) and {"JOHTO_ROUTE_35", "JOHTO_ROUTE_36", "POKEATHLON_DOME"} == set(_np.run.floor.exits.values())
      and _np.run.player[0] >= 72, "National Park: SoulSilver's own 96 x 96, in from Route 36 (east gate), the Dome and Route 35")
_r36 = kanto("JOHTO_ROUTE_36", came="VIOLET_CITY")
check((_r36.run.floor.w, _r36.run.floor.h) == (96, 32) and {"VIOLET_CITY", "RUINS_OF_ALPH", "JOHTO_ROUTE_35", "JOHTO_ROUTE_37", "NATIONAL_PARK"} == set(_r36.run.floor.exits.values())
      and _r36.run.player[0] >= 93, "Route 36: SoulSilver's own 96 x 32, in from Violet (east gate), all five ways out")
_r37 = kanto("JOHTO_ROUTE_37", came="JOHTO_ROUTE_36")
check({"JOHTO_ROUTE_36", "ECRUTEAK_CITY"} == set(_r37.run.floor.exits.values()), "Route 37: Route 36 and Ecruteak")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "ECRUTEAK_CITY", "JOHTO_ROUTE_37"
_ec = _CS(g); g.change_state(_ec); _tap_through(_ec)
check(isinstance(_ec, _WTS) and (_ec.w, _ec.h) == (64, 64) and {"burned", "bellchime", "theater", "gym", "mart", "center"} <= set(_ec.doors.values())
      and {"JOHTO_ROUTE_37", "JOHTO_ROUTE_38", "JOHTO_ROUTE_42"} == set(_ec.exits.values()) and _ec.player[1] >= 60,
      "Ecruteak City: exact map, in from Route 37 (south); its towers, theater, Gym and shops; three ways out")
for _k in ("burned", "bellchime", "theater"):
    check(_ec._door_options(_k), f"...the {_k} door leads somewhere")
_ec.draw()
_bt = kanto("BURNED_TOWER", came="ECRUTEAK_CITY")
check(_bt.run.n_floors == 2 and "ECRUTEAK_CITY" in _bt.run.floor.exits.values() and _bt.run.recipe["art"]["floors"][0].get("links") if isinstance(_bt.run.recipe.get("art"), dict) else _bt.run.n_floors == 2,
      "Burned Tower: SoulSilver's 1F, the way out, the stairs down to the basement")
_r38 = kanto("JOHTO_ROUTE_38", came="ECRUTEAK_CITY")
check((_r38.run.floor.w, _r38.run.floor.h) == (64, 32) and {"ECRUTEAK_CITY", "JOHTO_ROUTE_39"} == set(_r38.run.floor.exits.values()), "Route 38: exact map, Ecruteak and Route 39")
_r39 = kanto("JOHTO_ROUTE_39", came="JOHTO_ROUTE_38")
check((_r39.run.floor.w, _r39.run.floor.h) == (32, 64) and {"JOHTO_ROUTE_38", "OLIVINE_CITY", "MOOMOO_BARN", "MOOMOO_HOUSE"} == set(_r39.run.floor.exits.values()), "Route 39: exact to the HGSS picture with Moomoo Farm; Route 38, Olivine, the barn and house doors")
_bct = kanto("BELLCHIME_TRAIL", came="ECRUTEAK_CITY")
check((_bct.run.floor.w, _bct.run.floor.h) == (64, 32) and {"ECRUTEAK_CITY", "BELL_TOWER"} == set(_bct.run.floor.exits.values()) and _bct.run.player[0] <= 12, f"Bellchime Trail: SoulSilver's own 64 x 32, in from Ecruteak's gatehouse at {_bct.run.player}; the Bell Tower door")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "OLIVINE_CITY", "JOHTO_ROUTE_39"
_ol = _CS(g); g.change_state(_ol); _tap_through(_ol)
check(isinstance(_ol, _WTS) and (_ol.w, _ol.h) == (64, 64) and {"gym", "center", "mart", "harbor"} <= set(_ol.doors.values())
      and {"JOHTO_ROUTE_39", "JOHTO_ROUTE_40", "OLIVINE_LIGHTHOUSE_FLOORS"} == set(_ol.exits.values()) and _ol.player[1] <= 3,
      "Olivine City: exact map, in from Route 39 (north); its doors, the Lighthouse, the beach west")
_ol.player = _ol.anim_from = (23, 52); _ol.anim = 0
check((23, 53) in _ol.doors and _ol.doors[(23, 53)] == "harbor", "...the harbor terminal's door faces the pier")
_ol.draw()
_lh = kanto("OLIVINE_LIGHTHOUSE_FLOORS", came="OLIVINE_CITY")
check(_lh.run.n_floors == 5 and _lh.run.index == 0 and "OLIVINE_CITY" in _lh.run.floor.exits.values(), "Glitter Lighthouse: five floors, in on 1F")
_bal = kanto("OLIVINE_LIGHTHOUSE_BALCONY", came="OLIVINE_LIGHTHOUSE_FLOORS")
check((_bal.run.floor.w, _bal.run.floor.h) == (17, 16) and set(_bal.run.floor.exits.values()) == {"OLIVINE_LIGHTHOUSE_FLOORS"}, "...the balcony: the tower's door back in")
_back = kanto("OLIVINE_LIGHTHOUSE_FLOORS", came="OLIVINE_LIGHTHOUSE_BALCONY")
_f3 = _back.run.floor
check(_back.run.index == 2 and _f3.walkable(*_back.run.player) and _back.run.player[1] >= 15, f"...and back in on 3F by its south door {_back.run.player}")
_back.run.floor
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "OLIVINE_LIGHTHOUSE", "OLIVINE_LIGHTHOUSE_FLOORS"
_top = _CS(g); g.change_state(_top); _tap_through(_top)
check(isinstance(_top, _WTS) and sorted(o["text"] for o in _top._people().values()) == ["Check Amphy", "Talk to Jasmine"]
      and {"OLIVINE_CITY", "OLIVINE_LIGHTHOUSE_FLOORS"} == set(_top.exits.values()), "...the beacon room: Jasmine, Amphy, the stairs, the elevator")
_lift = next(t for t, v in _top.exits.items() if v == "OLIVINE_CITY")
story.story_flags.pop("ampharos_cured", None)
_top.player = _top.anim_from = (_lift[0], _lift[1] + 1); _top.anim = 0
_top.step(0, -1)
check("locked" in _top.toast and type(g.current_state).__name__ != "AreaTransitionState", "...the elevator is locked until Amphy has its medicine")
story.story_flags["ampharos_cured"] = True
_top.anim = 0
_top.player = _top.anim_from = (_lift[0], _lift[1] + 1)
_top.step(0, -1)
check(type(g.current_state).__name__ == "AreaTransitionState", "...and opens after")
story.story_flags.pop("ampharos_cured", None)
_r40 = kanto("JOHTO_ROUTE_40", came="OLIVINE_CITY")
check((_r40.run.floor.w, _r40.run.floor.h) == (32, 64) and {"OLIVINE_CITY", "JOHTO_ROUTE_41", "FRONTIER_ACCESS"} == set(_r40.run.floor.exits.values()), "Route 40: exact map, Olivine, the Frontier's gateway, the sea to Route 41")
_r41 = kanto("JOHTO_ROUTE_41", came="JOHTO_ROUTE_40")
check((_r41.run.floor.w, _r41.run.floor.h) == (64, 64) and {"JOHTO_ROUTE_40", "CIANWOOD_CITY", "WHIRL_ISLANDS"} == set(_r41.run.floor.exits.values())
      and sum(v == "WHIRL_ISLANDS" for v in _r41.run.floor.exits.values()) == 4, "Route 41: exact map, Route 40, Cianwood, all four Whirl Island caves")
_r40 = kanto("JOHTO_ROUTE_40", came="OLIVINE_CITY")
check((_r40.run.floor.w, _r40.run.floor.h) == (32, 64) and {"OLIVINE_CITY", "JOHTO_ROUTE_41", "FRONTIER_ACCESS"} == set(_r40.run.floor.exits.values()), "Route 40: exact map, Olivine, the Frontier's gateway, the sea to Route 41")
_r41 = kanto("JOHTO_ROUTE_41", came="JOHTO_ROUTE_40")
check((_r41.run.floor.w, _r41.run.floor.h) == (64, 64) and {"JOHTO_ROUTE_40", "CIANWOOD_CITY", "WHIRL_ISLANDS"} == set(_r41.run.floor.exits.values())
      and sum(v == "WHIRL_ISLANDS" for v in _r41.run.floor.exits.values()) == 4, "Route 41: exact map, Route 40, Cianwood, all four Whirl Island caves")
_r40 = kanto("JOHTO_ROUTE_40", came="OLIVINE_CITY")
check((_r40.run.floor.w, _r40.run.floor.h) == (32, 64) and {"OLIVINE_CITY", "JOHTO_ROUTE_41", "FRONTIER_ACCESS"} == set(_r40.run.floor.exits.values()), "Route 40: exact map, Olivine, the Frontier's gateway, the sea to Route 41")
_r41 = kanto("JOHTO_ROUTE_41", came="JOHTO_ROUTE_40")
check((_r41.run.floor.w, _r41.run.floor.h) == (64, 64) and {"JOHTO_ROUTE_40", "CIANWOOD_CITY", "WHIRL_ISLANDS"} == set(_r41.run.floor.exits.values())
      and sum(v == "WHIRL_ISLANDS" for v in _r41.run.floor.exits.values()) == 4, "Route 41: exact map, Route 40, Cianwood, all four Whirl Island caves")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "CIANWOOD_CITY", "JOHTO_ROUTE_41"
_cw = _CS(g); g.change_state(_cw); _tap_through(_cw)
check(isinstance(_cw, _WTS) and (_cw.w, _cw.h) == (32, 64) and {"gym", "center", "pharmacy"} <= set(_cw.doors.values())
      and {"JOHTO_ROUTE_41", "CLIFF_EDGE_GATE"} == set(_cw.exits.values()) and len(_cw._door_options("pharmacy")) == 2,
      "Cianwood City: exact map; the Gym, Center, Pharmacy (medicine and shop), the sea and the cliff gate")
_w41 = kanto("JOHTO_ROUTE_41", came="JOHTO_ROUTE_40")
_wf = _w41.run.floor
def _sea_reach(f, start):
    seen, todo = {start}, [start]
    while todo:
        x, y = todo.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if 0 <= n[0] < f.w and 0 <= n[1] < f.h and n not in seen and f.tiles[n[1]][n[0]] in (core.FLOOR, core.GRASS, core.SURF):
                seen.add(n); todo.append(n)
    return seen
_caves = [t for t, v in _wf.exits.items() if v == "WHIRL_ISLANDS"]
_open = _sea_reach(_wf, (40, 1))
check(_caves and not any(c in _open for c in _caves), "Route 41: all four islands are sealed; no cave without getting past a whirlpool")
for _key in [k for k in story.story_flags if k.startswith("boulder_JOHTO_ROUTE_41")]:
    story.story_flags.pop(_key)
_had_wp = story.inventory.pop("HM_WHIRLPOOL", None)
_w41.run.player = (25, 12); _w41.facing = (-1, 0)
_w41._read_sign()
check(str(_wf.decor.get((24, 12), "")).startswith("whirl:"), "...a whirlpool won't budge without Whirlpool")
story.inventory["HM_WHIRLPOOL"] = 1
_w41.run.player = (25, 12); _w41.facing = (-1, 0)
_w41._read_sign()
_w41._render_floor()
check((24, 12) not in _wf.decor and any(c in _sea_reach(_wf, (40, 1)) for c in _caves), "...and with it the whirlpool clears and that island opens")
for _key in [k for k in story.story_flags if k.startswith("boulder_JOHTO_ROUTE_41")]:
    story.story_flags.pop(_key)
story.inventory.pop("HM_WHIRLPOOL", None)
if _had_wp:
    story.inventory["HM_WHIRLPOOL"] = _had_wp
_r40 = kanto("JOHTO_ROUTE_40", came="OLIVINE_CITY")
check((_r40.run.floor.w, _r40.run.floor.h) == (32, 64) and {"OLIVINE_CITY", "JOHTO_ROUTE_41", "FRONTIER_ACCESS"} == set(_r40.run.floor.exits.values()), "Route 40: exact map, Olivine, the Frontier's gateway, the sea to Route 41")
_r41 = kanto("JOHTO_ROUTE_41", came="JOHTO_ROUTE_40")
check((_r41.run.floor.w, _r41.run.floor.h) == (64, 64) and {"JOHTO_ROUTE_40", "CIANWOOD_CITY", "WHIRL_ISLANDS"} == set(_r41.run.floor.exits.values())
      and sum(v == "WHIRL_ISLANDS" for v in _r41.run.floor.exits.values()) == 4, "Route 41: exact map, Route 40, Cianwood, all four Whirl Island caves")
_r40 = kanto("JOHTO_ROUTE_40", came="OLIVINE_CITY")
check((_r40.run.floor.w, _r40.run.floor.h) == (32, 64) and {"OLIVINE_CITY", "JOHTO_ROUTE_41", "FRONTIER_ACCESS"} == set(_r40.run.floor.exits.values()), "Route 40: exact map, Olivine, the Frontier's gateway, the sea to Route 41")
_r41 = kanto("JOHTO_ROUTE_41", came="JOHTO_ROUTE_40")
check((_r41.run.floor.w, _r41.run.floor.h) == (64, 64) and {"JOHTO_ROUTE_40", "CIANWOOD_CITY", "WHIRL_ISLANDS"} == set(_r41.run.floor.exits.values())
      and sum(v == "WHIRL_ISLANDS" for v in _r41.run.floor.exits.values()) == 4, "Route 41: exact map, Route 40, Cianwood, all four Whirl Island caves")
from src.dungeon import core as _c
_rooms = {}
for _i, _name in enumerate(("NW", "NE", "SW", "SE")):
    _c.ENTRANCE_INDEX = _i
    _wi = kanto("WHIRL_ISLANDS", came="JOHTO_ROUTE_41")
    _rooms[_name] = _wi.run.player
_c.ENTRANCE_INDEX = 0
_near_wi = lambda p, q: abs(p[0] - q[0]) + abs(p[1] - q[1]) <= 2
check(_wi.run.n_floors == 5 and _near_wi(_rooms["NW"], (8, 14)) and _near_wi(_rooms["NE"], (34, 19)) and _near_wi(_rooms["SW"], (5, 48)) and _near_wi(_rooms["SE"], (49, 53)),
      f"Whirl Islands: SoulSilver's five floors; each of Route 41's cave mouths leads to its own island's room on 1F {_rooms}")
_r42 = kanto("JOHTO_ROUTE_42", came="ECRUTEAK_CITY")
check((_r42.run.floor.w, _r42.run.floor.h) == (96, 32) and {"ECRUTEAK_CITY", "MAHOGANY_TOWN", "MT_MORTAR"} == set(_r42.run.floor.exits.values())
      and sum(v == "MT_MORTAR" for v in _r42.run.floor.exits.values()) == 4, "Route 42: exact map; Ecruteak, Mahogany, four ways into Mt. Mortar")
_mm = {}
for _i, _name in enumerate(("upper", "west", "east", "middle")):  # (Route 42's four mouths in reading order)
    _c.ENTRANCE_INDEX, _c.ENTRANCE_COUNT = _i, 4
    _mt = kanto("MT_MORTAR", came="JOHTO_ROUTE_42")
    _mm[_name] = tuple(_mt.run.player)
_c.ENTRANCE_INDEX = _c.ENTRANCE_COUNT = 0
_near_mm = lambda p, q: abs(p[0] - q[0]) + abs(p[1] - q[1]) <= 2
check(_mt.run.n_floors == 4 and _near_mm(_mm["west"], (4, 46)) and _near_mm(_mm["east"], (54, 46)) and _near_mm(_mm["middle"], (29, 50)) and _near_mm(_mm["upper"], (43, 53))
      and [t for t, v in _mt.run.floor.exits.items() if v == "JOHTO_ROUTE_42"] == [(43, 53), (4, 46), (54, 46), (29, 50)],
      f"Mt. Mortar: SoulSilver's four floors; each of Route 42's mouths leads to its own mouth inside, and back {_mm}")
_r43 = kanto("JOHTO_ROUTE_43", came="MAHOGANY_TOWN")
check((_r43.run.floor.w, _r43.run.floor.h) == (32, 64) and {"MAHOGANY_TOWN", "LAKE_OF_RAGE"} == {v for v in _r43.run.floor.exits.values() if not str(v).startswith("WARP")} and _r43.run.player[1] >= 58
      and sum(str(v).startswith("WARP") for v in _r43.run.floor.exits.values()) == 4,
      f"Route 43: exact map; in from Mahogany's gate (south) at {_r43.run.player}; the toll gate walked through door to door; north to the Lake of Rage")
story.story_flags.pop("rocket_hq_cleared", None)
story.defeated_trainers.pop("JOHTO_ROUTE_43", None)
_r43 = kanto("JOHTO_ROUTE_43", came="MAHOGANY_TOWN")
_gr = {(m.x, m.y) for f in _r43.run.floors for m in f.movers if m.kind == "trainer"}
story.story_flags["rocket_hq_cleared"] = True
_r43b = kanto("JOHTO_ROUTE_43", came="MAHOGANY_TOWN")
_gr2 = {(m.x, m.y) for f in _r43b.run.floors for m in f.movers if m.kind == "trainer"}
story.story_flags.pop("rocket_hq_cleared", None)
check({(24, 36), (27, 49)} <= _gr and not ({(24, 36), (27, 49)} & _gr2) and len(_gr2) == len(_gr) - 2,
      f"Route 43: two Rocket Grunts stand outside the toll gate's doors, gone once the hideout is cleared {sorted(_gr)} -> {sorted(_gr2)}")
_r44 = kanto("JOHTO_ROUTE_44", came="MAHOGANY_TOWN")
check((_r44.run.floor.w, _r44.run.floor.h) == (96, 32) and {"MAHOGANY_TOWN", "ICE_PATH"} == set(_r44.run.floor.exits.values()) and _r44.run.player[0] <= 2,
      f"Route 44: exact map; in from Mahogany (west) at {_r44.run.player}; the Ice Path's mouth east")
_hq = kanto("ROCKET_HQ", came="MAHOGANY_TOWN")
_hqr = _hq.recipe
check(_hq.run.n_floors == 3 and "MAHOGANY_TOWN" in _hq.run.floor.exits.values() and _hq.run.player[0] >= 40 and _hq.run.player[1] <= 6
      and (_hqr.get("art") or {}).get("figure_floors", {}).get("Executive Petrel") == 2,
      f"Rocket Hideout: exact B1F-B3F; in from the shop's stairs (NE) at {_hq.run.player}; Petrel waits on B3F, Ariana on B2F")
story.defeated_trainers.pop("ROCKET_HQ", None)
_hq = kanto("ROCKET_HQ", came="MAHOGANY_TOWN")
while _hq.run.index < _hq.run.n_floors - 1:
    _hq.run.enter_floor(_hq.run.index + 1)
_hqt = [(i, m.x, m.y) for i, f in enumerate(_hq.run.floors) for m in f.movers if m.kind == "trainer"]
check(len(_hqt) == 5 and len(set(_hqt)) == 5 and [t[0] for t in _hqt].count(0) == 1 and [t[0] for t in _hqt].count(1) == 2,
      f"Rocket Hideout: a grunt on each floor on a spot of their own (three share one name), Ariana on B2F, Petrel on B3F {_hqt}")
_r44 = kanto("JOHTO_ROUTE_44", came="MAHOGANY_TOWN")
check(len({(m.x, m.y) for m in _r44.run.floor.movers if m.kind == "trainer"}) == 7, "Route 44: seven trainers, each on a spot of the game's")
story.defeated_trainers.pop("JOHTO_ROUTE_43", None)
_r43 = kanto("JOHTO_ROUTE_43", came="MAHOGANY_TOWN")
check({(m.x, m.y) for m in _r43.run.floor.movers if m.kind == "trainer"} >= {(18, 8), (25, 15), (8, 17), (19, 26), (14, 31), (14, 53)}, "Route 43: the game's six trainers on the game's six spots")
_ip = kanto("ICE_PATH", came="JOHTO_ROUTE_44")
check(_ip.run.n_floors == 4 and _ip.run.player[1] >= 43 and len(_ip.run.floor.ice) > 100 and {"JOHTO_ROUTE_44", "BLACKTHORN_CITY"} <= set(_ip.run.floor.exits.values()),
      f"Ice Path: exact 1F-B3F; in from Route 44 (south) at {_ip.run.player}; sheet ice on 1F")
_ip.run.floor.movers = []
_ip.run.player, _ip.mode, _ip.anim, _ip.walk_goal = (10, 43), "MAP", 0, None
_ip.dialogue_box.visible = False
_ip.step(0, -1)
for _ in range(400):
    _ip.update()
    if not _ip.sliding and _ip.anim == 0:
        break
_up = _ip.run.player
_ip.step(1, 0)
for _ in range(400):
    _ip.update()
    if not _ip.sliding and _ip.anim == 0:
        break
check(_up == (10, 36) and _ip.run.player == (18, 36) and not _ip.sliding,
      f"Ice Path: step onto the ice and you slide till something stops you (up to {_up}, then right to {_ip.run.player})")
for _bx, _by in ((9, 11), (12, 12), (17, 10), (24, 10)):
    story.story_flags[f"boulder_ICE_PATH_1_{_bx}_{_by}"] = True
while _ip.run.index < 2:  # (floors are made in order)
    _ip.run.enter_floor(_ip.run.index + 1)
_ip._clear_boulders()
_fallen = sorted(t for t, w in _ip.run.floor.decor.items() if str(w).startswith("fallen:"))
for _bx, _by in ((9, 11), (12, 12), (17, 10), (24, 10)):
    story.story_flags.pop(f"boulder_ICE_PATH_1_{_bx}_{_by}", None)
check(_fallen == [(8, 20), (9, 12), (16, 9), (17, 21)] and all(not _ip.run.floor.walkable(*t) for t in _fallen),
      f"Ice Path: B1F's four boulders, pushed into their holes, land on B2F's ice as stops {_fallen}")
_ipl = [f.get("links") or {} for f in (_ip.recipe.get("art") or {}).get("floors", [])]
check(len(_ipl) == 4 and _ipl[2].get("13,16") == [3, 4, 9] and _ipl[3].get("23,10") == [2, 47, 4] and _ipl[0].get("48,4") == [1, 5, 19],
      f"Ice Path: every ladder joined to its real far end (B2F's middle ladder to B3F's west, B3F's east ladder up to B2F's east) {_ipl[2:]}")
_w = {}
for _k, _cm in (("CLIFF_EDGE_GATE", "CIANWOOD_CITY"), ("CLIFF_EDGE_GATE", "JOHTO_ROUTE_47"), ("JOHTO_ROUTE_47", "CLIFF_EDGE_GATE"), ("JOHTO_ROUTE_47", "JOHTO_ROUTE_48"), ("JOHTO_ROUTE_48", "JOHTO_ROUTE_47"),
               ("JOHTO_ROUTE_48", "SAFARI_ZONE_GATE")):
    story.defeated_trainers.pop(_k, None)
    _r = kanto(_k, came=_cm)
    _w[(_k, _cm)] = (_r.run.floor.w, _r.run.floor.h, _r.run.player, set(map(str, _r.run.floor.exits.values())), {(m.x, m.y) for m in _r.run.floor.movers if m.kind == "trainer"})
check(_w[("CLIFF_EDGE_GATE", "CIANWOOD_CITY")][3] >= {"CIANWOOD_CITY", "JOHTO_ROUTE_47"} and _w[("CLIFF_EDGE_GATE", "CIANWOOD_CITY")][2] != _w[("CLIFF_EDGE_GATE", "JOHTO_ROUTE_47")][2],
      f"Cliff Edge Gate: SoulSilver's passage; in from Cianwood at one door, from Route 47 at the other {_w[('CLIFF_EDGE_GATE', 'CIANWOOD_CITY')][2], _w[('CLIFF_EDGE_GATE', 'JOHTO_ROUTE_47')][2]}")
_x = _w[("JOHTO_ROUTE_47", "CLIFF_EDGE_GATE")]
check(_x[:2] == (96, 64) and _x[2][0] >= 83 and _x[3] >= {"CLIFF_EDGE_GATE", "JOHTO_CLIFF_CAVE", "JOHTO_EMBEDDED_TOWER", "JOHTO_ROUTE_48"} and _x[4] >= {(36, 12), (67, 31), (53, 38), (71, 40)}
      and _w[("JOHTO_ROUTE_47", "JOHTO_ROUTE_48")][2][1] <= 1,
      f"Route 47: exact map; in from the Cliff Edge Gate (east) at {_x[2]}; Cliff Cave, the Embedded Tower, Route 48 north; four trainers on the game's spots")
_x = _w[("JOHTO_ROUTE_48", "JOHTO_ROUTE_47")]
check(_x[:2] == (64, 32) and _x[2][1] >= 30 and _x[3] == {"JOHTO_ROUTE_47", "SAFARI_ZONE_GATE"} and _w[("JOHTO_ROUTE_48", "SAFARI_ZONE_GATE")][2][1] <= 1,
      f"Route 48: exact map; in from Route 47 (south) at {_x[2]}; the long bridge north to the Safari Zone Gate")
_cc = {}
for _i, _name in enumerate(("upper", "middle", "lower")):  # (Route 47's three mouths in reading order)
    _c.ENTRANCE_INDEX, _c.ENTRANCE_COUNT = _i, 3
    _cv = kanto("JOHTO_CLIFF_CAVE", came="JOHTO_ROUTE_47")
    _cc[_name] = tuple(_cv.run.player)
_c.ENTRANCE_INDEX = _c.ENTRANCE_COUNT = 0
check(_near_mm(_cc["upper"], (6, 29)) and _near_mm(_cc["middle"], (6, 7)) and _near_mm(_cc["lower"], (26, 13)),
      f"Cliff Cave: each of Route 47's three mouths leads to its own level inside {_cc}")
_tf = {}
for _i, _name in enumerate(("east", "west")):  # (Route 27's two mouths in reading order)
    _c.ENTRANCE_INDEX, _c.ENTRANCE_COUNT = _i, 2
    _tj = kanto("TOHJO_FALLS", came="KANTO_ROUTE_27")
    _tf[_name] = tuple(_tj.run.player)
_c.ENTRANCE_INDEX = _c.ENTRANCE_COUNT = 0
check(_tj.run.n_floors == 2 and _near_mm(_tf["east"], (28, 19)) and _near_mm(_tf["west"], (13, 21)) and {v for v in _tj.run.floor.exits.values() if not str(v).startswith("WARP")} == {"KANTO_ROUTE_27"}
      and ((_tj.recipe.get("art") or {}).get("figure_floors") or {}).get("Waterfall Cave") == 1,
      f"Tohjo Falls: SoulSilver's falls and the hidden room; each of Route 27's mouths leads to its own {_tf}; Giovanni waits in the hidden room")
_et = kanto("JOHTO_EMBEDDED_TOWER", came="JOHTO_ROUTE_47")
check((_et.run.floor.w, _et.run.floor.h) == (17, 28) and _et.run.player[1] >= 23 and set(_et.run.floor.exits.values()) == {"JOHTO_ROUTE_47"}
      and len(((_et.recipe.get("art") or {}).get("floors") or [{}])[0].get("people") or []) == 3,
      f"Embedded Tower: SoulSilver's chamber; in from Route 47 at {_et.run.player}; Groudon, Kyogre and Rayquaza each have a spot")
_dd = kanto("DRAGONS_DEN", came="BLACKTHORN_CITY")
_dd_in = (_dd.run.index, _dd.run.player)
_dd2 = kanto("DRAGONS_DEN", came="DRAGON_SHRINE")
check(_dd.run.n_floors == 2 and _dd_in[0] == 0 and _dd_in[1][1] >= 6 and _dd2.run.index == 1 and abs(_dd2.run.player[0] - 24) <= 1 and _dd2.run.player[1] >= 49
      and "DRAGON_SHRINE" in _dd2.run.floor.exits.values(),
      f"Dragon's Den: exact 1F and B1F; in from Blackthorn at {_dd_in}; back out of the shrine at its door on B1F {_dd2.run.player}")
_r45 = kanto("JOHTO_ROUTE_45", came="BLACKTHORN_CITY")
check((_r45.run.floor.w, _r45.run.floor.h) == (32, 160) and {"BLACKTHORN_CITY", "DARK_CAVE", "JOHTO_ROUTE_46"} == set(_r45.run.floor.exits.values()) and _r45.run.player[1] <= 2,
      f"Route 45: exact map; in from Blackthorn (north) at {_r45.run.player}; the Dark Cave's mouth, west to Route 46")
_r46 = kanto("JOHTO_ROUTE_46", came="JOHTO_ROUTE_29")
check((_r46.run.floor.w, _r46.run.floor.h) == (32, 64) and {"DARK_CAVE", "JOHTO_ROUTE_45", "JOHTO_ROUTE_29"} == set(_r46.run.floor.exits.values()) and _r46.run.player[1] >= 57,
      f"Route 46: exact map; in from Route 29's gate (south) at {_r46.run.player}; the Dark Cave's mouth, east to Route 45")
_r27 = kanto("KANTO_ROUTE_27", came="NEW_BARK_TOWN")
check((_r27.run.floor.w, _r27.run.floor.h) == (126, 20) and {"NEW_BARK_TOWN", "TOHJO_FALLS", "KANTO_ROUTE_26"} == set(_r27.run.floor.exits.values()) and _r27.run.player[0] <= 2,
      f"Route 27: exact map; in from New Bark by Surf (west) at {_r27.run.player}; Tohjo Falls' two mouths, east to Route 26")
_sw = [(m.x, m.y) for f in _r27.run.floors for m in f.movers if m.kind == "trainer" and "Swimmer Glenn" in str(m.payload)]
check(_sw == [(102, 10)] or (102, 10) in {(m.x, m.y) for f in _r27.run.floors for m in f.movers if m.kind == "trainer"},
      f"Route 27: the swimmer out in the channel by the long bridge {_sw}")
_r26 = kanto("KANTO_ROUTE_26", came="KANTO_ROUTE_27")
check((_r26.run.floor.w, _r26.run.floor.h) == (31, 126) and {"POKEMON_LEAGUE_GATE", "KANTO_ROUTE_27"} == set(_r26.run.floor.exits.values()) and _r26.run.player[1] >= 110,
      f"Route 26: exact map; in from Route 27 over the long bridge at {_r26.run.player}; the Reception Gate north")
_rt = kanto("RADIO_TOWER", came="GOLDENROD_CITY")
_rt.run.player = (13, 3)
_rt_in = _rt.run.player
check(_rt.run.n_floors == 6 and "GOLDENROD_CITY" in _rt.run.floor.exits.values(), "the Radio Tower: exact 1F-5F and the Observation Deck; in from Goldenrod on 1F")
_ms = kanto("MT_SILVER", came="MT_SILVER_CITY")
check((_ms.run.floor.w, _ms.run.floor.h) == (64, 57) and _ms.run.player[1] >= 50 and {"MT_SILVER_CITY", "MT_SILVER_2F", "MT_SILVER_MOLTRES", "MT_SILVER_EXPERT", "MT_SILVER_LOWER"} == set(_ms.run.floor.exits.values()),
      f"Mt. Silver 1F: exact; in from the Pokemon Center at its foot {_ms.run.player}; 2F, Moltres's and the Expert Belt's chambers, three ways onto the mountainside")
_ms2 = kanto("MT_SILVER_2F", came="MT_SILVER")
check(abs(_ms2.run.player[0] - 22) <= 1 and 22 <= _ms2.run.player[1] <= 26, f"Mt. Silver 2F: in from 1F on the crater's floor {_ms2.run.player}")
from src.dungeon import core as _c
_c.ENTRANCE_INDEX = 4
_msu = kanto("MT_SILVER_UPPER", came="MT_SILVER_2F")
_c.ENTRANCE_INDEX = 1
_msl = kanto("MT_SILVER_LOWER", came="MT_SILVER")
_c.ENTRANCE_INDEX = 0
check(abs(_msu.run.player[0] - 18) <= 1 and 40 <= _msu.run.player[1] <= 41 and abs(_msl.run.player[0] - 18) <= 1 and abs(_msl.run.player[1] - 24) <= 1,
      f"Mt. Silver: each mouth leads to its own (2F's fifth onto the mountainside's low mouth {_msu.run.player}; 1F's middle opening to the Lower Mountainside's middle level {_msl.run.player})")
_champ = story.story_flags.get("beat_johto_champion")
story.story_flags["beat_johto_champion"] = True
_mo = kanto("MT_SILVER_MOLTRES", came="MT_SILVER")
_su = kanto("MT_SILVER_SUMMIT", came="MT_SILVER_3F")
story.story_flags["beat_johto_champion"] = _champ
_figs = ([(m.x, m.y, str(m.payload.get("text"))) for m in _mo.run.floor.movers if m.kind == "figure"], [(m.x, m.y, str(m.payload.get("text"))) for m in _su.run.floor.movers if m.kind == "figure"])
check([(m.x, m.y) for m in _mo.run.floor.movers if m.kind == "figure" and m.payload.get("action") == "BOSS"] == [(12, 14)]
      and [(m.x, m.y) for m in _su.run.floor.movers if m.kind == "figure" and "RED" in str(m.payload.get("text"))] == [(20, 2)],
      f"Mt. Silver: Moltres in the pit of its chamber; Red at the summit {_figs}")
_had = story.inventory.pop("HM_ROCK_CLIMB", 0)
_m3 = kanto("MT_SILVER_3F", came="MT_SILVER_UPPER")
_walls = sum(1 for w in _m3.run.floor.decor.values() if str(w).startswith("climb:"))
story.inventory["HM_ROCK_CLIMB"] = 1
_m3._clear_boulders()
_left = sum(1 for w in _m3.run.floor.decor.values() if str(w).startswith("climb:"))
story.inventory.pop("HM_ROCK_CLIMB", None)
if _had:
    story.inventory["HM_ROCK_CLIMB"] = _had
check(_walls == 15 and _left == 0 and _m3.run.floor.walkable(15, 10), f"Mt. Silver 3F: the towering cliff waits for Rock Climb ({_walls} footholds), then it's climbable")
_h101 = kanto("HOENN_ROUTE_101", came="LITTLEROOT_TOWN")
check((_h101.run.floor.w, _h101.run.floor.h) == (20, 20) and {"LITTLEROOT_TOWN", "OLDALE_TOWN"} == set(_h101.run.floor.exits.values()) and _h101.run.player[1] >= 17,
      f"Hoenn Route 101: from the Emerald map; in from Littleroot (south) at {_h101.run.player}; Oldale north")
_h102 = kanto("HOENN_ROUTE_102", came="OLDALE_TOWN")
_t102 = {str(m.payload) for m in _h102.run.floor.movers if m.kind == "trainer"}
check((_h102.run.floor.w, _h102.run.floor.h) == (50, 20) and {"PETALBURG_CITY", "OLDALE_TOWN"} == set(_h102.run.floor.exits.values()) and _h102.run.player[0] >= 46 and len(_t102) == 3,
      f"Hoenn Route 102: from the Emerald map; in from Oldale (east) at {_h102.run.player}; Petalburg west; {len(_t102)} trainers standing where the picture has them")
_h103 = kanto("HOENN_ROUTE_103", came="OLDALE_TOWN")
check((_h103.run.floor.w, _h103.run.floor.h) == (80, 22) and {"OLDALE_TOWN", "HOENN_ALTERING_CAVE", "HOENN_ROUTE_110"} == set(_h103.run.floor.exits.values()) and _h103.run.player[1] >= 19 and _h103.run.player[0] <= 14,
      f"Hoenn Route 103: from the Emerald map; in from Oldale (south) at {_h103.run.player}; Altering Cave north, Route 110 across the water")
from src.dungeon import core as _c
_w104, _pw = {}, {}
for _i in range(3):
    _c.ENTRANCE_INDEX = _i
    _w104[_i] = kanto("HOENN_ROUTE_104", came="HOENN_PETALBURG_WOODS").run.player
    _c.ENTRANCE_INDEX = _i
    _pw[_i] = kanto("HOENN_PETALBURG_WOODS", came="HOENN_ROUTE_104").run.player
_c.ENTRANCE_INDEX = 0
_h104 = kanto("HOENN_ROUTE_104", came="PETALBURG_CITY")
check((_h104.run.floor.w, _h104.run.floor.h) == (40, 80) and _h104.run.player[0] >= 37 and 60 <= _h104.run.player[1] <= 64
      and {"RUSTBORO_CITY", "PETALBURG_CITY", "HOENN_PETALBURG_WOODS", "DEWFORD_TOWN", "HOENN_ROUTE_105"} == set(_h104.run.floor.exits.values()),
      f"Hoenn Route 104: read from the Emerald map; in from Petalburg (east) at {_h104.run.player}; the Woods, Rustboro, Briney's dock and the sea south")
check(_w104[0][1] <= 30 and _w104[1][0] <= 12 and 38 <= _w104[1][1] <= 41 and _w104[2][0] >= 31 and _pw[0][1] <= 2 and _pw[1][0] <= 18 and _pw[1][1] >= 41 and _pw[2][0] >= 35 and _pw[2][1] >= 41,
      f"Petalburg Woods and Route 104: each of the three doors leads to its own (Route 104 side {_w104}; Woods side {_pw})")
_hpw = kanto("HOENN_PETALBURG_WOODS", came="HOENN_ROUTE_104")
_tpw = {str(m.payload) for m in _hpw.run.floor.movers if m.kind == "trainer"}
check((_hpw.run.floor.w, _hpw.run.floor.h) == (48, 44) and len(_tpw) == 3, f"Petalburg Woods: read from the Emerald map, 48 x 44; {len(_tpw)} trainers")
_h116 = kanto("HOENN_ROUTE_116", came="RUSTBORO_CITY")
check((_h116.run.floor.w, _h116.run.floor.h) == (100, 20) and _h116.run.player[0] <= 2 and {"RUSTBORO_CITY", "HOENN_RUSTURF_TUNNEL"} == set(_h116.run.floor.exits.values())
      and sum(1 for v in _h116.run.floor.exits.values() if v == "HOENN_RUSTURF_TUNNEL") == 2,
      f"Hoenn Route 116: from the Emerald map; in from Rustboro (west) at {_h116.run.player}; Rusturf Tunnel's two mouths")
_rtw, _rte = {}, {}
for _i in range(2):
    _c.ENTRANCE_INDEX = _i
    _rtw[_i] = kanto("HOENN_RUSTURF_TUNNEL", came="HOENN_ROUTE_116").run.player
    _c.ENTRANCE_INDEX = _i
    _rte[_i] = kanto("HOENN_ROUTE_116", came="HOENN_RUSTURF_TUNNEL").run.player
_c.ENTRANCE_INDEX = 0
_hrt = kanto("HOENN_RUSTURF_TUNNEL", came="HOENN_ROUTE_116")
check((_hrt.run.floor.w, _hrt.run.floor.h) == (36, 24) and {"HOENN_ROUTE_116", "VERDANTURF_TOWN"} == set(_hrt.run.floor.exits.values())
      and _rtw[0][0] <= 6 and _rtw[1][0] >= 27 and _rte[0][0] <= 48 and _rte[1][0] >= 64,
      f"Rusturf Tunnel: from the Emerald map; Route 116's two mouths each lead to their own (tunnel side {_rtw}; route side {_rte}); Verdanturf below")
_h106 = kanto("HOENN_ROUTE_106", came="DEWFORD_TOWN")
check((_h106.run.floor.w, _h106.run.floor.h) == (80, 20) and _h106.run.player[1] >= 17 and {"DEWFORD_TOWN", "HOENN_GRANITE_CAVE", "HOENN_ROUTE_105"} == set(_h106.run.floor.exits.values()),
      f"Hoenn Route 106: read from the Emerald map; in from Dewford (south) at {_h106.run.player}; Granite Cave's mouth, Surf north to Route 105")
_hgc = kanto("HOENN_GRANITE_CAVE", came="HOENN_ROUTE_106")
_gc_at = (_hgc.run.index, tuple(_hgc.run.player), (_hgc.run.floor.w, _hgc.run.floor.h))
check(_hgc.run.n_floors == 4 and _gc_at[0] == 1 and _gc_at[2] == (42, 15) and _gc_at[1][0] == 37 and "HOENN_ROUTE_106" in _hgc.run.floor.exits.values(),
      f"Granite Cave: four floors from the Emerald maps; in from Route 106 onto 1F at {_gc_at}")
_ms_had = story.story_flags.pop("met_steven", None)
_hgc = kanto("HOENN_GRANITE_CAVE", came="HOENN_ROUTE_106")
_hgc._clear_boulders()  # (as every step does)
_gc_shut = not _hgc.run.floor.walkable(12, 12) and str(_hgc.run.floor.decor.get((12, 12), "")).startswith("rubble:")
story.story_flags["met_steven"] = True
_hgc._clear_boulders()
_gc_open = _hgc.run.floor.walkable(12, 12) and (12, 12) not in _hgc.run.floor.decor
if _ms_had is None:
    story.story_flags.pop("met_steven", None)
check(_gc_shut and _gc_open, f"Granite Cave 1F: fallen rocks bar the short way to Steven's side ({_gc_shut}); gone once you've met him ({_gc_open})")
_h109 = kanto("HOENN_ROUTE_109", came="SLATEPORT_CITY")
check((_h109.run.floor.w, _h109.run.floor.h) == (40, 63) and _h109.run.player[1] <= 3 and {"SLATEPORT_CITY", "HOENN_ROUTE_108"} == set(_h109.run.floor.exits.values()),
      f"Hoenn Route 109: from the Emerald map; in from Slateport (north) at {_h109.run.player}; Surf west to Route 108")
_h110 = kanto("HOENN_ROUTE_110", came="SLATEPORT_CITY")
_h110n = kanto("HOENN_ROUTE_110", came="MAUVILLE_CITY")
check((_h110.run.floor.w, _h110.run.floor.h) == (40, 100) and _h110.run.player[1] >= 96 and _h110n.run.player[1] <= 2
      and {"SLATEPORT_CITY", "MAUVILLE_CITY", "HOENN_ROUTE_103"} <= set(_h110.run.floor.exits.values()) and "HOENN_NEW_MAUVILLE" not in _h110.run.floor.exits.values(),
      f"Hoenn Route 110: read from the Emerald map; in from Slateport (south) at {_h110.run.player}, from Mauville (north) at {_h110n.run.player}")
_bk_had = story.inventory.pop("BICYCLE", None)
_h110._clear_boulders()  # (as every step does)
_bar110 = [str(_h110.run.floor.decor.get(t, "")) for t in ((15, 17), (16, 89))]
story.inventory["BICYCLE"] = 1
_h110._clear_boulders()
_open110 = [_h110.run.floor.walkable(*t) for t in ((15, 17), (16, 89))]
if _bk_had is None:
    story.inventory.pop("BICYCLE", None)
else:
    story.inventory["BICYCLE"] = _bk_had
_h110._clear_boulders()
check(_h110.run.n_floors == 2 and all(b.startswith("barrier:") for b in _bar110) and all(_open110) and len(_h110._overheads()) == 1
      and sum(1 for v in _h110.run.floor.exits.values() if v == core.STAIRS) == 2,
      f"Hoenn Route 110: the Seaside Cycling Road is its own layer overhead; its two gates are barred without a Bicycle {_bar110} and open with one {_open110}")
_f110 = _h110.run.floor
_seen110, _todo110 = {tuple(_h110.run.player)}, [tuple(_h110.run.player)]
while _todo110:
    _x, _y = _todo110.pop()
    for _dx, _dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        _n = (_x + _dx, _y + _dy)
        if _n not in _seen110 and 0 <= _n[0] < _f110.w and 0 <= _n[1] < _f110.h and _f110.tiles[_n[1]][_n[0]] in (core.FLOOR, core.GRASS):
            _seen110.add(_n); _todo110.append(_n)
_north110 = [t for t, v in _f110.exits.items() if v == "MAUVILLE_CITY"]
check(any(abs(t[0] - n[0]) + abs(t[1] - n[1]) == 1 for t in _seen110 for n in _north110), "Hoenn Route 110: you can walk from Slateport to Mauville without Surf (the path under the Cycling Road)")
_h117 = kanto("HOENN_ROUTE_117", came="MAUVILLE_CITY")
check((_h117.run.floor.w, _h117.run.floor.h) == (60, 20) and _h117.run.player[0] >= 56 and {"MAUVILLE_CITY", "VERDANTURF_TOWN"} == set(_h117.run.floor.exits.values())
      and "door:daycare" in _h117.run.floor.decor.values(),
      f"Hoenn Route 117: from the Emerald map; in from Mauville (east) at {_h117.run.player}; the Day Care's door; Verdanturf west")
_h111 = kanto("HOENN_ROUTE_111", came="MAUVILLE_CITY")
_a111, _a112 = {}, {}
for _i in range(2):
    _c.ENTRANCE_INDEX = _i
    _a111[_i] = kanto("HOENN_ROUTE_111", came="HOENN_ROUTE_112").run.player
    _c.ENTRANCE_INDEX = _i
    _a112[_i] = kanto("HOENN_ROUTE_112", came="HOENN_ROUTE_111").run.player
_c.ENTRANCE_INDEX = 0
check((_h111.run.floor.w, _h111.run.floor.h) == (40, 140) and _h111.run.player[1] >= 136
      and {"MAUVILLE_CITY", "HOENN_ROUTE_112", "HOENN_ROUTE_113", "HOENN_MIRAGE_TOWER"} == set(_h111.run.floor.exits.values())
      and any(m.kind == "figure" and "DESERT" in str(m.payload.get("text")) for m in _h111.run.floor.movers) is not None,
      f"Hoenn Route 111: read from the Emerald map, desert and all; in from Mauville (south) at {_h111.run.player}")
check(_a111[0][1] < 40 and _a111[1][1] > 60 and _a112[0][1] < 15 and _a112[1][1] > 45,
      f"Hoenn Routes 111 and 112: the meadow and the junction each lead to their own (Route 111 side {_a111}; Route 112 side {_a112})")
def _reach111(p):
    f = p.run.floor
    seen, todo = {tuple(p.run.player)}, [tuple(p.run.player)]
    while todo:
        x, y = todo.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if n not in seen and 0 <= n[0] < f.w and 0 <= n[1] < f.h and f.tiles[n[1]][n[0]] in (core.FLOOR, core.GRASS):
                seen.add(n); todo.append(n)
    return seen
_gg_had = story.inventory.pop("GO_GOGGLES", None)
_h111 = kanto("HOENN_ROUTE_111", came="MAUVILLE_CITY")
_h111._clear_boulders()  # (as every step does)
_dry = _reach111(_h111)
story.inventory["GO_GOGGLES"] = 1
_h111._clear_boulders()
_wet = _reach111(_h111)
if _gg_had is None:
    story.inventory.pop("GO_GOGGLES", None)
check((20, 50) not in _dry and (1, 9) not in _dry and (1, 69) in _dry and (20, 50) in _wet and (1, 9) in _wet
      and str(_h111.run.floor.decor.get((10, 62), "")) == "",
      f"Hoenn Route 111: a sandstorm bars the desert without the Go-Goggles (the junction to Route 112 stays open); with them you can cross to Route 113")
_c.ENTRANCE_INDEX = 1
_h112 = kanto("HOENN_ROUTE_112", came="HOENN_ROUTE_111")
_c.ENTRANCE_INDEX = 0
_f112 = _h112.run.floor
_seen112, _todo112 = {tuple(_h112.run.player)}, [tuple(_h112.run.player)]
while _todo112:
    _x, _y = _todo112.pop()
    for _dx, _dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        _n = (_x + _dx, _y + _dy)
        if _n not in _seen112 and 0 <= _n[0] < _f112.w and 0 <= _n[1] < _f112.h and _f112.tiles[_n[1]][_n[0]] in (core.FLOOR, core.GRASS):
            _seen112.add(_n); _todo112.append(_n)
_near112 = lambda who: any(abs(t[0] - n[0]) + abs(t[1] - n[1]) == 1 for n in _seen112 for t, v in _f112.exits.items() if v == who)
check((_f112.w, _f112.h) == (40, 60) and _h112.run.player[0] >= 37 and _h112.run.player[1] > 45 and not _near112("LAVARIDGE_TOWN") and not _near112("HOENN_JAGGED_PASS") and _near112("HOENN_FIERY_PATH") and "ledge:1,0" in _f112.decor.values()
      and (39, 8) not in _seen112 and (38, 9) not in _seen112 and "door:cablecar" in _f112.decor.values() and sum(1 for v in _f112.exits.values() if v == "HOENN_FIERY_PATH") == 2,
      f"Hoenn Route 112: read from the Emerald map; in from Route 111 (east) at {_h112.run.player}; you can walk to the Fiery Path, but not to the north meadow, nor west past the ledges to Lavaridge and the Jagged Pass (they hop east only); the Cable Car's door")
_fpa, _fpb = {}, {}
for _i in range(2):
    _c.ENTRANCE_INDEX = _i
    _fpa[_i] = kanto("HOENN_FIERY_PATH", came="HOENN_ROUTE_112").run.player
    _c.ENTRANCE_INDEX = _i
    _fpb[_i] = kanto("HOENN_ROUTE_112", came="HOENN_FIERY_PATH").run.player
_c.ENTRANCE_INDEX = 0
_hfp = kanto("HOENN_FIERY_PATH", came="HOENN_ROUTE_112")
check((_hfp.run.floor.w, _hfp.run.floor.h) == (35, 38) and {"HOENN_ROUTE_112", "HOENN_MT_CHIMNEY"} == set(_hfp.run.floor.exits.values())
      and _fpa[0][1] < 10 and _fpa[1][1] > 34 and _fpb[0][1] < 14 and _fpb[1][1] > 34,
      f"The Fiery Path: from the Emerald map; Route 112's two mouths each lead to their own (cave side {_fpa}; route side {_fpb})")
_h113 = kanto("HOENN_ROUTE_113", came="HOENN_ROUTE_111")
check((_h113.run.floor.w, _h113.run.floor.h) == (100, 20) and _h113.run.player[0] >= 97 and {"HOENN_ROUTE_111", "FALLARBOR_TOWN"} == set(_h113.run.floor.exits.values()),
      f"Hoenn Route 113: read from the Emerald map; in from Route 111 (east) at {_h113.run.player}; Fallarbor west")
_h114 = kanto("HOENN_ROUTE_114", came="FALLARBOR_TOWN")
check((_h114.run.floor.w, _h114.run.floor.h) == (40, 80) and _h114.run.player[0] >= 37 and {"FALLARBOR_TOWN", "HOENN_METEOR_FALLS"} == set(_h114.run.floor.exits.values())
      and "door:fossil" in _h114.run.floor.decor.values(),
      f"Hoenn Route 114: read from the Emerald map; in from Fallarbor (east) at {_h114.run.player}; Meteor Falls at the canyon's end; the Fossil Maniac's door")
_hmf = kanto("HOENN_METEOR_FALLS", came="HOENN_ROUTE_114")
_hmf2 = kanto("HOENN_METEOR_FALLS", came="HOENN_ROUTE_115")
check((_hmf.run.floor.w, _hmf.run.floor.h) == (30, 42) and _hmf.run.player[0] >= 25 and _hmf2.run.player[1] >= 38 and {"HOENN_ROUTE_114", "HOENN_ROUTE_115"} == set(_hmf.run.floor.exits.values()),
      f"Meteor Falls: read from the Emerald map; in from Route 114 at {_hmf.run.player}, from Route 115 at {_hmf2.run.player}")
_h115 = kanto("HOENN_ROUTE_115", came="RUSTBORO_CITY")
check((_h115.run.floor.w, _h115.run.floor.h) == (40, 80) and _h115.run.player[1] >= 76 and {"RUSTBORO_CITY", "HOENN_METEOR_FALLS"} == set(_h115.run.floor.exits.values()),
      f"Hoenn Route 115: read from the Emerald map; in from Rustboro (south) at {_h115.run.player}; Meteor Falls up the canyon")
_hmc = kanto("HOENN_MT_CHIMNEY", came="HOENN_JAGGED_PASS")
check((_hmc.run.floor.w, _hmc.run.floor.h) == (40, 47) and _hmc.run.player[1] >= 39 and "HOENN_JAGGED_PASS" in _hmc.run.floor.exits.values() and "door:cablecar" in _hmc.run.floor.decor.values(),
      f"Mt. Chimney: read from the Emerald map; in from the Jagged Pass (south) at {_hmc.run.player}; the Cable Car's door")
_hjp = kanto("HOENN_JAGGED_PASS", came="HOENN_ROUTE_112")
_hjp2 = kanto("HOENN_JAGGED_PASS", came="HOENN_MT_CHIMNEY")
check((_hjp.run.floor.w, _hjp.run.floor.h) == (30, 46) and _hjp.run.player[1] >= 43 and _hjp2.run.player[1] <= 2
      and {"HOENN_ROUTE_112", "HOENN_MT_CHIMNEY", "HOENN_MAGMA_HIDEOUT"} == set(_hjp.run.floor.exits.values()),
      f"The Jagged Pass: read from the Emerald map; in from Route 112 (the foot) at {_hjp.run.player}, from Mt. Chimney (the top) at {_hjp2.run.player}")
_me_had = story.inventory.pop("MAGMA_EMBLEM", None)
_hjp._clear_boulders()  # (as every step does)
_hid = str(_hjp.run.floor.decor.get((16, 18), "")).startswith("barrier:") and not _hjp.run.floor.walkable(16, 18)
story.inventory["MAGMA_EMBLEM"] = 1
_hjp._clear_boulders()
_shown = (16, 18) not in _hjp.run.floor.decor and _hjp.run.floor.exits.get((16, 18)) == "HOENN_MAGMA_HIDEOUT"
if _me_had is None:
    story.inventory.pop("MAGMA_EMBLEM", None)
from src.dungeon import art as _lava_art
check(_hid and _shown and "*" in _lava_art.BLOCK, f"The Jagged Pass: the Magma Hideout's door is plain rock without the Magma Emblem ({_hid}) and opens with it ({_shown}); lava is its own tile, in the way")
_hjp = kanto("HOENN_JAGGED_PASS", came="HOENN_ROUTE_112")
_fj = _hjp.run.floor
_led = next((t for t, w in sorted(_fj.decor.items()) if w == "ledge:0,1" and _fj.walkable(t[0], t[1] - 1) and _fj.walkable(t[0], t[1] + 1)
             and _fj.mover_at(t[0], t[1] - 1) is None and _fj.mover_at(t[0], t[1] + 1) is None), None)
_hjp.run.player = (_led[0], _led[1] + 1); _hjp.anim = 0; _hjp.sliding = None
_hjp.step(0, -1)
_up = tuple(_hjp.run.player)
_hjp.run.player = (_led[0], _led[1] - 1); _hjp.anim = 0
_hjp.step(0, 1)
_down, _hopping = tuple(_hjp.run.player), _hjp.hop
check(_up == (_led[0], _led[1] + 1) and _down == (_led[0], _led[1] + 1) and _hopping,
      f"The Jagged Pass: a ledge at {_led} can't be climbed from below ({_up}) but you hop down over it ({_down}, hopping {_hopping})")
_h118 = kanto("HOENN_ROUTE_118", came="MAUVILLE_CITY")
check((_h118.run.floor.w, _h118.run.floor.h) == (80, 20) and _h118.run.player[0] <= 2 and {"MAUVILLE_CITY", "HOENN_ROUTE_119", "HOENN_ROUTE_123"} == set(_h118.run.floor.exits.values()),
      f"Hoenn Route 118: read from the Emerald map; in from Mauville (west) at {_h118.run.player}; Route 119 north and Route 123 east across the water")
_h119 = kanto("HOENN_ROUTE_119", came="HOENN_ROUTE_118")
_f119 = _h119.run.floor
_s119, _t119 = {tuple(_h119.run.player)}, [tuple(_h119.run.player)]
while _t119:
    _x, _y = _t119.pop()
    for _dx, _dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        _n = (_x + _dx, _y + _dy)
        if _n not in _s119 and 0 <= _n[0] < _f119.w and 0 <= _n[1] < _f119.h and _f119.tiles[_n[1]][_n[0]] in (core.FLOOR, core.GRASS):
            _s119.add(_n); _t119.append(_n)
check((_f119.w, _f119.h) == (40, 140) and _h119.run.player[1] >= 136 and {"HOENN_ROUTE_118", "FORTREE_CITY"} == set(_f119.exits.values())
      and any(abs(t[0] - n[0]) + abs(t[1] - n[1]) == 1 for n in _s119 for t, v in _f119.exits.items() if v == "FORTREE_CITY") and "door:weather" in _f119.decor.values(),
      f"Hoenn Route 119: read from the Emerald map; in from Route 118 (south) at {_h119.run.player}; you can walk the bridges to Fortree without Surf; the Weather Institute's door")
_h120 = kanto("HOENN_ROUTE_120", came="FORTREE_CITY")
check((_h120.run.floor.w, _h120.run.floor.h) == (40, 100) and _h120.run.player[0] <= 2 and {"FORTREE_CITY", "HOENN_ROUTE_121", "HOENN_SCORCHED_SLAB"} == set(_h120.run.floor.exits.values()),
      f"Hoenn Route 120: read from the Emerald map; in from Fortree (west) at {_h120.run.player}; Route 121 east, the Scorched Slab on the pond")
_h121 = kanto("HOENN_ROUTE_121", came="HOENN_ROUTE_120")
check((_h121.run.floor.w, _h121.run.floor.h) == (80, 20) and _h121.run.player[0] <= 2 and {"HOENN_ROUTE_120", "LILYCOVE_CITY", "HOENN_ROUTE_122"} == set(_h121.run.floor.exits.values())
      and "door:safari" in _h121.run.floor.decor.values(),
      f"Hoenn Route 121: read from the Emerald map; in from Route 120 (west) at {_h121.run.player}; Lilycove east, the pier to Route 122, the Safari Zone's door")
_h122 = kanto("HOENN_ROUTE_122", came="HOENN_ROUTE_121")
_h122s = kanto("HOENN_ROUTE_122", came="HOENN_ROUTE_123")
check((_h122.run.floor.w, _h122.run.floor.h) == (40, 40) and _h122.run.player[1] <= 1 and _h122s.run.player[1] >= 37
      and {"HOENN_ROUTE_121", "HOENN_MT_PYRE", "HOENN_ROUTE_123"} == set(_h122.run.floor.exits.values())
      and _h122s.run.floor.tiles[_h122s.run.player[1]][_h122s.run.player[0]] != core.SURF,
      f"Hoenn Route 122: read from the Emerald map; in across the sea from Route 121 (north) at {_h122.run.player}, on the strip of land from Route 123 (south) at {_h122s.run.player}; Mt. Pyre's door")
_pyre = kanto("HOENN_MT_PYRE", came="HOENN_ROUTE_122")
_pyre_who = [(m.payload.get("text") if isinstance(m.payload, dict) else m.payload[1].get("name")) for m in _pyre.run.floor.movers if m.kind in ("figure", "trainer")]
check(_pyre.run.n_floors == 2 and _pyre.run.index == 0 and (_pyre.run.floor.w, _pyre.run.floor.h) == (38, 51) and abs(_pyre.run.player[0] - 10) <= 1 and 41 <= _pyre.run.player[1] <= 44
      and "HOENN_ROUTE_122" in _pyre.run.floor.exits.values() and "Hex Maniac Leah" in _pyre_who and "THE BLACK FOG" in _pyre_who
      and "Admin Courtney" not in _pyre_who and "TALK TO THE ELDERS" not in _pyre_who,
      f"Mt. Pyre: the mountainside and the summit from the Emerald maps; in from Route 122 at its door {_pyre.run.player}; on the mountainside {_pyre_who}, Courtney and the elders up on the summit")
_h123 = kanto("HOENN_ROUTE_123", came="HOENN_ROUTE_122")
_h123w = kanto("HOENN_ROUTE_123", came="HOENN_ROUTE_118")
_hops123 = [v for v in _h123.run.floor.decor.values() if str(v).startswith("ledge:")]
check((_h123.run.floor.w, _h123.run.floor.h) == (140, 20) and _h123.run.player[1] <= 1 and 119 <= _h123.run.player[0] <= 121 and _h123w.run.player[0] <= 1
      and {"HOENN_ROUTE_118", "HOENN_ROUTE_122"} == set(_h123.run.floor.exits.values()) and "ledge:-1,0" in _hops123 and "ledge:0,1" in _hops123,
      f"Hoenn Route 123: read from the Emerald map; in from Route 122 (north) at {_h123.run.player}, from Route 118 (west) at {_h123w.run.player}; ledges hopped south and west ({len(_hops123)})")
_h124 = kanto("HOENN_ROUTE_124", came="LILYCOVE_CITY")
_sea124 = [_h124.run.floor.tiles[y][x] == core.SURF for (x, y) in _h124.run.floor.exits]
check((_h124.run.floor.w, _h124.run.floor.h) == (80, 80) and _h124.run.player[0] <= 1 and {"LILYCOVE_CITY", "MOSSDEEP_CITY", "HOENN_ROUTE_126"} == set(_h124.run.floor.exits.values())
      and _sea124 and all(_sea124),
      f"Hoenn Route 124: read from the Emerald map; in from Lilycove (west) at {_h124.run.player}; Mossdeep east and Route 126 south, every way out across the water ({len(_sea124)} tiles)")
for _k, _came, _size, _outs in (("HOENN_ROUTE_125", "MOSSDEEP_CITY", (80, 40), {"MOSSDEEP_CITY", "HOENN_SHOAL_CAVE"}),
                               ("HOENN_ROUTE_126", "HOENN_ROUTE_124", (80, 80), {"HOENN_ROUTE_124", "HOENN_ROUTE_127"}),
                               ("HOENN_ROUTE_127", "MOSSDEEP_CITY", (80, 80), {"MOSSDEEP_CITY", "HOENN_ROUTE_126", "HOENN_ROUTE_128"}),
                               ("HOENN_ROUTE_128", "HOENN_ROUTE_127", (120, 40), {"HOENN_ROUTE_127", "HOENN_ROUTE_129", "EVER_GRANDE_CITY"}),
                               ("HOENN_ROUTE_107", "DEWFORD_TOWN", (60, 20), {"DEWFORD_TOWN", "HOENN_ROUTE_108"}),
                               ("HOENN_ROUTE_108", "HOENN_ROUTE_107", (80, 20), {"HOENN_ROUTE_107", "HOENN_ROUTE_109", "HOENN_ABANDONED_SHIP"}),
                               ("HOENN_ROUTE_129", "HOENN_ROUTE_128", (80, 40), {"HOENN_ROUTE_128", "HOENN_ROUTE_130"}),
                               ("HOENN_ROUTE_130", "HOENN_ROUTE_129", (80, 40), {"HOENN_ROUTE_129", "HOENN_ROUTE_131"}),
                               ("HOENN_ROUTE_131", "HOENN_ROUTE_130", (60, 40), {"HOENN_ROUTE_130", "PACIFIDLOG_TOWN"}),
                               ("HOENN_ROUTE_132", "PACIFIDLOG_TOWN", (80, 40), {"PACIFIDLOG_TOWN", "HOENN_ROUTE_133"}),
                               ("HOENN_ROUTE_133", "HOENN_ROUTE_132", (80, 40), {"HOENN_ROUTE_132", "HOENN_ROUTE_134"}),
                               ("HOENN_ROUTE_134", "HOENN_ROUTE_133", (80, 40), {"HOENN_ROUTE_133", "SLATEPORT_CITY"}),
                               ("HOENN_ROUTE_105", "HOENN_ROUTE_104", (40, 80), {"HOENN_ROUTE_104", "HOENN_ROUTE_106"})):
    _sr = kanto(_k, came=_came)
    _f = _sr.run.floor
    _at = [t for t, v in _f.exits.items() if v == _came]
    _swim = [m for m in _f.movers if m.kind == "trainer"]
    check((_f.w, _f.h) == _size and set(_f.exits.values()) == _outs and _at and min(abs(t[0] - _sr.run.player[0]) + abs(t[1] - _sr.run.player[1]) for t in _at) <= 2
          and all(_f.tiles[y][x] == core.SURF for (x, y), v in _f.exits.items() if v == _came) and len(_swim) == 3,
          f"{_k}: the sea route from the Emerald map, {_size}; in from {_came} at {_sr.run.player}, beside its own way out across the water; ways out {sorted(set(_f.exits.values()))}; {len(_swim)} trainers")
# New Mauville lives in Mauville City now (Jordan, 11-11): a door in town, a small generator room with its content
_nm = kanto("HOENN_NEW_MAUVILLE", came="MAUVILLE_CITY")
_nm_who = {(m.payload[1] or {}).get("name") for m in _nm.run.floor.movers if m.kind == "trainer"} | {m.payload.get("text") for m in _nm.run.floor.movers if m.kind == "figure"}
check(set(_nm.run.floor.exits.values()) == {"MAUVILLE_CITY"} and _nm.run.player[1] >= 8 and {"Wattson", "Team Magma Grunt", "Team Aqua Grunt"} <= _nm_who,
      f"New Mauville: a room under Mauville City; in from town at {_nm.run.player}; inside {sorted(str(w) for w in _nm_who)}")
story.current_area_key, story.last_area_key = "MAUVILLE_CITY", "HOENN_NEW_MAUVILLE"
g.walk_town_pos = None
_mv = _CS(g); g.change_state(_mv); _tap_through(_mv)
_mv_door = [t for t, v in _mv.exits.items() if v == "HOENN_NEW_MAUVILLE"]
check(len(_mv_door) == 1 and abs(_mv_door[0][0] - _mv.player[0]) + abs(_mv_door[0][1] - _mv.player[1]) <= 2,
      f"Mauville City: New Mauville's door at {_mv_door}; out of it you stand beside it at {_mv.player}")
g.walk_town_pos = None
# the sea currents (Routes 132-134): they carry you their own way till something stops you
_cu = kanto("HOENN_ROUTE_132", came="PACIFIDLOG_TOWN")
_cf = _cu.run.floor
_cf.movers = []
_ways = set(_cf.current.values())
_c0 = next(t for t in sorted(_cf.current) if _cf.current[t] == (-1, 0) and _cf.current.get((t[0] - 1, t[1])) == (-1, 0) and _cf.current.get((t[0] - 2, t[1])) == (-1, 0)
           and _cf.tile(t[0] + 1, t[1]) == core.SURF and (t[0] + 1, t[1]) not in _cf.current and (t[0] + 1, t[1]) not in _cf.exits)
_cu.run.player, _cu.mode, _cu.anim, _cu.walk_goal = (_c0[0] + 1, _c0[1]), "MAP", 0, None
_cu.dialogue_box.visible = False
_cu.step(-1, 0)
_swept = bool(_cu.sliding)
for _ in range(900):
    _cu.update()
    if (not _cu.sliding and _cu.anim == 0) or _cu.run.player in _cf.exits:
        break
_cend = _cu.run.player
check(len(_cf.current) > 900 and (-1, 0) in _ways and len(_ways) >= 2 and _swept and _cend[0] <= _c0[0] - 2 and all(_cf.tiles[y][x] == core.SURF for x, y in _cf.current),
      f"Hoenn Route 132: {len(_cf.current)} current tiles ({sorted(_ways)}); stepping onto one at {_c0} you're carried on to {_cend} without a key pressed")
# Dive (Routes 124, 126, 127, 128): the dark deep water, the seabed floor under it, back up where there's open sea above
_had_dive = story.inventory.pop("HM_DIVE", None)
_dv = kanto("HOENN_ROUTE_126", came="HOENN_ROUTE_124")
_df = _dv.run.floor
_df.movers = []
_deep = sorted(_df.deep)
_dspot = _deep[len(_deep) // 2]
_dv.run.player, _dv.mode, _dv.anim, _dv.walk_goal = _dspot, "MAP", 0, None
_dv.dialogue_box.visible = False
_dact = _dv._act_here()
_dv.dive_here()
_no_dive = _dv.run.index
_dv.dialogue_box.visible = False
_dv.mode = "MAP"
story.inventory["HM_DIVE"] = 1
_dv.dive_here()
_down = (_dv.run.index, _dv.run.player)
_bed = _dv.run.floor
_bed_wild = {int(m.payload.id) for m in _bed.movers if m.kind == "wild" and hasattr(m.payload, "id")}
_bed.movers = []
_uact = _dv._act_here()
_bed_out = set(_bed.exits.values())
_dv.anim = 0
_dv.surface_here()
_upagain = (_dv.run.index, _dv.run.player)
check(_dv.run.n_floors == 2 and len(_deep) > 500 and _dact and _dact[0] == "DIVE" and _no_dive == 0 and _down == (1, _dspot) and _uact and _uact[0] == "SURFACE"
      and _bed_out == {"SOOTOPOLIS_CITY"} and _upagain == (0, _dspot) and _bed_wild <= {170, 171, 366, 369, 370},
      f"Hoenn Route 126: Dive on the deep water ({len(_deep)} tiles): not without the HM; with it down to the seabed at the same spot {_dspot}, its own wild Pokemon {sorted(_bed_wild)}, the way into Sootopolis down there; SURFACE brings you back up")
_from_soot = kanto("HOENN_ROUTE_126", came="SOOTOPOLIS_CITY")
_from_cav = kanto("HOENN_ROUTE_128", came="HOENN_SEAFLOOR_CAVERN")
_m126 = [t for t, v in _from_soot.run.floor.exits.items() if v == "SOOTOPOLIS_CITY"]
_m128 = [t for t, v in _from_cav.run.floor.exits.items() if v == "HOENN_SEAFLOOR_CAVERN"]
check(_from_soot.run.index == 1 and _m126 and abs(_m126[0][0] - _from_soot.run.player[0]) + abs(_m126[0][1] - _from_soot.run.player[1]) <= 2
      and _from_cav.run.index == 1 and _m128 and abs(_m128[0][0] - _from_cav.run.player[0]) + abs(_m128[0][1] - _from_cav.run.player[1]) <= 2,
      f"Dive: out of Sootopolis you're on Route 126's seabed by its mouth {_from_soot.run.player}; out of the Seafloor Cavern on Route 128's seabed {_from_cav.run.player}")
_sc = kanto("HOENN_ROUTE_134", came="HOENN_SEALED_CHAMBER")
check(_sc.run.index == 1 and "HOENN_SEALED_CHAMBER" in _sc.run.floor.exits.values() and len(_sc.run.made(0).deep) >= 2 and all(_sc.run.floor.walkable(*t) for t in _sc.run.made(0).deep),
      f"Hoenn Route 134: its dive spot ({len(_sc.run.made(0).deep)} tiles) leads down to the Sealed Chamber's mouth; out of the chamber you're on the seabed at {_sc.run.player}")
for _k in ("HOENN_ROUTE_124", "HOENN_ROUTE_127", "HOENN_ROUTE_128"):
    _dk = kanto(_k, came="HOENN_ROUTE_127" if _k == "HOENN_ROUTE_128" else "MOSSDEEP_CITY")
    _below = _dk.run.made(1)
    _fits = [t for t in _dk.run.floor.deep if _below.walkable(*t)]
    check(_dk.run.n_floors == 2 and len(_dk.run.floor.deep) > 50 and len(_fits) >= 0.9 * len(_dk.run.floor.deep) and _dk.run.index == 0,
          f"{_k}: two floors, the sea and its seabed; {len(_fits)} of its {len(_dk.run.floor.deep)} deep-water tiles have seabed to dive to")
story.inventory.pop("HM_DIVE", None)
if _had_dive:
    story.inventory["HM_DIVE"] = _had_dive
_vr = kanto("HOENN_VICTORY_ROAD", came="EVER_GRANDE_CITY")
# its log bridges have two levels: over one along its length, under it across its width, never from one to the other
_vf = _vr.run.floor
_vf.movers = []
_br = _vf.bridge
_bt = next(t for t in sorted(_br) if _br[t] == (1, 0) and _vf.walkable(t[0], t[1] - 1) and (t[0], t[1] - 1) not in _br and (t[0] - 1, t[1]) in _br)
_vr.run.player, _vr.run.deck = (_bt[0], _bt[1] - 1), True
_vr.run.step(0, 1)
_under = (_vr.run.player == _bt, _vr.run.deck)
while (_vr.run.player[0] - 1, _vr.run.player[1]) in _br:
    _vr.run.step(-1, 0)
_bend = _vr.run.player
_vr.run.step(-1, 0)
_no_climb = _vr.run.player == _bend and _vf.walkable(_bend[0] - 1, _bend[1])
_vr.run.player, _vr.run.deck = (_bend[0] - 1, _bend[1]), True
_vr.run.step(1, 0)
_on_deck = (_vr.run.player == _bend, _vr.run.deck)
while _vr.run.player != _bt:
    _vr.run.step(1, 0)
_vr.run.step(0, -1)
_no_drop = _vr.run.player == _bt
check(len(_br) >= 60 and _under == (True, False) and _no_climb and _on_deck == (True, True) and _no_drop,
      f"Victory Road 1F: {len(_br)} log-bridge tiles; stepping under one at {_bt} you can't climb onto its end at {_bend}, and crossing on its deck you can't step off its side")
_vr = kanto("HOENN_VICTORY_ROAD", came="EVER_GRANDE_CITY")
_vr_out = sorted(t for t, v in _vr.run.floor.exits.items() if v == "EVER_GRANDE_CITY")
check(_vr.run.n_floors == 3 and (_vr.run.floor.w, _vr.run.floor.h) == (46, 45) and len(_vr_out) == 2 and {(39, 6), (15, 41)} == set(_vr_out),
      f"Victory Road: three floors from the Emerald maps; in at {_vr.run.player}; two mouths back to Ever Grande {_vr_out} (the top one pairs with the League side)")
core.ENTRANCE_INDEX = 1  # (as leaving Ever Grande by its lower mouth sets it)
_vr_low = kanto("HOENN_VICTORY_ROAD", came="EVER_GRANDE_CITY")
_eg_at = []
for _i in (0, 1):  # (as leaving Victory Road by its top, then its bottom mouth sets it)
    g.walk_town_exit = ("HOENN_VICTORY_ROAD", _i, 2)
    g.walk_town_pos = None
    story.current_area_key, story.last_area_key = "EVER_GRANDE_CITY", "HOENN_VICTORY_ROAD"
    _eg2 = _CS(g); g.change_state(_eg2); _tap_through(_eg2)
    _eg_at.append(tuple(_eg2.player))
g.walk_town_pos = None
check(_vr_low.run.player[1] >= 39 and _eg_at[0][1] <= 29 and _eg_at[1][1] >= 40,
      f"Ever Grande and Victory Road: in by the lower mouth you start at the cave's foot {tuple(_vr_low.run.player)}; out by its top mouth you stand on the League side {_eg_at[0]}, by its bottom one back below {_eg_at[1]}")
for _k, _came, _n, _size in (("HOENN_SEAFLOOR_CAVERN", "HOENN_ROUTE_128", 2, (20, 20)), ("HOENN_CAVE_OF_ORIGIN", "SOOTOPOLIS_CITY", 2, (19, 26))):
    _cv = kanto(_k, came=_came)
    _at = [t for t, v in _cv.run.floor.exits.items() if v == _came]
    check(_cv.run.n_floors == _n and _cv.run.index == 0 and (_cv.run.floor.w, _cv.run.floor.h) == _size and _at
          and min(abs(t[0] - _cv.run.player[0]) + abs(t[1] - _cv.run.player[1]) for t in _at) <= 2,
          f"{_k}: {_n} floors from the Emerald maps; in from {_came} at {_cv.run.player} on the entrance floor {_size}")
story.story_flags.pop("defeated_red_gyarados", None)
_lor = kanto("LAKE_OF_RAGE", came="JOHTO_ROUTE_43")
_gy = [m for f in _lor.run.floors for m in f.movers if m.kind == "figure" and m.payload.get("action") == "BOSS"]
check((_lor.run.floor.w, _lor.run.floor.h) == (96, 64) and set(_lor.run.floor.exits.values()) == {"JOHTO_ROUTE_43"} and _lor.run.player[1] >= 60
      and _gy and (_gy[0].x, _gy[0].y) == (45, 39), f"Lake of Rage: exact map; in from Route 43 (south); the Red Gyarados out on the lake {[(m.x, m.y) for m in _gy]}")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "MAHOGANY_TOWN", "JOHTO_ROUTE_42"
_mh = _CS(g); g.change_state(_mh); _tap_through(_mh)
check(isinstance(_mh, _WTS) and (_mh.w, _mh.h) == (32, 32) and {"gym", "center", "souvenir"} <= set(_mh.doors.values()) and _mh.player[0] <= 2
      and {"JOHTO_ROUTE_42", "JOHTO_ROUTE_44"} == set(_mh.exits.values()) and "JOHTO_ROUTE_43" in _mh.town_map["rooms"]["gate"]["exits"].values(),
      "Mahogany Town: exact map, in from Route 42 (west); the Gym and Center; Routes 43 and 44, the shop over the hideout")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "BLACKTHORN_CITY", "ICE_PATH"
_bt = _CS(g); g.change_state(_bt); _tap_through(_bt)
check(isinstance(_bt, _WTS) and (_bt.w, _bt.h) == (64, 64) and {"gym", "center", "mart"} <= set(_bt.doors.values()) and _bt.player[0] >= 48
      and {"JOHTO_ROUTE_45", "ICE_PATH", "DRAGONS_DEN"} == set(_bt.exits.values()),
      f"Blackthorn City: exact map, in from the Ice Path (east) at {_bt.player}; the Gym on the lake, Surf to Dragon's Den, the bridge to Route 45")
g.walk_town_pos = None
# Johto's building insides (11-11): every town's Gym, Center, Mart, lab, home and shop is SoulSilver's own room; walk into each, find its people, walk out
_jr = {}
for _k in ("NEW_BARK_TOWN", "CHERRYGROVE_CITY", "VIOLET_CITY", "AZALEA_TOWN", "CIANWOOD_CITY", "GOLDENROD_CITY", "OLIVINE_CITY", "ECRUTEAK_CITY", "MAHOGANY_TOWN", "BLACKTHORN_CITY", "MT_SILVER_CITY", "SAFARI_ZONE_GATE"):
    g.walk_town_pos = None; g.walk_town_room = None
    story.current_area_key, story.last_area_key = _k, None
    _t = _CS(g); g.change_state(_t); _tap_through(_t)
    _bad, _n, _gym = [], 0, None
    for _d, _name in sorted((_t.town_map.get("inside") or {}).items()):
        _door = tuple(int(v) for v in _d.split(","))
        _t._enter(_door)
        if _t.room != _name:
            _bad.append((_d, "not in", _name)); continue
        _seen = {_name}
        while True:  # (through the building's rooms by their stairs)
            _n += 1
            if any(isinstance(o, dict) and str(o.get("action")).upper() == "GYM" for o in _t.people.values()):
                _gym = _t.room
            if not all(isinstance(o, dict) for o in _t.people.values()):
                _bad.append((_d, _t.room, "someone with nothing to say"))
            _nxt = next((v for v in _t.exits.values() if str(v).startswith("ROOM:") and v[5:] not in _seen), None)
            if not _nxt:
                break
            _t._leave(_nxt); _seen.add(_nxt[5:])
            if _t.room != _nxt[5:]:
                _bad.append((_d, "stairs to", _nxt)); break
        _t._go(_name, "OUT:" + _d)  # (back to the first room, at its mat)
        _t._leave("OUT:" + _d)
        if _t.room is not None or _t.player not in ((_door[0], _door[1] + 1), (_door[0], _door[1] - 1)):  # (below the door; above it for a door on its building's far side: Olivine's harbour)
            _bad.append((_d, "out at", _t.player))
        g.walk_town_room = None
    _jr[_k] = (_n, _gym, _bad)
check(all(not v[2] for v in _jr.values()) and all(_jr[k][1] for k in _jr if k not in ("NEW_BARK_TOWN", "CHERRYGROVE_CITY", "MT_SILVER_CITY", "SAFARI_ZONE_GATE")) and sum(v[0] for v in _jr.values()) >= 45,
      f"Johto's building insides: {sum(v[0] for v in _jr.values())} rooms walked in twelve places (in by the door, up every stair, out below the door); each of the eight Gyms has its Leader inside {[(k, v[2]) for k, v in _jr.items() if v[2]]}")
# the Silver League plateau (Jordan, 11-12): Indigo Plateau's own map and lobby, Johto's league inside
import json as _json_s
_tm_s = _json_s.load(open("assets/town_maps.json", encoding="utf-8"))
g.walk_town_pos = None; g.walk_town_room = None
story.current_area_key, story.last_area_key = "SILVER_LEAGUE_PLATEAU", "MT_SILVER_CITY"
_sl = _CS(g); g.change_state(_sl); _tap_through(_sl)
_sl_in = _sl.player
_sl_gym = _sl.area_data["gym"]
_sl._enter(next(t for t, k in _sl.doors.items() if k == "league"))
_sl_opts = sorted(str(o.get("action")) for o in _sl.people.values())
check(isinstance(_sl, _WTS) and _tm_s["SILVER_LEAGUE_PLATEAU"]["art"] == _tm_s["INDIGO_PLATEAU"]["art"] and _sl_in[1] >= 17 and _sl.room == "lobby"
      and _sl_opts == ["GYM", "HEAL", "SHOP"] and [t["name"] for t in _sl_gym["trainers"]] == ["Will", "Koga", "Bruno", "Karen"] and _sl_gym["leader"]["name"] == "Lance",
      f"the Silver League plateau: Indigo Plateau's map; in from Mt. Silver's clearing (south) at {_sl_in}; the lobby's nurse, clerk and the League door; Will, Koga, Bruno, Karen, Champion Lance")
_ip_gym = g.loader.area_data["STORY_PROGRESSION"]["INDIGO_PLATEAU"]["gym"]
check([t["name"] for t in _ip_gym["trainers"]] == ["Lorelei", "Bruno", "Agatha", "Lance"] and _sl.exits and set(_tm_s["SILVER_LEAGUE_PLATEAU"]["exits"].values()) == {"MT_SILVER_CITY"}
      and "reception" in _tm_s["SILVER_LEAGUE_PLATEAU"]["buildings"].values(),
      "...and Indigo keeps Kanto's own (Lorelei, Bruno, Agatha, Lance): the two leagues are distinct; the Silver plateau's hut leads to the Reception Gate")
g.walk_town_pos = None; g.walk_town_room = None
# Johto's gatehouses and route buildings (11-12): walked through, as Kanto's are. From the far side you arrive inside, at the far mat
_gt = {}
for _k, _far in (("JOHTO_ROUTE_29", "JOHTO_ROUTE_46"), ("JOHTO_ROUTE_35", "NATIONAL_PARK"), ("ILEX_FOREST", "JOHTO_ROUTE_34")):
    _r = kanto(_k, came=_far)
    _gt[(_k, _far)] = (_r.run.index >= _r.run.recipe.get("art", {}).get("outdoor_floors", 1), _far in map(str, _r.run.floor.exits.values()), any(str(v).startswith("WARP") for v in _r.run.floor.exits.values()))
for _k, _far in (("GOLDENROD_CITY", "JOHTO_ROUTE_35"), ("MAHOGANY_TOWN", "JOHTO_ROUTE_43"), ("RUINS_OF_ALPH", "JOHTO_ROUTE_36"), ("SAFARI_ZONE_GATE", "JOHTO_SAFARI_ZONE")):
    g.walk_town_pos = None; g.walk_town_room = None
    story.current_area_key, story.last_area_key = _k, _far
    _t = _CS(g); g.change_state(_t); _tap_through(_t)
    _in = _t.room
    _out = next((v for v in _t.exits.values() if str(v).startswith("OUT:")), None)
    _t._leave(_out) if _out else None
    _gt[(_k, _far)] = (_in == "gate", _out is not None, _t.room is None)
check(all(all(v) for v in _gt.values()), f"Johto's gatehouses: from the far side you arrive inside the gatehouse, and its other mat leads on {[(k, v) for k, v in _gt.items() if not all(v)]}")
_r32 = kanto("JOHTO_ROUTE_32", came="VIOLET_CITY")
_r34b = kanto("JOHTO_ROUTE_34", came="GOLDENROD_CITY")
check("center" in (_r32.run.recipe.get("art") or {}).get("room_floors", {}) and "daycare" in (_r34b.run.recipe.get("art") or {}).get("room_floors", {}),
      "Route 32's Pokemon Center and Route 34's Day Care are rooms you walk into")
g.walk_town_pos = None; g.walk_town_room = None
# Johto places that had no map (11-12): each from SoulSilver's own room or zone
_nm = {}
for _k, _cm in (("MR_POKEMONS_HOUSE", "JOHTO_ROUTE_30"), ("MT_SILVER_CITY", "POKEMON_LEAGUE_GATE")):
    g.walk_town_pos = None; g.walk_town_room = None
    story.current_area_key, story.last_area_key = _k, _cm
    _t = _CS(g); g.change_state(_t); _tap_through(_t)
    _nm[_k] = (isinstance(_t, _WTS), (_t.w, _t.h), _t.player, set(map(str, _t.exits.values())), len(_t.people), set(_t.doors.values()))
story.defeated_trainers.pop("ECRUTEAK_DANCE_THEATER", None)
_dt = kanto("ECRUTEAK_DANCE_THEATER", came="ECRUTEAK_CITY")
_dtt = {(m.x, m.y) for m in _dt.run.floor.movers if m.kind == "trainer"}
check(set(map(str, _dt.run.floor.exits.values())) == {"ECRUTEAK_CITY"} and len(_dtt) == 5,
      f"the Dance Theater: SoulSilver's hall, in at its door {_dt.run.player}, the five Kimono Girls on the stage {sorted(_dtt)}")
check(_nm["MR_POKEMONS_HOUSE"][0] and _nm["MR_POKEMONS_HOUSE"][3] == {"JOHTO_ROUTE_30"} and _nm["MR_POKEMONS_HOUSE"][4] == 2,
      f"Mr. Pokemon's house: SoulSilver's room, in from Route 30 at {_nm['MR_POKEMONS_HOUSE'][2]}, two people to talk to")
check(_nm["MT_SILVER_CITY"][0] and _nm["MT_SILVER_CITY"][1] == (32, 32) and _nm["MT_SILVER_CITY"][3] == {"MT_SILVER", "POKEMON_LEAGUE_GATE"} and "center" in _nm["MT_SILVER_CITY"][5]
      and _nm["MT_SILVER_CITY"][2][0] >= 29, f"Mt. Silver's clearing: SoulSilver's 32 x 32, in from the Reception Gate (east) at {_nm['MT_SILVER_CITY'][2]}; the Center, the cave mouth, a guide for the other two ways")
_aq = kanto("JOHTO_SS_AQUA", came="OLIVINE_CITY")
check(_aq.run.n_floors == 7 and {"OLIVINE_CITY", "VERMILLION_CITY"} <= set(map(str, _aq.run.floor.exits.values())),
      f"the S.S. Aqua: seven decks and cabins from SoulSilver; aboard from Olivine at {_aq.run.player}; gangway mats for Olivine and Vermilion")
_fa = kanto("FRONTIER_ACCESS", came="JOHTO_ROUTE_40")
_fa2 = kanto("FRONTIER_ACCESS", came="JOHTO_BATTLE_FRONTIER")
check({"JOHTO_ROUTE_40", "JOHTO_BATTLE_FRONTIER"} == set(map(str, _fa.run.floor.exits.values())) and _fa.run.player[1] < _fa2.run.player[1],
      f"Frontier Access: SoulSilver's gate hall; in from Route 40 at the north mat {_fa.run.player}, from the Frontier at the south doors {_fa2.run.player}")
_bc = kanto("BUG_CONTEST", came="NATIONAL_PARK")
check((_bc.run.floor.w, _bc.run.floor.h) == (96, 96) and set(map(str, _bc.run.floor.exits.values())) == {"NATIONAL_PARK"} and not [m for m in _bc.run.floor.movers if m.kind == "trainer"],
      "the Bug-Catching Contest: the National Park's own map, no trainers, every gate back to the park")
g.walk_town_pos = None; g.walk_town_room = None
story.current_area_key, story.last_area_key = "OLIVINE_CITY", "JOHTO_ROUTE_39"
_ol = _CS(g); g.change_state(_ol); _tap_through(_ol)
_ol._enter(next(t for t, k in _ol.doors.items() if k == "harbor"))
_ol_in = (_ol.room, len(_ol.people))
_ol._leave("ROOM:harbor_2")
check(_ol_in[0] == "harbor" and _ol_in[1] >= 3 and _ol.room == "harbor_2" and "JOHTO_SS_AQUA" in _ol.exits.values(),
      f"Olivine's harbour: the terminal (the ferry man and the rides to ask for), its stairs out to the pier, the gangway onto the S.S. Aqua {_ol_in}")
g.walk_town_pos = None; g.walk_town_room = None
story.current_area_key, story.last_area_key = "MAHOGANY_TOWN", "JOHTO_ROUTE_42"
_mh2 = _CS(g); g.change_state(_mh2); _tap_through(_mh2)
_mh2._enter(next(t for t, k in _mh2.doors.items() if k == "souvenir"))
check(_mh2.room == "souvenir" and "ROCKET_HQ" in _mh2.exits.values() and len(_mh2.people) == 1,
      f"Mahogany's shop: its own room, the clerk at the counter, the stairs down to the hideout {sorted(map(str, _mh2.exits.values()))}")
g.walk_town_pos = None; g.walk_town_room = None
story.current_area_key, story.last_area_key = "SAFARI_ZONE_GATE", "JOHTO_ROUTE_48"
_sg = _CS(g); g.change_state(_sg); _tap_through(_sg)
_sg_in = _sg.player
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "SAFARI_ZONE_GATE", "JOHTO_SAFARI_ZONE"
_sg2 = _CS(g); g.change_state(_sg2); _tap_through(_sg2)
check(isinstance(_sg, _WTS) and (_sg.w, _sg.h) == (64, 64) and _sg_in[1] >= 61 and {"JOHTO_ROUTE_48"} == set(_sg.exits.values()) and "center" in _sg.doors.values()
      and len(_sg._door_options("center")) == 1 and _sg2.room == "gate" and "JOHTO_SAFARI_ZONE" in _sg2.exits.values(),
      f"Safari Zone Gate: a town now, SoulSilver's plaza; in from Route 48 (south) at {_sg_in}; the Center heals; back out of the Safari Zone you stand inside the gatehouse {_sg2.room, _sg2.player}")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "DRAGON_SHRINE", "DRAGONS_DEN"
_ds = _CS(g); g.change_state(_ds); _tap_through(_ds)
check(isinstance(_ds, _WTS) and set(_ds.exits.values()) == {"DRAGONS_DEN"} and (_ds.w, _ds.h) == (9, 13) and _ds.player[1] >= 9,
      f"the Dragon Shrine: inside, in at its door {_ds.player}; the Elder's test")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "POKEMON_LEAGUE_GATE", "KANTO_ROUTE_26"
_lg = _CS(g); g.change_state(_lg); _tap_through(_lg)
check(isinstance(_lg, _WTS) and {"KANTO_ROUTE_22", "KANTO_ROUTE_28", "KANTO_ROUTE_26"} == set(_lg.exits.values()) and "leaguegate" in _lg.doors.values() and _lg.player[1] >= 17,
      f"the Reception Gate: exact; in from Route 26 (south) at {_lg.player}; Route 22 west, Route 28 east, the great door north")
_lg_held = _lg._check_menu_condition
_lg_door = next(t for t, k in _lg.doors.items() if k == "leaguegate")
_lg_seen = {}
for _name, _yes in (("johto", {"has_8_johto_badges"}), ("kanto", {"has_8_kanto_badges"}), ("both", {"has_8_johto_badges", "has_8_kanto_badges"}), ("neither", set())):
    _lg._check_menu_condition = lambda c, _y=_yes: (c in _y) if c in ("has_8_johto_badges", "has_8_kanto_badges") else _lg_held(c)
    _lg_seen[_name] = sorted(o.get("target_area") for o in _lg._door_options("leaguegate"))
_lg._check_menu_condition = _lg_held
check(_lg_seen == {"johto": ["SILVER_LEAGUE_PLATEAU"], "kanto": ["VICTORY_ROAD"], "both": ["SILVER_LEAGUE_PLATEAU", "VICTORY_ROAD"], "neither": []},
      f"the Reception Gate's great door: with Johto's eight badges it leads to the Silver League, with Kanto's to Victory Road, with both you choose {_lg_seen}")
g.walk_town_pos = None; g.walk_town_room = None
story.current_area_key, story.last_area_key = "POKEMON_LEAGUE_GATE", "SILVER_LEAGUE_PLATEAU"
_lg2 = _CS(g); g.change_state(_lg2); _tap_through(_lg2)
check(abs(_lg2.player[0] - _lg_door[0]) <= 1 and _lg2.player[1] <= _lg_door[1] + 2, f"...and back from the Silver League you stand at the great door {_lg2.player}")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "POKEATHLON_DOME", "NATIONAL_PARK"
_pd = _CS(g); g.change_state(_pd); _tap_through(_pd)
check(isinstance(_pd, _WTS) and set(_pd.exits.values()) == {"NATIONAL_PARK"} and "dome" in _pd.doors.values() and len(_pd._door_options("dome")) == 1 and "CONSTRUCTION" in str(_pd._door_options("dome")[0]) and _pd.player[1] >= 40,
      f"the Pokeathlon Dome: its plaza, in from the National Park's north gatehouse {_pd.player}; the Dome's door says it's under construction")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "LITTLEROOT_TOWN", "HOENN_ROUTE_101"
_lt = _CS(g); g.change_state(_lt); _tap_through(_lt)
check(isinstance(_lt, _WTS) and (_lt.w, _lt.h) == (20, 20) and {"home", "rival", "lab"} <= set(_lt.doors.values()) and set(_lt.exits.values()) == {"HOENN_ROUTE_101"}
      and _lt.player[1] <= 2 and _lt._door_options("rival") and _lt._door_options("lab") and _lt._door_options("home"),
      f"Littleroot Town: from the Emerald map; in from Route 101 (north) at {_lt.player}; your house, Birch's house and the Lab each have their own door")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "OLDALE_TOWN", "HOENN_ROUTE_101"
_ot = _CS(g); g.change_state(_ot); _tap_through(_ot)
check(isinstance(_ot, _WTS) and (_ot.w, _ot.h) == (20, 20) and {"center", "mart"} <= set(_ot.doors.values()) and _ot.player[1] >= 17
      and {"HOENN_ROUTE_101", "HOENN_ROUTE_102", "HOENN_ROUTE_103"} == set(_ot.exits.values()),
      f"Oldale Town: from the Emerald map; in from Route 101 (south) at {_ot.player}; the Center and Mart; Routes 102 and 103")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "PETALBURG_CITY", "HOENN_ROUTE_102"
_pc = _CS(g); g.change_state(_pc); _tap_through(_pc)
check(isinstance(_pc, _WTS) and (_pc.w, _pc.h) == (30, 30) and {"center", "mart", "gym"} <= set(_pc.doors.values()) and _pc.player[0] >= 26
      and {"HOENN_ROUTE_102", "HOENN_ROUTE_104"} == set(_pc.exits.values()),
      f"Petalburg City: from the Emerald map; in from Route 102 (east) at {_pc.player}; the Gym, Center and Mart; Route 104 west")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "RUSTBORO_CITY", "HOENN_ROUTE_104"
_rc = _CS(g); g.change_state(_rc); _tap_through(_rc)
check(isinstance(_rc, _WTS) and (_rc.w, _rc.h) == (40, 60) and {"center", "mart", "gym", "devon", "school"} <= set(_rc.doors.values()) and _rc.player[1] >= 56
      and {"HOENN_ROUTE_104", "HOENN_ROUTE_115", "HOENN_ROUTE_116"} == set(_rc.exits.values()) and len(_rc._door_options("devon")) >= 2,
      f"Rustboro City: from the Emerald map; in from Route 104 (south) at {_rc.player}; Devon's door holds {len(_rc._door_options('devon'))} things to do")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "DEWFORD_TOWN", "HOENN_ROUTE_106"
_dw = _CS(g); g.change_state(_dw); _tap_through(_dw)
check(isinstance(_dw, _WTS) and (_dw.w, _dw.h) == (20, 20) and {"center", "gym", "harbor"} <= set(_dw.doors.values()) and _dw.player[1] <= 2
      and {"HOENN_ROUTE_106", "HOENN_ROUTE_107"} == set(_dw.exits.values()) and any("104" in str(o.get("text")) for o in _dw._door_options("harbor")),
      f"Dewford Town: from the Emerald map; in from Route 106 (north) at {_dw.player}; Mr. Briney's boat at the dock: {[o.get('text') for o in _dw._door_options('harbor')]}")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "SLATEPORT_CITY", "HOENN_ROUTE_109"
_sl = _CS(g); g.change_state(_sl); _tap_through(_sl)
check(isinstance(_sl, _WTS) and (_sl.w, _sl.h) == (40, 60) and {"center", "mart", "harbor", "museum", "contest", "shipyard", "market"} <= set(_sl.doors.values()) and _sl.player[1] >= 56
      and {"HOENN_ROUTE_109", "HOENN_ROUTE_110", "HOENN_ROUTE_134"} == set(_sl.exits.values()) and _sl._door_options("museum") and _sl._door_options("market") and _sl._door_options("shipyard"),
      f"Slateport City: from the Emerald map; in from Route 109 (the beach) at {_sl.player}; the Museum, Harbor, Shipyard, Contest Hall and market each have their own door")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "MAUVILLE_CITY", "HOENN_ROUTE_110"
_mv = _CS(g); g.change_state(_mv); _tap_through(_mv)
check(isinstance(_mv, _WTS) and (_mv.w, _mv.h) == (40, 20) and {"center", "mart", "gym", "bike", "game corner"} <= set(_mv.doors.values()) and _mv.player[1] >= 17
      and {"HOENN_ROUTE_110", "HOENN_ROUTE_111", "HOENN_ROUTE_117", "HOENN_ROUTE_118", "HOENN_NEW_MAUVILLE"} == set(_mv.exits.values()) and _mv._door_options("bike") and _mv._door_options("game corner"),
      f"Mauville City: laid out from the Emerald map; in from Route 110 (south) at {_mv.player}; the Gym, Center, Mart, Rydel's Cycles and the Game Corner")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "VERDANTURF_TOWN", "HOENN_ROUTE_117"
_vt = _CS(g); g.change_state(_vt); _tap_through(_vt)
check(isinstance(_vt, _WTS) and (_vt.w, _vt.h) == (20, 20) and {"center", "contest", "wally"} <= set(_vt.doors.values()) and _vt.player[0] >= 17
      and {"HOENN_ROUTE_117", "HOENN_RUSTURF_TUNNEL"} == set(_vt.exits.values()) and _vt._door_options("wally") and _vt._door_options("contest"),
      f"Verdanturf Town: from the Emerald map; in from Route 117 (east) at {_vt.player}; the Contest Hall, the Center, Wally's uncle's house; Rusturf Tunnel north")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "FALLARBOR_TOWN", "HOENN_ROUTE_113"
_fb = _CS(g); g.change_state(_fb); _tap_through(_fb)
check(isinstance(_fb, _WTS) and (_fb.w, _fb.h) == (20, 20) and {"center", "contest", "cozmo", "mart"} <= set(_fb.doors.values()) and _fb.player[0] >= 17
      and {"HOENN_ROUTE_113", "HOENN_ROUTE_114"} == set(_fb.exits.values()) and _fb._door_options("cozmo") and _fb._door_options("contest"),
      f"Fallarbor Town: laid out from the Emerald map; in from Route 113 (east) at {_fb.player}; the Contest Hall, the Center, Professor Cozmo's house")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "LAVARIDGE_TOWN", "HOENN_ROUTE_112"
_lv = _CS(g); g.change_state(_lv); _tap_through(_lv)
check(isinstance(_lv, _WTS) and (_lv.w, _lv.h) == (20, 20) and {"center", "mart", "gym"} <= set(_lv.doors.values()) and _lv.player[0] >= 17 and {"Heal", "Hot Springs"} <= {o.get("text") for o in _lv._door_options("center")} and set(_lv.exits.values()) == {"HOENN_ROUTE_112"},
      f"Lavaridge Town: laid out from the Emerald map; in from Route 112 (east) at {_lv.player}; the Center's door offers Heal and the Hot Springs; the Gym and Mart")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "FORTREE_CITY", "HOENN_ROUTE_119"
_ft = _CS(g); g.change_state(_ft); _tap_through(_ft)
_fup, _fdn = {}, {}
for _i in range(5):
    g.walk_town_pos = None
    g.walk_town_exit = ("FORTREE_CITY", _i, 5)
    story.current_area_key, story.last_area_key = "FORTREE_CITY_UPPER", "FORTREE_CITY"
    _f2 = _CS(g); g.change_state(_f2); _tap_through(_f2); _fup[_i] = _f2.player
    g.walk_town_pos = None
    g.walk_town_exit = ("FORTREE_CITY_UPPER", _i, 5)
    story.current_area_key, story.last_area_key = "FORTREE_CITY", "FORTREE_CITY_UPPER"
    _f1 = _CS(g); g.change_state(_f1); _tap_through(_f1); _fdn[_i] = _f1.player
g.walk_town_exit = None
_planks = all(_f2._open(t) == (_f2.rows[t[1]][t[0]] == ".") for t in ((12, 4), (20, 14))) and _f2._open((20, 4)) and _f2._open((25, 14)) and not _f2._open((3, 8)) and not _f2._open((22, 12))
check(isinstance(_ft, _WTS) and (_ft.w, _ft.h) == (40, 20) and {"center", "mart", "gym"} <= set(_ft.doors.values()) and _ft.player[0] <= 2
      and {"HOENN_ROUTE_119", "HOENN_ROUTE_120", "FORTREE_CITY_UPPER"} == set(_ft.exits.values()) and len(_ft.overheads) == 4
      and [_fup[i] for i in range(5)] == [(10, 5), (25, 5), (32, 5), (12, 15), (37, 15)] and [_fdn[i] for i in range(5)] == [(10, 7), (25, 7), (32, 7), (12, 17), (37, 17)] and _planks,
      f"Fortree City: read from the Emerald map; in from Route 119 (west) at {_ft.player}; each of the five ladders leads to its own (up {_fup}; down {_fdn}); up top you walk only the planks ({_planks})")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "LILYCOVE_CITY", "HOENN_ROUTE_121"
_lc = _CS(g); g.change_state(_lc); _tap_through(_lc)
check(isinstance(_lc, _WTS) and (_lc.w, _lc.h) == (80, 40) and {"center", "mart", "contest", "museum", "harbor"} <= set(_lc.doors.values()) and _lc.player[0] <= 2
      and {"HOENN_ROUTE_121", "HOENN_ROUTE_124"} == set(_lc.exits.values()) and _lc._door_options("museum") and _lc._door_options("mart") and _lc._door_options("contest"),
      f"Lilycove City: from the Emerald map; in from Route 121 (west) at {_lc.player}; the Museum, the Department Store, the Contest Hall and the Harbor each have their own door")
g.walk_town_pos = None
for _k, _came, _size, _doors, _outs in (("MOSSDEEP_CITY", "HOENN_ROUTE_124", (80, 40), {"gym", "center", "mart", "steven"}, {"HOENN_ROUTE_124", "HOENN_ROUTE_125", "HOENN_ROUTE_127", "HOENN_SPACE_CENTER"}),
                                        ("PACIFIDLOG_TOWN", "HOENN_ROUTE_131", (20, 40), {"center"}, {"HOENN_ROUTE_131", "HOENN_ROUTE_132"}),
                                        ("SOOTOPOLIS_CITY", "HOENN_ROUTE_126", (60, 60), {"gym", "center", "mart"}, {"HOENN_ROUTE_126", "HOENN_CAVE_OF_ORIGIN"}),
                                        ("EVER_GRANDE_CITY", "HOENN_ROUTE_128", (40, 80), {"league", "center"}, {"HOENN_ROUTE_128", "HOENN_VICTORY_ROAD"})):
    g.walk_town_pos = None
    story.current_area_key, story.last_area_key = _k, _came
    _tw = _CS(g); g.change_state(_tw); _tap_through(_tw)
    _own = [t for t, v in _tw.exits.items() if v == _came]
    check(isinstance(_tw, _WTS) and (_tw.w, _tw.h) == _size and _doors <= set(_tw.doors.values()) and set(_tw.exits.values()) == _outs
          and _own and min(abs(t[0] - _tw.player[0]) + abs(t[1] - _tw.player[1]) for t in _own) <= 2 and all(_tw._door_options(d) for d in _doors),
          f"{_k}: from the Emerald map, {_size}; in from {_came} at {_tw.player}, beside its own way out; doors {sorted(_doors)} each open something; ways out {sorted(set(_tw.exits.values()))}")
# Ever Grande's waterfall (a town's own waterfall tile): in the way until you have Waterfall
g.walk_town_pos = None
_had_wf = story.inventory.pop("HM_WATERFALL", None)
story.current_area_key, story.last_area_key = "EVER_GRANDE_CITY", "HOENN_ROUTE_128"
_tw = _CS(g); g.change_state(_tw); _tap_through(_tw)
_falls = [(x, y) for y in range(_tw.h) for x in range(_tw.w) if _tw.rows[y][x] == "$"]
_foot = next((x, y + 1) for x, y in sorted(_falls, key=lambda t: -t[1]) if _tw._open((x, y + 1)))
_tw.player, _tw.anim = _foot, 0
_tw.step(0, -1)
_held_back = (_tw.player == _foot, "WATERFALL" in str(_tw.toast).upper())
story.inventory["HM_WATERFALL"] = 1
_tw.anim = 0
_tw.step(0, -1)
_climbed = _tw.player
check(len(_falls) >= 100 and _held_back == (True, True) and _climbed == (_foot[0], _foot[1] - 1),
      f"Ever Grande City: its waterfall ({len(_falls)} tiles) turns you back at {_foot} without Waterfall, and with it you climb on to {_climbed}")
story.inventory.pop("HM_WATERFALL", None)
if _had_wf:
    story.inventory["HM_WATERFALL"] = _had_wf
g.walk_town_pos = None


class _Held:  # (an arrow key held down)
    def __init__(self, key):
        self.key = key

    def __getitem__(self, key):
        return key == self.key


_orig_pressed = pygame.key.get_pressed
try:  # hold to keep walking (Jordan, 11-07), in a town and on a route map
    _ld.npc_active = False
    _x0 = _ld.player[0]
    pygame.key.get_pressed = lambda: _Held(pygame.K_LEFT)
    for _k in range(40):
        _ld.update()
    _town_ok = _ld.player[0] <= _x0 - 3
    _r29 = kanto("JOHTO_ROUTE_29", came="NEW_BARK_TOWN")
    _r29.run.floor.movers = []  # (none in the way)
    _r29.run.player = (93, 14)  # (the sand road in from New Bark)
    _rx = _r29.run.player[0]
    for _k in range(40):
        _r29.update()
    check(_town_ok and _r29.run.player[0] <= _rx - 3, "hold an arrow key: you keep walking (town and route)")
finally:
    pygame.key.get_pressed = _orig_pressed
from src.pokemon import items as _it2
_tw = mk(158)
_tw.held_item = "MYSTIC_WATER"
check(_it2.held_boost(_tw, "WATER") == 1.2 and _it2.held_boost(_tw, "FIRE") == 1.0,
      "Mystic Water, held: Water moves x1.2 (only Water)")

# Routes 12-18, Fuchsia and the Safari Zone (Jordan, 11-07)
_inv = dict(story.inventory)
story.inventory.pop("POKE_FLUTE", None)
_r16 = kanto("KANTO_ROUTE_16", came="CELADON_CITY")
check(_r16._boss_spot() == (31, 13) and _r16.run.floor.exits.get((31, 13)) == "BOSS",
      "Route 16: Snorlax asleep on the road where FireRed has him, before the gatehouse (11-11; the Bicycle is asked for at the head of the slope)")
story.inventory.pop("HM_FLY", None)
story.story_flags.pop("got_hm_fly_kanto", None)
_d = next(t for t, v in _r16.run.floor.decor.items() if v == "door:flyhouse")
_r16.run.player, _r16.facing = (_d[0], _d[1] + 1), (0, -1)
_r16._read_sign()
talk(_r16)
check(story.inventory.get("HM_FLY") == 1, "...the quiet house: HM Fly")
story.inventory.clear()
story.inventory.update(_inv)
for _k in ("heard_warden_teeth", "got_hm_strength_kanto", "got_good_rod_kanto", "got_gold_teeth"):
    story.story_flags.pop(_k, None)
for _k in ("GOLD_TEETH", "HM_STRENGTH", "GOOD_ROD"):
    story.inventory.pop(_k, None)
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "FUCHSIA_CITY", "KANTO_ROUTE_15"
_fu = _CS(g); g.change_state(_fu); _tap_through(_fu)
check({"warden", "brother", "gym", "center", "mart"} <= set(_fu.doors.values()) and set(_fu.exits.values()) == {
    "KANTO_ROUTE_15", "KANTO_ROUTE_18", "KANTO_ROUTE_19", "SAFARI_ZONE"}, "Fuchsia: walked, its doors and four ways out")
def _talk_inside(t, kind):  # (11-11: their houses are rooms now: in by the door, talk to whoever is there, out again)
    door = max((d for d, k in t.doors.items() if k == kind), key=lambda d: d[1])
    t._enter(door)
    for spot in list(t.people):
        t.player = t.anim_from = (spot[0], spot[1] + 1); t.anim = 0; t.walk_goal = None
        t.step(0, -1); _tap_through(t)
    t._go(None, "OUT:%d,%d" % door); g.walk_town_room = None


_talk_inside(_fu, "warden")
_talk_inside(_fu, "brother")
check(story.story_flags.get("heard_warden_teeth") and story.inventory.get("GOOD_ROD") == 1,
      "the Warden has lost his teeth; the Fishing Guru's brother: the Good Rod")
_sz = kanto("SAFARI_ZONE", came="FUCHSIA_CITY")
check([_sz.zones[_sz._zone_index(0, x, y)] for x, y in ((70, 70), (130, 60), (50, 20), (20, 60))] == ["center", "east", "north", "west"]
      and story.story_flags.get("zone_SAFARI_ZONE") == "center", "the Safari Zone: one map, four areas; in at the Center")
_sz.run.player = (130, 60)
_sz._note_area()
check(story.story_flags.get("zone_SAFARI_ZONE") == "east", "...walk into the East: its Pokemon")
_tt = [m for m in _sz.run.floor.movers if m.kind == "figure" and m.payload.get("text") == "GOLD TEETH"]
check(_tt and _tt[0].x < 53, "the Gold Teeth, in the West")
if _tt:
    _sz._get_route_callback(_tt[0].payload)()
    talk(_sz)
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "FUCHSIA_CITY", "SAFARI_ZONE"
_fu = _CS(g); g.change_state(_fu); _tap_through(_fu)
_talk_inside(_fu, "warden")
check(story.inventory.get("HM_STRENGTH") == 1 and not story.inventory.get("GOLD_TEETH"), "the Warden: HM Strength for his teeth")

# the sea loop (Jordan, 11-07): Routes 19-21 surfed, Seafoam's boulders (Strength and the slide puzzle), Cinnabar
from src.states.slide_puzzle import SlidePuzzleState, numbers
import random as _rr
check(numbers(1, _rr.Random(1)) == (3, list(range(1, 9))) and numbers(3, _rr.Random(1))[0] == 4
      and numbers(2, _rr.Random(1))[1][:2] == [2, 4], "the slide puzzle: 1-8 at Poke Ball, by 2s at Great, 4 x 4 from Ultra")
_inv = dict(story.inventory)
story.inventory.pop("HM_SURF", None); story.inventory.pop("HM_STRENGTH", None)
_r19 = kanto("KANTO_ROUTE_19", came="FUCHSIA_CITY")
_f = _r19.run.floor
_bch = next((x, y) for y in range(_f.h) for x in range(_f.w) if _f.tile(x, y) == core.FLOOR
            and _f.tile(x, y + 1) == core.SURF and not _f.occupied(x, y) and not _f.occupied(x, y + 1))
_r19.run.player = _r19.anim_from = _bch
_r19.anim = 0
_r19.step(0, 1)
check(_r19.run.player == _bch and "Surf" in (_r19.toast or ""), "Route 19: the open sea needs Surf")
story.inventory["HM_SURF"] = 1
_r19.step(0, 1)
_r19.draw()
check(_r19._on_surf() and _r19._beside("water") is not None, "...with HM Surf: out on the water (riding; fish anywhere)")
_r20 = kanto("KANTO_ROUTE_20", came="KANTO_ROUTE_19")
check(sum(1 for v in _r20.run.floor.exits.values() if v == "SEAFOAM_ISLANDS") == 2 and _r20._on_surf(),
      "Route 20: Seafoam's two mouths; in from Route 19, surfing")
for _k in [k for k in story.story_flags if k.startswith("boulder_SEAFOAM")]:
    story.story_flags.pop(_k)
_sf = kanto("SEAFOAM_ISLANDS", came="KANTO_ROUTE_20")
_bd = next(t for t, v in _sf.run.floor.decor.items() if str(v).startswith("boulder:"))
_sf.run.player, _sf.facing = (_bd[0], _bd[1] + 1), (0, -1)
_sf._read_sign()
check(_sf.dialogue_box.visible and "Strength" in " ".join(_sf.dialogue_box.text_lines), "Seafoam: a boulder (no Strength: it won't move)")
talk(_sf)
story.inventory["HM_STRENGTH"] = 1
_sf._read_sign()
talk(_sf)
_pz = g.current_state
check(isinstance(_pz, SlidePuzzleState), "...with Strength: the slide puzzle")
_pz.board = list(range(_pz.side * _pz.side - 1)) + [None]
_n = len(_pz.board)
_pz.board[_n - 2], _pz.board[_n - 1] = None, _n - 2
_pz.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT)])
for _k in range(90):
    _pz.update()
check(g.current_state is _sf and _sf.run.floor.walkable(*_bd), "...solved: the boulder slides aside")
talk(_sf)
_sf2 = kanto("SEAFOAM_ISLANDS", came="KANTO_ROUTE_20")
_sf2.step(0, 1)
check(_sf2.run.floor.walkable(*_bd), "...and stays aside")
story.inventory.clear(); story.inventory.update(_inv)
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "CINNABAR_ISLAND", "KANTO_ROUTE_21"
_ci = _CS(g); g.change_state(_ci); _tap_through(_ci)
check({"mansion", "fossil", "gym", "center", "mart", "harbor"} <= set(_ci.doors.values())
      and {"KANTO_ROUTE_20", "KANTO_ROUTE_21", "CINNABAR_VOLCANO"} <= set(_ci.exits.values()),
      "Cinnabar Island: walked; Mansion, Lab, Gym, Center, Mart, harbor; Surf north and east; the volcano")

# the rest of Kanto (Jordan, 11-07): Saffron, the Power Plant, Route 23, Victory Road, Indigo Plateau, Cerulean Cave
_inv = dict(story.inventory)
story.inventory.update({"HM_SURF": 1, "HM_STRENGTH": 1})
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "SAFFRON_CITY", "KANTO_ROUTE_5"
_sa = _CS(g); g.change_state(_sa); _tap_through(_sa)
check({"station", "dojo", "gym", "copycat", "mart", "center"} <= set(_sa.doors.values()) and {
    "KANTO_ROUTE_5", "KANTO_ROUTE_6", "KANTO_ROUTE_7", "KANTO_ROUTE_8", "SILPH_CITY"} <= set(_sa.exits.values()),
      "Saffron: walked; the Magnet Train, the Dojo, the Gym, Copycat's, a gatehouse each side, Silph Co.")
_pp = kanto("POWER_PLANT", came="KANTO_ROUTE_10")
_z = [m for m in _pp.run.floor.movers if m.kind == "figure" and m.payload.get("text") == "CHALLENGE ZAPDOS"]
check(_z and (_z[0].x, _z[0].y) == (5, 11) and (_pp.run.floor.w, _pp.run.floor.h) == (49, 40), "the Power Plant: FireRed's own 49 x 40; Zapdos in its north-west room, where FireRed has it")
_r23 = kanto("KANTO_ROUTE_23", came="KANTO_ROUTE_22")
_gds = {m.payload.get("text"): m for m in _r23.run.floor.movers if m.kind == "figure"}
check(sum(1 for t in _gds if t.endswith("BADGE GUARD")) == 8 and _gds["BOULDER BADGE GUARD"].y > _gds["EARTH BADGE GUARD"].y
      and any(_r23.run.floor.tile(x, y) == core.SURF for y in range(_r23.run.floor.h) for x in range(_r23.run.floor.w)),
      "Route 23: eight badge guards (Boulder first), ponds to Surf")
_vr = kanto("VICTORY_ROAD", came="KANTO_ROUTE_23")
_vb = [t for t, v in _vr.run.floor.decor.items() if str(v).startswith("boulder:")]
_vr._warp(1, 1, 9)
check("KANTO_ROUTE_23" in _vr.run.floor.exits.values() and _vr.run.n_floors == 3,
      "Victory Road: FireRed's three floors (11-12); 2F's way out leads to Route 23's forecourt, below Indigo Plateau")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "INDIGO_PLATEAU", "VICTORY_ROAD"
_ip = _CS(g); g.change_state(_ip); _tap_through(_ip)
_ipd = set(_ip.doors.values())  # (the town's doors, before you step into the lobby)
_ip._enter(next(t for t, k in _ip.doors.items() if k == "league"))
check({"league", "johto"} <= _ipd and _ip.room == "lobby" and {o.get("text") for o in _ip.people.values()} >= {"Heal", "Shop", "ELITE_FOUR"},
      "Indigo Plateau: the League's door, the ride to Johto; in its lobby the nurse, the clerk and the Elite Four's door (11-12: FireRed's lobby)")
_ip._go(None, "OUT:11,6"); g.walk_town_room = None
_cc = kanto("CERULEAN_CAVE", came="CERULEAN_CITY")
while _cc.run.index < 2:
    _cc._descend()
check(any(m.kind == "figure" and m.payload.get("text") == "CHALLENGE MEWTWO" for m in _cc.run.floor.movers),
      "Cerulean Cave: Mewtwo on B1F")
story.inventory.clear(); story.inventory.update(_inv)
g.walk_towns = False

print(f"##### {fails} failures")
