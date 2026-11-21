# Unova batch 3a, part 1 (11-20): Castelia City, Black 2's way: the waterfront avenue (the game's rails), each street, pier
# and building a room through its own camera, doors paired by the game's own warps. The ship's arrival, the Harlequin Hunt,
# the Battle Company's lift and clerks, Burgh away, Iris to Thumb Pier; gifts, the Casteliacone, the version's line.
#   bash dev/checks/run.sh unovab3a
import json
from src.states.overworld import CityState, PlayState
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.states.overworld.dungeon import DungeonState as _DS
from src.states.battle import TrainerIntroState, TrainerBattleState
from src.states.xtransceiver import XtransceiverCallState
from src.states import pokestar as _ps

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.player_character = "nate"
g.rival_name = "HUGH"
said, battles, calls, films = [], [], [], []
FILM_PICK = {"want": "good", "script": None}   # (what the movie test picks: every line "good", "odd"...; a script for the list)


def _note(st):
    box = getattr(st, "npc_dialogue", None) if getattr(st, "npc_active", False) else getattr(st, "dialogue_box", None)
    if box is not None and getattr(box, "visible", True):
        for line in getattr(box, "text_lines", []) or []:
            if not said or said[-1] != line:
                said.append(line)


def _win(b):
    b = getattr(b, "next_state", None) or b
    if isinstance(b, TrainerBattleState):
        battles.append((getattr(b, "trainer_name", None), [(p.id, p.level) for p in b.opponent_team]))
        g.change_state(b)
        b.player_won = True
        b.exit_battle()
        return True
    return False


def _film(st):
    """The movie game, played: the script asked for from the list, then the wanted kind of line every beat."""
    if st.stage == "pick":
        films_ = _ps.unlocked(story)
        i = next((k for k, s in enumerate(films_) if s["key"] == FILM_PICK["script"]), len(films_))
        st.stage_t = -10 ** 6
        r = st.buttons[i] if i < len(st.buttons) else None
        if r is None:
            st.draw(); r = st.buttons[i]
        st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=r.center)])
    elif st.stage == "beat":
        order = st._order()
        k = next(j for j, (_t, kind) in enumerate(order) if kind == FILM_PICK["want"])
        st._choose(k)
    else:
        st.stage_t = -10 ** 6
        if st.stage == "theater":
            films.append((st.script["key"], st.ending, _ps.rank(story)))
        st._next()


def play(until, n=3000):
    for _ in range(n):
        if until():
            return True
        st = g.current_state
        if isinstance(st, (TrainerIntroState, TrainerBattleState)):
            _win(st)
            continue
        if isinstance(st, XtransceiverCallState):
            if not calls or calls[-1] is not st:
                calls.append(st)
            for ln in st.lines:
                if not said or said[-1] != ln:
                    said.append(ln)
            st.t0 -= 2000
            st._tap()
            st.update(); st.draw()
            continue
        if isinstance(st, _ps.MovieState):
            st.draw()
            _film(st)
            continue
        if isinstance(st, _DS) and getattr(st, "mode", None) == "CHOICE":
            mv = st.encounter
            st.encounter, st.mode = None, "MAP"
            if mv in st.run.floor.movers:
                st.run.floor.movers.remove(mv)
            continue
        if getattr(st, "npc_active", False):
            _note(st)
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
            _note(st)
            st.dialogue_box.advance()
        st.update(); st.draw()
    return until()


def pos():
    st = g.current_state
    return tuple(st.run.player) if isinstance(st, _DS) else tuple(getattr(st, "player", (-1, -1)))


def idle():
    st = g.current_state
    if isinstance(st, _WTS):
        return not st._busy() and st.anim == 0
    if isinstance(st, _DS):
        box = getattr(st, "dialogue_box", None)
        return st.anim == 0 and not getattr(st, "_scene_lock", False) and not getattr(st, "npc_active", False)             and not (box is not None and getattr(box, "visible", False))
    return False


def put(x, y, face=(0, 1)):
    st = g.current_state
    if isinstance(st, _DS):
        st.run.player = st.anim_from = (x, y)
    else:
        st.player = st.anim_from = (x, y)
        st.partner = st.partner_from = (x, y)
        st.deck = True
    st.anim = 0
    st.facing = face


def step(dx, dy, n=1):
    for _ in range(n):
        play(idle, 600)
        g.current_state.step(dx, dy)
        play(lambda: g.current_state.anim == 0 if hasattr(g.current_state, "anim") else True, 80)


def shot(name):
    g.current_state.draw()
    pygame.image.save(pygame.display.get_surface(), f"{S}/unovab3a_{name}.png")


def town(area, room=None, at_=None):
    story.current_area_key = area
    g.walk_town_pos = (area, at_, (0, 1)) if at_ else None
    g.walk_town_room = (area, room) if room else None
    g.change_state(CityState(g))
    play(idle, 400)
    t = g.current_state
    if room and getattr(t, "room", None) != room:
        t._go(room, None); play(idle, 300); t = g.current_state
    if at_:
        put(*at_)
    return g.current_state


def route(area, came, at_):
    story.current_area_key, story.last_area_key = area, came
    g.change_state(PlayState(g))
    play(lambda: isinstance(g.current_state, _DS) and idle(), 400)
    put(*at_)
    return g.current_state


def talk(who):
    t = g.current_state
    xy = next((xy for xy, o in t._people().items() if (o.get("text") if isinstance(o, dict) else None) == who), None)
    if xy:
        t._talk(xy); play(idle, 4000)
    return xy



flags = story.story_flags
for f in [k for k in flags if k.startswith(("b2_hunt", "b2_castelia", "b2_bc_", "b2_burgh", "b2_iris", "b2_thumb", "b2_gf_", "b2_cafe",
                                              "b2_studio", "b2_sewers", "b2_casteliacone"))]:
    flags.pop(f, None)
for f in ("received_starter_unova", "b2_mom_talk", "b2_basic_badge", "b2_toxic_badge", "b2_virbank_dock", "b2_r20_hugh",
          "b2_pop_roxie_back", "b2_hugh_terminal"):
    flags[f] = True
flags.pop("b2_sailed_castelia", None)
story.story_flags["unova_version"] = "BLACK_2"
story.starting_region = "UNOVA"
story.badges["UNOVA"] = ["BASIC", "TOXIC"]
story.money = max(getattr(story, "money", 0), 5000)
_tm = json.load(open("assets/town_maps.json", encoding="utf-8"))
_c = _tm["CASTELIA_CITY"]

print("1) Castelia from Black 2's own layouts")
check((len(_c["art"][0]), len(_c["art"])) == (89, 89) and "_cam" in _c["roofs"],
      "the waterfront avenue: Black 2's rails laid on the grid, 89 x 89, through a camera")
want = {"plaza", "gym_street", "route4_street", "mode_street", "castelia_street", "narrow_street", "prime_pier", "thumb_pier",
        "unity_pier", "liberty_pier", "cruise_dock", "center", "battle_co", "battle_co_47", "battle_co_55", "game_freak", "fennel"}
check(want <= set(_c["rooms"]), f"its streets, piers and buildings are rooms ({len(_c['rooms'])})")
check(all("_cam" in _c["rooms"][r]["roofs"] for r in ("plaza", "gym_street", "mode_street", "narrow_street")), "each street through its own camera")

print("2) the ship from Virbank: Hugh registers your Xtransceiver")
said.clear()
t = town("VIRBANK_CITY", "terminal", (6, 6))
xy = next(xy for xy, o in t._people().items() if (o.get("text") if isinstance(o, dict) else "").startswith("Pop Roxie"))
t._talk(xy)
play(lambda: story.current_area_key == "CASTELIA_CITY" and isinstance(g.current_state, _WTS) and idle(), 3000)
t = g.current_state
check(story.current_area_key == "CASTELIA_CITY" and getattr(t, "room", None) == "prime_pier", f"off the boat on Prime Pier ({getattr(t, 'room', None)})")
play(lambda: flags.get("b2_castelia_arrived") and idle(), 4000)
check(flags.get("b2_castelia_arrived") and any("Xtransceiver" in x for x in said), "Hugh: let's register each other's Xtransceiver numbers")
shot("01_prime_pier")
put(13, 2, (0, -1)); step(0, -1)
play(lambda: getattr(g.current_state, "room", "x") is None and idle(), 1000)
check(getattr(g.current_state, "room", "x") is None, f"up the pier onto the waterfront avenue ({pos()})")
shot("02_avenue")

print("3) the Castelia Harlequin Hunt")
b = story.inventory.get("RARE_CANDY", 0)
talk("Harlequin")
check(story.inventory.get("BICYCLE", 0) >= 1 and flags.get("b2_hunt_start"), "the Harlequin's welcome: a Bicycle")
for room, who in (("battle_co", "Harlequin in the lobby"), ("passerby", "Harlequin at the desks"), ("medal_office", "Harlequin in the Medal Office")):
    town("CASTELIA_CITY", room)
    talk(who)
check(all(flags.get(f) for f in ("b2_hunt_medal", "b2_hunt_passerby", "b2_hunt_battleco")), "all three hidden Harlequins found")
town("CASTELIA_CITY")
talk("Harlequin ")
check(story.inventory.get("RARE_CANDY", 0) == b + 1, "back to the first: a Rare Candy")

print("4) the Battle Company: its lift and clerks")
t = town("CASTELIA_CITY", "battle_co")
shot("03_battle_co")
spot = next((tuple(int(v) for v in k.split(",")) for k in (t.town_map["rooms"]["battle_co"].get("sign_events") or {})), None)
check(spot is not None, "the lift's doors at the top wall")
from src.states.systems.pick_list import PickListState
if spot:
    t._read(spot)
play(lambda: isinstance(g.current_state, PickListState), 200)
pl = g.current_state
check(isinstance(pl, PickListState), f"the lift asks which floor ({type(pl).__name__})")
if isinstance(pl, PickListState):
    pl.pick(next(v for _l, v in pl.choices if v[1] == "battle_co_47"))
play(idle, 300)
check(getattr(g.current_state, "room", None) == "battle_co_47", f"up to 47F ({getattr(g.current_state, 'room', None)})")
battles.clear()
for who in ("Clerk Clemens", "Clerk Warren", "Clerk Gilligan", "Clerk Britney", "Developer"):
    talk(who)
check(sorted(b_[0] for b_ in battles) == ["Clerk Britney", "Clerk Clemens", "Clerk Gilligan", "Clerk Warren"], f"four clerks battle ({battles})")
check(story.inventory.get("QUICK_BALL", 0) >= 2 and story.inventory.get("TIMER_BALL", 0) >= 5 and story.inventory.get("SCOPE_LENS", 0) >= 1,
      "Quick Balls, Timer Balls and the developer's Scope Lens")

print("5) Burgh's away: Clyde and Iris; Thumb Pier; Hugh runs into the Sewers")
said.clear()
t = town("CASTELIA_CITY", "gym_street", (21, 53))
step(0, -1)
play(lambda: flags.get("b2_burgh_away") and idle(), 4000)
check(flags.get("b2_burgh_away") and any("Iris" in x for x in said), "Clyde: Burgh's out; Iris turns up with a hunch")
shot("04_gym_street")
said.clear()
put(23, 48, (1, 0)); step(1, 0); play(lambda: any("here right now" in x for x in said) and idle(), 600)
check(any("here right now" in x for x in said), f"Clyde keeps you from the Gym door ({pos()}, {said[-1:]})")
said.clear()
t = town("CASTELIA_CITY", None, (77, 46))
step(0, -1)
play(lambda: flags.get("b2_iris_thumb") and idle(), 4000)
check(flags.get("b2_iris_thumb"), f"on the avenue, Iris leads on to Thumb Pier ({pos()})")
said.clear()
t = town("CASTELIA_CITY", "thumb_pier", (3, 14))
step(1, 0)
play(lambda: flags.get("b2_thumb_scene") and idle(), 4000)
check(flags.get("b2_thumb_scene") and any("Team Plasma" in x for x in said), "Thumb Pier: Hugh runs into the Sewers")
shot("05_thumb_pier")
ex = g.current_state.town_map["rooms"]["thumb_pier"]["exits"]
check("CASTELIA_SEWERS" in ex.values(), f"the Sewers' door on Thumb Pier ({ex})")

print("6) gifts and the city's sights")
t = town("CASTELIA_CITY", "mode_street", (11, 37))
m0 = story.money
talk("Casteliacone seller")
check(story.inventory.get("CASTELIACONE", 0) >= 1 and story.money == m0 - 100, f"a Casteliacone, $100, once a day ({story.money - m0})")
t = town("CASTELIA_CITY", "narrow_street")
talk("Man by the dumpsters")
check(story.inventory.get("TM291", 0) >= 1, "Narrow Street: TM291 Flash (Black 2's TM70)")
t = town("CASTELIA_CITY", "fennel")
talk("Amanita")
check(flags.get("b2_castelia_eevee"), "Amanita's Eevee")
t = town("CASTELIA_CITY", "route4_street")
said.clear(); talk("Man on the street")
check(any("ruins" in x for x in said), "Black 2: the man talks of Route 4's ruins (White 2: its new buildings)")
t = town("CASTELIA_CITY", "plaza"); shot("06_plaza")

print("7) the Journal")
for k, mid, off in (("b2_castelia_arrived", "b2_m14", ("b2_burgh_away", "b2_thumb_scene")), ("b2_burgh_away", "b2_m15", ("b2_thumb_scene",)),
                    ("b2_thumb_scene", "b2_m16", ())):
    saved = {x: flags.pop(x, None) for x in off}
    main = [m["id"] for m in story.get_active_missions() if m.get("type") == "MAIN"]
    check(mid in main, f"after {k}: {mid} ({main})")
    flags.update({x: v for x, v in saved.items() if v})

print("8) the Castelia Sewers: Hugh walks with you; Team Plasma; Burgh, Strength, Colress")
from src.world import seasons as _seasons, walk_partners as _wp
_real_season = _seasons.current_season
_seasons.current_season = lambda date=None: "SUMMER"
_sw = _tm["CASTELIA_SEWERS"]
check((len(_sw["art"][0]), len(_sw["art"])) == (96, 96) and "_cam" in _sw["roofs"], "the Sewers: Black 2's own layout, 96 x 96, through its camera")
check([sm["when"] for sm in _sw.get("story_maps", [])] == [["season:AUTUMN"], ["season:WINTER"]]
      and _sw["story_maps"][0]["map"]["art"][13][53:59] == "cccccc" and _sw["art"][13][53:59] != "cccccc",
      "the water: high in spring and summer, low in autumn and winter (the game's own second map)")
check(set(_sw["rooms"]) == {"manhole_w", "manhole_e", "lab_m", "lab_f", "back_street"} and "CASTELIA_EMPTY_LOT" in _tm,
      "side rooms (manholes, the scientists, Back Street) and the Empty Lot")
flags["b2_thumb_scene"] = True
for f in [k for k in flags if k.startswith(("walk_hugh", "b2_sewer", "b2_got_strength", "b2_back_", "b2_empty_lot"))]:
    flags.pop(f, None)
flags["visited_CASTELIA_SEWERS"] = True
said.clear()
d = route("CASTELIA_SEWERS", "CASTELIA_CITY", (85, 20, (-1, 0)))
check(isinstance(d, _DS), f"in from Thumb Pier on the walked map ({type(d).__name__})")
step(-1, 0)
play(lambda: flags.get("walk_hugh") and idle(), 4000)
check(_wp.active(story, "CASTELIA_SEWERS") == "hugh" and any("stinky" in x for x in said), f"Hugh's waiting inside: he walks with you ({said[-3:]})")
check(d._companions() == ("{rival_name}",), f"he follows a step behind ({d._companions()})")
step(-1, 0, 3)
shot("07_sewers")
_bp = _wp.battle_partner("hugh")
check(_bp["team_choice"]["495"] == [499, 519] and _bp["levels"] == [20, 18], "his team by your starter: Pignite / Dewott / Servine 20, Pidove 18")
said.clear(); battles.clear()
put(50, 11, (0, -1)); step(0, -1)
play(lambda: flags.get("b2_sewer_plasma_battled") and idle(), 6000)
check(flags.get("b2_sewer_plasma_battled") and any("liberate" in x for x in said), f"the north walkway: you and Hugh against two Plasma Grunts ({battles})")
check(not _wp.active(story, "CASTELIA_SEWERS"), "after the battle he's no longer walking with you")
step(0, 1); step(0, -1)
play(lambda: flags.get("b2_sewers_done") and idle(), 8000)
check(flags.get("b2_sewers_done") and story.inventory.get("HM_STRENGTH", 0) >= 1, f"Hugh's thanks: HM04 Strength ({pos()}, {said[-4:]})")
check(any("Burgh" in x for x in said) and any("demonstration" in x for x in said), "Burgh turns up; Colress watches")
shot("08_sewers_after")
print("9) the Sewers' people, rooms and seasons")
battles.clear()
for xy, face in (((25, 31), (0, 1)), ((59, 50), (0, 1)), ((34, 40), (0, 1))):
    put(*xy, face); step(*face); play(idle, 3000)
check(len(battles) >= 2, f"the Sewer trainers battle you ({battles})")
d = route("CASTELIA_SEWERS", "CASTELIA_CITY", (18, 19, (0, -1)))
step(0, -1); play(idle, 600)
check(getattr(d.run, "index", 0) > 0, f"into the scientist's room ({getattr(d.run, 'index', None)})")
_seasons.current_season = lambda date=None: "AUTUMN"
d = route("CASTELIA_SEWERS", "CASTELIA_CITY", (85, 20, (-1, 0)))
check(d.run.floor.art[13][53:59] == "cccccc" if hasattr(d.run.floor, "art") else True, "in autumn, the low-water map")
shot("09_sewers_autumn")
_seasons.current_season = _real_season
d = route("CASTELIA_EMPTY_LOT", "CASTELIA_SEWERS", (8, 14, (0, -1)))
check(isinstance(d, _DS) and _tm["CASTELIA_EMPTY_LOT"].get("dark_grass"), "the Empty Lot: its park, tall and dark grass")
shot("10_empty_lot")
from src.world import wild_tables as _wt
_sp = json.load(open("assets/unova_area_data.json", encoding="utf-8"))["STORY_PROGRESSION"]
check(_wt.has(_sp["CASTELIA_SEWERS"], "grass") and _wt.has(_sp["CASTELIA_EMPTY_LOT"], "dark"), "wild tables from Black 2's file")
for k, mid, off in (("b2_thumb_scene", "b2_m16", ("b2_sewers_done",)), ("b2_sewers_done", "b2_m17", ())):
    saved = {x: flags.pop(x, None) for x in off}
    main = [m["id"] for m in story.get_active_missions() if m.get("type") == "MAIN"]
    check(mid in main, f"after {k}: {mid} ({main})")
    flags.update({x: v for x, v in saved.items() if v})


print("10) Burgh's Gym: Black 2's cocoons, three floors, the threads to Burgh")
_g = json.load(open("dev/builders/town_maps/castelia_gym.json", encoding="utf-8"))
check(len(_g["threads"]) == 16 and sorted(_g["floors"]) == ["0", "10", "20"], "the Gym's threads and floors from Black 2's gym_insect overlay")
flags["b2_sewers_done"] = True
for f in [k for k in flags if k.startswith(("gym_trainer_CASTELIA", "gym_jack", "b2_burgh_hello", "b2_clyde_castelia", "b2_insect"))]:
    flags.pop(f, None)
story.badges["UNOVA"] = ["BASIC", "TOXIC"]
t = town("CASTELIA_CITY", "gym_street")
door = next((x, y) for y, r in enumerate(t.rows) for x, c in enumerate(r) if (x, y) in t.exits and t.exits[(x, y)] == "ROOM:gym")
put(door[0] + 1, door[1], (-1, 0)); step(-1, 0); play(idle, 600)
check(getattr(g.current_state, "room", None) == "gym", f"Gym Street's door: into the Gym ({getattr(g.current_state, 'room', None)})")
t = town("CASTELIA_CITY", "gym")
fw = story.inventory.get("FRESH_WATER", 0)
talk("Clyde")
check(story.inventory.get("FRESH_WATER", 0) == fw + 1, "Clyde: a Fresh Water, and the cocoons explained")
shot("11_gym")
put(16, 13, (0, -1)); play(idle, 50)
g.current_state.step(0, -1)
_r = getattr(g.current_state, "_ride", None)
check(_r is not None and g.current_state._busy(), "walking into the centre cocoon starts the ride (animated, you can't walk meanwhile)")
for _i in range(14):
    g.current_state.update(); g.current_state.draw()
shot("14_ride_in")
for _i in range(18):
    g.current_state.update(); g.current_state.draw()
shot("15_ride_thread")
play(idle, 300)
check(getattr(g.current_state, "room", None) == "gym_10" and tuple(g.current_state.player) == (16, 12) and not getattr(g.current_state, "_ride", None),
      f"set down on the silk web once the ride ends ({getattr(g.current_state, 'room', None)}, {pos()})")
route_ = [((28, 5), (0, -1), "gym_20", (20, 7), "the right tower's ring: up to the top right")]
for (sx, sy), face, room_, at, what in route_:
    put(sx, sy, face); step(*face); play(idle, 300)
    st = g.current_state
    check(getattr(st, "room", None) == room_ and tuple(st.player) == at, f"{what} ({getattr(st, 'room', None)}, {getattr(st, 'player', None)})")
battles.clear(); said.clear()
put(23, 17, (1, 0)); step(1, 0); play(lambda: flags.get("gym_trainer_CASTELIA_CITY_2") and idle(), 3000)
check(flags.get("gym_trainer_CASTELIA_CITY_2") and any("pops out" in x for x in said), f"Harlequin Jack pops out of the lower-right cocoon ({battles})")
shot("12_gym_top")
put(25, 17, (0, -1)); step(0, -1); play(idle, 300)
check(getattr(g.current_state, "room", None) == "gym" and tuple(g.current_state.player) == (26, 6), f"the lower-right cocoon, up: down to the ground's east side ({pos()})")
put(24, 10, (0, -1)); step(0, -1); play(idle, 3000)
check(flags.get("gym_trainer_CASTELIA_CITY_3"), "Harlequin Gary")
put(28, 4, (-1, 0)); step(-1, 0); play(idle, 300)
check(getattr(g.current_state, "room", None) == "gym_20" and tuple(g.current_state.player) == (11, 5), f"the east pillar from its right: up to the top middle ({pos()})")
put(13, 3, (-1, 0)); step(-1, 0); play(idle, 300)
check(tuple(g.current_state.player) == (4, 16), f"the top middle, left: to the lower left ({pos()})")
put(8, 13, (-1, 0)); step(-1, 0); play(idle, 3000)
check(flags.get("gym_trainer_CASTELIA_CITY_4"), "Harlequin Anders")
said.clear()
put(2, 14, (1, 0)); step(1, 0); play(lambda: flags.get("b2_burgh_hello") and idle(), 3000)
check(getattr(g.current_state, "room", None) == "gym_burgh" and any("sewers" in x for x in said), f"the lower-left cocoon from its left: Burgh's studio ({getattr(g.current_state, 'room', None)})")
shot("13_burgh")
flags["gym_challenge_done_CASTELIA_CITY"] = True   # (his game before the battle: won; the minigame suites play those)
talk("Gym")
play(lambda: flags.get("b2_insect_badge") and idle(), 6000)
check(flags.get("b2_insect_badge") and "INSECT" in story.badges.get("UNOVA", []) and story.inventory.get("TM015", 0) >= 1,
      f"Burgh: the Insect Badge and TM015 Struggle Bug ({story.badges.get('UNOVA')}, {battles[-1:]})")
check(any(b[0] == "Burgh" and [p[0] for p in b[1]] == [541, 557, 542] for b in battles), "Burgh's Black 2 team: Swadloon, Dwebble, Leavanny")
put(9, 14, (0, -1)); step(0, -1); play(idle, 300)
check(getattr(g.current_state, "room", None) == "gym" and tuple(g.current_state.player) == (8, 6), f"the studio's left hole: down to the ground ({pos()})")
put(8, 6, (0, -1)); step(0, -1); play(idle, 300)
check(getattr(g.current_state, "room", None) == "gym_burgh", "with the badge, the north-west pillar goes back up to Burgh")

print(f"##### {len(fails)} failures")
