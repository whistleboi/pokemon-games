"""The Black Tower and White Treehollow (Unova batch 11b, 11-25): Unova's Challenge, as Black 2 (Jordan 11-24: ten Areas,
their trainers and gate keys, the boss at the end, Black 2's prizes).

Being built: the lobby desk's event {"world": "black_tower", "desk": "BLACK" | "WHITE"} only greets you until the Areas
land (kanto_handoff/HANDOFF_UNOVA_MAPS.md, "Batch 11b research")."""

NAMES = {"BLACK": "the Black Tower", "WHITE": "the White Treehollow"}


def condition(story, arg):
    return False


def event(state, ev, lines, show):
    which = str(ev.get("desk") or "BLACK").upper()
    show(["Welcome to %s, Unova's Challenge!" % NAMES.get(which, "the Black Tower"),
          "We're still getting the Areas ready. Please come back soon!"])
