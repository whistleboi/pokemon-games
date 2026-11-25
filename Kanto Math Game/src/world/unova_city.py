"""Black City and White Forest (Unova batch 11b, 11-25): which of the two stands between Route 14's and Route 15's Black
Gates, and how far you've climbed its tower.

Jordan 11-19: the two swap after each League win. Your version's place stands first (Black 2: Black City, White 2: White
Forest); after your second win in Unova's Hall of Fame the other one stands, after your third yours again, and so on (each
win is a record in story flag "hall_of_fame_records", region UNOVA).

Each tower keeps its own progress: story flag "b2_tower" {"BLACK": {"cleared": areas cleared, best ever}, "WHITE": {...}}.
Conditions (map and event conditions "world:unova_city:<arg>"):
  white                 White Forest stands now (else Black City)
  cleared:<T>:<n>       tower T (BLACK / WHITE) has had at least n Areas cleared
The tower itself (its Areas, trainers and prizes) is src/world/black_tower.py."""


def _wins(story):
    return sum(1 for r in (story.story_flags.get("hall_of_fame_records") or [])
               if isinstance(r, dict) and str(r.get("region", "")).upper() == "UNOVA")


def white(story):
    """White Forest stands now?"""
    mine = str(story.story_flags.get("unova_version") or "BLACK_2").upper() == "WHITE_2"
    swaps = max(0, _wins(story) - 1)
    return mine != (swaps % 2 == 1)


def tower(story, which):
    t = story.story_flags.setdefault("b2_tower", {})
    return t.setdefault(which, {"cleared": 0})


def cleared(story, which):
    return int(((story.story_flags.get("b2_tower") or {}).get(which) or {}).get("cleared", 0) or 0)


def event(state, ev, lines, show):
    """{"monthly": flag, "battle": {...}, "lines": [...], "done": [...]}: a battle once a month by the real clock (N's
    seasonal rematch in his castle, Black 2: a team that changes with the season, once a month)."""
    import datetime
    story = state.game.story_manager
    if ev.get("monthly"):
        month = datetime.date.today().strftime("%Y-%m")
        if story.story_flags.get(ev["monthly"]) == month:
            show(ev.get("done") or ["Come back next month."])
            return
        story.story_flags[ev["monthly"]] = month
        from src.states.overworld.common import _start_event_battle, _say_then
        info = dict(ev["battle"])
        _say_then(state, list(ev.get("lines") or []), lambda: state.game.change_state(
            _start_event_battle(state.game, story.current_area_key, info, None)))
        return
    show(lines or ["..."])


def condition(story, arg):
    what, *rest = str(arg).split(":")
    if what == "white":
        return white(story)
    if what == "black":
        return not white(story)
    if what == "cleared":
        return cleared(story, rest[0].upper()) >= int(rest[1])
    return False
