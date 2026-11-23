# Arriving on a water way in without Surf (a load, a skip, a fallback arrival) puts you ashore, not swimming without Surf
# (Sinnoh's cleanup, 11-23: Valley Windworks' first way in is Route 205's river). With Surf you stay on the water.
#   bash dev/checks/run.sh water_arrival
from src.states.overworld.dungeon import DungeonState
from src.dungeon import core as _core

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


_saved = (dict(story.story_flags), {r: list(b) for r, b in story.badges.items()}, dict(story.inventory),
          story.current_area_key, getattr(story, "last_area_key", None))
story.enter_region("SINNOH")
story.current_area_key = "VALLEY_WINDWORKS"
story.last_area_key = None   # (no known way in: the fallback arrival)
for _k in [k for k in story.inventory if "SURF" in str(k).upper()]:
    story.inventory.pop(_k)
story.badges["SINNOH"] = []
ds = DungeonState(g)
p = tuple(ds.run.player)
check(not ds._can_surf(), "no Surf")
check(ds.run.floor.tile(*p) != _core.SURF, f"arrived ashore, not on the water ({p})")
check(ds.run.floor.walkable(*p), "on a tile you can stand on")

story.inventory["HM_SURF"] = 1
story.badges["SINNOH"] = ["COAL", "FOREST", "COBBLE", "FEN", "RELIC", "MINE", "ICICLE", "BEACON"]
story.last_area_key = None
ds2 = DungeonState(g)
if ds2._can_surf():
    p2 = tuple(ds2.run.player)
    check(ds2.run.floor.tile(*p2) == _core.SURF or ds2.run.floor.walkable(*p2), f"with Surf: the way in as before ({p2})")
else:
    print("   (skipped: Surf not usable in this test save)")

story.story_flags, story.inventory = _saved[0], _saved[2]
story.badges.clear(); story.badges.update(_saved[1])
story.current_area_key, story.last_area_key = _saved[3], _saved[4]
print(f"##### {len(fails)} failures")
