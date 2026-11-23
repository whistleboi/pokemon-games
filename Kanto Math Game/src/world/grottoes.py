"""Hidden Grottoes (Black 2 / White 2; Jordan 11-23: "Build them, backfill"): a small clearing off a route, reached through
a gap in the trees. Each holds one thing at a time: a Pokemon with its Hidden Ability, an item on the ground, or a hidden
item. Once taken (a Pokemon met: caught, beaten or run from, as every wild Pokemon on our maps) it's empty, and every 256
steps walked in Unova it has a 5% chance to fill again. A refill is a Pokemon 20% of the time (the grotto's rare 1%,
uncommon 4% and common 15% groups), an item 40%, a hidden item 40% (Bulbapedia's rates for both lists).

Data: assets/unova_area_data.json "HIDDEN_GROTTOES", read from the game file by kanto_handoff/unova_map_tools/grottoes.py
(a/2/7/3: species, levels, female chance per version). The grotto map is Black 2's zone 518 (dev/builders/town_maps/unova.py
grotto_room), its contents a person on (15, 12) with one option per thing it can hold, each shown by the condition
"world:grottoes:<grotto>:<kind>[:<species>]". State: story flag "grottoes" {grotto: {"kind", "id", "level", "female",
"steps"}}. Steps: the Feats' Unova step count (src/world/feats.py)."""
import random

PERIOD, CHANCE = 256, 0.05
VISIBLE = {"POKE_BALL": 12.5, "GREAT_BALL": 5, "ULTRA_BALL": 2, "POTION": 6.25, "SUPER_POTION": 2.5, "HYPER_POTION": 1,
           "REPEL": 6.25, "SUPER_REPEL": 2.5, "MAX_REPEL": 1}
HIDDEN = {"DAMP_MULCH": 6.25, "GROWTH_MULCH": 6.25, "STABLE_MULCH": 6.25, "GOOEY_MULCH": 6.25, "TINY_MUSHROOM": 7.5,
          "BIG_MUSHROOM": 2.5, "RED_SHARD": 1, "GREEN_SHARD": 1, "YELLOW_SHARD": 1, "BLUE_SHARD": 1, "RARE_CANDY": 0.25,
          "PP_UP": 0.5, "PP_MAX": 0.25}


def table(story):
    game = getattr(story, "game", None)
    return list(((getattr(getattr(game, "loader", None), "area_data", None) or {}).get("HIDDEN_GROTTOES")) or [])


def grotto(story, gid):
    return next((g for g in table(story) if int(g["grotto"]) == int(gid)), None)


def _state(story):
    return story.story_flags.setdefault("grottoes", {})


def _steps(story):
    return int(((getattr(story, "feat_counts", {}) or {}).get("UNOVA") or {}).get("steps", 0))


def _version(story):
    return "WHITE_2" if str(story.story_flags.get("unova_version", "")).upper() == "WHITE_2" else "BLACK_2"


def _pick(rng, weights):
    total = sum(weights.values())
    r = rng.uniform(0, total)
    for k, w in weights.items():
        r -= w
        if r <= 0:
            return k
    return next(iter(weights))


def _fill(story, g, rng):
    """What the grotto holds after a refill."""
    roll = rng.random() * 100
    if roll < 20:
        slots = g["pokemon"][_version(story)]
        s = slots[_pick(rng, {i: s["rate"] for i, s in enumerate(slots)})]
        return {"kind": "pokemon", "id": int(s["id"]), "level": rng.randint(int(s["min"]), int(s["max"])),
                "female": rng.random() * 100 < int(s["female"])}
    hidden = roll >= 60
    items = dict(HIDDEN if hidden else VISIBLE)
    if not hidden:
        items.update(g.get("stones") or {})
    return {"kind": "hidden" if hidden else "item", "id": _pick(rng, items)}


def refresh(story, gid):
    """The grotto's contents now: filled on the first look, and an empty one maybe refilled by the steps walked since."""
    g = grotto(story, gid)
    if g is None:
        return {"kind": "empty"}
    st, key, now = _state(story), str(gid), _steps(story)
    cur = st.get(key)
    if cur is None:
        cur = st[key] = _fill(story, g, random.Random())
    elif cur.get("kind") == "empty":
        last = int(cur.get("steps", 0))
        periods = max(0, (now - last) // PERIOD)
        if periods:
            rng = random.Random()
            if any(rng.random() < CHANCE for _ in range(min(periods, 200))):
                cur = st[key] = _fill(story, g, rng)
            else:
                cur["steps"] = last + periods * PERIOD
    return cur


def empty(story, gid):
    """Taken: empty from now (counted for the Quest Book's Grotto Explorer Feat)."""
    _state(story)[str(gid)] = {"kind": "empty", "steps": _steps(story)}
    from src.world import feats as _feats
    _feats.note(story, "grottoes")


def condition(story, arg):
    """"<grotto>:pokemon:<species>", "<grotto>:item", "<grotto>:hidden", "<grotto>:empty": what it holds now."""
    parts = str(arg).split(":")
    cur = refresh(story, parts[0])
    if cur.get("kind") != parts[1]:
        return False
    return len(parts) < 3 or int(parts[2]) == int(cur.get("id", -1))


def species(g):
    """Every species a grotto can hold, both versions, in the file's order."""
    out = []
    for v in ("BLACK_2", "WHITE_2"):
        for s in g["pokemon"][v]:
            if int(s["id"]) not in out:
                out.append(int(s["id"]))
    return out


def make(game, cur):
    """The grotto's Pokemon: its level, its Hidden Ability, its gender."""
    from src.pokemon.data import Pokemon
    raw = game.loader.fetch_specific(int(cur["id"]))
    p = Pokemon(raw, game.assets, size_mult=3.125)
    p.level = int(cur["level"])
    p.ability_slot = 2
    if getattr(p, "gender", "?") in ("M", "F"):
        p.gender = "F" if cur.get("female") else "M"
    p.current_hp = p.get_max_hp()
    return p


def event(state, ev, lines, show):
    """Someone reached the grotto's spot (its person on (15, 12)): take what's there."""
    game = state.game
    story = game.story_manager
    gid = ev.get("grotto")
    if ev.get("fill"):   # (a story fills it: Route 5's first visit is always a Minccino with Skill Link, as Black 2's script)
        _state(story)[str(gid)] = dict(ev["fill"])
        return
    cur = refresh(story, gid)
    kind = cur.get("kind")
    if kind == "pokemon" and hasattr(state, "_meet_wild"):
        p = make(game, cur)
        empty(story, gid)
        from src.dungeon.core import Mover
        x, y = ev.get("at") or (15, 12)
        m = Mover("wild", int(x), int(y) + 1, p)
        state.run.floor.movers.append(m)
        if hasattr(state, "_sync_figures"):
            state._sync_figures()
        state._meet_wild(m)
        return
    if kind in ("item", "hidden"):
        item = cur["id"]
        empty(story, gid)
        story.add_item(item, 1)
        name = item.replace("_", " ").title()
        if hasattr(state, "_sync_figures"):
            state._sync_figures()
        show((["Something is buried here..."] if kind == "hidden" else []) + [f"You found a {name}!"])
        return
    show(["There's nothing here right now.", "Maybe something will turn up after a while."])
