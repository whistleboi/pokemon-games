# Johto's live 3D camera (Jordan 11-21: "Plan Johto live 3D" -> "SoulSilver's fixed camera"): SoulSilver's own models
# drawn every frame from its own fixed camera, standing you on the game's own floor heights. Scenes: assets/ss_3d
# (kanto_handoff/johto_map_tools/jexport3d.py); plan: kanto_handoff/JOHTO_LIVE3D_PLAN.md. Needs moderngl and an OpenGL 3.3
# card: without them this suite says so and stops (the game keeps its baked pictures).
#   bash dev/checks/run.sh johto_live3d
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
story.starting_region = "JOHTO"
story.story_flags.update({"received_starter_johto": True})


def settle(n=60):
    for _ in range(n):
        st = g.current_state
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


print("1) the scenes: SoulSilver's models, camera and floor heights, exported")
if not live3d.available(g):
    print("   (no moderngl / OpenGL 3.3 card here: the live camera is off, the baked pictures stay)")
    print(f"##### {len(fails)} failures")
    raise SystemExit
PILOT = {"NEW_BARK_TOWN": ("lab", "home", "home_2", "rival", "elmhouse"), "CHERRYGROVE_CITY": ("center", "mart", "gent", "fisher", "evohouse"),
         "SILVER_LEAGUE_PLATEAU": ("lobby", "lobby_2", "league_will", "league_koga", "league_bruno", "league_karen", "league_lance", "hall_of_fame")}   # (11-22: SoulSilver's own T10)
sc = live3d.scene_of(g, "ss_ground/T20.png", [0, 0])
check(sc is not None and sc.cam is not None and abs(float(sc.cam[0]) - 48.68) < 0.05 and abs(float(sc.cam[1]) - 41.68) < 0.05
      and abs(float(sc.cam[2]) - 16.18) < 0.05,
      f"New Bark: SoulSilver's outdoor camera (type 0: 48.68 degrees down, 41.68 tiles away, a 16.18 degree view) ({None if sc is None else [round(float(v), 2) for v in sc.cam]})")
check(sc is not None and sc.bdhc is not None, "New Bark: the game's own floor heights came with the scene")
sc = live3d.scene_of(g, "ss_ground/T21PC0101.png", None, True)
check(sc is not None and abs(float(sc.cam[0]) - 49.91) < 0.05 and sc.indoor, "Cherrygrove's Center: the room camera (type 4), a room drawn on black")
check(sc is not None and sc.zshift is not None and float(sc.zshift.max()) >= 2, "Cherrygrove's Center: its moved walk grid comes with the way back (zshift)")
check(live3d.scene_of(g, "b2_ground/28.png") is live3d.scene(g, 28), "Black 2's scenes are found the same way as before")

print("2) the towns, opened as the game opens them")
for key, rooms in PILOT.items():
    t = town(key)
    lv = t._live() if hasattr(t, "_live") else None
    check(type(t).__name__ == "WalkTownState" and bool(lv), f"{key}: live")
    if not lv:
        continue
    sc = lv[0]
    opens = [(x, y) for y in range(t.h) for x in range(t.w) if t._open((x, y))]
    check(not sc.holes(opens), f"{key}: the scene's ground is under every tile you can walk ({len(opens)})")
    t._live_height(*t.player)
    H = list(t.__dict__["_live_ground"].values())[-1]
    own = 0
    for (x, y), h in H.items():
        zx, zy = int(x + sc.origin[0]), int(y + sc.origin[1])
        vs = [float(v) for v in sc.bdhc[zy, zx] if v == v] if 0 <= zy < sc.bdhc.shape[0] and 0 <= zx < sc.bdhc.shape[1] else []
        own += bool(vs) and min(abs(v - h) for v in vs) < 0.01
    check(own >= 0.98 * len(H), f"{key}: you stand on SoulSilver's own floor heights ({own} of {len(H)} tiles)")
    settle(2)
    pygame.image.save(pygame.display.get_surface(), f"{S}/johto_live3d_{key}.png")
    img = pygame.display.get_surface()
    v = t._view()
    sky = sum(1 for px in range(v.x + 4, v.right - 4, 16) for py in range(v.y + 4, v.bottom - 4, 16) if tuple(img.get_at((px, py)))[:3] in ((150, 190, 235), live3d.GAP))
    check(sky == 0, f"{key}: no sky showing where you arrive ({sky} sampled points)")
    for nm, (cx, cy) in (("north-west", (0, 0)), ("north-east", (t.w, 0)), ("south-west", (0, t.h)), ("south-east", (t.w, t.h))):
        at = min(opens, key=lambda q: (q[0] - cx) ** 2 + (q[1] - cy) ** 2)
        t.player = t.anim_from = t.partner = t.partner_from = at; settle(3)
        img = pygame.display.get_surface()
        sky = sum(1 for px in range(v.x + 4, v.right - 4, 16) for py in range(v.y + 4, v.bottom - 4, 16) if tuple(img.get_at((px, py)))[:3] in ((150, 190, 235), live3d.GAP))
        check(sky == 0, f"{key}: no sky past its {nm} edge, standing at {at} ({sky} sampled points)")
    for room in rooms:
        t = town(key, room)
        lv = t._live()
        check(bool(lv), f"{key} / {room}: live")
        if not lv:
            continue
        sc = lv[0]
        opens = {(x, y) for y in range(t.h) for x in range(t.w) if t._open((x, y))}
        check(not sc.holes([(x, int(round(sc.wz(x, y)))) for x, y in opens]), f"{key} / {room}: the room's floor is under every tile you can walk")
        got = reach(opens, tuple(t.player))
        jump = [(a, b) for a in got for b in ((a[0] + 1, a[1]), (a[0], a[1] + 1)) if b in got
                and (abs(t._live_height(*a) - t._live_height(*b)) > 1.01 or abs(sc.wz(*a) - sc.wz(*b)) > 2.01)]
        check(not jump, f"{key} / {room}: no step between two neighbouring tiles jumps a level or across the room ({jump[:3]})")
        r_ = t._me_drawn[0]
        check(t._tile_at((r_.centerx, r_.bottom - 6)) == tuple(t.player), f"{key} / {room}: a tap on yourself finds your own tile")
        settle(2)
        pygame.image.save(pygame.display.get_surface(), f"{S}/johto_live3d_{key}_{room}.png")

print("3) Cherrygrove's Center: its two levels")
t = town("CHERRYGROVE_CITY", "center")
if t._live():
    sc = t._live()[0]
    opens = {(x, y) for y in range(t.h) for x in range(t.w) if t._open((x, y))}
    got = reach(opens, tuple(t.player))
    hs = sorted({round(t._live_height(*q), 1) for q in got})
    check(hs[0] < 0.1 and hs[-1] >= 2.9, f"the main hall and the back level, 3 tiles up, both reached on foot (heights {hs})")
    back = min(got, key=lambda q: q[1])
    check(sc.wz(*back) - back[1] >= 1.9, f"the back level's tiles stand where the real room has them ({back} -> row {sc.wz(*back)})")
    nurse = next((p for p, o in t._people().items() if "heal" in str(o).lower()), None)
    check(nurse is not None and any((nurse[0], nurse[1] + d) in got for d in (1, 2)), f"the nurse is reached across her counter ({nurse})")

print("4) Route 29, in the route walker")
story.current_area_key = "JOHTO_ROUTE_29"; story.story_flags["visited_JOHTO_ROUTE_29"] = True
g.walk_town_pos = g.walk_town_room = None
g.change_state(_PS(g)); settle(8)
t = g.current_state
check(type(t).__name__ == "DungeonState" and bool(t._dl_live()), "Route 29: live in the walker the game hands out")
if type(t).__name__ == "DungeonState" and t._dl_live():
    f = t.run.floor
    opens = [(x, y) for y in range(f.h) for x in range(f.w) if f.walkable(x, y)]
    check(not t._dl_live()[0].holes(opens), f"Route 29: ground under every tile you can walk ({len(opens)})")
    pygame.image.save(pygame.display.get_surface(), f"{S}/johto_live3d_ROUTE_29.png")
    for i in range(1, t.run.n_floors):   # (its buildings' rooms: floors after the route's own, dungeon.with_rooms)
        t._warp(i, 1, 1); settle(4)
        f = t.run.floor
        opens = [(x, y) for y in range(f.h) for x in range(f.w) if f.walkable(x, y)]
        if not opens or t.run.index != i:
            check(False, f"Route 29's room {i}: could not be entered by the check"); continue
        t.run.player = opens[len(opens) // 2]; t._dl_key = None; settle(4)
        lv = t._dl_live()
        check(bool(lv), f"Route 29's room {i} ({t._floor_name(i)}): live")
        if lv:
            sc = lv[0]
            check(not sc.holes([(x, int(round(sc.wz(x, y)))) for x, y in opens]), f"Route 29's room {i}: floor under every tile you can walk")
            so = set(opens)
            jump = [(a_, b_) for a_ in opens for b_ in ((a_[0] + 1, a_[1]), (a_[0], a_[1] + 1)) if b_ in so
                    and (abs(t._dl_height(*a_) - t._dl_height(*b_)) > 1.01 or abs(sc.wz(*a_) - sc.wz(*b_)) > 2.01)]
            check(not jump, f"Route 29's room {i}: no step jumps a level or across the room ({jump[:3]})")
            pygame.image.save(pygame.display.get_surface(), f"{S}/johto_live3d_ROUTE_29_room{i}.png")

print("4b) no stepping between far levels (the DS's rule), Goldenrod Gym")
t = town("GOLDENROD_CITY", "gym")
if t._live():
    sc = t._live()[0]
    opens = {(x, y) for y in range(t.h) for x in range(t.w) if t._open((x, y))}
    pairs = [(a_, b_) for a_ in opens for b_ in ((a_[0] + 1, a_[1]), (a_[0], a_[1] + 1)) if b_ in opens]
    far = [(a_, b_) for a_, b_ in pairs if abs(t._live_height(*a_) - t._live_height(*b_)) > 1.5 and not sc.stacked(*a_) and not sc.stacked(*b_)
           and t._art_char(a_) == "." and t._art_char(b_) == "."]
    check(len(far) >= 6 and all(t._level_edge(a_, b_) for a_, b_ in far), f"floor and walkway, three levels apart: no step between them ({len(far)} pairs, e.g. {far[:2]})")
    check(t._level_edge((4, 13), (5, 13)), "the pair the review named, (4,13)-(5,13), is blocked")
    def _reach(edge):
        seen = {tuple(t.player)}; todo = [tuple(t.player)]
        while todo:
            c = todo.pop()
            for d in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                q = (c[0] + d[0], c[1] + d[1])
                if q in opens and q not in seen and not (edge and t._level_edge(c, q)):
                    seen.add(q); todo.append(q)
        return seen
    lost = sorted(_reach(False) - _reach(True))
    check(not lost, f"...and nothing is cut off by it ({lost[:4]})")
    who = [p for p in t._people()]
    check(all(any((p[0] + dx, p[1] + dy) in _reach(True) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0), (0, 2))) for p in who), f"Whitney is still reached, under the walkway's arch ({who})")
t = town("VIOLET_CITY", "gym")
if t._live():
    check(not t._level_edge((8, 17), (8, 16)) and abs(t._live_height(8, 17) - t._live_height(8, 16)) > 10, "Violet Gym: the lift's 29 levels are a ride, not a blocked drop")

print("5) the flat pictures stay when the live camera is off")
g.live3d = False
t = town("NEW_BARK_TOWN")
check(not t._live(), "3D camera Flat: New Bark draws its baked picture")
g.live3d = True

print(f"##### {len(fails)} failures")
