"""Nimbasa's Big Stadium and Small Court (Black 2 / White 2; Unova batch 4c, 11-24), through main's region hook
({"world": "nimbasa_sports"}, conditions "world:nimbasa_sports:<arg>"). Data: assets/b2_sports.json
(dev/builders/unova_sports.py, from Black 2's own file).

- The day's sport, by the real clock (Big Stadium: baseball Sunday / Monday / Thursday, soccer Tuesday / Friday, football
  Wednesday / Saturday; Small Court: tennis Sunday / Monday / Wednesday / Friday, basketball Tuesday / Thursday /
  Saturday). The lobby's warp panel takes you onto that field; during a game (Big Stadium 2-5 PM on baseball days, 2-4 PM
  else; Small Court 10-11 AM tennis, 10 AM-12 PM basketball) the ushers stand in front of it and the stands cheer.
- The athletes battle once a day each, their teams by your badges (tier 1: 3-4 badges; 2: 5-6, the Backers join; 3: 7-8;
  4: after the League), each with Black 2's item after a win (Potion, Super Potion, Hyper Potion; a vitamin after the
  League; the Backers give none).
- After the League: three visitors a day (Black 2's 52), on one arena's field, chosen by the date.
Events: {"enter": "stadium" | "court"} (the lobby's warp panel), {"leave": arena} (a field's), {"athlete": key},
{"visitor": id}. Conditions: "open:<arena>", "game:<arena>", "sport:<arena>:<sport>", "tier:<n>" (at least),
"athlete:<key>", "visitor:<arena>:<slot>:<id>"."""
import datetime
import json
import os
import random

AREA = "NIMBASA_CITY"
LOBBY = {"stadium": "stadium", "court": "court"}                       # (the lobbies: rooms of Nimbasa in unova.py)
PAD = (9, 8)                                                           # (the lobby's warp panel)
FIELD_ROOM = {"football": "field_football", "baseball": "field_baseball", "soccer": "field_soccer",
              "tennis": "court_tennis", "basketball": "court_basketball"}
FIELD_PAD = {"football": (9, 29), "baseball": (9, 61), "soccer": (10, 29), "tennis": (6, 25), "basketball": (6, 25)}
SPORT_WORD = {"football": "football", "baseball": "baseball", "soccer": "soccer", "tennis": "tennis", "basketball": "basketball"}
_DATA = None


def data(game=None):
    global _DATA
    if _DATA is None:
        base = getattr(getattr(game, "assets", None), "assets_dir", None) or os.path.join(os.path.dirname(__file__), "..", "..", "assets")
        with open(os.path.join(base, "b2_sports.json"), encoding="utf-8") as f:
            _DATA = json.load(f)
    return _DATA


def now():
    """The real clock (a test may set NOW)."""
    return NOW or datetime.datetime.now()


NOW = None


def sport(arena, when=None):
    when = when or now()
    return data()["schedule"][arena][when.weekday()]


def game_on(arena, when=None):
    when = when or now()
    a, b = data()["schedule"]["hours"][sport(arena, when)]
    return a <= when.hour < b


def tier(story):
    """0 before the 3rd badge, 1 with 3-4, 2 with 5-6, 3 with 7-8, 4 once you're Unova's Champion."""
    try:
        if story.is_region_champion("UNOVA"):
            return 4
    except Exception:
        pass
    n = len((getattr(story, "badges", {}) or {}).get("UNOVA", []))
    return 3 if n >= 7 else 2 if n >= 5 else 1 if n >= 3 else 0


def _athlete_entry(story, key):
    a = data()["athletes"].get(key)
    if not a:
        return None
    t = tier(story)
    return a["tiers"].get(str(t)) if t else None


def visitors_today(when=None):
    """{"arena": arena, "slots": [visitor id per slot]}: the day's three (one from each slot's group)."""
    when = when or now()
    rng = random.Random(when.date().toordinal() * 7919)
    groups = {}
    for v in data()["visitors"]:
        groups.setdefault(v["slot"], []).append(v["id"])
    return {"arena": rng.choice(["stadium", "court"]), "slots": [rng.choice(groups[s]) for s in sorted(groups)]}


def condition(story, arg):
    bits = str(arg).split(":")
    if bits[0] == "open":
        return not game_on(bits[1])
    if bits[0] == "game":
        return game_on(bits[1])
    if bits[0] == "sport":
        return sport(bits[1]) == bits[2]
    if bits[0] == "tier":
        return tier(story) >= int(bits[1])
    if bits[0] == "athlete":
        return _athlete_entry(story, ":".join(bits[1:])) is not None
    if bits[0] == "visitor":
        if tier(story) < 4:
            return False
        today = visitors_today()
        return today["arena"] == bits[1] and today["slots"][int(bits[2])] == int(bits[3])
    return False


def _put(game, room, at, face, lines=None):
    from src.world.battle_subway import _put as put
    return put(game, room, at, face, lines)


def _battle_event(game, battle, flag, lines, done):
    b = {k: v for k, v in battle.items() if k != "b2_id"}
    b["dialogue"] = {"player_won": list(done[:1])}
    return {"lines": list(lines), "battle": b, "flag": flag, "daily": True, "done": list(done[1:] or done)}


def event(state, ev, lines, show):
    game = state.game
    story = game.story_manager
    if ev.get("enter"):
        arena = ev["enter"]
        if game_on(arena):
            show(lines or ["I'm sorry, but you can't go onto the field while a game is on."])
            return
        sp = sport(arena)
        x, y = FIELD_PAD[sp]
        _put(game, FIELD_ROOM[sp], (x, y - 1), (0, -1))
        return
    if ev.get("leave"):
        arena = ev["leave"]
        _put(game, LOBBY[arena], (PAD[0], PAD[1] + 1), (0, 1))
        return
    if ev.get("athlete"):
        key = ev["athlete"]
        e = _athlete_entry(story, key)
        if e is None:
            show(lines or ["(They're busy practising.)"])
            return
        who = key.split(" ", 1)[-1]
        said = list(lines or []) or ["%s: You came to watch us practise? Then let's battle! Our Pokemon train every day!" % who]
        done = ["%s: Wow! You'd make a great player yourself!" % who,
                "%s: That was a good workout! Come back tomorrow, we'll be practising again!" % who]
        ev2 = _battle_event(game, e, "b2_sport_" + key.lower().replace(" & ", "_").replace(" ", "_"), said, done)
        from src.states.overworld.common import _run_story_event
        _run_story_event(state, ev2, lambda c: True, show)
        return
    if ev.get("visitor"):
        v = next((v for v in data()["visitors"] if v["id"] == ev["visitor"]), None)
        if v is None:
            show(["..."])
            return
        b = v["battle"]
        said = list(lines or []) or ["%s: I came to watch the athletes, but a battle with you sounds even better!" % b["name"]]
        done = ["%s: You're as good as any athlete here!" % b["name"],
                "%s: I'll be back another day. Maybe we'll meet again!" % b["name"]]
        from src.states.overworld.common import _run_story_event
        _run_story_event(state, _battle_event(game, b, "b2_sport_visitor_%d" % v["id"], said, done), lambda c: True, show)
        return
    show(lines or ["..."])
