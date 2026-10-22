
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
