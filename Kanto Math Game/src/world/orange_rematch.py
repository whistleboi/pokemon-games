"""The Orange Crew battle again after the title (Jordan 11-23: Rudy, Luana and Danny as Cissy and Drake already do).

5.7's Rudy, Luana and Danny are one-time story battles (Rudy on his cliff, Luana in the hotel arena, Danny at the top of
Navel Mountain). Once you're Orange Champion, talking to them again starts a rematch: their 5.7 team, each Pokemon at
its first level plus the canon League boost (levels.canon_league_boost, main's rule for regions whose games have no
rematch teams; Cissy's Gym hall and Drake's Stadium use the same through gym_lobby), as often as you like, no badge.
Before the title they say what they always said.

A region hook (common.py: event {"world": "orange_rematch"}):
    {"world": "orange_rematch", "first": <the event they run before the title>, "rematch": <their battle>,
     "rematch_lines": [what they say first]}
Written into Orange's data by kanto_handoff/orange_rom_tools/orematch.py (kept by odata and the drift check)."""
from src.world import levels


def boosted(game, battle):
    """Their battle again: the same team and moves, each level + the canon League boost; no badge, no TM."""
    b = dict(battle)
    boost = levels.canon_league_boost(game)
    b["levels"] = [min(100, int(lv) + boost) for lv in battle.get("levels") or []]
    for k in ("badge_reward", "victory_flag", "flag"):
        b.pop(k, None)
    b["rewards"] = {"balls": 5}
    name = str(battle.get("name") or "")
    b["dialogue"] = {"player_won": [f"{name}: You're every bit the Champion. Come back any time!"],
                     "player_lost": [f"{name}: Not today, Champion! Train up and try again."]}
    return b


def _check(state):
    if hasattr(state, "_check_route_condition"):
        return lambda c: state._check_route_condition(c, False)
    return state._check_menu_condition


def event(state, ev, lines, show):
    from src.states.overworld.common import _run_story_event
    story = state.game.story_manager
    if story.story_flags.get("beat_orange_champion") and ev.get("rematch"):
        _run_story_event(state, {"lines": list(ev.get("rematch_lines") or ["Ready for another battle, Champion?"]),
                                 "battle": boosted(state.game, ev["rematch"])}, _check(state), show)
        return
    _run_story_event(state, ev.get("first") or {"lines": ["..."]}, _check(state), show)
