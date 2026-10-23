
story.badges = {"GALAR": []}
story.inventory = {}
story.story_flags = {"visited_POSTWICK": True}
story.defeated_trainers = {}
story.starting_region = "GALAR"
R, S = "GALAR", "POSTWICK"
seen = report("start", S, set())
for b in ["GRASS", "WATER", "FIRE", "FIGHTING", "FAIRY", "ROCK", "DARK", "DRAGON"]:
    badge(R, b)
    seen = report(b, S, seen)

# ---- Galar small spots (areas_12_galar.patch)
story.badges = {"GALAR": []}
seen = report("galar spots: no badges", S, set())
print("   FAIL" if "MOTOSTOKE_OUTSKIRTS" in seen else "   OK", "Motostoke Outskirts needs the Grass badge")
badge(R, "GRASS")
expansion_check("galar small spots", ["MOTOSTOKE_OUTSKIRTS", "GALAR_MINE_NO_2", "MEETUP_SPOT"], S)
print("   OK" if "HULBURY" in links("GALAR_MINE_NO_2") and "GALAR_MINE_NO_2" in links("HULBURY") else "   FAIL", "Mine No. 2 <-> Hulbury")
