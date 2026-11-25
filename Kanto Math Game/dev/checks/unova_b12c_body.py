# Unova batch 12c (11-25): Unova two years ago on Pokemon White's own maps (questions/UNOVA.md 19, 20) - the Memory Link from
# today's Juniper to the past's Nuvema (White's 389-396, you as yourself with your own team) and back; Fly stays in its era;
# the past's places draw White's own 3D scenes (assets/w1_3d).
#   bash dev/checks/run.sh unova_b12c
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
for k in ("beat_unova_champion", "b2_hall_of_fame", "move_offer_unova", "visited_ASPERTIA_CITY", "visited_NUVEMA_TOWN"):
    flags[k] = True
said = []
tmaps = json.load(open("assets/town_maps.json", encoding="utf-8"))
prog = json.load(open("assets/unova_area_data.json", encoding="utf-8"))
SP = prog["STORY_PROGRESSION"]
exec(open("dev/checks/unova_lib.py", encoding="utf-8").read())

print("1) the past's Nuvema, from Pokemon White's file")
pn = tmaps["PAST_NUVEMA_TOWN"]
check(SP["PAST_NUVEMA_TOWN"].get("era") == "past" and pn["roofs"]["_picture"]["f"].startswith("w1_ground/"),
      "PAST_NUVEMA_TOWN: an area of the past, drawn from White's maps")
check({"hero", "hero_2f", "bianca", "cheren", "lab"} <= set(pn["rooms"]), "the hero's house, Bianca's, Cheren's, Juniper's lab")
from src.dungeon import live3d
check(live3d.has_scene(g, 389, "w1") and live3d.has_scene(g, 389) and live3d.scene_of(g, "w1_ground/389.png") is not None
      and live3d.scene_of(g, "w1_ground/389.png") is not live3d.scene_of(g, "b2_ground/389.png"),
      "White's 3D scene for Nuvema, kept apart from Black 2's (same zone number)")

print("2) the Memory Link")
st = town("NUVEMA_TOWN", (6, 12), "lab")
talk(st, "Professor Juniper"); settle(400)
check(story.current_area_key == "PAST_NUVEMA_TOWN" and flags.get("unova_past"), f"today's Juniper sends you two years back ({story.current_area_key})")
cur = g.current_state
check(getattr(cur, "room", None) == "lab", "into the past's lab")
st = cur if isinstance(cur, CityState) else town("PAST_NUVEMA_TOWN", (6, 12), "lab")
talk(st, "Professor Juniper"); settle(400)
check(story.current_area_key == "NUVEMA_TOWN", f"the past's Juniper sends you back to today ({story.current_area_key})")

print("3) Fly keeps to its era")
from src.states.systems.fly_map import fly_ok
story.current_area_key = "NUVEMA_TOWN"
check(not fly_ok(g, "PAST_NUVEMA_TOWN") and fly_ok(g, "ASPERTIA_CITY"), "today: no flying into the past")
story.current_area_key = "PAST_NUVEMA_TOWN"
check(not fly_ok(g, "ASPERTIA_CITY"), "the past: no flying out to today")
story.current_area_key = "NUVEMA_TOWN"

print("4) the past from Nuvema to Striaton")
T = {k: tmaps[k] for k in ("PAST_NUVEMA_TOWN", "PAST_UNOVA_ROUTE_1", "PAST_ACCUMULA_TOWN", "PAST_UNOVA_ROUTE_2", "PAST_STRIATON_CITY",
                           "PAST_DREAMYARD", "PAST_DREAMYARD_B1F")}
check(T["PAST_NUVEMA_TOWN"]["exits"].get("^") == "PAST_UNOVA_ROUTE_1"
      and set(T["PAST_UNOVA_ROUTE_1"]["exits"].values()) == {"PAST_ACCUMULA_TOWN", "PAST_NUVEMA_TOWN"}
      and T["PAST_ACCUMULA_TOWN"]["rooms"]["gate_w"]["exits"].get("<") == "PAST_UNOVA_ROUTE_2"
      and set(T["PAST_UNOVA_ROUTE_2"]["exits"].values()) == {"PAST_STRIATON_CITY", "PAST_ACCUMULA_TOWN"}
      and {"PAST_UNOVA_ROUTE_2", "PAST_DREAMYARD"} <= set(T["PAST_STRIATON_CITY"]["exits"].values()),
      "Nuvema -> Route 1 -> Accumula -> its gate -> Route 2 -> Striaton -> the Dreamyard, all two years ago")
check(all(str(m["roofs"]["_picture"]["f"]).startswith("w1_ground/") and SP[k].get("era") == "past" for k, m in T.items()),
      "every one drawn from White's maps, an area of the past")
for k in ("PAST_UNOVA_ROUTE_1", "PAST_UNOVA_ROUTE_2", "PAST_DREAMYARD", "PAST_DREAMYARD_B1F"):
    pool = {t["name"] for t in SP[k]["trainer_pool"]}
    check(SP[k].get("wild_tables") and set(T[k].get("trainer_spots", [])) == pool, f"{k}: White's wild tables and trainers ({len(pool)})")
gyms = T["PAST_STRIATON_CITY"]["rooms"]["gym"]
check(len(gyms.get("barred") or []) == 3 and len(gyms.get("scenes") or []) == 9, "the Gym: three curtains, three switches before each")

print("5) the Trio Badge")
flags["starter_unova"] = 495
story.inventory["VS_SEEKER"] = 1   # (else the first trainer talk hands you one instead)
flags.pop("past_badge_trio", None)
st = town("PAST_STRIATON_CITY", (12, 5), "gym")
talk(st, "Chili")
cur = until(("TrainerIntroState", "TrainerBattleState", "GymBattleState", "BattleState"), 800)
t = team_of(cur)
check(t[:1] == [(631, 65)], f"Snivy first: Chili steps up, with Black 2's team ({t})")
if type(cur).__name__ in ("TrainerIntroState", "TrainerBattleState", "GymBattleState", "BattleState"):
    win(cur)
settle(300)
check(flags.get("past_badge_trio"), "the Trio Badge, a keepsake")

print("6) back from any Center two years ago")
st = town("PAST_STRIATON_CITY", (6, 17), "center")
talk(st, "Trainer with a C-Gear"); settle(400)
check(story.current_area_key == "NUVEMA_TOWN", f"the C-Gear's Memory Link takes you home ({story.current_area_key})")

print("7) Route 3 to Pinwheel Forest, two years ago")
T2 = {k: tmaps[k] for k in ("PAST_UNOVA_ROUTE_3", "PAST_WELLSPRING_CAVE", "PAST_WELLSPRING_CAVE_B1F", "PAST_NACRENE_CITY",
                            "PAST_PINWHEEL_FOREST_OUTSIDE", "PAST_PINWHEEL_FOREST")}
check(tmaps["PAST_STRIATON_CITY"]["exits"].get("^") == "PAST_UNOVA_ROUTE_3"
      and tmaps["PAST_STRIATON_CITY"]["gated_exits"].get("PAST_UNOVA_ROUTE_3") == ["past_badge_trio"],
      "Striaton's north road to Route 3, once you hold the Trio Badge")
check(set(T2["PAST_UNOVA_ROUTE_3"]["exits"].values()) == {"PAST_NACRENE_CITY", "PAST_STRIATON_CITY", "PAST_WELLSPRING_CAVE"}
      and T2["PAST_NACRENE_CITY"]["exits"].get("<") == "PAST_PINWHEEL_FOREST_OUTSIDE"
      and "PAST_UNOVA_ROUTE_3" in T2["PAST_NACRENE_CITY"]["exits"].values()
      and set(T2["PAST_PINWHEEL_FOREST_OUTSIDE"]["exits"].values()) == {"PAST_PINWHEEL_FOREST", "PAST_NACRENE_CITY"},
      "Route 3 -> Nacrene -> Pinwheel Forest; Wellspring Cave off Route 3")
for k in ("PAST_UNOVA_ROUTE_3", "PAST_WELLSPRING_CAVE_B1F", "PAST_PINWHEEL_FOREST_OUTSIDE", "PAST_PINWHEEL_FOREST"):
    pool = {t["name"] for t in SP[k]["trainer_pool"]}
    check(SP[k].get("wild_tables") and set(T2[k].get("trainer_spots", [])) == pool, f"{k}: White's wild tables and trainers ({len(pool)})")

print("8) Lenora and the Basic Badge")
nac = T2["PAST_NACRENE_CITY"]["rooms"]
check(nac["gym"].get("barred") and nac["gym"]["barred"][0]["until"]["condition"] == ["w1_nacrene_book"],
      "the library's stairs wait for the librarian's book riddle")
flags.pop("past_badge_basic", None)
flags["w1_nacrene_book"] = True
st = town("PAST_NACRENE_CITY", (5, 12), "office")
talk(st, "Lenora")
cur = until(("TrainerIntroState", "TrainerBattleState", "GymBattleState", "BattleState"), 800)
t = team_of(cur)
check(t == [(507, 18), (505, 20)], f"Lenora battles with White's own team ({t})")
if type(cur).__name__ in ("TrainerIntroState", "TrainerBattleState", "GymBattleState", "BattleState"):
    win(cur)
settle(300)
check(flags.get("past_badge_basic"), "the Basic Badge, a keepsake")

for f_ in fails:
    print("  -", f_)
print(f"##### {len(fails)} failures")
