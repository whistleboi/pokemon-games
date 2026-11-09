"""Co-op on the map (Jordan, 11-08): the host's side, run once a frame from the game loop. Tells guests where the host
is, hears where they are, and draws them on the host's map. The guest's own screen is src/states/coop_world.py."""
import base64
import json
import os
import types
import zlib

import pygame

TILE = 56
SEND_EVERY = 6      # frames
SCENE_AGAIN = 60    # frames: what's on the map is sent when it changes, and this often anyway (someone just joined)
FACING_ROW = {(0, 1): 0, (-1, 0): 1, (1, 0): 2, (0, -1): 3}


def where(game):
    """(area, floor, x, y, facing) of whoever is walking this screen, or None (a battle, a menu)."""
    st = game.current_state
    area = getattr(st, "area_key", None)
    if area is None:
        return None
    run = getattr(st, "run", None)
    if run is not None and getattr(st, "mode", None) != "CATCH":
        return area, run.index, run.player[0], run.player[1], tuple(getattr(st, "facing", (0, 1)))
    if run is None and isinstance(getattr(st, "player", None), tuple):
        return area, 0, st.player[0], st.player[1], tuple(getattr(st, "facing", (0, 1)))
    return None


def _look(item):
    """What a guest needs to draw a figure or a townsperson (the same drawing code, on the same game files)."""
    out = {"text": str(item.get("text", ""))}
    action = item.get("action")
    if action == "ARRIVAL":
        out.update(action=action, event={"trainer": {"sprite": ((item.get("event") or {}).get("trainer") or {}).get("sprite")}})
    elif action == "BOSS":
        out.update(action=action, boss={"id": (item.get("boss") or {}).get("id")})
    return out


def _named(game, lines):
    from src.states.overworld.common import _fill_names
    return [str(_fill_names(game, line)) for line in lines]


def encode_seen(floor):
    bits = bytearray((floor.w * floor.h + 7) // 8)
    for x, y in floor.seen:
        i = y * floor.w + x
        bits[i // 8] |= 1 << (i % 8)
    return base64.b64encode(zlib.compress(bytes(bits))).decode("ascii")


def decode_seen(text, w, h):
    bits = zlib.decompress(base64.b64decode(text))
    return {(i % w, i // w) for i in range(w * h) if bits[i // 8] >> (i % 8) & 1}


def exit_label(st, target):
    """Where a way out on a walked map goes, in words."""
    from src.dungeon import core
    if target == core.STAIRS:
        return st._floor_name(st.run.index + 1)
    if target == core.STAIRS_UP:
        return st._floor_name(st.run.index - 1)
    return str(st._area_name(target))


def _dungeon_scene(game, st, out):
    f = st.run.floor
    for m in f.movers:
        if m.kind == "wild":
            p = m.payload
            out["movers"].append({"k": "w", "x": m.x, "y": m.y, "uid": id(m), "id": int(p.id), "meta": int(getattr(p, "meta_id", p.id) or p.id),
                                  "form": str(getattr(p, "form", "normal") or "normal"), "shiny": bool(p.is_shiny), "gender": getattr(p, "gender", None),
                                  "alert": bool(m.alert), "f": list(getattr(m, "facing", (0, 1)) or (0, 1))})
        elif m.kind == "trainer":
            out["movers"].append({"k": "t", "x": m.x, "y": m.y, "uid": id(m), "sprite": m.payload[1].get("sprite"), "f": list(m.facing)})
        elif m.kind == "figure":
            out["movers"].append({"k": "f", "x": m.x, "y": m.y, "look": _look(m.payload)})
    out["items"] = [[x, y, str(key)] for (x, y), key in f.items.items()]
    if st.run.explore:  # (the host's first visit: the guest gets the same fog)
        out["fog"] = encode_seen(f)
    out["exits"] = [[x, y, exit_label(st, target)] for (x, y), target in f.exits.items()]
    out["tms"] = [[x, y] for (x, y) in f.tm_spots]
    m = st.run.recipe.get("art") or {}
    lines = m["floors"][st.run.index].get("signs", []) if m.get("floors") else m.get("signs", [])
    for (x, y), what in f.decor.items():
        what = str(what)
        if what.startswith("boulder:"):
            out["boulders"].append([x, y])
        elif what.startswith("sign:") and int(what[5:]) < len(lines):
            out["signs"].append([x, y, _named(game, lines[int(what[5:])])])
    flags = game.story_manager.story_flags
    for (x, y), target in f.exits.items():
        gate = st._gate(target)
        if gate and (not gate[2] or (gate[1] and not flags.get(f"gate_used_{st.area_key}_{target}"))):
            out["gates"].append([x, y, gate[0]])
    boss = (st.area_data.get("area_boss") or {}).get("id")
    if boss is not None:
        out["boss"] = boss


def _town_scene(game, st, out):
    for (x, y), opt in st._people().items():
        out["movers"].append({"k": "f", "x": x, "y": y, "look": _look(opt), "town": True,
                              "label": _named(game, [opt.get("text", "")])[0].upper()[:28]})
    out["signs"] = [[x, y, _named(game, lines)] for (x, y), lines in st.signs.items()]
    out["town"] = True
    from src.coop import travel
    out["exits"] = [[x, y, travel.area_name(game, target)] for (x, y), target in st.exits.items()]


def scene(game):
    """What's on the map where the host is, for guests: None in a battle or a menu (they keep the last one)."""
    me = where(game)
    if me is None:
        return None
    st = game.current_state
    out = {"area": me[0], "floor": me[1], "movers": [], "items": [], "tms": [], "boulders": [], "gates": [], "signs": []}
    (_dungeon_scene if getattr(st, "run", None) is not None else _town_scene)(game, st, out)
    return out


def _partner(game):
    """The tile the host's lead Pokemon is on."""
    view = getattr(game.current_state, "overworld", None)
    st = view.play if view is not None else game.current_state
    p = getattr(st, "partner", None)
    return list(p) if isinstance(p, tuple) else None


def people_tiles(game):
    """The tiles guests and their Pokemon stand on, where the host is."""
    host, out = getattr(game, "coop_host", None), set()
    me = where(game) if host is not None else None
    if me is None:
        return out
    for g in host.guests.values():
        at = g.get("at")
        if at and g["cid"] is not None and at[0] == me[0] and at[1] == me[1]:
            out.add((at[2], at[3]))
            if g.get("p"):
                out.add(tuple(g["p"]))
    return out


def occupied(game, t):
    return t in people_tiles(game)


def _mission(game):
    from src.world import guide
    m = guide.tracked_mission(game)
    return {k: m.get(k) for k in ("text", "title", "desc", "description", "type")} if m else None


def relay_watch(host, pid):
    """A guest's fight, for the other guests to watch too."""
    g = host.guests[pid]
    for other in list(host.guests):
        if other != pid:
            host.send(other, {"t": "state", "watch": g.get("watch"), "who": g["name"]})


def _publish_battle(game, host):
    """The host's own fight, for guests to watch."""
    from src.states.battle import TrainerBattleState
    from src.states.coop_watch import snapshot
    st = game.current_state
    feed = snapshot(st) if isinstance(st, TrainerBattleState) and st.opponent_pokemon is not None and st.player_pokemon is not None else None
    if feed != getattr(game, "coop_feed", None):
        game.coop_feed = feed
        for pid in list(host.guests):
            host.send(pid, {"t": "state", "watch": feed})


def tick(game):
    host = getattr(game, "coop_host", None)
    if host is None:
        return
    from src.coop import roster, travel
    for ev in host.poll():
        if ev[0] == "gone":
            roster.release(game, host, ev[1])
        elif ev[0] == "left" and ev[1] in host.guests:
            host.guests[ev[1]]["watch"] = None
            relay_watch(host, ev[1])
            from src.coop import raid
            raid.drop(game, host, ev[1])
        elif ev[0] == "intent" and ev[1] in host.guests and "at" not in ev[2]:
            roster.handle(game, host, ev[1], ev[2])
        elif ev[0] == "intent":
            at = ev[2].get("at")
            if isinstance(at, list) and len(at) == 6 and ev[1] in host.guests:
                host.guests[ev[1]]["at"] = at
                host.guests[ev[1]]["char"] = str(ev[2].get("char") or "")
                host.guests[ev[1]]["lead"], host.guests[ev[1]]["p"] = ev[2].get("lead"), ev[2].get("p")
    roster.tick(game, host)
    travel.tick(game, host)
    game.coop_frame = getattr(game, "coop_frame", 0) + 1
    if game.coop_frame % SEND_EVERY:
        return
    me = where(game)
    run = getattr(game.current_state, "run", None)
    if run is not None:  # (wild Pokemon don't appear next to a friend)
        run.others = [(g["at"][2], g["at"][3]) for g in host.guests.values() if g.get("at") and g["at"][0] == getattr(game.current_state, "area_key", None)]
        if run.explore:
            for g in host.guests.values():
                if g.get("at") and g["at"][0] == getattr(game.current_state, "area_key", None) and g["at"][1] == run.index:
                    run.reveal_at(g["at"][2], g["at"][3])
    if game.coop_frame % 30 < SEND_EVERY:
        game.coop_quest = _mission(game)
    view = getattr(game.current_state, "overworld", None)
    if view is not None:  # (fighting on the map: stepped back behind its Pokemon, and guests should see that)
        game.coop_last = (view.play.area_key, view.play.run.index, view.play.run.player[0], view.play.run.player[1], tuple(view.play.facing))
    info = {"t": "state", "host": {"name": str(getattr(game, "player_name", "") or "Host"),
                                   "char": str(getattr(game, "player_character", "") or "red"), "busy": me is None,
                                   "active": roster.host_active(game), "down": roster.down_list(game, host), "mission": getattr(game, "coop_quest", None),
                                   "lead": lead_of(game.story_manager.player_team), "p": _partner(game),
                                   "others": [{"pid": p, "name": g["name"], "char": g.get("char"), "at": g["at"], "lead": g.get("lead"), "p": g.get("p")}
                                              for p, g in host.guests.items() if g.get("at") and g["cid"] is not None]}}
    if me:
        game.coop_last = me
    last = getattr(game, "coop_last", None)
    if last:
        info["host"].update(area=last[0], floor=last[1], x=last[2], y=last[3], f=list(last[4]))
    _publish_battle(game, host)
    now = scene(game)
    if now is not None:
        text = json.dumps(now, sort_keys=True)
        if text != getattr(game, "coop_scene", None) or game.coop_frame % SCENE_AGAIN < SEND_EVERY:
            game.coop_scene = text
            info["scene"] = now
    for pid in list(host.guests):
        host.send(pid, info)


def sheet_for(game, char):
    from src.states.overworld.dungeon import sprite_map
    players = sprite_map(game).get("players") or {}
    char = str(char or "").lower()
    return players.get(char) or players.get("female" if char in players.get("girls", []) else "male")


GLIDE_STEP = 1 / 8     # tiles a frame: someone else walking, between the updates that say where they are


def glide(game, key, x, y):
    """Where to draw someone else (key) heading for tile (x, y): (x, y, still walking)."""
    at = game.__dict__.setdefault("_coop_glide", {})
    p = at.get(key)
    if p is None or abs(p[0] - x) + abs(p[1] - y) > 3:
        at[key] = [float(x), float(y)]
        return float(x), float(y), False
    moving = False
    for i, target in enumerate((x, y)):
        gap = target - p[i]
        if gap:
            moving = True
            p[i] = target if abs(gap) <= GLIDE_STEP else p[i] + (GLIDE_STEP if gap > 0 else -GLIDE_STEP)
    return p[0], p[1], moving


def walk_frame(moving):
    return (pygame.time.get_ticks() // 160) % 4 if moving else 0


def _base_id(state, pid):
    """A form's species number (2001, Alolan Rattata: 19): its sheets are found by either."""
    if int(pid) < 2000:
        return pid
    entry = state.game.loader.area_data.get("FORM_MAP", {}).get(str(pid)) or {}
    return entry.get("id", pid)


def draw_follower(game, state, lead, x, y, facing, ox, oy):
    """Someone's lead Pokemon, walking behind them. lead: [id, form, shiny]."""
    mon = types.SimpleNamespace(id=lead[0], meta_id=_base_id(state, lead[0]), form=lead[1], is_shiny=lead[2], gender=lead[3] if len(lead) > 3 else None)
    img = state._icon(mon, TILE, facing=tuple(facing))
    if img is not None:
        r = pygame.Rect(int(ox + x * TILE), int(oy + y * TILE), TILE, TILE)
        game.screen.blit(img, img.get_rect(midbottom=(r.centerx, r.bottom - 2)))


def lead_of(team):
    p = next((m for m in team if m and m.current_hp > 0 and not getattr(m, "is_egg", False)), None)
    return [int(p.id), str(p.form), bool(p.is_shiny), getattr(p, "gender", None)] if p is not None else None


def person_img(game, char, facing, height=TILE + 22, frame=0):
    """A player's overworld sprite, facing their way (frame: a step of its walk)."""
    cache = game.__dict__.setdefault("_coop_imgs", {})
    key = (char, tuple(facing), height, frame)
    if key not in cache:
        img = None
        try:
            sheet = sheet_for(game, char)
            big = pygame.image.load(os.path.join(game.assets.assets_dir, "dungeon", "characters", sheet)).convert_alpha()
            cw, ch = big.get_width() // 4, big.get_height() // 4
            cell = big.subsurface((frame * cw, FACING_ROW.get(tuple(facing), 0) * ch, cw, ch))
            cell = cell.subsurface(cell.get_bounding_rect())
            k = max(1, round(height / max(1, cell.get_height())))
            img = pygame.transform.scale(cell, (cell.get_width() * k, cell.get_height() * k))
        except (pygame.error, OSError, TypeError, ValueError):
            pass
        cache[key] = img
    return cache[key]


def draw_person(game, char, name, sx, sy, facing=(0, 1), frame=0):
    """A player at the tile whose top-left is (sx, sy) on screen, with their name above."""
    screen = game.screen
    img = person_img(game, char, facing, frame=frame)
    if img is not None:
        screen.blit(img, img.get_rect(midbottom=(sx + TILE // 2, sy + TILE - 4)))
    else:
        pygame.draw.circle(screen, (232, 90, 90), (sx + TILE // 2, sy + TILE // 2), 18)
    tag = game.assets.fonts["caption"].render(str(name), True, (255, 255, 255))
    pill = tag.get_rect(midbottom=(sx + TILE // 2, sy - 22)).inflate(12, 6)
    pygame.draw.rect(screen, (30, 36, 58), pill, border_radius=8)
    screen.blit(tag, tag.get_rect(center=pill.center))


def draw_guests(game, ox, oy, area, floor):
    """The guests standing on this map, for the host's screen."""
    for g in game.coop_host.guests.values():
        at = g.get("at")
        if at and g["cid"] is not None and at[0] == area and at[1] == floor:
            if g.get("lead") and g.get("p") and list(g["p"]) != [at[2], at[3]]:
                fx, fy, _m = glide(game, ("pet", g["name"]), g["p"][0], g["p"][1])
                draw_follower(game, game.current_state if hasattr(game.current_state, "_icon") else game.current_state.back, g["lead"], fx, fy, (at[4], at[5]), ox, oy)
            x, y, moving = glide(game, ("guest", g["name"]), at[2], at[3])
            draw_person(game, g.get("char"), g["name"], int(ox + x * TILE), int(oy + y * TILE), (at[4], at[5]), walk_frame(moving))


FRIEND_DOT = (255, 170, 70)


def draw_friends_on_minimap(game, rect, area, floor):
    """Guests on the host's mini-map."""
    for g in game.coop_host.guests.values():
        at = g.get("at")
        if at and g["cid"] is not None and at[0] == area and at[1] == floor:
            pygame.draw.circle(game.screen, FRIEND_DOT, (rect.x + 6 + at[2] * 4, rect.y + 6 + at[3] * 4), 3)


def _watchable(game):
    """(the guest who's fighting) if the host, on the map, could watch them now."""
    host = getattr(game, "coop_host", None)
    if host is None or where(game) is None or getattr(game.current_state, "mode", "MAP") != "MAP":
        return None
    return next((p for p, g in host.guests.items() if g.get("watch")), None)


def _pc_friends(game):
    host = getattr(game, "coop_host", None)
    return list(host.guests) if host is not None and type(game.current_state).__name__ == "PCState" else []


def _pc_friend_rect(row):
    return pygame.Rect(170 + row * 206, 14, 196, 56)


def _revive_rect(game):
    return pygame.Rect(game.width // 2 - 150, 246, 300, 52)


def _draw_host_help(game, host, me):
    """Fainted out: where you stand. A friend fainted out: a button, if you've a Revive to give."""
    from src.coop import roster
    screen, font = game.screen, game.assets.fonts["label"]
    if getattr(game, "coop_host_down", False) and me:
        tag = font.render("Your team fainted! Stay close to a friend.", True, (255, 255, 255))
        pill = tag.get_rect(midtop=(game.width // 2, 246)).inflate(24, 12)
        pygame.draw.rect(screen, (150, 60, 60), pill, border_radius=10)
        screen.blit(tag, tag.get_rect(center=pill.center))
    target = roster.host_can_help(game, host) if me else None
    if target:
        r = _revive_rect(game)
        pygame.draw.rect(screen, (60, 150, 90), r, border_radius=10)
        word = font.render(f"REVIVE {target['name']}"[:22], True, (255, 255, 255))
        screen.blit(word, word.get_rect(center=r.center))


def _watch_rect(game):
    return pygame.Rect(game.width // 2 - 150, 186, 300, 52)


def handle_events(game, events):
    """The host's vote, REVIVE and WATCH buttons come before the map's own taps."""
    from src.coop import roster, travel
    events = travel.handle_events(game, events)
    for row, pid in enumerate(_pc_friends(game)):  # (at the PC: a friend's team)
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and _pc_friend_rect(row).collidepoint(e.pos):
                from src.states.coop_borrow import CoopTakeBackState
                game.change_state(CoopTakeBackState(game, game.current_state, pid, roster.rows(game, game.coop_host, pid)))
                return [x for x in events if x is not e]
    target = roster.host_can_help(game, game.coop_host) if where(game) is not None else None
    if target:
        for e in events:
            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and _revive_rect(game).collidepoint(e.pos):
                roster.revive(game, game.coop_host, 0, target["who"])
                return [x for x in events if x is not e]
    pid = _watchable(game)
    if pid is None:
        return events
    for e in events:
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1 and _watch_rect(game).collidepoint(e.pos):
            from src.states.coop_watch import CoopWatchState
            host = game.coop_host
            source = lambda: host.guests[pid].get("watch") if pid in host.guests else None
            game.change_state(CoopWatchState(game, game.current_state, source, host.guests[pid]["name"]))
            return [x for x in events if x is not e]
    return events


def draw(game):
    """Over the host's screen: guests in the same place, and a note if someone's asking to join."""
    host = getattr(game, "coop_host", None)
    if host is None:
        return
    st = game.current_state
    me = where(game)
    camera = getattr(st, "_camera", None)
    minimap = getattr(st, "_minimap_rect", None)
    if me and callable(minimap) and getattr(st, "mode", "MAP") != "CATCH":
        draw_friends_on_minimap(game, minimap(), me[0], me[1])
    if me and callable(camera):
        cx, cy = camera()
        ox, oy = int(game.width / 2 - cx), int(game.height / 2 - cy)
        draw_guests(game, ox, oy, me[0], me[1])
    pid = _watchable(game)
    if pid is not None:
        r = _watch_rect(game)
        pygame.draw.rect(game.screen, (50, 90, 170), r, border_radius=10)
        tag = game.assets.fonts["label"].render(f"WATCH {host.guests[pid]['name']}"[:22], True, (255, 255, 255))
        game.screen.blit(tag, tag.get_rect(center=r.center))
    from src.coop import travel
    travel.draw(game)
    for row, pid in enumerate(_pc_friends(game)):
        r = _pc_friend_rect(row)
        pygame.draw.rect(game.screen, (60, 110, 190), r, border_radius=10)
        tag = game.assets.fonts["label"].render(f"{host.guests[pid]['name']}'s team"[:14], True, (255, 255, 255))
        game.screen.blit(tag, tag.get_rect(center=r.center))
    _draw_host_help(game, host, me)
    note = getattr(game, "coop_toast", None)
    if note:
        game.coop_toast = (note[0], note[1] - 1) if note[1] > 1 else None
        tag = game.assets.fonts["label"].render(note[0], True, (255, 255, 255))
        pill = tag.get_rect(midtop=(game.width // 2, 130)).inflate(24, 12)
        pygame.draw.rect(game.screen, (40, 110, 90), pill, border_radius=10)
        game.screen.blit(tag, tag.get_rect(center=pill.center))
    waiting = host.waiting()
    if waiting and st.__class__.__name__ != "CoopState":
        text = f"{waiting[0][1]} wants to join: open Options, then CO-OP"
        tag = game.assets.fonts["label"].render(text, True, (255, 255, 255))
        pill = tag.get_rect(midtop=(game.width // 2, 78)).inflate(24, 12)
        pygame.draw.rect(game.screen, (120, 60, 180), pill, border_radius=10)
        game.screen.blit(tag, tag.get_rect(center=pill.center))
