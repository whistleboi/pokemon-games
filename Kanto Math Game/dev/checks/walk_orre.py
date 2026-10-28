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
         ("PYRITE badge", {}, "PYRITE", "PYRITE_CAVE"),
         ("Miror B. at Pyrite Cave", {"orre_miror_cave": True}, None, "AGATE_VILLAGE"),
         ("Dakim at Mt. Battle", {"orre_dakim_mt_battle": True}, None, "THE_UNDER"),
         ("UNDER badge", {}, "UNDER", "SHADOW_PKMN_LAB"),
         ("Ein's lab", {"orre_ein_lab": True}, None, "GATEON_PORT"),
         ("Lovrina", {"xd_lovrina_beaten": True}, None, "XD_ONBS"),
         ("Exol", {"xd_exol_beaten": True}, None, "PRESTIGE_PRECEPT_CENTER"),
         ("PHENAC badge", {}, "PHENAC", "SNAGEM_HIDEOUT"),
         ("Gonzap", {"beat_gonzap": True}, None, "ORRE_COLOSSEUM"),
         ("ORRE badge", {}, "ORRE", "XD_CIPHER_KEY_LAIR"),
         ("Gorigan", {"xd_gorigan_beaten": True}, None, "REALGAM_TOWER")]
for title, flags, b, opens in STEPS:
    print("   FAIL" if opens in seen else "   OK", f"{opens} waits for {title}")
    story.story_flags.update(flags)
    if b:
        badge(R, b)
    seen = report(title, S, seen)
    print("   OK" if opens in seen else "   FAIL", f"{opens} opens after {title}")
gate_check("orre post-game", ["XD_CITADARK_ISLE", "DEEP_COLOSSEUM"], S, "beat_orre_champion")
story.story_flags["beat_orre_champion"] = True
seen = report("champion", S, seen)
ALL = [k for k, a in PROG.items() if isinstance(a, dict) and a.get("region") == "ORRE"]
missing = [k for k in ALL if k not in seen]
print("   OK" if not missing else "   FAIL", f"every Orre area reachable: {missing}")
