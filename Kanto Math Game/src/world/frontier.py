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
    # Johto's Battle Frontier (HeartGold / SoulSilver; Jordan 11-16: "real streaks per facility"). The Brains' teams and moves are the
    # game file's own (a/2/0/2 trainers, a/2/0/3 sets; first print = Silver, second = Gold). Thorton (rentals) and Argenta (the Hall's
    # pool) have no fixed team in the game: a random strong one here, as for Emerald's Noland. Prints, not Symbols.
    "jtower": ("Tower Tycoon Palmer", "master.png", [464, 350, 149], [485, 488, 486], "Tower"),
    "jfactory": ("Factory Head Thorton", "master.png", None, None, "Factory"),
    "jhall": ("Hall Matron Argenta", "master.png", None, None, "Hall"),
    "jcastle": ("Castle Valet Darach", "master.png", [395, 398, 229], [395, 475, 244], "Castle"),
    "jarcade": ("Arcade Star Dahlia", "master.png", [308, 272, 477], [257, 468, 145], "Arcade"),
}
# The Johto Brains' own moves (HGSS, by species; Darach's first of his two sets for each).
BRAIN_MOVES = {
    "jtower": ({"464": ["ROCK-WRECKER", "EARTHQUAKE", "CRUNCH", "ROAR"], "350": ["SURF", "ICE-BEAM", "ATTRACT", "HYPNOSIS"],
                "149": ["DRAGON-CLAW", "AERIAL-ACE", "THUNDER-WAVE", "DRAGON-DANCE"]},
               {"485": ["MAGMA-STORM", "FLASH-CANNON", "EARTH-POWER", "EXPLOSION"], "488": ["PSYCHIC", "ICE-BEAM", "SIGNAL-BEAM", "MOONLIGHT"],
                "486": ["CRUSH-GRIP", "EARTHQUAKE", "STONE-EDGE", "DRAIN-PUNCH"]}),
    "jarcade": ({"308": ["ZEN-HEADBUTT", "REVERSAL", "ENDURE", "FAKE-OUT"], "272": ["WATERFALL", "RAZOR-LEAF", "DRAIN-PUNCH", "SWORDS-DANCE"],
                 "477": ["SHADOW-PUNCH", "FLING", "WILL-O-WISP", "TRICK-ROOM"]},
                {"257": ["FLARE-BLITZ", "SUPERPOWER", "THUNDER-PUNCH", "NIGHT-SLASH"], "468": ["HYPER-BEAM", "AIR-SLASH", "AURA-SPHERE", "PSYCHIC"],
                 "145": ["THUNDERBOLT", "AIR-CUTTER", "HEAT-WAVE", "SIGNAL-BEAM"]}),
    "jcastle": ({"395": ["WATERFALL", "METAL-CLAW", "BRICK-BREAK", "KNOCK-OFF"], "398": ["RETURN", "AERIAL-ACE", "DOUBLE-TEAM", "ROOST"],
                 "229": ["FIRE-FANG", "CRUNCH", "ROAR", "COUNTER"]},
                {"395": ["SURF", "EARTHQUAKE", "BLIZZARD", "SIGNAL-BEAM"], "475": ["PSYCHO-CUT", "STONE-EDGE", "AERIAL-ACE", "X-SCISSOR"],
                 "244": ["FIRE-BLAST", "SOLAR-BEAM", "HYPER-BEAM", "SUNNY-DAY"]}),
}
# The Gen IV Brains' held items, in team order (Silver team, Gold team): Serebii's Pokearth Battle Frontier page for Platinum
# (sources/sinnoh, Jordan 11-22); HGSS's Brains are the same people with the same sets.
BRAIN_HELD = {
    "jtower": (["FOCUS_BAND", "SHELL_BELL", "LUM_BERRY"], ["FOCUS_SASH", "LEFTOVERS", "BRIGHT_POWDER"]),
    "jcastle": (["RAZOR_CLAW", "KINGS_ROCK", "FOCUS_SASH"], ["QUICK_CLAW", "SCOPE_LENS", "SHUCA_BERRY"]),
    "jarcade": (["SALAC_BERRY", "MUSCLE_BAND", "IRON_BALL"], ["WHITE_HERB", "EXPERT_BELT", "BRIGHT_POWDER"]),
}
JOHTO_FIVE = ["jtower", "jfactory", "jhall", "jcastle", "jarcade"]
# Sinnoh's Battle Frontier (Platinum; Jordan 11-22: "that is the next place to build"): the same five facilities and Brains as
# HeartGold / SoulSilver's (HGSS reused Platinum's Frontier: the same map, D32, its rooms tile for tile), its own streaks and Prints.
SINNOH_FIVE = ["stower", "sfactory", "shall", "scastle", "sarcade"]
for _j, _s in zip(JOHTO_FIVE, SINNOH_FIVE):
    BRAINS[_s] = BRAINS[_j]
    if _j in BRAIN_MOVES:
        BRAIN_MOVES[_s] = BRAIN_MOVES[_j]
    if _j in BRAIN_HELD:
        BRAIN_HELD[_s] = BRAIN_HELD[_j]
GEN4 = set(JOHTO_FIVE) | set(SINNOH_FIVE)   # (Gen IV's facilities: its own trainers, Prints not Symbols)
FRONTIER_SEVEN = [f for f in BRAINS if f != "maison" and f not in GEN4]   # (the Symbols: the Maison gives none of its own)
NAMES = {"tower": "Battle Tower", "dome": "Battle Dome", "palace": "Battle Palace", "arena": "Battle Arena",
         "factory": "Battle Factory", "pike": "Battle Pike", "pyramid": "Battle Pyramid", "maison": "Battle Maison",
         "jtower": "Battle Tower", "jfactory": "Battle Factory", "jhall": "Battle Hall", "jcastle": "Battle Castle", "jarcade": "Battle Arcade",
         "stower": "Battle Tower", "sfactory": "Battle Factory", "shall": "Battle Hall", "scastle": "Battle Castle", "sarcade": "Battle Arcade"}
# Orre's Battle Tower (the fan game Pokemon Orre 2.1.1's, after Orre's League - Jordan 11-24, questions/ORRE.md 10b: "all
# three"): no Brain, an endless streak each, its best kept. "otower" single battles (three Pokemon a side, Lv 50); "otower2"
# 2-on-2 double battles (exactly two Pokemon); "olc" the Little Cup (three unevolved Pokemon that can still evolve, Lv 5 or
# under; the tower's seller has some for BP - src/world/orre_frontier.py). Emerald's Frontier trainers, Gen 3 Pokemon.
ENDLESS = {"otower": (3, 50, False), "otower2": (2, 50, True), "olc": (3, 5, False)}   # facility: (team size, level, double)
NAMES.update({"otower": "Battle Tower", "otower2": "Battle Tower's 2-on-2", "olc": "Battle Tower's Little Cup"})
_LC = None


def lc_pool(game):
    """The Little Cup's Pokemon: Gen 3 and earlier, the first of a line that still evolves by level (no legends, no babies
    that only evolve by friendship)."""
    global _LC
    if _LC is None:
        with open(os.path.join(game.assets.assets_dir, "pokemon_levels.json"), encoding="utf-8") as f:
            lv = json.load(f)
        pairs = [tuple(int(x) for x in k.split(">")) + (v,) for k, v in lv["pairs"].items()]
        later = {b for a, b, _v in pairs}
        _LC = sorted({a for a, b, v in pairs if a <= 386 and b <= 386 and a not in later and isinstance(v, dict) and v.get("level")})
    return _LC


def best(game, fac):
    return int(_flags(game).get(f"frontier_{fac}_best", 0) or 0)


def rule_problem(game, fac):
    """Why your party can't enter this facility (lines), else None."""
    if fac not in ENDLESS:
        return None
    team = [p for p in game.story_manager.player_team if p is not None and not getattr(p, "is_egg", False)]
    if fac == "otower2" and len(team) != 2:
        return ["The 2-on-2 challenge takes exactly two Pokemon. Leave the rest in the PC, then come back."]
    if fac == "olc":
        pool = set(lc_pool(game))
        bad = [p for p in team if int(p.level) > 5 or int(getattr(p, "id", 0)) not in pool]
        if len(team) != 3 or bad:
            return ["The Little Cup takes exactly three Pokemon, each Lv 5 or under and not yet evolved - ones that can still evolve.",
                    "The seller here has some for Battle Points."]
    return None


_DATA = None
_DATA4 = None


def data4(game):
    """Platinum / HeartGold / SoulSilver's own Frontier trainers (assets/frontier_gen4.json: 300, none repeating Emerald's;
    Jordan 11-22: "add the missing frontier trainers from johto"). Johto's facilities draw from these."""
    global _DATA4
    if _DATA4 is None:
        with open(os.path.join(game.assets.assets_dir, "frontier_gen4.json"), encoding="utf-8") as f:
            _DATA4 = json.load(f)
    return _DATA4


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
    """Wins needed before the Brain: 5 the first time, 10 after the Silver Symbol. (Orre's endless streaks: no Brain.)"""
    if fac in ENDLESS:
        return 10 ** 9
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
    if fac in ENDLESS:   # (Orre's Battle Tower: Emerald's trainers; the Little Cup's from its own pool)
        n, lvl, double = ENDLESS[fac]
        t = random.choice(data(game)["trainers"])
        cls = t["class"].rstrip("♂♀")
        w = wins(game, fac)
        team = random.sample(lc_pool(game), n) if fac == "olc" else _team(game, [2, 3] if w < 10 else [3], n)
        info = {"name": f"{cls} {t['name']}", "class": cls.upper().replace(" ", "_").replace("É", "E").replace("é", "E"),
                "sprite": t["sprite"], "team": team, "levels": [lvl] * len(team)}
        if double:
            info["double"] = True
        return info
    if brain_next(game, fac):
        title, sprite, silver, gold, _sym = BRAINS[fac]
        is_gold = bool(_flags(game).get(f"frontier_{fac}_silver"))
        team = (gold if is_gold else silver) or _team(game, [3])
        info = {"name": title, "class": "FRONTIER_BRAIN", "sprite": sprite, "team": list(team),
                "is_boss_battle": True, "rewards": {"balls": 5}}
        if fac in BRAIN_MOVES:
            info["movesets"] = dict(BRAIN_MOVES[fac][1 if is_gold else 0])
        if fac in BRAIN_HELD:   # (their held items, by team slot)
            info["held"] = list(BRAIN_HELD[fac][1 if is_gold else 0])
        return info
    w = wins(game, fac)
    col = min(7, w // 7)   # (Emerald's columns: battles 1-7, 8-14, ... who may appear)
    pool = data4(game)["trainers"] if fac in GEN4 else data(game)["trainers"]   # (Johto and Sinnoh: Gen IV's own trainers)
    trainers = [t for t in pool if col in t["cols"]] or pool
    t = random.choice(trainers)
    cls = t["class"].rstrip("♂♀")
    return {"name": f"{cls} {t['name']}", "class": cls.upper().replace(" ", "_").replace("É", "E").replace("é", "E"),
            "sprite": t["sprite"], "team": _team(game, _groups(game, fac))}


def intro_lines(game, fac):
    """The attendant's words before a battle."""
    w, g = wins(game, fac), goal(game, fac)
    name = NAMES[fac]
    if fac in ENDLESS:
        if w == 0:
            return [f"Welcome to the {name}! Win as many battles in a row as you can - the streak never ends until you lose.",
                    f"Your best so far: {best(game, fac)}. Your team will be healed before every battle. Here comes your first opponent!"]
        return [f"Your streak: {w} win{'s' if w != 1 else ''} (best {best(game, fac)}). Your team has been healed. Here comes the next!"]
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
    from src.world import battle_points as _bp   # (Battle Points for every win, more for a Brain: 11-22)
    if fac in ENDLESS:   # (Orre's Battle Tower: no Brain; the best streak kept)
        flags[key] = wins(game, fac) + 1
        flags[f"frontier_{fac}_best"] = max(best(game, fac), wins(game, fac))
        got = _bp.add_bp(game.story_manager, _bp.WIN_BP)
        return [f"You earned {got} BP! You have {_bp.bp(game.story_manager)} BP."] if got else []
    if not brain_next(game, fac):
        flags[key] = wins(game, fac) + 1
        got = _bp.add_bp(game.story_manager, _bp.WIN_BP)
        return [f"You earned {got} BP! You have {_bp.bp(game.story_manager)} BP."] if got else []
    flags[key] = 0
    title, _s, _a, _b, sym = BRAINS[fac]
    first = not flags.get(f"frontier_{fac}_silver")
    _bp.add_bp(game.story_manager, _bp.BRAIN_BP if first else _bp.BRAIN_GOLD_BP)
    flags[f"frontier_{fac}_silver" if first else f"frontier_{fac}_gold"] = True
    _mark = "Print" if fac in GEN4 else "Symbol"   # (Platinum / HGSS: Prints)
    lines = [f"You beat {title}! You earned the {'Silver' if first else 'Gold'} {sym} {_mark}!"] if fac != "maison" else         [f"You beat {title}! Your name goes up on the Maison's wall of {'champions' if first else 'grand champions'}!"]
    lines.append(f"You earned {_bp.BRAIN_BP if first else _bp.BRAIN_GOLD_BP} BP! You have {_bp.bp(game.story_manager)} BP.")
    if first:
        lines.append(f"Next time it's {AGAIN} wins in a row for a battle with the {'Chatelaine' if fac == 'maison' else 'Brain'}'s real team.")
    if fac.startswith("j") and all(flags.get(f"frontier_{f}_silver") for f in JOHTO_FIVE) and not flags.get("johto_battle_frontier_cleared"):
        flags["johto_battle_frontier_cleared"] = True
        lines.append("You hold a Silver Print from every facility in the Battle Frontier!")
    if fac in SINNOH_FIVE and all(flags.get(f"frontier_{f}_silver") for f in SINNOH_FIVE) and not flags.get("sinnoh_battle_frontier_cleared"):
        flags["sinnoh_battle_frontier_cleared"] = True
        lines.append("You hold a Silver Print from every facility in the Battle Frontier!")
    if fac not in GEN4 and all(flags.get(f"frontier_{f}_silver") for f in FRONTIER_SEVEN) and not flags.get("hoenn_battle_frontier_cleared"):
        flags["hoenn_battle_frontier_cleared"] = True
        lines.append("You hold a Symbol from every facility in the Battle Frontier!")
    return lines


def symbols(game):
    """[(facility, 'gold' / 'silver' / None)] for the record."""
    f = _flags(game)
    return [(fac, "gold" if f.get(f"frontier_{fac}_gold") else "silver" if f.get(f"frontier_{fac}_silver") else None)
            for fac in FRONTIER_SEVEN]
