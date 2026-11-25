# Unova batch 12b (11-25): Black 2's north after the title - Tubeline Bridge (the Soundproof woman, Flame Charge, the thirsty
# runner), Route 8 (the rock giver, a Hip Wader), the Moor of Icirrus, Icirrus City (the Shadow Triad's three battles, Aha's
# quiz, the Fan Club, the Ore Collector) and Dragonspiral Tower (its seven floors; the Dark Stone / Light Stone wakes at the top).
#   bash dev/checks/run.sh unova_b12b
import json
from src.states.overworld import CityState, PlayState

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.player_character = "nate"
flags = story.story_flags
flags["unova_version"] = "BLACK_2"; story.starting_region = "UNOVA"
story.badges["UNOVA"] = ["BASIC", "TOXIC", "INSECT", "BOLT", "QUAKE", "JET", "LEGEND", "WAVE"]
for k in ("beat_unova_champion", "b2_hall_of_fame", "move_offer_unova", "visited_ASPERTIA_CITY"):
    flags[k] = True
said = []
tmaps = json.load(open("assets/town_maps.json", encoding="utf-8"))
prog = json.load(open("assets/unova_area_data.json", encoding="utf-8"))
SP = prog["STORY_PROGRESSION"]
exec(open("dev/checks/unova_lib.py", encoding="utf-8").read())
BATTLES = ("TrainerIntroState", "TrainerBattleState", "DoubleBattleState", "GymBattleState", "BattleState")

print("1) the places and how they join")
tl, r8, moor, ic, dt = (tmaps[k] for k in ("TUBELINE_BRIDGE", "UNOVA_ROUTE_8", "MOOR_OF_ICIRRUS", "ICIRRUS_CITY", "DRAGONSPIRAL_TOWER"))
r9 = tmaps["UNOVA_ROUTE_9"]
check(any(r.get("exits", {}).get("<") == "TUBELINE_BRIDGE" for r in r9.get("rooms", {}).values()), "Route 9's gate leads onto Tubeline Bridge")
check(set(tl["exits"].values()) == {"UNOVA_ROUTE_9", "UNOVA_ROUTE_8"}, "Tubeline Bridge: Route 9 to Route 8")
check(r8["rooms"]["gate"]["exits"].get(">") == "TUBELINE_BRIDGE" and set(r8["exits"].values()) == {"ICIRRUS_CITY", "MOOR_OF_ICIRRUS"},
      "Route 8: its gate to the bridge; Icirrus, the Moor")
check(set(moor["exits"].values()) == {"UNOVA_ROUTE_8"}, "the Moor of Icirrus: back to Route 8")
check(r8["edge_to"].get("16,31") == [50, 33] and ic["edge_to"].get("50,32") == [16, 30], "Route 8's south road and Icirrus meet tile for tile")
check({"DRAGONSPIRAL_TOWER", "UNOVA_ROUTE_8", "TWIST_MOUNTAIN"} <= set(ic["exits"].values())
      and {"gym", "center", "aha", "fan_club"} <= set(ic["rooms"]), "Icirrus: the tower, Route 8, Twist Mountain; the old Gym, Center, Aha's, the Fan Club")
check({"grounds", "f1", "f2", "f3", "f4", "f5", "f6", "top"} <= set(dt["rooms"]), "Dragonspiral Tower: the grounds and seven floors")
for k in ("UNOVA_ROUTE_8", "MOOR_OF_ICIRRUS"):
    pool = {t["name"] for t in SP[k]["trainer_pool"]}
    check(SP[k].get("wild_tables") and set(tmaps[k].get("trainer_spots", [])) == pool, f"{k}: Black 2's wild tables and trainers ({len(pool)})")
check(not SP["ICIRRUS_CITY"].get("on_enter_event") and not SP["UNOVA_ROUTE_8"].get("on_enter_event"),
      "BW's menu-era scene battles are off (saved for 12c)")

print("2) the Shadow Triad")
for i in (1, 2, 3):
    flags.pop("b2_triad_%d" % i, None)
st = town("ICIRRUS_CITY", (58, 35))
got = []
for i, label in enumerate(("Shadow Triad", "Shadow Triad ", "Shadow Triad  ")):
    st = g.current_state if isinstance(g.current_state, CityState) else town("ICIRRUS_CITY", (58, 35))
    talk(st, label)
    cur = until(BATTLES, 800)
    got.append((type(cur).__name__, team_of(cur)[:1]))
    if type(cur).__name__ in BATTLES:
        win(cur)
    settle(300)
check([t for _n, t in got] == [[(625, 65)], [(625, 65)], [(354, 67)]] and all(flags.get("b2_triad_%d" % i) for i in (1, 2, 3)),
      f"three battles in turn: single, then the triple and rotation as doubles ({got})")

print("3) Tubeline Bridge")
tms = story.inventory.get("TM038", 0)
flags.pop("b2_tl_tm038", None)
ds = walked("TUBELINE_BRIDGE", (17, 103))
bg = next((m for m in ds.run.floor.movers if m.kind == "figure" and isinstance(m.payload, dict) and m.payload.get("text") == "Battle Girl on the bridge"), None)
if bg:
    ds._get_route_callback(bg.payload)(); settle(200)
check(bg is not None and story.inventory.get("TM038", 0) == tms + 1, "the Battle Girl's TM038 Flame Charge")
sky = tmaps["SKYARROW_BRIDGE"]
runner = next(o for o in sky["people"] for o in (o if isinstance(o, list) else [o]) if (o.get("event") or {}).get("runner") == "b2_sky_runner")
check("b2_tubeline_runner" in runner["event"]["chain"], "Skyarrow's runner counts the Tubeline Bridge runner too")

print("4) Dragonspiral Tower's top")
top = dt["rooms"]["top"]
boss = [o for p in top["people"] for o in (p if isinstance(p, list) else [p]) if o.get("action") == "BOSS"]
check(sorted((o["boss"]["id"], o["boss"]["level"]) for o in boss) == [(643, 70), (644, 70)] and all("b2_n_beaten" in o["condition"] for o in boss),
      "the Dark Stone / Light Stone wakes as Zekrom / Reshiram, Lv 70, once N's given it")

for f_ in fails:
    print("  -", f_)
print(f"##### {len(fails)} failures")
