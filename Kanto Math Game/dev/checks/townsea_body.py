# A town's sea needs Surf (11-18, roadmap bug: towns without a "surf" key let you walk on their sea). Every walked
# town's own map now treats its sea as the routes do; a room's pool (a Gym's, where swimmers stand) only if marked
# "surf"; "wade" keeps listed sea tiles walkable (Tangelo: the step to Lapras, who brings Surf).
#   cat dev/checks/harness_head.py dev/checks/townsea_body.py > dev/checks/out/check_townsea.py
import glob, json
from src.states.overworld import CityState as _CS
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.dungeon import art as _art
fails = 0
g.walk_towns = True


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


def town(area, region):
    story.enter_region(region)
    g.walk_town_pos = None; g.walk_town_room = None
    story.current_area_key, story.last_area_key = area, None
    st = _CS(g); g.change_state(st)
    for _ in range(3):
        g.current_state.update()
    st = g.current_state
    for _ in range(600):   # (tap through whatever the town says or plays first, as a player would)
        if not (isinstance(st, _WTS) and st._busy()):
            break
        st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        st.update(); st.draw()
    return g.current_state


_types = {}
for _f in glob.glob(os.path.join("assets", "*_area_data.json")):
    for _k, _v in (json.load(open(_f, encoding="utf-8")).get("STORY_PROGRESSION") or {}).items():
        if isinstance(_v, dict):
            _types[_k] = _v.get("area_type")
story.story_flags["hoenn_version"] = "OMEGA_RUBY"
_tm = json.load(open(os.path.join("assets", "town_maps.json"), encoding="utf-8"))

print("1) the map data: every town's own sea is Surf water")
_bad = []
for _k, _m in _tm.items():
    if not isinstance(_m, dict) or "art" not in _m or _types.get(_k) != "town" or _m.get("surf") is False:
        continue
    _wade = {tuple(t) for t in _m.get("wade", [])}
    _sea = [(x, y) for y, r in enumerate(_m["art"]) for x, c in enumerate(r) if c in _art.SEA_CHARS and (x, y) not in _wade]
    if _sea and _m.get("surf") is not None and not _m.get("surf"):
        _bad.append(_k)
check(not _bad, f"no town turns its sea off by mistake ({_bad})")

print("2) in the game: Mossdeep (Hoenn), Sunyshore (Sinnoh), Blackthorn (Johto), Tangelo (Orange)")
for _area, _region in (("MOSSDEEP_CITY", "HOENN"), ("SUNYSHORE_CITY", "SINNOH"), ("BLACKTHORN_CITY", "JOHTO"), ("TANGELO_ISLAND", "ORANGE")):
    st = town(_area, _region)
    if not isinstance(st, _WTS):
        check(False, f"{_area}: walked ({type(st).__name__})")
        continue
    _m = _tm[_area]
    _wade = {tuple(t) for t in _m.get("wade", [])}
    _sea = [(x, y) for y, r in enumerate(_m["art"]) for x, c in enumerate(r) if c in _art.SEA_CHARS and (x, y) not in _wade]
    check(_sea and all(st.rows[y][x] == "o" for x, y in _sea), f"{_area}: its {len(_sea)} sea tiles are Surf water")
    # a shore tile beside the sea: step in without Surf (blocked), then with it
    _shore = next(((x, y), (dx, dy)) for x, y in _sea for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))
                  if 2 <= x - dx < st.w - 2 and 2 <= y - dy < st.h - 2 and 2 <= x < st.w - 2 and 2 <= y < st.h - 2
                  and st.rows[y - dy][x - dx] == "." and (x, y) not in getattr(st, "bridge", {}) and (x - dx, y - dy) not in getattr(st, "bridge", {})
                  and (x - dx, y - dy) not in st._people())
    (_sx, _sy), (_dx, _dy) = _shore
    story.inventory.pop("HM_SURF", None)
    st.player = st.anim_from = (_sx - _dx, _sy - _dy); st.anim = 0
    st.step(_dx, _dy)
    for _ in range(20):
        st.update()
    check(tuple(st.player) == (_sx - _dx, _sy - _dy), f"{_area}: without Surf you can't step into the sea at {(_sx, _sy)} ({st.player})")
    story.inventory["HM_SURF"] = 1
    from src.world import hms as _hms
    _need = _hms.USE_BADGE.get(_region, {}).get("HM_SURF")
    story.badges[_region] = [_need] if _need else []
    check(st._has("HM_SURF") and not st._busy(), f"{_area}: Surf usable here, nothing on screen ({_need})")
    if st._has("HM_SURF"):
        st.player = st.anim_from = (_sx - _dx, _sy - _dy); st.anim = 0
        st.step(_dx, _dy)
        for _ in range(20):
            st.update()
        check(tuple(st.player) == (_sx, _sy), f"{_area}: with Surf you can ({st.player})" + ("" if tuple(st.player) == (_sx, _sy) else f" {getattr(st, 'flash_text', '')}"))
    story.inventory.pop("HM_SURF", None)
    story.badges[_region] = []

print("3) Tangelo: Lapras (who brings Surf) is reached without it")
st = town("TANGELO_ISLAND", "ORANGE")
_lap = (31, 15)   # (o_batch2's add_people: Lapras in the pond, shown once the story calls for it)
check(_tm["TANGELO_ISLAND"]["art"][15][31] == "N", "Tangelo: Lapras stands at (31, 15) in its pond")
check(st.rows[_lap[1] - 1][_lap[0]] == "." and st.rows[_lap[1] - 2][_lap[0]] == ".",
      f"Tangelo: the tile north of Lapras {_lap} is waded, from the shore")
check(not st._has("HM_SURF") and st._open((_lap[0], _lap[1] - 1)), "Tangelo: ...and it's open without Surf")

print("4) a Gym's pool needs Surf too (FireRed's and Orange 5.7's own water, behaviour 0x15), and Misty is reached on foot")
story.story_flags["visited_BILLS_HOUSE"] = True
story.inventory.pop("HM_SURF", None)
st = town("CERULEAN_CITY", "KANTO")
st._go("gym", "")
for _ in range(5):
    st.update()
st = g.current_state
_pool = [(x, y) for y, r in enumerate(st.rows) for x, c in enumerate(r) if c == "o"]
check(getattr(st, "room", None) == "gym" and len(_pool) > 100, f"Cerulean Gym: its pool ({len(_pool)} tiles) is Surf water")
_seen, _todo = {tuple(st.player)}, [tuple(st.player)]
while _todo:
    _x, _y = _todo.pop()
    for _dx, _dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        _t = (_x + _dx, _y + _dy)
        if _t not in _seen and 0 <= _t[0] < st.w and 0 <= _t[1] < st.h and st.rows[_t[1]][_t[0]] == ".":
            _seen.add(_t); _todo.append(_t)
check(any((8 + dx, 6 + dy) in _seen for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))),
      f"Cerulean Gym: Misty (8, 6) is reached on foot, round the pool (FireRed's walkway) from {st.player}")

print("5) wild Pokemon on a town's water: its own Surf table, else the nearest water's, else Tentacool")
fails_before = fails
_names = {}
for _area, _region in (("PALLET_TOWN", "KANTO"), ("CIANWOOD_CITY", "JOHTO"), ("PETALBURG_CITY", "HOENN"), ("LILYCOVE_CITY", "HOENN"),
                       ("MOSSDEEP_CITY", "HOENN"), ("SUNYSHORE_CITY", "SINNOH"), ("FIGHT_AREA", "SINNOH"), ("GOLDENROD_CITY", "JOHTO"),
                       ("TANGELO_ISLAND", "ORANGE")):
    st = town(_area, _region)
    _pool, _from = st._surf_table()
    _mon = st._surf_mon()
    check(bool(_pool) and _mon is not None,
          f"{_area}: surfing Pokemon from {_from}'s table ({sorted(_pool, key=lambda k: -_pool[k])[:4]}), e.g. {_mon.display_name if _mon else None} Lv {_mon.level if _mon else '-'}")
# a battle starts on the water, then you're back in the town where you were
st = town("MOSSDEEP_CITY", "HOENN")
_sea = [(x, y) for y in range(2, st.h - 2) for x in range(2, st.w - 2) if st.rows[y][x] == "o" and st.rows[y][x + 1] == "o"]
story.inventory["HM_SURF"] = 1
st.player = st.anim_from = _sea[0]; st.anim = 0
_keep = st.SURF_RATE
type(st).SURF_RATE = 1.0
st.step(1, 0)
type(st).SURF_RATE = _keep
from src.states.battle import WildBattleState as _WBS
_b = g.current_state
check(isinstance(_b, _WBS) and getattr(_b, "back_to_town", False), f"Mossdeep: surfing on, a wild battle starts ({type(_b).__name__})")
if isinstance(_b, _WBS):
    _b.player_won = True
    try:
        _b.exit_battle()
    except Exception as _e:
        print("   (exit_battle:", _e, ")")
    for _ in range(60):
        g.current_state.update()
    check(isinstance(g.current_state, _WTS) and tuple(g.current_state.player) == (_sea[0][0] + 1, _sea[0][1]),
          f"...and after it you're back on Mossdeep's water where you were ({type(g.current_state).__name__} {getattr(g.current_state, 'player', None)})")
st = g.current_state if isinstance(g.current_state, _WTS) else town("MOSSDEEP_CITY", "HOENN")
story.repel_routes = 3
type(st).SURF_RATE = 1.0
st.player = st.anim_from = _sea[0]; st.anim = 0
st.step(1, 0)
type(st).SURF_RATE = _keep
check(isinstance(g.current_state, _WTS), "with a Repel going, no wild Pokemon on the water")
story.repel_routes = 0
story.inventory.pop("HM_SURF", None)

print("6) Sinnoh's water: its routes' and towns' own Surf tables (BDSP, from Bulbapedia); towns surfed in the games have Surf water")
_sd = json.load(open(os.path.join("assets", "sinnoh_area_data.json"), encoding="utf-8"))
_ssp = _sd["STORY_PROGRESSION"]
_have = [k for k in ("SINNOH_ROUTE_213", "SINNOH_ROUTE_222", "LAKE_VERITY", "GREAT_MARSH", "TWINLEAF_TOWN", "CANALAVE_CITY", "SUNYSHORE_CITY")
         if _ssp[k].get("surf_pool_percentages") in _sd]
check(len(_have) == 7, f"Sinnoh routes, lakes and towns have Surf tables ({_have})")
check(set(_sd["SINNOH_ROUTE_222_SURF_PERCENTAGES"]) <= {"72", "73", "278", "279"} and "72" in _sd["SINNOH_ROUTE_222_SURF_PERCENTAGES"],
      f"Route 222's water: Tentacool, Wingull and their evolutions ({_sd['SINNOH_ROUTE_222_SURF_PERCENTAGES']})")
check(all(not any("~" in r for r in _tm[k]["art"]) and any("o" in r for r in _tm[k]["art"])
          for k in ("CANALAVE_CITY", "CELESTIC_TOWN", "ETERNA_CITY", "PASTORIA_CITY", "TWINLEAF_TOWN")),
      "Canalave, Celestic, Eterna, Pastoria and Twinleaf's water is Surf water (it was a pond you couldn't enter)")
print("FAILURES:", fails)
