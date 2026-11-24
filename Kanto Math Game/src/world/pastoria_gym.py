"""Pastoria Gym's water (Sinnoh S4, 11-24; Platinum's: pret pokeplatinum gym_features.c, PastoriaGym_*).

Three kinds of button set the water's height: orange low, green middle, blue high. It starts in the middle (the way in
from the door crosses middle ground; Platinum's saved button starts at 0, the green one). Some walkway tiles
are high ground, middle ground or low ground (Platinum's tile behaviours): high ground is walkable only with the water low,
middle ground with it in the middle, low ground with it high (PastoriaGym_DynamicMapFeaturesCheckCollision); every other
tile as the room's walk grid has it.
Map side (kanto_handoff/sinnoh_map_tools/s_s4_pastoria_gym.py): those tiles are the room's "barred" (unseen) blockers,
each gone while "world:pastoria_gym:is:<level>" holds; a button is an "every" scene on its tile, condition
"world:pastoria_gym:not:<level>", event {"world": "pastoria_gym", "press": <level>}. Story flag pastoria_gym_water."""
FLAG = "pastoria_gym_water"
LEVELS = ("low", "mid", "high")
SAY = {"low": "The water level dropped!", "mid": "The water level changed!", "high": "The water level rose!"}


def level(story):
    v = story.story_flags.get(FLAG)
    return v if v in LEVELS else "mid"


def condition(story, arg):
    what, _, lv = str(arg).partition(":")
    if what == "is":
        return level(story) == lv
    if what == "not":
        return level(story) != lv
    return False


def _reopen(state):
    if hasattr(state, "_bar_list") and hasattr(state, "_bar_met"):
        state.barred = {tuple(t): bar for bar in state._bar_list if not state._bar_met(bar) and state._bar_here(bar) for t in bar.get("tiles", [])}
        if hasattr(state, "_rot_bars"):
            state.barred.update(state._rot_bars())
    if hasattr(state, "_refresh_picture"):
        state._refresh_picture()


def event(state, ev, lines, show):
    lv = ev.get("press")
    if lv not in LEVELS:
        return
    story = state.game.story_manager
    if level(story) == lv:
        return
    story.story_flags[FLAG] = lv
    _reopen(state)
    show(["You pressed the button.", SAY[lv]])
