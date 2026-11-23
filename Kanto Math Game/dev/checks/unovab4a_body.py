# Unova batch 4a (11-23): Nimbasa City (Center, houses, gates, the park, Elesa's Gym, the roller coaster, Hugh and Team
# Plasma, the Subway Bosses with Rosa / Nate, your BW rival's meeting), Route 16, Lostlorn Forest, Route 5 (Bianca's Fly,
# the grotto, Charles at the drawbridge). Teams from Black 2's own trainer table. Played as a player meets them, in the
# walker the game uses (towns: CityState; routes: PlayState -> DungeonState).
#   bash dev/checks/run.sh unovab4a
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


def settle(n=60):
    for _ in range(n):
        st = g.current_state
        box = getattr(st, "npc_dialogue", None) if getattr(st, "npc_active", False) else getattr(st, "dialogue_box", None)
        if box is not None and getattr(box, "visible", True):
            for line in getattr(box, "text_lines", []) or []:
                if not said or said[-1] != line:
                    said.append(line)
        db = getattr(st, "dialogue_box", None)
        if db is not None and getattr(db, "visible", False):
            db.advance()
        elif getattr(st, "npc_active", False):
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        st.update(); st.draw()


def heard():
    return " ".join(said)


def town(area, at, room=None, face=(0, 1)):
    story.current_area_key = area
    g.walk_town_pos = (area, tuple(at), face)
    g.walk_town_room = (area, room) if room else None
    said.clear()
    g.change_state(CityState(g)); settle(30)
    return g.current_state


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
check(not any(k in prog["NIMBASA_CITY"] for k in ("explore_options", "travel_options")) and "route_menu" not in prog["UNOVA_ROUTE_5"],
      "the rebuilt places' menu-era data is gone")
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

print("5b) the roller coaster's cars carry you between platforms")
st = town("NIMBASA_CITY", (12, 41), "coaster", (0, -1))
st.step(0, -1); settle(40)
check(tuple(st.player) == (22, 40) or tuple(getattr(g.current_state, "player", ())) == (22, 40),
      f"the entrance's car: off at the middle platform ({getattr(g.current_state, 'player', None)})")

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
story.region_rivals["UNOVA"].pop("friend_character", None)
print(f"##### {len(fails)} failures")
