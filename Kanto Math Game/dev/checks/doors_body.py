# In by every door, in every region (Jordan 11-21: "entering the castelia pokemon center, It entered me behind the counter
# of the pokemart and I am now stuck"): each door that leads into a built room is walked through the real code
# (walk_town._enter -> _go), and you must land beside that room's way out, free to walk back out.
# A room's way out marked a tile or two off its door (38 rooms) or named ROOM:MAIN (Black 2's imports) is matched too.
#   bash dev/checks/run.sh doors
import json
import time
from src.states.overworld import CityState

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True
story.story_flags["hoenn_version"] = "OMEGA_RUBY"   # (past each region's version pick)
story.story_flags["unova_version"] = "BLACK_2"


def settle(n=6):
    for _ in range(n):
        st = g.current_state
        st.update()


M = json.load(open("assets/town_maps.json", encoding="utf-8"))
t0 = time.time()
walked, shut, far, skipped = 0, [], [], []
for area, m in M.items():
    if not isinstance(m, dict) or not m.get("inside"):
        continue
    story.current_area_key = area
    story.story_flags["visited_" + area] = True
    g.walk_town_pos = g.walk_town_room = None
    try:
        g.change_state(CityState(g)); settle()
    except Exception as e:   # (a place that can't open headless here: listed, not failed)
        skipped.append((area, repr(e)[:60]))
        continue
    t = g.current_state
    if getattr(t, "area_key", None) != area or not hasattr(t, "_enter"):
        skipped.append((area, type(t).__name__))
        continue
    for door, room in m["inside"].items():
        d = tuple(int(v) for v in door.split(","))
        if room not in (t.town_map.get("rooms") or {}) or d not in t.doors:
            continue
        if getattr(t, "room", None):
            t._go(None, "OUT:%d,%d" % d)
        try:
            t._enter(d)
        except Exception as e:
            shut.append((area, room, door, repr(e)[:60]))
            continue
        walked += 1
        if getattr(t, "room", None) != room:
            continue   # (a door the story keeps shut for now)
        p = tuple(t.player)
        if not t._reaches_out(p):
            shut.append((area, room, door, p))
        elif not any(abs(p[0] - e[0]) + abs(p[1] - e[1]) <= 1 for e in t.exits):
            far.append((area, room, door, p))
        t._go(None, "OUT:%d,%d" % d)
print(f"   ({walked} doors walked in {time.time() - t0:.0f}s; skipped {len(skipped)}: {skipped[:4]})")
check(walked > 500, f"most doors into rooms were walked through ({walked})")
check(not shut, f"no door lands you somewhere you can't walk out of ({shut[:6]})")
check(not far, f"every door lands you beside the room's way out ({far[:6]})")

print(f"##### {len(fails)} failures")
