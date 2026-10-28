story.badges = {"ORANGE": []}
story.inventory = {}
story.story_flags = {"visited_VALENCIA_ISLAND": True}
story.defeated_trainers = {}
story.starting_region = "ORANGE"
R, S = "ORANGE", "VALENCIA_ISLAND"
seen = report("start (no partner yet)", S, set())
print("   FAIL" if "ORANGE_ROUTE_49" in seen else "   OK", "Route 49 waits for Professor Ivy's partner")
story.story_flags["received_starter_orange"] = True
seen = report("partner", S, seen)
BADGE_AREAS = {"CORAL_EYE": "ORANGE_ROUTE_53", "SEA_RUBY": "ORANGE_ROUTE_59", "SPIKE_SHELL": "ORANGE_ROUTE_57_NORTH",
               "JADE_STAR": "ORANGE_ROUTE_67"}
for b in ["CORAL_EYE", "SEA_RUBY", "SPIKE_SHELL", "JADE_STAR"]:
    print("   FAIL" if BADGE_AREAS[b] in seen else "   OK", f"{BADGE_AREAS[b]} waits for the {b} badge")
    badge(R, b)
    seen = report(b, S, seen)
    print("   OK" if BADGE_AREAS[b] in seen else "   FAIL", f"{BADGE_AREAS[b]} opens with the {b} badge")
POST = ["ORANGE_ROUTE_70", "TARROCO_ISLAND", "HAMLIN_ISLAND", "SHAMOUTI_ISLAND"]
gate_check("orange post-game", POST, S, "beat_orange_champion")
story.story_flags["beat_orange_champion"] = True
seen = report("champion", S, seen)
ALL = [k for k, a in PROG.items() if isinstance(a, dict) and a.get("region") == "ORANGE"]
missing = [k for k in ALL if k not in seen and k not in ("FIRE_ISLAND", "ICE_ISLAND", "LIGHTNING_ISLAND", "SHAMOUTI_SHRINE")]
print("   OK" if not missing else "   FAIL", f"every Orange area reachable: {missing}")
