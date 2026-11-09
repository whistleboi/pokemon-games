"""Co-op's Pokemon and fights, on the host (Jordan, 11-08): what a guest may borrow (up to 6), and the wild Pokemon a guest
is fighting. The fight itself runs on the guest's device; the host hands out the Pokemon, holds it off the map meanwhile,
checks what comes back, and is the only one who saves. A lent Pokemon waits in the PC (locked), so a crash can't lose it."""
import types

from src.coop import raid, travel, world

MAX_BORROW = 6
LEVEL_JUMP = 10     # the most levels one fight can believably add
REACH = 2           # tiles: how near a guest must be to start a fight
TOAST_FRAMES = 200
REVIVES = ("REVIVE", "MAX_REVIVE")
TETHER = 4          # tiles: how far someone who's fainted out can be from a friend who can fight
START_BALLS = 10    # the Poke Balls a guest starts with (those aren't merged)


def _state(host):
    return host.__dict__.setdefault("roster", {"lent": {}, "fights": {}, "uids": 0, "later": [], "ledgers": {}})


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


def rows(game, host, pid=None):
    """What can be borrowed now, for the guest's picking screen; first what this guest already holds."""
    story = game.story_manager
    out = []
    held = [e["mon"] for e in _state(host)["lent"].get(pid, [])]
    for group, party, mine in ((held, False, True), (_spare_party(story), True, False),
                               ([p for p in story.pc_pokemon if _free(p)], False, False)):
        for p in group:
            out.append({"uid": _uid(host, p), "id": int(p.id), "form": str(p.form), "shiny": bool(p.is_shiny),
                        "name": str(p.display_name), "level": int(p.level), "hp": int(p.current_hp),
                        "max": int(p.get_max_hp()), "party": party, "mine": mine})
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


def lend(game, host, pid, uids, replace=False):
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
    if replace:  # (a swap at the PC: the whole team again)
        out = [{"uid": e["mon"].coop_uid, "rec": story._pokemon_record(e["mon"])} for e in mine]
    host.send(pid, {"t": "event", "lent": out, "settings": _settings(story), "replace": replace})


def _return_one(game, entry):
    story = game.story_manager
    p = entry["mon"]
    p.coop_lent = None
    if entry["party"] and len(story.player_team) < 6 and p in story.pc_pokemon:
        story.pc_pokemon[story.pc_pokemon.index(p)] = None
        story.player_team.append(p)


def _give_back(game, host, pid):
    for entry in _state(host)["lent"].pop(pid, []):
        _return_one(game, entry)


def exchange(game, host, pid, uids):
    """A swap at the PC, as one step: what's no longer wanted goes home, then the new ones are lent."""
    st = _state(host)
    if not isinstance(uids, list) or not uids or len(uids) > MAX_BORROW or _fighting(st, pid):
        return
    mine = st["lent"].setdefault(pid, [])
    for entry in list(mine):
        if entry["mon"].coop_uid not in uids:
            mine.remove(entry)
            _return_one(game, entry)
    held = {e["mon"].coop_uid for e in mine}
    lend(game, host, pid, [u for u in uids if u not in held], replace=True)


# ------------------------------------------------------------------ a guest's money and items
def _journal(game, st):
    """In the host's save too, so a crash can't lose what a guest is owed."""
    game.story_manager.story_flags["coop_ledgers"] = {str(pid): led for pid, led in st["ledgers"].items()}


def _ledger(game, st, pid):
    if pid not in st["ledgers"]:
        st["ledgers"][pid] = {"money": 0, "items": {}, "balls": START_BALLS}
        _journal(game, st)
    return st["ledgers"][pid]


def _send_ledger(game, host, pid):
    st = _state(host)
    host.send(pid, {"t": "event", "ledger_now": _ledger(game, st, pid)})


def sync_data(game):
    """What a guest's menus show: the host's journey (the host's Pokedex, Badges, Journal)."""
    story, data = game.story_manager, game.data.data
    return {"badges": story.badges, "active_badge_region": story.active_badge_region, "story_flags": story.story_flags,
            "catch_counts": story.catch_counts, "defeated": {k: sorted(v) for k, v in story.defeated_trainers.items()},
            "notified_missions": story.notified_missions, "pokedex": data.get("pokedex", {}), "seen": data.get("seen_pokemon", [])}


HONEY_DRAWS = 3


def honey(game, host, pid):
    """A guest spreads Honey: wild Pokemon come out near them."""
    from src.dungeon import core
    import random
    st, ds, at = _state(host), getattr(game, "dungeon_state", None), host.guests[pid].get("at")
    led = _ledger(game, st, pid)

    def note(text):
        host.send(pid, {"t": "event", "fight_no": text})
    if led["items"].get("HONEY", 0) <= 0:
        return note("You don't have any Honey.")
    if ds is None or not hasattr(ds, "run") or not at or at[0] != ds.area_key or at[1] != ds.run.index or not ds._get_wild_pool(ds.area_data):
        return note("No wild Pokemon around here.")
    floor, rng, made = ds.run.floor, random.Random(), 0
    near = [(at[2] + dx, at[3] + dy) for dx in range(-4, 5) for dy in range(-4, 5) if 2 <= abs(dx) + abs(dy) <= 4]
    rng.shuffle(near)
    for t in near:
        if made >= HONEY_DRAWS:
            break
        if floor.walkable(*t) and not floor.occupied(*t) and t != tuple(ds.run.player) and t not in world.people_tiles(game):
            mon = ds._make_wild(rng, t)
            if mon is not None:
                floor.movers.append(core.Mover("wild", t[0], t[1], mon))
                made += 1
    if not made:
        return note("Nothing came out.")
    _use_up(led["items"], "HONEY")
    _journal(game, st)
    _send_ledger(game, host, pid)
    note("Wild Pokemon were drawn in!")


def _sell_price(game, item):
    from src.states.systems.mart import PokeMartState
    mart = types.SimpleNamespace(game=game, BASE_PRICES=PokeMartState.BASE_PRICES, WEATHER_ROCKS=PokeMartState.WEATHER_ROCKS)
    return PokeMartState._price(mart, item) // 2


def pick_up(game, host, pid, tile):
    """An item a guest walked onto: theirs, and gone from the map."""
    from src.pokemon import catching
    from src.states.overworld.dungeon import DungeonState
    ds, st, at = getattr(game, "dungeon_state", None), _state(host), host.guests[pid].get("at")
    if ds is None or not hasattr(ds, "run") or not at or at[0] != ds.area_key or at[1] != ds.run.index or not isinstance(tile, list):
        return
    t = tuple(tile)
    if len(t) != 2 or abs(t[0] - at[2]) + abs(t[1] - at[3]) > 1 or t not in ds.run.floor.items:
        return
    key, led = ds.run.floor.items.pop(t), _ledger(game, st, pid)
    if key == catching.POKE:
        led["balls"] += 1
    elif key == DungeonState.HONEY_PACK:
        led["items"]["HONEY"] = led["items"].get("HONEY", 0) + 3
    else:
        led["items"][key] = led["items"].get(key, 0) + 1
    _journal(game, st)
    host.send(pid, {"t": "event", "found": str(key)})
    _send_ledger(game, host, pid)


def apply_ledger(game, host, pid, got):
    """The guest's Bag after shopping or a fight. Money only comes from what's sold, at the Mart's price, and
    nothing is gained for free."""
    st = _state(host)
    led = _ledger(game, st, pid)
    try:
        money, balls = int(got["money"]), int(got["balls"])
        items = {str(k): int(v) for k, v in got["items"].items() if int(v) > 0 and k != "POKE_BALLS"}  # (the Bag's copy of "balls")
    except (KeyError, TypeError, ValueError, AttributeError):
        return
    gained = balls > led["balls"] or any(v > led["items"].get(k, 0) for k, v in items.items())
    most = led["money"] + sum((q - items.get(k, 0)) * _sell_price(game, k) for k, q in led["items"].items() if q > items.get(k, 0))
    bad = money < 0 or money > most or balls < 0 or max(items.values(), default=0) > 999
    if not bad and (money < most or not gained):
        led.update(money=money, balls=balls, items=items)
        _journal(game, st)


def _merge(game, led):
    """A guest's money and items, into the host's."""
    story = game.story_manager
    story.money += int(led["money"])
    for key, qty in led["items"].items():
        story.add_item(key, int(qty))
    story.balls_left += max(0, int(led["balls"]) - START_BALLS)


def _merge_out(game, host, pid):
    """On leaving, exactly once: the entry goes as it's merged."""
    st = _state(host)
    led = st["ledgers"].pop(pid, None)
    if led is None:
        return
    _merge(game, led)
    _journal(game, st)
    game.update_save_data()
    game.data.save()
    if led["money"] or led["items"]:
        toast(game, f"Added from your friend: ${led['money']:,} and {sum(led['items'].values())} items.")


def recover(game, host):
    """What a crashed session still owed: merged when the next one opens."""
    old = game.story_manager.story_flags.pop("coop_ledgers", None) or {}
    for led in old.values():
        _merge(game, led)
    if old:
        game.update_save_data()
        game.data.save()


def release(game, host, pid):
    """A guest has gone for good: wild Pokemon back on the map, borrowed Pokemon home."""
    st = _state(host)
    raid.drop(game, host, pid)
    for eid in [e for e, f in st["fights"].items() if f["pid"] == pid]:
        f = st["fights"].pop(eid)
        f["floor"].movers.append(f["mover"])
    st["later"].append(lambda: (_give_back(game, host, pid), _merge_out(game, host, pid)))


def close_out(game, host):
    """The session is closing: everyone's Pokemon, money and items come home now."""
    st = _state(host)
    for pid in set(st["lent"]) | set(st["ledgers"]) | {f["pid"] for f in st["fights"].values()}:
        release(game, host, pid)
    for job in st["later"]:
        job()
    st["later"] = []


# ------------------------------------------------------------------ fights
def _fighting(st, pid):
    return pid in st.get("raiders", ()) or any(f["pid"] == pid for f in st["fights"].values())


def _refuse(host, pid, why):
    host.send(pid, {"t": "event", "fight_no": why})


def _claim(game, host, pid, uid, kind):
    """The wild Pokemon or trainer a guest walked up to, off the map (nobody else can meet it), or None if they can't."""
    st = _state(host)
    ds = getattr(game, "dungeon_state", None)
    at = host.guests[pid].get("at")
    if not any(_healthy(e["mon"]) for e in st["lent"].get(pid, [])):
        return _refuse(host, pid, "You need a Pokemon that can fight.")
    if _fighting(st, pid):
        return _refuse(host, pid, "You're already in a fight.")
    if ds is None or not hasattr(ds, "run") or not at or at[0] != ds.area_key or at[1] != ds.run.index:
        return _refuse(host, pid, "It's too far away.")
    floor = ds.run.floor
    mover = next((m for m in floor.movers if m.kind == kind and id(m) == uid), None)
    if mover is None:
        return _refuse(host, pid, "It's gone.")
    pending = getattr(ds, "pending", None) or (None, None)
    if mover is getattr(ds, "encounter", None) or mover is pending[1]:
        return _refuse(host, pid, "Someone else is fighting that one.")
    if abs(mover.x - at[2]) + abs(mover.y - at[3]) > REACH:
        return _refuse(host, pid, "It's too far away.")
    return ds, floor, mover


def _next_eid(st):
    eid = max(list(st["fights"]) + [st.get("last", 0)]) + 1
    st["last"] = eid
    return eid


def start_trainer(game, host, pid, uid):
    """The host's game makes the trainer's team (as for a fight of its own, without showing it); the guest fights it."""
    from src.states.battle import TrainerBattleState, TrainerIntroState
    st, story = _state(host), game.story_manager
    got = _claim(game, host, pid, uid, "trainer")
    if got is None:
        return
    ds, floor, mover = got
    index = mover.payload[0]
    if not story.trainer_on_map(ds.area_key, index, ds.area_data.get("trainer_pool", [{}])[index]):
        return _refuse(host, pid, "That trainer has been beaten.")
    ui, before = game.ui_manager, list(game.ui_manager.elements)
    keep = getattr(ds, "play_state_data", None)
    state = ds._capture_state(lambda: ds.trigger_trainer_battle(specific_index=index))
    ui.elements, ds.play_state_data = before, keep
    battle = state.next_state if isinstance(state, TrainerIntroState) else state
    if not isinstance(battle, TrainerBattleState):
        return _refuse(host, pid, "Not right now.")
    lines = list(state.dialogue_box.text_lines or [])[1:] if isinstance(state, TrainerIntroState) else []
    floor.movers.remove(mover)
    eid = _next_eid(st)
    st["fights"][eid] = {"pid": pid, "floor": floor, "mover": mover, "kind": "trainer", "battle": battle,
                         "area": ds.area_key, "index": index}
    host.send(pid, {"t": "event", "trainer_fight": {
        "eid": eid, "team": [story._pokemon_record(p) for p in battle.opponent_team], "class": battle.trainer_class,
        "name": battle.trainer_name, "dialogue": battle.custom_dialogue, "rewards": battle.rewards,
        "boss": bool(battle.is_boss_battle), "sprite": mover.payload[1].get("sprite"), "lines": [str(x) for x in lines],
        "area": ds.area_key, "battle_type": battle.battle_type, "bg": ds._get_battle_background_for_area(),
        "x": mover.x, "y": mover.y, "f": list(mover.facing), "on_map": bool(ds._ow_on())}})


def _trainer_won(game, host, pid, fight):
    """All progress is the host's. Prize money and ordinary prizes wait with the guest until they leave; things the
    journey needs now (key items, TMs, gift Pokemon) go straight to the host."""
    st, story, battle = _state(host), game.story_manager, fight["battle"]
    story.mark_trainer_defeated(fight["area"], fight["index"])
    if battle.victory_flag:
        story.story_flags[battle.victory_flag] = True
    led = _ledger(game, st, pid)
    led["money"] += int(battle._calc_money_reward())
    candy = int(battle._calc_candy_reward())
    if candy > 0:
        led["items"]["RARE_CANDY"] = led["items"].get("RARE_CANDY", 0) + candy
    tm = battle._tm_reward()
    if tm:
        story.add_item(tm, 1)
    key_items = game.loader.area_data.get("GAME_CONFIG", {}).get("KEY_ITEMS", [])
    for item, qty in battle.rewards.items():
        if item == "balls":
            led["balls"] += int(qty)
        elif item.startswith("POKEMON_"):
            from src.world import story_events
            story_events.gift_pokemon(game, int(item[8:]))
        elif item in key_items:
            story.add_item(item if story.inventory.get(item, 0) <= 0 else "RARE_CANDY", qty if story.inventory.get(item, 0) <= 0 else 2)
        else:
            led["items"][item] = led["items"].get(item, 0) + int(qty)
    _journal(game, st)
    game.update_save_data()
    game.data.save()
    toast(game, f"{host.guests[pid]['name']} beat {battle.trainer_name or 'a trainer'}!")


def start_fight(game, host, pid, uid):
    st, story = _state(host), game.story_manager
    got = _claim(game, host, pid, uid, "wild")
    if got is None:
        return
    ds, floor, mover = got
    floor.movers.remove(mover)
    game.data.mark_seen(mover.payload.id)
    eid = _next_eid(st)
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
        if isinstance(msg.get("ledger"), dict):
            apply_ledger(game, host, pid, msg["ledger"])
        name = host.guests[pid]["name"]
        mover, outcome = fight["mover"], msg.get("outcome")
        if fight.get("kind") == "trainer":
            if outcome == "beaten":
                _trainer_won(game, host, pid, fight)
            else:
                fight["floor"].movers.append(mover)
            host.send(pid, {"t": "event", "fight_done": eid})
            _send_ledger(game, host, pid)
            check_wipe(game, host)
            return
        mon = str(mover.payload.display_name).upper()
        if outcome == "caught":
            lines = _keep_catch(game, mover.payload, msg.get("ball"))
            toast(game, f"{name} caught {mon}! Sent to the PC." if not lines else f"{name} caught {mon}! {lines[-1]}")
        elif outcome == "beaten":
            toast(game, f"{name} beat a wild {mon}.")
        else:
            fight["floor"].movers.append(mover)
    host.send(pid, {"t": "event", "fight_done": eid})
    _send_ledger(game, host, pid)
    check_wipe(game, host)


# ------------------------------------------------------------------ fainting: "active" is having a Pokemon that can fight
def host_active(game):
    return any(_healthy(p) for p in game.story_manager.player_team)


def _guest_active(host, pid):
    return any(_healthy(e["mon"]) for e in _state(host)["lent"].get(pid, []))


def _someone_else_active(host):
    return any(g["cid"] is not None and _guest_active(host, pid) for pid, g in host.guests.items())


def host_down(game):
    """The host's whole team has fainted. True: a friend's still going, so the host stays and can revive. False: a wipe."""
    host = getattr(game, "coop_host", None)
    if host is None or not _someone_else_active(host):
        return False
    game.coop_host_down = True
    return True


def down_list(game, host):
    """Who has fainted out and could be revived: who 0 is the host."""
    st, out = _state(host), []
    if getattr(game, "coop_host_down", False):
        out.append({"who": 0, "name": str(getattr(game, "player_name", "") or "Host")})
    for pid, g in host.guests.items():
        if g["cid"] is not None and st["lent"].get(pid) and not _guest_active(host, pid) and not _fighting(st, pid):
            out.append({"who": pid, "name": g["name"]})
    return out


def revive_item(items):
    return next((k for k in REVIVES if items.get(k, 0) > 0), None)


def _use_up(items, item):
    items[item] -= 1
    if items[item] <= 0:
        del items[item]


def host_can_help(game, host):
    """The first friend the host could revive with a Revive from the host's own Bag, or None."""
    if getattr(game, "coop_vote", None) or not host_active(game) or not revive_item(game.story_manager.inventory):
        return None
    return next((d for d in down_list(game, host) if d["who"] != 0), None)


def revive(game, host, rescuer, who):
    """An active player spends one of their own Revives on someone who's fainted out (rescuer / who 0: the host)."""
    from src.pokemon import items as itemlib
    st, story = _state(host), game.story_manager
    if rescuer == who or who not in [d["who"] for d in down_list(game, host)]:
        return
    if not (host_active(game) if rescuer == 0 else _guest_active(host, rescuer) and not _fighting(st, rescuer)):
        return
    bag = story.inventory if rescuer == 0 else _ledger(game, st, rescuer)["items"]
    item = revive_item(bag)
    team = story.player_team if who == 0 else [e["mon"] for e in st["lent"].get(who, [])]
    p = next((m for m in team if m.current_hp <= 0 and not getattr(m, "is_egg", False)), None)
    if item is None or p is None or not itemlib.medicine_effect(item, p)[0]:
        return
    _use_up(bag, item)
    if rescuer != 0:
        _journal(game, st)
        _send_ledger(game, host, rescuer)
    helper = str(getattr(game, "player_name", "") or "Host") if rescuer == 0 else host.guests[rescuer]["name"]
    if who == 0:
        game.coop_host_down = False
        toast(game, f"{helper} revived your {p.display_name.upper()}!")
    else:
        host.send(who, {"t": "event", "revived": {"uid": p.coop_uid, "hp": p.current_hp, "by": helper}})


def host_tethered(game, t):
    """The host has fainted out: only near a friend who can still fight."""
    host = getattr(game, "coop_host", None)
    me = world.where(game)
    if host is None or not getattr(game, "coop_host_down", False) or me is None:
        return False
    near = [g["at"] for pid, g in host.guests.items() if g.get("at") and tuple(g["at"][:2]) == me[:2] and _guest_active(host, pid)]
    return bool(near) and all(abs(a[2] - t[0]) + abs(a[3] - t[1]) > TETHER for a in near)


def wipe_guests(game):
    """Everyone's out: back to the last Pokemon Center together, teams healed."""
    host = getattr(game, "coop_host", None)
    if host is None:
        return
    for pid, entries in _state(host)["lent"].items():
        for entry in entries:
            entry["mon"].heal_full()
        host.send(pid, {"t": "event", "wipe": True})


def check_wipe(game, host):
    """No one has an active Pokemon: the shared wipe. (Not in the middle of the host's own battle: its end decides.)"""
    if not host.guests or host_active(game) or _someone_else_active(host) or world.where(game) is None:
        return
    from src.states.overworld import white_out
    game.coop_host_down = False
    game.coop_vote = None
    wipe_guests(game)
    white_out(game)


# ------------------------------------------------------------------ from the game loop
def handle(game, host, pid, msg):
    if msg.get("roster_ask"):
        host.send(pid, {"t": "event", "roster": rows(game, host, pid)})
    elif "propose" in msg:
        travel.propose(game, host, pid, msg["propose"])
    elif "vote_answer" in msg:
        travel.answer(game, host, pid, msg)
    elif "pick" in msg:
        pick_up(game, host, pid, msg["pick"])
    elif "team" in msg:  # (healed at a Center)
        _apply_team(game, host, pid, msg["team"])
    elif "exchange" in msg:
        _state(host)["later"].append(lambda: exchange(game, host, pid, msg["exchange"]) if pid in host.guests else None)
    elif "ledger" in msg and isinstance(msg["ledger"], dict):
        apply_ledger(game, host, pid, msg["ledger"])
        _send_ledger(game, host, pid)
    elif "borrow" in msg:  # (not in the middle of the host's own battle: its party can't change then)
        _state(host)["later"].append(lambda: lend(game, host, pid, msg["borrow"]) if pid in host.guests else None)
    elif "watch" in msg:  # (the guest's fight, for the host to watch)
        host.guests[pid]["watch"] = msg["watch"] if isinstance(msg["watch"], dict) else None
        world.relay_watch(host, pid)
    elif "sync" in msg:
        host.send(pid, {"t": "event", "sync": sync_data(game)})
    elif "honey" in msg:
        honey(game, host, pid)
    elif "raid_join" in msg:
        raid.join(game, host, pid)
    elif "raid_leave" in msg:
        raid.drop(game, host, pid)
        host.send(pid, {"t": "event", "raid_over": True, "won": False})
    elif "raid_turn" in msg:
        raid.submit(game, host, pid, msg["raid_turn"])
    elif "revive" in msg:
        revive(game, host, pid, msg["revive"])
    elif "trainer" in msg:
        start_trainer(game, host, pid, msg["trainer"])
    elif "fight" in msg:
        start_fight(game, host, pid, msg["fight"])
    elif "fight_end" in msg and isinstance(msg["fight_end"], dict):
        end_fight(game, host, pid, msg["fight_end"])


def tick(game, host):
    st = _state(host)
    if getattr(game, "coop_raid_battle", None) is not None and world.where(game) is not None:
        raid.finish(game, host)  # (back on the map: the raid is over)
    if not st.get("recovered"):
        st["recovered"] = True
        recover(game, host)
    if getattr(game, "coop_host_down", False):
        if host_active(game):  # (healed some other way: a Center, the Bag)
            game.coop_host_down = False
        else:
            check_wipe(game, host)
    if st["later"] and world.where(game) is not None:
        for job in st["later"]:
            job()
        st["later"] = []
