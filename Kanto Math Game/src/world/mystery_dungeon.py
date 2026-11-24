"""The Giant Volcano: a Pokemon Mystery Dungeon easter egg under Cinnabar Island (Jordan, 11-16).

After Blaine (the Volcano Badge), a scientist in the Lab's Testing Room offers to try a machine on you. He walks you
out to the volcano's mouth, the machine misfires, and you fall in, turned into a Charmander, with a Vulpix who
lives there as your partner. Ten floors of Explorers of Sky's Giant Volcano (its tiles, its Pokemon, every floor
made fresh), every battle fought on the map; a shiny Moltres waits at the top until it has joined you. Then you
wake up in the Lab as yourself (also when both of you faint), and the Moltres comes along (party, else the PC).

The dungeon is the area GIANT_VOLCANO (assets/pokemon_area_data.json, its "mystery_dungeon"; its floors in
assets/dungeon_routes.json), walked by src/states/overworld/mystery_dungeon.py. While you're in it your real party
and battle style are kept aside here (story.gv_real); a save made meanwhile saves them, with you back on Cinnabar,
so nothing is lost if the game closes inside."""
import random

AREA = "GIANT_VOLCANO"
HOME = "CINNABAR_ISLAND"
LAB_ROOM = "lab_test"
LAB_SPOT = (10, 8)           # (beside the scientist in the Testing Room, facing him)
LAB_DOOR = "OUT:8,9"         # (out of the Lab: below its door)
WALK_FLAG = "gv_walk"        # (set while the scientist walks you to the volcano)
MOLTRES_FLAG = "giant_volcano_moltres"   # (the shiny Moltres has joined you: it isn't at the top any more)
BEATEN_FLAG = "giant_volcano_moltres_beaten"
CLEARS_FLAG = "giant_volcano_clears"
HERO, PARTNER = 4, 37        # Charmander (you), Vulpix (your partner)
LEVEL = 55                   # (strong enough for the volcano's Lv 43-52 evolved Pokemon: fun, not a grind)
MOVES = {HERO: ["FLAMETHROWER", "DRAGON-CLAW", "ROCK-SLIDE", "SLASH"],
         PARTNER: ["FLAMETHROWER", "EXTRASENSORY", "QUICK-ATTACK", "CONFUSE-RAY"]}
MOLTRES_LEVEL = 44           # (Giant Volcano's own: Moltres on 10F at Lv 44)

# Giant Volcano's Pokemon on floors 1-10 (Explorers of Sky, Bulbapedia): species, first and last floor, levels
WILD = [
    (390, 1, 7, 5, 6),     # Chimchar
    (77, 1, 8, 17, 18),    # Ponyta
    (255, 1, 8, 5, 6),     # Torchic
    (322, 1, 9, 14, 15),   # Numel
    (4, 1, 10, 5, 7),      # Charmander
    (58, 1, 10, 16, 18),   # Growlithe
    (155, 1, 10, 5, 7),    # Cyndaquil
    (218, 1, 10, 15, 17),  # Slugma
    (5, 1, 19, 43, 46),    # Charmeleon
    (59, 1, 19, 48, 51),   # Arcanine
    (78, 1, 19, 48, 51),   # Rapidash
    (136, 1, 19, 49, 52),  # Flareon
    (156, 1, 19, 48, 51),  # Quilava
    (219, 1, 19, 49, 52),  # Magcargo
    (256, 1, 19, 45, 48),  # Combusken
    (323, 1, 19, 46, 49),  # Camerupt
    (391, 1, 19, 43, 46),  # Monferno
]
EVOLVED_WEIGHT = 0.6   # (the evolved ones are rarer, so the climb isn't one long hard fight)


def wild_on(floor):
    """[(species, weight, (low, high))] that can appear on floor (1-based)."""
    out = []
    for pid, a, b, lo, hi in WILD:
        if a <= floor <= b:
            out.append((pid, EVOLVED_WEIGHT if lo >= 40 else 1.0, (lo, hi)))
    return out


def pick_wild(floor, rng=None):
    """(species, level) for a wild Pokemon on floor (1-based)."""
    rng = rng or random
    pool = wild_on(floor)
    total = sum(w for _p, w, _l in pool)
    r = rng.uniform(0, total)
    for pid, w, (lo, hi) in pool:
        r -= w
        if r <= 0:
            return pid, rng.randint(lo, hi)
    pid, _w, (lo, hi) = pool[-1]
    return pid, rng.randint(lo, hi)


# ---------------------------------------------------------------- being a Pokemon
def active(story):
    return story.__dict__.get("gv_real") is not None


def _make(game, pid, level, shiny=False):
    from src.pokemon.data import Pokemon
    mon = Pokemon(game.loader.fetch_specific(int(pid), is_shiny=shiny), game.assets, size_mult=2.5).max_ivs()
    mon.is_shiny = bool(shiny)
    mon.level = int(level)
    mon.ability_slot = 0     # (Blaze; Flash Fire for Vulpix: handy in a fire dungeon)
    mon.everstone = True     # (you stay a Charmander, whatever you win)
    mon.moves = list(MOVES.get(int(pid), []))
    mon.current_hp = mon.get_max_hp()
    return mon


def become(game):
    """You're the Charmander now, the Vulpix beside you: your real party and battle style kept aside."""
    story = game.story_manager
    if active(story):
        return
    story.gv_real = {"team": list(story.player_team), "style": getattr(story, "battle_style", "TRADITIONAL"),
                     "names": (getattr(game, "player_name", ""),)}
    hero = _make(game, HERO, LEVEL)
    hero.display_name = str(getattr(game, "player_name", "") or hero.display_name)   # (it's you)
    partner = _make(game, PARTNER, LEVEL)
    story.player_team = [hero, partner]
    story.battle_style = "OVERWORLD"   # (every fight on the map, Moltres's too)


def back_to_normal(game):
    """Your own party and battle style again. Returns the shiny Moltres's line if it's coming along, else None."""
    story = game.story_manager
    real = story.__dict__.get("gv_real")
    if real is None:
        return None
    story.player_team = list(real["team"])
    story.battle_style = real["style"]
    story.gv_real = None
    story.story_flags[WALK_FLAG] = False
    if story.story_flags.get(BEATEN_FLAG) and not story.story_flags.get(MOLTRES_FLAG):
        story.story_flags[MOLTRES_FLAG] = True
        return give_moltres(game)
    return None


def give_moltres(game):
    """The shiny Moltres joins you: the party, else the PC."""
    story = game.story_manager
    mon = _make(game, 146, MOLTRES_LEVEL, shiny=True)
    mon.everstone = False
    mon.moves = []           # (its own moves, from its learnset)
    mon.ability_slot = 0
    mon.caught_region = story.get_current_region()
    mon.caught_level = MOLTRES_LEVEL
    if len([p for p in story.player_team if p]) < 6:
        story.player_team.append(mon)
        where = "joined your team"
    else:
        story.deposit_to_pc(mon)
        where = "was sent to the PC"
    game.data.mark_seen(mon.id)
    game.data.add_pokemon(mon)
    return f"The shiny MOLTRES {where}!"


def save_view(story, data):
    """story.serialize()'s result as it should be saved while you're in the dungeon: your real party (in the region's
    storage too), your own battle style, and you on Cinnabar Island."""
    real = story.__dict__.get("gv_real")
    if real is None:
        return data
    rec = [story._pokemon_record(p) for p in real["team"] if p]
    data["player_team"] = rec
    st = (data.get("region_stores") or {}).get(story.active_store)
    if st is not None:
        st["team"] = rec
    data["battle_style"] = real["style"]
    if data.get("current_area_key") == AREA:
        data["current_area_key"] = HOME
    flags = dict(data.get("story_flags") or {})
    flags[WALK_FLAG] = False
    data["story_flags"] = flags
    return data


# ---------------------------------------------------------------- the lab and the fall
OFFER = {
    "text": "Volcano experiment", "action": "EVENT", "condition": "has_badge:VOLCANO",
    "event": {"scene": "giant_volcano", "lines": [
        "Scientist: You beat Blaine? Then a little heat won't bother you.",
        "I've built a machine that lets a person see the world the way a Pokemon does!",
        "It needs the volcano's heat to run. Come on, I'll show you!"]}}

CAST = {   # (the scientist out of the Lab door, then up to the volcano's mouth; then the fall)
    "trigger": "enter", "flag_condition": WALK_FLAG, "every": True, "then": "event:giant_volcano_fall",
    "cast": [{"from": [8, 9], "sheet": "fr_55.png", "to": "player", "lines": ["Scientist: This way! Follow me!"],
              "lead": [[22, 6, ["Scientist: Feel that heat? Perfect for the machine.",
                                "Hold still now... Switching it on!",
                                "...", "The machine is sparking! The ground shakes...",
                                "You lose your footing and tumble into the volcano!"]]]}]}


def overlay(maps):
    """Our additions to the town maps (assets/town_maps.json is written by the FireRed builders): the offer in the
    Testing Room and the walk to the volcano outside."""
    town = maps.get(HOME)
    if not isinstance(town, dict) or town.get("_gv"):
        return maps
    town["_gv"] = True
    room = (town.get("rooms") or {}).get(LAB_ROOM)
    if room:
        people = room.setdefault("people", [])
        for i, who in enumerate(people):   # (the scientist by the machines: the experiment too, after Blaine. Since Kanto batch 23
            text = who.get("text") if isinstance(who, dict) else who   #  that's FireRed's fossil scientist, "Pokemon Lab", 11-24)
            if text in ("Scientist", "Pokemon Lab"):
                people[i] = [OFFER, who]
                break
    town.setdefault("scenes", []).append(CAST)
    return maps


def offer_scene(state, lines, show):
    """The scientist's offer accepted: out of the Lab together, and the walk to the volcano (CAST) begins."""
    game = state.game
    story = game.story_manager

    def out():
        end = getattr(state, "end_npc_interaction", None)   # (his words closed first)
        if end is not None:
            end()
        story.story_flags[WALK_FLAG] = True
        go = getattr(state, "_go", None)
        if go is not None and getattr(state, "town_map", None):
            go(None, LAB_DOOR)
            x, y = state.player   # (a step aside, so he can come out of the door after you)
            if state._open((x + 1, y)):
                state.player = state.anim_from = state.partner = state.partner_from = (x + 1, y)
                state.facing = (-1, 0)
        else:   # (the old town menu: straight to the volcano)
            fall(game)
    say = getattr(state, "show_message", None) or getattr(state, "show_dialogue")
    say(lines or ["..."], callback=out)


def fall(game):
    """Into the volcano as a Charmander."""
    from src.states.overworld.area_transition import AreaTransitionState
    story = game.story_manager
    story.story_flags[WALK_FLAG] = False
    become(game)
    game.walk_town_pos = None
    game.change_state(AreaTransitionState(game, AREA))


def wake_in_lab(game, lines):
    """Back in the Testing Room as yourself, the scientist beside you."""
    from src.states.overworld.town import CityState
    story = game.story_manager
    joined = back_to_normal(game)
    for p in story.player_team:
        if p:
            p.heal_full()
    game.dungeon_state = None
    story.current_area_key = HOME
    game.walk_town_pos = (HOME, LAB_SPOT, (1, 0))
    game.walk_town_room = (HOME, LAB_ROOM)
    game.skip_arrival_event = True
    town = game.states["city"] = CityState(game)
    game.change_state(town)
    lines = list(lines) + ([joined] if joined else [])
    say = getattr(town, "show_message", None) or getattr(town, "show_dialogue")
    say(lines)
    return town


LOST = ["...", "Scientist: You're awake! The machine shut itself off and you just... came back.",
        "You're yourself again. Your own Pokemon are fine.",
        "Want to try again? Just ask me any time!"]
WON = ["...", "Scientist: You're back! The machine overloaded, but the readings are amazing!",
       "You were a Charmander? Climbing a volcano with a Vulpix? Incredible!"]
WON_MOLTRES = WON + ["Wait... what's that behind you?!", "A Moltres, glowing gold, followed you back!"]
