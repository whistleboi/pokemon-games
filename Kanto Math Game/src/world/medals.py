"""The Medal Rally, a starter set (11-20, Jordan: "Starter set"): Black 2 / White 2's Medal Box and Mr. Medal.

Mr. Medal gives you the MEDAL_BOX in Floccesy Town (after Alder's training). As you play, you earn medals for things the
game already keeps count of; Mr. Medal in a Pokemon Center hands over the ones you've earned (as in B2W2, where he hands
them out). The Medal Box (the Bag) shows what you have. More medals can be added to MEDALS later: each is (key, name,
how it's earned, test(story)). Received medals are story flags "medal_<key>"."""


def _caught(story):
    return sum(int(v) for v in (story.catch_counts or {}).values() if isinstance(v, (int, float)))


def _trainers(story):
    return sum(len(v) for v in (story.defeated_trainers or {}).values())


def _flags(story, prefix):
    return sum(1 for k, v in (story.story_flags or {}).items() if v and str(k).startswith(prefix))


def _badges(story):
    return len((story.badges or {}).get("UNOVA", []) or [])


def _right(story):
    return int((story.math_stats or {}).get("right", 0))


MEDALS = [
    ("first_catch", "First Catch", "Catch a wild Pokemon.", lambda s: _caught(s) >= 1),
    ("catch_10", "Capture Starter", "Catch 10 Pokemon.", lambda s: _caught(s) >= 10),
    ("catch_50", "Capture Fan", "Catch 50 Pokemon.", lambda s: _caught(s) >= 50),
    ("catch_100", "Capture Expert", "Catch 100 Pokemon.", lambda s: _caught(s) >= 100),
    ("trainer_10", "Battle Starter", "Beat 10 Trainers.", lambda s: _trainers(s) >= 10),
    ("trainer_50", "Battle Fan", "Beat 50 Trainers.", lambda s: _trainers(s) >= 50),
    ("trainer_100", "Battle Expert", "Beat 100 Trainers.", lambda s: _trainers(s) >= 100),
    ("hidden_1", "Treasure Seeker", "Find a hidden item.", lambda s: _flags(s, "hidden_") >= 1),
    ("hidden_10", "Treasure Hunter", "Find 10 hidden items.", lambda s: _flags(s, "hidden_") >= 10),
    ("visit_10", "Wanderer", "Visit 10 places.", lambda s: _flags(s, "visited_") >= 10),
    ("visit_30", "Globetrotter", "Visit 30 places.", lambda s: _flags(s, "visited_") >= 30),
    ("badge_1", "Basic Badge Holder", "Win a Unova Gym Badge.", lambda s: _badges(s) >= 1),
    ("badge_4", "Halfway There", "Win four Unova Gym Badges.", lambda s: _badges(s) >= 4),
    ("badge_8", "Badge Collector", "Win all eight Unova Gym Badges.", lambda s: _badges(s) >= 8),
    ("math_100", "Quick Thinker", "Answer 100 questions right.", lambda s: _right(s) >= 100),
    ("math_500", "Math Whiz", "Answer 500 questions right.", lambda s: _right(s) >= 500),
    # (batch 2, 11-20: Pokestar Studios, src/states/pokestar.py)
    ("film_1", "Rising Star", "Shoot your first film at Pokestar Studios.", lambda s: int(s.story_flags.get("pokestar_films", 0) or 0) >= 1),
    ("film_happy", "Happy Ending", "Get a happy ending at Pokestar Studios.", lambda s: _flags(s, "pokestar_happy_") >= 1),
    ("film_10", "Silver Screen", "Shoot 10 films at Pokestar Studios.", lambda s: int(s.story_flags.get("pokestar_films", 0) or 0) >= 10),
    ("star_10", "Big Star", "Reach the top Star Rank.", lambda s: int(s.story_flags.get("pokestar_rank", 0) or 0) >= 10),
]


def have_box(story):
    return (story.inventory or {}).get("MEDAL_BOX", 0) > 0


def received(story):
    return [m for m in MEDALS if story.story_flags.get("medal_" + m[0])]


def waiting(story):
    """Earned, not handed over yet."""
    out = []
    for key, name, how, test in MEDALS:
        if story.story_flags.get("medal_" + key):
            continue
        try:
            if test(story):
                out.append((key, name, how, test))
        except Exception:
            continue
    return out


def hand_out(story):
    """Mr. Medal at a Pokemon Center: the medals you've earned. Returns his lines."""
    if not have_box(story):
        return ["Mr. Medal: Hello! You don't have a Medal Box? Find me in Floccesy Town!"]
    new = waiting(story)
    if not new:
        return ["Mr. Medal: No new Medals for now. Keep at it, and come and see me again!",
                "Mr. Medal: You have %d of %d Medals." % (len(received(story)), len(MEDALS))]
    lines = ["Mr. Medal: Ah! You've earned %s!" % ("a Medal" if len(new) == 1 else "%d Medals" % len(new))]
    for key, name, how, _t in new:
        story.story_flags["medal_" + key] = True
        lines.append("You received the %s Medal! (%s)" % (name, how))
    lines.append("Mr. Medal: That makes %d of %d. Splendid!" % (len(received(story)), len(MEDALS)))
    return lines


def summary(story):
    """The Medal Box, opened."""
    got = received(story)
    lines = ["MEDAL BOX: %d of %d Medals." % (len(got), len(MEDALS))]
    if got:
        lines.append(", ".join(m[1] for m in got) + ".")
    left = len(waiting(story))
    if left:
        lines.append("%d more earned! Mr. Medal at a Pokemon Center will hand them over." % left)
    return lines
