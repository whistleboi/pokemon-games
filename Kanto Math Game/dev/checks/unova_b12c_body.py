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

for f_ in fails:
    print("  -", f_)
print(f"##### {len(fails)} failures")
