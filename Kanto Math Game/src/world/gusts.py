"""Timed gusts: a walked room's wind (Black 2's Mistralton Gym, a wind tunnel; Unova 11-24, main cleanup
clean-main-unova-gym-wind).

A room's "gusts": {"every": frames between gusts (default 300), "warn": frames of warning before one (default 90),
"blow": frames it blows (default 40), "from": the side the wind comes from - "n", "s", "e" or "w" (default "n": the turbines
at the back, blowing toward the door), "lanes": [[x0, y0, x1, y1], ...] where the wind reaches (none: the whole room),
"shelter": [[x, y], ...] extra sheltered tiles, "to": [x, y] where a blown player ends up (the door), "lines": {"warn": text,
"blown": text}}.

The turbines spin up (a warning), then blow. Anyone standing in a lane with open floor upwind of them is caught: they slide
downwind tile by tile until something stops them, then (if the room says "to") they're set down at the door. A wall, a
pillar or a person straight upwind shelters you. The clock only runs while you can move (not in a text box or a battle) and
starts again each time you come into the room. walk_town.py calls tick() each frame and draw() with the room's floor."""
import pygame

WINDS = {"n": (0, 1), "s": (0, -1), "e": (-1, 0), "w": (1, 0)}   # (where the wind comes from -> the way it pushes)


def _cfg(state):
    g = getattr(state, "gusts", None)
    return g if isinstance(g, dict) else None


def _push(g):
    return WINDS.get(str(g.get("from") or "n").lower()[:1], (0, 1))


def in_lane(g, t):
    lanes = g.get("lanes") or []
    if not lanes:
        return True
    x, y = t
    return any(min(a, c) <= x <= max(a, c) and min(b, d) <= y <= max(b, d) for a, b, c, d in lanes)


def sheltered(state, g, t):
    """Something solid straight upwind of t: a wall, a pillar, a person (or a tile the room lists)."""
    if [t[0], t[1]] in (g.get("shelter") or []) or tuple(t) in {tuple(s) for s in (g.get("shelter") or [])}:
        return True
    dx, dy = _push(g)
    up = (t[0] - dx, t[1] - dy)
    if not (0 <= up[0] < state.w and 0 <= up[1] < state.h):
        return False
    return state.rows[up[1]][up[0]] != "." or up in state._people()


def phase(state):
    """"calm", "warn" or "blow" now."""
    g = _cfg(state)
    if not g:
        return "calm"
    every, warn, blow = int(g.get("every", 300)), int(g.get("warn", 90)), int(g.get("blow", 40))
    t = getattr(state, "_gust_t", 0) % max(1, every)
    if t >= every - blow:
        return "blow"
    if t >= every - blow - warn:
        return "warn"
    return "calm"


def reset(state):
    state._gust_t, state._gust_slide, state._gust_said = 0, False, None


def tick(state):
    """Each frame. True while you're being blown along (the caller takes no other moves)."""
    g = _cfg(state)
    if not g:
        return False
    if getattr(state, "_gust_slide", False):
        if state.anim > 0:
            state.anim = max(0, state.anim - 1)
            return True
        dx, dy = _push(g)
        nxt = (state.player[0] + dx, state.player[1] + dy)
        if (0 <= nxt[0] < state.w and 0 <= nxt[1] < state.h and state.rows[nxt[1]][nxt[0]] == "."
                and nxt not in state.exits and nxt not in state._people() and nxt not in getattr(state, "barred", {})):
            state.anim_from, state.player = state.player, nxt
            state.anim = max(1, getattr(state, "STEP_GUST", 4))
            return True
        state._gust_slide = False
        to = g.get("to")
        if to and tuple(to) != tuple(state.player):
            state.anim_from = state.player = tuple(to)
            state.facing = (-dx, -dy) if (dx, dy) != (0, 0) else state.facing
        return True
    if state._busy():
        return False
    state._gust_t = getattr(state, "_gust_t", 0) + 1
    now = phase(state)
    lines = g.get("lines") or {}
    if now == "warn" and getattr(state, "_gust_said", None) != "warn":
        state._gust_said = "warn"
        state.flash(lines.get("warn") or "The turbines are spinning up...", 80)
    elif now == "blow":
        if getattr(state, "_gust_said", None) != "blow":
            state._gust_said = "blow"
        if state.anim == 0 and in_lane(g, state.player) and not sheltered(state, g, state.player):
            state.walk_goal = None
            state._gust_slide = True
            state.flash(lines.get("blown") or "A gust blew you back!", 100)
            return True
    elif now == "calm":
        state._gust_said = None
    return False


def draw(state, screen, at, fonts=None):
    """Wind streaks over the lanes while it warns (faint) and blows."""
    g = _cfg(state)
    now = phase(state) if g else "calm"
    if now == "calm":
        return
    dx, dy = _push(g)
    t = getattr(state, "_gust_t", 0)
    alpha = 70 if now == "warn" else 150
    lanes = g.get("lanes") or [[0, 0, state.w - 1, state.h - 1]]
    for a, b, c, d in lanes:
        x0, y0, x1, y1 = min(a, c), min(b, d), max(a, c), max(b, d)
        r0, r1 = at((x0, y0)), at((x1, y1))
        box = pygame.Rect(r0.x, r0.y, r1.right - r0.x, r1.bottom - r0.y)
        if box.w <= 0 or box.h <= 0:
            continue
        veil = pygame.Surface(box.size, pygame.SRCALPHA)
        n = max(4, (box.w * box.h) // 2600)
        for i in range(n):
            # (streaks drift downwind with the clock; each one's own lane across the wind)
            if dy:
                x = (i * 37 + 11) % max(1, box.w)
                y = ((i * 53 + t * 9 * (1 if dy > 0 else -1)) % (box.h + 40)) - 20
                pygame.draw.line(veil, (235, 245, 255, alpha), (x, y), (x, y + 18 * dy), 2)
            else:
                y = (i * 37 + 11) % max(1, box.h)
                x = ((i * 53 + t * 9 * (1 if dx > 0 else -1)) % (box.w + 40)) - 20
                pygame.draw.line(veil, (235, 245, 255, alpha), (x, y), (x + 18 * dx, y), 2)
        screen.blit(veil, box.topleft)
