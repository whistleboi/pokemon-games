"""XD's Orre Colosseum after the title (Orre batch 8b, Jordan 11-21: "all seven, as the disc"; raised to fit).

Eagun's battle outside the HQ Lab opens it (flag xd_eagun_lab). Seven rounds of four battles, each round's last an Admin
or a big name (the disc's D7_out list: Lovrina, Snattle, Gorigan, Chobin, Gonzap, Ardos, Eldes). A round is four battles
in a row; your team is healed between them (Jordan 11-21: XD heals nothing, but four Lv 75-82 doubles back to back beat
even six Lv 100 legends - so we heal, as Battle Frontier halls don't but this one does). Lose one and
the round ends (you're healed and back at the desk; it starts from its first battle next time). Win the fourth: that
round's TM and title (Serebii's list), and the next round opens. A won round can be played again, for the battles.

The event ({"xd_colosseum": {"rounds": [[battle x4] x7]}}) is the Colosseum desk's (dev/builders/town_maps/orre_story.py);
battle.py calls after_battle at each battle's end (TrainerBattleState.xd_colo).

    cleared(story)          -> rounds won (0-7)
    start(state, ev, lines, show)
    after_battle(game, info, won) -> a function that starts the next battle, or lines to say back at the desk"""

CLEARED = "xd_colo_cleared"
OPEN = "xd_eagun_lab"
# (each round's prize: its TM by move, our numbers - src/pokemon/tms.py - and its title, as Serebii lists them)
PRIZES = [("TOXIC", "Lovrina Fan Club Member #1"), ("RETURN", "Orre Governor's Secretary Candidate"),
          ("SKILL-SWAP", "The Hexagonal Bolt of Friendship Holder"), ("SLUDGE-BOMB", "Defeater of Chobin"),
          ("REST", "Honorary Team Snagem Member"), ("STEEL-WING", "Cipher's Biggest Enemy"), ("DRAGON-CLAW", "Eldes's Top Rival")]
MONEY = 5000   # (per round number: XD pays Poke Coupons; ours is money)


def cleared(story):
    return int(story.story_flags.get(CLEARED, 0) or 0)


def titles(story):
    return [PRIZES[i][1] for i in range(cleared(story))]


def start(state, ev, lines, show):
    from src.states.systems.pick_list import PickListState
    game = state.game
    story = game.story_manager
    if not story.story_flags.get(OPEN):
        show(["The Orre Colosseum's desk: \"The tournament's closed today. Come back another time!\""])
        return
    rounds = (ev.get("xd_colosseum") or {}).get("rounds") or []
    n = min(len(rounds), cleared(story) + 1)
    rows = [(f"ROUND {r}" + (" (WON)" if r <= cleared(story) else ""), r) for r in range(1, n + 1)]

    def picked(r):
        if r is None:
            show(["Come back when you're ready to battle!"])
            return
        if not [p for p in story.player_team if p and p.current_hp > 0]:
            show(["Your Pokemon can't battle. Heal them first!"])
            return
        begin(game, rounds, r, 1)

    said = list(lines or []) + ["Four battles in a row. We'll heal your team between battles. Which round?"]
    from src.states.overworld.common import _say_then
    _say_then(state, said, lambda: game.change_state(PickListState(game, state, "WHICH ROUND?", rows, picked)))


def begin(game, rounds, r, m):
    """Round r's battle m (1-4)."""
    from src.states.overworld.common import _start_event_battle
    b = dict(rounds[r - 1][m - 1])
    who = b.get("name", "Your opponent")
    intro = [f"Round {r}, battle {m} of 4!" if m < 4 else f"Round {r}, the final!"] + list(b.pop("intro", None) or [f"{who} steps up!"])
    intro_state = _start_event_battle(game, game.story_manager.current_area_key, dict(b, _intro_lines=intro), None)
    intro_state.next_state.xd_colo = {"rounds": rounds, "round": r, "match": m}
    game.change_state(intro_state)


def after_battle(game, info, won):
    story = game.story_manager
    r, m, rounds = info["round"], info["match"], info["rounds"]
    if not won:
        return [f"Round {r} is over for you. Your Pokemon were healed. Try again any time!"]
    if m < 4:   # (healed, then the next battle at once: Jordan 11-21)
        from src.states.overworld.area_transition import heal_team
        heal_team(game)
        return lambda: begin(game, rounds, r, m + 1)
    lines = [f"You won Round {r} of the Orre Colosseum!"]
    if r > cleared(story):
        from src.pokemon import tms
        move, title = PRIZES[r - 1]
        tm = tms.key_for_move(game, move)
        story.story_flags[CLEARED] = r
        if tm:
            story.add_item(tm, 1)
            lines.append(f"{getattr(game, 'player_name', 'You')} received {tms.label(game, tm)}!")
        story.money += MONEY * r
        lines += [f"And ${MONEY * r} in prize money.", f"Your new title: \"{title}\"."]
        if r == 1:   # (the Lucky Egg quest starts: Beluh's e-mail - XD part 8)
            story.story_flags["xd_beluh_mail"] = True
            lines.append("Your P*DA beeps: an e-mail from Beluh. \"Please come to Agate Village. Something's wrong with our Pokemon.\"")
        if r < len(rounds):
            lines.append(f"Round {r + 1} is open now.")
        else:
            story.story_flags["xd_colo_all"] = True
            lines.append("You've won every round of the Orre Colosseum!")
    return lines
