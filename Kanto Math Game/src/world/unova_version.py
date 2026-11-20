"""Unova follows Black 2 or White 2, chosen when the region starts (story flag `unova_version`; Jordan 11-20: "I want the
version selection at the start of the region like in Hoenn so we should be building with that in mind").

Built once for both versions, like Hoenn (src/world/hoenn.py):
- text uses tokens: {legend} (Zekrom / Reshiram), {other_legend}, {kyurem} (Black / White Kyurem), {version},
  {city} (Black City / White Forest), filled by common._fill_names;
- conditions take "unova_version:BLACK_2" / "unova_version:WHITE_2" (story.special_condition): version-only people,
  items, trainers and places;
- the version changes the STORY only (Jordan 11-20): never the wild Pokemon (both versions' are in one table:
  dev/builders/unova_wild.py merged()), and every species stays catchable in one playthrough, post-game included: the
  version's legend in the story's place, the other version's legend in a place of its own (a White 2 player who catches
  Reshiram still finds Zekrom; Black Kyurem / White Kyurem likewise), set with the legend batches.
Before a choice is made the text stays neutral.
"""

VERSIONS = {
    "BLACK_2": {"key": "BLACK_2", "title": "BLACK 2", "legend": "Zekrom", "legend_id": 644, "other_legend": "Reshiram",
                "other_legend_id": 643, "kyurem": "Black Kyurem", "city": "Black City", "other_city": "White Forest",
                "color": (40, 40, 48), "accent": (230, 60, 60)},
    "WHITE_2": {"key": "WHITE_2", "title": "WHITE 2", "legend": "Reshiram", "legend_id": 643, "other_legend": "Zekrom",
                "other_legend_id": 644, "kyurem": "White Kyurem", "city": "White Forest", "other_city": "Black City",
                "color": (232, 232, 236), "accent": (70, 140, 230)},
}
NEUTRAL = {"legend": "the legendary dragon", "other_legend": "the other legendary dragon", "kyurem": "Kyurem",
           "version": "Unova", "city": "Black City or White Forest", "other_city": "White Forest or Black City"}
TOKENS = ("other_legend", "legend", "kyurem", "version", "other_city", "city")


def version(story):
    return (story.story_flags or {}).get("unova_version")


def info(story):
    return VERSIONS.get(version(story))


def needs_choice(story):
    return story.get_current_region() == "UNOVA" and not version(story)


def words(story):
    v = info(story)
    if not v:
        return dict(NEUTRAL)
    return {"legend": v["legend"], "other_legend": v["other_legend"], "kyurem": v["kyurem"], "version": v["title"].title(),
            "city": v["city"], "other_city": v["other_city"]}


def fill(story, text):
    if not isinstance(text, str) or "{" not in text:
        return text
    w = words(story)
    for t in TOKENS:
        text = text.replace("{" + t + "}", w[t])
    return text


def current(game=None):
    """The version being played, from the running game (for code that has no story at hand: the wild tables)."""
    if game is None:
        from src.ui import theme
        game = getattr(theme, "GAME", None)
    story = getattr(game, "story_manager", None)
    return version(story) if story is not None else None
