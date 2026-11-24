"""Anville Town's errands (Black 2 / White 2; Unova batch 4b, 11-23), through main's region hook ({"world": "anville"}).

- The turntable: a different train car rests on it each day of the month (Black 2's Worker on the bridge, text 647 14-46):
  {"turntable": true}. On the Hyperspeed Train's days (the 8th, 18th, 28th) no train comes and the weekend traders stay away.
- The weekend traders (Saturday and Sunday): Revive for two Escape Ropes, PP Up for a Star Piece, Full Restore for twenty
  Poke Balls: {"trade": [give, n, get, m]}.
- Lost-and-found (the Depot Agent's house): a Rare Candy the first time; after that he finds an item each time you win a
  seven-Trainer Subway train (battle_subway calls found_item), up to ten of it: {"lost_found": true}.
Conditions ("world:anville:<arg>"): "weekend" (Saturday / Sunday and a train in town), "hyperspeed" (the train-less days)."""
import datetime
import random

# day of the month -> (the car, the Worker's two lines: our words, after Black 2's)
CARS = [
    ((1, 11, 21, 31), "a Single Train", ["This is a Single Train! It's the oldest train on the Battle Subway, built for a loop line round Unova.",
                                         "Do you know Tubeline Bridge? This is the train that runs across it!"]),
    ((2, 12, 22), "a Double Train", ["This car is a Double Train, mass-produced about ten years ago, with fewer parts than a Single Train.",
                                     "Fewer parts, less cost. And that streamlined shape is still loved today!"]),
    ((3, 13, 23), "a Multi Train", ["This car is a Multi Train! Only a few were ever built: it was a test car for future trains.",
                                    "What they learned building it made the Super Single and Super Double Trains possible!"]),
    ((4, 14, 24), "a Super Double Train", ["This Super Double Train is a brand-new mass-produced car! Beauty and usefulness together!",
                                           "It's the same car as a Super Single Train. Only the paint is different!"]),
    ((5, 15, 25), "a Super Single Train", ["This Super Single Train is a new mass-produced car, rebuilt part by part to use far less power!",
                                           "New trains have to work well and be kind to the environment. They've come a long way!"]),
    ((6, 16, 26), "a Super Multi Train", ["This is a Super Multi Train, the newest car of all! Faster starts, smoother stops, self-driving controls!",
                                          "Brakes that make power, a body that tilts... and lots of other systems I can't remember!"]),
    ((7, 17, 27), "the Anville local", ["This is the little local train to Anville Town! Isn't it cute? A bit slow, and it sways as it goes.",
                                        "It's the same model as a Single Train. Old and hard to look after, but I've loved it since I was a kid!"]),
    ((8, 18, 28), "the Hyperspeed Train", ["Today's train is the Hyperspeed Train! Faster than a rocket, quieter than an air conditioner!",
                                           "I can see it so clearly... but no one can touch it. It's a dream train, one we engineers hope to build someday!"]),
    ((9, 19, 29), "a Wi-Fi Train", ["This is a Wi-Fi Train, the fastest long-distance train on the Battle Subway! A pendulum car:",
                                     "its body tilts round the curves, so it never slows down. Faster! Farther!"]),
    ((10, 20, 30), "an old train car", ["This car is the kind that ran long ago. More parts than today's trains, so it was hard to build.",
                                        "Those old cars have a beauty of their own. They don't run here now, but I hear a faraway region still uses them!"]),
]
TRADES = {"REVIVE": ("ESCAPE_ROPE", 2), "PP_UP": ("STAR_PIECE", 1), "FULL_RESTORE": ("balls", 20)}
LOST_FOUND = ["RARE_CANDY", "FULL_RESTORE", "MAX_REVIVE", "ELIXIR", "PROTEIN", "IRON", "CALCIUM", "ZINC", "CARBOS", "HP_UP"]


def _today():
    return datetime.date.today()


def car_today():
    d = _today().day
    return next(((name, lines) for days, name, lines in CARS if d in days), CARS[0][1:])


def hyperspeed():
    return _today().day in (8, 18, 28)


def known(item):
    """An item the game has (PP Up and Elixir wait for main's items list: Main's inbox clean-main-unova-pp-items)."""
    from src.pokemon import items
    return any(item in t for t in (getattr(items, n, None) for n in dir(items)) if isinstance(t, dict))


def condition(story, arg):
    if arg.startswith("item:"):
        return known(arg[5:])
    if arg == "hyperspeed":
        return hyperspeed()
    if arg == "weekend":
        return _today().weekday() >= 5 and not hyperspeed()
    return False


def found_item(story):
    """A seven-Trainer Subway train won: the lost-and-found gets an item (more of it, up to ten), once its first is given."""
    f = story.story_flags
    if not f.get("b2_lost_found_first"):
        return
    item, n = f.get("b2_lost_found_item"), int(f.get("b2_lost_found_n", 0) or 0)
    if not item:
        f["b2_lost_found_item"], f["b2_lost_found_n"] = random.choice([i for i in LOST_FOUND if known(i)]), 1
    else:
        f["b2_lost_found_n"] = min(10, n + 1)


def _have(story, item):
    return int(getattr(story, "balls_left", 0) or 0) if item == "balls" else int(story.inventory.get(item, 0) or 0)


def _give(story, item, n):
    if item == "balls":
        story.balls_left = int(getattr(story, "balls_left", 0) or 0) + n
    else:
        story.inventory[item] = story.inventory.get(item, 0) + n


def event(state, ev, lines, show):
    game = state.game
    story = game.story_manager
    f = story.story_flags
    from src.pokemon import forms
    label = lambda k: "Poke Ball" if k == "balls" else forms.item_label(k)
    if ev.get("turntable"):
        name, said = car_today()
        show(list(lines or []) + (["Unfortunately, no train has come here today.", "...Ah, but I can almost see it!"] + said
                                  if hyperspeed() else [f"See the train on the turntable? That's {name}!"] + said))
        return
    if ev.get("trade"):
        get = ev["trade"]
        give, n = TRADES[get]
        from src.states.systems.pick_list import PickListState
        from src.states.overworld.common import _say_then
        ask = list(lines or []) + [f"Will you trade {n} {label(give)}{'s' if n > 1 else ''} for my {label(get)}?"]

        def picked(k):
            if k != "yes":
                show(["Oh, that's a shame."])
            elif _have(story, give) < n:
                show([f"...Uh-oh. You don't have enough {label(give)}s."])
            else:
                _give(story, give, -n)
                _give(story, get, 1)
                show([f"{getattr(game, 'player_name', 'You')} traded {n} {label(give)}{'s' if n > 1 else ''} for the {label(get)}!",
                      "Hehe! A delightful trade, wasn't it?"])
        _say_then(state, ask, lambda: game.change_state(PickListState(game, state, "TRADE?", [("YES", "yes"), ("NO", "no")], picked)))
        return
    if ev.get("lost_found"):
        pname = getattr(game, "player_name", "You")
        if not f.get("b2_lost_found_first"):
            f["b2_lost_found_first"] = True
            _give(story, "RARE_CANDY", 1)
            show(["I'll bet you're a Pokemon Trainer! I work as a Depot Agent on the Battle Subway.",
                  "Some Trainers get so wrapped up in their battles, there's no end to the lost-and-found!",
                  "Nobody ever came for this, so you have it!", f"{pname} received a RARE CANDY!",
                  "Win seven in a row on the Subway, and I'm sure I'll have found something else."])
            return
        item, n = f.get("b2_lost_found_item"), int(f.get("b2_lost_found_n", 0) or 0)
        if not item:
            show(["Nothing new in the lost-and-found yet. Win a whole train on the Battle Subway, then come and see me!"])
            return
        _give(story, item, n)
        f.pop("b2_lost_found_item", None)
        f.pop("b2_lost_found_n", None)
        show(["No one has claimed this, so please take it off my hands!", f"{pname} received {n} {label(item).upper()}!",
              "It's better for a Trainer to use it than for me to keep it. I'm sure the item is happier, too!"])
        return
    show(lines or ["..."])
