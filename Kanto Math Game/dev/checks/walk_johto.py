
story.badges = {"JOHTO": []}
story.inventory = {}
story.story_flags = {"visited_NEW_BARK_TOWN": True}
story.defeated_trainers = {}
R = "JOHTO"
S = "NEW_BARK_TOWN"
seen = report("start", S, set())
story.story_flags["defeated_elder_li"] = True
seen = report("Elder Li beaten (Falkner open?)", S, seen)
badge(R, "ZEPHYR")
seen = report("ZEPHYR (+Flash)", S, seen)
clear_area("SLOWPOKE_WELL")
seen = report("Slowpoke Well cleared (Bugsy?)", S, seen)
badge(R, "HIVE")
story.inventory["OLD_ROD"] = 1
seen = report("HIVE (+Cut)", S, seen)
badge(R, "PLAIN")
story.inventory["SQUIRT_BOTTLE"] = 1
seen = report("PLAIN (+Strength, SquirtBottle)", S, seen)
story.story_flags["defeated_sudowoodo"] = True
seen = report("Sudowoodo", S, seen)
story.story_flags["defeated_rival_burned_tower"] = True
seen = report("Burned Tower rival (Morty?)", S, seen)
badge(R, "FOG")
seen = report("FOG (+Surf)", S, seen)
badge(R, "STORMBADGE")
story.story_flags["ampharos_cured"] = True
seen = report("STORM + Amphy cured (Jasmine?)", S, seen)
badge(R, "MINERAL")
story.story_flags["defeated_red_gyarados"] = True
seen = report("MINERAL + Red Gyarados (Rocket HQ?)", S, seen)
story.story_flags["rocket_hq_cleared"] = True
seen = report("Rocket HQ cleared (Pryce?)", S, seen)
badge(R, "GLACIER")
story.story_flags["radio_tower_cleared"] = True
seen = report("GLACIER + Radio Tower (Route 44?)", S, seen)
badge(R, "RISING")
seen = report("RISING (League?)", S, seen)
story.story_flags["beat_johto_champion"] = True
seen = report("Johto Champion", S, seen)
for b in ["BOULDER", "CASCADE", "THUNDER", "RAINBOW", "SOUL", "MARSH", "VOLCANO", "EARTH"]:
    badge("KANTO", b)
seen = report("+ 8 Kanto badges (Mt. Silver?)", S, seen)
print("HMs:", sorted(k for k in story.inventory if k.startswith("HM_")))
