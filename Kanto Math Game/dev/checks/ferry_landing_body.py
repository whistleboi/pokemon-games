# Off a boat at the harbour, even where there's no boat back the same way (Kanto 11-23: FireRed's Seagallop from Cinnabar
# to One Island is one way, so you landed outside One Island's Center and Bill's welcome at the harbour never played).
#   bash dev/checks/run.sh ferry_landing
import pygame
from src.states.overworld import CityState

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True
story.enter_region("KANTO")


def land(came):
    story.current_area_key = "ONE_ISLAND"
    story.last_area_key = came
    story.story_flags["visited_ONE_ISLAND"] = True
    g.walk_town_pos = g.walk_town_room = None
    t = CityState(g)
    door = min((d for d, k in t.doors.items() if k == "harbor"), key=lambda d: abs(d[0] - t.player[0]) + abs(d[1] - t.player[1]), default=None)
    center = next((d for d, k in t.doors.items() if k == "center"), None)
    return t, door, center


for came in ("VERMILLION_CITY", "CINNABAR_ISLAND"):
    t, harbor, center = land(came)
    near = harbor is not None and abs(harbor[0] - t.player[0]) + abs(harbor[1] - t.player[1]) <= 1
    check(near, f"from {came}: off the boat at One Island's harbour {harbor} (standing at {tuple(t.player)}; the Center's door {center})")
print(f"##### {len(fails)} failures")
