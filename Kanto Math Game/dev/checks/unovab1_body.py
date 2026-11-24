# Unova batch 1 (11-20): Black 2 / White 2's story from Route 19 to the first badge, walked as a player meets it.
# Route 19 into Floccesy (Alder waits); the two Town Maps; Route 20 (Hiker Jerome won't let you up the steps yet); up to
# Floccesy Ranch: Hugh's battle, the owners, the missing Herdier, the Plasma Grunt; Alder's two students; the Gym opens;
# Cheren's Gym behind the Trainers' School; after the badge: Jerome, Cheren and Hugh by the dark grass, Bianca's gifts.
# Screenshots go to dev/checks/out/unovab1_*.png. Glue after harness_head.py:
#   bash dev/checks/run.sh unovab1
import json
from src.states.overworld import CityState, PlayState
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.states.overworld.dungeon import DungeonState as _DS
from src.states.battle import TrainerIntroState, TrainerBattleState

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.player_character = "nate"
g.rival_name = "HUGH"
said = []
battles = []


def _note(st):
    box = getattr(st, "npc_dialogue", None) if getattr(st, "npc_active", False) else getattr(st, "dialogue_box", None)
    if box is not None and getattr(box, "visible", True):
        for line in getattr(box, "text_lines", []) or []:
            if not said or said[-1] != line:
                said.append(line)


def _win(b):
    """A trainer battle: noted, and won."""
    b = getattr(b, "next_state", None) or b
    if isinstance(b, TrainerBattleState):
        battles.append((getattr(b, "trainer_name", None), [(p.id, p.level) for p in b.opponent_team]))
        g.change_state(b)
        b.player_won = True
        b.exit_battle()
        return True
    return False


def play(until, n=3000):
    for _ in range(n):
        if until():
            return True
        st = g.current_state
        if isinstance(st, (TrainerIntroState, TrainerBattleState)):
            _win(st)
            continue
        if isinstance(st, _DS) and getattr(st, "mode", None) == "CHOICE":   # (a wild Pokemon in the grass on the way: not
            mv = st.encounter                                                 #  this suite's business: it wanders off)
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
    return tuple(st.run.player) if isinstance(st, _DS) else tuple(st.player)


def idle():
    st = g.current_state
    if isinstance(st, _WTS):
        return not st._busy() and st.anim == 0
    if isinstance(st, _DS):
        return st.anim == 0 and not getattr(st, "_scene_lock", False) and not getattr(st, "npc_active", False)
    return False


def put(x, y, face=(0, 1)):
    st = g.current_state
    if isinstance(st, _DS):
        st.run.player = st.anim_from = (x, y)
    else:
        st.player = st.anim_from = (x, y)
        st.partner = st.partner_from = (x, y)
    st.anim = 0
    st.facing = face


def step(dx, dy, n=1):
    for _ in range(n):
        play(idle, 600)
        g.current_state.step(dx, dy)
        play(lambda: g.current_state.anim == 0 if hasattr(g.current_state, "anim") else True, 80)


def shot(name):
    g.current_state.draw()
    pygame.image.save(pygame.display.get_surface(), f"{S}/unovab1_{name}.png")


def at(area, room=None):
    st = g.current_state
    return story.current_area_key == area and (room is None or getattr(st, "room", None) == room) and idle()


flags = story.story_flags
for f in [k for k in flags if k.startswith("b2_") or k.startswith("gym_trainer_ASPERTIA")]:
    flags.pop(f, None)
for f in ("b2_mom_talk", "b2_hugh_met", "received_starter_unova", "received_pokedex_unova", "b2_hugh_battled", "b2_led_to_center",
          "b2_center_tour", "b2_send_off", "b2_town_map", "b2_route19_lesson", "b2_ledge_demo", "b2_alder_met"):
    flags[f] = True   # (the opening and Route 19 played: unovastart, unovacam)
story.starting_region = "UNOVA"
story.story_flags["unova_version"] = "BLACK_2"   # (the version picked at the start: unovastart plays the pick)
story.badges["UNOVA"] = []
story.defeated_trainers.pop("UNOVA_ROUTE_20", None); story.defeated_trainers.pop("FLOCCESY_RANCH", None)
_snivy = story.player_team[0] if story.player_team else None
if _snivy is None or _snivy.id != 495:
    raw = g.loader.fetch_specific(495)
    from src.pokemon.data import Pokemon
    story.player_team = [Pokemon(raw, g.assets, size_mult=3.125)]
story.player_team[0].level = max(story.player_team[0].level, 12)
_tm = json.load(open("assets/town_maps.json", encoding="utf-8"))

print("1) the maps: batch 1 from Black 2's own layouts")
for k, size in (("FLOCCESY_TOWN", (32, 64)), ("UNOVA_ROUTE_20", (64, 64)), ("FLOCCESY_RANCH_OUTSIDE", (32, 32)),
                ("FLOCCESY_RANCH", (64, 64)), ("PLEDGE_GROVE", (32, 64))):
    m = _tm.get(k) or {}
    check(m and (len(m["art"][0]), len(m["art"])) == size and "_cam" in m.get("roofs", {}), f"{k}: Black 2's {size[0]} x {size[1]}, drawn from its camera")
check(set(_tm["FLOCCESY_TOWN"].get("rooms", {})) == {"alder", "house_w", "house_e", "center"}, "Floccesy's rooms: Alder's house, two houses, the Pokemon Center")
check("gym" in _tm["ASPERTIA_CITY"]["rooms"] and _tm["ASPERTIA_CITY"]["rooms"]["school"]["exits"].get("^") == "ROOM:gym",
      "Aspertia's Gym: behind the Trainers' School, through its back door")
check(len(_tm["UNOVA_ROUTE_20"].get("trainer_spots", [])) == 7 and len(_tm["FLOCCESY_RANCH"].get("trainer_spots", [])) == 3,
      "trainers where Black 2 has them: Route 20 7, the Ranch 3")

print("2) Route 19 into Floccesy: Alder is waiting")
story.current_area_key, story.last_area_key = "UNOVA_ROUTE_19", "ASPERTIA_CITY"
g.change_state(PlayState(g))
play(lambda: isinstance(g.current_state, _DS) and idle(), 300)
put(62, 22, (1, 0))
said.clear()
step(1, 0)
play(lambda: isinstance(g.current_state, _WTS) and story.current_area_key == "FLOCCESY_TOWN", 600)
t = g.current_state
check(isinstance(t, _WTS) and story.current_area_key == "FLOCCESY_TOWN" and pos()[0] <= 1 and 53 <= pos()[1] <= 57,
      f"east off Route 19, into Floccesy by its west road ({story.current_area_key}, {pos()})")
shot("01_floccesy")
step(1, 0)
play(lambda: flags.get("b2_floccesy_met") and idle(), 2000)
check(flags.get("b2_floccesy_met") and any("Alder" in x for x in said), f"Alder greets you as you come in ({said[:1]})")
said.clear()
put(17, 31, (0, -1))
step(0, -1)
play(lambda: flags.get("b2_alder_maps") and idle(), 2000)
check(flags.get("b2_alder_maps") and any("Town Map" in x for x in said) and any("Route 20" in x for x in said),
      f"by the clock tower: why two Town Maps? Hugh's on Route 20 ({[x for x in said if 'Town Map' in x][:1]})")

print("3) Route 20: Hiker Jerome keeps the steps; up to the ranch")
put(30, 22, (1, 0))
step(1, 0)
play(lambda: isinstance(g.current_state, _DS) and story.current_area_key == "UNOVA_ROUTE_20" and idle(), 600)
d = g.current_state
check(isinstance(d, _DS) and story.current_area_key == "UNOVA_ROUTE_20" and pos()[0] <= 1, f"east out of Floccesy onto Route 20 ({pos()})")
shot("02_route20")
said.clear()
put(30, 4, (1, 0))
step(1, 0)
play(idle, 600)
check(pos()[0] <= 30 and any("Badge" in x for x in said), f"no badge: Jerome turns you back from the steps ({pos()}, {said[:1]}, {type(g.current_state).__name__})")
put(15, 1, (0, -1))
step(0, -1)
play(lambda: story.current_area_key == "FLOCCESY_RANCH_OUTSIDE" and idle(), 600)
check(story.current_area_key == "FLOCCESY_RANCH_OUTSIDE", f"north up the path toward the ranch ({story.current_area_key}, {pos()})")
put(14, 22, (0, -1))
step(0, -1)
play(lambda: story.current_area_key == "FLOCCESY_RANCH" and idle(), 600)
check(story.current_area_key == "FLOCCESY_RANCH" and pos()[1] >= 50, f"under the arch into Floccesy Ranch ({pos()})")
shot("03_ranch")

print("4) the ranch: Hugh's battle, the Town Map, the owners, Herdier")
battles.clear(); said.clear()
put(41, 47, (0, -1))
step(0, -1)
play(lambda: flags.get("b2_hugh_ranch") and flags.get("b2_ranch_owners") and idle(), 6000)
check(any(b[1] == [(498, 8)] for b in battles), f"Hugh battles you: Tepig, Lv. 8, strong against your Snivy ({battles[:1]})")
check(flags.get("b2_ranch_owners") and any("Town Map" in x for x in said) and any("Herdier" in x for x in said),
      f"you give him the Town Map; the owners' Herdier is missing ({[x for x in said if 'Herdier' in x][:1]})")
check(flags.get("b2_ranch_potion"), "the owner's wife gives you a Potion")
said.clear()
put(22, 35, (0, -1)); step(0, -1)
play(lambda: flags.get("b2_ranch_north") and idle(), 2000)
check(flags.get("b2_ranch_north"), "Hugh heads into the north woods with you")
_ph = story.inventory.get("PARALYZE_HEAL", 0)
put(23, 14, (0, -1)); step(0, -1)
play(lambda: flags.get("b2_ranch_parlyz") and idle(), 2000)
check(flags.get("b2_ranch_parlyz") and story.inventory.get("PARALYZE_HEAL", 0) == _ph + 1, "by the janitor, Hugh shares a Paralyze Heal")
put(41, 15, (0, -1)); step(0, -1)
play(lambda: flags.get("b2_ranch_cry") and idle(), 2000)
check(flags.get("b2_ranch_cry") and any("hear" in x for x in said), "a cry from the woods: Hugh sends you deeper in")
said.clear()
put(50, 26, (0, -1)); step(0, -1)
_seen = []
for _ in range(400):
    st = g.current_state
    if hasattr(st, "_scenes") and any("c293" in str(a.get("sheet")) for a in st._scenes().actors) and not _seen:
        _seen.append(1); shot("04_grunt")
    if flags.get("b2_herdier_found") and idle():
        break
    play(lambda: False, 1)
play(lambda: flags.get("b2_herdier_found") and idle(), 4000)
check(flags.get("b2_herdier_found") and any("Team Plasma" in x for x in said), f"Herdier found, a Plasma Grunt with it ({[x for x in said if 'Plasma' in x][:1]})")
check(story.inventory.get("TM273", 0) >= 1, "the Grunt throws TM273 Frustration at you as he runs")
check(bool(_seen), "the Grunt is on the map in the scene")

print("5) Alder's students, then the Gym opens")
battles.clear(); said.clear()
story.current_area_key = "FLOCCESY_TOWN"
g.walk_town_pos, g.walk_town_room = (11, 22), None
g.change_state(CityState(g))
play(idle, 300)
t = g.current_state
put(11, 22, (0, -1))
step(0, -1)
play(lambda: flags.get("b2_alder_training") and idle(), 8000)
check([b[1] for b in battles][:2] == [[(515, 9)], [(513, 9)]],
      f"his students: Seymour's Panpour, then Cassie's Pansear, Lv. 9 (strong against Snivy) ({battles})")
check(flags.get("b2_alder_training") and any("type" in x.lower() for x in said), "Alder's lesson on types")
shot("05_alder")
t = g.current_state
_door = next(xy for xy, v in t.exits.items() if str(v).startswith("OUT:"))
put(_door[0], _door[1] - 1, (0, 1)); said.clear()
step(0, 1)
play(lambda: flags.get("b2_gym_open") and idle(), 4000)
check(flags.get("b2_gym_open") and any("Mr. Medal" in x for x in said) and any("Gym" in x for x in said),
      f"outside: Mr. Medal, and Alder's news: Aspertia's Gym Leader has arrived ({[x for x in said if 'Gym' in x][:1]})")

print("6) Cheren's Gym, behind the Trainers' School")
story.current_area_key = "ASPERTIA_CITY"
g.walk_town_pos, g.walk_town_room = None, "school"
g.change_state(CityState(g))
play(idle, 300)
t = g.current_state
if getattr(t, "room", None) != "school":
    t._go("school", None); play(idle, 300); t = g.current_state
check(getattr(t, "room", None) == "school", f"in the Trainers' School ({getattr(t, 'room', None)})")
put(9, 2, (0, -1))
step(0, -1)
play(lambda: getattr(g.current_state, "room", None) == "gym" and idle(), 600)
t = g.current_state
check(getattr(t, "room", None) == "gym", f"out the back door into the Gym ({getattr(t, 'room', None)})")
shot("06_gym")
check(t.gym_closed() is not None, "Cheren wants his two Gym Trainers beaten first")
battles.clear()
for who in ("Youngster Pedro", "Lass Serena", "Clyde"):
    xy = next((xy for xy, o in t._people().items() if (o.get("text") if isinstance(o, dict) else None) == who), None)
    if xy:
        t._talk(xy); play(idle, 3000); t = g.current_state
check([b[0] for b in battles] == ["Youngster Pedro", "Lass Serena"] and all(lv == 9 for b in battles for _i, lv in b[1]),
      f"Pedro and Serena, Lv. 9 ({battles})")
check(story.inventory.get("FRESH_WATER", 0) >= 1, "Clyde, the Gym guide: a Fresh Water for your debut")
check(t.gym_closed() is None, "now Cheren will battle you")
from src.world import levels as _lv
check(_lv.gym_team_levels("UNOVA", "ASPERTIA_CITY", 2, "leader") == [11, 13], "Cheren's team at Black 2's levels: Patrat 11, Lillipup 13")

print("7) after the Basic Badge")
story.badges["UNOVA"] = ["BASIC"]; flags["b2_basic_badge"] = True
said.clear()
story.current_area_key = "ASPERTIA_CITY"
g.walk_town_pos, g.walk_town_room = (7, 35), None
g.change_state(CityState(g))
play(lambda: flags.get("b2_bianca_return") and idle(), 3000)
check(flags.get("b2_bianca_return") and story.inventory.get("TM274", 0) >= 1, "Bianca's present outside: TM274 Return")
said.clear()
story.current_area_key, story.last_area_key = "UNOVA_ROUTE_20", "FLOCCESY_TOWN"
g.change_state(PlayState(g))
play(lambda: isinstance(g.current_state, _DS) and idle(), 300)
battles.clear()
put(30, 5, (1, 0))
d = g.current_state
xy = (31, 5)
d.run.player = (30, 5)
if hasattr(d, "_talk_at"):
    d._talk_at(xy)
else:
    d.step(1, 0)
play(idle, 3000)
check(any(b[0] == "Hiker Jerome" and b[1] == [(447, 11)] for b in battles) or flags.get("b2_jerome"),
      f"Jerome battles you now: Riolu, Lv. 11 ({battles[:1]})")
said.clear()
put(34, 18, (0, 1)); step(0, 1)
play(lambda: flags.get("b2_cheren_route20") and idle(), 4000)
check(flags.get("b2_cheren_route20") and any("dark" in x for x in said) and story.inventory.get("PECHA_BERRY", 0) >= 3,
      f"Cheren and Hugh by the dark grass; 3 Pecha Berries ({[x for x in said if 'dark' in x][:1]})")
shot("07_route20_east")

print("8) the 'not done yet' (11-20, Jordan's answers): wild tables, dark grass, seasons, phenomena")
import random as _rnd
from src.world import seasons as _seasons, wild_tables as _wt, phenomena as _phen, medals as _medals
_real_season = _seasons.current_season
sp_ = g.loader.area_data["STORY_PROGRESSION"]
r20 = sp_["UNOVA_ROUTE_20"]
check(set(_wt.tables(r20)) == {"SPRING", "SUMMER", "AUTUMN", "WINTER"} and _wt.has(r20, "dark") and _wt.has(r20, "rustle"),
      "Route 20's wild Pokemon from Black 2's file: four seasons, grass, dark grass, rustling grass, water")
_seasons.current_season = lambda date=None: "SUMMER"
_sum = _wt.pool(r20, "grass")
_seasons.current_season = lambda date=None: "SPRING"
_spr = _wt.pool(r20, "grass")
check(_sum.get("191", 0) > _spr.get("191", 0), f"in summer more Sunkern come out ({_spr.get('191')} -> {_sum.get('191')})")
story.current_area_key, story.last_area_key = "UNOVA_ROUTE_20", "FLOCCESY_TOWN"
g.change_state(PlayState(g))
play(lambda: isinstance(g.current_state, _DS) and idle(), 300)
d = g.current_state
_dark = sorted(d._dark_tiles())
check(len(_dark) >= 90, f"Route 20's dark grass, from the game's walk data ({len(_dark)} tiles)")
d._wild_spot = _dark[0]
_lv = [d._from_wild_tables(_rnd.Random(k)).level for k in range(12)]
d._wild_spot = (24, 8)
_lg = [d._from_wild_tables(_rnd.Random(k)).level for k in range(12)]
check(min(_lv) >= 9 and max(_lg) <= 4, f"dark grass Pokemon are stronger (Lv. {min(_lv)}-{max(_lv)}) than the tall grass's (Lv. {min(_lg)}-{max(_lg)})")
d._phenom_kind = "rustle"
_rs = {d._from_wild_tables(_rnd.Random(k)).id for k in range(30)}
d._phenom_kind = None
check(_rs <= {531, 206} and 531 in _rs, f"rustling grass: Audino (and Dunsparce) ({sorted(_rs)})")
_st = _phen._state(d)
_st.update(spot=None, quiet=99)
d.run.player = d.anim_from = (27, 12); d.anim = 0   # (by the tall grass west of the steps)
_ok = False
for k in range(40):
    sp_t, kind = _phen._start(d, _rnd.Random(k))
    if sp_t and kind == "rustle":
        _st.update(spot=sp_t, kind=kind, floor=d.run.index)
        _ok = True
        break
check(_ok, f"a patch of tall grass near you starts to rustle ({_st.get('spot')})")
if _ok:
    shot("08_rustle")
    d.run.player = d.anim_from = _st["spot"]; d.anim = 0
    _phen.on_step(d)
    _enc = getattr(d, "encounter", None)
    check(_enc is not None and _enc.payload.id in (531, 206), f"step into it: its own Pokemon jumps out ({getattr(getattr(_enc, 'payload', None), 'id', None)})")
    d.encounter, d.mode = None, "MAP"
_seasons.current_season = lambda date=None: "AUTUMN"
story.current_area_key, story.last_area_key = "UNOVA_ROUTE_20", "FLOCCESY_TOWN"
g.change_state(PlayState(g))
play(lambda: isinstance(g.current_state, _DS) and idle(), 300)
d = g.current_state
f_ = d.run.floor
check(f_.walkable(15, 11), "in autumn the leaves open the way to the Poke Ball west of the steps (Black 2's autumn blocks)")
_names = {getattr(m, "payload", {}).get("text") if isinstance(getattr(m, "payload", None), dict) else None for m in f_.movers}
check({"Ranger Naoko", "Ranger Bret", "Ranger Malory"} <= _names and "Ranger Leaf" not in _names,
      f"autumn's Pokemon Rangers are out (Leaf only after Virbank's Team Plasma) ({sorted(n for n in _names if n and 'Ranger' in n)})")
shot("09_autumn")
put(1, 0, (-1, 0))
step(-1, 0)
play(lambda: isinstance(g.current_state, _WTS) and story.current_area_key == "FLOCCESY_TOWN" and idle(), 600)
check(story.current_area_key == "FLOCCESY_TOWN" and pos() in ((31, 0), (31, 1), (30, 0), (30, 1), (31, 2)),   # (11-23: the walker
      # sets you one step in from the way out you came by: (31, 2), at the top of the dead end, (31, 0/1) being Route 20's edge)
      f"the leaves' top corner leads west onto Floccesy's dead end ({story.current_area_key}, {pos()})")
_ht = g.current_state
check("31,15" in (_ht.town_map or {}).get("hidden", {}), "where Floccesy's hidden Potion waits")
_seasons.current_season = lambda date=None: "AUTUMN"
put(30, 22, (1, 0)) if False else None
story.current_area_key, story.last_area_key = "FLOCCESY_TOWN", "UNOVA_ROUTE_19"
g.walk_town_pos, g.walk_town_room = (30, 22), None
g.change_state(CityState(g)); play(idle, 300)
put(30, 22, (1, 0)); step(1, 0)
play(lambda: isinstance(g.current_state, _DS) and idle(), 600)
check(story.current_area_key == "UNOVA_ROUTE_20" and pos()[1] in (21, 22, 23), f"the main road still comes out on the main road ({pos()})")
_seasons.current_season = lambda date=None: "SPRING"
g.change_state(PlayState(g))
play(lambda: isinstance(g.current_state, _DS) and idle(), 300)
d = g.current_state
check(not d.run.floor.walkable(15, 11), "in spring the way is shut again")
_seasons.current_season = _real_season

print("9) fishing, Alder's Berries, Mr. Medal, the second rival")
from src.states.overworld.route_actions import RouteActions as _RA
story.current_area_key = "UNOVA_ROUTE_19"


class _F:
    game = g
bites = [_RA._fish_bite(_F()) for _ in range(20)]
check(all(b is not None and b.id in (60, 550) and 40 <= b.level <= 70 for b in bites),
      f"fishing on Route 19: Black 2's own bites and levels ({sorted({(b.id, b.level) for b in bites if b})[:4]})")
flags["b2_gym_open"] = True
flags.pop("b2_alder_oran", None)
_or = story.inventory.get("ORAN_BERRY", 0)
story.current_area_key, story.last_area_key = "UNOVA_ROUTE_19", "FLOCCESY_TOWN"
g.change_state(PlayState(g))
play(lambda: isinstance(g.current_state, _DS) and idle(), 300)
put(59, 22, (-1, 0)); said.clear()
step(-1, 0)
play(lambda: flags.get("b2_alder_oran") and idle(), 3000)
check(flags.get("b2_alder_oran") and story.inventory.get("ORAN_BERRY", 0) == _or + 5, "on the way back to Aspertia, Alder runs after you: 5 Oran Berries")
story.inventory["MEDAL_BOX"] = 1
for k in [k for k in flags if k.startswith("medal_")]:
    flags.pop(k)
_lines = _medals.hand_out(story)
check(any("Basic Badge Holder" in x for x in _lines) and flags.get("medal_badge_1"), f"Mr. Medal hands over the Medals you've earned ({_lines[1:3]})")
check(_medals.hand_out(story)[0].startswith("Mr. Medal: No new"), "and nothing twice")
story.region_rivals.setdefault("UNOVA", {})["friend_character"] = "cheren"
flags.pop("b2_gym_open", None)
story.current_area_key = "ASPERTIA_CITY"
g.walk_town_pos, g.walk_town_room = (8, 38), None
g.change_state(CityState(g))
play(idle, 300)
t = g.current_state
check(any((o.get("text") if isinstance(o, dict) else None) == "Cheren" for o in t._people().values()),
      "Cheren picked as your second rival: he meets you outside the school")
story.region_rivals["UNOVA"]["friend_character"] = "bianca"
g.change_state(CityState(g)); play(idle, 300); t = g.current_state
check(not any((o.get("text") if isinstance(o, dict) else None) == "Cheren" for o in t._people().values()),
      "Bianca picked: no Cheren there (Black 2's way); her promise comes on Route 19")
flags["b2_gym_open"] = True
from src.pokemon import items as _items
check("STICKY_BARB" in str(_items.__dict__), "the Sticky Barb exists (Route 20's autumn item)")

print(f"##### {len(fails)} failures")
