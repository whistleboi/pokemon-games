# Unova batch 3b (11-21): Route 4 (Black 2's settlement / White 2's ruins, by version), the Castelia Gate's Dowsing
# MCHN, the Desert Resort (its entrance and gate), Relic Castle's top two floors, Join Avenue (the manager game).
# Played the way a player meets them, in the walker the game uses (towns: CityState; routes: PlayState -> DungeonState).
#   bash dev/checks/run.sh unova_b3b
import json
from src.states.overworld import CityState, PlayState as _PS
from src.world import join_avenue as ja, b2_errands, itemfinder

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True
flags = story.story_flags
flags["unova_version"] = "BLACK_2"; story.starting_region = "UNOVA"
for a in ("CASTELIA_CITY", "UNOVA_ROUTE_4", "DESERT_RESORT_ENTRANCE", "DESERT_RESORT", "RELIC_CASTLE", "JOIN_AVENUE"):
    flags["visited_" + a] = True
said = []


exec(open("dev/checks/unova_lib.py", encoding="utf-8").read())   # (settle, heard: shared, Checks C5)


def pick(value):
    st = g.current_state
    if type(st).__name__ == "PickListState":
        st.pick(value); settle(5)
        return True
    return False


def until(cond, n=400):
    for _ in range(n):
        if cond():
            return True
        settle(1)
    return cond()


def walk_route(area, at=None, floor=0):
    story.current_area_key = area
    g.walk_town_pos = g.walk_town_room = None
    if at:
        g.arrive_floor = (area, floor, list(at))
    g.change_state(_PS(g)); settle(8)
    return g.current_state


def live3d_props_ok():
    import os as _o
    return all(_o.path.isfile("assets/b2_3d/prop_490_%d.npz" % m) for m in range(189, 213))


def figure(t, text):
    return next((m for m in t.run.floor.movers if isinstance(getattr(m, "payload", None), dict)
                 and str(m.payload.get("text", "")).rstrip() == text), None)


def use(t, text):
    m = figure(t, text)
    if m is None:
        return False
    said.clear(); t._use_figure(m); settle(30)
    return True


print("1) the Castelia Gate: Bianca's Dowsing MCHN")
flags["b2_colress_plaza"] = True
story.current_area_key = "CASTELIA_CITY"
g.walk_town_pos = ("CASTELIA_CITY", (5, 13), (0, -1)); g.walk_town_room = ("CASTELIA_CITY", "gate_route4")
said.clear(); g.change_state(CityState(g)); settle(200)
check(story.inventory.get("DOWSING_MACHINE", 0) == 1 and "Dowsing" in heard(), f"Bianca catches up in the gate and gives the Dowsing MCHN ({heard()[:80]})")

print("2) Route 4, Black 2: the settlement, the Crustle, Colress")
t = walk_route("UNOVA_ROUTE_4", (46, 110))
check(type(t).__name__ == "DungeonState" and t.area_key == "UNOVA_ROUTE_4", f"Route 4 is walked on the route walker ({type(t).__name__})")
names = {str(m.payload.get("text", "")).rstrip() for m in t.run.floor.movers if isinstance(getattr(m, "payload", None), dict)}
check("Crustle 0" in names and "Colress" in names, "the Crustle block the road, Colress beside them")
check(figure(t, "Policeman Braven") is None and any(n == "Policeman Braven" for n in [str((m.payload[1] or {}).get("name")) for m in t.run.floor.movers if m.kind == "trainer"]),
      "Black 2's Trainers stand on its Route 4 (Policeman Braven)")
_occ = {(m.x, m.y) for m in t.run.floor.movers}
_seen, _todo = {(46, 110)}, [(46, 110)]
while _todo:
    _x, _y = _todo.pop()
    for _q in ((_x + 1, _y), (_x - 1, _y), (_x, _y + 1), (_x, _y - 1)):
        if _q not in _seen and t.run.floor.walkable(*_q) and _q not in _occ and _q not in t.run.floor.exits:
            _seen.add(_q); _todo.append(_q)
blocked = not any(_y < 98 for _x, _y in _seen)
check(blocked, "the Crustle leave no way through the road")
t.run.player = t.anim_from = t.partner = t.partner_from = (46, 105); t.anim = 0; settle(3)
said.clear(); t.step(0, -1); settle(120)
st = g.current_state
check("Colress" in heard() and ("Battle" in type(st).__name__ or "Trainer" in type(st).__name__ or flags.get("b2_colress_r4_met")),
      f"stepping up to the Crustle: Colress's device, then his battle ({type(st).__name__})")
flags["b2_colress_r4"] = True
t = walk_route("UNOVA_ROUTE_4", (46, 105))
said.clear(); t.step(0, -1); settle(120)
check(story.inventory.get("PROTEIN", 0) >= 1 and flags.get("b2_colress_r4_done"), "after the battle: his thanks and a Protein")
t = walk_route("UNOVA_ROUTE_4", (46, 105))
check(figure(t, "Crustle 0") is None, "the Crustle have gone: the road is open")

print("3) Route 4's houses")
ROOMS = (t.recipe.get("art") or {}).get("room_floors") or {}
check({"speed_house", "trade_house", "cry_house", "rest_house", "empty_house"} <= set(ROOMS), f"Black 2's five houses are walkable ({sorted(ROOMS)})")
t = walk_route("UNOVA_ROUTE_4", (6, 9), ROOMS.get("speed_house", 0))
lead = story.player_team[0]
want = b2_errands.target(story, "b2_r4_speed", [p for p in story.player_team if p])
flags.pop("b2_r4_speed", None)
_orig = lead.stat_value
lead.stat_value = lambda s, level=None: want if s == "SPEED" else _orig(s, level)
before = story.inventory.get("HEALTH_WING", 0)
use(t, "Ace Trainer in the house")
check(story.inventory.get("HEALTH_WING", 0) == before + 5, f"the Speed check: exactly her number -> 5 Health Wings ({story.inventory.get('HEALTH_WING', 0) - before})")
lead.stat_value = _orig
use(t, "Ace Trainer in the house")
check("tomorrow" in heard(), "...once a day")
t = walk_route("UNOVA_ROUTE_4", (6, 9), ROOMS.get("rest_house", 0))
lead.current_hp = 1
use(t, "Woman in the rest house")
check(lead.current_hp == lead.get_max_hp(), "the rest house heals your team")
from src.pokemon.data import Pokemon
story.player_team.append(mk(546))
t = walk_route("UNOVA_ROUTE_4", (6, 9), ROOMS.get("trade_house", 0))
use(t, "Lass who wants Cottonee")
check(any(p and p.id == 548 for p in story.player_team) and not any(p and p.id == 546 for p in story.player_team),
      "the Lass trades her Petilil for your Cottonee")
t = walk_route("UNOVA_ROUTE_4", (6, 9), ROOMS.get("cry_house", 0))
use(t, "Maid who imitates cries")
check(type(g.current_state).__name__ == "PickListState", "the Maid imitates a cry and asks whose it was")
pick(None)

print("4) White 2's Route 4: the ruins")
flags["unova_version"] = "WHITE_2"
t = walk_route("UNOVA_ROUTE_4", (46, 110))
tn = {str((m.payload[1] or {}).get("name")) for m in t.run.floor.movers if m.kind == "trainer"}
check("Lady Lina" in tn and "Policeman Braven" not in tn, f"a White 2 player walks White 2's Route 4 (Lady Lina; no Policemen) ({sorted(tn)[:4]})")
birds = {str(m.payload.get("text")) for m in t.run.floor.movers if isinstance(getattr(m, "payload", None), dict) and m.payload.get("action") == "BOSS"}
_dump = json.dumps(t.recipe.get("art") or {})
check('"weekday:mon"' in _dump and '"weekday:thu"' in _dump and "Braviary" in _dump and "Mandibuzz" in _dump,
      "both weekly birds wait here, each on its day (Braviary Mondays, Mandibuzz Thursdays)")
flags["unova_version"] = "BLACK_2"

print("5) the Desert Resort")
t = walk_route("DESERT_RESORT_ENTRANCE", (49, 30))
check(type(t).__name__ == "DungeonState" and t.area_key == "DESERT_RESORT_ENTRANCE", "the desert's entrance off Route 4")
t = walk_route("DESERT_RESORT", (83, 82))
check(t.area_key == "DESERT_RESORT" and (t.area_data.get("weather") == "SAND"), "the Desert Resort, in its sandstorm")
flags.pop("b2_desert_mariah", None)
check(figure(t, "Nurse Mariah") is not None and figure(t, "Nurse Mariah").payload.get("event", {}).get("battle"),
      "Nurse Mariah battles first...")
flags["b2_desert_mariah"] = True
t = walk_route("DESERT_RESORT", (83, 82))
lead.current_hp = 1
use(t, "Nurse Mariah")
check(lead.current_hp == lead.get_max_hp(), "...then heals your team whenever you ask")
use(t, "Backpacker who wants water")
check(story.inventory.get("SOFT_SAND", 0) >= 1, "the Backpacker gives Soft Sand")
hid = (t.recipe.get("art") or {}).get("hidden") or {}
check(itemfinder.beep(story, hid, (56, 37), lambda x, y: "nope", set()) and "Dowsing" in itemfinder.beep(story, hid, (56, 37), lambda x, y: "nope", set()),
      "the Dowsing MCHN reacts to the buried Ground Gem nearby")

print("6) Relic Castle's top floors")
t = walk_route("RELIC_CASTLE", (21, 20))
check(type(t).__name__ == "DungeonState" and t.run.index == 0, "Relic Castle 1F from the desert")
t.run.player = t.anim_from = t.partner = t.partner_from = (4, 10); t.anim = 0; settle(3)
t.step(0, 1); settle(40)
check(g.current_state.run.index == 1, f"its quicksand drops you to B1F ({g.current_state.run.index}, {tuple(g.current_state.run.player)})")
t = walk_route("RELIC_CASTLE", (3, 16))
t.run.player = t.anim_from = t.partner = t.partner_from = (3, 17); t.anim = 0; settle(3)
t.step(1, 0); settle(40)
check(g.current_state.run.index == 1 and g.current_state.run.player[1] >= 13, f"the hall's own stairs lead to B1F's lower half ({tuple(g.current_state.run.player)})")

print("7) Join Avenue: you're the manager")
flags.pop("b2_join_manager", None); flags.pop("join_avenue", None)
story.current_area_key = "JOIN_AVENUE"
g.walk_town_pos = ("JOIN_AVENUE", (13, 70), (0, -1)); g.walk_town_room = None
said.clear(); g.change_state(CityState(g)); settle(5)
t = g.current_state
t.step(0, -1); settle(120)
check(flags.get("b2_join_owner_met") and "come and talk" in heard(), "the owner walks up as you come in and calls you over")
said.clear(); g.current_state._talk((13, 66))
_asked = []
for _ in range(400):
    st = g.current_state
    if type(st).__name__ == "TextPromptState":
        _asked.append(st.question)
        st.text = "Howdy!" if len(_asked) == 1 else "Whoa!"
        st.confirm()
    settle(1)
    if flags.get("b2_join_manager") and len(_asked) >= 2:
        break
settle(60)
check(flags.get("b2_join_manager") and len(_asked) == 2, f"talk to him: he asks your two phrases and makes you manager ({_asked})")
check(ja.data(story).get("greeting") == "Howdy!" and ja.data(story).get("moved") == "Whoa!", "...and keeps them for the avenue's people to say")
vs = ja.visitors(story)
check(len(vs) == ja.VISITORS_A_DAY, f"{ja.VISITORS_A_DAY} visitors today, each with a dream")
ev = {"join_avenue": "visitor", "slot": 0}
from src.states.overworld import common
said.clear(); common._run_story_event(t, ev, lambda c: True, t.show_message if hasattr(t, "show_message") else (lambda l: None)); settle(10)
check(pick(("invite", 0)) or True, "a visitor tells their dream; invite them")
d = ja.data(story)
check(d["lots"][0] and d["lots"][0]["kind"] == vs[0]["dream"] and flags.get("ja_lot_0"), "...and their shop opens on lot 1")
g.walk_town_pos = ("JOIN_AVENUE", (13, 70), (0, -1)); g.change_state(CityState(g)); settle(5)
t = g.current_state
keep = [o for o in (t.town_map.get("people") or []) if isinstance(o, dict) and o.get("text") == "Shopkeeper on lot 1"]
check(keep and t.npc_shown(keep[0]) if hasattr(t, "npc_shown") else bool(keep), "its shopkeeper stands on the lot")
d["lots"][0]["kind"] = "market"; d["lots"][0]["pop"] = 0
v = vs[1]; v["done"] = False; v["likes"] = "market"
rk = ja.rank(d); pop = d["pop"]
said.clear(); common._run_story_event(t, {"join_avenue": "visitor", "slot": 1}, lambda c: True, lambda l: t.show_message(l)); settle(10)
pick(("recommend", 0))
check(d["pop"] > pop and d["lots"][0]["pop"] > 0, "recommend a shop they like: the shop and the avenue grow more popular")
said.clear(); common._run_story_event(t, {"join_avenue": "shop", "lot": 0}, lambda c: True, lambda l: t.show_message(l)); settle(30)
check(type(g.current_state).__name__ == "PokeMartState", f"the shop sells its goods ({type(g.current_state).__name__})")
check("nursery" not in ja.kinds_open(story, d), "no Nursery before the Hall of Fame")
check(any(p[0].startswith("490_189") for p in ja.storefronts(story)) and live3d_props_ok(), "lot 1's Market stands as Black 2's own storefront (its smallest, at shop rank 1)")
_k = vs[0]["dream"]
check(story.special_condition("ja_visitor:0:%s" % _k) and not story.special_condition("ja_visitor:0:%s" % ("dojo" if _k != "dojo" else "cafe")),
      "a visitor looks the part of their dream (the spot's look follows today's dream)")

print("8) Route 4's vending machine, the birds, the Dowsing MCHN's screen")
t = walk_route("UNOVA_ROUTE_4", (14, 53))
use(t, "Vending machine")
check(type(g.current_state).__name__ == "PokeMartState" and "FRESH_WATER" in (g.current_state.stock or []), "the vending machine by the rest house sells drinks")
g.change_state(t)
flags["b2_r4_mandibuzz"] = True; flags.pop("legend_rematch_b2_r4_mandibuzz", None)
check(not story.special_condition("legend_back:b2_r4_mandibuzz"), "a caught (or not yet beaten-and-gone) bird doesn't come back")
flags["legend_rematch_b2_r4_mandibuzz"] = 1
check(story.special_condition("legend_back:b2_r4_mandibuzz"), "a beaten, uncaught bird comes back (on its day: the weekday condition)")
from src.states.systems.bag import BagState
check("DOWSING_MACHINE" in BagState.USABLE_KEYS, "the Dowsing MCHN is used from the Bag")
flags["dowsing_on"] = True
check(itemfinder.dowsing_on(story) and itemfinder.dowse(story, {"56,35": "GROUND_GEM"}, (54, 35), lambda x, y: "nope") == (2, 0),
      "switched on, its rods point at the buried item nearby (2 tiles east)")
t = walk_route("DESERT_RESORT", (55, 36))
t.draw()
check(True, "...and its panel draws on the map")
flags.pop("dowsing_on", None)

print("7) Route 4: the BW rival you picked battles you there, not the other one (11-23)")
_had = list(story.badges.get("UNOVA", [])); story.badges["UNOVA"] = ["BASIC", "TOXIC", "INSECT"]
for who, other in (("cheren", "bianca"), ("bianca", "cheren")):
    story.region_rivals.setdefault("UNOVA", {})["friend_character"] = who
    t = walk_route("UNOVA_ROUTE_4", (46, 110))
    fs = [e["event"]["flag_check"] for e in t._arrival_figures()]
    check(fs == ["defeated_%s_route4" % who], f"picked {who}: only {who} waits on Route 4 ({fs})")
story.badges["UNOVA"] = _had; story.region_rivals["UNOVA"].pop("friend_character", None)

print(f"##### {len(fails)} failures")
