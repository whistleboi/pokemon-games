"""Professor Oak's Lab, FireRed's way (11-23, Kanto K4): once you and your rival have each taken a Poke Ball, the third
stays on the table - Professor Oak's last Pokemon. Its spot on the table shows it through the condition
"world:kanto_lab:last:<species id>" (the Lab's people in k_batch1: one per ball).
"world:kanto_lab:not_mine:<species id>": that starter isn't yours (Yellow's three starter gifts, k_batch5 / k_batch6)."""

STARTERS = (1, 4, 7)


def left_on_table(story):
    """The species in the ball left on the table, or None (not chosen yet, or no rival's pick to go by)."""
    if not story.story_flags.get("received_starter_kanto"):
        return None
    mine = story.story_flags.get("starter_kanto")
    if not mine and story.player_team:
        mine = getattr(story.player_team[0], "id", None)
    rival = story.rival_starter_id("KANTO", default=None)
    left = [s for s in STARTERS if s not in (_id(mine), _id(rival))]
    return left[0] if len(left) == 1 else None


def _id(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def condition(story, arg):
    what, _, val = str(arg).partition(":")
    if what == "last":
        return str(left_on_table(story)) == val
    if what == "not_mine":   # (Pokemon Yellow's starter gifts - Cerulean's Bulbasaur, Route 24's Charmander, Vermilion's Squirtle -
        return _id(val) != _id(my_starter(story))   #  only the ones that weren't your pick; Jordan 11-24)
    return False


def my_starter(story):
    """Your Kanto starter's species, or None (a run that began in another region: every gift is offered)."""
    mine = _id(story.story_flags.get("starter_kanto"))
    if mine in STARTERS:
        return mine
    if story.story_flags.get("received_starter_kanto") and story.player_team:
        first = _id(getattr(story.player_team[0], "id", None))
        return first if first in STARTERS else None
    return None
