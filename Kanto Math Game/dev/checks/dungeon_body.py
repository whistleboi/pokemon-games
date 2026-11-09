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

# Viridian Forest: our own open map now (Jordan, 11-07), one floor, Viridian below and Route 2's gatehouse above
p = kanto("VIRIDIAN_FOREST", came="KANTO_ROUTE_2")
check(p.run.n_floors == 1 and {"VIRIDIAN_CITY", "KANTO_ROUTE_2"} <= set(p.run.floor.exits.values()),
      "Viridian Forest: one open map, out to Viridian City and to Route 2")
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
    """Where you can get to from start, a boulder counting as pushed aside (Strength and the slide puzzle)."""
    held = {t: f.tiles[t[1]][t[0]] for t, v in f.decor.items() if str(v).startswith("boulder:")}
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
            if _i < len(_art_floors) and _art_floors[_i].get("parts"):  # (in parts: each from its own ladder)
                for _t in [t for t, v in _f.exits.items() if v in (core.STAIRS, core.STAIRS_UP)]:
                    _reach = {**_reach, **_reach_of(_f, _t)}
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
        _reach = _reach_of(_f, _p.run.player)
        _af = ((_dg.recipe_for(g, _a).get("art") or {}).get("floors") or [])
        if _af and _af[_p.run.index].get("parts"):  # (in parts, Rock Tunnel's 1F: each from its own ladder)
            for _t in [t for t, v in _f.exits.items() if v in (core.STAIRS, core.STAIRS_UP)]:
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
_r1 = kanto("JOHTO_ROUTE_30", came="CHERRYGROVE_CITY")  # (a made-up route map: our own ones are open)
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
for _k, _n, _w in (("HOENN_SAFARI_ZONE", 1, 4), ("GREAT_MARSH", 2, 3)):
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
check(_r12._gate("KANTO_ROUTE_13") == ("boss", None, False) and not any(
    m.kind == "figure" and m.payload.get("action") == "BOSS" for f in _r12.run.floors for m in f.movers),
      "Route 12: Snorlax asleep across the way to Route 13 (not somewhere else on the map)")
_r12._try_exit("KANTO_ROUTE_13")
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
    if _wt.hover_menu_active:
        break
check(_wt.hover_menu_active and any("Oak" in b.text for b in _wt.hover_buttons), "walk into the Lab: Oak's options")
_wt.clear_hover_menu()
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
    if g.current_state is not _wt:
        break
_pc = g.current_state
check(type(_pc).__name__ == "PokeCenterState" and _pc.previous_state is _wt, "walk into the Pokemon Center: inside")
_spot = _wt.player
g.change_state(_wt)
check(_wt.player == _spot and _wt.action_menu not in g.ui_manager.elements, "...out again: where you were, no menu bar")

# the Johto pilot (Jordan, 11-06): our own maps, laid out after Pokemon Journeys' (New Bark, Route 29, Cherrygrove)
g.walk_town_pos = None
story.story_flags["received_starter_johto"] = True
story.story_flags["move_offer_johto"] = True
story.current_area_key, story.last_area_key = "NEW_BARK_TOWN", None
_nb = _CS(g); g.change_state(_nb); _tap_through(_nb)
check(isinstance(_nb, _WTS) and {"lab", "home"} <= set(_nb.doors.values())
      and [o["text"] for o in _nb._people().values()] == ["Talk to Nice Lady"],
      "New Bark Town: our map, Elm's Lab and your house have doors, the Nice Lady outside")
_nb.walk_goal = next(t for t, k in _nb.doors.items() if k == "lab")
for _k in range(400):
    frames(_nb)
    if _nb.npc_active:
        break
check(_nb.npc_active and _nb.current_npc == "professor_elm", "walk into Elm's Lab: Professor Elm")
_tap_through(_nb)
_w = min(_nb.exits)
_nb.player = _nb.anim_from = (_w[0] + 1, _w[1])
_nb.anim = 0
_nb.step(-1, 0)
check(type(g.current_state).__name__ == "AreaTransitionState", "walk off the west edge: on to Route 29")
_r29 = kanto("JOHTO_ROUTE_29", came="NEW_BARK_TOWN")
_f = _r29.run.floor
check(_r29.run.recipe.get("art") and not _r29.run.fog
      and sorted(set(_f.exits.values())) == ["CHERRYGROVE_CITY", "JOHTO_ROUTE_46", "NEW_BARK_TOWN"]
      and _r29.run.player[0] >= _f.w - 3, "Route 29: our map, open, in from New Bark (east); Cherrygrove, Route 46's gate")
_wl = [m for m in _f.movers if m.kind == "wild"]
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
_cg._enter(next(t for t, k in _cg.doors.items() if k == "fisher"))
_tap_through(_cg)
check(story.inventory.get("MYSTIC_WATER") == 1, "the fisherman's house: Mystic Water")
_cg._enter(next(t for t, k in _cg.doors.items() if k == "fisher"))
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
    _r29.run.floor.movers = [m for m in _r29.run.floor.movers if m.kind != "wild"]  # (none in the way)
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
check(_r16._gate("KANTO_ROUTE_17") == ("boss", None, False), "Route 16: Snorlax asleep at Cycling Road's gate (before the Bicycle)")
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
_fu._enter(next(t for t, k in _fu.doors.items() if k == "warden")); _tap_through(_fu)
_fu._enter(next(t for t, k in _fu.doors.items() if k == "brother")); _tap_through(_fu)
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
_fu._enter(next(t for t, k in _fu.doors.items() if k == "warden")); _tap_through(_fu)
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
check(_z and _z[0].y <= 5, "the Power Plant: Zapdos in its back room")
_r23 = kanto("KANTO_ROUTE_23", came="KANTO_ROUTE_22")
_gds = {m.payload.get("text"): m for m in _r23.run.floor.movers if m.kind == "figure"}
check(sum(1 for t in _gds if t.endswith("BADGE GUARD")) == 8 and _gds["BOULDER BADGE GUARD"].y > _gds["EARTH BADGE GUARD"].y
      and any(_r23.run.floor.tile(x, y) == core.SURF for y in range(_r23.run.floor.h) for x in range(_r23.run.floor.w)),
      "Route 23: eight badge guards (Boulder first), ponds to Surf")
_vr = kanto("VICTORY_ROAD", came="KANTO_ROUTE_23")
_vb = [t for t, v in _vr.run.floor.decor.items() if str(v).startswith("boulder:")]
_vr._descend()
check("INDIGO_PLATEAU" in _vr.run.floor.exits.values(), "Victory Road: up to 2F; out to Indigo Plateau from there (as in the original)")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "INDIGO_PLATEAU", "VICTORY_ROAD"
_ip = _CS(g); g.change_state(_ip); _tap_through(_ip)
check({"league", "johto"} <= set(_ip.doors.values()) and {o.get("text") for o in _ip.people.values()} >= {"Heal", "Shop"},
      "Indigo Plateau: the Elite Four's door, the ride to Johto; the nurse and the clerk at their counters")
_cc = kanto("CERULEAN_CAVE", came="CERULEAN_CITY")
while _cc.run.index < 2:
    _cc._descend()
check(any(m.kind == "figure" and m.payload.get("text") == "CHALLENGE MEWTWO" for m in _cc.run.floor.movers),
      "Cerulean Cave: Mewtwo on B1F")
story.inventory.clear(); story.inventory.update(_inv)
g.walk_towns = False

print(f"##### {fails} failures")
