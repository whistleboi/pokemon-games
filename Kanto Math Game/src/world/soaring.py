"""Soaring in the Sky's landing places (Jordan, 11-14): what happens when you land on a Mirage spot. The flight itself is
the 3D one (src/states/overworld/soaring3d.py, src/world/soaring3d.py); its landings call on_landing here.

- One legend per visit (Jordan, 11-14: not by day or time as in ORAS): landing picks one still to catch, at random, and
  now and then none comes out (NO_SHOW: one visit in five). Its SEEK option's condition is "mirage_here_<victory flag>".
- Each Mirage forest / cave / mountain / island is one of ORAS's eight places of its kind; its once-only item shows in
  its own nook (the item option's condition "mirage_spot_<kind>_<n>", dev/builders/town_maps/soaring.py).
- Each Mirage spot hides one more item, a new one each day (ORAS's daily slot): DAILY_ITEMS, the option's "gift_daily".
- ORAS's Mirage Islands (not Emerald's on Route 130) are home to Gen 1-3 legends Hoenn has no place for (Jordan, 11-14).
Places are map pixels on the game's Hoenn map picture (assets/region_maps/hoenn.png, 480 x 320).
"""
import datetime
import random

# The legends at each landing place (their victory flags), as the places' SEEK options name them.
LEGENDS = {
    "HOENN_CRESCENT_ISLE": ["mirage_cresselia"],
    "HOENN_PATHLESS_PLAIN": ["mirage_cobalion", "mirage_terrakion", "mirage_virizion"],
    "HOENN_NAMELESS_CAVERN": ["mirage_uxie", "mirage_mesprit", "mirage_azelf"],
    "HOENN_FABLED_CAVE": ["mirage_reshiram", "mirage_zekrom"],
    "HOENN_GNARLED_DEN": ["mirage_kyurem"],
    "HOENN_TRACKLESS_FOREST": ["mirage_raikou", "mirage_entei", "mirage_suicune"],
    "HOENN_MIRAGE_ISLANDS": ["mirage_articuno", "mirage_zapdos", "mirage_moltres", "mirage_mewtwo", "mirage_celebi"],
}
ISLAND_LEGENDS = LEGENDS["HOENN_MIRAGE_ISLANDS"]

# ORAS's places for each kind of Mirage spot ("Mirage spot", Bulbapedia), as near as the map picture allows: their order
# is the order of the places' once-only items (town_maps/soaring.py MIRAGE_ITEMS).
DAILY = {
    "island": ("HOENN_MIRAGE_ISLANDS", "Mirage Island", [(30, 178), (52, 276), (118, 26), (336, 84), (382, 98),
                                                        (296, 252), (272, 248), (204, 250)]),
    "forest": ("HOENN_MIRAGE_FOREST", "Mirage Forest", [(36, 222), (172, 266), (160, 34), (58, 62), (318, 78),
                                                       (348, 80), (444, 128), (262, 250)]),
    "cave": ("HOENN_MIRAGE_CAVE", "Mirage Cave", [(112, 292), (92, 26), (26, 92), (214, 26), (340, 86),
                                                 (424, 232), (334, 252), (268, 196)]),
    "mountain": ("HOENN_MIRAGE_MOUNTAIN", "Mirage Mountain", [(28, 150), (322, 80), (386, 94), (412, 100),
                                                             (432, 114), (428, 236), (414, 250), (326, 258)]),
}
KIND_OF = {v[0]: k for k, v in DAILY.items()}
KIND_OF["HOENN_CRESCENT_ISLE"] = "crescent"

# Each Mirage spot hides one more item, a new one each day (ORAS's daily slot; Bulbapedia "Mirage spot").
DAILY_ITEMS = {
    "cave": [("RED_SHARD", 50), ("BLUE_SHARD", 30), ("DEEP_SEA_TOOTH", 20)],
    "forest": [("TINY_MUSHROOM", 50), ("BIG_MUSHROOM", 30), ("RAZOR_CLAW", 20)],
    "island": [("PEARL", 50), ("BIG_PEARL", 30), ("RAZOR_FANG", 20)],
    "mountain": [("YELLOW_SHARD", 50), ("GREEN_SHARD", 30), ("DEEP_SEA_SCALE", 20)],
    "crescent": [("HEART_SCALE", 40), ("DEEP_SEA_TOOTH", 20), ("RAZOR_CLAW", 10), ("DEEP_SEA_SCALE", 10), ("RAZOR_FANG", 20)],
}
NO_SHOW = 0.2   # how often a Mirage spot's legends stay away (one visit in five)


def mount(game):
    """(species id, name) of your Eon: one in your party first, else your version's (Steven's gift), else Latios.
    (The figure waiting where it set you down: dungeon._figure_img "eon".)"""
    story = game.story_manager
    for p in getattr(story, "player_team", []) or []:
        if getattr(p, "id", None) in (380, 381):
            return p.id, ("Latias" if p.id == 380 else "Latios")
    from src.world import hoenn
    v = hoenn.info(story)
    if v:
        return v["eon_id"], v["eon"]
    return 381, "Latios"


def daily_item(story, kind, day=None):
    """Today's hidden item at a kind of Mirage spot: the same all day (each save its own), by ORAS's odds."""
    day = day or datetime.date.today()
    seed = sum(ord(c) for c in str(getattr(story, "player_name", "") or ""))
    rng = random.Random(day.toordinal() * 31 + seed)
    items, weights = zip(*DAILY_ITEMS[kind])
    return rng.choices(items, weights)[0]


def new_day_item(story, day=None):
    """Landing on a Mirage spot: its hidden item is there again if you haven't taken one today (the flag its option
    waits for: "mirage_daily_ready")."""
    today = (day or datetime.date.today()).toordinal()
    if story.story_flags.get("mirage_daily_day") != today:
        story.story_flags["mirage_daily_day"] = today
        story.story_flags["mirage_daily_ready"] = True


def mark_place(story, kind, i):
    """Landing on a Mirage forest / cave / mountain / island: which of its kind's places this is (its item's nook shows)."""
    for k in DAILY:
        for j in range(len(DAILY[k][2])):
            story.story_flags.pop(f"mirage_spot_{k}_{j}", None)
    story.story_flags[f"mirage_spot_{kind}_{i}"] = True


def roll_visit(story, legends, rng=random):
    """Which of a place's legends is out this visit (flag "mirage_here_<victory flag>"), or None: quiet this time."""
    for f in legends:
        story.story_flags.pop(f"mirage_here_{f}", None)
    left = [f for f in legends if not story.story_flags.get(f)]
    if not left or rng.random() < NO_SHOW:
        return None
    pick = rng.choice(left)
    story.story_flags[f"mirage_here_{pick}"] = True
    return pick


def caught_all(story, legends):
    return all(story.story_flags.get(f) for f in legends)


def today_place(story, area, day=None):
    """Which of its kind's places a Mirage spot is today (ORAS: they turn up somewhere new each day). The 3D Soaring map
    has one landing per kind, so the day picks the place - every place's item nook comes round in turn (11-24)."""
    kind = KIND_OF.get(area)
    if kind not in DAILY:
        return None
    places = DAILY[kind][2]
    seed = sum(ord(c) for c in str(getattr(story, "player_name", "") or ""))
    return places[((day or datetime.date.today()).toordinal() + seed) % len(places)]


def on_landing(story, area, place=None, rng=random):
    """You land on a Mirage spot (the flight's landing): today's hidden item, which place of its kind it is (place: its map
    point), which legend is out. Returns a line to add to the landing message, or ""."""
    kind = KIND_OF.get(area)
    if kind is None and area not in LEGENDS:
        return ""
    new_day_item(story)
    if kind in DAILY:
        places = DAILY[kind][2]
        i = places.index(tuple(place)) if place and tuple(place) in places else 0
        mark_place(story, kind, i)
    legends = LEGENDS.get(area)
    if legends and roll_visit(story, legends, rng) is None and not caught_all(story, legends):
        return " It's very quiet here this time..."
    return ""
