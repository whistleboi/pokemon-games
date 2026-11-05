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
check(p._scent_source() == "HONEY", "HONEY in the Bag: the HONEY button works")
p.use_scent()
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

# CLASSIC VIEW
p._classic()
check(type(g.current_state) is PlayState, "CLASSIC: the old route menu for this visit")
check(type(PlayState(g, restore_data={"x": 1})) is PlayState, "CLASSIC lasts through battles on that visit")
story.current_area_key = "KANTO_ROUTE_1"
check(isinstance(PlayState(g), DungeonState), "...and ends once you're somewhere else")
print(f"##### {fails} failures")
