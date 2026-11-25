"""Marlon's Gym in Humilau City (Unova batch 9a, 11-24): Black 2's lily pads.

Black 2's Gym is docks in water, joined by lily pads that float you across in a straight line until they bump something.
The pads are moving objects the game loads for the puzzle (not in the map, like Drayden's statues), so each pad here is a
ride between two docks across open water (the walkthrough's route: the entrance -> Doyle's dock -> Melina's -> the middle
dock with Santino's islet -> Enzio, Jeanne and Sable -> Marlon). A pad waits at one end; step onto the dock's edge where
it waits and it carries you to the other end, where it stays till ridden back (saved: story flag humilau_gym_pads).
Map side (dev/builders/town_maps/unova.py, OPE_GYM's neighbour HUM_GYM): an "every" scene on each pad end, condition
"world:humilau_gym:at:<i>:<A|B>", event {"world": "humilau_gym", "ride": i}, as Canalave's platforms (canalave_gym.py)."""
FLAG, ARRIVED = "humilau_gym_pads", "humilau_gym_arrived"
ROOM = "gym"
# (A, B): dock edge tiles, each pad's two ends, on one row or column across water (zone 473's walk grid)
PADS = [((11, 64), (4, 64)),     # entrance -> Doyle's dock (south-west)
        ((24, 60), (24, 56)),    # entrance -> the south-east dock
        ((18, 54), (18, 47)),    # -> Melina's dock
        ((19, 46), (23, 46)),    # Melina's -> the middle dock
        ((12, 56), (12, 63)),    # the entrance's north end <-> the little south dock
        ((12, 48), (12, 41)),    # the little south dock -> the middle dock
        ((3, 34), (7, 34)),      # the middle dock -> Santino's islet
        ((24, 39), (24, 35)),    # the middle dock -> Jeanne's dock (east)
        ((12, 27), (12, 20)),    # the middle dock -> Enzio's dock
        ((3, 27), (3, 23)),      # the middle dock -> the west dock
        ((4, 10), (8, 10)),      # the west dock -> Sable's dock
        ((10, 10), (14, 10)),    # Sable's -> Marlon's platform
        ((24, 15), (24, 11)),    # Jeanne's dock -> the north-east dock
        ((20, 10), (16, 10))]    # the north-east dock -> Marlon's platform
STEP = 6   # (frames a tile, floating)


def bits(story):
    v = story.story_flags.get(FLAG)
    return v if isinstance(v, int) else 0   # (every pad starts at its A end)


def end(story, i):
    return "B" if bits(story) >> i & 1 else "A"


def where(i, e):
    return PADS[i][0 if e == "A" else 1]


def condition(story, arg):
    what, *rest = str(arg).split(":")
    if what == "at":
        i, e = int(rest[0]), rest[1]
        if end(story, i) != e:
            return False
        t = where(i, e)
        return story.story_flags.get(ARRIVED) != [t[0], t[1]]
    if what == "rode":   # (pad i has carried you to its B end and waits there: the Journal's way-points, 11-25)
        return end(story, int(rest[0])) == "B"
    return False


def _tick(state):
    a = getattr(state, "_hg_ride", None)
    story = state.game.story_manager
    arr = story.story_flags.get(ARRIVED)
    if arr and not a and tuple(state.player) != (arr[0], arr[1]):
        story.story_flags.pop(ARRIVED, None)   # (stepped off the pad: it can carry you again)
    if not a:
        if not arr:
            state.__dict__.get("_tickers", {}).pop("humilau_gym", None)
        return
    a["t"] += 1
    if a["t"] % STEP == 0 and a["path"]:
        state.player = state.anim_from = a["path"].pop(0)
    if not a["path"]:
        state._hg_ride = None
        state._scene_lock = False


def ride(story, i):
    """Flip pad i to its other end; (from, to, path tiles between)."""
    e0 = end(story, i)
    e1 = "A" if e0 == "B" else "B"
    story.story_flags[FLAG] = bits(story) ^ (1 << i)
    t0, t1 = where(i, e0), where(i, e1)
    story.story_flags[ARRIVED] = [t1[0], t1[1]]
    dx = (t1[0] > t0[0]) - (t1[0] < t0[0])
    dy = (t1[1] > t0[1]) - (t1[1] < t0[1])
    path, x, y = [], t0[0], t0[1]
    while (x, y) != tuple(t1):
        x += dx; y += dy
        path.append((x, y))
    return t0, t1, path


def event(state, ev, lines, show):
    i = int(ev.get("ride", -1))
    if not 0 <= i < len(PADS) or getattr(state, "_hg_ride", None):
        return
    _t0, _t1, path = ride(state.game.story_manager, i)
    state.__dict__.setdefault("_tickers", {})["humilau_gym"] = _tick
    state._hg_ride = {"t": 0, "path": path}
    state._scene_lock = True
    state.walk_goal = None
    if hasattr(state, "flash"):
        state.flash("You hopped onto a lily pad!", 50)


def scenes():
    """The Gym room's scenes: one on each pad end."""
    out = []
    for i, (a, b) in enumerate(PADS):
        for e, t in (("A", a), ("B", b)):
            out.append({"trigger": {"zone": [t[0], t[1], t[0], t[1]]}, "every": True,
                        "condition": ["world:humilau_gym:at:%d:%s" % (i, e)], "cast": [],
                        "event": {"world": "humilau_gym", "ride": i}})
    return out
