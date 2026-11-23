"""Unova's own story conditions (11-23, batch 4a), through main's region hook: "world:unova_story:<arg>".

- "female_player" / "male_player": Black 2 / White 2 change some people by the player's character (Nimbasa's Subway
  partner is Rosa for a boy and Nate for a girl; the Ferris wheel's trainer). Our characters, by look."""

FEMALE = {"rosa", "hilda", "dawn", "leaf", "female", "may", "girls", "lyra", "kris", "serena", "selene", "gloria",
          "juliana", "lillie"}


def female(story):
    game = getattr(story, "game", None)
    return str(getattr(game, "player_character", "") or "").lower() in FEMALE


def condition(story, arg):
    """"female_player" / "male_player"; "not_today:<flag>": the flag is set, and not today (the day it was first seen
    set is kept as <flag>_day: the Ferris wheel's second visit is another day, as Black 2)."""
    if arg.startswith("not_today:"):
        import datetime
        flag = arg[10:]
        if not story.story_flags.get(flag):
            return False
        today = datetime.date.today().isoformat()
        day = story.story_flags.setdefault(flag + "_day", today)
        return day != today
    if arg == "female_player":
        return female(story)
    if arg == "male_player":
        return not female(story)
    return False


def event(state, ev, lines, show):
    """{"toggle": flag}: flip a flag (the roller coaster's switches: each press changes a car's route)."""
    if ev.get("toggle"):
        flags = state.game.story_manager.story_flags
        flags[ev["toggle"]] = not flags.get(ev["toggle"])
        if lines:
            show(lines)
        return
    show(lines or ["..."])
