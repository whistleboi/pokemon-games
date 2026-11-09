"""Co-op Max Raids (Jordan, 11-08): the host's raid runs on the host's game; up to 3 guests join in place of the computer
teammates. Each picks their own move and answers their own math each turn; the boss can hit any of them. All on the host:
guests send what they chose, and borrowed Pokemon already live here."""
import random
import time

from src.pokemon import balance, moves as movelib
from src.pokemon.mechanics import TypeAdvantage

MAX_GUESTS = 3
WAIT_SECONDS = 20       # how long a turn waits for friends to answer
WRONG_POWER = 0.6       # a wrong answer weakens the move, as it does for the host
WRONG_CAP = 0.49        # ...and at most this share of the boss's HP


def is_raid(battle):
    foe = getattr(battle, "opponent_pokemon", None)
    return foe is not None and bool(getattr(foe, "raid_stage", None)) and getattr(battle, "raid_allies", None) is not None


def _state(battle):
    return battle.__dict__.setdefault("coop_raid", {"humans": {}, "turn": 1, "until": 0, "said": False})


def humans(battle):
    return battle.__dict__.get("coop_raid", {}).get("humans", {})


def info(battle):
    """What guests need: who's in it and which turn it is."""
    st = _state(battle)
    out = []
    for pid, h in st["humans"].items():
        p = h["mon"]
        out.append({"pid": pid, "who": h["name"], "name": str(p.display_name), "id": int(p.id), "form": str(p.form), "shiny": bool(p.is_shiny), "level": int(p.level),
                    "status": p.status, "hp": max(0, int(p.current_hp)), "max": int(p.get_max_hp()), "moves": list(battle._battle_moves(p)), "answered": h["plan"] is not None})
    return {"turn": st["turn"], "humans": out, "open": len(out) < MAX_GUESTS}


def _lead(mons):
    return next((p for p in mons if p.current_hp > 0 and not getattr(p, "is_egg", False)), None)


def join(game, host, pid):
    from src.coop import roster
    battle, st = game.current_state, roster._state(host)

    def no(why):
        host.send(pid, {"t": "event", "fight_no": why})
    if not is_raid(battle) or pid not in host.guests:
        return no("That raid is over.")
    raid = _state(battle)
    if pid in raid["humans"]:
        return
    if len(raid["humans"]) >= MAX_GUESTS:
        return no("That raid is full.")
    if roster._fighting(st, pid):
        return no("You're already in a fight.")
    p = _lead([e["mon"] for e in st["lent"].get(pid, [])])
    if p is None:
        return no("You need a Pokemon that can fight.")
    bots = [a for a in battle.raid_allies if not any(a[2] is h["mon"] for h in raid["humans"].values())]
    if len(battle.raid_allies) >= MAX_GUESTS and bots:  # (a friend takes a computer teammate's place)
        battle.raid_allies.remove(bots[0])
    name = host.guests[pid]["name"]
    raid["humans"][pid] = {"mon": p, "name": name, "plan": None}
    battle.raid_allies.append((name, None, p))
    st.setdefault("raiders", set()).add(pid)
    game.coop_raid_battle = battle
    host.send(pid, {"t": "event", "raid_joined": True})


def _forget(host, pid):
    from src.coop import roster
    roster._state(host).get("raiders", set()).discard(pid)


def drop(game, host, pid):
    """A guest has left the raid or the session."""
    battle = getattr(game, "coop_raid_battle", None)
    if battle is None or pid not in humans(battle):
        return
    h = humans(battle).pop(pid)
    battle.raid_allies[:] = [a for a in battle.raid_allies if a[2] is not h["mon"]]
    _forget(host, pid)


def submit(game, host, pid, msg):
    battle = getattr(game, "coop_raid_battle", None)
    h = humans(battle).get(pid) if battle is not None else None
    if h is None or not isinstance(msg, dict) or msg.get("turn") != _state(battle)["turn"]:
        return
    if msg.get("move") in battle._battle_moves(h["mon"]):
        h["plan"] = {"move": msg["move"], "right": bool(msg.get("right"))}


def on_turn(battle):
    """A turn is starting: it waits for friends who haven't answered yet (not for long)."""
    raid = _state(battle)
    if any(h["mon"].current_hp > 0 for h in raid["humans"].values()):
        raid["until"], raid["said"] = time.monotonic() + WAIT_SECONDS, False
        battle.turn_actions.insert(0, lambda: _wait(battle))


def _wait(battle):
    from src.coop import roster
    raid = _state(battle)
    missing = [h for h in raid["humans"].values() if h["plan"] is None and h["mon"].current_hp > 0]
    if missing and time.monotonic() < raid["until"]:
        if not raid["said"]:
            raid["said"] = True
            roster.toast(battle.game, "Waiting for your friends...")
        battle.feedback_timer = 4
        battle.turn_actions.insert(0, lambda: _wait(battle))


def plan_for(battle, mon):
    """None: a computer teammate. False: a friend sitting this turn out. Else what they chose."""
    h = next((x for x in humans(battle).values() if x["mon"] is mon), None)
    if h is None:
        return None
    return (h["plan"] or False) if mon.current_hp > 0 else False


def _hit(attacker, target, move, chart):
    special = str(move.get("category") or "").upper() == "SPECIAL"
    eff = chart.get_multiplier(move.get("type"), target.types or [])
    dmg, _crit = balance.damage(attacker.level, move.get("power") or 40, attacker.stat_value("SPATK" if special else "ATTACK"),
                                target.stat_value("SPDEF" if special else "DEFENSE"), stab=move.get("type") in (attacker.types or []),
                                effectiveness=eff)
    return dmg if eff else 0, eff


def human_attack(battle, name, mon, plan):
    """A friend's chosen move on the boss."""
    foe = battle.opponent_pokemon
    chart = TypeAdvantage(battle.game.loader.area_data.get("TYPE_CHART", {}))
    move = movelib.info(battle.game, plan["move"])
    lines = [f"{name}'s {mon.display_name.upper()} used {str(move.get('name', plan['move'])).replace('-', ' ')}!"]
    if not (move.get("power") or 0):
        return lines
    dmg, eff = _hit(mon, foe, move, chart)
    if not plan["right"]:
        dmg = min(int(dmg * WRONG_POWER), int(battle.opp_max_hp * WRONG_CAP))
    if eff:
        dmg = max(1, dmg)
    battle.opponent_hp = max(0, battle.opponent_hp - dmg)
    foe.current_hp = battle.opponent_hp
    if eff > 1:
        lines.append("It's super effective!")
    return lines


def boss_strikes(battle):
    """The boss also goes for one of the friends."""
    from src.coop import roster
    raid, foe = _state(battle), battle.opponent_pokemon
    alive = [(pid, h) for pid, h in raid["humans"].items() if h["mon"].current_hp > 0]
    if not alive or battle.opponent_hp <= 0:
        return []
    pid, h = random.choice(alive)
    target, chart = h["mon"], TypeAdvantage(battle.game.loader.area_data.get("TYPE_CHART", {}))
    infos = [movelib.info(battle.game, m) for m in (foe.moves or [])]
    infos = [i for i in infos if (i.get("power") or 0) > 0] or [movelib.info(battle.game, "TACKLE")]
    move = max(infos, key=lambda i: (i.get("power") or 0) * chart.get_multiplier(i.get("type"), target.types or []))
    dmg, _eff = _hit(foe, target, move, chart)
    target.current_hp = max(0, target.current_hp - dmg)
    lines = [f"{foe.display_name.upper()} hit {h['name']}'s {target.display_name.upper()}!"]
    if target.current_hp <= 0:
        lines.append(f"{target.display_name.upper()} fainted!")
        host = battle.game.coop_host
        team = [e["mon"] for e in roster._state(host)["lent"].get(pid, [])]
        nxt = _lead(team)
        if nxt is None:
            lines.append(f"{h['name']} is out of the raid!")
        else:
            battle.raid_allies[:] = [(a[0], a[1], nxt) if a[2] is target else a for a in battle.raid_allies]
            h["mon"] = nxt
            lines.append(f"{h['name']} sent out {nxt.display_name.upper()}!")
    return lines


def next_turn(battle):
    raid = _state(battle)
    for h in raid["humans"].values():
        h["plan"] = None
    raid["turn"] += 1


def finish(game, host):
    """Back on the map after a raid: friends get their Pokemon's XP and the team as it now is."""
    from src.coop import roster
    from src.pokemon import growth
    from src.pokemon.evolution import base_id
    from src.world import levels
    battle = getattr(game, "coop_raid_battle", None)
    game.coop_raid_battle = None
    if battle is None:
        return
    foe = battle.opponent_pokemon
    won = battle.opponent_hp <= 0 or battle.player_won
    base = game.assets.movesets.get(str(base_id(foe)), {}).get("base_xp") or 100
    cap = levels.xp_cap(game.story_manager)
    for pid, h in list(humans(battle).items()):
        _forget(host, pid)
        if won:
            for e in roster._state(host)["lent"].get(pid, []):
                if e["mon"].current_hp > 0 and e["mon"].level < cap:
                    e["mon"].gain_xp(max(1, int(growth.battle_xp(base, foe.level, e["mon"].level, trainer=False))), cap)
        if pid in host.guests:
            roster.lend(game, host, pid, [], replace=True)
            host.send(pid, {"t": "event", "raid_over": True, "won": bool(won)})
