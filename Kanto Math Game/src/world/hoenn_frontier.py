"""Hoenn's Battle Frontier: Emerald's people with something to do (Jordan 11-24, questions/HOENN.md 15: "all five, plus the
info people"; read from Emerald's own scripts, hoenn_rom_tools/hscript.py on its 48 Frontier maps). The map's events are
{"world": "hoenn_frontier", ...}:
  {"scott": true}    Scott, in his house (26.46): Battle Points on your first visit (Emerald gives 1 to 4 by how often you met
                     him on your journey; there is no Scott in Omega Ruby / Alpha Sapphire's story, so 1); a Lansat Berry once
                     you hold all seven Silver Symbols, a Starf Berry for all seven Gold ones.
  {"bet": true}      the gambler in the lounge (26.44): he names a facility; spot him 5, 10 or 15 BP, win five battles there in a
                     row (with no loss in between) and he pays you back double. A loss there and the bet is gone.
  {"news": true}     the Frontier's news man (26.43): today's busiest facility.
  {"records": true}  the Ranking Hall (26.40): your best streak and Symbol in each facility.
  {"multi": true}    the Battle Tower's Multi Battle Room counter (26.5): pick a partner of eight (each with two Pokemon you see
                     first), then the Multi streak (src/world/frontier.py "tower_multi").
The streak records used here are frontier.py's: "frontier_<fac>_run" (wins in a row, a Brain's battle included),
"frontier_<fac>_best", "frontier_<fac>_won" / "_lost" (all-time counts)."""
import datetime
import random

SEVEN = ["tower", "dome", "palace", "arena", "factory", "pike", "pyramid"]
BET_WINS = 5
BETS = (5, 10, 15)
# The Multi room's eight partners (Emerald's room holds eight Trainers to pick from): eight of its own Frontier Trainers.
PARTNERS = [("Cooltrainer", "Braden", "acetrainer_m.png"), ("Cooltrainer", "Julia", "acetrainer_f.png"),
            ("Black Belt", "Hitomi", "blackbelt.png"), ("Battle Girl", "Joana", "battle_girl.png"),
            ("Psychic", "Kaitlyn", "psychic.png"), ("Gentleman", "Marvin", "gentleman.png"),
            ("Dragon Tamer", "Roberto", "dragon_tamer.png"), ("Expert", "Kristen", "veteranf.png")]


def condition(story, arg):
    return False


def _flags(game):
    return game.story_manager.story_flags


def partner_info(game):
    """The partner you picked at the Multi counter, as a trainer (their two Pokemon as they told you)."""
    got = _flags(game).get("frontier_multi_partner") or {}
    i = int(got.get("i", 0)) % len(PARTNERS)
    cls, name, sprite = PARTNERS[i]
    return {"name": f"{cls} {name}", "class": cls.upper().replace(" ", "_"), "sprite": sprite, "team": list(got.get("team") or [])}


def _name(game, pid):
    try:
        return game.loader.fetch_specific(int(pid)).get("name", str(pid)).title()
    except Exception:
        return str(pid)


def event(state, ev, lines, show):
    game = state.game
    f = _flags(game)
    from src.world import frontier, battle_points as bp
    from src.states.overworld.common import _say_then
    from src.states.systems.pick_list import PickListState
    if ev.get("scott"):
        said = list(lines or [])
        story = game.story_manager
        if not f.get("scott_frontier_welcome"):
            f["scott_frontier_welcome"] = True
            got = bp.add_bp(story, 1)
            said += ["Scott: Every Trainer leads a life of their own. But when they battle, they all shine the same way.",
                     "Scott: You came all this way to my Frontier! Please, take this as my thanks.",
                     f"You received {got} BP from Scott! You have {bp.bp(story)} BP."]
        if all(f.get(f"frontier_{x}_silver") for x in SEVEN) and not f.get("got_scott_lansat"):
            f["got_scott_lansat"] = True
            story.add_item("LANSAT_BERRY")
            said += ["Scott: All seven Silver Symbols! I knew I had the eye for a good Trainer.", "You received a LANSAT BERRY!"]
        if all(f.get(f"frontier_{x}_gold") for x in SEVEN) and not f.get("got_scott_starf"):
            f["got_scott_starf"] = True
            story.add_item("STARF_BERRY")
            said += ["Scott: Seven Gold Symbols... Nobody has ever done that. I'll be hearing great things about you!",
                     "You received a STARF BERRY!"]
        if len(said) == len(lines or []):
            said.append("Scott: I'm expecting great things from you! Win a Symbol in every facility, and come and tell me.")
        return show(said)
    if ev.get("bet"):
        return _bet(state, f, show, _say_then, PickListState)
    if ev.get("news"):
        day = datetime.date.today().toordinal()
        hot = random.Random(day).choice(SEVEN)
        return show(list(lines or []) + [f"News man: Let's see now... It sounds like the {frontier.NAMES[hot]} is the hottest place going today!",
                                         "News man: Come back tomorrow for the latest word!"])
    if ev.get("records"):
        said = list(lines or [])
        for x in SEVEN + ["tower_double", "tower_multi"]:
            sym = "Gold Symbol" if f.get(f"frontier_{x}_gold") else "Silver Symbol" if f.get(f"frontier_{x}_silver") else None
            best = max(int(f.get(f"frontier_{x}_best", 0) or 0), frontier.best(game, x))
            said.append(f"{frontier.NAMES[x]}: best streak {best}" + (f", {sym}." if sym else "."))
        return show(said)
    if ev.get("multi"):
        return _multi(state, f, lines, show, _say_then, PickListState)
    show(lines or ["..."])


def _bet(state, f, show, _say_then, PickListState):
    game = state.game
    from src.world import frontier, battle_points as bp
    story = game.story_manager
    b = f.get("frontier_bet")
    if b:
        fac = b["fac"]
        won = int(f.get(f"frontier_{fac}_won", 0) or 0) - int(b["won"])
        if int(f.get(f"frontier_{fac}_lost", 0) or 0) != int(b["lost"]):
            f.pop("frontier_bet", None)
            return show([f"Gambler: You lost in the {frontier.NAMES[fac]}? Aww, I backed the wrong Trainer again!",
                         f"Gambler: Those {b['bp']} BP are gone, kid. Want to try again?"])
        if won >= BET_WINS:
            f.pop("frontier_bet", None)
            got = bp.add_bp(story, 2 * int(b["bp"]))
            return show([f"Gambler: {BET_WINS} wins in a row in the {frontier.NAMES[fac]}! I knew it!",
                         f"Gambler: Here's your cut: double! You received {got} BP. You have {bp.bp(story)} BP."])
        return show([f"Gambler: The {frontier.NAMES[fac]}, remember? Win {BET_WINS} battles in a row there - {max(0, BET_WINS - won)} to go!"])
    fac = random.choice(SEVEN)
    have = bp.bp(story)
    rows = [(f"{n} BP", n) for n in BETS if n <= have]
    said = ["Gambler: Heheh... You look like a tough Trainer. I've got a proposition.",
            f"Gambler: Win {BET_WINS} battles in a row in the {frontier.NAMES[fac]} for me. Spot me some BP, and if you do it, I pay you back double!"]
    if not rows:
        return show(said + [f"Gambler: You've only got {have} BP? Come back with at least {BETS[0]}."])

    def chose(n):
        if n is None:
            return show(["Gambler: Suit yourself. I know a winner when I see one, though!"])
        bp.add_bp(story, -int(n))
        f["frontier_bet"] = {"fac": fac, "bp": int(n), "won": int(f.get(f"frontier_{fac}_won", 0) or 0),
                             "lost": int(f.get(f"frontier_{fac}_lost", 0) or 0)}
        show([f"Gambler: {n} BP on you in the {frontier.NAMES[fac]}! Don't let me down!"])
    _say_then(state, said, lambda: game.change_state(PickListState(game, state, "HOW MUCH?", rows, chose)))


def _multi(state, f, lines, show, _say_then, PickListState):
    game = state.game
    from src.world import frontier
    rows, teams = [], {}
    for i, (cls, name, _s) in enumerate(PARTNERS):
        team = frontier._team(game, [2, 3], 2)
        teams[i] = team
        rows.append((f"{cls} {name}: {' & '.join(_name(game, p) for p in team)}", i))
    said = list(lines or []) + ["Attendant: Welcome to the Multi Battle Room! You and a partner take on two Trainers at once.",
                                "Attendant: These Trainers are looking for a partner. Who will you team up with?"]

    def chose(i):
        if i is None:
            return show(["Attendant: Please come back when you're ready."])
        f["frontier_multi_partner"] = {"i": i, "team": teams[i]}
        cls, name, _s = PARTNERS[i]
        go = getattr(state, "action_frontier", None)
        _say_then(state, [f"{cls} {name}: Let's do this together!"], lambda: go({"facility": "tower_multi"}) if go else show(["..."]))
    _say_then(state, said, lambda: game.change_state(PickListState(game, state, "PICK A PARTNER", rows, chose)))
