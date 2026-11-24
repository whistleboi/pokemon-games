"""A Gym Leader standing in one of Orre's walked places (story rework S2/S3, 11-24: Pryce in the Snagem Hideout's ruins,
Jasmine on the Gateon lighthouse's roof, Norman in the Key Lair's hall, Drake in Citadark's Dome, Birch in Realgam's
Colosseum in the sky - the fan game's own Gym spots). A region hook: the Leader's option runs {"world": "orre_gym"}, with
"gym": "<field>" for a second Gym in an area that has one (Realgam's "gym_birch"). Its "requirements" (badges, a flag) are
checked here, as a Gym lobby would.

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
    if ev.get("gym"):   # (a second Gym in an area that has one already: Realgam's Birch beside its Colosseum, S3 11-24)
        gd = story.get_current_area_data().get(ev["gym"]) or {}
        lobby.gym_data, lobby.leader, lobby.trainers = gd, gd.get("leader"), []
    ld = dict(lobby.leader or {})
    name = _fill_names(game, ld.get("name", "The Leader"))
    badge = ld.get("badge_reward")
    if badge and story.has_badge(badge):
        rm = ld.get("orre_rematch")
        if rm and story.is_region_champion("ORRE"):   # (S6d, Jordan 11-24: their second team after the League, once a day)
            import datetime
            day = f"orre_rematch_{area}_{ev.get('gym') or 'gym'}@{datetime.date.today().isoformat()}"
            if story.story_flags.get(day):
                return show([f"{name}: That was a great battle today. Come back tomorrow for another!"])
            for k in [k for k in story.story_flags if k.startswith(day.split("@")[0] + "@")]:
                story.story_flags.pop(k)   # (yesterday's forgotten)
            story.story_flags[day] = True
            info = dict(ld, team=list(rm["team"]), levels=list(rm["levels"]), team_moves=[list(m) for m in rm["team_moves"]],
                        badge_reward=None, rewards={"balls": 10},
                        dialogue={"player_won": [f"{name}: Still the Champion! Come back tomorrow."],
                                  "player_lost": [f"{name}: Not today, Champion! Try again tomorrow."]})
            for k in ("victory_flag", "orre_rematch"):
                info.pop(k, None)
            info["_intro_lines"] = [f"{name}: Champion! My team has grown too. Let's see how far you've come!"]
            return game.change_state(_start_event_battle(game, area, info, None))
        return show(lines or [f"{name}: You have my badge already. Keep it with pride."])
    req = dict((lobby.gym_data or {}).get("requirements") or {})
    have = len(story.badges.get(lobby.region, []))
    if have < int(req.get("badges", 0)) or (req.get("flag") and not story.story_flags.get(req["flag"])):
        return show(_resolve_lines(game, [req.get("fail_text") or f"{name}: Come back with {req.get('badges', 0)} badges."]))

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
