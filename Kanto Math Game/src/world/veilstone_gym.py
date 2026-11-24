"""Veilstone Gym's punching bags (Sinnoh S4, Jordan 11-24: "Start S4"; the Gym as Platinum's).

Platinum (pret pokeplatinum src/overlay008/gym_features.c, VeilstoneGym_*, read 11-24): nine punching bags and eleven
stacks of tires stand in the Gym's rooms. Face a bag and hit it: it slides the way you hit it until the tile it is on, or
the next one, stops it (sVeilstoneTileBehaviors: 1 a bag can't be there, 3 it can't go west or east from here, 5 it can't
go west from here, 4 it stops when it passes here) or a stack of tires is next in its way - then it knocks the stack over
and the stack is gone. A bag that can't move just swings. Bags never meet (checked: every push from the start).
Here: walk into a bag to hit it (as you push a boulder); the bags and stacks are the room's "barred" blockers, each
shown while "world:veilstone_gym:nobag:<x>:<y>" / "nostack:<k>" is false; where they stand is kept in story flags
(veilstone_gym_bags, veilstone_gym_stacks) and set back as you come in (the room's "enter" scene: {"world":
"veilstone_gym", "reset": true}), as Platinum's do when you leave its Gym. The slide is animated: a wind-up swing, then
the bag glides to its stop (the room's frame tickers, walk_town._tickers).
Map side: kanto_handoff/sinnoh_map_tools/s_s4_veilstone_gym.py (the blockers, the pictures from Platinum's own models)."""
OY = 1   # (our room is Platinum's C07GYM0101 cropped at (0, 1): room y = zone y - 1)
_ROWS = {   # sVeilstoneTileBehaviors rows z 7..27 (every other row: 1)
    7: "11111111000400000000001111111111", 10: "11101111100004004001111111111111", 11: "11101111111111111111111011111111",
    12: "11135000111111111111011011111111", 13: "11130111111111111111011011111111", 14: "11100000111111111111011011111111",
    15: "11110111111111111111011011111111", 16: "11110111111111111111301011111111", 17: "11100000011111111111301011111111",
    18: "11100111011111111111101011111111", 19: "11100111011111111111101011111111", 20: "11100000011111111111141011111111",
    21: "11110111111111111111101011111111", 22: "11110111111111111111101011111111", 23: "11111111111111111111101011111111",
    24: "11111111111111111111101011111111", 25: "11111111111111111111111011111111", 26: "11111111111111100000111011111111",
    27: "11111111111111111111111011111111"}
BAGS = [(3, 10), (4, 22), (8, 7), (8, 20), (15, 26), (16, 10), (20, 17), (21, 24), (23, 11)]   # (sPunchingBagPositions, z - 2)
STACKS = [(3, 21), (8, 10), (8, 12), (8, 14), (12, 7), (12, 10), (19, 10), (20, 11), (20, 26), (22, 7), (23, 28)]   # (sTireStackPositions, z - 2)
BAG_FLAG, STACK_FLAG = "veilstone_gym_bags", "veilstone_gym_stacks"
CANT, STACK, PAUSE = 1, 2, 4
WIND, STEP = 14, 5   # (frames: the swing before it moves, then each tile it glides)


def beh(x, y):
    row = _ROWS.get(y)
    return int(row[x]) if row and 0 <= x < 32 else 1


def tile_flags(x, y, d, stacks):
    """VeilstoneGym_GetTileFlags: d = (dx, dy)."""
    f = 0
    b = beh(x, y)
    if b == 4:
        f |= PAUSE
    elif b == 2 and d[1]:
        f |= CANT
    elif b == 3 and d[0]:
        f |= CANT
    elif b == 5 and d == (-1, 0):
        f |= CANT
    n = (x + d[0], y + d[1])
    if beh(*n) == 1:
        f |= CANT
    if n in stacks:
        f |= STACK
    return f


def slide(pos, d, stacks):
    """(where the bag stops, the stack it knocks over or None): CalculateDistanceBagWillTravel + MovePunchingBag."""
    x, y = pos
    if tile_flags(x, y, d, stacks) not in (0, PAUSE):
        return tuple(pos), None
    while True:
        x += d[0]; y += d[1]
        f = tile_flags(x, y, d, stacks)
        if f:
            break
    return (x, y), ((x + d[0], y + d[1]) if f & STACK else None)


def bags(story):
    v = story.story_flags.get(BAG_FLAG)
    return [tuple(b) for b in v] if isinstance(v, list) and len(v) == len(BAGS) else list(BAGS)


def stacks(story):
    v = story.story_flags.get(STACK_FLAG)
    gone = set(v) if isinstance(v, list) else set()
    return {s for k, s in enumerate(STACKS) if k not in gone}


def condition(story, arg):
    """"nobag:<x>:<y>" (room tile: no bag there now), "nostack:<k>" (stack k knocked over)."""
    what, *rest = str(arg).split(":")
    try:
        if what == "nobag":
            x, y = int(rest[0]), int(rest[1]) + OY
            return (x, y) not in bags(story)
        if what == "nostack":
            return STACKS[int(rest[0])] not in stacks(story)
    except (ValueError, IndexError):
        pass
    return False


def _reopen(state):
    if hasattr(state, "_bar_list") and hasattr(state, "_bar_met"):
        state.barred = {tuple(t): bar for bar in state._bar_list if not state._bar_met(bar) and state._bar_here(bar) for t in bar.get("tiles", [])}
        if hasattr(state, "_rot_bars"):
            state.barred.update(state._rot_bars())


def reset(story):
    story.story_flags[BAG_FLAG] = [list(b) for b in BAGS]
    story.story_flags[STACK_FLAG] = []


def _tick(state):
    a = getattr(state, "_vg_anim", None)
    if not a:
        state.__dict__.get("_tickers", {}).pop("veilstone_gym", None)
        return
    a["t"] += 1
    t, dist, (dx, dy), to = a["t"], a["dist"], a["d"], a["to"]
    if t < WIND:   # (it swings away from the hit, and back)
        import math
        k = 0.18 * math.sin(math.pi * t / WIND)
        nudge = [dx * (k - dist), dy * (k - dist)]
    else:
        left = max(0.0, dist - (t - WIND) / STEP)
        nudge = [-dx * left, -dy * left]
    bar = state.barred.get(to)
    if bar is not None:
        state.barred[to] = dict(bar, nudge=nudge)
    if t >= WIND + dist * STEP:
        story = state.game.story_manager
        if a.get("knock") is not None:   # (the stack it hit topples over: gone)
            story.story_flags[STACK_FLAG] = sorted(set(story.story_flags.get(STACK_FLAG) or []) | {a["knock"]})
        state._vg_anim = None
        state._scene_lock = False
        _reopen(state)
        if hasattr(state, "_refresh_picture"):
            state._refresh_picture()


def event(state, ev, lines, show):
    story = state.game.story_manager
    if ev.get("reset"):
        reset(story)
        state._vg_anim = None
        _reopen(state)
        return
    if getattr(state, "_vg_anim", None) or not ev.get("at"):
        return
    rx, ry = ev["at"]
    px, py = tuple(state.player)
    d = (rx - px, ry - py)
    if abs(d[0]) + abs(d[1]) != 1:
        return
    here = (rx, ry + OY)
    bs = bags(story)
    if here not in bs:
        return
    st = stacks(story)
    to, knock = slide(here, d, st)
    dist = abs(to[0] - here[0]) + abs(to[1] - here[1])
    i = bs.index(here)
    if dist == 0:   # (it only swings)
        state._vg_anim = {"t": 0, "dist": 0, "d": d, "to": (rx, ry), "knock": None}
    else:
        bs[i] = to
        story.story_flags[BAG_FLAG] = [list(b) for b in bs]
        state._vg_anim = {"t": 0, "dist": dist, "d": d, "to": (to[0], to[1] - OY),
                          "knock": STACKS.index(knock) if knock in STACKS else None}
        _reopen(state)
    state._scene_lock = True
    state.walk_goal = None
    state.__dict__.setdefault("_tickers", {})["veilstone_gym"] = _tick

