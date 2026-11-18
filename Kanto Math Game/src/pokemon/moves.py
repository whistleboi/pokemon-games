# [REF-0082: Moves]
"""
Each Pokemon knows up to four moves, chosen from its level-up learnset
(assets/pokemon_levels.json) using real move data (assets/moves.json, from PokeAPI).

Every move works in battle (Jordan, 11-17: "Make all moves work"): damaging moves, weather, the status moves
(src/states/battle_effects.py) and every move with a mechanic of its own (src/states/battle_moves.py: Gyro Ball,
Counter, Baton Pass, Trick, Sleep Talk, Self-Destruct...). The doubles-only ones work as they would with no partner
(src/states/battle_doubles.py). So every move in assets/moves.json can be learned.

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
# Power from weight (as in the games): Low Kick / Grass Knot by the target's weight, Heavy Slam / Heat Crash by
# how many times heavier the user is (weights: assets/dex_info.json; a held Float Stone halves it).
WEIGHT_MOVES = {"LOW-KICK": "target", "GRASS-KNOT": "target", "HEAVY-SLAM": "ratio", "HEAT-CRASH": "ratio"}


def weight_power(game, name, user, target):
    """The power of a weight move against this target."""
    from src.pokemon.catching import weight
    t = max(0.1, weight(game, target))
    if WEIGHT_MOVES.get(name) == "target":
        return next(p for kg, p in ((10, 20), (25, 40), (50, 60), (100, 80), (200, 100), (float("inf"), 120)) if t < kg)
    ratio = weight(game, user) / t
    return 120 if ratio >= 5 else 100 if ratio >= 4 else 80 if ratio >= 3 else 60 if ratio >= 2 else 40
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
            "ELECTRO-SHOT": "{n} absorbed electricity!", "SKY-DROP": "{n} took its target into the sky!",
            "GEOMANCY": "{n} is absorbing power!"}
# Semi-invulnerable while charging: which moves still hit, and their damage multiplier.
_SKY = {"GUST": 2, "TWISTER": 2, "THUNDER": 1, "SKY-UPPERCUT": 1, "HURRICANE": 1, "SMACK-DOWN": 1}
SEMI_INVULNERABLE = {"FLY": _SKY, "BOUNCE": _SKY, "SKY-DROP": _SKY, "DIG": {"EARTHQUAKE": 2, "MAGNITUDE": 2, "FISSURE": 1},
                     "DIVE": {"SURF": 2, "WHIRLPOOL": 2}, "PHANTOM-FORCE": {}, "SHADOW-FORCE": {}}
# Must rest a turn after hitting.
RECHARGE = {"HYPER-BEAM", "GIGA-IMPACT", "BLAST-BURN", "HYDRO-CANNON", "FRENZY-PLANT", "ROCK-WRECKER",
            "ROAR-OF-TIME", "PRISMATIC-LASER", "METEOR-ASSAULT", "ETERNABEAM"}
# What our PokeAPI copy leaves out for some moves (most of them Scarlet/Violet's, which it has no effect data for),
# filled in as the games have them (11-17). Applied when the table loads.
_DROP_SELF = {"category_meta": "damage-raise", "stat_chance": 100}
_DROP_FOE = {"category_meta": "damage-lower", "stat_chance": 100}
DATA_FIX = {
    "AQUA-CUTTER": {"crit_rate": 1}, "AQUA-STEP": _DROP_SELF, "ARMOR-CANNON": _DROP_SELF,
    "AXE-KICK": {"ailment": "confusion", "ailment_chance": 30, "category_meta": "damage-ailment"},
    "BARB-BARRAGE": {"ailment": "poison", "ailment_chance": 50, "category_meta": "damage-ailment"},
    "BITTER-BLADE": {"drain": 50, "category_meta": "damage-heal"},
    "BITTER-MALICE": dict(_DROP_FOE, stat_changes=[["ATTACK", -1]]),
    "BLEAKWIND-STORM": {"category_meta": "damage-lower", "stat_changes": [["SPEED", -1]], "stat_chance": 30},
    "BLAZING-TORQUE": {"ailment": "burn", "ailment_chance": 30, "category_meta": "damage-ailment"},
    "CEASELESS-EDGE": {"crit_rate": 1}, "CHILLING-WATER": _DROP_FOE,
    "COMBAT-TORQUE": {"ailment": "paralysis", "ailment_chance": 30, "category_meta": "damage-ailment"},
    "DIRE-CLAW": {"crit_rate": 1},
    "ESPER-WING": dict(_DROP_SELF, crit_rate=1, stat_changes=[["SPEED", 1]]),
    "FLOWER-TRICK": {"crit_rate": 6},
    "HEADLONG-RUSH": dict(_DROP_SELF, stat_changes=[["DEFENSE", -1], ["SPDEF", -1]]),
    "INFERNAL-PARADE": {"ailment": "burn", "ailment_chance": 30, "category_meta": "damage-ailment"},
    "IVY-CUDGEL": {"crit_rate": 1}, "LUMINA-CRASH": _DROP_FOE,
    "MAGICAL-TORQUE": {"ailment": "confusion", "ailment_chance": 30, "category_meta": "damage-ailment"},
    "MAKE-IT-RAIN": _DROP_SELF,
    "MALIGNANT-CHAIN": {"ailment": "toxic", "ailment_chance": 50, "category_meta": "damage-ailment"},
    "MATCHA-GOTCHA": {"drain": 50, "ailment": "burn", "ailment_chance": 20, "category_meta": "damage-ailment"},
    "MORTAL-SPIN": {"ailment": "poison", "ailment_chance": 100, "category_meta": "damage-ailment"},
    "MOUNTAIN-GALE": {"flinch": 30},
    "MYSTICAL-POWER": dict(_DROP_SELF, stat_changes=[["SPATK", 1]]),
    "NOXIOUS-TORQUE": {"ailment": "poison", "ailment_chance": 30, "category_meta": "damage-ailment"},
    "POUNCE": _DROP_FOE,
    "PSYSHIELD-BASH": dict(_DROP_SELF, stat_changes=[["DEFENSE", 1]]),
    "SANDSEAR-STORM": {"ailment": "burn", "ailment_chance": 20, "category_meta": "damage-ailment"},
    "SPIN-OUT": _DROP_SELF,
    "SPRINGTIDE-STORM": {"category_meta": "damage-lower", "stat_changes": [["ATTACK", -1]], "stat_chance": 30},
    "STONE-AXE": {"crit_rate": 1},
    "SYRUP-BOMB": {"stat_changes": [], "stat_chance": 0},   # (its Speed drops come each turn: battle_moves.py)
    "TORCH-SONG": _DROP_SELF, "TRAILBLAZE": _DROP_SELF,
    "TRIPLE-ARROWS": {"crit_rate": 1, "flinch": 30, "category_meta": "damage-lower",
                      "stat_changes": [["DEFENSE", -1]], "stat_chance": 50},
    "TRIPLE-DIVE": {"min_hits": 3, "max_hits": 3}, "TWIN-BEAM": {"min_hits": 2, "max_hits": 2},
    "TACHYON-CUTTER": {"min_hits": 2, "max_hits": 2, "accuracy": None},
    "UPPER-HAND": {"flinch": 100}, "WAVE-CRASH": {"drain": -33},
    "WICKED-TORQUE": {"ailment": "sleep", "ailment_chance": 10, "category_meta": "damage-ailment"},
    "WILDBOLT-STORM": {"ailment": "paralysis", "ailment_chance": 20, "category_meta": "damage-ailment"},
    "ELECTRO-SHOT": {"stat_changes": [], "stat_chance": 0},   # (its Sp. Atk rise comes on the charge turn)
    "METEOR-BEAM": {"stat_changes": [], "stat_chance": 0},
    "TERA-BLAST": {"stat_changes": [], "stat_chance": 0},     # (Stellar only: there's no Stellar type here)
    "TERA-STARSTORM": {"stat_changes": [], "stat_chance": 0},
    # Effects the copy has wrong for singles play
    "BURNING-JEALOUSY": {"ailment": "none", "ailment_chance": 0},   # (only on a foe whose stats rose: battle_moves.py)
    "TAR-SHOT": {"category_meta": "unique"}, "TOXIC-THREAD": {"category_meta": "unique"},   # (no confusion)
    "VENOM-DRENCH": {"category_meta": "unique"}, "CAPTIVATE": {"category_meta": "unique"},
    "RAGING-FURY": {"min_turns": 2, "max_turns": 3},
    "DRAGON-DARTS": {"min_hits": 2, "max_hits": 2},
}
# Older spellings some trainer movesets use.
OLD_NAMES = {"BUBBLEBEAM": "BUBBLE-BEAM", "DRAGONBREATH": "DRAGON-BREATH", "FEATHERDANCE": "FEATHER-DANCE",
             "GRASSWHISTLE": "GRASS-WHISTLE", "POISONPOWDER": "POISON-POWDER", "SONICBOOM": "SONIC-BOOM",
             "SELFDESTRUCT": "SELF-DESTRUCT", "THUNDERPUNCH": "THUNDER-PUNCH", "THUNDERSHOCK": "THUNDER-SHOCK",
             "SMOKESCREEN": "SMOKESCREEN", "SOFTBOILED": "SOFT-BOILED", "SOLARBEAM": "SOLAR-BEAM",
             "HI-JUMP-KICK": "HIGH-JUMP-KICK", "VICEGRIP": "VISE-GRIP", "DOUBLESLAP": "DOUBLE-SLAP",
             "DYNAMICPUNCH": "DYNAMIC-PUNCH", "EXTREMESPEED": "EXTREME-SPEED", "ANCIENTPOWER": "ANCIENT-POWER",
             "FAINT-ATTACK": "FEINT-ATTACK"}


def table(game):
    cache = getattr(game, "_move_table", None)
    if cache is None:
        path = os.path.join(game.assets.assets_dir, "moves.json")
        try:
            with open(path, encoding="utf-8") as f:
                cache = json.load(f)
        except OSError:
            cache = {}
        for name, fix in DATA_FIX.items():
            if name in cache:
                cache[name] = dict(cache[name], **fix)
        game._move_table = cache
    return cache


def info(game, name):
    """Move data with its name (TACKLE stand-in if unknown)."""
    if name == STRUGGLE:
        return dict(STRUGGLE_DATA, name=name)
    d = table(game).get(name)
    if d is None:   # (unknown: a Tackle stand-in, never learned)
        d = dict(table(game).get(FALLBACK) or {"type": "NORMAL", "power": 40, "accuracy": 100, "category": "PHYSICAL",
                                                "priority": 0}, _unknown=True)
    return dict(d, name=name)


def usable(d):
    """Can this game use the move? Every move in assets/moves.json works now (11-17: Self-Destruct and Explosion
    too: they were left out only while the battle couldn't make the user faint). Unknown names can't."""
    return bool(d) and not d.get("_unknown") and d.get("name") not in ("STRUGGLE",)


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


def fixed_moves(game, poke):
    """A Pokemon with one set of moves and nothing else, or None. Nown (Jordan, 11-04): only
    Found Power, even when the Unown it came from knew Hidden Power."""
    if int(poke.id) == game.loader.get_special_id("NOWN", 3025):
        return ["FOUND-POWER"]
    return None


def ensure_moves(game, poke):
    fixed = fixed_moves(game, poke)
    if fixed:
        poke.moves = list(fixed)
        return poke.moves
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
        name = OLD_NAMES.get(name, name)
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
    plus its learnset up to its level, its current moves included, and the moves of the TMs in your
    Bag it can learn (a TM unlocks its move for every Pokemon that can learn it: Jordan, 11-04)."""
    fixed = fixed_moves(game, poke)
    if fixed:
        poke.move_pool = list(fixed)
        return poke.move_pool
    pool = list(getattr(poke, "move_pool", None) or [])
    for name in learnable(game, poke) + list(ensure_moves(game, poke)) + tm_moves(game, poke):
        if name not in pool:
            pool.append(name)
    poke.move_pool = pool
    return pool


def tm_moves(game, poke):
    """The moves of the TMs you have that this Pokemon can learn."""
    from src.pokemon import tms
    story = getattr(game, "story_manager", None)
    if story is None or getattr(poke, "is_egg", False):
        return []
    return [tms.move_of(game, k) for k in sorted(tms.owned(story))
            if tms.can_learn(game, poke, k) and usable(info(game, tms.move_of(game, k)))]


def set_move(poke, slot, name):
    """Put a pool move in slot 0-3 (or add it while it knows fewer than four). Returns True if set."""
    moves = poke.moves
    if name in moves:
        return False
    from src.pokemon import pp
    if slot is None or slot >= len(moves):
        if len(moves) >= MAX_MOVES:
            return False
        moves.append(name)
        pp.forget(poke, name)  # (a move set in comes with full PP)
        return True
    moves[slot] = name
    pp.forget(poke, name)
    return True




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
