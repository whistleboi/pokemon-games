"""Canalave Gym's moving platforms (Sinnoh S5, 11-24; Platinum's: pret pokeplatinum gym_features.c, CanalaveGym_*).

Four floors in one tower (our rooms gym, gym_2f, gym_3f, gym_4f). Nineteen platforms, each at one of its two ends: a lift
between two floors, or a slider along one floor (east-west or north-south). Step onto a platform where it stands and it
carries you to its other end (CanalaveGym_MovePlatform: the platform's state bit flips; it stays there till ridden back).
Platinum keeps the bits in the save; so do we (story flag canalave_gym_platforms; Platinum's starting ends).
Map side (kanto_handoff/sinnoh_map_tools/s_s5_canalave_gym.py): on each floor, an "every" scene on each platform end,
condition "world:canalave_gym:at:<i>:<A|B>", event {"world": "canalave_gym", "ride": i}. The tile you arrive on doesn't
carry you off again till you've stepped off it (story flag canalave_gym_arrived)."""
FLAG, ARRIVED = "canalave_gym_platforms", "canalave_gym_arrived"
ROOMS = ["gym", "gym_2f", "gym_3f", "gym_4f"]
# (axis, A (x, height in tiles, z), B, starts at B) - sCanalavePlatformPaths
PLATFORMS = [("y", (16, 0, 9), (16, 30, 9), False), ("y", (11, 0, 13), (11, 10, 13), False), ("y", (15, 0, 13), (15, 10, 13), False),
             ("y", (19, 0, 13), (19, 10, 13), False), ("y", (24, 0, 13), (24, 10, 13), False), ("y", (21, 0, 22), (21, 10, 22), False),
             ("y", (25, 0, 9), (25, 10, 9), True), ("y", (25, 0, 22), (25, 10, 22), True), ("y", (29, 0, 22), (29, 10, 22), True),
             ("y", (5, 10, 26), (5, 20, 26), False), ("x", (11, 10, 22), (18, 10, 22), True), ("y", (29, 10, 9), (29, 20, 9), True),
             ("x", (10, 20, 4), (14, 20, 4), False), ("x", (19, 20, 4), (22, 20, 4), False), ("x", (7, 20, 12), (22, 20, 12), False),
             ("x", (9, 20, 26), (21, 20, 26), False), ("z", (2, 20, 19), (2, 20, 22), True), ("z", (26, 20, 16), (26, 20, 22), False),
             ("z", (29, 20, 16), (29, 20, 22), True)]
STEP = 6   # (frames a tile, sliding)


def start_bits():
    return sum(1 << i for i, p in enumerate(PLATFORMS) if p[3])


def bits(story):
    v = story.story_flags.get(FLAG)
    return v if isinstance(v, int) else start_bits()


def end(story, i):
    return "B" if bits(story) >> i & 1 else "A"


def where(i, e):
    """(room, (x, z)) of platform i's end e."""
    x, h, z = PLATFORMS[i][1 if e == "A" else 2]
    return ROOMS[h // 10], (x, z)


def condition(story, arg):
    what, *rest = str(arg).split(":")
    if what == "at":
        i, e = int(rest[0]), rest[1]
        if end(story, i) != e:
            return False
        room, t = where(i, e)
        return story.story_flags.get(ARRIVED) != [room, t[0], t[1]]
    return False


def _tick(state):
    a = getattr(state, "_cg_ride", None)
    story = state.game.story_manager
    arr = story.story_flags.get(ARRIVED)
    if arr and not a and (getattr(state, "room", None) != arr[0] or tuple(state.player) != (arr[1], arr[2])):
        story.story_flags.pop(ARRIVED, None)   # (stepped off the platform: it can carry you again)
    if not a:
        if not arr:
            state.__dict__.get("_tickers", {}).pop("canalave_gym", None)
        return
    a["t"] += 1
    if a["t"] % STEP == 0 and a["path"]:
        state.player = state.anim_from = a["path"].pop(0)
    if not a["path"]:
        state._cg_ride = None
        state._scene_lock = False


def event(state, ev, lines, show):
    i = int(ev.get("ride", -1))
    if not 0 <= i < len(PLATFORMS) or getattr(state, "_cg_ride", None):
        return
    story = state.game.story_manager
    e0 = end(story, i)
    e1 = "A" if e0 == "B" else "B"
    story.story_flags[FLAG] = bits(story) ^ (1 << i)
    room1, t1 = where(i, e1)
    room0, t0 = where(i, e0)
    story.story_flags[ARRIVED] = [room1, t1[0], t1[1]]
    state.__dict__.setdefault("_tickers", {})["canalave_gym"] = _tick
    if room1 != room0:   # (a lift: up or down to its other floor)
        up = ROOMS.index(room1) > ROOMS.index(room0)
        if hasattr(state, "_go"):
            state._go(room1, "ROOM:" + room0)
        state.player = state.anim_from = tuple(t1)
        state.anim = 0
        if hasattr(state, "flash"):
            state.flash("The lift carried you " + ("up!" if up else "down!"), 70)
        return
    dx = (t1[0] > t0[0]) - (t1[0] < t0[0])
    dz = (t1[1] > t0[1]) - (t1[1] < t0[1])
    path, x, z = [], t0[0], t0[1]
    while (x, z) != tuple(t1):
        x += dx; z += dz
        path.append((x, z))
    state._cg_ride = {"t": 0, "path": path}
    state._scene_lock = True
    state.walk_goal = None
