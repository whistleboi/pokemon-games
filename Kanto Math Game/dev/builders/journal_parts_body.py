# Places in parts, for the Journal marker (Journal branch J7, 11-24; Jordan: "build part-level reach").
# A walked place whose ways out don't all join (Mt. Coronet: the south rooms reach Route 216 only with Rock Climb; Hoenn's
# Routes 129-131: two seas each; Team Galactic HQ: the warehouse side and the front door) - which ways out join which,
# for each set of the HMs that change it. Worked out with the walker's own reach (DungeonState._step_route, loose: as the
# marker plans, people and Strength boulders don't count), once, here; the game only reads assets/journal_parts.json.
#   cat dev/checks/harness_head.py dev/builders/journal_parts_body.py > dev/checks/out/jparts.py
#   python dev/checks/out/jparts.py dev/checks/out [AREA ...]       (no areas: every walked place; rerun when maps change)
import json, itertools, time
from src.states.overworld.dungeon import DungeonState
from src.states.overworld.walk_town import custom
from src.world import guide, hms

story = g.story_manager
g.walk_towns = True
g.dungeon_routes = True
prog = g.loader.area_data["STORY_PROGRESSION"]
REGIONS = {"KANTO", "JOHTO", "ORANGE", "HOENN", "SINNOH", "UNOVA", "ORRE"}
HMS = ["HM_SURF", "HM_STRENGTH", "HM_CUT", "HM_ROCK_SMASH", "HM_WATERFALL", "HM_ROCK_CLIMB", "HM_DIVE", "HM_WHIRLPOOL",
       "HM_DEFOG", "HM_FLASH", "BICYCLE"]
hms.usable = lambda st, item: st.inventory.get(item, 0) > 0   # (badges: a kit counts as usable here)
areas = sys.argv[2:] or sorted(k for k, a in custom(g).items() if isinstance(a, dict) and k in prog
                               and (prog[k].get("area_type") != "town") and str(story.area_region(k)).upper() in REGIONS)
guide.WALKED_REGIONS |= REGIONS
base_flags, base_inv = dict(story.story_flags), dict(story.inventory)
saved = {k: getattr(g, k, None) for k in ("arrive_edge", "arrive_floor", "walk_town_pos", "walk_town_room")}


def groups(area, kit):
    story.story_flags.clear(); story.story_flags.update(base_flags)
    story.inventory.clear(); story.inventory.update(base_inv)
    for h in kit:
        story.inventory[h] = 1
    for k, v in saved.items():
        setattr(g, k, v)
    story.current_area_key = area
    st = DungeonState(g)
    run = st.run
    outs = {}
    for i in range(run.n_floors):
        for (x, y), t in run.made(i).exits.items():
            if isinstance(t, str) and t in prog and t != area:
                outs[(i, x, y)] = t
    got, seen = [], set()
    for node in sorted(outs):
        if node in seen:
            continue
        reach = st._step_route(node, frozenset(), None, reach=True, loose=True)
        grp = frozenset(n for n in outs if n in reach or n == node)
        seen |= grp
        got.append(grp)
    return outs, frozenset(got)


out, t0, done = {}, time.time(), 0
for area in areas:
    try:
        outs, every = groups(area, HMS)
        _, none = groups(area, [])
    except Exception as e:   # (a place the walker can't build headless: left to the marker as before)
        print(f"   skip {area}: {type(e).__name__}: {e}")
        continue
    done += 1
    if len(every) <= 1 and len(none) <= 1:
        continue
    rel = [h for h in HMS if every != none and groups(area, [x for x in HMS if x != h])[1] != every]
    sets = {}
    for n in range(len(rel) + 1):
        for kit in itertools.combinations(rel, n):
            _, grp = groups(area, list(kit) + [x for x in HMS if x not in rel])   # (the HMs that don't change it: held)
            if len(grp) > 1:
                sets[",".join(sorted(kit))] = [sorted([*n, outs[n]] for n in gr) for gr in sorted(grp, key=lambda s: sorted(s))]
    if sets:
        out[area] = {"hms": rel, "sets": sets}
        print(f"   {area}: {len(outs)} ways out, HMs that change it {rel}, {len(sets)} kits in parts")
story.story_flags.clear(); story.story_flags.update(base_flags)
story.inventory.clear(); story.inventory.update(base_inv)
path = "assets/journal_parts.json"
if sys.argv[2:]:   # (some areas: merge into the file)
    try:
        old = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        old = {}
    for a in sys.argv[2:]:
        old.pop(a, None)
    old.update(out)
    out = old
with open(path, "w", encoding="utf-8", newline="\n") as f:
    f.write("{\n" + ",\n".join(f"  {json.dumps(k)}: {json.dumps(v, separators=(',', ':'))}" for k, v in sorted(out.items())) + "\n}\n")
print(f"{done} places read, {len(out)} in parts, {time.time() - t0:.0f} s")
print("##### 0 failures")
