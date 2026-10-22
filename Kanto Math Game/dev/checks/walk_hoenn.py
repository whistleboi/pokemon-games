
story.badges = {"HOENN": []}
story.inventory = {}
story.story_flags = {"visited_LITTLEROOT_TOWN": True, "hoenn_version": "OMEGA_RUBY"}
story.defeated_trainers = {}
story.starting_region = "HOENN"
R, S = "HOENN", "LITTLEROOT_TOWN"
seen = report("start", S, set())
for b, extra in [("STONE", {}), ("KNuckle", {}), ("DYNAMO", {}), ("HEAT", {}), ("BALANCE", {}),
                 ("FEATHER", {"weather_institute_cleared": True}), ("MIND", {"seafloor_cavern_cleared": True}),
                 ("RAIN", {"cave_of_origin_cleared": True})]:
    badge(R, b)
    story.story_flags.update(extra)
    seen = report(f"{b} badge", S, seen)
story.story_flags["beat_hoenn_champion"] = True
seen = report("champion", S, seen)
print("HMs:", sorted(k for k in story.inventory if k.startswith("HM_")))
