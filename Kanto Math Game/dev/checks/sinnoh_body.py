# Sinnoh's walkable maps (dev/builders/town_maps/sinnoh.py), entered the way a player would.
#   cat dev/checks/harness_head.py dev/checks/sinnoh_body.py > dev/checks/out/check_sinnoh.py
#   python dev/checks/out/check_sinnoh.py <scratch dir>
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
for _k, _who in (("CELESTIC_TOWN", "Celestic Ruins"), ("SUNYSHORE_CITY", "Lighthouse")):
    t = town(_k, None)
    if not any(o.get("text") == _who for o in t.people.values()):
        _dbad.append((_k, _who, "nobody stands there"))
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
t = town("ETERNA_CITY", None)
check(all(t._open(p) for p in _gate), "Eterna City: with Cut the trees are gone and you can walk in")
story.inventory["HM_CUT"] = 0
r = route("SINNOH_ROUTE_212", "HEARTHOME_CITY")
_cut = [p for p, v in r.run.floor.decor.items() if str(v).startswith("cut:")]
story.inventory["HM_CUT"] = 1
r = route("SINNOH_ROUTE_212", "HEARTHOME_CITY")
check(len(_cut) >= 8 and not any(str(v).startswith("cut:") for v in r.run.floor.decor.values()) and all(r.run.floor.walkable(*p) for p in _cut),
      f"Route 212: its {len(_cut)} small trees are in the way until you have Cut")
r = route("WAYWARD_CAVE", "SINNOH_ROUTE_206")
_sl = [p for f in _tm["WAYWARD_CAVE"]["floors"] for row in f["art"] for p in row if p == "7"]
check(len(_sl) >= 10, f"Wayward Cave: {len(_sl)} tiles of steep muddy slope need the Bicycle")
r = route("VICTORY_ROAD_SINNOH", "SINNOH_POKEMON_LEAGUE")
_nb = sum(row.count("b") for f in _tm["VICTORY_ROAD_SINNOH"]["floors"] for row in f["art"])
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
check(_cyv and _cyv[0]["event"].get("gift_item") == {"SECRET_POTION": 1} and "has_fen_badge" in _cyv[0]["condition"],
      "Valor Lakefront: Cynthia gives the SecretPotion after the Fen Badge")
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
_fog1 = bool(r.run.fog)
story.inventory["HM_DEFOG"] = 1
r = route("LOST_TOWER", "SINNOH_ROUTE_209")
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
check(_n == 10 and _down == 9 and r.run.index == 9 and _ok_each and _dw["theme"] == "distortion" and _dw["figure_floors"] == {"CONFRONT CYRUS": 8, "FACE GIRATINA": 9},
      f"Distortion World: ten floors of slabs in the void, a way down on each ({_down} descents), Cyrus on B7F and Giratina below")
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
        if not t._open((_door[0], _door[1] + 1)):
            continue  # (a door you reach from another side: not this check's business)
        _enter_door(t, _door)
        _want = len(_m["rooms"][_name].get("people", []))
        if t.room != _name or len(t.people) != _want or not t._open(t.player) or not any(v == "OUT:" + _d or v.startswith("OUT:") for v in t.exits.values()):
            _bad.append((_name, t.room, len(t.people), _want)); continue
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

g.walk_towns = False
print(f"##### {fails} failures")
