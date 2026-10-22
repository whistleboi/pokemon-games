
story.badges = {"UNOVA": []}
story.inventory = {}
story.story_flags = {"visited_NUVEMA_TOWN": True}
story.defeated_trainers = {}
story.starting_region = "UNOVA"
R, S = "UNOVA", "NUVEMA_TOWN"
seen = report("start", S, set())
steps = [("TRIO", {}, "TRIO"), ("BASIC", {}, "BASIC"), ("Castelia sewers", {"plasma_castelia_cleared": True}, None),
         ("INSECT", {}, "INSECT"), ("BOLT", {}, "BOLT"), ("Relic Castle", {"plasma_relic_castle_cleared": True}, None),
         ("QUAKE", {}, "QUAKE"), ("JET", {}, "JET"), ("Dragonspiral", {"plasma_dragonspiral_cleared": True}, None),
         ("FREEZE", {}, "FREEZE"), ("LEGEND", {}, "LEGEND"), ("champion", {"beat_unova_champion": True}, None)]
for title, flags, b in steps:
    story.story_flags.update(flags)
    if b:
        badge(R, b)
    seen = report(title, S, seen)
print("HMs:", sorted(k for k in story.inventory if k.startswith("HM_")))
