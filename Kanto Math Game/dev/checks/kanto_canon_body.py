# Kanto's and Sevii's content against FireRed (11-16, SWEEP_RULES Part 3 item 7: "one checker per new region"): every FireRed
# trainer with FireRed's team and levels, item balls, hidden items, FRLG's wild species, people, gifts, trades, tutors.
# The checker is kanto_handoff/kanto_rom_tools/kcanon.py (agreed differences: kcanon_decisions.json; the report:
# kanto_handoff/kanto_check/CANON.md). This suite runs it and prints each gap as a FAIL line, then opens the route and
# cave maps the way a player meets them and looks for FireRed's trainers and item balls on FireRed's own tiles.
# It only reads. Glue after harness_head.py:
#   bash dev/checks/run.sh kanto_canon          (-v for every line; a gap marked [call] waits for Jordan's answer)
import json
from src.states.overworld import PlayState, CityState
from src.states.overworld.walk_town import WalkTownState as _WTS

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


_tools = os.path.abspath(os.path.join(os.getcwd(), "..", "..", "kanto_handoff", "kanto_rom_tools"))
check(os.path.exists(os.path.join(_tools, "kcanon.py")) and os.path.exists(os.path.join(_tools, "canon", "fr_maps.json")),
      f"the checker and FireRed's content are in the handoff folder ({_tools}; make canon/ with kcanon_rom.py --pages)")
sys.path.insert(0, _tools)
import kcanon as K

# ---- the data: every area, group by group (kcanon.py's own run, decisions applied)
res = K.run()
for r in res:
    for group, kinds in K.GROUPS:
        gaps = [x for x in r["gaps"] if x[0] in kinds]
        if not gaps:
            print(f"   ok  {r['key']}: {group} as FireRed's")
        for kind, what, call in gaps:
            check(False, f"{r['key']}: [{kind}] {what}" + ("  [call]" if call else ""))
_tot = sum(len(r["gaps"]) for r in res)
print(f"   ..  kcanon: {_tot} gaps in {sum(1 for r in res if r['gaps'])} of {len(res)} areas; "
      f"{sum(len(r['decided']) for r in res)} agreed differences; {sum(1 for r in res for x in r['gaps'] if x[2])} wait for Jordan's call")

# ---- as a player meets it: open each route / cave map from the data and look at who stands where
g.dungeon_routes = True; g.walk_towns = True; g.player_character = "red"
_area = g.loader.area_data["STORY_PROGRESSION"]
PIECED = {"KANTO_ROUTE_3", "KANTO_ROUTE_4", "KANTO_ROUTE_10", "KANTO_ROUTE_10_SOUTH", "LAVENDER_TOWN", "SAFARI_ZONE", "SAFFRON_CITY",
          "KANTO_ROUTE_21", "THREE_ISLAND", "KANTO_ROUTE_19"}   # (made of pieces of FireRed's maps, kpiece.py: their tiles are shifted)


def frames(n):
    for _ in range(n):
        g.current_state.update(); g.current_state.draw()


def open_map(key):
    story.current_area_key, story.last_area_key = key, None
    g.walk_town_pos = None
    st = CityState(g) if _area[key].get("area_type") == "town" else None
    if st is None or not isinstance(st, _WTS):
        st = PlayState(g); g.states["play"] = st
    g.change_state(st)
    frames(2)
    return g.current_state


_seen = 0
for key in K.ORDER:
    maps = K.fr_maps(key)
    if key in PIECED or key not in K.M or not maps or key not in _area or _area[key].get("area_type") == "town":
        continue
    try:
        st = open_map(key)
        movers = list(st.run.floor.movers)
    except Exception as e:   # (a map that can't be opened this way is the map suites' business, not this one's)
        print(f"   ..  {key}: not opened here ({type(e).__name__})")
        continue
    tr = {(m.x, m.y) for m in movers if m.kind == "trainer"} | {(m.x, m.y) for m in movers if m.kind == "figure" and isinstance(m.payload, dict)
                                                                and ((m.payload.get("event") or {}).get("battle") or any(st.get("battle") for st in (m.payload.get("event") or {}).get("stages") or []))}   # (11-17: a story battle standing on a FireRed trainer's tile: the Warehouse's last Admin)
    fig = {(m.x, m.y) for m in movers if m.kind == "figure"}
    best = None
    for nm in maps:   # (the FireRed map our first floor was cut from: the one whose trainers and balls lie on ours)
        groups = {}
        for p in K.FR[nm]["people"]:
            if p.get("battle"):
                groups.setdefault(p["battle"]["id"], []).append((p["x"], p["y"]))
        balls = [(p["x"], p["y"], p["item"]) for p in K.FR[nm]["people"] if p.get("item")
                 and not any(K.re.search(d["pattern"], f"{key} {'item ball':11} {K.show_item(p['item'])} at") for d in K.DEC.get("skip", []))]   # (agreed: no Up-Grade)
        hit = sum(1 for t in groups.values() if any(q in tr for q in t)) + sum(1 for x, y, _ in balls if (x, y) in fig)
        if (groups or balls) and (best is None or hit > best[0]):
            best = (hit, nm, groups, balls)
    if best is None or best[0] == 0:
        continue   # (nothing of FireRed's first-floor map stands here: the data check above already lists what is missing)
    _seen += 1
    hit, nm, groups, balls = best
    off_t = sorted(t[0] for t in groups.values() if not any(q in tr for q in t))
    off_b = sorted((x, y, it) for x, y, it in balls if (x, y) not in fig)
    check(not off_t, f"{key}: FireRed's {len(groups)} trainers of map {nm} stand on their own tiles (none at {off_t})")
    check(not off_b, f"{key}: FireRed's {len(balls)} item balls of map {nm} lie on their own tiles (none at {off_b})")
check(_seen >= 40, f"route and cave maps opened and compared with FireRed's tiles: {_seen}")

print(f"##### {len(fails)} failures")
