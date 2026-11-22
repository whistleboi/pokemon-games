"""Colosseum rounds at a desk: XD's Orre Colosseum after the title (Orre batch 8b) and Colosseum's Deep Colosseum (8c).

The Orre Colosseum (Jordan 11-21: "all seven, as the disc"; raised to fit): Eagun's battle outside the HQ Lab opens it
(flag xd_eagun_lab). Seven rounds of four battles, each round's last an Admin or a big name (the disc's D7_out list:
Lovrina, Snattle, Gorigan, Chobin, Gonzap, Ardos, Eldes). The Deep Colosseum (8c): five rounds of four from the disc's
"bottom sets" (three trainers, then an Admin; the fifth ends with the Deep King), reached with the D-Disk.
A round is four battles in a row; your team is healed between them (Jordan 11-21: XD heals nothing, but four Lv 75-82
doubles back to back beat even six Lv 100 legends). Lose one and the round ends (you're healed and back at the desk; it
starts from its first battle next time). Win the fourth: that round's prize, and the next round opens. A won round can be
played again, for the battles. A battle may carry "if_snagged" (an Admin's team once its Shadow is snagged: col_post.py).

The event: {"xd_colosseum": {"rounds": [[battle x4] ...], and for another colosseum "cleared", "open", "prizes", "money"...}}
(dev/builders/town_maps/orre_story.py); battle.py calls after_battle at each battle's end (TrainerBattleState.xd_colo).

    cleared(story, cfg)     -> rounds won
    start(state, ev, lines, show)
    after_battle(game, info, won) -> a function that starts the next battle, or lines to say back at the desk"""

CLEARED = "xd_colo_cleared"
OPEN = "xd_eagun_lab"
# (the Orre Colosseum's prizes: each round's TM by move, our numbers - src/pokemon/tms.py - and its title, as Serebii lists them)
PRIZES = [("TOXIC", "Lovrina Fan Club Member #1"), ("RETURN", "Orre Governor's Secretary Candidate"),
          ("SKILL-SWAP", "The Hexagonal Bolt of Friendship Holder"), ("SLUDGE-BOMB", "Defeater of Chobin"),
          ("REST", "Honorary Team Snagem Member"), ("STEEL-WING", "Cipher's Biggest Enemy"), ("DRAGON-CLAW", "Eldes's Top Rival")]
MONEY = 5000   # (per round number: XD pays Poke Coupons; ours is money)


def _cfg(cfg):
    cfg = cfg or {}
    own = "cleared" in cfg
    return {"cleared": cfg.get("cleared", CLEARED), "open": cfg.get("open", OPEN), "prizes": cfg.get("prizes", [] if own else PRIZES),
            "money": cfg.get("money"), "all_flag": cfg.get("all_flag", "xd_colo_all"),
            "name": cfg.get("name", "the Orre Colosseum"), "first_flag": cfg.get("first_flag", None if own else "xd_beluh_mail"),
            "closed": cfg.get("closed")}


def cleared(story, cfg=None):
    return int(story.story_flags.get(_cfg(cfg)["cleared"], 0) or 0)


def titles(story, cfg=None):
    c = _cfg(cfg)
    return [c["prizes"][i][1] for i in range(cleared(story, cfg)) if i < len(c["prizes"]) and c["prizes"][i][1]]


def start(state, ev, lines, show):
    from src.states.systems.pick_list import PickListState
    game = state.game
    story = game.story_manager
    cfg = ev.get("xd_colosseum") or {}
    c = _cfg(cfg)
    if not story.story_flags.get(c["open"]):
        show(c["closed"] or ["The desk: \"The tournament's closed today. Come back another time!\""])
        return
    rounds = cfg.get("rounds") or []
    n = min(len(rounds), cleared(story, cfg) + 1)
    rows = [(f"ROUND {r}" + (" (WON)" if r <= cleared(story, cfg) else ""), r) for r in range(1, n + 1)]

    def picked(r):
        if r is None:
            show(["Come back when you're ready to battle!"])
            return
        if not [p for p in story.player_team if p and p.current_hp > 0]:
            show(["Your Pokemon can't battle. Heal them first!"])
            return
        begin(game, cfg, r, 1)

    said = list(lines or []) + ["Four battles in a row. We'll heal your team between battles. Which round?"]
    from src.states.overworld.common import _say_then
    _say_then(state, said, lambda: game.change_state(PickListState(game, state, "WHICH ROUND?", rows, picked)))


def begin(game, cfg, r, m):
    """Round r's battle m (1-4)."""
    from src.states.overworld.common import _start_event_battle
    from src.world import col_post
    if isinstance(cfg, list):   # (the rounds alone)
        cfg = {"rounds": cfg}
    rnd = cfg["rounds"][r - 1]
    b = dict(col_post.second_chance(game, dict(rnd[m - 1])))
    who = b.get("name", "Your opponent")
    last = len(rnd)
    intro = [f"Round {r}, battle {m} of {last}!" if m < last else f"Round {r}, the final!"] + list(b.pop("intro", None) or [f"{who} steps up!"])
    b.pop("if_snagged", None)
    intro_state = _start_event_battle(game, game.story_manager.current_area_key, dict(b, _intro_lines=intro), None)
    intro_state.next_state.xd_colo = {"cfg": cfg, "round": r, "match": m}
    game.change_state(intro_state)


def after_battle(game, info, won):
    story = game.story_manager
    cfg = info.get("cfg") or {"rounds": info.get("rounds")}
    c = _cfg(cfg)
    r, m = info["round"], info["match"]
    rounds = cfg["rounds"]
    if not won:
        return [f"Round {r} is over for you. Your Pokemon were healed. Try again any time!"]
    if m < len(rounds[r - 1]):   # (healed, then the next battle at once: Jordan 11-21)
        from src.states.overworld.area_transition import heal_team
        heal_team(game)
        return lambda: begin(game, cfg, r, m + 1)
    lines = [f"You won Round {r} of {c['name']}!"]
    if r > cleared(story, cfg):
        from src.pokemon import tms
        move, title = c["prizes"][r - 1] if r - 1 < len(c["prizes"]) else (None, None)
        story.story_flags[c["cleared"]] = r
        tm = tms.key_for_move(game, move) if move else None
        if tm:
            story.add_item(tm, 1)
            lines.append(f"{getattr(game, 'player_name', 'You')} received {tms.label(game, tm)}!")
        pay = (c["money"][r - 1] if c["money"] and r - 1 < len(c["money"]) else None) or MONEY * r
        story.money += pay
        lines.append(f"And ${pay} in prize money.")
        if title:
            lines.append(f"Your new title: \"{title}\".")
        if r == 1 and c["first_flag"]:   # (the Lucky Egg quest starts: Beluh's e-mail - XD part 8)
            story.story_flags[c["first_flag"]] = True
            lines.append("Your P*DA beeps: an e-mail from Beluh. \"Please come to Agate Village. Something's wrong with our Pokemon.\"")
        if r < len(rounds):
            lines.append(f"Round {r + 1} is open now.")
        else:
            story.story_flags[c["all_flag"]] = True
            lines.append(f"You've won every round of {c['name']}!")
    return lines
