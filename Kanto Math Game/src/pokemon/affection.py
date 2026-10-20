# [REF-0074: Pokemon-Amie affection]
"""
Kalos's Pokemon-Amie: affection (0-255, shown as 0-5 hearts) grows by petting and
playing with a Pokemon in Pokemon-Amie (Kalos Pokemon Centers). Like X/Y, a
Pokemon that loves its trainer helps out in battle, in every region:

    2+ hearts  1.2x battle XP
    3+ hearts  may hang on with 1 HP after a knockout blow (10% / 15% / 20%)
    4+ hearts  may dodge an attack (10% at 4, 20% at 5) and shake off a status (20%)
    5 hearts   critical hits twice as often
"""
import datetime
import random

MAX_AFFECTION = 255
HEART_AT = (50, 100, 150, 200, 255)
DAILY_CAP = 100  # affection from Pokemon-Amie per Pokemon per day

ENDURE = {3: 0.10, 4: 0.15, 5: 0.20}
EVADE = {4: 0.10, 5: 0.20}
CURE_CHANCE = 0.20

ENDURE_TEXT = "{n} toughed it out so you wouldn't feel sad!"
EVADE_TEXT = "{n} avoided the attack in time to respond to your call!"
CURE_TEXT = "{n} shook off its {s} so you wouldn't worry!"
STATUS_NAME = {"burn": "burn", "paralysis": "paralysis", "poison": "poison", "sleep": "drowsiness",
               "freeze": "ice", "toxic": "poison"}


def get(poke):
    return int(getattr(poke, "affection", 0) or 0)


def hearts(poke):
    a = get(poke)
    return sum(1 for t in HEART_AT if a >= t)


def gain_today(poke):
    """Affection already earned in Pokemon-Amie today (resets each day)."""
    today = datetime.date.today().isoformat()
    if poke.counters.get("amie_day") != today:
        return 0
    return poke.counters.get("amie_gain", 0)


def add(poke, amount, daily=True):
    """Raise affection (Amie gains respect the daily cap). Returns the amount actually added."""
    if daily:
        today = datetime.date.today().isoformat()
        if poke.counters.get("amie_day") != today:
            poke.counters["amie_day"], poke.counters["amie_gain"] = today, 0
        amount = min(amount, DAILY_CAP - poke.counters["amie_gain"])
    amount = max(0, min(amount, MAX_AFFECTION - get(poke)))
    poke.affection = get(poke) + amount
    if daily:
        poke.counters["amie_gain"] += amount
    return amount


def xp_mult(poke):
    return 1.2 if hearts(poke) >= 2 else 1.0


def endures(poke):
    return random.random() < ENDURE.get(hearts(poke), 0)


def evades(poke):
    return random.random() < EVADE.get(hearts(poke), 0)


def shakes_off_status(poke):
    return hearts(poke) >= 4 and random.random() < CURE_CHANCE


def crit_chance(poke, base):
    return base * 2 if hearts(poke) >= 5 else base


def mood(poke):
    """A line for the Amie screen."""
    return ("is curious about you.", "is starting to warm up to you.", "seems to like you!",
            "really likes you!", "loves being around you!", "adores you more than anything!")[hearts(poke)]
