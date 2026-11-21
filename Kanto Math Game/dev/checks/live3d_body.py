# The live 3D camera (Jordan 11-20, Castelia: "the camera does not tilt" -> "Live 3D camera"; "follow the curve"):
# Black 2's models drawn every frame from its own camera for each place, following you; on the avenue the camera
# circles the city's middle and your keys follow the road's bend. Needs moderngl and an OpenGL 3.3 card: without them
# this suite says so and stops (the game then keeps its baked pictures).
#   bash dev/checks/run.sh live3d
import json
from src.states.overworld import CityState
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.dungeon import live3d

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.live3d_headless = True
story.story_flags["unova_version"] = "BLACK_2"
story.starting_region = "UNOVA"
for _a in ("CASTELIA_CITY",):
    story.story_flags["visited_" + _a] = True


def settle(n=60):
    for _ in range(n):
        st = g.current_state
        if getattr(st, "npc_active", False):
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
            st.dialogue_box.advance()
        st.update(); st.draw()


def town(room=None, at=None):
    g.story_manager.current_area_key = "CASTELIA_CITY"
    g.walk_town_pos = ("CASTELIA_CITY", at, (0, 1)) if at else None
    g.walk_town_room = ("CASTELIA_CITY", room) if room else None
    g.change_state(CityState(g)); settle()
    t = g.current_state
    if room and getattr(t, "room", None) != room:
        t._go(room, None); settle()
    if at:
        t.player = t.anim_from = t.partner = t.partner_from = at; t._remember(); t._live_yaw = None; settle(5)
    return g.current_state


def walk(dx, dy, n):
    out = []
    for _ in range(n):
        settle(1); g.current_state.step(dx, dy, by_key=True); settle(16)
        out.append(tuple(g.current_state.player))
    return out


print("1) the scenes: Black 2's models and cameras, exported")
if not live3d.available(g):
    print("   (no moderngl / OpenGL 3.3 card here: the live camera is off, the baked pictures stay)")
    print(f"##### {len(fails)} failures")
    raise SystemExit
for z in (28, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40):
    check(live3d.has_scene(g, z), f"zone {z}: its 3D scene is in assets/b2_3d")
sc = live3d.scene(g, 31)
check(sc is not None and len(sc.parts) > 20 and sc.cam is not None and abs(float(sc.cam[0]) - 38.0) < 0.5,
      f"Gym Street: its models and Black 2's camera 8 (38 degrees) ({None if sc is None else [round(float(v), 1) for v in sc.cam]})")

import numpy as np
sc = live3d.scene(g, 30)   # (the plaza: what the export left out, put back, 11-21)
kinds = [k for k, _t, _v in sc.parts]
check(kinds.count(3) >= 5, f"the plaza's lamp glows are light sheets, drawn faint ({kinds.count(3)})")
_c = [float(v) for v in sc.cam]
_img = sc.render((480, 360), live3d.follow(21.5, -0.3, 30.5, _c[0], _c[1], 0, _c[2]))
_px = pygame.surfarray.array3d(_img).reshape(-1, 3)
check(not np.all(_px == live3d.KEY, axis=1).any(), "no atlas key colour (magenta) on screen")
_cream = (_px[:, 0] > 245) & (_px[:, 1] > 236) & (_px[:, 2] > 185) & (_px[:, 2] < 210)
check(_cream.mean() < 0.01, f"no solid cream wedges where the lamps' glows are ({_cream.mean():.3f} of the picture)")

print("2) a street: drawn live, the camera following you")
t = town("gym_street", (21, 50))
check(isinstance(t, _WTS) and t._live() is not None, "Gym Street is drawn live")
c1 = t._live_cam()
walk(0, 1, 4)
c2 = g.current_state._live_cam()
check(abs(c2["eye"][2] - c1["eye"][2] - 4) < 0.6 and abs(c2["eye"][0] - c1["eye"][0]) < 0.01,
      f"walking south, the camera moves south with you ({c1['eye']} -> {c2['eye']})")
pygame.image.save(pygame.display.get_surface(), f"{S}/live3d_01_street.png")
v = t._view()
tile = t._tile_at((v.centerx, v.centery + 120))
check(abs(tile[0] - t.player[0]) <= 3 and tile[1] > t.player[1], f"a tap below you picks a tile below you ({tile}, you at {t.player})")

print("3) the avenue: the camera circles the city's middle; your keys follow the road's bend")
t = town(None, (64, 67))
y1 = (settle(40), g.current_state._live_yaw)[1]
path = walk(-1, 0, 36)
y2 = (settle(60), g.current_state._live_yaw)[1]
check(path[-1][0] <= 33 and path[-1][1] < 74 and any(p[1] == 74 for p in path),
      f"holding left from the Pokemon Center: round the south bend and up the west side ({path[0]} .. {path[-1]})")
check(y1 is not None and y2 is not None and y1 > 20 and y2 < -25, f"the camera swung round with you (from the south-east bend to the south-west) ({y1:.0f} -> {y2:.0f} degrees)")
pygame.image.save(pygame.display.get_surface(), f"{S}/live3d_02_avenue.png")
up = walk(0, -1, 2)
check(up[0][0] > path[-1][0] or up[0][1] < path[-1][1], f"up: in toward the city ({path[-1]} -> {up})")

print("3b) on the bend: you face the key you press; others turn with the camera; taps aren't turned (Jordan 11-21)")
t = town(None, (31, 70)); settle(60)
yaw = t._live_yaw
for key in ((-1, 0), (0, -1), (1, 0), (0, 1)):
    settle(20); t = g.current_state; t.step(*key, by_key=True); settle(4)
    check(t._live_me_face() == key, f"key {key} at the west bend (camera {yaw:.0f} degrees): drawn facing {t._live_me_face()}, the map's facing {tuple(t.facing)}")
settle(20)
check(t._live_face((0, -1)) == (0, -1) or abs(yaw) < 45, "the map's north, turned by under 45 degrees, still looks up")
t = town(None, (31, 70)); settle(60)
start = tuple(t.player)
_open = [(start[0] + dx, start[1] + dy) for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)) if t._open((start[0] + dx, start[1] + dy))]
goal = _open[0]
t.walk_goal = goal; settle(30)
check(tuple(g.current_state.player) == goal, f"a tapped tile next to you, on the bend: you step straight onto it ({start} -> {goal}: at {tuple(g.current_state.player)})")
t = town(None, (31, 70)); settle(60)
far = (30, 65)
t.walk_goal = far; settle(400)
check(tuple(g.current_state.player) == far, f"a tapped tile up the west side: you walk there ({far}: at {tuple(g.current_state.player)})")

print("4) a scene's zoom, shadows, the Options switch, no numpy (11-21)")
t = town("gym_street", (21, 50))
d0 = abs(t._live_cam()["eye"][1] - t._live_cam()["target"][1])
t.npc_zoom(1.25); settle(120)
d1 = abs(t._live_cam()["eye"][1] - t._live_cam()["target"][1])
check(d1 < d0 * 0.9, f"a scene's zoom moves the live camera in ({d0:.1f} -> {d1:.1f} tiles up)")
t.npc_zoom(None); settle(120)
check(getattr(t, "shadows", False), "an oval under everyone's feet, in the scene too")
from src.core import settings
settings.put(g, "live3d", False); settle(3)
check(t._live() is None, "Options, 3D camera: Flat draws the baked pictures")
settings.put(g, "live3d", True)
from src.states.systems.options import OptionsState
o = OptionsState(g, t, lambda: None)
o.tab = o.tabs.index("SCREEN & SOUND")
check(any(r[0] == "3D camera" for r in o.rows()), "Options, SCREEN & SOUND: a 3D camera row")
_np, live3d.np = live3d.np, None   # (a Python without numpy: flat, never a crash)
t = town("plaza", (21, 30))
check(t.room == "plaza" and t._live() is None, "no numpy: the plaza loads and draws flat")
live3d.np = _np
t = town("prime_pier", (16, 20)); settle(5)
pygame.image.save(pygame.display.get_surface(), f"{S}/live3d_03_pier.png")
t = town("plaza", (21, 30)); settle(5)
pygame.image.save(pygame.display.get_surface(), f"{S}/live3d_04_plaza.png")

print("5) off: the baked picture")
g.live3d = False
t = town("gym_street", (21, 50))
check(t._live() is None, "with the live camera off, the baked picture is drawn")
g.live3d = True
print(f"##### {len(fails)} failures")
