
# The three story blockers fixed on 2026-10-23 (Sinnoh HQ key, Unova N at Icirrus, Galar Eternatus).
from src.states.overworld import CityState, PlayState
from src.world import levels
fails = 0


def check(ok, msg):
    global fails
    print(("ok   " if ok else "FAIL ") + msg)
    fails += 0 if ok else 1


def city_options(area, kind):
    story.current_area_key = area
    c = CityState(g); g.change_state(c)
    if kind == "travel_options":
        c.open_travel_menu()  # tags each option TRAVEL, as a tap on TRAVEL does
    else:
        c.open_explore_menu()
    return [b.text for b in c.hover_buttons]


def route_buttons(area):
    story.current_area_key = area
    p = PlayState(g); g.change_state(p)
    p.show_progression_menu()
    return [b.text for b in p.route_buttons]


# Sinnoh: the Galactic Key (a Bag item from Jupiter) opens the HQ.
story.inventory.pop("GALACTIC_KEY", None)
check("Team Galactic HQ" not in city_options("VEILSTONE_CITY", "travel_options"), "Veilstone: no HQ travel without the key")
check("Galactic Veilstone HQ" not in city_options("VEILSTONE_CITY", "explore_options"), "Veilstone: no HQ explore without the key")
story.inventory["GALACTIC_KEY"] = 1
check("Team Galactic HQ" in city_options("VEILSTONE_CITY", "travel_options"), "Veilstone: HQ travel with the key")
check("Galactic Veilstone HQ" in city_options("VEILSTONE_CITY", "explore_options"), "Veilstone: HQ explore with the key")

# Unova: N at Icirrus no longer brings a Lv 70 Zekrom to a badge-6 fight.
ev = g.loader.area_data["STORY_PROGRESSION"]["ICIRRUS_CITY"]["on_enter_event"]
team = ev["trainer"]["team"]
check(not any(levels.is_legendary(pid) for pid in team), f"Icirrus N team has no legendary: {team}")
story.current_area_key = "ICIRRUS_CITY"
lv = levels.trainer_level(g, "ICIRRUS_CITY")
check(lv <= 39, f"Icirrus trainer level {lv} is under the badge-6 cap (39)")

# Galar: Oleana, Rose and the Eternatus fight, then the catchable Eternatus boss.
area = "ROSE_TOWER"
pool = g.loader.area_data["STORY_PROGRESSION"][area]["trainer_pool"]
check(not any(levels.is_legendary(pid) for pid in pool[1]["team"]), f"Rose's team has no legendary: {pool[1]['team']}")
for i in range(len(pool)):
    story.defeated_trainers.get(area, set()).discard(i)
for f in ("oleana_defeated", "rose_tower_cleared", "eternatus_defeated", "ROSE_TOWER_boss_defeated"):
    story.story_flags.pop(f, None)
for i, flag in enumerate(["oleana_defeated", "rose_tower_cleared", "eternatus_defeated"]):
    btns = route_buttons(area)
    check("BATTLE ROSE TOWER" in btns and "THE ENERGY PLANT ROOF" not in btns, f"before trainer {i + 1} ({pool[i]['name']}): {btns}")
    story.mark_trainer_defeated(area, i)
    story.story_flags[flag] = True
btns = route_buttons(area)
check("THE ENERGY PLANT ROOF" in btns and "BATTLE ROSE TOWER" not in btns, f"after all three: {btns}")
story.story_flags["ROSE_TOWER_boss_defeated"] = True
check("THE ENERGY PLANT ROOF" not in route_buttons(area), "boss gone once Eternatus is caught")

print(f"##### blockers: {fails} fails")
