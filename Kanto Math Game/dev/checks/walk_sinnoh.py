
story.badges = {"SINNOH": []}
story.inventory = {}
story.story_flags = {"visited_TWINLEAF_TOWN": True, "received_starter_sinnoh": True,  # past Lake Verity
                     "received_pokedex_sinnoh": True}
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

# ---- areas expansion (areas_01_sinnoh.patch)
SINNOH_NEW = ["SINNOH_ROUTE_219", "SINNOH_ROUTE_220", "SINNOH_ROUTE_221", "FIGHT_AREA", "SINNOH_ROUTE_225", "SURVIVAL_AREA",
              "SINNOH_ROUTE_226", "SINNOH_ROUTE_227", "SINNOH_ROUTE_228", "SINNOH_ROUTE_229", "RESORT_AREA", "SINNOH_ROUTE_230",
              "SINNOH_ROUTE_224", "SINNOH_BATTLE_FRONTIER", "DISTORTION_WORLD", "WAYWARD_CAVE", "LOST_TOWER", "FLOAROMA_MEADOW",
              "FUEGO_IRONWORKS", "RAVAGED_PATH", "MANIAC_TUNNEL", "TROPHY_GARDEN", "ACUITY_LAKEFRONT", "VALOR_LAKEFRONT",
              "VERITY_LAKEFRONT", "SENDOFF_SPRING", "OREBURGH_GATE", "ETERNA_GALACTIC_BUILDING", "GALACTIC_WAREHOUSE", "GRAND_UNDERGROUND"]
story.inventory["STORAGE_KEY"] = 1  # the grunt outside the Galactic building drops it (BDSP)
expansion_check("sinnoh expansion", SINNOH_NEW, S)
gate_check("battle zone gate", ["FIGHT_AREA", "SINNOH_ROUTE_224", "SINNOH_ROUTE_227", "STARK_MOUNTAIN", "SINNOH_BATTLE_FRONTIER", "TROPHY_GARDEN", "SENDOFF_SPRING"], S, "beat_sinnoh_champion")
gate_check("distortion world gate", ["DISTORTION_WORLD"], S, "spear_pillar_resolved")
