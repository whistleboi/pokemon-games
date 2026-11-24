# Johto on the route walker: every place from SoulSilver - towns, caves and their stairs, buildings, gatehouses,
# Victory Road, the Safari Zone, the Bug-Catching Contest (split from dungeon 11-23).
#   bash dev/checks/run.sh dungeon_johto
exec(open("dev/checks/dungeon_lib.py", encoding="utf-8").read())
g.dungeon_routes = True

# every region (Jordan, 11-05: each region's maps checked against its games)
_want = {"HAINA_DESERT": "desert", "ASADO_DESERT": "desert", "GLASEADO_MOUNTAIN": "snow",
         "HOENN_TRACKLESS_FOREST": "forest", "SPROUT_TOWER": "field", "MOUNT_LANAKILA": "snow"}  # (Sprout Tower: our own exact floors now;
# Pledge Grove: Black 2's own map and picture since 11-20, the Desert Resort since 11-21: unova suites)
_got = {k: _dg.recipe_for(g, k).get("style") for k in _want}
check(_got == _want, f"each region's places look like its game's {[(k, v) for k, v in _got.items() if _want[k] != v]}")
_fl = {k: _dg.recipe_for(g, k).get("floors") for k in ("UNION_CAVE", "BELL_TOWER", "MT_CORONET_BASE", "CHARGESTONE_CAVE", "REFLECTION_CAVE")}
check(all((v or 1) > 1 for v in _fl.values()), f"the big dungeons have their floors {_fl}")
_bt = kanto("BELL_TOWER", came="ECRUTEAK_CITY")
check(_bt.run.n_floors == 11 and _bt._figure_floor({"text": "TALK TO SAGE LI", "action": "NPC"}, 11) == 0 and _bt._figure_floor({"text": "CHALLENGE HO-OH", "action": "BOSS"}, 11) == 10,
      "Bell Tower: SoulSilver's ten floors and roof; the sage at the entrance, Ho-Oh on the roof")

# the Johto Safari Zone (N19, 11-16): SoulSilver's own twelve areas (land 652-663) in HGSS's ten default layouts, one floor each;
# the receptionist's Area Setup picks the layout (story flag safari_layout); Hoenn's Safari Game (30 Safari Balls, 500 steps)
_jz = _prog["JOHTO_SAFARI_ZONE"]
_sv57 = story.story_flags.get("safari_layout")
_lay57 = {}
for _l in (0, 5, 9):
    story.story_flags["safari_layout"] = _l
    _js = kanto("JOHTO_SAFARI_ZONE", came="SAFARI_ZONE_GATE")
    _lay57[_l] = (_js.run.index, tuple(_js.run.player), [_js.zones[_js._zone_index(_js.run.index, _x, _y)] for _x, _y in ((10, 10), (40, 10), (75, 10), (10, 45), (40, 45), (75, 45))])
story.story_flags["safari_layout"] = _sv57
check(_js.run.n_floors == 10 and [_lay57[_l][0] for _l in (0, 5, 9)] == [0, 5, 9] and _lay57[0][2] == ["plains", "swamp", "meadow", "wetland", "peak", "forest"]
      and _lay57[5][2] == ["marshland", "plains", "wasteland", "mountain", "peak", "savannah"] and all(_lay57[_l][1] == (47, 67) for _l in _lay57),
      f"the Johto Safari Zone: ten layouts of SoulSilver's areas, in by the gatehouse below the Peak; Area Setup picks the layout {_lay57}")
check(getattr(_js, "safari", None) and _js.safari["balls"] == 30, "...the Safari Game: 30 Safari Balls a visit, as in Hoenn's")

# the Bug-Catching Contest (Jordan, 11-05): National Park, its own map
check(_dg.CONTEST_DAYS == tuple(range(7)), "the contest is open any day (once a day)")
story.story_flags.pop("bug_contest_day", None)
_np = kanto("NATIONAL_PARK", came="JOHTO_ROUTE_35")
_off = [m for m in _np.run.floor.movers if m.kind == "figure" and m.payload.get("action") == "BUG_CONTEST"]
check(_off, "National Park: the contest officer stands on the map")
_dg.contest_entry(_np)
talk(_np)
for _ in range(400):
    g.current_state.update()
    if isinstance(g.current_state, DungeonState):
        break
_bc = g.current_state
check(isinstance(_bc, DungeonState) and _bc.area_key == "BUG_CONTEST" and _bc.contest and _bc.contest["balls"] == 20,
      "the officer: the contest's map, 20 Sport Balls")
_bugs = {int(k) for k in g.loader.area_data["JOHTO_BUG_CONTEST_PERCENTAGES"]}
_wild = [m for m in _bc.run.floor.movers if m.kind == "wild"]
check(_wild and all(m.payload.id in _bugs or str(m.payload.id).startswith(tuple(str(b) for b in _bugs)) for m in _wild),
      f"only Bug Pokemon roam it ({sorted({m.payload.id for m in _wild})})")
_bc.draw()
_m = _wild[0]
_bc._meet_wild(_m)
_bc._pick(1)
check(_bc.mode == "CHOICE", "no BATTLE in the contest (MATH only)")
_bc._start_math()
_bc._answer(_bc.options.index(_bc.correct_ans))
check(_bc.contest["balls"] == 19, "a throw uses a Sport Ball (not your own)")
_bc.throw_result = "caught"
_bc._resolve_throw()
talk(_bc)
check(_bc.contest["best"] is _m.payload, "the catch is your contest Pokemon")
_team = len(story.player_team) + len([x for x in story.pc_pokemon if x])
_bc.mode, _bc.anim = "MAP", 0
_bc.contest["turns"] = 0
_bc._contest_check()
_lines = list(_bc.dialogue_box.text_lines)
check(any("scored" in l for l in _lines) and any("yours to keep" in l for l in _lines), f"time's up: the judging {_lines[:3]}")
check(len(story.player_team) + len([x for x in story.pc_pokemon if x]) == _team + 1, "you keep your bug")
talk(_bc)
for _ in range(400):
    g.current_state.update()
    if isinstance(g.current_state, DungeonState) and g.current_state is not _bc:
        break
check(story.current_area_key == "NATIONAL_PARK", "...and you're back in National Park")
_np2 = kanto("NATIONAL_PARK", came="JOHTO_ROUTE_35")
_dg.contest_entry(_np2)
check(any("already" in l for l in _np2.dialogue_box.text_lines), "once a day")
# (Hoenn's Safari Zone: rebuilt in a coming batch; its old check is in kanto_handoff/hoenn_rom_tools/old_hoenn_checks.py)

g.walk_towns = True
# the Johto pilot (Jordan, 11-06): our own maps, laid out after Pokemon Journeys' (New Bark, Route 29, Cherrygrove)
g.walk_town_pos = None
story.story_flags["received_starter_johto"] = True
story.story_flags["move_offer_johto"] = True
story.current_area_key, story.last_area_key = "NEW_BARK_TOWN", None
_nb = _CS(g); g.change_state(_nb); _tap_through(_nb)
_nb_out = sorted((o.get("text") for o in _nb._people().values() if isinstance(o, dict)), key=str)
check(isinstance(_nb, _WTS) and {"lab", "home", "rival", "elmhouse"} <= set(_nb.doors.values()) and _nb_out == ["Marill", "Woman"]
      and (_nb.w, _nb.h) == (32, 32) and len(_nb.signs) == 7,
      f"New Bark Town: SoulSilver's own 32 x 32 map, doors for Elm's Lab, your house, Silver's mom's and Elm's house, its signs, the woman and Marill outside ({_nb_out})")
_nb_rd = next(t for t, k in _nb.doors.items() if k == "rival")
_nb._enter(_nb_rd)
check(_nb.room == "rival" and len(_nb.people) == 1, f"Silver's mom's door: you walk into her house (SoulSilver's own room), the Nice Lady standing there {_nb.room, len(_nb.people)}")
_nb._talk(next(iter(_nb.people)))
check(_nb.npc_active and _nb.current_npc == "silver_mom", "...talk to her: the Nice Lady")
_tap_through(_nb)
_nb._leave("OUT:%d,%d" % _nb_rd)
check(_nb.room is None and _nb.player == (_nb_rd[0], _nb_rd[1] + 1), f"...and back out below her door {_nb.player}")
_nb_eh = next(t for t, k in _nb.doors.items() if k == "elmhouse")
_nb._enter(_nb_eh)
check(_nb.room == "elmhouse" and [o.get("text") for o in _nb.people.values() if isinstance(o, dict)] == ["Elm's wife"],
      f"Elm's house: open, as in SoulSilver, his wife at home ({_nb.room})")
_nb._leave("OUT:%d,%d" % _nb_eh)
_nb_surf = story.inventory.pop("HM_SURF", None)
_nb.player = _nb.anim_from = (28, 16)
_nb.anim = 0
_nb.step(1, 0)
check(_nb.player == (28, 16) and _nb.rows[16][29] == "o" and any(o.get("kind") == "picture" and "ss_top/" in o.get("f", "") for o, *_r in getattr(_nb, "overheads", [])),
      "New Bark's bay is Surf water (no Surf: you stay on the shore); the tree tops and roofs are SoulSilver's own top layer (Jordan 11-15: native look)")
story.inventory["HM_SURF"] = 1
_nb.player = _nb.anim_from = (30, 16)
_nb.anim = 0
_held = _nb._check_menu_condition
_nb._check_menu_condition = lambda c: False if c == "has_8_johto_badges" else _held(c)
_nb.step(1, 0)
check(_nb.player == (30, 16) and "8 Johto badges" in _nb.toast and type(g.current_state).__name__ != "AreaTransitionState",
      "the east bay without 8 badges: turned back, told why")
_nb._check_menu_condition = lambda c: True if c == "has_8_johto_badges" else _held(c)
_nb.anim = 0
_nb.step(1, 0)
check(type(g.current_state).__name__ == "AreaTransitionState", "the east bay with 8 badges: on to Route 27")
_nb._check_menu_condition = _held
if _nb_surf is None:
    story.inventory.pop("HM_SURF", None)
else:
    story.inventory["HM_SURF"] = _nb_surf
g.change_state(_nb)
_nb.player = _nb.anim_from = (20, 11)
_nb.anim = 0
_nb_ld = next(t for t, k in _nb.doors.items() if k == "lab")
_nb.walk_goal = _nb_ld
for _k in range(400):
    frames(_nb)
    if _nb.npc_active or _nb.room:
        break
_nb_lab = _nb.room
if _nb.room:  # (11-11: the Lab is SoulSilver's own room now: walk in, talk to the Professor, walk out)
    _nb._talk(next(iter(_nb.people)))
check(_nb_lab == "lab" and _nb.npc_active and _nb.current_npc == "professor_elm", "walk into Elm's Lab (its own room): Professor Elm")
_tap_through(_nb)
_nb._go(None, "OUT:%d,%d" % _nb_ld); g.walk_town_room = None
_w = min(_nb.exits)
_nb.player = _nb.anim_from = (_w[0] + 1, _w[1])
_nb.anim = 0
_nb.step(-1, 0)
check(type(g.current_state).__name__ == "AreaTransitionState", "walk off the west edge: on to Route 29")
_r29 = kanto("JOHTO_ROUTE_29", came="NEW_BARK_TOWN")
_f = _r29.run.floor
check(_r29.run.recipe.get("art") and not _r29.run.fog
      and sorted({v for v in _f.exits.values() if not str(v).startswith("WARP")}) == ["CHERRYGROVE_CITY", "NEW_BARK_TOWN"] and _r29.run.recipe["exit_floors"].get("JOHTO_ROUTE_46", 0) >= 1
      and _r29.run.player[0] >= _f.w - 3, "Route 29: our map, open, in from New Bark (east); Cherrygrove; Route 46 through the gatehouse (a room of its own)")
_wl = [m for m in _f.movers if m.kind == "wild"]
check((_f.w, _f.h) == (96, 32) and str(_f.exits.get((50, 5))).startswith("WARP") and str(_f.exits.get((51, 5))).startswith("WARP")
      and _f.walkable(50, 6), f"Route 29: SoulSilver's own 96 x 32, the gatehouse's two-tile doorway (it leads inside) with open ground in front {_f.exits.get((50, 5))}")
_l29 = [v for v in _f.decor.values() if str(v).startswith("ledge:")]
check((_l29.count("ledge:0,1"), _l29.count("ledge:1,0"), _l29.count("ledge:-1,0")) == (49, 15, 8) and _f.decor.get((15, 12)) == "ledge:0,1",
      f"Route 29: SoulSilver's ledges are real one-way hops: 49 south, 15 east, 8 west ({len(_l29)})")
_m29 = _f.movers; _f.movers = []
_r29.run.player = (15, 13); _r29.anim = 0; _r29.sliding = None
_r29.step(0, -1)
_up29 = tuple(_r29.run.player)
_r29.run.player = (15, 11); _r29.anim = 0
_r29.step(0, 1)
_down29 = tuple(_r29.run.player)
_r29.hop = None; _r29.anim = 0
_r29.run.player = (28, 8); _r29.step(-1, 0)
_west29 = tuple(_r29.run.player)
_r29.run.player = (26, 8); _r29.anim = 0; _r29.step(1, 0)
_east29 = tuple(_r29.run.player)
_r29.hop = None; _r29.anim = 0; _f.movers = _m29
check(_up29 == (15, 13) and _down29 == (15, 13) and _west29 == (28, 8) and _east29 == (28, 8),
      f"Route 29: the ledge at (15, 12) is hopped down ({_down29}) and not climbed ({_up29}); the one at (27, 8) is hopped east ({_east29}), not west ({_west29})")
check(_wl and any(_f.tiles[m.y][m.x] == core.GRASS for m in _wl)
      and sum(m.kind == "trainer" for m in _f.movers) == sum(
          not story.is_trainer_defeated("JOHTO_ROUTE_29", i) for i in range(len(_r29.area_data.get("trainer_pool", [])))),
      "...wild Pokemon in its tall grass, its trainers on the map")
g.walk_town_pos = None
story.story_flags["defeated_rival_cherrygrove"] = True
story.current_area_key, story.last_area_key = "CHERRYGROVE_CITY", "JOHTO_ROUTE_29"
_cg = _CS(g); g.change_state(_cg); _tap_through(_cg)
check(_cg.player[0] >= _cg.w - 3 and {"center", "mart", "gent", "fisher"} <= set(_cg.doors.values())
      and set(_cg.exits.values()) == {"JOHTO_ROUTE_29", "JOHTO_ROUTE_30"},
      "Cherrygrove City: in from Route 29 (east); the Center, the Mart, the Guide Gent's and the fisherman's houses")
story.inventory.pop("MYSTIC_WATER", None)
story.story_flags.pop("got_mystic_water", None)
def _in_and_talk(t, kind):  # (11-11: Johto's houses are SoulSilver's own rooms now: in by the door, talk to whoever is there, out again)
    door = next(d for d, k in t.doors.items() if k == kind)
    t._enter(door)
    was = t.room
    for spot in list(t.people) if was else []:
        t._talk(spot); _tap_through(t)
    if was:
        t._go(None, "OUT:%d,%d" % door); g.walk_town_room = None
    return was


_cg_room = _in_and_talk(_cg, "fisher")
_tap_through(_cg)
check(_cg_room == "fisher" and story.inventory.get("MYSTIC_WATER") == 1, "the fisherman's house (its own room): Mystic Water")
_in_and_talk(_cg, "fisher")
_tap_through(_cg)
check(story.inventory.get("MYSTIC_WATER") == 1, "...once (after that he just talks)")
# Jordan 11-15 ("recheck the centers ... they have multiple layers"): a Johto Center is SoulSilver's own two-level room drawn with the true
# camera; the nurse stands on the game's own spot inside her counter, talked to across it, and both stairways climb to the back level
_pc_door = next(d for d, k in _cg.doors.items() if k == "center")
_cg._enter(_pc_door)
_pc_in = _cg.room == "center" and _cg.player
_pc_nurse = next(iter(_cg._people()), None)                       # (the nurse, wherever the room's crop puts her)
_pc_front = (_pc_nurse[0], _pc_nurse[1] + 2) if _pc_nurse else None
for _p in [_cg.player] + _cg._path(_pc_front):
    _cg.player = _cg.anim_from = _p
_cg.anim = 0
_pc_mon = story.player_team[0] if story.player_team else None
if _pc_mon:
    _pc_mon.current_hp = 1
_cg.step(0, -1)
_tap_through(_cg)
check(_pc_in and _pc_nurse and _cg.player == _pc_front and _cg.grid[_pc_nurse[1] + 1][_pc_nurse[0]] == "m"
      and (not _pc_mon or _pc_mon.current_hp == _pc_mon.get_max_hp()),
      f"Cherrygrove's Center: up to the counter {_cg.player}, talk to the nurse across it, healed")
_pc_top = min(y for y, row in enumerate(_cg.grid) if any(_cg._open((x, y)) for x in range(len(row))))   # (the back level's first row)
_pc_ends = [x for x in range(len(_cg.grid[_pc_top])) if _cg._open((x, _pc_top))]
check(_pc_ends and bool(_cg._path((_pc_ends[0], _pc_top))) and bool(_cg._path((_pc_ends[-1], _pc_top))) and _pc_top < _pc_nurse[1] - 4,
      "...the back level is reached by its stairs (left ramp and right steps, as the game)")
_cg._go(None, "OUT:%d,%d" % _pc_door); g.walk_town_room = None
# a save loaded straight into a walked town (Jordan, 11-07: it went back to the title): nothing to come from
_had = story.__dict__.pop("last_area_key", None)
g.walk_town_pos = None
story.current_area_key = "CHERRYGROVE_CITY"
try:
    _ld = _CS(g)
    check(isinstance(_ld, _WTS) and _ld._open(_ld.player), "a loaded save in a walked town: it opens (no came-from)")
except Exception as _e:
    check(False, f"a loaded save in a walked town: {_e!r}")
story.last_area_key = _had


# Johto's exact maps, Cherrygrove through Azalea (Jordan, 11-09)
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "VIOLET_CITY", "JOHTO_ROUTE_31"
_vi = _CS(g); g.change_state(_vi); _tap_through(_vi)
check(isinstance(_vi, _WTS) and (_vi.w, _vi.h) == (64, 64) and {"sprout", "gym", "mart", "center"} <= set(_vi.doors.values())
      and set(_vi.exits.values()) == {"JOHTO_ROUTE_31", "JOHTO_ROUTE_32", "JOHTO_ROUTE_36"} and _vi.player[0] >= _vi.w - 12,
      "Violet City: exact map, in from Route 31 (east); Tower, Gym, Mart, Center doors and its three ways out")
_vi._enter(next(t for t, k in _vi.doors.items() if k == "sprout"))
check(type(g.current_state).__name__ == "AreaTransitionState", "Sprout Tower's door: in you go")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "AZALEA_TOWN", "JOHTO_ROUTE_33"
_az = _CS(g); g.change_state(_az); _tap_through(_az)
check(isinstance(_az, _WTS) and (_az.w, _az.h) == (64, 32) and {"kurt", "gym", "mart", "center"} <= set(_az.doors.values())
      and "SLOWPOKE_WELL" in _az.exits.values() and "JOHTO_ROUTE_33" in _az.exits.values() and "ILEX_FOREST" in _az.exits.values(),
      "Azalea Town: exact map; Kurt's, the Gym, Mart and Center doors; the Well, Ilex and Route 33")
_az_kd = next(t for t, k in _az.doors.items() if k == "kurt")
_az._enter(_az_kd)
_az_room = _az.room
_az._talk(next(iter(_az.people)))
check(_az_room == "kurt" and _az.npc_active and _az.current_npc == "kurt", "Kurt's door: his house (its own room), Kurt inside")
_tap_through(_az)
_az._go(None, "OUT:%d,%d" % _az_kd); g.walk_town_room = None
_had_flash = story.inventory.pop("HM_FLASH", None)
_r31 = kanto("JOHTO_ROUTE_31", came="JOHTO_ROUTE_30")
_f31 = _r31.run.floor
check((_f31.w, _f31.h) == (64, 32) and _f31.exits.get((53, 13)) == "DARK_CAVE" and _f31.exits.get((6, 13)) == "VIOLET_CITY" and _f31.exits.get((6, 14)) == "VIOLET_CITY"
      and _r31.run.player[1] >= 29, f"Route 31: SoulSilver's own 64 x 32; in from Route 30 (south) at {_r31.run.player}; the Dark Cave mouth in the east cliff, the gatehouse's two-tile doorway to Violet")
_dc_open = _r31._try_exit("DARK_CAVE") or type(g.current_state).__name__ == "AreaTransitionState"
check(bool(_dc_open), "...and in you go without Flash, as in SoulSilver (it's dark until you have it, 11-15)")
if _had_flash:
    story.inventory["HM_FLASH"] = _had_flash
_r30 = kanto("JOHTO_ROUTE_30", came="CHERRYGROVE_CITY")
check((_r30.run.floor.w, _r30.run.floor.h) == (32, 96) and _r30.run.floor.exits.get((24, 6)) == "MR_POKEMONS_HOUSE" and _r30.run.player[1] >= 93
      and "JOHTO_ROUTE_31" in _r30.run.floor.exits.values() and list(_r30.run.floor.decor.values()).count("ledge:0,1") == 32,
      f"Route 30: SoulSilver's own 32 x 96; in from Cherrygrove (south) at {_r30.run.player}; Mr. Pokemon's door top right, the way north, its ledges hopped south")
_r32 = kanto("JOHTO_ROUTE_32", came="VIOLET_CITY")
check((_r32.run.floor.w, _r32.run.floor.h) == (32, 160) and _r32.run.player[1] <= 2 and _r32.run.floor.exits.get((14, 142)) == "UNION_CAVE" and {"VIOLET_CITY", "RUINS_OF_ALPH", "UNION_CAVE"} <= set(_r32.run.floor.exits.values())
      and any(o.get("door") == "center" for o in _r32.area_data["route_menu"]), "Route 32: exact map, its ways out, a working Center door")
_r33 = kanto("JOHTO_ROUTE_33", came="AZALEA_TOWN")
check({"AZALEA_TOWN", "UNION_CAVE"} == set(_r33.run.floor.exits.values()), "Route 33: Azalea and Union Cave")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "RUINS_OF_ALPH", "JOHTO_ROUTE_32"
_ra = _CS(g); g.change_state(_ra); _tap_through(_ra)
check(isinstance(_ra, _WTS) and (_ra.w, _ra.h) == (32, 64) and {"kabuto", "hooh", "omanyte", "aerodactyl", "ruins", "lab"} <= set(_ra.doors.values())
      and {"JOHTO_ROUTE_32", "UNION_CAVE"} <= set(_ra.exits.values()) and "JOHTO_ROUTE_36" in _ra.town_map["rooms"]["gate"]["exits"].values(),
      "Ruins of Alph: exact map; four chambers, the ruins, the lab, its ways out (Route 36 through the north gatehouse)")
for _k in ("kabuto", "hooh", "omanyte", "aerodactyl"):
    check(len(_ra._door_options(_k)) == 1, f"...the {_k} door opens its puzzle")
_r_un = kanto("UNION_CAVE", came="JOHTO_ROUTE_32")
_un_names = [m.payload[1].get("name") if isinstance(m.payload, tuple) else None for m in _r_un.run.floor.movers if m.kind == "trainer"]
check(_r_un.run.n_floors == 3 and _r_un.run.index == 0 and {"JOHTO_ROUTE_32", "JOHTO_ROUTE_33", "RUINS_OF_ALPH"} <= set(_r_un.run.floor.exits.values()) and len(_un_names) == 5,
      f"Union Cave: SoulSilver's three floors; in from Route 32 on 1F; five of its six trainers there (the sixth on B1F) {_r_un.run.n_floors, _r_un.run.index, sorted(set(map(str, _r_un.run.floor.exits.values()))), [(m.kind, str(m.payload)[:50]) for m in _r_un.run.floor.movers if m.kind != 'wild'][:8]}")
# Johto's caves from SoulSilver's own floors: every stair is a passage to its real far end; walk each one
import json as _json_j
_tm_j = _json_j.load(open("assets/town_maps.json", encoding="utf-8"))
_walked_j = []
for _kj, _camej in (("UNION_CAVE", "JOHTO_ROUTE_32"), ("SLOWPOKE_WELL", "AZALEA_TOWN"), ("WHIRL_ISLANDS", "JOHTO_ROUTE_41"),
                     ("BURNED_TOWER", "ECRUTEAK_CITY"), ("SPROUT_TOWER", "VIOLET_CITY"),
                     ("OLIVINE_LIGHTHOUSE_FLOORS", "OLIVINE_CITY"), ("RADIO_TOWER", "GOLDENROD_CITY"), ("GOLDENROD_UNDERGROUND", "GOLDENROD_CITY"), ("BELL_TOWER", "BELLCHIME_TRAIL"), ("MT_MORTAR", "JOHTO_ROUTE_42"),
                     ("ROCKET_HQ", "MAHOGANY_TOWN"), ("ICE_PATH", "JOHTO_ROUTE_44"), ("DRAGONS_DEN", "BLACKTHORN_CITY"), ("JOHTO_CLIFF_CAVE", "JOHTO_ROUTE_47"), ("TOHJO_FALLS", "KANTO_ROUTE_27")):
    for _i, _fj2 in enumerate(_tm_j[_kj]["floors"]):
        for _at, (_j, _x, _y) in (_fj2.get("links") or {}).items():
            _rj = kanto(_kj, came=_camej)
            _ax, _ay = (int(v) for v in _at.split(","))
            _rj.run.warp(_i, _ax, _ay)
            _px, _py = _rj.run.player
            _ev = _rj.run.step(_ax - _px, _ay - _py)
            _rj._handle(_ev)
            for _q in range(40):
                if getattr(_rj, "dialogue_box", None) and _rj.dialogue_box.visible:
                    _rj.dialogue_box.advance()
                frames(_rj)
            _okj = (any(e[0] == "warp" for e in _ev) and _rj.run.index == _j and _rj.run.floor.walkable(*_rj.run.player)
                    and (abs(_rj.run.player[0] - _x) + abs(_rj.run.player[1] - _y) <= 1 or _rj.run.player == _rj.run.floor.start))
            _walked_j.append((_kj, _i, _at, _okj))
check(len(_walked_j) == 217 and all(w[3] for w in _walked_j),
      f"Johto's caves and towers from SoulSilver (Union Cave, Slowpoke Well, Whirl Islands, Burned and Sprout Towers, Lighthouse, Radio Tower, Underground, Bell Tower, Mt. Mortar, Rocket HQ, Ice Path): stepping onto each of their {len(_walked_j)} stairs takes you beside its far end on the right floor {[w for w in _walked_j if not w[3]][:6]}")
_ilx = kanto("ILEX_FOREST", came="AZALEA_TOWN")
check((_ilx.run.floor.w, _ilx.run.floor.h) == (64, 96) and {"AZALEA_TOWN"} == {v for v in _ilx.run.floor.exits.values() if not str(v).startswith("WARP")} and _ilx.run.recipe["exit_floors"].get("JOHTO_ROUTE_34", 0) >= 1
      and _ilx.run.player[1] >= 78, f"Ilex Forest: SoulSilver's own 64 x 96, in from Azalea at the south-west gate {_ilx.run.player}, Route 34 north")
_r34 = kanto("JOHTO_ROUTE_34", came="ILEX_FOREST")
check((_r34.run.floor.w, _r34.run.floor.h) == (32, 96) and _r34.run.player[1] in (64, 65, 66) and {"ILEX_FOREST", "GOLDENROD_CITY"} == {v for v in _r34.run.floor.exits.values() if not str(v).startswith("WARP")}
      and "daycare" in (_r34.run.recipe.get("art") or {}).get("room_floors", {}) and any(o.get("door") == "daycare" for o in _r34.area_data["route_menu"]),
      "Route 34: exact map, Goldenrod and Ilex, the Day Care (a room of its own)")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "GOLDENROD_CITY", "JOHTO_ROUTE_34"
_gd = _CS(g); g.change_state(_gd); _tap_through(_gd)
check(isinstance(_gd, _WTS) and (_gd.w, _gd.h) == (96, 64) and _gd.player[1] >= 60
      and {"radio", "gym", "center", "dept", "bike", "flower", "station", "game corner"} <= set(_gd.doors.values())
      and {"JOHTO_ROUTE_34", "GOLDENROD_UNDERGROUND"} == set(_gd.exits.values()) and "JOHTO_ROUTE_35" in _gd.town_map["rooms"]["gate"]["exits"].values(),
      "Goldenrod City: exact map, in from Route 34 (south); every shop's door, both Underground stairs, the gate north")
_gd.player = _gd.anim_from = (70, 23); _gd.anim = 0
for _k in range(5):
    _gd.step(0, 1)
    _gd.anim = 0
check(_gd.player == (70, 28) and any(o[0].get("kind") == "rail" for o in _gd.overheads), "...you walk under the Magnet Train line")
_gd.draw()
for _k in ("radio", "dept", "bike", "flower", "center", "game corner"):
    check(_gd._door_options(_k), f"...the {_k} door has something behind it")
_r35 = kanto("JOHTO_ROUTE_35", came="GOLDENROD_CITY")
check((_r35.run.floor.w, _r35.run.floor.h) == (32, 64) and {"JOHTO_ROUTE_36", "GOLDENROD_CITY"} == {v for v in _r35.run.floor.exits.values() if not str(v).startswith("WARP")}
      and _r35.run.player[1] >= 58 and core.distances(_r35.run.floor, _r35.run.player).get((10, 11)) is not None
      and _r35.run.floor.exits.get((26, 0)) == "JOHTO_ROUTE_36" and str(_r35.run.floor.exits.get((10, 10))).startswith("WARP") and _r35.run.recipe["exit_floors"].get("NATIONAL_PARK", 0) >= 1,
      f"Route 35: SoulSilver's own 32 x 64, in from Goldenrod's gatehouse (south) at {_r35.run.player}; on foot to the National Park gate's door; the east lane north to Route 36")
_np = kanto("NATIONAL_PARK", came="JOHTO_ROUTE_36")
check((_np.run.floor.w, _np.run.floor.h) == (96, 96) and {"JOHTO_ROUTE_35", "JOHTO_ROUTE_36", "POKEATHLON_DOME"} == set(_np.run.floor.exits.values())
      and _np.run.player[0] >= 72, "National Park: SoulSilver's own 96 x 96, in from Route 36 (east gate), the Dome and Route 35")
_r36 = kanto("JOHTO_ROUTE_36", came="VIOLET_CITY")
check((_r36.run.floor.w, _r36.run.floor.h) == (96, 32) and {"VIOLET_CITY", "RUINS_OF_ALPH", "JOHTO_ROUTE_35", "JOHTO_ROUTE_37", "NATIONAL_PARK"} == set(_r36.run.floor.exits.values())
      and _r36.run.player[0] >= 93, "Route 36: SoulSilver's own 96 x 32, in from Violet (east gate), all five ways out")
_r37 = kanto("JOHTO_ROUTE_37", came="JOHTO_ROUTE_36")
check({"JOHTO_ROUTE_36", "ECRUTEAK_CITY"} == set(_r37.run.floor.exits.values()), "Route 37: Route 36 and Ecruteak")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "ECRUTEAK_CITY", "JOHTO_ROUTE_37"
_ec = _CS(g); g.change_state(_ec); _tap_through(_ec)
check(isinstance(_ec, _WTS) and (_ec.w, _ec.h) == (64, 64) and {"burned", "bellchime", "theater", "gym", "mart", "center"} <= set(_ec.doors.values())
      and {"JOHTO_ROUTE_37", "JOHTO_ROUTE_38", "JOHTO_ROUTE_42"} == set(_ec.exits.values()) and _ec.player[1] >= 60,
      "Ecruteak City: exact map, in from Route 37 (south); its towers, theater, Gym and shops; three ways out")
for _k in ("burned", "bellchime", "theater"):
    check(_ec._door_options(_k), f"...the {_k} door leads somewhere")
_ec.draw()
_bt = kanto("BURNED_TOWER", came="ECRUTEAK_CITY")
check(_bt.run.n_floors == 2 and "ECRUTEAK_CITY" in _bt.run.floor.exits.values() and _bt.run.recipe["art"]["floors"][0].get("links") if isinstance(_bt.run.recipe.get("art"), dict) else _bt.run.n_floors == 2,
      "Burned Tower: SoulSilver's 1F, the way out, the stairs down to the basement")
_r38 = kanto("JOHTO_ROUTE_38", came="ECRUTEAK_CITY")
check((_r38.run.floor.w, _r38.run.floor.h) == (64, 32) and {"ECRUTEAK_CITY", "JOHTO_ROUTE_39"} == set(_r38.run.floor.exits.values()), "Route 38: exact map, Ecruteak and Route 39")
_r39 = kanto("JOHTO_ROUTE_39", came="JOHTO_ROUTE_38")
check((_r39.run.floor.w, _r39.run.floor.h) == (32, 64) and {"JOHTO_ROUTE_38", "OLIVINE_CITY"} == {str(v) for v in _r39.run.floor.exits.values() if not str(v).startswith(("ROOM:", "OUT:", "WARP:"))} and sum(str(v).startswith("WARP:") for v in _r39.run.floor.exits.values()) == 2, "Route 39: exact to the HGSS picture with Moomoo Farm; Route 38, Olivine (the barn and house are its rooms now)")
_bct = kanto("BELLCHIME_TRAIL", came="ECRUTEAK_CITY")
check((_bct.run.floor.w, _bct.run.floor.h) == (64, 32) and {"ECRUTEAK_CITY", "BELL_TOWER"} == set(_bct.run.floor.exits.values()) and _bct.run.player[0] <= 12, f"Bellchime Trail: SoulSilver's own 64 x 32, in from Ecruteak's gatehouse at {_bct.run.player}; the Bell Tower door")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "OLIVINE_CITY", "JOHTO_ROUTE_39"
_ol = _CS(g); g.change_state(_ol); _tap_through(_ol)
check(isinstance(_ol, _WTS) and (_ol.w, _ol.h) == (64, 64) and {"gym", "center", "mart", "harbor"} <= set(_ol.doors.values())
      and {"JOHTO_ROUTE_39", "JOHTO_ROUTE_40", "OLIVINE_LIGHTHOUSE_FLOORS"} == set(_ol.exits.values()) and _ol.player[1] <= 3,
      "Olivine City: exact map, in from Route 39 (north); its doors, the Lighthouse, the beach west")
_ol.player = _ol.anim_from = (23, 52); _ol.anim = 0
check((23, 53) in _ol.doors and _ol.doors[(23, 53)] == "harbor", "...the harbor terminal's door faces the pier")
_ol.draw()
_lh = kanto("OLIVINE_LIGHTHOUSE_FLOORS", came="OLIVINE_CITY")
check(_lh.run.n_floors == 5 and _lh.run.index == 0 and "OLIVINE_CITY" in _lh.run.floor.exits.values(), "Glitter Lighthouse: five floors, in on 1F")
_bal = kanto("OLIVINE_LIGHTHOUSE_BALCONY", came="OLIVINE_LIGHTHOUSE_FLOORS")
check((_bal.run.floor.w, _bal.run.floor.h) == (17, 16) and set(_bal.run.floor.exits.values()) == {"OLIVINE_LIGHTHOUSE_FLOORS"}, "...the balcony: the tower's door back in")
_back = kanto("OLIVINE_LIGHTHOUSE_FLOORS", came="OLIVINE_LIGHTHOUSE_BALCONY")
_f3 = _back.run.floor
check(_back.run.index == 2 and _f3.walkable(*_back.run.player) and _back.run.player[1] >= 15, f"...and back in on 3F by its south door {_back.run.player}")
_back.run.floor
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "OLIVINE_LIGHTHOUSE", "OLIVINE_LIGHTHOUSE_FLOORS"
_top = _CS(g); g.change_state(_top); _tap_through(_top)
check(isinstance(_top, _WTS) and sorted(o["text"] for o in _top._people().values() if not o.get("found")) == ["Check Amphy", "Talk to Jasmine"]
      and {"OLIVINE_CITY", "OLIVINE_LIGHTHOUSE_FLOORS"} == set(_top.exits.values()), "...the beacon room: Jasmine, Amphy, the stairs, the elevator")
_lift = next(t for t, v in _top.exits.items() if v == "OLIVINE_CITY")
story.story_flags.pop("ampharos_cured", None); story.story_flags.pop("jasmine_explained", None)
_top.player = _top.anim_from = (_lift[0], _lift[1] + 1); _top.anim = 0
_top.step(0, -1)
check("locked" in _top.toast and type(g.current_state).__name__ != "AreaTransitionState", "...the elevator is locked till Jasmine has told you about Amphy")
story.story_flags["jasmine_explained"] = True   # (11-23: she lends you the lift once she has explained, so you can go for the potion)
_top.anim = 0
_top.player = _top.anim_from = (_lift[0], _lift[1] + 1)
_top.step(0, -1)
check(type(g.current_state).__name__ == "AreaTransitionState", "...and opens after")
story.story_flags.pop("ampharos_cured", None)
_r40 = kanto("JOHTO_ROUTE_40", came="OLIVINE_CITY")
check((_r40.run.floor.w, _r40.run.floor.h) == (32, 64) and {"OLIVINE_CITY", "JOHTO_ROUTE_41", "FRONTIER_ACCESS"} == set(_r40.run.floor.exits.values()), "Route 40: exact map, Olivine, the Frontier's gateway, the sea to Route 41")
_r41 = kanto("JOHTO_ROUTE_41", came="JOHTO_ROUTE_40")
check((_r41.run.floor.w, _r41.run.floor.h) == (64, 64) and {"JOHTO_ROUTE_40", "CIANWOOD_CITY", "WHIRL_ISLANDS"} == set(_r41.run.floor.exits.values())
      and sum(v == "WHIRL_ISLANDS" for v in _r41.run.floor.exits.values()) == 4, "Route 41: exact map, Route 40, Cianwood, all four Whirl Island caves")
_r40 = kanto("JOHTO_ROUTE_40", came="OLIVINE_CITY")
check((_r40.run.floor.w, _r40.run.floor.h) == (32, 64) and {"OLIVINE_CITY", "JOHTO_ROUTE_41", "FRONTIER_ACCESS"} == set(_r40.run.floor.exits.values()), "Route 40: exact map, Olivine, the Frontier's gateway, the sea to Route 41")
_r41 = kanto("JOHTO_ROUTE_41", came="JOHTO_ROUTE_40")
check((_r41.run.floor.w, _r41.run.floor.h) == (64, 64) and {"JOHTO_ROUTE_40", "CIANWOOD_CITY", "WHIRL_ISLANDS"} == set(_r41.run.floor.exits.values())
      and sum(v == "WHIRL_ISLANDS" for v in _r41.run.floor.exits.values()) == 4, "Route 41: exact map, Route 40, Cianwood, all four Whirl Island caves")
_r40 = kanto("JOHTO_ROUTE_40", came="OLIVINE_CITY")
check((_r40.run.floor.w, _r40.run.floor.h) == (32, 64) and {"OLIVINE_CITY", "JOHTO_ROUTE_41", "FRONTIER_ACCESS"} == set(_r40.run.floor.exits.values()), "Route 40: exact map, Olivine, the Frontier's gateway, the sea to Route 41")
_r41 = kanto("JOHTO_ROUTE_41", came="JOHTO_ROUTE_40")
check((_r41.run.floor.w, _r41.run.floor.h) == (64, 64) and {"JOHTO_ROUTE_40", "CIANWOOD_CITY", "WHIRL_ISLANDS"} == set(_r41.run.floor.exits.values())
      and sum(v == "WHIRL_ISLANDS" for v in _r41.run.floor.exits.values()) == 4, "Route 41: exact map, Route 40, Cianwood, all four Whirl Island caves")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "CIANWOOD_CITY", "JOHTO_ROUTE_41"
_cw = _CS(g); g.change_state(_cw); _tap_through(_cw)
check(isinstance(_cw, _WTS) and (_cw.w, _cw.h) == (32, 64) and {"gym", "center", "pharmacy"} <= set(_cw.doors.values())
      and {"JOHTO_ROUTE_41", "CLIFF_EDGE_GATE"} == set(_cw.exits.values()) and len(_cw._door_options("pharmacy")) == 2,
      "Cianwood City: exact map; the Gym, Center, Pharmacy (medicine and shop), the sea and the cliff gate")
_w41 = kanto("JOHTO_ROUTE_41", came="JOHTO_ROUTE_40")
_wf = _w41.run.floor
def _sea_reach(f, start):
    seen, todo = {start}, [start]
    while todo:
        x, y = todo.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (x + dx, y + dy)
            if 0 <= n[0] < f.w and 0 <= n[1] < f.h and n not in seen and f.tiles[n[1]][n[0]] in (core.FLOOR, core.GRASS, core.SURF):
                seen.add(n); todo.append(n)
    return seen
_caves = [t for t, v in _wf.exits.items() if v == "WHIRL_ISLANDS"]
_open = _sea_reach(_wf, (40, 1))
check(_caves and not any(c in _open for c in _caves), "Route 41: all four islands are sealed; no cave without getting past a whirlpool")
for _key in [k for k in story.story_flags if k.startswith("boulder_JOHTO_ROUTE_41")]:
    story.story_flags.pop(_key)
_had_wp = story.inventory.pop("HM_WHIRLPOOL", None)
_w41.run.player = (25, 12); _w41.facing = (-1, 0)
_w41._read_sign()
check(str(_wf.decor.get((24, 12), "")).startswith("whirl:"), "...a whirlpool won't budge without Whirlpool")
story.inventory["HM_WHIRLPOOL"] = 1
_w41.run.player = (25, 12); _w41.facing = (-1, 0)
_w41._read_sign()
_w41._render_floor()
check((24, 12) not in _wf.decor and any(c in _sea_reach(_wf, (40, 1)) for c in _caves), "...and with it the whirlpool clears and that island opens")
for _key in [k for k in story.story_flags if k.startswith("boulder_JOHTO_ROUTE_41")]:
    story.story_flags.pop(_key)
story.inventory.pop("HM_WHIRLPOOL", None)
if _had_wp:
    story.inventory["HM_WHIRLPOOL"] = _had_wp
_r40 = kanto("JOHTO_ROUTE_40", came="OLIVINE_CITY")
check((_r40.run.floor.w, _r40.run.floor.h) == (32, 64) and {"OLIVINE_CITY", "JOHTO_ROUTE_41", "FRONTIER_ACCESS"} == set(_r40.run.floor.exits.values()), "Route 40: exact map, Olivine, the Frontier's gateway, the sea to Route 41")
_r41 = kanto("JOHTO_ROUTE_41", came="JOHTO_ROUTE_40")
check((_r41.run.floor.w, _r41.run.floor.h) == (64, 64) and {"JOHTO_ROUTE_40", "CIANWOOD_CITY", "WHIRL_ISLANDS"} == set(_r41.run.floor.exits.values())
      and sum(v == "WHIRL_ISLANDS" for v in _r41.run.floor.exits.values()) == 4, "Route 41: exact map, Route 40, Cianwood, all four Whirl Island caves")
_r40 = kanto("JOHTO_ROUTE_40", came="OLIVINE_CITY")
check((_r40.run.floor.w, _r40.run.floor.h) == (32, 64) and {"OLIVINE_CITY", "JOHTO_ROUTE_41", "FRONTIER_ACCESS"} == set(_r40.run.floor.exits.values()), "Route 40: exact map, Olivine, the Frontier's gateway, the sea to Route 41")
_r41 = kanto("JOHTO_ROUTE_41", came="JOHTO_ROUTE_40")
check((_r41.run.floor.w, _r41.run.floor.h) == (64, 64) and {"JOHTO_ROUTE_40", "CIANWOOD_CITY", "WHIRL_ISLANDS"} == set(_r41.run.floor.exits.values())
      and sum(v == "WHIRL_ISLANDS" for v in _r41.run.floor.exits.values()) == 4, "Route 41: exact map, Route 40, Cianwood, all four Whirl Island caves")
from src.dungeon import core as _c
_rooms = {}
for _i, _name in enumerate(("NW", "NE", "SW", "SE")):
    _c.ENTRANCE_INDEX = _i
    _wi = kanto("WHIRL_ISLANDS", came="JOHTO_ROUTE_41")
    _rooms[_name] = _wi.run.player
_c.ENTRANCE_INDEX = 0
_near_wi = lambda p, q: abs(p[0] - q[0]) + abs(p[1] - q[1]) <= 2
check(_wi.run.n_floors == 5 and _near_wi(_rooms["NW"], (8, 14)) and _near_wi(_rooms["NE"], (34, 19)) and _near_wi(_rooms["SW"], (5, 48)) and _near_wi(_rooms["SE"], (49, 53)),
      f"Whirl Islands: SoulSilver's five floors; each of Route 41's cave mouths leads to its own island's room on 1F {_rooms}")
_r42 = kanto("JOHTO_ROUTE_42", came="ECRUTEAK_CITY")
check((_r42.run.floor.w, _r42.run.floor.h) == (96, 32) and {"ECRUTEAK_CITY", "MAHOGANY_TOWN", "MT_MORTAR"} == set(_r42.run.floor.exits.values())
      and sum(v == "MT_MORTAR" for v in _r42.run.floor.exits.values()) == 4, "Route 42: exact map; Ecruteak, Mahogany, four ways into Mt. Mortar")
_mm = {}
for _i, _name in enumerate(("upper", "west", "east", "middle")):  # (Route 42's four mouths in reading order)
    _c.ENTRANCE_INDEX, _c.ENTRANCE_COUNT = _i, 4
    _mt = kanto("MT_MORTAR", came="JOHTO_ROUTE_42")
    _mm[_name] = tuple(_mt.run.player)
_c.ENTRANCE_INDEX = _c.ENTRANCE_COUNT = 0
_near_mm = lambda p, q: abs(p[0] - q[0]) + abs(p[1] - q[1]) <= 2
check(_mt.run.n_floors == 4 and _near_mm(_mm["west"], (4, 46)) and _near_mm(_mm["east"], (54, 46)) and _near_mm(_mm["middle"], (29, 50)) and _near_mm(_mm["upper"], (43, 53))
      and [t for t, v in _mt.run.floor.exits.items() if v == "JOHTO_ROUTE_42"] == [(43, 53), (4, 46), (54, 46), (29, 50)],
      f"Mt. Mortar: SoulSilver's four floors; each of Route 42's mouths leads to its own mouth inside, and back {_mm}")
_r43 = kanto("JOHTO_ROUTE_43", came="MAHOGANY_TOWN")
check((_r43.run.floor.w, _r43.run.floor.h) == (32, 64) and {"MAHOGANY_TOWN", "LAKE_OF_RAGE"} == {v for v in _r43.run.floor.exits.values() if not str(v).startswith("WARP")} and _r43.run.player[1] >= 58
      and sum(str(v).startswith("WARP") for v in _r43.run.floor.exits.values()) == 4,
      f"Route 43: exact map; in from Mahogany's gate (south) at {_r43.run.player}; the toll gate walked through door to door; north to the Lake of Rage")
story.story_flags.pop("rocket_hq_cleared", None)
story.defeated_trainers.pop("JOHTO_ROUTE_43", None)
_r43 = kanto("JOHTO_ROUTE_43", came="MAHOGANY_TOWN")
_gr = {(m.x, m.y) for f in _r43.run.floors for m in f.movers if m.kind == "trainer"}
story.story_flags["rocket_hq_cleared"] = True
_r43b = kanto("JOHTO_ROUTE_43", came="MAHOGANY_TOWN")
_gr2 = {(m.x, m.y) for f in _r43b.run.floors for m in f.movers if m.kind == "trainer"}
story.story_flags.pop("rocket_hq_cleared", None)
check({(24, 36), (27, 49)} <= _gr and not ({(24, 36), (27, 49)} & _gr2) and len(_gr2) == len(_gr) - 2,
      f"Route 43: two Rocket Grunts stand outside the toll gate's doors, gone once the hideout is cleared {sorted(_gr)} -> {sorted(_gr2)}")
_r44 = kanto("JOHTO_ROUTE_44", came="MAHOGANY_TOWN")
check((_r44.run.floor.w, _r44.run.floor.h) == (96, 32) and {"MAHOGANY_TOWN", "ICE_PATH"} == set(_r44.run.floor.exits.values()) and _r44.run.player[0] <= 2,
      f"Route 44: exact map; in from Mahogany (west) at {_r44.run.player}; the Ice Path's mouth east")
_hq = kanto("ROCKET_HQ", came="MAHOGANY_TOWN")
_hqr = _hq.recipe
check(_hq.run.n_floors == 3 and "MAHOGANY_TOWN" in _hq.run.floor.exits.values() and _hq.run.player[0] >= 40 and _hq.run.player[1] <= 6
      and (_hqr.get("art") or {}).get("figure_floors", {}).get("Executive Petrel") == 2,
      f"Rocket Hideout: exact B1F-B3F; in from the shop's stairs (NE) at {_hq.run.player}; Petrel waits on B3F, Ariana on B2F")
story.defeated_trainers.pop("ROCKET_HQ", None)
_hq = kanto("ROCKET_HQ", came="MAHOGANY_TOWN")
while _hq.run.index < _hq.run.n_floors - 1:
    _hq.run.enter_floor(_hq.run.index + 1)
_hqt = [(i, m.x, m.y) for i, f in enumerate(_hq.run.floors) for m in f.movers if m.kind == "trainer"]
check(len(_hqt) == 11 and len(set(_hqt)) == 11,   # (11-15: SoulSilver's own grunts and scientists joined ours, each on a spot of its own)
      f"Rocket Hideout: a grunt on each floor on a spot of their own (three share one name), Ariana on B2F, Petrel on B3F {_hqt}")
_r44 = kanto("JOHTO_ROUTE_44", came="MAHOGANY_TOWN")
_r44t = [(m.x, m.y) for m in _r44.run.floor.movers if m.kind == "trainer"]
check(len(_r44t) == len(set(_r44t)) == 9, f"Route 44: nine trainers (SoulSilver's Ace Trainers Cybil and Allen joined, 11-15), each on a spot of the game's {len(_r44t)}")
story.defeated_trainers.pop("JOHTO_ROUTE_43", None)
_r43 = kanto("JOHTO_ROUTE_43", came="MAHOGANY_TOWN")
check({(m.x, m.y) for m in _r43.run.floor.movers if m.kind == "trainer"} >= {(18, 8), (25, 15), (8, 17), (19, 26), (14, 31), (14, 53)}, "Route 43: the game's six trainers on the game's six spots")
_ip = kanto("ICE_PATH", came="JOHTO_ROUTE_44")
check(_ip.run.n_floors == 4 and _ip.run.player[1] >= 43 and len(_ip.run.floor.ice) > 100 and {"JOHTO_ROUTE_44", "BLACKTHORN_CITY"} <= set(_ip.run.floor.exits.values()),
      f"Ice Path: exact 1F-B3F; in from Route 44 (south) at {_ip.run.player}; sheet ice on 1F")
_ip.run.floor.movers = []
_ip.run.player, _ip.mode, _ip.anim, _ip.walk_goal = (10, 43), "MAP", 0, None
_ip.dialogue_box.visible = False
_ip.step(0, -1)
for _ in range(400):
    _ip.update()
    if not _ip.sliding and _ip.anim == 0:
        break
_up = _ip.run.player
_ip.step(1, 0)
for _ in range(400):
    _ip.update()
    if not _ip.sliding and _ip.anim == 0:
        break
check(_up == (10, 36) and _ip.run.player == (18, 36) and not _ip.sliding,
      f"Ice Path: step onto the ice and you slide till something stops you (up to {_up}, then right to {_ip.run.player})")
for _bx, _by in ((9, 11), (12, 12), (17, 10), (24, 10)):
    story.story_flags[f"boulder_ICE_PATH_1_{_bx}_{_by}"] = True
while _ip.run.index < 2:  # (floors are made in order)
    _ip.run.enter_floor(_ip.run.index + 1)
_ip._clear_boulders()
_fallen = sorted(t for t, w in _ip.run.floor.decor.items() if str(w).startswith("fallen:"))
for _bx, _by in ((9, 11), (12, 12), (17, 10), (24, 10)):
    story.story_flags.pop(f"boulder_ICE_PATH_1_{_bx}_{_by}", None)
check(_fallen == [(8, 20), (9, 12), (16, 9), (17, 21)] and all(not _ip.run.floor.walkable(*t) for t in _fallen),
      f"Ice Path: B1F's four boulders, pushed into their holes, land on B2F's ice as stops {_fallen}")
_ipl = [f.get("links") or {} for f in (_ip.recipe.get("art") or {}).get("floors", [])]
check(len(_ipl) == 4 and _ipl[2].get("13,16") == [3, 4, 9] and _ipl[3].get("23,10") == [2, 47, 4] and _ipl[0].get("48,4") == [1, 5, 19],
      f"Ice Path: every ladder joined to its real far end (B2F's middle ladder to B3F's west, B3F's east ladder up to B2F's east) {_ipl[2:]}")
_w = {}
for _k, _cm in (("CLIFF_EDGE_GATE", "CIANWOOD_CITY"), ("CLIFF_EDGE_GATE", "JOHTO_ROUTE_47"), ("JOHTO_ROUTE_47", "CLIFF_EDGE_GATE"), ("JOHTO_ROUTE_47", "JOHTO_ROUTE_48"), ("JOHTO_ROUTE_48", "JOHTO_ROUTE_47"),
               ("JOHTO_ROUTE_48", "SAFARI_ZONE_GATE")):
    story.defeated_trainers.pop(_k, None)
    _r = kanto(_k, came=_cm)
    _w[(_k, _cm)] = (_r.run.floor.w, _r.run.floor.h, _r.run.player, set(map(str, _r.run.floor.exits.values())), {(m.x, m.y) for m in _r.run.floor.movers if m.kind == "trainer"})
check(_w[("CLIFF_EDGE_GATE", "CIANWOOD_CITY")][3] >= {"CIANWOOD_CITY", "JOHTO_ROUTE_47"} and _w[("CLIFF_EDGE_GATE", "CIANWOOD_CITY")][2] != _w[("CLIFF_EDGE_GATE", "JOHTO_ROUTE_47")][2],
      f"Cliff Edge Gate: SoulSilver's passage; in from Cianwood at one door, from Route 47 at the other {_w[('CLIFF_EDGE_GATE', 'CIANWOOD_CITY')][2], _w[('CLIFF_EDGE_GATE', 'JOHTO_ROUTE_47')][2]}")
_x = _w[("JOHTO_ROUTE_47", "CLIFF_EDGE_GATE")]
check(_x[:2] == (96, 64) and _x[2][0] >= 83 and _x[3] >= {"CLIFF_EDGE_GATE", "JOHTO_CLIFF_CAVE", "JOHTO_EMBEDDED_TOWER", "JOHTO_ROUTE_48"} and _x[4] >= {(36, 12), (67, 31), (53, 38), (71, 40)}
      and _w[("JOHTO_ROUTE_47", "JOHTO_ROUTE_48")][2][1] <= 1,
      f"Route 47: exact map; in from the Cliff Edge Gate (east) at {_x[2]}; Cliff Cave, the Embedded Tower, Route 48 north; four trainers on the game's spots")
_x = _w[("JOHTO_ROUTE_48", "JOHTO_ROUTE_47")]
check(_x[:2] == (64, 32) and _x[2][1] >= 30 and _x[3] == {"JOHTO_ROUTE_47", "SAFARI_ZONE_GATE"} and _w[("JOHTO_ROUTE_48", "SAFARI_ZONE_GATE")][2][1] <= 1,
      f"Route 48: exact map; in from Route 47 (south) at {_x[2]}; the long bridge north to the Safari Zone Gate")
_cc = {}
for _i, _name in enumerate(("upper", "middle", "lower")):  # (Route 47's three mouths in reading order)
    _c.ENTRANCE_INDEX, _c.ENTRANCE_COUNT = _i, 3
    _cv = kanto("JOHTO_CLIFF_CAVE", came="JOHTO_ROUTE_47")
    _cc[_name] = tuple(_cv.run.player)
_c.ENTRANCE_INDEX = _c.ENTRANCE_COUNT = 0
check(_near_mm(_cc["upper"], (6, 29)) and _near_mm(_cc["middle"], (6, 7)) and _near_mm(_cc["lower"], (26, 13)),
      f"Cliff Cave: each of Route 47's three mouths leads to its own level inside {_cc}")
_tf = {}
for _i, _name in enumerate(("east", "west")):  # (Route 27's two mouths in reading order)
    _c.ENTRANCE_INDEX, _c.ENTRANCE_COUNT = _i, 2
    _tj = kanto("TOHJO_FALLS", came="KANTO_ROUTE_27")
    _tf[_name] = tuple(_tj.run.player)
_c.ENTRANCE_INDEX = _c.ENTRANCE_COUNT = 0
check(_tj.run.n_floors == 2 and _near_mm(_tf["east"], (28, 19)) and _near_mm(_tf["west"], (13, 21)) and {v for v in _tj.run.floor.exits.values() if not str(v).startswith("WARP")} == {"KANTO_ROUTE_27"}
      and ((_tj.recipe.get("art") or {}).get("figure_floors") or {}).get("Waterfall Cave") == 1,
      f"Tohjo Falls: SoulSilver's falls and the hidden room; each of Route 27's mouths leads to its own {_tf}; Giovanni waits in the hidden room")
_et = kanto("JOHTO_EMBEDDED_TOWER", came="JOHTO_ROUTE_47")
check((_et.run.floor.w, _et.run.floor.h) == (17, 28) and _et.run.player[1] >= 23 and set(_et.run.floor.exits.values()) == {"JOHTO_ROUTE_47"}
      and len(((_et.recipe.get("art") or {}).get("floors") or [{}])[0].get("people") or []) == 3,
      f"Embedded Tower: SoulSilver's chamber; in from Route 47 at {_et.run.player}; Groudon, Kyogre and Rayquaza each have a spot")
_dd = kanto("DRAGONS_DEN", came="BLACKTHORN_CITY")
_dd_in = (_dd.run.index, _dd.run.player)
_dd2 = kanto("DRAGONS_DEN", came="DRAGON_SHRINE")
check(_dd.run.n_floors == 2 and _dd_in[0] == 0 and _dd_in[1][1] >= 6 and _dd2.run.index == 1 and abs(_dd2.run.player[0] - 24) <= 1 and _dd2.run.player[1] >= 49
      and "DRAGON_SHRINE" in _dd2.run.floor.exits.values(),
      f"Dragon's Den: exact 1F and B1F; in from Blackthorn at {_dd_in}; back out of the shrine at its door on B1F {_dd2.run.player}")
_r45 = kanto("JOHTO_ROUTE_45", came="BLACKTHORN_CITY")
check((_r45.run.floor.w, _r45.run.floor.h) == (32, 160) and {"BLACKTHORN_CITY", "DARK_CAVE", "JOHTO_ROUTE_46"} == set(_r45.run.floor.exits.values()) and _r45.run.player[1] <= 2,
      f"Route 45: exact map; in from Blackthorn (north) at {_r45.run.player}; the Dark Cave's mouth, west to Route 46")
_r46 = kanto("JOHTO_ROUTE_46", came="JOHTO_ROUTE_29")
check((_r46.run.floor.w, _r46.run.floor.h) == (32, 64) and {"DARK_CAVE", "JOHTO_ROUTE_45", "JOHTO_ROUTE_29"} == set(_r46.run.floor.exits.values()) and _r46.run.player[1] >= 57,
      f"Route 46: exact map; in from Route 29's gate (south) at {_r46.run.player}; the Dark Cave's mouth, east to Route 45")
_r27 = kanto("KANTO_ROUTE_27", came="NEW_BARK_TOWN")
check((_r27.run.floor.w, _r27.run.floor.h) == (192, 32) and {"NEW_BARK_TOWN", "TOHJO_FALLS", "KANTO_ROUTE_26"} == {v for v in _r27.run.floor.exits.values() if not str(v).startswith("WARP")} and _r27.run.player[0] <= 2,
      f"Route 27: exact map; in from New Bark by Surf (west) at {_r27.run.player}; Tohjo Falls' two mouths, east to Route 26")
_sw = [(m.x, m.y) for f in _r27.run.floors for m in f.movers if m.kind == "trainer" and "Swimmer Glenn" in str(m.payload)]
check(len(_sw) == 1, f"Route 27: our swimmer still out on the water (N16: moved off the game's trainer tiles) {_sw}")
_r26 = kanto("KANTO_ROUTE_26", came="KANTO_ROUTE_27")
check((_r26.run.floor.w, _r26.run.floor.h) == (32, 128) and {"POKEMON_LEAGUE_GATE", "KANTO_ROUTE_27"} == {v for v in _r26.run.floor.exits.values() if not str(v).startswith("WARP")} and _r26.run.player[0] <= 1 and _r26.run.player[1] >= 100,
      f"Route 26: exact map; in from Route 27 on its west edge (SoulSilver's seam) at {_r26.run.player}; the Reception Gate north")
_rt = kanto("RADIO_TOWER", came="GOLDENROD_CITY")
_rt.run.player = (13, 3)
_rt_in = _rt.run.player
check(_rt.run.n_floors == 6 and "GOLDENROD_CITY" in _rt.run.floor.exits.values(), "the Radio Tower: exact 1F-5F and the Observation Deck; in from Goldenrod on 1F")
_ms = kanto("MT_SILVER", came="MT_SILVER_CITY")
_msa = (_ms.recipe.get("art") or {})
_msf = _msa.get("floors") or []
check(_ms.run.n_floors == 8 and (_ms.run.floor.w, _ms.run.floor.h) == (51, 57) and _ms.run.player[1] >= 50
      and {v for v in _ms.run.floor.exits.values() if not str(v).startswith("WARP")} == {"MT_SILVER_CITY"},
      f"Mt. Silver (N16): one cave of eight floors as in SoulSilver; in from the Pokemon Center's clearing at 1F's foot {_ms.run.player}")
_msl = [len(f.get("links") or {}) for f in _msf]
_bad = [(i, k, v) for i, f in enumerate(_msf) for k, v in (f.get("links") or {}).items() if not (0 <= v[0] < 8 and _msf[v[0]]["art"][v[2]][v[1]] != "c")]
check(_msl == [6, 3, 1, 1, 7, 7, 2, 1] and not _bad, f"Mt. Silver: every ladder and mouth joined to its real far end {_msl} {_bad[:3]}")
_ff = _msa.get("figure_floors") or {}
check(_ff.get("SEEK MOLTRES") == 3 and _ff.get("CHALLENGE RED") == 7 and _msf[7].get("people") == ["CHALLENGE RED"]
      and {o["text"] for o in _prog["MT_SILVER"]["route_menu"]} >= {"SEEK MOLTRES", "CHALLENGE RED"},
      f"Mt. Silver: Moltres in its own chamber, Red at the summit {_ff}")
check([sum(r.count("/") for r in f["art"]) for f in _msf] == [11, 0, 0, 12, 0, 20, 10, 0],
      f"Mt. Silver: the Rock Climb walls where the game has them {[sum(r.count('/') for r in f['art']) for f in _msf]}")
# Johto's Victory Road (11-22, Jordan: "add it"): SoulSilver's own cave (D43R0101-03) between the Reception Gate and the Silver League
_vr = kanto("JOHTO_VICTORY_ROAD", came="POKEMON_LEAGUE_GATE")
_vra = (_vr.recipe.get("art") or {})
_vrf = _vra.get("floors") or []
check(_vr.run.n_floors == 3 and _vr.run.index == 0 and (_vr.run.floor.w, _vr.run.floor.h) == (37, 60) and _vr.run.player[1] >= 55
      and {v for v in _vr.run.floor.exits.values() if not str(v).startswith("WARP")} == {"POKEMON_LEAGUE_GATE"}
      and _prog["JOHTO_VICTORY_ROAD"]["route_name"] == "Victory Road" and _prog["JOHTO_VICTORY_ROAD"]["region"] == "JOHTO",
      f"Johto's Victory Road: SoulSilver's three floors, shown as Victory Road; in from the Reception Gate's great door at 1F's foot {_vr.run.player}")
_vr2 = kanto("JOHTO_VICTORY_ROAD", came="SILVER_LEAGUE_PLATEAU")
check(_vr2.run.index == 2 and _vr2.run.player[1] <= 5 and "SILVER_LEAGUE_PLATEAU" in _vr2.run.floor.exits.values(),
      f"...and down from the Silver League's cliff foot you arrive at the top of 3F {_vr2.run.index, _vr2.run.player}")
_vrl = [len(f.get("links") or {}) for f in _vrf]
_bad = [(i, k, v) for i, f in enumerate(_vrf) for k, v in (f.get("links") or {}).items() if not (0 <= v[0] < 3 and _vrf[v[0]]["art"][v[2]][v[1]] != "c")]
check(_vrl == [2, 9, 4] and not _bad, f"Johto's Victory Road: every stair joined to its real far end {_vrl} {_bad[:3]}")
_vrt = _prog["JOHTO_VICTORY_ROAD"]["trainer_pool"]
_vff = _vra.get("figure_floors") or {}
check([t["name"] for t in _vrt] == ["{rival_name}"] and _vrt[0]["victory_flag"] == "defeated_rival_victory_road_johto" and _vrf[2].get("trainer_spots") == ["{rival_name}"]
      and _vrf[2]["art"][18][31] == "X" and not _prog["MT_SILVER_CITY"].get("on_enter_event"),
      "Johto's Victory Road: the rival waits on 3F where SoulSilver has him (his battle moved here from Mt. Silver City's old stand-in)")
check(sum(1 for k in _vff if k != "{rival_name}") == 9 and sum(len(f.get("hidden") or {}) for f in _vrf) == 7,
      f"Johto's Victory Road: SoulSilver's nine item balls and seven hidden items {sorted(_vff)}")
story.story_flags.pop("defeated_red_gyarados", None)
_lor = kanto("LAKE_OF_RAGE", came="JOHTO_ROUTE_43")
_gy = [m for f in _lor.run.floors for m in f.movers if m.kind == "figure" and m.payload.get("action") == "BOSS"]
check((_lor.run.floor.w, _lor.run.floor.h) == (96, 64) and {str(v) for v in _lor.run.floor.exits.values() if not str(v).startswith(("WARP:", "OUT:", "ROOM:"))} == {"JOHTO_ROUTE_43"} and _lor.run.player[1] >= 60
      and _gy and (_gy[0].x, _gy[0].y) == (45, 39), f"Lake of Rage: exact map; in from Route 43 (south); the Red Gyarados out on the lake {[(m.x, m.y) for m in _gy]}")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "MAHOGANY_TOWN", "JOHTO_ROUTE_42"
_mh = _CS(g); g.change_state(_mh); _tap_through(_mh)
check(isinstance(_mh, _WTS) and (_mh.w, _mh.h) == (32, 32) and {"gym", "center", "souvenir"} <= set(_mh.doors.values()) and _mh.player[0] <= 2
      and {"JOHTO_ROUTE_42", "JOHTO_ROUTE_44"} == set(_mh.exits.values()) and "JOHTO_ROUTE_43" in _mh.town_map["rooms"]["gate"]["exits"].values(),
      "Mahogany Town: exact map, in from Route 42 (west); the Gym and Center; Routes 43 and 44, the shop over the hideout")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "BLACKTHORN_CITY", "ICE_PATH"
_bt = _CS(g); g.change_state(_bt); _tap_through(_bt)
check(isinstance(_bt, _WTS) and (_bt.w, _bt.h) == (64, 64) and {"gym", "center", "mart"} <= set(_bt.doors.values()) and _bt.player[0] >= 48
      and {"JOHTO_ROUTE_45", "ICE_PATH", "DRAGONS_DEN"} == set(_bt.exits.values()),
      f"Blackthorn City: exact map, in from the Ice Path (east) at {_bt.player}; the Gym on the lake, Surf to Dragon's Den, the bridge to Route 45")
g.walk_town_pos = None
# Johto's building insides (11-11): every town's Gym, Center, Mart, lab, home and shop is SoulSilver's own room; walk into each, find its people, walk out
_jr = {}
for _k in ("NEW_BARK_TOWN", "CHERRYGROVE_CITY", "VIOLET_CITY", "AZALEA_TOWN", "CIANWOOD_CITY", "GOLDENROD_CITY", "OLIVINE_CITY", "ECRUTEAK_CITY", "MAHOGANY_TOWN", "BLACKTHORN_CITY", "MT_SILVER_CITY", "SAFARI_ZONE_GATE"):
    g.walk_town_pos = None; g.walk_town_room = None
    story.current_area_key, story.last_area_key = _k, None
    _t = _CS(g); g.change_state(_t); _tap_through(_t)
    _bad, _n, _gym = [], 0, None
    for _d, _name in sorted((_t.town_map.get("inside") or {}).items()):
        _door = tuple(int(v) for v in _d.split(","))
        _t._enter(_door)
        if _t.room != _name:
            _bad.append((_d, "not in", _name)); continue
        _seen = {_name}
        while True:  # (through the building's rooms by their stairs)
            _n += 1
            if any(isinstance(q, dict) and str(q.get("action")).upper() == "GYM" for o in _t.people.values() if isinstance(o, dict)
                   for q in o.get("any", [o])):   # (a Leader with stages, by the story: Cianwood's Chuck under the waterfall first, 11-22)
                _gym = _t.room
            if not all(isinstance(o, dict) for o in _t.people.values()):
                _bad.append((_d, _t.room, "someone with nothing to say"))
            _nxt = next((v for v in _t.exits.values() if str(v).startswith("ROOM:") and v[5:] not in _seen), None)
            if not _nxt:
                break
            _t._leave(_nxt); _seen.add(_nxt[5:])
            if _t.room != _nxt[5:]:
                _bad.append((_d, "stairs to", _nxt)); break
        _t._go(_name, "OUT:" + _d)  # (back to the first room, at its mat)
        _t._leave("OUT:" + _d)
        if _t.room is not None or _t.player not in ((_door[0], _door[1] + 1), (_door[0], _door[1] - 1), (_door[0] - 1, _door[1] + 1), (_door[0] + 1, _door[1] + 1)):  # (below the door; above it for a door on its building's far side: Olivine's harbour; beside the tile below when someone stands there: Azalea's Rocket by the Gym, SoulSilver's spot)
            _bad.append((_d, "out at", _t.player))
        g.walk_town_room = None
    _jr[_k] = (_n, _gym, _bad)
check(all(not v[2] for v in _jr.values()) and all(_jr[k][1] for k in _jr if k not in ("NEW_BARK_TOWN", "CHERRYGROVE_CITY", "MT_SILVER_CITY", "SAFARI_ZONE_GATE")) and sum(v[0] for v in _jr.values()) >= 45,
      f"Johto's building insides: {sum(v[0] for v in _jr.values())} rooms walked in twelve places (in by the door, up every stair, out below the door); each of the eight Gyms has its Leader inside {[(k, v[2]) for k, v in _jr.items() if v[2]]}")
# the Silver League plateau (11-22, Jordan: "make it like SoulSilver's own"): SoulSilver's Indigo Plateau (zone T10), its League walked
import json as _json_s
_tm_s = _json_s.load(open("assets/town_maps.json", encoding="utf-8"))
g.walk_town_pos = None; g.walk_town_room = None
story.current_area_key, story.last_area_key = "SILVER_LEAGUE_PLATEAU", "JOHTO_VICTORY_ROAD"
_sl = _CS(g); g.change_state(_sl); _tap_through(_sl)
_sl_in = _sl.player
_sl_gym = _sl.area_data["gym"]
_slm = _tm_s["SILVER_LEAGUE_PLATEAU"]
_sl._enter(next(t for t, k in _sl.doors.items() if k == "league"))
_sl_opts = sorted(str(o.get("action")) for o in _sl.people.values() if str(o.get("action")) in ("HEAL", "SHOP"))
check(isinstance(_sl, _WTS) and (len(_slm["art"][0]), len(_slm["art"])) == (32, 32) and _slm["roofs"]["_picture"]["f"] == "ss_ground/T10.png" and _sl_in[1] >= 24
      and _sl.room == "lobby" and _sl_opts == ["HEAL", "SHOP"] and [t["name"] for t in _sl_gym["trainers"]] == ["Will", "Koga", "Bruno", "Karen"] and _sl_gym["leader"]["name"] == "Lance",
      f"the Silver League plateau: SoulSilver's own (T10); up from Victory Road at the cliff foot {_sl_in}; the lobby's nurse and clerk; Will, Koga, Bruno, Karen, Champion Lance")
_sl_rooms = _slm["rooms"]
_sl_chain = ["league_will", "league_koga", "league_bruno", "league_karen", "league_lance", "hall_of_fame"]
_sl_ok = []
for _i, _rn in enumerate(_sl_chain[:5]):
    _r = _sl_rooms.get(_rn) or {}
    _m = [p for p in _r.get("people", []) if isinstance(p, dict) and p.get("action") == "LEAGUE"]
    _bar = (_r.get("barred") or [{}])[0].get("until", {}).get("flag_condition")
    _sl_ok.append(bool(_m) and _m[0]["index"] == _i and "ROOM:" + _sl_chain[_i + 1] in _r["exits"].values()
                  and _bar == (f"league_won_SILVER_LEAGUE_PLATEAU_{_i + 1}" if _i < 4 else "hall_of_fame_due_SILVER_LEAGUE_PLATEAU"))
check(all(_sl_ok) and "ROOM:league_will" in _sl_rooms["lobby"]["exits"].values() and any("johto_hall_of_fame" in str(sc.get("then")) for sc in _sl_rooms["hall_of_fame"].get("scenes", [])),
      f"...the lobby's hall leads to Will's room, then Koga, Bruno, Karen, Lance (each far door shut till you've won there), then the Hall of Fame {_sl_ok}")
_ip_gym = g.loader.area_data["STORY_PROGRESSION"]["INDIGO_PLATEAU"]["gym"]
check([t["name"] for t in _ip_gym["trainers"]] == ["Lorelei", "Bruno", "Agatha", "Lance"] and _sl.exits and set(_slm["exits"].values()) == {"JOHTO_VICTORY_ROAD"},
      "...and Indigo keeps Kanto's own (Lorelei, Bruno, Agatha, Lance): the two leagues are distinct; the Silver plateau's way down leads into Johto's Victory Road")
g.walk_town_pos = None; g.walk_town_room = None
# Johto's gatehouses and route buildings (11-12): walked through, as Kanto's are. From the far side you arrive inside, at the far mat
_gt = {}
for _k, _far in (("JOHTO_ROUTE_29", "JOHTO_ROUTE_46"), ("JOHTO_ROUTE_35", "NATIONAL_PARK"), ("ILEX_FOREST", "JOHTO_ROUTE_34")):
    _r = kanto(_k, came=_far)
    _gt[(_k, _far)] = (_r.run.index >= _r.run.recipe.get("art", {}).get("outdoor_floors", 1), _far in map(str, _r.run.floor.exits.values()), any(str(v).startswith("WARP") for v in _r.run.floor.exits.values()))
for _k, _far in (("GOLDENROD_CITY", "JOHTO_ROUTE_35"), ("MAHOGANY_TOWN", "JOHTO_ROUTE_43"), ("RUINS_OF_ALPH", "JOHTO_ROUTE_36"), ("SAFARI_ZONE_GATE", "JOHTO_SAFARI_ZONE")):
    g.walk_town_pos = None; g.walk_town_room = None
    story.current_area_key, story.last_area_key = _k, _far
    _t = _CS(g); g.change_state(_t); _tap_through(_t)
    _in = _t.room
    _out = next((v for v in _t.exits.values() if str(v).startswith("OUT:")), None)
    _t._leave(_out) if _out else None
    _gt[(_k, _far)] = (_in == "gate", _out is not None, _t.room is None)
check(all(all(v) for v in _gt.values()), f"Johto's gatehouses: from the far side you arrive inside the gatehouse, and its other mat leads on {[(k, v) for k, v in _gt.items() if not all(v)]}")
_r32 = kanto("JOHTO_ROUTE_32", came="VIOLET_CITY")
_r34b = kanto("JOHTO_ROUTE_34", came="GOLDENROD_CITY")
check("center" in (_r32.run.recipe.get("art") or {}).get("room_floors", {}) and "daycare" in (_r34b.run.recipe.get("art") or {}).get("room_floors", {}),
      "Route 32's Pokemon Center and Route 34's Day Care are rooms you walk into")
g.walk_town_pos = None; g.walk_town_room = None
# Johto places that had no map (11-12): each from SoulSilver's own room or zone
_nm = {}
for _k, _cm in (("MR_POKEMONS_HOUSE", "JOHTO_ROUTE_30"), ("MT_SILVER_CITY", "KANTO_ROUTE_28")):
    g.walk_town_pos = None; g.walk_town_room = None
    story.current_area_key, story.last_area_key = _k, _cm
    _t = _CS(g); g.change_state(_t); _tap_through(_t)
    _nm[_k] = (isinstance(_t, _WTS), (_t.w, _t.h), _t.player, set(map(str, _t.exits.values())), len(_t.people), set(_t.doors.values()))
story.defeated_trainers.pop("ECRUTEAK_DANCE_THEATER", None)
_jb = list(story.badges.get("JOHTO", []))   # (HGSS: the Kimono Girls battle only after the Rising Badge, 11-15)
story.badges["JOHTO"] = ["ZEPHYR", "HIVE", "PLAIN", "FOG", "STORM", "MINERAL", "GLACIER", "RISING"]
_dt = kanto("ECRUTEAK_DANCE_THEATER", came="ECRUTEAK_CITY")
_dtt = {(m.x, m.y) for m in _dt.run.floor.movers if m.kind == "trainer"}
story.badges["JOHTO"] = _jb
check(set(map(str, _dt.run.floor.exits.values())) == {"ECRUTEAK_CITY"} and len(_dtt) == 5,
      f"the Dance Theater: SoulSilver's hall, in at its door {_dt.run.player}, the five Kimono Girls on the stage {sorted(_dtt)}")
check(_nm["MR_POKEMONS_HOUSE"][0] and _nm["MR_POKEMONS_HOUSE"][3] == {"JOHTO_ROUTE_30"} and _nm["MR_POKEMONS_HOUSE"][4] == 2,
      f"Mr. Pokemon's house: SoulSilver's room, in from Route 30 at {_nm['MR_POKEMONS_HOUSE'][2]}, two people to talk to")
check(_nm["MT_SILVER_CITY"][0] and _nm["MT_SILVER_CITY"][1] == (32, 32) and _nm["MT_SILVER_CITY"][3] == {"MT_SILVER", "KANTO_ROUTE_28"} and "center" in _nm["MT_SILVER_CITY"][5]
      and _nm["MT_SILVER_CITY"][2][0] >= 29, f"Mt. Silver's clearing: SoulSilver's 32 x 32, in from Route 28 (east) at {_nm['MT_SILVER_CITY'][2]}; the Center, the cave mouth, a guide for the League plateau")
_r28 = kanto("KANTO_ROUTE_28", came="MT_SILVER_CITY")
_r28in = tuple(_r28.run.player)
_r28b = kanto("KANTO_ROUTE_28", came="POKEMON_LEAGUE_GATE")
check((_r28.run.floor.w, _r28.run.floor.h) == (64, 32) and {v for v in _r28.run.floor.exits.values() if not str(v).startswith("WARP")} == {"MT_SILVER_CITY", "POKEMON_LEAGUE_GATE"}
      and _r28in[0] <= 1 and _r28b.run.player[0] >= 50,
      f"Route 28 (N17): SoulSilver's 64 x 32; in from Mt. Silver's clearing (west) at {_r28in}, from the Reception Gate (east) at {_r28b.run.player}")
_aq = kanto("JOHTO_SS_AQUA", came="OLIVINE_CITY")
check(_aq.run.n_floors == 7 and {"OLIVINE_CITY", "VERMILLION_CITY"} <= set(map(str, _aq.run.floor.exits.values())),
      f"the S.S. Aqua: seven decks and cabins from SoulSilver; aboard from Olivine at {_aq.run.player}; gangway mats for Olivine and Vermilion")
_fa = kanto("FRONTIER_ACCESS", came="JOHTO_ROUTE_40")
_fa2 = kanto("FRONTIER_ACCESS", came="JOHTO_BATTLE_FRONTIER")
check({"JOHTO_ROUTE_40", "JOHTO_BATTLE_FRONTIER"} == {str(v) for v in _fa.run.floor.exits.values() if not str(v).startswith("WARP")}
      and _fa.run.player[1] > _fa2.run.player[1],   # (11-22: SoulSilver's own Frontier Access, D32R0102 outdoors: Route 40 south, the Frontier north)
      f"Frontier Access: SoulSilver's own (outdoors); in from Route 40 at the south gate {_fa.run.player}, from the Frontier at the north {_fa2.run.player}")
_bfr = kanto("JOHTO_BATTLE_FRONTIER", came="FRONTIER_ACCESS")
_bfk = {k for k in (_bfr.recipe.get("art") or {}).get("buildings", {}).values()}
check((_bfr.run.floors[0].w, _bfr.run.floors[0].h) == (96, 96) and _bfr._floor_name(_bfr.run.index) == "Gate"
      and "FRONTIER_ACCESS" in {str(v) for v in _bfr.run.floor.exits.values()} and {"jtower", "jgate", "jfactory", "jhall", "jcastle", "jarcade"} <= _bfk,
      f"the Battle Frontier (N18): SoulSilver's plaza; in from Frontier Access through the gate ({_bfr._floor_name(_bfr.run.index)}); the Tower north, five facility doors {sorted(_bfk)}")
_bc = kanto("BUG_CONTEST", came="NATIONAL_PARK")
check((_bc.run.floor.w, _bc.run.floor.h) == (96, 96) and set(map(str, _bc.run.floor.exits.values())) == {"NATIONAL_PARK"} and not [m for m in _bc.run.floor.movers if m.kind == "trainer"],
      "the Bug-Catching Contest: the National Park's own map, no trainers, every gate back to the park")
g.walk_town_pos = None; g.walk_town_room = None
story.current_area_key, story.last_area_key = "OLIVINE_CITY", "JOHTO_ROUTE_39"
_ol = _CS(g); g.change_state(_ol); _tap_through(_ol)
_ol._enter(next(t for t, k in _ol.doors.items() if k == "harbor"))
_ol_in = (_ol.room, len(_ol.people))
_ol._leave("ROOM:harbor_2")
check(_ol_in[0] == "harbor" and _ol_in[1] >= 3 and _ol.room == "harbor_2" and "JOHTO_SS_AQUA" in _ol.exits.values(),
      f"Olivine's harbour: the terminal (the ferry man and the rides to ask for), its stairs out to the pier, the gangway onto the S.S. Aqua {_ol_in}")
g.walk_town_pos = None; g.walk_town_room = None
story.current_area_key, story.last_area_key = "MAHOGANY_TOWN", "JOHTO_ROUTE_42"
_mh2 = _CS(g); g.change_state(_mh2); _tap_through(_mh2)
_mh2._enter(next(t for t, k in _mh2.doors.items() if k == "souvenir"))
check(_mh2.room == "souvenir" and "ROCKET_HQ" in _mh2.exits.values() and any((o.get("text") if isinstance(o, dict) else o) == "Shop" for o in _mh2.people.values()),   # (11-15: Lance and Dragonite there too, after the red Gyarados)
      f"Mahogany's shop: its own room, the clerk at the counter, the stairs down to the hideout {sorted(map(str, _mh2.exits.values()))}")
g.walk_town_pos = None; g.walk_town_room = None
story.current_area_key, story.last_area_key = "SAFARI_ZONE_GATE", "JOHTO_ROUTE_48"
_sg = _CS(g); g.change_state(_sg); _tap_through(_sg)
_sg_in = _sg.player
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "SAFARI_ZONE_GATE", "JOHTO_SAFARI_ZONE"
_sg2 = _CS(g); g.change_state(_sg2); _tap_through(_sg2)
check(isinstance(_sg, _WTS) and (_sg.w, _sg.h) == (64, 64) and _sg_in[1] >= 61 and {"JOHTO_ROUTE_48"} == set(_sg.exits.values()) and "center" in _sg.doors.values()
      and len(_sg._door_options("center")) == 1 and _sg2.room == "gate" and "JOHTO_SAFARI_ZONE" in _sg2.exits.values(),
      f"Safari Zone Gate: a town now, SoulSilver's plaza; in from Route 48 (south) at {_sg_in}; the Center heals; back out of the Safari Zone you stand inside the gatehouse {_sg2.room, _sg2.player}")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "DRAGON_SHRINE", "DRAGONS_DEN"
_ds = _CS(g); g.change_state(_ds); _tap_through(_ds)
check(isinstance(_ds, _WTS) and set(_ds.exits.values()) == {"DRAGONS_DEN"} and (_ds.w, _ds.h) == (9, 13) and _ds.player[1] >= 9,
      f"the Dragon Shrine: inside, in at its door {_ds.player}; the Elder's test")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "POKEMON_LEAGUE_GATE", "KANTO_ROUTE_26"
_lg = _CS(g); g.change_state(_lg); _tap_through(_lg)
check(isinstance(_lg, _WTS) and {"KANTO_ROUTE_22", "KANTO_ROUTE_28", "KANTO_ROUTE_26"} == set(_lg.exits.values()) and "leaguegate" in _lg.doors.values() and _lg.player[1] >= 8 and (_lg.w, _lg.h) == (15, 12),
      f"the Reception Gate: FireRed's League Gate (Jordan 11-16); in from Route 26 (south) at {_lg.player}; Route 28 west, Route 22 east, the great door north")
_gg = [o for o in _prog["POKEMON_LEAGUE_GATE"]["explore_options"] if o.get("text") == "GATE GUARD"]
_lg_reg = story.story_flags.get("border_region")
_gg_on = {}
for _reg in ("JOHTO", "KANTO"):
    story.story_flags["border_region"] = _reg
    _gg_on[_reg] = [o["event"]["requires"] for o in _gg if _lg._check_menu_condition(o.get("condition"))]
story.story_flags["border_region"] = _lg_reg
check(_gg_on == {"JOHTO": [["has_8_johto_badges"]], "KANTO": [["has_8_kanto_badges"]]},
      f"...its guard checks Johto's eight Badges on a Johto playthrough, Kanto's on a Kanto one {_gg_on}")
_lg_held = _lg._check_menu_condition
_lg_door = next(t for t, k in _lg.doors.items() if k == "leaguegate")
_lg_seen = {}
for _name, _yes in (("johto", {"has_8_johto_badges"}), ("kanto", {"has_8_kanto_badges"}), ("both", {"has_8_johto_badges", "has_8_kanto_badges"}), ("neither", set())):
    _lg._check_menu_condition = lambda c, _y=_yes: (c in _y) if c in ("has_8_johto_badges", "has_8_kanto_badges") else _lg_held(c)
    _lg_seen[_name] = sorted(o.get("target_area") for o in _lg._door_options("leaguegate"))
_lg._check_menu_condition = _lg_held
check(_lg_seen == {"johto": ["JOHTO_VICTORY_ROAD"], "kanto": ["VICTORY_ROAD"], "both": ["JOHTO_VICTORY_ROAD", "VICTORY_ROAD"], "neither": []},
      f"the Reception Gate's great door: with Johto's eight badges it leads into Johto's Victory Road, with Kanto's into Kanto's, with both you choose {_lg_seen}")
g.walk_town_pos = None; g.walk_town_room = None
story.current_area_key, story.last_area_key = "POKEMON_LEAGUE_GATE", "JOHTO_VICTORY_ROAD"
_lg2 = _CS(g); g.change_state(_lg2); _tap_through(_lg2)
check(abs(_lg2.player[0] - _lg_door[0]) <= 1 and _lg2.player[1] <= _lg_door[1] + 2, f"...and back from Victory Road you stand at the great door {_lg2.player}")
g.walk_town_pos = None
story.current_area_key, story.last_area_key = "POKEATHLON_DOME", "NATIONAL_PARK"
_pd = _CS(g); g.change_state(_pd); _tap_through(_pd)
check(isinstance(_pd, _WTS) and set(_pd.exits.values()) == {"NATIONAL_PARK"} and "dome" in _pd.doors.values() and len(_pd._door_options("dome")) == 1 and "CONSTRUCTION" in str(_pd._door_options("dome")[0]) and _pd.player[1] >= 40,
      f"the Pokeathlon Dome: its plaza, in from the National Park's north gatehouse {_pd.player}; the Dome's door says it's under construction")
g.walk_town_pos = None  # (Hoenn's places: dev/checks/hoenn_maps_body.py; the old checks: kanto_handoff/hoenn_rom_tools/old_hoenn_checks.py)


class _Held:  # (an arrow key held down)
    def __init__(self, key):
        self.key = key

    def __getitem__(self, key):
        return key == self.key


_orig_pressed = pygame.key.get_pressed
try:  # hold to keep walking (Jordan, 11-07), in a town and on a route map
    _ld.npc_active = False
    _x0 = _ld.player[0]
    pygame.key.get_pressed = lambda: _Held(pygame.K_LEFT)
    for _k in range(40):
        _ld.update()
    _town_ok = _ld.player[0] <= _x0 - 3
    _r29 = kanto("JOHTO_ROUTE_29", came="NEW_BARK_TOWN")
    _r29.run.floor.movers = []  # (none in the way)
    _r29.run.player = (93, 14)  # (the sand road in from New Bark)
    _rx = _r29.run.player[0]
    for _k in range(40):
        _r29.update()
    check(_town_ok and _r29.run.player[0] <= _rx - 3, "hold an arrow key: you keep walking (town and route)")
finally:
    pygame.key.get_pressed = _orig_pressed
from src.pokemon import items as _it2
_tw = mk(158)
_tw.held_item = "MYSTIC_WATER"
check(_it2.held_boost(_tw, "WATER") == 1.2 and _it2.held_boost(_tw, "FIRE") == 1.0,
      "Mystic Water, held: Water moves x1.2 (only Water)")

g.walk_towns = False

print(f"##### {fails} failures")
