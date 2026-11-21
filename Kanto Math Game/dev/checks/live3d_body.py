# The live 3D camera (11-21, Jordan: "Live 3D camera"): Castelia's own Black 2 models drawn every frame from Black 2's
# camera (src/dungeon/live3d.py) instead of the baked pictures: people stood in the scene (buildings hide them), the
# camera on you at the zone's pitch and field of view, taps landing on the tile under the finger, the Options switch
# (SCREEN & SOUND: 3D camera) and the flat pictures whenever the card can't draw 3D. Needs moderngl; headless it draws
# through EGL. Screenshots: dev/checks/out/live3d_*.png.   bash dev/checks/run.sh live3d
import json
import numpy as np
from src.states.overworld import CityState
from src.states.overworld.walk_town import WalkTownState as _WTS, TILE
from src.core import settings
from src.dungeon import live3d

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.player_character = "nate"
g.live3d_headless = True   # (the checks draw through EGL: the game itself keeps headless runs flat)
flags = story.story_flags
for f in ("received_starter_unova", "b2_mom_talk", "b2_basic_badge", "b2_toxic_badge", "b2_virbank_dock", "b2_r20_hugh",
          "b2_pop_roxie_back", "b2_hugh_terminal", "b2_sailed_castelia", "b2_castelia_arrival", "b2_burgh_away"):
    flags[f] = True
story.story_flags["unova_version"] = "BLACK_2"
story.badges["UNOVA"] = ["BASIC", "TOXIC"]


def idle():
    st = g.current_state
    return isinstance(st, _WTS) and not st._busy() and st.anim == 0


def play(until, n=400):
    for _ in range(n):
        if until():
            return True
        st = g.current_state
        if getattr(st, "npc_active", False):
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        st.update(); st.draw()
    return until()


def town(room=None, at_=None):
    story.current_area_key = "CASTELIA_CITY"
    g.walk_town_pos = ("CASTELIA_CITY", at_, (0, 1)) if at_ else None
    g.walk_town_room = ("CASTELIA_CITY", room) if room else None
    g.change_state(CityState(g))
    play(idle)
    t = g.current_state
    if room and getattr(t, "room", None) != room:
        t._go(room, None); play(idle); t = g.current_state
    if at_:
        put(*at_)
    return g.current_state


def put(x, y, face=(0, 1)):
    st = g.current_state
    st.player = st.anim_from = (x, y)
    st.partner = st.partner_from = (x, y)
    st.anim = 0
    st.facing = face
    st._cam_ease = None; st._cam_cur = None; st._cam_ease_until = 0


def shot(name):
    g.current_state.draw()
    pygame.image.save(pygame.display.get_surface(), f"{S}/live3d_{name}.png")


try:
    import moderngl  # noqa: F401
    HAVE = True
except ImportError:
    HAVE = False
    print("   (moderngl isn't installed here: only the flat fallback is checked)")

print("1) the scenes: Black 2's models, with what the export left out put back")
for z in (28, 30, 34, 38):
    check(live3d.has_scene(g, z), f"zone {z}'s scene is there")
if HAVE:
    check(live3d.available(g), "a context to draw on (EGL when there's no display)")
    sc = live3d.scene(g, 30)
    kinds = [k for k, _t, _v in sc.parts]
    check(kinds.count(3) >= 5, f"the plaza's lamp glows are light sheets, drawn faint ({kinds.count(3)})")
    pitch, fov = live3d.zone_camera("assets/b2_3d/30.npz")
    img = sc.render((480, 360), live3d.framed((21.5, -0.3, 30.5), pitch, fov, 40, 360))
    px = pygame.surfarray.array3d(img).reshape(-1, 3)
    check(not np.all(px == live3d.KEY, axis=1).any(), "no atlas key colour (magenta) on screen")
    cream = (px[:, 0] > 245) & (px[:, 1] > 236) & (px[:, 2] > 185) & (px[:, 2] < 210)
    check(cream.mean() < 0.01, f"no solid cream wedges where the lamps' glows are ({cream.mean():.3f} of the picture)")

print("2) Castelia walked through the live camera")
t = town("plaza", (21, 30))
check(isinstance(t, _WTS) and t.room == "plaza" and (t.live or {}).get("zone") == 30, f"the plaza: zone 30's scene ({getattr(t, 'live', None)})")
if HAVE:
    play(lambda: False, 5)
    check(t._live() is not None and t._live_cam is not None, "drawn by the live camera")
    shot("01_plaza")
    view = t._view()
    me = t._me_drawn[0]
    check(abs(me.centerx - view.centerx) < TILE and abs(me.centery - view.centery) < TILE * 1.5,
          f"the camera on you: you're drawn mid-frame ({me.center} vs {view.center})")
    for dx, dy in ((0, 0), (2, 1), (-3, 2), (1, -2)):
        tile = (21 + dx, 30 + dy)
        sc_, size, cam, plane, (vx, vy) = t._live_cam
        p = sc_.project(size, cam, (tile[0] + 0.5, plane, tile[1] + 0.5))
        got = t._tile_at((vx + p[0], vy + p[1]))
        check(tuple(got) == tile, f"a tap on tile {tile} lands on it ({got})")
    play(idle, 600); before = t._me_drawn[0].center
    t.step(0, -1); play(idle, 60); play(lambda: False, 30)
    check(tuple(t.player) == (21, 29), f"a step north ({t.player})")
    check(abs(t._me_drawn[0].centery - before[1]) < TILE, f"the camera follows: you stay mid-frame ({before} -> {t._me_drawn[0].center})")
    def tile_px():
        sc_, size, cam, plane, _o = t._live_cam
        a = sc_.project(size, cam, (21.0, plane, 29.5)); b = sc_.project(size, cam, (22.0, plane, 29.5))
        return b[0] - a[0]
    w0 = tile_px()
    check(abs(w0 - TILE * t.zoom) < 2, f"a tile under you is the flat map's size ({w0:.1f} vs {TILE * t.zoom:.1f} px)")
    t.npc_zoom(1.25); play(lambda: abs(t.zoom - t.zoom_base * 1.25) < 0.01 or abs(t.zoom - 1.25) < 0.01, 200)
    w1 = tile_px()
    check(w1 > w0 * 1.15, f"a scene's zoom moves the live camera in ({w0:.1f} -> {w1:.1f} px a tile)")
    t.npc_zoom(None); play(lambda: False, 120)
    t._cam_focus = (21, 22); play(lambda: False, 120)
    sc_, size, cam, plane, _o = t._live_cam
    check(abs(cam["target"][2] - 22.5) < 1.0, f"a scene's pan swings the live camera there ({cam['target'][2]:.1f})")
    t._cam_focus = None; play(lambda: False, 120)
    for room, at_, name in (("castelia_street", (16, 40), "02_castelia_street"), ("prime_pier", (16, 20), "03_prime_pier"),
                            (None, (40, 72), "04_avenue"), (None, (75, 46), "05_avenue_east")):
        t = town(room, at_)
        play(lambda: False, 5)
        check(t._live_cam is not None, f"{room or 'the avenue'}: live ({(t.live or {}).get('zone')})")
        shot(name)

print("3) the Options switch, and the flat pictures without it")
t = town("plaza", (21, 30))
settings.put(g, "live3d", False)
play(lambda: False, 3)
check(t._live() is None and t._live_cam is None, "3D camera: Flat draws the baked pictures")
shot("06_plaza_flat")
settings.put(g, "live3d", True)
g.live3d_headless = False
play(lambda: False, 3)
check(t._live() is None, "headless without the checks' say-so: flat (the other suites draw as ever)")
g.live3d_headless = True
from src.states.systems.options import OptionsState
o = OptionsState(g, t, lambda: None)
o.tab = o.tabs.index("SCREEN & SOUND")
check(any(r[0] == "3D camera" for r in o.rows()), "Options, SCREEN & SOUND: a 3D camera row")

print("FAILURES:", len(fails))
for f in fails:
    print("  FAIL", f)
