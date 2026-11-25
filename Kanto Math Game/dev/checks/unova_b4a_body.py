# Unova batch 4a (11-23): Nimbasa City (Center, houses, gates, the park, Elesa's Gym, the roller coaster, Hugh and Team
# Plasma, the Subway Bosses with Rosa / Nate, your BW rival's meeting), Route 16, Lostlorn Forest, Route 5 (Bianca's Fly,
# the grotto, Charles at the drawbridge). Teams from Black 2's own trainer table. Played as a player meets them, in the
# walker the game uses (towns: CityState; routes: PlayState -> DungeonState).
#   bash dev/checks/run.sh unova_b4a
import json
from src.states.overworld import CityState, PlayState as _PS
from src.states.overworld.dungeon import DungeonState as _DS


fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.player_character = "nate"; g.rival_name = "HUGH"
flags = story.story_flags
flags["unova_version"] = "BLACK_2"; story.starting_region = "UNOVA"
for a in ("NIMBASA_CITY", "UNOVA_ROUTE_16", "LOSTLORN_FOREST", "UNOVA_ROUTE_5", "JOIN_AVENUE"):
    flags["visited_" + a] = True
said = []
prog = json.load(open("assets/unova_area_data.json", encoding="utf-8"))["STORY_PROGRESSION"]
tmaps = json.load(open("assets/town_maps.json", encoding="utf-8"))


exec(open("dev/checks/unova_lib.py", encoding="utf-8").read())   # (settle, heard, town: shared, Checks C5)


def walk_route(area, at=None, floor=0):
    story.current_area_key = area
    g.walk_town_pos = g.walk_town_room = None
    if at:
        g.arrive_floor = (area, floor, list(at))
    g.change_state(_PS(g)); settle(8)
    return g.current_state


def people(st):
    """Who's standing in the town or room now: their labels (the options showing, by their conditions)."""
    out = {}
    for home, o in (getattr(st, "people", None) or {}).items():
        for c in (o.get("any") if isinstance(o, dict) and "any" in o else [o]):
            if isinstance(c, dict) and st._shown(c):
                out[str(c.get("text", "")).rstrip()] = home
    return out


def movers(t):
    return {str(m.payload.get("text", "")).rstrip(): m for m in t.run.floor.movers if isinstance(getattr(m, "payload", None), dict)}


def use(t, text):
    m = movers(t).get(text)
    if m is None:
        return False
    said.clear(); t._use_figure(m); settle(40)
    return True


print("1) the data: Black 2's own trainers and teams")
r16 = [t["name"] for t in prog["UNOVA_ROUTE_16"]["trainer_pool"]]
check(r16 == ["Backers Stu & Art", "Cyclist Krissa", "Cyclist Hector", "Backpacker Blossom", "Backpacker Ivan", "Depot Agent Hank"],
      f"Route 16's six trainers, from the file ({r16})")
ll = {t["name"]: t for t in prog["LOSTLORN_FOREST"]["trainer_pool"]}
check(ll["Veteran Murphy"]["levels"] == [51] * 5 and "Pokemon Breeder Galen" in ll, "Lostlorn Forest: Galen, the Rangers, Veteran Murphy at Lv 51")
r5 = {t["name"]: t for t in prog["UNOVA_ROUTE_5"]["trainer_pool"]}
check(r5["Backers Ava & Aya"].get("battle_options", {}).get("double") and r5["Motorcyclist Charles"].get("battle_options", {}).get("double"),
      "Route 5's pair and Charles (Rotation / Triple in the games) are double battles")
el = prog["NIMBASA_CITY"]["gym"]["leader"]
check(el["team"] == [587, 180, 523] and el["levels"] == [28, 28, 30] and el["held_items"] == {"523": "SITRUS_BERRY"},
      "Elesa: Emolga 28, Flaaffy 28, Zebstrika 30 with a Sitrus Berry (Normal mode, from the file)")
check(el["rewards"].get("TM048") == 1 and el["badge_reward"] == "BOLT", "the Bolt Badge and TM Volt Switch")
check("explore_options" not in prog["NIMBASA_CITY"] and "route_menu" not in prog["UNOVA_ROUTE_5"]
      and sorted(o["target_area"] for o in prog["NIMBASA_CITY"].get("travel_options", [])) == ["JOIN_AVENUE", "UNOVA_ROUTE_16", "UNOVA_ROUTE_5"],
      "the menu-era data is gone; travel options only for Nimbasa's own ways out (walk_town opens an exit by them: 11-23)")
check(all(prog[a].get("wild_tables") for a in ("UNOVA_ROUTE_16", "LOSTLORN_FOREST", "UNOVA_ROUTE_5")),
      "Routes 5 and 16 and Lostlorn Forest have Black 2's wild tables")

print("2) into Nimbasa from Join Avenue: your BW rival's meeting")
story.region_rivals.setdefault("UNOVA", {})["friend_character"] = "cheren"
flags["b2_colress_route4"] = True
st = town("NIMBASA_CITY", (46, 62), face=(0, -1))
settle(200)
check(flags.get("b2_nimbasa_rival") and "Cheren" in heard(), f"Cheren meets you as you arrive ({heard()[:70]})")
mission = [m["id"] for m in story.get_active_missions() if str(m.get("type", "")).upper() == "MAIN"]
check(mission[:1] == ["b2_m20"], f"the Journal: The City of Lights ({mission})")

print("3) the Center")
st = town("NIMBASA_CITY", (7, 16), "center", (0, -1))
ps = people(st)
check({"Pokémon Center", "Shop", "Mr. Medal", "Gentleman by the counter"} <= set(ps), f"the Center's nurse, shop, Mr. Medal, the Gentleman ({sorted(ps)[:8]})")

print("4) the park: the Leader is out; the roller coaster; Elesa's Gym")
st = town("NIMBASA_CITY", (12, 13), "park", (1, 0))
check(getattr(st, "room", None) == "park", f"the amusement park is its own map ({getattr(st, 'room', None)})")
st = town("NIMBASA_CITY", (71, 13), "park", (0, -1))
settle(120)
check(flags.get("b2_nimbasa_gym_out"), "the guide stops you at the Gym: Elesa is out (The Leader Is Out)")
st = town("NIMBASA_CITY", (15, 43), "coaster", (0, -1))
check(getattr(st, "room", None) == "coaster", "into the Shining Roller Coaster")
ps = people(st)
check({"Woman at the back", "Rich Boy Rolan", "Lady Colette"} <= set(ps), f"the roller coaster's people and its two trainers ({sorted(ps)})")
flags["b2_elesa_coaster"] = True   # (her gift: talked to below, in the walker)
st = town("NIMBASA_CITY", (15, 58), "gym", (0, -1))
ps = people(st)
check({"Gym", "Gym guide", "Beauty Nikola", "Beauty Fleming", "Beauty Ampere"} <= set(ps), f"Elesa's Gym: the catwalk's Beauties and Elesa ({sorted(ps)})")

print("5) after the Bolt Badge: Hugh and Team Plasma at Big Stadium")
flags["b2_bolt_badge"] = True; story.badges.setdefault("UNOVA", [])
st = town("NIMBASA_CITY", (27, 22), face=(-1, 0))
ps = people(st)
check("{rival_name}" in ps and "Plasma Grunt" in ps, "Hugh and the Grunts stand outside Big Stadium")
from src.world import story_events as _se
ev = _se.EVENTS["b2_nimbasa_plasma"]["battle"]
check(ev["battle_options"]["double"] and ev["battle_options"]["partner"]["sprite"] == "hugh.png" and ev["team"] == [568]
      and ev["battle_options"]["second_trainer"]["team"] == [505], "the battle: you and Hugh against two Grunts (Trubbish, Watchog Lv 27)")

st = town("NIMBASA_CITY", (26, 22), face=(-1, 0))
st.step(-1, 0)
seen_battle = None
for _ in range(900):
    cur = g.current_state
    if type(cur).__name__ in ("TrainerIntroState", "DoubleBattleState", "TrainerBattleState"):
        seen_battle = cur
        break
    settle(1)
nxt = getattr(seen_battle, "next_state", None) or seen_battle
check(seen_battle is not None and type(nxt).__name__ == "DoubleBattleState" and getattr(nxt, "partner_name", None) == "HUGH",
      f"walking up to them starts the scene, then the double battle beside Hugh ({type(nxt).__name__})")
if seen_battle is not None:
    flags["b2_nimbasa_plasma_battled"] = True
    g.change_state(st); settle(5)

print("5a) out of Nimbasa by its gates (11-23: the playthrough found every way out shut)")
st = town("NIMBASA_CITY", (4, 5), "gate_w", (-1, 0))
for _ in range(6):
    st = g.current_state
    if story.current_area_key != "NIMBASA_CITY":
        break
    if hasattr(st, "step"):
        st.step(-1, 0)
    settle(60)
check(story.current_area_key == "UNOVA_ROUTE_5", f"west through the gate onto Route 5 ({story.current_area_key})")
print("5b) the roller coaster: Black 2's cars and switches (overlay 102)")
for k in range(4):
    flags.pop("b2_coaster_sw%d" % k, None)


def ride(at, face):
    # (straight onto the platform: a car-only platform is kept as your spot, by the room's "landings" - main 11-23)
    st = town("NIMBASA_CITY", at, "coaster", face)
    check(tuple(st.player) == tuple(at), f"back in the room on its platform {at}")
    st.step(*face)
    quiet = 0
    for _ in range(600):   # (the car moves a tile at a time: wait till the ride has stopped for a while)
        settle(1)
        cur = g.current_state
        busy = getattr(cur, "anim", 0) or getattr(cur, "npc_active", False) or             (getattr(cur, "scenes", None) and getattr(cur.scenes, "playing", None))
        quiet = 0 if busy else quiet + 1
        if quiet > 30:
            break
    return tuple(g.current_state.player)


check(ride((14, 40), (0, -1)) == (22, 40), "the entrance's car: off at the middle platform")
st = town("NIMBASA_CITY", (29, 34), "coaster", (0, -1)); st.step(0, -1); settle(120)
check(flags.get("b2_coaster_sw0"), "the middle platform's switch flips")
check(ride((22, 40), (0, -1)) == (16, 28), "...now the middle's car goes to the left platform")
check(ride((16, 16), (0, -1)) == (16, 15), "the left platform's top car: no track yet (you just step to its edge)")
flags["b2_coaster_sw1"] = True
check(ride((16, 16), (0, -1)) == (41, 41), "its switch flipped: off at the back platform, by Lady Colette")
flags["b2_coaster_sw2"] = True
check(ride((49, 41), (0, -1)) == (34, 9), "the back platform's switch: up to the top, where the woman waits")
flags["b2_coaster_sw3"] = True
check(ride((22, 9), (0, -1)) == (5, 40), "the top's switch: a car straight back to the entrance")
ps = people(town("NIMBASA_CITY", (34, 9), "coaster", (0, 1)))
check({"Woman at the back", "Lady Colette", "Rich Boy Rolan", "Guide at the entrance"} <= set(ps), f"everyone in the roller coaster ({sorted(ps)})")

print("6) the Subway Bosses' partner: Rosa for a boy, Nate for a girl")
st = town("NIMBASA_CITY", (38, 48), face=(0, -1))
ps = people(st)
check("Rosa" in ps and "Nate" not in ps, f"a boy player: Rosa asks to team up ({[k for k in ps if k in ('Rosa', 'Nate')]})")
g.player_character = "rosa"
st = town("NIMBASA_CITY", (38, 48), face=(0, -1))
ps = people(st)
check("Nate" in ps and "Rosa" not in ps, "a girl player: Nate asks")
g.player_character = "nate"

print("7) Route 5: Bianca's Fly and the grotto; Charles; your rival")
flags["b2_nimbasa_plasma"] = True
t = walk_route("UNOVA_ROUTE_5", (53, 22))
check(isinstance(t, _DS) and t.area_key == "UNOVA_ROUTE_5", f"Route 5 is walked on the route walker ({type(t).__name__})")
t.step(-1, 0); settle(400)
check(story.inventory.get("HM_FLY", 0) == 1 and "Fly" in heard(), f"Bianca catches up: HM02 Fly ({heard()[:60]})")
check(flags.get("grottoes", {}).get("1", {}).get("id") == 572, "...and the grotto off the route holds a Minccino")
t = g.current_state
names = set(movers(t))
check("Motorcyclist Charles" in names, "Charles blocks the drawbridge")
arr = [e["event"]["flag_check"] for e in t._arrival_figures()]
check(arr == ["defeated_cheren_route5"], f"Cheren (your pick) waits to battle before the bridge ({arr})")

print("8) Route 16 and Lostlorn Forest")
t = walk_route("UNOVA_ROUTE_16", (8, 22))
check(isinstance(t, _DS) and t.area_key == "UNOVA_ROUTE_16", "Route 16 on the route walker")
art = tmaps["UNOVA_ROUTE_16"]["art"]
check(art[9][26] == "2" and art[21][34] == "b", "a small tree (Cut) and a boulder (Strength) where Black 2 has them")
t = walk_route("LOSTLORN_FOREST", (12, 50))
check(isinstance(t, _DS) and "Odd Backpacker" in movers(t), "Lostlorn Forest: the odd Backpacker")
check("grotto" in tmaps["LOSTLORN_FOREST"].get("rooms", {}) and "grotto" in tmaps["UNOVA_ROUTE_5"].get("rooms", {}),
      "Lostlorn's and Route 5's Hidden Grottoes")

print("9) the Journal and the Quest Book")
book = json.load(open("assets/quest_book.json", encoding="utf-8"))["UNOVA"]
ids = [c["mission"] for a in book for c in a["chapters"]]
check(all(f"b2_m{n}" in ids for n in range(20, 25)), "chapters for The City of Lights to West to Route 5")
print("5c) Elesa's catwalk: dark, a new stretch lit as you reach each trigger (overlay 92)")
for k in (1, 2, 3):
    flags.pop("b2_elesa_lit%d" % k, None)
st = town("NIMBASA_CITY", (10, 59), "gym", (0, -1))
r0 = st.light_radius()
for _ in range(6):
    st.step(0, -1); settle(20)
check(r0 is not None and flags.get("b2_elesa_lit1"), "the first trigger lights the next stretch")
_lit = [z for z in st.dark.get("lit", []) if z[4] is None or flags.get(z[4])]
check(any(z[4] == "b2_elesa_lit1" for z in _lit) and not any(z[4] == "b2_elesa_lit2" for z in _lit),
      "...that stretch only, up to its model (the next still dark)")
check(tmaps["NIMBASA_CITY"]["rooms"]["gym"]["dark"].get("lit"), "the lit stretches are in the map, for main's section lighting")
check(tmaps["LOSTLORN_FOREST"].get("hidden", {}).get("19,33") == "GRASS_GEM", "Lostlorn's hidden Grass Gem, where Black 2 hides it")
import os as _os
_ingo = [o for o in json.dumps(tmaps).split('"sprite": ') if o.startswith('"b2_ingo.png"')]
check(_ingo and _os.path.exists("assets/sprites/trainers/b2_ingo.png"),
      "Ingo's own battle picture, from Black 2's animated set (a/0/7/1 slot 87)")
story.region_rivals["UNOVA"].pop("friend_character", None)
print(f"##### {len(fails)} failures")
