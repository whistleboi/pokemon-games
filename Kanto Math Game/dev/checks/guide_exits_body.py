# The Journal marker reads a map's ways out exactly as the walker does (Unova 11-23: Castelia's streets and piers use the
# extra exit letters g h i j k l q t y z, which the marker skipped, so no gold marker at Burgh's Gym or the north gate).
#   bash dev/checks/run.sh guide_exits
from src.states.overworld import CityState

fails = 0


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


g.dungeon_routes = True; g.walk_towns = True; g.live3d_headless = True
story.enter_region("UNOVA")
for area in ("CASTELIA_CITY", "NIMBASA_CITY"):
    story.current_area_key, story.last_area_key = area, None
    story.story_flags["visited_" + area] = True
    g.walk_town_pos = g.walk_town_room = None
    t = CityState(g)
    if not hasattr(t, "exits"):
        print(f"   ({area} isn't walked on this branch yet)")
        continue
    walker = {tg for tg in t.exits.values()}
    marker = set(t._guide_part(None)["exits"].values())
    check(walker <= marker, f"{area}: the marker knows every way out the walker does (missing {sorted(walker - marker)})")
print("a place in parts (Jordan 11-24): the marker points the way round; a part can be named")
story.current_area_key, story.last_area_key = "FLOCCESY_TOWN", "UNOVA_ROUTE_19"
g.walk_town_pos = g.walk_town_room = None
t = CityState(g)
if hasattr(t, "exits"):
    parts = t._parts()
    mine = t._part_of(t.player)
    other = next((tile for tile, p in parts.items() if p != mine and tile not in t.exits), None)
    check(other is not None, f"Floccesy has a part you can't walk to from where you came in ({len(set(parts.values()))} parts)")
    if other:
        way = t._guide_round(other)
        check(way and t.exits.get(way[0]) == "UNOVA_ROUTE_20" and way[1] == "Way round",
              f"...the marker points at the way out that leads round to it: Route 20 ({way and (t.exits.get(way[0]), way[1])})")
        check(t._guide_round(t.player) is None, "...nothing to go round for in your own part")
        t.town_map = dict(t.town_map, part_names={"%d,%d" % other: "Zz Corner"})
        way = t._guide_round(other)
        check(way and way[1] == "To Zz Corner" and t.part_name(other) == "Zz Corner" and t.part_name() is None,
              f"...a named part: 'To Zz Corner' ({way and way[1]}); your own part has no name")
else:
    print("   (Floccesy isn't walked on this branch yet)")
print("Castelia Gym's cocoons (Unova 11-24): the marker rides them to Burgh")
story.current_area_key, story.last_area_key = "CASTELIA_CITY", None
g.walk_town_pos = g.walk_town_room = None
t = CityState(g)
if hasattr(t, "exits") and "gym_burgh" in (t.town_map.get("rooms") or {}):
    story.story_flags.pop("b2_insect_badge", None)
    t._go("gym", None)
    check(getattr(t, "room", None) == "gym" and t._guide_cocoons("gym"), f"in the Gym: its cocoons ({len(t._guide_cocoons('gym'))} you can ride now)")
    check("gym_burgh" in t._guide_rooms(), "the marker's rooms reach Burgh's, by the cocoons")
    burgh = next(iter((t.town_map["rooms"]["gym_burgh"].get("people") and t._guide_part("gym_burgh")["people"]) or {}), (9, 10))
    hit = t._guide_toward({("gym_burgh", tuple(burgh))}, "Burgh")
    cocs = {c for (c, _w) in t._guide_cocoons("gym")}
    check(hit is not None and hit[0] in cocs and hit[1] == "Cocoon", f"...and points at a cocoon to step into ({hit})")
else:
    print("   (Castelia Gym isn't walked on this branch yet)")
print("a building's front door back to the town says 'Way out', not 'Stairs' (Unova 11-24)")
story.current_area_key, story.last_area_key = "NIMBASA_CITY", None
g.walk_town_pos = g.walk_town_room = None
t = CityState(g)
if hasattr(t, "exits") and "center" in (t.town_map.get("rooms") or {}):
    t._go("center", None)
    kinds = {kind for _t, to, kind in t._guide_passages("center") if to is None}
    check(getattr(t, "room", None) == "center" and kinds == {"out"}, f"Nimbasa's Center: its way back to the town is 'out' ({kinds})")
    far = next(iter(t._guide_part(None)["doors"]), None)
    hit = t._guide_toward({(None, far)}, "Here") if far else None
    check(hit is not None and hit[1] == "Way out", f"...and the marker inside says 'Way out' ({hit})")
else:
    print("   (Nimbasa's Center isn't walked on this branch yet)")
g.walk_town_pos = g.walk_town_room = None
print(f"##### {fails} failures")
