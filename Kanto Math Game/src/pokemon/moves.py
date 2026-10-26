# [REF-0082: Moves]
"""
Each Pokemon knows up to four moves, chosen from its level-up learnset
(assets/pokemon_levels.json) using real move data (assets/moves.json, from PokeAPI).

Only moves that work in this game are learned:
  - damaging moves (power > 0, one-hit KO moves; not self-KO moves),
  - weather moves (Rain Dance, Sunny Day, Sandstorm, Hail/Snowscape),
  - status moves the battle runs (src/states/battle_effects.py): burn, paralysis, poison, sleep,
    freeze, confusion and the other conditions, stat moves, healing, field moves and a set of
    unique moves (Protect, Substitute, Rest, Metronome...).

A new Pokemon knows the last four of those it learned by its level, like the games.

Move pool (like Legends: Z-A): every move a Pokemon has learned stays in its move pool (kept through
evolution). A new move is set right away while it has fewer than four; after that it just joins the
pool, and the player picks the four it uses from the Summary screen. Nothing is forgotten.

Trainers can list canon moves per species ("movesets": {"25": ["THUNDERBOLT", ...]}, see
forms.mark_trainer_team); moves this game can't use are skipped and the set is filled from the
learnset.
"""
import json
import os

WEATHER_MOVES = {"RAIN-DANCE": "RAIN", "SUNNY-DAY": "SUN", "SANDSTORM": "SAND", "HAIL": "SNOW", "SNOWSCAPE": "SNOW"}
STATUSES = ("burn", "paralysis", "poison", "sleep", "freeze", "toxic")  # toxic = badly poisoned (Toxic)
STATUS_LABEL = {"burn": "BRN", "paralysis": "PAR", "poison": "PSN", "sleep": "SLP", "freeze": "FRZ", "toxic": "TOX"}
POWDER_MOVES = {"SLEEP-POWDER", "STUN-SPORE", "POISON-POWDER", "SPORE", "COTTON-SPORE", "RAGE-POWDER",
                "MAGIC-POWDER", "POWDER"}  # Grass types are immune (Gen 6+)
TYPE_CHECKED_STATUS = {"THUNDER-WAVE"}  # status moves the type chart applies to (Ground ignores it)
SELF_KO = {"EXPLOSION", "SELF-DESTRUCT", "MISTY-EXPLOSION", "MEMENTO", "FINAL-GAMBIT", "HEALING-WISH"}
FALLBACK = "TACKLE"
STRUGGLE = "STRUGGLE"  # used only when no known move can affect the foe
STRUGGLE_DATA = {"type": None, "power": 50, "accuracy": None, "category": "PHYSICAL", "priority": 0,
                 "category_meta": "damage"}
MAX_MOVES = 4
# Fixed damage: "level" = user's level, "half" = half the target's HP, a number = that much HP.
FIXED_DAMAGE = {"SEISMIC-TOSS": "level", "NIGHT-SHADE": "level", "DRAGON-RAGE": 40, "SONIC-BOOM": 20,
                "SUPER-FANG": "half", "RUINATION": "half", "NATURES-MADNESS": "half"}
# Charge on the first turn, hit on the second (Solar Beam skips the charge in sun).
TWO_TURN = {"SOLAR-BEAM": "{n} took in sunlight!", "SOLAR-BLADE": "{n} took in sunlight!",
            "RAZOR-WIND": "{n} whipped up a whirlwind!", "SKULL-BASH": "{n} tucked in its head!",
            "SKY-ATTACK": "{n} became cloaked in a harsh light!", "FLY": "{n} flew up high!",
            "DIG": "{n} burrowed its way under the ground!", "DIVE": "{n} hid underwater!",
            "BOUNCE": "{n} sprang up!", "METEOR-BEAM": "{n} is overflowing with space power!",
            "PHANTOM-FORCE": "{n} vanished instantly!", "SHADOW-FORCE": "{n} vanished instantly!",
            "FREEZE-SHOCK": "{n} became cloaked in a freezing light!", "ICE-BURN": "{n} became cloaked in freezing air!",
            "ELECTRO-SHOT": "{n} absorbed electricity!"}
# Semi-invulnerable while charging: which moves still hit, and their damage multiplier.
_SKY = {"GUST": 2, "TWISTER": 2, "THUNDER": 1, "SKY-UPPERCUT": 1, "HURRICANE": 1, "SMACK-DOWN": 1}
SEMI_INVULNERABLE = {"FLY": _SKY, "BOUNCE": _SKY, "DIG": {"EARTHQUAKE": 2, "MAGNITUDE": 2, "FISSURE": 1},
                     "DIVE": {"SURF": 2, "WHIRLPOOL": 2}, "PHANTOM-FORCE": {}, "SHADOW-FORCE": {}}
# Must rest a turn after hitting.
RECHARGE = {"HYPER-BEAM", "GIGA-IMPACT", "BLAST-BURN", "HYDRO-CANNON", "FRENZY-PLANT", "ROCK-WRECKER",
            "ROAR-OF-TIME", "PRISMATIC-LASER", "METEOR-ASSAULT", "ETERNABEAM"}


def table(game):
    cache = getattr(game, "_move_table", None)
    if cache is None:
        path = os.path.join(game.assets.assets_dir, "moves.json")
        try:
            with open(path, encoding="utf-8") as f:
                cache = json.load(f)
        except OSError:
            cache = {}
        game._move_table = cache
    return cache


def info(game, name):
    """Move data with its name (TACKLE stand-in if unknown)."""
    if name == STRUGGLE:
        return dict(STRUGGLE_DATA, name=name)
    d = table(game).get(name) or table(game).get(FALLBACK) or {"type": "NORMAL", "power": 40, "accuracy": 100,
                                                                "category": "PHYSICAL", "priority": 0}
    return dict(d, name=name)


def usable(d):
    """Can this game use the move? Damaging moves, one-hit KO moves, weather moves and the status
    moves the battle runs (stat moves, conditions, healing, field moves...: battle_effects)."""
    if d.get("name") in SELF_KO:
        return False
    if (d.get("power") or 0) > 0 or d.get("name") in FIXED_DAMAGE or d.get("category_meta") == "ohko":
        return True
    if d.get("name") in WEATHER_MOVES:
        return True
    if d.get("category") == "STATUS" and d.get("ailment") in STATUSES and d.get("category_meta") == "ailment":
        return True
    from src.states.battle_effects import usable_status
    return d.get("category") == "STATUS" and usable_status(d)


def _species(poke):
    from src.pokemon.evolution import base_id
    return base_id(poke)


def _learner(game, poke):
    from src.pokemon.evolution import move_species
    return move_species(game, poke)


def learnable(game, poke, up_to=None, after=0):
    """Usable level-up moves learned in (after, up_to], oldest first."""
    from src.pokemon.evolution import learnset
    lv = poke.level if up_to is None else up_to
    out = []
    for learn_level, name in sorted(learnset(game, _learner(game, poke)), key=lambda x: x[0]):
        if after < max(1, learn_level) <= lv and name not in out and usable(info(game, name)):
            out.append(name)
    return out


def default_moves(game, poke):
    """The last four usable moves learned by its level (Tackle if none)."""
    moves = learnable(game, poke)
    return moves[-MAX_MOVES:] or [FALLBACK]


def ensure_moves(game, poke):
    if not getattr(poke, "moves", None):
        preset = getattr(poke, "preset_moves", None)
        poke.moves = preset_moves(game, poke, preset) if preset else default_moves(game, poke)
    return poke.moves


def preset_moves(game, poke, names):
    """A trainer's canon moves (the ones this game can use), topped up to four from its learnset."""
    known = table(game)
    out = []
    for name in names:
        name = str(name).upper().replace(" ", "-")
        if name in known and usable(info(game, name)) and name not in out:
            out.append(name)
    for name in reversed(default_moves(game, poke)):
        if len(out) >= MAX_MOVES:
            break
        if name not in out and name != FALLBACK:
            out.append(name)
    return out[:MAX_MOVES] or [FALLBACK]


def move_pool(game, poke):
    """Every move this Pokemon can choose from: everything it has learned (kept through evolution)
    plus its learnset up to its level, its current moves included."""
    pool = list(getattr(poke, "move_pool", None) or [])
    for name in learnable(game, poke) + list(ensure_moves(game, poke)):
        if name not in pool:
            pool.append(name)
    poke.move_pool = pool
    return pool


def set_move(poke, slot, name):
    """Put a pool move in slot 0-3 (or add it while it knows fewer than four). Returns True if set."""
    moves = poke.moves
    if name in moves:
        return False
    if slot is None or slot >= len(moves):
        if len(moves) >= MAX_MOVES:
            return False
        moves.append(name)
        return True
    moves[slot] = name
    return True


def move_value(game, poke, name):
    """How useful a move is to keep: STAB damage, then status, then weather."""
    d = info(game, name)
    power = d.get("power") or 0
    if name in FIXED_DAMAGE:
        return 60  # about a 60-power move at the levels it is learned
    if power:
        return power * (1.5 if d["type"] in (poke.types or []) else 1.0) * ((d.get("accuracy") or 100) / 100)
    return 35 if name not in WEATHER_MOVES else 30


def learn_new_moves(game, poke, old_level):
    """Learn moves reached between old_level and its level (into the move pool; set while it knows
    fewer than four). Returns message lines."""
    ensure_moves(game, poke)
    pool = move_pool(game, poke)
    lines = []
    for name in learnable(game, poke, after=old_level):
        label = name.replace("-", " ")
        if name in poke.moves:
            continue
        if name not in pool:
            pool.append(name)
        if len(poke.moves) < MAX_MOVES:
            poke.moves.append(name)
            lines.append(f"{poke.display_name.upper()} learned {label}!")
        else:
            lines.append(f"{poke.display_name.upper()} learned {label}! Set its moves in the Summary.")
    return lines
