"""Co-op on the map (Jordan, 11-08): the host's side, run once a frame from the game loop. Tells guests where the host
is, hears where they are, and draws them on the host's map. The guest's own screen is src/states/coop_world.py."""
import os

import pygame

TILE = 56
SEND_EVERY = 6      # frames
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


def tick(game):
    host = getattr(game, "coop_host", None)
    if host is None:
        return
    for ev in host.poll():
        if ev[0] == "intent":
            at = ev[2].get("at")
            if isinstance(at, list) and len(at) == 6 and ev[1] in host.guests:
                host.guests[ev[1]]["at"] = at
                host.guests[ev[1]]["char"] = str(ev[2].get("char") or "")
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


def draw_person(game, char, name, sx, sy):
    """A player at the tile whose top-left is (sx, sy) on screen, with their name above."""
    screen = game.screen
    img = person_img(game, char, (0, 1))
    if img is not None:
        screen.blit(img, img.get_rect(midbottom=(sx + TILE // 2, sy + TILE - 4)))
    else:
        pygame.draw.circle(screen, (232, 90, 90), (sx + TILE // 2, sy + TILE // 2), 18)
    tag = game.assets.fonts["caption"].render(str(name), True, (255, 255, 255))
    pill = tag.get_rect(midbottom=(sx + TILE // 2, sy - 22)).inflate(12, 6)
    pygame.draw.rect(screen, (30, 36, 58), pill, border_radius=8)
    screen.blit(tag, tag.get_rect(center=pill.center))


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
                draw_person(game, g.get("char"), g["name"], ox + at[2] * TILE, oy + at[3] * TILE)
    waiting = host.waiting()
    if waiting and st.__class__.__name__ != "CoopState":
        text = f"{waiting[0][1]} wants to join: open Options, then CO-OP"
        tag = game.assets.fonts["label"].render(text, True, (255, 255, 255))
        pill = tag.get_rect(midtop=(game.width // 2, 78)).inflate(24, 12)
        pygame.draw.rect(game.screen, (120, 60, 180), pill, border_radius=10)
        game.screen.blit(tag, tag.get_rect(center=pill.center))
