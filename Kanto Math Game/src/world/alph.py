"""The Ruins of Alph's Unown (HeartGold/SoulSilver): each chamber's slide puzzle calls its own letters into the underground hall
(Bulbapedia, "Ruins of Alph", Generation IV): Kabuto A-J, Omanyte K-Q, Aerodactyl R-V, Ho-Oh W-Z. The ! and ? come once all 26
letters are caught. Puzzles: src/minigames/tiles.AlphPuzzle (story flag alph_<chamber>_solved); the walk-in rooms: j_alph.py."""
import random

PUZZLE_LETTERS = {"kabuto": "abcdefghij", "omanyte": "klmnopq", "aerodactyl": "rstuv", "hooh": "wxyz"}
MARKS = ("exclamation", "question")


def solved(story, chamber):
    return bool(story.story_flags.get(f"alph_{chamber}_solved"))


def all_letters_caught(story):
    counts = getattr(story, "catch_counts", {}) or {}
    return all(counts.get(f"201_{c}", 0) > 0 for c in "abcdefghijklmnopqrstuvwxyz")


def open_forms(story):
    """The Unown shapes the ruins call now (their forms: "a".."z", "exclamation", "question")."""
    out = {c for ch, letters in PUZZLE_LETTERS.items() if solved(story, ch) for c in letters}
    if len(out) == 26 and all_letters_caught(story):
        out.update(MARKS)
    return out


def is_ruins(area_data):
    return isinstance(area_data, dict) and area_data.get("route_name") == "Ruins of Alph"


def pick(story, weights, rng=random):
    """One open form, by the area's weights ({"201_a": w, ...}); None if no puzzle is solved yet."""
    forms = open_forms(story)
    opts = [(k.split("_", 1)[1], w) for k, w in (weights or {}).items() if k.startswith("201_") and k.split("_", 1)[1] in forms]
    if not opts:
        opts = [(f, 1.0) for f in sorted(forms)]
    if not opts:
        return None
    roll = rng.random() * sum(w for _f, w in opts)
    for f, w in opts:
        roll -= w
        if roll < 0:
            return f
    return opts[-1][0]
