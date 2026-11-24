"""Partner Pokemon beside the important people on the walked maps (Jordan 11-24, region/systems): Gym Leaders, the Elite
Four and Champions, rivals, and the villain teams' bosses, admins and commanders each have their ace - the highest-level
Pokemon of the team they battle you with - standing beside them, following them a step behind as they walk (npc.py's
"trail"). Grunts and other trainers don't. Jessie and James already have their Meowth (src/world/escorts.py).

Who counts is read from the people's own battle data, whatever the region: a Gym's leader (action GYM: the area's
gym "leader"), a League room (action LEAGUE: the area's gym "trainers" by "index", then the "leader"), and any person or
trainer whose battle class is one of CLASSES. Added on the town maps (walk_town.py) and the route maps (dungeon.py)."""
import re

CLASSES = re.compile(r"GYM_LEADER|ELITE_FOUR|CHAMPION|RIVAL|ADMIN|BOSS|EXEC|COMMANDER|LOREKEEPER|_LEADER$|^LEADER$")
NOT = re.compile(r"GRUNT|PREGYM|SAGE|SCIENTIST")
SKIP_NAMES = re.compile(r"jessie|james|meowth", re.I)   # (their Meowth: escorts.py)


def _battle_of(opt):
    """The battle data a person's option carries (its event's battle, its own), or None."""
    if not isinstance(opt, dict):
        return None
    ev = opt.get("event")
    if isinstance(ev, dict) and isinstance(ev.get("battle"), dict):
        return ev["battle"]
    if isinstance(opt.get("battle"), dict):
        return opt["battle"]
    if opt.get("team") and (opt.get("class") or opt.get("trainer_class")):   # (a route trainer's own entry)
        return opt
    return None


def trainer_of(area, opt):
    """(name, team, levels) of the important person behind opt (an option of a walked town's person, a route map's
    figure or trainer entry) in the area's data, or None for anyone else."""
    if not isinstance(opt, dict):
        return None
    if "any" in opt:   # (someone with several options by the story: the first that battles)
        for o in opt["any"]:
            got = trainer_of(area, o)
            if got:
                return got
        return None
    action = str(opt.get("action") or "").upper()
    gym = (area or {}).get("gym") or {}
    data = None
    if action == "GYM":
        data = gym.get("leader")
    elif action == "LEAGUE":
        i, trainers = int(opt.get("index") or 0), gym.get("trainers") or []
        data = trainers[i] if i < len(trainers) else gym.get("leader")
    else:
        b = _battle_of(opt)
        cls = str((b or {}).get("class") or (b or {}).get("trainer_class") or "").upper()
        if b and CLASSES.search(cls) and not NOT.search(cls):
            data = b
    if not isinstance(data, dict):
        return None
    name = str(data.get("name") or opt.get("text") or "")
    if SKIP_NAMES.search(name) or SKIP_NAMES.search(str(opt.get("text") or "")):
        return None
    team = [t for t in (data.get("team") or []) if t]
    if not team:
        return None
    return name, team, list(data.get("levels") or [])


def ace(team, levels):
    """The highest-level Pokemon of a team (the last one of them, if several share it: the one saved for last)."""
    best, best_lv = None, -1
    for i, pid in enumerate(team):
        lv = levels[i] if i < len(levels) else 0
        if lv >= best_lv:
            best, best_lv = pid, lv
    try:
        return int(best)
    except (TypeError, ValueError):
        return None


def partner_name(game, pid):
    """The species' name as a map person's text (it's drawn as that Pokemon's overworld sprite)."""
    raw = game.loader.fetch_specific(int(pid)) if pid else None
    return str((raw or {}).get("name", "")).replace("-", " ").title() if raw else None


def partner_for(game, area, opt):
    """(the partner's map text, the trainer's name) for an important person's option, or None."""
    got = trainer_of(area, opt)
    if not got:
        return None
    pid = ace(got[1], got[2])
    name = partner_name(game, pid) if pid else None
    return (name, got[0]) if name else None


def line(owner, species):
    """What you're told when you talk to the partner (our own words)."""
    who = owner.split(" (")[0]
    return [f"{who}'s {species.upper()} is watching you closely."]
