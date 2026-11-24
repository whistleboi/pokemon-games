
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
    ("COAL", {"got_hm_rock_smash_oreburgh_gate": True}, "COAL"),   # (the Oreburgh Gate hiker's Rock Smash, after the badge)
    ("Windworks", {"windworks_cleared": True}, None),
    ("FOREST", {"received_hm_cut": True}, "FOREST"),   # (Cynthia's Cut, after the badge)
    ("Galactic Eterna", {"galactic_eterna_cleared": True}, None),
    ("COBBLE (Maylene)", {}, "COBBLE"),
    ("Galactic Warehouse (Dawn's tag battle, Looker)", {"sinnoh_dawn_warehouse_call": True, "sinnoh_warehouse_guards_beaten": True,
                                                       "galactic_warehouse_cleared": True}, None),   # (Platinum, S4 11-24)
    ("FEN (Wake)", {"got_hm_defog_solaceon_ruins_d07r0116_6_7": True}, "FEN"),   # (Defog lies in the Solaceon Ruins)
    ("Pastoria's bomb, the chase, Cynthia's SecretPotion", {"sinnoh_pastoria_bomb_warned": True, "sinnoh_pastoria_bomb": True,
                                                           "sinnoh_valor_grunt_beaten": True, "sinnoh_secretpotion": True}, None),
    ("Celestic: the Old Charm, Surf from the Elder", {"got_old_charm_r210": True, "sinnoh_celestic_grunt_beaten": True,
                                                       "delivered_old_charm": True, "got_hm_surf_celestic": True}, None),   # (Platinum, S4 11-24)
    ("RELIC (Fantina, 4+ badges)", {}, "RELIC"),
    ("Iron Island", {"visited_IRON_ISLAND": True, "got_hm_strength_iron_island": True}, None),   # (Riley's Strength, Jordan 11-24)
    ("MINE (Byron)", {}, "MINE"),
    ("ICICLE (Candice)", {"got_hm_rock_climb_sinnoh_route_217_r217_8_49": True}, "ICICLE"),   # (Rock Climb: Route 217's ball)
    ("Galactic HQ", {"galactic_hq_cleared": True}, None),
    ("Spear Pillar", {"spear_pillar_resolved": True, "SPEAR_PILLAR_boss_defeated": True}, None),
    ("BEACON (Volkner)", {}, "BEACON"),
    ("champion", {"beat_sinnoh_champion": True}, None),
]
for title, flags, b in steps:
    story.story_flags.update(flags)
    if flags.get("got_hm_surf_celestic"):
        story.inventory["HM_SURF"] = 1   # (the Elder's gift, not a badge's)
    for _f, _hm in (("got_hm_rock_smash_oreburgh_gate", "HM_ROCK_SMASH"), ("received_hm_cut", "HM_CUT"),
                    ("got_hm_defog_solaceon_ruins_d07r0116_6_7", "HM_DEFOG"), ("got_hm_rock_climb_sinnoh_route_217_r217_8_49", "HM_ROCK_CLIMB")):   # (Platinum's givers, not the badges: 11-24 cleanup)
        if flags.get(_f):
            story.inventory[_hm] = 1
    if flags.get("got_hm_strength_iron_island"):
        story.inventory["HM_STRENGTH"] = 1   # (Riley's gift on Iron Island, not the Mine Badge's)
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
story.inventory["STORAGE_KEY"] = 1  # (the Underpass door's key: S5, from Looker after Lake Acuity)
expansion_check("sinnoh expansion", SINNOH_NEW, S)
gate_check("battle zone gate", ["FIGHT_AREA", "SINNOH_ROUTE_224", "SINNOH_ROUTE_227", "STARK_MOUNTAIN", "SINNOH_BATTLE_FRONTIER"], S, "beat_sinnoh_champion")
# (11-13: Sinnoh follows Platinum now: the Trophy Garden (Route 212) and Sendoff Spring (out of the Distortion World) are open before the League)
gate_check("distortion world gate", ["DISTORTION_WORLD"], S, "spear_pillar_resolved")
