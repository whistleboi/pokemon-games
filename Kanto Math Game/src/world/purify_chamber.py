"""XD's Purify Chamber (Orre batch 8b, Jordan 11-21: "XD's nine chambers"). Rules from the fan wikis (Bulbapedia's Purify
Chamber page, Serebii), kanto_handoff/orre_check/DECISIONS.md "Batch 8b calls" 1.

- Nine sets at the HQ Lab. Each holds a Shadow Pokemon in its middle and up to four other (not Shadow) Pokemon in a ring
  round it. Pokemon in the chamber leave your party / PC while they're in it (kept in story flag KEY as save records).
- Flow: read clockwise round the ring, each Pokemon's best type against the next one's types - super effective +1,
  resisted -1 (an immunity counts as resisted), else 0; Normal counts as super effective on Normal. Max Tempo: four in
  the ring and every one of the four links super effective.
- Every 161 steps you walk, each set's Shadow Pokemon's heart opens by 10 / 27 / 49 / 96 (one to four in its ring), half
  as much again for each point of flow (up to double at Max Tempo). An open heart is purified at the Lab's chamber.
- Shadow Lugia (XD001) can only go in when all nine sets are at Max Tempo (a "best circle"); then its heart opens at once.
  Purified, it learns FeatherDance and Psycho Boost too, as in XD.

    sets(story) -> the nine sets [{"shadow": record or None, "ring": [record, ...]}]
    flow(game, s) / tempo_max(game, s) / best_circle(game)
    walked(game, steps) -> lines (called from the map's step counter)"""

KEY = "purify_chamber"
SETS = 9
RING = 4
EVERY = 161
BASE = (10, 27, 49, 96)
LUGIA = 9400
LUGIA_EXTRA = ["FEATHER-DANCE", "PSYCHO-BOOST"]


def sets(story):
    s = story.story_flags.get(KEY)
    if not isinstance(s, list) or len(s) != SETS:
        s = [{"shadow": None, "ring": []} for _ in range(SETS)] if not isinstance(s, list) else (s + [{"shadow": None, "ring": []}] * SETS)[:SETS]
        s = [dict(x) for x in s]
        story.story_flags[KEY] = s
    return s


def _types(game, rec):
    raw = game.loader.fetch_specific(int(rec["id"])) or {}
    return [str(t).upper() for t in raw.get("types") or []]


def link(game, a, b):
    """+1 super effective, -1 resisted (or no effect), 0 neutral: a's best type against b."""
    from src.pokemon.mechanics import TypeAdvantage
    chart = TypeAdvantage(game.loader.area_data.get("TYPE_CHART", {}))
    at, bt = _types(game, a), _types(game, b)
    best = None
    for t in at:
        m = 2.0 if (t == "NORMAL" and "NORMAL" in bt) else chart.get_multiplier(t, bt)
        best = m if best is None else max(best, m)
    if best is None:
        return 0
    return 1 if best > 1 else (-1 if best < 1 else 0)


def flow(game, s):
    ring = s.get("ring") or []
    if len(ring) < 2:
        return 0
    pairs = [(ring[i], ring[(i + 1) % len(ring)]) for i in range(len(ring))] if len(ring) > 2 else [(ring[0], ring[1]), (ring[1], ring[0])]
    return sum(link(game, a, b) for a, b in pairs)


def tempo_max(game, s):
    ring = s.get("ring") or []
    return len(ring) == RING and flow(game, s) == RING


def best_circle(game):
    return all(tempo_max(game, s) for s in sets(game.story_manager))


def opens_by(game, s):
    """How much this set's Shadow heart opens every EVERY steps."""
    n = len(s.get("ring") or [])
    if not n or not s.get("shadow"):
        return 0
    return int(BASE[n - 1] * (1 + 0.25 * max(0, flow(game, s))))


def is_open(rec):
    return bool(rec) and int(((rec.get("shadow") or {}).get("gauge", 1))) <= 0


def walked(game, steps=1):
    story = game.story_manager
    if not any(x.get("shadow") for x in sets(story)):
        return []
    n = int(story.story_flags.get("_chamber_steps", 0) or 0) + steps
    lines = []
    while n >= EVERY:
        n -= EVERY
        for s in sets(story):
            rec = s.get("shadow")
            if not rec or is_open(rec):
                continue
            sh = rec.setdefault("shadow", {"gauge": 1, "max": 1, "hidden": []})
            sh["gauge"] = max(0, int(sh.get("gauge", 0)) - opens_by(game, s))
            if sh["gauge"] <= 0:
                lines.append(f"A message from the HQ Lab: the Shadow Pokemon in the Purify Chamber has opened its heart!")
    story.story_flags["_chamber_steps"] = n
    return lines


# ------------------------------------------------------------------ putting in and taking out (the Lab's screen)
def put_shadow(game, i, mon):
    """Into set i's middle. Returns lines, or None when it went in."""
    story = game.story_manager
    s = sets(story)[i]
    if s.get("shadow"):
        return ["There's already a Shadow Pokemon in that set."]
    if int(getattr(mon, "id", 0)) == LUGIA:
        if not best_circle(game):
            return ["The chamber can't take XD001 yet. Its heart is shut too tight.",
                    "Krane thinks every set would need to be at Max Tempo at once - all nine."]
        rec = story._pokemon_record(mon)
        rec["shadow"] = dict(rec.get("shadow") or {"max": 1, "hidden": []}, gauge=0)
        s["shadow"] = rec
        return None
    s["shadow"] = story._pokemon_record(mon)
    return None


def put_ring(game, i, mon):
    story = game.story_manager
    s = sets(story)[i]
    if len(s.get("ring") or []) >= RING:
        return ["That set's ring is full."]
    s.setdefault("ring", []).append(story._pokemon_record(mon))
    return None


def take(game, i, which):
    """A Pokemon back out of set i ("shadow", or a ring index): the Pokemon."""
    story = game.story_manager
    s = sets(story)[i]
    rec = s.get("shadow") if which == "shadow" else (s.get("ring") or [None])[which]
    if not rec:
        return None
    if which == "shadow":
        s["shadow"] = None
    else:
        s["ring"].pop(which)
    return story._load_pokemon(rec, game.loader)


def purify(game, i):
    """Set i's open-hearted Shadow Pokemon purified: the Pokemon (out of the chamber), or None."""
    story = game.story_manager
    s = sets(story)[i]
    if not is_open(s.get("shadow")):
        return None
    mon = take(game, i, "shadow")
    lugia = int(mon.id) == LUGIA
    new = story.purified_copy(mon)
    if lugia:
        new.move_pool = list(dict.fromkeys(list(getattr(new, "move_pool", []) or []) + LUGIA_EXTRA))
        story.story_flags["xd_lugia_purified"] = True
    return new
