# Unova batch 8b (11-24): Route 9 (its gate to Tubeline Bridge, frozen with Opelucid), Shopping Mall Nine (five counters, the
# Waitress and Waiter, the Lady's Hyper Potion errand, the stockroom's appliances for Rotom), the Marine Tube (Undella's
# building, open after Cheren's call; the 3 pm Wailord; the Roxie fan's Black Sludge), Route 11's frozen look.
#   bash dev/checks/run.sh unova_b8b
import json
from src.states.overworld import CityState, PlayState
from src.states.overworld import walk_town as WT


fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.player_character = "nate"
flags = story.story_flags
flags["unova_version"] = "BLACK_2"; story.starting_region = "UNOVA"
NEW = ("UNOVA_ROUTE_9", "MARINE_TUBE", "OPELUCID_CITY", "UNDELLA_TOWN")
for a in NEW:
    flags["visited_" + a] = True
story.badges["UNOVA"] = ["BASIC", "TOXIC", "INSECT", "BOLT", "QUAKE", "JET"]
for k in ("b2_mom_talk", "b2_jet_badge", "b2_lucky_egg", "b2_lentimas_flight", "b2_lentimas_juniper", "visited_UNDELLA_TOWN",
          "b2_lacunosa_juniper", "b2_lacunosa_tale", "b2_lacunosa_zinzolin"):
    flags[k] = True
said = []
tmaps = json.load(open("assets/town_maps.json", encoding="utf-8"))
prog = json.load(open("assets/unova_area_data.json", encoding="utf-8"))
SP = prog["STORY_PROGRESSION"]


exec(open("dev/checks/unova_lib.py", encoding="utf-8").read())   # (settle, heard, town, until, _opts, talk, walked, team_of, win, battle_talk, go: shared, Checks C5)


def where():
    return story.current_area_key, tuple(getattr(getattr(g.current_state, "run", None), "player", None) or getattr(g.current_state, "player", (0, 0)))


BATTLES = ("TrainerIntroState", "TrainerBattleState", "DoubleBattleState", "GymBattleState", "BattleState")


def mains():
    return [m["id"] for m in story.get_active_missions() if m["type"] == "MAIN"]


print("1) the places")
for a in NEW:
    check(a in tmaps, f"{a} is walked")
check(len(SP["UNOVA_ROUTE_9"]["trainer_pool"]) == 5 and SP["UNOVA_ROUTE_9"].get("wild_tables"), "Route 9: Black 2's 5 trainers, its wild Pokemon")
r9 = tmaps["UNOVA_ROUTE_9"]
check({"mall", "stockroom", "gate_w"} <= set(r9["rooms"]), "Route 9: Shopping Mall Nine, its stockroom, the Bridge Gate")
check(r9.get("story_maps") and tmaps["UNOVA_ROUTE_11"].get("story_maps"), "Routes 9 and 11 freeze with Opelucid")
check("tube" in tmaps["UNDELLA_TOWN"]["rooms"] and "tube" in tmaps["HUMILAU_CITY"]["rooms"], "the Marine Tube's buildings at both ends (Undella, Humilau: 9a)")
check(not SP["UNOVA_ROUTE_9"].get("route_menu") and not SP["MARINE_TUBE"].get("route_menu"), "old menu buttons gone")

print("2) the road: Opelucid -> Route 9 -> the Mall")
ds = walked("UNOVA_ROUTE_9", (55, 15))
go(1, 0, 2, 120)
check(where()[0] == "OPELUCID_CITY", f"east from Route 9 into Opelucid ({where()})")
mall = r9["rooms"]["mall"]
shops = [c for o in mall["people"] for c in _opts(o) if isinstance(c, dict) and c.get("event", {}).get("stock")]
stock = {i for c in shops for i in c["event"]["stock"]}
check(len(shops) >= 5 and {"TM163", "TM152", "HP_UP", "X_SPEED", "MAX_POTION", "TIMER_BALL"} <= stock,
      f"the Mall's counters: Black 2's stock ({len(shops)} counters)")
from src.world import unova_story as US
_S = type("S", (), {"game": g})()
flags.pop("b2_mall_lady_day", None); flags.pop("b2_mall_lady_done", None)
m0 = story.money
said.clear(); US.event(_S, {"potion_errand": True}, [], lambda ls: said.extend(ls))
check(story.money == m0 + 1200, "the Lady: $1,200 for a Hyper Potion")
story.inventory["HYPER_POTION"] = story.inventory.get("HYPER_POTION", 0) + 1
said.clear(); US.event(_S, {"potion_errand": True}, [], lambda ls: said.extend(ls))
check(story.inventory.get("ENERGY_ROOT", 0) >= 1 and flags.get("b2_mall_lady_done"), "...brought the same day: an Energy Root")

print("3) the stockroom: Rotom's forms")
sr = r9["rooms"]["stockroom"]
forms_here = {e["event"]["rotom_form"] for e in (sr.get("sign_events") or {}).values()}
check(forms_here == {"heat", "wash", "frost", "fan", "mow", "normal"}, f"six appliance boxes ({sorted(forms_here)})")
story.player_team.append(mk(479))
said.clear(); US.event(_S, {"rotom_form": "wash", "lines": []}, [], lambda ls: said.extend(ls))
rot = story.player_team[-1]
check("HYDRO-PUMP" in [str(m).upper() for m in (rot.moves or [])] or "wash" in str(getattr(rot, "form", "")).lower(),
      f"the washing machine: Wash Rotom ({getattr(rot, 'form', None)}, {rot.moves})")

print("4) the Marine Tube")
for k in ("b2_opelucid_cheren",):
    flags.pop(k, None)
tube = tmaps["UNDELLA_TOWN"]["rooms"]["tube"]
check(any(b.get("until", {}).get("flag_condition") == "b2_opelucid_cheren" for b in tube.get("barred") or []),
      "closed for cleaning till Cheren's call from Opelucid")
flags["b2_opelucid_cheren"] = True
ds = walked("MARINE_TUBE", (15, 185))
go(0, 1, 6, 80)
check(where()[0] == "UNDELLA_TOWN", f"south out of the Tube into Undella ({where()})")
mt = tmaps["MARINE_TUBE"]
check(any("hour:15" in str(sc.get("condition")) for sc in mt.get("scenes") or []), "the Wailord swims by at 3 pm")
sl = [c for o in mt["people"] for c in _opts(o) if isinstance(c, dict) and c.get("event", {}).get("gift_item") == {"BLACK_SLUDGE": 1}]
check(sl and "holding:POISON_BARB" in str(sl[0]["condition"]), "the Roxie fan: a Black Sludge for a Poison Barb holder")

for f_ in fails:
    print("  -", f_)
print(f"##### {len(fails)} failures")
