# Sinnoh's live 3D camera (Jordan 11-23: every Sinnoh place goes live 3D, batch by batch; pilot in batch S1): Platinum's own
# models drawn every frame from its own camera, standing you on the game's own floor heights. Scenes: assets/pt_3d
# (kanto_handoff/sinnoh_map_tools/pexport3d.py, the same format as Johto's ss_3d); plan: ROADMAP_SINNOH.md "Game plan".
# Each batch adds its places to PILOT / ROUTES below. Needs moderngl and an OpenGL 3.3 card: without them this suite says so
# and stops (the game keeps its baked pictures).
#   bash dev/checks/run.sh sinnoh_live3d
import os
from collections import deque
from src.states.overworld import CityState, PlayState as _PS
from src.dungeon import live3d

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True; g.live3d_headless = True
story.starting_region = "SINNOH"
story.story_flags.update({"received_starter_sinnoh": True, "defeated_rival_sinnoh_starter": True, "has_sinnoh_starter": True,
                          "sinnoh_starly_driven_off": True, "sinnoh_rowan_walked_up": True})   # (past the opening: Lake Verity's Starly scene stays quiet)
# (the batches' places: towns with their rooms, then places the route walker opens)
PILOT = {"TWINLEAF_TOWN": ("home", "home_2f", "rival", "rival_2f", "house_0301", "house_0401"),
         "SANDGEM_TOWN": ("lab", "assistant", "center", "center_2", "center_b1", "mart", "house_0301")}
# (Sandgem's assistant_2f stays flat: Platinum's own picture of T02R0202 comes out dark, so it has no ground picture to go live from)
ROUTES = ("SINNOH_ROUTE_201", "VERITY_LAKEFRONT", "LAKE_VERITY")
# S2 (11-23): Jubilife to Eterna Forest. A town's rooms: all of them (None), less any listed in FLAT (no ground picture)
_TM = __import__("json").load(open("assets/town_maps.json", encoding="utf-8"))
FLAT = {("SANDGEM_TOWN", "assistant_2f")}
for _k in ("JUBILIFE_CITY", "OREBURGH_CITY", "FLOAROMA_TOWN"):
    PILOT[_k] = tuple(n for n in (_TM[_k].get("rooms") or {}) if (_k, n) not in FLAT)
ROUTES += ("SINNOH_ROUTE_202", "SINNOH_ROUTE_203", "OREBURGH_GATE", "OREBURGH_MINE", "SINNOH_ROUTE_204", "RAVAGED_PATH",
           "FLOAROMA_MEADOW", "SINNOH_ROUTE_205", "VALLEY_WINDWORKS", "ETERNA_FOREST", "ETERNA_FOREST_OUTSKIRTS")


def settle(n=60):
    for _ in range(n):
        st = g.current_state
        if type(st).__name__ == "DungeonState" and hasattr(st, "run"):   # (no wild Pokemon: they'd start a battle mid-check)
            st.run.floor.movers = [m for m in st.run.floor.movers if m.kind != "wild"]
        if getattr(st, "npc_active", False):
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif getattr(st, "dialogue_box", None) is not None and getattr(st.dialogue_box, "visible", False):
            st.dialogue_box.advance()
        st.update(); st.draw()


def town(key, room=None):
    story.current_area_key = key; story.story_flags["visited_" + key] = True
    g.walk_town_pos = None; g.walk_town_room = (key, room) if room else None
    g.change_state(CityState(g)); settle()
    t = g.current_state
    if room and getattr(t, "room", None) != room:
        t._go(room, None); settle()
    return g.current_state


def reach(opens, start):
    seen = {start}; dq = deque([start])
    while dq:
        c = dq.popleft()
        for d in ((0, -1), (1, 0), (-1, 0), (0, 1)):
            q = (c[0] + d[0], c[1] + d[1])
            if q in opens and q not in seen:
                seen.add(q); dq.append(q)
    return seen


def sky_points(v):
    img = pygame.display.get_surface()
    return sum(1 for px in range(v.x + 4, v.right - 4, 16) for py in range(v.y + 4, v.bottom - 4, 16)
               if tuple(img.get_at((px, py)))[:3] in ((150, 190, 235), live3d.GAP))


print("1) the scenes: Platinum's models, camera and floor heights, exported")
if not live3d.available(g):
    print("   (no moderngl / OpenGL 3.3 card here: the live camera is off, the baked pictures stay)")
    print(f"##### {len(fails)} failures")
    raise SystemExit
sc = live3d.scene_of(g, "pt_ground/T01.png", [0, 0])
check(sc is not None and sc.cam is not None and 30 < float(sc.cam[0]) < 70,
      f"Twinleaf: Platinum's outdoor camera came with the scene ({None if sc is None or sc.cam is None else [round(float(v), 2) for v in sc.cam]})")
check(sc is not None and sc.bdhc is not None, "Twinleaf: the game's own floor heights came with the scene")
check(live3d.scene_of(g, "ss_ground/T20.png", [0, 0]) is not None, "SoulSilver's scenes are still found the same way")

print("2) the towns and their rooms, opened as the game opens them")
for key, rooms in PILOT.items():
    t = town(key)
    lv = t._live() if hasattr(t, "_live") else None
    check(type(t).__name__ == "WalkTownState" and bool(lv), f"{key}: live")
    if not lv:
        continue
    sc = lv[0]
    opens = [(x, y) for y in range(t.h) for x in range(t.w) if t._open((x, y))]
    check(not sc.holes(opens), f"{key}: the scene's ground is under every tile you can walk ({len(opens)})")
    if sc.bdhc is not None:
        t._live_height(*t.player)
        H = list(t.__dict__["_live_ground"].values())[-1]
        own = 0
        for (x, y), h in H.items():
            zx, zy = int(x + sc.origin[0]), int(y + sc.origin[1])
            vs = [float(v) for v in sc.bdhc[zy, zx] if v == v] if 0 <= zy < sc.bdhc.shape[0] and 0 <= zx < sc.bdhc.shape[1] else []
            own += bool(vs) and min(abs(v - h) for v in vs) < 0.01
        check(own >= 0.98 * len(H), f"{key}: you stand on Platinum's own floor heights ({own} of {len(H)} tiles)")
    settle(2)
    pygame.image.save(pygame.display.get_surface(), f"{S}/sinnoh_live3d_{key}.png")
    v = t._view()
    check(sky_points(v) == 0, f"{key}: no sky showing where you arrive")
    for nm, (cx, cy) in (("north-west", (0, 0)), ("north-east", (t.w, 0)), ("south-west", (0, t.h)), ("south-east", (t.w, t.h))):
        at = min(opens, key=lambda q: (q[0] - cx) ** 2 + (q[1] - cy) ** 2)
        t.player = t.anim_from = t.partner = t.partner_from = at; settle(3)
        n = sky_points(v)
        check(n == 0, f"{key}: no sky past its {nm} edge, standing at {at} ({n} sampled points)")
        if n:
            pygame.image.save(pygame.display.get_surface(), f"{S}/sinnoh_live3d_{key}_{nm}.png")
    for room in rooms:
        t = town(key, room)
        if getattr(t, "room", None) != room:
            check(False, f"{key} / {room}: could not be entered by the check"); continue
        lv = t._live()
        check(bool(lv), f"{key} / {room}: live")
        if not lv:
            continue
        sc = lv[0]
        opens = {(x, y) for y in range(t.h) for x in range(t.w) if t._open((x, y))}
        check(not sc.holes([(x, int(round(sc.wz(x, y)))) for x, y in opens]), f"{key} / {room}: the room's floor is under every tile you can walk")
        got = reach(opens, tuple(t.player))
        jump = [(a, b) for a in got for b in ((a[0] + 1, a[1]), (a[0], a[1] + 1)) if b in got
                and not t._level_edge(a, b)   # (a step the game itself refuses: Platinum's floor heights, Oreburgh Gym's platforms)
                and not (sc.stacked(*a) or sc.stacked(*b))   # (a two-floor tile: the level is the one you came in on, which a cold
                                                             #  pair can't know - Oreburgh Gym's walkway; main 78976135)
                and (abs(t._live_height(*a) - t._live_height(*b)) > 1.01 or abs(sc.wz(*a) - sc.wz(*b)) > 2.01)]
        check(not jump, f"{key} / {room}: no step between two neighbouring tiles jumps a level ({jump[:3]})")
        r_ = t._me_drawn[0]
        check(t._tile_at((r_.centerx, r_.bottom - 6)) == tuple(t.player), f"{key} / {room}: a tap on yourself finds your own tile")
        settle(2)
        pygame.image.save(pygame.display.get_surface(), f"{S}/sinnoh_live3d_{key}_{room}.png")

print("3) Sandgem's Center: the nurse across her counter, live")
t = town("SANDGEM_TOWN", "center")
if t._live():
    opens = {(x, y) for y in range(t.h) for x in range(t.w) if t._open((x, y))}
    got = reach(opens, tuple(t.player))
    nurse = next((p for p, o in t._people().items() if "heal" in str(o).lower()), None)
    check(nurse is not None and any((nurse[0], nurse[1] + d) in got for d in (1, 2, 3)), f"the nurse is reached across her counter ({nurse})")

print("4) routes and the lake, in the route walker")
for key in ROUTES:
    story.current_area_key = key; story.story_flags["visited_" + key] = True
    g.walk_town_pos = g.walk_town_room = None
    g.change_state(_PS(g)); settle(8)
    t = g.current_state
    lv = t._dl_live() if type(t).__name__ == "DungeonState" else None
    check(bool(lv), f"{key}: live in the walker the game hands out ({type(t).__name__})")
    if not lv:
        continue
    for i in range(t.run.n_floors):
        if i:
            t._warp(i, 1, 1); settle(4)
        f = t.run.floor
        opens = [(x, y) for y in range(f.h) for x in range(f.w) if f.walkable(x, y)]
        if not opens or t.run.index != i:
            check(False, f"{key} floor {i}: could not be entered by the check"); continue
        if i:
            t.run.player = opens[len(opens) // 2]; t._dl_key = None; settle(4)
        lv = t._dl_live()
        check(bool(lv), f"{key} floor {i} ({t._floor_name(i)}): live")
        if not lv:
            continue
        sc = lv[0]
        check(not sc.holes([(x, int(round(sc.wz(x, y)))) for x, y in opens]), f"{key} floor {i}: ground under every tile you can walk ({len(opens)})")
        so = set(opens)
        two = set(getattr(f, "bridge", {}) or {})   # (a two-level bridge: on its deck or under it, both right - as Johto's suite)
        jump = [(a_, b_) for a_ in opens for b_ in ((a_[0] + 1, a_[1]), (a_[0], a_[1] + 1)) if b_ in so
                and not (a_ in two or b_ in two or sc.stacked(*a_) or sc.stacked(*b_))
                and (abs(t._dl_height(*a_) - t._dl_height(*b_)) > 1.01 or abs(sc.wz(*a_) - sc.wz(*b_)) > 2.01)]
        check(not jump, f"{key} floor {i}: no step jumps a level ({jump[:3]})")
        pygame.image.save(pygame.display.get_surface(), f"{S}/sinnoh_live3d_{key}_{i}.png")

print("5) the flat pictures stay when the live camera is off")
g.live3d = False
t = town("TWINLEAF_TOWN")
check(not t._live(), "3D camera Flat: Twinleaf draws its baked picture")
g.live3d = True

print(f"##### {len(fails)} failures")
