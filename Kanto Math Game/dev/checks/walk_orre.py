# Orre's walked maps add ways with no menu button, each behind its own gate on the map (11-23): the Pyrite Building behind
# the Cipher Peons (till the Pyrite Badge), its lift down to The Under (the Elevator Key, after Vander's Time Flute - story
# rework 11-24, the order below follows the reworked story: the Journal's MAIN steps).
_menu_links = links
WALK_GATES = {("PYRITE_TOWN", "PYRITE_BUILDING"): lambda: "PYRITE" in story.badges.get("ORRE", []),
              ("PYRITE_BUILDING", "THE_UNDER"): lambda: story.inventory.get("ELEVATOR_KEY", 0) > 0}


def links(area):
    out = [t for t in _menu_links(area) if WALK_GATES.get((area, t), lambda: True)()]
    return out + [t for (a, t), ok in WALK_GATES.items() if a == area and t not in out and ok()]


import json as _json
_MAPS = _json.load(open("assets/town_maps.json", encoding="utf-8"))


def _strings(o, out):
    if isinstance(o, str):
        out.add(o)
    elif isinstance(o, dict):
        for v in o.values():
            _strings(v, out)
    elif isinstance(o, list):
        for v in o:
            _strings(v, out)
    return out


def _open_now(o, st, town):
    """Is this option or route button shown and passable now (its flag and condition, as the game judges them)?"""
    if not _flag_ok(o.get("flag_condition")):
        return False
    cond = o.get("condition")
    if not cond:
        return True
    return st._check_menu_condition(cond) if town else st._check_route_condition(cond, False, o)


def walked_links(area):
    """R1 (11-23): only the ways a player can walk - the map's own exits (the place, its rooms, every floor), each behind
    the travel option or route button that locks it, and doors that run a kind of travel option (the bike's "cycle", a
    harbour). Menu buttons with no way on the map don't count: that is how the Shadow Lab's missing way in hid."""
    a, m = PROG.get(area) or {}, _MAPS.get(area) or {}
    st = _state(area)
    town = a.get("area_type") == "town"
    words = _strings(m, set())
    kinds = set((m.get("buildings") or {}).values()) | {w[5:] for w in words if w.startswith("door:")}
    for r in (m.get("rooms") or {}).values():
        kinds |= set((r.get("buildings") or {}).values())
    out = []
    for t in dict.fromkeys(t for t in _walk_exits(area) if t != area):
        if town:
            opt = next((o for o in a.get("travel_options") or [] if o.get("target_area") == t), None) or                   next((o for o in a.get("explore_options") or [] if o.get("action") == "TRAVEL" and o.get("target_area") == t), None)
            if opt is None or not _open_now(opt, st, True):
                continue
        else:
            it = next((o for o in a.get("route_menu") or [] if o.get("action") in ("EXIT", "TRAVEL")
                       and (o.get("target_area") or o.get("target")) == t), None)
            if it is not None and not _open_now(it, st, False):
                continue
        out.append(t)
    for o in (a.get("travel_options") or []) + (a.get("route_menu") or []):   # (doors that offer rides: the bike, a boat)
        d, t = o.get("door"), o.get("target_area") or o.get("target")
        if d and t and d in kinds and t not in out and _open_now(o, st, town):
            out.append(t)
    return [t for t in out if WALK_GATES.get((area, t), lambda: True)()]


def walkthrough(tag):
    global seen
    print(f"##### {tag}")
    story.badges = {"ORRE": []}
    story.inventory = {}
    story.story_flags = {"visited_OUTSKIRT_STAND": True}
    story.defeated_trainers = {}
    story.starting_region = "ORRE"
    R, S = "ORRE", "OUTSKIRT_STAND"
    seen = report("start (no partner yet)", S, set())
    print("   FAIL" if "ORRE_DESERT" in seen else "   OK", "the Desert Trail waits for Espeon or Umbreon")
    story.story_flags["received_starter_orre"] = True
    # (step, flags to set, badges, the areas that must open) - the reworked story (11-24), in the Journal's order
    STEPS = [("the Snag Machine", {"got_snag_machine": True}, [], ["PYRITE_TOWN"]),
             ("PHENAC badge", {}, ["PHENAC"], []),
             ("Duking's power cut", {"orre_beat_cail": True, "orre_power_out": True}, [], ["CONSTRUCTION_LOT"]),
             ("the gear back, PYRITE badge", {"orre_power_on": True}, ["PYRITE"], ["PYRITE_BUILDING"]),
             ("Doken on the Pyrite Building roof", {"orre_beat_doken": True}, [], ["PYRITE_CAVE"]),
             ("Miror B. at Pyrite Cave (then Fateen by the bike)", {"orre_miror_cave": True, "orre_fateen": True}, [], ["AGATE_VILLAGE"]),
             ("the Agate elder", {"met_agate_elder": True}, [], ["RELIC_CAVE"]),
             ("Skrub at the Relic Cave", {"orre_beat_skrub": True}, [], ["MT_BATTLE"]),
             ("AGATE badge, Dakim, Vander's Time Flute, the Elevator Key",
              {"orre_dakim_mt_battle": True, "orre_time_flute": True, "orre_got_jail_key": True, "orre_elevator_key": True,
               "_item": "ELEVATOR_KEY"}, ["AGATE"], ["THE_UNDER", "UNDER_COLOSSEUM"]),
             ("Venus, then the Under Colosseum", {"orre_kids_grid": True, "orre_r_disk": True, "cleared_the_under": True,
                                                   "orre_maingate_key": True, "orre_under_colosseum_won": True}, [], ["SHADOW_PKMN_LAB"]),
             ("Ein's lab and his Data ROM", {"orre_ein_lab": True, "orre_data_rom_given": True}, [], ["SNAGEM_HIDEOUT", "REALGAM_TOWER"]),
             ("SNAGEM badge, Evice at Realgam (Part 2)", {"col_venus_realgam": True, "col_ein_realgam": True, "col_miror_realgam": True,
                                                         "col_dakim_realgam": True, "col_gonzap_realgam": True,
                                                         "orre_evice_beaten": True, "orre_part2": True},
              ["SNAGEM"], ["GATEON_PORT", "POKEMON_HQ_LAB", "KAMINKO_HOUSE", "DEEP_COLOSSEUM"]),
             ("Krane taken, the machine part, GATEON badge", {"xd_krane_taken": True, "xd_machine_part_given": True,
                                                              "xd_gateon_bridges": True}, ["GATEON"], ["XD_CIPHER_LAB"]),
             ("Lovrina", {"xd_lovrina_beaten": True}, [], ["XD_ONBS"]),
             ("Nett's ROM, Exol", {"xd_nett_rom": True, "xd_exol_beaten": True}, [], []),
             ("Phenac freed, Hordel, Gonzap", {"orre_snattle_phenac": True, "xd_pregym_freed": True, "xd_hordel": True,
                                               "beat_gonzap": True}, [], ["ORRE_COLOSSEUM"]),
             ("the Orre Colosseum", {"orre_colosseum_won": True}, [], ["XD_CIPHER_KEY_LAIR"]),
             ("Gorigan, KEY_LAIR badge, the Master Ball", {"xd_lair_guards": True, "xd_lair_voltage": True, "xd_gorigan_beaten": True,
                                                          "xd_master_ball": True}, ["KEY_LAIR"], ["XD_CITADARK_ISLE"]),
             ("Greevil, Eldes: CITADARK and REALGAM badges", {"xd_greevil_beaten": True, "xd_eldes_beaten": True},
              ["CITADARK", "REALGAM"], [])]
    for title, flags, bs, opens in STEPS:
        for o in opens:
            print("   FAIL" if o in seen else "   OK", f"{o} waits for {title}")
        if flags.get("_item"):
            story.inventory[flags["_item"]] = 1
        story.story_flags.update({k: v for k, v in flags.items() if not k.startswith("_")})
        for b in bs:
            badge(R, b)
        seen = report(title, S, seen)
        for o in opens:
            print("   OK" if o in seen else "   FAIL", f"{o} opens after {title}")
        if title.startswith("SNAGEM badge"):   # (Part 2: Cipher holds the Pre Gym till Exol is beaten)
            print("   FAIL" if "PRESTIGE_PRECEPT_CENTER" in links("PHENAC_CITY") else "   OK", "the Pre Gym shut in Part 2 till Exol")
        if title == "Nett's ROM, Exol":
            print("   OK" if "PRESTIGE_PRECEPT_CENTER" in links("PHENAC_CITY") else "   FAIL", "the Pre Gym opens after Exol")
    POST = ["ORRE_BATTLE_FRONTIER", "ORRE_SKY_PILLAR", "ORRE_BIRTH_ISLAND", "ORRE_LAKE_OF_RAGE"]
    gate_check("orre post-game", POST, S, "beat_orre_champion")
    story.story_flags["beat_orre_champion"] = True
    seen = report("champion", S, seen)
    print("   OK" if all(t in seen for t in POST) else "   FAIL", f"the post-game opens {[t for t in POST if t not in seen]}")
    for f, t in (("orre_rocket_done", "MARINE_CAVE"), ("orre_mewtwo_fled", "ORRE_NEW_ISLAND")):
        print("   FAIL" if t in seen else "   OK", f"{t} waits for {f}")
        story.story_flags[f] = True
        seen = report(f, S, seen)
        print("   OK" if t in seen else "   FAIL", f"{t} opens after {f}")
    SIDE = {"xd_spot_oasis": "OASIS_POKE_SPOT", "xd_spot_cave": "CAVE_POKE_SPOT", "xd_scooter_sand": "SS_LIBRA"}
    print("   FAIL" if any(t in seen for f, t in SIDE.items() if not story.story_flags.get(f)) else "   OK",
          "the side places wait for their own story points (the Poke Spots, the scooter)")
    story.story_flags.update({f: True for f in SIDE})
    seen = report("side places", S, seen)
    print("   OK" if all(t in seen for t in SIDE.values()) else "   FAIL", f"...and open after them {[t for t in SIDE.values() if t not in seen]}")
    ALL = [k for k, a in PROG.items() if isinstance(a, dict) and a.get("region") == "ORRE"]
    missing = [k for k in ALL if k not in seen]
    print("   OK" if not missing else "   FAIL", f"every Orre area reachable: {missing}")


walkthrough("menu buttons")
links = walked_links
walkthrough("R1: the same story, walking only (map exits, doors, the bike)")
