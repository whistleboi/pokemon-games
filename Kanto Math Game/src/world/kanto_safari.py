"""The Safari Zone's $500 fee, FireRed's (11-23, Kanto K5; FireRed map 11.0's desk triggers): step up to the desk in the
Fuchsia gate room and the attendant takes $500 for the Safari Game (its 30 Safari Balls and 600 steps: the area's
"safari_game"). Too little money and you're turned back. Paid, you go on in; the fee is spent once you're back out of
the Safari Zone. The gate room's scenes (k_batch17, FUCHSIA_CITY "safari"):
    event {"world": "kanto_safari"}                 at the desk: pay (flag kanto_safari_paid) or be turned back
    event {"world": "kanto_safari", "back": true}   coming back from the Safari Zone: the fee is used up
    condition "world:kanto_safari:back"             paid, and just back from the Safari Zone"""

FEE = 500
PAID = "kanto_safari_paid"


def condition(story, arg):
    if arg == "back":
        return bool(story.story_flags.get(PAID)) and getattr(story, "last_area_key", None) == "SAFARI_ZONE"
    if arg == "paid":
        return bool(story.story_flags.get(PAID))
    return False


def event(state, ev, lines, show):
    game = state.game
    story = game.story_manager
    if ev.get("back"):
        story.story_flags.pop(PAID, None)
        show(list(lines or []) + ["Attendant: Did you catch your fair share? Come again!"])
        return
    if story.story_flags.get(PAID):
        show(list(lines or []) + ["Attendant: Go right on in. Good luck!"])
        return
    head = list(lines or []) + ["Attendant: Welcome to the Safari Zone!",
                                f"Attendant: For just ${FEE} you can play the Safari Game. Catch what you can with 30 Safari Balls in 600 steps!"]
    if getattr(story, "money", 0) < FEE:
        show(head + [f"Attendant: Oh, I'm sorry. You don't have enough money. It's ${FEE} to play."])
        return
    story.money -= FEE
    story.story_flags[PAID] = True
    show(head + [f"{getattr(game, 'player_name', 'You')} paid ${FEE}.",
                 "Attendant: Here are your Safari Balls. We only use a special kind of Poke Ball here. Good luck!"])
