"""The Royal Unova (Black 2 / White 2; batch 3a's close-out, 11-21): the evening cruise from Castelia's Cruise Dock.

As the game has it (Bulbapedia's Royal Unova page): it sails once a day in the evening (the hours change with the
season), for $1,000. Aboard, the voyage lasts 3 minutes, marked by 5 blows of the ship's whistle 45 seconds apart (one
as it sets off); the fifth ends it. The clock stops in menus, battles and talks, except after a passenger who talks
for a long time: then the next whistle blows at once. The day's Trainers (Mon 4, Tue 3, Wed 4, Thu 5, Fri 4, Sat 6,
Sun 7) wait in the cabins; a crewman by the stairs counts them and lets you off early; the port crewman says how many
are on each side, the starboard one how many are behind blue doors. Beat them all and a prize waits back on the dock.

The map (dev/builders/town_maps/unova.py ROYAL_UNOVA) carries "cruise": the day's Trainers, their cabins' sides and
door colours, the prizes. Which Trainers sail on which day is our reading (the game's own rota isn't written down
anywhere we found): a fixed set a weekday, the counts as the game's.

Hooks: the walker's update calls tick(state) on a map with "cruise"; the event runner hands {"cruise": ...} events to
event(); the Cruise Dock attendant's is "board"."""
import datetime

from src.world import seasons

EVENING = {"SPRING": (17, 20), "SUMMER": (19, 21), "AUTUMN": (18, 20), "WINTER": (17, 19)}   # (boarding hours, 24h)
FARE = 1000
WHISTLES = 5
WHISTLE_FRAMES = 45 * 60          # (45 seconds at 60 frames a second)
DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
SHIP = "ROYAL_UNOVA"
BOARD_AT = (29, 17)               # (aboard, facing the bow: the crewman behind you, the deck stairs ahead)
DOCK = ("CASTELIA_CITY", "cruise_dock", 17, 16)


def _today(story):
    return getattr(story, "_cruise_today", None) or datetime.date.today()


def _now(story):
    return getattr(story, "_cruise_now", None) or datetime.datetime.now()


def boarding_open(story):
    """It's evening (this season's hours) and you haven't sailed today."""
    lo, hi = EVENING.get(seasons.current_season(_today(story)), (17, 20))
    return lo <= _now(story).hour < hi


def sailed_today(story):
    return story.story_flags.get("royal_unova_sailed") == _today(story).isoformat()


def plan(state):
    """The ship map's "cruise" table (the day's Trainers, cabins, prizes), from the walker's map."""
    art = (getattr(state, "recipe", None) or {}).get("art") or {}
    return art.get("cruise") or {}


def todays(state):
    cr = plan(state)
    return list((cr.get("days") or {}).get(DAYS[_today(state.game.story_manager).weekday()], []))


def beaten(state):
    flags = state.game.story_manager.story_flags
    cabins = plan(state).get("cabins") or {}
    return [t for t in todays(state) if flags.get((cabins.get(t) or {}).get("flag", ""))]


# ---------------------------------------------------------------------------------------------- the voyage's clock
def _voyage(state):
    return state.game.__dict__.setdefault("royal_unova_voyage", {"frames": 0, "blown": 1, "skip": False})


def start(game):
    """Aboard: a fresh voyage (the first whistle blows as she sets off)."""
    game.royal_unova_voyage = {"frames": 0, "blown": 1, "skip": False, "hello": True}


def tick(state):
    """Once a frame on the ship, while you're free to walk about (not talking, not in a scene): the clock runs; each
    45 seconds the whistle; the fifth ends the voyage."""
    if getattr(state, "area_key", None) != SHIP or getattr(state, "mode", "MAP") != "MAP":
        return
    v = _voyage(state)
    if state.dialogue_box.visible or getattr(state, "npc_active", False) or getattr(state, "_ending_cruise", False):
        return
    if hasattr(state, "_scenes") and state._scenes().actors:
        return
    if v.pop("hello", False):
        state.flash("*BWOOOH!* The Royal Unova has set sail! (Whistle 1 of 5)", 150)
    if v.pop("skip", False):   # (a long talker: the next whistle blows at once)
        v["frames"] = v["blown"] * WHISTLE_FRAMES
    else:
        v["frames"] += 1
    due = v["frames"] // WHISTLE_FRAMES + 1
    if due > v["blown"]:
        v["blown"] = min(due, WHISTLES)
        if v["blown"] >= WHISTLES:
            arrive(state)
        else:
            state.flash(f"*BWOOOH!* The ship's whistle! (Whistle {v['blown']} of {WHISTLES})", 150)


def arrive(state, early=False):
    """Back at Castelia: the prize when every Trainer aboard today was beaten, then off at the Cruise Dock."""
    from src.states.overworld import AreaTransitionState
    game, story = state.game, state.game.story_manager
    state._ending_cruise = True
    game.__dict__.pop("royal_unova_voyage", None)
    lines = (["You disembark early..."] if early else
             ["*BWOOOOOH!* That's the fifth whistle.", "The Royal Unova has returned to Castelia City. Thank you for sailing with us!"])
    day = todays(state)
    if day and len(beaten(state)) == len(day):
        prize = (plan(state).get("prizes") or {}).get(DAYS[_today(story).weekday()])
        if prize:
            story.add_item(prize, 1)
            story.story_flags["royal_unova_prize"] = True   # (the Quest Book's errand: a day's Trainers all beaten)
            name = prize.replace("_", " ").title().replace("Ragecandybar", "RageCandyBar")
            lines += ["Captain: You beat every Trainer aboard today? Splendid!", f"Please accept this: a {name}!",
                      f"{getattr(game, 'player_name', 'You')} received a {name}!"]
    area, room, x, y = DOCK
    game.walk_town_pos = (area, (x, y), (0, 1))
    game.walk_town_room = (area, room)
    state.say(lines, then=lambda: game.change_state(AreaTransitionState(game, area)))


# ---------------------------------------------------------------------------------------------- the people's events
def event(state, ev, lines, show):
    """{"cruise": "board" | "crew" | "port_hint" | "blue_hint" | "talker"} (common._run_story_event hands them here)."""
    kind = ev.get("cruise")
    game, story = state.game, state.game.story_manager
    if kind == "board":
        return _board(state, ev, lines, show)
    if getattr(state, "area_key", None) != SHIP:
        show(lines or ["..."])
        return
    day, done = todays(state), beaten(state)
    cabins = plan(state).get("cabins") or {}
    if kind == "crew":   # (by the stairs: how many aboard, how many you've beaten, and off early if you like)
        from src.states.systems.pick_list import PickListState
        said = [f"Sailor: Welcome aboard the Royal Unova! There are {len(day)} Trainers aboard today.",
                f"Sailor: You've battled {len(done)} of them so far." if done else
                "Sailor: Find them all before the voyage is over! They're in the cabins."]

        def picked(v):
            game.change_state(state)
            if v:
                arrive(state, early=True)
        _say(state, said, lambda: game.change_state(PickListState(game, state, "GET OFF THE SHIP NOW?", [("Stay aboard", False), ("Disembark", True)], picked)))
        return
    if kind == "port_hint":
        port = sum(1 for t in day if (cabins.get(t) or {}).get("side") == "port")
        show([f"Sailor: Today there are {port} Trainer{'s' if port != 1 else ''} on the port side, and "
              f"{len(day) - port} on the starboard side.", "Sailor: Port is to your left as you face the bow."])
        return
    if kind == "blue_hint":
        blue = sum(1 for t in day if (cabins.get(t) or {}).get("door") == "blue")
        show([f"Sailor: Psst. {blue} of today's Trainers {'is' if blue == 1 else 'are'} behind blue doors."])
        return
    if kind == "talker":   # (a passenger who talks and talks: the next whistle blows as they finish)
        _voyage(state)["skip"] = True
        show(lines or ["..."])
        return
    show(lines or ["..."])


def _say(state, lines, then):
    from src.states.overworld.common import _say_then
    _say_then(state, lines, then)


def _board(state, ev, lines, show):
    """The Cruise Dock attendant: in the evening, once a day, $1,000."""
    from src.states.systems.pick_list import PickListState
    from src.states.overworld import AreaTransitionState
    game, story = state.game, state.game.story_manager
    if sailed_today(story):
        show(["Attendant: You've already sailed with us today. The Royal Unova sails once a day, in the evening.",
              "Attendant: We hope to see you again tomorrow!"])
        return
    if not boarding_open(story):
        lo, hi = EVENING.get(seasons.current_season(_today(story)), (17, 20))
        show(["Attendant: Welcome to the Royal Unova! It sails once a day, in the evening.",
              f"Attendant: This {seasons.season_name().lower()}, boarding is from {lo - 12}:00 to {hi - 12}:00 PM. Please come back then!"])
        return

    def picked(v):
        game.change_state(state)
        if not v:
            show(["Attendant: Please come again!"])
            return
        if getattr(story, "money", 0) < FARE:
            show(["Attendant: I'm sorry, but you don't have enough money for a ticket."])
            return
        story.money -= FARE
        story.story_flags["royal_unova_sailed"] = _today(story).isoformat()
        for k in [k for k in story.story_flags if k.startswith("b2_ru_")]:   # (a new voyage: today's Trainers aboard afresh)
            story.story_flags.pop(k, None)
        start(game)
        game.arrive_floor = (SHIP, 0, list(BOARD_AT))
        game.change_state(AreaTransitionState(game, SHIP, initial_message=[
            f"{getattr(game, 'player_name', 'You')} paid ${FARE}.", "Attendant: All aboard! Enjoy your cruise!"]))
    _say(state, ["Attendant: Welcome to the Royal Unova! Tonight's cruise sails up the river past the Skyarrow Bridge.",
                 f"Attendant: A ticket is ${FARE:,}. Trainers who love to battle fill the cabins!"],
         lambda: game.change_state(PickListState(game, state, f"BOARD FOR ${FARE:,}?", [("Board", True), ("Not now", False)], picked)))
