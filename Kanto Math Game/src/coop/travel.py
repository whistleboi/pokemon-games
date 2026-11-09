"""Co-op travel votes (Jordan, 11-08): either player can suggest going somewhere, and if it's agreed on, everyone goes. The
host can go anyway after a guest says no. Runs on the host; a guest's own panel is in src/states/coop_world.py."""
import pygame

PANEL_Y = 240


def _connected(host):
    return [pid for pid, g in host.guests.items() if g["cid"] is not None and g.get("at")]


def _fighting(host, pid):
    return any(f["pid"] == pid for f in host.__dict__.get("roster", {}).get("fights", {}).values())


def area_name(game, key):
    return str((game.loader.area_data.get("STORY_PROGRESSION", {}).get(key) or {}).get("route_name") or key)


def _run(game, go):
    """Goes ahead: anything it calls that would ask again doesn't."""
    game.coop_travel_ok = True
    try:
        go()
    finally:
        game.coop_travel_ok = False


def passing(game, go):
    """(a way out already agreed on, finishing a moment later: after "used CUT!")"""
    _run(game, go)


def _begin(game, host, label, go, step_back, by, need):
    game.coop_vote_id = getattr(game, "coop_vote_id", 0) + 1
    vote = {"id": game.coop_vote_id, "label": str(label), "go": go, "step_back": step_back, "by": by, "need": set(need),
            "yes": set(), "no": set(), "host_says": None if by is not None else True}
    game.coop_vote = vote
    who = host.guests[by]["name"] if by is not None else str(getattr(game, "player_name", "") or "Host")
    for pid in need:
        host.send(pid, {"t": "event", "vote": {"id": vote["id"], "who": who, "label": vote["label"]}})


def held(game, label, go, step_back=None):
    """Ask before travelling. True: the trip waits for the vote (go runs if it's agreed on). False: just go."""
    host = getattr(game, "coop_host", None)
    if host is None or getattr(game, "coop_travel_ok", False):
        return False
    if getattr(game, "coop_vote", None):  # (one question at a time)
        if step_back:
            step_back()
        return True
    need = _connected(host)
    if not need:
        return False
    _begin(game, host, label, go, step_back, None, need)
    return True


def _end(game, host, went):
    vote, game.coop_vote = game.coop_vote, None
    for pid in list(host.guests):
        host.send(pid, {"t": "event", "vote_over": vote["id"], "went": went})
    if went:
        _run(game, vote["go"])
    elif vote["step_back"]:
        vote["step_back"]()


def _settle(game, host):
    vote = game.coop_vote
    if vote["host_says"] is False or (vote["by"] is not None and vote["no"]):
        _end(game, host, False)
    elif vote["host_says"] and not vote["no"] and vote["need"] <= vote["yes"]:
        _end(game, host, True)


def answer(game, host, pid, msg):
    vote = getattr(game, "coop_vote", None)
    if vote is None or msg.get("vote_answer") != vote["id"] or pid not in vote["need"]:
        return
    (vote["yes"] if msg.get("yes") else vote["no"]).add(pid)
    _settle(game, host)


def propose(game, host, pid, tile):
    """A guest suggests a way out they've walked to."""
    from src.coop import world
    from src.dungeon import core

    def no(why):
        host.send(pid, {"t": "event", "propose_no": why})
    me, at = world.where(game), host.guests[pid].get("at")
    if not isinstance(tile, list) or len(tile) != 2 or me is None or not at or tuple(at[:2]) != me[:2]:
        return no("The host is busy right now.")
    if getattr(game, "coop_vote", None):
        return no("There's already a question waiting.")
    t, st = tuple(tile), game.current_state
    if abs(t[0] - at[2]) + abs(t[1] - at[3]) > 1:
        return no("That's too far away.")
    if getattr(st, "run", None) is not None:
        target = st.run.floor.exits.get(t)
        if target is None:
            return no("There's no way through there.")
        event = ("stairs",) if target == core.STAIRS else ("stairs_up",) if target == core.STAIRS_UP else ("exit", target)
        label, go = world.exit_label(st, target), (lambda: st._handle([event]))
    else:
        target = st.exits.get(t)
        if target is None:
            return no("There's no way through there.")
        label, go = area_name(game, target), (lambda: st._leave(target))
    _begin(game, host, label, go, None, pid, [p for p in _connected(host) if p != pid])
    _settle(game, host)


def tick(game, host):
    vote = getattr(game, "coop_vote", None)
    if vote is None:
        return
    here = set(_connected(host))
    if vote["by"] is not None and vote["by"] not in here:  # (whoever suggested it has gone)
        return _end(game, host, False)
    if vote["need"] - here:  # (someone who dropped doesn't hold everyone up)
        vote["need"] &= here
        vote["no"] &= here
        vote["yes"] &= here
        _settle(game, host)


def _host_yes(game):
    vote, host = game.coop_vote, game.coop_host
    vote["host_says"] = True
    _settle(game, host)


def _host_no(game):
    game.coop_vote["host_says"] = False
    _settle(game, game.coop_host)


def _go_anyway(game):
    vote = game.coop_vote
    vote["no"].clear()
    vote["yes"] |= vote["need"]
    _settle(game, game.coop_host)


def _cancel(game):
    _end(game, game.coop_host, False)


def _can_override(game, vote):
    """After a no, or while the only ones left to answer are in a fight (they answer when it's over)."""
    host = game.coop_host
    waiting = vote["need"] - vote["yes"] - vote["no"]
    return bool(vote["no"]) or (bool(waiting) and all(_fighting(host, p) for p in waiting))


def _lines_and_buttons(game):
    vote, host = game.coop_vote, game.coop_host
    if vote["by"] is not None:
        text = f"{host.guests[vote['by']]['name']} wants to go to {vote['label']}."
        return text, [("YES", (60, 150, 90), _host_yes), ("NO", (200, 70, 60), _host_no)]
    if vote["no"]:
        names = ", ".join(host.guests[p]["name"] for p in vote["no"] if p in host.guests)
        text = f"{names} said no to {vote['label']}."
    else:
        text = f"Asking to go to {vote['label']}..."
    buttons = [("GO ANYWAY", (60, 150, 90), _go_anyway)] if _can_override(game, vote) else []
    return text, buttons + [("STAY" if vote["no"] else "CANCEL", (200, 70, 60), _cancel)]


def _rects(game, count):
    w, gap = 220, 16
    x = game.width // 2 - (count * w + (count - 1) * gap) // 2
    return [pygame.Rect(x + i * (w + gap), PANEL_Y + 70, w, 60) for i in range(count)]


def handle_events(game, events):
    """The host's answer comes before anything else on the screen; waiting on a vote, the map waits too."""
    vote = getattr(game, "coop_vote", None)
    if vote is None:
        return events
    _text, buttons = _lines_and_buttons(game)
    rects = _rects(game, len(buttons))
    left = []
    for e in events:
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            hit = next((b for r, b in zip(rects, buttons) if r.collidepoint(e.pos)), None)
            if hit:
                hit[2](game)
                return left
        if vote["by"] is None and e.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.KEYDOWN):
            continue
        left.append(e)
    return left


def draw(game):
    if getattr(game, "coop_vote", None) is None:
        return
    screen = game.screen
    text, buttons = _lines_and_buttons(game)
    font = game.assets.fonts["label"]
    tag = font.render(text, True, (255, 255, 255))
    panel = pygame.Rect(0, PANEL_Y, max(tag.get_width() + 60, len(buttons) * 236 + 40), 146)
    panel.centerx = game.width // 2
    pygame.draw.rect(screen, (30, 36, 58), panel, border_radius=12)
    pygame.draw.rect(screen, (120, 140, 200), panel, 3, border_radius=12)
    screen.blit(tag, tag.get_rect(midtop=(panel.centerx, panel.y + 18)))
    for r, (label, color, _fn) in zip(_rects(game, len(buttons)), buttons):
        pygame.draw.rect(screen, color, r, border_radius=10)
        word = font.render(label, True, (255, 255, 255))
        screen.blit(word, word.get_rect(center=r.center))
