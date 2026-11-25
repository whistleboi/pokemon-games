# Sinnoh's walkable maps (dev/builders/town_maps/sinnoh.py), entered the way a player would.
#   cat dev/checks/harness_head.py dev/checks/sinnoh_maps_body.py > dev/checks/out/check_sinnoh_maps.py
#   python dev/checks/out/check_sinnoh_maps.py <scratch dir>
from src.states.overworld import PlayState, CityState as _CS
from src.states.overworld.dungeon import DungeonState
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.dungeon import core

fails = 0
g.dungeon_routes = True
g.walk_towns = True


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


def frames(p, n=1):
    for _ in range(n):
        g.current_state.update()
        g.current_state.draw()


def _tap_through(st, n=400):
    """Tap through whatever the town says first, as a player would."""
    for _ in range(n):
        if not getattr(st, "npc_active", False):
            return
        st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        frames(st)


def town(area, came):
    g.walk_town_pos = None
    story.current_area_key, story.last_area_key = area, came
    st = _CS(g); g.change_state(st); _tap_through(st)
    return st


def route(area, came):
    story.current_area_key, story.last_area_key = area, came
    story.player_team = [mk(387)]
    story.player_team[0].level = 12
    story.balls_left = 20
    p = PlayState(g)
    g.states["play"] = p
    g.change_state(p)
    frames(p, 3)
    return p


story.story_flags["received_starter_sinnoh"] = True

# ---- Twinleaf Town
t = town("TWINLEAF_TOWN", "SINNOH_ROUTE_201")
check(isinstance(t, _WTS) and (t.w, t.h) == (32, 32) and t.player[1] <= 2 and set(t.exits.values()) == {"SINNOH_ROUTE_201"},
      f"Twinleaf Town: walked, 32 x 32; in from Route 201 at the top {t.player}")
check({"home", "rival"} <= set(t.doors.values()) and t._door_options("home") and t._door_options("rival"),
      f"Twinleaf Town: your house opens Mom, the house top left opens your friend's ({sorted(set(t.doors.values()))})")
_home = min(p for p, k in t.doors.items() if k == "home")
check(_home == (20, 21) and next(p for p, k in t.doors.items() if k == "rival") == (9, 11), f"Twinleaf Town: your door bottom right {_home}, your friend's top left")
t.walk_goal = _home
for _k in range(400):
    frames(t)
check(t.room == "home" or abs(t.player[0] - _home[0]) + abs(t.player[1] - _home[1]) <= 1,
      f"Twinleaf Town: you can walk from the top of town to your own door, and in ({t.room}, {t.player})")

# ---- Route 201
r = route("SINNOH_ROUTE_201", "TWINLEAF_TOWN")
f = r.run.floor
check(isinstance(r, DungeonState) and (f.w, f.h) == (64, 24) and r.run.player[1] >= 21 and 14 <= r.run.player[0] <= 17
      and set(f.exits.values()) == {"TWINLEAF_TOWN", "SANDGEM_TOWN", "VERITY_LAKEFRONT"},
      f"Route 201: 64 x 24; in from Twinleaf at the bottom {r.run.player}; Sandgem east, the lakefront west")
check(sum(v == "ledge:0,1" for v in f.decor.values()) >= 30, "Route 201: the long ledge is a one-way hop south")
r = route("SINNOH_ROUTE_201", "SANDGEM_TOWN")
check(r.run.player[0] >= 62, f"Route 201: in from Sandgem at the east edge {r.run.player}")
r = route("SINNOH_ROUTE_201", "VERITY_LAKEFRONT")
check(r.run.player[0] <= 1, f"Route 201: in from the lakefront at the west edge {r.run.player}")

# ---- Verity Lakefront and Lake Verity
r = route("VERITY_LAKEFRONT", "SINNOH_ROUTE_201")
f = r.run.floor
check(isinstance(r, DungeonState) and (f.w, f.h) == (22, 17) and r.run.player[0] >= 20 and set(f.exits.values()) == {"SINNOH_ROUTE_201", "LAKE_VERITY"} and "ledge:-1,0" in f.decor.values(),
      f"Verity Lakefront: 22 x 17; in from Route 201 at the east edge {r.run.player}; the lake north")
r = route("LAKE_VERITY", "VERITY_LAKEFRONT")
f = r.run.floor
check(isinstance(r, DungeonState) and r.run.n_floors == 2 and r.run.index == 0 and (f.w, f.h) == (50, 44) and r.run.player[1] >= 39
      and "VERITY_LAKEFRONT" in f.exits.values() and core.STAIRS in f.exits.values(),
      f"Lake Verity: the lake (50 x 44) and Verity Cavern under its island; in from the lakefront at the bottom {r.run.player}")
check(sum(row.count(core.SURF) for row in f.tiles) > 600, "Lake Verity: the lake is Surf water")
_lv = __import__("json").load(open("assets/town_maps.json", encoding="utf-8"))["LAKE_VERITY"]
check(_lv["figure_floors"].get("Confront Galactic at the Lake") == 0 and _lv["figure_floors"].get("Mesprit's Lair") == 1 and _lv["floors"][1]["people"] == ["Mesprit's Lair"],   # (11-19: the shore's item ball stands there too)
      "Lake Verity: Team Galactic stand on the shore, Mesprit inside the cavern")

# ---- Sandgem Town
t = town("SANDGEM_TOWN", "SINNOH_ROUTE_201")
check(isinstance(t, _WTS) and (t.w, t.h) == (32, 32) and t.player[0] <= 1 and set(t.exits.values()) == {"SINNOH_ROUTE_201", "SINNOH_ROUTE_202", "SINNOH_ROUTE_219"},
      f"Sandgem Town: walked, 32 x 32; in from Route 201 at the west edge {t.player}")
check({"center", "mart", "lab", "assistant"} <= set(t.doors.values()) and all(t._door_options(k) for k in ("center", "mart", "lab", "assistant")),
      f"Sandgem Town: the Center, the Mart, Rowan's Lab and the assistant's house each open their own option ({sorted(set(t.doors.values()))})")
t = town("SANDGEM_TOWN", "SINNOH_ROUTE_202")
check(t.player[1] <= 1, f"Sandgem Town: in from Route 202 at the top {t.player}")

# ---- Route 202
r = route("SINNOH_ROUTE_202", "SANDGEM_TOWN")
f = r.run.floor
check(isinstance(r, DungeonState) and (f.w, f.h) == (32, 32) and r.run.player[1] >= 30 and set(f.exits.values()) == {"SANDGEM_TOWN", "JUBILIFE_CITY"}
      and sum(v == "ledge:0,1" for v in f.decor.values()) >= 10,
      f"Route 202: 32 x 32; in from Sandgem at the bottom {r.run.player}; Jubilife north; its ledges hop south")
check(len(g.loader.area_data["STORY_PROGRESSION"]["SINNOH_ROUTE_202"]["trainer_pool"]) == 3 and sum(m.kind == "trainer" for m in f.movers) == 3,
      f"Route 202: its three trainers stand on the map ({[m.kind for m in f.movers]})")

# ---- Jubilife City
t = town("JUBILIFE_CITY", "SINNOH_ROUTE_202")
check(isinstance(t, _WTS) and (t.w, t.h) == (64, 64) and t.player[1] >= 61
      and set(t.exits.values()) == {"SINNOH_ROUTE_202", "SINNOH_ROUTE_203", "SINNOH_ROUTE_204", "SINNOH_ROUTE_218"},
      f"Jubilife City: walked, 64 x 64; in from Route 202 at the bottom {t.player}; ways out on all four sides")
check({"center", "mart", "poketch", "gts", "school"} <= set(t.doors.values()) and all(t._door_options(k) for k in ("center", "mart", "poketch", "gts")),
      f"Jubilife City: the Center, Mart, Poketch Company and Global Terminal each open their own option ({sorted(set(t.doors.values()))})")
_school = next(p for p, k in t.doors.items() if k == "school")
check(_school == (40, 40), f"Jubilife City: the Trainers' School's door is on its porch {_school}")
t = town("JUBILIFE_CITY", "SINNOH_ROUTE_203")
check(t.player[0] >= 62, f"Jubilife City: in from Route 203 at the east edge {t.player}")

# ---- Route 203 and Oreburgh Gate
r = route("SINNOH_ROUTE_203", "JUBILIFE_CITY")
f = r.run.floor
check(isinstance(r, DungeonState) and (f.w, f.h) == (64, 22) and r.run.player[0] <= 1 and set(f.exits.values()) == {"JUBILIFE_CITY", "OREBURGH_GATE"},
      f"Route 203: 64 x 22; in from Jubilife at the west edge {r.run.player}; the Gate's cave mouth east")
r = route("SINNOH_ROUTE_203", "OREBURGH_GATE")
check(r.run.player[0] >= 50, f"Route 203: out of the Gate by the cave mouth {r.run.player}")
r = route("OREBURGH_GATE", "SINNOH_ROUTE_203")
f = r.run.floor
check(isinstance(r, DungeonState) and (f.w, f.h) == (30, 27) and r.run.player[0] <= 4 and set(f.exits.values()) - {"STAIRS"} == {"SINNOH_ROUTE_203", "OREBURGH_CITY"},
      f"Oreburgh Gate: 30 x 27; in from Route 203 at the west mouth {r.run.player}; Oreburgh east")
_st = next((t for t, v in f.exits.items() if v == "STAIRS"), None)   # (11-23 S2: Platinum's B1F, down the stairs at 1F (18,3))
if _st:
    r._warp(1, 1, 1); frames(r, 2)
check(_st == (18, 3) and r.run.index == 1 and r.run.n_floors == 2, f"Oreburgh Gate: the stairs down to B1F ({_st}, floor {r.run.index} of {r.run.n_floors})")
r = route("OREBURGH_GATE", "OREBURGH_CITY")
check(r.run.player[0] >= 25, f"Oreburgh Gate: in from Oreburgh at the east mouth {r.run.player}")

# ---- Oreburgh City
t = town("OREBURGH_CITY", "OREBURGH_GATE")
check(isinstance(t, _WTS) and (t.w, t.h) == (64, 62) and t.player[0] <= 3
      and set(t.exits.values()) == {"OREBURGH_GATE", "SINNOH_ROUTE_207", "OREBURGH_MINE"},
      f"Oreburgh City: walked, 64 x 62; in from the Gate at the west {t.player}; Route 207 north, the mine south")
check({"center", "mart", "gym", "museum"} <= set(t.doors.values()) and all(t._door_options(k) for k in ("center", "mart", "gym", "museum")),
      f"Oreburgh City: the Center, Mart, Gym and Mining Museum each open their own option ({sorted(set(t.doors.values()))})")
_mine = [p for p, v in t.exits.items() if v == "OREBURGH_MINE"]
t.walk_goal = _mine[0]
for _k in range(900):
    frames(t)
    if g.current_state is not t:
        break
check(g.current_state is not t or abs(t.player[0] - _mine[0][0]) + abs(t.player[1] - _mine[0][1]) <= 1,
      f"Oreburgh City: you can walk from the Gate, through town and down the steps to the mine mouth ({t.player})")

# ---- Oreburgh's conveyor belts, overhead
_tm = __import__("json").load(open("assets/town_maps.json", encoding="utf-8"))
_ov = _tm["OREBURGH_CITY"].get("overheads", [])
check(len(_ov) == 1 and _ov[0]["kind"] == "belt" and len(_ov[0]["runs"]) > 30 and len(t.overheads) == 1,
      "Oreburgh City: the mine's conveyor belts are an overhead layer you walk under")

# ---- Oreburgh Mine
r = route("OREBURGH_MINE", "OREBURGH_CITY")
check(isinstance(r, DungeonState) and r.run.n_floors == 2 and r.run.index == 0 and r.run.player[1] <= 3 and "OREBURGH_CITY" in r.run.floor.exits.values() and "STAIRS" in r.run.floor.exits.values(),
      f"Oreburgh Mine: two floors; in from Oreburgh at the mouth on 1F {r.run.player}; the way down to B1F")

# ---- Route 204 and Ravaged Path (cracked rocks: Rock Smash)
r = route("SINNOH_ROUTE_204", "JUBILIFE_CITY")
f = r.run.floor
check(isinstance(r, DungeonState) and (f.w, f.h) == (32, 64) and r.run.player[1] >= 62 and set(f.exits.values()) == {"JUBILIFE_CITY", "FLOAROMA_TOWN", "RAVAGED_PATH"},
      f"Route 204: 32 x 64; in from Jubilife at the bottom {r.run.player}; Floaroma north, Ravaged Path's two mouths")
r = route("SINNOH_ROUTE_204", "FLOAROMA_TOWN")
check(r.run.player[1] <= 1, f"Route 204: in from Floaroma at the top {r.run.player}")
_had = story.inventory.get("HM_ROCK_SMASH", 0)
story.inventory["HM_ROCK_SMASH"] = 0
r = route("RAVAGED_PATH", "SINNOH_ROUTE_204")
f = r.run.floor
_cr = [t for t, v in f.decor.items() if str(v).startswith("crack:")]
check((f.w, f.h) == (32, 52) and len(_cr) >= 20 and all(not f.walkable(*t) for t in _cr) and set(f.exits.values()) == {"SINNOH_ROUTE_204"},
      f"Ravaged Path: 32 x 52; without Rock Smash its {len(_cr)} cracked rocks are in the way")
story.inventory["HM_ROCK_SMASH"] = 1
_rs_bv = list(story.badges.get("SINNOH", []))
story.badges["SINNOH"] = sorted(set(story.badges.get("SINNOH", [])) | {"COAL"})   # (Platinum: Rock Smash needs the Coal Badge on the map; Jordan 11-24)
r = route("RAVAGED_PATH", "SINNOH_ROUTE_204")
f = r.run.floor
check(not any(str(v).startswith("crack:") for v in f.decor.values()) and all(f.walkable(*t) for t in _cr),
      "Ravaged Path: with Rock Smash the cracked rocks are broken and you can walk through")
_ex = sorted(f.exits, key=lambda t: (t[1], t[0]))
_seen, _todo = {_ex[0]}, [_ex[0]]
while _todo:
    _x, _y = _todo.pop()
    for _dx, _dy in core.DIRS:
        _n = (_x + _dx, _y + _dy)
        if _n not in _seen and 0 <= _n[0] < f.w and 0 <= _n[1] < f.h and f.walkable(*_n) and f.tiles[_n[1]][_n[0]] != core.SURF:
            _seen.add(_n); _todo.append(_n)
check(_ex[1] in _seen, f"Ravaged Path: then its two mouths join on foot ({_ex[0]} to {_ex[1]})")
story.badges["SINNOH"] = _rs_bv
story.inventory["HM_ROCK_SMASH"] = _had

# ---- Floaroma Town and Meadow
t = town("FLOAROMA_TOWN", "SINNOH_ROUTE_204")
check(isinstance(t, _WTS) and (t.w, t.h) == (32, 34) and t.player[1] >= 31
      and set(t.exits.values()) == {"SINNOH_ROUTE_204", "SINNOH_ROUTE_205", "FLOAROMA_MEADOW"},
      f"Floaroma Town: walked, 32 x 34; in from Route 204 at the bottom {t.player}; Route 205 east, the Meadow west")
check({"center", "mart", "flower"} <= set(t.doors.values()) and all(t._door_options(k) for k in ("center", "mart", "flower")),
      f"Floaroma Town: the Center, Mart and Flower Shop each open their own option ({sorted(set(t.doors.values()))})")
r = route("FLOAROMA_MEADOW", "FLOAROMA_TOWN")
f = r.run.floor
check(isinstance(r, DungeonState) and (f.w, f.h) == (64, 64) and r.run.player[1] >= 50 and r.run.player[0] <= 15
      and {v for v in f.exits.values() if not str(v).startswith("WARP:")} == {"FLOAROMA_TOWN", "FUEGO_IRONWORKS"} and sum(v == "ledge:0,1" for v in f.decor.values()) >= 30,
      f"Floaroma Meadow: 64 x 64; in from Floaroma at the south-west gap {r.run.player}; the long ledge hops south")

# ---- every Sinnoh map: it opens as a walked map, and coming in from each neighbour puts you by that neighbour's way out
_prog = g.loader.area_data["STORY_PROGRESSION"]
_sin = [k for k in _tm if k in _prog and str(_prog[k].get("region", "")).upper() == "SINNOH"]
_bad, _far, _n = [], [], 0
story.inventory["HM_ROCK_SMASH"] = story.inventory.get("HM_ROCK_SMASH", 0) or 1
story.inventory["HM_SURF"] = story.inventory.get("HM_SURF", 0) or 1   # (some neighbours are met across water)
for _k in _sin:
    _m = _tm[_k]
    _targets = sorted({v for f in (_m.get("floors") or [_m]) for v in (f.get("exits") or {}).values()})
    _is_town = _prog[_k].get("area_type") == "town"
    for _t in _targets or [None]:
        try:
            _st = town(_k, _t) if _is_town else route(_k, _t)
            _n += 1
            if _is_town:
                if not isinstance(_st, _WTS):
                    _bad.append((_k, "not a walked town")); break
                _ex, _pl = _st.exits, _st.player
            else:
                if not isinstance(_st, DungeonState):
                    _bad.append((_k, "not a map")); break
                _ex, _pl = _st.run.floor.exits, _st.run.player
            _near = [abs(x - _pl[0]) + abs(y - _pl[1]) for (x, y), v in _ex.items() if v == _t]
            if _t and _t in _tm and (not _near or min(_near) > 3):
                _far.append((_k, _t, tuple(_pl)))
        except Exception as _e:
            _bad.append((_k, _t, repr(_e)[:90]))
check(not _bad, f"every Sinnoh map opens as a walked map, entered from each of its neighbours ({len(_sin)} areas, {_n} ways in) {_bad[:6]}")
check(not _far, f"coming in from a neighbour puts you beside that neighbour's way out {_far[:8]}")

# ---- passages between any two floors (a map's "links"): Mt. Coronet's inner stairs, Galactic HQ's warp panels, the Ruins' side rooms
_lk_bad, _lk_n = [], 0
for _k in _sin:
    _fl = _tm[_k].get("floors") or []
    if not any(f.get("links") for f in _fl):
        continue
    for _i, _f in enumerate(_fl):
        for _at, (_j, _x, _y) in (_f.get("links") or {}).items():
            _lk_n += 1
            if not (0 <= _j < len(_fl) and 0 <= _y < len(_fl[_j]["art"]) and 0 <= _x < len(_fl[_j]["art"][0])):
                _lk_bad.append((_k, _i, _at, "lands off the map")); continue
            _ax, _ay = (int(v) for v in _at.split(","))
            if _f["art"][_ay][_ax] != "1":
                _lk_bad.append((_k, _i, _at, "no passage tile"))
check(_lk_n > 60 and not _lk_bad, f"every passage between floors has a tile at its near end and lands on its far floor ({_lk_n} passages) {_lk_bad[:5]}")
r = route("MT_CORONET_BASE", "SINNOH_ROUTE_207")
_walked = []
for _k2 in ("MT_CORONET_BASE", "TEAM_GALACTIC_HQ", "SOLACEON_RUINS"):
    r = route(_k2, None)
    _fl = _tm[_k2]["floors"]
    _i = next(i for i, f in enumerate(_fl) if f.get("links"))
    _at, (_j, _x, _y) = next(iter(_fl[_i]["links"].items()))
    _ax, _ay = (int(v) for v in _at.split(","))
    r.run.warp(_i, _ax, _ay)                                     # stand beside the passage's near end...
    _px, _py = r.run.player
    _ev = r.run.step(_ax - _px, _ay - _py)                       # ...and step onto it
    _is_warp = any(e[0] == "warp" for e in _ev)
    r._handle(_ev); talk(r) if "talk" in globals() else None
    for _q in range(40):
        if getattr(r, "dialogue_box", None) and r.dialogue_box.visible:
            r.dialogue_box.advance()
        frames(r)
    _walked.append((_k2, _is_warp, r.run.index == _j, abs(r.run.player[0] - _x) + abs(r.run.player[1] - _y) <= 1 or r.run.player == r.run.floor.start, r.run.floor.walkable(*r.run.player)))   # (beside the far end; the floor's own start if something stands there)
check(all(all(w[1:]) for w in _walked), f"stepping onto a passage takes you to its far end on the other floor {_walked}")

# ---- bridges with two levels: over along the deck, under across it (routes and towns)
r = route("SINNOH_ROUTE_206", "ETERNA_CITY")
f = r.run.floor
check(len(f.bridge) > 500 and set(f.bridge.values()) == {(0, 1)} and _tm["SINNOH_ROUTE_206"]["roofs"].get("_bridge") == "steel",
      f"Route 206: the Cycling Road is one long two-level bridge running north-south ({len(f.bridge)} tiles), drawn in steel")
_side = next(((x, y), dx) for (x, y) in sorted(f.bridge) for dx in (-1, 1) if (x + dx, y) not in f.bridge and f.walkable(x + dx, y) and f.tiles[y][x + dx] != core.SURF)
(_bx, _by), _dx = _side
r.run.player = (_bx + _dx, _by); r.run.deck = True
_ev = r.run.step(-_dx, 0)
_under = (r.run.player == (_bx, _by) and r.run.deck is False)
_x = _bx
while (_x - _dx, _by) in f.bridge:
    _x -= _dx
r.run.player = (_x, _by)
_out = r.run.step(-_dx, 0) if f.walkable(_x - _dx, _by) else [("moved",)]
check(_under and _out[0][0] != "blocked", f"Route 206: from the route below you pass under the Cycling Road and out the far side ({_side})")
r.run.player = (_bx, _by); r.run.deck = True                     # up on the deck...
_off = r.run.step(_dx, 0)
check(_off[0][0] == "blocked", "Route 206: up on the Cycling Road you can't step off its side")
# (11-18: under the wide Cycling Road every bridge tile you and your Pokemon overlap is drawn back over you, not just
#  the one at your feet; it's in the Platinum picture, so the map's own tile is copied back)
from src.states.overworld.dungeon import TILE
_w = next(((x, y), dx) for (x, y) in sorted(f.bridge) for dx in (-1, 1)
          if (x + dx, y) not in f.bridge and f.walkable(x + dx, y) and f.tiles[y][x + dx] != core.SURF
          and (x - dx, y) in f.bridge and (x - 2 * dx, y) in f.bridge and (x, y - 1) in f.bridge and (x - dx, y - 1) in f.bridge)
(_wx, _wy), _wd = _w
r.run.player = (_wx + _wd, _wy); r.run.deck = True
r.anim_from = r.partner = r.partner_from = r.run.player
f.seen |= {(x, y) for x in range(f.w) for y in range(f.h)}
f.movers = [m for m in f.movers if abs(m.x - _wx) > 6 or abs(m.y - _wy) > 6]   # (nobody wandering into the tiles looked at)


def _bare(tiles):
    """Each tile on screen is just the map (nobody drawn over it)."""
    ox, oy = r._origin()
    out = []
    for tx, ty in tiles:
        a = pygame.Surface((TILE, TILE)); a.blit(g.screen, (0, 0), pygame.Rect(ox + tx * TILE, oy + ty * TILE, TILE, TILE))
        b = pygame.Surface((TILE, TILE)); b.blit(r._floor_surf, (0, 0), pygame.Rect(tx * TILE, ty * TILE, TILE, TILE))
        out.append(pygame.image.tobytes(a, "RGB") == pygame.image.tobytes(b, "RGB"))
    return out


_mid = None
for _s in range(2):
    r.step(-_wd, 0)
    if _s == 1:
        r.anim = max(1, r.anim // 2); r.draw()
        _mid = _bare([r.anim_from, r.run.player, (r.run.player[0], _wy - 1), (r.anim_from[0], _wy - 1)])
    for _q in range(20):
        r.update()
r.banner = 0; r.draw()
_cov = _bare([r.run.player, (r.run.player[0], _wy - 1), tuple(r.partner)])
check(r.run.deck is False and all(_cov) and _mid and all(_mid),
      f"Route 206: under the Cycling Road you, your head and your Pokemon are all hidden, mid-step too ({_w} {_cov} {_mid})")
r.run.deck = True; r.draw()
check(not all(_bare([r.run.player, (r.run.player[0], _wy - 1)])), "Route 206: up on the Cycling Road at the same spot you're drawn over it")
t = town("CANALAVE_CITY", "SINNOH_ROUTE_218")
_br = sorted(k for k, v in t.bridge.items() if v == (1, 0))        # (the pier by the boats is a short one of its own, running north-south)
check(len(_br) >= 20, f"Canalave City: the drawbridge is a two-level bridge running east-west ({len(_br)} tiles)")
_y = _br[0][1]; _x0 = min(x for x, y in _br if y == _y); _x1 = max(x for x, y in _br if y == _y)
t.player = (_x0 - 1, _y); t.deck = True
for _q in range((_x1 - _x0 + 2) * 12):
    t.step(1, 0); frames(t)
check(t.player[0] >= _x1 + 1 and t.deck, f"Canalave City: you walk across the drawbridge from the west bank to the east ({t.player})")
t = town("SUNYSHORE_CITY", "SINNOH_ROUTE_222")
check(len(t.bridge) > 250 and _tm["SUNYSHORE_CITY"]["roofs"].get("_bridge") == "solar", f"Sunyshore City: the solar walkways are two-level bridges ({len(t.bridge)} tiles)")

# ---- the named buildings of the later towns each open their own option
_doors = {"ETERNA_CITY": ["bike", "gym", "center", "mart"], "HEARTHOME_CITY": ["contest", "amity", "poffin", "gym"], "SOLACEON_TOWN": ["daycare", "center"],
          "VEILSTONE_CITY": ["game corner", "mart", "gym"], "CELESTIC_TOWN": ["elder", "center"], "SUNYSHORE_CITY": ["gym", "center"],
          "CANALAVE_CITY": ["library", "gym"], "PASTORIA_CITY": ["gym", "center", "mart"], "SNOWPOINT_CITY": ["gym", "center"]}
_dbad = []
story.story_flags["galactic_eterna_cleared"] = True                # (the Bike Shop opens once its owner is freed)
for _k, _want in _doors.items():
    t = town(_k, None)
    for _d in _want:
        if _d not in t.doors.values():
            _dbad.append((_k, _d, "no such door"))
        elif not t._door_options(_d):
            _dbad.append((_k, _d, "opens nothing"))
t = town("CELESTIC_TOWN", None)
if "ruins" not in (t.town_map.get("inside") or {}).values():   # (S4 11-24: the ruins are Platinum's room now, behind their doorway; no menu person)
    _dbad.append(("CELESTIC_TOWN", "ruins", "no such door"))
t = town("SUNYSHORE_CITY", None)
if "lighthouse" not in (t.town_map.get("inside") or {}).values():   # (S6 11-24: the Vista Lighthouse is Platinum's rooms now, behind its door; no menu person)
    _dbad.append(("SUNYSHORE_CITY", "lighthouse", "no such door"))
check(not _dbad, f"the later towns' named buildings each open their own option ({sum(len(v) for v in _doors.values())} doors) {_dbad}")

# ---- the games' own paths: what stands in the way till you have the move, the special floors, the opening walk to the lake
_inv0 = dict(story.inventory)
for _it in ("HM_CUT", "HM_ROCK_SMASH", "BICYCLE", "HM_STRENGTH"):
    story.inventory[_it] = 0
g.__dict__.pop("_walk_town_imgs", None)
t = town("ETERNA_CITY", None)
_trees = [(x, y) for y, row in enumerate(_tm["ETERNA_CITY"]["art"]) for x, c in enumerate(row) if c == "2"]
_gate = [p for p in _trees if p[1] == 9]
check(len(_gate) == 3 and all(not t._open(p) for p in _gate), f"Eterna City: without Cut, three small trees shut the Galactic building's yard {_gate}")
story.inventory["HM_CUT"] = 1
_cut_bv = list(story.badges.get("SINNOH", []))
story.badges["SINNOH"] = sorted(set(story.badges.get("SINNOH", [])) | {"FOREST"})   # (Platinum: Cut needs the Forest Badge on the map)
t = town("ETERNA_CITY", None)
check(all(t._open(p) for p in _gate), "Eterna City: with Cut the trees are gone and you can walk in")
story.inventory["HM_CUT"] = 0
r = route("SINNOH_ROUTE_212", "HEARTHOME_CITY")
_cut = [p for p, v in r.run.floor.decor.items() if str(v).startswith("cut:")]
story.inventory["HM_CUT"] = 1
r = route("SINNOH_ROUTE_212", "HEARTHOME_CITY")
check(len(_cut) >= 8 and not any(str(v).startswith("cut:") for v in r.run.floor.decor.values()) and all(r.run.floor.walkable(*p) for p in _cut),
      f"Route 212: its {len(_cut)} small trees are in the way until you have Cut")
story.badges["SINNOH"] = _cut_bv
r = route("WAYWARD_CAVE", "SINNOH_ROUTE_206")
_sl = [p for f in _tm["WAYWARD_CAVE"]["floors"] for row in f["art"] for p in row if p == "7"]
check(len(_sl) >= 10, f"Wayward Cave: {len(_sl)} tiles of steep muddy slope need the Bicycle")
r = route("VICTORY_ROAD_SINNOH", "SINNOH_POKEMON_LEAGUE")
_nb = sum(len(f.get("boxes") or []) for f in _tm["VICTORY_ROAD_SINNOH"]["floors"])   # (S6: pushed boulders now, the floors' "boxes")
check(_nb >= 20, f"Victory Road: {_nb} Strength boulders stand where the game has them")
# Victory Road 2F: Platinum's bike ramps (0xD7 ridden east, 0xD8 west): a short hop in normal gear, a long jump in top gear
# (Shift held), the only ways into the north-west pockets (the Max Elixir's room), the Full Restore's and TM71's ledges.
import src.states.overworld.dungeon as _dnm
_rr = route("VICTORY_ROAD_SINNOH", "SINNOH_POKEMON_LEAGUE")
_rr.run.jump_floor(0, (49, 16))
_f0 = _rr.run.floor
_ramps = {p: v for p, v in _f0.decor.items() if str(v).startswith("ramp:")}
check(len(_ramps) == 9 and list(_ramps.values()).count("ramp:1,0") == 1 and _ramps.get((9, 9)) == "ramp:1,0" and _ramps.get((6, 15)) == "ramp:-1,0",
      f"Victory Road 2F: Platinum's nine bike ramps, one ridden east and eight west ({sorted(_ramps.items())[:3]}...)")
_m0, _f0.movers = _f0.movers, []
_run0 = _dnm.running
_bike0 = story.inventory.get("BICYCLE", 0)


def _jump(frm, d, far, bike=True):
    story.inventory["BICYCLE"] = 1 if bike else 0
    _dnm.running = (lambda: far)
    _rr.run.player = frm; _rr.anim = 0; _rr.hop = None; _rr.sliding = None; _rr.walk_goal = None
    _rr.dialogue_box.visible = False if hasattr(_rr, "dialogue_box") else None
    _rr.step(*d)
    return tuple(_rr.run.player)


_nobike = _jump((8, 9), (1, 0), False, bike=False)
_short = _jump((8, 9), (1, 0), False)
_long = _jump((8, 9), (1, 0), True)
_back = _jump((10, 9), (-1, 0), False)
check(_nobike == (8, 9) and _short == (10, 9) and _long == (12, 9) and _back == (10, 9),
      f"Victory Road 2F: the north-west ramp, ridden east: a hop to the Max Elixir's corridor {_short}, a long jump to the ledge strip {_long}; "
      f"not on foot {_nobike}, not from its far side {_back}")
_in = _jump((7, 15), (-1, 0), True)
_hop = _jump((7, 15), (-1, 0), False)
_wrong = _jump((5, 15), (1, 0), True)
check(_in == (3, 15) and _hop == (5, 15) and _wrong == (5, 15),
      f"Victory Road 2F: the first ramp's long jump crosses the wall into the west room {_in} (a hop lands short {_hop}; never ridden backwards {_wrong})")
_fr = _jump((49, 15), (-1, 0), True)
_tm71 = _jump((41, 22), (-1, 0), True)
check(_fr == (45, 15) and _tm71 == (37, 22), f"Victory Road 2F: long jumps reach the Full Restore's room {_fr} and TM71's ledge {_tm71}")
_rock = _f0.decor.pop((8, 9), None); _f0.tiles[9][8] = core.FLOOR   # (the Rock Smash rock before the ramp, broken; the Journal's route finder
_rr._clear_boulders = lambda: None                                          #  would wait for Rock Smash, as the game does)
_way = _rr._step_route((0, 7, 15), {(0, 3, 4)}, "Max Elixir", reach=True)   # (from beside the first ramp: everything you can get to)
story.inventory["BICYCLE"] = 0
_walk = _rr._step_route((0, 7, 15), {(0, 3, 4)}, "Max Elixir", reach=True)
story.inventory["BICYCLE"] = 1
_dnm.running = _run0
check((0, 3, 15) in _way and (0, 3, 4) in _way and (0, 12, 9) in _way and (0, 3, 4) not in _walk,
      f"Victory Road 2F: the Journal's route finder rides the ramps to the Max Elixir's room (not on foot)")
story.inventory["BICYCLE"] = _bike0
_f0.decor[(8, 9)] = _rock; _f0.tiles[9][8] = core.WALL
del _rr._clear_boulders
_f0.movers = _m0
r = route("FUEGO_IRONWORKS", "SINNOH_ROUTE_205")
_spin = sum(row.count(c) for row in _tm["FUEGO_IRONWORKS"]["floors"][1]["art"] for c in "3456")
r._descend(); frames(r, 2)
_cur = r.run.floor.current
check(_spin >= 50 and len(_cur) == _spin and set(_cur.values()) == {(-1, 0), (1, 0), (0, -1), (0, 1)}, f"Fuego Ironworks: {_spin} spin tiles carry you across its floor, all four ways")
story.repel_routes = max(getattr(story, "repel_routes", 0), 1)   # (11-19: no wild Pokemon on the step, and a spin tile nobody
_p0 = next(p for p, v in sorted(_cur.items()) if r.run.floor.walkable(p[0] - v[0], p[1] - v[1]) and (p[0] - v[0], p[1] - v[1]) not in _cur   #  is standing on or near - the
           and not any(abs(m.x - p[0]) + abs(m.y - p[1]) <= 3 for m in r.run.floor.movers if m.kind != "player"))   #  Ironworks' people walk about)
r.run.player = (_p0[0] - _cur[_p0][0], _p0[1] - _cur[_p0][1])
r.step(*_cur[_p0]) if hasattr(r, "step") else None
for _q in range(120):
    frames(r)
check(r.run.player != _p0 and r.run.player != (_p0[0] - _cur[_p0][0], _p0[1] - _cur[_p0][1]), f"Fuego Ironworks: stepping onto a spin tile sends you on past it ({_p0} to {r.run.player})")
story.inventory.clear(); story.inventory.update(_inv0)
_data_only = {"JUBILIFE_VILLAGE", "HALL_OF_ORIGIN", "SPEAR_PILLAR_RIFT", "DISTORTION_WORLD", "SEA_TEMPLE", "TURNBACK_CAVE", "SENDOFF_SPRING"}
_jump = [(k, o.get("target_area")) for k in _sin for o in _prog[k].get("route_menu", []) + _prog[k].get("travel_options", [])
         if o.get("target_area") and o["target_area"] not in {v for f in (_tm[k].get("floors") or [_tm[k]]) + list((_tm[k].get("rooms") or {}).values())
                                                              for v in (f.get("exits") or {}).values()}   # (a gatehouse's far door counts: the Frontier's gate, 11-22)
         and o["target_area"] in _tm]
check(not _jump, f"the area data lists no jump between two mapped places that aren't joined on the maps {_jump[:6]}")
_sv = dict(story.story_flags); _team = list(story.player_team)
story.story_flags.pop("received_starter_sinnoh", None)
t = town("TWINLEAF_TOWN", None)
check("SINNOH_ROUTE_201" in t.exits.values() and "LAKE_VERITY" not in [o.get("target_area") for o in _prog["TWINLEAF_TOWN"]["travel_options"]],
      "Twinleaf Town: before your first Pokemon you set out by Route 201 (no jump to the lake)")
story.story_flags.clear(); story.story_flags.update(_sv); story.player_team = _team

# ---- the story's blockers stand where Platinum has them, and step aside when the story says
_sv = dict(story.story_flags); _bd = {k: list(v) for k, v in story.badges.items()}; _inv0 = dict(story.inventory); _dt = dict(story.defeated_trainers)
def _blocked(key, came, look=None):
    r = route(key, came)
    mine = {tuple(t) for b in (_tm[key].get("barred") or [q for f in _tm[key].get("floors", []) for q in f.get("barred", [])])
            if look is None or b.get("look") == look or (look == "BICYCLE" and b.get("item") == "BICYCLE") for t in b["tiles"]}
    return r, [t for t, v in r.run.floor.decor.items() if str(v).startswith("barrier:") and t in mine]
story.badges["SINNOH"] = []
r, _ps = _blocked("SINNOH_ROUTE_210", "SOLACEON_TOWN", "psyduck")
_reach = core.on_foot(r.run.floor, r.run.player)
_cel = [t for t, v in r.run.floor.exits.items() if v == "CELESTIC_TOWN"]
check(len(_ps) == 4 and all(not r.run.floor.walkable(*t) for t in _ps) and _cel and not any(t in _reach for t in _cel),
      f"Route 210: without the Fen Badge four Psyduck fill the path north, and Celestic can't be reached from Solaceon")
frames(r, 3)
story.badges["SINNOH"] = ["COAL", "FOREST", "RELIC", "COBBLE", "FEN", "MINE"]
r, _ps1 = _blocked("SINNOH_ROUTE_210", "SOLACEON_TOWN", "psyduck")
story.inventory["SECRET_POTION"] = 1   # (11-23 S3, Jordan: Platinum's rule - Cynthia's SecretPotion cures them, not the Fen Badge)
r, _ps2 = _blocked("SINNOH_ROUTE_210", "SOLACEON_TOWN", "psyduck")
story.inventory.pop("SECRET_POTION", None)
check(_ps1 and not _ps2, f"Route 210: the Psyduck stay till you have the SecretPotion, then they're gone ({len(_ps1)} -> {len(_ps2)})")
_vl = _tm["VALOR_LAKEFRONT"]
_cyv = [p for f in (_vl.get("floors") or [_vl]) for p in f.get("people") or [] if isinstance(p, dict) and p.get("text") == "Cynthia"]
check(_cyv and _cyv[0]["event"].get("gift_item") == {"SECRET_POTION": 1} and "has_fen_badge" in _cyv[0]["condition"] and "sinnoh_valor_grunt_beaten" in _cyv[0]["condition"],
      "Valor Lakefront: Cynthia gives the SecretPotion after the Fen Badge, once the Pastoria grunt is beaten (S4, Platinum)")
story.story_flags.pop("windworks_cleared", None)
story.inventory["HM_SURF"] = 0                                     # (you have no Surf this early: the river can't take you round them)
r, _gr = _blocked("SINNOH_ROUTE_205", "FLOAROMA_TOWN")
_reach = core.on_foot(r.run.floor, r.run.player)                   # (on foot: not across the river)
_for = [t for t, v in r.run.floor.exits.items() if v == "ETERNA_FOREST"]; _ww = [t for t, v in r.run.floor.exits.items() if v == "VALLEY_WINDWORKS"]
check(len(_gr) == 3 and not any(t in _reach for t in _for) and any(t in _reach for t in _ww),
      f"Route 205: Team Galactic's grunts bar the way north to Eterna Forest, but you can still reach the Windworks ({len(_gr)} grunts; forest reached {any(t in _reach for t in _for)}; Windworks reached {any(t in _reach for t in _ww)}; you at {r.run.player})")
story.story_flags["windworks_cleared"] = True
r, _gr2 = _blocked("SINNOH_ROUTE_205", "FLOAROMA_TOWN")
check(not _gr2 and "SINNOH_ROUTE_205" in [o.get("target_area") for o in _prog["FLOAROMA_TOWN"]["travel_options"] if not o.get("condition")],
      "Route 205: once the Windworks is cleared the grunts are gone (and Floaroma's own way onto the route is open from the start)")
story.inventory.pop("WORKS_KEY", None)
r, _wg = _blocked("VALLEY_WINDWORKS", "SINNOH_ROUTE_205")
story.inventory["WORKS_KEY"] = 1   # (11-23, S2: Platinum's rule - the door opens with the Works Key, the Meadow's second grunt's)
r, _wg2 = _blocked("VALLEY_WINDWORKS", "SINNOH_ROUTE_205")
story.inventory.pop("WORKS_KEY", None)
check(len(_wg) == 1 and not _wg2, "Valley Windworks: the door is shut until you have the Works Key")
story.inventory["BICYCLE"] = 0
r, _bk = _blocked("SINNOH_ROUTE_206", "ETERNA_CITY")
story.inventory["BICYCLE"] = 1
r, _bk2 = _blocked("SINNOH_ROUTE_206", "ETERNA_CITY")
check(len(_bk) >= 6 and not _bk2, f"Route 206: the Cycling Road's two ends are barred until you have the Bicycle ({len(_bk)} tiles)")
story.story_flags.pop("beat_sinnoh_champion", None)
t = town("SNOWPOINT_CITY", None)
_g1 = dict(t.barred)
story.story_flags["beat_sinnoh_champion"] = True
t = town("SNOWPOINT_CITY", None)
check(len(_g1) == 2 and not t.barred and all(not o.get("target_area") == "SNOWPOINT_TEMPLE" or "beat_sinnoh_champion" in str(o) for o in _prog["SNOWPOINT_CITY"]["travel_options"]),
      "Snowpoint City: a guard bars the Temple until you are Champion")
t.draw()
story.story_flags.clear(); story.story_flags.update(_sv); story.badges.clear(); story.badges.update(_bd)
story.inventory.clear(); story.inventory.update(_inv0); story.defeated_trainers.clear(); story.defeated_trainers.update(_dt)

# ---- new rules: deep snow slows you, thick fog needs Defog, narrow log bridges need the Bicycle, rooms have their furniture
import src.states.overworld.dungeon as _dmod
_inv0 = dict(story.inventory)
r = route("SINNOH_ROUTE_217", "SINNOH_ROUTE_216")
_g = _tm["SINNOH_ROUTE_217"]["art"]
_sn = next(((x, y), (dx, dy)) for y, row in enumerate(_g) for x, c in enumerate(row) if c == "8" for dx, dy in core.DIRS
           if 0 <= y - dy < len(_g) and 0 <= x - dx < len(row) and _g[y - dy][x - dx] == "." and r.run.floor.walkable(x - dx, y - dy) and not r.run.floor.occupied(x - dx, y - dy))
(_sx, _sy), (_dx, _dy) = _sn
r.run.floor.movers = [m for m in r.run.floor.movers if abs(m.x - _sx) > 4 or abs(m.y - _sy) > 4]   # (11-18: a wild Pokemon wandering in made this flaky)
r.run.player = (_sx - _dx, _sy - _dy); r.anim = 0
r.step(_dx, _dy)
_slow = r.anim
r.anim = 0; r.run.player = (_sx, _sy)
r.step(-_dx, -_dy)
check(_slow == _dmod.STEP_FRAMES * 2 and r.anim == _dmod.STEP_FRAMES and sum(row.count("8") for row in _g) > 2000,
      f"Route 217: a step into deep snow takes twice as long ({_slow} frames against {r.anim}); {sum(row.count('8') for row in _g)} tiles of it")
story.inventory["HM_DEFOG"] = 0
r = route("LOST_TOWER", "SINNOH_ROUTE_209")
r._warp(4, 1, 1); frames(r, 3)   # (5F: the fog is on 3F-5F only, Platinum's zone weather - checked floor by floor in S3's part)
_fog1 = bool(r.run.fog)
story.inventory["HM_DEFOG"] = 1
r = route("LOST_TOWER", "SINNOH_ROUTE_209")
r._warp(4, 1, 1); frames(r, 3)
check(_fog1 and not r.run.fog and _tm["TURNBACK_CAVE"].get("fog") == "defog", "Lost Tower: thick fog until you have Defog (Turnback Cave the same)")
story.inventory["BICYCLE"] = 0
r = route("SINNOH_ROUTE_228", "SINNOH_ROUTE_226")
_bb = [t for t, v in r.run.floor.decor.items() if str(v).startswith("barrier:")]
story.inventory["BICYCLE"] = 1
r = route("SINNOH_ROUTE_228", "SINNOH_ROUTE_226")
check(len(_bb) >= 8 and not any(str(v).startswith("barrier:") for v in r.run.floor.decor.values()),
      f"Route 228: its narrow log bridges are barred at each end until you have the Bicycle ({len(_bb)} ends)")
_fur = {k: sum(row.count(c) for f in _tm[k]["floors"] for row in f["art"] for c in "myz") for k in ("TEAM_GALACTIC_HQ", "OLD_CHATEAU", "ETERNA_GALACTIC_BUILDING", "FUEGO_IRONWORKS")}
_graves = sum(row.count("r") for f in _tm["LOST_TOWER"]["floors"] for row in f["art"])
check(all(v >= 60 for v in _fur.values()) and _graves >= 100, f"the buildings have their furniture where the game stands it {_fur}; the Lost Tower its {_graves} graves")
r = route("TEAM_GALACTIC_HQ", "VEILSTONE_CITY"); frames(r, 3)
check(_tm["TEAM_GALACTIC_HQ"].get("theme") == "tunnel" and sum(row.count("1") for f in _tm["TEAM_GALACTIC_HQ"]["floors"] for row in f["art"]) >= 20,
      "Team Galactic HQ: its warp panels are drawn as glowing pads (a passage tile indoors)")
story.inventory.clear(); story.inventory.update(_inv0)

# ---- Spear Pillar's three ways on: the Hall of Origin, the rift, the Distortion World
r = route("SPEAR_PILLAR", "HALL_OF_ORIGIN")
check(r.run.index == 3 and {"HALL_OF_ORIGIN", "SPEAR_PILLAR_RIFT", "DISTORTION_WORLD"} <= set(r.run.floor.exits.values()),
      f"Spear Pillar: back from the Hall of Origin you stand on the summit (floor {r.run.index + 1}), with the stair of light and both rifts")
r = route("HALL_OF_ORIGIN", "SPEAR_PILLAR")
check(isinstance(r, DungeonState) and (r.run.floor.w, r.run.floor.h) == (21, 33) and _tm["HALL_OF_ORIGIN"]["people"] == ["Approach Arceus"],
      "Hall of Origin: the stair up from the columns, Arceus pinned on the platform at its head")
r = route("DISTORTION_WORLD", "SPEAR_PILLAR")
_n = r.run.n_floors
_down = 0
for _q in range(_n - 1):
    try:
        r._descend(); frames(r, 2); _down += 1
    except Exception as _e:
        break
_dw = _tm["DISTORTION_WORLD"]
_ok_each = all(any("+" in row for row in f["art"]) for f in _dw["floors"][:-1]) and all(any("-" in row for row in f["art"]) for f in _dw["floors"][1:])
_last_reach = core.distances(r.run.floor, r.run.player)
check(_n == 9 and _down == 8 and r.run.index == 8 and _ok_each and _dw["theme"] == "distortion" and _dw["figure_floors"] == {"FACE GIRATINA": 8, "PICK UP THE GLOWING ORB": 8, "Galactic Boss Cyrus": 7} and _dw["floors"][7].get("trainer_spots") == ["Galactic Boss Cyrus"]
      and _dw["floor_names"][5:] == ["B5F", "B6F", "B7F", "Giratina's room"],
      f"Distortion World: Platinum's nine floors (its unused map 578 left out), a way down on each ({_down} descents), Cyrus on B7F and Giratina below")
_bad_dw = []
for _i, _f in enumerate(_dw["floors"]):                              # on each floor the way in and the way on are joined
    _a = [(x, y) for y, row in enumerate(_f["art"]) for x, c in enumerate(row) if c in "-n"]
    _b = [(x, y) for y, row in enumerate(_f["art"]) for x, c in enumerate(row) if c == "+"]
    if _a and _b:
        _seen, _todo = {_a[0]}, [_a[0]]
        while _todo:
            _x, _y = _todo.pop()
            for _dx, _dy in core.DIRS:
                _t = (_x + _dx, _y + _dy)
                if _t not in _seen and 0 <= _t[1] < len(_f["art"]) and 0 <= _t[0] < len(_f["art"][0]) and _f["art"][_t[1]][_t[0]] in ".,o+-nN$":
                    _seen.add(_t); _todo.append(_t)
        if _b[0] not in _seen:
            _bad_dw.append(_i)
check(not _bad_dw, f"Distortion World: on every floor you can get from the way in to the way on {_bad_dw}")

# ---- the Great Marsh: one map of its six areas, each with its own wild Pokemon
r = route("GREAT_MARSH", "PASTORIA_CITY")
f = r.run.floor
_zi = [r._zone_index(0, x + 16, y + 16) for x, y, w, h in _tm["GREAT_MARSH"]["zone_rects"]]
_gm = _tm["GREAT_MARSH"]["art"]
check(isinstance(r, DungeonState) and r.run.n_floors == 1 and (f.w, f.h) == (64, 96) and r.run.player[1] >= 80 and set(f.exits.values()) == {"PASTORIA_CITY"},
      f"Great Marsh: one map, 64 x 96; in from Pastoria's gate at the foot {r.run.player}")
check(len(r.zones) == 6 and _zi == [0, 1, 2, 3, 4, 5] and [r._zone_name(i) for i in (0, 5)] == ["Area 1", "Area 6"],
      f"Great Marsh: its six areas lie two across and three down, Area 1 top left to Area 6 bottom right {_zi}")
check(_tm["GREAT_MARSH"].get("theme") == "marsh" and sum(row.count("9") for row in _gm) > 500 and sum(row.count('"') for row in _gm) > 800,
      "Great Marsh: wet reeds for its tall grass, and deep mud that slows you")
r.draw()

# ---- the opening, played: walk into Lake Verity with no Pokemon, pick a starter, drive off the Starly, home to Twinleaf
from src.states.menus import StarterSelectionState as _SSS
_sv = dict(story.story_flags); _team = list(story.player_team)
for _k in ("received_starter_sinnoh", "sinnoh_starly_driven_off", "defeated_rival_sinnoh_starter"):
    story.story_flags.pop(_k, None)
story.current_area_key, story.last_area_key = "LAKE_VERITY", "VERITY_LAKEFRONT"
story.player_team = []
_p = PlayState(g); g.states["play"] = _p; g.change_state(_p)
def _adv(n, stop):
    for _ in range(n):
        st = g.current_state
        if stop(st):
            return True
        box = getattr(st, "dialogue_box", None)
        if box is not None and box.visible:
            box.advance()
        st.update(); st.draw()
    return False
_said = bool(_p.dialogue_box.visible)
_s1 = _adv(300, lambda st: isinstance(st, _SSS))
if _s1:
    g.current_state.load_starters(); g.current_state.selected_idx = 0; g.current_state.complete_selection()
_s2 = _adv(400, lambda st: "Battle" in type(st).__name__)
_got = len(story.player_team) == 1 and bool(story.story_flags.get("received_starter_sinnoh"))
if _s2:
    g.current_state.player_won = True; g.current_state.exit_battle()
_s3 = _adv(400, lambda st: story.current_area_key == "TWINLEAF_TOWN")  # (Rowan walks up and off, about 150 frames, then the trip home, about 75)
check(_said and _s1 and _s2 and _got and _s3 and story.story_flags.get("sinnoh_starly_driven_off"),
      f"the opening plays through on the maps: the lake scene {_said}, the starter choice {_s1}, your first Pokemon {_got}, the Starly battle {_s2}, home to Twinleaf {_s3}")
story.story_flags.clear(); story.story_flags.update(_sv); story.player_team = _team

# ---- the insides of the towns' buildings (rooms): each from Platinum's own room; the town's options are the people standing in them
def _enter_door(t, door):
    t.player = t.anim_from = (door[0], door[1] + 1); t.anim = 0; t.walk_goal = None
    t.step(0, -1); t.anim = 0


_area = __import__("json").load(open("assets/sinnoh_area_data.json", encoding="utf-8"))["STORY_PROGRESSION"]
_rooms_seen = 0
for _key in [k for k, v in _tm.items() if v.get("rooms") and _area.get(k, {}).get("region") == "SINNOH"
             and _area[k].get("area_type") != "dungeon"]:   # (a place walked as a dungeon, its rooms floors of it: the Battle Frontier - battle_points walks it, 11-22)
    _m = _tm[_key]
    _bad = []
    for _d, _name in _m["inside"].items():
        _door = tuple(int(v) for v in _d.split(","))
        t = town(_key, _area[_key]["travel_options"][0]["target_area"] if _area[_key].get("travel_options") else _key)
        if not t._open((_door[0], _door[1] + 1)) or _door in getattr(t, "barred", {}):
            continue  # (a door you reach from another side, or one the story keeps shut - the Battleground: its own check)
        _enter_door(t, _door)
        _want = len(_m["rooms"][_name].get("people", []))
        _own = [o for o in t.people.values() if not (isinstance(o, dict) and o.get("_partner_of"))]   # (main 11-24: a leader's partner Pokemon beside them)
        if t.room != _name or len(_own) != _want or not t._open(t.player) or not any(v == "OUT:" + _d or v.startswith("OUT:") for v in t.exits.values()):
            _bad.append((_name, t.room, len(_own), _want)); continue
        _mat = next(k for k, v in t.exits.items() if v.startswith("OUT:"))
        _back = tuple(int(v) for v in t.exits[_mat][4:].split(","))  # (a building with two doors: out below its main one)
        t._go(None, t.exits[_mat])
        if t.room is not None or abs(t.player[0] - _back[0]) + abs(t.player[1] - _back[1]) > 2:
            _bad.append((_name, "out", t.player, _door))
        _rooms_seen += 1
    check(not _bad, f"{_key}: in through each building's door to its room, its people there, and out again below the door ({len(_m['inside'])} doors) {_bad[:3]}")
check(_rooms_seen >= 50, f"Sinnoh's town rooms walked into and out of: {_rooms_seen}")
t = town("SANDGEM_TOWN", "SINNOH_ROUTE_201")
_d = next(tuple(int(v) for v in d.split(",")) for d, n in _tm["SANDGEM_TOWN"]["inside"].items() if n == "lab")
_enter_door(t, _d)
check(t.room == "lab" and [o.get("target") for o in t.people.values() if o.get("target")] == ["professor_rowan"], f"Sandgem: Prof. Rowan stands in his lab (with Platinum's lab aides) ({t.room}, {[o.get('text') for o in t.people.values()]})")
t = town("OREBURGH_CITY", "SINNOH_ROUTE_203")
_d = next(tuple(int(v) for v in d.split(",")) for d, n in _tm["OREBURGH_CITY"]["inside"].items() if n == "gym")
_enter_door(t, _d)
check(t.room == "gym" and [str(o.get("action")).upper() for o in t.people.values()].count("GYM") == 1, f"Oreburgh Gym: the Leader inside is the Gym challenge ({t.room}, {[o.get('action') for o in t.people.values()]})")
_d = next(tuple(int(v) for v in d.split(",")) for d, n in _tm["OREBURGH_CITY"]["inside"].items() if n == "center")
t._go(None, "OUT:%d,%d" % next(tuple(int(v) for v in d.split(",")) for d, n in _tm["OREBURGH_CITY"]["inside"].items() if n == "gym"))
_enter_door(t, _d)
check(t.room == "center" and [str(o.get("action")).upper() for o in t.people.values()].count("HEAL") == 1, f"Oreburgh's Pokemon Center: the nurse inside heals ({t.room})")

# ---- S1 (11-23): Platinum's two opening gates (sinnoh_map_tools/s_s1_gates.py; found by sgates.py)
def _drive(st, n=900, done=None):
    """Frames with every line tapped through, till the scene is over (or done() says so)."""
    for _ in range(n):
        cur = g.current_state
        if done and done():
            return True
        if getattr(cur, "npc_active", False):
            cur.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        box = getattr(cur, "dialogue_box", None)
        if box is not None and getattr(box, "visible", False):
            box.advance()
        cur.update(); cur.draw()
    return bool(done and done())


_sv = dict(story.story_flags)
for _k in ("received_starter_sinnoh", "sinnoh_visited_rival_home"):
    story.story_flags.pop(_k, None)
t = town("TWINLEAF_TOWN", "TWINLEAF_TOWN")
t.player = t.anim_from = (15, 4); t.anim = 0; t.walk_goal = None
t.step(0, -1); t.anim = 0
_hit = _drive(t, 30, lambda: t.scenes.busy())
_drive(t, 900, lambda: not t.scenes.busy())
check(_hit and tuple(t.player)[1] >= 4, f"Twinleaf: before you've been to your friend's house, a neighbour calls you back from the north way out (scene {_hit}, you at {t.player})")
_enter_door(t, (9, 11))
_mom = next((s for s, o in t.people.items() if "House" in str(o.get("text"))), None)
if _mom:
    t._talk(_mom); _drive(t, 200, lambda: not getattr(t, "npc_active", False))
check(t.room == "rival" and story.story_flags.get("sinnoh_visited_rival_home"), f"Twinleaf: your friend's mom, in his house, sends you after him ({t.room}, {_mom})")
t = town("TWINLEAF_TOWN", "TWINLEAF_TOWN")
t.player = t.anim_from = (15, 4); t.anim = 0; t.walk_goal = None
t.step(0, -1); t.anim = 0
_drive(t, 30)
check(not t.scenes.busy() and tuple(t.player) == (15, 3), f"Twinleaf: after that, the way north is open ({t.player})")
story.story_flags.clear(); story.story_flags.update(_sv)

for _k in ("rowan_assistant_balls", "sinnoh_route202_lesson"):
    story.story_flags.pop(_k, None)
story.story_flags["received_pokedex_sinnoh"] = True
r = route("SINNOH_ROUTE_202", "SANDGEM_TOWN")
_balls = story.balls_left
r.run.floor.movers = [m for m in r.run.floor.movers if m.kind != "wild"]
r.run.player = (21, 27); frames(r, 2)
r.run.player = (20, 27)
_hit = _drive(r, 60, lambda: r._scene_run is not None and r._scene_run.busy())
_drive(r, 2000, lambda: story.story_flags.get("rowan_assistant_balls") and not (r._scene_run and r._scene_run.busy()))
check(_hit and story.story_flags.get("rowan_assistant_balls") and story.balls_left >= _balls + 5,
      f"Route 202: Dawn catches up, shows you how to catch, and gives you 5 Poke Balls (scene {_hit}, balls {_balls} -> {story.balls_left})")
story.story_flags.clear(); story.story_flags.update(_sv)

# ---- S2 (11-23): the Windworks chain and Jubilife's Pokétch campaign, as Platinum has them (s_s2_windworks.py, s_s2_jubilife.py)
from src.states.systems.pick_list import PickListState as _PLS
_sv = dict(story.story_flags); _inv = dict(story.inventory)
for _k in ("sinnoh_r205_girl", "windworks_cleared", "got_poketch", "sinnoh_coupon_1", "sinnoh_coupon_2", "sinnoh_coupon_3"):
    story.story_flags.pop(_k, None)
story.inventory.pop("WORKS_KEY", None)
for _b in [b for b in story.badges.get("SINNOH", [])]:
    pass
_badges = list(story.badges.get("SINNOH", []))
t = town("FLOAROMA_TOWN", "SINNOH_ROUTE_204")
check((2, 3) in t.barred and (3, 3) in t.barred, f"Floaroma: two grunts stand in the Meadow's way in before you've met the girl on Route 205 ({sorted(t.barred)[:2]})")
r = route("SINNOH_ROUTE_205", "FLOAROMA_TOWN")
_girl = next((m for m in r.run.floor.movers if m.kind == "figure" and str((m.payload or {}).get("text")) == "Little girl"), None) if hasattr(r, "run") else None
if _girl is not None:
    r._use_figure(_girl); _drive(r, 300, lambda: not (getattr(r, "dialogue_box", None) and r.dialogue_box.visible))
check(_girl is not None and story.story_flags.get("sinnoh_r205_girl"), f"Route 205: the girl whose papa is trapped in the Windworks asks for help ({_girl is not None})")
t = town("FLOAROMA_TOWN", "SINNOH_ROUTE_204")
check((2, 3) not in t.barred, "Floaroma: then the grunts have gone into the Meadow")
_mg = __import__("json").load(open("assets/sinnoh_area_data.json", encoding="utf-8"))["STORY_PROGRESSION"]["FLOAROMA_MEADOW"]["trainer_pool"]
check(_mg[-1].get("rewards", {}).get("WORKS_KEY") == 1, "Floaroma Meadow: the second grunt gives the Works Key")
r = route("VALLEY_WINDWORKS", "SINNOH_ROUTE_205")
_door = next((b for f in (_tm["VALLEY_WINDWORKS"].get("floors") or [_tm["VALLEY_WINDWORKS"]]) for b in f.get("barred") or [] if b.get("item") == "WORKS_KEY"), None)
check(_door is not None, "Valley Windworks: its door opens with the Works Key")

_r205 = _tm["SINNOH_ROUTE_205"]; _et = _tm["ETERNA_CITY"]
_at = lambda m, x, y: m["exits"].get(m["art"][y][x])
check(_at(_r205, 22, 0) == "ETERNA_FOREST_OUTSKIRTS" and _at(_r205, 14, 5) == "ETERNA_FOREST" and _at(_et, 0, 20) == "ETERNA_FOREST_OUTSKIRTS"
      and _at(_et, 3, 12) == "ETERNA_FOREST", "Eterna Forest's outskirts (Platinum's D03): Route 205's north edge and Eterna's west edge lead there, the forest's doors into the forest")
r = route("ETERNA_FOREST_OUTSKIRTS", "SINNOH_ROUTE_205")
_o = r.run.floor
check(isinstance(r, DungeonState) and set(_o.exits.values()) >= {"SINNOH_ROUTE_205", "ETERNA_CITY"}, f"the outskirts: walked, ways out to Route 205 and Eterna ({set(_o.exits.values())})")

t = town("JUBILIFE_CITY", "SINNOH_ROUTE_202")   # (11-23 S2: Jubilife TV's 3F doorways, s_s2_tv.py)
_tvb = []
for _ch, _want in (("<", "tv_4f"), (">", "tv_groups"), ("u", "tv_records")):
    t._go("house_0201_3f", None); frames(t, 2)
    _sp = next(((x, y) for y, r in enumerate(_tm["JUBILIFE_CITY"]["rooms"]["house_0201_3f"]["art"]) for x, c in enumerate(r) if c == _ch), None)
    _nb = next(((x + dx, y + dy) for x, y in [_sp] for dx, dy in ((0, 1), (1, 0), (-1, 0), (0, -1)) if t._open((x + dx, y + dy)) and (x + dx, y + dy) != _sp), None) if _sp else None
    if _nb:
        t.player = t.anim_from = _nb; t.anim = 0; t.walk_goal = None
        t.step(_sp[0] - _nb[0], _sp[1] - _nb[1]); t.anim = 0; frames(t, 3)
    _tvb.append((_ch, t.room == _want, len(t.people)))
check(all(ok and n for _c, ok, n in _tvb), f"Jubilife TV 3F: each doorway leads to its room, people there ({_tvb})")

story.badges["SINNOH"] = []
t = town("JUBILIFE_CITY", "SINNOH_ROUTE_202")
_cl = {xy: o for xy, o in t._people().items() if str(o.get("text", "")).startswith("Clown")}
check(len(_cl) == 3, f"Jubilife: three Pokétch campaign clowns on Platinum's spots ({sorted(_cl)})")
_xy = sorted(_cl)[0]
_got = []
for _ans in (1, 0):   # (wrong first: no Coupon; then right)
    t._talk(_xy)
    _drive(t, 200, lambda: isinstance(g.current_state, _PLS))
    if isinstance(g.current_state, _PLS):
        g.current_state.pick(_ans)
    _drive(t, 200, lambda: not getattr(t, "npc_active", False) and g.current_state is t)
    _got.append(bool(story.story_flags.get(_cl[_xy]["event"]["quiz_flag"])))
check(_got == [False, True], f"Jubilife: a clown's Coupon only for the right answer (wrong, then right: {_got})")
t.player = t.anim_from = (61, 22); t.anim = 0; t.walk_goal = None
t.step(-1, 0); t.anim = 0
_hit = _drive(t, 40, lambda: t.scenes.busy())
_drive(t, 900, lambda: not t.scenes.busy())
check(_hit and t.player[0] >= 59, f"Jubilife: without a Pokétch, Looker stops you at the way east ({_hit}, {t.player})")
t.player = t.anim_from = (26, 44); t.anim = 0; t.walk_goal = None
t.step(1, 0); t.anim = 0
_hit = _drive(t, 40, lambda: t.scenes.busy())
_drive(t, 900, lambda: not t.scenes.busy())
check(_hit and t.player[0] >= 28, f"Jubilife: no Badge yet, so the guide turns you back from the Global Terminal ({_hit}, {t.player})")
_d = next(tuple(int(v) for v in d.split(",")) for d, n in _tm["JUBILIFE_CITY"]["inside"].items() if n == "poketch")
_enter_door(t, _d)
_pres = next((s for s, o in t.people.items() if str(o.get("text")) == "Pokétch Company"), None)
if _pres:
    t._talk(_pres); _drive(t, 200, lambda: not getattr(t, "npc_active", False))
_early = bool(story.story_flags.get("got_poketch"))
story.story_flags.update({"sinnoh_coupon_1": True, "sinnoh_coupon_2": True, "sinnoh_coupon_3": True})
if _pres:
    t._talk(_pres); _drive(t, 200, lambda: not getattr(t, "npc_active", False))
check(_pres and not _early and story.story_flags.get("got_poketch"), f"the Pokétch Company: the Pokétch only for all three Coupons (before {_early}, after {story.story_flags.get('got_poketch')})")
story.story_flags.clear(); story.story_flags.update(_sv); story.inventory.clear(); story.inventory.update(_inv); story.badges["SINNOH"] = _badges

# ---- S3 (11-23): Cynthia's Egg in Eterna (s_s3_eterna.py; Platinum's C04 script 27)
_sv = dict(story.story_flags); _team = list(story.player_team)
# (11-24: first Platinum's Cynthia outside the Galactic building, on Cut: she finishes the side mission "Cynthia's Gift")
story.story_flags.pop("received_hm_cut", None); story.story_flags.pop("galactic_eterna_cleared", None)
_fb = list(story.badges.get("SINNOH", []))
story.badges["SINNOH"] = sorted(set(_fb) | {"COAL", "FOREST"})
t = town("ETERNA_CITY", "SINNOH_ROUTE_211")
_cc = next((s for s, o in t._people().items() if str(o.get("text")) == "Cynthia "), None)
if _cc:
    t._talk(_cc); _drive(t, 300, lambda: not getattr(t, "npc_active", False))
check(_cc == (51, 10) and story.story_flags.get("received_hm_cut") and story.inventory.get("HM_CUT"),   # (outside the yard's trees: she gives Cut, 11-24)
      f"Eterna: with the Forest Badge, Cynthia outside the Galactic building gives HM Cut (\"Cynthia's Gift\" done) ({_cc})")
story.badges["SINNOH"] = _fb
story.story_flags["galactic_eterna_cleared"] = True; story.story_flags.pop("sinnoh_cynthia_egg", None)
t = town("ETERNA_CITY", "SINNOH_ROUTE_211")
check((53, 29) in t.barred, "Eterna: after the Galactic building, a stop across the street east until Cynthia's Egg")
_cy = next((s for s, o in t._people().items() if str(o.get("text")) == "Cynthia"), None)
_n = len(story.player_team)
if _cy:
    t._talk(_cy); _drive(t, 300, lambda: not getattr(t, "npc_active", False))
_egg = len(story.player_team) == _n + 1 and getattr(story.player_team[-1], "is_egg", False) and story.player_team[-1].id == 175
t = town("ETERNA_CITY", "SINNOH_ROUTE_211")
check(_cy and _egg and story.story_flags.get("sinnoh_cynthia_egg") and (53, 29) not in t.barred,
      f"Eterna: Cynthia gives the Togepi Egg, then the way east is open ({_cy}, egg {_egg})")
story.story_flags.clear(); story.story_flags.update(_sv); story.player_team = _team

# ---- S3 (11-23): Eterna Gym's flower clock, Platinum's own walk tables (s_s3_eterna_gym.py)
_sv = dict(story.story_flags)
_cf = ["gym_trainer_ETERNA_CITY_1", "gym_trainer_ETERNA_CITY_2", "gym_trainer_ETERNA_CITY_3"]
for _k in _cf:
    story.story_flags.pop(_k, None)
_open = []
for _n in range(3):
    t = town("ETERNA_CITY", "SINNOH_ROUTE_206")
    t._go("gym", None); frames(t, 25)
    _open.append(((11, 15) in t.barred, (20, 19) in t.barred))
    story.story_flags[_cf[_n]] = True
check(_open == [(True, True), (False, True), (True, False)],
      f"Eterna Gym: the clock's hands move with each trainer beaten - (11,15) shut, open, shut; the east fountain row shut, shut, open ({_open})")
story.story_flags.clear(); story.story_flags.update(_sv)

# ---- S3 (11-23): Hearthome Gym, Platinum's rooms; a question from our maths engine picks the door (s_s3_hearthome_gym.py)
from src.world import hearthome_gym as _hg
_sv = dict(story.story_flags)
for _k in [k for k in story.story_flags if k.startswith("gym_trainer_HEARTHOME") or k.startswith("hearthome_gym_door")] + ["sinnoh_beat_fantina"]:
    story.story_flags.pop(_k, None)


def _hg_walk(t, at, d):
    """Stand at, then walk one step that way (a door: into the next room). Waits for anything still playing first."""
    _drive(t, 120, lambda: not (getattr(t, "scenes", None) and t.scenes.busy()) and not getattr(t, "npc_active", False))
    was = t.room
    t.player = t.anim_from = at; t.anim = 0; t.walk_goal = None
    t.step(*d)
    _drive(t, 120, lambda: t.room != was)


def _hg_answer(t, right):
    _drive(t, 300, lambda: isinstance(g.current_state, _PLS))
    if not isinstance(g.current_state, _PLS):
        return None
    n = len(g.current_state.choices)
    k = _hg.LAST["right"] if right else (_hg.LAST["right"] + 1) % n
    g.current_state.pick(k)
    _drive(t, 300, lambda: g.current_state is t and not getattr(t, "npc_active", False))
    return k


t = town("HEARTHOME_CITY", "SINNOH_ROUTE_208")
t._go("gym", None); frames(t, 10)
check(t.room == "gym" and (11, 3) in t.barred and "ROOM:gym_1" in t.exits.values(),
      f"Hearthome Gym: the lobby, one door on, its warp panel shut till Fantina is beaten ({t.room}, {sorted(t.exits.values())})")
_hg_walk(t, (4, 3), (0, -1))
_in1 = t.room
_k = _hg_answer(t, True)
_door = sorted(xy for xy, v in t.exits.items() if v == "ROOM:gym_2")[_k] if _k is not None else None
check(_in1 == "gym_1" and _k is not None and _door not in t.barred and all(d in t.barred for d in t.exits if t.exits[d] == "ROOM:gym_2" and d != _door),
      f"Hearthome Gym room 1: a sum as you come in; the right answer opens its door, the others stay shut ({_in1}, door {_door}, {_hg.LAST.get('problem')})")
_hg_walk(t, (_door[0], _door[1] + 1), (0, -1)) if _door else None
_in2 = t.room
_kw = _hg_answer(t, False)
check(_in2 == "gym_2" and _kw is not None and t.room == "gym",
      f"Hearthome Gym room 2: a wrong answer walks you through the wrong door, back to the lobby ({_in2} -> {t.room})")
t._go("gym_2", "ROOM:gym_1"); frames(t, 5)
_k2 = _hg_answer(t, True)
_door2 = sorted(xy for xy, v in t.exits.items() if v == "ROOM:gym_3")[_k2] if _k2 is not None else None
_hg_walk(t, (_door2[0], _door2[1] + 1), (0, -1)) if _door2 else None
check(t.room == "gym_3" and "Gym" in t.town_map["rooms"]["gym_3"]["people"] and (8, 9) in t.barred,
      f"Hearthome Gym: the right door in room 2 leads to Fantina; the way to the warp panel shut till she's beaten ({t.room})")
story.story_flags["sinnoh_beat_fantina"] = True
t._go("gym_3", "ROOM:gym_2"); frames(t, 25)
check((8, 9) not in t.barred, "Hearthome Gym: beaten, Fantina's warp panel takes you back to the lobby")
story.story_flags.clear(); story.story_flags.update(_sv)

# ---- S3 (11-23): the Lost Tower's fog on 3F-5F only, as Platinum's zone weather (s_s3_lost_tower.py)
_inv = dict(story.inventory)
story.inventory.pop("HM_DEFOG", None)
r = route("LOST_TOWER", "SINNOH_ROUTE_209")
_fog = []
for _i in range(5):
    if r.run.index != _i:
        r._warp(_i, 1, 1); frames(r, 3)
    _fog.append(bool(r.run.fog))
story.inventory["HM_DEFOG"] = 1
r = route("LOST_TOWER", "SINNOH_ROUTE_209")
r._warp(4, 1, 1); frames(r, 3)
check(_fog == [False, False, True, True, True] and not r.run.fog,
      f"Lost Tower: fog on 3F-5F only, as Platinum; gone once you have Defog ({_fog}, with Defog 5F: {r.run.fog})")
story.inventory.clear(); story.inventory.update(_inv)

# ---- S3 (11-23): the Old Chateau's ghosts and its one Dread Plate (s_s3_old_chateau.py)
from src.world import old_chateau as _oc
_roll = _oc.condition
_oc.condition = lambda story, arg: True   # (the ghosts come now and then: here, every time)
_seen = []
for _fl in (3, 0):
    r = route("OLD_CHATEAU", "ETERNA_FOREST")
    r._warp(_fl, 1, 1); r._scene_key = None
    _was = _drive(r, 200, lambda: r._scene_run is not None and r._scene_run.busy() and r._scene_run.actors)
    _done = _drive(r, 900, lambda: not (r._scene_run and r._scene_run.busy()))
    _seen.append((_fl, bool(_was), bool(_done), r.run.index))
_oc.condition = _roll
_dp = [o for o in __import__("json").load(open("assets/sinnoh_area_data.json", encoding="utf-8"))["STORY_PROGRESSION"]["OLD_CHATEAU"]["route_menu"]
       if str(o.get("text")).strip() == "DREAD PLATE"]
check(all(w and d and i == fl for fl, w, d, i in _seen) and len(_dp) == 1,
      f"Old Chateau: the ghost girl drifts through Bedroom 4 and the butler through the dining hall, then are gone; one Dread Plate ({_seen}, {len(_dp)})")

# ---- S3 (11-24): Cynthia gives the Old Charm on Route 210, past the Psyduck (s_s3_old_charm.py)
_sv = dict(story.story_flags); _inv = dict(story.inventory)
story.story_flags.pop("got_old_charm_r210", None); story.inventory.pop("OLD_CHARM", None)
r = route("SINNOH_ROUTE_210", "SOLACEON_TOWN")
_none = next((m for m in r.run.floor.movers if m.kind == "figure" and str((m.payload or {}).get("text")) == "Cynthia"), None)
story.inventory["SECRET_POTION"] = 1
r = route("SINNOH_ROUTE_210", "SOLACEON_TOWN")
_cy = next((m for m in r.run.floor.movers if m.kind == "figure" and str((m.payload or {}).get("text")) == "Cynthia"), None)
if _cy is not None:
    r._use_figure(_cy); _drive(r, 300, lambda: not (getattr(r, "dialogue_box", None) and r.dialogue_box.visible))
check(_none is None and _cy is not None and (_cy.x, _cy.y) == (81, 71) and story.inventory.get("OLD_CHARM") and story.story_flags.get("got_old_charm_r210"),
      f"Route 210: past the Psyduck, Cynthia gives the Old Charm once you have the SecretPotion ({_none is None}, {(getattr(_cy, 'x', None), getattr(_cy, 'y', None))})")
story.story_flags.clear(); story.story_flags.update(_sv); story.inventory.clear(); story.inventory.update(_inv)

# ---- S3 (11-24): fog and darkness by Platinum's zone weather (s_s3_fog.py)
_inv = dict(story.inventory)
for _k in ("HM_DEFOG", "HM_FLASH"):
    story.inventory.pop(_k, None)
r = route("SINNOH_ROUTE_210", "SOLACEON_TOWN")
r.run.player = (80, 100); r.run.reveal()
_r210 = (r.run.visible(80, 110), r.run.visible(20, 10))   # (the south half clear, the north half R210B in fog)
_cor = []
r = route("MT_CORONET_BASE", "SINNOH_ROUTE_207")
for _i in (0, 8):
    if r.run.index != _i:
        r._warp(_i, 1, 1); frames(r, 3)
    _cor.append(bool(r.run.fog))
_way = []
r = route("WAYWARD_CAVE", "SINNOH_ROUTE_206")
for _i in (0, 1):
    if r.run.index != _i:
        r._warp(_i, 1, 1); frames(r, 3)
    _way.append(bool(r.run.fog))
story.inventory["HM_DEFOG"] = 1; story.inventory["HM_FLASH"] = 1
r = route("SINNOH_ROUTE_210", "SOLACEON_TOWN")
_lift = not r.run.fog
check(_r210 == (True, False) and _cor == [False, True] and _way == [True, False] and _lift,
      f"Fog as Platinum's weather: Route 210's north half, Mt. Coronet's D05R0113, Wayward Cave 1F dark; Defog clears ({_r210}, {_cor}, {_way}, {_lift})")
story.inventory.clear(); story.inventory.update(_inv)

# ---- S3 (11-24): Platinum's gatehouses, walked through (s_s3_gates.py)
_sv = dict(story.story_flags); story.story_flags["galactic_eterna_cleared"] = True
_gates = []
for _town, _room, _door, _route in (("HEARTHOME_CITY", "gate_208", (5, 54), "SINNOH_ROUTE_208"), ("HEARTHOME_CITY", "gate_209", (58, 54), "SINNOH_ROUTE_209"),
                                    ("HEARTHOME_CITY", "gate_212", (10, 57), "SINNOH_ROUTE_212"), ("ETERNA_CITY", "gate_206", (48, 57), "SINNOH_ROUTE_206")):
    t = town(_town, _route)   # (in from the route: inside its gate, by the route-side mat - as Platinum)
    _near = getattr(t, "room", None) == _room and any(v == _route and abs(k[0] - t.player[0]) + abs(k[1] - t.player[1]) <= 1 for k, v in t.exits.items())
    _in = (t.town_map.get("inside") or {}).get("%d,%d" % _door) == _room and set(t.town_map["rooms"][_room]["exits"].values()) == {"OUT:%d,%d" % _door, _route}
    _gates.append((_room, _near, _in))
check(all(n and i for _r, n, i in _gates), f"Gatehouses: Hearthome's three and Eterna's Cycling Road gate: in from the route inside the gate, through it to the town ({_gates})")
r = route("SINNOH_ROUTE_206", "SINNOH_ROUTE_207")   # (Route 206's own gate: in by a south door, out by the north mat above it)
if r.run.index != 0:
    r._warp(0, 1, 1); frames(r, 3)
r.run.player = (14, 113); r.anim = 0; r.step(0, -1); frames(r, 3)
_g_in = r.run.index == (r.recipe.get("art") or {}).get("room_floors", {}).get("gate")
_tmg = __import__("json").load(open("assets/town_maps.json", encoding="utf-8"))["SINNOH_ROUTE_206"]["rooms"]["gate"]["art"]
_vm = next(((mx, my) for my, rr in enumerate(_tmg) for mx, c in enumerate(rr) if c == "v"), None)
if _g_in and _vm:
    r.run.player = (_vm[0], _vm[1] + 1); r.anim = 0; r.step(0, -1); frames(r, 3)
_g_out = r.run.index == 0 and r.run.player[1] <= 104 and 11 <= r.run.player[0] <= 18
check(_g_in and _g_out, f"Route 206's gate: in from the south, out at its north side under Cycling Road ({_g_in}, {r.run.index}, {r.run.player})")
t = town("ETERNA_CITY", "SINNOH_ROUTE_211")
t._go("underground_man", "OUT:54,18"); frames(t, 3)
check(t.room == "underground_man" and len(t._people()) == 4, f"Eterna: the Underground Man's house, his visitors inside ({t.room}, {len(t._people())})")
story.story_flags.clear(); story.story_flags.update(_sv)

# ---- S3 (11-24): the Pokemon Hotel's lift to its 2F (the Shell Bell), Route 212's gate held by the TV crew till Pastoria
_sv = dict(story.story_flags); _inv = dict(story.inventory)
for _k in ("hearthome_hotel_lift", "got_shell_bell_hearthome_hotel", "visited_PASTORIA_CITY"):
    story.story_flags.pop(_k, None)
story.inventory.pop("SHELL_BELL", None)
t = town("HEARTHOME_CITY", "SINNOH_ROUTE_208")
t._go("house_0101", "OUT:46,38"); frames(t, 3)
_up = next(k for k, v in t.exits.items() if v == "ROOM:hotel_lift")
t.player = t.anim_from = (_up[0], _up[1] + 1); t.anim = 0; t.walk_goal = None
t.step(0, -1)
_drive(t, 300, lambda: isinstance(g.current_state, _PLS))
_asked = isinstance(g.current_state, _PLS)
if _asked:
    g.current_state.pick("house_0102")
_drive(t, 300, lambda: g.current_state is t and not getattr(t, "npc_active", False))
_out = next((k for k, v in t.exits.items() if str(v).startswith("ROOM:")), None) if t.room == "hotel_lift" else None   # (the car's door: it opens on the floor it's at)
if _out:
    _drive(t, 200, lambda: not (getattr(t, "scenes", None) and t.scenes.busy()) and not getattr(t, "npc_active", False))
    t.player = t.anim_from = (_out[0], _out[1] - 1); t.anim = 0; t.step(0, 1)
    _drive(t, 120, lambda: t.room == "house_0102")
_guest = next((s for s, o in t._people().items() if str(o.get("text")) == "Hotel guest"), None) if t.room == "house_0102" else None
if _guest:
    t._talk(_guest); _drive(t, 300, lambda: not getattr(t, "npc_active", False))
check(_asked and t.room == "house_0102" and story.inventory.get("SHELL_BELL"),
      f"Pokemon Hotel: into the lift from 1F, up to 2F, and the guest there gives a Shell Bell ({_asked}, {t.room}, {story.inventory.get('SHELL_BELL')})")
t = town("HEARTHOME_CITY", "SINNOH_ROUTE_208")
t._go("gate_212", "OUT:10,57"); frames(t, 3)
_shut = (5, 12) in t.barred
story.story_flags["visited_PASTORIA_CITY"] = True
t._go("gate_212", "OUT:10,57"); frames(t, 25)
check(_shut and (5, 12) not in t.barred, f"Route 212's gate: the TV crew stand in the way out till you've been to Pastoria City ({_shut})")
story.story_flags.clear(); story.story_flags.update(_sv); story.inventory.clear(); story.inventory.update(_inv)

# ---- S4 (11-24): the Veilstone Department Store, every floor as Platinum (s_s4_dept.py)
from src.states.systems import PokeMartState as _PMS
_sv = dict(story.story_flags)
story.story_flags.pop("veilstone_dept_lift", None)
t = town("VEILSTONE_CITY", "SINNOH_ROUTE_214")
t._go("mart", "OUT:29,27"); frames(t, 3)
_title = t.town_map["rooms"]["mart"].get("title")
_bc = next((s for s, o in t._people().items() if str(o.get("text")) == "Ball clerk"), None)
_shop = None
if _bc:
    t._talk(_bc); _drive(t, 200, lambda: isinstance(g.current_state, _PMS))
    _shop = list(getattr(g.current_state, "stock", None) or []) if isinstance(g.current_state, _PMS) else None
t = town("VEILSTONE_CITY", "SINNOH_ROUTE_214")   # (a fresh visit for the lift: the shop screen left as a player leaves it)
t._go("mart", "OUT:29,27"); frames(t, 3)
_lift = next(k for k, v in t.exits.items() if v == "ROOM:dept_lift")
_drive(t, 200, lambda: not t._busy())
t.player = t.anim_from = (_lift[0], _lift[1] + 1); t.anim = 0; t.walk_goal = None; t.step(0, -1)
_drive(t, 120, lambda: t.room == "dept_lift")
_att = next((s for s, o in t._people().items() if str(o.get("text")) == "Lift attendant"), None)
if _att:
    t._talk(_att); _drive(t, 300, lambda: isinstance(g.current_state, _PLS))
    if isinstance(g.current_state, _PLS):
        g.current_state.pick("dept_3f")
    _drive(t, 300, lambda: g.current_state is t and not getattr(t, "npc_active", False))
_door = next((k for k, v in t.exits.items() if str(v).startswith("ROOM:")), None)
if _door:
    t.player = t.anim_from = (_door[0], _door[1] - 1); t.anim = 0; t.step(0, 1)
    _drive(t, 120, lambda: t.room == "dept_3f")
_tms = [o for o in t._people().values() if str(o.get("text")) == "TM clerk"]
check(_title == "Veilstone Dept. Store 1F" and _shop and "POKE_BALLS" in _shop and t.room == "dept_3f" and _tms and _tms[0]["event"]["stock"],
      f"Veilstone Dept. Store: 1F's ball counter sells balls, the lift's attendant takes you to 3F's TM Corner ({_title}, {_shop and _shop[:3]}, {t.room})")
story.story_flags.clear(); story.story_flags.update(_sv)

# ---- S4 (11-24): Veilstone Gym's punching bags, Platinum's rules (src/world/veilstone_gym.py, s_s4_veilstone_gym.py)
from src.world import veilstone_gym as _vg
_sv = dict(story.story_flags)
t = town("VEILSTONE_CITY", "SINNOH_ROUTE_214")
t._go("gym", "OUT:12,35"); frames(t, 5); _drive(t, 200, lambda: not t._busy())   # (its "enter" scene sets the bags up)
_start = (8, 6) in t.barred and (12, 6) in t.barred   # (a bag, and the tire stack east of it)


def _hit(bag, d):
    """Stand beside the bag (room tile) and walk into it; wait for the slide."""
    t.player = t.anim_from = (bag[0] - d[0], bag[1] - d[1]); t.anim = 0; t.walk_goal = None
    t.step(*d)
    _drive(t, 300, lambda: not getattr(t, "_vg_anim", None) and not t._busy())


_hit((8, 6), (1, 0))
_one = (11, 6) in t.barred and (12, 6) not in t.barred and (8, 6) not in t.barred
# the rest of a way to Maylene (s_s4_veilstone_gym.explore found it; zone tiles less 1 row): 11 more hits
for _b, _d in [((15, 25), (1, 0)), ((3, 9), (0, 1)), ((3, 13), (1, 0)), ((8, 19), (0, -1)), ((8, 16), (-1, 0)), ((3, 16), (0, 1)),
               ((4, 21), (0, -1)), ((4, 11), (1, 0)), ((20, 16), (0, -1)), ((16, 9), (-1, 0)), ((13, 9), (-1, 0))]:
    _hit(_b, _d)
_seen, _todo = {(12, 29)}, [(12, 29)]
while _todo:
    _x, _y = _todo.pop()
    for _dx, _dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        _n = (_x + _dx, _y + _dy)
        if _n not in _seen and 0 <= _n[1] < t.h and 0 <= _n[0] < t.w and t.rows[_n[1]][_n[0]] == "." and _n not in t.barred:
            _seen.add(_n); _todo.append(_n)
_reach = any((12 + _dx, 3 + _dy) in _seen for _dx, _dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
t._go("gym", "OUT:12,35"); frames(t, 5); _drive(t, 200, lambda: not t._busy())   # (its "enter" scene sets the bags up)
_back = (8, 6) in t.barred and (12, 6) in t.barred
check(_start and _one and _reach and _back,
      f"Veilstone Gym: a bag hit east slides to its stop and knocks the tires over; twelve hits open the way to Maylene; coming back in sets them up again ({_start}, {_one}, {_reach}, {_back})")
story.story_flags.clear(); story.story_flags.update(_sv)

# ---- S4 (11-24): the Galactic Warehouse raid as Platinum's (s_s4_warehouse.py): Dawn's Pokedex, a tag battle, Looker
_sv = dict(story.story_flags); _inv = dict(story.inventory); _badges = list(story.badges.get("SINNOH", []))
for _k in ("sinnoh_dawn_warehouse_call", "sinnoh_warehouse_guards_beaten", "sinnoh_warehouse_looker", "galactic_warehouse_cleared"):
    story.story_flags.pop(_k, None)
story.inventory.pop("STORAGE_KEY", None); story.inventory.pop("HM_FLY", None)
story.badges["SINNOH"] = ["COAL", "FOREST", "COBBLE"]
t = town("VEILSTONE_CITY", "SINNOH_ROUTE_215"); frames(t, 3)
_shut = (25, 20) in t.barred
t.player = t.anim_from = (12, 37); t.anim = 0; t.walk_goal = None   # (out of the Gym with the Cobble Badge)
_drive(t, 600, lambda: story.story_flags.get("sinnoh_dawn_warehouse_call") and not t._busy())
_dawn = next((s for s, o in t._people().items() if str(o.get("text")) == "Dawn"), None)
_bs = None
if _dawn:
    t.player = t.anim_from = (_dawn[0] - 1, _dawn[1]); t.anim = 0
    t._talk(_dawn); _drive(t, 400, lambda: "Battle" in type(g.current_state).__name__)
    _bs = g.current_state
story.story_flags["sinnoh_warehouse_guards_beaten"] = True   # (won)
g.change_state(t); frames(t, 25)
t.player = t.anim_from = (23, 20); t.anim = 0
_drive(t, 900, lambda: story.story_flags.get("sinnoh_warehouse_looker") and not t._busy())
_open = (25, 20) not in t.barred and not [s for s, o in t._people().items() if str(o.get("text")).startswith("Galactic Grunt")]
t.player = t.anim_from = (29, 16); t.anim = 0; t.walk_goal = None; t.step(0, -1)
_drive(t, 400, lambda: hasattr(g.current_state, "run"))
frames(g.current_state, 5)
r = g.current_state
_lk = next((m for m in r.run.floor.movers if m.kind == "figure" and str((m.payload or {}).get("text")) == "Looker"), None) if hasattr(r, "run") else None
if _lk is not None:
    r._use_figure(_lk); _drive(r, 300, lambda: not (getattr(r, "dialogue_box", None) and r.dialogue_box.visible))
_locked = hasattr(r, "run") and r.run.floor.tile(8, 6) == core.WALL   # (the rusty door across the corridor to the Underpass: Platinum's, opened by Looker after Lake Acuity)
check(_locked and _shut and _dawn == (24, 20) and _bs is not None and story.story_flags.get("sinnoh_warehouse_looker") and _open
      and _lk is not None and story.story_flags.get("galactic_warehouse_cleared"),
      f"Galactic Warehouse: the Grunts block the lane; with the Cobble Badge Dawn asks for help; a tag battle; Looker leads you in and the mission ends; the Underpass door stays locked ({_locked}, {_shut}, {_dawn}, {type(_bs).__name__}, {_open}, {_lk is not None})")
story.story_flags.clear(); story.story_flags.update(_sv); story.inventory.clear(); story.inventory.update(_inv); story.badges["SINNOH"] = _badges

# ---- S4 (11-24, Jordan "Add it"): Platinum's scene before the Veilstone Gym - Dawn, then Crasher Wake out of the Gym
_sv = dict(story.story_flags); _badges = list(story.badges.get("SINNOH", []))
story.story_flags.pop("sinnoh_veilstone_wake_scene", None); story.badges["SINNOH"] = ["COAL", "FOREST"]
t = town("VEILSTONE_CITY", "SINNOH_ROUTE_215"); frames(t, 3)

t.player = t.anim_from = (11, 40); t.anim = 0; t.walk_goal = None
_heard = []
_orig = t.show_message
def _listen(lines, *a, **k):
    _heard.extend(lines); return _orig(lines, *a, **k)
t.show_message = _listen
_drive(t, 1500, lambda: story.story_flags.get("sinnoh_veilstone_wake_scene") and not t._busy())
t.show_message = _orig
check(story.story_flags.get("sinnoh_veilstone_wake_scene") and not t._busy(),
      f"Veilstone: walking up to the Gym, Dawn chats and Crasher Wake comes out of the Gym ({len(_heard)} lines heard)")
story.story_flags.clear(); story.story_flags.update(_sv); story.badges["SINNOH"] = _badges

# ---- S4 (11-24): Pastoria's Fen Badge story and the chase, as Platinum's (s_s4_pastoria_story.py)
_sv = dict(story.story_flags); _inv = dict(story.inventory); _badges = list(story.badges.get("SINNOH", []))
for _k in ("defeated_rival_pastoria", "sinnoh_pastoria_barry", "sinnoh_pastoria_bomb_warned", "sinnoh_pastoria_bomb", "sinnoh_r213_grunt_heard",
           "sinnoh_r213_looker", "sinnoh_valor_grunt_beaten", "sinnoh_valor_cynthia_came", "sinnoh_secretpotion"):
    story.story_flags.pop(_k, None)
story.inventory.pop("SECRET_POTION", None)
story.badges["SINNOH"] = ["COAL", "FOREST", "COBBLE"]
t = town("PASTORIA_CITY", "SINNOH_ROUTE_212"); frames(t, 3)
t.player = t.anim_from = (13, 29); t.anim = 0; t.walk_goal = None; t.step(0, -1)   # (Barry at the Gym's door: walk into him)
_drive(t, 600, lambda: "Battle" in type(g.current_state).__name__)
_bb = g.current_state if "Battle" in type(g.current_state).__name__ else None
story.story_flags["defeated_rival_pastoria"] = True
story.badges["SINNOH"] = ["COAL", "FOREST", "COBBLE", "FEN"]
t = town("PASTORIA_CITY", "SINNOH_ROUTE_212"); frames(t, 3)
t.player = t.anim_from = (13, 28); t.anim = 0; t.walk_goal = None
_drive(t, 900, lambda: story.story_flags.get("sinnoh_pastoria_bomb_warned") and not t._busy())
_two = {str(o.get("text")) for o in t._people().values()} >= {"Crasher Wake", "Barry"}
t.player = t.anim_from = (34, 10); t.anim = 0; t.walk_goal = None
_drive(t, 1500, lambda: story.story_flags.get("sinnoh_pastoria_bomb") and not t._busy())
_guarded = (34, 10) in t.barred
r = route("SINNOH_ROUTE_213", "PASTORIA_CITY")
_gr = next((m for m in r.run.floor.movers if m.kind == "figure" and str((m.payload or {}).get("text")) == "Galactic Grunt"), None)
if _gr is not None:
    r.run.player = [_gr.x - 1, _gr.y]
    r._use_figure(_gr); _drive(r, 900, lambda: story.story_flags.get("sinnoh_r213_looker") and not (getattr(r, "dialogue_box", None) and r.dialogue_box.visible))
r = route("VALOR_LAKEFRONT", "SINNOH_ROUTE_213")
_vg = next((m for m in r.run.floor.movers if m.kind == "figure" and str((m.payload or {}).get("text")) == "Galactic Grunt"), None)
_vb = None
if _vg is not None:
    r.run.player = [_vg.x - 1, _vg.y]
    r._use_figure(_vg); _drive(r, 600, lambda: "Battle" in type(g.current_state).__name__)
    _vb = g.current_state if "Battle" in type(g.current_state).__name__ else None
story.story_flags["sinnoh_valor_grunt_beaten"] = True
r = route("VALOR_LAKEFRONT", "SINNOH_ROUTE_213")
r.run.player = [36, 55]
_drive(r, 1500, lambda: story.story_flags.get("sinnoh_valor_cynthia_came") and not (getattr(r, "dialogue_box", None) and r.dialogue_box.visible))
_cy = next((m for m in r.run.floor.movers if m.kind == "figure" and str((m.payload or {}).get("text")) == "Cynthia"), None)
if _cy is not None:
    r._use_figure(_cy); _drive(r, 300, lambda: not (getattr(r, "dialogue_box", None) and r.dialogue_box.visible))
t = town("PASTORIA_CITY", "SINNOH_ROUTE_213"); frames(t, 25)
check(_bb is not None and _two and _guarded and story.story_flags.get("sinnoh_r213_looker") and _vb is not None
      and story.inventory.get("SECRET_POTION") and (34, 10) not in t.barred,
      f"Pastoria: Barry battles you at the Gym; with the Fen Badge, Wake and Barry, the bomb, Barry guards the gate; the chase: Route 213, Looker, the Valor grunt, Cynthia's SecretPotion; the gate opens "
      f"({_bb is not None}, {_two}, {_guarded}, {story.story_flags.get('sinnoh_r213_looker')}, {_vb is not None}, {story.inventory.get('SECRET_POTION')}, {(34, 10) in t.barred})")
story.story_flags.clear(); story.story_flags.update(_sv); story.inventory.clear(); story.inventory.update(_inv); story.badges["SINNOH"] = _badges

# ---- S4 (11-24): Celestic as Platinum's - the Grunt at the ruins, the Elder takes the Old Charm, Cyrus and Surf in the ruins
_sv = dict(story.story_flags); _inv = dict(story.inventory); _badges = list(story.badges.get("SINNOH", []))
for _k in ("sinnoh_celestic_grunt_beaten", "delivered_old_charm", "defeated_cyrus_celestic", "got_hm_surf_celestic"):
    story.story_flags.pop(_k, None)
story.inventory.pop("HM_SURF", None); story.inventory["OLD_CHARM"] = 1
story.badges["SINNOH"] = ["COAL", "FOREST", "COBBLE", "FEN"]
t = town("CELESTIC_TOWN", "SINNOH_ROUTE_210"); frames(t, 3)
_shut = any(str(o.get("text")) == "Galactic Grunt" for o in t._people().values())
_g = next((s_ for s_, o in t._people().items() if str(o.get("text")) == "Galactic Grunt"), None)
_gb = None
if _g:
    t.player = t.anim_from = (_g[0], _g[1] + 1); t.anim = 0; t.walk_goal = None
    t._talk(_g); _drive(t, 600, lambda: "Battle" in type(g.current_state).__name__)
    _gb = g.current_state if "Battle" in type(g.current_state).__name__ else None
story.story_flags["sinnoh_celestic_grunt_beaten"] = True
t = town("CELESTIC_TOWN", "SINNOH_ROUTE_210"); frames(t, 3)
t.player = t.anim_from = (15, 11); t.anim = 0; t.walk_goal = None
_drive(t, 1200, lambda: story.story_flags.get("delivered_old_charm") and not t._busy())
_taken = story.story_flags.get("delivered_old_charm") and not story.inventory.get("OLD_CHARM")
t.player = t.anim_from = (15, 10); t.anim = 0; t.walk_goal = None; t.step(0, -1)
_drive(t, 200, lambda: t.room == "ruins")
_cy = next((s_ for s_, o in t._people().items() if str(o.get("text")) == "Cyrus"), None)
_el = next((s_ for s_, o in t._people().items() if str(o.get("text")) == "Elder"), None)
if _el:
    t.player = t.anim_from = (_el[0], _el[1] + 1); t.anim = 0
    t._talk(_el); _drive(t, 400, lambda: not getattr(t, "npc_active", False))
check(_shut and _gb is not None and _taken and t.room == "ruins" and _cy is not None and story.inventory.get("HM_SURF"),
      f"Celestic: the Grunt at the ruins battles you; the Elder takes the Old Charm; in the ruins Cyrus, and the Elder's HM Surf "
      f"({_shut}, {_gb is not None}, {_taken}, {t.room}, {_cy}, {story.inventory.get('HM_SURF')})")
story.story_flags.clear(); story.story_flags.update(_sv); story.inventory.clear(); story.inventory.update(_inv); story.badges["SINNOH"] = _badges

# ---- S4 (11-24): Pastoria's and Route 213's rooms as Platinum's (s_s4_pastoria_rooms.py, s_s4_r213.py)
_sv = dict(story.story_flags); _inv = dict(story.inventory); _team = list(story.player_team)
_c1, _c2 = mk(415), mk(415); _c1.gender, _c2.gender = "M", "F"
story.player_team = [_c1, _c2]
t = town("PASTORIA_CITY", "SINNOH_ROUTE_212"); frames(t, 3)
t._go("house_0301", "OUT:25,35"); frames(t, 3)
_boy = next((s_ for s_, o in t._people().items() if str(o.get("text")) == "Boy"), None)
if _boy:
    t._talk(_boy); _drive(t, 400, lambda: story.inventory.get("MACHO_BRACE"))
_brace = story.inventory.get("MACHO_BRACE")
story.player_team = _team
t._go("house_0401", "OUT:35,35"); frames(t, 3)
_maniac = any(str(o.get("text")) == "Move Reminder" for o in t._people().values()) or "Move Reminder" in t.town_map["rooms"]["house_0401"]["people"]
story.story_flags["sinnoh_valor_grunt_beaten"] = True; story.story_flags["sinnoh_pastoria_bomb"] = True
t = town("PASTORIA_CITY", "SINNOH_ROUTE_212"); frames(t, 3)
t.player = t.anim_from = (34, 10); t.anim = 0; t.walk_goal = None; t.step(0, -1)
_drive(t, 120, lambda: t.room == "observatory_gate")
_gate = t.room == "observatory_gate"
_n = next((k for k, v in t.exits.items() if v == "GREAT_MARSH"), None)
if _n:
    t.player = t.anim_from = (_n[0], _n[1] + 1); t.anim = 0; t.step(0, -1)
    _drive(t, 400, lambda: getattr(g.current_state, "area_key", None) == "GREAT_MARSH" or story.current_area_key == "GREAT_MARSH")
_marsh = story.current_area_key == "GREAT_MARSH"
r = route("SINNOH_ROUTE_213", "PASTORIA_CITY")
_r213_gate = r.run.index > 0 or getattr(r, "room", None) == "gate" or any(str(k).startswith("gate") for k in [getattr(r.run, "name", "")])
story.inventory["SUITE_KEY"] = 1
r = route("VALOR_LAKEFRONT", "SINNOH_ROUTE_213")
_sg = next((m for m in r.run.floor.movers if m.kind == "figure" and str((m.payload or {}).get("text")) == "Suite guest"), None)
if _sg is not None:
    r._use_figure(_sg); _drive(r, 300, lambda: not (getattr(r, "dialogue_box", None) and r.dialogue_box.visible))
check(_brace and _maniac and _gate and _marsh and story.inventory.get("WHITE_FLUTE") and not story.inventory.get("SUITE_KEY"),
      f"Pastoria: the Combee pair earns a Macho Brace, the Move Maniac in his own house, the Observatory Gate into the Great Marsh; "
      f"Valor: the Suite Key brings a White Flute ({_brace}, {_maniac}, {_gate}, {_marsh}, {story.inventory.get('WHITE_FLUTE')}; Route 213 from Pastoria in its gate: {_r213_gate})")
story.story_flags.clear(); story.story_flags.update(_sv); story.inventory.clear(); story.inventory.update(_inv)

# ---- S4 (11-24): Pastoria Gym's water, Platinum's rule (src/world/pastoria_gym.py, s_s4_pastoria_gym.py)
_sv = dict(story.story_flags)
story.story_flags.pop("pastoria_gym_water", None)
t = town("PASTORIA_CITY", "SINNOH_ROUTE_212"); frames(t, 3)
t._go("gym", "OUT:13,27"); frames(t, 5); _drive(t, 200, lambda: not t._busy())
_mid_open = (13, 35) not in t.barred and (6, 8) in t.barred   # (middle ground open, high ground shut, with the water in the middle)
t.player = t.anim_from = (9, 15); t.anim = 0; t.walk_goal = None; t.step(0, -1)   # (onto the orange button (9,14))
_drive(t, 300, lambda: story.story_flags.get("pastoria_gym_water") == "low" and not t._busy())
frames(t, 3)
_low = story.story_flags.get("pastoria_gym_water") == "low" and (6, 8) not in t.barred and (13, 35) in t.barred
check(_mid_open and _low, f"Pastoria Gym: the water starts in the middle; the orange button drains it, high ground opens, middle ground shuts ({_mid_open}, {_low})")
story.story_flags.clear(); story.story_flags.update(_sv)

# ---- S5 (11-24): Canalave Gym, Platinum's four floors and moving platforms (src/world/canalave_gym.py, s_s5_canalave_gym.py)
_sv = dict(story.story_flags)
for _k in ("canalave_gym_platforms", "canalave_gym_arrived"):
    story.story_flags.pop(_k, None)
t = town("CANALAVE_CITY", "SINNOH_ROUTE_218"); frames(t, 3)
t._go("gym", "OUT:7,27"); frames(t, 5); _drive(t, 200, lambda: not t._busy())
_f1 = t.room == "gym"
t.player = t.anim_from = (11, 14); t.anim = 0; t.walk_goal = None; t.step(0, -1)   # (onto the lift at (11,13): up to 2F)
_drive(t, 300, lambda: t.room == "gym_2f" and not t._busy())
_up = t.room == "gym_2f" and tuple(t.player) == (11, 13)
frames(t, 30)
_stays = t.room == "gym_2f"   # (standing where it set you down: it doesn't carry you straight back)
check(_f1 and _up and _stays, f"Canalave Gym: the lift at (11,13) carries you from 1F up to 2F, and stays put till you step off ({_f1}, {_up}, {_stays}, {t.room}, {t.player})")
story.story_flags.clear(); story.story_flags.update(_sv)

# ---- S5 (11-24, Jordan's answers): Barry on Canalave's bridge, and at the Library door till you have Strength from Riley
_sv, _bv, _iv = dict(story.story_flags), list(story.badges.get("SINNOH", [])), dict(story.inventory)
story.story_flags.pop("defeated_rival_canalave", None)
story.badges["SINNOH"] = ["COAL", "FOREST", "COBBLE", "FEN", "RELIC"]
t = town("CANALAVE_CITY", "SINNOH_ROUTE_218"); frames(t, 3); _drive(t, 100, lambda: not t._busy())
t.player = t.anim_from = (16, 20); t.anim = 0; t.walk_goal = None; t.step(-1, 0)   # (west over the bridge, onto x=15)
_drive(t, 60, lambda: t._busy())
_stopped = t._busy()
_ad = __import__("json").load(open("assets/sinnoh_area_data.json", encoding="utf-8"))["STORY_PROGRESSION"]["CANALAVE_CITY"]
check(_stopped and not _ad.get("on_enter_event"), f"Canalave: Barry stops you on the bridge before the Gym (Platinum's), no arrival battle ({_stopped})")
story.story_flags["defeated_rival_canalave"] = True
story.badges["SINNOH"] = _bv[:0] + ["COAL", "FOREST", "COBBLE", "FEN", "RELIC", "MINE"]
story.inventory["HM_STRENGTH"] = 0
t = town("CANALAVE_CITY", "SINNOH_ROUTE_218"); frames(t, 3)
_wait = (5, 15) in t.barred
story.inventory["HM_STRENGTH"] = 1
t = town("CANALAVE_CITY", "SINNOH_ROUTE_218"); frames(t, 3)
_in = (5, 15) not in t.barred
_hm = __import__("src.world.hms", fromlist=["HM_BY_BADGE"]).HM_BY_BADGE["SINNOH"]
check(_wait and _in and "MINE" not in _hm, f"Canalave: Barry waits at the Library door till you have HM Strength (Riley's, not the Mine Badge's) ({_wait}, {_in})")
story.story_flags.clear(); story.story_flags.update(_sv); story.badges["SINNOH"] = _bv
story.inventory.clear(); story.inventory.update(_iv)

# ---- S5 (11-24, the Journal's full playthrough): back from Iron Island you land on Canalave's dock, not a pocket by the boats
t = town("CANALAVE_CITY", "IRON_ISLAND"); frames(t, 3)
_seen, _todo = {tuple(t.player)}, [tuple(t.player)]
while _todo:
    _c = _todo.pop()
    for _dx, _dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        _n = (_c[0] + _dx, _c[1] + _dy)
        if _n not in _seen and t._open(_n) and _n not in t.exits:
            _seen.add(_n); _todo.append(_n)
check((7, 28) in _seen and (13, 45) not in _seen, f"Canalave: off the Iron Island boat at {t.player}, the Gym's door can be walked to ({len(_seen)} tiles open)")

# ---- S5 (11-24, the Journal's split-place step): in at Mt. Coronet's Route 211 side, its north part, sets coronet_north_side
story.story_flags.pop("coronet_north_side", None)
r = route("MT_CORONET_BASE", "SINNOH_ROUTE_211")
for _ in range(120):
    g.current_state.update()
_f7 = getattr(getattr(r, "run", None), "index", None)
check(_f7 == 7 and story.story_flags.get("coronet_north_side"), f"Mt. Coronet: in from Route 211 you're on its north side (floor {_f7}), and it's noted (coronet_north_side: {story.story_flags.get('coronet_north_side')})")
story.story_flags.pop("coronet_north_side", None)
r = route("MT_CORONET_BASE", "SINNOH_ROUTE_207")
for _ in range(120):
    g.current_state.update()
check(not story.story_flags.get("coronet_north_side"), "Mt. Coronet: in from Route 207 (the south rooms) it isn't")

# ---- (11-24, inbox clean-sinnoh-main-frontier-gen4-pokemon): Sinnoh's Frontier draws Gen IV's own Tower sets' Pokemon (HGSS = Platinum's)
from src.world import frontier as _fr
_ids = {i for _ in range(40) for i in _fr._team(g, [0, 1, 2, 3], 3, fac="stower")}
_g4 = {str(i) for gg in _fr.data4(g)["groups"].values() for i in gg}
check(_ids and all(str(i) in _g4 for i in _ids) and any(387 <= int(i) <= 493 for i in _ids),
      f"Sinnoh's Battle Tower: its Pokemon from Gen IV's groups, Gen 4 ones among them ({len(_ids)} seen)")

# ---- S6 (11-24, s_s6_sunyshore.py): Volkner at the Vista Lighthouse, then his Gym's three rooms of turning walkways
_sv = dict(story.story_flags)
for _k in ("volkner_returned_to_gym", "sunyshore_gym_gears"):
    story.story_flags.pop(_k, None)
story.story_flags["spear_pillar_resolved"] = True
_ad = __import__("json").load(open("assets/sinnoh_area_data.json", encoding="utf-8"))["STORY_PROGRESSION"]["SUNYSHORE_CITY"]
_req = _ad["gym"]["requirements"].get("flag") == "volkner_returned_to_gym"
t = town("SUNYSHORE_CITY", "SINNOH_ROUTE_222"); frames(t, 3)
_door = t._room_for((54, 54)) == "lighthouse" if hasattr(t, "_room_for") else (54, 54) in t.doors
t._go("lighthouse_top", "ROOM:lighthouse"); frames(t, 5); _drive(t, 200, lambda: not t._busy())
_vk = next((p_ for p_, o in t._people().items() if str(o.get("text")) == "Volkner"), None)
if _vk is not None:
    t.player = t.anim_from = (_vk[0], _vk[1] + 1); t.anim = 0; t.facing = (0, -1)
    t._talk(tuple(_vk)); _drive(t, 600, lambda: not t._busy() and not getattr(t, "npc_active", False))
_met = bool(story.story_flags.get("volkner_returned_to_gym"))
from src.world import sunyshore_gym as _SG
t = town("SUNYSHORE_CITY", "SINNOH_ROUTE_222"); frames(t, 3)
t._go("gym", "OUT:13,11"); frames(t, 5); _drive(t, 200, lambda: not t._busy())
_gap0 = (4, 8) in t.barred          # (room 1, state 0: region 2 (4,8) is turned away)
_drive(t, 300, lambda: not t._busy() and not getattr(t, "npc_active", False) and not getattr(getattr(t, "dialogue_box", None), "visible", False))
t.player = t.anim_from = (2, 8); t.anim = 0; t.walk_goal = None; t.step(1, 0)   # (onto the west gear's middle: a quarter turn)
for _q in range(120):
    g.current_state.update()
_drive(t, 300, lambda: not t._busy())
_st = _SG.state(story, 0)
_gap1 = (4, 8) not in t.barred and (9, 8) in t.barred   # (state 1: region 2 (4,8) open, region 6 (9,8) turned away)
_pic = getattr(t, "_pic_now", None)
_gap1 = _gap1 and str(_pic).endswith("C08GYM0101_g1.png")   # (and the room's live scene is the one with the gears turned)
_rooms = all(r in t.town_map["rooms"] for r in ("gym_2", "gym_3", "lighthouse", "lighthouse_top"))
_vg = any((p_ if isinstance(p_, str) else p_.get("text") if isinstance(p_, dict) else None) == "Gym" for p_ in t.town_map["rooms"]["gym_3"].get("people", []))
check(_req and _door and _met and _gap0 and _st == 1 and _gap1 and _rooms and _vg,
      f"Sunyshore: Volkner at the Vista Lighthouse opens his Gym; its walkways turn as you step on a gear's middle, the scene with Platinum's gears turned (Platinum's) ({_req}, {_door}, {_met}, {_gap0}, {_st}, {_gap1} {_pic}, {_rooms}, {_vg})")
story.story_flags.clear(); story.story_flags.update(_sv)

# ---- S6 (11-24, s_s6_victory_road.py): Victory Road's Strength boulders pushed a tile at a time, back at their start on coming in
_vr = _tm["VICTORY_ROAD_SINNOH"]["floors"]
_n = (len(_vr[0].get("boxes") or []), len(_vr[4].get("boxes") or []))
_sv, _bv = dict(story.story_flags), list(story.badges.get("SINNOH", []))
story.badges["SINNOH"] = ["COAL", "FOREST", "COBBLE", "FEN", "RELIC", "MINE", "ICICLE", "BEACON"]
story.inventory["HM_STRENGTH"] = 1
story.story_flags.pop("boxes_VICTORY_ROAD_SINNOH_0", None)
r = route("VICTORY_ROAD_SINNOH", "SINNOH_ROUTE_223")
r.run.jump_floor(0, (19, 4)); frames(r, 3); r._place_boxes()
_b = next((tuple(b) for b in _vr[0]["boxes"] for d in ((1, 0), (-1, 0), (0, 1), (0, -1))
           if r.run.floor.walkable(b[0] - d[0], b[1] - d[1]) and r.run.floor.tile(b[0] + d[0], b[1] + d[1]) == 1
           and (b[0] + d[0], b[1] + d[1]) not in r.run.floor.decor), None)
_d = next(d for d in ((1, 0), (-1, 0), (0, 1), (0, -1)) if _b and r.run.floor.walkable(_b[0] - d[0], _b[1] - d[1])
          and r.run.floor.tile(_b[0] + d[0], _b[1] + d[1]) == 1 and (_b[0] + d[0], _b[1] + d[1]) not in r.run.floor.decor) if _b else None
_moved = bool(_b) and r._push_box(_b, *_d) and str(r.run.floor.decor.get((_b[0] + _d[0], _b[1] + _d[1]), "")).startswith("box:")
story.last_area_key = "SINNOH_ROUTE_223"
r = route("VICTORY_ROAD_SINNOH", "SINNOH_ROUTE_223")
r.run.jump_floor(0, (19, 4)); frames(r, 3); r._place_boxes()
_back = bool(_b) and str(r.run.floor.decor.get(_b, "")).startswith("box:")
check(_n == (16, 10) and _moved and _back,
      f"Victory Road: Platinum's 26 Strength boulders (2F {_n[0]}, the side room {_n[1]}) pushed a tile at a time, back at their start when you come in again ({_b}, {_d}, {_moved}, {_back})")
story.story_flags.clear(); story.story_flags.update(_sv); story.badges["SINNOH"] = _bv

# ---- S5 (11-24): Route 213's gatehouse is a room again, walked through (main a91de160: arrival by land or by sea)
story.badges["SINNOH"] = ["COAL", "FOREST", "COBBLE", "FEN", "RELIC"]
t = town("PASTORIA_CITY", "SINNOH_ROUTE_212"); frames(t, 3); _drive(t, 200, lambda: not t._busy())
t.player = t.anim_from = (62, 12); t.anim = 0; t.walk_goal = None; t.step(1, 0)   # (east on foot, out by the land way)
_drive(t, 300, lambda: story.current_area_key == "SINNOH_ROUTE_213" and "Play" in type(g.current_state).__name__)
r = g.current_state
_fl = getattr(getattr(r, "run", None), "floor", None)
_here = [str((m.payload or {}).get("text")) for m in (getattr(_fl, "movers", None) or []) if m.kind == "figure"]
_pos = tuple(getattr(getattr(r, "run", None), "player", None) or ())
_ok = story.current_area_key == "SINNOH_ROUTE_213" and {"Man", "Gentleman"} <= set(_here) and _fl is not None and _fl.walkable(*_pos)
check(_ok, f"Route 213: walking out of Pastoria by land puts you in its gatehouse, on its floor, beside its two people ({story.current_area_key}, {_here}, {_pos})")
story.badges["SINNOH"] = _bv

# ---- S5 (11-24): Lake Valor as Platinum's - the drained lake with Saturn's grunts till he's beaten in Valor Cavern, then the full lake
_sv = dict(story.story_flags)
story.story_flags["canalave_library_meeting"] = True
story.story_flags.pop("galactic_lake_valor_cleared", None)
r = route("LAKE_VALOR", "VALOR_LAKEFRONT")
_dr = r.run.index == 0
_gr = [m for m in r.run.floor.movers if m.kind == "trainer"]
_lk = (r.run.recipe.get("art") or {}).get("floors", [{}])[0].get("links") or {}
r.run.warp(0, 32, 32)                                          # (beside the drained lake's cave mouth...)
_px, _py = r.run.player
r._handle(r.run.step(32 - _px, 32 - _py))                      # (...and into Valor Cavern)
for _q in range(40):
    frames(r)
_cav = r.run.index == 2
_sat = next((m for m in r.run.floor.movers if m.kind == "figure" and str((m.payload or {}).get("text")) == "Confront Saturn at the Lake"), None)
_vb = False
if _sat is not None:
    r.run.player = [_sat.x, _sat.y + 1]
    r._use_figure(_sat)
    _drive(r, 600, lambda: "Battle" in type(g.current_state).__name__)
    _vb = "Battle" in type(g.current_state).__name__
    _st = g.current_state
    _foe = [p.id if hasattr(p, "id") else getattr(p, "species_id", None) for p in (getattr(_st, "enemy_team", None) or [])]
check(_cav and _vb, f"Lake Valor: the drained lake's cave mouth leads into Valor Cavern, where Saturn battles you ({_cav}, {_sat is not None}, {_vb})")
story.story_flags["galactic_lake_valor_cleared"] = True
r = route("LAKE_VALOR", "VALOR_LAKEFRONT")
_full = r.run.index == 1
check(_dr and len(_gr) == 2 and _full and list(_lk.values()) == [[2, 14, 29]],
      f"Lake Valor: drained with two Galactic Grunts till Saturn is beaten (the cave mouth leads to Valor Cavern), then the full lake ({_dr}, {len(_gr)}, {_full}, {_lk})")
story.story_flags.clear(); story.story_flags.update(_sv)

# ---- S5 (11-24): Lake Verity after Valor, as Platinum's - Mars at the lake's edge with Rowan and Dawn beside her, four grunts
_sv = dict(story.story_flags)
story.story_flags.update({"canalave_library_meeting": True, "galactic_lake_valor_cleared": True, "sinnoh_rowan_walked_up": True, "received_starter_sinnoh": True})
story.story_flags.pop("galactic_lake_verity_cleared", None)
r = route("LAKE_VERITY", "VERITY_LAKEFRONT")
_f = r.run.floor
_mars = next((m for m in _f.movers if m.kind == "figure" and str((m.payload or {}).get("text")) == "Confront Galactic at the Lake"), None)
_two = all(str(_f.decor.get(t, "")).startswith("barrier:") for t in ((45, 25), (46, 24)))
_gr = [m for m in _f.movers if m.kind == "trainer"]
_vb = False
if _mars is not None:
    r.run.player = [_mars.x - 1, _mars.y]
    r._use_figure(_mars)
    _drive(r, 600, lambda: "Battle" in type(g.current_state).__name__)
    _vb = "Battle" in type(g.current_state).__name__
check(_mars is not None and (_mars.x, _mars.y) == (47, 24) and _two and len(_gr) == 4 and _vb,
      f"Lake Verity after Valor: Mars at Platinum's spot with Rowan and Dawn beside her, four grunts, and her battle ({_mars and (_mars.x, _mars.y)}, {_two}, {len(_gr)}, {_vb})")
story.story_flags.clear(); story.story_flags.update(_sv)

# ---- S5 (11-24): Snowpoint Gym as Platinum's - you slide across its ice; sliding into a snowball crushes it, walking into one doesn't
_sv = dict(story.story_flags)
for _k in [k for k in story.story_flags if k.startswith("snowpoint_gym_snowball_")]:
    story.story_flags.pop(_k)
t = town("SNOWPOINT_CITY", "SINNOH_ROUTE_217"); frames(t, 3)
t._go("gym", "OUT:15,30"); frames(t, 5); _drive(t, 200, lambda: not t._busy())
_ga = _tm["SNOWPOINT_CITY"]["rooms"]["gym"]["art"]
_balls = {tuple(b["tiles"][0]): b for b in _tm["SNOWPOINT_CITY"]["rooms"]["gym"]["barred"] if b.get("smash")}
_try = None
for (_bx, _by), _b in sorted(_balls.items()):
    for _dx, _dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        _cx, _cy, _n = _bx - _dx, _by - _dy, 0
        while 0 <= _cy < len(_ga) and 0 <= _cx < len(_ga[0]) and _ga[_cy][_cx] == "%" and (_cx, _cy) not in _balls:
            _cx, _cy, _n = _cx - _dx, _cy - _dy, _n + 1
        if _n >= 2 and 0 <= _cy < len(_ga) and _ga[_cy][_cx] == "." and t._open((_cx, _cy)):
            _try = ((_cx, _cy), (_dx, _dy), (_bx, _by), _b["smash"])
            break
    if _try:
        break
_slid = _crushed = False
if _try:
    (_sx, _sy), (_dx, _dy), _bt, _bf = _try
    t.player = t.anim_from = (_sx, _sy); t.anim = 0; t.walk_goal = None
    t.step(_dx, _dy)
    _drive(t, 400, lambda: not getattr(t, "_slide", None) and t.anim == 0 and not t._busy())
    _crushed = bool(story.story_flags.get(_bf)) and _bt not in t.barred
    _slid = abs(t.player[0] - _sx) + abs(t.player[1] - _sy) >= 2
check(_try is not None and _slid and _crushed and t.room == "gym",
      f"Snowpoint Gym: you slide across the ice and crush a snowball in your way ({_try}, {_slid}, {_crushed}, {t.player})")
story.story_flags.clear(); story.story_flags.update(_sv)

# ---- S5 (11-24): the road to Snowpoint as Platinum's - Maylene on Route 217, Barry at Acuity's lumpy rocks, Rock Climb walls
_sv, _bv, _iv = dict(story.story_flags), list(story.badges.get("SINNOH", [])), dict(story.inventory)
story.badges["SINNOH"] = ["COAL", "FOREST", "COBBLE", "FEN", "RELIC", "MINE"]
for _k in ("sinnoh_r217_maylene", "sinnoh_acuity_barry"):
    story.story_flags.pop(_k, None)
t = town("SINNOH_ROUTE_217", "SINNOH_ROUTE_216"); frames(t, 3); _drive(t, 100, lambda: not t._busy())
t.player = t.anim_from = (14, 121); t.anim = 0; t.walk_goal = None; t.step(0, -1)
_drive(t, 900, lambda: story.story_flags.get("sinnoh_r217_maylene") and not t._busy())
_may = bool(story.story_flags.get("sinnoh_r217_maylene"))
story.inventory["HM_ROCK_CLIMB"] = 0
t = town("ACUITY_LAKEFRONT", "SINNOH_ROUTE_217"); frames(t, 3); _drive(t, 100, lambda: not t._busy())
t.player = t.anim_from = (12, 35); t.anim = 0; t.walk_goal = None; t.step(0, -1)
_drive(t, 900, lambda: story.story_flags.get("sinnoh_acuity_barry") and not t._busy())
_bar = bool(story.story_flags.get("sinnoh_acuity_barry"))
_wall = not t._open((12, 30))
story.inventory["HM_ROCK_CLIMB"] = 1
_noclimb = not t._open((12, 30))   # (Platinum: Rock Climb needs the Icicle Badge too; Jordan 11-24)
story.badges["SINNOH"] = story.badges["SINNOH"] + ["ICICLE"]
_climb = t._open((12, 30)) and _noclimb
t = town("SNOWPOINT_CITY", "SINNOH_ROUTE_217"); frames(t, 3)
t._go("center", "OUT:27,41"); frames(t, 5); _drive(t, 200, lambda: not t._busy())
_mp = [o for o in t.people.values() if o.get("text") == "Maylene"]
check(_may and _bar and _wall and _climb and len(_mp) == 1,
      f"Snowpoint road: Maylene meets you on Route 217, Barry warns you off Acuity's rocks, they're climbed with Rock Climb, Maylene warms up in the Center ({_may}, {_bar}, {_wall}, {_climb}, {len(_mp)})")
story.story_flags.clear(); story.story_flags.update(_sv); story.badges["SINNOH"] = _bv
story.inventory.clear(); story.inventory.update(_iv)

# ---- S5 (11-24): Lake Acuity as Platinum's - Barry has just lost to Jupiter as you arrive; she leaves for the Veilstone HQ, he swears to get stronger
_sv, _bv = dict(story.story_flags), list(story.badges.get("SINNOH", []))
story.badges["SINNOH"] = ["COAL", "FOREST", "COBBLE", "FEN", "RELIC", "MINE", "ICICLE"]
story.story_flags.pop("galactic_lake_acuity_cleared", None)
r = route("LAKE_ACUITY", "ACUITY_LAKEFRONT")
for _q in range(1500):
    if getattr(r, "dialogue_box", None) and r.dialogue_box.visible:
        r.dialogue_box.advance()
    frames(r)
    if story.story_flags.get("galactic_lake_acuity_cleared"):
        break
_done = bool(story.story_flags.get("galactic_lake_acuity_cleared"))
r = route("LAKE_ACUITY", "ACUITY_LAKEFRONT"); frames(r, 5)
_jgone = not any(m.kind == "figure" and str((m.payload or {}).get("text")) == "Confront Jupiter at the Lake" for m in r.run.floor.movers)
check(_done and _jgone, f"Lake Acuity: Platinum's scene plays as you arrive with the Icicle Badge (Barry beaten, Jupiter off to Veilstone), then she's gone ({_done}, {_jgone})")
story.story_flags.clear(); story.story_flags.update(_sv); story.badges["SINNOH"] = _bv

# ---- 11-24 (hub cleanup): Veilstone's Game Corner machines are played by walking up to them, as Goldenrod's
_iv = dict(story.inventory)
t = town("VEILSTONE_CITY", None); frames(t, 3)
t._go("game_corner", "OUT:34,47"); frames(t, 5); _drive(t, 200, lambda: not t._busy())
_mach = [(x, y) for x in (7, 8, 12, 13) for y in range(4, 9) if t._game_machine((x, y))]
story.inventory["COIN_CASE"] = 1
t.player = t.anim_from = (6, 6); t.anim = 0; t.walk_goal = None; t.step(1, 0)
frames(t, 3)
_play = "Voltorb" in type(g.current_state).__name__
check(len(_mach) == 20 and _play, f"Veilstone Game Corner: its 20 slot machine tiles are machines you walk up to and play ({len(_mach)}, {_play}, {type(g.current_state).__name__})")
story.inventory.clear(); story.inventory.update(_iv)

# ---- 11-24 (encyclopedia cleanup): Platinum's Berry patches are soft soil on the routes (src/world/berries.py)
r = route("SINNOH_ROUTE_211", "ETERNA_CITY")
_soil = sorted(t for t, d in r.run.floor.decor.items() if str(d).startswith("soil:"))
_ns = sum(len(((_tm[k].get("floors") or [_tm[k]])[0]).get("berry_soil") or []) for k in _tm if k in _sin)
check(len(_soil) == 4 and _ns >= 80, f"Route 211: Platinum's four Berry patches stand as soil you can pick and plant; {_ns} patches over Sinnoh's routes ({_soil})")

# ---- S5 (11-24): Galactic HQ as Platinum's - Looker opens the Warehouse with the Storage Key, Galactic Key doors, Cyrus on 4F, Saturn and the lake trio's machine
_sv, _iv = dict(story.story_flags), dict(story.inventory)
for _k in ("sinnoh_storage_door_open", "sinnoh_hq_cyrus_beaten", "sinnoh_hq_saturn_beaten", "galactic_hq_cleared"):
    story.story_flags.pop(_k, None)
story.story_flags.update({"galactic_lake_acuity_cleared": True, "sinnoh_warehouse_looker": True})
story.inventory["GALACTIC_KEY"] = 0
r = route("GALACTIC_WAREHOUSE", "VEILSTONE_CITY")
for _q in range(900):
    if getattr(r, "dialogue_box", None) and r.dialogue_box.visible:
        r.dialogue_box.advance()
    frames(r)
    if story.story_flags.get("sinnoh_storage_door_open"):
        break
_door = bool(story.story_flags.get("sinnoh_storage_door_open"))
def _hq_battle(r, who):
    _m = next((m for m in r.run.floor.movers if m.kind == "figure" and str((m.payload or {}).get("text")) == who), None)
    if _m is None:
        return None
    r.run.player = [_m.x - 1, _m.y]
    r._use_figure(_m)
    _drive(r, 600, lambda: "Battle" in type(g.current_state).__name__)
    return "Battle" in type(g.current_state).__name__
r = route("TEAM_GALACTIC_HQ", "VEILSTONE_CITY")
r.run.warp(3, 8, 10); frames(r, 3)
_locked = str(r.run.floor.decor.get((8, 13), "")).startswith("barrier:")
_cy = _hq_battle(r, "Cyrus")
r = route("TEAM_GALACTIC_HQ", "VEILSTONE_CITY")
r.run.warp(5, 8, 11); frames(r, 3)
_trio = sum(1 for t in ((2, 3), (14, 3), (8, 9)) if str((getattr(r, "_bars", {}).get(t) or {}).get("look", "")).startswith("mon:48") and str(r.run.floor.decor.get(t, "")).startswith("barrier:"))
_sa = _hq_battle(r, "Commander Saturn")
story.story_flags["sinnoh_hq_saturn_beaten"] = True
r = route("TEAM_GALACTIC_HQ", "VEILSTONE_CITY")
r.run.warp(5, 8, 11); frames(r, 3)
_mc = next((m for m in r.run.floor.movers if m.kind == "figure" and str((m.payload or {}).get("text")) == "Galactic machine"), None)
if _mc is not None:
    r.run.player = [_mc.x - 1, _mc.y]
    r._use_figure(_mc)
    for _q in range(300):
        if getattr(r, "dialogue_box", None) and r.dialogue_box.visible:
            r.dialogue_box.advance()
        frames(r)
_free = bool(story.story_flags.get("galactic_hq_cleared"))
check(_door and _locked and _cy and _trio == 3 and _sa and _free,
      f"Galactic HQ: Looker opens the Warehouse door, Galactic Key doors, Cyrus battles on 4F, the trio sealed, Saturn battles, the button frees them ({_door}, {_locked}, {_cy}, {_trio}, {_sa}, {_free})")
story.story_flags.clear(); story.story_flags.update(_sv); story.inventory.clear(); story.inventory.update(_iv)

# ---- S5 (11-24, s_s5_spear_pillar.py / s_s5_distortion.py): Spear Pillar's summit and the Distortion World's Cyrus, walked
_sv = dict(story.story_flags)
for _k in ("spear_pillar_commanders", "spear_pillar_resolved", "SPEAR_PILLAR_boss_defeated", "distortion_world_cleared"):
    story.story_flags.pop(_k, None)
story.story_flags["galactic_hq_cleared"] = True
def _figs(r):
    return {str((m.payload or {}).get("text")): m for m in r.run.floor.movers if m.kind == "figure"}
r = route("SPEAR_PILLAR", "MT_CORONET_BASE")
r.run.jump_floor(3, (10, 44)); frames(r, 3)
_f0 = set(_figs(r))
_mj = _hq_battle(r, "Battle Mars and Jupiter")
_b = g.current_state
_double = bool(getattr(_b, "partner", None) or getattr(_b, "is_double", False) or "Double" in type(_b).__name__ or getattr(_b, "double", False))
story.story_flags["spear_pillar_commanders"] = True
r = route("SPEAR_PILLAR", "MT_CORONET_BASE")
r.run.jump_floor(3, (10, 40)); frames(r, 3)
_cy = _hq_battle(r, "Confront Cyrus")
_cyteam = [getattr(p_, "id", None) for p_ in (getattr(g.current_state, "opponent_team", None) or [])]
story.story_flags["spear_pillar_resolved"] = True
r = route("SPEAR_PILLAR", "MT_CORONET_BASE")
r.run.jump_floor(3, (10, 13)); frames(r, 3)
_f2 = set(_figs(r))
check("Encounter Dialga" not in _f0 and {"Battle Mars and Jupiter", "Confront Cyrus"} <= _f0 and _mj and _cy and _cyteam[:1] == [229]
      and "Encounter Dialga" in _f2 and "Confront Cyrus" not in _f2,
      f"Spear Pillar: Mars and Jupiter battle at the narrow way in, Cyrus (Platinum's team, {_cyteam}) before the altar, then Dialga there ({_f0}, {_mj}, {_double}, {_cy}, {_f2})")
r = route("DISTORTION_WORLD", "SPEAR_PILLAR")
r.run.jump_floor(7, (5, 32)); frames(r, 3)
_cyd = [m for m in r.run.floor.movers if m.kind == "trainer"]
check(len(_cyd) == 1 and (_cyd[0].x, _cyd[0].y) == (5, 27), f"Distortion World: Cyrus stands at Platinum's spot on B7F ({[(m.x, m.y) for m in _cyd]})")
# (Platinum's Cynthia, s_s5_distortion.py: she walks with you from 1F and goes on alone on B2F)
for _k in [k for k in story.story_flags if k.startswith("walk_cynthia")]:
    story.story_flags.pop(_k)
r = route("DISTORTION_WORLD", "SPEAR_PILLAR")
r.run.jump_floor(0, (20, 31)); frames(r, 3); r._sync_figures()
_cm = next((m for m in r.run.floor.movers if m.kind == "figure" and str((m.payload or {}).get("text")) == "Cynthia"), None)
if _cm is not None:
    r.run.player = [_cm.x, _cm.y + 1]
    r._use_figure(_cm)
    _drive(r, 600, lambda: not getattr(r.dialogue_box, "visible", False))
_walks = bool(story.story_flags.get("walk_cynthia"))
from src.world import walk_partners as _wp
_bye = _wp.on_floor(story, "DISTORTION_WORLD", 1) == [] and bool(_wp.on_floor(story, "DISTORTION_WORLD", 2))
check(_cm is not None and _walks and _bye and story.story_flags.get("walk_cynthia_done"),
      f"Distortion World: Cynthia joins you on 1F and goes on alone on B2F, as in Platinum ({_cm is not None}, {_walks}, {_bye})")
for _k in [k for k in story.story_flags if k.startswith("walk_cynthia")]:
    story.story_flags.pop(_k)
# (Platinum's lake trio boulders, s_s5_distortion.py: pushed off B5F they fall to B6F; a wrong pit sends one back, the right one holds it)
for _k in [k for k in story.story_flags if k.startswith(("dw_", "boxes_DISTORTION_WORLD"))]:
    story.story_flags.pop(_k)
story.inventory["HM_STRENGTH"] = 1
_bv5 = list(story.badges.get("SINNOH", []))
story.badges["SINNOH"] = ["COAL", "FOREST", "COBBLE", "FEN", "RELIC", "MINE", "ICICLE"]
r = route("DISTORTION_WORLD", "SPEAR_PILLAR")
r.run.jump_floor(5, (11, 30)); frames(r, 3); r._place_boxes()
_b5 = str(r.run.floor.decor.get((12, 30), "")).startswith("box:")
r._push_box((12, 30), 1, 0); _drive(r, 200, lambda: not r.dialogue_box.visible) if hasattr(r, "dialogue_box") else None
_drop = bool(story.story_flags.get("dw_mesprit_dropped")) and not str(r.run.floor.decor.get((12, 30), "")).startswith("box:")
r.run.jump_floor(6, (10, 20)); frames(r, 3); r._place_boxes()
_land = str(r.run.floor.decor.get((10, 19), "")).startswith("box:")
r._push_box((10, 19), 0, -1)                                   # (north: into the wrong pit)
_back = not story.story_flags.get("dw_mesprit_dropped") and not str(r.run.floor.decor.get((10, 19), "")).startswith("box:")
r.run.jump_floor(5, (11, 30)); frames(r, 3); r._place_boxes()
_again = str(r.run.floor.decor.get((12, 30), "")).startswith("box:")
r._push_box((12, 30), 1, 0)
r.run.jump_floor(6, (11, 19)); frames(r, 3); r._place_boxes()
_t = (10, 19)
for _q in range(7):                                             # (west along the passage to its own pit, then north into it)
    r._push_box(_t, -1, 0); _t = (_t[0] - 1, _t[1])
r._push_box(_t, 0, -1)
_right = bool(story.story_flags.get("dw_mesprit_pit")) and story.story_flags.get("dw_mesprit_dropped")
_shut = str(r.run.floor.decor.get((21, 38), "")).startswith("barrier:")
check(_b5 and _drop and _land and _back and _again and _right and _shut,
      f"Distortion World: Mesprit's boulder pushed off B5F falls to B6F; a wrong pit sends it back to B5F, its own pit holds it; the way down waits for all three ({_b5}, {_drop}, {_land}, {_back}, {_again}, {_right}, {_shut})")
story.badges["SINNOH"] = _bv5
for _k in [k for k in story.story_flags if k.startswith(("dw_", "boxes_DISTORTION_WORLD"))]:
    story.story_flags.pop(_k)
story.story_flags.clear(); story.story_flags.update(_sv)

# ---- 11-24 (cleanups): the Coin Case (Veilstone's clown), the Sprayduck (Floaroma's florist) that waters Berry soil, and
#      Regigigas waking only for the three Regis in your party (Platinum)
_sv, _iv, _team = dict(story.story_flags), dict(story.inventory), list(story.player_team)
_rm = _tm["VEILSTONE_CITY"]["rooms"]["house_0501"]["people"]
_clown = next(p for p in _rm if isinstance(p, dict) and p.get("text") == "Sad clown")
_fl = next(p for p in _tm["FLOAROMA_TOWN"]["rooms"]["flower"]["people"] if isinstance(p, dict) and p.get("text") == "Florist")
from src.world import berries as _bz
story.inventory["SPRAYDUCK"] = 1; story.inventory.pop("WAILMER_PAIL", None)
_bz._all(story)["SINNOH_ROUTE_211:19,12"] = {"berry": "ORAN_BERRY", "t": __import__("time").time(), "water": []}
_wl, _ = _bz.touch(story, "SINNOH_ROUTE_211", (19, 12), "ORAN_BERRY")
_wet = any("Sprayduck" in l for l in _wl)
_boss = __import__("json").load(open("assets/sinnoh_area_data.json", encoding="utf-8"))["STORY_PROGRESSION"]["SNOWPOINT_TEMPLE"]["area_boss"]
story.player_team = [mk(387)]
r = route("SNOWPOINT_TEMPLE", "SNOWPOINT_CITY")
r.action_challenge_boss(dict(_boss)); frames(r, 5)
_asleep = "Battle" not in type(g.current_state).__name__
story.player_team = [mk(377), mk(378), mk(379)]
r = route("SNOWPOINT_TEMPLE", "SNOWPOINT_CITY"); story.player_team = [mk(377), mk(378), mk(379)]
r.action_challenge_boss(dict(_boss)); _drive(r, 300, lambda: "Battle" in type(g.current_state).__name__)
_wakes = "Battle" in type(g.current_state).__name__
check(_clown["event"].get("gift_item") == {"COIN_CASE": 1} and _fl["event"].get("gift_item") == {"SPRAYDUCK": 1} and _wet and _asleep and _wakes,
      f"Veilstone's clown gives the Coin Case, Floaroma's florist the Sprayduck that waters Berry soil, Regigigas wakes only for the three Regis ({_wet}, {_asleep}, {_wakes})")
story.story_flags.clear(); story.story_flags.update(_sv); story.inventory.clear(); story.inventory.update(_iv); story.player_team = _team

# ---- 11-24 (Jordan: "from the game file"): Sinnoh's own soundtrack, Platinum's tracks (s_music.py): every track music.json
#      names is there, and the game picks Sinnoh's own for a Sinnoh town and a wild battle
_mj = __import__("json").load(open("assets/music/sinnoh/music.json", encoding="utf-8"))
_names = set()
for _v in list(_mj["areas"].values()) + list(_mj["rooms"].values()) + list(_mj["kinds"].values()):
    _names |= set(_v.values()) if isinstance(_v, dict) else {_v}
_missing = sorted(n for n in _names if not __import__("os").path.isfile(f"assets/music/sinnoh/{n}.ogg"))
t = town("TWINLEAF_TOWN", None); frames(t, 3)
_tt = g.music.region_track("town", "SINNOH") if hasattr(g, "music") else None
_wt = g.music.region_track("wild", "SINNOH") if hasattr(g, "music") else None
check(not _missing and len(_mj["areas"]) >= 80 and _tt and "town01" in _tt and _wt and _wt.endswith("ba_poke.ogg"),
      f"Sinnoh's own music: {len(_names)} Platinum tracks for {len(_mj['areas'])} places and {len(_mj['rooms'])} rooms, Twinleaf's theme in Twinleaf ({_missing[:3]}, {_tt}, {_wt})")

# ---- S7a (11-24, s_s7_fight_area.py): the Fight Area as Platinum's - Barry drags you to the Frontier gate, a Multi Battle
#      with him against Flint and Volkner (Platinum's teams), then Buck
_sv, _team = dict(story.story_flags), list(story.player_team)
for _k in [k for k in story.story_flags if k.startswith(("fight_area_", "stark_", "r227_", "battleground_"))]:
    story.story_flags.pop(_k)
story.story_flags["beat_sinnoh_champion"] = True
story.player_team = [mk(392)]; story.player_team[0].level = 70
t = town("FIGHT_AREA", "SNOWPOINT_CITY"); frames(t, 3)
_fa = {str(o.get("text")): s for s, o in t._people().items()}
_gate = _fa.get("Flint") == (46, 8) and _fa.get("Volkner") == (47, 8)
_tag = _drive(t, 3000, lambda: "Battle" in type(g.current_state).__name__)
_b = g.current_state
_opts = getattr(_b, "battle_options", None) or {}
_pt = [getattr(p_, "id", None) for p_ in (getattr(_b, "partner_team", None) or [])]
_foes = [getattr(p_, "id", None) for p_ in (getattr(_b, "opponent_team", None) or [])]
from src.states.overworld.common import _region_starter_id as _rsi
_bc = {"393": 389, "387": 392, "390": 395}.get(str(_rsi(g)), 389)   # (his last: the starter strong against yours)
_multi = _tag and getattr(_b, "partner_name", None) == "Barry" and str(getattr(_b, "foe2_name", "")) == "Flint" and _pt[-1:] == [_bc] \
    and _foes == [405, 135, 466, 229, 136, 467]
story.story_flags["fight_area_tag_won"] = True
t = town("FIGHT_AREA", "SNOWPOINT_CITY"); frames(t, 3)
_fa2 = {str(o.get("text")) for o in t._people().values()}
_after = "Flint" not in _fa2 and "Volkner" not in _fa2 and "Barry" not in _fa2 and "Buck" in _fa2
check(_gate and _multi and _after,
      f"Fight Area: Barry leads you to Flint and Volkner at the Frontier gate; a Multi Battle beside him (his ace the starter strong against yours) against Platinum's teams; then Buck ({_gate}, {_tag}, {getattr(_b, 'partner_name', None)}, {getattr(_b, 'foe2_name', None)}, {_pt}, {_foes}, {_after})")

# ---- S7a (11-24, s_s7_stark.py): Route 227 and Stark Mountain as Platinum's - Mars then Jupiter on 1F, Platinum's Strength
#      boulders, Charon arrested by Looker in Heatran's room; Heatran only once the Battleground's legend is heard
_sm = _tm["STARK_MOUNTAIN"]["floors"]
_nb = (len(_sm[1].get("boxes") or []), len(_sm[2].get("boxes") or []))
_r227 = {str(p_.get("text")) for p_ in _tm["SINNOH_ROUTE_227"]["people"] if isinstance(p_, dict)}
r = route("STARK_MOUNTAIN", "SINNOH_ROUTE_227")
story.player_team = [mk(392)]; story.player_team[0].level = 70
r.run.jump_floor(1, (16, 28)); frames(r, 3)
_f1 = set(_figs(r))
_mars = _hq_battle(r, "Mars")
_mt = [getattr(p_, "id", None) for p_ in (getattr(g.current_state, "opponent_team", None) or [])]
story.story_flags["stark_mars_beaten"] = True
r = route("STARK_MOUNTAIN", "SINNOH_ROUTE_227")
r.run.jump_floor(1, (16, 28)); frames(r, 3)
_jup = _hq_battle(r, "Jupiter")
_jt = [getattr(p_, "id", None) for p_ in (getattr(g.current_state, "opponent_team", None) or [])]
story.story_flags["stark_jupiter_beaten"] = True
r = route("STARK_MOUNTAIN", "SINNOH_ROUTE_227")
r.run.jump_floor(1, (16, 28)); frames(r, 3)
_gone = not ({"Mars", "Jupiter", "Charon"} & set(_figs(r)))
r.run.jump_floor(3, (5, 14)); frames(r, 3)
_f3 = set(_figs(r))
_arrest = _drive(r, 3000, lambda: story.story_flags.get("stark_charon_arrested"))
_drive(r, 600, lambda: not (r._scene_run and r._scene_run.busy()))
r = route("STARK_MOUNTAIN", "SINNOH_ROUTE_227")
r.run.jump_floor(3, (5, 14)); frames(r, 3)
_f3b = set(_figs(r))
story.story_flags["battleground_buck_talked"] = story.story_flags["battleground_heard_legend"] = True
r = route("STARK_MOUNTAIN", "SINNOH_ROUTE_227")
r.run.jump_floor(3, (5, 14)); frames(r, 3)
_f3c = set(_figs(r))
_lv = _tm and __import__("json").load(open("assets/sinnoh_area_data.json", encoding="utf-8"))["STORY_PROGRESSION"]["STARK_MOUNTAIN"]["area_boss"]["level"]
check(_nb == (7, 3) and {"Crasher Wake", "Barry", "Buck"} <= _r227 and {"Mars", "Charon"} <= _f1 and _mars and _mt == [437, 42, 432]
      and _jup and _jt == [437, 42, 435] and _gone and {"Charon", "Stranger"} <= _f3 and _arrest and "Charon" not in _f3b
      and "Face Heatran" not in _f3b and "Face Heatran" in _f3c and _lv == 50,
      f"Stark Mountain: Platinum's boulders {_nb}; Wake, Barry and Buck on Route 227; Mars then Jupiter on 1F (their teams), gone after; Looker arrests Charon; Heatran (Lv {_lv}) once you've heard the legend ({_r227}, {_f1}, {_mars} {_mt}, {_jup} {_jt}, {_gone}, {_f3}, {_arrest}, {_f3b}, {_f3c})")

# ---- S7a (11-24, s_s7_survival.py, src/world/battleground.py): the Battleground opens after Charon's arrest; four of
#      Platinum's thirteen stand there each day, each battled once a day with Platinum's rematch team
from src.world import battleground as _BG
story.story_flags.pop("stark_charon_arrested", None)
t = town("SURVIVAL_AREA", "SINNOH_ROUTE_226"); frames(t, 3)
_locked = (12, 17) in t.barred
story.story_flags["stark_charon_arrested"] = True
t = town("SURVIVAL_AREA", "SINNOH_ROUTE_226"); frames(t, 3)
_open = (12, 17) not in t.barred
t._go("house_0101", "OUT:12,17"); frames(t, 5)
_today = _BG.picks()
_shown = {}
for _s, _o in t.people.items():
    for _c in (_o.get("any") or [_o]):
        if t._shown(_c):
            _shown[str(_c.get("text"))] = _s
            break
_want = {"roark": "Roark", "gardenia": "Gardenia", "maylene": "Maylene", "wake": "Crasher Wake", "fantina": "Fantina", "byron": "Byron",
         "candice": "Candice", "volkner": "Volkner", "cheryl": "Cheryl", "riley": "Riley", "marley": "Marley", "mira": "Mira", "buck": "Buck"}
_four = [_want[k] for k in _today]
_here = all(n in _shown for n in _four) and len([n for n in _shown if n in _want.values()]) == 4 + (1 if "Buck" not in _four else 0)
_who = _four[0]
_ts = _shown.get(_who)
_fought = False
if _ts:
    t.player = t.anim_from = (_ts[0], _ts[1] + 1); t.anim = 0; t.facing = (0, -1)
    t._talk(tuple(_ts)); _fought = _drive(t, 600, lambda: "Battle" in type(g.current_state).__name__)
_ft = [getattr(p_, "id", None) for p_ in (getattr(g.current_state, "opponent_team", None) or [])]
_owners = []
for _s, _o in t.people.items():
    if _o.get("_partner_of") is not None and t._shown(_o):
        _lead = t.people.get(_o["_partner_of"]) or {}
        _now = next((c for c in (_lead.get("any") or [_lead]) if t._shown(c)), {})
        _owners.append((str(_o.get("text")), str(_now.get("text"))))
_mons = sorted(_owners)
_stray = [m for m, o in _owners if o not in _four + ["Buck"]]
check(_locked and _open and _here and _fought and len(_ft) == 5 and not _stray,
      f"Survival Area: the Battleground locked till Charon's arrest; inside, today's four ({_four}) at Platinum's spots, {_who} battles with Platinum's rematch team ({_locked}, {_open}, {sorted(_shown)}, {_fought}, {_ft}, their Pokemon {_mons})")
_days = {tuple(_BG.picks(__import__("datetime").date(2026, 11, d))) for d in range(1, 29)}
check(len(_days) >= 10 and all(len(p_) == 4 for p_ in _days), f"Battleground: who stands there changes day by day ({len(_days)} different line-ups in 28 days)")
story.story_flags.clear(); story.story_flags.update(_sv); story.player_team = _team

# ---- S7b (11-24, s_s7_turnback.py, src/world/turnback_cave.py): Turnback Cave as Platinum's - each door picks the next room
#      as you go (one in four the next pillar room), the door you came by leads out, the room after the third pillar room is
#      Giratina's; there Giratina if you fought it in the Distortion World and didn't catch it, else the item for the rooms taken
from src.world import turnback_cave as _TC
_sv, _iv = dict(story.story_flags), dict(story.inventory)
for _k in ("turnback", "turnback_giratina_done"):
    story.story_flags.pop(_k, None)
story.story_flags["TURNBACK_CAVE_boss_defeated"] = True
story.inventory["HM_ROCK_SMASH"] = 1
def _tb_step(r, d):
    _drive(r, 200, lambda: not (getattr(r, "dialogue_box", None) and r.dialogue_box.visible) and not getattr(r, "_busy", lambda: False)())
    r.walk_goal = None
    r.step(*d)
    _drive(r, 300, lambda: not (getattr(r, "dialogue_box", None) and r.dialogue_box.visible))
    for _q in range(60):
        g.current_state.update()
    return (r.run.index, tuple(r.run.player))
r = route("TURNBACK_CAVE", "SENDOFF_SPRING")
r.run.jump_floor(0, (21, 8)); frames(r, 3)
_in = _tb_step(r, (0, -1))                                  # (the entrance's door: the first room)
_ww = (r.recipe.get("art") or {}).get("warp_world")
_seq = []
_rolls = iter([0.1, 0.9, 0.1, 0.1])                          # (pillar, rock room, pillar, pillar)
_TC.RNG.random = lambda: next(_rolls, 0.9)
r.run.player = (11, 2); frames(r, 2)
_seq.append(_tb_step(r, (0, -1)))                           # (north: pillar room 1, in at its south door)
_p1 = dict(story.story_flags.get("turnback") or {})
r.run.player = (19, 11); frames(r, 2)
_seq.append(_tb_step(r, (1, 0)))                            # (east: a rock room, in at its west door)
r.run.player = (11, 2); frames(r, 2)
_seq.append(_tb_step(r, (0, -1)))                           # (pillar 2)
r.run.player = (11, 2); frames(r, 2)
_seq.append(_tb_step(r, (0, -1)))                           # (pillar 3)
r.run.player = (11, 2); frames(r, 2)
_seq.append(_tb_step(r, (0, -1)))                           # (after the third pillar: Giratina's room)
_end = dict(story.story_flags.get("turnback") or {})
_gfig = {str((m.payload or {}).get("text")) for m in r.run.floor.movers if m.kind == "figure"}
r.run.player = (11, 19); frames(r, 2)
_back = _tb_step(r, (0, 1))                                 # (out of Giratina's room: back at the entrance)
_near = lambda a, b: abs(a[0] - b[0]) + abs(a[1] - b[1]) <= 1
_ok_path = (_in[0] == 1 and [s[0] for s in _seq] == [2, _seq[1][0], 2, 2, 3] and 4 <= _seq[1][0] <= 9
            and _near(_seq[0][1], (11, 20)) and _near(_seq[1][1], (2, 11)) and _p1.get("pillars") == 1 and _end.get("pillars") == 3
            and "Giratina" in _gfig and _back[0] == 0)
# the door you came in by leads straight back out
_TC.RNG.random = lambda: 0.9
r = route("TURNBACK_CAVE", "SENDOFF_SPRING")
r.run.jump_floor(0, (21, 8)); frames(r, 3)
_tb_step(r, (0, -1))
r.run.player = (11, 2); frames(r, 2)
_a = _tb_step(r, (0, -1))
r.run.player = (11, 19); frames(r, 2)
_b = _tb_step(r, (0, 1))                                    # (back through the south door you came in by)
# caught it: an item on the pedestal instead, by the rooms taken
story.story_flags["turnback_giratina_done"] = True
r = route("TURNBACK_CAVE", "SENDOFF_SPRING")
story.story_flags["turnback"] = {"pillars": 3, "rooms": 2, "came": [11, 20]}
r.run.jump_floor(2, (11, 3)); frames(r, 2)
r.run.player = (11, 2); frames(r, 2)
_tb_step(r, (0, -1))
_ifig = {str((m.payload or {}).get("text")) for m in r.run.floor.movers if m.kind == "figure"}
_im = next((m for m in r.run.floor.movers if m.kind == "figure" and str((m.payload or {}).get("text")) == "Item"), None)
_rc = story.inventory.get("REAPER_CLOTH", 0)
if _im is not None:
    r.run.player = (_im.x, _im.y + 1); r._use_figure(_im); _drive(r, 300, lambda: not r.dialogue_box.visible)
    r._use_figure(_im); _drive(r, 300, lambda: not r.dialogue_box.visible)
_got = story.inventory.get("REAPER_CLOTH", 0) - _rc
check(_ww == "turnback_cave" and _ok_path and 4 <= _a[0] <= 9 and _b[0] == 0 and r.run.index == 3 and "Item" in _ifig and "Giratina" not in _ifig and _got == 1
      and _TC.item_for(4) == "RARE_BONE" and _TC.item_for(3) == "REAPER_CLOTH" and _TC.item_for(20) == "STARDUST",
      f"Turnback Cave: doors pick the next room as Platinum's - three pillar rooms then Giratina's, the way you came leads out; Giratina there, else the item ({_in}, {_seq}, {_p1}, {_end.get('rooms')}, {_gfig}, {_back}, {_a}, {_b}, {r.run.index}, {_ifig}, {_got})")
import random as _rnd
_TC.RNG = _rnd.Random()
story.story_flags.clear(); story.story_flags.update(_sv); story.inventory.clear(); story.inventory.update(_iv)

# ---- S7b (11-24, s_s7_resort.py, src/world/ribbon_syndicate.py; Jordan: "Build it as Platinum"): the Ribbon Syndicate -
#      members only (ten kinds of Ribbon on your party), the lift to the spa (friendlier, once a day), the shop's Ribbons
from src.world import ribbon_syndicate as _RS
_sv, _team, _money = dict(story.story_flags), list(story.player_team), story.money
story.story_flags.pop("syndicate_spa_day", None)
_m = mk(25); _m.level = 50; _m.ribbons = []; _m.friendship = 100
story.player_team = [_m]
t = town("RESORT_AREA", "SINNOH_ROUTE_229"); frames(t, 3)
t._go("house_0101", "OUT:24,5"); frames(t, 5)
_shut = (14, 13) in t.barred
_m.ribbons = [f"{c}_{r}" for c in ("COOL", "BEAUTY", "CUTE", "SMART", "TOUGH") for r in ("NORMAL", "GREAT")]
t = town("RESORT_AREA", "SINNOH_ROUTE_229"); frames(t, 3)
t._go("house_0101", "OUT:24,5"); frames(t, 5)
_in = (14, 13) not in t.barred and _RS.condition(story, "member")
_lift = "syndicate_lift" in t.town_map["rooms"] and t.town_map["rooms"]["syndicate_lift"].get("dynamic_exit", {}).get("rooms") == ["house_0101", "house_0102"]
t._go("house_0102", "ROOM:syndicate_lift"); frames(t, 5)
_spa = next((s for s, o in t.people.items() if str(o.get("text")) == "Spa attendant"), None)
_f0 = _m.friendship
if _spa:
    t.player = t.anim_from = (_spa[0], _spa[1] + 1); t.anim = 0; t.facing = (0, -1)
    t._talk(tuple(_spa)); _drive(t, 300, lambda: not getattr(t, "npc_active", False))
_f1 = story.player_team[0].friendship
if _spa:
    t._talk(tuple(_spa)); _drive(t, 300, lambda: not getattr(t, "npc_active", False))
_f2 = story.player_team[0].friendship
story.money = 20000
_lines = []
_RS.event(t, {"buy": "GORGEOUS"}, [], lambda l: _lines.extend(l))
_RS.event(t, {"buy": "ROYAL"}, [], lambda l: _lines.extend(l))
_bought = "GORGEOUS" in story.player_team[0].ribbons and "ROYAL" not in story.player_team[0].ribbons and story.money == 10000
from src.pokemon.contest import ribbon_label as _rl
check(_shut and _in and _lift and _spa and _f1 > _f0 and _f2 == _f1 and _bought and _rl("GORGEOUS_ROYAL") == "Gorgeous Royal Ribbon",
      f"Ribbon Syndicate: members only (ten kinds of Ribbon), the lift to the spa, its treatment once a day, the shop's Ribbons ({_shut}, {_in}, {_lift}, {_spa}, {_f0}->{_f1}->{_f2}, {_bought}, {_lines[-1:]})")
story.player_team = _team; story.money = _money

# ---- S7b (11-24, s_s7_rotom.py, src/world/rotom_room.py): Rotom's room behind 1F of the Galactic Eterna Building, open once
#      you're Champion; its five appliances change a Rotom's form, and the same one brings it back
_r = mk(479); _r.level = 40
story.player_team = [_r]
story.story_flags.pop("beat_sinnoh_champion", None)
r = route("ETERNA_GALACTIC_BUILDING", "ETERNA_CITY")
story.player_team = [_r]
r.run.jump_floor(0, (2, 3)); frames(r, 3)
_lock = str(r.run.floor.decor.get((2, 2), "")).startswith("barrier:")
story.story_flags["beat_sinnoh_champion"] = True
r = route("ETERNA_GALACTIC_BUILDING", "ETERNA_CITY")
story.player_team = [_r]
r.run.jump_floor(0, (2, 3)); frames(r, 3)
_open = not str(r.run.floor.decor.get((2, 2), "")).startswith("barrier:")
r.run.jump_floor(4, (7, 10)); frames(r, 3)
_ap = {str((m.payload or {}).get("text")): m for m in r.run.floor.movers if m.kind == "figure"}
_wm = _ap.get("Washing machine")
if _wm is not None:
    r.run.player = (_wm.x, _wm.y + 1); r._use_figure(_wm); _drive(r, 300, lambda: not r.dialogue_box.visible)
_wash = story._pokemon_record(story.player_team[0]).get("form")
_mv = list(getattr(story.player_team[0], "moves", []) or [])
if _wm is not None:
    _wm2 = next((m for m in r.run.floor.movers if m.kind == "figure" and str((m.payload or {}).get("text")) == "Washing machine"), _wm)
    r._use_figure(_wm2); _drive(r, 300, lambda: not r.dialogue_box.visible)
_back = story._pokemon_record(story.player_team[0]).get("form")
check(_lock and _open and len(_ap) == 5 and _wash == "wash" and "HYDRO-PUMP" in _mv and _back == "normal",
      f"Rotom's room: shut till you're Champion, then five appliances; the washer makes Rotom Wash Rotom (Hydro Pump), again brings it back ({_lock}, {_open}, {sorted(_ap)}, {_wash}, {_mv}, {_back})")
story.player_team = _team

story.story_flags.clear(); story.story_flags.update(_sv)

# ---- S8 (11-24, s_s8_canalave_dream.py): the sailor's son in Canalave - his nightmare after the title, the Lunar Wing wakes him
_sv, _iv, _team = dict(story.story_flags), dict(story.inventory), list(story.player_team)
for _k in ("canalave_dream_seen", "canalave_dream_woke"):
    story.story_flags.pop(_k, None)
story.story_flags["beat_sinnoh_champion"] = True
story.inventory.pop("LUNAR_WING", None)
t = town("CANALAVE_CITY", "SINNOH_ROUTE_218"); frames(t, 3)
t._go("house_0501", "OUT:7,44"); frames(t, 3)
def _boy(t):
    return next((s for s, o in t.people.items() if any(str(c.get("text")) == "Little boy" for c in (o.get("any") or [o]))), None)
_b = _boy(t)
if _b:
    t.player = t.anim_from = (_b[0], _b[1] + 1); t.anim = 0; t.facing = (0, -1)
    t._talk(tuple(_b)); _drive(t, 300, lambda: not getattr(t, "npc_active", False))
_seen = bool(story.story_flags.get("canalave_dream_seen"))
story.inventory["LUNAR_WING"] = 1
t = town("CANALAVE_CITY", "SINNOH_ROUTE_218"); frames(t, 3)
t._go("house_0501", "OUT:7,44"); frames(t, 3)
_b = _boy(t)
if _b:
    t.player = t.anim_from = (_b[0], _b[1] + 1); t.anim = 0; t.facing = (0, -1)
    t._talk(tuple(_b)); _drive(t, 300, lambda: not getattr(t, "npc_active", False))
check(_b is not None and _seen and story.story_flags.get("canalave_dream_woke"),
      f"Canalave: the sailor's son is caught in a nightmare after the title; seeing him opens the Fullmoon boat, the Lunar Wing wakes him ({_b}, {_seen}, {story.story_flags.get('canalave_dream_woke')})")
story.story_flags.clear(); story.story_flags.update(_sv); story.inventory.clear(); story.inventory.update(_iv)

# ---- S8 (11-24, s_s8_amity.py): Amity Square walked - Platinum's pads take you hut to hut, its four item balls, the tidy man
_pk = mk(25); _pk.level = 30
story.player_team = [_pk]
t = town("HEARTHOME_CITY", "SINNOH_ROUTE_208"); frames(t, 3)
t._go("amity", "OUT:10,11"); frames(t, 3)
t.player = t.anim_from = (3, 3); t.anim = 0; t.walk_goal = None
t.step(0, -1)
_drive(t, 200, lambda: getattr(g.current_state, "room", None) == "amity_square")
t = g.current_state
_in = getattr(t, "room", None) == "amity_square"
_items = sorted(str(o.get("text")) for o in t.people.values() if (o.get("event") or {}).get("gift_item"))
t.player = t.anim_from = (17, 16); t.anim = 0; t.walk_goal = None
t.step(0, 1)   # (onto the pad at (17,17): to the hut at (35,15))
_drive(t, 600, lambda: tuple(getattr(g.current_state, "player", (0, 0))) == (35, 16))
_pad = tuple(getattr(g.current_state, "player", (0, 0)))
check(_in and len(_items) == 4 and _pad == (35, 16),
      f"Amity Square: in with a Pikachu leading, Platinum's four item balls, a pad takes you from one hut to another ({_in}, {_items}, {_pad})")
story.player_team = _team

# ---- S8 (11-25, s_s8_gifts.py, src/world/sinnoh_gifts.py): Platinum's givers - Jasmine's Waterfall after the Beacon Badge (not
#      the badge itself), Julia's Ribbon of the day, the Footprint Ribbon, the Route 221 number man, Rowan's TM27 Return
from src.world import sinnoh_gifts as _SGf, hms as _hm
_sv, _iv, _team, _bv = dict(story.story_flags), dict(story.inventory), list(story.player_team), list(story.badges.get("SINNOH", []))
def _talk_to(t, name):
    _s = next((s for s, o in t.people.items() if any(str(c.get("text")) == name and t._shown(c) for c in (o.get("any") or [o]))), None)
    if _s:
        t.player = t.anim_from = (_s[0], _s[1] + 1); t.anim = 0; t.facing = (0, -1)
        t._talk(tuple(_s)); _drive(t, 400, lambda: not getattr(t, "npc_active", False))
    return _s
_nobadge = "HM_WATERFALL" not in (_hm.HM_BY_BADGE.get("SINNOH") or {}).values()
story.inventory.pop("HM_WATERFALL", None)
story.badges["SINNOH"] = ["COAL", "FOREST", "COBBLE", "FEN", "RELIC", "MINE", "ICICLE"]
t = town("SUNYSHORE_CITY", "SINNOH_ROUTE_222"); frames(t, 3)
_talk_to(t, "Jasmine")
_before = story.inventory.get("HM_WATERFALL", 0)
story.badges["SINNOH"] = ["COAL", "FOREST", "COBBLE", "FEN", "RELIC", "MINE", "ICICLE", "BEACON"]
t = town("SUNYSHORE_CITY", "SINNOH_ROUTE_222"); frames(t, 3)
_js = _talk_to(t, "Jasmine")
_after = story.inventory.get("HM_WATERFALL", 0)
_m = mk(25); _m.level = 30; _m.ribbons = []; _m.friendship = 255
story.player_team = [_m]
story.story_flags.pop("sinnoh_julia_day", None)
t = town("SUNYSHORE_CITY", "SINNOH_ROUTE_222"); frames(t, 3)
t._go("house_0201", "OUT:0,0"); frames(t, 3)
_talk_to(t, "Julia")
_rib = list(_m.ribbons)
_lines = []
class _St:
    game = g
_SGf.event(_St(), {"footstep": True}, [], lambda l: _lines.extend(l))
_foot = "FOOTPRINT" in _m.ribbons
_m.level = _SGf.todays_level()
story.story_flags.pop("sinnoh_route221_level_day", None)
_belts_before = sum(story.inventory.get(b, 0) for b in _SGf.BELTS)
_SGf.event(_St(), {"level_man": True}, [], lambda l: _lines.extend(l))
_belt = sum(story.inventory.get(b, 0) for b in _SGf.BELTS) - _belts_before
story.story_flags["received_pokedex_sinnoh"] = True
story.story_flags.pop("got_tm274_sandgem", None)
t = town("SANDGEM_TOWN", "SINNOH_ROUTE_201"); frames(t, 3)
t._go("lab", "OUT:0,0"); frames(t, 3)
_dr = next((x, y) for y, row in enumerate(t.town_map["rooms"]["lab"]["art"]) for x, c in enumerate(row) if c == "v")
t.player = t.anim_from = (_dr[0], _dr[1] - 3); t.anim = 0; t.walk_goal = None
t.step(0, 1)   # (heading for the door: Rowan comes over)
_drive(t, 1500, lambda: story.inventory.get("TM274", 0) > 0 and not t.scenes.busy())
_tm = story.inventory.get("TM274", 0)
check(_nobadge and _before == 0 and _js and _after == 1 and len(_rib) == 1 and _foot and _belt == 1 and _tm == 1,
      f"Platinum's givers: Jasmine's Waterfall only after the Beacon Badge, Julia's Ribbon of the day, the Footprint Ribbon, the Route 221 number man's belt, Rowan's TM27 ({_nobadge}, {_before}->{_after}, {_rib}, {_foot}, {_belt}, {_tm})")
story.story_flags.clear(); story.story_flags.update(_sv); story.inventory.clear(); story.inventory.update(_iv)
story.player_team = _team; story.badges["SINNOH"] = _bv

g.walk_towns = False
print(f"##### {fails} failures")
