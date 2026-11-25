"""Sunyshore Gym's turning walkways (Sinnoh S6, 11-24; Platinum's: pret pokeplatinum gym_features.c, SunyshoreGym_*).

Three rooms (our gym, gym_2, gym_3), each with gear-shaped walkways that all turn together: one rotation state per room,
0 to 3, starting at 0 as you come into the room (Platinum's InitPersistedMapFeaturesForSunyshoreGym). Stepping onto a
gear's middle presses its button: normal (+1, a quarter turn), reverse (-1) or double (+2). In each state some of the
room's arm regions are turned away - those tiles are gaps you can't walk on (SunyshoreGym_DynamicMapFeaturesCheckCollision);
every other tile as the room's walk grid has it.
Map side (kanto_handoff/sinnoh_map_tools/s_s6_sunyshore.py): each region's tiles are the room's "barred" (unseen) blockers,
gone while "world:sunyshore_gym:open:<room>:<region>" holds; a button is an "every" scene on its tile, event {"world":
"sunyshore_gym", "press": "normal" | "reverse" | "double", "room": r}; an "enter" scene, event {"world": "sunyshore_gym",
"enter": r}. Story flag sunyshore_gym_gears: [room, state].
Looks (Jordan 11-24: "use the real game"): each room has four live 3D scenes, one per state, with Platinum's own gear props
turned to it (pexport3d.py's C08GYM010<r>_g<s>); the room's picture follows flag sunyshore_gym_r<room>_s<state> (set here,
one at a time), and a press plays the region's own screen wipe while the scene changes (src/vfx/area_changes.py)."""
FLAG = "sunyshore_gym_gears"
STEP = {"normal": 1, "reverse": -1, "double": 2}
# (Platinum's sSunyshoreCollisionLists: for each room and state, the regions turned away)
BLOCKED = [
    [[1, 2, 4, 5, 10, 11], [0, 1, 5, 6, 9, 10], [0, 3, 6, 7, 8, 9], [2, 3, 4, 7, 8, 11]],
    [[1, 2, 4, 5, 7, 8, 9, 10, 11, 12, 15], [0, 1, 4, 5, 6, 11, 12, 13, 14, 0, 0],
     [0, 3, 5, 6, 7, 8, 9, 10, 12, 13, 17], [2, 3, 4, 6, 7, 10, 11, 13, 16, 2, 2]],
    [[2, 6, 7, 11, 14, 15, 17, 21, 25, 28, 29, 31, 38, 39], [1, 4, 7, 10, 12, 15, 16, 20, 22, 26, 29, 30, 34, 35],
     [0, 4, 5, 9, 13, 16, 19, 23, 25, 27, 30, 33, 36, 39], [3, 5, 6, 8, 12, 13, 14, 18, 24, 26, 27, 28, 32, 37]],
]


def state(story, room):
    v = story.story_flags.get(FLAG)
    if isinstance(v, list) and len(v) == 2 and v[0] == room and v[1] in (0, 1, 2, 3):
        return v[1]
    return 0


def condition(story, arg):
    what, *rest = str(arg).split(":")
    if what == "open":
        room, region = int(rest[0]), int(rest[1])
        return region not in BLOCKED[room][state(story, room)]
    if what == "state":
        return state(story, int(rest[0])) == int(rest[1])
    return False


def _show(story, room):
    """The flag the room's picture follows: this room's state, and no other."""
    for r in range(3):
        for k in range(4):
            story.story_flags.pop(f"sunyshore_gym_r{r}_s{k}", None)
    story.story_flags[f"sunyshore_gym_r{room}_s{state(story, room)}"] = True


def _reopen(state_):
    if hasattr(state_, "_bar_list") and hasattr(state_, "_bar_met"):
        state_.barred = {tuple(t): bar for bar in state_._bar_list if not state_._bar_met(bar) and state_._bar_here(bar) for t in bar.get("tiles", [])}
        if hasattr(state_, "_rot_bars"):
            state_.barred.update(state_._rot_bars())
    if hasattr(state_, "_refresh_picture"):
        state_._refresh_picture()


def event(state_, ev, lines, show):
    story = state_.game.story_manager
    if "enter" in ev:   # (into a room: its walkways as they start)
        r = int(ev["enter"])
        v = story.story_flags.get(FLAG)
        if not (isinstance(v, list) and v and v[0] == r):
            story.story_flags[FLAG] = [r, 0]
        _show(story, r)
        _reopen(state_)
        return
    kind = ev.get("press")
    if kind not in STEP:
        return
    r = int(ev.get("room", 0))

    def turn():
        story.story_flags[FLAG] = [r, (state(story, r) + STEP[kind]) % 4]
        _show(story, r)
        _reopen(state_)
    try:
        from src.vfx import area_changes
        area_changes.change(state_, "stairs", turn)   # (a quick fade, as the scene changes to the gears turned)
    except Exception:
        turn()
    show(["You stepped on the switch.", "With a grinding of gears, the walkways turned!"])
