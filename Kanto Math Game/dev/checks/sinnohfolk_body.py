# Sinnoh's townspeople from the re-audit (kanto_handoff/sinnoh_map_tools/sfolk.py -> s_folk.py, 11-19), met the way a
# player meets them: walk into the town or route, find the person standing on the map with Platinum's sprite, talk.
# Gift-givers hand over their item once (and wait for a Badge / Defog when Platinum does); night patrols only at night.
#   bash dev/checks/run_par.sh sinnohfolk
import json as _json
import datetime as _dt
from src.states.overworld import PlayState, CityState as _CS
from src.states.overworld.dungeon import DungeonState
from src.states.overworld.walk_town import WalkTownState as _WTS

fails = 0
g.dungeon_routes = True
g.walk_towns = True
OUT = S


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


def frames(n=1):
    for _ in range(n):
        g.current_state.update()
        g.current_state.draw()


def talk(p, n=80):
    if isinstance(p, _WTS):   # (a town: tap through what's said)
        said = []
        for _ in range(400):
            if not getattr(p, "npc_active", False):
                break
            box = getattr(p, "npc_dialogue", None)
            for line in (getattr(box, "pages", None) or getattr(box, "text_lines", None) or getattr(box, "lines", None) or []):
                if not said or said[-1] != line:
                    said.append(line)
            p.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
            frames()
        return said
    said = []
    for _ in range(n):
        if not p.dialogue_box.visible:
            return said
        for line in p.dialogue_box.text_lines:
            if not said or said[-1] != line:
                said.append(line)
        p.dialogue_box.advance()
    return said


def enter(area, came):
    g.walk_town_pos = None
    story.current_area_key, story.last_area_key = area, came
    if _AD.get(area, {}).get("area_type") == "town" or "TOWN" in area or "CITY" in area or area.endswith("_AREA"):
        st = _CS(g)
        g.change_state(st)
        if isinstance(g.current_state, _WTS):
            talk(g.current_state)
            return g.current_state
    p = PlayState(g)
    g.states["play"] = p
    g.change_state(p)
    frames(3)
    return p


class _Spot:
    def __init__(self, xy, opt):
        self.x, self.y, self.payload = xy[0], xy[1], opt


def figures(p):
    out = {}
    if isinstance(p, _WTS):
        for xy, o in p._people().items():
            for q in o.get("any", [o]) if isinstance(o, dict) else []:
                out[q.get("text")] = (0, _Spot(xy, q))
        return out
    for i, f in enumerate(getattr(p.run, "floors", None) or [p.run.floor]):
        for m in f.movers:
            if m.kind == "figure" and isinstance(m.payload, dict) and m.payload.get("text"):
                out[m.payload["text"]] = (i, m)
    return out


story.story_flags["received_starter_sinnoh"] = True
story.story_flags["starter_sinnoh"] = 390
story.enter_region("SINNOH")
story.player_team = [mk(392)]
_tm = _json.load(open("assets/town_maps.json", encoding="utf-8"))
_sp = _json.load(open("assets/dungeon_sprites.json", encoding="utf-8"))["figures"]
_AD = g.loader.area_data["STORY_PROGRESSION"]


def came_from(area):
    ex = (_tm[area].get("floors") or [_tm[area]])[0].get("exits") or {}
    for v in ex.values():
        t = str(v).split(":")[0]
        if t in _AD and t != area:
            return t
    return None


def use(p, m):
    if isinstance(p, _WTS):
        p._talk((m.x, m.y))
    else:
        p._use_figure(m)


print("1) every townsperson stands on the map, drawn as Platinum draws them")
folk = {}
_SIN = set(_json.load(open("assets/sinnoh_area_data.json", encoding="utf-8"))["STORY_PROGRESSION"])
for area, e in _tm.items():
    if area not in _SIN:
        continue
    for fi, f in enumerate(e.get("floors") or [e]):
        for q in f.get("people") or []:
            if isinstance(q, dict) and q.get("action") == "EVENT" and not q.get("found") and f"{area}:{q.get('text')}" in _sp:
                folk.setdefault(area, []).append(q)
check(sum(len(v) for v in folk.values()) >= 205, f"{sum(len(v) for v in folk.values())} Sinnoh people with lines and a look, in {len(folk)} areas")
missing = []
for area in ("HEARTHOME_CITY", "OREBURGH_CITY", "JUBILIFE_CITY", "SINNOH_ROUTE_212", "VEILSTONE_CITY", "SNOWPOINT_CITY"):
    p = enter(area, came_from(area))
    if not isinstance(p, (DungeonState, _WTS)):
        check(False, f"{area}: walked (got {type(p).__name__})")
        continue
    fs = figures(p)
    want = [q["text"] for q in folk.get(area, []) if not q.get("condition")]
    gone = [w for w in want if w not in fs]
    missing += [(area, w) for w in gone]
    check(not gone, f"{area}: {len(want) - len(gone)}/{len(want)} people standing{(' - missing ' + str(gone[:4])) if gone else ''}")
    who = next((w for w in want if w in fs), None)
    if who:
        fi, m = fs[who]
        ok = (lambda x, y: 0 <= y < p.h and 0 <= x < p.w and p.rows[y][x] == ".") if isinstance(p, _WTS) else p.run.floor.walkable
        tgt = next(((m.x + dx, m.y + dy) for dx, dy in ((0, 1), (1, 0), (-1, 0), (0, -1)) if ok(m.x + dx, m.y + dy)), None)
        if tgt and isinstance(p, _WTS):
            p.player = tgt
        elif tgt:
            p.run.player = tgt
        frames(4)
        pygame.image.save(pygame.display.get_surface(), os.path.join(OUT, f"folk_{area}.png"))
        use(p, m)
        said = talk(p)
        line = (next(q for q in folk[area] if q["text"] == who)["event"]["lines"][0])
        check(any(line[:25] in s or s[:25] in line for s in said) or bool(said), f"{area}: talking to {who.strip()} -> {said[:1]}")

print("2) gifts: once, and only when Platinum allows")


def gift_test(area, who, item, need=None):
    p = enter(area, came_from(area))
    fs = figures(p)
    if who not in fs:
        check(False, f"{area}: {who} not on the map")
        return
    fi, m = fs[who]
    story.inventory.pop(item, None)
    if need:
        use(p, m)
        talk(p)
        check(not story.inventory.get(item), f"{area}: {who.strip()} keeps the {item} until you have {need}")
        story.inventory[need.upper()] = 1 if need.upper().startswith("HM") else story.inventory.get(need.upper(), 0)
        if need.startswith("has_"):
            pass
    use(p, m)
    talk(p)
    got = story.inventory.get(item, 0)
    use(p, m)
    talk(p)
    check(got == 1 and story.inventory.get(item, 0) == 1, f"{area}: {who.strip()} gives one {item} (then {story.inventory.get(item, 0)} after asking again)")


gift_test("SINNOH_ROUTE_201", "Mart worker", "POTION")
gift_test("SINNOH_ROUTE_209", "Fisherman", "GOOD_ROD")
gift_test("FIGHT_AREA", "Fisherman", "SUPER_ROD")
_tm210 = next(q for f in (_tm["SINNOH_ROUTE_210"].get("floors") or [_tm["SINNOH_ROUTE_210"]]) for q in f.get("people") or []
              if isinstance(q, dict) and q.get("text") == "Girl")
gift_test("SINNOH_ROUTE_210", "Girl", list(_tm210["event"]["gift_item"])[0])   # (Platinum's TM51 Roost, as our TM)
_lt = [q for f in _tm["LOST_TOWER"]["floors"][4:5] for q in f.get("people") or [] if isinstance(q, dict)]
check(sorted(list(q["event"]["gift_item"])[0] for q in _lt) == ["CLEANSE_TAG", "SPELL_TAG"] and all(q["event"].get("requires") == ["has_hm_defog"] for q in _lt),
      "Lost Tower 5F: the two old women give the Spell Tag and Cleanse Tag once you have Defog")
story.badges["SINNOH"] = []
p = enter("OREBURGH_GATE", "OREBURGH_CITY")
fs = figures(p)
if "Hiker" in fs:
    story.inventory.pop("HM_ROCK_SMASH", None)
    p._use_figure(fs["Hiker"][1]); talk(p)
    check(not story.inventory.get("HM_ROCK_SMASH"), "Oreburgh Gate: the Hiker waits for the Coal Badge")
    story.badges["SINNOH"] = ["COAL"]
    p._use_figure(fs["Hiker"][1]); talk(p)
    check(story.inventory.get("HM_ROCK_SMASH") == 1, "Oreburgh Gate: with the Coal Badge, HM Rock Smash")
else:
    check(False, "Oreburgh Gate: the Hiker stands by the way in")

print("3) the night patrol on Route 212")
night = _dt.datetime.now().hour < 6 or _dt.datetime.now().hour >= 20
p = enter("SINNOH_ROUTE_212", "HEARTHOME_CITY")
fs = figures(p)
cops = [t for t in fs if t.startswith("Policeman")]
check((len(cops) > 0) == night, f"policemen out: {len(cops)} ({'night' if night else 'day'})")

print("4) inside: the rooms' visitors (a Center, the Mining Museum, Fight Area's Mart gift)")


def into(area, room):
    t = enter(area, came_from(area))
    door = next(tuple(int(v) for v in d.split(",")) for d, n in _tm[area]["inside"].items() if n == room)
    t.player = t.anim_from = (door[0], door[1] + 1); t.anim = 0; t.walk_goal = None
    t.step(0, -1); t.anim = 0
    frames(2)
    return t


for area, room, who in (("OREBURGH_CITY", "museum", "Museum guide"), ("JUBILIFE_CITY", "center", "Center visitor"),
                        ("SUNYSHORE_CITY", "gym", "Gym guide")):
    t = into(area, room)
    fs = figures(t)
    want = [q["text"] for q in _tm[area]["rooms"][room].get("people") or [] if isinstance(q, dict) and f"{area}:{q.get('text')}" in _sp]
    check(t.room == room and want and all(w in fs for w in want), f"{area} {room}: in, {len(want)} visitors standing")
    if who in fs:
        pygame.image.save(pygame.display.get_surface(), os.path.join(OUT, f"room_{area}_{room}.png"))
        use(t, fs[who][1])
        said = talk(t)
        check(bool(said), f"{area} {room}: {who} -> {said[:1]}")
t = into("FIGHT_AREA", "mart")
fs = figures(t)
story.inventory.pop("SCOPE_LENS", None)
if "Shopping lady" in fs:
    use(t, fs["Shopping lady"][1]); talk(t)
    use(t, fs["Shopping lady"][1]); talk(t)
check(story.inventory.get("SCOPE_LENS") == 1, "Fight Area Mart: the lady gives one Scope Lens")

print("5) the houses (s_houses.py): in through their doors, their people, gifts")
_h = {k: [n for n in (e.get("rooms") or {}) if n.startswith("house_")] for k, e in _tm.items() if k in _SIN}
check(sum(len(v) for v in _h.values()) >= 70, f"{sum(len(v) for v in _h.values())} house rooms in {sum(1 for v in _h.values() if v)} towns")
t = into("FLOAROMA_TOWN", "house_0301")
fs = figures(t)
_pl = list(next(q for q in _tm["FLOAROMA_TOWN"]["rooms"]["house_0301"]["people"] if isinstance(q, dict) and q.get("text") == "Little girl")["event"]["gift_item"])[0]
story.inventory.pop(_pl, None)
check(t.room == "house_0301" and "Little girl" in fs and "Clefairy" in fs, f"Floaroma's house: in, the girl and her Clefairy ({sorted(fs)[:5]})")
pygame.image.save(pygame.display.get_surface(), os.path.join(OUT, "house_FLOAROMA_TOWN.png"))
if "Little girl" in fs:
    use(t, fs["Little girl"][1]); talk(t)
check(story.inventory.get(_pl) == 1, f"Floaroma: the girl gives Platinum's TM88 Pluck as our {_pl}")
t = into("OREBURGH_CITY", "house_0201")
t._go("house_0201_2f", "ROOM:house_0201")
frames(2)
fs = figures(t)
story.inventory.pop("HEAL_BALL", None)
story.player_team = [mk(392)]
if "Geodude fan" in fs:
    use(t, fs["Geodude fan"][1]); talk(t)
    no = story.inventory.get("HEAL_BALL", 0)
    story.player_team = [mk(392), mk(74)]
    use(t, fs["Geodude fan"][1]); talk(t)
    check(no == 0 and story.inventory.get("HEAL_BALL") == 1, "Oreburgh 2F: the Heal Ball only once you show him a Geodude")
else:
    check(False, f"Oreburgh house 2F: the Geodude fan upstairs ({t.room}, {sorted(fs)[:4]})")
story.player_team = [mk(392)]

print("6) route houses and the lakeside hotel: rooms on route maps (dungeon.with_rooms), their people")
for area, room in (("SINNOH_ROUTE_213", "house_0501"), ("VALOR_LAKEFRONT", "house_0101"), ("SINNOH_ROUTE_216", "house_0101")):
    p = enter(area, came_from(area))
    rf = (p.recipe.get("art") or {}).get("room_floors") or {}
    if room in rf:          # (in through its door: the room is a floor of the route; its people stand once you're in)
        _art = _tm[area]["rooms"][room]["art"]
        _mat = next((x, y) for y, r in enumerate(_art) for x, c in enumerate(r) if c == "v")
        p._warp(rf[room], _mat[0], _mat[1] - 1)
        frames(3)
    fs = figures(p)
    want = [q["text"] for q in _tm[area]["rooms"][room].get("people") or [] if isinstance(q, dict) and not q.get("condition")]   # (not the restaurant's pairs: only today's are there)
    on = {w: fs[w][0] for w in want if w in fs}
    check(isinstance(p, DungeonState) and want and len(on) == len(want) and len(set(on.values())) == 1 and min(on.values()) >= 1,
          f"{area} {room}: {len(on)}/{len(want)} people, on the room's own floor {sorted(set(on.values()))}")
def into_route_room(area, room):
    p = enter(area, came_from(area))
    rf = (p.recipe.get("art") or {}).get("room_floors") or {}
    _art = _tm[area]["rooms"][room]["art"]
    _mat = next((x, y) for y, r in enumerate(_art) for x, c in enumerate(r) if c == "v")
    p._warp(rf[room], _mat[0], _mat[1] - 1)
    frames(3)
    return p


p = into_route_room("SINNOH_ROUTE_213", "house_0501")
pygame.image.save(pygame.display.get_surface(), os.path.join(OUT, "routehouse_R213.png"))
fs = figures(p)
_k = list(next(q for q in _tm["SINNOH_ROUTE_213"]["rooms"]["house_0501"]["people"] if isinstance(q, dict) and q.get("text") == "Clown")["event"]["gift_item"])[0]
story.inventory.pop(_k, None)
if "Clown" in fs:
    use(p, fs["Clown"][1]); talk(p)
check(story.inventory.get(_k) == 1, f"Route 213's performers: the clown gives Platinum's TM92 Trick Room as our {_k}")
p = into_route_room("SINNOH_ROUTE_216", "house_0101")
fs = figures(p)
story.player_team = [mk(392)]
story.player_team[0].current_hp = 1
if "Lodge owner" in fs:
    use(p, fs["Lodge owner"][1]); talk(p)
check(story.player_team[0].current_hp == story.player_team[0].get_max_hp(), "Route 216's lodge: its owner heals your team")

print("7) walked: in through every route house's door and out again")
_bad, _n = [], 0
for area in [k for k in _SIN if (_tm.get(k) or {}).get("rooms") and _AD.get(k, {}).get("area_type") != "town" and not any(w in k for w in ("TOWN", "CITY")) and not k.endswith("_AREA")]:
    for d, room in (_tm[area].get("inside") or {}).items():
        p = enter(area, came_from(area))
        if not isinstance(p, DungeonState):
            continue
        x, y = (int(v) for v in d.split(","))
        if p.run.index != 0:   # (in at a room: the Battle Frontier's gate, from the Fight Area - out on the map first)
            p._warp(0, 1, 1); frames(3)
        _f0 = p.run.floor   # (the open side of the door: below, else beside it - the Battle Frontier's side doors, 11-22)
        dx, dy = next(((a, b) for a, b in ((0, 1), (-1, 0), (1, 0), (0, -1)) if _f0.walkable(x + a, y + b)
                       and f"{x + a},{y + b}" not in (_tm[area].get("inside") or {})), (0, 1))   # (not the door's other half)
        p.run.player = (x + dx, y + dy); p.anim = 0; p.sliding = None; p.hop = None
        p.step(-dx, -dy); frames(3)
        inside = p.run.index == (p.recipe.get("art") or {}).get("room_floors", {}).get(room)
        mat = next(((mx, my) for my, r in enumerate(_tm[area]["rooms"][room]["art"]) for mx, c in enumerate(r) if c == "v"), None)
        out = False
        if inside and mat:
            p.run.player = (mat[0], mat[1] - 1); p.anim = 0
            p.step(0, 1); frames(3)
            out = p.run.index == 0 and abs(p.run.player[0] - (x + dx)) <= 1 and abs(p.run.player[1] - (y + dy)) <= 1
        _n += 1
        if not (inside and out):
            _bad.append((area, d, room, inside, out, p.run.index, p.run.player))
check(_n >= 20 and not _bad, f"{_n} route doors: in to the room and back out below the door {_bad[:3]}")

print("8) Gym trainers in the Gym rooms (sgym.py): Platinum's own, talk and you battle, once")
from src.states.battle import TrainerIntroState, TrainerBattleState
_gn = {k: [q for q in (e.get("rooms") or {}).get("gym", {}).get("people") or [] if isinstance(q, dict) and (q.get("event") or {}).get("battle")]
       for k, e in _tm.items() if k in _SIN}
check(sum(len(v) for v in _gn.values()) >= 29, f"{sum(len(v) for v in _gn.values())} Gym trainers standing in {sum(1 for v in _gn.values() if v)} Gyms")
t = into("OREBURGH_CITY", "gym")
fs = figures(t)
_j = next((q for q in _gn["OREBURGH_CITY"] if q["text"] == "Youngster Jonathon"), None)
story.story_flags.pop(_j["event"]["flag"], None) if _j else None
if _j and "Youngster Jonathon" in fs:
    use(t, fs["Youngster Jonathon"][1])
    for _ in range(300):
        if isinstance(g.current_state, (TrainerIntroState, TrainerBattleState)):
            break
        if getattr(g.current_state, "npc_active", False):
            g.current_state.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        frames()
check(isinstance(g.current_state, (TrainerIntroState, TrainerBattleState)) and _j and _j["event"]["battle"]["team"] == [74] and _j["event"]["battle"]["levels"] == [11],
      f"Oreburgh Gym: talk to Youngster Jonathon and you battle his Geodude Lv 11 ({type(g.current_state).__name__})")
_lob = {k: [t.get("name") for t in (_AD[k].get("gym") or {}).get("trainers") or []] for k in ("OREBURGH_CITY", "ETERNA_CITY", "SUNYSHORE_CITY")}
check(_lob["OREBURGH_CITY"] == ["Youngster Jonathon", "Youngster Darius"] and len(_lob["ETERNA_CITY"]) == 3 and len(_lob["SUNYSHORE_CITY"]) == 8,
      f"the Gyms' own trainer lists are Platinum's too (menu play): {_lob}")

print("9) the Seven Stars Restaurant: five of nine pairs today, each a two-trainer double battle once a day")
from src.states.battle_double import DoubleBattleState
p = into_route_room("VALOR_LAKEFRONT", "house_0101")
fs = figures(p)
_rp = [q for q in _tm["VALOR_LAKEFRONT"]["rooms"]["house_0101"]["people"] if isinstance(q, dict) and (q.get("event") or {}).get("battle")]
_here = [q["text"] for q in _rp if q["text"] in fs]
check(len(_rp) == 18 and len(_here) == 10, f"18 diners (9 pairs), 10 seated today: {_here}")
pygame.image.save(pygame.display.get_surface(), os.path.join(OUT, "restaurant.png"))
_first = next((q for q in _rp if q["text"] in fs), None)
_seen = []
if _first:
    _flag = _first["event"]["flag"]
    for k in [k for k in story.story_flags if k.startswith(_flag)]:
        story.story_flags.pop(k)
    use(p, fs[_first["text"]][1])
    for _ in range(600):
        _seen.append(type(g.current_state).__name__)
        if isinstance(g.current_state, DoubleBattleState):
            break
        if _seen[-1] == "TrainerIntroState" and _seen.count("TrainerIntroState") == 25:   # (the intro: both trainers' portraits)
            pygame.image.save(pygame.display.get_surface(), os.path.join(OUT, "restaurant_intro.png"))
        st_ = g.current_state
        box = getattr(st_, "dialogue_box", None)
        if box is not None and getattr(box, "visible", False):
            box.advance()
        elif hasattr(st_, "handle_events"):
            st_.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        frames()
b = g.current_state
if isinstance(b, DoubleBattleState):
    for _ in range(40):
        frames()
    pygame.image.save(pygame.display.get_surface(), os.path.join(OUT, "restaurant_battle.png"))
check(isinstance(b, DoubleBattleState) and getattr(b, "foe2_name", None) and len(getattr(b, "foe_teams", []) or []) == 2,
      f"talk to {(_first or {}).get('text')}: a double battle against two trainers ({type(b).__name__}, {getattr(b, 'foe2_name', None)}; {sorted(set(_seen))})")
check(all(q["event"].get("daily") and q["event"]["battle"]["battle_options"]["second_trainer"]["team"] for q in _rp),
      "every pair: once a day, and both trainers' Platinum teams")

_dbl = {"Young Couple Mike & Nat", "Belle & Pa Beth & Bob", "Double Team Al & Kay", "Double Team Jo & Pat", "Twins Liv & Liz",
        "Twins Emma & Lil", "Young Couple Ty & Sue", "Twins Teri & Tia", "Belle & Pa Ava & Matt", "Double Team Zac & Jen"}
_have = {t.get("name"): t for a in _AD.values() if isinstance(a, dict) for t in a.get("trainer_pool") or [] if isinstance(t, dict) and t.get("name") in _dbl}
from src.states.battle_double import battle_options as _bo
check(set(_have) == _dbl and all(_bo(t).get("double") for t in _have.values()),
      f"Platinum's 10 route double battles (Twins, Young Couples, Double Teams, Belle & Pa) are doubles: {len(_have)}")

print("10) move tutors sell their moves' TMs; the shops don't (Jordan 11-19), every region")
from src.pokemon import tutors as _tut, tms as _tms
from src.states.systems.mart import PokeMartState
from src.states.systems.pick_list import PickListState
story.badges["SINNOH"] = ["COAL", "FOREST", "COBBLE", "FEN", "RELIC", "MINE", "ICICLE", "BEACON"]
p = into_route_room("SINNOH_ROUTE_212", "house_0101")
fs = figures(p)
_ip = _tms.key_for_move(g, "ICE-PUNCH")
for k in [k for k in story.inventory if _tms.is_tm(k)]:
    story.inventory.pop(k)
use(p, fs["Shard tutor"][1])
for _ in range(80):
    if isinstance(g.current_state, PickListState):
        break
    box = getattr(g.current_state, "dialogue_box", None)
    if box is not None and box.visible:
        box.advance()
    frames()
_menu = g.current_state
check(isinstance(_menu, PickListState) and [v for _l, v in _menu.choices] == ["teach", "buy"],
      f"Route 212's Shard tutor: LEARN IT NOW or BUY THE TMs ({type(_menu).__name__})")
if isinstance(_menu, PickListState):
    _menu.pick("buy")
_shop = g.current_state
_items = _shop._shop_items() if isinstance(_shop, PokeMartState) else []
check(isinstance(_shop, PokeMartState) and _ip in _items and len(_items) >= 10 and all(_tms.is_tm(i) for i in _items),
      f"...BUY: a shop of just the tutor's TMs ({len(_items)}, Ice Punch {_ip} among them)")
g.change_state(p)
story.current_area_key = "JUBILIFE_CITY"
_m = PokeMartState(g, p)
_jub = _m._shop_items()
_only = _tut.tutor_tms(g, "SINNOH")
check(_ip not in _jub and not (_only & set(_jub)) and any(_tms.is_tm(i) for i in _jub),
      f"Jubilife's Mart: other TMs yes, none of the {len(_only)} Sinnoh tutor TMs")
story.current_area_key = "CELADON_CITY"
_kb = _tms.key_for_move(g, "BODY-SLAM")
_cel = PokeMartState(g, p)._shop_items()
story.badges["KANTO"] = ["B%d" % i for i in range(8)]
_cel = PokeMartState(g, p)._shop_items()
check(_kb not in _cel and _ip in _cel, f"Celadon (Kanto): no Body Slam TM (Kanto's tutors teach it), Ice Punch's still sold (no Kanto tutor for it)")
story.current_area_key = "SINNOH_ROUTE_212"
p = into_route_room("SINNOH_ROUTE_212", "house_0101")
fs = figures(p)
ev = next(q for q in _tm["SINNOH_ROUTE_212"]["rooms"]["house_0101"]["people"] if isinstance(q, dict) and q.get("text") == "Shard tutor")["event"]
check(ev["tutor"]["costs"]["ICE-PUNCH"] == {"RED_SHARD": 2, "BLUE_SHARD": 6} and len(ev["tutor"]["choices"]) == 13,
      "Platinum's prices: Ice Punch for 2 Red and 6 Blue Shards; 13 moves here")
from src.states.overworld import common as _cm
_inf = mk(392)
story.player_team = [_inf]
story.inventory.update({"RED_SHARD": 2, "BLUE_SHARD": 6})
_out = _cm._tutor_teach(g, dict(ev["tutor"], move="FIRE-PUNCH", like="FIRE-PUNCH", take=ev["tutor"]["costs"]["FIRE-PUNCH"]), ev, who=_inf)
for i, q in ev["tutor"]["costs"]["FIRE-PUNCH"].items():
    story.inventory[i] = story.inventory.get(i, 0) - q   # (the flow takes them once taught: as _tutor_flow does)
check(_out and _out[0] != "\x00fail" and "learned" in _out[0], f"Infernape learns Fire Punch for 2 Red and 6 Blue Shards ({_out[:1]})")
story.inventory.update({"RED_SHARD": 0, "BLUE_SHARD": 0})
_out = _cm._tutor_teach(g, dict(ev["tutor"], move="THUNDER-PUNCH", like="THUNDER-PUNCH", take=ev["tutor"]["costs"]["THUNDER-PUNCH"]), ev, who=_inf)
check(_out and _out[0] == "\x00fail", f"...without the Shards, no lesson ({_out[1:2]})")

t = into("ETERNA_CITY", "house_0501")
fs = figures(t)
if "Herb Shop" in fs:
    use(t, fs["Herb Shop"][1])
    for _ in range(20):
        if isinstance(g.current_state, PokeMartState):
            break
        talk(t)
_hs = g.current_state
check(isinstance(_hs, PokeMartState) and _hs._shop_items() == ["HEAL_POWDER", "ENERGY_POWDER", "ENERGY_ROOT", "REVIVAL_HERB"],
      f"Eterna's Herb Shop: Platinum's four herbs ({type(_hs).__name__})")

print("11) Platinum's four in-game trades: their Pokemon, nickname and held item")
from src.states.overworld.common import _run_story_event as _rse11


def _ev11(area, room, who):
    return next(q for q in _tm[area]["rooms"][room]["people"] if isinstance(q, dict) and q.get("text") == who)["event"]


for area, room, who, want, give, nick, item in (("OREBURGH_CITY", "house_0201", "Trade girl", 66, 63, "Kazza", "ORAN_BERRY"),
                                                ("ETERNA_CITY", "rater", "Trade girl", 418, 441, "Charap", "LEPPA_BERRY"),
                                                ("SNOWPOINT_CITY", "house_0101", "Trade lady", 308, 93, "Gaspar", "EVERSTONE"),
                                                ("SINNOH_ROUTE_226", "house_0101", "Meister", 456, 129, "Foppa", "LUM_BERRY")):
    ev = _ev11(area, room, who)
    story.story_flags.pop(ev["flag"], None)
    story.player_team = [mk(392)]
    said = []
    _rse11(p, ev, lambda c: True, lambda l, **k: said.extend(l))
    kept = story.player_team[0].id == 392
    story.player_team = [mk(392), mk(want)]
    _rse11(p, ev, lambda c: True, lambda l, **k: said.extend(l))
    got = story.player_team[1]
    check(kept and got.id == give and got.nickname == nick and got.held_item == item and got.traded and story.story_flags.get(ev["flag"]),
          f"{area}: your {want} for {nick} ({give}) holding {item}; nothing to trade, nothing happens ({got.id}, {got.nickname}, {got.held_item})")
_rr = _tm["ETERNA_CITY"]["rooms"]
check({"rater", "rater_2f", "rater_3f", "rater_4f"} <= set(_rr) and "Name Rater" in (_rr["rater"].get("people") or []),
      "Eterna Condominiums: the Name Rater's building, its four floors, from Platinum's own rooms")
story.player_team = [mk(392)]

print("12) Team Galactic's grunts as Platinum stands them, each for its stretch of the story (s_grunts.py)")


def _grunts12(area):
    return [(i, t) for i, t in enumerate(_AD[area].get("trainer_pool") or []) if str(t.get("spot_name", "")).startswith("Galactic Grunt")]


_sv12 = dict(story.story_flags)
for f in ("galactic_lake_valor_cleared", "galactic_lake_verity_cleared", "galactic_hq_cleared", "spear_pillar_resolved"):
    story.story_flags.pop(f, None)
_lv = _grunts12("LAKE_VERITY")
_on = lambda area, lst: sum(story.trainer_on_map(area, i, t) for i, t in lst)
a0 = _on("LAKE_VERITY", _lv)
story.story_flags["galactic_lake_valor_cleared"] = True
a1 = _on("LAKE_VERITY", _lv)
story.story_flags["galactic_lake_verity_cleared"] = True
a2 = _on("LAKE_VERITY", _lv)
check(len(_lv) == 4 and (a0, a1, a2) == (0, 4, 0), f"Lake Verity: Platinum's 4 grunts only between Lake Valor's blast and Mars's defeat ({a0}, {a1}, {a2})")
_mc = _grunts12("MT_CORONET_BASE") + _grunts12("SPEAR_PILLAR")
b0 = _on("MT_CORONET_BASE", _grunts12("MT_CORONET_BASE"))
story.story_flags["galactic_hq_cleared"] = True
b1 = _on("MT_CORONET_BASE", _grunts12("MT_CORONET_BASE")) + _on("SPEAR_PILLAR", _grunts12("SPEAR_PILLAR"))
story.story_flags["spear_pillar_resolved"] = True
b2 = _on("MT_CORONET_BASE", _grunts12("MT_CORONET_BASE"))
check(len(_mc) == 10 and (b0, b1, b2) == (0, 10, 0), f"Mt. Coronet and Spear Pillar: 10 grunts from the HQ till Spear Pillar is over ({b0}, {b1}, {b2})")
_hq = _grunts12("TEAM_GALACTIC_HQ")
check(len(_hq) == 8 and all(t.get("levels") for _i, t in _hq) and any(t["sprite"] == "pt_galactic_grunt_f.png" for _i, t in _hq + _lv),
      f"Galactic HQ: Platinum's 8 grunts, levels exact; the women grunts in Platinum's own portrait ({[t['levels'] for _i, t in _hq][:3]})")
story.story_flags.clear(); story.story_flags.update(_sv12)

print("13) swarms (src/world/swarms.py): Platinum's 22, one a day once you have the National Pokedex; Sandgem's news")
from src.world import swarms as _sw
from src.states.overworld.route_encounters import RouteEncounters as _RS13
_sv13 = dict(story.story_flags)
story.story_flags.pop("unlocked_national_dex", None)
check(_sw.today(story, "SINNOH") is None and _sw.news(g) is None, "no swarms before the National Pokedex")
story.story_flags["unlocked_national_dex"] = True
_t1, _t2 = _sw.today(story, "SINNOH"), _sw.today(story, "SINNOH")
_days = {_sw.today(story, "SINNOH", day="2026-12-%02d" % d)[0] for d in range(1, 29)}
check(_t1 == _t2 and _t1[0] in _sw.SWARMS["SINNOH"] and len(_days) >= 8, f"one swarm a day, the same all day ({_t1}); {len(_days)} different places over 28 days")
_area, _sp = _t1
story.current_area_key = _area
_rs = _RS13.__new__(_RS13); _rs.game = g; _rs.area_data = _AD[_area]
_rs._zone = lambda: None
_pool = _rs._get_wild_pool(_AD[_area])
_share = _pool.get(str(_sp), 0) / max(1, sum(_pool.values()))
_other = next(k for k in _sw.SWARMS["SINNOH"] if k != _area)
story.current_area_key = _other
_rs.area_data = _AD[_other]
_pool2 = _rs._get_wild_pool(_AD[_other])
check(0.35 <= _share <= 0.45 and str(_sw.SWARMS["SINNOH"][_other]) not in _pool2,
      f"{_area}: {_sp} is {_share:.0%} of the grass today; {_other} has no swarm Pokemon today")
_kid = next(q for q in _tm["SANDGEM_TOWN"]["rooms"]["assistant"]["people"] if isinstance(q, dict) and q.get("text") == "Little sibling")
_said13 = []
from src.states.overworld.common import _run_story_event as _rse13
_rse13(p, _kid["event"], lambda c: True, lambda l, **k: _said13.extend(l))
_nm13 = str(g.loader.fetch_specific(int(_sp))["name"]).replace("-", " ").title()
check(any(_nm13 in l and _sw.place_name(_area) in l for l in _said13), f"Sandgem: the little sibling saw it on the news ({_said13[:1]})")
story.story_flags.clear(); story.story_flags.update(_sv13)

print("14) the Poke Radar (src/world/poke_radar.py): Rowan's gift after the National Pokedex; shaking grass, chains")
from src.world import poke_radar as _pr
from src.dungeon import core as _core14
_sv14 = dict(story.story_flags)
_aide = next(q for q in _tm["SANDGEM_TOWN"]["rooms"]["lab"]["people"] if isinstance(q, dict) and q.get("text") == "Lab aide ")
story.inventory.pop("POKE_RADAR", None)
story.story_flags.pop(_aide["event"]["flag"], None)
story.story_flags.pop("unlocked_national_dex", None)
_rse11(p, _aide["event"], lambda c: True, lambda l, **k: None)
_no = story.inventory.get("POKE_RADAR", 0)
story.story_flags["unlocked_national_dex"] = True
_rse11(p, _aide["event"], lambda c: True, lambda l, **k: None)
check(_aide["event"].get("requires") == ["unlocked_national_dex"] and story.inventory.get("POKE_RADAR") == 1,
      "Sandgem's lab: the POKE RADAR once you have the National Pokedex (the test's save already counts as having it)")
_rep14 = getattr(story, "repel_routes", 0)
story.repel_routes = 9
story.player_team = [mk(392)]
r = enter("SINNOH_ROUTE_229", came_from("SINNOH_ROUTE_229"))
f = r.run.floor
for m in [m for m in f.movers if m.kind == "wild"]:
    f.movers.remove(m)
_g = [(x, y) for y in range(f.h) for x in range(f.w) if f.tile(x, y) == _core14.GRASS
      and sum(f.tile(x + a, y + b) == _core14.GRASS for a in range(-3, 4) for b in range(-3, 4)) >= 40]
r.run.player = _g[len(_g) // 2]; r.anim = 0
story.radar_steps = 10
_btn = [b for b in r._buttons() if b[1] == "RADAR"]
check(_btn and not _btn[0][4], f"in the grass: a RADAR button, still charging ({_btn[0][5] if _btn else None})")
story.radar_steps = _pr.CHARGE
r.use_radar(); talk(r)
_st = r._radar
f.seen.update((x, y) for y in range(f.h) for x in range(f.w))
frames(4)
pygame.image.save(pygame.display.get_surface(), os.path.join(OUT, "radar.png"))
check(len(_st["patches"]) == 4 and all(f.tile(*t) == _core14.GRASS for t in _st["patches"]) and _pr.charge(story) == 0,
      f"used: 4 patches of grass shake, the radar recharges ({sorted(_st['patches'])})")
_rp = set(g.loader.area_data[_AD["SINNOH_ROUTE_229"]["radar_pool_percentages"]])
check({"48", "49"} <= _rp, "Route 229's radar pool has Platinum's radar-only Venonat and Venomoth")


def _into_patch(t):
    for dx, dy in ((0, 1), (1, 0), (-1, 0), (0, -1)):
        nb = (t[0] - dx, t[1] - dy)
        if f.walkable(*nb) and nb not in r._radar["patches"] and f.mover_at(*nb) is None:
            r.run.player = nb; r.anim = 0; r.sliding = None; r.hop = None
            r.step(dx, dy)
            return True
    return False


_sp = 48
for t in list(_st["patches"]):
    _st["patches"][t]["species"] = _sp
_t0 = next(iter(_st["patches"]))
_into_patch(_t0)
_met = r.encounter.payload.id if r.encounter else None
check(r.mode == "CHOICE" and _met == _sp and _st["chain"] == 1, f"into a shaking patch: a wild Venonat jumps out (chain {_st['chain']})")
r.run.remove(r.encounter); r.encounter = None; r.mode = "MAP"
frames(2)
check(len(_st["patches"]) >= 1, f"after the meeting the grass shakes again by itself ({len(_st['patches'])} patches)")
for t in list(_st["patches"]):
    _st["patches"][t]["species"] = _sp
_into_patch(next(iter(_st["patches"])))
check(_st["chain"] == 2, f"the same kind again: the chain grows ({_st['chain']})")
r.run.remove(r.encounter); r.encounter = None; r.mode = "MAP"
frames(2)
_off = next(((x, y) for y in range(f.h) for x in range(f.w) if f.walkable(x, y) and (x, y) not in _st["patches"]
             and abs(x - r.run.player[0]) + abs(y - r.run.player[1]) == 1 and f.mover_at(x, y) is None), None)
if _off:
    r.anim = 0; r.sliding = None; r.hop = None; r.walk_goal = None
    r.step(_off[0] - r.run.player[0], _off[1] - r.run.player[1])
check(_st["chain"] == 0 and not _st["patches"], "a step anywhere else: the chain breaks")
check(_pr._shiny_chance(40) >= 1 / 200 and _pr._shiny_chance(0) < 1 / 4000, "shiny patches likelier with the chain (1 in 200 at 40)")
story.repel_routes = _rep14
story.story_flags.clear(); story.story_flags.update(_sv14)
print(f"##### {fails} fails")
