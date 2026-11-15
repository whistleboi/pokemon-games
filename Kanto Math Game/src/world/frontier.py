"""Hoenn's Battle Frontier (Emerald), made simple (Jordan, 11-14): each of the seven facilities is a streak of
single trainer battles against random Frontier trainers with random Frontier Pokemon (Emerald's own lists:
assets/frontier_gen3.json, from Bulbapedia), then the facility's Frontier Brain.
- First challenge: 5 wins in a row, then the Brain (the Silver Symbol).
- After that: 10 wins in a row, then the Brain's stronger team (the Gold Symbol). Again after that: 10 and the Gold team.
  (Jordan, 11-14: shorter streaks, "more realistic for kids": intervals of 5.)
- A loss ends the streak (no whiting out: the team is healed and you're back in the lobby).
- The team is healed before every battle of a streak, as the Frontier does.
The streak's count is a story flag, "frontier_<facility>_wins"; the Symbols "frontier_<facility>_silver" / "_gold".
All seven Silver Symbols: hoenn_battle_frontier_cleared (the Journal's Battle Frontier mission)."""
import json
import os
import random

FIRST, AGAIN = 5, 10

# facility: (its Brain's title and name, sprite, Silver team, Gold team (Emerald's), the Symbol's name)
# The Factory's Head Noland battles with rental Pokemon in Emerald: here his team is three random strong ones.
BRAINS = {
    "tower": ("Salon Maiden Anabel", "acetrainer_f.png", [65, 244, 143], [243, 381, 143], "Ability"),
    "dome": ("Dome Ace Tucker", "acetrainer_m.png", [260, 373, 6], [373, 376, 380], "Tactics"),
    "palace": ("Palace Maven Spenser", "acetrainer_m.png", [169, 289, 131], [245, 94, 289], "Spirits"),
    "arena": ("Arena Tycoon Greta", "acetrainer_f.png", [214, 197, 292], [197, 94, 286], "Guts"),
    "factory": ("Factory Head Noland", "acetrainer_m.png", None, None, "Knowledge"),
    "pike": ("Pike Queen Lucy", "acetrainer_f.png", [336, 350, 213], [130, 208, 350], "Luck"),
    "pyramid": ("Pyramid King Brandon", "acetrainer_m.png", [377, 378, 379], [243, 244, 245], "Brave"),
    # the Battle Maison (Omega Ruby / Alpha Sapphire's, from the Battle Resort: Jordan 11-14, in Emerald's Battle Tent):
    # its singles Chatelaine, Nita; her teams kept to Hoenn's Gen 1-3 Pokemon (Jordan: Gen 3 or earlier for Hoenn)
    "maison": ("Chatelaine Nita", "lady.png", [36, 282, 350], [282, 376, 373], "Maison"),
}
FRONTIER_SEVEN = [f for f in BRAINS if f != "maison"]   # (the Symbols: the Maison gives none of its own)
NAMES = {"tower": "Battle Tower", "dome": "Battle Dome", "palace": "Battle Palace", "arena": "Battle Arena",
         "factory": "Battle Factory", "pike": "Battle Pike", "pyramid": "Battle Pyramid", "maison": "Battle Maison"}
_DATA = None


def data(game):
    global _DATA
    if _DATA is None:
        with open(os.path.join(game.assets.assets_dir, "frontier_gen3.json"), encoding="utf-8") as f:
            _DATA = json.load(f)
    return _DATA


def _flags(game):
    return game.story_manager.story_flags


def wins(game, fac):
    return int(_flags(game).get(f"frontier_{fac}_wins", 0) or 0)


def goal(game, fac):
    """Wins needed before the Brain: 5 the first time, 10 after the Silver Symbol."""
    return AGAIN if _flags(game).get(f"frontier_{fac}_silver") else FIRST


def brain_next(game, fac):
    return wins(game, fac) >= goal(game, fac)


def _team(game, groups, n=3):
    pool = [i for g in groups for i in data(game)["groups"].get(str(g), [])]
    team = []
    while len(team) < n and pool:
        pid = random.choice(pool)
        pool = [i for i in pool if i != pid]
        team.append(pid)
    return team


def _groups(game, fac):
    """Stronger Pokemon as the streak goes on (Emerald's groups: 0 the weakest, 3 the strongest)."""
    w, g = wins(game, fac), goal(game, fac)
    if g == FIRST:
        return [0, 1] if w < 2 else [1, 2] if w < 4 else [2, 3]
    return [2, 3] if w < 5 else [3]


def next_trainer(game, fac):
    """The next opponent's trainer info (as a trainer_pool entry): a random Frontier trainer, or the Brain."""
    if brain_next(game, fac):
        title, sprite, silver, gold, _sym = BRAINS[fac]
        team = (gold if _flags(game).get(f"frontier_{fac}_silver") else silver) or _team(game, [3])
        return {"name": title, "class": "FRONTIER_BRAIN", "sprite": sprite, "team": list(team),
                "is_boss_battle": True, "rewards": {"balls": 5}}
    w = wins(game, fac)
    col = min(7, w // 7)   # (Emerald's columns: battles 1-7, 8-14, ... who may appear)
    trainers = [t for t in data(game)["trainers"] if col in t["cols"]] or data(game)["trainers"]
    t = random.choice(trainers)
    cls = t["class"].rstrip("♂♀")
    return {"name": f"{cls} {t['name']}", "class": cls.upper().replace(" ", "_").replace("É", "E"),
            "sprite": t["sprite"], "team": _team(game, _groups(game, fac))}


def intro_lines(game, fac):
    """The attendant's words before a battle."""
    w, g = wins(game, fac), goal(game, fac)
    name = NAMES[fac]
    if brain_next(game, fac):
        if fac == "maison":
            return [f"{w} wins in a row! The Chatelaine herself, {BRAINS[fac][0]}, will battle you!"]
        return [f"{w} wins in a row! The {name}'s Frontier Brain, {BRAINS[fac][0]}, wants to battle you!"]
    if w == 0 and fac == "maison":
        return [f"Welcome to the Battle Maison! Win {g} single battles in a row and the Chatelaine will battle you.",
                "Your team will be healed before every battle. This way to the battle room!"]
    if w == 0:
        return [f"Welcome to the {name}! Win {g} battles in a row to face its Frontier Brain.",
                "Your team will be healed before every battle. Here comes your first opponent!"]
    return [f"Your streak: {w} win{'s' if w != 1 else ''}. Battle {w + 1} of {g}. Your team has been healed. Good luck!"]


def heal(game):
    for p in game.story_manager.player_team:
        if p is not None:
            p.heal_full()


def after_battle(game, fac, won):
    """A streak battle's end. Returns lines to show back in the lobby (or [])."""
    flags = _flags(game)
    key = f"frontier_{fac}_wins"
    if not won:
        w = wins(game, fac)
        flags[key] = 0
        heal(game)
        return [f"Your streak ended at {w} win{'s' if w != 1 else ''}. Your team was healed. Try again any time!"]
    if not brain_next(game, fac):
        flags[key] = wins(game, fac) + 1
        return []
    flags[key] = 0
    title, _s, _a, _b, sym = BRAINS[fac]
    first = not flags.get(f"frontier_{fac}_silver")
    flags[f"frontier_{fac}_silver" if first else f"frontier_{fac}_gold"] = True
    lines = [f"You beat {title}! You earned the {'Silver' if first else 'Gold'} {sym} Symbol!"] if fac != "maison" else         [f"You beat {title}! Your name goes up on the Maison's wall of {'champions' if first else 'grand champions'}!"]
    if first:
        lines.append(f"Next time it's {AGAIN} wins in a row for a battle with the {'Chatelaine' if fac == 'maison' else 'Brain'}'s real team.")
    if all(flags.get(f"frontier_{f}_silver") for f in FRONTIER_SEVEN) and not flags.get("hoenn_battle_frontier_cleared"):
        flags["hoenn_battle_frontier_cleared"] = True
        lines.append("You hold a Symbol from every facility in the Battle Frontier!")
    return lines


def symbols(game):
    """[(facility, 'gold' / 'silver' / None)] for the record."""
    f = _flags(game)
    return [(fac, "gold" if f.get(f"frontier_{fac}_gold") else "silver" if f.get(f"frontier_{fac}_silver") else None)
            for fac in FRONTIER_SEVEN]
