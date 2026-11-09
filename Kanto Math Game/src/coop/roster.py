"""Co-op's Pokemon and fights, on the host (Jordan, 11-08): what a guest may borrow (up to 6), and the wild Pokemon a guest
is fighting. The fight itself runs on the guest's device; the host hands out the Pokemon, holds it off the map meanwhile,
checks what comes back, and is the only one who saves. A lent Pokemon waits in the PC (locked), so a crash can't lose it."""
from src.coop import world

MAX_BORROW = 6
LEVEL_JUMP = 10     # the most levels one fight can believably add
REACH = 2           # tiles: how near a guest must be to start a fight
TOAST_FRAMES = 200


def _state(host):
    return host.__dict__.setdefault("roster", {"lent": {}, "fights": {}, "uids": 0, "later": []})


def toast(game, text):
    game.coop_toast = (str(text), TOAST_FRAMES)


def _uid(host, p):
    if not getattr(p, "coop_uid", None):
        st = _state(host)
        st["uids"] += 1
        p.coop_uid = st["uids"]
    return p.coop_uid


def _healthy(p):
    return p is not None and p.current_hp > 0 and not getattr(p, "is_egg", False)


def _free(p):
    return p is not None and not getattr(p, "is_egg", False) and getattr(p, "coop_lent", None) is None


def _spare_party(story):
    """The party without the host's own lead: the host always keeps a Pokemon that can fight."""
    keep = next((p for p in story.player_team if _healthy(p)), None)
    return [p for p in story.player_team if p is not keep and _free(p)]


def rows(game, host):
    """What can be borrowed now, for the guest's picking screen."""
    story = game.story_manager
    out = []
    for group, party in ((_spare_party(story), True), ([p for p in story.pc_pokemon if _free(p)], False)):
        for p in group:
            out.append({"uid": _uid(host, p), "id": int(p.id), "form": str(p.form), "shiny": bool(p.is_shiny),
                        "name": str(p.display_name), "level": int(p.level), "hp": int(p.current_hp),
                        "max": int(p.get_max_hp()), "party": party})
    return out


def _to_pc(story, p):
    """Out of the party, to the PC as it is (no free heal)."""
    story.player_team.remove(p)
    slot = next((i for i, m in enumerate(story.pc_pokemon) if m is None), None)
    if slot is None:
        story.pc_pokemon.append(p)
    else:
        story.pc_pokemon[slot] = p


def _settings(story):
    return {"badges": story.badges, "active_badge_region": story.active_badge_region,
            "can_catch": bool(story.catch_unlocked()), "math_difficulty": story.math_difficulty,
            "story_flags": story.story_flags, "level_cap_mode": getattr(story, "level_cap_mode", "STORY")}


def lend(game, host, pid, uids):
    st, story = _state(host), game.story_manager
    mine = st["lent"].setdefault(pid, [])
    party, pc = _spare_party(story), [p for p in story.pc_pokemon if _free(p)]
    out = []
    for uid in uids if isinstance(uids, list) else []:
        if len(mine) >= MAX_BORROW:
            break
        p = next((m for m in party + pc if getattr(m, "coop_uid", None) == uid and _free(m)), None)
        if p is None:
            continue
        from_party = p in party
        if from_party:
            _to_pc(story, p)
        p.coop_lent = pid
        mine.append({"mon": p, "party": from_party})
        out.append({"uid": uid, "rec": story._pokemon_record(p)})
    host.send(pid, {"t": "event", "lent": out, "settings": _settings(story)})


def _give_back(game, host, pid):
    st, story = _state(host), game.story_manager
    for entry in st["lent"].pop(pid, []):
        p = entry["mon"]
        p.coop_lent = None
        if entry["party"] and len(story.player_team) < 6 and p in story.pc_pokemon:
            story.pc_pokemon[story.pc_pokemon.index(p)] = None
            story.player_team.append(p)


def release(game, host, pid):
    """A guest has gone for good: wild Pokemon back on the map, borrowed Pokemon home."""
    st = _state(host)
    for eid in [e for e, f in st["fights"].items() if f["pid"] == pid]:
        f = st["fights"].pop(eid)
        f["floor"].movers.append(f["mover"])
    st["later"].append(lambda: _give_back(game, host, pid))


# ------------------------------------------------------------------ fights
def _fighting(st, pid):
    return any(f["pid"] == pid for f in st["fights"].values())


def _refuse(host, pid, why):
    host.send(pid, {"t": "event", "fight_no": why})


def start_fight(game, host, pid, uid):
    st, story = _state(host), game.story_manager
    ds = getattr(game, "dungeon_state", None)
    at = host.guests[pid].get("at")
    if not any(_healthy(e["mon"]) for e in st["lent"].get(pid, [])):
        return _refuse(host, pid, "You need a Pokemon that can fight.")
    if _fighting(st, pid):
        return _refuse(host, pid, "You're already in a fight.")
    if ds is None or not hasattr(ds, "run") or not at or at[0] != ds.area_key or at[1] != ds.run.index:
        return _refuse(host, pid, "It's too far away.")
    floor = ds.run.floor
    mover = next((m for m in floor.movers if m.kind == "wild" and id(m) == uid), None)
    if mover is None:
        return _refuse(host, pid, "It's gone.")
    pending = getattr(ds, "pending", None) or (None, None)
    if mover is getattr(ds, "encounter", None) or mover is pending[1]:
        return _refuse(host, pid, "Someone else is fighting that one.")
    if abs(mover.x - at[2]) + abs(mover.y - at[3]) > REACH:
        return _refuse(host, pid, "It's too far away.")
    floor.movers.remove(mover)  # (off the map till the fight ends: nobody else can meet it)
    game.data.mark_seen(mover.payload.id)
    eid = max(list(st["fights"]) + [st.get("last", 0)]) + 1
    st["last"] = eid
    st["fights"][eid] = {"pid": pid, "floor": floor, "mover": mover}
    host.send(pid, {"t": "event", "fight": {"eid": eid, "rec": story._pokemon_record(mover.payload), "area": ds.area_key,
                                            "bg": ds._get_battle_background_for_area(),
                                            "x": mover.x, "y": mover.y, "on_map": bool(ds._ow_on())}})


def _apply_team(game, host, pid, team):
    """What a fight did to the borrowed Pokemon, if it's believable; only Pokemon this guest really holds."""
    held = {getattr(e["mon"], "coop_uid", None): e["mon"] for e in _state(host)["lent"].get(pid, [])}
    for rec in team if isinstance(team, list) else []:
        p = held.get(rec.get("uid")) if isinstance(rec, dict) else None
        if p is None:
            continue
        try:
            level, xp = int(rec["level"]), int(rec["xp"])
            if p.level <= level <= min(100, p.level + LEVEL_JUMP) and xp >= 0:
                if level > p.level:
                    p.evo_due = True
                p.level, p.xp = level, xp
                p.max_hp = p.get_max_hp()
            p.current_hp = max(0, min(int(rec["hp"]), p.get_max_hp()))
            status = rec.get("status")
            p.status = status if status is None or isinstance(status, str) else p.status
            p.sleep_turns = max(0, int(rec.get("sleep_turns", 0)))
            p.friendship = max(p.friendship, min(int(rec.get("friendship", 0)), p.friendship + 20))
            moves, pool = rec.get("moves"), rec.get("move_pool")
            if isinstance(moves, list) and 0 < len(moves) <= 4 and all(isinstance(m, str) for m in moves):
                p.moves = list(moves)
            if isinstance(pool, list) and all(isinstance(m, str) for m in pool):
                p.move_pool = list(pool)
        except (KeyError, TypeError, ValueError):
            continue


def _keep_catch(game, p, ball):
    """A guest's catch: the host's, in the PC, the Pokedex and the save."""
    from src.pokemon import catching
    story = game.story_manager
    p.caught_region = story.get_current_region()
    p.caught_level = p.level
    story.deposit_to_pc(p)
    catching.after_catch(game, p, ball if ball in catching.BALLS else catching.POKE)
    key = f"201_{'a' if p.form.lower() == 'normal' else p.form.lower()}" if str(p.id) == "201" else str(p.id)
    story.catch_counts[key] = story.catch_counts.get(key, 0) + 1
    game.loader.total_caught += 1
    ds = getattr(game, "dungeon_state", None)
    if ds is not None:
        ds.total_caught = game.loader.total_caught
    lines = story.catch_milestones()
    game.data.add_pokemon(p)
    if p.is_shiny:
        game.data.add_shiny()
    game.update_save_data()
    game.data.save()
    return lines


def end_fight(game, host, pid, msg):
    st = _state(host)
    eid = msg.get("eid")
    fight = st["fights"].get(eid)
    if fight is not None and fight["pid"] == pid:  # (each fight counts once: a repeat just gets its answer again)
        del st["fights"][eid]
        _apply_team(game, host, pid, msg.get("team"))
        name = host.guests[pid]["name"]
        mover, outcome = fight["mover"], msg.get("outcome")
        mon = str(mover.payload.display_name).upper()
        if outcome == "caught":
            lines = _keep_catch(game, mover.payload, msg.get("ball"))
            toast(game, f"{name} caught {mon}! Sent to the PC." if not lines else f"{name} caught {mon}! {lines[-1]}")
        elif outcome == "beaten":
            toast(game, f"{name} beat a wild {mon}.")
        else:
            fight["floor"].movers.append(mover)
    host.send(pid, {"t": "event", "fight_done": eid})


# ------------------------------------------------------------------ from the game loop
def handle(game, host, pid, msg):
    if msg.get("roster_ask"):
        host.send(pid, {"t": "event", "roster": rows(game, host)})
    elif "borrow" in msg:  # (not in the middle of the host's own battle: its party can't change then)
        _state(host)["later"].append(lambda: lend(game, host, pid, msg["borrow"]) if pid in host.guests else None)
    elif "watch" in msg:  # (the guest's fight, for the host to watch)
        host.guests[pid]["watch"] = msg["watch"] if isinstance(msg["watch"], dict) else None
    elif "fight" in msg:
        start_fight(game, host, pid, msg["fight"])
    elif "fight_end" in msg and isinstance(msg["fight_end"], dict):
        end_fight(game, host, pid, msg["fight_end"])


def tick(game, host):
    st = _state(host)
    if st["later"] and world.where(game) is not None:
        for job in st["later"]:
            job()
        st["later"] = []
