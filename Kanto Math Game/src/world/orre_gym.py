"""A Gym Leader standing in one of Orre's walked dungeons (story rework S2, 11-24: Pryce in the Snagem Hideout's ruins, the
fan game's own Gym room there). A region hook: the Leader's route option runs {"world": "orre_gym"}.

The area's own "gym" data names the Leader (badge, team, lines). As every Gym (Jordan 11-13): the Gym's math game first,
till it's won; then the Leader's battle - a story battle that gives the badge (battle.py's badge_reward) and brings you back
to the room you stood in. A town's Gym room uses gym_lobby.leader_in_room instead; a dungeon can't (its lobby would send you
back to a town)."""


def condition(story, arg):
    return False


def event(state, ev, lines, show):
    from src import minigames
    from src.states.overworld.gym_lobby import GymLobbyState
    from src.states.overworld.common import _fill_names, _resolve_lines, _start_event_battle, _say_then
    game = state.game
    story = game.story_manager
    area = story.current_area_key
    lobby = GymLobbyState(game, state)
    ld = dict(lobby.leader or {})
    name = _fill_names(game, ld.get("name", "The Leader"))
    badge = ld.get("badge_reward")
    if badge and story.has_badge(badge):
        return show(lines or [f"{name}: You have my badge already. Keep it with pride."])
    closed = state.gym_closed() if hasattr(state, "gym_closed") else None
    if closed:
        return show(closed)

    def battle():
        info = dict(ld)
        info["_intro_lines"] = _resolve_lines(game, list((ld.get("dialogue") or {}).get("intro") or [f"{name}: Let's battle!"]))
        game.change_state(_start_event_battle(game, area, info, ld.get("victory_flag")))

    if getattr(lobby, "challenge", None):
        lead = next((p for p in story.player_team if p), None)

        def done(won):
            if won:
                story.story_flags[minigames.done_flag(area)] = True
            game.change_state(state)
            if won:
                _say_then(state, [f"{name}: Well played. Now - our battle!"], battle)
            else:
                _say_then(state, [f"{name}: Not quite. Talk to me when you'd like to try my game again."], lambda: None)

        intro = [f"{name}: Welcome, challenger. Before we battle, I want to play a game with you.",
                 f"{name}: Win it, and then we'll see how strong you really are."]
        return _say_then(state, intro, lambda: game.change_state(lobby.challenge(
            game, done, level=len(story.badges.get(lobby.region, [])), background=lobby.bg,
            leader=dict(ld, name=name), team=lobby._leader_team(), partner=getattr(lead, "id", 25))))
    battle()
