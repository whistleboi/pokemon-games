"""An area whose Gym changes with the story (Orre's Realgam Tower, story rework S5 11-24: Evice's run in Part 1, the Orre
League in Part 2). The area's data names the other Gym and when it takes over:

    "gym_when": [{"flags": ["orre_part2"], "use": "gym_league"}]     (the first entry whose flags are all set wins)

apply(game) puts that Gym in the loaded area data's "gym" (the area's own is kept as "_gym_base"), so everything that reads an
area's Gym - the lobby, the League's Hall of Fame and title, the League Redo, the closed-Gym words - sees the one in force.
Called when a save is loaded (game.load_game_data) and when a story step flips it (src/world/orre_skip.py)."""


def apply(game):
    story = getattr(game, "story_manager", None)
    prog = game.loader.area_data.get("STORY_PROGRESSION", {}) if getattr(game, "loader", None) else {}
    flags = story.story_flags if story is not None else {}
    for area in prog.values():
        if not isinstance(area, dict) or not area.get("gym_when"):
            continue
        if "_gym_base" not in area:
            area["_gym_base"] = area.get("gym")
        gym = area["_gym_base"]
        for rule in area["gym_when"]:
            if all(flags.get(f) for f in rule.get("flags") or []) and area.get(rule.get("use")):
                gym = area[rule["use"]]
                break
        area["gym"] = gym
