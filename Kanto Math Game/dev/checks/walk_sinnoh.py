
story.badges = {"SINNOH": []}
story.inventory = {}
story.story_flags = {"visited_TWINLEAF_TOWN": True}
story.defeated_trainers = {}
story.starting_region = "SINNOH"
R, S = "SINNOH", "TWINLEAF_TOWN"
seen = report("start", S, set())
steps = [
    ("met Roark", {"met_roark": True}, None),
    ("COAL", {}, "COAL"),
    ("Windworks", {"windworks_cleared": True}, None),
    ("FOREST", {}, "FOREST"),
    ("Galactic Eterna", {"galactic_eterna_cleared": True}, None),
    ("COBBLE (Maylene)", {}, "COBBLE"),
    ("FEN (Wake)", {}, "FEN"),
    ("RELIC (Fantina, 4+ badges)", {}, "RELIC"),
    ("Iron Island", {"visited_IRON_ISLAND": True}, None),
    ("MINE (Byron)", {}, "MINE"),
    ("ICICLE (Candice)", {}, "ICICLE"),
    ("Galactic HQ", {"galactic_hq_cleared": True}, None),
    ("Spear Pillar", {"spear_pillar_resolved": True, "SPEAR_PILLAR_boss_defeated": True}, None),
    ("BEACON (Volkner)", {}, "BEACON"),
    ("champion", {"beat_sinnoh_champion": True}, None),
]
for title, flags, b in steps:
    story.story_flags.update(flags)
    if b:
        badge(R, b)
    seen = report(title, S, seen)
print("HMs:", sorted(k for k in story.inventory if k.startswith("HM_")))
