# The Orange Islands' walkable maps from Orange Islands Beta 5.7 (11-17): every built map opened the way a player meets it,
# on 5.7's own picture, every way out known to the story data, everything reachable; then each batch's own things.
#   bash dev/checks/run.sh orange_maps
import json
import os
from collections import deque
from src.states.overworld import PlayState, CityState
from src.states.overworld.walk_town import WalkTownState as _WTS
from src.states.overworld.dungeon import DungeonState
from src.states.menus import region_opening_state, RegionSelectionState as _RSS
from src.states import overworld as ow

fails = []


def check(c, m):
    print(("   ok  " if c else "   FAIL ") + m)
    if not c:
        fails.append(m)


g.dungeon_routes = True; g.walk_towns = True
_tm = json.load(open("assets/town_maps.json", encoding="utf-8"))
_area = g.loader.area_data["STORY_PROGRESSION"]
import importlib.util as _u
_spec = _u.spec_from_file_location("oi57", "dev/builders/town_maps/oi57.py")
_oi = _u.module_from_spec(_spec); _spec.loader.exec_module(_oi)
BUILT = list(_oi.ORANGE)
story.enter_region("ORANGE")
story.story_flags.update({"received_starter_orange": True, "orange_ivy_met": True})


def frames(n):
    for _ in range(n):
        g.current_state.update(); g.current_state.draw()


def tap(st, n=600):
    for _ in range(n):
        if getattr(st, "npc_active", False):
            st.handle_events([pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(640, 600))])
        elif getattr(st, "dialogue_box", None) is not None and st.dialogue_box.visible:
            st.dialogue_box.advance()
        else:
            return
        st.update(); st.draw()


def open_map(key, came):
    story.current_area_key, story.last_area_key = key, came
    g.walk_town_pos = None; g.walk_town_room = None
    st = CityState(g) if _area[key].get("area_type") == "town" else None
    if st is None or not isinstance(st, _WTS):
        st = PlayState(g); g.states["play"] = st
    g.change_state(st)
    frames(2)
    tap(g.current_state)
    return g.current_state


print("1) every built Orange map")
for key in BUILT:
    m = _tm[key]
    a = _area.get(key, {})
    check(a.get("region") == "ORANGE", f"{key}: an Orange area")
    _parts = m["floors"] if m.get("floors") else [m]
    targets = set(v for f in _parts for v in f.get("exits", {}).values() if not str(v).startswith(("ROOM:", "OUT:")))
    known = {o.get("target_area") or o.get("target") for o in a.get("travel_options", []) + a.get("route_menu", []) + a.get("explore_options", [])}
    check(targets <= known, f"{key}: every way out on the map is a way out in the story data {sorted(targets - known)}")
    came = sorted(targets)[0] if targets else key
    st = open_map(key, came)
    is_town = isinstance(st, _WTS)
    w, h = (st.w, st.h) if is_town else (st.run.floor.w, st.run.floor.h)
    _ha = _parts[st.run.index]["art"] if (not is_town and m.get("floors")) else m["art"]
    check((w, h) == (len(_ha[0]), len(_ha)) and (is_town or isinstance(st, DungeonState)),
          f"{key}: opens on its 5.7 map ({w} x {h}, {'town' if is_town else 'route'}), in from {came}")
    check(all("oi_ground/" in json.dumps(f.get("roofs", {})) for f in _parts), f"{key}: drawn from 5.7's own picture (every floor)")
    for rname, room in (m.get("rooms") or {}).items():
        outs = [v for v in room.get("exits", {}).values() if str(v).startswith(("OUT:", "ROOM:"))]
        _own = "oi_ground/" in json.dumps(room.get("roofs", {})) or (key, rname) in (("VALENCIA_ISLAND", "home"), ("VALENCIA_ISLAND", "home_2"))
        check(outs and _own, f"{key}@{rname}: 5.7's own room (Mom's home: Kanto's, 11-18), with its way out {outs}")
        st = open_map(key, came)
        if is_town:
            st._go(rname, ""); frames(2); tap(st)
            check(st.room == rname, f"{key}@{rname}: you can go in ({st.room})")
        else:   # (a room on a route: a floor of the area after its own, joined to its door: in by the door, 11-17)
            from src.states.overworld.dungeon import with_rooms as _wr
            _rf = _wr(m)["room_floors"].get(rname)
            _door = next((d for d, r in (m.get("inside") or {}).items() if r == rname), None)
            if _rf is not None and _door:
                _dx, _dy = (int(v) for v in _door.split(","))
                for _b in m.get("barred") or []:   # (a door shut till the story opens it, Hamlin's till the Electrode are moved: opened)
                    _fc = ((_b.get("until") or {}).get("flag_condition") or "").split()
                    if [_dx, _dy] in _b.get("tiles", []) and len(_fc) == 1:
                        story.story_flags[_fc[0]] = True
                st.run.player = (_dx, _dy + 1); st.anim = 0; st.step(0, -1); frames(30); tap(st)
                check(st.run.index == _rf, f"{key}@{rname}: you can go in at its door (floor {st.run.index}, its room is floor {_rf})")

print("2) batch 1: Valencia's opening, played")
if "VALENCIA_ISLAND" in BUILT:
    for f in [k for k in story.story_flags if k.startswith("orange_") or k in ("received_starter_orange", "has_orange_starter")]:
        story.story_flags.pop(f, None)
    story.player_team = []
    story.starting_region = "ORANGE"
    st = region_opening_state(g, "ORANGE")
    check(st is not None, "a new Orange game opens on the walked map (starter_in_town)")
    g.change_state(st)
    for _ in range(600):
        if isinstance(g.current_state, _WTS):
            break
        c = g.current_state
        if getattr(c, "dialogue_box", None) is not None and getattr(c.dialogue_box, "visible", False):
            c.dialogue_box.advance()
        c.update(); c.draw()
    t = g.current_state
    check(isinstance(t, _WTS) and t.area_key == "VALENCIA_ISLAND" and t.room is None and tuple(t.player) == (24, 60),
          f"you start at Valencia's airport, where 5.7's blimp lands you ({getattr(t, 'area_key', None)}, {getattr(t, 'player', None)})")
    _ppl = t._people()
    check((25, 71) in _ppl and _ppl[(25, 71)].get("text") == "Blimp clerk" and (42, 6) in _ppl,
          "the blimp clerk (5.7's 17,31 of the airport) and the Old Rod fisherman (42,6) on 5.7's spots")
    # the Old Rod
    story.inventory.pop("OLD_ROD", None)
    o = next(o for o in _area["VALENCIA_ISLAND"]["explore_options"] if o["text"] == "Old Rod fisherman")
    ow._run_story_event(t, o["event"], t._check_menu_condition, lambda l: None)
    check(story.inventory.get("OLD_ROD") == 1, "the fisherman gives the Old Rod (5.7's gift), once")
    lab = _tm["VALENCIA_ISLAND"]["rooms"]["lab"]
    _sp = [(x, y) for y, r in enumerate(lab["art"]) for x, c in enumerate(r) if c == "N"]
    check((6, 3) in _sp and (11, 6) in _sp, "Ivy (6,3) and Brock (11,6) stand on 5.7's spots in the lab")
    check(any(b.get("tiles") == [[9, 4]] for b in lab.get("barred", [])), "the GS Ball lies on the lab table (5.7's 9,4): looked at, no item")
    park = _tm["VALENCIA_PARK"]
    check(park.get("hidden") == {"9,37": "PARALYZE_HEAL", "44,9": "ANTIDOTE"}, f"Valencia Park's two hidden items, 5.7's ({park.get('hidden')})")
    pp = _tm["TANGELO_JUNGLE"]
    check(pp.get("arrive", {}).get("VALENCIA_ISLAND") == [35, 7], "the parachute lands you at 5.7's 35,7 in Pokémon Park")
    check(len(pp.get("trainer_spots", [])) == 4 and all(t.get("levels") for t in _area["TANGELO_JUNGLE"]["trainer_pool"]),
          "Pokémon Park's four 5.7 trainers, on its tiles, with fixed levels")
    _forms = [s for s in g.loader.area_data.get("ORANGE_VALENCIA_PARK_PERCENTAGES", {}) if int(s) >= 9500]
    check(len(_forms) == 17, f"our 17 Valencia forms kept as extras in Valencia Park ({len(_forms)})")
    check(not any("CROSS" in json.dumps(v) for k, v in _area.items() if k in BUILT), "no rival Cross in the built areas")
print("3) Jordan's answers of 11-17 (batches 1-2)")
cfg = story.get_region_start("ORANGE")
check(cfg.get("starter_level") == 10, "Ivy's partner starts at Lv 10 (REGION_START starter_level)")
from src.states.menus import StarterSelectionState as _SSS
story.story_flags.pop("received_starter_orange", None)
_s = _SSS(g, starter_ids=cfg["starters"], region="ORANGE"); _s.load_starters(); _s.selected_idx = 0; _s.complete_selection()
check(story.player_team and story.player_team[0].level == 10, f"...and the partner you take is Lv 10 ({story.player_team[0].level if story.player_team else None})")
check("ORANGE_ROUTE_52" not in _area and not any("ORANGE_ROUTE_52" in json.dumps(a) for a in _area.values()), "Route 52 is gone, and nothing leads there")
check(cfg.get("arrive_room") == [None, 24, 60], "a Kanto player moving here lands at the airport (arrive_room)")
_v = _area["VERMILLION_CITY"]
check(any(o.get("move_region") == "ORANGE" and "Blimp" in o["text"] for o in _v["travel_options"])
      and not any("S.S. Anne to the Orange" in o.get("text", "") for o in _v["travel_options"]), "Kanto's way to Orange is a blimp, not the S.S. Anne")
import pygame as _pg
_top = _pg.image.load("assets/tiles/oi_top/o_val.png")
check(_top.get_at((296 + 64, 960 + 32)).a > 0 and _top.get_at((296 + 64, 1056 + 32)).a > 0, "the two moored blimps are drawn on Valencia's layer over you")
print("4) batch 3: Mikan Gym, Cissy's tests then her battle")
if "MIKAN_ISLAND" in BUILT:
    from src import minigames as _mg
    from src.minigames.orange import CissyChallenge as _CC
    check(_mg.GYM_GAMES.get("MIKAN_ISLAND") == "cissy" and _mg.pick(g, "MIKAN_ISLAND", [117, 9]) is _CC, "Mikan Gym's challenge is Cissy's own (always)")
    _won = []
    c = _CC(g, lambda w: _won.append(w), level=0, seed=1)
    c._play()
    for _ in range(4000):   # (the target test: hit each target as it pops up)
        if c.targets:
            t = c.targets[0]; c.on_tap((t[0], t[1]))
        c.frames += 1; c.step()
        if c.round == 2 or c.phase != "PLAY":
            break
    check(c.round == 2 and c.phase == "PLAY", f"round 1: hitting {c.HITS} targets moves on to the Lapras race ({c.round}, {c.phase})")
    for i in range(6000):   # (the race: swim on, dodge a rock coming up in your lane)
        ahead = [r for r in c.rocks if r[0] == c.lane and 0 < r[1] - c.me < 2]
        if ahead:
            c.on_key(pygame.K_DOWN if c.lane < c.LANES - 1 else pygame.K_UP)
        if i % 4 == 0:
            c.on_key(pygame.K_SPACE)
        c.frames += 1; c.step()
        if c.phase != "PLAY":
            break
    check(c.phase == "WON", f"round 2: Lapras reaches the buoy before Seadra ({c.phase}, {round(c.me)} vs {round(c.foe)})")
    c2 = _CC(g, lambda w: None, level=0, seed=2); c2._play()
    for _ in range(4000):
        c2.frames += 1; c2.step()
        if c2.phase != "PLAY":
            break
    check(c2.phase == "LOST", "doing nothing loses the target test (targets get away)")
    L = _area["MIKAN_ISLAND"]["gym"]["leader"]
    check(L["team"] == [117, 9] and L["levels"] == [20, 22] and L["badge_reward"] == "CORAL_EYE" and L["rewards"].get("TM011") == 1,
          f"Cissy: 5.7's Seadra 20 and Blastoise 22, the Coral-Eye Badge and TM Water Pulse ({L['team']} {L['levels']})")
    gym = _tm["MIKAN_ISLAND"]["rooms"]["gym"]
    _sp = [(x, y) for y, r in enumerate(gym["art"]) for x, ch in enumerate(r) if ch == "N"]
    check(set(_sp) == {(8, 9), (1, 12), (13, 9), (4, 15), (12, 13)}, f"Cissy and her four Gym trainers on 5.7's tiles ({sorted(_sp)})")
print("5) batches 7-10: Jordan's 11-17 answers and Navel / Grapefruit / Moro, played")
from src.states.systems.pick_list import PickListState as _PLS


def _play_event(key, text, pick=None, n=300):
    """Run an option's event on its area's map, the way a player meets it: dialogue advanced, a pick list answered."""
    st = open_map(key, key)
    o = next(o for o in _area[key].get("explore_options", []) + _area[key].get("route_menu", []) if o.get("text") == text)
    said = []
    ow._run_story_event(st, o["event"], getattr(st, "_check_menu_condition", None) or (lambda c: st._check_route_condition(c, False)),
                        lambda l: said.extend(l))
    for _ in range(n):
        c = g.current_state
        if isinstance(c, _PLS):
            c.pick(pick)
            continue
        if getattr(c, "dialogue_box", None) is not None and getattr(c.dialogue_box, "visible", False):
            c.dialogue_box.advance()
        elif getattr(c, "npc_active", False):
            tap(c, 5)
        else:
            break
        c.update(); c.draw()
    return said


if "BAY_CAVE" in BUILT:
    for fossil in ("HELIX_FOSSIL", "DOME_FOSSIL"):
        story.story_flags.pop("got_fossil_bay_cave", None)
        story.inventory.pop("HELIX_FOSSIL", None); story.inventory.pop("DOME_FOSSIL", None)
        _play_event("BAY_CAVE", "FOSSIL", pick=fossil)
        other = "DOME_FOSSIL" if fossil == "HELIX_FOSSIL" else "HELIX_FOSSIL"
        check(story.inventory.get(fossil) == 1 and not story.inventory.get(other) and story.story_flags.get("got_fossil_bay_cave") == fossil,
              f"Bay Cave: you pick the fossil you found, and get that one only ({fossil}: {story.inventory.get(fossil)}, {other}: {story.inventory.get(other)})")
    story.story_flags.pop("got_fossil_bay_cave", None); story.inventory.pop("DOME_FOSSIL", None)
    _play_event("BAY_CAVE", "FOSSIL", pick=None)
    check(not story.story_flags.get("got_fossil_bay_cave") and not story.inventory.get("HELIX_FOSSIL") and not story.inventory.get("DOME_FOSSIL"),
          "...backing out of the question leaves the fossil in the rock for later")
    _fk = _area["FUKUHARA_ISLAND"]
    check(not any(o.get("action") == "HEAL" for o in _fk.get("route_menu", []) + _fk.get("explore_options", [])),
          "Fukuhara's Nurse Joy doesn't heal (Jordan 11-17: she only runs the dig, as 5.7)")
    for fossil in ("HELIX_FOSSIL", "DOME_FOSSIL"):   # (the Old Amber side mission works with either fossil)
        story.story_flags.update({"orange_fukuhara_pickaxe": True, "got_fossil_bay_cave": fossil})
        story.story_flags.pop("orange_fukuhara_amber", None); story.inventory.pop("OLD_AMBER", None)
        _play_event("FUKUHARA_ISLAND", "Nurse Joy")
        check(story.inventory.get("OLD_AMBER") == 1, f"...and Nurse Joy's Old Amber follows with the {fossil.replace('_', ' ').title()}")
if "MT_NAVEL" in BUILT:
    _d = next(o for o in _area["MT_NAVEL"]["route_menu"] if o["text"] == "Danny")["event"]["battle"]
    check(_d["team"] == [74, 101, 67, 123, 31] and _d["levels"] == [30, 30, 32, 32, 35] and _d["badge_reward"] == "SEA_RUBY"
          and _d["rewards"].get("TM135") == 1, f"Danny atop Navel Mountain: 5.7's five (to Nidoqueen 35), the Sea Ruby Badge and TM Ice Beam ({_d['team']})")
    _mt = _tm["MT_NAVEL"]
    check(sum(r.count("/") for r in _mt["art"]) >= 8, "the climb: 5.7's climbable faces drawn for the Climb Kit")
    story.story_flags.pop("orange_danny_badge", None)
    check(_play_event("MT_NAVEL", "Cable car (foot)") and g.current_state.__class__.__name__ != "AreaTransitionState" and getattr(g, "arrive_floor", None) is None,
          "the cable car waits until you've beaten Danny (5.7: reach the top on foot)")
    story.story_flags["orange_danny_badge"] = True
    _play_event("MT_NAVEL", "Cable car (foot)")
    _rooms = list(_mt.get("rooms") or {})
    check(_rooms[:2] == ["cable", "cable_2"] and getattr(g.current_state, "area_key", None) == "MT_NAVEL"
          and getattr(getattr(g.current_state, "run", None), "index", None) == 2, f"after the badge it carries you up to the top station ({_rooms}, floor {getattr(getattr(g.current_state, 'run', None), 'index', None)})")
    _nv = _area["NAVEL_ISLAND"]
    check(not any(o.get("action") in ("GYM", "SHOP") for o in _nv["explore_options"]), "Navel: no Gym building and no Mart, as 5.7")
    _tr = next(o for o in _nv["explore_options"] if o["text"] == "Trader")["event"]
    check(_tr["trade"] == {"want": 124, "give": 126, "item": "CHARCOAL"}, "Navel's trader: 5.7's trade, a Magmar holding Charcoal for a Jynx")
if "MORO_ISLAND" in BUILT:
    story.story_flags.pop("orange_danny_badge", None)
    st = open_map("MORO_ISLAND", "ORANGE_ROUTE_59_SOUTH")
    _pp = st._people() if hasattr(st, "_people") else {}
    check(all((x, 6) in _pp for x in (30, 31, 32)), "Moro: three kids sit on the north stairs before Danny's badge (5.7's gate)")
    story.story_flags["orange_danny_badge"] = True
    st = open_map("MORO_ISLAND", "ORANGE_ROUTE_59_SOUTH")
    _pp = st._people() if hasattr(st, "_people") else {}
    check(not any((x, 6) in _pp for x in (30, 31, 32)) and (42, 24) in _pp, "...and move to the east beach after it")
    for fossil, sp in (("HELIX_FOSSIL", 138), ("DOME_FOSSIL", 140), ("OLD_AMBER", 142)):
        story.story_flags.pop("orange_moro_fossil", None); story.story_flags.pop("orange_moro_amber", None)
        story.inventory.pop("HELIX_FOSSIL", None); story.inventory.pop("DOME_FOSSIL", None); story.inventory.pop("OLD_AMBER", None)
        story.inventory[fossil] = 1
        before = len([p for p in story.player_team if p])
        story.current_area_key = "MORO_ISLAND"
        _play_event("MORO_ISLAND", "Fossil researcher")
        got = [p.id for p in story.player_team if p][before:] or [getattr(p, "id", None) for p in (story.pc_boxes[-1] if getattr(story, "pc_boxes", None) else [])][-1:]
        check(not story.inventory.get(fossil) and sp in got, f"the Museum's researcher revives the {fossil.replace('_', ' ').title()} ({got})")
if "SEVEN_GRAPEFRUITS" in BUILT:
    story.story_flags.pop("orange_grapefruit_snorlax", None); story.inventory.pop("SILK_SCARF", None); story.story_flags.pop("got_silk_scarf_grapefruit", None)
    _play_event("SEVEN_GRAPEFRUITS", "Ruby")
    check(not story.inventory.get("SILK_SCARF"), "Grapefruits: Ruby's Silk Scarf waits for the Snorlax battle")
    story.story_flags["orange_grapefruit_snorlax"] = True
    _play_event("SEVEN_GRAPEFRUITS", "Ruby")
    check(story.inventory.get("SILK_SCARF") == 1, "...and comes after it")
    check(_area["SEVEN_GRAPEFRUITS"]["area_boss"]["id"] == 143 and _area["SEVEN_GRAPEFRUITS"]["area_boss"]["level"] == 30, "the Snorlax: 5.7's wild Lv 30")
print("6) Jordan's batch 9-10 answers (11-17): ride scenes, Danny's picture, the snowy mountain, the sailor's TM, extras dropped")
from src.states.overworld.area_transition import AreaTransitionState as _ATS, ride_scene as _ride_scene
import os as _os
_shots = _os.environ.get("ORANGE_RIDE_SHOTS")   # (a folder: each ride scene's middle frame saved there, for the check-in)
for _name in ("oi_blimp", "oi_parachute", "oi_cable_up", "oi_cable_down"):
    _legs = _ride_scene(g, _name)
    check(bool(_legs), f"ride scene {_name}: its pictures load ({len(_legs or [])} legs)")
    if not _legs:
        continue
    story.current_area_key = "VALENCIA_ISLAND"
    _t = _ATS(g, "MT_NAVEL" if "cable" in _name else "VALENCIA_ISLAND", initial_message=["..."], ride=_name)
    g.change_state(_t)
    _total = sum(l["frames"] for l in _legs)
    _mid = None
    for _i in range(_total + 400):
        if g.current_state is not _t:
            break
        if _t.dialogue_box.visible and not _t.dialogue_box.is_finished:
            _t.dialogue_box.advance()
        _t.update(); _t.draw()
        if _shots and _i in (_legs[0]["frames"] // 2, _total - _legs[-1]["frames"] // 2):
            pygame.image.save(g.screen, _os.path.join(_shots, f"ride_{_name}_{_i}.png"))
    check(g.current_state is not _t, f"...and plays through to the place ({type(g.current_state).__name__})")
_vb = [o["event"] for o in _area["VALENCIA_ISLAND"]["explore_options"] if o.get("text") in ("Blimp clerk", "Kanto blimp clerk")]
check([e.get("ride") for e in _vb] == ["oi_parachute", "oi_blimp"], f"Valencia's blimps play 5.7's flight (the parachute drop; to Kanto) ({[e.get('ride') for e in _vb]})")
check(story.get_region_start("ORANGE").get("arrive_ride") == "oi_blimp", "a Kanto player arrives on the blimp flight")
if "MT_NAVEL" in BUILT:
    _cab = [o["event"].get("ride") for o in _area["MT_NAVEL"]["route_menu"] if o["text"].startswith("Cable car")]
    check(_cab == ["oi_cable_up", "oi_cable_down"], f"Navel's cable car rides up and down ({_cab})")
    check(_area["MT_NAVEL"].get("weather") == "SNOW", "Navel Mountain is snowy (the whole area)")
    from src.world import seasons as _sea
    check(_sea.area_weather(g, "MT_NAVEL") == "SNOW", "...and battles there start in the snow (Hail / Blizzard)")
    _dn = next(o for o in _area["MT_NAVEL"]["route_menu"] if o["text"] == "Danny")["event"]["battle"]
    check(_dn["sprite"] == "danny_oi.png" and _os.path.isfile("assets/sprites/trainers/danny_oi.png"), "Danny: 5.7's own battle picture (trainer pic 119)")
    check(not {"37", "27", "41", "42"} & set(g.loader.area_data["ORANGE_MT_NAVEL_PERCENTAGES"]), "Navel Mountain: the old menu extras (Vulpix, Sandshrew, Zubat, Golbat) dropped")
if "SEVEN_GRAPEFRUITS" in BUILT:
    # (11-19, Jordan: the old pokeorange hack's Gen 2 species back where it had them - Mareep, Flaaffy, Skiploom here; Hoppip on Pinkan)
    check({"188", "179", "180"} <= set(g.loader.area_data["ORANGE_SEVEN_GRAPEFRUITS_PERCENTAGES"]), "the Grapefruits: the hack's Mareep, Flaaffy and Skiploom (11-19)")
if "MORO_ISLAND" in BUILT:
    story.story_flags.pop("got_tm_hydro_pump_moro", None); story.inventory.pop("TM142", None)
    _play_event("MORO_ISLAND", "Sailor")
    check(story.inventory.get("TM142") == 1, "Moro's sailor gives TM Hydro Pump (our TM142)")
    _mu = _tm["MORO_ISLAND"]["rooms"]["museum"]
    check(all("orange_moro_museum_paid" in str(s.get("condition")) for s in _mu.get("scenes", [])), "the Museum's ticket scene stops once you've paid")
print("7) batch 11: Route 60, Golden Island, Route 61, Murcott and its Meadows, played")
if "GOLDEN_ISLAND" in BUILT:
    _gs = _tm["GOLDEN_ISLAND"].get("scenes") or []
    check(any(s.get("flag") == "orange_golden_meowth" and s["trigger"]["zone"] == [13, 19, 15, 19] for s in _gs),
          "Golden Island: the Bounty Ceremony plays on 5.7's trigger row (13-15,19)")
    story.story_flags.pop("got_amulet_coin_golden", None); story.inventory.pop("AMULET_COIN", None)
    _play_event("GOLDEN_ISLAND", "Elder")
    check(story.inventory.get("AMULET_COIN") == 1, "...and the elder gives the Amulet Coin")
if "MURCOTT_ISLAND" in BUILT:
    story.story_flags.pop("got_tm_aerial_ace_murcott", None); story.inventory.pop("TM027", None)
    _play_event("MURCOTT_ISLAND", "Bug hater")
    check(story.inventory.get("TM027") == 1, "Murcott: TM Aerial Ace (5.7's TM40 = our TM027) from the man who hates bugs")
    story.story_flags.pop("orange_crystal_onix_seen", None)
    st = open_map("MURCOTT_ISLAND", "ORANGE_ROUTE_61")
    _pp = st._people() if hasattr(st, "_people") else {}
    check((39, 24) in _pp and (39, 25) in _pp, "two Bug Catchers stand before the Meadows' doors until Tracey's Crystal Cave scene (5.7's 0x4015 <= 4)")
    story.story_flags["orange_crystal_onix_seen"] = True
    st = open_map("MURCOTT_ISLAND", "ORANGE_ROUTE_61")
    _pp = st._people() if hasattr(st, "_people") else {}
    check((39, 24) not in _pp and (14, 32) in _pp, "...then they're off to their own spots")
if "MURCOTT_MEADOWS" in BUILT:
    for _f in ("orange_murcott_tracey1", "orange_scyther_flew", "orange_murcott_swarm"):
        story.story_flags.pop(_f, None)
    _play_event("MURCOTT_MEADOWS", "Tracey")
    check(story.story_flags.get("orange_murcott_tracey1"), "Murcott Meadows: Tracey takes the injured Scyther to the Center")
    story.current_area_key = "MURCOTT_ISLAND"
    _play_event("MURCOTT_ISLAND", "Tracey")
    check(story.story_flags.get("orange_scyther_flew"), "...in the Center, Nurse Joy calls: Scyther flew back to the Meadows")
    _ms = [s for s in (_tm["MURCOTT_MEADOWS"].get("scenes") or []) if s.get("flag") == "orange_murcott_swarm"]
    _tb = (_ms[0]["cast"][-1].get("event") or {}).get("battle") if _ms else {}
    check(bool(_ms) and _tb.get("team") == [48, 183, 123] and _tb.get("levels") == [30, 30, 30],
          f"...then the swarm and Team Rocket's glue gun, and Tracey battles you with Scyther (5.7's trainer 10: {(_tb or {}).get('team')})")
print("8) batches 11-12: story scenes that end in a battle, played on the map (Tracey's swarm, Gary on Mandarin South)")
from src.states.battle import TrainerIntroState as _TIS, TrainerBattleState as _TBS


def _calm(st):
    """(11-17) No wild Pokemon on the floor while a story scene is checked: they wander at random (unseeded) and one that
    walks into you starts a wild battle mid-scene. That was orange_maps' occasional Route 64 fail (the Magnemite scene and
    the hold after it), seen in a combined run but not caused by it: a wild Sandshrew/Cacnea-style wanderer on the sand."""
    if isinstance(st, DungeonState):
        st.run.floor.movers = [m for m in st.run.floor.movers if m.kind != "wild"]
        st.run.recipe = dict(st.run.recipe, respawn=False)


def _play_scene(key, at, step, flag, came, n=4000):
    """Walk onto a scene's trigger and let it play: lines tapped, its battle won; True once its flag is set and you're back."""
    st = open_map(key, came)
    _calm(st)
    if isinstance(st, DungeonState):   # (a route: its player is the floor run's)
        st.run.player = tuple(at)
    else:
        st.player = tuple(at)
    st.anim = 0
    st.step(*step)
    won = []
    for _ in range(n):
        c = g.current_state
        if isinstance(c, _TIS) and isinstance(getattr(c, "next_state", None), _TBS):
            g.change_state(c.next_state); c = c.next_state
        if isinstance(c, _TBS):
            won.append(getattr(c, "trainer_name", "?")); c.player_won = True; c.exit_battle(); continue
        if getattr(c, "npc_active", False):
            tap(c, 3)
        elif getattr(c, "dialogue_box", None) is not None and getattr(c.dialogue_box, "visible", False):
            c.dialogue_box.advance()
        g.current_state.update(); g.current_state.draw()
        if story.story_flags.get(flag) and not getattr(g.current_state, "npc_active", False) and isinstance(g.current_state, (_WTS, DungeonState))                 and not (getattr(g.current_state, "dialogue_box", None) is not None and g.current_state.dialogue_box.visible):
            return won
    return None


if "MURCOTT_MEADOWS" in BUILT:
    story.story_flags.update({"orange_murcott_tracey1": True, "orange_scyther_flew": True})
    story.story_flags.pop("orange_murcott_swarm", None); story.story_flags.pop("orange_murcott_tracey_battle", None)
    _w = _play_scene("MURCOTT_MEADOWS", (49, 20), (0, -1), "orange_murcott_swarm", "MURCOTT_ISLAND")
    check(bool(_w) and story.story_flags.get("orange_murcott_tracey_battle"), f"Murcott Meadows: the swarm scene plays, Tracey battles you, and you're back on the map ({_w})")
if "MANDARIN_SOUTH" in BUILT:
    story.story_flags.pop("orange_gary_mandarin", None); story.story_flags.pop("orange_gary_mandarin_battle", None)
    _w = _play_scene("MANDARIN_SOUTH", (30, 4), (0, -1), "orange_gary_mandarin", "ORANGE_ROUTE_62")
    check(bool(_w) and story.story_flags.get("orange_gary_mandarin_battle"), f"Mandarin South: Gary stops you at the north edge and battles you (5.7's var 28 -> 29) ({_w})")
    _ms = _area["MANDARIN_SOUTH"]
    _pr = next(o for o in _ms["explore_options"] if o["text"] == "Prima")["event"]["battle"]
    check(_pr["team"] == [87, 91, 131, 124, 80] and _pr["levels"] == [50] * 5 and _pr["rewards"].get("PP_MAX") == 1, "Prima of the Elite Four: 5.7's team at Lv 50, PP Max after")
    story.story_flags.pop("got_hm_fly_orange", None); story.inventory.pop("HM_FLY", None)
    _play_event("MANDARIN_SOUTH", "Fly man")
    check(story.inventory.get("HM_FLY") == 1, "Mandarin South: HM Fly from the man at the top of town (5.7's HM02)")
if "ORANGE_ROUTE_62" in BUILT:
    _sw = next(o for o in _area["ORANGE_ROUTE_62"]["route_menu"] if o["text"] == "Swimmer")["event"]
    check((_sw.get("tutor") or {}).get("move") == "WATERFALL", "Route 62: the swimmer on the Farfetch'd island teaches Waterfall (5.7's tutor)")

print("9) batch 11-12 answers and batch 13 (11-17): the rival, Prima, Fly, Route 63, Yambera, Route 64")


def _drive(flag, n=4000):
    """Let what's playing on the map run: lines tapped, any battle won; the trainers battled once flag is set and you're back."""
    won = []
    for _ in range(n):
        c = g.current_state
        if isinstance(c, _TIS) and isinstance(getattr(c, "next_state", None), _TBS):
            g.change_state(c.next_state); c = c.next_state
        if isinstance(c, _TBS):
            won.append(getattr(c, "trainer_name", "?")); c.player_won = True; c.exit_battle(); continue
        if getattr(c, "npc_active", False):
            tap(c, 3)
        elif getattr(c, "dialogue_box", None) is not None and getattr(c.dialogue_box, "visible", False):
            c.dialogue_box.advance()
        g.current_state.update(); g.current_state.draw()
        if story.story_flags.get(flag) and not getattr(g.current_state, "npc_active", False) and isinstance(g.current_state, (_WTS, DungeonState)) \
                and not (getattr(g.current_state, "dialogue_box", None) is not None and g.current_state.dialogue_box.visible):
            return won
    return None


# the rival (Jordan 11-17): Orange's "Gary" is the save's Kanto rival, name and look, and the other way round
_rr, _sr0 = dict(story.region_rivals), story.starting_region
story.starting_region = "KANTO"   # (a Kanto player now in Orange)
story.region_rivals = {"KANTO": {"name": "ZED", "character": "blue", "chosen": True}}
story.sync_rival()
check(g.rival_name == "ZED" and g.rival_character == "blue" and story.region_rivals.get("ORANGE", {}).get("name") == "ZED",
      f"Orange's rival is the Kanto rival the player named ({g.rival_name}, {g.rival_character})")
story.region_rivals = {"ORANGE": {"name": "MOSS", "character": "blue", "chosen": True}}
check(story.assign_region_rival("KANTO").get("name") == "MOSS" and not story.needs_rival_choice("KANTO"),
      "...and the other way round: a player who named the rival in Orange meets the same one in Kanto, no second pick")
story.region_rivals = {"KANTO": {"name": "ZED", "character": "blue", "chosen": True}}
story.sync_rival()
_pk = next(o for o in _area["PINKAN_ISLAND"]["route_menu"] if o.get("action") == "EVENT" and "orange_pinkan_gary" in str(o.get("flag_condition")))
_pb = next(st for st in _pk["event"]["stages"] if st.get("battle"))["battle"]
check(_pk["text"] == "{rival_name}" and _pb["name"] == "{rival_name}" and _pb["sprite"] == "{rival_character}"
      and all(l.startswith("{rival_name}:") for st in _pk["event"]["stages"] for l in st.get("lines", [])),
      "Pinkan: the rival's battle and words use the save's rival (name, picture)")
check(ow._fill_names(g, _pk["text"]) == "ZED", "...and the figure on Pinkan is named for them")
_gs = [x for x in (_tm["MANDARIN_SOUTH"].get("scenes") or []) if x.get("flag") == "orange_gary_mandarin"]
_gb = _gs[0]["cast"][0]["event"]["battle"] if _gs else {}
check(bool(_gs) and _gs[0]["cast"][0]["sheet"] == "@rival" and _gb.get("name") == "{rival_name}" and _gb.get("sprite") == "{rival_character}",
      "Mandarin South: the rival who walks up and battles is the save's own")
from src.states.overworld.dungeon import scene_sheet as _ss
check(_ss(g, "@rival") == "oi_72.png", f"...drawn on Orange's maps as 5.7's Gary sheet ({_ss(g, '@rival')})")
_m9 = next(m for m in g.loader.area_data["JOURNAL_MISSIONS"] if m["id"] == "orange_m9c")
check("{rival_name}" in _m9["text"] and "Gary" not in _m9["text"] + _m9["desc"], f"the Journal's Mandarin South step names the rival ({_m9['text']})")
story.region_rivals, story.starting_region = _rr, _sr0; story.sync_rival()

# Prima walks up to you in her house and battles (Jordan 11-17), till you've beaten her
if "MANDARIN_SOUTH" in BUILT:
    story.story_flags.pop("orange_prima_battle", None)
    story.current_area_key, story.last_area_key = "MANDARIN_SOUTH", "ORANGE_ROUTE_62"
    _pa = _tm["MANDARIN_SOUTH"]["rooms"]["prima"]["art"]
    _dy = max(y for y, r in enumerate(_pa) if "v" in r); _dx = _pa[_dy].index("v")
    g.walk_town_room = ("MANDARIN_SOUTH", "prima"); g.walk_town_pos = ("MANDARIN_SOUTH", (_dx, _dy - 1), (0, -1))
    st = CityState(g); g.change_state(st); frames(2)
    _w = _drive("orange_prima_battle")
    check(_w is not None and any("Prima" in str(x) for x in _w), f"Prima's house: she walks up to you and battles you ({_w})")

# Fly in Orange (Jordan 11-17): only islands with a Pokemon Center, landing outside its door; who carries you
from src.states.systems.fly_map import FlyState as _FS, fly_land as _fl, fly_ok as _fok
for k in ("MANDARIN_SOUTH", "GOLDEN_ISLAND", "MURCOTT_ISLAND", "YAMBERA"):
    story.story_flags[f"visited_{k}"] = True
story.current_area_key = "MANDARIN_SOUTH"
_fc = [k for k, _n in _FS(g, g.current_state).cities]
check("MANDARIN_SOUTH" in _fc and "YAMBERA" in _fc and "GOLDEN_ISLAND" not in _fc,
      f"Fly's list: Orange islands with a Center only, Golden Island left out ({[k for k in _fc if _area.get(k, {}).get('region') == 'ORANGE']})")
check(not _fok(g, "PINKAN_ISLAND") and not _fok(g, "FUKUHARA_ISLAND") and _fok(g, "VIRIDIAN_CITY"),
      "...Pinkan (Jenny's hut) and Fukuhara (no Center) aren't flown to; other regions as before")
story.last_area_key = "ORANGE_ROUTE_63"   # (flying from next door: still down at the Center, not at the edge)
_fl(g, "MANDARIN_SOUTH")
for _ in range(400):
    g.current_state.update(); g.current_state.draw()
    if isinstance(g.current_state, _WTS):
        break
_cd = next((t for t, k in g.current_state.doors.items() if k == "center"), None) if isinstance(g.current_state, _WTS) else None
check(_cd is not None and tuple(g.current_state.player) == (_cd[0], _cd[1] + 1),
      f"Fly lands you outside Mandarin South's Center door ({getattr(g.current_state, 'player', None)}, door {_cd})")
from src.states.systems import fly_scene as _fsc
_dex = g.data.data.setdefault("pokedex", {})
_pk = {k: v for k, v in _dex.items() if isinstance(v, dict) and (str(v.get("id")) == "25" or "PIKACHU" in str(v.get("name", "")).upper())}
for _k in _pk:
    _dex.pop(_k)
check(_fsc.carrier(g) is not None and _fsc.carrier_frames(g) is not None,
      f"Fly (game-wide, Jordan 11-17): never caught a Pikachu, your Fly Pokemon carries you ({getattr(_fsc.carrier(g), 'id', None)})")
_dex["25-normal"] = {"id": 25, "name": "Pikachu", "form": "normal", "shiny": False, "gmax": False}
check(_fsc.carrier(g) is None, "...once you've ever caught a Pikachu (the Pokedex's record, even if it's in the PC), Pikachu's balloon scene")
_reg0 = story.current_area_key
story.current_area_key = "VIRIDIAN_CITY"
check(_fsc.carrier(g) is None, "...in every region (Kanto too)")
_dex.pop("25-normal")
check(_fsc.carrier(g) is not None, "...and in Kanto without a Pikachu caught, your Pokemon carries you")
story.current_area_key = _reg0
_dex.update(_pk)
# Jordan 11-17, batch 13 answers: Fly reaches every place with a Pokemon Center (Desert Town too), on the Town Map and in the list
for k in ("ORANGE_ROUTE_64", "KINNOW_ISLAND", "ORANGE_ROUTE_58", "VALENCIA_ISLAND", "TROVITOPOLIS", "TROVITA_ISLAND"):
    story.story_flags[f"visited_{k}"] = True
story.current_area_key = "MANDARIN_SOUTH"
_fl2 = dict(_FS(g, g.current_state).cities)
check(_fl2.get("ORANGE_ROUTE_64") == "Desert Town" and "KINNOW_ISLAND" in _fl2 and "ORANGE_ROUTE_58" not in _fl2,
      f"Fly's list: Desert Town (Route 64's Center) is a stop; Kinnow by its Center, not Route 58's Clinic ({[v for k, v in _fl2.items() if _area.get(k, {}).get('region') == 'ORANGE']})")
from src.states.region_map import RegionMapState as _RMS
_rm = _RMS(g, g.current_state, fly=True)
_want = [k for k in _fl2 if _area.get(k, {}).get("region") == "ORANGE"]
check(all(k in _rm.visited for k in _want),
      f"...and every one of them is on the Orange Town Map to fly from ({sorted(set(_want) - _rm.visited)})")
_pts = (json.load(open("assets/map_points.json", encoding="utf-8")).get("region_maps") or {}).get("ORANGE", {}).get("points", {})
check(all(k in _pts for k in _want), f"...each with its own point on the Town Map ({sorted(set(_want) - set(_pts))})")
_fl(g, "ORANGE_ROUTE_64")
for _ in range(400):
    g.current_state.update(); g.current_state.draw()
    if isinstance(g.current_state, DungeonState):
        break
check(isinstance(g.current_state, DungeonState) and g.current_state.run.index == 0 and tuple(g.current_state.run.player) == (17, 10),
      f"...Fly to Desert Town lands you outside its Center's door on Route 64 ({getattr(getattr(g.current_state, 'run', None), 'player', None)})")
_hl = next(o for o in _area["ORANGE_ROUTE_64"]["route_menu"] if o["text"] == "Heal")
check(_hl.get("action") == "CENTER", "...and Desert Town's nurse heals you (a route's Center: action CENTER, so she stands at her counter)")
story.last_area_key = "ORANGE_ROUTE_49"
_fl(g, "VALENCIA_ISLAND")
for _ in range(400):
    g.current_state.update(); g.current_state.draw()
    if isinstance(g.current_state, _WTS):
        break
_vd = next((t for t, k in g.current_state.doors.items() if k == "center"), None) if isinstance(g.current_state, _WTS) else None
check(_vd is not None and tuple(g.current_state.player) == (_vd[0], _vd[1] + 1),
      f"...Fly to Valencia lands you at its Center, not the airport ({getattr(g.current_state, 'player', None)}, door {_vd})")

if "ORANGE_ROUTE_63" in BUILT:
    story.story_flags["orange_gary_mandarin"] = True
    story.story_flags.pop("orange_route63_rocket", None); story.story_flags.pop("orange_route63_rocket_battle", None)
    _w = _play_scene("ORANGE_ROUTE_63", (25, 9), (0, -1), "orange_route63_rocket", "MANDARIN_SOUTH")
    check(bool(_w) and story.story_flags.get("orange_route63_rocket_battle"), f"Route 63: Team Rocket drop in and battle you (5.7's var 29 -> 30) ({_w})")
if "YAMBERA" in BUILT:
    for _f in ("orange_yambera_asked", "orange_yambera_love", "got_poison_barb_yambera"):
        story.story_flags.pop(_f, None)
    story.inventory.pop("POISON_BARB", None)
    _play_event("YAMBERA", "Ralph")
    check(story.story_flags.get("orange_yambera_asked"), "Yambera: Ralph and Emily ask after their runaway Nidoran")
    _play_event("YAMBERA", "Tony")
    check(story.story_flags.get("orange_yambera_love"), "...the two Nidoran by the park are in love, and evolve")
    _play_event("YAMBERA", "Ralph")
    check(story.inventory.get("POISON_BARB") == 1, "...Ralph thanks you with a Poison Barb (5.7's)")
    story.story_flags.pop("got_tm_shock_wave_yambera", None)
    _play_event("YAMBERA", "Shock Wave man")
    check(story.inventory.get("TM298") == 1, "Yambera: TM Shock Wave (5.7's TM34 = our TM298)")
if "ORANGE_ROUTE_64" in BUILT:
    for _f in ("orange_magnemite_seen", "orange_magnemite_saved", "got_magnet_route64"):
        story.story_flags.pop(_f, None)
    _w = _play_scene("ORANGE_ROUTE_64", (74, 22), (0, -1), "orange_magnemite_seen", "YAMBERA")
    check(_w is not None and story.story_flags.get("orange_magnemite_seen"), "Route 64: you see a Magnemite trailing Team Rocket (5.7's var 31 -> 32)")
    st = open_map("ORANGE_ROUTE_64", "YAMBERA"); _calm(st)
    st.run.player = (66, 32); st.anim = 0; st.step(-1, 0)
    _drive("never_set_flag", n=300)
    check(tuple(g.current_state.run.player)[0] >= 66, f"...and you can't walk on west past them till you've dealt with them ({g.current_state.run.player})")
    _play_event("ORANGE_ROUTE_64", "Team Rocket")
    _w = _drive("orange_magnemite_saved")
    check(story.story_flags.get("orange_magnemite_saved"), f"...talk to them: the battle, Number 6 evolves into Magneton (5.7's var 33) ({_w})")
    _play_event("ORANGE_ROUTE_64", "Ethan ")
    check(story.inventory.get("MAGNET") == 1, "...and Ethan gives you a Magnet in Desert Town")

print("10) batch 13 answers and batch 14 (11-17): the dex, Desert Town's herd, Trovitopolis, the Sewers, Route 65, Trovita")
_dl = g.loader.area_data["REGION_START"]["ORANGE"]["dex_list"]
_drop = [171, 176, 177, 178, 179, 180, 183, 191, 192, 211, 218, 219, 223, 226, 231, 232]
_ofile = json.load(open("assets/orange_area_data.json", encoding="utf-8"))
_left = sorted({k for k, v in _ofile.items() if k.endswith("_PERCENTAGES") and isinstance(v, dict) and any(x.isdigit() and int(x) in _drop for x in v)})
_ext = g.loader.area_data["REGION_START"]["ORANGE"]["dex_extra"]   # (11-19, Jordan: the hack's species back, the dex only what Orange gives)
_back = [171, 176, 179, 180, 183, 191, 192, 211, 218, 219, 223, 226, 231, 232]
check(len(_dl) == 192 and set(_back) <= set(_ext) <= set(_dl) and not {177, 178} & set(_dl) and len(_left) >= 8,
      f"Orange dex (Jordan 11-23: everything Orange gives, odex.py): 192; the old hack's species back as extras and in their tables, Natu and Xatu not ({len(_dl)}; {_left[:4]})")
check(not {"MANDARIN_DESERT", "SUNRAY_CAVE"} & set(_ofile["STORY_PROGRESSION"]), "the menu-era Mandarin Desert and Sunray Cave are deleted")
if "ORANGE_ROUTE_64" in BUILT:
    story.story_flags["orange_magnemite_saved"] = True
    st = open_map("ORANGE_ROUTE_64", "YAMBERA")
    _fi = {o.get("text") for o in st._figure_items()}
    check({"Town Magnemite", "Town Jolteon", "Town Tauros"} <= _fi and "Magnemite" not in _fi and "Jolteon" not in _fi,
          "Ethan's herd lives in Desert Town after the story, at 5.7's spots (not at the ranch)")
if "TROVITOPOLIS" in BUILT:
    for _f in ("orange_mayor_met", "orange_bulbasaur_found", "orange_mayor_exposed", "got_tm_solar_beam_trovitopolis"):
        story.story_flags.pop(_f, None)
    st = open_map("TROVITOPOLIS", "ORANGE_ROUTE_64")
    st.player = (34, 36); st.anim = 0; st.step(-1, 0)
    _drive("never_set_flag", n=300)
    check(tuple(g.current_state.player)[0] >= 34, f"Trovitopolis: the policeman turns you back from the sewers (5.7's 33,36-37) ({g.current_state.player})")
    _play_event("TROVITOPOLIS", "Mayor")
    check(story.story_flags.get("orange_mayor_met"), "...the Mayor's election talk (5.7's 0x402B 0 -> 1); the guard dozes off")
    _play_event("TROVITOPOLIS_SEWERS", "Bulbasaur")
    check(story.story_flags.get("orange_bulbasaur_found"), "...in the sewers you find a Bulbasaur in the Mayor's collar (-> 2)")
    story.current_area_key, story.last_area_key = "TROVITOPOLIS", "ORANGE_ROUTE_64"
    g.walk_town_room = ("TROVITOPOLIS", "mayor_office"); g.walk_town_pos = ("TROVITOPOLIS", (7, 9), (0, -1))
    st = CityState(g); g.change_state(st); frames(2)
    st.player = (7, 9); st.anim = 0; st.step(0, -1)
    _drive("orange_mayor_exposed")
    check(story.story_flags.get("orange_mayor_exposed"), "...back in his office: Officer Jenny, Nurse Joy and the truth (-> 3)")
    story.inventory.pop("TM168", None)
    _play_event("TROVITOPOLIS", "Officer Jenny ")
    check(story.inventory.get("TM168") == 1, "...and Officer Jenny gives you TM Solar Beam (5.7's TM22 = our TM168)")
    story.story_flags.pop("got_porygon_trovitopolis", None)
    _play_event("TROVITOPOLIS", "Porygon man")
    check(story.story_flags.get("got_porygon_trovitopolis"), "Trovitopolis Center: the Super Nerd's Porygon (Lv 15)")
    story.inventory.pop("TM129", None); story.story_flags.pop("got_tm_calm_mind_trovitopolis", None)
    _play_event("TROVITOPOLIS", "Psychic mother")
    check(story.inventory.get("TM129") == 1, "The psychics' house: TM Calm Mind (5.7's TM04 = our TM129)")
    import random as _rnd
    _ch = _rnd.choice
    _rnd.choice = lambda seq: "LEFT" if tuple(seq) == ("LEFT", "RIGHT") else _ch(seq)
    story.inventory.pop("TWISTED_SPOON", None); story.story_flags.pop("got_twisted_spoon_trovitopolis", None)
    _play_event("TROVITOPOLIS", "Psychic father", pick="LEFT", n=600)
    _rnd.choice = _ch
    check(story.inventory.get("TWISTED_SPOON") == 1, "...the father's coin test: three right in a row, a TwistedSpoon (our coin_guess)")
    _tro = {o["text"]: o for o in _area["TROVITOPOLIS"]["explore_options"]}
    check(all(_tro[c].get("stock") for c in ("Market clerk", "TM clerk", "Gift clerk", "Vitamin clerk", "Battle item clerk")),
          "Trovito Dept. Store: five clerks, each with 5.7's own shelf")
    story.current_area_key = "TROVITOPOLIS"
    g.walk_town_room = ("TROVITOPOLIS", "lift"); g.walk_town_pos = ("TROVITOPOLIS", (2, 4), (0, -1))
    st = CityState(g); g.change_state(st); frames(2)
    _ev = st.sign_events.get((0, 2))
    ow._run_story_event(st, _ev["event"], lambda c: True, lambda l: None)
    for _ in range(600):
        c = g.current_state
        if isinstance(c, _PLS):
            c.pick("dept_3"); continue
        if getattr(c, "dialogue_box", None) is not None and getattr(c.dialogue_box, "visible", False):
            c.dialogue_box.advance()
        c.update(); c.draw()
        if isinstance(g.current_state, _WTS) and getattr(g.current_state, "room", None) == "dept_3":
            break
    check(isinstance(g.current_state, _WTS) and g.current_state.room == "dept_3",
          f"...the lift's panel takes you to 3F, the TV game shop ({getattr(g.current_state, 'room', None)})")
if "TROVITOPOLIS_SEWERS" in BUILT:
    _sm = next(o for o in _area["TROVITOPOLIS_SEWERS"]["route_menu"] if o["text"] == "Sewer man")["event"]
    check((_sm.get("tutor") or {}).get("move") == "THUNDER-WAVE", "The sewers' back room: the man teaches Thunder Wave once (5.7's tutor)")
if "TROVITA_ISLAND" in BUILT:
    for _f in ("orange_rudy_outside", "orange_rudy_flew", "orange_rudy_flew_scene", "orange_rudy_badge", "orange_rudy_down", "got_whirlpuller_trovita"):
        story.story_flags.pop(_f, None)
    story.inventory.pop("WHIRLPULLER", None)
    _bd = story.badges.setdefault("ORANGE", [])
    if "SPIKE_SHELL" in _bd:
        _bd.remove("SPIKE_SHELL")
    _play_event("TROVITA_ISLAND", "Rudy")
    check(story.story_flags.get("orange_rudy_outside"), "Trovita Gym: Rudy asks you outside (5.7's var 34 -> 35)")
    _w = _play_scene("TROVITA_ISLAND", (29, 23), (0, 1), "orange_rudy_flew", "ORANGE_ROUTE_65")
    _c = g.current_state
    check(story.story_flags.get("orange_rudy_flew") and isinstance(_c, _WTS) and tuple(_c.player) == (37, 9),
          f"...outside he leads you to his balloon, and it sets you down on the cliff top (the ride scene) ({getattr(_c, 'player', None)})")
    _play_event("TROVITA_ISLAND", "Rudy ")
    _w = _drive("orange_rudy_badge")
    check("SPIKE_SHELL" in story.badges.get("ORANGE", []) and story.inventory.get("TM120", 0) >= 1,
          f"...Rudy battles you on the cliff: the Spike Shell Badge and TM Psychic (5.7's TM29 = our TM120) ({_w})")
    _play_event("TROVITA_ISLAND", "Rudy ")
    _drive("orange_rudy_down")
    _c = g.current_state
    check(story.story_flags.get("orange_rudy_down") and isinstance(_c, _WTS) and tuple(_c.player) == (29, 23),
          f"...and the balloon brings you back down by the Gym (5.7's var 36) ({getattr(_c, 'player', None)})")
    _play_event("TROVITA_ISLAND", "Whirlpuller man")
    check(story.inventory.get("WHIRLPULLER") == 1, "...the islander gives the Whirlpuller to the badge's holder")

print("11) batches 15-16 (11-17): Route 66, Fairchild (the Whirlpuller, the Pidgeot's nest), Route 67's Team Rocket, Route 68's Tad, Cleopatra")
if "FAIRCHILD_ISLAND" in BUILT:
    _tm56 = _tm["ORANGE_ROUTE_56"]
    check(bool(_tm56.get("whirl")) and "FAIRCHILD_ISLAND" in _tm56["exits"].values(),
          f"Route 56: Fairchild's forest doors open, its flowing whirlpools listed for the Whirlpuller ({len(_tm56.get('whirl') or [])} tiles)")
    for _f in ("orange_fairchild_rocket", "orange_pidgeot_seen", "orange_fairchild_pidgeot"):
        story.story_flags.pop(_f, None)
    story.story_flags["orange_fairchild_north"] = True   # (else coming in from Route 56 by the north door plays that line first)
    story.story_flags["got_whirlpuller_trovita"] = True
    _play_scene("FAIRCHILD_ISLAND", (42, 36), (0, -1), "orange_fairchild_rocket", "ORANGE_ROUTE_56")
    check(story.story_flags.get("orange_fairchild_rocket"), "Fairchild: Team Rocket run past you on the path (5.7's var 36 -> 37)")
    _play_scene("FAIRCHILD_ISLAND", (45, 19), (-1, 0), "orange_pidgeot_seen", "ORANGE_ROUTE_56")
    _boss = next(o for o in _area["FAIRCHILD_ISLAND"]["route_menu"] if o["text"] == "PIDGEOT")
    _ab = _area["FAIRCHILD_ISLAND"]["area_boss"]
    check(story.story_flags.get("orange_pidgeot_seen") and _boss.get("flag_condition") == "orange_pidgeot_seen"
          and (_ab["id"], _ab["level"], _ab["catchable"]) == (18, 40, True),
          "...the giant nest: a Pidgeot (Lv 40, catchable) lands beside it once you've seen it")
    _sb = next(o for o in _area["FAIRCHILD_ISLAND"]["route_menu"] if o["text"] == "SHARP BEAK")
    check(_sb.get("condition") == "orange_fairchild_pidgeot" and _sb["event"]["gift_item"] == {"SHARP_BEAK": 1},
          "...and after the battle it leaves a Sharp Beak behind")
if "ORANGE_ROUTE_67" in BUILT:
    story.story_flags.pop("orange_route67_rocket", None)
    story.story_flags["orange_fairchild_rocket"] = True
    _w = _play_scene("ORANGE_ROUTE_67", (13, 81), (0, -1), "orange_route67_rocket", "ORANGE_ROUTE_56")
    check(story.story_flags.get("orange_route67_rocket"), f"Route 67: Team Rocket land in their balloon and battle (5.7's trainer 17) ({_w})")
if "ORANGE_ROUTE_68" in BUILT:
    story.story_flags.pop("orange_tad_battle", None)
    story.inventory.pop("MACHO_BRACE", None)
    _play_event("ORANGE_ROUTE_68", "Tad")
    _w = _drive("orange_tad_battle")
    check(story.story_flags.get("orange_tad_battle") and story.inventory.get("MACHO_BRACE", 0) >= 1,
          f"Route 68: Tad's match (Poliwrath Lv 40), then the Macho Brace ({_w})")
    check("ORANGE_ROUTE_57_NORTH" not in _area, "the menu's Route 57 North (no 5.7 place) is gone")

print("12) batch 17 (11-17/18): Shamouti before the League, Ascorbia's Team Wartortle, Ascorbia Forest; Mom's home on Valencia")
if "SHAMOUTI_ISLAND" in BUILT:
    _q = _tm["ORANGE_ROUTE_67"]
    check(_q["exits"].get("<") == "SHAMOUTI_ISLAND" and any(k.startswith("56,") for k in _q.get("edge_to", {})),
          "Route 67's west side (5.7's 3.45, column 56 of our map) joins Shamouti")
    _s = _area["SHAMOUTI_ISLAND"]
    check(_s["area_type"] == "town" and not any(o.get("condition") == "beat_orange_champion" for o in _s.get("travel_options", []) if o.get("target_area") == "ORANGE_ROUTE_67"),
          "Shamouti is open before the League (5.7: the festival being got ready)")
    check(sorted((b["until"]["flag_condition"], tuple(b["tiles"][0])) for b in _tm["SHAMOUTI_ISLAND"]["barred"])
          == [("heard_shamouti_legend", (6, 59)), ("heard_shamouti_legend", (42, 52)), ("shamouti_lugia_rose", (20, 60))],
          "the three islands as 5.7 gates them (batch 28, Q31): Fire and Lightning's caves after Melody's play, Ice's stairs after Lugia rises")
    for _f in ("shamouti_chosen_one", "heard_shamouti_legend"):
        story.story_flags.pop(_f, None)
    story.story_flags.pop("beat_orange_champion", None)
    st = open_map("SHAMOUTI_ISLAND", "ORANGE_ROUTE_67"); st.player = (15, 24); st.anim = 0; st.step(0, -1); _drive("never_set_flag", n=200)
    check(not story.story_flags.get("shamouti_chosen_one"), "before the League, no festival scene at the square")
    story.story_flags["beat_orange_champion"] = True
    story.story_flags["move_offer_orange"] = True   # (Mom's champion call has been made: not what this checks)
    _w = _play_scene("SHAMOUTI_ISLAND", (15, 24), (0, -1), "shamouti_chosen_one", "ORANGE_ROUTE_67")
    check(story.story_flags.get("shamouti_chosen_one"), "after the League: Melody and the festival folk name you the Chosen One")
    _play_event("SHAMOUTI_ISLAND", "Melody")
    check(story.story_flags.get("heard_shamouti_legend"), "...Melody's play in the Festival House sends you for the three spheres")
    story.story_flags.pop("beat_orange_champion", None); story.story_flags.pop("move_offer_orange", None)
    _kd = next(o for o in _s["explore_options"] if o["text"] == "Kindler")["event"]
    check(_kd["gift_item"] == {"TM157": 1}, "the Kindler's TM Overheat (5.7's TM50)")
    check("HEART_SCALE_COVE" not in _area, "the menu's Heart Scale Cove (no 5.7 place) is gone")
if "ASCORBIA_ISLAND" in BUILT:
    for _f in ("orange_wartortle_taken", "orange_aidan_forest", "orange_ascorbia_jj", "orange_ascorbia_jj_battle",
               "orange_butch_ascorbia", "orange_cassidy_ascorbia", "orange_wartortle_beaten", "orange_wartortle_saved", "got_tm_flamethrower_ascorbia"):
        story.story_flags.pop(_f, None)
    _w = _play_scene("ASCORBIA_ISLAND", (10, 22), (0, -1), "orange_wartortle_taken", "ORANGE_ROUTE_68")
    check(story.story_flags.get("orange_wartortle_taken"), "Ascorbia: Team Rocket's balloon carries off Team Wartortle; Captain Aidan asks for help (5.7's var 39 -> 40)")
    st = open_map("ASCORBIA_ISLAND", "ORANGE_ROUTE_68"); st.player = (7, 13); st.anim = 0; st.step(0, -1); _drive("never_set_flag", n=300)
    check(tuple(g.current_state.player)[1] >= 13, f"...and the stairs to the west beach turn you back till they're saved ({g.current_state.player})")
    _play_event("ASCORBIA_FOREST", "Captain Aidan")
    check(story.story_flags.get("orange_aidan_forest"), "Ascorbia Forest: Aidan by the warehouse door goes in with you")
    g.arrive_floor = ("ASCORBIA_FOREST", 1, [2, 8])
    st = open_map("ASCORBIA_FOREST", "ASCORBIA_ISLAND"); _calm(st)
    check(st.run.index == 1, f"...the Rocket warehouse is the forest's second floor ({st.run.index})")
    st.run.player = (2, 8); st.anim = 0; st.step(0, -1)
    _w = _drive("orange_ascorbia_jj_battle")
    check(story.story_flags.get("orange_ascorbia_jj_battle"), f"...Jessie, James and Meowth stop you inside and battle (5.7's trainer 18) ({_w})")
    g.arrive_floor = ("ASCORBIA_FOREST", 1, [16, 3])
    st = open_map("ASCORBIA_FOREST", "ASCORBIA_ISLAND"); _calm(st)
    st.run.player = (16, 3); st.anim = 0; st.step(1, 0)
    _w = _drive("orange_wartortle_saved")
    check(story.story_flags.get("orange_wartortle_saved") and _w and len(_w) >= 2,
          f"...Cassidy and Butch battle you by the cage, and Aidan frees Team Wartortle ({_w})")
    st = open_map("ASCORBIA_ISLAND", "ORANGE_ROUTE_68"); st.player = (7, 13); st.anim = 0; st.step(0, -1); _drive("never_set_flag", n=300)
    check(tuple(g.current_state.player)[1] <= 12, f"...then the way west is open ({g.current_state.player})")
    _play_event("ASCORBIA_ISLAND", "Captain Aidan")
    check(story.inventory.get("TM125") == 1, "...and Aidan thanks you at the fire station with TM Flamethrower (5.7's TM35)")
if "VALENCIA_ISLAND" in BUILT:
    _v = _tm["VALENCIA_ISLAND"]
    check(_v["inside"].get("29,7") == "home" and _v["rooms"]["home"]["exits"].get("v") == "OUT:29,7" and "home_2" in _v["rooms"],
          "Valencia: Mom's home behind 5.7's door at 29,7, with its room upstairs")
    _k = json.load(open("assets/town_maps.json", encoding="utf-8"))["PALLET_TOWN"]["rooms"]
    check(_v["rooms"]["home"]["art"] == _k["home"]["art"] and _v["rooms"]["home_2"]["art"] == _k["home_2"]["art"]
          and _v["rooms"]["home"]["roofs"]["_picture"]["f"] == _k["home"]["roofs"]["_picture"]["f"],
          "...built exactly as Kanto's player house (layout and picture, upstairs too)")
    check("Talk to Mom" in _v["rooms"]["home"]["people"], "...with Mom inside")
    st = open_map("VALENCIA_ISLAND", "ORANGE_ROUTE_49")
    st._go("home", ""); frames(2); tap(st)
    check(st.room == "home", f"...you can walk in ({st.room})")
    from src.states.overworld import town_story as _ts
    _hr = next((r for r, c in story.get_region_starts() if c.get("start_area") == "VALENCIA_ISLAND" and not c.get("travel_only")), None)
    check(_hr == "ORANGE", f"...and it counts as home (Valencia is Orange's start: Mom heals, keeps the rowdy Pikachu, offers the move) ({_hr})")

def _ride_lift(st, to):
    """(batch 29, Q61) From the lobby: into 5.7's one lift car, its attendant asks, pick `to`, out of its doors: (car room, where you are)."""
    st._go("gym", "OUT:24,16"); tap(st); st.player = (3, 5); st.anim = 0; st.step(0, -1)
    car = None
    for _ in range(600):
        c = g.current_state
        if isinstance(c, _WTS) and c.room == "lift":
            car = "lift"
        if isinstance(c, _PLS):
            c.pick(to); continue
        if getattr(c, "npc_active", False):
            tap(c, 3)
        elif getattr(c, "dialogue_box", None) is not None and getattr(c.dialogue_box, "visible", False):
            c.dialogue_box.advance()
        c.update(); c.draw()
        if car and isinstance(c, _WTS) and c.room == "lift" and story.story_flags.get("orange_kumquat_lift_floor") == to and not c.npc_active \
                and not c._busy():
            break
    c = g.current_state
    out = [t for t, v in c.exits.items() if str(v).startswith("ROOM:")]
    if out:
        c.player = (out[0][0], out[0][1] - 1); c.anim = 0; c.step(0, 1); frames(30); tap(c)
    return car, g.current_state


print("13) batch 18 (11-18): Route 69, Butwal (Gulzar, HM Cut, the falls), Kumquat (the hotel, Luana's battle)")
if "ORANGE_ROUTE_69" in BUILT:
    check("ORANGE_ROUTE_69_EAST" not in _area, "the menu's second Route 69 (5.7 has one Route S) is gone")
    _r = _tm["ORANGE_ROUTE_69"]["exits"]
    check(set(_r.values()) >= {"ASCORBIA_ISLAND", "KUMQUAT_ISLAND", "BUTWAL_ISLAND"}, f"Route 69 joins Ascorbia, Kumquat and Butwal's door ({sorted(set(_r.values()))})")
if "BUTWAL_ISLAND" in BUILT:
    from src.world import hms as _hms
    for _f in ("orange_gulzar_met", "orange_gulzar_battle", "got_hm_cut_orange"):
        story.story_flags.pop(_f, None)
    story.inventory.pop("HM_CUT", None)
    _w = _play_scene("BUTWAL_ISLAND", (42, 19), (0, -1), "orange_gulzar_met", "ORANGE_ROUTE_69")
    check(story.story_flags.get("orange_gulzar_battle") and _w, f"Butwal: Gulzar walks up at the stairs and battles you (5.7's trainer 37) ({_w})")
    _play_event("BUTWAL_ISLAND", "Gulzar")
    check(story.inventory.get("HM_CUT") == 1, "...then gives you HM Cut at the Center (5.7's HM01)")
    _bw = _area["BUTWAL_ISLAND"]
    check(_bw.get("fly_point", {}).get("room") == "center" and any(o.get("action") == "CENTER" for o in _bw["route_menu"]),
          "Butwal's Center: a Fly stop, its nurse heals")
    _p = story.player_team[0] if story.player_team else None
    if _p is not None:
        _mv = list(getattr(_p, "moves", []) or [])
        _p.moves = [m for m in _mv if str(m).upper() != "WATERFALL"]
        story.inventory.pop("HM_WATERFALL", None)
        check(not _hms.field(story, "HM_WATERFALL"), "Butwal's falls stay shut without a Pokemon that knows Waterfall")
        _p.moves = (_p.moves[:3] + ["WATERFALL"])
        check(_hms.field(story, "HM_WATERFALL"), "...and a Pokemon taught Waterfall (Route 62's swimmer) climbs them (5.7: the move, no HM)")
        story.inventory["HM_SURF"] = 1
        st = open_map("BUTWAL_ISLAND", "ORANGE_ROUTE_69"); _calm(st)
        st.run.player = (25, 15); st.anim = 0
        for _ in range(9):
            st.step(0, -1)
            for _i in range(40):
                g.current_state.update(); g.current_state.draw(); tap(g.current_state)
                if not getattr(g.current_state, "anim", 0) and not getattr(g.current_state, "sliding", None):
                    break
        _py = tuple(g.current_state.run.player)
        check(_py[1] <= 7, f"...walked: up the pond's falls to the river at the top of the island ({_py})")
        _p.moves = _mv
if "KUMQUAT_ISLAND" in BUILT:
    for _f in ("orange_luana_met", "orange_luana_hotel", "orange_luana_badge"):
        story.story_flags.pop(_f, None)
    story.badges["ORANGE"] = [b for b in story.badges.get("ORANGE", []) if "JADE" not in str(b).upper()]
    story.inventory.pop("TM149", None)
    _k = _tm["KUMQUAT_ISLAND"]
    check(_k["inside"].get("24,16") == "gym" and {"gym", "top_floor", "arena"} <= set(_k["rooms"]), "Kumquat: the hotel (the Gym), its top floor and the battle arena")
    _play_event("KUMQUAT_ISLAND", "Misty")
    check(story.story_flags.get("orange_luana_met"), "Misty on the beach: Luana runs up, mistaking you for her son (5.7's var 41 -> 42)")
    st = open_map("KUMQUAT_ISLAND", "ORANGE_ROUTE_69")
    st._go("gym", "OUT:24,16"); tap(st)
    _drive("orange_luana_hotel", n=1500)
    check(story.story_flags.get("orange_luana_hotel"), "...in the hotel lobby she walks up: see you in the battle arena (42 -> 43)")
    _ga = _k["rooms"]["gym"]
    check(any([3, 4] in b["tiles"] and b["until"] == {"flag_condition": "orange_luana_hotel"} for b in _ga.get("barred", [])),
          "the lift is for guests and challengers only till then (5.7's attendant)")
    st = open_map("KUMQUAT_ISLAND", "ORANGE_ROUTE_69")
    _car, _c = _ride_lift(st, "top_floor")
    check(_car == "lift" and g.current_state.room == "top_floor" and tuple(g.current_state.player) == (2, 6),
          f"...then the lift (batch 28, Q8: 5.7's lift car) takes you up to the top floor ({_car}, {g.current_state.room}, {g.current_state.player})")
    _lu = next(o for o in _area["KUMQUAT_ISLAND"]["explore_options"] if o["text"] == "Luana ")
    check(_lu["event"]["battle"]["team"] == [105, 65] and _lu["event"]["battle"]["levels"] == [46, 46], "Luana: 5.7's Marowak and Alakazam, Lv 46")
    st = open_map("KUMQUAT_ISLAND", "ORANGE_ROUTE_69")
    ow._run_story_event(st, _lu["event"], st._check_menu_condition, lambda l: None)
    _w = _drive("orange_luana_badge")
    check(story.story_flags.get("orange_luana_badge") and story.inventory.get("TM149") == 1
          and any("JADE" in str(b).upper() for b in story.badges.get("ORANGE", [])),
          f"...her battle wins the Jade Star Badge and TM Earthquake ({_w}, {story.badges.get('ORANGE')})")
    _ms = next(o for o in _area["KUMQUAT_ISLAND"]["explore_options"] if o["text"] == "Misty ")
    check(not st._check_menu_condition(_ms["condition"][-1]) if isinstance(_ms["condition"], list) else True,
          "...and Misty and Tracey move on from the beach")

    # (11-18) a walked town has no sight trainers: its trainers battle when talked to (Kumquat's beach; Sunburst fixed too)
    for _tk, _names in (("KUMQUAT_ISLAND", {"Kanae", "Eiichiro", "Dora", "Oliver"}), ("SUNBURST_ISLAND", {"Blanche", "Bud", "Emma", "Noel", "Ayami"})):
        _m = _tm[_tk]
        _ev = {p["text"]: p for p in _m["people"] if isinstance(p, dict) and (p.get("event") or {}).get("battle")}
        check(not any("X" in r for r in _m["art"]) and _names <= set(_ev), f"{_tk}: its trainers stand on the map and battle when talked to ({sorted(_ev)})")
    _kn = next(p for p in _tm["KUMQUAT_ISLAND"]["people"] if isinstance(p, dict) and p.get("text") == "Kanae")
    story.story_flags.pop(_kn["event"]["flag"], None)
    st = open_map("KUMQUAT_ISLAND", "ORANGE_ROUTE_69")
    ow._run_story_event(st, _kn["event"], st._check_menu_condition, lambda l: None)
    _w = _drive(_kn["event"]["flag"])
    check(_w == ["Kanae"], f"...talk to Crush Girl Kanae and she battles you (5.7's trainer 439) ({_w})")

print("14) batch 19 (11-18): Routes 70-72, Rind Island (Quackenpoker's Magikarp), Salveyo Island (the Salveyo Weed)")
if "ORANGE_ROUTE_71" in BUILT:
    check(_area["ORANGE_ROUTE_71"]["route_name"] == "Route 71" and "ORANGE_ROUTE_72" in _area, "the menu's \"Routes 71 and 72\" is 5.7's two routes: 71 (U) and 72 (V)")
    check("PUMMELO_ISLAND" in _tm["ORANGE_ROUTE_72"]["exits"].values() and "SALVEYO_ISLAND" in _tm["ORANGE_ROUTE_72"]["exits"].values(),
          "Route 72 leads on to Pummelo and has Salveyo's door")
    for _f in ("orange_quack_met", "orange_quack_rind", "orange_quack_ritual", "orange_quack_sea", "got_dragon_fang_orange"):
        story.story_flags.pop(_f, None)
    story.inventory.pop("DRAGON_FANG", None)
    _play_scene("ORANGE_ROUTE_71", (19, 20), (0, -1), "orange_quack_met", "ORANGE_ROUTE_70")
    check(story.story_flags.get("orange_quack_met"), "Route 71: Dr. Quackenpoker watches the Magikarp head for Rind Island (5.7's var 0x4030 0 -> 1)")
    _play_scene("RIND_ISLAND", (30, 33), (0, -1), "orange_quack_rind", "ORANGE_ROUTE_71")
    check(story.story_flags.get("orange_quack_rind"), "...on Rind the Magikarp climb the falls (1 -> 2)")
    _play_scene("RIND_ISLAND", (31, 12), (0, -1), "orange_quack_ritual", "ORANGE_ROUTE_71")
    check(story.story_flags.get("orange_quack_ritual"), "...at the lake some evolve into Gyarados (2 -> 3)")
    _play_scene("ORANGE_ROUTE_71", (19, 20), (0, -1), "orange_quack_sea", "ORANGE_ROUTE_70")
    check(story.story_flags.get("orange_quack_sea"), "...back on Route 71 they swim out to sea (3 -> 4)")
    _play_event("ORANGE_ROUTE_71", "Quackenpoker")
    check(story.inventory.get("DRAGON_FANG") == 1, "...and Quackenpoker gives you a Dragon Fang (4 -> 5)")
    _r70 = {o["text"]: o for o in _area["ORANGE_ROUTE_70"]["route_menu"]}
    check(_r70["Mega Punch man"]["event"]["tutor"]["move"] == "MEGA-PUNCH" and _r70["Mega Kick man"]["event"]["tutor"]["move"] == "MEGA-KICK",
          "Route 70: the Mega Punch and Mega Kick tutors (our move keys, hyphenated: 11-23, orange_events plays them)")
if "SALVEYO_ISLAND" in BUILT:
    for _f in ("orange_salveyo_asked", "got_salveyo_weed", "orange_tracey_healed"):
        story.story_flags.pop(_f, None)
    _play_event("SALVEYO_ISLAND", "Misty")
    check(story.story_flags.get("orange_salveyo_asked"), "Salveyo: in the cabin Misty asks you for Salveyo Weed for Tracey (5.7's var 0x4031)")
    _play_scene("SALVEYO_ISLAND", (19, 25), (0, -1), "got_salveyo_weed", "ORANGE_ROUTE_72")
    check(story.story_flags.get("got_salveyo_weed"), "...the Poliwag brings you some weed (3 -> 4)")
    _play_event("SALVEYO_ISLAND", "Misty")
    check(story.story_flags.get("orange_tracey_healed"), "...and Misty's tea heals Tracey (4 -> 5)")

print("15) batch 20 (11-18): Pummelo Island, the Palace of Victory, Pummelo Stadium and Drake")
if "PUMMELO_ISLAND" in BUILT:
    check("ORANGE_VICTORY_ROAD" not in _area, "the menu's Orange Victory Road (no 5.7 place) is gone")
    _pr = _tm["PUMMELO_ISLAND"]["rooms"]
    check(_pr["stadium"]["exits"].get("^") == "ROOM:league" and _pr["league"]["exits"].get("n") == "ROOM:stadium",
          "Pummelo Stadium: the lobby's north door leads into the arena (5.7's waiting room skipped)")
    for _f in ("orange_rival_pummelo_met", "orange_rival_pummelo", "orange_drake_met", "beat_orange_champion", "gym_progress_PUMMELO_ISLAND"):
        story.story_flags.pop(_f, None)
    _w = _play_scene("PUMMELO_ISLAND", (31, 28), (0, -1), "orange_rival_pummelo_met", "ORANGE_ROUTE_72")
    check(story.story_flags.get("orange_rival_pummelo"), f"arriving, your rival battles you (5.7's trainer 31, var 44 -> 45) ({_w})")
    st = open_map("PUMMELO_ISLAND", "ORANGE_ROUTE_72")
    st._go("stadium", "OUT:43,19"); tap(st); _calm(st)
    st.player = (6, 8); st.anim = 0; st.step(0, -1); _drive("never_set_flag", n=300)
    check(tuple(g.current_state.player)[1] >= 8, f"the Stadium guard turns you back before you've met Drake ({g.current_state.player})")
    story.badges["ORANGE"] = ["CORAL_EYE", "SEA_RUBY", "SPIKE_SHELL"]
    _play_event("PUMMELO_ISLAND", "Drake")
    check(not story.story_flags.get("orange_drake_met"), "Drake at the Palace wants all four badges")
    story.badges["ORANGE"] = ["CORAL_EYE", "SEA_RUBY", "SPIKE_SHELL", "JADE_STAR"]
    _play_event("PUMMELO_ISLAND", "Drake")
    check(story.story_flags.get("orange_drake_met"), "...with them, Drake meets you at the Palace of Victory and heads for the Stadium")
    _ld = _area["PUMMELO_ISLAND"]["gym"]["leader"]
    check(_ld["team"] == [132, 95, 94, 3, 125, 149] and _ld["levels"] == [50, 50, 50, 50, 50, 52] and _ld.get("victory_flag") == "beat_orange_champion",
          "Drake: 5.7's six (Ditto, Onix, Gengar, Venusaur, Electabuzz, Dragonite), Lv 50-52")
    st = open_map("PUMMELO_ISLAND", "ORANGE_ROUTE_72")
    st._go("league", "ROOM:stadium"); tap(st)
    _dk = next(p for p in _pr["league"]["people"] if isinstance(p, dict) and p.get("text") == "Drake")
    st._get_callback_for_option(_dk)()
    _w = _drive("beat_orange_champion", n=6000)
    check(story.story_flags.get("beat_orange_champion"), f"...and in the arena Drake's six-on-six makes you Orange League Champion ({_w})")

print("16) batch 21 (11-18): Route 73, Tarroco, Route 74, Hamlin (Poncho and the Electrode), Hamlin Fields")
if "HAMLIN_ISLAND" in BUILT:
    check(_area["ORANGE_ROUTE_73"]["route_name"] == "Route 73" and _area["ORANGE_ROUTE_74"]["route_name"] == "Route 74",
          "the menu's \"Routes 73 and 74\" is 5.7's two routes: 73 (W) and 74 (X)")
    check(_tm["ORANGE_ROUTE_73"]["exits"].get("v") == "PUMMELO_ISLAND" and "TARROCO_ISLAND" in _tm["ORANGE_ROUTE_73"]["exits"].values()
          and "HAMLIN_ISLAND" in _tm["ORANGE_ROUTE_74"]["exits"].values(), "Pummelo - Route 73 - Tarroco - Route 74 - Hamlin, as 5.7 joins them")
    _tr = [o for o in _area["TARROCO_ISLAND"]["explore_options"] if (o.get("event") or {}).get("trade")]
    check(sorted((o["event"]["trade"]["give"], o["event"]["trade"]["want"]) for o in _tr) == [(35, 39), (82, 105)],
          "Tarroco: 5.7's trades 4 and 5 (Magneton for a Marowak, Clefairy for a Jigglypuff)")
    for _f in ("orange_hamlin_explosion", "orange_hamlin_electrode", "orange_hamlin_diglett", "orange_hamlin_fields", "got_scope_lens_hamlin"):
        story.story_flags.pop(_f, None)
    story.inventory.pop("SCOPE_LENS", None)
    st = open_map("HAMLIN_ISLAND", "ORANGE_ROUTE_74"); _calm(st)
    st.run.player = (17, 30); st.anim = 0; st.step(0, -1); _drive("never_set_flag", n=200)
    check(g.current_state.run.index == 0, f"Hamlin: the Pokemon Center is shut till the Electrode are moved (5.7's closed doors) (floor {g.current_state.run.index})")
    _play_scene("HAMLIN_ISLAND", (15, 18), (-1, 0), "orange_hamlin_explosion", "ORANGE_ROUTE_74")
    check(story.story_flags.get("orange_hamlin_explosion"), "...on the street an explosion, and an angry Electrode rolls up (5.7's var 0x4033 1)")
    st = open_map("HAMLIN_ISLAND", "ORANGE_ROUTE_74")
    _figs = [i.get("text") for i in st._figure_items()]
    check("ELECTRODE" in _figs and _area["HAMLIN_ISLAND"]["area_boss"]["id"] == 101 and _area["HAMLIN_ISLAND"]["area_boss"]["level"] == 40,
          f"...the Electrode stands in the street to battle (5.7's wild Electrode Lv 40) ({_figs})")
    story.story_flags["orange_hamlin_electrode"] = True
    _play_scene("HAMLIN_ISLAND", (15, 18), (-1, 0), "orange_hamlin_diglett", "ORANGE_ROUTE_74")
    check(story.story_flags.get("orange_hamlin_diglett"), "...then Poncho's Diglett take the Electrode underground (1 -> 2)")
    _play_scene("HAMLIN_FIELDS", (11, 23), (-1, 0), "orange_hamlin_fields", "HAMLIN_ISLAND")
    check(story.story_flags.get("orange_hamlin_fields"), "...in Hamlin Fields Poncho shows you the Electrode, happy at last (2 -> 3)")
    st = open_map("HAMLIN_ISLAND", "ORANGE_ROUTE_74"); _calm(st)
    st.run.player = (17, 30); st.anim = 0; st.step(0, -1); frames(30); tap(st)
    check(g.current_state.run.index != 0, f"...and the Center opens (floor {g.current_state.run.index})")
    _figs = [i.get("text") for i in g.current_state._figure_items()]
    check("Shop" in _figs and "Heal" in _figs, f"Hamlin's nurse and Mart clerk stand in their rooms on the route ({sorted(t for t in _figs if t in ('Shop', 'Heal'))})")
    _play_event("HAMLIN_ISLAND", "Poncho")
    check(story.inventory.get("SCOPE_LENS") == 1, "...back in town Poncho gives you a Scope Lens (3 -> 4)")
    from src.states.systems import fly_map as _fm
    check(_fm.fly_name(g, "HAMLIN_ISLAND") == "Hamlin Island" and _area["HAMLIN_ISLAND"].get("fly_point", {}).get("room") == "center"
          and "TARROCO_ISLAND" in json.load(open("assets/map_points.json", encoding="utf-8"))["region_maps"]["ORANGE"]["points"],
          "Fly: Tarroco and Hamlin (each has a Center) are on the Town Map and land at the Center")

print("17) batch 22 (11-18): the spheres story after the League (Fire Island, Lawrence III's palace, Lightning Island, the shrine, Ice Island)")
if "FIRE_ISLAND" in BUILT and _tm["FIRE_ISLAND"].get("floors"):
    _sp = ("shamouti_fire_sphere", "shamouti_fire_scene", "shamouti_palace_taken", "shamouti_palace_crash_seen", "shamouti_palace_crash",
           "shamouti_lightning_sphere", "shamouti_lightning_scene", "shamouti_lightning_done", "shamouti_lugia_rose", "shamouti_ice_sphere",
           "shamouti_lugia_song", "shamouti_sphere_set", "orange_lightning_birds_seen")
    for _f in _sp:
        story.story_flags.pop(_f, None)
    story.story_flags.update({"beat_orange_champion": True, "heard_shamouti_legend": True, "move_offer_orange": True})
    check("SHAMOUTI_SHRINE" not in _area and len(_tm["FIRE_ISLAND"]["floors"]) == 2 and len(_tm["ICE_ISLAND"]["floors"]) == 2,
          "Fire, Lightning and Ice Island are 5.7's caves and summits; the menu's shrine is gone (5.7's is Shamouti's own)")
    _play_event("FIRE_ISLAND", "FIRE SPHERE")
    check(story.story_flags.get("shamouti_fire_sphere"), "Fire Island: the Fire Sphere on its altar (5.7's var 0x4039 4 -> 5)")
    g.arrive_floor = ("FIRE_ISLAND", 1, [21, 35])
    st = open_map("FIRE_ISLAND", "SHAMOUTI_ISLAND"); _calm(st)
    st.run.player = (21, 35); st.anim = 0; st.step(0, 1)
    _drive("shamouti_palace_taken")
    check(story.story_flags.get("shamouti_palace_taken") and story.current_area_key == "LAWRENCE_SHIP",
          f"...going back down, Melody, Zapdos, and the flying ship's beam takes you aboard (5 -> 6) ({story.current_area_key})")
    st = g.current_state
    if isinstance(st, DungeonState) and st.area_key == "LAWRENCE_SHIP":
        _calm(st); st.run.player = (8, 11); st.anim = 0; st.step(0, -1)
        _drive("shamouti_palace_crash")
    check(story.story_flags.get("shamouti_palace_crash") and story.current_area_key == "LIGHTNING_ISLAND",
          f"...Lawrence III's flying palace: Melody frees the birds and it crashes on Lightning Island (6 -> 7 -> 8) ({story.current_area_key})")
    _play_event("LIGHTNING_ISLAND", "LIGHTNING SPHERE")
    check(story.story_flags.get("shamouti_lightning_sphere"), "...the Lightning Sphere at the top of the island (8 -> 9)")
    g.arrive_floor = ("LIGHTNING_ISLAND", 1, [23, 28])
    st = open_map("LIGHTNING_ISLAND", "SHAMOUTI_ISLAND"); _calm(st)
    st.run.player = (23, 28); st.anim = 0; st.step(0, 1)
    _drive("shamouti_lightning_done")
    check(story.story_flags.get("shamouti_lightning_done") and story.current_area_key == "SHAMOUTI_ISLAND",
          f"...going back, the birds fight overhead and a force carries you to the shrine (9 -> 10) ({story.current_area_key})")
    _play_scene("SHAMOUTI_ISLAND", (30, 32), (0, -1), "shamouti_lugia_rose", "LIGHTNING_ISLAND")   # (batch 29, Q59: come by the force)
    check(story.story_flags.get("shamouti_lugia_rose"), "...at the altar Lugia rises; Slowking sends you to Ice Island (10 -> 11)")
    _play_event("ICE_ISLAND", "ICE SPHERE")
    check(story.story_flags.get("shamouti_ice_sphere"), "...the Ice Sphere (11 -> 12)")
    _play_scene("SHAMOUTI_ISLAND", (30, 32), (0, -1), "shamouti_lugia_song", "ICE_ISLAND")   # (out of Ice Island's cave: the storm map)
    check(story.story_flags.get("shamouti_lugia_song"), "...the last sphere on the altar: Lugia's song calms the three birds (12 -> 13 -> 14)")
    st = open_map("FIRE_ISLAND", "SHAMOUTI_ISLAND")
    _figs = [i.get("text") for i in st._figure_items()]
    check("MOLTRES" in _figs, f"...and afterwards Moltres waits on Fire Island's summit (5.7's wild Lv 50) ({[f for f in _figs if f and f.isupper()]})")
    st = open_map("ICE_ISLAND", "SHAMOUTI_ISLAND")
    _figs = [i.get("text") for i in st._figure_items()]
    check("ARTICUNO" in _figs and "LUGIA" in _figs, f"...Articuno on Ice Island, and Lugia resting there too (ours: the dex counts it) ({[f for f in _figs if f and f.isupper()]})")
    for _f in ("beat_orange_champion", "move_offer_orange"):
        story.story_flags.pop(_f, None)

print("18) batch 23 (11-18): New Island (Tracey's MysticTicket, the Hamlin ferry, Mewtwo, Mew)")
if "NEW_ISLAND" in BUILT:
    for _f in ("orange_tracey_ivy", "orange_mystic_ticket", "orange_mew_1", "orange_mew_2", "orange_mew_3", "orange_mew_found"):
        story.story_flags.pop(_f, None)
    story.story_flags["shamouti_lugia_song"] = True
    _play_event("VALENCIA_ISLAND", "Tracey")
    check(story.story_flags.get("orange_tracey_ivy") and not story.story_flags.get("orange_mystic_ticket"),
          "after the story Tracey is in Ivy's lab; no ticket before 100 kinds of Kanto Pokemon caught (5.7's 0xD4 count)")
    _kc = story.kanto_caught_count
    story.kanto_caught_count = lambda: 100
    _play_event("VALENCIA_ISLAND", "Tracey")
    story.kanto_caught_count = _kc
    check(story.story_flags.get("orange_mystic_ticket"), "...with 100 caught he gives you the MysticTicket")
    from src.states.overworld.area_transition import ride_scene as _ride
    check(all(_ride(g, r) for r in ("oi_ferry_to_new_island", "oi_ferry_to_hamlin")),
          "the ferry's ride scenes load (5.7's ferry, sprite 226, over Hamlin's bay and New Island's jetty)")
    _play_event("HAMLIN_ISLAND", "Harbor clerk")
    for _ in range(900):
        if story.current_area_key == "NEW_ISLAND" and isinstance(g.current_state, DungeonState):
            break
        _db = getattr(g.current_state, "dialogue_box", None)
        if _db is not None and getattr(_db, "visible", False):
            _db.advance()
        frames(1)
    check(story.current_area_key == "NEW_ISLAND", f"...and Hamlin's ferry takes you to New Island, the ride scene on the way ({story.current_area_key})")
    st = open_map("NEW_ISLAND", "HAMLIN_ISLAND")
    _figs = [i.get("text") for i in st._figure_items()]
    check("MEWTWO" in _figs and "MEW" not in _figs, f"New Island: Mewtwo in the lab's back room (5.7's Lv 60) ({[f for f in _figs if f and f.isupper()]})")
    _ni = json.dumps(_area["NEW_ISLAND"]) + json.dumps(_tm["NEW_ISLAND"])
    check('"id": 151' not in _ni and "MEW\"" not in _ni.replace("MEWTWO", ""),
          "...and no Mew anywhere on New Island (Jordan 11-18, Q41: Mew = Kanto #150 only); the garden is still 5.7's")
    story.story_flags.pop("shamouti_lugia_song", None)

print("19) batch 24 (11-18): the Pokemon Showboat (the Pass, the play, Kay and her Raichu, the cabins)")
if "SHOWBOAT" in BUILT:
    for _f in ("got_showboat_pass", "orange_showboat_seen", "orange_showboat_show", "orange_kay_battle"):
        story.story_flags.pop(_f, None)
    check(_tm["KINNOW_ISLAND"]["exits"].get("n") == "SHOWBOAT" and len(_tm["SHOWBOAT"]["floors"]) == 13,
          "Kinnow's gangway leads aboard the Showboat: 13 rooms (every one 5.7 joins up)")
    st = open_map("KINNOW_ISLAND", "ORANGE_ROUTE_57"); _calm(st)
    st.player = (43, 33); st.anim = 0; st.step(0, 1); _drive("never_set_flag", n=200)
    check(story.current_area_key == "KINNOW_ISLAND", f"...without the Showboat Pass the deckhand turns you back (5.7's 43,33) ({story.current_area_key})")
    story.story_flags["got_showboat_pass"] = True
    st = open_map("KINNOW_ISLAND", "ORANGE_ROUTE_57"); _calm(st)
    st.player = (43, 33); st.anim = 0; st.step(0, 1)
    for _ in range(600):
        if isinstance(g.current_state, DungeonState):
            break
        _db = getattr(g.current_state, "dialogue_box", None)
        if _db is not None and getattr(_db, "visible", False):
            _db.advance()
        frames(1)
    check(story.current_area_key == "SHOWBOAT", f"...with it, up the gangway and aboard ({story.current_area_key})")
    g.arrive_floor = ("SHOWBOAT", 1, [22, 13])
    st = open_map("SHOWBOAT", "KINNOW_ISLAND")
    for _ in range(600):
        if isinstance(g.current_state, DungeonState) and g.current_state.run.index == 1:
            break
        _db = getattr(g.current_state, "dialogue_box", None)
        if _db is not None and getattr(_db, "visible", False):
            _db.advance()
        frames(1)
    st = g.current_state; _calm(st)
    st.run.player = (22, 13); st.anim = 0; st.step(0, -1)
    _drive("orange_showboat_show")
    check(story.story_flags.get("orange_showboat_show") and g.current_state.run.index == 2,
          f"...the play 'The Heroic Hitmonchan', then backstage (5.7's var 0x4019 0 -> 1) (floor {g.current_state.run.index})")
    _ky = next(o for o in _area["SHOWBOAT"]["route_menu"] if o["text"] == "Kay")["event"]
    ow._run_story_event(g.current_state, _ky, lambda c: g.current_state._check_route_condition(c, False), lambda l: None)
    _w = _drive("orange_kay_battle")
    check(story.story_flags.get("orange_kay_battle") and _ky["stages"][0]["battle"]["team"] == [26] and _ky["stages"][0]["battle"]["levels"] == [25],
          f"...Kay battles you to win her Raichu's trust (5.7's trainer 35, Raichu Lv 25) ({_w})")
    _tp = _area["SHOWBOAT"]["trainer_pool"]
    check(len(_tp) == 10 and sum(1 for f in _tm["SHOWBOAT"]["floors"] for r in f["art"] for c in r if c == "X") == 10,
          "the cabins: 5.7's ten Gentlemen, Sailors and the Juggler, each in their cabin")

print("20) batch 25 (11-18): the dive spots (the Scuba Gear: Route 58's and Route 60's seabeds)")
if "ORANGE_ROUTE_58" in BUILT and _tm["ORANGE_ROUTE_58"].get("floors"):
    for _k, _n in (("ORANGE_ROUTE_58", 2), ("ORANGE_ROUTE_60", 3)):
        _fl = _tm[_k]["floors"]
        _deep = [(x, y) for y, r in enumerate(_fl[0]["art"]) for x, c in enumerate(r) if c == ":"]
        check(len(_fl) == _n and _deep and _fl[0].get("dive") == 1 and _fl[1].get("surface") == 0,
              f"{_k}: 5.7's dive spots ({len(_deep)} deep tiles) over its seabed ({len(_fl)} floors)")
        story.inventory.pop("SCUBA_GEAR", None)
        st = open_map(_k, "KINNOW_ISLAND" if _k == "ORANGE_ROUTE_58" else "MORO_ISLAND"); _calm(st)
        _ok = [t for t in _deep if st.run.made(1).walkable(*t)]
        st.run.player = _ok[0]; st.anim = 0
        st.dive_here(); tap(st)
        check(st.run.index == 0, f"...without the Scuba Gear you can't dive ({st.run.index})")
        story.inventory["SCUBA_GEAR"] = 1
        story.story_flags["orange_joy_seabed"] = True   # (batch 28, Q48: she swims off as you first arrive: seen already here)
        st.dive_here(); frames(5)
        check(st.run.index == 1, f"...with it (Nurse Joy's gift) you dive to the seabed (floor {st.run.index})")
        st.surface_here(); frames(5)
        check(st.run.index == 0, f"...and come back up (floor {st.run.index})")
    story.inventory.pop("SCUBA_GEAR", None)

print("21) batch 27 (11-18): 5.7's switch puzzles (Fire Island's cave, Lightning Island's third switch, New Island's lab)")


def _press(st, at, face):
    """Stand on at, face the switch, and press the action key's CHECK (as a player does): what it said."""
    st.run.player = tuple(at); st.facing = tuple(face); st.anim = 0
    act = st._act_here()
    if not act or act[0] != "CHECK":
        return None
    heard, real = [], st.say
    st.say = lambda lines, then=None: (heard.extend(lines if isinstance(lines, list) else [lines]), real(lines, then))[1]
    try:
        act[1]()
        tap(st)
        if isinstance(g.current_state, _PLS):   # (batch 28, Q51: "Do you want to press it?" Yes)
            heard.append("[" + g.current_state.title + "]")
            g.current_state.pick(True)
            tap(st)
    finally:
        del st.say
    tap(st)
    return heard


from src.dungeon import art as _dart
if "FIRE_ISLAND" in BUILT and _tm["FIRE_ISLAND"]["floors"][0].get("secret_switches"):
    _FS = ["orange_fire_switch_" + c for c in "abcd"]
    for _f in _FS + ["shamouti_fire_sphere"]:
        story.story_flags.pop(_f, None)
    story.story_flags["heard_shamouti_legend"] = True
    st = open_map("FIRE_ISLAND", "SHAMOUTI_ISLAND"); _calm(st)
    _pic = _tm["FIRE_ISLAND"]["floors"][0]["roofs"]["_picture"]
    _fl = st.run.floor
    check(not _fl.walkable(26, 35) and not _fl.walkable(26, 32) and not _fl.walkable(22, 14) and not _fl.walkable(28, 6)
          and _dart._version_file(_pic).endswith("1_97_shut.png"), "Fire Island's cave: 5.7's four rock blocks shut as you come in (drawn shut)")
    _hop = st._step_route((0, *st.run.player), (1, 21, 30), "Fire Sphere")
    check(_hop and _hop[1] == "Switch" and tuple(_hop[0]) in ((45, 33), (6, 49)),
          f"...the Journal's marker leads to a secret switch first (A or B, 5.7's either order) ({_hop})")
    _hop = st._step_route((0, 28, 50), (0, 24, 14), "D")
    check(_hop and _hop[1] == "Switch", f"...the last switch (D, 25,14) is reached only once the others are pressed (5.7's order: A and B, C, D) ({_hop})")
    for (_at, _face, _flag, _rock) in (((44, 33), (1, 0), _FS[0], (26, 35)), ((6, 48), (0, 1), _FS[1], (26, 32)),
                                       ((51, 14), (0, -1), _FS[2], (22, 14)), ((24, 14), (1, 0), _FS[3], (28, 6))):
        _w = _press(st, _at, _face)
        check(story.story_flags.get(_flag) and st.run.floor.walkable(*_rock), f"...switch {_flag[-1].upper()}: a small tremor, its rocks move away ({_w})")
    check(_dart._version_file(_pic).endswith("1_97_open.png"), f"...all four pressed: drawn open (5.7's map) ({_dart._version_file(_pic)})")
    _w = _press(st, (44, 33), (1, 0))
    check(_w and "already" in " ".join(_w), f"...a switch pressed again says so ({_w})")
    _hop = st._step_route((0, 28, 50), (1, 21, 30), "Fire Sphere")
    check(_hop and _hop[1] != "Switch", f"...then the marker leads straight up to the summit ({_hop})")
if "LIGHTNING_ISLAND" in BUILT and _tm["LIGHTNING_ISLAND"]["floors"][0].get("secret_switches"):
    story.story_flags.pop("orange_lightning_switch", None)
    story.story_flags.update({"shamouti_palace_crash": True, "orange_lightning_switch_a": True, "orange_lightning_switch_b": True})   # (the crash's: 5.7's var 3)
    st = open_map("LIGHTNING_ISLAND", "SHAMOUTI_ISLAND"); _calm(st)
    _pic = _tm["LIGHTNING_ISLAND"]["floors"][0]["roofs"]["_picture"]
    check(not st.run.floor.walkable(23, 7) and st.run.floor.walkable(32, 21) and _dart._version_file(_pic).endswith("1_81_shut.png"),
          "Lightning Island: after the crash its rocks and two switches are moved (5.7's var 3), the third switch's rocks still shut")
    _hop = st._step_route((0, 36, 11), (1, 23, 22), "Lightning Sphere")
    check(_hop and _hop[1] == "Switch" and tuple(_hop[0]) == (39, 11), f"...the marker leads to the third switch (5.7's 39,11) ({_hop})")
    _w = _press(st, (3, 34), (1, 0)) or _press(st, (4, 34), (0, 1))
    check(_w and "already" in " ".join(_w) and not story.story_flags.get("orange_lightning_switch"), f"...a switch the crash pressed says so ({_w})")
    _w = _press(st, (38, 11), (1, 0))
    check(story.story_flags.get("orange_lightning_switch") and st.run.floor.walkable(23, 7) and _dart._version_file(_pic).endswith("1_81_open.png"),
          f"...pressed: a tremor, the way up opens ({_w})")
if "NEW_ISLAND" in BUILT and _tm["NEW_ISLAND"]["floors"][1].get("switch"):
    _L1, _L2 = "orange_lab_switch_1", "orange_lab_switch_2"
    for _f in (_L1, _L2):
        story.story_flags.pop(_f, None)
    story.story_flags.update({"orange_mystic_ticket": True, "shamouti_lugia_song": True})
    g.arrive_floor = ("NEW_ISLAND", 1, [18, 32])
    st = open_map("NEW_ISLAND", "HAMLIN_ISLAND"); _calm(st)
    check(st.run.index == 1 and not st.run.floor.walkable(9, 24) and st.run.floor.walkable(29, 6) and not st.run.floor.walkable(27, 27),
          "New Island's lab: 5.7's barriers as it starts (both switches off)")
    _r = {n: st._step_route((1, 18, 32), t, n) for n, t in (("Mewtwo", (3, 15, 12)), ("Master Ball", (2, 27, 21)), ("PP Up", (3, 27, 27)), ("Iron", (1, 3, 32)))}
    check(all(_r.values()), f"...every corner of the lab can be reached by working the two switches (marker: {_r})")
    _w = _press(st, (34, 32), (0, -1))
    check(story.story_flags.get(_L2) and st.run.floor.walkable(9, 24) and not st.run.floor.walkable(29, 6),
          f"...1F's statue switch (5.7's 0x274): one barrier opens, another shuts ({_w})")
    _pic = _tm["NEW_ISLAND"]["floors"][1]["roofs"]["_picture"]
    check(_dart._version_file(_pic).endswith("1_59_b.png"), "...drawn as 5.7 draws it then")
    _press(st, (34, 32), (0, -1))
    check(not story.story_flags.get(_L2) and not st.run.floor.walkable(9, 24) and st.run.floor.walkable(29, 6), "...pressed again, back the other way")
    g.arrive_floor = ("NEW_ISLAND", 2, [11, 4])
    st = open_map("NEW_ISLAND", "HAMLIN_ISLAND"); _calm(st)
    _w = _press(st, (4, 6), (0, -1))
    check(st.run.index == 2 and story.story_flags.get(_L1) and st.run.floor.walkable(16, 16) and not st.run.floor.walkable(14, 30),
          f"...2F's statue switch (5.7's 0x273) swings 2F's barriers ({_w})")
    story.story_flags[_L2] = True
    g.arrive_floor = ("NEW_ISLAND", 3, [8, 28])
    st = open_map("NEW_ISLAND", "HAMLIN_ISLAND"); _calm(st)
    check(st.run.index == 3 and not st.run.floor.walkable(15, 19), "...in the back room, with 1F's switch on, a barrier shuts Mewtwo's room")
    _w = _press(st, (14, 31), (0, -1))
    check(not story.story_flags.get(_L2) and st.run.floor.walkable(15, 19), f"...its own statue (0x274 again) opens it ({_w})")
    for _f in (_L1, _L2, "orange_mystic_ticket", "shamouti_lugia_song"):
        story.story_flags.pop(_f, None)

if _area.get("SHAMOUTI_ISLAND", {}).get("story_weather"):
    from src.world import seasons as _seas
    _was = {f: story.story_flags.get(f) for f in ("shamouti_lightning_done", "shamouti_lugia_song")}
    story.story_flags.pop("shamouti_lightning_done", None); story.story_flags.pop("shamouti_lugia_song", None); story.story_flags.pop("shamouti_sphere_set", None)
    for _f in ("shamouti_palace_crash", "heard_shamouti_legend"):   # (batch 28: 5.7's rain and snow before the storm come with these)
        _was[_f] = story.story_flags.pop(_f, None)
    _w0 = _seas.area_weather(g, "SHAMOUTI_ISLAND")
    story.story_flags["shamouti_lightning_done"] = True
    st = open_map("SHAMOUTI_ISLAND", "LIGHTNING_ISLAND"); frames(3)   # (batch 29, Q59: by the force: the storm map, its snow)
    _w1 = _seas.area_weather(g, "SHAMOUTI_ISLAND")
    _drawn = isinstance(st, _WTS) and (_seas.story_weather(g, "SHAMOUTI_ISLAND") or {}).get("show") == "snow"
    story.story_flags["shamouti_sphere_set"] = True   # (batch 28: the storm ends as the Ice Sphere is set: 5.7's setweather 2)
    _w2 = _seas.area_weather(g, "SHAMOUTI_ISLAND")
    story.story_flags.pop("shamouti_sphere_set", None)
    check(_w0 != "SNOW" and _w1 == "SNOW" and _w2 != "SNOW" and _drawn,
          f"Shamouti's storm (5.7's 3.60, snow): from the force that carries you to the shrine until the Ice Sphere is set, snow falls ({_w0}, {_w1}, {_w2})")
    for _f, _v in _was.items():
        if _v:
            story.story_flags[_f] = _v
        else:
            story.story_flags.pop(_f, None)

print("22) batch 28 (11-18): Jordan's answers: no Mew, 5.7's gating, switches that ask, the storm map, the hotel lift, scenes played out")
from src.dungeon import npc as _npc
from src.states.overworld import walk_town as _wt
_SEEN = {"actors": 0, "shakes": 0, "looks": 0}
_ct = _npc.Scenes._cast_tick


def _ct_watch(self, s, st):   # (how many of a scene's cast were out at once: a scene played out, not told in lines)
    r = _ct(self, s, st)
    _SEEN["actors"] = max(_SEEN["actors"], len(self.actors) + sum(1 for a in st.get("by", {}).values() if a.get("person") and not a.get("ghost") and a["m"].path))
    return r


_npc.Scenes._cast_tick = _ct_watch


def _played(key, at, step, flag, came, floor=None, n=6000):
    _SEEN["actors"] = 0
    if floor is not None:
        g.arrive_floor = (key, floor, list(at))
    w = _play_scene(key, at, step, flag, came, n=n)
    return w is not None and story.story_flags.get(flag), _SEEN["actors"]


_dl = g.loader.area_data["REGION_START"]["ORANGE"]["dex_list"]
_isl = [g.loader.area_data.get(f"ORANGE_{k}_PERCENTAGES") or {} for k in ("FIRE_ISLAND", "LIGHTNING_ISLAND", "ICE_ISLAND")]
check(all(p in _dl for p in (68, 236, 238, 239, 240)) and not any(str(p) in t for t in _isl for p in (236, 238, 239, 240, 68)),
      "Q35: no Magby, Elekid, Tyrogue, Machamp or Smoochum on the islands (5.7's own tables); in the dex since they come other ways (11-19: the roof Eggs, the Tyrogue gift, the Linking Cord; D1 11-23)")
_sh = _area["SHAMOUTI_ISLAND"]
_tr = {o["target_area"]: o.get("condition") for o in _sh["travel_options"]}
_bars = {tuple(t): b["until"]["flag_condition"] for b in _tm["SHAMOUTI_ISLAND"]["barred"] for t in b["tiles"]}
check(_tr.get("LIGHTNING_ISLAND") == "heard_shamouti_legend" and _bars.get((6, 59)) == "heard_shamouti_legend" and _bars.get((20, 60)) == "shamouti_lugia_rose"
      and (25, 67) not in _bars, f"Q31: 5.7's gating: Fire and Lightning's caves after Melody's play, Ice behind 5.7's rocks at its stairs (20-21,60) till Lugia rises ({_bars})")
# the switches ask first (Q51): No leaves it, "Maybe later."
for _f in ("orange_fire_switch_a", "orange_fire_switch_b", "orange_fire_switch_c", "orange_fire_switch_d"):
    story.story_flags.pop(_f, None)
story.story_flags["heard_shamouti_legend"] = True
st = open_map("FIRE_ISLAND", "SHAMOUTI_ISLAND"); _calm(st)
st.run.player = (44, 33); st.facing = (1, 0); st.anim = 0
_act = st._act_here(); _heard = []
_real = st.say
st.say = lambda lines, then=None: (_heard.extend(lines if isinstance(lines, list) else [lines]), _real(lines, then))[1]
_act[1](); tap(st)
_asked = isinstance(g.current_state, _PLS) and g.current_state.title == "PRESS THE SWITCH?"
if _asked:
    g.current_state.pick(False); tap(st)
del st.say
check(_asked and not story.story_flags.get("orange_fire_switch_a") and "Maybe later." in _heard and any("press it" in h for h in _heard),
      f"Q51: a secret switch asks first, as 5.7: No, and it's 'Maybe later.' ({_heard})")
_w = _press(st, (44, 33), (1, 0))
check(story.story_flags.get("orange_fire_switch_a") and getattr(st, "_shake_until", 0), f"...Yes: pressed, and the tremor shakes the screen (Q52) ({_w})")
story.story_flags.pop("orange_fire_switch_a", None)
# Lightning Island before the crash (5.7: open after the play; its own rocks and A / B)
for _f in ("shamouti_palace_crash", "orange_lightning_switch_a", "orange_lightning_switch_b", "orange_lightning_switch"):
    story.story_flags.pop(_f, None)
st = open_map("LIGHTNING_ISLAND", "SHAMOUTI_ISLAND"); _calm(st)
_fl = st.run.floor
check(not _fl.walkable(23, 17) and not _fl.walkable(32, 21) and not _fl.walkable(37, 11) and _dart._version_file(_tm["LIGHTNING_ISLAND"]["floors"][0]["roofs"]["_picture"]).endswith("1_81_pre.png"),
      "Lightning Island after the play, before the crash: 5.7's rocks shut (A's, B's, the crash's), drawn so")
_press(st, (4, 34), (0, 1))
check(story.story_flags.get("orange_lightning_switch_a") and st.run.floor.walkable(23, 17) and not st.run.floor.walkable(37, 11),
      "...switch A (4,35) is yours to press then: its rocks move; the crash's stay shut")
story.story_flags.pop("orange_lightning_switch_a", None)
_pe = next(sc for sc in _tm["LAWRENCE_SHIP"]["floors"][0]["scenes"])["event"]
check(set(_pe.get("also_flags") or []) == {"orange_lightning_switch_a", "orange_lightning_switch_b"}, "...and the palace's crash presses A and B (5.7's var 3)")
# the storm map (Q57)
_sm = (_tm["SHAMOUTI_ISLAND"].get("story_maps") or [{}])[0]
check(_sm.get("when") == ["shamouti_lightning_done", "not:shamouti_sphere_set"] and "3_60f" in json.dumps(_sm.get("map", {}).get("roofs")) and _sm["map"].get("view_top") == 20,
      "Q57: Shamouti's storm map is 5.7's 3.60 (in Shamouti's frame), from the force until the Ice Sphere is set")
for _f in ("shamouti_lugia_rose", "shamouti_ice_sphere", "shamouti_sphere_set", "shamouti_lugia_song"):
    story.story_flags.pop(_f, None)
story.story_flags["shamouti_lightning_done"] = True
st = open_map("SHAMOUTI_ISLAND", "LIGHTNING_ISLAND")
_cx, _cy = st._camera() if isinstance(st, _WTS) else (0, 0)
check(isinstance(st, _WTS) and st.town_map is _wt.story_map(g, "SHAMOUTI_ISLAND") and st.town_map is not _wt.custom(g).get("SHAMOUTI_ISLAND") and "3_60f" in st._pic_now
      and _cy - st._view().h / 2 >= 20 * 48 - 1 and (0, 59) not in st.exits and any(t == "ICE_ISLAND" for t in st.exits.values()),
      f"...walked on it: snowy ground, the sea frozen and walked on, the view kept off the empty north ({st._pic_now if isinstance(st, _WTS) else st})")
_ok, _n = _played("SHAMOUTI_ISLAND", (30, 32), (0, -1), "shamouti_lugia_rose", "LIGHTNING_ISLAND")
check(_ok and _n >= 3, f"...on it Lugia rises, the three birds fight over the frozen sea, played out ({_n} on the stage at once)")
story.story_flags["shamouti_ice_sphere"] = True
_ok, _n = _played("SHAMOUTI_ISLAND", (30, 32), (0, -1), "shamouti_lugia_song", "ICE_ISLAND")
st = g.current_state
check(_ok and story.story_flags.get("shamouti_sphere_set") and isinstance(st, _WTS) and st.town_map is _wt.custom(g).get("SHAMOUTI_ISLAND") and _n >= 3,
      f"...the Ice Sphere set, the storm breaks: Shamouti as it was, and Lugia's song is played out there ({_n})")
# Q59 (batch 29): only the caves, the festival house and the force lead to the storm map; Fly and the sea, to Shamouti as it is
story.story_flags.pop("shamouti_ice_sphere", None); story.story_flags.pop("shamouti_sphere_set", None); story.story_flags.pop("shamouti_lugia_song", None)
story.story_flags["shamouti_lugia_rose"] = True
st = open_map("SHAMOUTI_ISLAND", "ORANGE_ROUTE_67")
_by_sea = isinstance(st, _WTS) and st.town_map is _wt.custom(g).get("SHAMOUTI_ISLAND") and (20, 60) not in st.barred
st._go("festival", "OUT:9,33"); frames(2); st._go(None, "OUT:9,33"); frames(2)
_fest = st.town_map is _wt.story_map(g, "SHAMOUTI_ISLAND") and st.town_map is not _wt.custom(g).get("SHAMOUTI_ISLAND")
st = open_map("SHAMOUTI_ISLAND", "FIRE_ISLAND")
_cave = st.town_map is not _wt.custom(g).get("SHAMOUTI_ISLAND")
check(_by_sea and _fest and _cave, f"Q59: by sea or Fly in the storm, Shamouti as it is (Ice Island's stairs open, as 5.7); out of the festival house or a cave, the storm map ({_by_sea}, {_fest}, {_cave})")
# Q63: 5.7's own Lugia in its scenes, at its own size; the birds our followers
_ls = [c for sc in (_tm["SHAMOUTI_ISLAND"]["story_maps"][0]["map"]["scenes"] + _tm["SHAMOUTI_ISLAND"]["scenes"]) for c in sc.get("cast") or []
       if c.get("sheet") and ("138" in c["sheet"] or c["sheet"] == "mon:249")]
check(_ls and all(c["sheet"] == "oi_138.png" and c.get("native") for c in _ls) and os.path.exists("assets/dungeon/characters/oi_138.png"),
      f"Q63: Lugia flies as 5.7's own sprite (sheet 138, its own size) in its scenes; Moltres, Zapdos, Articuno stay our followers ({len(_ls)})")
# Q64: the shrine's pillars light up in the song
_pp = [c.get("picture") for c in _tm["SHAMOUTI_ISLAND"]["scenes"][-1]["cast"] if c.get("picture")]
check(len(_pp) >= 7 and all(os.path.exists(f"assets/tiles/oi_ground/{p}.png") for p in set(_pp)), f"Q64: 5.7's pillar flashes are drawn during Lugia's song ({len(_pp)} flashes)")
for _f in ("shamouti_lugia_rose", "shamouti_ice_sphere", "shamouti_sphere_set", "shamouti_lugia_song", "shamouti_lightning_done", "heard_shamouti_legend"):
    story.story_flags.pop(_f, None)
# the hotel lift (Q8)
story.story_flags.update({"orange_luana_met": True, "orange_luana_hotel": True})
_k = _tm["KUMQUAT_ISLAND"]["rooms"]
check("lift" in _k and "lift_down" not in _k and "ROOM:lift" in _k["gym"]["exits"].values() and "ROOM:lift" in _k["top_floor"]["exits"].values()
      and (_k["lift"].get("dynamic_exit") or {}).get("rooms") == ["gym", "top_floor"],
      "Q8 / Q61: the Kumquat Hotel's lift is 5.7's one lift car (39.0), its doors on the floor its attendant picks")
st = open_map("KUMQUAT_ISLAND", "ORANGE_ROUTE_69")
_in, _c = _ride_lift(st, "top_floor")
check(_in == "lift" and isinstance(_c, _WTS) and _c.room == "top_floor" and tuple(_c.player) == (2, 6),
      f"...you walk into the car, its attendant asks which floor, and its doors open on the top floor ({_in}, {getattr(_c, 'room', None)}, {getattr(_c, 'player', None)})")
_c._go("lift", "ROOM:top_floor"); frames(3); _tap = [0]
for _ in range(300):   # (in again from the top floor: say nothing, BACK: its doors stay on the top floor)
    _x = g.current_state
    if isinstance(_x, _PLS):
        _x.pick(None); continue
    if getattr(_x, "npc_active", False):
        tap(_x, 3)
    _x.update(); _x.draw()
    if isinstance(_x, _WTS) and not _x._busy() and not _x.npc_active:
        break
_c = g.current_state
_out = [t for t, v in _c.exits.items() if str(v).startswith("ROOM:")]
_c.player = (_out[0][0], _out[0][1] - 1); _c.anim = 0; _c.step(0, 1); frames(30); tap(_c)
check(g.current_state.room == "top_floor", f"...and with no floor picked its doors open where you got in, as 5.7's dynamic warp ({g.current_state.room})")
# scenes played out (Q44 and the rest)
for _f in ("orange_showboat_show", "orange_showboat_seen"):
    story.story_flags.pop(_f, None)
_ok, _n = _played("SHOWBOAT", (22, 13), (0, -1), "orange_showboat_show", "KINNOW_ISLAND", floor=1)
check(_ok and _n >= 4, f"Q44: the Showboat's play played out: Hitmonchan, Machoke, Abra and Clefable on the stage together ({_n})")
story.story_flags["orange_kay_battle"] = True
st = open_map("SHOWBOAT", "KINNOW_ISLAND")
_fans = [p for p in _tm["SHOWBOAT"]["floors"][1]["people"] if isinstance(p, dict) and str(p.get("text", "")).startswith("Fan")]
check(_fans and all(p.get("flag_condition") == "not orange_kay_battle" for p in _fans), "Q45: the theatre's fans and the voice actors leave after Kay's battle (5.7's hide flags)")
story.story_flags.pop("orange_kay_battle", None)
story.story_flags.update({"got_whirlpuller_trovita": True})
story.story_flags.pop("orange_fairchild_rocket", None)
_ok, _n = _played("FAIRCHILD_ISLAND", (42, 34), (0, 1), "orange_fairchild_rocket", "ORANGE_ROUTE_56")
check(_ok and _n >= 3, f"Fairchild: Jessie, James and Meowth run past you, played out ({_n})")
story.story_flags.pop("orange_wartortle_taken", None)
_ok, _n = _played("ASCORBIA_ISLAND", (10, 22), (0, -1), "orange_wartortle_taken", "ORANGE_ROUTE_68")
check(_ok and _n >= 1, f"Ascorbia: the Meowth balloon carries Team Wartortle off, Aidan runs up ({_n})")
for _f in ("orange_hamlin_explosion", "orange_hamlin_electrode", "orange_hamlin_diglett", "orange_hamlin_fields"):
    story.story_flags.pop(_f, None)
_ok, _n = _played("HAMLIN_ISLAND", (13, 18), (1, 0), "orange_hamlin_explosion", "ORANGE_ROUTE_74")
check(_ok and _n >= 1, f"Hamlin: an Electrode rolls up the street, played out ({_n})")
story.story_flags["orange_hamlin_electrode"] = True
_ok, _n = _played("HAMLIN_ISLAND", (13, 18), (1, 0), "orange_hamlin_diglett", "ORANGE_ROUTE_74")
check(_ok and _n >= 8, f"...the Electrode close in, Poncho's Diglett and Dugtrio dig them away ({_n})")
st = open_map("HAMLIN_FIELDS", "HAMLIN_ISLAND")
_tp = _area["HAMLIN_FIELDS"]["trainer_pool"]
check(all(t.get("when_flags") == ["orange_hamlin_diglett"] for t in _tp), "Q26: Hamlin Fields' four trainers come out with the Diglett scene (5.7)")
_ok, _n = _played("HAMLIN_FIELDS", (11, 23), (-1, 0), "orange_hamlin_fields", "HAMLIN_ISLAND")
check(_ok and _n >= 3, f"...in the Fields the Electrode roll about happily, Poncho comes over ({_n})")
story.story_flags.pop("orange_joy_seabed", None)
story.inventory["SCUBA_GEAR"] = 1
g.arrive_floor = ("ORANGE_ROUTE_58", 1, [30, 15])
_SEEN["actors"] = 0
st = open_map("ORANGE_ROUTE_58", "KINNOW_ISLAND"); _calm(st)
_drive("orange_joy_seabed", n=3000)
check(story.story_flags.get("orange_joy_seabed") and _SEEN["actors"] >= 1, f"Q48: on the seabed Nurse Joy and her Shellder swim off as you arrive ({_SEEN['actors']})")
story.inventory.pop("SCUBA_GEAR", None)
# Q66 (batch 29): the last beats played out
story.story_flags.pop("orange_park_done", None); story.story_flags.pop("orange_park_seen", None)
g.arrive_floor = None
st = open_map("VALENCIA_PARK", "VALENCIA_ISLAND"); _calm(st)
_SEEN["actors"] = 0
_iv = next((m for m in st.run.floor.movers if m.kind == "figure" and (m.payload or {}).get("text") == "Professor Ivy"), None)
if _iv is not None:
    st.run.player = (_iv.x - 1, _iv.y); st.facing = (1, 0); st.anim = 0   # (beside her: Brock stands below)
    st.step(1, 0)   # (walk into her: talk)
_drive("orange_park_done", n=5000)
check(story.story_flags.get("orange_park_done") and _SEEN["actors"] >= 5, f"Q66: Valencia Park's Vileplume dance, the Stun Spore catches Raticate and Ivy, played out ({_SEEN['actors']})")
story.story_flags.update({"orange_bulbasaur_found": True}); story.story_flags.pop("orange_mayor_exposed", None)
_SEEN["actors"] = 0
st = open_map("TROVITOPOLIS", "ORANGE_ROUTE_64"); st._go("mayor_office", "OUT:11,16"); frames(2)
st.player = (7, 9); st.anim = 0; st.step(0, -1); _drive("orange_mayor_exposed", n=4000)
check(story.story_flags.get("orange_mayor_exposed") and _SEEN["actors"] >= 3, f"...the Mayor's office: Jenny, Joy and the Bulbasaur ({_SEEN['actors']})")
for _f in ("orange_quack_met", "orange_quack_rind", "orange_quack_ritual", "orange_quack_sea"):
    story.story_flags.pop(_f, None)
_ok, _n = _played("ORANGE_ROUTE_71", (19, 20), (0, -1), "orange_quack_met", "ORANGE_ROUTE_70")
check(_ok and _n >= 4, f"...Quackenpoker's Magikarp swim for Rind Island ({_n})")
_ok, _n = _played("RIND_ISLAND", (30, 33), (0, -1), "orange_quack_rind", "ORANGE_ROUTE_71")
_ok2, _n2 = _played("RIND_ISLAND", (31, 12), (0, -1), "orange_quack_ritual", "ORANGE_ROUTE_71")
_ok3, _n3 = _played("ORANGE_ROUTE_71", (19, 20), (0, -1), "orange_quack_sea", "RIND_ISLAND")
check(_ok and _ok2 and _ok3 and min(_n, _n2, _n3) >= 3, f"...up the falls, the ritual at the lake (Gyarados), out to sea ({_n}, {_n2}, {_n3})")
story.story_flags["orange_salveyo_asked"] = True; story.story_flags.pop("got_salveyo_weed", None)
_ok, _n = _played("SALVEYO_ISLAND", (19, 23), (0, 1), "got_salveyo_weed", "ORANGE_ROUTE_72")
check(_ok, f"...Salveyo's Poliwag dives and brings the weed ({_n})")
story.story_flags.pop("orange_magnemite_seen", None)
_ok, _n = _played("ORANGE_ROUTE_64", (74, 20), (0, 1), "orange_magnemite_seen", "YAMBERA")
check(_ok and _n >= 4, f"...Route 64: Team Rocket haul their machine across the dunes, the Magnemite trailing ({_n})")
for _f in ("orange_quack_met", "orange_quack_rind", "orange_quack_ritual", "orange_quack_sea", "orange_salveyo_asked", "got_salveyo_weed", "orange_magnemite_seen"):
    story.story_flags.pop(_f, None)
# Q15, Q21, Q28
_q = next(o for o in _area["ORANGE_ROUTE_71"]["route_menu"] if o["text"] == "Quackenpoker")
story.story_flags["orange_quack_met"] = True; story.story_flags.pop("orange_quack_ritual", None)
st = open_map("ORANGE_ROUTE_71", "ORANGE_ROUTE_70")
_away = "Quackenpoker" not in [i.get("text") for i in st._figure_items()]
story.story_flags["orange_quack_ritual"] = True
st = open_map("ORANGE_ROUTE_71", "ORANGE_ROUTE_70")
check(_away and "Quackenpoker" in [i.get("text") for i in st._figure_items()], "Q15: Quackenpoker is away while he's up the river (5.7's hide flag), back after the ritual")
for _f in ("orange_quack_met", "orange_quack_ritual"):
    story.story_flags.pop(_f, None)
_lg = _tm["PUMMELO_ISLAND"]["rooms"]["league"].get("barred") or []
check(len([b for b in _lg if b.get("scenery")]) == 11, "Q21: the arena's eleven fans sit in the stands, scenery you can't reach or talk to")
_ta = _tm["TARROCO_ISLAND"]
check(_ta["art"][31][47] in _ta["exits"] and _tm["ORANGE_ROUTE_74"]["art"][31][0] in _tm["ORANGE_ROUTE_74"]["exits"],
      "Q28: you can sail into Tarroco's south-east sea pocket from Route 74's row 31, as 5.7")

print("23) batch 30 (11-18, Jordan's Q70): every scene's swimmers keep to water and its walkers to ground (flyers cross anything)")
_otools = os.environ.get("ORANGE_TOOLS") or next((os.path.join(_d, "kanto_handoff", "orange_rom_tools") for _d in
           [os.path.abspath(os.path.join(os.getcwd(), *[".."] * _n)) for _n in range(1, 8)]
           if os.path.isdir(os.path.join(_d, "kanto_handoff", "orange_rom_tools"))), "")   # (main folder or a worktree, 11-23)
_osp = _u.spec_from_file_location("oscenepaths", os.path.join(_otools, "oscenepaths.py"))
_osm = _u.module_from_spec(_osp); _osp.loader.exec_module(_osm)
_bad = _osm.report(_oi.ORANGE)
_n = sum(1 for _ in _osm.every_scene(_oi.ORANGE))
check(not _bad, f"the moves of {_n} scenes, as the game routes them: no swimmer or walker on rock, shore or wall, none short of its stop ({_bad[:3]})")

print(f"##### {len(fails)} failures")
