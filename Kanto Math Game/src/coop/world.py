"""Co-op on the map (Jordan, 11-08): the host's side, run once a frame from the game loop. Tells guests where the host
is, hears where they are, and draws them on the host's map. The guest's own screen is src/states/coop_world.py."""
import json
import os

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


def _dungeon_scene(game, st, out):
    f = st.run.floor
    for m in f.movers:
        if m.kind == "wild":
            p = m.payload
            out["movers"].append({"k": "w", "x": m.x, "y": m.y, "uid": id(m), "id": int(p.id), "meta": int(getattr(p, "meta_id", p.id) or p.id),
                                  "form": str(getattr(p, "form", "normal") or "normal"), "shiny": bool(p.is_shiny),
                                  "alert": bool(m.alert), "f": list(getattr(m, "facing", (0, 1)) or (0, 1))})
        elif m.kind == "trainer":
            out["movers"].append({"k": "t", "x": m.x, "y": m.y, "sprite": m.payload[1].get("sprite"), "f": list(m.facing)})
        elif m.kind == "figure":
            out["movers"].append({"k": "f", "x": m.x, "y": m.y, "look": _look(m.payload)})
    out["items"] = [[x, y, str(key)] for (x, y), key in f.items.items()]
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


def scene(game):
    """What's on the map where the host is, for guests: None in a battle or a menu (they keep the last one)."""
    me = where(game)
    if me is None:
        return None
    st = game.current_state
    out = {"area": me[0], "floor": me[1], "movers": [], "items": [], "tms": [], "boulders": [], "gates": [], "signs": []}
    (_dungeon_scene if getattr(st, "run", None) is not None else _town_scene)(game, st, out)
    return out


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
    from src.coop import roster
    for ev in host.poll():
        if ev[0] == "gone":
            roster.release(game, host, ev[1])
        elif ev[0] == "left" and ev[1] in host.guests:
            host.guests[ev[1]]["watch"] = None
        elif ev[0] == "intent" and ev[1] in host.guests and "at" not in ev[2]:
            roster.handle(game, host, ev[1], ev[2])
        elif ev[0] == "intent":
            at = ev[2].get("at")
            if isinstance(at, list) and len(at) == 6 and ev[1] in host.guests:
                host.guests[ev[1]]["at"] = at
                host.guests[ev[1]]["char"] = str(ev[2].get("char") or "")
    roster.tick(game, host)
    game.coop_frame = getattr(game, "coop_frame", 0) + 1
    if game.coop_frame % SEND_EVERY:
        return
    me = where(game)
    info = {"t": "state", "host": {"name": str(getattr(game, "player_name", "") or "Host"),
                                   "char": str(getattr(game, "player_character", "") or "red"), "busy": me is None}}
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


def person_img(game, char, facing, height=TILE + 22):
    """A player's overworld sprite, facing their way."""
    cache = game.__dict__.setdefault("_coop_imgs", {})
    key = (char, tuple(facing), height)
    if key not in cache:
        img = None
        try:
            sheet = sheet_for(game, char)
            big = pygame.image.load(os.path.join(game.assets.assets_dir, "dungeon", "characters", sheet)).convert_alpha()
            cw, ch = big.get_width() // 4, big.get_height() // 4
            cell = big.subsurface((0, FACING_ROW.get(tuple(facing), 0) * ch, cw, ch))
            cell = cell.subsurface(cell.get_bounding_rect())
            k = max(1, round(height / max(1, cell.get_height())))
            img = pygame.transform.scale(cell, (cell.get_width() * k, cell.get_height() * k))
        except (pygame.error, OSError, TypeError, ValueError):
            pass
        cache[key] = img
    return cache[key]


def draw_person(game, char, name, sx, sy, facing=(0, 1)):
    """A player at the tile whose top-left is (sx, sy) on screen, with their name above."""
    screen = game.screen
    img = person_img(game, char, facing)
    if img is not None:
        screen.blit(img, img.get_rect(midbottom=(sx + TILE // 2, sy + TILE - 4)))
    else:
        pygame.draw.circle(screen, (232, 90, 90), (sx + TILE // 2, sy + TILE // 2), 18)
    tag = game.assets.fonts["caption"].render(str(name), True, (255, 255, 255))
    pill = tag.get_rect(midbottom=(sx + TILE // 2, sy - 22)).inflate(12, 6)
    pygame.draw.rect(screen, (30, 36, 58), pill, border_radius=8)
    screen.blit(tag, tag.get_rect(center=pill.center))


def _watchable(game):
    """(the guest who's fighting) if the host, on the map, could watch them now."""
    host = getattr(game, "coop_host", None)
    if host is None or where(game) is None or getattr(game.current_state, "mode", "MAP") != "MAP":
        return None
    return next((p for p, g in host.guests.items() if g.get("watch")), None)


def _watch_rect(game):
    return pygame.Rect(game.width // 2 - 150, 186, 300, 52)


def handle_events(game, events):
    """The host's WATCH button comes before the map's own taps."""
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
    if me and callable(camera):
        cx, cy = camera()
        ox, oy = int(game.width / 2 - cx), int(game.height / 2 - cy)
        for g in host.guests.values():
            at = g.get("at")
            if at and g["cid"] is not None and at[0] == me[0] and at[1] == me[1]:
                draw_person(game, g.get("char"), g["name"], ox + at[2] * TILE, oy + at[3] * TILE, (at[4], at[5]))
    pid = _watchable(game)
    if pid is not None:
        r = _watch_rect(game)
        pygame.draw.rect(game.screen, (50, 90, 170), r, border_radius=10)
        tag = game.assets.fonts["label"].render(f"WATCH {host.guests[pid]['name']}"[:22], True, (255, 255, 255))
        game.screen.blit(tag, tag.get_rect(center=r.center))
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
