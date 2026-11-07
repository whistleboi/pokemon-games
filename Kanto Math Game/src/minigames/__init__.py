"""Gym challenges (Jordan, 11-01): in place of a Gym's trainers, one minigame with a goal; win it and
the Leader is next. The game is picked at random the first time (more often one that suits the
Gym's type) and kept, so TRY AGAIN, or coming back later, is the same game until it's won.

    gym_challenge_<AREA>       the game picked for that Gym (its key)
    gym_challenge_done_<AREA>  won: the Leader is open
"""
import random

from src.minigames.arcade import PidgeyFlight, PonytaDash, BerryCatch, RouteCrossing
from src.minigames.board import EkansTrail, PokemonMatch, VoltorbField, TypeClash
from src.minigames.timing import RhythmTiles, GymPong
from src.minigames.chase import FishEscape
from src.minigames.kanto import SurgeCans, KogaWalls, SabrinaWarps, BlaineQuiz
from src.minigames.tiles import TilePuzzle

GAMES = {g.key: g for g in (PidgeyFlight, PonytaDash, BerryCatch, RouteCrossing, EkansTrail, PokemonMatch,
                            VoltorbField, TypeClash, RhythmTiles, GymPong, FishEscape, TilePuzzle,
                            SurgeCans, KogaWalls, SabrinaWarps, BlaineQuiz)}
# Gyms with their own challenge (Kanto's canon puzzles, drawn as games): always that one.
GYM_GAMES = {"VERMILLION_CITY": "surge", "FUCHSIA_CITY": "koga", "SAFFRON_CITY": "sabrina",
             "CINNABAR_ISLAND": "quiz"}

# The games that suit a Gym's type (picked three times as often).
SUITS = {
    "FLYING": ("flight",), "FIRE": ("dash", "typeclash"), "WATER": ("chase", "typeclash"),
    "GRASS": ("catch", "typeclash"), "ELECTRIC": ("voltorb", "rhythm"), "POISON": ("snake",),
    "DRAGON": ("snake", "flight"), "PSYCHIC": ("match", "tiles"), "GHOST": ("match", "rhythm"),
    "NORMAL": ("crossing", "catch"), "FIGHTING": ("pong", "dash"), "ROCK": ("crossing", "pong", "tiles"),
    "GROUND": ("crossing", "dash", "tiles"), "BUG": ("catch", "match"), "ICE": ("dash", "pong"),
    "STEEL": ("voltorb", "pong"), "DARK": ("match", "crossing"), "FAIRY": ("rhythm", "match"),
}


def picked_flag(area_key):
    return f"gym_challenge_{area_key}"


def done_flag(area_key):
    return f"gym_challenge_done_{area_key}"


def gym_type(game, team):
    from src.world import league_redo
    _by_name, data = league_redo._species(game)
    return league_redo._main_type(data, team)


def pick(game, area_key, team, rng=random):
    """The game for this Gym: the one picked before, else a new random pick (kept)."""
    if area_key in GYM_GAMES:
        return GAMES[GYM_GAMES[area_key]]
    flags = game.story_manager.story_flags
    key = flags.get(picked_flag(area_key))
    if key not in GAMES or not GAMES[key].in_pool:
        suits = SUITS.get(gym_type(game, team) or "", ())
        keys = [k for k, g in GAMES.items() if g.in_pool]
        key = rng.choices(keys, weights=[3 if k in suits else 1 for k in keys])[0]
        flags[picked_flag(area_key)] = key
    return GAMES[key]


def beaten(game):
    """[(key, Gym's area)]: each Gym game won so far (once each, the first Gym it was won at), for the
    Game Corner's GYM GAMES (Jordan, 11-06)."""
    flags = game.story_manager.story_flags
    out, seen = [], set()
    for flag, on in list(flags.items()):
        if not on or not flag.startswith("gym_challenge_done_"):
            continue
        area = flag[len("gym_challenge_done_"):]
        key = GYM_GAMES.get(area) or flags.get(picked_flag(area))
        if key in GAMES and key not in seen:
            seen.add(key)
            out.append((key, area))
    return out
