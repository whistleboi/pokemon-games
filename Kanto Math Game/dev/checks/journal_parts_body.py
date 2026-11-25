# The Journal marker in places whose parts don't join (Journal branch J7, 11-24; Jordan: "build part-level reach").
#   bash dev/checks/run.sh journal_parts
# assets/journal_parts.json (dev/builders/journal_parts_body.py: the walker's own reach, per HM that changes a place) tells
# the marker which ways out of a place join which; the planner then never sends you in by a part that can't lead on.
import itertools
from src.world import guide
from src.states.overworld import CityState
fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


story = g.story_manager
g.walk_towns = True
g.dungeon_routes = True
guide.WALKED_REGIONS |= {"SINNOH"}
inv = story.inventory
HM = ("HM_SURF", "HM_STRENGTH", "HM_ROCK_CLIMB", "HM_DIVE")


def kit(*have):
    for h in HM:
        inv.pop(h, None)
    for h in have:
        inv[h] = 1


print("The table")
groups = guide.place_groups
kit("HM_SURF", "HM_STRENGTH")
check(groups(g, "MT_CORONET_BASE") is not None, "Mt. Coronet is in parts")
nb = lambda area, came: set(guide.neighbours(g, area, True, came))
print("Mt. Coronet: Strength joins the Route 211 side to Route 216; the south rooms need Rock Climb")
check("SINNOH_ROUTE_216" not in nb("MT_CORONET_BASE", "SINNOH_ROUTE_207"), "in from Route 207 (south rooms), no way on to Route 216")
check("SINNOH_ROUTE_216" in nb("MT_CORONET_BASE", "SINNOH_ROUTE_211"), "in from Route 211 with Strength, Route 216 is the way on")
path = guide.path_to(g, "SINNOH_ROUTE_207", "SNOWPOINT_CITY")
check(path and "SINNOH_ROUTE_211" in path, f"from Route 207 to Snowpoint, the way goes round by Route 211 ({path})")
kit("HM_SURF", "HM_STRENGTH", "HM_ROCK_CLIMB")
check("SINNOH_ROUTE_216" in nb("MT_CORONET_BASE", "SINNOH_ROUTE_207"), "with Rock Climb too, the south rooms lead on")
kit("HM_SURF")
check("SINNOH_ROUTE_216" not in nb("MT_CORONET_BASE", "SINNOH_ROUTE_211"), "without Strength, the Route 211 side doesn't either")

print("Splits the same with every HM and none (story gates a new game sees shut) are left out: the planner keeps them whole")
check(groups(g, "KANTO_ROUTE_23") is None, "Kanto's Route 23 (its badge gates) isn't treated as a place in parts")

print("Route 213: Pastoria's sea edge lands in a part that can't reach Valor Lakefront; the gatehouse way can")
kit("HM_SURF", "HM_STRENGTH")
r213 = groups(g, "SINNOH_ROUTE_213") or []
bad = [grp for grp in r213 if {e[3] for e in grp} == {"PASTORIA_CITY"}]
good = [grp for grp in r213 if {"PASTORIA_CITY", "VALOR_LAKEFRONT"} <= {e[3] for e in grp}]
check(bad and good, "Route 213 has a Pastoria-only part and a part joining Pastoria to Valor Lakefront")
story.current_area_key = "PASTORIA_CITY"
exec(open("dev/checks/walk_lib.py", encoding="utf-8").read())
city = walk_town("PASTORIA_CITY", None, play=False)
tiles = {(None, t) for t, tg in city.exits.items() if tg == "SINNOH_ROUTE_213"}
fake = {"id": "_t", "target": "VALOR_LAKEFRONT"}
_mt = guide.mission_target
guide.mission_target = lambda game, m: "VALOR_LAKEFRONT" if m is fake else _mt(game, m)
kept = city._ways_on("SINNOH_ROUTE_213", tiles, fake)
guide.mission_target = _mt
check(0 < len(kept) < len(tiles), f"out of Pastoria toward Valor Lakefront, the marker keeps {len(kept)} of {len(tiles)} ways out to Route 213")

print("A way-point step with no floor, on a route with rooms, means the route's ground (Unova's Route 4, 11-24)")
guide.WALKED_REGIONS |= {"UNOVA"}
from src.states.overworld.dungeon import DungeonState
story.current_area_key = "UNOVA_ROUTE_4"
_m = dict(g.loader.area_data and next(m for m in g.loader.area_data["JOURNAL_MISSIONS"] if m["id"] == "b2_m19"))
for _v, _at in (("BLACK_2", (45, 104)), ("WHITE_2", (21, 98))):
    story.story_flags["unova_version"] = _v
    _ds = DungeonState(g)
    _hit = _ds._guide_step(_m)
    check(_hit is not None, f"{_v}: the marker leads to Colress's step on Route 4 ({_hit}, his spot {_at})")


print("Rides and lifts in a town's rooms (Unova's card, 11-24)")
story.story_flags.pop("unova_version", None)
co = walk_town("NIMBASA_CITY", None, room="coaster", play=False)
_rides, _sw = co._guide_rides("coaster")
for _f in _sw.values():
    story.story_flags.pop(_f, None)
co.player = (14, 44)
check(co._guide_walk({("coaster", (28, 5))}) is None, "Nimbasa's coaster: with the switches as they start, no walk reaches its back room")
_seen = []
for _i in range(30):   # (follow the marker from the entrance: ride where it says Ride, press where it says Switch)
    _hit = co._guide_toward({("coaster", (28, 5))}, "Elesa")
    if not _hit or _hit[1] == "Elesa":
        break
    _seen.append(_hit[1])
    if _hit[1] == "Ride":
        co.player = next(l for c, l in _rides[_hit[0]] if co._ride_ok(c, frozenset()))
    elif _hit[1] == "Switch":
        co.player = _hit[0]
        story.story_flags[_sw[_hit[0]]] = not story.story_flags.get(_sw[_hit[0]])
    else:
        co.player = _hit[0]
check(_hit and _hit[1] == "Elesa" and "Switch" in _seen and "Ride" in _seen,
      f"from the entrance, the marker's rides and switches lead to the back room ({_seen}, then {_hit})")
lob = walk_town("DRIFTVEIL_CITY", None, room="gym_lobby", play=False)
_hit = lob._guide_toward({("gym", (10, 87))}, "Clay")
check(_hit and _hit[1].startswith("Lift to") and (getattr(lob, "_lift_plan", None) or [None, None])[1] == "gym",
      f"Driftveil Gym's lobby: the marker leads to the lift and picks the Gym floor ({_hit}, {getattr(lob, '_lift_plan', None)})")
lux = walk_town("DRIFTVEIL_CITY", None, room="luxury", play=False)
_hit = lux._guide_toward({("luxury_23", (3, 4))}, "Up top")
check(_hit and (getattr(lux, "_lift_plan", None) or [None, None])[1] == "luxury_23",
      f"the Luxury Suites: the lift, to 23F ({_hit})")

lea = walk_town("UNOVA_POKEMON_LEAGUE", None, room="plaza", play=False)
_e4 = ("b2_e4_shauntal", "b2_e4_grimsley", "b2_e4_caitlin", "b2_e4_marshal")
for _f in _e4:
    story.story_flags.pop(_f, None)
check(not lea._guide_lifts("plaza"), "the League statue's lift is no way yet with the Elite Four unbeaten (its 'requires')")
for _f in _e4:
    story.story_flags[_f] = True
lea._guide_parts = {}
check(list(lea._guide_lifts("plaza").values()) == [[["Down to the Champion", "chamber", 30, 84]]],
      "with all four beaten, it goes down to the Champion")
for _f in _e4:
    story.story_flags.pop(_f, None)

print("Team Galactic HQ before the Galactic Key: the marker goes by the pads to the west door, not back the way you came (Sinnoh, 11-25)")
from src.states.overworld.dungeon import DungeonState as _DS
guide.WALKED_REGIONS |= {"SINNOH"}
for _f in ("galactic_lake_acuity_cleared", "sinnoh_storage_door_open"):
    story.story_flags[_f] = True
_m11 = next(m for m in g.loader.area_data["JOURNAL_MISSIONS"] if m["id"] == "sinnoh_m11")
story.current_area_key, story.last_area_key = "TEAM_GALACTIC_HQ", "GALACTIC_WAREHOUSE"
_hq = _DS(g)
_hq.run.index, _hq.run.player = 0, (47, 3)
check(_hq._guide_step(_m11) is None, "the HQ's own way-point (Cyrus) waits while the warehouse's Galactic Key is the step")
_sp = _hq._guide_spot()
check(_sp and _sp[0] != (46, 2), f"and the marker isn't the door you came in by ({_sp})")
for _f in ("galactic_lake_acuity_cleared", "sinnoh_storage_door_open"):
    story.story_flags.pop(_f, None)

print("Way-points sharing one done flag are one leg: any of its places leads (Hoenn's sail to Sky Pillar, 11-25)")
guide.WALKED_REGIONS |= {"HOENN"}
_d1 = next(m for m in g.loader.area_data["JOURNAL_MISSIONS"] if m["id"] == "hoenn_d1")
_shared = [s_ for s_ in _d1.get("steps") or [] if s_.get("area") == "HOENN_ROUTE_128"]
if _shared and any(o is not _shared[0] and o.get("done") == _shared[0].get("done") for o in _d1["steps"]):
    story.story_flags["delta_matt_mossdeep"] = True
    inv["HM_SURF"] = 1
    story.current_area_key, story.last_area_key = "HOENN_ROUTE_128", "HOENN_ROUTE_127"
    _r128 = _DS(g)
    check(_r128._guide_step(_d1) is not None, f"on Route 128 the marker takes its way-point though Route 127's, under the same flag, isn't done ({_r128._guide_step(_d1)})")
else:
    check(True, "(hoenn_d1 has no shared-flag legs any more: nothing to test)")

print(f"##### {fails} failures")
