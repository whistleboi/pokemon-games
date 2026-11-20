# Unova's DS camera (11-20, Jordan: "all 4"): Aspertia walked as Black 2's camera sees it. The ground lifted by its heights
# (the Outlook and the terrace raised, stairs you walk down), shadows under everyone, buildings leaning with where they
# are on screen and drawn in depth order with the people, and the camera gliding and zooming for scenes and places.
# Screenshots go to dev/checks/out/unovacam_*.png. Glue after harness_head.py:
#   bash dev/checks/run.sh unovacam
import json
from src.states.overworld import CityState
from src.states.overworld.walk_town import WalkTownState as _WTS, TILE

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.player_character = "nate"
flags = story.story_flags
story.story_flags["unova_version"] = "BLACK_2"   # (the version picked at the start: unovastart plays the pick)
for f in ("b2_mom_talk", "b2_hugh_met", "received_starter_unova", "received_pokedex_unova", "b2_hugh_battled",
          "b2_led_to_center", "b2_center_tour", "b2_send_off", "b2_route19_lesson"):
    flags[f] = True   # (past the opening: the town as you walk it afterwards)
story.badges.setdefault("UNOVA", [])
g.walk_town_pos = None
g.walk_town_room = None
story.current_area_key, story.last_area_key = "ASPERTIA_CITY", "UNOVA_ROUTE_19"
t = CityState(g)
g.change_state(t)


def frames(n=1):
    for _ in range(n):
        st = g.current_state
        if getattr(st, "npc_active", False):
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        st.update(); st.draw()


def shot(name):
    g.current_state.draw()
    pygame.image.save(pygame.display.get_surface(), f"{S}/unovacam_{name}.png")


def put(x, y, face=(0, 1)):
    t.room = None
    t.player = t.anim_from = (x, y); t.partner = t.partner_from = (x, y - 1); t.anim = 0; t.facing = face
    t._cam_ease = None; t._cam_cur = None; t._cam_ease_until = 0


frames(30)
t = g.current_state
print("1) Aspertia as Black 2's camera sees it")
t._go(None, "OUT:20,37") if t.room else None; frames(5); t = g.current_state; c3 = None
check(isinstance(t, _WTS) and t.area_key == "ASPERTIA_CITY" and t.room is None, f"in Aspertia, outside ({type(t).__name__}, {t.room})")
c3 = getattr(t, "cam3d", None)
check(c3 is not None and c3.top > TILE * 2, f"its ground drawn from the camera, the raised parts above row 0 ({getattr(c3, 'top', None)} px)")
check(c3 is not None and len(c3.buildings) >= 12, f"its buildings drawn every frame, not baked in ({len(getattr(c3, 'buildings', []))})")
check(getattr(t, "shadows", False), "an oval under everyone's feet")

print("2) the stairs: down from the Outlook to the terrace, smoothly")
lifts = [round(c3.lift(5, y), 2) for y in range(11, 20)]
check(lifts[0] - lifts[-1] > 2.0 and all(a >= b - 0.05 for a, b in zip(lifts, lifts[1:])),
      f"the Outlook stands about 4 tiles above the terrace, stepping down the stairs ({lifts})")
put(5, 11)
shot("01_outlook")
ys = []
for i in range(8):
    t.step(0, 1)
    for _ in range(12):
        frames()
        r, (ox, oy) = t._me_drawn
        ys.append(r.bottom - oy)   # (where you're drawn on the map's picture)
    if i == 3:
        shot("02_stairs")
jumps = [b - a for a, b in zip(ys, ys[1:])]
check(t.player == (5, 19), f"walked down to the terrace ({t.player})")
check(max(abs(j) for j in jumps) < TILE * 0.4, f"no jumps: you glide down a step at a time (largest move a frame {max(abs(j) for j in jumps)} px)")
_down = (ys[-1] - ys[0]) / TILE
check(_down > 8 + 2.0, f"on screen you went down {_down:.1f} tiles for 8 steps: more than the walk, the stairs' drop added (B2W2's look)")
shot("03_terrace")
put(7, 21, (1, 0))
lifts = [round(c3.lift(x, 21), 2) for x in range(7, 15)]
check(lifts[0] - lifts[-1] > 1.5, f"the east stairs down to the street ({lifts})")

print("3) buildings lean with where they are on screen, and stand in depth order with you")
put(20, 37)
frames(3)
view = t._view()
ox, oy = t._origin()
got = {b.key: (b, i) for b, i in ((b, None) for b in c3.buildings)}
lean = {}
for b in c3.buildings:
    off = (ox + b.at[0] * TILE - view.centerx) / TILE
    from src.dungeon import camera3d as _c3m
    i = b.n + max(-b.n, min(b.n, round(off * c3.lean_tile / b.step)))
    lean[(b.key, tuple(b.at))] = (round(off, 1), i - b.n)
left = [v for k, v in lean.items() if v[0] < -3]
right = [v for k, v in lean.items() if v[0] > 3]
check(left and all(v[1] < 0 for v in left) and right and all(v[1] > 0 for v in right),
      f"a building left of you leans left, one right of you leans right ({sorted(lean.values())[:3]} ... {sorted(lean.values())[-3:]})")
shot("04_lean")
put(12, 37)
frames(3)
shot("04b_lean_moved")
school = next(b for b in c3.buildings if b.key == "427_307_0")
center = next(b for b in c3.buildings if b.key == "427_0_0")
check(school.row <= 34.5 + 1e-6 and center.row <= 35.5 + 1e-6,
      f"someone at a door or on its steps stands in front of the building (school {school.row}, Center {center.row})")
check(c3.buildings_drawn(ox, oy, view) and all(len(e) == 3 for e in c3.buildings_drawn(ox, oy, view)), "the buildings go into the same depth list as the people")

print("3b) trees, lamp posts and rails stand in depth order too")
check(len(c3.tops) >= 40, f"what stands up out of the ground is cut out a row at a time ({len(c3.tops)} rows)")
put(19, 18)
frames(3)
ox, oy = t._origin()
_lamp = [e for e in c3.buildings_drawn(ox, oy, t._view()) if e[0] == oy + 20 * TILE - TILE // 2]
_me = oy + 19 * TILE
check(_lamp and all(k > _me for k, _i, _p in _lamp), "standing just north of the lamp post, it's drawn over you (row 19's pieces after you)")
shot("07_behind_lamp")
put(19, 20, (0, -1))
frames(3)
check(all(k < oy + 21 * TILE for k, _i, _p in _lamp), "south of it, you're in front")
shot("07b_front_of_lamp")

print("4) a tap on raised ground finds the tile you see")
put(5, 8)
frames(2)
ox, oy = t._origin()
for tile in ((5, 8), (4, 14), (5, 19)):
    px = (ox + (tile[0] + 0.5) * TILE, oy + (tile[1] + 0.5 - c3.lift(*tile)) * TILE)
    if t._view().collidepoint(px):
        check(t._tile_at(px) == tile, f"tapping where {tile} is drawn picks {tile} ({t._tile_at(px)})")

print("5) the camera: glides for a scene's look, zooms in and back")
put(20, 37)
frames(2)
c0 = t._cam_cur
t.npc_look((20, 52))
frames(1)
c1 = t._cam_cur
frames(90)
c2 = t._cam_cur
check(c1 and c0 and c2 and abs(c1[1] - c0[1]) < abs(c2[1] - c0[1]) * 0.3 and c2[1] > c0[1] + TILE * 5,
      f"the view glides to what the scene looks at, not a jump ({c0[1]:.0f} -> {c1[1]:.0f} -> {c2[1]:.0f})")
t.npc_zoom(1.5)
frames(60)
check(abs(t.zoom - 1.5) < 0.05, f"a scene's zoom: the camera moves in ({t.zoom:.2f})")
shot("05_zoom")
v = t._view()
mid = t._tile_at(v.center)
c = t._cam_cur
check(abs(mid[1] - (c[1] / TILE)) < 2.5, f"tapping zoomed in still finds the tile under the finger ({mid})")
t._scene_lock = True
t.npc_lock(False)
frames(90)
check(abs(t.zoom - 1.0) < 0.02 and t._cam_focus is None, f"when the scene ends the camera comes back to you, at its usual distance ({t.zoom:.2f})")
t.cameras = [{"rect": [19, 30, 12, 10], "zoom": 0.8}]
frames(60)
check(abs(t.zoom - 0.8) < 0.05, f"a place's own camera (a map's \"cameras\" zone): further out where it says ({t.zoom:.2f})")
shot("06_zone_out")
t.cameras = []
frames(60)

print("5b) the Outlook: Black 2's camera moves as you walk onto it (its moving-camera strip, a/1/5/6; 11-20)")
t.cameras = json.load(open("assets/town_maps.json", encoding="utf-8"))["ASPERTIA_CITY"].get("cameras") or []
check(any(c.get("rect") == [0, 5, 7, 7] and isinstance(c.get("zoom"), list) for c in t.cameras),
      f"Aspertia's map carries the Outlook's strip from the game file ({t.cameras})")
put(5, 13, (0, -1))
frames(80)
z_low, c_low = t.zoom, t._cam_cur
zs = []
for i in range(8):
    if t.player[1] <= 5:
        break
    t.step(0, -1)
    for _ in range(12):
        frames()
        zs.append(t.zoom)
frames(80)
check(t.player[1] <= 6, f"walked up onto the Outlook ({t.player})")
check(abs(z_low - 1.0) < 0.02 and t.zoom > 1.04, f"the camera moves in as you go out onto it ({z_low:.2f} -> {t.zoom:.2f})")
check(max(abs(b - a) for a, b in zip(zs, zs[1:])) < 0.01, "smoothly, a little each step (no jump)")
shot("05b_outlook_view")
_strip = t.cameras
_pan = t._camera()
t.cameras = []
_flat = t._camera()
t.cameras = _strip
check(_pan[1] <= _flat[1], f"and looks north as far as the picture reaches (the game lifts its gaze to the sky past the map; ours stops at the map's top: {_flat[1]:.0f} -> {_pan[1]:.0f} px)")
put(5, 15, (0, 1))
frames(120)
check(abs(t.zoom - 1.0) < 0.02, f"back to the usual camera off the Outlook ({t.zoom:.2f})")

print("6) other regions' towns are drawn as before")
from src.states.overworld import walk_town as _wtm
_k = json.load(open("assets/town_maps.json", encoding="utf-8"))
import importlib.util as _iu   # (Unova's walkable maps: the ones dev/builders/town_maps/unova.py writes, 11-20 batch 1 on)
_sp = _iu.spec_from_file_location("_unova_maps", "dev/builders/town_maps/unova.py"); _um = _iu.module_from_spec(_sp); _sp.loader.exec_module(_um)
_unova = set(_um.MAPS)
check(not any("_cam" in (m.get("roofs") or {}) for k, m in _k.items() if isinstance(m, dict) and k not in _unova),
      f"only Unova's maps carry the camera picture ({sorted(_unova)})")

print("7) Route 19 through the same camera: Bianca's lesson, the ledge, Alder")
from src.states.overworld.dungeon import DungeonState as _DS
for _f in ("b2_route19_lesson", "b2_ledge_demo", "b2_alder_met"):
    flags.pop(_f, None)
said = []


def play(until, n=2000):
    for _ in range(n):
        if until():
            return True
        st = g.current_state
        if isinstance(st, _DS) and getattr(st, "mode", None) == "CHOICE":   # (a wild Pokemon from the grass: it wanders off;
            mv = st.encounter                                                 #  not this suite's business, and it stalled the walk)
            st.encounter, st.mode = None, "MAP"
            if mv in st.run.floor.movers:
                st.run.floor.movers.remove(mv)
            continue
        box = getattr(st, "npc_dialogue", None) if getattr(st, "npc_active", False) else getattr(st, "dialogue_box", None)
        if box is not None and getattr(box, "visible", False):
            for line in getattr(box, "text_lines", []) or []:
                if not said or said[-1] != line:
                    said.append(line)
            if getattr(st, "npc_active", False):
                st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
            else:
                box.advance()
        st.update(); st.draw()
    return until()


put(20, 7, (0, -1))
t.step(0, -1)
play(lambda: getattr(g.current_state, "room", None) == "gate" and g.current_state.anim == 0, 300)
t = g.current_state
_up = next(xy for xy, v in t.exits.items() if v == "UNOVA_ROUTE_19")
t.player = t.anim_from = (_up[0], _up[1] + 1); t.anim = 0
t.step(0, -1)
play(lambda: isinstance(g.current_state, _DS), 600)
d = g.current_state
check(isinstance(d, _DS) and story.current_area_key == "UNOVA_ROUTE_19", f"out of the gate onto Route 19, walked on its map ({type(d).__name__})")
play(lambda: d._floor_surf is not None and getattr(d, "cam3d", None) is not None, 60)
rc = getattr(d, "cam3d", None)
check(rc is not None and rc.top > TILE * 3, f"Route 19 is drawn from Black 2's camera too, the hills raised ({getattr(rc, 'top', None)} px)")
check(rc is not None and len(rc.tops) > 10 and d.shadows, f"its trees stand in depth order, shadows on ({len(getattr(rc, 'tops', []))} rows)")
shot("10_route19")
check(tuple(d.run.player)[1] >= 29, f"you come out by the gate ({d.run.player})")
_seen_mon = []
for _ in range(6):
    if flags.get("b2_route19_lesson"):
        break
    x, y = d.run.player
    if y > 26:
        d.step(0, -1)
    for _k in range(30):
        st = g.current_state
        if hasattr(st, "_scenes") and any(str(a.get("sheet")).startswith("mon:") for a in st._scenes().actors):
            if not _seen_mon:
                _seen_mon.append(True); shot("11_lesson")
        play(lambda: False, 1)
play(lambda: flags.get("b2_route19_lesson") and not g.current_state._scene_lock if hasattr(g.current_state, "_scene_lock") else flags.get("b2_route19_lesson"), 3000)
check(flags.get("b2_route19_lesson") and any("Purrloin" in x for x in said), f"Bianca's catching lesson plays out: a wild Purrloin, caught ({[x for x in said if 'Purrloin' in x][:1]})")
check(bool(_seen_mon), "the Purrloin is on the map in the scene")
d = g.current_state
said.clear()
d.run.player = d.anim_from = (45, 18); d.anim = 0
d.step(0, -1)
play(lambda: flags.get("b2_ledge_demo"), 2000)
check(flags.get("b2_ledge_demo") and any("Boing" in x for x in said), f"the Youngster hops off the ledge for you ({said[-1:]})")
play(lambda: d.anim == 0, 200)
d.run.player = d.anim_from = (49, 17); d.anim = 0; d.partner = d.partner_from = (50, 17)
d.step(-1, 0)
play(lambda: d.anim == 0, 200)
check(tuple(d.run.player) == (47, 17), f"you hop down the ledge too: west, over it in one go ({d.run.player})")
d.step(1, 0)
play(lambda: d.anim == 0, 200)
check(tuple(d.run.player) == (47, 17), f"...and can't climb back up it ({d.run.player})")
said.clear()
zs = []
d.run.player = d.anim_from = (54, 23); d.anim = 0
for _ in range(3):
    if not getattr(d, "_scene_lock", False):
        d.step(1, 0)
    play(lambda: d.anim == 0, 60)
for _ in range(1500):
    if flags.get("b2_alder_met") and not getattr(d, "_scene_lock", False):
        break
    zs.append(getattr(d, "zoom", 1.0))
    if abs(zs[-1] - 1.25) < 0.03 and "zoom" not in [k for k in ()]:
        if not getattr(d, "_shot_zoom", False):
            d._shot_zoom = True; shot("12_alder_zoom")
    play(lambda: False, 1)
check(flags.get("b2_alder_met") and any("Alder" in x for x in said), f"Alder calls from the hill, jumps down and leads you on ({said[:1]})")
check(max(zs or [1]) > 1.15, f"the camera moves in as he jumps down ({max(zs or [1]):.2f})")
play(lambda: abs(getattr(d, "zoom", 1.0) - 1.0) < 0.02, 300)
check(abs(getattr(d, "zoom", 1.0) - 1.0) < 0.02, "and back out when the scene's over")
shot("13_route19_east")

print("8) Your Pokemon beside Nate: the follower size every region uses (11-20)")
for _k in ("_t_scale",):
    d.__dict__.pop(_k, None)
check(d._trainer_scale() == 2, f"followers at 2x, the Journeys trainers' scale, not Nate's 3x ({d._trainer_scale()})")
me = d._player_img()
_snivy = d._mon_img(495, (0, 1))
check(me is not None and _snivy is not None and _snivy.get_height() < me.get_height(),
      f"Snivy stands shorter than Nate ({getattr(_snivy, 'get_height', lambda: None)()} vs {getattr(me, 'get_height', lambda: None)()} px)")

print("FAILURES:", len(fails))
for f in fails:
    print("  FAIL", f)
