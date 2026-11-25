# Unova batch 9a (11-24): Humilau City (Hugh, Marlon on the pier, Marlon's lily-pad Gym, the Wave Badge, Hugh and Marlon after),
# Route 22 (Colress, the Colress Machine, Terrakion), Route 21, Seaside Cave (Black Belt Rocky, the Crustle at the east exit).
#   bash dev/checks/run.sh unovab9a
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
NEW = ("HUMILAU_CITY", "UNOVA_ROUTE_22", "UNOVA_ROUTE_21", "SEASIDE_CAVE", "SEASIDE_CAVE_B1F")
for a in NEW:
    flags["visited_" + a] = True
story.badges["UNOVA"] = ["BASIC", "TOXIC", "INSECT", "BOLT", "QUAKE", "JET", "LEGEND"]
for k in ("b2_mom_talk", "b2_jet_badge", "b2_lucky_egg", "b2_lentimas_flight", "b2_lentimas_juniper", "visited_UNDELLA_TOWN",
          "b2_lacunosa_juniper", "b2_lacunosa_tale", "b2_lacunosa_zinzolin", "b2_legend_badge", "b2_opelucid_cheren",
          "visited_OPELUCID_CITY"):
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
for a, n in (("UNOVA_ROUTE_22", 6), ("UNOVA_ROUTE_21", 7), ("SEASIDE_CAVE", 4), ("SEASIDE_CAVE_B1F", 2)):
    check(len(SP[a]["trainer_pool"]) == n, f"{a}: Black 2's {n} trainers")
hu = tmaps["HUMILAU_CITY"]
check({"gym", "center", "tutor", "trade", "luvdisc", "mienfoo", "honeymoon"} <= set(hu["rooms"]), "Humilau's Gym, Center and houses")
gym = SP["HUMILAU_CITY"]["gym"]["leader"]
check(gym["team"] == [565, 321, 593] and gym["levels"] == [49, 49, 51] and gym["rewards"].get("TM188"),
      f"Marlon: Carracosta, Wailord, Jellicent 49/49/51 and Scald ({gym['team']}, {gym['levels']})")

print("2) Humilau: Hugh, Marlon, the Gym's lily pads")
flags["visited_HUMILAU_CITY"] = True
story.current_area_key = "HUMILAU_CITY"
check("b2_m40" in mains(), f"the Journal: Marlon ({mains()})")
for k in ("b2_humilau_hugh", "b2_humilau_marlon"):
    flags.pop(k, None)
st = town("HUMILAU_CITY", (21, 48), face=(0, -1))
go(0, -1, 2, 60); settle(1200)
check(flags.get("b2_humilau_hugh") and "Badge" in heard(), "Hugh by the Marine Tube: the Gym first")
st = town("HUMILAU_CITY", (26, 30), face=(0, -1))
go(0, -1, 1, 60); settle(1200)
check(flags.get("b2_humilau_marlon") and "Marlon" in heard(), "Marlon leaps out of the water onto the pier")
from src.world import humilau_gym as HG
flags.pop(HG.FLAG, None); flags.pop(HG.ARRIVED, None)
st = town("HUMILAU_CITY", (12, 64), "gym", (-1, 0))
go(-1, 0, 1, 120)
check(tuple(g.current_state.player) == HG.PADS[0][1], f"a lily pad floats you from the entrance to Doyle's dock ({tuple(g.current_state.player)})")
check(HG.end(story, 0) == "B", "...and the pad stays over there")
_seen = set()
for i in range(len(HG.PADS)):
    _seen |= {i}
check(len(HG.PADS) == 14 and all(a != b for a, b in HG.PADS), "14 lily pads between the docks")
gr = hu["rooms"]["gym"]
check(len([1 for sc in gr.get("scenes") or [] if (sc.get("event") or {}).get("world") == "humilau_gym"]) == 28, "a ride on each pad's two ends")

print("3) the Wave Badge -> Route 22 -> Seaside Cave")
flags["b2_wave_badge"] = True
st = town("HUMILAU_CITY", (15, 48), face=(0, -1))
go(0, -1, 1, 60); settle(1500)
check(flags.get("b2_humilau_after") and "Route 22" in heard(), "outside the Gym: Hugh and Marlon, then Route 22")
check("b2_m41" in mains(), f"the Journal: Route 22 ({mains()})")
ds = walked("UNOVA_ROUTE_22", (25, 10))
go(-1, 0, 2, 120); settle(1500)
check(flags.get("b2_colress_mchn") and "Colress Machine" in heard(), "Colress and Terrakion: the Colress Machine")
r22 = tmaps["UNOVA_ROUTE_22"]
ter = [c for o in r22["people"] for c in _opts(o) if isinstance(c, dict) and c.get("action") == "BOSS"]
check(ter and ter[0]["boss"]["id"] == 639 and ter[0]["boss"]["level"] == 45, "Terrakion: a Lv 45 boss on Route 22")
check("b2_m42" in mains(), f"the Journal: Seaside Cave ({mains()})")
sc = tmaps["SEASIDE_CAVE"]
cr = [c for o in sc["people"] for c in _opts(o) if isinstance(c, dict) and c.get("action") == "BOSS"]
check(cr and cr[0]["boss"]["id"] == 558 and cr[0]["condition"] == ["b2_colress_mchn", "not:b2_seaside_crustle"],
      "the big boulder: a Crustle, woken with the Colress Machine")
rk = [c for o in sc["people"] for c in _opts(o) if isinstance(c, dict) and c.get("text") == "Black Belt Rocky"]
check(rk and rk[0]["event"]["battle"]["team"] == [524, 524, 524, 524], "Black Belt Rocky and his four Roggenrola guard the bay exit")
bay = tmaps["UNDELLA_BAY"]
check(any(b.get("until", {}).get("flag_condition") == "b2_seaside_rocky" for b in bay.get("barred") or []),
      "Undella Bay's cave mouth opens once Rocky's beaten")
flags["b2_seaside_crustle"] = True
check("b2_m43" in mains(), f"the Journal: the ship off Route 21 ({mains()})")

for f_ in fails:
    print("  -", f_)
print(f"##### {len(fails)} failures")
