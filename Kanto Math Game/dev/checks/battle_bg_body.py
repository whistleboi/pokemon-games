# Battle backgrounds from each region's own game (main 11-23, src/world/battle_bg.py): a walked region's
# assets/battle_bg/<REGION>/index.json picks by area, kind of battle, terrain and time of day; a Gym it doesn't name
# keeps its own (Kanto's custom Gyms); a region with no index is untouched (the menu regions).
#   bash dev/checks/run.sh battle_bg
import json, os, tempfile, datetime
import pygame
from src.world import battle_bg as bbg

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


tmp = tempfile.mkdtemp(prefix="bbg_")
_folder = bbg.folder
bbg.folder = lambda game, region: os.path.join(tmp, str(region).upper())
story.enter_region("JOHTO")
reg = str(story.area_region("VIOLET_CITY")).upper()
check(reg == "JOHTO", f"Violet City is in Johto ({reg})")
d = os.path.join(tmp, reg); os.makedirs(d)
for n in ("grass_summer.png", "grass_summer_night.png", "grass.png", "grass_night.png", "cave.png", "water.png", "r29.png", "town_w.png", "town_t.png", "gym.png", "lead.png", "e1.png", "e2.png"):
    pygame.image.save(pygame.Surface((8, 8)), os.path.join(d, n))
json.dump({"terrain": {"grass": "grass.png", "cave": "cave.png", "water": "water.png"},
           "areas": {"JOHTO_ROUTE_29": "r29.png",
                     "VIOLET_CITY": {"wild": "town_w.png", "trainer": "town_t.png", "gym": "gym.png", "leader": "lead.png",
                                     "elite": ["e1.png", "e2.png"]}}}, open(os.path.join(d, "index.json"), "w"))
bbg._INDEX.clear()
noon, night = datetime.datetime(2026, 1, 1, 12), datetime.datetime(2026, 1, 1, 23)
name = lambda p: os.path.basename(p) if p else None

print("1) by area and kind")
check(name(bbg.pick(g, "JOHTO_ROUTE_29", water=False, now=noon)) == "r29.png", "one picture for an area")
check(name(bbg.pick(g, "VIOLET_CITY", water=False, now=noon)) == "town_w.png", "wild")
check(name(bbg.pick(g, "VIOLET_CITY", trainer=True, water=False, now=noon)) == "town_t.png", "trainer")
check(name(bbg.pick(g, "VIOLET_CITY", gym=True, trainer=True, water=False, now=noon)) == "gym.png", "Gym trainer")
check(name(bbg.pick(g, "VIOLET_CITY", gym=True, leader=True, water=False, now=noon)) == "lead.png", "Gym Leader")
check(bbg.pick(g, "JOHTO_ROUTE_29", gym=True, leader=True, water=False, now=noon) is None, "a Gym in an area naming only one picture: its own (None)")
_ent = bbg.index(g, reg)["areas"]["VIOLET_CITY"]; _gl = (_ent.pop("gym"), _ent.pop("leader"))
check(bbg.pick(g, "VIOLET_CITY", gym=True, leader=True, trainer=True, water=False, now=noon) is None, "a Gym town naming only trainer / wild: the Gym keeps its own (None)")
_ent["gym"], _ent["leader"] = _gl
check(name(bbg.pick(g, "VIOLET_CITY", gym=True, elite_index=1, water=False, now=noon)) == "e2.png", "Elite Four by place")
check(name(bbg.pick(g, "VIOLET_CITY", gym=True, elite_index=9, water=False, now=noon)) == "e2.png", "a place past the list: the last")

print("2) terrain and time")
area = next((k for k, a in g.loader.area_data.get("STORY_PROGRESSION", {}).items()
             if str(story.area_region(k)).upper() == reg and k not in ("JOHTO_ROUTE_29", "VIOLET_CITY")
             and bbg.TERRAIN.get(str(a.get("battle_type") or "").lower()) == "grass"), None)
check(area is not None, f"a grass area in {reg}: {area}")
if area:
    check(name(bbg.pick(g, area, water=False, now=noon)) == "grass.png", f"{area}: the region's grass")
    check(name(bbg.pick(g, area, water=False, now=night)) == "grass_night.png", f"{area} at night: its night picture")
    check(name(bbg.pick(g, area, water=True, now=noon)) == "water.png", f"{area} on the water: water")
    check(bbg.pick(g, area, gym=True, water=False, now=noon) is None, "a Gym the index doesn't name: its own (None)")
    _jul, _julnight = datetime.datetime(2026, 2, 1, 12), datetime.datetime(2026, 2, 1, 23)   # (February: Black 2's summer)
    check(name(bbg.pick(g, area, water=False, now=_jul)) == "grass_summer.png", f"{area} in summer: its summer picture (Unova 11-24)")
    check(name(bbg.pick(g, area, water=False, now=_julnight)) == "grass_summer_night.png", f"{area} on a summer night: both")
    check(name(bbg.pick(g, area, water=False, now=datetime.datetime(2026, 3, 1, 12))) == "grass.png", f"{area} in autumn with no autumn picture: the plain one")

print("3) no index: untouched")
check(bbg.pick(g, "PALLET_TOWN", water=False, now=noon) is None, "Kanto (no index in the test folder): None")
bbg.folder = _folder; bbg._INDEX.clear()
real = [r for r in ("KANTO", "JOHTO", "HOENN", "SINNOH", "UNOVA", "ORANGE", "ORRE") if bbg.index(g, r)]
print("   regions with their own index now:", real or "none yet")

print("4) event Leaders and trainers in a Gym's room (Orange 11-23)")
from src.states.battle import TrainerBattleState as _TBS
bbg.folder = lambda game, region: os.path.join(tmp, str(region).upper()); bbg._INDEX.clear()
_seen = []
_pick = bbg.pick
bbg.pick = lambda *a, **k: (_seen.append(k) or _pick(*a, **dict(k, water=False, now=noon)))
story.current_area_key = "VIOLET_CITY"
_g0 = getattr(g, "walk_town_room", None)
g.walk_town_room = None
_seen.clear(); _TBS(g, [mk(19)], trainer_class="GYM_LEADER", trainer_name="Falkner", area_name="VIOLET_CITY", trainer_img_name="falkner")
check(_seen and _seen[0].get("leader"), f"a Leader met through an event asks for the Leader's picture ({_seen[:1]})")
_seen.clear(); _TBS(g, [mk(19)], trainer_class="YOUNGSTER", trainer_name="Joey", area_name="VIOLET_CITY", trainer_img_name="youngster")
check(_seen and not _seen[0].get("gym") and not _seen[0].get("leader"), f"an ordinary trainer outside: the trainer picture ({_seen[:1]})")
g.walk_town_room = ("VIOLET_CITY", "gym")
_seen.clear(); _TBS(g, [mk(19)], trainer_class="BIRD_KEEPER", trainer_name="Rod", area_name="VIOLET_CITY", trainer_img_name="bird_keeper")
check(_seen and _seen[0].get("gym"), f"a trainer inside the Gym's room: the Gym's picture ({_seen[:1]})")
g.walk_town_room = _g0
_seen.clear(); _TBS(g, [mk(19)], trainer_class="GYM_LEADER", trainer_name="Falkner", area_name="VIOLET_CITY", trainer_img_name="falkner",
                   battle_type="gym", is_boss_battle=True)
check(_seen and _seen[0].get("leader") and _seen[0].get("gym"), f"a Gym Leader in the Gym (battle_type gym) asks the index for the Leader's picture ({_seen[:1]})")
bbg.pick = _pick; bbg.folder = _folder; bbg._INDEX.clear()

print("5) a Gym town listing several pictures isn't a League (Hoenn 11-24)")
bbg.folder = lambda game, region: os.path.join(tmp, str(region).upper()); bbg._INDEX.clear()
_vg = g.loader.area_data["STORY_PROGRESSION"].get("VIOLET_CITY") or {}
_saved_bg = _vg.get("backgrounds")
_vg["backgrounds"] = dict(_saved_bg or {}, gym=["a.png", "b.png"])
_seen = []
_pick = bbg.pick
bbg.pick = lambda *a, **k: (_seen.append(k) or _pick(*a, **dict(k, water=False, now=noon)))
story.get_gym_battle_background("VIOLET_CITY", 0, True)
check(_seen and _seen[0].get("leader") and _seen[0].get("elite_index") is None, f"Violet's Leader with two Gym pictures: the Leader's, not an Elite Four place ({_seen[:1]})")
bbg.pick = _pick; bbg.folder = _folder; bbg._INDEX.clear()
if _saved_bg is None:
    _vg.pop("backgrounds", None)
else:
    _vg["backgrounds"] = _saved_bg

print("6) a battle loads one by path")
from src.states.battle import TrainerBattleState
p = os.path.join(d, "gym.png")
b = TrainerBattleState(g, [mk(19)], trainer_class="YOUNGSTER", trainer_name="Joey", area_name=story.current_area_key, background_image=p)
check(b.background is not None, "background_image given as a path loads")
print(f"##### {len(fails)} failures")
