# The Journal marker in places whose parts don't join (Journal branch J7, 11-24; Jordan: "build part-level reach").
#   bash dev/checks/run.sh journal_parts
# assets/journal_parts.json (dev/builders/journal_parts_body.py: the walker's own reach, per HM that changes a place) tells
# the marker which ways out of a place join which; the planner then never sends you in by a part that can't lead on.
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

print("Team Galactic HQ: the warehouse side and the front door don't join")
hq = groups(g, "TEAM_GALACTIC_HQ") or []
sides = [{e[3] for e in grp} for grp in hq]
check({"GALACTIC_WAREHOUSE"} in sides and any("VEILSTONE_CITY" in s and "GALACTIC_WAREHOUSE" not in s for s in sides),
      f"two sides ({sides})")

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

print(f"##### {fails} failures")
