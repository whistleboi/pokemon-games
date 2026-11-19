# The Fly rule for every region (Jordan 11-17, set during Orange; all regions 11-18): Fly reaches every place with a
# Pokemon Center (a route's too: Route 10) and the region's home town, and lands you outside that Center's door.
#   cat dev/checks/harness_head.py dev/checks/flyrule_body.py > dev/checks/out/check_flyrule.py
from src.states.systems.fly_map import FlyState, fly_land, fly_ok, has_center
from src.states.overworld.walk_town import WalkTownState as _WTS
fails = 0
g.walk_towns = True
g.dungeon_routes = True


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


prog = g.loader.area_data["STORY_PROGRESSION"]
for k in prog:
    story.story_flags[f"visited_{k}"] = True

print("1) the Fly list, region by region")
f = FlyState(g, g.current_state)
keys = {k for k, _ in f.cities}
for region in ("KANTO", "JOHTO", "HOENN", "SINNOH", "ORANGE", "ORRE"):
    home = story.get_region_start(region).get("start_area")
    mine = {k for k in keys if story.area_region(k) == region}
    bad = sorted(k for k in mine if not (has_center(g, k) or k == home or prog[k].get("fly_island")))
    missing = sorted(k for k, a in prog.items() if isinstance(a, dict) and story.area_region(k) == region and has_center(g, k) and k not in keys)
    check(not bad and not missing and (home in keys or home not in prog),
          f"{region}: {len(mine)} places, each with a Center or the home town {home} (no Center: {bad}; Centers left out: {missing[:6]})")
check({"KANTO_ROUTE_10", "PALLET_TOWN"} <= keys and "BILLS_HOUSE" not in keys and "POKEMON_LEAGUE_GATE" not in keys,
      "Kanto: Route 10's Center and Pallet Town are in; Bill's House and the League gate are not")
check("JOHTO_ROUTE_32" in keys and "OLIVINE_LIGHTHOUSE" not in keys and "NEW_BARK_TOWN" in keys,
      "Johto: Route 32's Center and New Bark are in; the Lighthouse is not")

print("2) you land outside the Center's door")
story.enter_region("KANTO")
fly_land(g, "VIRIDIAN_CITY")
from src.states.overworld import AreaTransitionState as _ATS
for _ in range(2000):
    if not isinstance(g.current_state, _ATS):
        break
    g.current_state.update()
for _ in range(5):
    g.current_state.update()
st = g.current_state
door = next((t for t, k in getattr(st, "doors", {}).items() if k == "center"), None)
check(isinstance(st, _WTS) and door is not None and abs(st.player[0] - door[0]) + abs(st.player[1] - door[1]) <= 2,
      f"Viridian City: by the Center's door ({getattr(st, 'player', None)} vs door {door})")
fly_land(g, "KANTO_ROUTE_10")
from src.states.overworld import AreaTransitionState as _ATS
for _ in range(2000):
    if not isinstance(g.current_state, _ATS):
        break
    g.current_state.update()
for _ in range(5):
    g.current_state.update()
st = g.current_state
from src.states.overworld import walk_town as _wt
_m = _wt.custom(g).get("KANTO_ROUTE_10") or {}
_d = next((tuple(int(v) for v in d.split(",")) for d, r in (_m.get("inside") or {}).items() if r == "center"), None)
_p = getattr(getattr(st, "run", None), "player", None)
check(_d is not None and _p is not None and abs(_p[0] - _d[0]) + abs(_p[1] - _d[1]) <= 2,
      f"Route 10: by its Center's door ({type(st).__name__} {_p} vs door {_d})")
print("FAILURES:", fails)
