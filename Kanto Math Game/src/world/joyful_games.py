"""Two Island's Joyful Game Corner attendant (11-23, Kanto K4): FireRed's two link games as single-player games with sums
(src/minigames/sevii.py). Area option event {"world": "joyful_games"}. FireRed's rules kept where one player can keep
them: Dodrio Berry Picking wants a Dodrio with you; Pokemon Jump is your lead Pokemon. A prize Berry by score each time
(FireRed gives Berries), and the best score of each game is kept."""


def event(state, ev, lines, show):
    from src.states.systems.pick_list import PickListState
    from src.minigames import sevii
    game = state.game
    story = game.story_manager
    lead = next((p for p in story.player_team if p and not getattr(p, "is_egg", False) and getattr(p, "current_hp", 0) > 0), None)

    def back():
        if hasattr(state, "is_resuming"):
            state.is_resuming = True
        game.change_state(state)

    def play(kind):
        back()
        if kind is None:
            show(["Attendant: Please come again!"])
            return
        if kind == "berry" and not any(p and getattr(p, "id", None) == 85 for p in story.player_team):
            show(["Attendant: Dodrio Berry Picking needs a Dodrio! Bring one along and its three heads can pick away."])
            return
        if kind == "jump" and lead is None:
            show(["Attendant: Your Pokemon need a rest first!"])
            return
        cls = sevii.PokemonJump if kind == "jump" else sevii.DodrioBerryPicking
        holder = {}

        def done(_won):
            g = holder.get("g")
            score = int(getattr(g, "score", 0) or 0)
            back()
            got = sevii.prize(kind, score)
            out = [f"Attendant: You scored {score}!"]
            if got:
                story.add_item(got, 1)
                from src.pokemon import forms
                out += ["Here's your prize!", f"{getattr(game, 'player_name', 'You')} received a {forms.item_label(got).upper()}!"]
            best = story.story_flags.get(sevii.JUMP_BEST if kind == "jump" else sevii.BERRY_BEST)
            if best:
                out.append(f"Best score so far: {best}.")
            show(out)
        g = cls(game, done, partner=getattr(lead, "id", 25), team=[85] if kind == "berry" else [getattr(lead, "id", 25)])
        holder["g"] = g
        game.change_state(g)

    head = list(lines or []) + ["Attendant: Welcome to the Joyful Game Corner! Which game would you like to play?"]
    say = getattr(state, "show_message", None) or getattr(state, "say", None)
    then = lambda: game.change_state(PickListState(game, state, "JOYFUL GAMES",
                                                   [("Pokemon Jump", "jump"), ("Dodrio Berry Picking", "berry")], play))
    try:
        say(head, callback=then)
    except TypeError:
        say(head, then=then)
