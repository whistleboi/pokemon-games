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

print("3) FireRed's own rematch stages: the next one you haven't beaten, held back till its story point")
ben_i = next(k for k, t in enumerate(pool) if isinstance(t, dict) and t.get("name") == "Ben")
ben = pool[ben_i]
check((ben.get("rematch") or {}).get("source") == "FireRed", f"Youngster Ben carries FireRed's stages ({[None if t is None else t['levels'] for t in ben['rematch']['tiers']]})")
for k in ("visited_CELADON_CITY", "visited_FUCHSIA_CITY", "beat_champion", "vs_stage"):
    story.story_flags.pop(k, None)
vs_seeker._ready(story).setdefault(area, {})[str(ben_i)] = story._today()
re1 = vs_seeker.rematch(g, area, ben_i, dict(ben))
check(re1["levels"] == [17, 17], f"first rematch: FireRed's Lv 17 team ({re1['levels']})")
check(re1["rewards"].get("balls", 0) > (ben.get("rewards") or {}).get("balls", 0), f"...a bigger reward ({ben.get('rewards')} -> {re1['rewards']})")
vs_seeker.won(story, area, ben_i, re1["_vs_stage"])
vs_seeker._ready(story).setdefault(area, {})[str(ben_i)] = story._today()
check(vs_seeker.rematch(g, area, ben_i, dict(ben))["levels"] == [17, 17], "next stage still locked: the Lv 17 team again")
story.story_flags["visited_CELADON_CITY"] = True
check(vs_seeker.rematch(g, area, ben_i, dict(ben))["levels"] == [17, 17], "Celadon reached: still Lv 17 (Ben's Lv 28 team is FireRed's 3rd stage, held till Fuchsia)")
story.story_flags["visited_FUCHSIA_CITY"] = True
re2 = vs_seeker.rematch(g, area, ben_i, dict(ben))
check(re2["levels"] == [28, 28], f"Fuchsia reached: the Lv 28 team ({re2['levels']})")
vs_seeker.won(story, area, ben_i, re2["_vs_stage"])
vs_seeker._ready(story).setdefault(area, {})[str(ben_i)] = story._today()   # (called back again)
check(vs_seeker.rematch(g, area, ben_i, dict(ben))["levels"] == [28, 28], "the Lv 48 team waits for the Champion: Lv 28 again")
story.story_flags["beat_champion"] = True
check(vs_seeker.rematch(g, area, ben_i, dict(ben))["levels"] == [48, 48], "after the Champion: the Lv 48 team")
vs_seeker.won(story, area, ben_i, 3)
check(not vs_seeker.is_ready(story, area, ben_i), "won: gone till the next use or tomorrow")
plain = {"name": "Nobody", "class": "YOUNGSTER", "team": [19], "levels": [5]}
check(not vs_seeker._has_rematch(story, area, plain), "a Kanto trainer FireRed gives no rematch never wants one (FireRed's X)")
print("4) in a town, just Seven Island's Psychics Dario and Rodette (FireRed's one rematch each, after the Sevii quest)")
from src.states.overworld import CityState as _CS
from src.states.overworld import common as _common
from src.states.battle import TrainerIntroState as _TIS
g.walk_towns = True
story.enter_region("KANTO")
story.story_flags.update({"beat_dario_seven": True, "sevii_warehouse_cleared": True})
for _k in [k for k in (story.story_flags.get("vs_ready") or {}).get("SEVEN_ISLAND", {})]:
    story.story_flags["vs_ready"]["SEVEN_ISLAND"].pop(_k)
story.current_area_key, story.last_area_key = "SEVEN_ISLAND", None
g.walk_town_pos = None; g.walk_town_room = None
t = _CS(g); g.change_state(t)
for _ in range(3):
    g.current_state.update()
t = g.current_state
_d = next(((tile, ev) for tile, ev in vs_seeker._town_battles(t) if ev["battle"]["name"] == "Psychic Dario"), None)
check(_d is not None, f"Dario stands in Seven Island, beaten, with FireRed's rematch stage ({_d[0] if _d else None})")
t.player = (_d[0][0], _d[0][1] + 1)
story.story_flags["vs_seeker_steps"] = vs_seeker.CHARGE
lines = vs_seeker.use_town(t)
check(any("Psychic Dario wants a rematch" in l for l in lines) and vs_seeker.is_ready(story, "SEVEN_ISLAND", vs_seeker.town_key(_d[1])), f"used beside him: {lines}")
_common._run_story_event(t, _d[1], lambda c: True, lambda ls: None)
intro = g.current_state
b = getattr(intro, "next_state", None)
check(isinstance(intro, _TIS) and [p_.id for p_ in b.opponent_team] == [203] and b.opponent_team[0].level == 56,
      f"talk to him: FireRed's rematch, Girafarig Lv 56 ({type(intro).__name__}, {[(p_.id, p_.level) for p_ in getattr(b, 'opponent_team', [])]})")
story.story_flags[f"vs_won|SEVEN_ISLAND|{vs_seeker.town_key(_d[1])}"] = True   # (the battle won)
vs_seeker.settle_town(story, "SEVEN_ISLAND")
check(not vs_seeker.is_ready(story, "SEVEN_ISLAND", vs_seeker.town_key(_d[1])), "won: he waits for the VS Seeker again")
g.change_state(t)
story.story_flags["vs_seeker_steps"] = vs_seeker.CHARGE
t.player = (3, 3)
_far = vs_seeker.use_town(t); check(not any(l.endswith("wants a rematch!") for l in _far), f"far from them: nobody answers ({_far}, at {t.player})")
print("FAILURES:", fails)
