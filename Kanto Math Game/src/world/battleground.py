"""The Battleground in the Survival Area (Pokemon Platinum, 11-24, Sinnoh S7a; built by kanto_handoff/sinnoh_map_tools/
s_s7_survival.py): Buck's house, open after Charon is arrested at Stark Mountain. Four trainers stand in it each day, out of
the eight Gym Leaders and Platinum's five walking partners, each battled once a day (their Platinum rematch teams). Platinum
draws the four at random each day; here each of its four spots has its own group and the day picks one from each, so the
same four stand there all day and someone new may come tomorrow. Barry waits outside and battles on weekends (Platinum's).

Conditions ("world:battleground:<arg>"): a trainer's key (they're here today), "weekend" / "weekday" (by the real clock)."""
import datetime
import hashlib

SPOTS = [["roark", "gardenia", "maylene"],
         ["wake", "fantina", "byron"],
         ["candice", "volkner", "cheryl"],
         ["riley", "marley", "mira", "buck"]]


def _today():
    return datetime.date.today()


def picks(day=None):
    """The four standing in the Battleground on that day (today by default)."""
    d = (day or _today()).isoformat()
    out = []
    for i, group in enumerate(SPOTS):
        h = int(hashlib.md5(f"battleground:{d}:{i}".encode()).hexdigest(), 16)
        out.append(group[h % len(group)])
    return out


def condition(story, arg):
    if arg == "weekend":
        return _today().weekday() >= 5
    if arg == "weekday":
        return _today().weekday() < 5
    return arg in picks()
