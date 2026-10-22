
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
