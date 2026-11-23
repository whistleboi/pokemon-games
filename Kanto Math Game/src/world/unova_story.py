"""Unova's own story conditions (11-23, batch 4a), through main's region hook: "world:unova_story:<arg>".

- "female_player" / "male_player": Black 2 / White 2 change some people by the player's character (Nimbasa's Subway
  partner is Rosa for a boy and Nate for a girl; the Ferris wheel's trainer). Our characters, by look."""

FEMALE = {"rosa", "hilda", "dawn", "leaf", "female", "may", "girls", "lyra", "kris", "serena", "selene", "gloria",
          "juliana", "lillie"}


def female(story):
    game = getattr(story, "game", None)
    return str(getattr(game, "player_character", "") or "").lower() in FEMALE


def condition(story, arg):
    if arg == "female_player":
        return female(story)
    if arg == "male_player":
        return not female(story)
    return False


def event(state, ev, lines, show):
    show(lines or ["..."])
