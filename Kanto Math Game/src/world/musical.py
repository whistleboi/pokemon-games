"""Nimbasa's Pokemon Musical (Black 2 / White 2; Unova batch 4c, 11-24), through main's region hook ({"world": "musical"},
conditions "world:musical:<arg>"). The show itself is src/states/musical.py; the props and shows assets/b2_musical.json
(kanto_handoff/unova_map_tools/musical.py, from Black 2's own file).

Kept in the story flags: b2_props (the Prop Case: prop numbers), b2_musical_shows / _wins / _score (the Dress Up and
spotlight points added up: they bring the fans), b2_musical_fans (after a show, each waiting fan's Prop: a number, or
-1 once given), b2_musical_last (the last show: its name, your place, your look).
Jordan's calls (11-24): fans come about 20 shows in (Black 2's steps x 0.2); the Toy Cake after the first show.
Events: {"case": true} (the owner's Prop Case), {"join": true} (the receptionist: a show), {"owner": true} (his gifts:
the Toy Cake after the first show, the Crown at 5 wins, the Winner's Belt at 10), {"rival": true} (the rival stylist's
notes on your last show), {"fan": k}. Condition: "fan:<k>" (that fan is waiting)."""
import json
import os
import random

START_PROPS = [59, 1, 8, 76, 48, 70]   # (zone 606's lines: Top Hat, Blue Barrette, Square Glasses, Maraca, Umber Belt, Tie)
FAN_STEPS = [0, 20, 50, 100, 200, 400, 700, 1100, 1600, 2400]   # (Black 2's 0 / 100 / 250 ... 12,000, x 0.2: Jordan 11-24)
SPECIAL = {24, 55, 67, 82, 95, 96, 98, 99}   # (given by people, not fans: Toy Cake, Crown, Tiara, Winner's Belt and the Opelucid
#  gentleman's four. The Electric Guitar comes from a fan: Black and White's Musician Preston isn't on Black 2's Route 5)
TOY_CAKE, CROWN, WINNERS_BELT = 24, 55, 82
_DATA = None


def data(game=None):
    global _DATA
    if _DATA is None:
        base = getattr(getattr(game, "assets", None), "assets_dir", None) or os.path.join(os.path.dirname(__file__), "..", "..", "assets")
        with open(os.path.join(base, "b2_musical.json"), encoding="utf-8") as f:
            _DATA = json.load(f)
    return _DATA


def _flags(game):
    return game.story_manager.story_flags


def props(game):
    return sorted(set(_flags(game).get("b2_props") or []))


def give_prop(game, pid):
    f = _flags(game)
    have = set(f.get("b2_props") or [])
    have.add(int(pid))
    f["b2_props"] = sorted(have)


def prop_name(pid):
    return data()["props"][int(pid)]["name"]


def fan_count(score):
    return sum(1 for s in FAN_STEPS if score >= s)


def can_dress(mon):
    return mon is not None and not getattr(mon, "is_egg", False)


def condition(story, arg):
    if arg.startswith("fan:"):
        k = int(arg[4:])
        fans = story.story_flags.get("b2_musical_fans") or []
        return k < len(fans)
    return False


def after_show(game, result):
    """The show's end (src/states/musical.py): counts, points, the fans who'll wait in the lobby. Lines to say."""
    f = _flags(game)
    f["b2_musical_shows"] = int(f.get("b2_musical_shows", 0) or 0) + 1
    if result.get("place") == 1:
        f["b2_musical_wins"] = int(f.get("b2_musical_wins", 0) or 0) + 1
    f["b2_musical_score"] = int(f.get("b2_musical_score", 0) or 0) + int(result.get("points", 0))
    n = fan_count(f["b2_musical_score"])
    kind = result.get("kind")
    have = set(props(game))
    pool = [p["id"] for p in data()["props"] if p["id"] not in have and p["id"] not in SPECIAL]
    rng = random.Random()
    fans = []
    for _ in range(n):
        mine = [p for p in pool if data()["props"][p]["kind"] == kind] or pool
        pick = rng.choice(mine) if mine else -1
        if pick in pool:
            pool.remove(pick)
        fans.append(pick)
    f["b2_musical_fans"] = fans
    f["b2_musical_last"] = {"show": result.get("show"), "place": result.get("place"), "look": result.get("look"),
                            "accent": result.get("accent"), "weak": result.get("weak")}
    said = ["%d fan%s waiting for you in the lobby!" % (n, "" if n == 1 else "s")] if n else []
    return said


def event(state, ev, lines, show):
    game = state.game
    f = _flags(game)
    from src.states.overworld.common import _say_then, _resolve_lines
    _show = show
    show = lambda ls: _show(_resolve_lines(game, list(ls)))   # (names in the lines: {player_name})
    if ev.get("case"):
        if not f.get("b2_props"):
            f["b2_props"] = list(START_PROPS)
        f["b2_prop_case"] = True
        if lines:
            show(lines)
        return
    if ev.get("join"):
        if not f.get("b2_prop_case"):
            show(["Receptionist: Welcome to the Musical Theater! Please talk to the owner first."])
            return
        team = [p for p in game.story_manager.player_team if can_dress(p)]
        if not team:
            show(["Receptionist: You need a Pokemon to take part in the Musical!"])
            return
        said = list(lines or []) + ["Receptionist: Welcome to the Pokemon Musical! Pick a Pokemon and a show, dress it up "
                                    "with your Props, and dance on stage!"]

        def start():
            from src.states.musical import MusicalState
            game.change_state(MusicalState(game, state, then=lambda out: show(out)))
        _say_then(state, said, start)
        return
    if ev.get("owner"):
        shows, wins = int(f.get("b2_musical_shows", 0) or 0), int(f.get("b2_musical_wins", 0) or 0)
        for pid, flag, need, said in (
                (TOY_CAKE, "b2_musical_cake", shows >= 1,
                 ["Owner: Your first Musical! A celebration is in order. Here's a festive Prop from me, the owner!",
                  "It's a Toy Cake. It's a Prop, so put it on your Pokemon. Don't eat it!",
                  "Why a cake today? Because I'm the owner!"]),
                (CROWN, "b2_musical_crown", wins >= 5,
                 ["Owner: Your shows make me a happy owner! People are calling you a rising stylist.",
                  "Please accept this as a token of my thanks!"]),
                (WINNERS_BELT, "b2_musical_belt", wins >= 10,
                 ["Owner: Some in the audience call you a top stylist now! And who spotted your talent first? Me!",
                  "Please accept this as a token of my gratitude!"])):
            if need and not f.get(flag):
                f[flag] = True
                give_prop(game, pid)
                show(said + ["{player_name} received the %s!" % prop_name(pid)])
                return
        show(["Owner: I want Pokemon to look more glamorous than ever, so I study how everyone plays Dress Up.",
              "I hope to see you on stage again!"] if shows else
             ["Owner: If you have a Pokemon that can play Dress Up, join a Musical! The receptionist will help you."])
        return
    if ev.get("rival"):
        last = f.get("b2_musical_last")
        if not last:
            show(["Stylist: I'm going to be the Musical's top stylist! Let's see what you can do."])
            return
        said = ["Stylist: Nice work! I saw your Pokemon up there. Overall, totally %s!" % (last.get("look") or "balanced")]
        if last.get("accent"):
            said.append("The %s was a great accent." % last["accent"])
        if last.get("weak"):
            said.append("But your %s side was a bit quiet today." % last["weak"])
        said.append("OK! I'm not going to lose!")
        show(said)
        return
    if "fan" in ev:
        k = int(ev["fan"])
        fans = f.get("b2_musical_fans") or []
        if k >= len(fans):
            show(["..."])
            return
        pid = fans[k]
        if pid is None or pid < 0:
            show(["Fan: I'll be cheering for you at the next show!"])
            return
        give_prop(game, pid)
        fans[k] = -1
        f["b2_musical_fans"] = fans
        show(["Fan: Your Pokemon was wonderful on stage! I'm a fan now!",
              "Here, I want you to have this!", "{player_name} received the %s!" % prop_name(pid)])
        return
    show(lines or ["..."])
