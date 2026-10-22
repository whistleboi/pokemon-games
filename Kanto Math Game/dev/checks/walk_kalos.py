
story.badges = {"KALOS": []}
story.inventory = {}
story.story_flags = {"visited_VANIVILLE_TOWN": True}
story.defeated_trainers = {}
story.starting_region = "KALOS"
R, S = "KALOS", "VANIVILLE_TOWN"
seen = report("start", S, set())
steps = [("BUG", {}, "BUG"), ("Parfum Palace", {"visited_PARFUM_PALACE": True}, None), ("CLIFF", {}, "CLIFF"),
         ("RUMBLE", {}, "RUMBLE"), ("PLANT", {}, "PLANT"), ("VOLTAGE", {}, "VOLTAGE"), ("FAIRY", {}, "FAIRY"),
         ("PSYCHIC", {}, "PSYCHIC"), ("Flare stopped", {"geosenge_flare_cleared": True}, None),
         ("ICEBERG", {}, "ICEBERG"), ("champion", {"beat_kalos_champion": True}, None)]
for title, flags, b in steps:
    story.story_flags.update(flags)
    if b:
        badge(R, b)
    seen = report(title, S, seen)
print("HMs:", sorted(k for k in story.inventory if k.startswith("HM_")))
