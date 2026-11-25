"""Turnback Cave (Pokemon Platinum, 11-24, Sinnoh S7b; built by kanto_handoff/sinnoh_map_tools/s_s7_turnback.py): a maze of
rooms that changes as you go. Platinum's rules (Bulbapedia's Turnback Cave page):
- from the entrance you come into the first room; every door of a room leads to a new room, picked as you go through:
  one time in four the next pillar room, else one of the rock rooms;
- the door you came in by leads back to the entrance (not in the third pillar room);
- the room after the third pillar room is Giratina's room; any door out of it leads back to the entrance;
- go through 30 rooms without getting there and the next door leads back to the entrance;
- a pillar room's carving says which pillar it is and how many rooms you've come through.
In Giratina's room: Giratina (Altered Forme) if you fought it in the Distortion World and didn't catch it (beaten or run
from, it's back after you next enter the Hall of Fame); otherwise an item by how many rooms it took - 3 a Reaper Cloth,
4-15 a Rare Bone, 16-30 Stardust - there again each time you get there.

The map's floors: 0 the entrance, 1 the first room, 2 the pillar room, 3 Giratina's room, 4+ the rock rooms. Each room's
doors (Platinum's) are at N (11,1), E (20,11), S (11,20), W (2,11); you come in at the door opposite the one you took.
State: story flag "turnback" {"pillars", "rooms", "came": [x, y] the door you came in by, "end": rooms at Giratina's room,
"took": the item taken this time}. Hooks: dungeon.py's "warp_world" (warp), conditions "world:turnback_cave:<arg>"
("giratina", "item"), event {"world": "turnback_cave", "item": true}."""
import random

ENTRANCE, FIRST, PILLAR, GIRATINA, ROCK0 = 0, 1, 2, 3, 4
ROCKS = 6
DOORS = {(11, 1): (11, 20), (20, 11): (2, 11), (11, 20): (11, 1), (2, 11): (20, 11)}   # door taken -> door you come in at
BACK = (11, 16)          # (the first room's way back to the entrance)
OUTSIDE = (21, 8)        # (the entrance: below its door into the cave)
LIMIT = 30
RNG = random.Random()


def _st(story):
    return story.story_flags.setdefault("turnback", {"pillars": 0, "rooms": 0, "came": None})


def _reset(story):
    story.story_flags["turnback"] = {"pillars": 0, "rooms": 0, "came": None}


def _out(story):
    _reset(story)
    return (ENTRANCE, OUTSIDE[0], OUTSIDE[1])


def warp(state, door, to):
    """The room a door leads to now (dungeon.py's warp_world)."""
    story = state.game.story_manager
    here = state.run.index
    if here == ENTRANCE:   # (into the cave: the first room)
        story.story_flags["turnback"] = {"pillars": 0, "rooms": 1, "came": list(BACK)}
        return (FIRST, BACK[0], BACK[1] - 1)
    if here == FIRST and tuple(door) == BACK:
        return _out(story)
    st = _st(story)
    if here == GIRATINA or tuple(door) not in DOORS:
        return _out(story)
    if st.get("came") and tuple(door) == tuple(st["came"]) and not (here == PILLAR and st["pillars"] >= 3):
        return _out(story)
    if st["rooms"] >= LIMIT:
        return _out(story)
    arrive = DOORS[tuple(door)]
    st["rooms"] += 1
    st["came"] = list(arrive)
    if st["pillars"] >= 3:
        st["end"], st["took"] = st["rooms"], False
        return (GIRATINA, arrive[0], arrive[1])
    if RNG.random() < 0.25:
        st["pillars"] += 1
        return (PILLAR, arrive[0], arrive[1],
                [f"A stone pillar stands in the middle of the room. Carved at its base: {st['pillars']} ... {st['rooms']}"])
    return (ROCK0 + RNG.randrange(ROCKS), arrive[0], arrive[1])


def _caught(story):
    dex = story.game.data.data.get("pokedex", {}) if getattr(story, "game", None) else {}
    return any(int(v.get("id", 0)) in (487, 4001) for v in dex.values() if isinstance(v, dict))


def giratina_here(story):
    f = story.story_flags
    return bool(f.get("TURNBACK_CAVE_boss_defeated") and not f.get("turnback_giratina_done") and not _caught(story))


def item_for(rooms):
    return "REAPER_CLOTH" if rooms <= 3 else "RARE_BONE" if rooms <= 15 else "STARDUST"


def condition(story, arg):
    if arg == "giratina":
        return giratina_here(story)
    if arg == "item":   # (the pedestal's item stands whenever Giratina doesn't: a cave's figures are set as you come in)
        return not giratina_here(story)
    return False


def event(state_, ev, lines, show):
    story = state_.game.story_manager
    st = story.story_flags.get("turnback") or {}
    if ev.get("item") and st.get("end") and not st.get("took"):
        it = item_for(int(st["end"]))
        story.inventory[it] = story.inventory.get(it, 0) + 1
        st["took"] = True
        show([f"You found a {it.replace('_', ' ').title()}!"])
        return
    show(["There's nothing else on the pedestal."] if ev.get("item") else (lines or ["..."]))
