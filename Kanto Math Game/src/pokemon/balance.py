# [REF-0078: Battle damage]
"""
Damage works like the main-series games (Gen 6+), step by step with the same rounding:

    base   = floor(floor(floor(2 x Lv / 5 + 2) x Power x Atk / Def) / 50) + 2
    weather  x1.5 / x0.5 (rain, sun; 0 when extreme weather makes the move fizzle)
    crit     x1.5, 1 in 24
    random   x(85..100)/100
    STAB     x1.5 when the move matches the attacker's type
    type     effectiveness from the type chart
    then at least 1 HP (unless the move fizzled)

Atk/Def are the real stats at each Pokemon's level (Attack/Defense or Sp. Atk/Sp. Def by
the move's category). Sandstorm raises Rock types' Sp. Def and snow raises Ice types'
Defense by half, as in the games. There are no caps or extra multipliers.
"""
import math
import random

STAB = 1.5
CRIT_CHANCE, CRIT_MULT = 1 / 24, 1.5
ROLL_MIN, ROLL_MAX = 85, 100
DEFAULT_POWER = 40

# Legendary and Mythical Pokemon (and Ultra Beasts). Legendaries that evolve
# (Type: Null, Cosmog, Cosmoem, Poipole, Kubfu, Meltan) are left out.
LEGENDARY_IDS = (
    {144, 145, 146, 150, 151, 243, 244, 245, 249, 250, 251}
    | set(range(377, 387))
    | set(range(480, 495))
    | set(range(638, 650))
    | set(range(716, 722))
    | {773} | set(range(785, 789)) | {791, 792} | set(range(793, 803)) | set(range(804, 808)) | {809}
    | {888, 889, 890, 892, 893, 894, 895, 896, 897, 898, 905}
    | {1001, 1002, 1003, 1004, 1007, 1008, 1014, 1015, 1016, 1017, 1024, 1025}
)


def is_legendary(pid):
    try:
        return int(pid) in LEGENDARY_IDS
    except (TypeError, ValueError):
        return False


def poke_round(x):
    """The games round halves down."""
    return math.ceil(x - 0.5)


def damage(att_level, power, attack, defense, stab=True, effectiveness=1.0, weather=1.0, crit=None, roll=None):
    """HP lost to one hit. Returns (damage, was_crit). 0 if the weather made the move fizzle."""
    if weather == 0:
        return 0, False
    crit = (random.random() < CRIT_CHANCE) if crit is None else crit
    roll = random.randint(ROLL_MIN, ROLL_MAX) if roll is None else roll
    dmg = math.floor(math.floor(math.floor(2 * att_level / 5 + 2) * (power or DEFAULT_POWER)
                                * attack / max(1, defense)) / 50) + 2
    if weather != 1:
        dmg = poke_round(dmg * weather)
    if crit:
        dmg = math.floor(dmg * CRIT_MULT)
    dmg = math.floor(dmg * roll / 100)
    if stab:
        dmg = poke_round(dmg * STAB)
    dmg = math.floor(dmg * effectiveness)
    return max(1, dmg), crit
