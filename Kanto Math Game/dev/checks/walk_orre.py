# Orre's walked maps add ways with no menu button, each behind its own gate on the map (11-23): the Pyrite Building behind
# the Cipher Peons (till the Pyrite Badge), its lift down to The Under (the Subway Key, after Dakim).
_menu_links = links
WALK_GATES = {("PYRITE_TOWN", "PYRITE_BUILDING"): lambda: "PYRITE" in story.badges.get("ORRE", []),
              ("PYRITE_BUILDING", "THE_UNDER"): lambda: story.inventory.get("SUBWAY_KEY", 0) > 0}


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
    # (step, flags to set, badge, an area that must open)
    STEPS = [("the Snag Machine", {"got_snag_machine": True}, None, "PYRITE_TOWN"),
             ("PYRITE badge", {}, "PYRITE", "PYRITE_BUILDING"),
             ("Doken on the Pyrite Building roof", {"orre_beat_doken": True}, None, "PYRITE_CAVE"),
             ("Miror B. at Pyrite Cave (then Fateen by the bike)", {"orre_miror_cave": True, "orre_fateen": True}, None, "AGATE_VILLAGE"),
             ("Dakim at Mt. Battle, then the Subway Key", {"orre_dakim_mt_battle": True, "_item": "SUBWAY_KEY"}, None, "THE_UNDER"),
             ("UNDER badge", {}, "UNDER", "SHADOW_PKMN_LAB"),
             ("Ein's lab", {"orre_ein_lab": True}, None, "GATEON_PORT"),
             ("Lovrina", {"xd_lovrina_beaten": True}, None, "XD_ONBS"),
             ("Exol", {"xd_exol_beaten": True}, None, "PRESTIGE_PRECEPT_CENTER"),
             ("PHENAC badge, then Hordel points out the hideout", {"xd_hordel": True}, "PHENAC", "SNAGEM_HIDEOUT"),
             ("Gonzap", {"beat_gonzap": True}, None, "ORRE_COLOSSEUM"),
             ("ORRE badge", {}, "ORRE", "XD_CIPHER_KEY_LAIR"),
             ("Gorigan", {"xd_gorigan_beaten": True}, None, "REALGAM_TOWER")]
    for title, flags, b, opens in STEPS:
        print("   FAIL" if opens in seen else "   OK", f"{opens} waits for {title}")
        if flags.get("_item"):
            story.inventory[flags["_item"]] = 1
        story.story_flags.update({k: v for k, v in flags.items() if not k.startswith("_")})
        if b:
            badge(R, b)
        seen = report(title, S, seen)
        print("   OK" if opens in seen else "   FAIL", f"{opens} opens after {title}")
    gate_check("orre post-game", ["XD_CITADARK_ISLE", "DEEP_COLOSSEUM"], S, "beat_orre_champion")
    story.story_flags["beat_orre_champion"] = True
    seen = report("champion", S, seen)
    SIDE = {"orre_power_out": "CONSTRUCTION_LOT", "met_agate_elder": "RELIC_CAVE", "xd_spot_oasis": "OASIS_POKE_SPOT",
            "xd_spot_cave": "CAVE_POKE_SPOT", "xd_machine_part_given": "XD_CIPHER_LAB", "xd_scooter_sand": "SS_LIBRA"}
    print("   FAIL" if any(t in seen for f, t in SIDE.items() if not story.story_flags.get(f)) else "   OK",
          "the side places wait for their own story points (the power cut, the elder, the Poke Spots, the machine part, the scooter)")
    story.story_flags.update({f: True for f in SIDE})
    seen = report("side places", S, seen)
    print("   OK" if all(t in seen for t in SIDE.values()) else "   FAIL", f"...and open after them {[t for t in SIDE.values() if t not in seen]}")
    ALL = [k for k, a in PROG.items() if isinstance(a, dict) and a.get("region") == "ORRE"]
    missing = [k for k in ALL if k not in seen]
    print("   OK" if not missing else "   FAIL", f"every Orre area reachable: {missing}")


walkthrough("menu buttons")
links = walked_links
walkthrough("R1: the same story, walking only (map exits, doors, the bike)")
