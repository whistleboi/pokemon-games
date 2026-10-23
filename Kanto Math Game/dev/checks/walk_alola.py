
story.badges = {"ALOLA": []}
story.inventory = {}
story.story_flags = {"visited_IKI_TOWN": True}
story.defeated_trainers = {}
story.starting_region = "ALOLA"
R, S = "ALOLA", "IKI_TOWN"
seen = report("start", S, set())
steps = [("Verdant Cavern", {"VERDANT_CAVERN_boss_defeated": True}, None), ("NORMALIUM (Ilima)", {}, "NORMALIUM_Z"),
         ("Akala trials", {"BROOKLET_HILL_boss_defeated": True, "LUSH_JUNGLE_boss_defeated": True,
                           "WELA_VOLCANO_boss_defeated": True}, None),
         ("ROCKIUM (Olivia)", {}, "ROCKIUM_Z"),
         ("Ula'ula trials + Po Town", {"MT_HOKULANI_boss_defeated": True, "THRIFTY_MEGAMART_boss_defeated": True,
                                     "po_town_cleared": True}, None),
         ("DARKINIUM (Nanu)", {}, "DARKINIUM_Z"), ("Vast Poni", {"VAST_PONI_boss_defeated": True}, None),
         ("GROUNDIUM (Hapu)", {}, "GROUNDIUM_Z"), ("champion", {"beat_alola_champion": True}, None)]
for title, flags, b in steps:
    story.story_flags.update(flags)
    if b:
        badge(R, b)
    seen = report(title, S, seen)

# ---- areas expansion (areas_04_alola.patch)
story.badges = {"ALOLA": []}
story.story_flags = {"visited_IKI_TOWN": True}
MELE = ["ALOLA_ROUTE_3", "MELEMELE_MEADOW", "SEAWARD_CAVE", "KALAE_BAY", "HAUOLI_CEMETERY", "BIG_WAVE_BEACH", "SANDY_CAVE"]
AKALA = ["PANIOLA_TOWN", "PANIOLA_RANCH", "ALOLA_ROUTE_6", "ROYAL_AVENUE", "HANO_GRAND_RESORT", "HANO_BEACH", "HEAHEA_BEACH",
         "ALOLA_ROUTE_9", "AKALA_OUTSKIRTS", "DIVIDING_PEAK_TUNNEL"]
ULA = ["MALIE_GARDEN", "ALOLA_ROUTE_12", "SECLUDED_SHORE", "ULAULA_BEACH", "BLUSH_MOUNTAIN", "ALOLA_ROUTE_13", "HAINA_DESERT",
       "HOKULANI_OBSERVATORY", "AETHER_HOUSE", "ULAULA_MEADOW"]
PONI = ["EXEGGUTOR_ISLAND", "PONI_WILDS", "ANCIENT_PONI_PATH", "PONI_BREAKER_COAST"]
POST = ["PONI_GROVE", "PONI_PLAINS", "PONI_MEADOW", "PONI_COAST", "PONI_GAUNTLET", "RESOLUTION_CAVE", "BATTLE_TREE", "ROCKET_CASTLE",
        "ULTRA_DEEP_SEA", "ULTRA_JUNGLE", "ULTRA_DESERT", "ULTRA_PLANT", "ULTRA_CRATER", "ULTRA_FOREST", "ULTRA_RUIN"]
story.story_flags.update({"VERDANT_CAVERN_boss_defeated": True})
badge(R, "NORMALIUM_Z")
expansion_check("melemele+akala expansion", MELE + AKALA, S)
gate_check("ula'ula expansion", ULA, S, "ROCKIUM_Z")
story.story_flags.update({"BROOKLET_HILL_boss_defeated": True, "LUSH_JUNGLE_boss_defeated": True, "WELA_VOLCANO_boss_defeated": True})
badge(R, "ROCKIUM_Z")
expansion_check("ula'ula expansion", ULA, S)
story.story_flags.update({"MT_HOKULANI_boss_defeated": True, "THRIFTY_MEGAMART_boss_defeated": True, "po_town_cleared": True})
badge(R, "DARKINIUM_Z")
expansion_check("poni expansion", PONI, S)
gate_check("alola post-game", POST, S, "beat_alola_champion")
story.story_flags.update({"VAST_PONI_boss_defeated": True, "beat_alola_champion": True})
badge(R, "GROUNDIUM_Z")
expansion_check("alola post-game expansion", POST, S)
