# Saves keep where you stand (Jordan 11-20: "the game always stores your location, either in a building, route, town, or
# any other map"): save on a town's map, in one of its rooms, on a route's map and on a cave's lower floor, then Continue:
# back on that tile (src/core/game.py update_save_data "spot" / _restore_spot; walk_town._remember, dungeon update).
#   bash dev/checks/run.sh savespot
import copy
from src.states.overworld import CityState, PlayState
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.states.overworld.dungeon import DungeonState as _DS

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True
story.story_flags["unova_version"] = "BLACK_2"   # (Castelia: past the version pick)
story.starting_region = "UNOVA"; story.story_flags["received_starter_unova"] = True
for _a in ("CASTELIA_CITY", "CASTELIA_SEWERS", "MT_MOON"):
    story.story_flags["visited_" + _a] = True


def settle(n=80):
    for _ in range(n):
        st = g.current_state
        if getattr(st, "npc_active", False):
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
            st.dialogue_box.advance()
        st.update(); st.draw()


def go_town(area, room=None):
    g.story_manager.current_area_key = area
    g.walk_town_pos = None
    g.walk_town_room = (area, room) if room else None
    g.change_state(CityState(g)); settle()
    t = g.current_state
    if room and getattr(t, "room", None) != room:
        t._go(room, None); settle()
    return g.current_state


def go_map(area, came):
    g.story_manager.current_area_key, g.story_manager.last_area_key = area, came   # (the live story: a load makes a new one)
    g.change_state(PlayState(g)); settle()
    return g.current_state


def save_and_continue():
    """Save (the game's own save data), wander off to another place, then load that save as Continue does."""
    g.update_save_data()
    saved = copy.deepcopy(g.data.data["story"])
    g.story_manager.current_area_key = "PALLET_TOWN"
    g.last_spot = None
    g.walk_town_pos = g.walk_town_room = g.arrive_floor = None
    g.data.data["story"] = saved
    g.load_game_data(); settle()
    return saved.get("spot"), g.current_state


def open_tile(st, near):
    """An open tile near `near` (towns: rows; maps: the floor)."""
    best = None
    for dy in range(-6, 7):
        for dx in range(-6, 7):
            t = (near[0] + dx, near[1] + dy)
            if isinstance(st, _WTS):
                ok = st._open(t) and t not in st.exits
            else:
                ok = st.run.floor.walkable(*t) and t not in st.run.floor.exits
            if ok and (best is None or abs(dx) + abs(dy) < abs(best[0] - near[0]) + abs(best[1] - near[1])):
                best = t
    return best


print("1) a town's own map")
t = go_town("CASTELIA_CITY")
spot = open_tile(t, (60, 60))
t.player = t.anim_from = spot; t.facing = (1, 0); t._remember()
s, st = save_and_continue()
check(s and s.get("kind") == "town" and not s.get("room"), f"the save holds the spot ({s})")
check(isinstance(st, _WTS) and st.area_key == "CASTELIA_CITY" and getattr(st, "room", None) is None and tuple(st.player) == spot,
      f"Continue: back on that tile of the avenue ({getattr(st, 'room', None)}, {getattr(st, 'player', None)} vs {spot})")

print("2) inside a building (a town's room)")
t = go_town("CASTELIA_CITY", "battle_co")
spot = open_tile(t, (8, 6))
t.player = t.anim_from = spot; t.facing = (0, -1); t._remember()
s, st = save_and_continue()
check(isinstance(st, _WTS) and getattr(st, "room", None) == "battle_co" and tuple(st.player) == spot and tuple(st.facing) == (0, -1),
      f"Continue: back inside the Battle Company, same tile, same way ({getattr(st, 'room', None)}, {getattr(st, 'player', None)})")
t = go_town("CASTELIA_CITY", "gym_20")
spot = (20, 7)
t.player = t.anim_from = spot; t._remember()
s, st = save_and_continue()
check(getattr(st, "room", None) == "gym_20" and tuple(st.player) == spot, f"Continue: on Burgh's Gym's top floor ({getattr(st, 'room', None)}, {getattr(st, 'player', None)})")

print("3) a route's map")
d = go_map("CASTELIA_SEWERS", "CASTELIA_CITY")
spot = open_tile(d, (40, 20))
d.run.player = d.anim_from = spot; settle(2)
s, st = save_and_continue()
check(s and s.get("kind") == "map", f"the save holds the map spot ({s})")
check(isinstance(st, _DS) and st.area_key == "CASTELIA_SEWERS" and tuple(st.run.player) == spot,
      f"Continue: back in the Sewers on that tile ({getattr(getattr(st, 'run', None), 'player', None)} vs {spot})")

print("4) a cave's lower floor")
d = go_map("MT_MOON", "KANTO_ROUTE_3")
if d.run.n_floors > 1:
    d._descend() if hasattr(d, "_descend") else None
    settle(5)
fl = d.run.index
spot = open_tile(d, (d.run.floor.w // 2, d.run.floor.h // 2))
d.run.player = d.anim_from = spot; settle(2)
s, st = save_and_continue()
check(fl > 0, f"down a floor first ({fl})")
check(isinstance(st, _DS) and st.run.index == fl and tuple(st.run.player) == spot,
      f"Continue: back on Mt. Moon floor {fl}, same tile ({getattr(getattr(st, 'run', None), 'index', None)}, {getattr(getattr(st, 'run', None), 'player', None)} vs {spot})")

print("5) an older save with no spot: the usual arrival")
g.update_save_data()
saved = copy.deepcopy(g.data.data["story"]); saved.pop("spot", None)
g.last_spot = None
g.data.data["story"] = saved
check(g.load_game_data() and g.arrive_floor is None and g.walk_town_pos is None, "no spot: it loads as before")
print(f"##### {len(fails)} failures")
