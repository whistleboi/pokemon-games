# Kanto + Sevii on the route walker: every Kanto area reachable, the caves and buildings, Sevii, Pallet walked,
# Routes 12-23, the Safari Zone, Seafoam, Victory Road, Cerulean Cave (split from dungeon 11-23).
#   bash dev/checks/run.sh dungeon_kanto
exec(open("dev/checks/dungeon_lib.py", encoding="utf-8").read())
g.dungeon_routes = True

# ---- every Kanto area (Jordan, 11-05): routes, caves, the sea, the Safari Zone, the buildings
from src.states.overworld import dungeon as _dg


def _reach_of(f, start):
    """Where you can get to from start, a boulder counting as pushed aside (Strength and the slide puzzle), a cracked rock as broken (Rock Smash), a waterfall as climbed and a rock wall as scaled (Waterfall, Rock Climb), a ledge as hopped over (one way: near enough for this)."""
    held = {t: f.tiles[t[1]][t[0]] for t, v in f.decor.items() if str(v).startswith(("boulder:", "whirl:", "ledge:", "crack:", "falls:", "climb:", "cut:", "slope:"))}
    for (x, y) in held:
        f.tiles[y][x] = core.FLOOR
    try:
        return core.distances(f, start)
    finally:
        for (x, y), v in held.items():
            f.tiles[y][x] = v


_prog = g.loader.area_data["STORY_PROGRESSION"]
_kanto = [k for k in _dg.recipes(g) if k in _prog and _prog[k].get("area_type") != "town"
          and k not in ("DEFAULT",) and not k.startswith("_")]
_bad = []
for _a in _kanto:
    try:
        _p = kanto(_a, came=next(iter([i.get("target") or i.get("target_area") for i in _prog[_a].get("route_menu", [])
                                       if i.get("action") in ("EXIT", "TRAVEL")] or [None])))
        if not isinstance(_p, DungeonState):
            _bad.append((_a, "not a map"))
            continue
        while _p.run.index > 0:  # (a cave entered partway down, Cerulean Cave's 1F: from its top floor)
            _p._ascend()
        _art_floors = ((_dg.recipe_for(g, _a).get("art") or {}).get("floors") or [])
        for _i in range(_p.run.n_floors):
            _f = _p.run.floor
            _reach = _reach_of(_f, _p.run.player)
            if (_i < len(_art_floors) and _art_floors[_i].get("parts")) or (_dg.recipe_for(g, _a).get("art") or {}).get("parts"):  # (in parts: each from its own ladder)
                for _t in list(_f.exits):
                    _reach = {**_reach, **_reach_of(_f, _t)}
            for _t in (_art_floors[_i].get("landings") or [] if _i < len(_art_floors) else []):  # (where you land, falling through a hole above: Mt. Pyre)
                _reach = {**_reach, **_reach_of(_f, tuple(_t))}
            _things = list(_f.exits) + list(_f.items) + list(_f.tm_spots) + ([] if _dg.recipe_for(g, _a).get("layout") else [(m.x, m.y) for m in _f.movers])
            if any(t not in _reach for t in _things):
                _bad.append((_a, _i, "something out of reach", [(t, _f.exits.get(t), _f.items.get(t)) for t in _things if t not in _reach][:6]))
            _p.draw()
            if _i < _p.run.n_floors - 1:
                _p._descend()
        for _i in range(_p.run.n_floors - 1):
            _p._ascend()
        if _p.run.index != 0:
            _bad.append((_a, "stairs back up"))
    except Exception as _e:
        import traceback
        traceback.print_exc()
        _bad.append((_a, repr(_e)))
check(not _bad, f"all {len(_kanto)} areas with their own recipe: a map, every floor crossable and drawn, stairs both ways {_bad[:4]}")
check({"MT_MOON", "ROCK_TUNNEL", "SEAFOAM_ISLANDS", "KANTO_POKEMON_TOWER", "POWER_PLANT", "KANTO_ROUTE_20",
       "SAFARI_ZONE", "KANTO_SS_ANNE", "CERULEAN_CAVE", "VICTORY_ROAD"} <= set(_kanto), "caves, the sea, the buildings too")

# every region's areas (the map replaces the route menu everywhere): each opens and draws, every way out,
# figure and item on its first floor can be reached
_all = [k for k, a in _prog.items() if isinstance(a, dict) and a.get("area_type") != "town"
        and not a.get("soaring")]   # (Soaring in the Sky is its flight screen, not a map: dev/checks/soaring_body.py)
_bad = []
for _a in _all:
    try:
        story.badges.setdefault(str(_prog[_a].get("region") or "KANTO").upper(), [])
        _p = kanto(_a, came=None)
        if _a == "HOENN_SOARING_IN_THE_SKY" and type(_p).__name__ == "Soaring3DState":
            continue  # (the flight, not a map: its own suite, soaring3d)
        if not isinstance(_p, DungeonState):
            _bad.append((_a, "not a map"))
            continue
        _f = _p.run.floor
        _reach = _reach_of(_f, _p.run.player)
        _af = ((_dg.recipe_for(g, _a).get("art") or {}).get("floors") or [])
        if (_af and _af[_p.run.index].get("parts")) or (_dg.recipe_for(g, _a).get("art") or {}).get("parts") or (_dg.recipe_for(g, _a).get("art") or {}).get("split"):  # (in parts, Rock Tunnel's 1F: each from its own ladder; Route 42: each from its own way out)
            for _t in list(_f.exits):
                _reach = {**_reach, **_reach_of(_f, _t)}
        for _t in getattr(_f, "deep", ()):  # (deep sea: come up into it from the seabed by Dive: Route 124's rocky northern waters)
            if _t not in _reach:
                _reach = {**_reach, **_reach_of(_f, _t)}
        _grew = True
        while _grew:   # (a door to elsewhere on this same floor: the Royal Unova's cabins, 11-21)
            _grew = False
            for _t, _v in list(_f.exits.items()):
                _w = str(_v).split(":")
                if _t in _reach and _w[0] == "WARP" and len(_w) == 4 and int(_w[1]) == _p.run.index and (int(_w[2]), int(_w[3])) not in _reach:
                    _reach = {**_reach, **_reach_of(_f, (int(_w[2]), int(_w[3])))}
                    _grew = True
        _drawn = bool(_dg.recipe_for(g, _a).get("layout"))  # (a drawn place's clerk stands behind its counter)
        if any(t not in _reach for t in list(_f.exits) + ([] if _drawn else [(m.x, m.y) for m in _f.movers])):
            _bad.append((_a, "out of reach"))
        _p.draw()
    except Exception as _e:
        _bad.append((_a, repr(_e)[:80]))
check(not _bad, f"every region: all {len(_all)} areas that aren't towns are maps {_bad[:5]}")
_styles = {_dg.recipe_for(g, k).get("style") for k in _all}
check({"field", "forest", "cave", "building", "sea", "snow", "desert"} <= _styles, f"their looks from their battle types {sorted(_styles)}")

# zones: a floor each, the zone you're on is the one whose Pokemon you meet
_p = kanto("SEAFOAM_ISLANDS", came="KANTO_ROUTE_20")
check(_p.run.n_floors == 5 and story.story_flags.get("zone_SEAFOAM_ISLANDS") == "1f", "Seafoam: 1F to B4F, you start on 1F")
_p._descend()
check(story.story_flags.get("zone_SEAFOAM_ISLANDS") == "b1f" and _p._floor_name(1) == "B1F", "down the stairs: B1F's Pokemon")
_tower = kanto("KANTO_POKEMON_TOWER", came="LAVENDER_TOWN")
check(_tower.run.n_floors == 7 and "LAVENDER_TOWN" in _tower.run.floor.exits.values(), "the Pokemon Tower: FireRed's seven floors (Kanto batch 14), the way out on 1F")

# figures: a legendary doesn't wait for the trainers; story people; the rival on arrival
for _k in ("POWER_PLANT_boss_defeated",):
    story.story_flags.pop(_k, None)
_pp = kanto("POWER_PLANT", came="KANTO_ROUTE_10")
_zap = [m for f in _pp.run.floors for m in f.movers if m.kind == "figure" and m.payload.get("action") == "BOSS"]
check(_zap and not _prog["POWER_PLANT"].get("trainer_pool"), "Power Plant: Zapdos is on the map; no trainers here, as FireRed (ours were list-only, removed 11-17)")
check(_pp._figure_img(_zap[0].payload) is not None, "...drawn with its followers sprite (Jordan 11-14: every overworld Pokemon)")
story.story_flags.pop("mt_moon_nerd_defeated", None)
_mm = kanto("MT_MOON", came="PEWTER_CITY")
_last = _mm.run.n_floors - 1
while _mm.run.index < _last:
    _mm._descend()
_nerd = [m for m in _mm.run.floor.movers if m.kind == "figure" and m.payload.get("text") == "SUPER NERD"]
check(_nerd, "Mt. Moon: the Super Nerd stands on the last floor")
_called = []
_mm._get_route_callback = lambda item: (lambda: _called.append(item.get("text")))
_nm, _d = beside(_mm, "figure") if _nerd else (None, None)
if _nm:
    _mm.mode, _mm.anim = "MAP", 0
    _mm.dialogue_box.visible = False
    _mm.step(*_d)
# (11-14: FireRed's item balls lie on B2F too: whichever figure you walk into, its own button)
check(_called and _called[0] in {m.payload.get("text") for m in _mm.run.floor.movers if m.kind == "figure"}, "walking into a figure does its button's action")
story.story_flags["received_pokedex_kanto"] = True
_badges = story.badges.get("KANTO", [])
story.badges["KANTO"] = []
for _ev in (_prog["KANTO_ROUTE_22"].get("on_enter_event") or []):
    story.story_flags.pop(_ev.get("flag_check") or "", None)
_r22 = kanto("KANTO_ROUTE_22", came="VIRIDIAN_CITY")
check(any(m.kind == "figure" and m.payload.get("action") == "ARRIVAL" for f in _r22.run.floors for m in f.movers),
      "Route 22: the rival waits on the map")
story.badges["KANTO"] = _badges

# fishing beside a pond, Headbutt beside a tree
story.inventory["OLD_ROD"] = 1
_fish = kanto("KANTO_ROUTE_12", came="LAVENDER_TOWN")
_f = _fish.run.floor
_pond = next(((x, y) for y in range(_f.h) for x in range(_f.w) if _f.tiles[y][x] in (core.WATER, core.SURF)
              and any(_f.walkable(x + dx, y + dy) and _f.tiles[y + dy][x + dx] == core.FLOOR and not _f.occupied(x + dx, y + dy) for dx, dy in core.DIRS)), None)
check(_pond is not None, "Route 12 (fishing): the sea beside its piers (11-11: FireRed's Silence Bridge)")
if _pond:
    _spot = next((_pond[0] + dx, _pond[1] + dy) for dx, dy in core.DIRS
                 if _f.walkable(_pond[0] + dx, _pond[1] + dy) and _f.tiles[_pond[1] + dy][_pond[0] + dx] == core.FLOOR and not _f.occupied(_pond[0] + dx, _pond[1] + dy))
    _fish.run.player = _spot
    _act = _fish._act_here()
    check(_act and _act[0] == "FISH" and any(b[1] == "FISH" for b in _fish._buttons()), "beside the water: a FISH button")
    _fish.mode, _fish.anim = "MAP", 0
    _fish.dialogue_box.visible = False
    _fish.fish_here()
    check(isinstance(g.current_state, WildBattleState) or _fish.dialogue_box.visible, "FISH: a bite (the route's own fishing)")
_sea = kanto("KANTO_ROUTE_20", came="KANTO_ROUTE_19")
check(_sea._on_surf() and _sea._beside("water") is not None, "at sea (surfing Route 20): you can fish anywhere")

# the buildings (Jordan, 11-05): Silph Co., the Rocket Hideout, the Pokemon Mansion
for _k in ("silph_co_cleared", "hideout_giovanni_defeated", "game_corner_cleared", "got_secret_key"):
    story.story_flags.pop(_k, None)
story.defeated_trainers.pop("SILPH_CITY", None)
_sil = kanto("SILPH_CITY", came="SAFFRON_CITY")
check(_sil.run.n_floors == 11 and _sil._floor_name(10) == "11F" and "SAFFRON_CITY" in _sil.run.floor.exits.values(),
      "Silph Co.: 1F (the way out) up to 11F (FireRed's floors)")
while _sil.run.index < 8:
    _sil._descend()
check(any(m.kind == "figure" and m.payload.get("text") == "NURSE" for m in _sil.run.floor.movers), "a nurse on 9F (FireRed's)")
while _sil.run.index < 10:
    _sil._descend()
check(any(m.kind == "trainer" and m.payload[1].get("name") == "Giovanni" for m in _sil.run.floor.movers),
      "Giovanni waits on 11F")
_hid = kanto("ROCKET_HIDEOUT", came="CELADON_GAME_CORNER")
while _hid.run.index < 3:
    _hid._descend()
check(_hid._floor_name(3) == "B4F" and any(m.kind == "figure" and m.payload.get("text") == "GIOVANNI"
                                          for m in _hid.run.floor.movers), "the Rocket Hideout: Giovanni on B4F")
story.story_flags["hideout_giovanni_defeated"] = True
_hid._sync_figures()
check(any(m.payload.get("text") == "SILPH SCOPE" for m in _hid.run.floor.movers if m.kind == "figure")
      and not any(m.payload.get("text") == "GIOVANNI" for m in _hid.run.floor.movers if m.kind == "figure"),
      "...beaten: the Silph Scope lies there")
story.story_flags.pop("hideout_giovanni_defeated", None)
from src.states.systems.town_services import GameCornerState as _GC
story.current_area_key = "CELADON_CITY"
_gc = _GC(g, None)
_gc.start_rocket_gauntlet()
check(type(g.current_state).__name__ == "AreaTransitionState" and g.current_state.next_area_key == "ROCKET_HIDEOUT",
      "the Game Corner's stairs lead down into the hideout")
_man = kanto("POKEMON_MANSION", came="CINNABAR_ISLAND")
_man._warp(2, 8, 3)  # (11-12: FireRed's four floors; he stands on 3F, where FireRed has him)
check(any(m.kind == "figure" and m.payload.get("text") == "BURGLAR SIMON" for m in _man.run.floor.movers)
      and any(m.kind == "wild" for f in _man.run.floors for m in f.movers), "the Pokemon Mansion: wild Pokemon, the Burglar with the Secret Key")
check(any(o.get("target_area") == "POKEMON_MANSION" for o in _prog["CINNABAR_ISLAND"]["explore_options"]),
      "Cinnabar's Pokemon Mansion button leads in")

# buildings are fixed and have no fog; the Game Corner is drawn (Jordan, 11-05)
_a1 = kanto("SILPH_CITY", came="SAFFRON_CITY")
_t1 = [row[:] for row in _a1.run.floor.tiles]
_a2 = kanto("SILPH_CITY", came="SAFFRON_CITY")
check(_a2.run.floor.tiles == _t1, "Silph Co.: the same floor on every visit")
check(len(_a2.run.floor.seen) == _a2.run.floor.w * _a2.run.floor.h and _a2.run.visible(1, 1), "...and no fog: the whole floor shows")
_r1 = kanto("GALAR_ROUTE_2", came="GALAR_ROUTE_1")  # (a made-up route map: our own ones are open; Route 48 was the example till it got its SoulSilver map)
check(_r1.run.fog and len(_r1.run.floor.seen) < _r1.run.floor.w * _r1.run.floor.h, "a route keeps its fog")
story.inventory["COIN_CASE"] = 1
story.story_flags["game_corner_poster"] = True  # (the switch behind the poster pushed: the stairs are open; the guard and the switch: frlg_body)
_gc = kanto("CELADON_GAME_CORNER", came="CELADON_CITY")
_f = _gc.run.floor
check(_f.decor and sum(1 for v in _f.decor.values() if v == "slot") >= 12 and "ROCKET_HIDEOUT" in _f.exits.values()
      and "CELADON_CITY" in _f.exits.values(), "the Game Corner: drawn, slot machines, the door and the poster")
_clerk = [m for m in _f.movers if m.kind == "figure" and m.payload.get("text") == "CLERK"]
check(_clerk and _f.tile(_clerk[0].x, _clerk[0].y + 1) == core.WALL and _f.decor.get((_clerk[0].x, _clerk[0].y + 1)) == "counter",
      "the clerk stands behind the counter")
_counter = next(t for t, v in _f.decor.items() if v == "counter" and _f.walkable(t[0], t[1] + 1))
_gc.run.player = (_counter[0], _counter[1] + 1)
_gc.mode, _gc.anim = "MAP", 0
_gc.dialogue_box.visible = False
check(_gc._act_here() and _gc._act_here()[0] == "TALK", "at the counter: TALK")
_gc._act_here()[1]()
from src.states.systems import GameCornerState as _GCS
check(isinstance(g.current_state, _GCS) and g.current_state.previous_state is _gc, "the clerk: the Game Corner's games, coins and prizes")
g.current_state.go_back()
check(g.current_state is _gc, "LEAVE: back on the Game Corner's floor")
_slot = next(t for t, v in _f.decor.items() if v == "slot" and any(_f.walkable(t[0] + dx, t[1] + dy) for dx, dy in core.DIRS))
_gc.run.player = next((_slot[0] + dx, _slot[1] + dy) for dx, dy in core.DIRS if _f.walkable(_slot[0] + dx, _slot[1] + dy))
check(_gc._act_here() and _gc._act_here()[0] == "PLAY SLOTS", "at a machine: PLAY SLOTS")
_gc.draw()

# Sevii (Jordan, 11-05: each region's maps checked against its games)
_sty = {k: _dg.recipe_for(g, k).get("style") for k in ("KINDLE_ROAD", "RUIN_VALLEY", "TANOBY_RUINS", "TREASURE_BEACH",
                                                       "DOTTED_HOLE", "LOST_CAVE", "BIRTH_ISLAND")}
check(set(_sty.values()) == {"field"},  # (every Sevii place is our own drawn map now, laid out from FireRed's map data, 11-11: a drawn map's recipe is a "field"; its look is its theme)
      f"Sevii's places are drawn maps of their own {_sty}")
story.story_flags["beat_champion"] = True
for _k in ("navel_rock_lugia", "navel_rock_ho_oh"):
    story.story_flags.pop(_k, None)
_nr = kanto("NAVEL_ROCK", came="ONE_ISLAND")
_where = {t: i for i in range(_nr.run.n_floors) for t in _nr.run.made(i).spots}
check(_nr.run.n_floors == 21 and _where.get("SEEK LUGIA") == 20 and _where.get("SEEK HO-OH") == 8,  # (FireRed's own floors, 11-11: the island, the cave, the fork, the long stairs, 4 flights up to the summit, 11 down to the base)
      f"Navel Rock: FireRed's 21 floors; Ho-Oh on the summit, Lugia in the base {_where}")
_me = kanto("MT_EMBER", came="KINDLE_ROAD")
check(_me.run.n_floors == 13, "Mt. Ember: FireRed's 13 floors: the mountain, the Summit Path's three, the summit, the Ruby Path's eight")



# free movement (Jordan, 11-05): no "two route actions" before a way out; only the story locks one
_r3 = kanto("KANTO_ROUTE_3", came="PEWTER_CITY")
check(_r3.rounds_completed == 0 and _r3._exit_block(_r3.exit_items["MT_MOON"], True) == "route", "Route 3, nothing done yet")
_r3._try_exit("MT_MOON")  # (straight into the cave now: its Pokemon Center is on Route 3, Jordan 11-07)
check(type(g.current_state).__name__ == "AreaTransitionState", "...and you can walk straight on to Mt. Moon")
_kb = story.badges.get("KANTO", [])
story.badges["KANTO"] = []
_r22b = kanto("KANTO_ROUTE_22", came="VIRIDIAN_CITY")
_r22b._try_exit("KANTO_ROUTE_23")
check(g.current_state is _r22b and _r22b.dialogue_box.visible, "a story lock still holds (Route 23 needs the eight badges)")
story.badges["KANTO"] = _kb


# walkable towns (Jordan, 11-06): the town on its Pokemon Journeys map, walked like a route
from src.states.overworld import CityState as _CS
from src.states.overworld.walk_town import WalkTownState as _WTS
g.walk_towns = True
g.walk_town_pos = None
story.story_flags["received_starter_kanto"] = True
story.story_flags["move_offer_kanto"] = True  # (the suites' save is Kanto's Champion: no move offer here)
story.current_area_key, story.last_area_key = "PALLET_TOWN", "KANTO_ROUTE_1"
_wt = _CS(g); g.change_state(_wt)




_tap_through(_wt)
check(isinstance(_wt, _WTS) and _wt.player[1] <= 2, f"Pallet Town: walked, in from Route 1 at the top ({_wt.player})")
_lab = next(t for t, k in _wt.doors.items() if k == "lab")
_wt.walk_goal = _lab
for _k in range(300):
    frames(_wt)
    if _wt.hover_menu_active or _wt.room:
        break
check(_wt.room == "lab" and any(o.get("target") == "professor_oak" for v in _wt.people.values() for o in v.get("any", [v])), f"walk into the Lab: inside it, Professor Oak there ({_wt.room})")   # (11-14: his options as one person)
_wt._go(None, "OUT:16,13")
g.walk_town_room = None
_n = min(t for t, v in _wt.exits.items() if v == "KANTO_ROUTE_1")
_wt.player = _wt.anim_from = (_n[0], _n[1] + 1)
_wt.anim = 0
_wt.step(0, -1)
check(type(g.current_state).__name__ == "AreaTransitionState", "walk off the top: on to Route 1")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "VIRIDIAN_CITY", "KANTO_ROUTE_1"
_wt = _CS(g); g.change_state(_wt)
_tap_through(_wt)
_r1y = max(y for (x, y), v in _wt.exits.items() if v == "KANTO_ROUTE_1")
check(abs(_wt.player[1] - _r1y) <= 1 and set(_wt.doors.values()) >= {"center", "mart", "gym"},
      "Viridian City: in from Route 1 at its south gate; its Center, Mart and Gym have doors")
_wt.walk_goal = next(t for t, k in _wt.doors.items() if k == "center")
for _k in range(600):
    frames(_wt)
    if g.current_state is not _wt or _wt.room:
        break
check(_wt.room == "center" and g.current_state is _wt, f"walk into the Pokemon Center: inside its room ({_wt.room}, {_wt.player})")
_wt.player = _wt.anim_from = (7, 4); _wt.anim = 0; _wt.walk_goal = None
_wt.step(0, -1)
_pc = g.current_state
check(_pc is _wt and _wt.npc_active and bool(_wt.npc_dialogue), "...talk to the nurse across her counter: she heals you from the map, no screen of the Center's own")
_wt.end_npc_interaction()
_spot = _wt.player
g.change_state(_wt)
check(_wt.player == _spot and _wt.room == "center" and _wt.action_menu not in g.ui_manager.elements, "...out of it again: where you were, no menu bar")
_wt._go(None, "OUT:26,26")
g.walk_town_room = None


# Routes 12-18, Fuchsia and the Safari Zone (Jordan, 11-07)
_inv = dict(story.inventory)
story.inventory.pop("POKE_FLUTE", None)
_r16 = kanto("KANTO_ROUTE_16", came="CELADON_CITY")
check(_r16._boss_spot() == (31, 13) and _r16.run.floor.exits.get((31, 13)) == "BOSS",
      "Route 16: Snorlax asleep on the road where FireRed has him, before the gatehouse (11-11; the Bicycle is asked for at the head of the slope)")
story.inventory.pop("HM_FLY", None)
story.story_flags.pop("got_hm_fly_kanto", None)
_r16.run.floor.movers = [m for m in _r16.run.floor.movers if m.kind == "figure"]  # (the quiet house is a room now: in by its door, up to the girl)
_r16.run.player = (10, 6); _r16.anim = 0; _r16.anim_from = (10, 6)
_r16._handle(_r16.run.step(0, -1))
_r16.run.player = (4, 3); _r16.anim = 0; _r16.anim_from = (4, 3)
_r16._handle(_r16.run.step(0, -1))
talk(_r16)
check(story.inventory.get("HM_FLY") == 1, "...the quiet house: HM Fly")
story.inventory.clear()
story.inventory.update(_inv)
for _k in ("heard_warden_teeth", "got_hm_strength_kanto", "got_good_rod_kanto", "got_gold_teeth"):
    story.story_flags.pop(_k, None)
for _k in ("GOLD_TEETH", "HM_STRENGTH", "GOOD_ROD"):
    story.inventory.pop(_k, None)
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "FUCHSIA_CITY", "KANTO_ROUTE_15"
_fu = _CS(g); g.change_state(_fu); _tap_through(_fu)
check({"warden", "brother", "gym", "center", "mart", "safari"} <= set(_fu.doors.values()) and set(_fu.exits.values()) == {
    "KANTO_ROUTE_15", "KANTO_ROUTE_18", "KANTO_ROUTE_19"}, f"Fuchsia: walked, its doors and three ways out (the Safari Zone through its entrance house, Kanto batch 17) {sorted(set(_fu.doors.values()))} {sorted(set(_fu.exits.values()))}")
def _talk_inside(t, kind):  # (11-11: their houses are rooms now: in by the door, talk to whoever is there, out again)
    door = max((d for d, k in t.doors.items() if k == kind), key=lambda d: d[1])
    t._enter(door)
    for spot in list(t.people):
        t.player = t.anim_from = (spot[0], spot[1] + 1); t.anim = 0; t.walk_goal = None
        t.step(0, -1); _tap_through(t)
    t._go(None, "OUT:%d,%d" % door); g.walk_town_room = None


_talk_inside(_fu, "warden")
_talk_inside(_fu, "brother")
check(story.story_flags.get("heard_warden_teeth") and story.inventory.get("GOOD_ROD") == 1,
      "the Warden has lost his teeth; the Fishing Guru's brother: the Good Rod")
_sz = kanto("SAFARI_ZONE", came="FUCHSIA_CITY")
check([_sz.zones[_sz._zone_index(0, x, y)] for x, y in ((70, 70), (130, 60), (50, 20), (20, 60))] == ["center", "east", "north", "west"]
      and story.story_flags.get("zone_SAFARI_ZONE") == "center", "the Safari Zone: one map, four areas; in at the Center")
_sz.run.player = (130, 60)
_sz._note_area()
check(story.story_flags.get("zone_SAFARI_ZONE") == "east", "...walk into the East: its Pokemon")
_tt = [m for m in _sz.run.floor.movers if m.kind == "figure" and m.payload.get("text") == "GOLD TEETH"]
check(_tt and _tt[0].x < 53, "the Gold Teeth, in the West")
if _tt:
    _sz._get_route_callback(_tt[0].payload)()
    talk(_sz)
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "FUCHSIA_CITY", "SAFARI_ZONE"
_fu = _CS(g); g.change_state(_fu); _tap_through(_fu)
if getattr(_fu, "room", None) == "safari":   # (back from the Safari Zone you're in its entrance house: out to the street first. Kanto batch 17)
    _fu._go(None, "OUT:24,5"); g.walk_town_room = None
_talk_inside(_fu, "warden")
check(story.inventory.get("HM_STRENGTH") == 1 and not story.inventory.get("GOLD_TEETH"), "the Warden: HM Strength for his teeth")

# the sea loop (Jordan, 11-07): Routes 19-21 surfed, Seafoam's boulders (Strength and the slide puzzle), Cinnabar
from src.states.slide_puzzle import SlidePuzzleState, numbers
import random as _rr
check(numbers(1, _rr.Random(1)) == (3, list(range(1, 9))) and numbers(3, _rr.Random(1))[0] == 4
      and numbers(2, _rr.Random(1))[1][:2] == [2, 4], "the slide puzzle: 1-8 at Poke Ball, by 2s at Great, 4 x 4 from Ultra")
_inv = dict(story.inventory)
story.inventory.pop("HM_SURF", None); story.inventory.pop("HM_STRENGTH", None)
_kb = list(story.badges.get("KANTO", []))   # (Kanto, 11-16: FireRed's HM badges, hms.USE_BADGE; from here on these tests are about the maps)
story.badges["KANTO"] = _kb + [b for b in ("RAINBOW", "SOUL") if b not in _kb]
_r19 = kanto("KANTO_ROUTE_19", came="FUCHSIA_CITY")
_f = _r19.run.floor
_bch = next((x, y) for y in range(_f.h) for x in range(_f.w) if _f.tile(x, y) == core.FLOOR
            and _f.tile(x, y + 1) == core.SURF and not _f.occupied(x, y) and not _f.occupied(x, y + 1))
_r19.run.player = _r19.anim_from = _bch
_r19.anim = 0
_r19.step(0, 1)
check(_r19.run.player == _bch and "Surf" in (_r19.toast or ""), "Route 19: the open sea needs Surf")
story.inventory["HM_SURF"] = 1
story.badges["KANTO"] = [b for b in story.badges["KANTO"] if b != "SOUL"]
_r19.step(0, 1)
check(_r19.run.player == _bch, "...nor with HM Surf alone: Kanto's Surf wants the Soul Badge (FireRed; Jordan 11-16)")
story.badges["KANTO"] = story.badges["KANTO"] + ["SOUL"]
_r19.step(0, 1)
_r19.draw()
check(_r19._on_surf() and _r19._beside("water") is not None, "...with HM Surf and the Soul Badge: out on the water (riding; fish anywhere)")
_r20 = kanto("KANTO_ROUTE_20", came="KANTO_ROUTE_19")
check(sum(1 for v in _r20.run.floor.exits.values() if v == "SEAFOAM_ISLANDS") == 2 and _r20._on_surf(),
      "Route 20: Seafoam's two mouths; in from Route 19, surfing")
for _k in [k for k in story.story_flags if k.startswith("boulder_SEAFOAM")]:
    story.story_flags.pop(_k)
_sf = kanto("SEAFOAM_ISLANDS", came="KANTO_ROUTE_20")
_bd = next(t for t, v in _sf.run.floor.decor.items() if str(v).startswith("boulder:"))
_sf.run.player, _sf.facing = (_bd[0], _bd[1] + 1), (0, -1)
_sf._read_sign()
check(_sf.dialogue_box.visible and "Strength" in " ".join(_sf.dialogue_box.text_lines), "Seafoam: a boulder (no Strength: it won't move)")
talk(_sf)
story.inventory["HM_STRENGTH"] = 1
_sf._read_sign()
talk(_sf)
_pz = g.current_state
check(isinstance(_pz, SlidePuzzleState), "...with Strength: the slide puzzle")
_pz.board = list(range(_pz.side * _pz.side - 1)) + [None]
_n = len(_pz.board)
_pz.board[_n - 2], _pz.board[_n - 1] = None, _n - 2
_pz.handle_events([pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT)])
for _k in range(90):
    _pz.update()
check(g.current_state is _sf and _sf.run.floor.walkable(*_bd), "...solved: the boulder slides aside")
talk(_sf)
_sf2 = kanto("SEAFOAM_ISLANDS", came="KANTO_ROUTE_20")
_sf2.step(0, 1)
check(_sf2.run.floor.walkable(*_bd), "...and stays aside")
story.inventory.clear(); story.inventory.update(_inv)
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "CINNABAR_ISLAND", "KANTO_ROUTE_21"
_ci = _CS(g); g.change_state(_ci); _tap_through(_ci)
check({"fossil", "gym", "center", "mart"} <= set(_ci.doors.values())
      and {"KANTO_ROUTE_20", "KANTO_ROUTE_21", "CINNABAR_VOLCANO", "POKEMON_MANSION"} <= set(_ci.town_map.get("exits", {}).values()),
      f"Cinnabar Island: walked; Mansion, Lab, Gym, Center, Mart, harbor; Surf north and east; the volcano ({sorted(set(_ci.doors.values()))}, {[str((o or {}).get('text')) for o in _ci._people().values()]}, {sorted(set(_ci.town_map.get('exits', {}).values()))})")

# the rest of Kanto (Jordan, 11-07): Saffron, the Power Plant, Route 23, Victory Road, Indigo Plateau, Cerulean Cave
_inv = dict(story.inventory)
story.inventory.update({"HM_SURF": 1, "HM_STRENGTH": 1})
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "SAFFRON_CITY", "KANTO_ROUTE_5"
_sa = _CS(g); g.change_state(_sa); _tap_through(_sa)
check({"station", "dojo", "gym", "copycat", "mart", "center"} <= set(_sa.doors.values()) and {
    "KANTO_ROUTE_5", "KANTO_ROUTE_6", "KANTO_ROUTE_7", "KANTO_ROUTE_8", "SILPH_CITY"} <= set(_sa.exits.values()),
      "Saffron: walked; the Magnet Train, the Dojo, the Gym, Copycat's, a gatehouse each side, Silph Co.")
_pp = kanto("POWER_PLANT", came="KANTO_ROUTE_10")
_z = [m for m in _pp.run.floor.movers if m.kind == "figure" and m.payload.get("text") == "CHALLENGE ZAPDOS"]
check(_z and (_z[0].x, _z[0].y) == (5, 11) and (_pp.run.floor.w, _pp.run.floor.h) == (49, 40), "the Power Plant: FireRed's own 49 x 40; Zapdos in its north-west room, where FireRed has it")
_r23 = kanto("KANTO_ROUTE_23", came="KANTO_ROUTE_22")
_gds = {m.payload.get("text"): m for m in _r23.run.floor.movers if m.kind == "figure"}
check(sum(1 for t in _gds if t.endswith("BADGE GUARD")) == 8 and _gds["BOULDER BADGE GUARD"].y > _gds["EARTH BADGE GUARD"].y
      and any(_r23.run.floor.tile(x, y) == core.SURF for y in range(_r23.run.floor.h) for x in range(_r23.run.floor.w)),
      "Route 23: eight badge guards (Boulder first), ponds to Surf")
_vr = kanto("VICTORY_ROAD", came="KANTO_ROUTE_23")
_vb = [t for t, v in _vr.run.floor.decor.items() if str(v).startswith("boulder:")]
_vr._warp(1, 1, 9)
check("KANTO_ROUTE_23" in _vr.run.floor.exits.values() and _vr.run.n_floors == 3,
      "Victory Road: FireRed's three floors (11-12); 2F's way out leads to Route 23's forecourt, below Indigo Plateau")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "INDIGO_PLATEAU", "VICTORY_ROAD"
_ip = _CS(g); g.change_state(_ip); _tap_through(_ip)
_ipd = set(_ip.doors.values())  # (the town's doors, before you step into the lobby)
_ip._enter(next(t for t, k in _ip.doors.items() if k == "league"))
check({"league", "johto"} <= _ipd and _ip.room == "lobby" and {o.get("text") for o in _ip.people.values()} >= {"Heal", "Shop"}
      and "ROOM:league_lorelei" in _ip.town_map["rooms"]["lobby"].get("exits", {}).values(),
      "Indigo Plateau: the League's door, the ride to Johto; in its lobby the nurse, the clerk and the Elite Four's door (11-12: FireRed's lobby)")
_ip._go(None, "OUT:11,6"); g.walk_town_room = None
_cc = kanto("CERULEAN_CAVE", came="CERULEAN_CITY")
while _cc.run.index < 2:
    _cc._descend()
check(any(m.kind == "figure" and m.payload.get("text") == "CHALLENGE MEWTWO" for m in _cc.run.floor.movers),
      "Cerulean Cave: Mewtwo on B1F")
story.inventory.clear(); story.inventory.update(_inv)
g.walk_towns = False

print(f"##### {fails} failures")
