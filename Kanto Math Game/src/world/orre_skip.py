"""Orre's mid-story time skip (story rework S1, Jordan 11-24; kanto_handoff/orre_check/STORY_REWORK.md).

One journey in two parts: Colosseum's story ends with Evice beaten on Realgam's roof (after badge 4), and "five years later"
XD's story begins at the Pokemon HQ Lab. A region hook: Realgam's won scene runs {"world": "orre_skip"} (orre_story.py).

Flags: orre_evice_beaten (the battle's own victory flag), orre_part2 (the skip has happened: XD's places and people, and
Colosseum's after-game content as Part 2 side content, open on it). The title and the Hall of Fame wait for the League
after badge 8 (S5)."""
PART2 = "orre_part2"
START = "POKEMON_HQ_LAB"      # (XD's story starts here: Krane carried off, KIDNAP_SCENE in orre_story.py)
CAME_FROM = "PHENAC_CITY"     # (you arrive as if by the bike from Phenac)

LINES = [
    "Evice is led away by the authorities. Without its leader, Cipher falls apart.",
    "Rui: We did it... Orre's Shadow Pokemon can all be saved now. Grandpa will want to hear everything!",
    "Rui: I'm going home to Agate to help him at the Relic Stone. Come and see us, {player_name}. Promise?",
    "...",
    "FIVE YEARS LATER",
    "Orre has grown quiet. Phenac has a new mayor, the kids of the Under run a TV station in Pyrite, and Realgam Tower's lights are dark.",
    "But a message has arrived on your P*DA, from Professor Krane at the Pokemon HQ Lab: \"Please come at once.\"",
]


def condition(story, arg):
    if arg == "part2":
        return bool(story.story_flags.get(PART2))
    if arg == "part1":
        return not story.story_flags.get(PART2)
    return False


def event(state, ev, lines, show):
    """Evice beaten: close the tournament run, say goodbye, skip five years, and arrive at the HQ Lab."""
    game = state.game
    story = game.story_manager
    from src.world import orre_tournament
    area = story.current_area_key
    story.story_flags.pop(orre_tournament.RUN.format(area), None)
    story.story_flags.pop(orre_tournament.FIGHT.format(area), None)
    if story.story_flags.get(PART2):
        return show(lines) if lines else None
    story.story_flags[PART2] = True
    from src.world import gym_swaps   # (Realgam's Colosseum: the League from now on - S5)
    gym_swaps.apply(game)
    from src.states.overworld.common import _say_then, _fill_names
    say = [_fill_names(game, x) for x in (list(lines or []) + LINES)]
    _say_then(state, say, lambda: _arrive(state))


def _arrive(state):
    from src.states.overworld import CityState
    game = state.game
    story = game.story_manager
    story.current_area_key, story.last_area_key = START, CAME_FROM
    game.walk_town_room = None
    game.walk_town_pos = None
    game.walk_town_exit = None
    try:
        game.update_save_data()
        game.data.save()
    except Exception as e:   # (never block the skip on a save error)
        print("Orre time skip: save failed:", e)
    game.change_state(CityState(game))
