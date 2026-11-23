# Orre's walked maps add ways with no menu button, each behind its own gate on the map (11-23): the Pyrite Building behind
# the Cipher Peons (till the Pyrite Badge), its lift down to The Under (the Subway Key, after Dakim).
_menu_links = links
WALK_GATES = {("PYRITE_TOWN", "PYRITE_BUILDING"): lambda: "PYRITE" in story.badges.get("ORRE", []),
              ("PYRITE_BUILDING", "THE_UNDER"): lambda: story.inventory.get("SUBWAY_KEY", 0) > 0}


def links(area):
    out = [t for t in _menu_links(area) if WALK_GATES.get((area, t), lambda: True)()]
    return out + [t for (a, t), ok in WALK_GATES.items() if a == area and t not in out and ok()]


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
