"""XD's Battle CDs (Jordan 11-20, Orre Q12 + batch 5: all 50 as puzzle battles, played at the Pokemon HQ Lab, each CD found
where XD hides it - kanto_handoff/orre_check/BATTLE_CDS.md).

A CD is a key item BATTLE_CD_NN. Its battle (assets/orre_battle_cds.json, from the XD disc): you are lent the CD's own team
(species, level, moves, held items: never your own Pokemon), the opponent has its own, single or double, and some CDs
have a turn limit. Your team is put back the moment the battle ends, won or lost; nothing is caught, earned or lost.
A CD is cleared by winning within its turn limit (flag battle_cd_NN_cleared).

    choices(game)              -> [(label, key)] for the CDs you own, for a pick list
    start(game, key)           -> the battle's intro state (your team is swapped for the CD's)
    after_battle(game, battle, won) -> lines; puts your team back (src/states/battle.py exit_battle calls it)"""
import json
import os

_CACHE = {}


def data(game):
    if "cds" not in _CACHE:
        path = os.path.join(game.assets.assets_dir, "orre_battle_cds.json")
        _CACHE["cds"] = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    return _CACHE["cds"]


def item_key(key):
    return f"BATTLE_CD_{key}"


def cleared(game, key):
    return bool(game.story_manager.story_flags.get(f"battle_cd_{key}_cleared"))


def owned(game):
    inv = game.story_manager.inventory
    return [k for k in sorted(data(game)) if inv.get(item_key(k), 0) > 0]


def choices(game):
    out = []
    for k in owned(game):
        cd = data(game)[k]
        mark = " (cleared)" if cleared(game, k) else ""
        out.append((f"CD {k}: {cd['title']}{mark}", k))
    return out


def describe(game, key):
    cd = data(game)[key]
    stars = "*" * int(cd.get("stars") or 0) or "-"
    return [f"Battle CD {key}: {cd['title']}  [{stars}]", cd.get("tagline") or "", cd["rule"]]


def _mon(game, spec):
    from src.pokemon.data import Pokemon
    mon = Pokemon(game.loader.fetch_specific(int(spec["id"])), game.assets, size_mult=2.5)
    mon.level = int(spec["level"])
    if spec.get("moves"):
        mon.moves = list(spec["moves"])
    if spec.get("item"):
        mon.held_item = spec["item"]
    mon.current_hp = mon.get_max_hp()
    mon.battle_cd_loan = True
    return mon


def start(game, key):
    """Swap your team for the CD's and return the battle (its intro first)."""
    from src.states.overworld.common import _start_event_battle
    cd = data(game)[key]
    story = game.story_manager
    if getattr(story, "_battle_cd", None) is None:
        story._battle_cd = {"key": key, "team": story.player_team}
    story.player_team = [_mon(game, s) for s in cd["you"]]
    foe = cd["foe"]
    info = {"name": cd.get("foe_name") or "Sim Trainer", "class": "SIM_TRAINER", "sprite": "orre_scientist.png",
            "team": [s["id"] for s in foe], "levels": [s["level"] for s in foe],
            "team_moves": [s.get("moves") or [] for s in foe], "team_items": [s.get("item") for s in foe],
            "double": bool(cd.get("double")), "rewards": {"balls": 0},
            "_intro_lines": [f"Battle CD {key}: {cd['title']}", cd["rule"]],
            "dialogue": {"player_won": ["The simulation ends."], "player_lost": ["The simulation ends."]}}
    intro = _start_event_battle(game, story.current_area_key, info, None)
    battle = intro.next_state
    battle.frontier = "battle_cd"   # (no whiting out, as a Battle Frontier streak: src/states/battle.py)
    battle.battle_cd = key
    return intro


def restore(game):
    """Your own team back (also safe to call when no CD is running)."""
    story = game.story_manager
    saved = getattr(story, "_battle_cd", None)
    if saved is not None:
        story.player_team = saved["team"]
        story._battle_cd = None
        for p in story.player_team:
            if p is not None:
                p.heal_full()


def _give_prize(game, prize):
    """A CD's prize: an item key, or "tm:<MOVE>" (XD's TM by its move, our TM number - src/pokemon/tms.py)."""
    story = game.story_manager
    who = getattr(game, "player_name", "You")
    if str(prize).startswith("tm:"):
        from src.pokemon import tms
        tm = tms.key_for_move(game, prize[3:])
        if not tm:
            return []
        story.add_item(tm, 1)
        return [f"{who} received {tms.label(game, tm)}!"]
    from src.pokemon import forms
    story.add_item(prize, 1)
    return [f"{who} received the {forms.item_label(prize).upper()}!"]


def after_battle(game, battle, won):
    key = getattr(battle, "battle_cd", None)
    restore(game)
    if key is None:
        return []
    cd = data(game).get(key) or {}
    limit = int(cd.get("turn_limit") or 0)
    turns = int(getattr(battle, "turn_count", 0) or 0)
    if won and limit and turns > limit:
        return [f"You won, but it took {turns} turns. Battle CD {key} needs a win within {limit}. Try again!"]
    if won:
        first = not cleared(game, key)
        game.story_manager.story_flags[f"battle_cd_{key}_cleared"] = True
        lines = [f"Battle CD {key} cleared!" + (" Nicely done." if first else "")]
        prize = cd.get("prize") if first else None   # (XD's prize for each CD, the first clear only: Serebii's CD pages, 11-24)
        if prize:
            lines += _give_prize(game, prize)
        return lines
    return [f"Battle CD {key} not cleared. Your own team is back. Try again any time!"]
