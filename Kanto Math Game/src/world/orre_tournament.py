"""Orre's tournaments on their walked arenas (batch R2, Jordan 11-23): sign up at the lobby desk, stand on your side of the
arena; each round's opponent walks in, you battle, they walk off, the next walks in. Lose, and you're healed and back in
the lobby; the tournament starts over. Win the last round: the Colosseum's award (the badge comes with the battle).

The battles are the area's Gym data, started through GymLobbyState (its levels, badges, rematches and League rules all
stay), from the arena room (gym_lobby.in_room: back in the arena after each battle), as "facility" battles so a loss never
whites out (battle.py). The walking is the town map's own scenes, written into the maps by orre_story.py (_tournament):
    the desk     {"world": "orre_tournament", "signup": {"arena": room, "at": [x, y]}}   -> you're taken to your spot
    each round   a scene on entering the arena, "condition": ["world:orre_tournament:round:<k>"]: the k-th opponent walks
                 in with the event {"world": "orre_tournament", "fight": true} (the battle); back in the arena after a win,
                 the next round's scene plays (a fresh map: its "enter" scenes run again)
    a loss       "world:orre_tournament:lost" -> lines, {"world": "orre_tournament", "reset": true}, the scene's "room" (lobby)
    the title    "world:orre_tournament:won" -> the award lines, {"world": "orre_tournament", "done": true}
Story flags: orre_tourney_<AREA> (a run is on), orre_tourney_fight_<AREA> (the round a battle started at, plus one: so a
battle that left gym_progress where it was is a loss)."""
RUN = "orre_tourney_{}"
RETRY = "orre_tourney_retry_{}"   # (the math game before the final was lost: the referee offers it again; Jordan 11-23)
FIGHT = "orre_tourney_fight_{}"


def _progress(story, area):
    return int(story.story_flags.get(f"gym_progress_{area}", 0) or 0)


def _gym(story, area):
    game = getattr(story, "game", None)
    prog = game.loader.area_data.get("STORY_PROGRESSION", {}) if game is not None else {}
    return (prog.get(area) or {}).get("gym") or {}


def condition(story, arg):
    area = story.current_area_key
    on = bool(story.story_flags.get(RUN.format(area)))
    fight = int(story.story_flags.get(FIGHT.format(area), 0) or 0)
    prog = _progress(story, area)
    kind, _, n = str(arg).partition(":")
    trainers = len(_gym(story, area).get("trainers") or [])
    if kind == "round":   # (round k is next: a run is on, the last battle, if any, was won; the final waits for the math game)
        k = int(n or 0)
        return on and prog == k and fight <= prog and not (fight == trainers + 1 and k == 0) and (k < trainers or not _game_due(story, area))
    if kind == "game":    # (the Gym's math game, before the final: Jordan 11-01 / 11-23)
        return on and prog == trainers and fight <= prog and _game_due(story, area) and not story.story_flags.get(RETRY.format(area))
    if kind == "lost":    # (back from a battle that didn't move the run on: the count is where that battle left it)
        return on and fight and prog == fight - 1
    if kind == "won":     # (back from the last battle, won; a League's title resets its own count, the Hall of Fame first)
        return on and fight and ((prog >= fight and prog > trainers) or (fight == trainers + 1 and prog < fight - 1))
    if kind == "on":
        return on
    return False


def _game_due(story, area):
    """The Gym's math game is still to win before its Leader (gym_lobby: until the badge, unless won already)."""
    from src import minigames
    badge = (_gym(story, area).get("leader") or {}).get("badge_reward")
    return bool(badge and not story.has_badge(badge) and not story.story_flags.get(minigames.done_flag(area)))


def event(state, ev, lines, show):
    game = state.game
    story = game.story_manager
    area = story.current_area_key
    if ev.get("signup"):
        return _signup(state, ev, lines, show)
    if ev.get("to_arena"):   # (no tournament: just through to the arena - Snattle's takeover of Phenac Stadium, XD part 4)
        from src.states.overworld.common import _say_then
        cfg = ev["to_arena"]
        if cfg.get("flag"):   # (the Journal's way-point: through the desk)
            story.story_flags[cfg["flag"]] = True
        return _say_then(state, list(lines or []), lambda: _to_room(state, cfg["arena"], cfg["at"]))
    if ev.get("fight"):
        return _fight(state, area)
    if ev.get("referee"):
        if story.story_flags.get(RUN.format(area)) and story.story_flags.get(RETRY.format(area)) and _game_due(story, area):
            story.story_flags.pop(RETRY.format(area), None)
            from src.states.overworld.common import _say_then
            return _say_then(state, ["Referee: Ready to try the challenge again? Here we go!"], lambda: _fight(state, area))
        if story.story_flags.get(RUN.format(area)):
            return show(["Referee: Good luck out there!"])
        if ev.get("signup"):   # (no desk here: the host signs you up on the spot - Realgam's tower top)
            return _signup(state, ev, lines, show)
        return show(["Referee: Want to battle? Sign up at the front desk!"])
    if ev.get("reset"):   # (a loss: the run starts over next time)
        story.story_flags.pop(RUN.format(area), None)
        story.story_flags.pop(FIGHT.format(area), None)
        if _progress(story, area) <= len(_gym(story, area).get("trainers") or []):   # (the title not won yet: back to round one)
            story.story_flags[f"gym_progress_{area}"] = 0
        if lines:
            show(lines)
        return
    if ev.get("done"):
        story.story_flags.pop(RUN.format(area), None)
        story.story_flags.pop(FIGHT.format(area), None)
        if lines:
            show(lines)
        return
    if lines:
        show(lines)


def _signup(state, ev, lines, show):
    from src.states.overworld.gym_lobby import GymLobbyState
    game = state.game
    story = game.story_manager
    area = story.current_area_key
    cfg = ev["signup"]
    closed = state.gym_closed() if hasattr(state, "gym_closed") else None
    if closed:
        show(closed if isinstance(closed, list) else [closed])
        return
    lobby = GymLobbyState(game, state)
    if lobby.is_cleared and not getattr(lobby, "rematch", False):
        show(list(cfg.get("champion") or ["Receptionist: You're our champion! Come back any time to watch the battles."]))
        return
    if not [p for p in story.player_team if p and p.current_hp > 0]:
        show(["Receptionist: Your Pokemon can't battle. Please heal them first!"])
        return
    waiting = story.story_flags.get(RUN.format(area)) and story.story_flags.get(RETRY.format(area))
    if waiting:   # (the math game before the final is waiting: no starting over - Jordan 11-23)
        cfg = dict(cfg, lines=["Receptionist: Your challenge is waiting in the arena. Talk to the referee when you're ready!"])
    elif _progress(story, area) <= len(lobby.trainers) or not story.story_flags.get(RUN.format(area)):   # (a fresh run: from the first
        story.story_flags[f"gym_progress_{area}"] = 0   #  round - R6 11-24: a count left by another Gym in the same arena (Evice's
                                                        #  run, then the League) is no run of this one; a League mid-run keeps its own)
    story.story_flags[RUN.format(area)] = True
    story.story_flags.pop(FIGHT.format(area), None)
    said = list(lines or []) + list(cfg.get("lines") or ["Receptionist: You're entered! Please go to the arena. Good luck!"])
    room, at = cfg["arena"], cfg["at"]

    def go():
        _to_room(state, room, at)
    from src.states.overworld.common import _say_then
    _say_then(state, said, go)


def _to_room(state, room, at):
    """Into the arena room, standing on your spot (as a scene's "room" end does)."""
    from src.states.overworld import CityState
    game = state.game
    area = game.story_manager.current_area_key
    game.walk_town_room = (area, room)
    game.walk_town_pos = (area, tuple(at), (0, -1))   # (facing the far side)
    game.walk_town_exit = None
    game.change_state(CityState(game))


def _fight(state, area):
    from src.states.overworld.gym_lobby import GymLobbyState
    game = state.game
    story = game.story_manager
    lobby = GymLobbyState(game, state)
    prog = _progress(story, area)
    if prog >= len(lobby.trainers) and _game_due(story, area) and getattr(lobby, "challenge", None):
        return _math_game(state, area, lobby)
    if prog < len(lobby.trainers):   # (the round trainers are battled here; the Gym's math game waits for the final)
        lobby.challenge = None
        lobby.next_opponent = lobby.trainers[prog]
    story.story_flags[FIGHT.format(area)] = prog + 1
    game.gym_room_return = area
    game.transitioning = False
    lobby.challenge_gym()
    st = game.current_state
    battle = getattr(st, "next_state", None) or st
    try:
        battle.facility = {"world": "orre_tournament", "area": area}   # (no whiting out: battle.py; back in the arena)
    except Exception:
        pass


def _math_game(state, area, lobby):
    """The Gym's minigame before the final (gym_lobby._start_challenge's, but back in the arena either way): won, the
    champion walks in; lost, the referee offers it again - the run doesn't start over (Jordan 11-23)."""
    from src import minigames
    from src.states.overworld import CityState
    game = state.game
    story = game.story_manager
    lead = next((p for p in story.player_team if p), None)

    def done(won):
        if won:
            story.story_flags[minigames.done_flag(area)] = True
            story.story_flags[f"gym_progress_{area}"] = len(lobby.trainers)
            story.story_flags.pop(RETRY.format(area), None)
        else:
            story.story_flags[RETRY.format(area)] = True
        story.story_flags.pop(FIGHT.format(area), None)
        game.gym_room_return = None
        room = CityState(game)
        game.change_state(room)
        if not won and hasattr(room, "say"):
            room.say(["Referee: So close! Talk to me when you want another try."])

    from src.states.overworld.common import _fill_names
    game.change_state(lobby.challenge(
        game, done, level=len(story.badges.get(lobby.region, [])), background=lobby.bg,
        leader=dict(lobby.leader or {}, name=_fill_names(game, (lobby.leader or {}).get("name"))),
        team=lobby._leader_team(), partner=getattr(lead, "id", 25)))


def after_battle(game, info, won):
    """battle.py's facility hook; the Gym path takes you back to the arena first, so there's nothing left to say here."""
    return None
