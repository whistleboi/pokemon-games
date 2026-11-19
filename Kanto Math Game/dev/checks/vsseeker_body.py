# The VS Seeker and trainer rematches (11-18, Jordan's answers: kanto_handoff/VS_SEEKER.md).
#   cat dev/checks/harness_head.py dev/checks/vsseeker_body.py > dev/checks/out/check_vsseeker.py
from src.world import vs_seeker
from src.pokemon import items as itemlib
from src.states.overworld import PlayState
fails = 0
g.dungeon_routes = True


def check(c, m):
    global fails
    print(("   ok  " if c else "   FAIL ") + m)
    fails += 0 if c else 1


print("1) getting it: Vermilion City in Kanto; after the 2nd badge elsewhere")
story.enter_region("KANTO")
story.inventory.pop("VS_SEEKER", None)
check(vs_seeker.gift(g, "CERULEAN_CITY") == [], "not in Cerulean")
lines = vs_seeker.gift(g, "VERMILLION_CITY")
check(story.inventory.get("VS_SEEKER") == 1 and any("VS SEEKER" in l for l in lines), f"Vermilion: given ({lines[-1:]})")
check(vs_seeker.gift(g, "VERMILLION_CITY") == [], "...once")
check("VS_SEEKER" in itemlib.FIELD and itemlib.FIELD["VS_SEEKER"].get("keep"), "a Bag item, kept when used")
story.inventory.pop("VS_SEEKER", None)
story.enter_region("JOHTO")
story.badges["JOHTO"] = ["ZEPHYR"]
check(vs_seeker.gift(g, "AZALEA_TOWN") == [], "Johto with one badge: not yet")
story.badges["JOHTO"] = ["ZEPHYR", "HIVE"]
check(vs_seeker.gift(g, "AZALEA_TOWN") != [] and story.inventory.get("VS_SEEKER") == 1, "Johto after the 2nd badge: given on arrival")

print("2) used on a route: trainers beaten today in view come back with a '!'")
story.enter_region("KANTO")
story.badges["KANTO"] = ["BOULDER", "CASCADE"]
area = "KANTO_ROUTE_3"
pool = g.loader.area_data["STORY_PROGRESSION"][area]["trainer_pool"]
idxs = [i for i, t in enumerate(pool) if isinstance(t, dict) and vs_seeker._route_trainer(story, t)]
for i in idxs:
    story.mark_trainer_defeated(area, i)
    story.story_flags.setdefault("trainers_beaten_on", {}).setdefault(area, {})[str(i)] = story._today()
story.current_area_key, story.last_area_key = area, "PEWTER_CITY"
p = PlayState(g)
g.states["play"] = p
g.change_state(p)
for _ in range(3):
    p.update()
f = p.run.floor
check(not any(m.kind == "trainer" for m in f.movers), f"Route 3: all {len(idxs)} trainers beaten today, none out")
spot = next(f.spots[f"trainer:{pool[i]['name']}"] for i in idxs if f.spots.get(f"trainer:{pool[i]['name']}"))
p.run.player = next((spot[0] + dx, spot[1] + dy) for dx, dy in ((0, 1), (1, 0), (-1, 0), (0, -1), (0, 2), (2, 0)) if f.walkable(spot[0] + dx, spot[1] + dy))
story.inventory["VS_SEEKER"] = 1
story.story_flags["vs_seeker_steps"] = vs_seeker.CHARGE
vs_seeker.READY_CHANCE = 1.0
lines = vs_seeker.use(p)
back = [m for m in f.movers if m.kind == "trainer"]
check(back and all(vs_seeker.is_ready(story, area, m.payload[0]) for m in back) and "wants a rematch" in lines[-1],
      f"used: {len(back)} came back ({lines[:3]})")
check(all(story.trainer_on_map(area, m.payload[0], pool[m.payload[0]]) for m in back), "...and they stay out if you come back today")
check("charging" in vs_seeker.use(p)[0], "used again at once: the battery needs charging")
for _ in range(vs_seeker.CHARGE):
    vs_seeker.step(story)
check(vs_seeker.charge(story) == vs_seeker.CHARGE, "100 steps: charged again")

print("3) the rematch: stronger, a bigger reward; won, it goes back to waiting")
i = back[0].payload[0]
info = pool[i]
re = vs_seeker.rematch(g, area, i, dict(info))
check(min(re["levels"]) >= min(info["levels"]) and sum(re["levels"]) > sum(info["levels"]),
      f"{info['name']}: levels {info['levels']} -> {re['levels']}")
check(re["rewards"].get("balls", 0) > (info.get("rewards") or {}).get("balls", 0), f"reward {info.get('rewards')} -> {re['rewards']}")
vs_seeker.won(story, area, i)
check(not vs_seeker.is_ready(story, area, i) and not story.trainer_on_map(area, i, info), "won: gone till the next use or tomorrow")
print("FAILURES:", fails)
