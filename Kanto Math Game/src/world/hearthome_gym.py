"""Hearthome Gym's doors (Sinnoh S3, Jordan 11-23: "Platinum's rooms, the door questions from our maths engine").

Platinum (pret pokeplatinum src/overlay008/gym_features.c, HearthomeGym_*): two dark trainer rooms, the first with 3 doors
(circle, square, triangle), the second with 5 (sun, donut, moon, star, heart); one door is right, picked at random, and its
clue is a glowing tile; every other door's warp goes back to the lobby. Diamond and Pearl asked a sum instead.
Here: as you come into a trainer room, a question from our maths engine (the player's own maths level, one level harder in
the second room), its answers named by the room's doors. Answer, and you have chosen your door: the right answer opens that
door (the way on), a wrong one takes you through it... and back to the lobby, as in Platinum.

Map side (kanto_handoff/sinnoh_map_tools/s_s3_hearthome_gym.py): each trainer room has an "enter" scene, every time,
cast [] with "event" {"world": "hearthome_gym", "room": 1 or 2}; each door is barred until
"world:hearthome_gym:<room>:<door>" (the door just opened). Story flag: "hearthome_gym_door_<room>" = the open door, or None."""
DOORS = {1: ["Circle", "Square", "Triangle"], 2: ["Sun", "Donut", "Moon", "Star", "Heart"]}
LOBBY = "gym"
LAST = {}   # (the question just asked: {"room", "right": the right door} - for the checks)


def _flag(room):
    return f"hearthome_gym_door_{room}"


def condition(story, arg):
    """"<room>:<door>": that door is the one open now."""
    room, _, door = str(arg).partition(":")
    try:
        return story.story_flags.get(_flag(int(room))) == int(door)
    except ValueError:
        return False


def _reopen(state):
    """The room's doors as the flag now says (walk_town re-reads its blockers only every 20 frames)."""
    if hasattr(state, "_bar_list") and hasattr(state, "_bar_met"):
        state.barred = {tuple(t): bar for bar in state._bar_list if not state._bar_met(bar) and state._bar_here(bar) for t in bar.get("tiles", [])}
        if hasattr(state, "_rot_bars"):
            state.barred.update(state._rot_bars())


def question(game, room):
    """(problem, right answer, [an answer per door]) from the maths engine, at the player's level (+1 in the second room)."""
    story = game.story_manager
    n = len(DOORS[room])
    level = game.math.clamp_level(int(story.get_math_level()) + (room - 1))
    for _ in range(20):
        problem, ans, options = game.math.generate(level, num_options=n)
        if len(options) == n and len({str(o) for o in options}) == n and ans in options:
            return problem, ans, list(options)
    options = [ans] + [o for o in options if o != ans]   # (a format with fewer answers than doors: the rest stay shut)
    return problem, ans, options[:n]


def event(state, ev, lines, show):
    from src.states.systems.pick_list import PickListState
    game = state.game
    story = game.story_manager
    room = int(ev.get("room", 1))
    story.story_flags[_flag(room)] = None   # (every door shut again as you come in)
    _reopen(state)
    problem, ans, options = question(game, room)
    doors = DOORS[room]
    LAST.clear(); LAST.update(room=room, right=options.index(ans) if ans in options else None, problem=problem)
    pick = [(f"{doors[i]} door:  {o}", i) for i, o in enumerate(options)]
    intro = ["A voice echoes through the dark...",
             f"\"Solve this, and walk through the door that holds the answer: {problem}\""]

    def chose(i):
        if i is None:
            show(["You stay where you are. (Leave the room and come back in to hear the question again.)"])
            return
        if options[i] == ans:
            story.story_flags[_flag(room)] = i
            _reopen(state)
            show([f"The {doors[i]} door creaks open. That's the way on!"])
            return
        wrong = [f"You step through the {doors[i]} door into the dark...",
                 "...and find yourself back at the Gym's entrance! That wasn't the right answer."]
        if hasattr(state, "_go"):
            state._go(LOBBY, "ROOM:gym_1")   # (out at the lobby's door: Platinum's lobby warp 1)
        show(wrong)

    def ask():
        game.change_state(PickListState(game, state, problem, pick, chose))
    say = getattr(state, "show_message", None)
    if say:
        say(intro, callback=ask)
    else:
        ask()
