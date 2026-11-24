# The Journal marker reads a map's ways out exactly as the walker does (Unova 11-23: Castelia's streets and piers use the
# extra exit letters g h i j k l q t y z, which the marker skipped, so no gold marker at Burgh's Gym or the north gate).
#   bash dev/checks/run.sh guide_exits
from src.states.overworld import CityState

fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.dungeon_routes = True; g.walk_towns = True; g.live3d_headless = True
story.enter_region("UNOVA")
for area in ("CASTELIA_CITY", "NIMBASA_CITY"):
    story.current_area_key, story.last_area_key = area, None
    story.story_flags["visited_" + area] = True
    g.walk_town_pos = g.walk_town_room = None
    t = CityState(g)
    if not hasattr(t, "exits"):
        print(f"   ({area} isn't walked on this branch yet)")
        continue
    walker = {tg for tg in t.exits.values()}
    marker = set(t._guide_part(None)["exits"].values())
    check(walker <= marker, f"{area}: the marker knows every way out the walker does (missing {sorted(walker - marker)})")
g.walk_town_pos = g.walk_town_room = None
print(f"##### {fails} failures")
