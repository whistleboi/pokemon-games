# Rooms (Unova's cleanups, 11-23):
# - a dark room's "lit" sections: rectangles that light up once their flag is set (Black 2's Nimbasa Gym catwalk); a dark
#   room without them (Dewford Gym) lights as before, a wider circle per flag;
# - a room's "landings" (a platform reached only by a scene's ride, Nimbasa's roller coaster): back in the room after a
#   battle, you keep your spot there, not the entrance.
#   bash dev/checks/run.sh room_light
import pygame
from src.states.overworld import CityState

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


def settle(n=40):
    for _ in range(n):
        st = g.current_state
        if getattr(st, "npc_active", False):
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
            st.dialogue_box.advance()
        st.update(); st.draw()


g.dungeon_routes = True; g.walk_towns = True; g.live3d_headless = True
story.enter_region("HOENN")
_saved = dict(story.story_flags)
story.story_flags["hoenn_version"] = "OMEGA_RUBY"   # (past the version pick)
story.current_area_key = "DEWFORD_TOWN"; story.story_flags["visited_DEWFORD_TOWN"] = True
g.walk_town_pos = None; g.walk_town_room = ("DEWFORD_TOWN", "gym")
g.change_state(CityState(g)); settle()
t = g.current_state
if getattr(t, "room", None) != "gym" and hasattr(t, "_go"):
    t._go("gym", None); settle()
t = g.current_state
check(getattr(t, "room", None) == "gym" and bool(getattr(t, "dark", None)), "Dewford Gym: a dark room")

print("1) a dark room without lit sections: as before")
for f in t.dark.get("flags", []):
    story.story_flags.pop(f, None)
check(t.light_radius() == t.dark["radius"][0] and t._lit_sections() == [], f"no trainer beaten: radius {t.light_radius()}")
story.story_flags[t.dark["flags"][0]] = True
check(t.light_radius() == t.dark["radius"][1], f"one beaten: wider ({t.light_radius()})")

print("2) lit sections")
_dark = t.dark
x, y = t.player
t.dark = {"flags": ["zz_lit_a", "zz_lit_b"], "radius": [1.5, 4],
          "lit": [[x, y - 3, x + 2, y - 1, None], [x - 3, y - 3, x - 1, y, "zz_lit_a"]]}
story.story_flags.pop("zz_lit_a", None); story.story_flags.pop("zz_lit_b", None)
check(t.light_radius() == 1.5, f"with lit sections the circle stays the first radius ({t.light_radius()})")
check(t._lit_sections() == [(x, y - 3, x + 2, y - 1)], f"the always-lit section only ({t._lit_sections()})")
story.story_flags["zz_lit_a"] = True
check(len(t._lit_sections()) == 2 and t.light_radius() == 1.5, f"its trainer beaten: the second section lights up ({len(t._lit_sections())})")
try:
    settle(3)
    check(True, "drawn with lit sections (no error)")
except Exception as e:
    check(False, f"drawing a lit room: {type(e).__name__} {e}")
story.story_flags["zz_lit_b"] = True
check(t.light_radius() is None, "every flag set: fully lit")
t.dark = _dark

print("3) a ride's landing counts as a place you can stay")
_ex, _dr, _tm = t.exits, t.doors, t.town_map
t.exits, t.doors = {}, {}
spot = tuple(t.player)
check(not t._reaches_out(spot), "with no way out at all, a spot doesn't reach out")
_room = dict((_tm.get("rooms") or {}).get("gym") or {})
_room["landings"] = [list(spot)]
t.town_map = dict(_tm, rooms=dict(_tm.get("rooms") or {}, gym=_room))
check(t._reaches_out(spot), "standing on a landing: you stay there")
nb = next((q for q in ((spot[0] + 1, spot[1]), (spot[0] - 1, spot[1]), (spot[0], spot[1] + 1), (spot[0], spot[1] - 1)) if t._open(q)), None)
if nb:
    check(t._reaches_out(nb), "a spot that walks to a landing: you stay there too")
t.exits, t.doors, t.town_map = _ex, _dr, _tm

print("4) a room with nobody in it still plays its scenes (Black 2's Battle Subway car: each Trainer walks in by a scene)")
from src.dungeon import npc as _npc
_ppl, _mo, _sc = t.people, t.motions, t.scenes
t.people, t.motions = {}, {}
story.story_flags.pop("zz_empty_scene", None)
t.scenes = _npc.Scenes([{"trigger": "enter", "flag": "zz_empty_scene", "cast": [], "lines": ["The doors slide open."]}], t)
for _ in range(40):
    if story.story_flags.get("zz_empty_scene"):
        break
    t.update()
    if getattr(t, "dialogue_box", None) is not None and getattr(t.dialogue_box, "visible", False):
        t.dialogue_box.advance()
check(bool(story.story_flags.get("zz_empty_scene")), "an 'enter' scene ran with no people in the room")
t.people, t.motions, t.scenes = _ppl, _mo, _sc

story.story_flags = _saved
g.walk_town_pos = g.walk_town_room = None
print(f"##### {len(fails)} failures")
