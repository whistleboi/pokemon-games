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
# S3 (11-23): Eterna to Solaceon. Flat for now: Eterna's two houses with no Platinum room (house_0601/0701), the Contest Hall
# (2F: since 11-24). Hearthome's Gym: its four Platinum rooms, live (s_s3_hearthome_gym.py)
FLAT |= {("ETERNA_CITY", "house_0601"), ("ETERNA_CITY", "house_0701")}   # (the Contest Hall 2F has its picture since 11-24)
for _k in ("ETERNA_CITY", "HEARTHOME_CITY", "SOLACEON_TOWN"):
    PILOT[_k] = tuple(n for n in (_TM[_k].get("rooms") or {}) if (_k, n) not in FLAT)
KNOWN_JUMPS = {}   # ((area, floor): (steps, why)): level jumps left open on the roadmap. S3's three fixed 11-23: Route 210's
# bridge lettered as a bridge, the Old Chateau hall's landing above the dining door walled, Route 208's Surf strip
# (pexport3d BDHC_FIX) - kanto_handoff/sinnoh_map_tools/s_s3_jumps.py
ROUTES += ("SINNOH_ROUTE_206", "WAYWARD_CAVE", "SINNOH_ROUTE_207", "MT_CORONET_BASE", "SINNOH_ROUTE_208", "SINNOH_ROUTE_209",
           "SOLACEON_RUINS", "SINNOH_ROUTE_210", "OLD_CHATEAU", "ETERNA_GALACTIC_BUILDING", "LOST_TOWER")
# S4 (11-24): Veilstone, the town and every room (the Department Store's seven floors, the Gym with its punching bags)
PILOT["VEILSTONE_CITY"] = tuple(_TM["VEILSTONE_CITY"].get("rooms") or {})
# S4 (11-24, the rest): Pastoria and Celestic with every room (the Observatory Gate, the Combee house, the ruins), the routes
# between them, Valor Lakefront, Maniac Tunnel and the Galactic Warehouse (the Great Marsh's six zones
# don't join for export yet: flat for now, ROADMAP_SINNOH)
FLAT |= {("PASTORIA_CITY", "gym")}   # (its walkways' heights follow the water: one scene per water level still to make, as Eterna's clock)
for _k in ("PASTORIA_CITY", "CELESTIC_TOWN"):
    PILOT[_k] = tuple(n for n in (_TM[_k].get("rooms") or {}) if (_k, n) not in FLAT)
KNOWN_JUMPS[("VALOR_LAKEFRONT", 0)] = ({((20, 34), (21, 34))}, "the little pond's two water tiles read at two heights from Platinum's plates; surfing")
ROUTES += tuple(k for k in ("SINNOH_ROUTE_211", "SINNOH_ROUTE_212", "SINNOH_ROUTE_213", "SINNOH_ROUTE_214", "SINNOH_ROUTE_215", "VALOR_LAKEFRONT",
                            "MANIAC_TUNNEL", "GALACTIC_WAREHOUSE") if k not in ROUTES)


# S5 (11-24): Lake Valor's three floors (drained, full, Valor Cavern)
ROUTES += tuple(k for k in ("LAKE_VALOR", "SINNOH_ROUTE_216", "SINNOH_ROUTE_217", "ACUITY_LAKEFRONT", "LAKE_ACUITY", "TEAM_GALACTIC_HQ") if k not in ROUTES)
KNOWN_JUMPS[("SINNOH_ROUTE_216", 0)] = ({((31, 0), (32, 0))}, "the way out to Route 217 along the cliff top, on the map's top row: you leave the map on it")
# S5 (11-24): Canalave and its rooms (its Gym's four floors are flat pictures cut from one tower: no scene yet, Systems' card), Iron Island
FLAT |= {("CANALAVE_CITY", n) for n in ("gym", "gym_2f", "gym_3f", "gym_4f")}
PILOT["CANALAVE_CITY"] = tuple(n for n in (_TM["CANALAVE_CITY"].get("rooms") or {}) if ("CANALAVE_CITY", n) not in FLAT)
ROUTES += tuple(k for k in ("IRON_ISLAND",) if k not in ROUTES)
# S5 (11-24): Snowpoint and its rooms (its Gym's ice is flat: one level)
PILOT["SNOWPOINT_CITY"] = tuple(n for n in (_TM["SNOWPOINT_CITY"].get("rooms") or {}) if ("SNOWPOINT_CITY", n) not in FLAT)


def settle(n=60):
    for _ in range(n):
        st = g.current_state
        if type(st).__name__ == "DungeonState" and hasattr(st, "run"):   # (no wild Pokemon: they'd start a battle mid-check)
            st.run.floor.movers = [m for m in st.run.floor.movers if m.kind != "wild"]
        if type(st).__name__ == "PickListState":   # (a question as you come in: Hearthome Gym's door sums - not answered here)
            st.pick(None); continue
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
        opens = {(x, y) for y in range(t.h) for x in range(t.w) if t._open((x, y)) and (x, y) not in t.exits}   # (a way out: stepped into and left)
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
        if i or t.run.index != i:   # (a place entered on another floor: Mt. Coronet, the Old Chateau's hall)
            t._warp(i, 1, 1); settle(4)
        f = t.run.floor
        opens = [(x, y) for y in range(f.h) for x in range(f.w) if f.walkable(x, y)]
        so_ = set(opens)
        if not opens or t.run.index != i:
            check(False, f"{key} floor {i}: could not be entered by the check"); continue
        if i or t.run.player not in so_:
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
                and not t._level_edge(a_, b_)   # (a step the game itself refuses, as the towns' check: two levels' edge)
                and (abs(t._dl_height(*a_) - t._dl_height(*b_)) > 1.01 or abs(sc.wz(*a_) - sc.wz(*b_)) > 2.01)]
        _known = KNOWN_JUMPS.get((key, i))
        if jump and _known and set(jump) <= _known[0]:
            print(f"   known {key} floor {i}: {len(jump)} steps jump a level - {_known[1]} (ROADMAP_SINNOH S3)")
        else:
            check(not jump, f"{key} floor {i}: no step jumps a level ({jump[:3]})")
        pygame.image.save(pygame.display.get_surface(), f"{S}/sinnoh_live3d_{key}_{i}.png")

print("4b) S3: Eterna Gym's flower clock, live in each of its five states (the hands are Platinum's own models, turned)")
CLOCK_FLAGS = ("gym_trainer_ETERNA_CITY_1", "gym_trainer_ETERNA_CITY_2", "gym_trainer_ETERNA_CITY_3")
_had = {k: story.story_flags.get(k) for k in CLOCK_FLAGS}
_badge = story.has_badge("Forest Badge") if hasattr(story, "has_badge") else None
for s in range(4):   # (state 4 = after Gardenia: needs the badge, and its scene is checked the same way below)
    for i, k in enumerate(CLOCK_FLAGS):
        story.story_flags[k] = i < s
    t = town("ETERNA_CITY", "gym")
    if getattr(t, "room", None) != "gym":
        check(False, f"clock state {s}: the Gym could not be entered by the check"); continue
    lv = t._live()
    from src.dungeon import art as _art
    pic = _art._version_file(_TM["ETERNA_CITY"]["rooms"]["gym"]["roofs"]["_picture"]) or ""
    check(bool(lv) and pic.endswith(f"_clock{s}.png"), f"clock state {s}: live, on its own scene ({pic})")
    if not lv:
        continue
    sc = lv[0]
    opens = {(x, y) for y in range(t.h) for x in range(t.w) if t._open((x, y))}
    check(not sc.holes([(x, int(round(sc.wz(x, y)))) for x, y in opens]), f"clock state {s}: floor under every tile you can walk ({len(opens)})")
    settle(2)
    pygame.image.save(pygame.display.get_surface(), f"{S}/sinnoh_live3d_eterna_clock{s}.png")
for s in range(5):
    check(live3d.scene_of(g, f"pt_ground/C04GYM0101_clock{s}.png", [0, 0]) is not None, f"clock state {s}: its scene was exported")
for k, v in _had.items():
    if v is None:
        story.story_flags.pop(k, None)
    else:
        story.story_flags[k] = v

print("5) the checks-only switch off: Twinleaf still loads and draws")
g.live3d = False
t = town("TWINLEAF_TOWN"); t.draw()
check(not t._live(), "live camera switched off: Twinleaf draws without its scene, no crash")
g.live3d = True

print(f"##### {len(fails)} failures")
