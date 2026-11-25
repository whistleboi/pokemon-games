# Unova batch 11b (11-25): Black City and White Forest (one stands between the Black Gates, your version's first, swapping
# after each League win), their Markets and stores, and Unova's Challenge - the Black Tower / White Treehollow, ten Areas each
# (src/world/black_tower.py): the desk, the Areas' rooms joined door to door, a trainer battle at the Area's level, the gate
# trainer opening the Boss's door, the Boss, the prize and the next Area, the lift back down.
#   bash dev/checks/run.sh unova_b11b
import json
import random
from src.states.overworld import CityState, PlayState
from src.states.overworld import walk_town as WT
from src.states.systems.pick_list import PickListState

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.player_character = "nate"
flags = story.story_flags
flags["unova_version"] = "BLACK_2"; story.starting_region = "UNOVA"
story.badges["UNOVA"] = ["BASIC", "TOXIC", "INSECT", "BOLT", "QUAKE", "JET", "LEGEND", "WAVE"]
for k in ("beat_unova_champion", "b2_hall_of_fame", "visited_BLACK_CITY", "visited_WHITE_FOREST", "visited_UNOVA_ROUTE_14",
          "visited_UNOVA_ROUTE_15", "b2_vr_hugh", "b2_chasm_done", "move_offer_unova"):
    flags[k] = True
said = []
tmaps = json.load(open("assets/town_maps.json", encoding="utf-8"))
prog = json.load(open("assets/unova_area_data.json", encoding="utf-8"))
SP = prog["STORY_PROGRESSION"]
TW = json.load(open("assets/unova_towers.json", encoding="utf-8"))

exec(open("dev/checks/unova_lib.py", encoding="utf-8").read())   # (settle, heard, town, until, _opts, talk, walked, team_of, win, ...)

BATTLES = ("TrainerIntroState", "TrainerBattleState", "DoubleBattleState", "GymBattleState", "BattleState")
from src.world import black_tower as BT, unova_city as UC

print("1) the cities")
bc, wf = tmaps["BLACK_CITY"], tmaps["WHITE_FOREST"]
check(set(bc["exits"].values()) == {"UNOVA_ROUTE_14", "UNOVA_ROUTE_15"} and set(wf["exits"].values()) == {"UNOVA_ROUTE_14", "UNOVA_ROUTE_15"},
      "both lead back to the two Black Gates")
check({"center", "house", "market", "lobby"} <= set(bc["rooms"]) and {"center", "house", "lobby"} <= set(wf["rooms"]),
      "Black City: the Center, the house, the Market, the tower's lobby; White Forest: the Center, the house, the Treehollow's lobby")
check(SP["BLACK_CITY"]["area_type"] == "town" and SP["WHITE_FOREST"]["area_type"] == "town" and not SP["WHITE_FOREST"].get("route_menu"),
      "both are towns now (White Forest's old wild menu gone: Black 2 has no wild Pokemon there)")
flags["hall_of_fame_records"] = [{"region": "UNOVA", "team": []}]
check(not UC.white(story), "after the title, Black 2's Black City stands")
flags["hall_of_fame_records"] = [{"region": "UNOVA", "team": []}] * 2
check(UC.white(story), "after a second League win, White Forest")
flags["hall_of_fame_records"] = [{"region": "UNOVA", "team": []}] * 3
check(not UC.white(story), "after a third, Black City again")
flags["unova_version"] = "WHITE_2"
check(UC.white(story), "White 2: White Forest stands first")
flags["unova_version"] = "BLACK_2"; flags["hall_of_fame_records"] = [{"region": "UNOVA", "team": []}]

print("2) the Market and the people, by the tower")
mk = bc["rooms"]["market"]
stores = [c for o in mk["people"] for c in _opts(o) if isinstance(c, dict) and (c.get("event") or {}).get("pay")]
check(len(stores) == 8 and {c["event"]["pay"] for c in stores} == {10000, 20000, 40000, 60000},
      "four stores, a weekday item and a weekend one each, $10,000-$60,000")
flags["b2_tower"] = {"BLACK": {"cleared": 1}}
check(not story.special_condition("world:unova_city:cleared:BLACK:2"), "store 1 still shut after Area 1")
flags["b2_tower"] = {"BLACK": {"cleared": 2}}
check(story.special_condition("world:unova_city:cleared:BLACK:2"), "...open after Area 2")
st = town("BLACK_CITY", (30, 30))
k0 = [c for o in st.people.values() for c in _opts(o) if str(c.get("text", "")).startswith("Ken") and st._shown(c)]
flags["b2_tower"] = {"BLACK": {"cleared": 10}}
k1 = [c for o in st.people.values() for c in _opts(o) if str(c.get("text", "")).startswith("Ken") and st._shown(c)]
check(k0 and k1 and k0[0]["event"]["lines"] != k1[0]["event"]["lines"], "Ken's words change once you've cleared the tower")
flags["b2_tower"] = {}

print("3) the towers' data, from Black 2's file")
for t, first, last in (("BLACK", "Abed", "Benga"), ("WHITE", "Abigail", "Benga")):
    a = TW[t]
    check(len(a) == 10 and first in a["1"]["boss"]["name"] and last in a["10"]["boss"]["name"]
          and all(len(a[str(n)]["trainers"]) >= 25 and a[str(n)]["healers"] for n in range(1, 11)),
          f"{t}: ten Areas, each with its trainers, healers and Black 2's Boss ({first} ... {last})")
    check([a[str(n)]["levels"][0] for n in range(1, 11)] == [47 + 3 * k for k in range(10)], f"{t}: the Areas' levels 47-50, +3 each")
classes_b = {tr["class"] for n in range(1, 11) for tr in TW["BLACK"][str(n)]["trainers"]}
check({"YOUNGSTER", "LASS", "PSYCHIC", "SCIENTIST", "BACKPACKER", "WAITER", "WAITRESS"} <= classes_b
      and not classes_b & {"HIKER", "WORKER", "BAKER"}, f"the Black Tower's own classes ({sorted(classes_b)[:6]}...)")

print("4) every Area's rooms join up, with a gate below the Boss's room")
bad = []
for t, city in (("BLACK", bc), ("WHITE", wf)):
    for n in range(1, 11):
        L = BT.layout(t, n)
        f0 = L["floors"][0]["lift"]
        rooms = city["rooms"]
        fl = len(L["floors"])
        for f in range(fl):   # (each floor, from its lift room, through the rooms' doors)
            start = BT.room_name(t, n, f, *L["floors"][f]["lift"])
            seen, todo = {start}, [start]
            while todo:
                rm = rooms[todo.pop()]
                for tgt in (rm.get("links") or {}).values():
                    if tgt[0] not in seen:
                        seen.add(tgt[0]); todo.append(tgt[0])
            want = {BT.room_name(t, n, f, r, c) for (r, c) in L["floors"][f]["cells"]}
            if seen != want:
                bad.append((t, n, f, len(seen), len(want)))
        bf, br, bcol = L["boss"]
        gf, gr, gc, _s = L["gate"]
        if (gf, gr, gc) != (bf, br + 1, bcol):
            bad.append((t, n, "gate", L["gate"], L["boss"]))
        gate_room = rooms[BT.room_name(t, n, gf, gr, gc)]
        if not any(b["tiles"] == [list(BT.DOORS["N"])] for b in gate_room.get("barred") or []):
            bad.append((t, n, "no bar"))
check(not bad, f"all 20 Areas: every room reached from its floor's lift, the Boss's door barred in the gate's room ({bad[:3]})")

print("5) the desk, a battle, the gate, the Boss, the prize")
flags.pop("b2_tower", None)
st = town("BLACK_CITY", (28, 18), "lobby")
st.player = st.anim_from = BT.LOBBY_AT; settle(2)
ok = talk(st, "Receptionist")
pl = until(("PickListState",), 400)
check(isinstance(pl, PickListState) and [v for _l, v in pl.choices] == [1], f"the desk offers Area 1 only at first ({getattr(pl, 'choices', None)})")
if isinstance(pl, PickListState):
    pl.pick(1); settle(60)
st = g.current_state
L = BT.layout("BLACK", 1)
check(getattr(st, "room", None) == BT.room_name("BLACK", 1, 0, *L["floors"][0]["lift"]) and tuple(st.player) == BT.LIFT_AT,
      f"into Area 1's lift room ({getattr(st, 'room', None)}, {getattr(st, 'player', None)})")
# a trainer: two Pokemon at Area 1's level
p = next(x for x in L["people"] if x[4] == "trainer" and tuple(x[:4]) != tuple(L["gate"]))
WT_room = BT.room_name("BLACK", 1, *p[1:3]) if False else BT.room_name("BLACK", 1, p[0], p[1], p[2])
st = town("BLACK_CITY", (28, 18), WT_room)
ok = talk(st, TW["BLACK"]["1"]["trainers"][p[5] % len(TW["BLACK"]["1"]["trainers"])]["name"])
cur = until(BATTLES, 800)
t = team_of(cur)
check(ok and len(t) == 2 and all(47 <= lv <= 50 for _s, lv in t) and t[0][1] == t[1][1],
      f"a trainer: two Pokemon of one level, 47-50 in Area 1 ({t})")
if type(cur).__name__ in BATTLES:
    win(cur)
check(flags.get(BT._flag("BLACK", 1, *p[:4])), "beaten")
settle(60); said.clear()
talk(g.current_state, TW["BLACK"]["1"]["trainers"][p[5] % len(TW["BLACK"]["1"]["trainers"])]["name"])
check(any(w in heard() for w in ("gate trainer", "Boss Trainer", "Doctor")), f"then a hint ({heard()[:80]})")
# the gate
check(not story.special_condition("world:black_tower:gate:BLACK:1"), "the Boss's door is locked before the gate trainer")
flags[BT._flag("BLACK", 1, *L["gate"])] = True
check(story.special_condition("world:black_tower:gate:BLACK:1"), "...open once they're beaten")
# the Boss
broom = BT.room_name("BLACK", 1, *L["boss"])
st = town("BLACK_CITY", (28, 18), broom)
st.player = st.anim_from = (6, 8); settle(2)
items0 = {k: v for k, v in story.inventory.items()}
ok = talk(st, TW["BLACK"]["1"]["boss"]["name"])
cur = until(BATTLES, 800)
t = team_of(cur)
check(ok and [s for s, _l in t] == TW["BLACK"]["1"]["boss"]["team"], f"Area 1's Boss: Abed's own team ({t})")
if type(cur).__name__ in BATTLES:
    win(cur)
settle(300)
st = g.current_state
gained = {k: story.inventory.get(k, 0) - items0.get(k, 0) for k in story.inventory if story.inventory.get(k, 0) > items0.get(k, 0)}
check(UC.cleared(story, "BLACK") == 1 and getattr(st, "room", None) == "lobby",
      f"Area 1 cleared: back to the lobby ({UC.cleared(story, 'BLACK')}, {getattr(st, 'room', None)})")
check(any(k in ("HP_UP", "PROTEIN", "IRON", "CALCIUM", "ZINC", "CARBOS") for k in gained), f"Area 1's prize: a vitamin ({gained})")
check(not any(str(k).startswith(BT.prefix("BLACK", 1)) for k in flags), "the Area's trainers stand again next time")
ok = talk(g.current_state, "Receptionist")
pl = until(("PickListState",), 400)
check(isinstance(pl, PickListState) and [v for _l, v in pl.choices] == [1, 2], "Area 2 is open now")
if isinstance(pl, PickListState):
    pl.pick(2); settle(60)
st = g.current_state
check(str(getattr(st, "room", "")).startswith("tower_b2_"), f"into Area 2 ({getattr(st, 'room', None)})")

print("6) the lift: back down to the lobby")
st.player = st.anim_from = (6, 2); st.facing = (0, -1); settle(2)
st._read((6, 1)); settle(20)
pl = until(("PickListState",), 300)
check(isinstance(pl, PickListState) and any(v == -1 for _l, v in pl.choices), "the lift panel offers the lobby")
if isinstance(pl, PickListState):
    pl.pick(-1); settle(60)
check(getattr(g.current_state, "room", None) == "lobby", f"down: you leave the Area ({getattr(g.current_state, 'room', None)})")

print("7) lose in the tower: back to the lobby, no whiting out")
pl_t = BT.layout("BLACK", 2)
p2 = next(x for x in pl_t["people"] if x[4] == "trainer")
st = town("BLACK_CITY", (28, 18), BT.room_name("BLACK", 2, p2[0], p2[1], p2[2]))
ok = talk(st, TW["BLACK"]["2"]["trainers"][p2[5] % len(TW["BLACK"]["2"]["trainers"])]["name"])
cur = until(BATTLES, 800)
b = getattr(cur, "next_state", None) or cur
check(getattr(b, "facility", {}).get("world") == "black_tower", "a tower battle is a facility's (no whiting out)")
nxt = BT.after_battle(g, b.facility, False)
nxt(); settle(200)
check(getattr(g.current_state, "room", None) == "lobby" and "challenge ends" in heard(),
      f"lost: back in the lobby, the challenge over ({getattr(g.current_state, 'room', None)})")

for f_ in fails:
    print("  -", f_)
print(f"##### {len(fails)} failures")
