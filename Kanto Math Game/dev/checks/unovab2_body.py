# Unova batch 2 (11-20): Black 2 / White 2's story from Route 20's east gate to the boat for Castelia, walked as a player
# meets it. The gate's Great Balls; Mom's first Xtransceiver call; Roxie and Pop Roxie arguing; Virbank's bridges (over the
# deck, under it on the street); Roxie's Gym (Clyde, two bandmates, the Toxic Badge data); the Pokestar scout, the tour,
# Pop Roxie's film, your first film (the movie game) and the script list; Team Plasma at the docks (HM Cut); the Grunt on
# Route 20 and Hugh; Pop Roxie back as captain, the ship; the Complex (the daily ball swap, the foreman's Workers, the
# Scientist's Ether, the Habitat List girl, the Cut tree); wild tables. Screenshots: dev/checks/out/unovab2_*.png.
#   bash dev/checks/run.sh unovab2
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
    pygame.image.save(pygame.display.get_surface(), f"{S}/unovab2_{name}.png")


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
for f in [k for k in flags if k.startswith(("b2_", "gym_trainer_VIRBANK", "pokestar_", "medal_"))]:
    flags.pop(f, None)
for f in ("b2_mom_talk", "b2_hugh_met", "received_starter_unova", "received_pokedex_unova", "b2_hugh_battled", "b2_led_to_center",
          "b2_center_tour", "b2_send_off", "b2_town_map", "b2_route19_lesson", "b2_ledge_demo", "b2_alder_met", "b2_floccesy_met",
          "b2_alder_maps", "b2_hugh_ranch", "b2_ranch_owners", "b2_herdier_found", "b2_alder_training", "b2_gym_open",
          "b2_basic_badge", "b2_jerome", "b2_cheren_route20", "b2_habitat_list", "b2_bianca_return"):
    flags[f] = True   # (batch 1 played: unovab1)
story.starting_region = "UNOVA"
story.story_flags["unova_version"] = "BLACK_2"   # (the version picked at the start: unovastart plays the pick)
story.badges["UNOVA"] = ["BASIC"]
for a in ("UNOVA_ROUTE_20", "VIRBANK_COMPLEX"):
    story.defeated_trainers.pop(a, None)
story.inventory.pop("HM_CUT", None)
_lead = story.player_team[0] if story.player_team else None
if _lead is None or _lead.id != 495:
    raw = g.loader.fetch_specific(495)
    from src.pokemon.data import Pokemon
    story.player_team = [Pokemon(raw, g.assets, size_mult=3.125)]
story.player_team[0].level = max(story.player_team[0].level, 18)
_tm = json.load(open("assets/town_maps.json", encoding="utf-8"))
_sp = g.loader.area_data["STORY_PROGRESSION"]

print("1) the maps: batch 2 from Black 2's own layouts")
for k, size in (("VIRBANK_CITY", (64, 32)), ("VIRBANK_COMPLEX_OUTSIDE", (32, 32)), ("VIRBANK_COMPLEX", (32, 64)),
                ("POKESTAR_STUDIOS", (64, 64))):
    m = _tm.get(k) or {}
    check(m and (len(m["art"][0]), len(m["art"])) == size and "_cam" in m.get("roofs", {}), f"{k}: Black 2's {size[0]} x {size[1]}, drawn from its camera")
check(set(_tm["VIRBANK_CITY"]["rooms"]) == {"gate_w", "center", "house_ne", "nursery", "house_s", "terminal", "gate_n", "gym", "gym_stage"},
      "Virbank's rooms: both gates, the Center, three houses, the ship terminal, the Gym's lobby and stage")
check(set(_tm["POKESTAR_STUDIOS"]["rooms"]) == {"studio", "studio_vfx", "theater"}, "Pokestar Studios: the soundstage, its effects room, the theater")
_va = _tm["VIRBANK_CITY"]["art"]
check(_va[11][11] == ";" and _va[13][11] == "." and _va[18][18] == "|" and _va[30][24] == ";",
      "Virbank's lower level from the file's second walk layer: underpasses beneath the main street, the lane and the pier street")
_ca = _tm["VIRBANK_COMPLEX"]["art"]
check(all(_ca[y][8] == "|" for y in range(30, 35)) and _ca[44][23] == ";" and "m" not in "".join(_ca),
      "the Complex's raised walkways over the grass (bridges: along on top, across underneath); no counters on a route")
_nur = _tm["VIRBANK_CITY"]["rooms"]["nursery"]["art"]
check(sum(r.count("N") for r in _nur) == 6 and _nur[11][5] == "v", "the nursery's people and door on its own floor (its walk grid re-anchored)")
check(len(_tm["VIRBANK_COMPLEX"].get("trainer_spots", [])) == 3 and _tm["VIRBANK_COMPLEX"]["art"][24][4] == "2",
      "the Complex: three trainers where Black 2 has them; the small tree on the west path is for Cut")

print("2) Route 20's east gate: the attendant's Great Balls; into Virbank, Mom calls")
_gb = story.inventory.get("GREAT_BALL", 0)
route("UNOVA_ROUTE_20", "FLOCCESY_TOWN", (56, 11, (1, 0)))
step(1, 0)
play(lambda: story.current_area_key == "VIRBANK_CITY" and idle(), 3000)
t = g.current_state
check(story.current_area_key == "VIRBANK_CITY" and getattr(t, "room", None) == "gate_w", f"east off Route 20 into Virbank's gate ({getattr(t, 'room', None)}, {pos()})")
said.clear()
put(12, 5, (1, 0)); step(1, 0)
play(lambda: flags.get("b2_virbank_gate_balls") and idle(), 3000)
check(story.inventory.get("GREAT_BALL", 0) == _gb + 2, "the attendant comes over: 2 Great Balls")
shot("01_gate")
put(14, 5, (1, 0)); step(1, 0)
play(lambda: getattr(g.current_state, "room", "x") is None and idle(), 1000)
check(getattr(g.current_state, "room", "x") is None and pos()[0] <= 3, f"out of the gate into Virbank City ({pos()})")
shot("02_virbank")
said.clear()
put(2, 10, (1, 0)); step(1, 0)
play(lambda: flags.get("b2_virbank_arrived") and idle(), 3000)
check(calls and calls[-1].caller == "Mom" and flags.get("b2_mom_called"), "the Xtransceiver rings: Mom's video call, animated")
check(any("Complex" in x for x in said), "Mom: see the Virbank Complex at night")

print("3) Roxie and her father; the road north is shut; the bridges")
said.clear()
put(9, 11, (1, 0)); step(1, 0, 4)   # (along the street, under the bridge, to the Center)
play(lambda: flags.get("b2_roxie_argument") and idle(), 4000)
check(flags.get("b2_roxie_argument") and any("DOOFUS" in x for x in said) and any("Pokestar" in x for x in said),
      f"by the Center: Pop Roxie off to be a movie star, Roxie furious ({flags.get('b2_roxie_argument')}, {said[:3]}, {pos()})")
said.clear()
put(25, 3, (0, -1)); step(0, -1)
play(idle, 600)
check(pos()[1] >= 3 and any("Auditions" in x or "pass" in x for x in said), f"no badge: the guard keeps you off the studios' road ({pos()})")
put(11, 14, (0, -1))
step(0, -1, 3)
check(pos() == (11, 11) and not g.current_state.deck, f"through the underpass beneath the main street ({pos()}, deck {g.current_state.deck})")
shot("02b_underpass")
step(0, -1, 4)
check(pos() == (11, 7), f"...up to the sunken stairway corner ({pos()})")
put(8, 10, (1, 0))
step(1, 0, 6)
check(pos() == (14, 10) and g.current_state.deck, f"along the street over it ({pos()}, deck {g.current_state.deck})")

print("4) Roxie's Gym")
t = town("VIRBANK_CITY", "gym", (8, 5))
said.clear()
put(9, 4, (0, -1)); step(0, -1)
play(lambda: flags.get("b2_clyde_virbank") and idle(), 3000)
check(flags.get("b2_clyde_virbank") and story.inventory.get("FRESH_WATER", 0) >= 1, "Clyde comes over: a Fresh Water")
t = town("VIRBANK_CITY", "gym_stage", (8, 12))
shot("03_gym_stage")
check(t.gym_closed() is not None, "Roxie can't hear you: her bandmates first")
battles.clear()
for who in ("Roughneck Nicky", "Guitarist Billy Jo"):
    talk(who)
check([b[0] for b in battles] == ["Roughneck Nicky", "Guitarist Billy Jo"] and all(lv == 14 for b in battles for _i, lv in b[1]),
      f"Nicky and Billy Jo, Lv. 14 ({battles})")
check(g.current_state.gym_closed() is None, "the music stops: Roxie will battle you")
_gym = _sp["VIRBANK_CITY"]["gym"]["leader"]
check(_gym["team"] == [109, 544] and _gym["levels"] == [16, 18] and _gym["badge_reward"] == "TOXIC" and _gym["rewards"].get("TM045"),
      "Roxie: Koffing 16, Whirlipede 18 (Normal mode); the Toxic Badge and TM045 Venoshock")
from src.world import levels as _lv
check(_lv.GYM_ACE.get("UNOVA", [0, 0])[1] == 18 if isinstance(_lv.GYM_ACE.get("UNOVA"), list) else True, "the second Gym's ace is Black 2's Lv. 18")
story.badges["UNOVA"] = ["BASIC", "TOXIC"]; flags["b2_toxic_badge"] = True
said.clear()
t = town("VIRBANK_CITY", "gym_stage", (8, 12))
play(lambda: flags.get("b2_scout_met") and idle(), 4000)
check(flags.get("b2_scout_met") and any("Pokestar" in x for x in said) and any("old man" in x for x in said),
      "after the badge: the Pokestar scout, and Roxie runs off after her father")

print("5) Pokestar Studios: the tour, Pop Roxie's film, your first film")
said.clear()
story.last_area_key = "VIRBANK_CITY"
t = town("POKESTAR_STUDIOS")
play(lambda: flags.get("b2_pokestar_tour") and flags.get("b2_pop_roxie_movie") and idle(), 8000)
check(flags.get("b2_pokestar_tour") and any("Stu Deeoh" in x for x in said), "the scout and the boss, Stu Deeoh, meet you and show you round")
check(getattr(g.current_state, "room", None) == "theater" and flags.get("b2_pop_roxie_movie") and any("RIOLU-MAN" in x for x in said),
      f"into the theater: Pop Roxie's film flops ({getattr(g.current_state, 'room', None)})")
shot("04_theater")
said.clear(); films.clear()
FILM_PICK.update(want="good", script=None)
t = town("POKESTAR_STUDIOS", "studio", (14, 21))
put(14, 21, (0, -1)); step(0, -1)
play(lambda: flags.get("b2_first_film") and idle(), 6000)
check(films and films[0][0] == "brycen_man" and films[0][1] == "good", f"your first film, Brycen-Man Strikes Back: a happy ending ({films})")
check(_ps.rank(story) == 2 and flags.get("pokestar_happy_brycen_man"), "your Star Rank rises; the next script opens")
check([s["key"] for s in _ps.unlocked(story)] == ["brycen_man", "full_metal_cop"], "the script list: two now")
films.clear()
FILM_PICK.update(want="odd", script="full_metal_cop")
talk("Assistant director")
check(films and films[0] == ("full_metal_cop", "odd", 3), f"the assistant director's list: Full Metal Cop, a strange ending ({films})")
check(not flags.get("pokestar_happy_full_metal_cop") and len(_ps.unlocked(story)) == 2, "a strange ending doesn't open the next script")
from src.world import medals as _medals
story.inventory["MEDAL_BOX"] = 1
_ml = _medals.hand_out(story)
check(flags.get("medal_film_1") and flags.get("medal_film_happy"), f"Mr. Medal's Pokestar medals: Rising Star, Happy Ending ({_ml[1:3]})")

print("6) Team Plasma at the docks; HM Cut")
said.clear(); battles.clear()
t = town("VIRBANK_CITY", None, (41, 30))
check(any((o.get("text") if isinstance(o, dict) else None) == "Plasma Grunt" for o in t._people().values()), "Roxie, Hugh and three Grunts on the pier")
step(1, 0, 3)
play(lambda: flags.get("b2_dock_scene") and idle(), 4000)
check(flags.get("b2_dock_scene") and any("Team Plasma" in x for x in said), "Roxie and Hugh confront Team Plasma")
shot("05_docks")
put(48, 30, (1, 0))
talk("Plasma Grunt")
play(lambda: flags.get("b2_virbank_dock") and idle(), 4000)
check(any(b[0] == "Plasma Grunt" and b[1] == [(504, 14)] for b in battles), f"the Grunt in the middle: Patrat, Lv. 14 ({battles})")
check(flags.get("b2_virbank_dock") and story.inventory.get("HM_CUT", 0) == 1, "Roxie's thanks: HM01 Cut")
check(any("Route 20" in x for x in said), "Roxie: check Route 20")

print("7) the runaway Grunt on Route 20; Hugh's news")
said.clear(); battles.clear()
d = route("UNOVA_ROUTE_20", "VIRBANK_CITY", (26, 27, (1, 0)))
step(1, 0)
play(lambda: flags.get("b2_r20_hugh") and idle(), 5000)
check(any(b[0] == "Plasma Grunt" and b[1] == [(509, 14)] for b in battles), f"the Grunt in the clearing: Purrloin, Lv. 14 ({battles})")
check(flags.get("b2_r20_hugh") and any("ship" in x for x in said), "Hugh: Team Plasma's travelling by ship")

print("8) Pop Roxie back as captain; the ship to Castelia")
said.clear()
t = town("VIRBANK_CITY", None, (42, 30))
step(1, 0, 2)
play(lambda: flags.get("b2_pop_roxie_back") and idle(), 4000)
check(flags.get("b2_pop_roxie_back") and any("captain" in x for x in said), "Pop Roxie, back from the studios, will captain again")
said.clear()
t = town("VIRBANK_CITY", "terminal", (6, 10))
play(lambda: flags.get("b2_hugh_terminal") and idle(), 3000)
check(flags.get("b2_hugh_terminal") and any("Castelia" in x for x in said), "Hugh at the terminal: off to Castelia")
shot("06_terminal")
put(6, 5, (0, -1))
talk("Pop Roxie")
play(lambda: story.current_area_key == "CASTELIA_CITY", 3000)
check(story.current_area_key == "CASTELIA_CITY" and flags.get("b2_sailed_castelia"), f"all aboard: to Castelia City ({story.current_area_key}, {said[-2:]}, {pos()}, {type(g.current_state).__name__})")

print("9) the Virbank Complex")
_balls, _gb = getattr(story, "balls_left", 0), story.inventory.get("GREAT_BALL", 0)
story.balls_left = max(_balls, 3); _balls = story.balls_left
flags["visited_VIRBANK_COMPLEX_OUTSIDE"] = flags["visited_VIRBANK_COMPLEX"] = True   # (been before: no first-visit reveal in the pictures)
d = route("VIRBANK_COMPLEX_OUTSIDE", "VIRBANK_CITY", (20, 9, (1, 0)))
shot("07_complex_outside")
step(1, 0); play(idle, 2000)
check(story.balls_left == _balls - 1 and story.inventory.get("GREAT_BALL", 0) == _gb + 1, "the Roughneck: your Poke Ball for his Great Ball")
step(1, 0); play(idle, 2000)
check(story.balls_left == _balls - 1, "once a day only")
d = route("VIRBANK_COMPLEX", "VIRBANK_COMPLEX_OUTSIDE", (14, 26, (1, 0)))
shot("08_complex")
step(1, 0); play(idle, 2000)
check(flags.get("b2_foreman_ask"), "the foreman: fire up my three new Workers")
battles.clear()
for xy, face in (((29, 51), (1, 0)), ((19, 32), (1, 0)), ((4, 32), (1, 0))):
    put(*xy, face); step(*face); play(idle, 3000)
check(sorted(b[0] for b in battles) == ["Worker Isaac", "Worker Mitchell", "Worker Nathan"] and all(lv == 12 for b in battles for _i, lv in b[1]),
      f"Isaac, Mitchell and Nathan, Lv. 12 ({battles}, {[k for k in flags if k.startswith('b2_worker')]}, {said[-3:]})")
put(14, 26, (1, 0)); step(1, 0); play(idle, 2000)
check(story.inventory.get("TM294", 0) >= 1, "the foreman's thanks: TM294 Rock Smash (Black 2's TM94)")
_e = story.inventory.get("ETHER", 0)
put(28, 32, (1, 0)); step(1, 0); play(idle, 2000)
put(9, 44, (1, 0)); step(1, 0); play(idle, 2000)
put(13, 55, (1, 0)); step(1, 0); play(idle, 2000)
check(story.inventory.get("ETHER", 0) == _e + 1, "the Scientist, heard out three times: an Ether")
_gb = story.inventory.get("GREAT_BALL", 0)
put(10, 54, (1, 0)); step(1, 0); play(idle, 2000)
check(story.inventory.get("GREAT_BALL", 0) == _gb, "the Habitat List girl: not full yet")
_want = {int(s[0]) for season in _sp["VIRBANK_COMPLEX"]["wild_tables"].values() for kind in season.values() for s in kind}
g.data.data.setdefault("seen_pokemon", []).extend(sorted(_want))
check(story.habitat_done("VIRBANK_COMPLEX"), "every Complex species seen: its Habitat List is full")
d = route("VIRBANK_COMPLEX", "VIRBANK_COMPLEX_OUTSIDE", (10, 54, (1, 0)))   # (back another time: she sees the full list)
step(1, 0); play(idle, 2000)
check(story.inventory.get("GREAT_BALL", 0) == _gb + 5, "the list full: 5 Great Balls")
d = route("VIRBANK_COMPLEX", "VIRBANK_COMPLEX_OUTSIDE", (8, 29, (0, 1)))
step(0, 1, 5)
check(pos() == (8, 34) and d.run.deck, f"down the raised walkway over the grass, on top ({pos()}, deck {d.run.deck})")
put(7, 32, (1, 0)); d.run.deck = True
step(1, 0)
check(pos() == (8, 32) and not d.run.deck, f"across it through the grass: underneath ({pos()}, deck {d.run.deck})")
from src.world import wild_tables as _wt
_cx = _sp["VIRBANK_COMPLEX"]
check(_wt.has(_cx, "grass") and _wt.has(_cx, "dark") and _wt.has(_cx, "rustle"), "the Complex's wild tables: grass, dark grass, rustling grass")
check(_wt.has(_sp["VIRBANK_COMPLEX_OUTSIDE"], "grass"), "and the outside's")

print("10) the Journal follows the story")
want = [("b2_virbank_arrived", "b2_m9"), ("b2_toxic_badge", "b2_m10"), ("b2_first_film", "b2_m11"), ("b2_virbank_dock", "b2_m12"),
        ("b2_r20_hugh", "b2_m13")]
_keep = {k: flags.get(k) for k, _m in want + [("b2_sailed_castelia", None)]}
for k in _keep:
    flags.pop(k, None)
story.current_area_key = "VIRBANK_CITY"
for k, mid in want:
    flags[k] = True
    main = [m["id"] for m in story.get_active_missions() if m.get("type") == "MAIN"]
    check(mid in main, f"after {k}: {mid} ({main})")
for k, v in _keep.items():
    if v:
        flags[k] = v

print(f"##### {len(fails)} failures")
