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
    ("hidden_1", "Dowsing Beginner", "Find a hidden item.", lambda s: _flags(s, "hidden_") >= 1),
    ("hidden_10", "Dowsing Specialist", "Find 10 hidden items.", lambda s: _flags(s, "hidden_") >= 10),
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
    # (batch 3a, 11-20: Castelia's Back Street, under the Sewers: Ricky, Jean-Paul, then Tina)
    ("castelia_boss", "Castelia Boss", "Beat all three Trainers on Castelia's Back Street.",
     lambda s: all(s.story_flags.get(f) for f in ("b2_back_ricky", "b2_back_jean_paul", "b2_back_tina"))),
]

# ---- beyond the starter set (11-25, for Unova's roadmap): Black 2's own Medal Rally (Bulbapedia's list), every Medal our
# game can count, in our own words. Left out: link trades and battles, Join Avenue, Funfest, Entree Forest, the Union Room,
# Tag Mode, Pass Powers, Game Sync, Memory Link, the Xtransceiver minigames, vending machines, TV, signboards and other
# one-off spots, the Battle Subway / Black Tower counts, the PWT's per-tournament wins: nothing counts them yet.
MYTHICAL = {151, 251, 385, 386, 489, 490, 491, 492, 493, 494, 647, 648, 649}
TYPES = ["Normal", "Fire", "Water", "Electric", "Grass", "Ice", "Fighting", "Poison", "Ground", "Flying", "Psychic", "Bug",
         "Rock", "Ghost", "Dragon", "Dark", "Steel"]
UNOVA_TOWNS = ["ASPERTIA_CITY", "FLOCCESY_TOWN", "VIRBANK_CITY", "CASTELIA_CITY", "NIMBASA_CITY", "DRIFTVEIL_CITY",
               "MISTRALTON_CITY", "LENTIMAS_TOWN", "UNDELLA_TOWN", "LACUNOSA_TOWN", "OPELUCID_CITY", "HUMILAU_CITY",
               "ICIRRUS_CITY", "NUVEMA_TOWN", "ACCUMULA_TOWN", "STRIATON_CITY", "NACRENE_CITY", "ANVILLE_TOWN",
               "BLACK_CITY", "UNITY_TOWER"]
BRIDGES = ["SKYARROW_BRIDGE", "DRIFTVEIL_DRAWBRIDGE", "TUBELINE_BRIDGE", "VILLAGE_BRIDGE", "MARVELOUS_BRIDGE"]


def _count(story, kind):
    """A Unova count kept as you play (src/world/feats.py note(): steps, fish, evolved, heals, purchases, spent...)."""
    return int(((getattr(story, "feat_counts", {}) or {}).get("UNOVA") or {}).get(kind, 0) or 0)


def _mons(story):
    return [p for p in list(story.player_team or []) + list(getattr(story, "pc_pokemon", []) or []) if p is not None]


def _pc(story):
    return len(getattr(story, "pc_pokemon", []) or [])


def _unova_dex(story):
    from src.world import feats
    return feats._dex_ids(story, "UNOVA") - MYTHICAL


def _caught_unova(story):
    from src.world import feats
    return feats.caught_in(story, "UNOVA")


def _type_done(story, t):
    sets = story.game.assets.movesets
    want = {i for i in _unova_dex(story) if t.upper() in [str(x).upper() for x in ((sets.get(str(i), {}) or {}).get("types") or [])]}
    return bool(want) and want <= _caught_unova(story)


def _national_done(story):
    from src.world import feats
    return set(range(1, 650)) - MYTHICAL <= feats._owned_ids(story)


def _visited(story, keys):
    return all(story.story_flags.get("visited_" + k) for k in keys)


def _league_wins(story):
    return [r for r in (story.story_flags.get("hall_of_fame_records") or []) if str(r.get("region")).upper() == "UNOVA"]


def _mono(story, t):
    """Won Unova's League with only t-type Pokemon (the Hall of Fame's record of the team)."""
    sets = story.game.assets.movesets
    return any(r.get("team") and all(t.upper() in [str(x).upper() for x in ((sets.get(str(m.get("id")), {}) or {}).get("types") or [])]
                                       for m in r["team"])
               for r in _league_wins(story))


def _spree(story):
    """50 Pokemon caught on one day (their catch dates: src/pokemon/data.py caught_date)."""
    from collections import Counter
    days = Counter(getattr(p, "caught_date", None) for p in _mons(story))
    days.pop(None, None)
    return max(days.values(), default=0) >= 50


def _rank_count(story):
    return sum(1 for m in MEDALS if story.story_flags.get("medal_" + m[0]) and not m[0].startswith("rank_"))


def _n(kind, goal):
    return lambda s: _count(s, kind) >= goal


MEDALS += [
    ("first_step", "First Step", "Get the Medal Box.", lambda s: have_box(s)),
    ("rank_rookie", "Rookie Medalist", "Collect 50 Medals.", lambda s: _rank_count(s) >= 50),
    ("rank_elite", "Elite Medalist", "Collect 100 Medals.", lambda s: _rank_count(s) >= 100),
    ("walk_5000", "Light Walker", "Take 5,000 steps in Unova.", _n("steps", 5000)),
    ("walk_10000", "Middle Walker", "Take 10,000 steps in Unova.", _n("steps", 10000)),
    ("walk_20000", "Heavy Walker", "Take 20,000 steps in Unova.", _n("steps", 20000)),
    ("walk_100000", "Honored Footprints", "Take 100,000 steps in Unova.", _n("steps", 100000)),
    ("center_10", "Pokemon Center Fan", "Rest your team at a Pokemon Center 10 times.", _n("heals", 10)),
    ("fish_1", "Old Rod Fisherman", "Reel in a Pokemon.", _n("fish", 1)),
    ("fish_10", "Good Rod Fisherman", "Reel in 10 Pokemon.", _n("fish", 10)),
    ("fish_50", "Super Rod Fisherman", "Reel in 50 Pokemon.", _n("fish", 50)),
    ("fish_100", "Mighty Fisher", "Reel in 100 Pokemon.", _n("fish", 100)),
] + [("type_" + t.lower(), t + "-type Catcher", "Catch every %s-type Pokemon in the Unova Pokedex." % t,
      (lambda s, t=t: _type_done(s, t))) for t in TYPES] + [
    ("unova_dex", "Unova Catcher", "Complete the Unova Pokedex.", lambda s: _unova_dex(s) <= _caught_unova(s)),
    ("national_dex", "National Catcher", "Complete the National Pokedex.", _national_done),
    ("box_30", "30 Boxed", "Have 30 Pokemon in your PC Boxes.", lambda s: _pc(s) >= 30),
    ("box_120", "120 Boxed", "Have 120 Pokemon in your PC Boxes.", lambda s: _pc(s) >= 120),
    ("box_360", "360 Boxed", "Have 360 Pokemon in your PC Boxes.", lambda s: _pc(s) >= 360),
    ("box_720", "Boxes Max", "Have 720 Pokemon in your PC Boxes.", lambda s: _pc(s) >= 720),
    ("spree_50", "Capturing Spree", "Catch 50 Pokemon in one day.", _spree),
    ("evolve_1", "Evolution Hopeful", "Evolve a Pokemon.", _n("evolved", 1)),
    ("evolve_10", "Evolution Tech", "Evolve Pokemon 10 times.", _n("evolved", 10)),
    ("evolve_50", "Evolution Expert", "Evolve Pokemon 50 times.", _n("evolved", 50)),
    ("evolve_100", "Evolution Authority", "Evolve Pokemon 100 times.", _n("evolved", 100)),
    ("hidden_50", "Dowsing Collector", "Find 50 hidden items.", lambda s: _flags(s, "hidden_") >= 50),
    ("hidden_150", "Dowsing Wizard", "Find 150 hidden items.", lambda s: _flags(s, "hidden_") >= 150),
    ("shop_100", "Regular Customer", "Buy things at shops 100 times.", _n("purchases", 100)),
    ("spend_10k", "Moderate Customer", "Spend $10,000 at shops.", _n("spent", 10000)),
    ("spend_100k", "Great Customer", "Spend $100,000 at shops.", _n("spent", 100000)),
    ("spend_1m", "Indulgent Customer", "Spend $1,000,000 at shops.", _n("spent", 1000000)),
    ("spend_10m", "Super Rich", "Spend $10,000,000 at shops.", _n("spent", 10000000)),
    ("premier", "Smart Shopper", "Buy enough Poke Balls at once for a bonus Premier Ball.", _n("premier", 1)),
    ("lucky_color", "Lucky Color", "Have a Shiny Pokemon.", lambda s: any(getattr(p, "is_shiny", False) for p in _mons(s))),
    ("locator_10", "Superb Locator", "Meet 10 Pokemon in rustling grass, rippling water or dust clouds.", _n("phenomena", 10)),
    ("musical_10", "Talented Cast Member", "Take part in 10 Pokemon Musicals.", _n("musicals", 10)),
    ("bridges", "Bridge Enthusiast", "Visit every bridge in Unova.", lambda s: _visited(s, BRIDGES)),
    ("around_unova", "Around Unova", "Visit every city and town in Unova.", lambda s: _visited(s, UNOVA_TOWNS)),
] + [("champ_" + t.lower(), t + "-type Champ", "Win the Pokemon League with only %s-type Pokemon." % t,
      (lambda s, t=t: _mono(s, t))) for t in TYPES] + [
    ("champ_one", "One and Only", "Win the Pokemon League with only one Pokemon.",
     lambda s: any(len(r.get("team") or []) == 1 for r in _league_wins(s))),
]
# (Black 2's Master and Legend ranks need 150 and 200 Medals, more than can be earned here yet: added when they can be)


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
    from src.world import feats as _feats
    _feats.note(story, "medals", len(new))   # (a Feat: Medals received)
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
